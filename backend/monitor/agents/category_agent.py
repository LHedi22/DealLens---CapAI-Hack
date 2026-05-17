import asyncio

from backend.agents.ollama_client import call_ollama, MODEL_A

# Keyword library — never call Ollama for this, match in-process
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "rd": ["recherche", "développement", "r&d", "laboratoire", "brevet", "prototype",
           "université", "bureau d'études", "ingénierie", "innovation", "test", "analyse"],
    "construction": ["construction", "génie civil", "travaux", "bâtiment", "maçonnerie",
                     "entrepreneur", "chantier", "fondation", "rénovation", "aménagement"],
    "equipment": ["équipement", "matériel", "machine", "leasing", "location financière",
                  "achat matériel", "mobilier", "informatique", "serveur", "véhicule"],
    "salaries": ["salaire", "rémunération", "cnss", "irpp", "paie", "personnel",
                 "virement salaire", "traitement", "charges sociales"],
    "working_capital": ["fournisseur", "matière première", "stock", "approvisionnement",
                        "achat marchandise", "crédit fournisseur"],
    "marketing": ["publicité", "marketing", "communication", "salon", "foire", "impression",
                  "agence", "média", "réseaux sociaux"],
    "training": ["formation", "séminaire", "conférence", "certification", "coaching",
                 "renforcement capacités"],
}

_VALID_CATEGORIES = set(CATEGORY_KEYWORDS.keys()) | {"other"}

_SYSTEM_PROMPT = """You are a compliance analyst for Tunisian SICAR investment agreements.
Classify the following bank transaction into the most appropriate spending category.
Agreement categories available: rd, construction, equipment, salaries, working_capital, marketing, training, other.
Return ONLY a valid JSON object with these exact keys:
  category (string — one of the categories listed above),
  confidence (float between 0.0 and 1.0),
  reasoning_note (string — one sentence explaining your classification).
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""

# Confidence ≥ this threshold → AUTO_CLASSIFIED, else UNCLASSIFIED
CONFIDENCE_THRESHOLD = 0.80


def _keyword_score(beneficiary: str, memo: str | None) -> list[tuple[str, int]]:
    """Return (category, hit_count) pairs sorted descending, only non-zero."""
    text = f"{beneficiary} {memo or ''}".lower()
    scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in CATEGORY_KEYWORDS.items()}
    return sorted(((c, s) for c, s in scores.items() if s > 0), key=lambda x: -x[1])


def _keyword_classify(beneficiary: str, memo: str | None) -> tuple[str | None, float, list[tuple[str, int]]]:
    """
    Returns (category, confidence, ranked_candidates).
    Confidence < CONFIDENCE_THRESHOLD means the LLM should be called.
    """
    ranked = _keyword_score(beneficiary, memo)
    if not ranked:
        return None, 0.0, []

    top_cat, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    # Clear winner: top category has at least 2 hits and at least 2x the runner-up
    if top_score >= 2 and (second_score == 0 or top_score >= 2 * second_score):
        conf = round(min(0.97, 0.87 + 0.03 * top_score), 2)
        return top_cat, conf, ranked

    # Sole keyword match with no competition
    if top_score == 1 and second_score == 0:
        return top_cat, 0.82, ranked

    # Ambiguous — LLM resolves
    return top_cat, 0.55, ranked


async def _llm_classify(
    beneficiary: str,
    amount: float,
    memo: str | None,
    candidates: list[tuple[str, int]],
) -> dict:
    if candidates:
        total = sum(s for _, s in candidates)
        c1, s1 = candidates[0]
        c2, s2 = candidates[1] if len(candidates) > 1 else (c1, 0)
        c1_pct = int(s1 / max(total, 1) * 100)
        c2_pct = int(s2 / max(total, 1) * 100)
        candidate_str = f"{c1} ({c1_pct}%), {c2} ({c2_pct}%)"
    else:
        candidate_str = "none matched"

    user = (
        f'Transaction: beneficiary = "{beneficiary}", '
        f'amount = {amount} TND, memo = "{memo or ""}".\n'
        f"Top candidate categories from keyword matching: {candidate_str}."
    )
    result = await call_ollama(MODEL_A, _SYSTEM_PROMPT, user, agent="category_agent")
    if not result:
        return {"category": None, "confidence": 0.0, "reasoning_note": "LLM unavailable."}

    cat = result.get("category")
    if cat not in _VALID_CATEGORIES:
        cat = None
    conf = round(float(result.get("confidence") or 0.0), 2)
    note = result.get("reasoning_note") or ""
    return {"category": cat, "confidence": conf, "reasoning_note": note}


async def classify_transaction(beneficiary: str, amount: float, memo: str | None) -> dict:
    """
    Two-stage classifier. Returns dict with:
      category, confidence, reasoning_note, classification_status
    """
    top_cat, conf, ranked = _keyword_classify(beneficiary, memo)

    if conf >= CONFIDENCE_THRESHOLD:
        return {
            "category": top_cat,
            "confidence": conf,
            "reasoning_note": f"Keyword match: {top_cat}.",
            "classification_status": "AUTO_CLASSIFIED",
        }

    # Call LLM to resolve ambiguity
    llm = await _llm_classify(beneficiary, amount, memo, ranked)
    final_conf = llm["confidence"]
    final_cat = llm["category"]

    if final_conf >= CONFIDENCE_THRESHOLD and final_cat:
        return {
            "category": final_cat,
            "confidence": final_conf,
            "reasoning_note": llm["reasoning_note"],
            "classification_status": "AUTO_CLASSIFIED",
        }

    return {
        "category": final_cat,
        "confidence": final_conf,
        "reasoning_note": llm["reasoning_note"],
        "classification_status": "UNCLASSIFIED",
    }


async def classify_batch(transactions: list[dict]) -> list[dict]:
    """Classify all transactions in parallel. Never raises — exceptions become UNCLASSIFIED."""
    _safe_default = {"category": None, "confidence": 0.0, "reasoning_note": "Error.", "classification_status": "UNCLASSIFIED"}

    results = await asyncio.gather(
        *[
            classify_transaction(
                tx.get("beneficiary", ""),
                float(tx.get("amount_tnd") or 0),
                tx.get("memo"),
            )
            for tx in transactions
        ],
        return_exceptions=True,
    )
    return [r if isinstance(r, dict) else _safe_default for r in results]
