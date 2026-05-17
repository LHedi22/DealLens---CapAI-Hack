import json
from datetime import datetime

from backend.agents.ollama_client import call_ollama, MODEL_A

GAP_DETECTOR_SYSTEM = """You are a portfolio gap analyst for a startup investment fund.
Analyze the provided portfolio company profiles and identify shared unmet needs — operational or
strategic gaps that multiple companies have in common and that an external company could fill.

For each gap found, return:
- gap_label: short descriptive name (e.g. "B2B Payment Infrastructure")
- need_description: 1-2 sentences on the unmet need
- affected_companies: array of company names that share this gap
- affected_count: integer count
- estimated_annual_spend: rough cost estimate string (e.g. "~$50K–$150K/yr per company")
- suggested_sector: sector of an ideal partner company (e.g. "FinTech", "LegalTech")
- suggested_stage: ideal partner stage (e.g. "Seed", "Series A")
- urgency_score: integer 0–100 (higher = more urgent across the portfolio)

Identify 3–6 gaps maximum. Only include gaps shared by at least 2 companies.
Respond ONLY with a valid JSON object with a single key "gaps" containing an array.
No explanation. No markdown. No backticks."""

_DEFAULTS = {
    "gap_label":              "Unknown Gap",
    "need_description":       "",
    "affected_companies":     [],
    "affected_count":         0,
    "estimated_annual_spend": "Unknown",
    "suggested_sector":       "SaaS",
    "suggested_stage":        "Seed",
    "urgency_score":          50,
}


def _parse_array(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, ValueError):
            return []
    return []


async def detect_gaps(profiles: list[dict]) -> list[dict]:
    if not profiles:
        return []

    summary_parts = []
    for p in profiles:
        needs = _parse_array(p.get("operational_needs"))
        gaps  = _parse_array(p.get("strategic_gaps"))
        summary_parts.append(
            f"Company: {p['company_name']} ({p.get('sector', '')}, {p.get('stage', '')})\n"
            f"  Operational needs: {', '.join(needs) or 'none'}\n"
            f"  Strategic gaps:    {', '.join(gaps)  or 'none'}"
        )

    user_content = (
        f"Portfolio: {len(profiles)} companies. Identify shared gaps.\n\n"
        + "\n\n".join(summary_parts)
    )

    raw = await call_ollama(
        model=MODEL_A,
        system_prompt=GAP_DETECTOR_SYSTEM,
        user_content=user_content,
        agent="gap_detector",
    )

    gap_list = raw.get("gaps", []) if raw else []
    if not isinstance(gap_list, list):
        return []

    results = []
    for g in gap_list:
        if not isinstance(g, dict):
            continue
        affected = g.get("affected_companies", [])
        if not isinstance(affected, list):
            affected = []
        urgency = max(0, min(100, int(g.get("urgency_score") or 50)))
        results.append({
            "gap_label":              g.get("gap_label")              or _DEFAULTS["gap_label"],
            "need_description":       g.get("need_description")       or "",
            "affected_companies":     json.dumps(affected),
            "affected_count":         len(affected),
            "estimated_annual_spend": g.get("estimated_annual_spend") or "Unknown",
            "suggested_sector":       g.get("suggested_sector")       or "SaaS",
            "suggested_stage":        g.get("suggested_stage")        or "Seed",
            "urgency_score":          urgency,
            "status":                 "open",
            "created_at":             datetime.utcnow().isoformat(),
        })

    results.sort(key=lambda x: x["urgency_score"], reverse=True)
    return results
