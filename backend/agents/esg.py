from .ollama_client import call_ollama, MODEL_A
from backend.debug_state import step_started, step_completed, step_failed

RED_FLAGS = [
    {
        "code": "RF-01",
        "pattern_keywords": ["proprietary data", "user data", "personal data"],
        "negative_keywords": ["privacy policy", "consent", "gdpr", "data protection"],
        "axis": "S",
        "deduction": 10,
        "description": "Mentions user/personal data without referencing a privacy policy or consent mechanism"
    },
    {
        "code": "RF-02",
        "pattern_keywords": ["supply chain", "manufacturer", "supplier", "factory"],
        "negative_keywords": ["audit", "certified", "iso", "ethical sourcing"],
        "axis": "S",
        "deduction": 8,
        "description": "Supply chain mentioned without labor compliance evidence"
    },
    {
        "code": "RF-03",
        "pattern_keywords": ["founder veto", "sole discretion", "unilateral", "full control"],
        "negative_keywords": [],
        "axis": "G",
        "deduction": 15,
        "description": "Founder unilateral veto rights over all board decisions"
    },
    {
        "code": "RF-04",
        "pattern_keywords": ["carbon neutral", "net zero", "sustainable", "eco-friendly", "green"],
        "negative_keywords": ["certified", "measured", "verified", "third-party", "methodology", "scope"],
        "axis": "E",
        "deduction": 10,
        "description": "Environmental claims with no measurement methodology or certification"
    },
    {
        "code": "RF-05",
        "pattern_keywords": ["diverse team", "diversity", "inclusive"],
        "negative_keywords": ["named", "leads", "cto", "coo", "head of"],
        "axis": "S",
        "deduction": 5,
        "description": "Diversity mentioned in marketing language with no named diverse leaders"
    },
    {
        "code": "RF-06",
        "pattern_keywords": ["revenue projection", "forecast", "projected revenue", "financial model"],
        "negative_keywords": ["assumption", "based on", "assuming", "growth rate of"],
        "axis": "G",
        "deduction": 8,
        "description": "Financial projections with no stated assumptions"
    },
    {
        "code": "RF-07",
        "pattern_keywords": ["founder", "ceo", "cto", "co-founder"],
        "negative_keywords": ["linkedin", "previously at", "formerly", "worked at", "built", "founded"],
        "axis": "G",
        "deduction": 7,
        "description": "Team section lacks verifiable professional history"
    },
    {
        "code": "RF-08",
        "pattern_keywords": [],
        "negative_keywords": [],
        "axis": "G",
        "deduction": 10,
        "description": "Revenue figures inconsistent between documents"
    },
    {
        "code": "RF-09",
        "pattern_keywords": ["solo founder", "single founder", "founder and ceo"],
        "negative_keywords": ["co-founder", "board", "advisor", "advisory"],
        "axis": "G",
        "deduction": 15,
        "description": "Solo founder with no co-founder, board, or advisors"
    },
    {
        "code": "RF-10",
        "pattern_keywords": ["social impact", "social good", "changing lives", "making a difference", "impact-driven"],
        "negative_keywords": ["measured", "lives impacted", "beneficiaries", "survey", "data shows", "%"],
        "axis": "S",
        "deduction": 5,
        "description": "Social impact claimed with no quantified evidence"
    }
]

