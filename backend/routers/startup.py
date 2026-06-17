from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json

from backend.database import get_db
from backend.models import DealHistory
from backend.schemas import StartupProfile, DealSummary, DealDetail

router = APIRouter()


@router.post("/startup/profile")
async def submit_profile(profile: StartupProfile):
    return {"status": "ok", "startup_name": profile.startup_name}


@router.get("/pipeline", response_model=List[DealSummary])
async def get_pipeline(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DealHistory)
        .where(DealHistory.is_pipeline == True)  # noqa: E712
        .order_by(DealHistory.final_score.desc())
    )
    deals = result.scalars().all()
    return deals


@router.get("/pipeline/{deal_id}", response_model=DealDetail)
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DealHistory).where(DealHistory.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal
