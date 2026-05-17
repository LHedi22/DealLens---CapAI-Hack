import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import DealHistory, EntitySector
from backend.agents.ollama_client import call_ollama, MODEL_B
from backend.debug_state import step_started, step_completed, step_failed

logger = logging.getLogger(__name__)

WEIGHTS = {
    "sector":       0.30,
    "stage":        0.20,
    "model":        0.15,
    "revenue":      0.10,
    "geography":    0.10,
    "team_profile": 0.10,
    "esg_tier":     0.05,
}

STAGE_ORDER = ["Pre-seed", "Seed", "Series A", "Series B+"]

SECTOR_ADJACENCY = {
    "EdTech":            ["SaaS", "Consumer App"],
    "FinTech":           ["SaaS", "E-Commerce"],
    "HealthTech":        ["SaaS", "Deep Tech"],
    "Logistics":         ["E-Commerce", "Manufacturing"],
    "SaaS":              ["EdTech", "FinTech", "HealthTech"],
    "AgriTech":          ["CleanTech", "Manufacturing"],
    "E-Commerce":        ["Logistics", "FinTech"],
    "CleanTech":         ["AgriTech", "Manufacturing"],
    "Manufacturing":     ["Construction Tech", "CleanTech"],
    "Construction Tech": ["Manufacturing", "SaaS"],
}


def _sector_score(incoming: str, stored: str) -> float:
    if incoming == stored:
        return 1.0
    if stored in SECTOR_ADJACENCY.get(incoming, []):
        return 0.5
    return 0.0


def _stage_score(incoming: str, stored: str) -> float:
    try:
        i = STAGE_ORDER.index(incoming)
        j = STAGE_ORDER.index(stored)
        diff = abs(i - j)
        if diff == 0: return 1.0
        if diff == 1: return 0.5
        return 0.0
    except ValueError:
        return 0.0


def _model_score(incoming: str, stored: str) -> float:
    if not incoming or not stored:
        return 0.5
    return 1.0 if incoming == stored else 0.0


def _geography_score(incoming: str, stored: str) -> float:
    if not stored:
        return 0.5
    return 1.0 if incoming == stored else 0.0


def _esg_tier_score(incoming_composite: int, stored_composite: int) -> float:
    def to_tier(s: int) -> str:
        if s >= 80: return "Strong"
        if s >= 60: return "Adequate"
        if s >= 40: return "Weak"
        return "Critical"

    t1 = to_tier(incoming_composite or 50)
    t2 = to_tier(stored_composite or 50)
    if t1 == t2:
        return 1.0
    tiers = ["Critical", "Weak", "Adequate", "Strong"]
    diff = abs(tiers.index(t1) - tiers.index(t2))
    return 0.5 if diff == 1 else 0.0


def compute_similarity(incoming: dict, stored: DealHistory) -> float:
    scores = {
        "sector":       _sector_score(incoming.get("sector", ""), stored.sector or ""),
        "stage":        _stage_score(incoming.get("stage", ""), stored.stage or ""),
        "model":        _model_score(incoming.get("business_model_type"), stored.business_model_type),
        "revenue":      0.5,
        "geography":    _geography_score(incoming.get("geography"), stored.geography),
        "team_profile": 0.5,
        "esg_tier":     _esg_tier_score(
                            incoming.get("esg_composite", 50),
                            stored.esg_composite or 50,
                        ),
    }
    return round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS), 4)


def compute_conviction_delta(top_matches: list) -> int:
    POSITIVE = {"invested — performing", "invested — acquired", "performing", "acquired"}
    NEGATIVE = {
        "stalled at series a — founder-led sales",
        "failed",
        "failed — gig labor regulatory risk",
    }

    contributions = []
    for m in top_matches:
        decision = (m["decision"] or "").lower()
        outcome  = (m["outcome"]  or "").lower()
        sim      = m["similarity"]
        contrib  = 0.0

        if decision == "pursue":
            if any(o in outcome for o in POSITIVE):
                contrib = sim * 10
            elif any(o in outcome for o in NEGATIVE):
                contrib = -(sim * 10)
            else:
                contrib = sim * 3
        # pass decisions are neutral — they confirm caution, no delta applied

        contributions.append(contrib)

    if not contributions:
        return 0
    avg = sum(contributions) / len(contributions)
    return int(round(max(-20.0, min(20.0, avg))))


_EXPLANATION_SYSTEM = (
    "You are a memory analyst for an investment fund.\n"
    "Explain in 2-3 sentences why a conviction delta was applied to this startup's score, "
    "based on similar past deals from the fund's history.\n"
    "Be specific — mention the similar company names and what happened to them.\n"
    "Do not use filler phrases. Be direct.\n\n"
    "Return ONLY a valid JSON object:\n"
    "{\"explanation\": \"2-3 sentence explanation of the delta\"}\n\n"
    "Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."
)