ESG_SYSTEM_PROMPT = """You are an ESG analyst evaluating a startup for a responsible investment fund.
Score each ESG axis from 0 to 100 based strictly on the information provided.
Higher score = lower risk / better ESG practice.

Environmental (E): carbon intensity, resource use, supply chain exposure, climate risk, verifiability of claims.
Social (S): labor model (gig=risky), product harm potential, community impact, diversity evidence, financial inclusion.
Governance (G): founder concentration, board existence, financial transparency, shareholder protections.

ESG tier: 80-100=Strong, 60-79=Adequate, 40-59=Weak, 0-39=Critical Risk
Verifiability: High=third-party certs or named sources, Medium=specific claims, Low=general statements

Return ONLY a valid JSON object:
{
  "e_score": 0-100,
  "s_score": 0-100,
  "g_score": 0-100,
  "composite": 0-100,
  "tier": "Strong|Adequate|Weak|Critical Risk",
  "verifiability": "High|Medium|Low",
  "most_critical_flag": "one sentence or null",
  "esg_reasoning": "2-3 sentences"
}

Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""


def _scan_red_flags(document_text: str, extracted: dict) -> list:
    text_lower = document_text.lower()
    triggered = []

    for flag in RED_FLAGS:
        if flag["code"] == "RF-08":
            if extracted.get("inconsistencies"):
                triggered.append(flag["code"])
            continue

        pattern_hit = any(kw in text_lower for kw in flag["pattern_keywords"])
        if not pattern_hit:
            continue

        if flag["negative_keywords"]:
            mitigation_hit = any(kw in text_lower for kw in flag["negative_keywords"])
            if mitigation_hit:
                continue

        triggered.append(flag["code"])

    return triggered


def _get_flag_description(code: str) -> str:
    for flag in RED_FLAGS:
        if flag["code"] == code:
            return flag["description"]
    return code


async def run_esg_scoring(extracted: dict, document_text: str, sector: str) -> dict:
    step_started("esg")
    try:
        return await _run_esg_inner(extracted, document_text, sector)
    except Exception as e:
        step_failed("esg", type(e).__name__, str(e))
        raise


async def _run_esg_inner(extracted: dict, document_text: str, sector: str) -> dict:
    triggered_flags = _scan_red_flags(document_text, extracted)

    deductions = {"E": 0, "S": 0, "G": 0}
    for flag in RED_FLAGS:
        if flag["code"] in triggered_flags:
            deductions[flag["axis"]] += flag["deduction"]

    user_content = f"""Evaluate the ESG profile of this startup:

Sector: {sector}
Labor model: {extracted.get('labor_model')}
Environmental claims: {extracted.get('env_claims')}
Governance docs: {extracted.get('governance_docs')} | Board named: {extracted.get('board_named')}
Diversity claimed: {extracted.get('diversity_claimed')}
Founders: {extracted.get('founder_names')}
Advisors: {extracted.get('advisors_named')}
Inconsistencies found: {extracted.get('inconsistencies')}

Additional context from documents:
{document_text[:3000]}"""

    raw = await call_ollama(
        model=MODEL_A,
        system_prompt=ESG_SYSTEM_PROMPT,
        user_content=user_content,
        agent="esg",
    )

    def clamp(v, default=50):
        if isinstance(v, (int, float)):
            return max(0, min(100, int(v)))
        return default

    e_score = max(0, clamp(raw.get("e_score")) - deductions["E"])
    s_score = max(0, clamp(raw.get("s_score")) - deductions["S"])
    g_score = max(0, clamp(raw.get("g_score")) - deductions["G"])
    composite = int(e_score * 0.30 + s_score * 0.35 + g_score * 0.35)

    if composite >= 80:
        tier = "Strong"
    elif composite >= 60:
        tier = "Adequate"
    elif composite >= 40:
        tier = "Weak"
    else:
        tier = "Critical Risk"

    def _flag_meta(code):
        for f in RED_FLAGS:
            if f["code"] == code:
                return {"code": code, "description": f["description"], "deduction": f["deduction"]}
        return {"code": code, "description": code, "deduction": 0}

    red_flag_details = [_flag_meta(code) for code in triggered_flags]

    result = {
        "e_score": e_score,
        "s_score": s_score,
        "g_score": g_score,
        "composite": composite,
        "tier": tier,
        "verifiability": raw.get("verifiability") or "Low",
        "red_flags_triggered": triggered_flags,
        "red_flag_details": red_flag_details,
        "most_critical_flag": raw.get("most_critical_flag"),
        "esg_reasoning": raw.get("esg_reasoning") or "ESG assessment based on available information."
    }
    step_completed("esg", f"ESG: {composite} ({tier}) | Flags: {len(triggered_flags)}")
    return result
