import json
import logging
from datetime import date, datetime
from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models import (
    DealHistory, EntitySector,
    MonitorAgreement, MonitorLedgerSnapshot,
    SynergyProfile,
)

logger = logging.getLogger(__name__)


async def write_deal_record(evaluation_result: dict) -> None:
    """
    Persist a completed evaluation to deal_history and update entity_sectors.
    Creates its own DB session — safe to call with asyncio.create_task.
    """
    async with AsyncSessionLocal() as db:
        try:
            deal = DealHistory(
                startup_name=evaluation_result["startup_name"],
                sector=evaluation_result["sector"],
                stage=evaluation_result["stage"],
                geography=evaluation_result.get("geography"),
                business_model_type=evaluation_result.get("business_model_type"),
                date_evaluated=date.today().isoformat(),
                business_score=evaluation_result.get("business_score"),
                esg_composite=evaluation_result.get("esg_composite"),
                esg_e=evaluation_result.get("esg_e"),
                esg_s=evaluation_result.get("esg_s"),
                esg_g=evaluation_result.get("esg_g"),
                data_completeness=evaluation_result.get("data_completeness"),
                confidence_level=evaluation_result.get("confidence_level"),
                conviction_delta=evaluation_result.get("conviction_delta", 0),
                final_score=evaluation_result.get("final_score"),
                decision=evaluation_result.get("verdict"),
                decision_reason=evaluation_result.get("verdict_reason"),
                red_flags=json.dumps(evaluation_result.get("red_flags_triggered", [])),
                blind_spots=json.dumps(evaluation_result.get("blind_spots", [])),
                fix_verdict=None,
                outcome=None,
                outcome_notes=None,
                is_seed_data=False,
                is_pipeline=True,
            )
            db.add(deal)
            await db.flush()

            await _update_sector_entity(
                sector=evaluation_result["sector"],
                decision=evaluation_result.get("verdict", ""),
                business_score=evaluation_result.get("business_score") or 0,
                esg_composite=evaluation_result.get("esg_composite") or 0,
                db=db,
            )

            await db.commit()

            if evaluation_result.get("verdict") in ("pursue", "watch"):
                await _enroll_in_monitor(db, deal)
                await _create_synergy_profile(
                    db, deal,
                    evaluation_result.get("document_text", ""),
                )

            logger.info(f"Deal saved: {evaluation_result['startup_name']}")

        except Exception as e:
            logger.error(f"Feedback loop write failed: {e}")
            await db.rollback()


async def _update_sector_entity(
    sector: str,
    decision: str,
    business_score: int,
    esg_composite: int,
    db,
) -> None:
    result = await db.execute(
        select(EntitySector).where(EntitySector.sector_name == sector)
    )
    entity = result.scalar_one_or_none()

    if not entity:
        entity = EntitySector(
            sector_name=sector,
            total_evaluations=0,
            total_pursued=0,
            win_rate=0.0,
            avg_business_score=0.0,
            avg_esg_score=0.0,
            trend_direction="stable",
        )
        db.add(entity)

    prev_total = entity.total_evaluations
    entity.total_evaluations += 1

    if decision in ("pursue", "watch"):
        entity.total_pursued += 1

    n = entity.total_evaluations
    entity.win_rate = entity.total_pursued / n if n > 0 else 0.0
    entity.avg_business_score = (entity.avg_business_score * prev_total + business_score) / n
    entity.avg_esg_score = (entity.avg_esg_score * prev_total + esg_composite) / n

    if entity.win_rate >= 0.60:
        entity.trend_direction = "improving"
    elif entity.win_rate <= 0.35:
        entity.trend_direction = "declining"
    else:
        entity.trend_direction = "stable"


async def _enroll_in_monitor(db, deal: DealHistory) -> None:
    """Create a minimal MonitorAgreement + initial snapshot seeded from ESG composite."""
    try:
        exists = await db.scalar(
            select(MonitorAgreement).where(
                MonitorAgreement.startup_name == deal.startup_name
            )
        )
        if exists:
            return

        agreement = MonitorAgreement(
            startup_name=deal.startup_name,
            deal_history_id=deal.id,
            agreement_date=deal.date_evaluated,
            agreement_duration_months=60,
            total_committed_tnd=0.0,
            categories=json.dumps([]),
            time_milestones=json.dumps([]),
            source_type="AUTO",
            is_seed_data=False,
        )
        db.add(agreement)
        await db.flush()

        health = deal.esg_composite or 50
        db.add(MonitorLedgerSnapshot(
            agreement_id=agreement.id,
            startup_name=deal.startup_name,
            snapshot_month=deal.date_evaluated[:7],
            months_elapsed=0,
            category_totals=json.dumps({}),
            total_spent_tnd=0.0,
            total_planned_to_date_tnd=0.0,
            unclassified_tnd=0.0,
            compliance_health_score=health,
            alert_count_active=0,
            alert_count_total=0,
        ))
        deal.compliance_health_score = health
        await db.commit()
    except Exception as e:
        logger.error(f"Monitor enrollment failed for {deal.startup_name}: {e}")
        await db.rollback()


async def _create_synergy_profile(db, deal: DealHistory, document_text: str) -> None:
    """Extract a SynergyProfile via Ollama and score all new pairs."""
    try:
        exists = await db.scalar(
            select(SynergyProfile).where(
                SynergyProfile.company_name == deal.startup_name
            )
        )
        if exists:
            return

        from backend.synergy.agents.profile_extractor import extract_synergy_profile
        profile_data = await extract_synergy_profile(
            document_text=document_text,
            company_name=deal.startup_name,
            sector=deal.sector,
            stage=deal.stage,
            geography=deal.geography,
            deal_history_id=deal.id,
        )
        profile_data["extraction_source"] = "live_evaluation"
        db.add(SynergyProfile(**profile_data))
        await db.commit()

        from backend.synergy.engine.match_engine import run_full_pipeline
        await run_full_pipeline(db)
    except Exception as e:
        logger.error(f"Synergy profile creation failed for {deal.startup_name}: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
