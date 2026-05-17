from backend.agents.ollama_client import call_ollama, MODEL_B
from backend.debug_state import step_started, step_completed, step_failed

KNOWN_FIXES = {
    "no_commercial_cofounder": {
        "label": "No commercial co-founder or sales lead",
        "fix_score": 4,
        "score_impact": 8,
        "time_months": 2,
        "owner": "Founder (with investor network support)",
        "action": "Hire or appoint a commercial co-founder or VP Sales within 60 days",
        "closing_condition": True,
    },
    "no_board_governance": {
        "label": "No board or governance structure",
        "fix_score": 5,
        "score_impact": 5,
        "time_months": 1,
        "owner": "Founder + legal counsel",
        "action": "Appoint 2 independent advisors and draft a shareholder agreement",
        "closing_condition": True,
    },
    "no_paying_customers": {
        "label": "No paying customers or signed LOIs",
        "fix_score": 3,
        "score_impact": 6,
        "time_months": 3,
        "owner": "Founder",
        "action": "Convert at least 1 active pilot to a paid contract",
        "closing_condition": False,
    },
    "no_unit_economics": {
        "label": "Unit economics not defined (CAC/LTV unknown)",
        "fix_score": 4,
        "score_impact": 4,
        "time_months": 1,
        "owner": "Founder + CFO or finance advisor",
        "action": "Define and document CAC, LTV, and payback period with real data",
        "closing_condition": True,
    },
    "no_market_sizing": {
        "label": "Market size not quantified with a credible source",
        "fix_score": 5,
        "score_impact": 3,
        "time_months": 0.5,
        "owner": "Founder",
        "action": "Commission or cite a credible third-party market report for TAM/SAM",
        "closing_condition": False,
    },
    "no_ip_or_moat": {
        "label": "No IP, patent, or articulated competitive moat",
        "fix_score": 2,
        "score_impact": 4,
        "time_months": 6,
        "owner": "Founder + IP counsel",
        "action": "File provisional patent or document proprietary data/network advantage",
        "closing_condition": False,
    },
    "weak_team_balance": {
        "label": "Founding team lacks technical or commercial balance",
        "fix_score": 3,
        "score_impact": 6,
        "time_months": 3,
        "owner": "Founder (with investor support)",
        "action": "Recruit missing co-founder or senior hire to balance team skills",
        "closing_condition": False,
    },
    "esg_privacy_policy": {
        "label": "No privacy policy or data consent mechanism (RF-01)",
        "fix_score": 5,
        "score_impact": 3,
        "time_months": 0.25,
        "owner": "Founder + legal counsel",
        "action": "Publish a GDPR-compliant privacy policy and consent flow",
        "closing_condition": True,
    },
    "esg_governance_veto": {
        "label": "Founder unilateral veto rights over board (RF-03)",
        "fix_score": 3,
        "score_impact": 5,
        "time_months": 2,
        "owner": "Founder + legal counsel",
        "action": "Restructure governance documents to remove unilateral veto rights",
        "closing_condition": True,
    },
    "esg_no_board": {
        "label": "Solo founder with no board or advisors (RF-09)",
        "fix_score": 5,
        "score_impact": 4,
        "time_months": 1,
        "owner": "Founder",
        "action": "Appoint at least 2 independent advisors with named roles and bios",
        "closing_condition": True,
    },
    "esg_env_claims": {
        "label": "Unverified environmental claims (RF-04)",
        "fix_score": 4,
        "score_impact": 3,
        "time_months": 2,
        "owner": "Founder + sustainability advisor",
        "action": "Provide third-party verification or remove unsubstantiated claims",
        "closing_condition": False,
    },
}

STRUCTURAL_PROBLEMS = {
    "market_too_small": {
        "label": "Market appears structurally too small to support VC returns",
        "severity": "high",
        "why_unfixable": "TAM ceiling limits return potential regardless of execution quality",
    },
    "gig_labor_regulatory": {
        "label": "Gig labor model faces high regulatory risk (RF-02)",
        "severity": "high",
        "why_unfixable": "EU and emerging market labor law trends make gig-only models increasingly non-viable",
    },
}

