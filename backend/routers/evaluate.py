import asyncio
import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import MandateConfig, PortfolioCompany, DealHistory
from backend.parsers import merge_documents
from backend.agents.extraction import run_extraction
from backend.agents.business import run_business_scoring
from backend.agents.esg import run_esg_scoring
from backend.agents.memory import run_memory_matching
from backend.agents.forecasting import run_forecasting
from backend.agents.fix_analysis import run_fix_analysis
from backend.agents.portfolio import run_portfolio
from backend.engine.aggregator import aggregate_scores
from backend.engine.recommendation import generate_verdict
from backend.engine.feedback_loop import write_deal_record
from backend.schemas import EvaluationRequest
from backend.agents.ollama_client import check_ollama_available
from backend.models import CachedEvaluation
from backend.debug_state import (
    emit_log, reset_pipeline, finalize_pipeline,
    step_started, step_completed,
)

router = APIRouter()

_DEFAULT_BUSINESS = {
    "composite_score": 50,
    "team_score": 50, "market_score": 50, "revenue_score": 50,
    "traction_score": 50, "moat_score": 50, "scalability_score": 50,
    "top_strengths": ["Analysis unavailable — Ollama error"],
    "top_risks": ["Analysis unavailable — Ollama error"],
}

_DEFAULT_ESG = {
    "composite": 50, "e_score": 50, "s_score": 50, "g_score": 50,
    "tier": "Adequate", "red_flags_triggered": [], "red_flag_details": [],
    "verifiability": "Low", "most_critical_flag": None,
    "esg_reasoning": "ESG analysis unavailable.",
}

_ROI_DISCLAIMER = "AI-reasoned estimates. Not a financial model. Use for directional comparison only."


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


def _esg_tier(score):
    if score is None:
        return "Adequate"
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Adequate"
    if score >= 40:
        return "Weak"
    return "Critical Risk"


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


