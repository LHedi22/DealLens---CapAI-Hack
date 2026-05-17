import json
import os

import httpx

FALLBACK_COMPANIES = {
    "B2B Payment Infrastructure": [
        {
            "company_name": "Flouci",
            "website": "https://flouci.com",
            "description": "Tunisian B2B and consumer payment platform with QR and API solutions for SMEs.",
            "fit_score": 81,
            "fit_reason": "Direct B2B payment API provider already operating in Tunisia — minimal integration complexity.",
            "flags": ["Early stage — limited enterprise client data publicly available"],
            "source_url": "https://flouci.com",
        },
        {
            "company_name": "Konnect",
            "website": "https://konnect.network",
            "description": "MENA payment gateway offering online and in-store payment processing for businesses.",
            "fit_score": 76,
            "fit_reason": "Established MENA footprint and existing Tunisian merchant base reduces onboarding risk.",
            "flags": ["Pricing model not publicly disclosed", "No published SLA data"],
            "source_url": "https://konnect.network",
        },
        {
            "company_name": "Paymee",
            "website": "https://paymee.tn",
            "description": "Tunisian payment solution for e-commerce and B2B invoicing with local bank integrations.",
            "fit_score": 72,
            "fit_reason": "Native Tunisian platform — lowest regulatory and FX complexity for the portfolio.",
            "flags": ["Smaller team — scalability for enterprise volumes unconfirmed"],
            "source_url": "https://paymee.tn",
        },
    ],
    "Last-Mile Medical & Physical Delivery": [
        {
            "company_name": "Labayd",
            "website": "https://labayd.com",
            "description": "Tunisian last-mile logistics startup specializing in e-commerce and SME deliveries.",
            "fit_score": 74,
            "fit_reason": "Existing last-mile network in Tunisia with SME experience — could extend to medical with cold-chain add-on.",
            "flags": ["Cold-chain certification not confirmed", "Medical logistics experience unverified"],
            "source_url": "https://labayd.com",
        },
        {
            "company_name": "Maystro Delivery",
            "website": "https://maystro-delivery.com",
            "description": "Algerian and Tunisian delivery platform with API integration for e-commerce brands.",
            "fit_score": 68,
            "fit_reason": "Multi-country presence and API-first approach suits HealthCore's future MENA expansion.",
            "flags": ["Foreign HQ (Algeria) — cross-border complexity", "Medical supply delivery not in current scope"],
            "source_url": "https://maystro-delivery.com",
        },
        {
            "company_name": "Yassir Express",
            "website": "https://yassir.com",
            "description": "MENA super-app with B2B delivery arm operating in Tunisia and North Africa.",
            "fit_score": 61,
            "fit_reason": "Large fleet and existing Tunisia presence, but primarily consumer-focused — B2B medical pivot needed.",
            "flags": ["Consumer-first platform — B2B SLA unclear", "Cold-chain capability unconfirmed"],
            "source_url": "https://yassir.com",
        },
    ],
    "DEFAULT": [
        {
            "company_name": "Expensya",
            "website": "https://expensya.com",
            "description": "MENA expense management and HR tooling SaaS with Tunisian headquarters.",
            "fit_score": 70,
            "fit_reason": "Directly addresses HR and payroll operational needs across the portfolio.",
            "flags": ["Primarily expense management — full payroll module may require integration"],
            "source_url": "https://expensya.com",
        },
        {
            "company_name": "Rekrute",
            "website": "https://rekrute.com",
            "description": "North African HR platform offering recruitment, payroll, and people management tools.",
            "fit_score": 65,
            "fit_reason": "Regional coverage and existing Tunisian client base aligns with portfolio geography.",
            "flags": ["Morocco-headquartered — local support response times unverified"],
            "source_url": "https://rekrute.com",
        },
        {
            "company_name": "Elyte",
            "website": "https://elyte.io",
            "description": "Tunisian HR and payroll SaaS for SMEs, with compliance reporting features.",
            "fit_score": 60,
            "fit_reason": "Local compliance expertise and SME focus matches BuildSmart and CargoZip operational profiles.",
            "flags": ["Early stage — enterprise feature set still maturing"],
            "source_url": "https://elyte.io",
        },
    ],
}


async def hunt_gap(gap: dict) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    gap_label = gap.get("gap_label", "DEFAULT")

    prompt = (
        f'You are an investment sourcing analyst for a PE fund focused on Tunisia and MENA.\n'
        f'A portfolio company has this unmet need: "{gap.get("need_description", "")}"\n'
        f'Affected companies: {gap.get("affected_companies", [])}\n'
        f'Suggested sector: {gap.get("suggested_sector", "not specified")}\n'
        f'Estimated annual spend: {gap.get("estimated_annual_spend", "unknown")}\n\n'
        f'Search for 3 to 5 real startups or SMEs that could fill this need.\n'
        f'For each company return:\n'
        f'- company_name\n'
        f'- website\n'
        f'- description (one sentence, factual)\n'
        f'- fit_score (0–100, how well it fills the stated need)\n'
        f'- fit_reason (one sentence explaining the score)\n'
        f'- flags (JSON array of warning strings)\n'
        f'- source_url (the URL where you found this information)\n\n'
        f'Prioritize companies active in Tunisia or MENA, recently funded (Seed to Series A), '
        f'and verifiable with a real web presence.\n\n'
        f'Return ONLY a valid JSON array of company objects. No explanation. No markdown. No backticks.'
    )

    if not api_key:
        return _fallback(gap_label)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type":    "application/json",
                    "x-api-key":       api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model":      "claude-sonnet-4-5-20251001",
                    "max_tokens": 1024,
                    "tools":      [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages":   [{"role": "user", "content": prompt}],
                },
            )

        data = response.json()
        text = "".join(
            b["text"] for b in data.get("content", []) if b.get("type") == "text"
        )
        clean   = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        results = json.loads(clean)

        if not isinstance(results, list) or len(results) < 3:
            raise ValueError("Too few or malformed results")

        return results[:5]

    except Exception as e:
        print(f"[gap_hunter] API failed ({e}) — using fallback.")
        return _fallback(gap_label)


def _fallback(gap_label: str) -> list[dict]:
    return FALLBACK_COMPANIES.get(gap_label, FALLBACK_COMPANIES["DEFAULT"])