_FIX_ACTION_SYSTEM = """You are an investment advisor helping a fund decide whether to invest
in a startup with identified fixable problems.
For each problem listed, write a specific, actionable, one-sentence instruction
for the founding team.
The action must be concrete — name what to do, how, and roughly when.

Return ONLY a valid JSON object:
{
  "actions": [
    {"problem_key": "...", "action_text": "specific instruction"},
    ...
  ]
}

Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""


async def run_fix_analysis(
    business_result: dict,
    esg_result: dict,
    extracted: dict,
    final_score: int,
    blind_spots: list,
) -> dict:
    step_started("fix_analysis")
    try:
        return await _run_fix_inner(business_result, esg_result, extracted, final_score, blind_spots)
    except Exception as e:
        step_failed("fix_analysis", type(e).__name__, str(e))
        raise


async def _run_fix_inner(
    business_result: dict,
    esg_result: dict,
    extracted: dict,
    final_score: int,
    blind_spots: list,
) -> dict:
    problems = _identify_problems(business_result, esg_result, extracted, blind_spots)

    fixable = [p for p in problems if p["fix_score"] >= 2]
    structural = [p for p in problems if p["fix_score"] == 1]

    def priority_score(p):
        severity = p.get("score_impact", 3)
        fix_s = p.get("fix_score", 3)
        time = max(0.25, p.get("time_months", 2))
        return (severity * fix_s) / time

    fixable.sort(key=priority_score, reverse=True)
    top_3 = fixable[:3]

    if top_3:
        top_3 = await _enrich_action_text(top_3)

    top_3_delta = sum(p.get("score_impact", 0) for p in top_3)
    conditional_score = min(100, final_score + top_3_delta)

    verdict = _compute_fix_verdict(final_score, conditional_score, structural, top_3)

    result = {
        "problems_found": len(problems),
        "fixable_problems": fixable,
        "structural_problems": structural,
        "top_priority_actions": top_3,
        "current_score": final_score,
        "conditional_score": conditional_score,
        "score_gap": conditional_score - final_score,
        "fix_verdict": verdict["verdict"],
        "fix_verdict_label": verdict["label"],
        "fix_verdict_description": verdict["description"],
    }
    step_completed("fix_analysis", f"Verdict: {verdict['label']} | {final_score} → {conditional_score}")
    return result


def _identify_problems(
    business_result: dict,
    esg_result: dict,
    extracted: dict,
    blind_spots: list,
) -> list:
    problems = []

    dim_scores = {
        "team":        business_result.get("team_score", 50),
        "market":      business_result.get("market_score", 50),
        "revenue":     business_result.get("revenue_score", 50),
        "traction":    business_result.get("traction_score", 50),
        "moat":        business_result.get("moat_score", 50),
        "scalability": business_result.get("scalability_score", 50),
    }

    if dim_scores["team"] < 50:
        tc = (extracted.get("team_completeness") or "").lower()
        if "technical" in tc:
            problems.append({**KNOWN_FIXES["no_commercial_cofounder"], "key": "no_commercial_cofounder"})
        else:
            problems.append({**KNOWN_FIXES["weak_team_balance"], "key": "weak_team_balance"})

    if dim_scores["traction"] < 50:
        problems.append({**KNOWN_FIXES["no_paying_customers"], "key": "no_paying_customers"})

    if dim_scores["market"] < 50 and not extracted.get("tam_stated"):
        problems.append({**KNOWN_FIXES["no_market_sizing"], "key": "no_market_sizing"})

    if dim_scores["revenue"] < 50 and not extracted.get("unit_economics"):
        problems.append({**KNOWN_FIXES["no_unit_economics"], "key": "no_unit_economics"})

    if dim_scores["moat"] < 40:
        problems.append({**KNOWN_FIXES["no_ip_or_moat"], "key": "no_ip_or_moat"})

    red_flags = esg_result.get("red_flags_triggered", [])

    if "RF-01" in red_flags:
        problems.append({**KNOWN_FIXES["esg_privacy_policy"], "key": "esg_privacy_policy"})
    if "RF-03" in red_flags:
        problems.append({**KNOWN_FIXES["esg_governance_veto"], "key": "esg_governance_veto"})
    if "RF-09" in red_flags:
        existing_keys = {p.get("key") for p in problems}
        if "no_board_governance" not in existing_keys:
            problems.append({**KNOWN_FIXES["esg_no_board"], "key": "esg_no_board"})
    if "RF-04" in red_flags:
        problems.append({**KNOWN_FIXES["esg_env_claims"], "key": "esg_env_claims"})

    if not extracted.get("governance_docs") and not extracted.get("board_named"):
        existing_keys = {p.get("key") for p in problems}
        if "no_board_governance" not in existing_keys and "esg_no_board" not in existing_keys:
            problems.append({**KNOWN_FIXES["no_board_governance"], "key": "no_board_governance"})

    labor = (extracted.get("labor_model") or "").lower()
    if "gig" in labor and "RF-02" in red_flags:
        problems.append({
            **STRUCTURAL_PROBLEMS["gig_labor_regulatory"],
            "key": "gig_labor_regulatory",
            "fix_score": 1,
            "score_impact": 0,
            "time_months": 999,
        })

    # Deduplicate by key
    seen = set()
    unique = []
    for p in problems:
        k = p.get("key", p.get("label"))
        if k not in seen:
            seen.add(k)
            unique.append(p)

    return unique


async def _enrich_action_text(problems: list) -> list:
    problem_list = "\n".join(
        f"- key: {p.get('key')}, label: {p.get('label')}"
        for p in problems
    )

    raw = await call_ollama(
        MODEL_B,
        _FIX_ACTION_SYSTEM,
        f"Generate specific action instructions for these startup problems:\n{problem_list}",
        agent="fix_analysis",
    )

    if raw and "actions" in raw:
        action_map = {a["problem_key"]: a["action_text"] for a in raw.get("actions", [])}
        for p in problems:
            key = p.get("key")
            if key in action_map:
                p["action"] = action_map[key]

    return problems


def _compute_fix_verdict(
    final_score: int,
    conditional_score: int,
    structural: list,
    top_3: list,
) -> dict:
    high_severity_structural = [s for s in structural if s.get("severity") == "high"]
    if high_severity_structural:
        return {
            "verdict": "structural_pass",
            "label": "STRUCTURAL PASS",
            "description": (
                "One or more problems are not fixable within the investment horizon. "
                "The business model has a structural constraint that limits return potential."
            ),
        }

    closing_conditions = [p for p in top_3 if p.get("closing_condition")]

    if conditional_score >= 75:
        if closing_conditions:
            return {
                "verdict": "condition",
                "label": "CONDITION INVESTMENT",
                "description": (
                    f"Strong potential: conditional score of {conditional_score} reaches Pursue territory. "
                    f"Investment should be conditional on {len(closing_conditions)} specific fix(es) before funding."
                ),
            }
        return {
            "verdict": "invest_fix",
            "label": "INVEST AND FIX",
            "description": (
                f"Problems are fixable and the investor's support can unlock significant value. "
                f"Current score ({final_score}) understates potential ({conditional_score} if fixed)."
            ),
        }

    if conditional_score >= 60:
        return {
            "verdict": "condition",
            "label": "CONDITION INVESTMENT",
            "description": (
                f"Investment viable if top fixes are made. "
                f"Conditional score ({conditional_score}) reaches Watch territory. "
                f"Require {len(closing_conditions)} fix(es) before or immediately after close."
            ),
        }

    if conditional_score >= 50:
        return {
            "verdict": "fix_first",
            "label": "FIX FIRST, RETURN LATER",
            "description": (
                f"Problems require 3–6 months to address. "
                f"Conditional score ({conditional_score}) is marginal. "
                "Revisit after the founder has made meaningful progress."
            ),
        }

    return {
        "verdict": "structural_pass",
        "label": "STRUCTURAL PASS",
        "description": (
            f"Even with the top fixes applied, the conditional score ({conditional_score}) "
            "does not reach investable territory. Fundamental concerns remain."
        ),
    }
