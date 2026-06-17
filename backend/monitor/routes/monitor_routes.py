from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, and_
from pydantic import BaseModel
import json
import os
from datetime import datetime
from typing import Optional

from backend.database import get_db
from backend.models import MonitorAgreement, MonitorLedgerSnapshot, MonitorAlert, MonitorTransaction
from backend.monitor.agents.agreement_parser import parse_agreement
from backend.monitor.agents.statement_parser import parse_statement
from backend.monitor.agents.category_agent import classify_batch
from backend.monitor.engine.ledger import write_transactions, compute_and_write_snapshot, run_statement_pipeline

_MOCK_PATH = os.path.join(os.path.dirname(__file__), "../seed/bank_statement_mock.json")

router = APIRouter(prefix="/monitor")


class ReclassifyRequest(BaseModel):
    category: str


class ResolveRequest(BaseModel):
    note: str = ""


class OcrConfirmRequest(BaseModel):
    startup_name: str
    statement_month: str
    confirmed_transactions: list[dict]


class NoStatementRequest(BaseModel):
    startup_name: str
    month: str


# ── Agreement endpoints ───────────────────────────────────────────────────────

@router.post("/agreement/upload")
async def upload_agreement(
    startup_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    parsed = await parse_agreement(content, file.filename or "upload.pdf")

    agreement = MonitorAgreement(
        startup_name=startup_name,
        agreement_date=parsed.get("agreement_date"),
        agreement_duration_months=parsed.get("agreement_duration_months", 60),
        total_committed_tnd=parsed.get("total_committed_tnd"),
        categories=json.dumps(parsed.get("categories", [])),
        time_milestones=json.dumps(parsed.get("time_milestones", [])),
        uploaded_at=datetime.utcnow().isoformat(),
        source_type="DIGITAL",
        is_seed_data=False,
    )
    db.add(agreement)
    await db.commit()
    await db.refresh(agreement)

    return {
        "id": agreement.id,
        "startup_name": agreement.startup_name,
        "agreement_date": agreement.agreement_date,
        "total_committed_tnd": agreement.total_committed_tnd,
        "categories": parsed.get("categories", []),
        "message": "Agreement uploaded and parsed successfully.",
    }


@router.get("/agreement/{startup_name}")
async def get_agreement(startup_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonitorAgreement)
        .where(MonitorAgreement.startup_name == startup_name)
        .order_by(desc(MonitorAgreement.id))
    )
    agreement = result.scalar_one_or_none()
    if not agreement:
        raise HTTPException(status_code=404, detail="No agreement found for this startup.")
    return {
        "id": agreement.id,
        "startup_name": agreement.startup_name,
        "agreement_date": agreement.agreement_date,
        "agreement_duration_months": agreement.agreement_duration_months,
        "total_committed_tnd": agreement.total_committed_tnd,
        "categories": json.loads(agreement.categories) if agreement.categories else [],
        "time_milestones": json.loads(agreement.time_milestones) if agreement.time_milestones else [],
        "uploaded_at": agreement.uploaded_at,
        "source_type": agreement.source_type,
    }


# ── Dashboard endpoint ────────────────────────────────────────────────────────

@router.get("/dashboard/{startup_name}")
async def get_dashboard(startup_name: str, db: AsyncSession = Depends(get_db)):
    ag_result = await db.execute(
        select(MonitorAgreement)
        .where(MonitorAgreement.startup_name == startup_name)
        .order_by(desc(MonitorAgreement.id))
    )
    agreement = ag_result.scalars().first()

    if not agreement:
        return {"startup_name": startup_name, "has_agreement": False, "active_alerts": []}

    snap_result = await db.execute(
        select(MonitorLedgerSnapshot)
        .where(MonitorLedgerSnapshot.agreement_id == agreement.id)
        .order_by(desc(MonitorLedgerSnapshot.id))
    )
    snapshot = snap_result.scalars().first()

    alert_result = await db.execute(
        select(MonitorAlert)
        .where(MonitorAlert.agreement_id == agreement.id, MonitorAlert.resolved == 0)
        .order_by(MonitorAlert.severity, desc(MonitorAlert.fired_at))
    )
    active_alerts = alert_result.scalars().all()

    category_totals = None
    if snapshot and snapshot.category_totals:
        category_totals = json.loads(snapshot.category_totals)

    return {
        "startup_name": startup_name,
        "has_agreement": True,
        "agreement_id": agreement.id,
        "agreement_date": agreement.agreement_date,
        "agreement_duration_months": agreement.agreement_duration_months,
        "total_committed_tnd": agreement.total_committed_tnd,
        "categories": json.loads(agreement.categories) if agreement.categories else [],
        "snapshot_month": snapshot.snapshot_month if snapshot else None,
        "months_elapsed": snapshot.months_elapsed if snapshot else None,
        "compliance_health_score": snapshot.compliance_health_score if snapshot else None,
        "total_spent_tnd": snapshot.total_spent_tnd if snapshot else None,
        "total_planned_to_date_tnd": snapshot.total_planned_to_date_tnd if snapshot else None,
        "unclassified_tnd": snapshot.unclassified_tnd if snapshot else 0.0,
        "category_totals": category_totals,
        "alert_count_active": snapshot.alert_count_active if snapshot else 0,
        "alert_count_total": snapshot.alert_count_total if snapshot else 0,
        "active_alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "alert_summary": a.alert_summary,
                "alert_detail": a.alert_detail,
                "fired_at": a.fired_at,
                "transaction_id": a.transaction_id,
            }
            for a in active_alerts
        ],
    }


