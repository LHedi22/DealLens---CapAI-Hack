import json
from datetime import datetime
from backend.agents.ollama_client import call_ollama, MODEL_A

PAIR_SCORER_SYSTEM = """You are an investment analyst evaluating synergy potential between two portfolio companies.

Score the following on a scale of 0–100:
1. service_bridge_score: Can Company A's services satisfy Company B's operational needs or strategic gaps, or vice versa?
2. shared_customer_score: How much do their target customer segments overlap?
3. co_dev_score: Could they co-develop a new product or service together that neither could build alone?

Also return:
4. synergy_types_triggered: array containing any of ["SERVICE", "CUSTOMER", "CO_DEV"] where score > 40
5. match_explanation: one plain-language sentence describing the strongest synergy opportunity
6. value_creation_type: one of "cost_saving", "revenue_expansion", "new_market"
7. value_estimate_label: a rough estimate label like "~120,000 TND annual savings" (make reasonable estimates based on context)
8. action_suggestion: one concrete next step for the PE analyst (e.g. "Introduce founders", "Draft pilot agreement")

Return ONLY a valid JSON object with exactly these 8 keys.
No explanation. No markdown. No backticks."""

_DEFAULTS = {
    "service_bridge_score":   0,
    "shared_customer_score":  0,
    "co_dev_score":           0,
    "synergy_types_triggered": [],
    "match_explanation":      "No significant synergy detected.",
    "value_creation_type":    "cost_saving",
    "value_estimate_label":   "Unknown",
    "action_suggestion":      "Monitor for future opportunities.",
}


async def score_pair(profile_a: dict, profile_b: dict) -> dict:
    """
    Score a pair of SynergyProfiles via Ollama.
    Returns a dict ready to be persisted as a synergy_pairs row.
    """
    user_content = (
        f"Company A — {profile_a['company_name']}:\n"
        f"Services: {profile_a.get('services_offered', '[]')}\n"
        f"Customers: {profile_a.get('target_customers', '[]')}\n"
        f"Operational needs: {profile_a.get('operational_needs', '[]')}\n"
        f"Strategic gaps: {profile_a.get('strategic_gaps', '[]')}\n\n"
        f"Company B — {profile_b['company_name']}:\n"
        f"Services: {profile_b.get('services_offered', '[]')}\n"
        f"Customers: {profile_b.get('target_customers', '[]')}\n"
        f"Operational needs: {profile_b.get('operational_needs', '[]')}\n"
        f"Strategic gaps: {profile_b.get('strategic_gaps', '[]')}"
    )

    raw = await call_ollama(
        model=MODEL_A,
        system_prompt=PAIR_SCORER_SYSTEM,
        user_content=user_content,
        agent="synergy_pair_scorer",
    )

    if not raw:
        raw = dict(_DEFAULTS)

    svc   = max(0, min(100, int(raw.get("service_bridge_score")  or 0)))
    cust  = max(0, min(100, int(raw.get("shared_customer_score") or 0)))
    codev = max(0, min(100, int(raw.get("co_dev_score")          or 0)))
    composite = round(svc * 0.40 + cust * 0.35 + codev * 0.25)

    types = raw.get("synergy_types_triggered", [])
    if not isinstance(types, list):
        types = []

    return {
        "company_a":               profile_a["company_name"],
        "company_b":               profile_b["company_name"],
        "service_bridge_score":    svc,
        "shared_customer_score":   cust,
        "co_dev_score":            codev,
        "composite_score":         composite,
        "synergy_types_triggered": json.dumps(types),
        "match_explanation":       raw.get("match_explanation") or _DEFAULTS["match_explanation"],
        "value_creation_type":     raw.get("value_creation_type") or "cost_saving",
        "value_estimate_label":    raw.get("value_estimate_label") or "Unknown",
        "action_suggestion":       raw.get("action_suggestion") or _DEFAULTS["action_suggestion"],
        "confidence_level":        _compute_confidence(profile_a, profile_b, composite),
        "analyst_decision":        None,
        "created_at":              datetime.utcnow().isoformat(),
    }


def _compute_confidence(pa: dict, pb: dict, composite: int) -> str:
    if pa.get("profile_confidence") == "HIGH" and pb.get("profile_confidence") == "HIGH" and composite >= 70:
        return "HIGH"
    if composite >= 55 and "LOW" not in (pa.get("profile_confidence"), pb.get("profile_confidence")):
        return "MEDIUM"
    return "LOW"
