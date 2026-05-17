"""
anomaly_agent.py — Detect compliance anomalies and generate LLM explanations.

detect_anomalies : new_txs + all_txs + compliance state → list of anomaly dicts
"""

import asyncio
import json

from backend.agents.ollama_client import call_ollama, MODEL_A


# ── Static fallback text (used when LLM is unavailable) ───────────────────────

def _static_summary(a: dict) -> str:
    atype = a.get("alert_type", "")
    amount = a.get("amount") or 0
    ben = a.get("beneficiary") or "unknown beneficiary"
    cat = a.get("category") or "unknown"

    if atype == "OFF_PLAN":
        return f"Payment of {amount:,.0f} TND to '{ben}' classified as '{cat}' — this category has no allocation in the signed agreement."
    if atype == "OVER_BUDGET":
        return f"Category '{cat}' cumulative spending has exceeded its total agreed allocation."
    if atype == "LARGE_UNKNOWN":
        return f"Large unclassified payment of {amount:,.0f} TND to '{ben}' could not be automatically categorised."
    if atype == "REPEATED_UNCLASSIFIED":
        return f"Beneficiary '{ben}' appears 3 or more times with unclassified status — pattern warrants review."
    if atype == "ROUND_LARGE":
        return f"Round-number payment of {amount:,.0f} TND to '{ben}' may represent a transfer rather than a purchase."
    if atype == "PACE_WARNING":
        months = a.get("months_remaining", "?")
        return f"Category '{cat}' is significantly underspent with only {months} months remaining in the agreement."
    return "Compliance anomaly detected."


def _static_detail(a: dict) -> str:
    atype = a.get("alert_type", "")
    cat = a.get("category") or "this category"

    if atype == "OFF_PLAN":
        return (
            f"The signed SICAR agreement does not allocate any funds to '{cat}'. "
            "If this expenditure is confirmed, it may constitute a compliance breach subject to government audit. "
            "Request an invoice and written justification from the startup immediately."
        )
    if atype == "OVER_BUDGET":
        return (
            f"Total spending in '{cat}' has exceeded the amount permitted by the investment agreement. "
            "Excess spending is a direct SICAR compliance violation and will be flagged at the year-5 audit. "
            "No further spending in this category should be approved until a formal amendment is signed."
        )
    if atype == "LARGE_UNKNOWN":
        return (
            "This transaction could not be matched to any agreement category with sufficient confidence. "
            "A payment of this size without a clear classification represents a potential off-plan expenditure. "
            "Request documentary evidence (invoice, contract) and manually classify before the next statement cycle."
        )
    if atype == "REPEATED_UNCLASSIFIED":
        return (
            "Multiple payments to the same beneficiary remain unclassified. "
            "This pattern may indicate a recurring off-plan expense or an entity not anticipated in the agreement. "
            "Review all transactions from this beneficiary and assign a category or escalate to audit."
        )
    if atype == "ROUND_LARGE":
        return (
            "Large round-number payments are sometimes indicators of inter-company transfers, loans, or off-agreement transactions. "
            "Verify that this payment corresponds to a legitimate invoice covered by the signed agreement. "
            "Request supporting documentation if not already on file."
        )
    if atype == "PACE_WARNING":
        return (
            f"With few months remaining, '{cat}' spending is far below the agreed plan. "
            "The SICAR government auditor may view significantly unspent allocated funds as non-fulfilment of the investment commitment. "
            "Accelerate spending in this category or prepare a written justification for the shortfall."
        )
    return "Review this anomaly with the startup and document any resolution for the audit file."


# ── LLM explanation generator ─────────────────────────────────────────────────

