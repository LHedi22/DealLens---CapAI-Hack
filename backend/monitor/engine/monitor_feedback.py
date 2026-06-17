import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.models import DealHistory, EntitySector, PortfolioCompany

logger = logging.getLogger(__name__)

async def run_monitor_feedback(
    db: AsyncSession,
    startup_name: str,
    compliance_health_score: int,
    critical_alert_count: int
) -> None:
    """
    After every ledger update, sync the compliance health score back to:
    1. deal_history.compliance_health_score — shows in Dashboard compliance column
    2. portfolio_companies.compliance_health_score — used by synergy module
    3. entity_sectors — a startup with health score < 50 signals a negative outcome
       for the sector (reduces sector conviction signal for future pre-investment evals)

    Never raises — all errors are caught and logged.
    """
    try:
        # 1. Update deal_history
        await db.execute(
            update(DealHistory)
            .where(DealHistory.startup_name == startup_name)
            .values(compliance_health_score=compliance_health_score)
        )

        # 2. Update portfolio_companies
        await db.execute(
            update(PortfolioCompany)
            .where(PortfolioCompany.company_name == startup_name)
            .values(compliance_health_score=compliance_health_score)
        )

        # 3. Update sector entity if health is critically low
        if compliance_health_score < 50:
            # Get the sector for this startup
            result = await db.execute(
                select(DealHistory.sector).where(DealHistory.startup_name == startup_name)
            )
            row = result.fetchone()
            if row and row.sector:
                sector = row.sector
                # Fetch current sector stats
                sector_result = await db.execute(
                    select(EntitySector).where(EntitySector.sector_name == sector)
                )
                sector_row = sector_result.fetchone()
                if sector_row:
                    entity = sector_row[0]
                    # Decrease win_rate slightly to reflect compliance failure signal
                    # Floor at 0.0
                    new_win_rate = max(0.0, (entity.win_rate or 0.5) - 0.02)
                    entity.win_rate = new_win_rate
                    entity.trend_direction = "declining"
                    db.add(entity)

        await db.commit()
        logger.info(f"[monitor_feedback] Synced health score {compliance_health_score} for {startup_name}")

    except Exception as e:
        logger.error(f"[monitor_feedback] Failed for {startup_name}: {e}")
        await db.rollback()
