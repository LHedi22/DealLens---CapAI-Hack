from .ollama_client import call_ollama, MODEL_A
from backend.debug_state import step_started, step_completed, step_failed

BUSINESS_SYSTEM_PROMPT = """You are a senior investment analyst scoring a startup for a venture capital fund.
Score the startup across 6 dimensions based only on the information provided.
Be critical and realistic — most early-stage startups score between 40 and 75.
A score above 80 requires exceptional evidence. A score below 30 means the dimension is severely lacking.

Scoring dimensions and weights:
- team_score (25%): co-founders, domain expertise, prior exits, technical+commercial balance, advisors
- market_score (20%): TAM size and source quality, growth rate, demand evidence, SAM definition
- revenue_score (20%): clarity of revenue model, unit economics, recurring vs transactional, path to profitability
- traction_score (15%): paying customers, growth rate, LOIs, pilots, notable investors or grants
- moat_score (10%): IP, network effects, switching costs, distribution advantage, differentiation
- scalability_score (10%): product-led vs service-heavy, capital efficiency, geographic expansion potential

Return ONLY a valid JSON object with these exact keys:
{
  "team_score": 0-100,
  "market_score": 0-100,
  "revenue_score": 0-100,
  "traction_score": 0-100,
  "moat_score": 0-100,
  "scalability_score": 0-100,
  "composite_score": 0-100,
  "top_strengths": ["strength 1", "strength 2", "strength 3"],
  "top_risks": ["risk 1", "risk 2", "risk 3"]
}

Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."""


async def run_business_scoring(extracted: dict) -> dict:
    step_started("business")
    try:
        user_content = f"""Score this startup based on the following extracted information:

Team: {extracted.get('founder_names')} | Expertise: {extracted.get('domain_expertise')} | Prior exits: {extracted.get('prior_exits')} | Team type: {extracted.get('team_completeness')} | Advisors: {extracted.get('advisors_named')}
Market: TAM ${extracted.get('tam_stated')} | Source: {extracted.get('tam_source')} | Growth: {extracted.get('growth_rate')}
Revenue: Model: {extracted.get('revenue_model')} | Type: {extracted.get('revenue_type')} | Current: ${extracted.get('current_revenue')} | Projected Y1: ${extracted.get('projected_revenue_y1')} | Unit economics: {extracted.get('unit_economics')}
Traction: {extracted.get('traction_evidence')} | Users: {extracted.get('user_count')} | Customers: {extracted.get('customer_count')}
Competition: Competitors: {extracted.get('competitors_named')} | Differentiation: {extracted.get('differentiation')} | IP: {extracted.get('ip_mentioned')}
Scalability: Labor model: {extracted.get('labor_model')}"""

        raw = await call_ollama(
            model=MODEL_A,
            system_prompt=BUSINESS_SYSTEM_PROMPT,
            user_content=user_content,
            agent="business",
        )

        result = _normalize_business(raw)
        step_completed("business", f"Score: {result.get('composite_score')}")
        return result
    except Exception as e:
        step_failed("business", type(e).__name__, str(e))
        raise


def _normalize_business(raw: dict) -> dict:
    def clamp(v, default=50):
        if isinstance(v, (int, float)):
            return max(0, min(100, int(v)))
        return default

    team = clamp(raw.get("team_score"))
    market = clamp(raw.get("market_score"))
    revenue = clamp(raw.get("revenue_score"))
    traction = clamp(raw.get("traction_score"))
    moat = clamp(raw.get("moat_score"))
    scalability = clamp(raw.get("scalability_score"))

    composite = int(
        team * 0.25 + market * 0.20 + revenue * 0.20 +
        traction * 0.15 + moat * 0.10 + scalability * 0.10
    )

    return {
        "team_score": team,
        "market_score": market,
        "revenue_score": revenue,
        "traction_score": traction,
        "moat_score": moat,
        "scalability_score": scalability,
        "composite_score": composite,
        "top_strengths": raw.get("top_strengths") or ["Insufficient data"],
        "top_risks": raw.get("top_risks") or ["Insufficient data to assess risks"]
    }