# ── Portfolio health (sidebar list) ──────────────────────────────────────────

@router.get("/portfolio-health")
async def get_portfolio_health(db: AsyncSession = Depends(get_db)):
    ag_result = await db.execute(
        select(MonitorAgreement)
        .order_by(MonitorAgreement.startup_name)
    )
    agreements = ag_result.scalars().all()

    health_list = []
    for agreement in agreements:
        snap_result = await db.execute(
            select(MonitorLedgerSnapshot)
            .where(MonitorLedgerSnapshot.agreement_id == agreement.id)
            .order_by(desc(MonitorLedgerSnapshot.id))
        )
        snapshot = snap_result.scalars().first()

        health_list.append({
            "startup_name": agreement.startup_name,
            "compliance_health_score": snapshot.compliance_health_score if snapshot else None,
            "alert_count_active": snapshot.alert_count_active if snapshot else 0,
            "total_committed_tnd": agreement.total_committed_tnd,
            "months_elapsed": snapshot.months_elapsed if snapshot else None,
            "agreement_duration_months": agreement.agreement_duration_months,
        })

    return {"monitored_startups": health_list}


# ── Statement upload + classification ────────────────────────────────────────

@router.post("/statement/upload")
async def upload_statement(
    startup_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    ag_result = await db.execute(
        select(MonitorAgreement)
        .where(MonitorAgreement.startup_name == startup_name)
        .order_by(desc(MonitorAgreement.id))
    )
    agreement = ag_result.scalar_one_or_none()
    if not agreement:
        raise HTTPException(status_code=404, detail=f"No agreement found for '{startup_name}'.")

    content = await file.read()
    parsed = await parse_statement(content)
    txs = parsed.get("transactions") or []
    statement_month = parsed.get("statement_month")

    if not txs:
        return {
            "message": "No outgoing transactions found in statement.",
            "transaction_count": 0,
            "auto_classified": 0,
            "unclassified": 0,
            "statement_month": statement_month,
            "compliance_health_score": None,
        }

    classified = await classify_batch(txs)

    new_txs = await write_transactions(agreement.id, startup_name, txs, statement_month, classified, db)
    snapshot = await run_statement_pipeline(agreement.id, startup_name, new_txs, db)

    auto_count = sum(1 for c in classified if c.get("classification_status") == "AUTO_CLASSIFIED")

    return {
        "message": f"Statement processed: {len(txs)} transactions classified.",
        "transaction_count": len(txs),
        "auto_classified": auto_count,
        "unclassified": len(txs) - auto_count,
        "statement_month": statement_month,
        "compliance_health_score": snapshot.compliance_health_score,
    }


# ── Transaction log (paginated + filtered) ───────────────────────────────────

@router.get("/transactions/{startup_name}")
async def get_transactions(
    startup_name: str,
    page: int = 1,
    page_size: int = 50,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    base_q = select(MonitorTransaction).where(MonitorTransaction.startup_name == startup_name)

    if category:
        # Filter on effective category: human_category if set, else ai_category
        base_q = base_q.where(
            or_(
                and_(MonitorTransaction.human_category.isnot(None), MonitorTransaction.human_category == category),
                and_(MonitorTransaction.human_category.is_(None), MonitorTransaction.ai_category == category),
            )
        )
    if status:
        base_q = base_q.where(MonitorTransaction.classification_status == status)
    if month:
        base_q = base_q.where(MonitorTransaction.statement_month == month)

    count_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar_one()

    data_q = (
        base_q
        .order_by(desc(MonitorTransaction.transaction_date))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(data_q)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "transactions": [
            {
                "id": tx.id,
                "statement_month": tx.statement_month,
                "transaction_date": tx.transaction_date,
                "beneficiary": tx.beneficiary,
                "amount_tnd": tx.amount_tnd,
                "memo": tx.memo,
                "ai_category": tx.ai_category,
                "ai_confidence": tx.ai_confidence,
                "classification_status": tx.classification_status,
                "human_category": tx.human_category,
                "alert_triggered": tx.alert_triggered,
                "alert_type": tx.alert_type,
            }
            for tx in rows
        ],
    }


# ── Manual reclassification ───────────────────────────────────────────────────

@router.patch("/transaction/{tx_id}/classify")
async def reclassify_transaction(
    tx_id: int,
    payload: ReclassifyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MonitorTransaction).where(MonitorTransaction.id == tx_id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    tx.human_category = payload.category
    tx.classification_status = "HUMAN_VERIFIED"
    tx.alert_triggered = 0
    tx.alert_type = None

    # compute_and_write_snapshot will autoflush the tx update before querying
    snapshot = await compute_and_write_snapshot(tx.agreement_id, tx.startup_name, db)

    return {
        "id": tx.id,
        "human_category": tx.human_category,
        "classification_status": tx.classification_status,
        "compliance_health_score": snapshot.compliance_health_score,
    }


# ── Alert log ─────────────────────────────────────────────────────────────────

@router.get("/alerts/{startup_name}")
async def get_alerts(startup_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MonitorAlert)
        .where(MonitorAlert.startup_name == startup_name)
        .order_by(MonitorAlert.resolved, desc(MonitorAlert.fired_at))
    )
    alerts = result.scalars().all()
    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "alert_summary": a.alert_summary,
                "alert_detail": a.alert_detail,
                "fired_at": a.fired_at,
                "resolved": bool(a.resolved),
                "resolved_at": a.resolved_at,
                "resolved_by_note": a.resolved_by_note,
                "transaction_id": a.transaction_id,
            }
            for a in alerts
        ]
    }


