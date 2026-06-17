import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import MandateConfig, PortfolioCompany, DealHistory
from backend.agents.business import run_business_scoring
from backend.agents.esg import run_esg_scoring
from backend.agents.memory import run_memory_matching
from backend.agents.forecasting import run_forecasting
from backend.agents.fix_analysis import run_fix_analysis
from backend.agents.portfolio import run_portfolio
from backend.engine.aggregator import aggregate_scores
from backend.engine.recommendation import generate_verdict
from backend.engine.feedback_loop import write_deal_record
from backend.schemas import OCRConfirmRequest

router = APIRouter()

_ROI_DISCLAIMER = "AI-reasoned estimates. Not a financial model. Use for directional comparison only."

_DEFAULT_BUSINESS = {
    "composite_score": 50,
    "team_score": 50, "market_score": 50, "revenue_score": 50,
    "traction_score": 50, "moat_score": 50, "scalability_score": 50,
    "top_strengths": ["Analysis unavailable — Ollama offline"],
    "top_risks": ["Analysis unavailable — Ollama offline"],
}

_DEFAULT_ESG = {
    "composite": 50, "e_score": 50, "s_score": 50, "g_score": 50,
    "tier": "Adequate", "red_flags_triggered": [], "red_flag_details": [],
    "verifiability": "Low", "most_critical_flag": None,
    "esg_reasoning": "ESG analysis unavailable.",
}


def _default_forecast():
    return {
        "revenue_trajectory": None,
        "success_probability": {
            "probability_pct": 0, "sector_base_rate_pct": 0,
            "adjustments": [], "confidence": "LOW",
            "milestone": "Series A", "horizon_months": 24,
        },
        "roi_estimate": {
            "expected_multiple": None, "probability_weighted_multiple": None,
            "comparables_used": [], "confidence": "LOW",
            "note": "Forecast unavailable.", "disclaimer": _ROI_DISCLAIMER,
        },
        "sector_trend": {"signal": "NEUTRAL", "trend_direction": "stable", "fund_win_rate_pct": 0},
        "disclaimer": _ROI_DISCLAIMER,
    }


def _default_fix():
    return {
        "problems_found": 0, "fixable_problems": [], "structural_problems": [],
        "top_priority_actions": [], "current_score": 0, "conditional_score": 0,
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
        "fit_verdict": "neutral_fit",
        "fit_summary": "Portfolio analysis unavailable.",
        "best_pair": [], "optimizer_reason": "",
    }


@router.get("/ocr-mock")
async def get_ocr_mock():
    try:
        with open("backend/ocr_mock/scanned_result.json", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="OCR mock data not found")


