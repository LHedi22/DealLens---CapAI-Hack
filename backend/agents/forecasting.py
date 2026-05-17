import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import DealHistory
from backend.agents.ollama_client import call_ollama, MODEL_A
from backend.debug_state import step_started, step_completed, step_failed

SECTOR_BASE_RATES = {
    "EdTech":            0.44,
    "FinTech":           0.51,
    "HealthTech":        0.48,
    "SaaS":              0.55,
    "Logistics":         0.38,
    "AgriTech":          0.40,
    "E-Commerce":        0.42,
    "CleanTech":         0.46,
    "Manufacturing":     0.35,
    "Construction Tech": 0.37,
}
DEFAULT_BASE_RATE = 0.42

SECTOR_BENCHMARKS = {
    "EdTech":            {"avg_y1_growth": 1.4, "typical_seed_revenue": 80000},
    "FinTech":           {"avg_y1_growth": 1.8, "typical_seed_revenue": 120000},
    "HealthTech":        {"avg_y1_growth": 1.2, "typical_seed_revenue": 90000},
    "SaaS":              {"avg_y1_growth": 2.0, "typical_seed_revenue": 150000},
    "Logistics":         {"avg_y1_growth": 1.1, "typical_seed_revenue": 200000},
    "AgriTech":          {"avg_y1_growth": 0.9, "typical_seed_revenue": 60000},
    "E-Commerce":        {"avg_y1_growth": 1.3, "typical_seed_revenue": 100000},
    "CleanTech":         {"avg_y1_growth": 0.8, "typical_seed_revenue": 70000},
    "Manufacturing":     {"avg_y1_growth": 0.7, "typical_seed_revenue": 250000},
    "Construction Tech": {"avg_y1_growth": 0.9, "typical_seed_revenue": 80000},
}
DEFAULT_BENCHMARK = {"avg_y1_growth": 1.2, "typical_seed_revenue": 100000}

ROI_DISCLAIMER = "AI-reasoned estimates. Not a financial model. Use for directional comparison only."

