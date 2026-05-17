import json
from itertools import combinations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import SynergyProfile, SynergyPair
from backend.synergy.agents.pair_scorer import score_pair

SECTOR_COLORS = {
    "EdTech":            "#8B5CF6",
    "FinTech":           "#3B82F6",
    "Logistics":         "#F59E0B",
    "HealthTech":        "#22C55E",
    "Construction Tech": "#F97316",
}


async def run_full_pipeline(db: AsyncSession) -> dict:
    """
    1. Fetch all existing synergy profiles
    2. Score any pairs not yet in synergy_pairs
    3. Return pairs (composite >= 55) + full graph data
    """
    profiles_result = await db.execute(select(SynergyProfile))
    profiles = profiles_result.scalars().all()

    if not profiles:
        return {
            "profiles_ready":   0,
            "pairs_computed":   0,
            "new_pairs_scored": 0,
            "pairs":            [],
            "graph":            {"nodes": [], "edges": []},
        }

    profile_map = {p.company_name: p for p in profiles}

    # Build set of already-scored pairs (normalised both directions)
    existing_result = await db.execute(
        select(SynergyPair.company_a, SynergyPair.company_b)
    )
    existing: set[tuple[str, str]] = set()
    for row in existing_result.all():
        existing.add((row[0], row[1]))
        existing.add((row[1], row[0]))

    new_scored = 0
    for name_a, name_b in combinations(profile_map.keys(), 2):
        if (name_a, name_b) not in existing:
            pa = profile_to_dict(profile_map[name_a])
            pb = profile_to_dict(profile_map[name_b])
            pair_data = await score_pair(pa, pb)
            db.add(SynergyPair(**pair_data))
            existing.add((name_a, name_b))
            existing.add((name_b, name_a))
            new_scored += 1

    if new_scored:
        await db.commit()

    all_result = await db.execute(
        select(SynergyPair).order_by(SynergyPair.composite_score.desc())
    )
    all_pairs = all_result.scalars().all()

    return {
        "profiles_ready":   len(profiles),
        "pairs_computed":   len(all_pairs),
        "new_pairs_scored": new_scored,
        "pairs":            [pair_to_dict(p) for p in all_pairs if (p.composite_score or 0) >= 55],
        "graph":            build_graph(profiles, all_pairs),
    }


def profile_to_dict(p: SynergyProfile) -> dict:
    return {
        "company_name":       p.company_name,
        "sector":             p.sector,
        "stage":              p.stage,
        "geography":          p.geography,
        "profile_confidence": p.profile_confidence,
        "services_offered":   p.services_offered,
        "target_customers":   p.target_customers,
        "operational_needs":  p.operational_needs,
        "strategic_gaps":     p.strategic_gaps,
    }


def pair_to_dict(p: SynergyPair) -> dict:
    return {
        "id":                      p.id,
        "company_a":               p.company_a,
        "company_b":               p.company_b,
        "service_bridge_score":    p.service_bridge_score,
        "shared_customer_score":   p.shared_customer_score,
        "co_dev_score":            p.co_dev_score,
        "composite_score":         p.composite_score,
        "synergy_types_triggered": json.loads(p.synergy_types_triggered or "[]"),
        "match_explanation":       p.match_explanation,
        "value_creation_type":     p.value_creation_type,
        "value_estimate_label":    p.value_estimate_label,
        "action_suggestion":       p.action_suggestion,
        "confidence_level":        p.confidence_level,
        "analyst_decision":        p.analyst_decision,
        "decision_reason":         p.decision_reason,
        "created_at":              p.created_at,
    }


def build_graph(profiles: list, pairs: list) -> dict:
    nodes = [
        {
            "id":     p.company_name,
            "sector": p.sector or "Other",
            "stage":  p.stage,
            "color":  SECTOR_COLORS.get(p.sector, "#94A3B8"),
        }
        for p in profiles
    ]
    # Include pairs down to score 40 in the graph (borderline pairs still get an edge)
    edges = [
        {
            "source":           p.company_a,
            "target":           p.company_b,
            "composite_score":  p.composite_score,
            "types":            json.loads(p.synergy_types_triggered or "[]"),
            "analyst_decision": p.analyst_decision,
            "pair_id":          p.id,
        }
        for p in pairs
        if (p.composite_score or 0) >= 40
    ]
    return {"nodes": nodes, "edges": edges}