@router.post("/ocr-confirm")
async def ocr_confirm(
    request: OCRConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    extracted = request.confirmed_document
    data_completeness = int(extracted.get("data_completeness", 68))
    confidence_level = extracted.get("confidence_level", "MEDIUM")
    blind_spots = extracted.get("blind_spots", [])

    # Use JSON string of document as the text corpus for ESG keyword scanning
    document_text = json.dumps(extracted)

    # Step 1: Business + ESG in parallel (skip extraction — already confirmed)
    business_result, esg_result = await asyncio.gather(
        run_business_scoring(extracted),
        run_esg_scoring(extracted, document_text, request.sector),
        return_exceptions=True,
    )
    if isinstance(business_result, Exception):
        business_result = _DEFAULT_BUSINESS
    if isinstance(esg_result, Exception):
        esg_result = _DEFAULT_ESG

    # Step 2: Memory matching
    memory_result = await run_memory_matching(
        incoming={
            "sector":              request.sector,
            "stage":               request.stage,
            "geography":           request.geography,
            "business_model_type": request.business_model_type,
            "esg_composite":       esg_result.get("composite", 50),
            "extracted":           extracted,
        },
        db=db,
    )

    # Step 3: Mandate + aggregate + verdict
    mandate_record = await db.scalar(select(MandateConfig).where(MandateConfig.id == 1))
    mandate = None
    if mandate_record:
        mandate = {
            "sector_focus":      json.loads(mandate_record.sector_focus or "[]"),
            "stage_preference":  json.loads(mandate_record.stage_preference or "[]"),
            "min_esg_threshold": mandate_record.min_esg_threshold,
            "ticket_size_max":   mandate_record.ticket_size_max,
            "esg_priority_axis": mandate_record.esg_priority_axis,
        }

    aggregated = aggregate_scores(
        business=business_result,
        esg=esg_result,
        conviction_delta=memory_result.get("conviction_delta", 0),
        mandate=mandate,
        sector=request.sector,
        stage=request.stage,
        funding_asked=request.funding_asked,
    )
    recommendation = generate_verdict(aggregated)

    # Pre-fetch portfolio data
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
            DealHistory.is_pipeline == True,   # noqa: E712
            DealHistory.is_seed_data == False,  # noqa: E712
            DealHistory.decision.in_(["pursue", "watch"]),
        )
    )
    pipeline_candidates = [
        {
            "startup_name": d.startup_name,
            "sector":       d.sector,
            "stage":        d.stage,
            "decision":     d.decision,
        }
        for d in pipeline_rows.scalars().all()
    ]

    new_startup = {
        "sector":              request.sector,
        "stage":               request.stage,
        "geography":           request.geography,
        "business_model_type": request.business_model_type,
        "esg_composite":       esg_result.get("composite", 50),
    }

    # Step 4: Forecast + Fix + Portfolio in parallel
    forecast_result, fix_result, portfolio_result = await asyncio.gather(
        run_forecasting(
            extracted=extracted,
            business_result=business_result,
            esg_result=esg_result,
            sector_conviction=memory_result.get("sector_conviction", {}),
            sector=request.sector,
            stage=request.stage,
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
            new_startup=new_startup,
            portfolio_companies=portfolio_companies,
            pipeline_candidates=pipeline_candidates,
        ),
        return_exceptions=True,
    )
    if isinstance(forecast_result, Exception):
        forecast_result = _default_forecast()
    if isinstance(fix_result, Exception):
        fix_result = _default_fix()
    if isinstance(portfolio_result, Exception):
        portfolio_result = _default_portfolio()

    startup_name = extracted.get("startup_name", "EduTech Tunisia")

    # Step 5: Persist (fire-and-forget)
    asyncio.create_task(
        write_deal_record({
            "startup_name":        startup_name,
            "sector":              request.sector,
            "stage":               request.stage,
            "geography":           request.geography,
            "business_model_type": request.business_model_type,
            "business_score":      aggregated["business_score"],
            "esg_composite":       aggregated["esg_composite"],
            "esg_e":               esg_result.get("e_score"),
            "esg_s":               esg_result.get("s_score"),
            "esg_g":               esg_result.get("g_score"),
            "data_completeness":   data_completeness,
            "confidence_level":    confidence_level,
            "conviction_delta":    aggregated["conviction_delta"],
            "final_score":         aggregated["final_score"],
            "verdict":             recommendation["verdict"],
            "verdict_reason":      recommendation["verdict_reason"],
            "red_flags_triggered": esg_result.get("red_flags_triggered", []),
            "blind_spots":         blind_spots,
            "fix_verdict":         fix_result.get("fix_verdict"),
        })
    )

    mandate_breaches = recommendation.get("mandate_breaches", [])

    return {
        "startup_name": startup_name,
        "sector":       request.sector,
        "stage":        request.stage,
        "geography":    request.geography,

        "final_score":        aggregated["final_score"],
        "business_score":     aggregated["business_score"],
        "adjusted_business":  aggregated["adjusted_business"],
        "esg_composite":      aggregated["esg_composite"],
        "conviction_delta":   aggregated["conviction_delta"],
        "confidence_level":   confidence_level,
        "data_completeness":  data_completeness,

        "mandate_breach":   aggregated.get("force_pass", False),
        "mandate_flags":    mandate_breaches,
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

        "forecast":     forecast_result,
        "fix_analysis": fix_result,
        "portfolio":    portfolio_result,

        "source_type":    "PHYSICAL_SCAN",
        "ocr_confidence": 0.71,
        "files_analysed": 1,
    }
