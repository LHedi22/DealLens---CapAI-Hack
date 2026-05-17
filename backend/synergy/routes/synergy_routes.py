import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.models import DealHistory, SynergyProfile, SynergyPair, SynergyGap, GapShortlist
from backend.synergy.engine.match_engine import run_full_pipeline, pair_to_dict, build_graph, profile_to_dict
from backend.synergy.agents.gap_detector import detect_gaps
from backend.synergy.agents.gap_hunter import hunt_gap


class DecisionBody(BaseModel):
    decision:    str
    reason:      str = ""
    snooze_days: int = 0


class ShortlistActionBody(BaseModel):
    action: str  # "add_to_pipeline" | "dismissed"

router = APIRouter(prefix="/synergy")


@router.get("/status")
async def get_synergy_status(db: AsyncSession = Depends(get_db)):
    profiles_ready = await db.scalar(select(func.count()).select_from(SynergyProfile))
    pairs_computed = await db.scalar(select(func.count()).select_from(SynergyPair))
    gaps_detected  = await db.scalar(select(func.count()).select_from(SynergyGap))

    last_run_result = await db.execute(
        select(SynergyProfile.last_extracted_at)
        .order_by(SynergyProfile.last_extracted_at.desc())
        .limit(1)
    )
    last_run = last_run_result.scalar_one_or_none()

    pending_pairs = await db.scalar(
        select(func.count()).select_from(SynergyPair)
        .where(SynergyPair.analyst_decision.is_(None))
        .where(SynergyPair.composite_score >= 52)
    )

    return {
        "profiles_ready": profiles_ready or 0,
        "pairs_computed": pairs_computed or 0,
        "pending_pairs":  pending_pairs or 0,
        "gaps_detected":  gaps_detected or 0,
        "last_run":       last_run,
    }


@router.post("/run")
async def run_synergy(db: AsyncSession = Depends(get_db)):
    return await run_full_pipeline(db)


@router.get("/pairs")
async def get_pairs(
    type:     str = Query(None, description="Filter by synergy type: SERVICE | CUSTOMER | CO_DEV"),
    decision: str = Query(None, description="Filter by decision: pending | approved | rejected | snoozed"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SynergyPair).order_by(SynergyPair.composite_score.desc())
    )
    pairs = result.scalars().all()

    out = []
    for p in pairs:
        score = p.composite_score or 0
        # Always include borderline pairs (≥ 52) for demo richness; strict threshold elsewhere is 55
        if score < 52:
            continue
        types = json.loads(p.synergy_types_triggered or "[]")
        if type and type.upper() not in types:
            continue
        if decision == "pending" and p.analyst_decision is not None:
            continue
        if decision in ("approved", "rejected", "snoozed") and p.analyst_decision != decision:
            continue
        out.append(pair_to_dict(p))

    return out


@router.get("/pairs/{pair_id}")
async def get_pair(pair_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SynergyPair).where(SynergyPair.id == pair_id))
    pair = result.scalar_one_or_none()
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    return pair_to_dict(pair)


@router.get("/graph")
async def get_graph(db: AsyncSession = Depends(get_db)):
    profiles_result = await db.execute(select(SynergyProfile))
    profiles = profiles_result.scalars().all()
    pairs_result = await db.execute(
        select(SynergyPair).order_by(SynergyPair.composite_score.desc())
    )
    pairs = pairs_result.scalars().all()
    return build_graph(profiles, pairs)


@router.post("/pairs/{pair_id}/decide")
async def decide_pair(
    pair_id: int,
    body: DecisionBody,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SynergyPair).where(SynergyPair.id == pair_id))
    pair = result.scalar_one_or_none()
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    valid = {"approved", "rejected", "snoozed"}
    if body.decision not in valid:
        raise HTTPException(status_code=422, detail=f"decision must be one of {valid}")

    now = datetime.now(timezone.utc)
    pair.analyst_decision = body.decision
    pair.decision_reason  = body.reason or None
    pair.decision_at      = now

    if body.decision == "snoozed" and body.snooze_days > 0:
        pair.snooze_until = now + timedelta(days=body.snooze_days)
    else:
        pair.snooze_until = None

    await db.commit()
    await db.refresh(pair)
    return pair_to_dict(pair)


@router.post("/pairs/{pair_id}/undo")
async def undo_decision(pair_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SynergyPair).where(SynergyPair.id == pair_id))
    pair = result.scalar_one_or_none()
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    pair.analyst_decision = None
    pair.decision_reason  = None
    pair.decision_at      = None
    pair.snooze_until     = None

    await db.commit()
    await db.refresh(pair)
    return pair_to_dict(pair)


# ── Gap endpoints ─────────────────────────────────────────────────────────────

def _gap_to_dict(gap: SynergyGap, shortlist: list) -> dict:
    return {
        "id":                     gap.id,
        "gap_label":              gap.gap_label,
        "need_description":       gap.need_description,
        "affected_companies":     json.loads(gap.affected_companies or "[]"),
        "affected_count":         gap.affected_count or 0,
        "estimated_annual_spend": gap.estimated_annual_spend,
        "suggested_sector":       gap.suggested_sector,
        "suggested_stage":        gap.suggested_stage,
        "urgency_score":          gap.urgency_score or 0,
        "status":                 gap.status or "open",
        "created_at":             gap.created_at,
        "shortlist": [
            {
                "id":             s.id,
                "company_name":   s.company_name,
                "website":        s.website,
                "description":    s.description,
                "fit_score":      s.fit_score,
                "fit_reason":     s.fit_reason,
                "flags":          json.loads(s.flags or "[]"),
                "source_url":     s.source_url,
                "analyst_action": s.analyst_action,
            }
            for s in shortlist
        ],
    }


