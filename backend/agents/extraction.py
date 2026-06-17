from .ollama_client import call_ollama, MODEL_A
from backend.debug_state import emit_log, step_started, step_completed, step_failed, pipeline_state

EXTRACTION_SYSTEM_PROMPT = """You are a document analysis AI for startup investment screening.
Extract structured information from startup pitch documents.

Return ONLY a valid JSON object with these exact keys. Use null if information is not found.
Do not invent or guess information. Only extract what is explicitly stated.

{
  "founder_names": [],
  "team_size": null,
  "domain_expertise": null,
  "prior_exits": false,
  "team_completeness": null,
  "advisors_named": false,
  "tam_stated": null,
  "tam_source": null,
  "growth_rate": null,
  "revenue_model": null,
  "current_revenue": null,
  "projected_revenue_y1": null,
  "unit_economics": null,
  "revenue_type": null,
  "user_count": null,
  "customer_count": null,
  "traction_evidence": null,
  "competitors_named": [],
  "differentiation": null,
  "ip_mentioned": false,
  "labor_model": null,
  "env_claims": [],
  "governance_docs": false,
  "board_named": false,
  "diversity_claimed": false,
  "funding_ask": null,
  "inconsistencies": []
}

Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""

_DEFAULTS = {
    "founder_names": [],
    "team_size": None,
    "domain_expertise": None,
    "prior_exits": False,
    "team_completeness": None,
    "advisors_named": False,
    "tam_stated": None,
    "tam_source": None,
    "growth_rate": None,
    "revenue_model": None,
    "current_revenue": None,
    "projected_revenue_y1": None,
    "unit_economics": None,
    "revenue_type": None,
    "user_count": None,
    "customer_count": None,
    "traction_evidence": None,
    "competitors_named": [],
    "differentiation": None,
    "ip_mentioned": False,
    "labor_model": None,
    "env_claims": [],
    "governance_docs": False,
    "board_named": False,
    "diversity_claimed": False,
    "funding_ask": None,
    "inconsistencies": []
}


async def run_extraction(document_text: str) -> dict:
    step_started("extraction")
    emit_log("DEBUG", "extraction_agent", "Raw text extracted", {
        "char_count": len(document_text),
        "text_preview": document_text[:500],
    })
    # store raw text in pipeline_state for the trace view
    try:
        pipeline_state["raw_text"] = document_text[:10000]
    except Exception:
        pass

    try:
        if not document_text.strip():
            result = _empty_extraction()
            step_completed("extraction", "Empty document — no text extracted")
            return result

        raw = await call_ollama(
            model=MODEL_A,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_content=f"Extract all structured information from these startup documents:\n\n{document_text[:6000]}",
            agent="extraction",
        )

        if not raw:
            raise RuntimeError(
                "Extraction failed: Ollama returned no structured data. "
                "The model may be overloaded or the request timed out. "
                "Try uploading fewer files or waiting a moment before retrying."
            )

        extracted = _normalize(raw)
        completeness = _compute_completeness(extracted)
        confidence = _compute_confidence(completeness, extracted.get("inconsistencies", []))
        blind_spots = _generate_blind_spots(extracted)

        step_completed("extraction", f"Completeness: {completeness}% | Confidence: {confidence}")
        return {
            "extracted": extracted,
            "data_completeness": completeness,
            "confidence_level": confidence,
            "blind_spots": blind_spots,
        }
    except Exception as e:
        step_failed("extraction", type(e).__name__, str(e))
        raise


def _normalize(raw: dict) -> dict:
    result = dict(_DEFAULTS)
    for k, v in raw.items():
        if k in _DEFAULTS:
            result[k] = v
    return result


def _compute_completeness(e: dict) -> int:
    score = 0

    # Critical (20 pts each)
    if e.get("founder_names"):
        score += 20
    if e.get("revenue_model"):
        score += 20
    if e.get("tam_stated"):
        score += 20
    if e.get("revenue_type"):
        score += 20

    # Important (5 pts each)
    if e.get("traction_evidence"):
        score += 5
    if e.get("competitors_named"):
        score += 5
    if e.get("projected_revenue_y1") or e.get("current_revenue"):
        score += 5

    # Supporting (~2 pts each)
    if e.get("advisors_named"):
        score += 2
    if e.get("ip_mentioned"):
        score += 2
    if e.get("differentiation"):
        score += 1

    # Penalty for inconsistencies
    score -= len(e.get("inconsistencies", [])) * 10

    return max(0, min(100, score))


def _compute_confidence(completeness: int, inconsistencies: list) -> str:
    if completeness >= 75 and not inconsistencies:
        return "HIGH"
    elif completeness >= 45:
        return "MEDIUM"
    return "LOW"


def _generate_blind_spots(e: dict) -> list:
    blind_spots = []

    if not e.get("founder_names"):
        blind_spots.append({
            "field": "team",
            "risk": "Founder identities and backgrounds are unknown",
            "question": "Can you walk us through each founder's background and why they are the right team for this problem?"
        })
    if not e.get("traction_evidence"):
        blind_spots.append({
            "field": "traction",
            "risk": "No traction evidence — market validation unconfirmed",
            "question": "Do you have any paying customers, signed LOIs, or active pilots today?"
        })
    if not e.get("unit_economics"):
        blind_spots.append({
            "field": "unit_economics",
            "risk": "CAC and LTV unknown — path to profitability unclear",
            "question": "What is your current customer acquisition cost and lifetime value?"
        })
    if not e.get("tam_stated"):
        blind_spots.append({
            "field": "market_size",
            "risk": "Total addressable market not quantified",
            "question": "How did you arrive at your market size estimate, and what is your source?"
        })
    if not e.get("governance_docs") and not e.get("board_named"):
        blind_spots.append({
            "field": "governance",
            "risk": "No governance structure disclosed — investor protections unknown",
            "question": "Do you have a shareholder agreement, board, or advisory structure in place?"
        })
    if not e.get("differentiation"):
        blind_spots.append({
            "field": "competitive_moat",
            "risk": "Competitive differentiation not articulated",
            "question": "What makes your solution defensible against well-funded competitors?"
        })

    return blind_spots


def _empty_extraction() -> dict:
    return {
        "extracted": _normalize({}),
        "data_completeness": 0,
        "confidence_level": "LOW",
        "blind_spots": [{
            "field": "all",
            "risk": "No readable content was extracted from the uploaded documents",
            "question": "Please re-upload the startup documents in PDF, DOCX, or XLSX format."
        }]
    }
