import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models import SynergyPair, SynergyGap

logger = logging.getLogger(__name__)


async def process_decision(
    db: AsyncSession,
    pair_id: int,
    decision: str,          # "approved" | "rejected" | "snoozed"
    reason: str = "",
    snooze_days: int = 30
) -> dict:
    """
    Persist analyst decision on a synergy pair.
    On approve: check if any open gap is now satisfied by this pair.
    On reject: flag for exclusion from default view.
    On snooze: set snooze_until timestamp.
    Returns updated pair data.
    Never raises — all errors are caught and logged.
    """
    try:
        result = await db.execute(
            select(SynergyPair).where(SynergyPair.id == pair_id)
        )
        row = result.fetchone()
        if not row:
            logger.error(f"[synergy_feedback] Pair {pair_id} not found")
            return {}

        pair = row[0]
        now_iso = datetime.utcnow().isoformat()

        if decision == "approved":
            pair.analyst_decision = "approved"
            pair.decision_reason = reason
            pair.decision_at = now_iso

            # Mark any open gap as filled if both pair companies are in affected_companies
            gaps_result = await db.execute(
                select(SynergyGap).where(SynergyGap.status == "open")
            )
            gaps = gaps_result.fetchall()
            for gap_row in gaps:
                gap = gap_row[0]
                affected = json.loads(gap.affected_companies or "[]")
                if pair.company_a in affected and pair.company_b in affected:
                    gap.status = "filled"
                    db.add(gap)
                    logger.info(
                        f"[synergy_feedback] Gap '{gap.gap_label}' marked filled "
                        f"by pair {pair.company_a}↔{pair.company_b}"
                    )

        elif decision == "rejected":
            pair.analyst_decision = "rejected"
            pair.decision_reason = reason
            pair.decision_at = now_iso

        elif decision == "snoozed":
            pair.analyst_decision = "snoozed"
            pair.decision_reason = reason
            pair.decision_at = now_iso
            snooze_until = datetime.utcnow() + timedelta(days=snooze_days)
            pair.snooze_until = snooze_until.isoformat()

        db.add(pair)
        await db.commit()

        logger.info(f"[synergy_feedback] Pair {pair_id} decision: {decision}")
        return {
            "pair_id": pair_id,
            "decision": decision,
            "company_a": pair.company_a,
            "company_b": pair.company_b,
            "decision_at": now_iso,
        }

    except Exception as e:
        logger.error(f"[synergy_feedback] Error processing decision for pair {pair_id}: {e}")
        await db.rollback()
        return {}


async def resurface_snoozed_pairs(db: AsyncSession) -> int:
    """
    Called on Synergy page load. Re-opens any snoozed pairs whose snooze_until has passed.
    Returns count of re-surfaced pairs.
    """
    try:
        now_iso = datetime.utcnow().isoformat()
        result = await db.execute(
            select(SynergyPair).where(SynergyPair.analyst_decision == "snoozed")
        )
        rows = result.fetchall()
        count = 0
        for row in rows:
            pair = row[0]
            if pair.snooze_until and pair.snooze_until <= now_iso:
                pair.analyst_decision = None
                pair.snooze_until = None
                db.add(pair)
                count += 1
        if count > 0:
            await db.commit()
            logger.info(f"[synergy_feedback] Re-surfaced {count} snoozed pairs")
        return count
    except Exception as e:
        logger.error(f"[synergy_feedback] Error resurfacing snoozed pairs: {e}")
        return 0
