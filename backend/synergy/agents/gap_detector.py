import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import SynergyProfile, SynergyPair, SynergyGap
from backend.agents.ollama_client import call_ollama, MODEL_A

GAP_CLUSTER_SYSTEM = """You are analyzing the unmet needs of a portfolio of startups.
Below is a JSON array of need objects, each with a "company" and "need" field.
Group semantically similar needs into clusters.
For each cluster return:
- gap_label: a short descriptive name (3-6 words)
- need_description: one sentence explaining the shared need
- affected_companies: array of company names in this cluster
- suggested_sector: sector of an ideal partner company (e.g. "FinTech", "HR Tech")
- suggested_stage: ideal partner stage (e.g. "Seed", "Series A")
- cost_intensity_estimate: integer 0-30, how expensive this need is to solve externally
- mandate_fit_score: integer 0-30, how well filling this gap fits a PE fund mandate

Return ONLY a valid JSON object with key "clusters" containing an array of cluster objects.
No explanation. No markdown. No backticks."""


def _parse_array(val) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


async def detect_gaps(db: AsyncSession) -> list[dict]:
    profiles_result = await db.execute(select(SynergyProfile))
    profiles = profiles_result.scalars().all()
    if not profiles:
        return []

    total_portfolio_size = len(profiles)

    flat_needs = []
    for p in profiles:
        for need in _parse_array(p.operational_needs):
            flat_needs.append({"company": p.company_name, "need": need})
        for gap in _parse_array(p.strategic_gaps):
            flat_needs.append({"company": p.company_name, "need": gap})

    if not flat_needs:
        return []

    raw = await call_ollama(MODEL_A, GAP_CLUSTER_SYSTEM, json.dumps(flat_needs), "gap_detector")
    clusters = raw.get("clusters", []) if isinstance(raw, dict) else []
    if not isinstance(clusters, list):
        return []

    # Build approved-pair set for internal satisfaction check
    pairs_result = await db.execute(select(SynergyPair))
    approved_pairs: set[tuple] = set()
    for p in pairs_result.scalars().all():
        if p.analyst_decision == "approved":
            approved_pairs.add((p.company_a, p.company_b))
            approved_pairs.add((p.company_b, p.company_a))

    # All portfolio services: [(company_name, service_lower)]
    portfolio_services = []
    for p in profiles:
        for svc in _parse_array(p.services_offered):
            portfolio_services.append((p.company_name, svc.lower()))

    # Existing gap labels — INSERT OR IGNORE behaviour
    existing_labels_result = await db.execute(select(SynergyGap.gap_label))
    existing_labels = set(existing_labels_result.scalars().all())

    results = []
    for cluster in clusters:
        if not isinstance(cluster, dict):
            continue

        gap_label = (cluster.get("gap_label") or "Unknown Gap").strip()
        affected  = [c for c in cluster.get("affected_companies", []) if isinstance(c, str)]
        need_desc = cluster.get("need_description") or ""

        # Internal satisfaction check
        gap_words = set(gap_label.lower().split())
        internally_approved = False
        partial_filler      = None

        for company, svc in portfolio_services:
            svc_words = set(svc.split())
            if len(gap_words & svc_words) >= 2:
                for affected_co in affected:
                    if company != affected_co:
                        if (company, affected_co) in approved_pairs:
                            internally_approved = True
                            break
                        else:
                            partial_filler = company
                if internally_approved:
                    break

        if internally_approved:
            status = "filled"
        else:
            status = "open"
            if partial_filler:
                need_desc = (
                    f"{need_desc} "
                    f"(Partially covered by {partial_filler} — pair not yet approved.)"
                ).strip()

        # Urgency formula
        cost_intensity = max(0, min(30, int(cluster.get("cost_intensity_estimate") or 15)))
        mandate_fit    = max(0, min(30, int(cluster.get("mandate_fit_score")        or 15)))
        affected_count = len(affected)
        urgency = max(0, min(100, round(
            (affected_count / total_portfolio_size) * 40
            + cost_intensity
            + mandate_fit
        )))

        row = {
            "gap_label":              gap_label,
            "need_description":       need_desc,
            "affected_companies":     json.dumps(affected),
            "affected_count":         affected_count,
            "estimated_annual_spend": None,
            "suggested_sector":       cluster.get("suggested_sector"),
            "suggested_stage":        cluster.get("suggested_stage"),
            "urgency_score":          urgency,
            "status":                 status,
        }
        results.append(row)

        # INSERT OR IGNORE: skip if label already exists
        if gap_label in existing_labels:
            continue

        db.add(SynergyGap(
            gap_label=              gap_label,
            need_description=       need_desc,
            affected_companies=     json.dumps(affected),
            affected_count=         affected_count,
            estimated_annual_spend= None,
            suggested_sector=       cluster.get("suggested_sector"),
            suggested_stage=        cluster.get("suggested_stage"),
            urgency_score=          urgency,
            status=                 status,
        ))
        existing_labels.add(gap_label)

    await db.commit()
    results.sort(key=lambda x: x["urgency_score"], reverse=True)
    return results
