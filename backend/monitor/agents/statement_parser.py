import fitz  # PyMuPDF

from backend.agents.ollama_client import call_ollama, MODEL_A

_SYSTEM_PROMPT = """You are a bank statement analyst.
Extract all outgoing transactions (debits) from the following Tunisian bank statement.
Return ONLY a valid JSON object with these exact keys:
  statement_month (ISO year-month string, e.g. "2024-03"),
  transactions (array of objects: { transaction_date (ISO date YYYY-MM-DD), beneficiary (string), amount_tnd (positive number — outgoing only), memo (string or null) }).
Ignore incoming credits. Ignore balance lines. Ignore headers and footers.
If the document contains no outgoing transactions, return an empty transactions array.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""


def _extract_text(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def _default() -> dict:
    return {"statement_month": None, "transactions": []}


async def parse_statement(content: bytes) -> dict:
    text = _extract_text(content)
    if not text.strip():
        return _default()

    result = await call_ollama(
        MODEL_A,
        _SYSTEM_PROMPT,
        f"Bank statement document:\n\n{text[:6000]}",
        agent="statement_parser",
    )
    if not result:
        return _default()

    return {
        "statement_month": result.get("statement_month"),
        "transactions": result.get("transactions") or [],
    }
