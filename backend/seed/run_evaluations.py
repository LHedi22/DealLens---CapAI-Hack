"""
One-time evaluation runner — generates real AI scores from synthetic pitch deck documents.

Run from project root (with Ollama running):
    python backend/seed/run_evaluations.py

Prerequisites:
    ollama serve
    ollama pull mistral
    ollama pull llama3.2:3b

Output:
    backend/seed/cached_evals/{StartupName}.json  (one file per startup)

After this script completes:
    - Delete convictai.db
    - Restart the backend — seed_database() will pre-load all 15 cached evals automatically
"""
import asyncio
import json
import os
import sys
import traceback
from datetime import date
from pathlib import Path

# Project root must be in path so backend.* imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from backend.database import AsyncSessionLocal, init_db
from backend.agents.extraction import run_extraction
from backend.agents.business import run_business_scoring
from backend.agents.esg import run_esg_scoring
from backend.agents.memory import run_memory_matching
from backend.agents.forecasting import run_forecasting
from backend.agents.fix_analysis import run_fix_analysis
from backend.agents.portfolio import run_portfolio
from backend.engine.aggregator import aggregate_scores
from backend.engine.recommendation import generate_verdict
from backend.models import PortfolioCompany, DealHistory

DOCS_DIR = Path(__file__).parent / "docs"
CACHE_DIR = Path(__file__).parent / "cached_evals"

_ROI_DISCLAIMER = "AI-reasoned estimates. Not a financial model. Use for directional comparison only."

# Ordered list — history deals must be seeded before any evaluation so
# memory matching has something to compare against.
STARTUPS = [
    {"startup_name": "EduFlow",    "sector": "EdTech",           "stage": "Seed",      "geography": "MENA",          "business_model_type": "SaaS",        "funding_asked": 800000},
    {"startup_name": "NovaPay",    "sector": "FinTech",          "stage": "Pre-seed",  "geography": "Europe",        "business_model_type": "SaaS",        "funding_asked": 500000},
    {"startup_name": "CargoZip",   "sector": "Logistics",        "stage": "Series A",  "geography": "Europe",        "business_model_type": "Marketplace", "funding_asked": 3000000},
    {"startup_name": "HealthCore", "sector": "HealthTech",       "stage": "Seed",      "geography": "North America", "business_model_type": "SaaS",        "funding_asked": 1200000},
    {"startup_name": "BuildSmart", "sector": "Construction Tech","stage": "Seed",      "geography": "MENA",          "business_model_type": "SaaS",        "funding_asked": 600000},
    {"startup_name": "AgroSmart",  "sector": "AgriTech",         "stage": "Seed",      "geography": "MENA",          "business_model_type": "SaaS",        "funding_asked": 900000},
    {"startup_name": "EcoCharge",  "sector": "CleanTech",        "stage": "Pre-seed",  "geography": "Europe",        "business_model_type": "B2B",         "funding_asked": 400000},
    {"startup_name": "ShopNova",   "sector": "E-Commerce",       "stage": "Seed",      "geography": "Asia",          "business_model_type": "Marketplace", "funding_asked": 1100000},
    {"startup_name": "SecureAI",   "sector": "Cybersecurity",    "stage": "Seed",      "geography": "North America", "business_model_type": "SaaS",        "funding_asked": 2000000},
    {"startup_name": "PropMatch",  "sector": "PropTech",         "stage": "Series A",  "geography": "MENA",          "business_model_type": "Marketplace", "funding_asked": 2500000},
    {"startup_name": "InsureNow",  "sector": "InsurTech",        "stage": "Seed",      "geography": "Europe",        "business_model_type": "SaaS",        "funding_asked": 750000},
    {"startup_name": "ManuBot",    "sector": "Manufacturing",    "stage": "Pre-seed",  "geography": "Asia",          "business_model_type": "Hardware",    "funding_asked": 350000},
    {"startup_name": "GameLab",    "sector": "Gaming",           "stage": "Seed",      "geography": "Europe",        "business_model_type": "SaaS",        "funding_asked": 1400000},
    {"startup_name": "RoboFarm",   "sector": "AgriTech",         "stage": "Series A",  "geography": "North America", "business_model_type": "Hardware",    "funding_asked": 5000000},
    {"startup_name": "DataMind",   "sector": "AI/ML",            "stage": "Seed",      "geography": "North America", "business_model_type": "SaaS",        "funding_asked": 2500000},
]


