import logging
import asyncio
from backend.database import AsyncSessionLocal
from backend.synergy.engine.match_engine import run_full_pipeline

logger = logging.getLogger(__name__)

_synergy_running = False


async def trigger_synergy_run(startup_name: str) -> None:
    """
    Fire-and-forget. Creates a new DB session and runs the full synergy pipeline.
    Called when a deal is marked as added to the active portfolio.
    """
    global _synergy_running
    if _synergy_running:
        logger.info(f"[synergy_trigger] Synergy run already in progress, skipping for {startup_name}")
        return

    _synergy_running = True
    logger.info(f"[synergy_trigger] New portfolio company detected: {startup_name}. Running synergy pipeline...")

    try:
        async with AsyncSessionLocal() as db:
            await run_full_pipeline(db)
        logger.info(f"[synergy_trigger] Synergy pipeline complete after adding {startup_name}")
    except Exception as e:
        logger.error(f"[synergy_trigger] Synergy pipeline failed: {e}")
    finally:
        _synergy_running = False


def schedule_synergy_run(startup_name: str) -> None:
    """
    Called from any router that adds a company to the portfolio.
    Wraps trigger_synergy_run in asyncio.create_task for fire-and-forget.
    """
    asyncio.create_task(trigger_synergy_run(startup_name))
    logger.info(f"[synergy_trigger] Scheduled synergy run for new portfolio member: {startup_name}")
