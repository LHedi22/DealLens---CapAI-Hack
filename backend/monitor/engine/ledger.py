"""
Compliance ledger — single source of truth for all monitor state.

write_transactions       : persist classified transactions (flush only, no commit)
compute_and_write_snapshot : recompute full snapshot from all transactions + commit
run_statement_pipeline   : full pipeline after statement upload (anomalies → alerts → snapshot)
"""

import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.models import (
    MonitorTransaction,
    MonitorAgreement,
    MonitorLedgerSnapshot,
    MonitorAlert,
)
from backend.monitor.agents.compliance_agent import compute_compliance, compute_health_score
from backend.monitor.engine.monitor_feedback import run_monitor_feedback


# ── Helpers ───────────────────────────────────────────────────────────────────

def _months_between(agreement_date_iso: str, snapshot_month: str) -> int:
    """Months from agreement signing (YYYY-MM-DD) to statement month (YYYY-MM), minimum 1."""
    try:
        start = datetime.fromisoformat(agreement_date_iso)
        y, m = int(snapshot_month[:4]), int(snapshot_month[5:7])
        elapsed = (y - start.year) * 12 + (m - start.month) + 1
        return max(1, elapsed)
    except Exception:
        return 1


async def _load_agreement_context(agreement_id: int, db: AsyncSession) -> tuple:
    """Returns (plan_map, duration, agreement_date) for the given agreement."""
    ag_result = await db.execute(
        select(MonitorAgreement).where(MonitorAgreement.id == agreement_id)
    )
    agreement = ag_result.scalar_one_or_none()
    if not agreement:
        raise ValueError(f"Agreement {agreement_id} not found")
    plan_list = json.loads(agreement.categories) if agreement.categories else []
    plan_map = {c["name"]: float(c.get("allocated_tnd") or 0) for c in plan_list}
    duration = agreement.agreement_duration_months or 60
    agreement_date = agreement.agreement_date or datetime.utcnow().strftime("%Y-%m-%d")
    return plan_map, duration, agreement_date


async def _load_all_txs(agreement_id: int, db: AsyncSession) -> list[MonitorTransaction]:
    """Load all transactions for an agreement (autoflush ensures dirty rows are visible)."""
    result = await db.execute(
        select(MonitorTransaction)
        .where(MonitorTransaction.agreement_id == agreement_id)
        .order_by(desc(MonitorTransaction.transaction_date))
    )
    return result.scalars().all()


def _latest_snapshot_month(all_txs: list[MonitorTransaction]) -> str:
    snapshot_month = None
    for tx in all_txs:
        if tx.statement_month and (snapshot_month is None or tx.statement_month > snapshot_month):
            snapshot_month = tx.statement_month
    return snapshot_month or datetime.utcnow().strftime("%Y-%m")


# ── Write ─────────────────────────────────────────────────────────────────────

async def write_transactions(
    agreement_id: int,
    startup_name: str,
    parsed_txs: list[dict],
    statement_month: str | None,
    classified: list[dict],
    db: AsyncSession,
) -> list[MonitorTransaction]:
    """
    Bulk-insert transactions into monitor_transactions.
    Flushes but does NOT commit — caller controls the transaction boundary.
    Append-only: never updates existing rows.
    """
    now = datetime.utcnow().isoformat()
    rows: list[MonitorTransaction] = []

    for tx, cls in zip(parsed_txs, classified):
        is_unclassified = cls.get("classification_status") == "UNCLASSIFIED"
        row = MonitorTransaction(
            agreement_id=agreement_id,
            startup_name=startup_name,
            statement_month=statement_month,
            transaction_date=tx.get("transaction_date"),
            beneficiary=tx.get("beneficiary"),
            amount_tnd=tx.get("amount_tnd"),
            memo=tx.get("memo"),
            ai_category=cls.get("category"),
            ai_confidence=cls.get("confidence"),
            classification_status=cls.get("classification_status"),
            alert_triggered=1 if is_unclassified else 0,
            alert_type="UNCLASSIFIED" if is_unclassified else None,
            uploaded_at=now,
        )
        db.add(row)
        rows.append(row)

    await db.flush()
    return rows


# ── Snapshot ──────────────────────────────────────────────────────────────────

async def compute_and_write_snapshot(
    agreement_id: int,
    startup_name: str,
    db: AsyncSession,
) -> MonitorLedgerSnapshot:
    """
    Recompute compliance snapshot from all transactions for this agreement.
    Writes a new MonitorLedgerSnapshot row and commits the session.
    Called after every statement upload and manual reclassification.
    """
    plan_map, duration, agreement_date = await _load_agreement_context(agreement_id, db)
    all_txs = await _load_all_txs(agreement_id, db)
    snapshot_month = _latest_snapshot_month(all_txs)
    months_elapsed = _months_between(agreement_date, snapshot_month)

    compliance = compute_compliance(all_txs, plan_map, months_elapsed, duration)

    # Active alert count (for health score penalty)
    alert_result = await db.execute(
        select(MonitorAlert).where(MonitorAlert.agreement_id == agreement_id)
    )
    all_alerts = alert_result.scalars().all()
    active_count = sum(1 for a in all_alerts if not a.resolved)
    active_critical_count = sum(1 for a in all_alerts if not a.resolved and a.severity == "CRITICAL")
    total_count = len(all_alerts)

    health_score = compute_health_score(
        compliance["category_totals"],
        compliance["unclassified_tnd"],
        compliance["total_spent"],
        active_count,
    )

    snapshot = MonitorLedgerSnapshot(
        agreement_id=agreement_id,
        startup_name=startup_name,
        snapshot_month=snapshot_month,
        months_elapsed=months_elapsed,
        category_totals=json.dumps(compliance["category_totals"]),
        total_spent_tnd=compliance["total_spent"],
        total_planned_to_date_tnd=compliance["total_planned_to_date"],
        unclassified_tnd=compliance["unclassified_tnd"],
        compliance_health_score=health_score,
        alert_count_active=active_count,
        alert_count_total=total_count,
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(snapshot)

    await db.commit()
    await db.refresh(snapshot)

    await run_monitor_feedback(
        db=db,
        startup_name=startup_name,
        compliance_health_score=health_score,
        critical_alert_count=active_critical_count,
    )
    return snapshot


# ── Full pipeline ─────────────────────────────────────────────────────────────

async def run_statement_pipeline(
    agreement_id: int,
    startup_name: str,
    new_txs: list[MonitorTransaction],
    db: AsyncSession,
) -> MonitorLedgerSnapshot:
    """
    Orchestrate the full post-upload pipeline:
      1. Detect anomalies in new + all transactions
      2. Fire deduped alerts
      3. Compute and persist snapshot

    Imports are deferred to avoid circular dependencies.
    """
    from backend.monitor.agents.anomaly_agent import detect_anomalies
    from backend.monitor.engine.alert_engine import fire_alerts

    plan_map, duration, agreement_date = await _load_agreement_context(agreement_id, db)
    all_txs = await _load_all_txs(agreement_id, db)
    snapshot_month = _latest_snapshot_month(all_txs)
    months_elapsed = _months_between(agreement_date, snapshot_month)

    compliance = compute_compliance(all_txs, plan_map, months_elapsed, duration)

    anomalies = await detect_anomalies(
        new_txs, all_txs, plan_map, compliance, months_elapsed, duration
    )
    await fire_alerts(agreement_id, startup_name, anomalies, db)

    return await compute_and_write_snapshot(agreement_id, startup_name, db)
