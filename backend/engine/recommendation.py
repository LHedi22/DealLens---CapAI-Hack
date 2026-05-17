def generate_verdict(aggregated: dict) -> dict:
    score = aggregated["final_score"]
    force_pass = aggregated.get("force_pass", False)
    mandate_breaches = aggregated.get("mandate_breaches", [])

    if force_pass:
        verdict = "pass"
        verdict_label = "PASS"
        verdict_reason = f"This startup does not meet your fund mandate. {' '.join(mandate_breaches)}"
    elif score >= 75:
        verdict = "pursue"
        verdict_label = "PURSUE"
        verdict_reason = "Strong fundamentals across business and ESG dimensions. Recommend advancing to due diligence."
    elif score >= 60:
        verdict = "watch"
        verdict_label = "WATCH"
        verdict_reason = "Promising opportunity with some gaps. Request additional information before committing."
    elif score >= 45:
        verdict = "soft_pass"
        verdict_label = "SOFT PASS"
        verdict_reason = "Significant concerns identified. Would need material improvements to reconsider."
    else:
        verdict = "pass"
        verdict_label = "PASS"
        verdict_reason = "Does not meet minimum investment criteria at this stage."

    return {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "mandate_breaches": mandate_breaches
    }