def _default_forecast():
    return {
        "revenue_trajectory": None,
        "success_probability": {
            "probability_pct": 0, "sector_base_rate_pct": 0, "adjustments": [],
            "confidence": "LOW", "milestone": "Series A", "horizon_months": 24,
        },
        "roi_estimate": {
            "expected_multiple": None, "probability_weighted_multiple": None,
            "comparables_used": [], "confidence": "LOW",
            "note": "Forecast unavailable.", "disclaimer": _ROI_DISCLAIMER,
        },
        "sector_trend": {"signal": "NEUTRAL", "trend_direction": "stable", "fund_win_rate_pct": 0},
        "disclaimer": _ROI_DISCLAIMER,
    }


def _default_fix(final_score=50):
    return {
        "problems_found": 0, "fixable_problems": [], "structural_problems": [],
        "top_priority_actions": [], "current_score": final_score, "conditional_score": final_score,
        "score_gap": 0, "fix_verdict": "condition",
        "fix_verdict_label": "CONDITION INVESTMENT",
        "fix_verdict_description": "Fix analysis unavailable.",
    }


def _default_portfolio():
    return {
        "sector_distribution": {}, "concentration_warning": False, "overweight_sectors": [],
        "stage_distribution": {}, "stage_balance_ok": True,
        "geo_distribution": {}, "geo_warning": False,
        "portfolio_esg_before": 0.0, "portfolio_esg_after": 0.0,
        "esg_shift": 0.0, "esg_degradation_flag": False,
        "correlated_companies": [], "correlation_risk": False,
        "fit_verdict": "neutral_fit", "fit_summary": "Portfolio data unavailable.",
        "best_pair": [], "optimizer_reason": "",
    }


