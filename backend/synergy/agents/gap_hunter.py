import json
import os
import re
from datetime import datetime

ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"

GAP_HUNTER_SYSTEM = """You are a startup research analyst for a PE/VC fund investing in MENA markets.
Use web search to find real startup companies that could fill a specific portfolio gap.

Find 3-5 companies that:
- Offer products or services matching the described need
- Operate in or are expanding into MENA/Africa markets
- Are at the appropriate funding stage

For each company return:
- company_name: company name
- website: company website URL
- description: 1-2 sentences on what they do and their key differentiator
- fit_score: 0-100 (how well they fit this specific gap)
- fit_reason: 1 sentence explaining the fit for the affected portfolio companies
- flags: array of risk factors or caveats (empty array if none)

Respond ONLY with a valid JSON object with key "companies" containing an array.
No explanation. No markdown. No backticks."""


def _load_fallback(gap_label: str) -> list[dict]:
    seed_path = os.path.join(os.path.dirname(__file__), "..", "seed", "demo_synergy_seed.json")
    try:
        with open(seed_path) as f:
            seed = json.load(f)
        return seed.get("gap_shortlist_fallback", {}).get(gap_label, [])
    except Exception:
        return []


def _normalize(companies: list, source: str = "web") -> list[dict]:
    if not isinstance(companies, list):
        return []
    result = []
    for c in companies[:5]:
        if not isinstance(c, dict):
            continue
        flags = c.get("flags", [])
        if not isinstance(flags, list):
            flags = []
        result.append({
            "company_name": c.get("company_name") or c.get("name") or "Unknown",
            "website":      c.get("website") or c.get("url") or "",
            "description":  c.get("description") or "",
            "fit_score":    max(0, min(100, int(c.get("fit_score") or 50))),
            "fit_reason":   c.get("fit_reason") or c.get("reason") or "",
            "flags":        json.dumps(flags),
            "source_url":   c.get("source_url") or c.get("website") or "",
            "added_at":     datetime.utcnow().isoformat(),
        })
    result.sort(key=lambda x: x["fit_score"], reverse=True)
    return result


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


async def hunt_gap(gap: dict) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    gap_label = gap.get("gap_label", "")

    if not api_key:
        return _normalize(_load_fallback(gap_label), source="fallback")

    user_content = (
        f"Gap: {gap_label}\n"
        f"Need: {gap.get('need_description', '')}\n"
        f"Affects: {', '.join(gap.get('affected_companies', []))}\n"
        f"Suggested sector: {gap.get('suggested_sector', '')}\n"
        f"Suggested stage: {gap.get('suggested_stage', '')}\n"
        f"Estimated spend: {gap.get('estimated_annual_spend', '')}\n\n"
        f"Search for 3-5 real companies that could fill this gap for MENA-based startups."
    )

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            system=GAP_HUNTER_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )

        # Extract the last text block from the response
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text = block.text

        data = _extract_json(text)
        companies = data.get("companies", [])

        if companies:
            return _normalize(companies, source="web")

        # Web search returned no usable JSON — fall back
        return _normalize(_load_fallback(gap_label), source="fallback")

    except Exception:
        return _normalize(_load_fallback(gap_label), source="fallback")