@router.post("/evaluate")
async def evaluate_startup(
    request: EvaluationRequest,
    db: AsyncSession = Depends(get_db),
):
    if not await check_ollama_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama is not running or the 'mistral' model is not pulled. "
                "Run: ollama serve  then: ollama pull mistral"
            ),
        )

    reset_pipeline(request.startup_name)
    emit_log("INFO", "fastapi", "POST /api/evaluate received", {
        "startup_name": request.startup_name,
        "startup_id": request.startup_id,
    })

    upload_dir = f"uploads/{request.startup_id}"
    if not os.path.exists(upload_dir):
        raise HTTPException(
            status_code=404,
            detail=f"No uploaded files found for startup_id: {request.startup_id}",
        )

    file_paths = [
        os.path.join(upload_dir, f)
        for f in os.listdir(upload_dir)
        if os.path.isfile(os.path.join(upload_dir, f))
    ]
    if not file_paths:
        raise HTTPException(status_code=400, detail="No files found in upload directory.")

    document_text = merge_documents(file_paths)
    if not document_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the uploaded files. Please upload a readable PDF, DOCX, or XLSX file.",
        )

    # Step 1: Extraction
    try:
        extraction_result = await run_extraction(document_text)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    extracted         = extraction_result["extracted"]
    data_completeness = extraction_result["data_completeness"]
    confidence_level  = extraction_result["confidence_level"]
    blind_spots       = extraction_result["blind_spots"]

    # Step 2: Business + ESG in parallel
    business_result, esg_result = await asyncio.gather(
        run_business_scoring(extracted),
        run_esg_scoring(extracted, document_text, request.sector),
        return_exceptions=True,
    )
    if isinstance(business_result, Exception):
        business_result = _DEFAULT_BUSINESS
    if isinstance(esg_result, Exception):
        esg_result = _DEFAULT_ESG

    # Step 3: Memory matching
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

    # Step 4: Load mandate + aggregate + recommendation
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

    step_started("aggregator")
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
    step_completed("aggregator", f"Final: {aggregated['final_score']} | Verdict: {recommendation['verdict']}")
    emit_log("INFO", "aggregator", "Scores aggregated", {
        "business_score": aggregated["business_score"],
        "esg_composite": aggregated["esg_composite"],
        "conviction_delta": aggregated["conviction_delta"],
        "final_score": aggregated["final_score"],
        "mandate_breach": aggregated.get("force_pass", False),
    })

    # Pre-fetch portfolio data (before Step 5 gather — no DB calls inside agents)
    portfolio_rows = await db.execute(select(PortfolioCompany))
    portfolio_companies = [
        {
            "company_name":      co.company_name,
            "sector":            co.sector,
            "stage":             co.stage,
            "geography":         co.geography,
            "business_model_type": co.business_model_type,
            "esg_tier":          co.esg_tier,
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

    new_startup_for_portfolio = {
        "sector":              request.sector,
        "stage":               request.stage,
        "geography":           request.geography,
        "business_model_type": request.business_model_type,
        "esg_composite":       esg_result.get("composite", 50),
    }

    # Step 5: Forecasting + Fix Analysis + Portfolio in parallel
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
            new_startup=new_startup_for_portfolio,
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

    # Step 6: Persist deal record (fire-and-forget)
    asyncio.create_task(
        write_deal_record({
            "startup_name":        request.startup_name,
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
            "document_text":       document_text,
        })
    )

    mandate_breaches = recommendation.get("mandate_breaches", [])

    response_payload = {
        "startup_name": request.startup_name,
        "sector":       request.sector,
        "stage":        request.stage,
        "geography":    request.geography,

        # Scores
        "final_score":        aggregated["final_score"],
        "business_score":     aggregated["business_score"],
        "adjusted_business":  aggregated["adjusted_business"],
        "esg_composite":      aggregated["esg_composite"],
        "conviction_delta":   aggregated["conviction_delta"],
        "confidence_level":   confidence_level,
        "data_completeness":  data_completeness,

        # Mandate
        "mandate_breach":   aggregated.get("force_pass", False),
        "mandate_flags":    mandate_breaches,

        # Verdict
        "verdict":          recommendation["verdict"],
        "verdict_label":    recommendation["verdict_label"],
        "verdict_reason":   recommendation["verdict_reason"],
        "mandate_breaches": mandate_breaches,

        # Business breakdown
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

        # ESG
        "esg_e":                  esg_result.get("e_score"),
        "esg_s":                  esg_result.get("s_score"),
        "esg_g":                  esg_result.get("g_score"),
        "esg_tier":               esg_result.get("tier"),
        "esg_verifiability":      esg_result.get("verifiability"),
        "red_flags_triggered":    esg_result.get("red_flags_triggered", []),
        "red_flag_details":       esg_result.get("red_flag_details", []),
        "most_critical_esg_flag": esg_result.get("most_critical_flag"),
        "esg_reasoning":          esg_result.get("esg_reasoning"),

        # Blind spots
        "blind_spots": blind_spots,

        # Memory
        "delta_explanation":  memory_result.get("delta_explanation"),
        "top_memory_matches": memory_result.get("top_matches", []),
        "sector_conviction":  memory_result.get("sector_conviction", {}),

        # Forecast
        "forecast": forecast_result,

        # Fix Analysis
        "fix_analysis": fix_result,

        # Portfolio
        "portfolio": portfolio_result,

        "source_type":    "DIGITAL",
        "files_analysed": len(file_paths),
    }

    finalize_pipeline(response_payload)
    emit_log("INFO", "fastapi", f"Evaluation complete for {request.startup_name}", {
        "final_score": aggregated["final_score"],
        "verdict": recommendation["verdict"],
    })

    from datetime import date
    await db.merge(CachedEvaluation(
        startup_name=request.startup_name,
        evaluation_json=json.dumps(response_payload),
        cached_at=date.today().isoformat(),
    ))
    await db.commit()

    return response_payload


@router.get("/evaluate/cached/{startup_name}")
async def get_cached_evaluation(
    startup_name: str,
    db: AsyncSession = Depends(get_db),
):
    record = await db.scalar(
        select(CachedEvaluation).where(CachedEvaluation.startup_name == startup_name)
    )
    if record:
        return json.loads(record.evaluation_json)

    # Fallback: reconstruct a partial response from deal_history
    deal = await db.scalar(
        select(DealHistory).where(
            DealHistory.startup_name == startup_name,
            DealHistory.is_pipeline == True,
        )
    )
    if not deal:
        raise HTTPException(status_code=404, detail=f"No cached evaluation for '{startup_name}'")

    red_flags = json.loads(deal.red_flags) if deal.red_flags else []
    blind_spots = json.loads(deal.blind_spots) if deal.blind_spots else []

    return {
        "startup_name": deal.startup_name,
        "sector": deal.sector,
        "stage": deal.stage,
        "business_score": deal.business_score,
        "esg_composite": deal.esg_composite,
        "esg_e": deal.esg_e,
        "esg_s": deal.esg_s,
        "esg_g": deal.esg_g,
        "esg_tier": _esg_tier(deal.esg_composite),
        "esg_verifiability": "Medium",
        "final_score": deal.final_score,
        "conviction_delta": deal.conviction_delta or 0,
        "data_completeness": deal.data_completeness or 70,
        "confidence_level": deal.confidence_level or "MEDIUM",
        "verdict": deal.decision.upper() if deal.decision else "WATCH",
        "verdict_label": (deal.decision or "watch").replace("_", " ").upper(),
        "decision_reason": deal.decision_reason or "",
        "red_flags_triggered": red_flags,
        "red_flag_details": [],
        "most_critical_esg_flag": red_flags[0] if red_flags else None,
        "blind_spots": blind_spots,
        "dimension_scores": {"team": None, "market": None, "revenue": None,
                              "traction": None, "moat": None, "scalability": None},
        "top_strengths": [],
        "top_risks": [],
        "delta_explanation": None,
        "top_memory_matches": [],
        "sector_conviction": {},
        "forecast": _default_forecast(),
        "fix_analysis": _default_fix(),
        "portfolio": _default_portfolio(),
        "mandate_breach": False,
        "mandate_flags": [],
        "source_type": "HISTORY",
        "files_analysed": 0,
        "is_partial": True,
    }
