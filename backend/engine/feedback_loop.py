import json
import logging
from datetime import date
from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models import DealHistory, EntitySector

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
