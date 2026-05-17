def aggregate_scores(
    business: dict,
    esg: dict,
    conviction_delta: int = 0,
    mandate: dict = None,
    sector: str = None,
    stage: str = None,
    funding_asked: int = None,
) -> dict:
    business_score = business.get("composite_score", 50)
    esg_composite  = esg.get("composite", 50)

    delta = max(-20, min(20, conviction_delta))
    adjusted_business = max(0, min(100, business_score + delta))
    raw_final = int(adjusted_business * 0.70 + esg_composite * 0.30)

    mandate_breaches = []
    if mandate:
        sector_focus = mandate.get("sector_focus") or []
        stage_pref   = mandate.get("stage_preference") or []
        min_esg      = mandate.get("min_esg_threshold") or 0
        ticket_max   = mandate.get("ticket_size_max")

        if sector_focus and sector and sector not in sector_focus:
            mandate_breaches.append(
                f"Sector '{sector}' is outside your fund's focus ({', '.join(sector_focus)})"
            )
        if stage_pref and stage and stage not in stage_pref:
            mandate_breaches.append(
                f"Stage '{stage}' is outside your fund's preferred stages ({', '.join(stage_pref)})"
            )
        if min_esg > 0 and esg_composite < min_esg:
            mandate_breaches.append(
                f"ESG score {esg_composite} is below fund minimum of {min_esg}"
            )
        if ticket_max and funding_asked and funding_asked > ticket_max * 3:
            mandate_breaches.append(
                f"Funding ask ${funding_asked:,} exceeds 3× your maximum ticket size"
            )

    force_pass  = len(mandate_breaches) > 0
    final_score = 0 if force_pass else raw_final

    return {
        "business_score":    business_score,
        "esg_composite":     esg_composite,
        "conviction_delta":  delta,
        "adjusted_business": adjusted_business,
        "final_score":       final_score,
        "mandate_breaches":  mandate_breaches,
        "force_pass":        force_pass,
    }
