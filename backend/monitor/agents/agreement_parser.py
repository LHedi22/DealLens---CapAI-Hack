import fitz  # PyMuPDF
from docx import Document
import io

from backend.agents.ollama_client import call_ollama, MODEL_A

_SYSTEM_PROMPT = """You are a legal document analyst specializing in Tunisian investment agreements (SICAR framework).
Extract the investment allocation plan from the following document.
Return ONLY a valid JSON object with these exact keys:
  total_committed_tnd (number or null),
  agreement_date (ISO date string YYYY-MM-DD or null),
  agreement_duration_months (integer, default 60 if not stated),
  categories (array of objects: { name (one of: rd/construction/equipment/salaries/working_capital/marketing/training/other), allocated_tnd (number), notes (string or null) }),
  time_milestones (array of objects: { category, must_start_by_month (integer or null), must_complete_by_month (integer or null) } — empty array if none stated).
If a field is not found, use null.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""


def _extract_text_pdf(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def _extract_text_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _default() -> dict:
    return {
        "total_committed_tnd": None,
        "agreement_date": None,
        "agreement_duration_months": 60,
        "categories": [],
        "time_milestones": [],
    }


def _normalize(raw: dict) -> dict:
    result = _default()
    result["total_committed_tnd"] = raw.get("total_committed_tnd")
    result["agreement_date"] = raw.get("agreement_date")
    result["agreement_duration_months"] = int(raw.get("agreement_duration_months") or 60)
    result["categories"] = raw.get("categories") or []
    result["time_milestones"] = raw.get("time_milestones") or []
    return result


async def parse_agreement(content: bytes, filename: str) -> dict:
    fname = filename.lower()
    if fname.endswith(".pdf"):
        text = _extract_text_pdf(content)
    elif fname.endswith((".docx", ".doc")):
        text = _extract_text_docx(content)
    else:
        text = content.decode("utf-8", errors="ignore")

    if not text.strip():
        return _default()

    user_content = f"Investment agreement document:\n\n{text[:6000]}"
    result = await call_ollama(MODEL_A, _SYSTEM_PROMPT, user_content, agent="agreement_parser")

    if not result:
        return _default()

    return _normalize(result)