# ── Resolve alert ─────────────────────────────────────────────────────────────

@router.patch("/alert/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    payload: ResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MonitorAlert).where(MonitorAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    if alert.resolved:
        raise HTTPException(status_code=400, detail="Alert is already resolved.")

    alert.resolved = 1
    alert.resolved_at = datetime.utcnow().isoformat()
    alert.resolved_by_note = payload.note or ""

    snapshot = await compute_and_write_snapshot(alert.agreement_id, alert.startup_name, db)

    return {
        "id": alert.id,
        "resolved": True,
        "resolved_at": alert.resolved_at,
        "compliance_health_score": snapshot.compliance_health_score,
    }


# ── Timeline ──────────────────────────────────────────────────────────────────

@router.get("/timeline/{startup_name}")
async def get_timeline(startup_name: str, db: AsyncSession = Depends(get_db)):
    """
    Time-series data for the Timeline tab.
    Returns:
      - monthly_spending : per-statement-month actual spend (for bar chart)
      - snapshots        : cumulative totals + health score per upload (for area + health charts)
      - monthly_plan_rate_tnd : the linear planned pace per month
    """
    ag_result = await db.execute(
        select(MonitorAgreement)
        .where(MonitorAgreement.startup_name == startup_name)
        .order_by(desc(MonitorAgreement.id))
    )
    agreement = ag_result.scalar_one_or_none()
    if not agreement:
        return {"startup_name": startup_name, "has_agreement": False}

    # Snapshots in chronological order (one per statement upload)
    snap_result = await db.execute(
        select(MonitorLedgerSnapshot)
        .where(MonitorLedgerSnapshot.agreement_id == agreement.id)
        .order_by(MonitorLedgerSnapshot.snapshot_month)
    )
    snapshots = snap_result.scalars().all()

    # All transactions — group by statement_month to get monthly spend bars
    tx_result = await db.execute(
        select(MonitorTransaction)
        .where(MonitorTransaction.agreement_id == agreement.id)
        .order_by(MonitorTransaction.statement_month)
    )
    all_txs = tx_result.scalars().all()

    monthly_spend: dict[str, float] = {}
    for tx in all_txs:
        m = tx.statement_month
        if m:
            monthly_spend[m] = monthly_spend.get(m, 0.0) + (tx.amount_tnd or 0.0)

    duration = agreement.agreement_duration_months or 60
    total_committed = agreement.total_committed_tnd or 0.0
    monthly_plan_rate = round(total_committed / duration, 2) if duration > 0 else 0.0

    return {
        "startup_name": startup_name,
        "has_agreement": True,
        "total_committed_tnd": total_committed,
        "agreement_duration_months": duration,
        "monthly_plan_rate_tnd": monthly_plan_rate,
        "snapshots": [
            {
                "month": s.snapshot_month,
                "months_elapsed": s.months_elapsed,
                "total_spent_tnd": s.total_spent_tnd,
                "total_planned_to_date_tnd": s.total_planned_to_date_tnd,
                "compliance_health_score": s.compliance_health_score,
                "alert_count_active": s.alert_count_active,
                "unclassified_tnd": s.unclassified_tnd,
            }
            for s in snapshots
        ],
        "monthly_spending": [
            {"month": m, "spent_tnd": round(v, 2)}
            for m, v in sorted(monthly_spend.items())
        ],
    }


# ── OCR demo (bank statement mock) ───────────────────────────────────────────

@router.get("/ocr-mock")
async def monitor_ocr_mock():
    """Return pre-parsed NovaPay bank statement for the OCR animation demo."""
    with open(_MOCK_PATH, encoding="utf-8") as f:
        return json.load(f)


@router.post("/ocr-confirm")
async def monitor_ocr_confirm(
    payload: OcrConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept PE-confirmed transactions from the OCR review gate and run the full pipeline."""
    ag_result = await db.execute(
        select(MonitorAgreement)
        .where(MonitorAgreement.startup_name == payload.startup_name)
        .order_by(desc(MonitorAgreement.id))
    )
    agreement = ag_result.scalar_one_or_none()
    if not agreement:
        raise HTTPException(status_code=404, detail=f"No agreement found for '{payload.startup_name}'.")

    if not payload.confirmed_transactions:
        return {"message": "No transactions to process.", "transaction_count": 0}

    # Strip pre-classification so the category agent runs fresh
    raw_txs = [
        {
            "transaction_date": t.get("transaction_date"),
            "beneficiary": t.get("beneficiary"),
            "amount_tnd": t.get("amount_tnd"),
            "memo": t.get("memo"),
        }
        for t in payload.confirmed_transactions
    ]

    classified = await classify_batch(raw_txs)

    # Apply human overrides from the review gate (human_category wins over AI)
    for i, t in enumerate(payload.confirmed_transactions):
        human_cat = t.get("human_category")
        if human_cat:
            classified[i]["ai_category"] = human_cat
            classified[i]["ai_confidence"] = 1.0
            classified[i]["classification_status"] = "HUMAN_VERIFIED"

    new_txs = await write_transactions(
        agreement.id, payload.startup_name, raw_txs, payload.statement_month, classified, db
    )
    snapshot = await run_statement_pipeline(agreement.id, payload.startup_name, new_txs, db)

    auto_count = sum(1 for c in classified if c.get("classification_status") == "AUTO_CLASSIFIED")
    human_count = sum(1 for c in classified if c.get("classification_status") == "HUMAN_VERIFIED")

    return {
        "message": f"OCR statement imported: {len(raw_txs)} transactions.",
        "transaction_count": len(raw_txs),
        "auto_classified": auto_count,
        "human_verified": human_count,
        "unclassified": len(raw_txs) - auto_count - human_count,
        "statement_month": payload.statement_month,
        "compliance_health_score": snapshot.compliance_health_score,
    }


# ── Critical alert count (sidebar badge) ─────────────────────────────────────

@router.get("/critical-count")
async def get_critical_alert_count(db: AsyncSession = Depends(get_db)):
    """Returns the total count of unresolved CRITICAL alerts across all companies."""
    result = await db.execute(
        select(func.count(MonitorAlert.id))
        .where(MonitorAlert.severity == "CRITICAL")
        .where(MonitorAlert.resolved == 0)
    )
    count = result.scalar() or 0
    return {"critical_count": count}


# ── No-statement alert ────────────────────────────────────────────────────────

@router.post("/statement/no-statement")
async def mark_no_statement(
    payload: NoStatementRequest,
    db: AsyncSession = Depends(get_db),
):
    """Fire a NO_STATEMENT alert when a startup has not uploaded a statement for a given month."""
    ag_result = await db.execute(
        select(MonitorAgreement)
        .where(MonitorAgreement.startup_name == payload.startup_name)
        .order_by(desc(MonitorAgreement.id))
    )
    agreement = ag_result.scalar_one_or_none()
    if not agreement:
        raise HTTPException(status_code=404, detail=f"No agreement found for '{payload.startup_name}'.")

    alert = MonitorAlert(
        agreement_id=agreement.id,
        startup_name=payload.startup_name,
        transaction_id=None,
        alert_type="NO_STATEMENT",
        severity="WARNING",
        alert_summary=f"No bank statement received for {payload.month}.",
        alert_detail=(
            f"No bank statement was uploaded for {payload.startup_name} for the period {payload.month}. "
            "Startups are required to provide monthly statements within 10 days of month-end. "
            "Contact the startup to obtain the missing statement and verify continued compliance "
            "with the SICAR reporting schedule."
        ),
        fired_at=datetime.utcnow().isoformat(),
        resolved=0,
    )
    db.add(alert)
    await db.commit()

    snapshot = await compute_and_write_snapshot(agreement.id, payload.startup_name, db)

    return {
        "message": f"NO_STATEMENT alert filed for {payload.startup_name} ({payload.month}).",
        "compliance_health_score": snapshot.compliance_health_score,
    }
