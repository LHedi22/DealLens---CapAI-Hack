ESG_TIER_SCORE = {
    "Strong": 85.0,
    "Adequate": 65.0,
    "Weak": 45.0,
    "Critical Risk": 20.0,
}

_SAFE_DEFAULT = {
    "sector_distribution": {},
    "concentration_warning": False,
    "overweight_sectors": [],
    "stage_distribution": {},
    "stage_balance_ok": True,
    "geo_distribution": {},
    "geo_warning": False,
    "portfolio_esg_before": 0.0,
    "portfolio_esg_after": 0.0,
    "esg_shift": 0.0,
    "esg_degradation_flag": False,
    "correlated_companies": [],
    "correlation_risk": False,
    "fit_verdict": "neutral_fit",
    "fit_summary": "Portfolio data unavailable — no existing companies in fund.",
    "best_pair": [],
    "optimizer_reason": "Not enough pipeline candidates",
}


async def run_portfolio(
    new_startup: dict,
    portfolio_companies: list,
    pipeline_candidates: list,
) -> dict:
    from backend.debug_state import step_started, step_completed, step_failed
    step_started("portfolio")
    try:
        result = _compute_portfolio(new_startup, portfolio_companies, pipeline_candidates)
        step_completed("portfolio", f"Fit: {result.get('fit_verdict')} | Concentration warning: {result.get('concentration_warning')}")
        return result
    except Exception as e:
        step_failed("portfolio", type(e).__name__, str(e))
        return dict(_SAFE_DEFAULT)


