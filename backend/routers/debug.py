import asyncio
import copy
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, seed_database, engine, DATABASE_URL
from backend.debug_state import emit_log, log_store, pipeline_state
from backend.models import (
    Base, CachedEvaluation, DealHistory, EntityFounder,
    EntitySector, PortfolioCompany,
)

router = APIRouter(prefix="/debug", tags=["debug"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean(row) -> dict:
    """Strip SQLAlchemy internal keys from __dict__."""
    return {k: v for k, v in row.__dict__.items() if not k.startswith("_")}


# ── Log endpoints ─────────────────────────────────────────────────────────────

@router.get("/logs")
async def get_logs():
    return list(log_store)


@router.delete("/logs")
async def clear_logs():
    log_store.clear()
    return {"cleared": True}


@router.get("/logs/stream")
async def stream_logs():
    async def _generator():
        sent = 0
        # send all existing logs on connect
        current = list(log_store)
        for entry in current:
            yield f"data: {json.dumps(entry)}\n\n"
        sent = len(current)

        while True:
            await asyncio.sleep(0.3)
            current = list(log_store)
            if len(current) > sent:
                for entry in current[sent:]:
                    yield f"data: {json.dumps(entry)}\n\n"
                sent = len(current)

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Pipeline endpoints ────────────────────────────────────────────────────────

@router.get("/pipeline")
async def get_pipeline():
    state = copy.deepcopy(pipeline_state)
    # Convert float timestamps to strings for JSON
    for step in state.get("steps", {}).values():
        for key in ("started_at", "completed_at"):
            if isinstance(step.get(key), float):
                step[key] = time.strftime("%H:%M:%S", time.localtime(step[key]))
    return state


@router.get("/pipeline/stream")
async def stream_pipeline():
    async def _generator():
        while True:
            state = copy.deepcopy(pipeline_state)
            for step in state.get("steps", {}).values():
                for key in ("started_at", "completed_at"):
                    if isinstance(step.get(key), float):
                        step[key] = time.strftime("%H:%M:%S", time.localtime(step[key]))
            yield f"data: {json.dumps(state)}\n\n"
            # Always keep streaming — breaking on idle causes the frontend to
            # reconnect every 3s (onerror). A persistent 500ms heartbeat is cleaner.
            await asyncio.sleep(0.5)

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Knowledge graph endpoint ──────────────────────────────────────────────────

@router.get("/graph")
async def get_knowledge_graph(db: AsyncSession = Depends(get_db)):
    deal_count       = await db.scalar(select(func.count(DealHistory.id)))
    deal_seed        = await db.scalar(select(func.count(DealHistory.id)).where(DealHistory.is_seed_data == True))   # noqa: E712
    deal_pipeline    = await db.scalar(select(func.count(DealHistory.id)).where(DealHistory.is_pipeline == True))    # noqa: E712
    sector_count     = await db.scalar(select(func.count(EntitySector.id)))
    founder_count    = await db.scalar(select(func.count(EntityFounder.id)))
    portfolio_count  = await db.scalar(select(func.count(PortfolioCompany.id)))
    cached_count     = await db.scalar(select(func.count(CachedEvaluation.startup_name)))

    esg_flags_count  = 10  # hardcoded — never changes (seeded from code, not DB table)

    deal_sample    = [_clean(r) for r in (await db.execute(select(DealHistory).limit(5))).scalars()]
    sector_sample  = [_clean(r) for r in (await db.execute(select(EntitySector).limit(5))).scalars()]
    founder_sample = [_clean(r) for r in (await db.execute(select(EntityFounder).limit(5))).scalars()]
    portfolio_sample = [_clean(r) for r in (await db.execute(select(PortfolioCompany).limit(5))).scalars()]

    return {
        "tables": {
            "deal_history": {
                "count": deal_count,
                "seed_count": deal_seed,
                "pipeline_count": deal_pipeline,
                "sample": deal_sample,
            },
            "entity_sectors": {
                "count": sector_count,
                "sample": sector_sample,
            },
            "entity_founders": {
                "count": founder_count,
                "sample": founder_sample,
            },
            "portfolio_companies": {
                "count": portfolio_count,
                "sample": portfolio_sample,
            },
            "esg_red_flags": {
                "count": esg_flags_count,
                "sample": [],
            },
            "cached_evaluations": {
                "count": cached_count,
                "sample": [],
            },
        },
        "relationships": [
            {"from": "deal_history",        "to": "entity_sectors",      "label": "sector → sector_name",      "type": "many-to-one"},
            {"from": "deal_history",        "to": "entity_founders",     "label": "founder_names → name",      "type": "many-to-many"},
            {"from": "deal_history",        "to": "esg_red_flags",       "label": "red_flags → code",          "type": "many-to-many"},
            {"from": "portfolio_companies", "to": "entity_sectors",      "label": "sector → sector_name",      "type": "many-to-one"},
            {"from": "cached_evaluations",  "to": "deal_history",        "label": "startup_name → startup_name","type": "one-to-one"},
        ],
        "db_path": DATABASE_URL.replace("sqlite+aiosqlite:///", ""),
        "fetched_at": time.strftime("%H:%M:%S"),
    }


# ── Control endpoints ─────────────────────────────────────────────────────────

@router.post("/db/reseed")
async def reseed_db():
    await seed_database()
    return {"reseeded": True}


@router.post("/db/reset")
async def reset_db():
    from backend.debug_state import pipeline_state as ps
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_database()
    log_store.clear()
    ps.clear()
    from backend.debug_state import _blank_pipeline
    ps.update(_blank_pipeline())
    emit_log("WARN", "fastapi", "Database reset and re-seeded")
    return {"reset": True}
