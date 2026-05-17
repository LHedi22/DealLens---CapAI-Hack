"""
alert_engine.py — Persist anomalies as MonitorAlert rows with deduplication.

fire_alerts : takes anomaly list → writes new alerts (skips duplicates) → returns count fired
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import MonitorAlert


async def fire_alerts(
    agreement_id: int,
    startup_name: str,
    anomalies: list[dict],
    db: AsyncSession,
) -> int:
    """
    Dedup rules:
      tx-level alerts  → skip if active alert with (alert_type, transaction_id) already exists
      category-level   → skip if active alert with same alert_type already exists for this agreement
    Returns count of newly fired alerts.
    """
    if not anomalies:
        return 0

    existing_result = await db.execute(
        select(MonitorAlert).where(
            MonitorAlert.agreement_id == agreement_id,
            MonitorAlert.resolved == 0,
        )
    )
    existing = existing_result.scalars().all()

    existing_tx_pairs: set[tuple] = set()
    existing_category_types: set[str] = set()
    for a in existing:
        if a.transaction_id is not None:
            existing_tx_pairs.add((a.alert_type, a.transaction_id))
        else:
            existing_category_types.add(a.alert_type)

    now = datetime.utcnow().isoformat()
    fired = 0

    for anomaly in anomalies:
        alert_type = anomaly.get("alert_type")
        tx_id = anomaly.get("transaction_id")

        if tx_id is not None:
            if (alert_type, tx_id) in existing_tx_pairs:
                continue
        else:
            if alert_type in existing_category_types:
                continue

        db.add(MonitorAlert(
            agreement_id=agreement_id,
            startup_name=startup_name,
            transaction_id=tx_id,
            alert_type=alert_type,
            severity=anomaly.get("severity", "WARNING"),
            alert_summary=anomaly.get("alert_summary", ""),
            alert_detail=anomaly.get("alert_detail", ""),
            fired_at=now,
            resolved=0,
        ))
        fired += 1

    if fired:
        await db.flush()

    return fired