@router.get("/gaps")
async def get_gaps(db: AsyncSession = Depends(get_db)):
    gaps_result = await db.execute(
        select(SynergyGap)
        .where(SynergyGap.status != "dismissed")
        .order_by(SynergyGap.urgency_score.desc())
    )
    gaps = gaps_result.scalars().all()

    hunting_ids = {g.id for g in gaps if g.status == "hunting"}
    sl_by_gap: dict[int, list] = {}
    if hunting_ids:
        shortlists_result = await db.execute(
            select(GapShortlist).where(GapShortlist.gap_id.in_(hunting_ids))
        )
        for s in shortlists_result.scalars().all():
            sl_by_gap.setdefault(s.gap_id, []).append(s)

    return [_gap_to_dict(g, sl_by_gap.get(g.id, [])) for g in gaps]


@router.post("/gaps/detect")
async def detect_portfolio_gaps(
    force: bool = Query(False, description="Re-run even if gaps already exist"),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(select(func.count()).select_from(SynergyGap))
    if existing and existing > 0 and not force:
        return {"message": "Gaps already detected", "gaps_count": existing, "ran": False}

    if force:
        existing_rows = await db.execute(select(SynergyGap))
        for row in existing_rows.scalars().all():
            await db.delete(row)
        await db.commit()

    results = await detect_gaps(db)
    return {"message": "Gap detection complete", "gaps_count": len(results), "ran": True}


@router.post("/gaps/{gap_id}/hunt")
async def hunt_gap_candidates(gap_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SynergyGap).where(SynergyGap.id == gap_id))
    gap = result.scalar_one_or_none()
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")

    # Mark as hunting before the external call so the UI can reflect loading state
    gap.status = "hunting"
    await db.commit()

    gap_dict = _gap_to_dict(gap, [])
    candidates = await hunt_gap(gap_dict)

    # Replace existing shortlist for this gap
    existing_sl = await db.execute(select(GapShortlist).where(GapShortlist.gap_id == gap_id))
    for row in existing_sl.scalars().all():
        await db.delete(row)
    await db.flush()

    for c in candidates:
        flags = c.get("flags", [])
        db.add(GapShortlist(
            gap_id=         gap_id,
            company_name=   c["company_name"],
            website=        c.get("website"),
            description=    c.get("description"),
            fit_score=      c.get("fit_score", 50),
            fit_reason=     c.get("fit_reason"),
            flags=          json.dumps(flags) if isinstance(flags, list) else flags or "[]",
            source_url=     c.get("source_url"),
            analyst_action= None,
        ))

    await db.commit()

    shortlist_result = await db.execute(
        select(GapShortlist).where(GapShortlist.gap_id == gap_id)
    )
    await db.refresh(gap)
    return _gap_to_dict(gap, shortlist_result.scalars().all())


@router.post("/gaps/{gap_id}/shortlist/{shortlist_id}/action")
async def shortlist_action(
    gap_id: int,
    shortlist_id: int,
    body: ShortlistActionBody,
    db: AsyncSession = Depends(get_db),
):
    valid_actions = {"add_to_pipeline", "dismissed"}
    if body.action not in valid_actions:
        raise HTTPException(status_code=422, detail=f"action must be one of {valid_actions}")

    sl_result = await db.execute(
        select(GapShortlist)
        .where(GapShortlist.id == shortlist_id)
        .where(GapShortlist.gap_id == gap_id)
    )
    item = sl_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Shortlist item not found")

    item.analyst_action = body.action

    if body.action == "add_to_pipeline":
        existing = await db.scalar(
            select(func.count()).select_from(DealHistory)
            .where(DealHistory.startup_name == item.company_name)
        )
        if not existing:
            db.add(DealHistory(
                startup_name=    item.company_name,
                sector=          "Unknown",
                stage=           "Unknown",
                geography=       "Unknown",
                business_model_type= "Unknown",
                business_score=  0,
                esg_composite=   0,
                data_completeness= 0,
                confidence_level= "LOW",
                conviction_delta= 0,
                final_score=     0,
                decision=        "watch",
                decision_reason= "synergy_gap_hunt",
                is_pipeline=     True,
                is_seed_data=    False,
            ))

    await db.commit()
    return {"shortlist_id": shortlist_id, "action": body.action, "company_name": item.company_name}


@router.post("/gaps/{gap_id}/dismiss")
async def dismiss_gap(gap_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SynergyGap).where(SynergyGap.id == gap_id))
    gap = result.scalar_one_or_none()
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    gap.status = "dismissed"
    await db.commit()
    return {"gap_id": gap_id, "status": "dismissed"}


@router.get("/company/{company_name}/summary")
async def company_summary(company_name: str, db: AsyncSession = Depends(get_db)):
    approved_count = await db.scalar(
        select(func.count()).select_from(SynergyPair)
        .where(SynergyPair.analyst_decision == "approved")
        .where(
            (SynergyPair.company_a == company_name) | (SynergyPair.company_b == company_name)
        )
    )
    pending_count = await db.scalar(
        select(func.count()).select_from(SynergyPair)
        .where(SynergyPair.analyst_decision.is_(None))
        .where(
            (SynergyPair.company_a == company_name) | (SynergyPair.company_b == company_name)
        )
    )
    gap_count = await db.scalar(
        select(func.count()).select_from(SynergyGap)
        .where(SynergyGap.affected_companies.contains(company_name))
        .where(SynergyGap.status != "dismissed")
    )
    return {
        "company_name":  company_name,
        "approved_count": approved_count or 0,
        "pending_count":  pending_count or 0,
        "gap_count":      gap_count or 0,
    }