def _compute_portfolio(new_startup: dict, portfolio: list, pipeline: list) -> dict:
    sector    = new_startup.get("sector", "Unknown")
    stage     = new_startup.get("stage", "Unknown")
    geography = new_startup.get("geography", "Unknown")
    biz_model = new_startup.get("business_model_type", "")
    new_esg   = float(new_startup.get("esg_composite", 65))

    # ── 1. SECTOR CONCENTRATION ─────────────────────────────────────────
    sector_counts: dict[str, int] = {}
    for co in portfolio:
        s = co.get("sector", "Unknown")
        sector_counts[s] = sector_counts.get(s, 0) + 1

    # After adding new startup
    combined_sectors = dict(sector_counts)
    combined_sectors[sector] = combined_sectors.get(sector, 0) + 1
    total_after = len(portfolio) + 1

    sector_distribution = {
        s: round(c / total_after * 100, 1)
        for s, c in combined_sectors.items()
    }

    overweight_sectors = [s for s, pct in sector_distribution.items() if pct > 35]
    concentration_warning = len(overweight_sectors) > 0

    # ── 2. STAGE BALANCE ────────────────────────────────────────────────
    stage_counts: dict[str, int] = {}
    for co in portfolio:
        st = co.get("stage", "Unknown")
        stage_counts[st] = stage_counts.get(st, 0) + 1
    stage_counts[stage] = stage_counts.get(stage, 0) + 1

    stage_distribution = dict(stage_counts)
    total_stages = sum(stage_counts.values())
    stage_balance_ok = all(
        v / total_stages <= 0.80 for v in stage_counts.values()
    ) if total_stages else True

    # ── 3. GEOGRAPHIC CONCENTRATION ─────────────────────────────────────
    geo_counts: dict[str, int] = {}
    for co in portfolio:
        g = co.get("geography") or "Unknown"
        geo_counts[g] = geo_counts.get(g, 0) + 1
    if geography:
        geo_counts[geography] = geo_counts.get(geography, 0) + 1

    total_geo = sum(geo_counts.values())
    geo_distribution = {
        g: round(c / total_geo * 100, 1) for g, c in geo_counts.items()
    } if total_geo else {}
    geo_warning = any(pct > 60 for pct in geo_distribution.values())

    # ── 4. ESG PORTFOLIO SCORE ──────────────────────────────────────────
    if portfolio:
        esg_scores = [ESG_TIER_SCORE.get(co.get("esg_tier", "Adequate"), 65.0) for co in portfolio]
        portfolio_esg_before = round(sum(esg_scores) / len(esg_scores), 1)
        portfolio_esg_after = round(
            (sum(esg_scores) + new_esg) / (len(esg_scores) + 1), 1
        )
    else:
        portfolio_esg_before = 0.0
        portfolio_esg_after = round(new_esg, 1)

    esg_shift = round(portfolio_esg_after - portfolio_esg_before, 1)
    esg_degradation_flag = esg_shift < 0 and portfolio_esg_after < 60

    # ── 5. RISK CORRELATION ─────────────────────────────────────────────
    correlated = [
        co["company_name"]
        for co in portfolio
        if co.get("sector") == sector and co.get("business_model_type") == biz_model and biz_model
    ]
    correlation_risk = len(correlated) >= 2

    # ── 6. FIT VERDICT ──────────────────────────────────────────────────
    warning_count = sum([
        concentration_warning,
        not stage_balance_ok,
        geo_warning,
        esg_degradation_flag,
        correlation_risk,
    ])

    if concentration_warning and correlation_risk:
        fit_verdict = "warning"
        fit_summary = (
            "This startup creates sector concentration AND correlated model risk — "
            "strong portfolio warning before committing."
        )
    elif warning_count == 0:
        fit_verdict = "strong_fit"
        fit_summary = (
            "This startup is a strong portfolio addition — no concentration, "
            "balance, or ESG concerns detected."
        )
    elif warning_count == 1:
        fit_verdict = "neutral_fit"
        fit_summary = (
            "Acceptable fit with one portfolio consideration to review before committing."
        )
    else:
        fit_verdict = "weak_fit"
        fit_summary = (
            f"This startup triggers {warning_count} portfolio warnings — "
            "review concentration and risk before committing."
        )

    # ── 7. PIPELINE OPTIMIZER ───────────────────────────────────────────
    best_pair, optimizer_reason = _pipeline_optimizer(
        combined_sectors, total_after, pipeline
    )

    return {
        "sector_distribution": sector_distribution,
        "concentration_warning": concentration_warning,
        "overweight_sectors": overweight_sectors,
        "stage_distribution": stage_distribution,
        "stage_balance_ok": stage_balance_ok,
        "geo_distribution": geo_distribution,
        "geo_warning": geo_warning,
        "portfolio_esg_before": portfolio_esg_before,
        "portfolio_esg_after": portfolio_esg_after,
        "esg_shift": esg_shift,
        "esg_degradation_flag": esg_degradation_flag,
        "correlated_companies": correlated,
        "correlation_risk": correlation_risk,
        "fit_verdict": fit_verdict,
        "fit_summary": fit_summary,
        "best_pair": best_pair,
        "optimizer_reason": optimizer_reason,
    }


def _pipeline_optimizer(
    base_sector_counts: dict[str, int],
    base_total: int,
    pipeline: list,
) -> tuple[list, str]:
    if len(pipeline) < 2:
        return [], "Not enough pipeline candidates"

    best_pair: list[str] = []
    best_max_pct = 101.0

    for i in range(len(pipeline)):
        for j in range(i + 1, len(pipeline)):
            a, b = pipeline[i], pipeline[j]
            test = dict(base_sector_counts)
            test[a["sector"]] = test.get(a["sector"], 0) + 1
            test[b["sector"]] = test.get(b["sector"], 0) + 1
            total = base_total + 2
            max_pct = max(v / total * 100 for v in test.values())
            if max_pct < best_max_pct:
                best_max_pct = max_pct
                best_pair = [a["startup_name"], b["startup_name"]]

    reason = (
        f"This pair minimises sector concentration — "
        f"maximum exposure after both additions: {int(best_max_pct)}%"
    )
    return best_pair, reason
