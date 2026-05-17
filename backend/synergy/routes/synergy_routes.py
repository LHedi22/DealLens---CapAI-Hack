import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.models import SynergyProfile, SynergyPair, SynergyGap, GapShortlist
from backend.synergy.engine.match_engine import run_full_pipeline, pair_to_dict, build_graph, profile_to_dict
from backend.synergy.agents.gap_detector import detect_gaps
from backend.synergy.agents.gap_hunter import hunt_gap


class DecisionBody(BaseModel):
    decision:    str
    reason:      str = ""
    snooze_days: int = 0

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
        select(SynergyGap).order_by(SynergyGap.urgency_score.desc())
    )
    gaps = gaps_result.scalars().all()

    shortlists_result = await db.execute(select(GapShortlist))
    shortlists = shortlists_result.scalars().all()

    sl_by_gap: dict[int, list] = {}
    for s in shortlists:
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

    profiles_result = await db.execute(select(SynergyProfile))
    profiles = [profile_to_dict(p) for p in profiles_result.scalars().all()]

    if not profiles:
        return {"message": "No profiles available", "gaps_count": 0, "ran": False}

    gap_dicts = await detect_gaps(profiles)

    if force:
        existing_rows = await db.execute(select(SynergyGap))
        for row in existing_rows.scalars().all():
            await db.delete(row)
        await db.flush()

    for g in gap_dicts:
        db.add(SynergyGap(
            gap_label=              g["gap_label"],
            need_description=       g["need_description"],
            affected_companies=     g["affected_companies"],
            affected_count=         g["affected_count"],
            estimated_annual_spend= g["estimated_annual_spend"],
            suggested_sector=       g["suggested_sector"],
            suggested_stage=        g["suggested_stage"],
            urgency_score=          g["urgency_score"],
            status=                 "open",
        ))

    await db.commit()
    new_count = await db.scalar(select(func.count()).select_from(SynergyGap))
    return {"message": "Gap detection complete", "gaps_count": new_count or 0, "ran": True}


@router.post("/gaps/{gap_id}/hunt")
async def hunt_gap_candidates(gap_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SynergyGap).where(SynergyGap.id == gap_id))
    gap = result.scalar_one_or_none()
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")

    gap_dict = _gap_to_dict(gap, [])

    candidates = await hunt_gap(gap_dict)

    # Replace existing shortlist for this gap
    existing_sl = await db.execute(select(GapShortlist).where(GapShortlist.gap_id == gap_id))
    for row in existing_sl.scalars().all():
        await db.delete(row)
    await db.flush()

    for c in candidates:
        db.add(GapShortlist(
            gap_id=       gap_id,
            company_name= c["company_name"],
            website=      c["website"],
            description=  c["description"],
            fit_score=    c["fit_score"],
            fit_reason=   c["fit_reason"],
            flags=        c["flags"],
            source_url=   c["source_url"],
            analyst_action= None,
        ))

    gap.status = "shortlisted"
    await db.commit()

    shortlist_result = await db.execute(
        select(GapShortlist).where(GapShortlist.gap_id == gap_id)
    )
    return _gap_to_dict(gap, shortlist_result.scalars().all())
