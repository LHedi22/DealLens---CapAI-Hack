"""
compliance_agent.py — Pure Python compliance computation (no LLM, no DB).

compute_compliance : all transactions + plan_map → category_totals + variance data
"""


def _effective_category(tx) -> str | None:
    return tx.human_category if tx.human_category else tx.ai_category


def compute_compliance(
    all_txs: list,
    plan_map: dict[str, float],
    months_elapsed: int,
    duration: int = 60,
) -> dict:
    """
    Compute per-category compliance from all transactions.

    Returns:
        category_totals : { cat: { planned_tnd, spent_tnd, planned_to_date_tnd, variance_pct, status } }
        total_spent     : float
        total_planned_to_date : float
        unclassified_tnd : float
        spent_map       : { cat: float }  (needed by anomaly agent)
    """
    spent_map: dict[str, float] = {}
    unclassified_tnd = 0.0
    total_spent = 0.0

    for tx in all_txs:
        amount = tx.amount_tnd or 0.0
        total_spent += amount
        if tx.classification_status == "UNCLASSIFIED":
            unclassified_tnd += amount
            continue
        cat = _effective_category(tx)
        if cat:
            spent_map[cat] = spent_map.get(cat, 0.0) + amount

    all_cats = set(plan_map.keys()) | set(spent_map.keys())
    category_totals: dict = {}

    for cat in all_cats:
        planned_tnd = plan_map.get(cat, 0.0)
        spent_tnd = spent_map.get(cat, 0.0)

        if planned_tnd == 0 and spent_tnd > 0:
            category_totals[cat] = {
                "planned_tnd": 0.0,
                "spent_tnd": round(spent_tnd, 2),
                "planned_to_date_tnd": 0.0,
                "variance_pct": None,
                "status": "OFF_PLAN",
            }
            continue

        planned_to_date = (months_elapsed / duration) * planned_tnd if planned_tnd > 0 else 0.0

        if planned_to_date == 0:
            variance_pct = 0.0
            status = "ON_TRACK"
        else:
            variance_pct = round(((spent_tnd - planned_to_date) / planned_to_date) * 100, 2)
            if spent_tnd > planned_tnd:
                status = "OVER_BUDGET"
            elif abs(variance_pct) <= 15:
                status = "ON_TRACK"
            elif abs(variance_pct) <= 30:
                status = "WARNING"
            else:
                status = "CRITICAL"

        category_totals[cat] = {
            "planned_tnd": planned_tnd,
            "spent_tnd": round(spent_tnd, 2),
            "planned_to_date_tnd": round(planned_to_date, 2),
            "variance_pct": variance_pct,
            "status": status,
        }

    total_planned_to_date = sum((months_elapsed / duration) * v for v in plan_map.values())

    return {
        "category_totals": category_totals,
        "total_spent": round(total_spent, 2),
        "total_planned_to_date": round(total_planned_to_date, 2),
        "unclassified_tnd": round(unclassified_tnd, 2),
        "spent_map": spent_map,
    }


def compute_health_score(
    category_totals: dict,
    unclassified_tnd: float,
    total_spent: float,
    active_alert_count: int,
) -> int:
    score = 100
    for data in category_totals.values():
        status = data.get("status", "ON_TRACK")
        if status == "OVER_BUDGET":
            score -= 25
        elif status == "CRITICAL":
            score -= 20
        elif status == "WARNING":
            score -= 10
    score -= active_alert_count * 5
    if total_spent > 0 and unclassified_tnd / total_spent > 0.10:
        score -= 10
    return max(0, score)