async def evaluate_one(startup: dict, db) -> dict | None:
    name = startup["startup_name"]
    doc_path = DOCS_DIR / f"{name}.txt"

    if not doc_path.exists():
        print(f"  [SKIP] {name} — no doc found at {doc_path}")
        return None

    document_text = doc_path.read_text(encoding="utf-8")
    print(f"\n{'─'*58}")
    print(f"  {name}  ({startup['sector']}, {startup['stage']}, {startup['geography']})")
    print(f"{'─'*58}")

    # Step 1: Extraction
    print("  [1/5] Extracting document...")
    extraction_result = await run_extraction(document_text)
    extracted         = extraction_result["extracted"]
    data_completeness = extraction_result["data_completeness"]
    confidence_level  = extraction_result["confidence_level"]
    blind_spots       = extraction_result["blind_spots"]
    print(f"        completeness={data_completeness}%  confidence={confidence_level}  blind_spots={len(blind_spots)}")

    # Step 2: Business + ESG in parallel
    print("  [2/5] Scoring Business + ESG...")
    business_result, esg_result = await asyncio.gather(
        run_business_scoring(extracted),
        run_esg_scoring(extracted, document_text, startup["sector"]),
        return_exceptions=True,
    )
    if isinstance(business_result, Exception):
        print(f"        [WARN] business agent failed: {business_result}")
        business_result = {
            "composite_score": 50, "team_score": 50, "market_score": 50,
            "revenue_score": 50, "traction_score": 50, "moat_score": 50,
            "scalability_score": 50, "top_strengths": [], "top_risks": [],
        }
    if isinstance(esg_result, Exception):
        print(f"        [WARN] ESG agent failed: {esg_result}")
        esg_result = {
            "composite": 50, "e_score": 50, "s_score": 50, "g_score": 50,
            "tier": "Adequate", "red_flags_triggered": [], "red_flag_details": [],
            "verifiability": "Low", "most_critical_flag": None, "esg_reasoning": "unavailable",
        }
    print(f"        business={business_result.get('composite_score')}  esg={esg_result.get('composite')}  flags={esg_result.get('red_flags_triggered', [])}")

    # Step 3: Memory matching (needs DB for history deals)
    print("  [3/5] Memory matching...")
    memory_result = await run_memory_matching(
        incoming={
            "sector":              startup["sector"],
            "stage":               startup["stage"],
            "geography":           startup["geography"],
            "business_model_type": startup["business_model_type"],
            "esg_composite":       esg_result.get("composite", 50),
            "extracted":           extracted,
        },
        db=db,
    )
    conviction_delta = memory_result.get("conviction_delta", 0)
    top_matches      = memory_result.get("top_matches", [])
    print(f"        delta={conviction_delta:+d}  top_match={top_matches[0]['startup_name'] if top_matches else 'none'}")

    # Step 4: Aggregate + verdict (no mandate in seed evals — clean baseline)
    aggregated     = aggregate_scores(
        business=business_result,
        esg=esg_result,
        conviction_delta=conviction_delta,
        mandate=None,
        sector=startup["sector"],
        stage=startup["stage"],
        funding_asked=startup.get("funding_asked"),
    )
    recommendation = generate_verdict(aggregated)
    print(f"        final={aggregated['final_score']}  verdict={recommendation['verdict'].upper()}")

    # Pre-fetch portfolio context (no async inside agents)
    portfolio_rows = await db.execute(select(PortfolioCompany))
    portfolio_companies = [
        {
            "company_name":        co.company_name,
            "sector":              co.sector,
            "stage":               co.stage,
            "geography":           co.geography,
            "business_model_type": co.business_model_type,
            "esg_tier":            co.esg_tier,
        }
        for co in portfolio_rows.scalars().all()
    ]
    pipeline_rows = await db.execute(
        select(DealHistory).where(
            DealHistory.is_pipeline == True,    # noqa: E712
            DealHistory.is_seed_data == False,  # noqa: E712
            DealHistory.decision.in_(["pursue", "watch"]),
        )
    )
    pipeline_candidates = [
        {"startup_name": d.startup_name, "sector": d.sector, "stage": d.stage, "decision": d.decision}
        for d in pipeline_rows.scalars().all()
    ]

    # Step 5: Forecasting + Fix + Portfolio in parallel
    print("  [4/5] Forecasting + Fix + Portfolio...")
    forecast_result, fix_result, portfolio_result = await asyncio.gather(
        run_forecasting(
            extracted=extracted,
            business_result=business_result,
            esg_result=esg_result,
            sector_conviction=memory_result.get("sector_conviction", {}),
            sector=startup["sector"],
            stage=startup["stage"],
            db=db,
        ),
        run_fix_analysis(
            business_result=business_result,
            esg_result=esg_result,
            extracted=extracted,
            final_score=aggregated["final_score"],
            blind_spots=blind_spots,
        ),
        run_portfolio(
            new_startup={
                "sector":              startup["sector"],
                "stage":               startup["stage"],
                "geography":           startup["geography"],
                "business_model_type": startup["business_model_type"],
                "esg_composite":       esg_result.get("composite", 50),
            },
            portfolio_companies=portfolio_companies,
            pipeline_candidates=pipeline_candidates,
        ),
        return_exceptions=True,
    )
    if isinstance(forecast_result, Exception):
        print(f"        [WARN] forecast failed: {forecast_result}")
        forecast_result = _default_forecast()
    if isinstance(fix_result, Exception):
        print(f"        [WARN] fix analysis failed: {fix_result}")
        fix_result = _default_fix(aggregated["final_score"])
    if isinstance(portfolio_result, Exception):
        print(f"        [WARN] portfolio failed: {portfolio_result}")
        portfolio_result = _default_portfolio()

    prob = forecast_result.get("success_probability", {}).get("probability_pct", "?")
    cond = fix_result.get("conditional_score", "?")
    print(f"        success_prob={prob}%  conditional_score={cond}")

    # Build response payload — same shape as POST /evaluate
    mandate_breaches = recommendation.get("mandate_breaches", [])
    payload = {
        "startup_name":    name,
        "sector":          startup["sector"],
        "stage":           startup["stage"],
        "geography":       startup["geography"],

        "final_score":       aggregated["final_score"],
        "business_score":    aggregated["business_score"],
        "adjusted_business": aggregated["adjusted_business"],
        "esg_composite":     aggregated["esg_composite"],
        "conviction_delta":  aggregated["conviction_delta"],
        "confidence_level":  confidence_level,
        "data_completeness": data_completeness,

        "mandate_breach":   False,
        "mandate_flags":    [],
        "verdict":          recommendation["verdict"],
        "verdict_label":    recommendation["verdict_label"],
        "verdict_reason":   recommendation["verdict_reason"],
        "mandate_breaches": mandate_breaches,

        "dimension_scores": {
            "team":        business_result.get("team_score"),
            "market":      business_result.get("market_score"),
            "revenue":     business_result.get("revenue_score"),
            "traction":    business_result.get("traction_score"),
            "moat":        business_result.get("moat_score"),
            "scalability": business_result.get("scalability_score"),
        },
        "top_strengths": business_result.get("top_strengths", []),
        "top_risks":     business_result.get("top_risks", []),

        "esg_e":                  esg_result.get("e_score"),
        "esg_s":                  esg_result.get("s_score"),
        "esg_g":                  esg_result.get("g_score"),
        "esg_tier":               esg_result.get("tier"),
        "esg_verifiability":      esg_result.get("verifiability"),
        "red_flags_triggered":    esg_result.get("red_flags_triggered", []),
        "red_flag_details":       esg_result.get("red_flag_details", []),
        "most_critical_esg_flag": esg_result.get("most_critical_flag"),
        "esg_reasoning":          esg_result.get("esg_reasoning"),

        "blind_spots":        blind_spots,
        "delta_explanation":  memory_result.get("delta_explanation"),
        "top_memory_matches": memory_result.get("top_matches", []),
        "sector_conviction":  memory_result.get("sector_conviction", {}),

        "forecast":      forecast_result,
        "fix_analysis":  fix_result,
        "portfolio":     portfolio_result,

        "source_type":    "DIGITAL",
        "files_analysed": 1,
        "generated_at":   date.today().isoformat(),
    }

    print(f"  [5/5] Done → business={aggregated['business_score']}  esg={aggregated['esg_composite']}  final={aggregated['final_score']}  {recommendation['verdict'].upper()}")
    return payload


