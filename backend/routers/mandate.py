from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from backend.database import get_db
from backend.models import MandateConfig, DealHistory, CachedEvaluation
from backend.schemas import MandateConfigIn, MandateConfigOut, MandateApplyResult

router = APIRouter()


def _serialize_lists(mandate_in: MandateConfigIn) -> dict:
    data = mandate_in.model_dump()
    for field in ("sector_focus", "stage_preference", "geography_scope"):
        if data[field] is not None:
            data[field] = json.dumps(data[field])
    return data


def _deserialize_mandate(config: MandateConfig) -> MandateConfigOut:
    return MandateConfigOut(
        id=config.id,
        min_esg_threshold=config.min_esg_threshold,
        ticket_size_min=config.ticket_size_min,
        ticket_size_max=config.ticket_size_max,
        esg_priority_axis=config.esg_priority_axis,
        sector_focus=json.loads(config.sector_focus) if config.sector_focus else None,
        stage_preference=json.loads(config.stage_preference) if config.stage_preference else None,
        geography_scope=json.loads(config.geography_scope) if config.geography_scope else None,
    )


@router.get("/mandate", response_model=MandateConfigOut)
async def get_mandate(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MandateConfig).where(MandateConfig.id == 1))
    config = result.scalar_one_or_none()
    if not config:
        config = MandateConfig(id=1)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return _deserialize_mandate(config)


@router.post("/mandate", response_model=MandateConfigOut)
async def save_mandate(mandate_in: MandateConfigIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MandateConfig).where(MandateConfig.id == 1))
    config = result.scalar_one_or_none()
    data = _serialize_lists(mandate_in)
    if not config:
        config = MandateConfig(id=1, **data)
        db.add(config)
    else:
        for key, val in data.items():
            setattr(config, key, val)
    await db.commit()
    await db.refresh(config)
    return _deserialize_mandate(config)


@router.post("/mandate/apply", response_model=MandateApplyResult)
async def apply_mandate(db: AsyncSession = Depends(get_db)):
    """
    Re-apply the current mandate to all pipeline startups.
    Any that now breach the mandate are flipped to 'pass' in the DB.
    """
    mandate_record = await db.scalar(select(MandateConfig).where(MandateConfig.id == 1))
    if not mandate_record:
        return MandateApplyResult(changed_startups=[], message="No mandate configured.")

    sector_focus  = json.loads(mandate_record.sector_focus or "[]")
    stage_pref    = json.loads(mandate_record.stage_preference or "[]")
    min_esg       = mandate_record.min_esg_threshold or 0

    result = await db.execute(
        select(DealHistory).where(DealHistory.is_pipeline == True)  # noqa: E712
    )
    pipeline = result.scalars().all()

    changed = []
    for deal in pipeline:
        breaches = []
        if sector_focus and deal.sector not in sector_focus:
            breaches.append(f"Sector '{deal.sector}' outside fund focus")
        if stage_pref and deal.stage not in stage_pref:
            breaches.append(f"Stage '{deal.stage}' outside fund preference")
        if min_esg > 0 and (deal.esg_composite or 0) < min_esg:
            breaches.append(f"ESG score {deal.esg_composite} below fund minimum {min_esg}")

        if breaches and deal.decision != "pass":
            changed.append({
                "startup_name": deal.startup_name,
                "old_decision": deal.decision,
                "new_decision": "pass",
                "reasons": breaches,
            })
            deal.decision = "pass"
            deal.decision_reason = "Mandate breach: " + "; ".join(breaches)

            # Invalidate cached evaluation so next Dashboard click shows updated verdict
            cached = await db.scalar(
                select(CachedEvaluation).where(
                    CachedEvaluation.startup_name == deal.startup_name
                )
            )
            if cached:
                try:
                    payload = json.loads(cached.evaluation_json)
                    payload["verdict"] = "pass"
                    payload["verdict_label"] = "PASS"
                    payload["mandate_breach"] = True
                    payload["mandate_breaches"] = breaches
                    cached.evaluation_json = json.dumps(payload)
                except Exception:
                    pass

    if changed:
        await db.commit()

    n = len(changed)
    return MandateApplyResult(
        changed_startups=changed,
        message=f"{n} startup{'s' if n != 1 else ''} re-classified based on updated mandate."
        if n else "No pipeline startups were affected by the mandate change.",
    )