_EXPLAIN_SYSTEM = """You are a SICAR compliance analyst writing alerts for a Tunisian PE fund.
Given an anomaly in a startup's spending, generate:
  alert_summary : one clear sentence (plain language, no jargon)
  alert_detail  : 2-3 sentences explaining the compliance risk and what the PE should do
Return ONLY a valid JSON object with keys: alert_summary, alert_detail.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""


async def _generate_explanation(anomaly: dict) -> dict:
    safe = {k: v for k, v in anomaly.items() if k not in ("transaction_id",)}
    result = await call_ollama(
        MODEL_A, _EXPLAIN_SYSTEM,
        f"Anomaly:\n{json.dumps(safe, ensure_ascii=False)}",
        agent="anomaly_agent",
    )
    return {
        "alert_summary": result.get("alert_summary") or _static_summary(anomaly),
        "alert_detail":  result.get("alert_detail")  or _static_detail(anomaly),
    }


# ── Main detector ─────────────────────────────────────────────────────────────

async def detect_anomalies(
    new_txs: list,
    all_txs: list,
    plan_map: dict[str, float],
    compliance: dict,
    months_elapsed: int,
    duration: int = 60,
) -> list[dict]:
    """
    Check all anomaly types and return a list of anomaly dicts ready for fire_alerts().
    tx-level anomalies are checked on new_txs only (alert_engine dedup covers re-uploads).
    category-level anomalies are checked on the full compliance state.
    """
    raw: list[dict] = []

    # Pre-compute beneficiary → UNCLASSIFIED count across ALL transactions (for REPEATED_UNCLASSIFIED)
    beneficiary_unclassified: dict[str, int] = {}
    for tx in all_txs:
        if tx.classification_status == "UNCLASSIFIED":
            key = (tx.beneficiary or "").strip().lower()
            if key:
                beneficiary_unclassified[key] = beneficiary_unclassified.get(key, 0) + 1

    # ── Transaction-level checks (new_txs only) ────────────────────────────────
    for tx in new_txs:
        amount = tx.amount_tnd or 0.0
        cat = tx.human_category or tx.ai_category

        # OFF_PLAN: classified into a category with zero allocation
        if tx.classification_status in ("AUTO_CLASSIFIED", "HUMAN_VERIFIED") and cat:
            if plan_map.get(cat, 0.0) == 0:
                raw.append({
                    "transaction_id": tx.id,
                    "alert_type": "OFF_PLAN",
                    "severity": "CRITICAL",
                    "amount": amount,
                    "beneficiary": tx.beneficiary,
                    "category": cat,
                    "memo": tx.memo,
                })
                continue  # stop at first match per transaction

        # LARGE_UNKNOWN: unclassified AND large amount
        if tx.classification_status == "UNCLASSIFIED" and amount > 20_000:
            raw.append({
                "transaction_id": tx.id,
                "alert_type": "LARGE_UNKNOWN",
                "severity": "WARNING",
                "amount": amount,
                "beneficiary": tx.beneficiary,
                "category": None,
                "memo": tx.memo,
            })
            continue

        # ROUND_LARGE: ≥ 50,000 TND and no fractional millimes (round to nearest 1,000)
        if amount >= 50_000 and (amount % 1_000) < 0.001:
            raw.append({
                "transaction_id": tx.id,
                "alert_type": "ROUND_LARGE",
                "severity": "WARNING",
                "amount": amount,
                "beneficiary": tx.beneficiary,
                "category": cat,
                "memo": tx.memo,
            })

    # ── Beneficiary-level: REPEATED_UNCLASSIFIED ──────────────────────────────
    already_flagged: set[str] = set()
    for tx in new_txs:
        key = (tx.beneficiary or "").strip().lower()
        if key and key not in already_flagged and beneficiary_unclassified.get(key, 0) >= 3:
            already_flagged.add(key)
            raw.append({
                "transaction_id": None,
                "alert_type": "REPEATED_UNCLASSIFIED",
                "severity": "WARNING",
                "beneficiary": tx.beneficiary,
                "amount": None,
                "category": None,
                "memo": None,
            })

    # ── Category-level checks (full compliance state) ─────────────────────────
    category_totals = compliance.get("category_totals", {})
    spent_map = compliance.get("spent_map", {})

    for cat, data in category_totals.items():
        if data.get("status") == "OVER_BUDGET":
            raw.append({
                "transaction_id": None,
                "alert_type": "OVER_BUDGET",
                "severity": "CRITICAL",
                "category": cat,
                "amount": data.get("spent_tnd"),
                "planned_tnd": data.get("planned_tnd"),
                "beneficiary": None,
                "memo": None,
            })

    # PACE_WARNING: < 12 months remaining AND underspent > 20% of allocation
    months_remaining = duration - months_elapsed
    if months_remaining < 12:
        for cat, allocated in plan_map.items():
            spent = spent_map.get(cat, 0.0)
            if allocated > 0 and (allocated - spent) / allocated > 0.20:
                raw.append({
                    "transaction_id": None,
                    "alert_type": "PACE_WARNING",
                    "severity": "WARNING",
                    "category": cat,
                    "amount": round(allocated - spent, 2),
                    "planned_tnd": allocated,
                    "beneficiary": None,
                    "memo": None,
                    "months_remaining": months_remaining,
                })

    if not raw:
        return []

    # Generate LLM explanations in parallel; fall back to static text on any failure
    explanations = await asyncio.gather(
        *[_generate_explanation(a) for a in raw],
        return_exceptions=True,
    )

    results = []
    for anomaly, explanation in zip(raw, explanations):
        if isinstance(explanation, dict):
            anomaly["alert_summary"] = explanation.get("alert_summary") or _static_summary(anomaly)
            anomaly["alert_detail"]  = explanation.get("alert_detail")  or _static_detail(anomaly)
        else:
            anomaly["alert_summary"] = _static_summary(anomaly)
            anomaly["alert_detail"]  = _static_detail(anomaly)
        results.append(anomaly)

    return results