async def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 58)
    print("  ConvictAI — Seed Evaluation Runner")
    print("  Generating real AI scores for 15 pipeline startups")
    print("=" * 58)
    print()

    # Seed the DB (history deals must exist for memory matching)
    print("Initialising database (seeding history deals for memory matching)...")
    await init_db()
    print("Database ready.\n")

    results_summary = []
    failed = []

    async with AsyncSessionLocal() as db:
        for startup in STARTUPS:
            name = startup["startup_name"]
            out_path = CACHE_DIR / f"{name}.json"

            # Skip if already cached and user hasn't forced re-run
            if out_path.exists() and "--force" not in sys.argv:
                print(f"  [CACHED] {name} — already exists (pass --force to regenerate)")
                # Load existing for summary
                try:
                    existing = json.loads(out_path.read_text(encoding="utf-8"))
                    results_summary.append({
                        "name": name,
                        "business": existing.get("business_score", "?"),
                        "esg": existing.get("esg_composite", "?"),
                        "delta": existing.get("conviction_delta", 0),
                        "final": existing.get("final_score", "?"),
                        "verdict": existing.get("verdict", "?"),
                        "status": "cached",
                    })
                except Exception:
                    pass
                continue

            try:
                result = await evaluate_one(startup, db)
                if result:
                    out_path.write_text(
                        json.dumps(result, indent=2, default=str),
                        encoding="utf-8",
                    )
                    results_summary.append({
                        "name": name,
                        "business": result["business_score"],
                        "esg": result["esg_composite"],
                        "delta": result["conviction_delta"],
                        "final": result["final_score"],
                        "verdict": result["verdict"],
                        "status": "generated",
                    })
            except Exception as e:
                print(f"\n  [ERROR] {name}: {e}")
                traceback.print_exc()
                failed.append(name)

    # Summary table
    print(f"\n{'=' * 58}")
    print(f"  SUMMARY — {len(results_summary)}/15 evaluated  ({len(failed)} errors)")
    print(f"{'=' * 58}")
    print(f"  {'Startup':<14} {'Biz':>4} {'ESG':>4} {'Δ':>4} {'Final':>5}  {'Verdict':<12} {'Status'}")
    print(f"  {'-'*56}")
    for r in results_summary:
        delta_str = f"{r['delta']:+d}" if isinstance(r["delta"], (int, float)) else str(r["delta"])
        print(
            f"  {r['name']:<14} {str(r['business']):>4} {str(r['esg']):>4} "
            f"{delta_str:>4} {str(r['final']):>5}  {r['verdict']:<12} {r['status']}"
        )
    if failed:
        print(f"\n  Failed: {', '.join(failed)}")
        print(f"  Re-run with --force to retry failed startups.")

    print(f"\n  Output: backend/seed/cached_evals/  ({len(results_summary)} files)")
    print(f"\n  Next steps:")
    print(f"    1. Review scores above — re-run with --force to regenerate any startup")
    print(f"    2. Delete convictai.db")
    print(f"    3. Start backend — all 15 evals pre-cached automatically on startup")
    print()


if __name__ == "__main__":
    asyncio.run(main())
