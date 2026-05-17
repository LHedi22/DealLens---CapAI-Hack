import json
from datetime import datetime
from backend.agents.ollama_client import call_ollama, MODEL_A

PROFILE_SYSTEM_PROMPT = """You are an investment analyst building a synergy profile for a portfolio company.
From the startup document below, extract:
- services_offered: what products or services the company provides (list of strings)
- target_customers: who they sell to — be specific (list of strings)
- operational_needs: things they currently buy externally, outsource, or struggle without (list of strings)
- strategic_gaps: capabilities or resources they want but don't have (list of strings)

Return ONLY a valid JSON object with exactly these four keys, each containing an array of strings.
If a field cannot be determined, return an empty array [].
No explanation. No markdown. No backticks."""

_EMPTY_PROFILE = {
    "services_offered": [],
    "target_customers": [],
    "operational_needs": [],
    "strategic_gaps": [],
}


async def extract_synergy_profile(
    document_text: str,
    company_name: str,
    sector: str = None,
    stage: str = None,
    geography: str = None,
    deal_history_id: int = None,
) -> dict:
    """
    Extract a SynergyProfile from raw document text via Ollama.
    Returns a dict ready to be saved as a synergy_profiles row.
    """
    if not document_text.strip():
        return _build_profile_row(
            company_name=company_name,
            sector=sector,
            stage=stage,
            geography=geography,
            deal_history_id=deal_history_id,
            raw={},
        )

    raw = await call_ollama(
        model=MODEL_A,
        system_prompt=PROFILE_SYSTEM_PROMPT,
        user_content=f"Build a synergy profile for this startup:\n\n{document_text[:5000]}",
        agent="synergy_profile_extractor",
    )

    return _build_profile_row(
        company_name=company_name,
        sector=sector,
        stage=stage,
        geography=geography,
        deal_history_id=deal_history_id,
        raw=raw or {},
    )


def _build_profile_row(
    company_name: str,
    raw: dict,
    sector: str = None,
    stage: str = None,
    geography: str = None,
    deal_history_id: int = None,
) -> dict:
    services = raw.get("services_offered", [])
    customers = raw.get("target_customers", [])
    needs = raw.get("operational_needs", [])
    gaps = raw.get("strategic_gaps", [])

    return {
        "company_name": company_name,
        "deal_history_id": deal_history_id,
        "sector": sector,
        "stage": stage,
        "geography": geography,
        "services_offered": json.dumps(services if isinstance(services, list) else []),
        "target_customers": json.dumps(customers if isinstance(customers, list) else []),
        "operational_needs": json.dumps(needs if isinstance(needs, list) else []),
        "strategic_gaps": json.dumps(gaps if isinstance(gaps, list) else []),
        "profile_confidence": _compute_profile_confidence(services, customers, needs, gaps),
        "last_extracted_at": datetime.utcnow().isoformat(),
        "extraction_source": "deal_file",
    }


def _compute_profile_confidence(
    services: list,
    customers: list,
    needs: list,
    gaps: list,
) -> str:
    """
    Determine extraction confidence based on how populated the four profile arrays are.

    Rules from SYNERGY.md:
    - HIGH:   all 4 arrays have >= 2 items each
    - MEDIUM: at least 3 arrays have >= 1 item
    - LOW:    fewer than 3 arrays populated
    """
    arrays = [services, customers, needs, gaps]
    populated = sum(1 for a in arrays if len(a) >= 1)
    rich = sum(1 for a in arrays if len(a) >= 2)
    if rich == 4:
        return "HIGH"
    if populated >= 3:
        return "MEDIUM"
    return "LOW"