async def _generate_delta_explanation(top_3: list, delta: int, incoming: dict) -> str:
    matches_summary = "\n".join(
        f"- {m['startup_name']} ({m['sector']}, {m['stage']}): "
        f"decision={m['decision']}, outcome={m['outcome']}, similarity={m['similarity_pct']}%"
        for m in top_3
    )
    user_content = (
        f"Incoming startup sector: {incoming.get('sector')}, stage: {incoming.get('stage')}\n"
        f"Conviction delta applied: {delta:+d} points\n\n"
        f"Top 3 similar past deals:\n{matches_summary}\n\n"
        "Explain why this delta was applied."
    )
    raw = await call_ollama(MODEL_B, _EXPLANATION_SYSTEM, user_content, agent="memory")
    return raw.get("explanation") or _default_explanation(delta, top_3)


def _default_explanation(delta: int, top_3: list) -> str:
    if not top_3:
        return "No similar past deals found in memory. Delta set to 0."
    best = top_3[0]
    direction = "positive" if delta > 0 else "negative" if delta < 0 else "neutral"
    return (
        f"Memory matching found {len(top_3)} similar past deal(s). "
        f"The closest match is {best['startup_name']} ({best['similarity_pct']}% similar), "
        f"which resulted in: {best['outcome'] or 'unknown outcome'}. "
        f"This produced a {direction} conviction signal of {delta:+d} points."
    )


async def _get_sector_conviction(sector: str, db: AsyncSession) -> dict:
    result = await db.execute(
        select(EntitySector).where(EntitySector.sector_name == sector)
    )
    entity = result.scalar_one_or_none()

    if not entity:
        return {
            "sector": sector,
            "total_evaluations": 0,
            "total_pursued": 0,
            "win_rate": 0.0,
            "trend_direction": "stable",
            "learning_note": f"This is the first time the fund has evaluated a {sector} startup.",
        }

    win_pct = int(entity.win_rate * 100)
    learning = (
        f"The fund has evaluated {entity.total_evaluations} {entity.sector_name} "
        f"startup(s), pursuing {entity.total_pursued}. "
        f"Win rate: {win_pct}%. Sector trend: {entity.trend_direction}."
    )
    return {
        "sector": sector,
        "total_evaluations": entity.total_evaluations,
        "total_pursued": entity.total_pursued,
        "win_rate": round(entity.win_rate * 100, 1),
        "avg_business_score": round(entity.avg_business_score, 1),
        "avg_esg_score": round(entity.avg_esg_score, 1),
        "trend_direction": entity.trend_direction,
        "learning_note": learning,
    }


async def run_memory_matching(incoming: dict, db: AsyncSession) -> dict:
    step_started("memory")
    try:
        result = await db.execute(
            select(DealHistory).where(DealHistory.is_pipeline == False)
        )
        history_deals = result.scalars().all()

        if not history_deals:
            step_completed("memory", "Delta: 0 (no history)")
            return _empty_memory(incoming.get("sector", "Unknown"))

        scored = []
        for deal in history_deals:
            sim = compute_similarity(incoming, deal)
            scored.append({
                "startup_name":  deal.startup_name,
                "sector":        deal.sector,
                "stage":         deal.stage,
                "similarity":    sim,
                "similarity_pct": int(sim * 100),
                "decision":      deal.decision,
                "outcome":       deal.outcome,
                "outcome_notes": deal.outcome_notes,
                "business_score": deal.business_score,
                "esg_composite":  deal.esg_composite,
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        top_3 = scored[:3]

        delta = compute_conviction_delta(top_3)
        explanation = await _generate_delta_explanation(top_3, delta, incoming)
        sector_conviction = await _get_sector_conviction(
            incoming.get("sector", "Unknown"), db
        )

        step_completed("memory", f"Delta: {delta:+d} | Matches: {len(top_3)}")
        return {
            "top_matches":       top_3,
            "conviction_delta":  delta,
            "delta_explanation": explanation,
            "sector_conviction": sector_conviction,
        }

    except Exception as e:
        step_failed("memory", type(e).__name__, str(e))
        logger.error(f"Memory matching failed: {e}")
        return _empty_memory(incoming.get("sector", "Unknown"))


def _empty_memory(sector: str = "Unknown") -> dict:
    return {
        "top_matches": [],
        "conviction_delta": 0,
        "delta_explanation": "No past deals in memory yet. This is the first evaluation.",
        "sector_conviction": {
            "sector": sector,
            "total_evaluations": 0,
            "total_pursued": 0,
            "win_rate": 0.0,
            "trend_direction": "stable",
            "learning_note": "No historical data available yet.",
        },
    }