_REVENUE_SYSTEM = """You are a financial analyst forecasting startup revenue trajectories.
Based on the startup information provided, generate a 12-month revenue forecast.
Be realistic — most early-stage startups significantly miss their own projections.
Use the sector benchmark data provided to anchor your estimates.

Return ONLY a valid JSON object with these exact keys:
{
  "base_case_current": null,
  "base_case_12m": null,
  "optimistic_12m": null,
  "conservative_12m": null,
  "base_case_growth_pct": null,
  "optimistic_growth_pct": null,
  "conservative_growth_pct": null,
  "key_assumption": "one sentence stating the most important assumption",
  "growth_driver": "one sentence on what drives the base case growth"
}

All revenue values in USD integers or null if not determinable.
Growth percentages as integers (e.g. 133 for 133%).
If current revenue is null/zero, set base_case_current to 0.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""


async def run_forecasting(
    extracted: dict,
    business_result: dict,
    esg_result: dict,
    sector_conviction: dict,
    sector: str,
    stage: str,
    db: AsyncSession,
) -> dict:
    step_started("forecasting")
    try:
        revenue_forecast, comparable_exits = await asyncio.gather(
            _generate_revenue_forecast(extracted, sector, stage),
            _load_comparable_exits(db),
            return_exceptions=True,
        )
        if isinstance(revenue_forecast, Exception):
            revenue_forecast = _default_revenue_forecast(extracted, sector)
        if isinstance(comparable_exits, Exception):
            comparable_exits = []

        success_probability = _compute_success_probability(sector, business_result, esg_result)
        roi_estimate = _compute_roi_estimate(comparable_exits, success_probability)
        sector_trend = _build_sector_trend(sector_conviction, extracted, sector)

        result = {
            "revenue_trajectory": revenue_forecast,
            "success_probability": success_probability,
            "roi_estimate": roi_estimate,
            "sector_trend": sector_trend,
            "disclaimer": ROI_DISCLAIMER,
        }
        prob = success_probability.get("probability_pct", 0)
        step_completed("forecasting", f"P(success): {prob}% | Signal: {sector_trend.get('signal')}")
        return result
    except Exception as e:
        step_failed("forecasting", type(e).__name__, str(e))
        raise


async def _generate_revenue_forecast(extracted: dict, sector: str, stage: str) -> dict:
    benchmark = SECTOR_BENCHMARKS.get(sector, DEFAULT_BENCHMARK)

    user_content = (
        f"Forecast 12-month revenue for this startup:\n\n"
        f"Sector: {sector} | Stage: {stage}\n"
        f"Current revenue: ${extracted.get('current_revenue') or 0}\n"
        f"Projected Y1 (startup claim): ${extracted.get('projected_revenue_y1') or 'not stated'}\n"
        f"Revenue model: {extracted.get('revenue_model') or 'not stated'}\n"
        f"Traction: {extracted.get('traction_evidence') or 'none stated'}\n"
        f"Unit economics: {extracted.get('unit_economics') or 'not stated'}\n\n"
        f"Sector benchmark context:\n"
        f"- Average Y1 growth for {sector} seed stage: {int(benchmark['avg_y1_growth'] * 100)}%\n"
        f"- Typical {sector} seed starting revenue: ${benchmark['typical_seed_revenue']:,}\n\n"
        f"Base case = blend of startup projection and sector benchmark.\n"
        f"Optimistic = startup claim x1.35 (if stated) or benchmark x1.6.\n"
        f"Conservative = startup claim x0.45 (if stated) or benchmark x0.5."
    )

    raw = await call_ollama(MODEL_A, _REVENUE_SYSTEM, user_content, agent="forecasting")
    return _normalize_revenue_forecast(raw, extracted, benchmark)


def _normalize_revenue_forecast(raw: dict, extracted: dict, benchmark: dict) -> dict:
    def safe_int(v):
        try:
            return int(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    current = safe_int(extracted.get("current_revenue")) or 0
    projected = safe_int(extracted.get("projected_revenue_y1"))
    typical = benchmark.get("typical_seed_revenue", 100000)
    growth = benchmark.get("avg_y1_growth", 1.2)

    base_current = safe_int(raw.get("base_case_current")) or current
    base_12m = safe_int(raw.get("base_case_12m"))
    opt_12m = safe_int(raw.get("optimistic_12m"))
    con_12m = safe_int(raw.get("conservative_12m"))

    if base_12m is None:
        base_12m = int((projected or typical) * growth) if (projected or current == 0) else int(current * (1 + growth))
    if opt_12m is None:
        opt_12m = int(base_12m * 1.5)
    if con_12m is None:
        con_12m = int(base_12m * 0.45)

    def growth_pct(start, end):
        if not start or start == 0:
            return None
        return int(((end - start) / start) * 100) if end else None

    return {
        "base_case_current": base_current,
        "base_case_12m": base_12m,
        "optimistic_12m": opt_12m,
        "conservative_12m": con_12m,
        "base_case_growth_pct": safe_int(raw.get("base_case_growth_pct")) or growth_pct(base_current, base_12m),
        "optimistic_growth_pct": safe_int(raw.get("optimistic_growth_pct")) or growth_pct(base_current, opt_12m),
        "conservative_growth_pct": safe_int(raw.get("conservative_growth_pct")) or growth_pct(base_current, con_12m),
        "key_assumption": raw.get("key_assumption") or f"Based on {benchmark} sector benchmark growth rates.",
        "growth_driver": raw.get("growth_driver") or "Revenue growth driven by market expansion and product adoption.",
        "confidence": "MEDIUM" if extracted.get("projected_revenue_y1") else "LOW",
    }


def _default_revenue_forecast(extracted: dict, sector: str = "") -> dict:
    benchmark = SECTOR_BENCHMARKS.get(sector, DEFAULT_BENCHMARK)
    current = int(extracted.get("current_revenue") or 0)
    base = int(current * 2.0) if current else benchmark["typical_seed_revenue"]
    return {
        "base_case_current": current,
        "base_case_12m": base,
        "optimistic_12m": int(base * 1.5),
        "conservative_12m": int(base * 0.45),
        "base_case_growth_pct": 100 if current else None,
        "optimistic_growth_pct": 200 if current else None,
        "conservative_growth_pct": 10 if current else None,
        "key_assumption": "Sector benchmark growth rates applied. No startup projection available.",
        "growth_driver": "Market expansion and sales team scaling.",
        "confidence": "LOW",
    }


async def _load_comparable_exits(db: AsyncSession) -> list:
    result = await db.execute(
        select(DealHistory).where(
            DealHistory.is_pipeline == False,  # noqa: E712
            DealHistory.outcome.isnot(None),
        )
    )
    comparables = []
    for deal in result.scalars().all():
        outcome = (deal.outcome or "").lower()
        if "acquired" in outcome:
            comparables.append({
                "startup_name": deal.startup_name,
                "sector": deal.sector,
                "exit_type": "acquisition",
                "exit_multiple": 9.0,
                "description": f"{deal.startup_name} ({deal.sector}) — acquired",
            })
        elif "performing" in outcome:
            comparables.append({
                "startup_name": deal.startup_name,
                "sector": deal.sector,
                "exit_type": "performing",
                "exit_multiple": 4.5,
                "description": f"{deal.startup_name} ({deal.sector}) — performing (Series A track)",
            })
    return comparables


def _compute_success_probability(sector: str, business_result: dict, esg_result: dict) -> dict:
    base_rate = SECTOR_BASE_RATES.get(sector, DEFAULT_BASE_RATE)
    adjustments = []
    total_adj = 0.0

    biz_score = business_result.get("composite_score", 50)
    if biz_score >= 75:
        adj = +0.06; adjustments.append({"label": "Strong business score", "value": adj})
    elif biz_score >= 60:
        adj = +0.03; adjustments.append({"label": "Solid business score", "value": adj})
    elif biz_score < 50:
        adj = -0.08; adjustments.append({"label": "Weak business fundamentals", "value": adj})
    else:
        adj = 0.0
    total_adj += adj

    esg_tier = esg_result.get("tier", "Adequate")
    if esg_tier == "Strong":
        adj = +0.03; adjustments.append({"label": "Strong ESG profile", "value": adj})
        total_adj += adj
    elif esg_tier == "Critical Risk":
        adj = -0.10; adjustments.append({"label": "Critical ESG risk", "value": adj})
        total_adj += adj

    team_score = business_result.get("team_score", 50)
    if team_score >= 75:
        adj = +0.04; adjustments.append({"label": "Strong founding team", "value": adj})
        total_adj += adj
    elif team_score < 40:
        adj = -0.05; adjustments.append({"label": "Weak team score", "value": adj})
        total_adj += adj

    traction_score = business_result.get("traction_score", 50)
    if traction_score >= 75:
        adj = +0.04; adjustments.append({"label": "Strong traction evidence", "value": adj})
        total_adj += adj
    elif traction_score < 40:
        adj = -0.08; adjustments.append({"label": "No traction evidence", "value": adj})
        total_adj += adj

    red_flags = esg_result.get("red_flags_triggered", [])
    if "RF-03" in red_flags or "RF-09" in red_flags:
        adj = -0.04; adjustments.append({"label": "Governance red flag detected", "value": adj})
        total_adj += adj

    final_prob = max(0.05, min(0.95, base_rate + total_adj))

    milestone = (
        "Series A or strategic partnership"
        if sector in ("Manufacturing", "Construction Tech")
        else "Series A"
    )

    return {
        "probability_pct": int(round(final_prob * 100)),
        "sector_base_rate_pct": int(round(base_rate * 100)),
        "adjustments": [
            {"label": a["label"], "value_pct": int(round(a["value"] * 100))}
            for a in adjustments
        ],
        "confidence": "MEDIUM",
        "milestone": milestone,
        "horizon_months": 24,
    }


def _compute_roi_estimate(comparables: list, success_probability: dict) -> dict:
    if not comparables:
        return {
            "expected_multiple": None,
            "probability_weighted_multiple": None,
            "comparables_used": [],
            "confidence": "LOW",
            "note": "No comparable exits in fund memory yet. ROI estimate unavailable.",
            "disclaimer": ROI_DISCLAIMER,
        }

    multiples = [c["exit_multiple"] for c in comparables]
    avg_multiple = sum(multiples) / len(multiples)
    prob = success_probability["probability_pct"] / 100
    prob_weighted = round(avg_multiple * prob, 1)
    confidence = "HIGH" if len(comparables) >= 3 else "MEDIUM"

    return {
        "expected_multiple": round(avg_multiple, 1),
        "probability_weighted_multiple": prob_weighted,
        "comparables_used": [c["description"] for c in comparables],
        "confidence": confidence,
        "horizon_years": 5,
        "note": f"Based on {len(comparables)} comparable exit(s) in fund history.",
        "disclaimer": ROI_DISCLAIMER,
    }


def _build_sector_trend(sector_conviction: dict, extracted: dict, sector: str) -> dict:
    direction = sector_conviction.get("trend_direction", "stable")
    win_rate = sector_conviction.get("win_rate", 0)
    total_evals = sector_conviction.get("total_evaluations", 0)

    if direction == "improving" and win_rate >= 50:
        signal = "POSITIVE"
    elif direction == "declining" or win_rate < 30:
        signal = "CAUTIOUS"
    else:
        signal = "NEUTRAL"

    return {
        "sector": sector_conviction.get("sector", sector),
        "fund_win_rate_pct": win_rate,
        "total_fund_evaluations": total_evals,
        "trend_direction": direction,
        "signal": signal,
        "startup_growth_claim": extracted.get("growth_rate"),
        "note": sector_conviction.get("learning_note", ""),
    }
