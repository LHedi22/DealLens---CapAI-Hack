from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func, text
import json
from datetime import date, datetime
from pathlib import Path

from backend.models import (
    Base, DealHistory, EntitySector, MandateConfig, CachedEvaluation,
    MonitorAgreement, MonitorTransaction, MonitorLedgerSnapshot, MonitorAlert,
    SynergyProfile, SynergyPair, SynergyGap,
)

DATABASE_URL = "sqlite+aiosqlite:///./convictai.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add new columns to existing tables — silently skip if already present
        for stmt in [
            "ALTER TABLE deal_history ADD COLUMN compliance_health_score INTEGER",
            "ALTER TABLE portfolio_companies ADD COLUMN compliance_health_score INTEGER",
        ]:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass
    await seed_database()
    await seed_monitor_database()
    await seed_synergy_database()
    await sync_monitor_from_pipeline()
    await sync_synergy_from_pipeline()


_EDUFLOW_CACHE = {
    "startup_name": "EduFlow",
    "sector": "EdTech",
    "stage": "Seed",
    "geography": "MENA",
    "final_score": 72,
    "business_score": 78,
    "adjusted_business": 72,
    "esg_composite": 61,
    "esg_e": 74,
    "esg_s": 58,
    "esg_g": 51,
    "conviction_delta": -6,
    "confidence_level": "MEDIUM",
    "data_completeness": 72,
    "mandate_breach": False,
    "mandate_flags": [],
    "verdict": "watch",
    "verdict_label": "WATCH",
    "verdict_reason": (
        "Strong technical team and clear market, but memory matching to AlphaLearn "
        "(87% similarity, failed at Series A due to founder-led sales) warrants caution. "
        "Governance concerns and no traction evidence drag the conviction delta to -6."
    ),
    "mandate_breaches": [],
    "dimension_scores": {
        "team": 82, "market": 79, "revenue": 75,
        "traction": 65, "moat": 70, "scalability": 80,
    },
    "top_strengths": [
        "Strong technical founding team",
        "Large and growing TAM — 28% CAGR",
        "Clear B2B SaaS revenue model",
    ],
    "top_risks": [
        "No traction evidence provided",
        "Governance structure undisclosed — RF-09 triggered",
        "Founder-led sales risk — mirrors AlphaLearn failure pattern",
    ],
    "esg_tier": "Adequate",
    "esg_verifiability": "Low",
    "red_flags_triggered": ["RF-09", "RF-03", "RF-10"],
    "red_flag_details": [
        {"code": "RF-09", "description": "Solo founder, no board, no advisors", "axis": "G", "deduction": -15},
        {"code": "RF-03", "description": "Founder unilateral veto over all board decisions", "axis": "G", "deduction": -15},
        {"code": "RF-10", "description": "Impact or social good claimed, no evidence", "axis": "S", "deduction": -5},
    ],
    "most_critical_esg_flag": "RF-09 — Solo founder pattern with no board or advisors",
    "esg_reasoning": (
        "ESG score of 61 (Adequate tier). Three red flags triggered, primarily around governance. "
        "No environmental claims or violations. 50% female founding team is a positive social signal, "
        "but no formal diversity policy or named diverse leaders beyond the co-founder."
    ),
    "blind_spots": [
        {
            "field": "supply_chain_esg_exposure",
            "risk": "Unknown environmental or labor compliance in any hardware or content production",
            "question": "Who are your top 3 suppliers and where are they based?",
        },
        {
            "field": "team_execution_track_record",
            "risk": "Unknown ability to execute under pressure at scale",
            "question": "What is the hardest problem your team has solved together before this?",
        },
        {
            "field": "regulatory_risk",
            "risk": "EdTech in MENA can require government approval — approval timelines could delay growth",
            "question": "Have you mapped the regulatory approval process for operating in each target country?",
        },
    ],
    "delta_explanation": (
        "Memory matched to AlphaLearn (87% similarity — EdTech Seed, failed at Series A due to "
        "founder-led sales). This pattern directly mirrors EduFlow's profile. Sector conviction for "
        "EdTech is improving but the specific failure pattern warrants a -6 delta."
    ),
    "top_memory_matches": [
        {
            "startup_name": "AlphaLearn",
            "similarity_pct": 87,
            "sector": "EdTech",
            "stage": "Seed",
            "decision": "pursue",
            "outcome": "Stalled at Series A — founder-led sales",
        },
        {
            "startup_name": "DataVault",
            "similarity_pct": 62,
            "sector": "SaaS",
            "stage": "Seed",
            "decision": "pursue",
            "outcome": "Invested — acquired",
        },
        {
            "startup_name": "MedTrack",
            "similarity_pct": 51,
            "sector": "HealthTech",
            "stage": "Seed",
            "decision": "pursue",
            "outcome": "Invested — performing",
        },
    ],
    "sector_conviction": {
        "sector": "EdTech",
        "total_evaluations": 6,
        "total_pursued": 3,
        "win_rate": 50,
        "trend_direction": "improving",
        "learning_note": (
            "EdTech Seed deals have a 50% win rate in fund memory. "
            "AlphaLearn failure at Series A was linked to founder-led sales — look for commercial co-founders."
        ),
    },
    "forecast": {
        "revenue_trajectory": {
            "base_case_current": 180000,
            "base_case_12m": 420000,
            "base_case_growth_pct": 133,
            "optimistic_12m": 680000,
            "optimistic_growth_pct": 278,
            "conservative_12m": 240000,
            "conservative_growth_pct": 33,
            "key_assumption": "Base case assumes 3 additional school conversions and 2 LOIs closing within 6 months.",
        },
        "success_probability": {
            "probability_pct": 52,
            "sector_base_rate_pct": 44,
            "adjustments": [
                {"value_pct": 6, "label": "strong technical team"},
                {"value_pct": 4, "label": "large and growing TAM"},
                {"value_pct": -8, "label": "no traction evidence"},
                {"value_pct": -4, "label": "governance concerns"},
            ],
            "confidence": "LOW",
            "milestone": "Series A",
            "horizon_months": 24,
        },
        "roi_estimate": {
            "expected_multiple": 8.2,
            "probability_weighted_multiple": 4.3,
            "comparables_used": ["DataVault — acquired at 9×", "PayFlow — secondary at 7×"],
            "confidence": "LOW",
            "note": "Based on 2 comparable EdTech/SaaS exits in fund memory.",
            "disclaimer": "AI-reasoned estimates. Not a financial model. Use for directional comparison only.",
            "horizon_years": 5,
        },
        "sector_trend": {
            "signal": "POSITIVE",
            "trend_direction": "improving",
            "fund_win_rate_pct": 50,
            "sector": "EdTech",
            "startup_growth_claim": "28% CAGR",
            "note": "MENA EdTech market growing rapidly post-pandemic. Ministry relationships are a strong early signal.",
        },
        "disclaimer": "AI-reasoned estimates. Not a financial model. Use for directional comparison only.",
    },
    "fix_analysis": {
        "current_score": 72,
        "conditional_score": 81,
        "score_gap": 9,
        "fix_verdict": "condition",
        "fix_verdict_label": "CONDITION INVESTMENT",
        "fix_verdict_description": (
            "Three fixable issues identified. Address the commercial gap and governance structure "
            "before closing. Strong underlying business warrants conditional investment."
        ),
        "top_priority_actions": [
            {
                "label": "No commercial co-founder",
                "fix_score": 4,
                "score_impact": 5,
                "closing_condition": True,
                "time_months": 2,
                "action": "Hire or appoint a commercial lead with B2B SaaS sales experience within 60 days of term sheet.",
                "owner": "Founder",
            },
            {
                "label": "No board or governance structure — RF-09",
                "fix_score": 5,
                "score_impact": 3,
                "closing_condition": True,
                "time_months": 1,
                "action": "Appoint 2 independent advisors and draft a shareholder agreement before close.",
                "owner": "Founder + Legal",
            },
            {
                "label": "No paying customers — pre-revenue traction only",
                "fix_score": 3,
                "score_impact": 2,
                "closing_condition": False,
                "time_months": 3,
                "action": "Convert at least 1 pilot school to a paid annual contract before Series A.",
                "owner": "Founder",
            },
        ],
        "structural_problems": [],
    },
    "portfolio": {
        "sector_distribution": {"EdTech": 10, "FinTech": 40, "HealthTech": 20, "SaaS": 20, "Other": 10},
        "concentration_warning": False,
        "overweight_sectors": ["FinTech"],
        "stage_distribution": {"Seed": 3, "Pre-seed": 1, "Series A": 1},
        "stage_balance_ok": True,
        "geo_distribution": {"MENA": 60, "Europe": 40},
        "geo_warning": False,
        "portfolio_esg_before": 66.0,
        "portfolio_esg_after": 64.8,
        "esg_shift": -1.2,
        "esg_degradation_flag": False,
        "correlated_companies": [],
        "correlation_risk": False,
        "fit_verdict": "neutral_fit",
        "fit_summary": "EdTech adds sector diversity to a FinTech-heavy portfolio. Minor ESG dilution — not a blocking concern.",
        "best_pair": ["EduFlow", "HealthCore"],
        "optimizer_reason": "EduFlow + HealthCore gives maximum sector spread with complementary ESG profiles",
    },
    "source_type": "DIGITAL",
    "files_analysed": 1,
}


_ALL_SECTORS = [
    "EdTech", "FinTech", "Logistics", "HealthTech",
    "Construction Tech", "SaaS", "AgriTech", "E-Commerce",
    "CleanTech", "Manufacturing", "Cybersecurity", "PropTech",
    "InsurTech", "Gaming", "AI/ML",
]


_SCORE_FIELDS = (
    "business_score", "esg_composite", "esg_e", "esg_s", "esg_g",
    "data_completeness", "confidence_level", "conviction_delta", "final_score",
    "decision", "decision_reason", "fix_verdict",
)


async def seed_database():
    from sqlalchemy import update as sa_update

    async with AsyncSessionLocal() as session:
        # ── Load JSON once ───────────────────────────────────────────────────
        with open("backend/seed/demo_deals.json", encoding="utf-8-sig") as f:
            data = json.load(f)

        # ── Discover which names already exist ───────────────────────────────
        existing_result = await session.execute(select(DealHistory.startup_name))
        existing_names = {row[0] for row in existing_result.all()}
        first_run = not existing_names

        # ── Insert missing deals (safe for repeated restarts) ────────────────
        added = False
        for deal in data["history_deals"]:
            if deal["startup_name"] not in existing_names:
                session.add(DealHistory(**deal, is_seed_data=True, is_pipeline=False))
                added = True

        for deal in data["pipeline_deals"]:
            if deal["startup_name"] not in existing_names:
                session.add(DealHistory(**deal, is_seed_data=True, is_pipeline=True))
                added = True

        if added or first_run:
            await session.commit()

        # ── Re-sync scores for existing seed records ─────────────────────────
        # Keeps seed records authoritative regardless of how many times the
        # server restarts. Only touches is_seed_data=True rows so live
        # evaluations are never overwritten.
        all_seed = data["history_deals"] + data["pipeline_deals"]
        for deal in all_seed:
            name = deal["startup_name"]
            if name not in existing_names:
                continue  # just inserted above; skip
            patch = {k: deal[k] for k in _SCORE_FIELDS if k in deal}
            if patch:
                await session.execute(
                    sa_update(DealHistory)
                    .where(DealHistory.startup_name == name, DealHistory.is_seed_data == True)  # noqa: E712
                    .values(**patch)
                )
        await session.commit()

        # ── Seed support tables only on true first run ───────────────────────
        if first_run:
            for s in _ALL_SECTORS:
                session.add(EntitySector(sector_name=s))
            session.add(MandateConfig(id=1))
        else:
            # Top up any new sectors added to the list
            existing_sectors_result = await session.execute(
                select(EntitySector.sector_name)
            )
            existing_sectors = {row[0] for row in existing_sectors_result.all()}
            for s in _ALL_SECTORS:
                if s not in existing_sectors:
                    session.add(EntitySector(sector_name=s))
            await session.commit()

        # ── Seed cached evaluations ──────────────────────────────────────────
        # Primary: load all AI-generated eval JSONs from cached_evals/ directory.
        # Fallback: if directory doesn't exist yet, pre-load the hardcoded EduFlow cache
        # so the demo works immediately after cloning (before run_evaluations.py is run).
        cached_evals_dir = Path("backend/seed/cached_evals")
        if cached_evals_dir.is_dir():
            for json_file in sorted(cached_evals_dir.glob("*.json")):
                startup_name = json_file.stem
                existing = await session.scalar(
                    select(CachedEvaluation).where(CachedEvaluation.startup_name == startup_name)
                )
                if not existing:
                    session.add(CachedEvaluation(
                        startup_name=startup_name,
                        evaluation_json=json_file.read_text(encoding="utf-8"),
                        cached_at=date.today().isoformat(),
                    ))
            await session.commit()
        else:
            cache_count = await session.scalar(select(func.count()).select_from(CachedEvaluation))
            if cache_count == 0:
                session.add(CachedEvaluation(
                    startup_name="EduFlow",
                    evaluation_json=json.dumps(_EDUFLOW_CACHE),
                    cached_at=date.today().isoformat(),
                ))
                await session.commit()


async def seed_monitor_database():
    """Seed Monitor module with rich mock data for all 5 pipeline startups.
    Reads demo_agreements.json + demo_transactions.json. Per-company idempotent —
    skips any company that already has an is_seed_data=True MonitorAgreement.
    """
    from sqlalchemy import update as sa_update

    try:
        with open("backend/monitor/seed/demo_agreements.json", encoding="utf-8") as f:
            agreements_data = json.load(f)
        with open("backend/monitor/seed/demo_transactions.json", encoding="utf-8") as f:
            tx_data = json.load(f)
    except FileNotFoundError:
        return

    async with AsyncSessionLocal() as session:
        now = datetime.utcnow().isoformat()

        for ag in agreements_data["agreements"]:
            name = ag["startup_name"]

            exists = await session.scalar(
                select(MonitorAgreement).where(
                    MonitorAgreement.startup_name == name,
                    MonitorAgreement.is_seed_data == True,  # noqa: E712
                )
            )
            if exists:
                continue

            agreement = MonitorAgreement(
                startup_name=name,
                agreement_date=ag["agreement_date"],
                agreement_duration_months=ag["agreement_duration_months"],
                total_committed_tnd=ag["total_committed_tnd"],
                categories=json.dumps(ag["categories"]),
                time_milestones=json.dumps(ag.get("time_milestones", [])),
                source_type="DIGITAL",
                uploaded_at=now,
                is_seed_data=True,
            )
            session.add(agreement)
            await session.flush()

            if name not in tx_data:
                continue

            company_data = tx_data[name]

            for tx in company_data.get("transactions", []):
                session.add(MonitorTransaction(
                    agreement_id=agreement.id,
                    startup_name=name,
                    statement_month=tx["statement_month"],
                    transaction_date=tx["transaction_date"],
                    beneficiary=tx["beneficiary"],
                    amount_tnd=tx["amount_tnd"],
                    memo=tx["memo"],
                    ai_category=tx.get("ai_category"),
                    ai_confidence=tx.get("ai_confidence"),
                    classification_status=tx.get("classification_status"),
                    alert_triggered=tx.get("alert_triggered", 0),
                    alert_type=tx.get("alert_type"),
                    uploaded_at=now,
                ))

            snap = company_data.get("snapshot", {})
            if snap:
                session.add(MonitorLedgerSnapshot(
                    agreement_id=agreement.id,
                    startup_name=name,
                    snapshot_month=snap["snapshot_month"],
                    months_elapsed=snap["months_elapsed"],
                    category_totals=json.dumps(snap["category_totals"]),
                    total_spent_tnd=snap["total_spent_tnd"],
                    total_planned_to_date_tnd=snap["total_planned_to_date_tnd"],
                    unclassified_tnd=snap.get("unclassified_tnd", 0.0),
                    compliance_health_score=snap["compliance_health_score"],
                    alert_count_active=snap["alert_count_active"],
                    alert_count_total=snap["alert_count_total"],
                    created_at=now,
                ))
                await session.execute(
                    sa_update(DealHistory)
                    .where(DealHistory.startup_name == name)
                    .values(compliance_health_score=snap["compliance_health_score"])
                )

            for alert in company_data.get("alerts", []):
                session.add(MonitorAlert(
                    agreement_id=agreement.id,
                    startup_name=name,
                    alert_type=alert["alert_type"],
                    severity=alert["severity"],
                    alert_summary=alert.get("alert_summary"),
                    alert_detail=alert.get("alert_detail"),
                    fired_at=alert.get("fired_at"),
                    resolved=alert.get("resolved", 0),
                    resolved_at=alert.get("resolved_at"),
                    resolved_by_note=alert.get("resolved_by_note"),
                ))

        await session.commit()


async def seed_synergy_database():
    """Seed Synergy module with profiles, pairs, and gaps from demo_synergy_seed.json.
    Idempotent — skips entirely if any extraction_source='seed' profiles already exist.
    """
    try:
        with open("backend/synergy/seed/demo_synergy_seed.json", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(func.count()).select_from(SynergyProfile).where(
                SynergyProfile.extraction_source == "seed"
            )
        )
        if existing:
            return

        now = datetime.utcnow().isoformat()

        for p in data.get("profiles", []):
            session.add(SynergyProfile(
                company_name=p["company_name"],
                sector=p.get("sector"),
                geography=p.get("geography"),
                stage=p.get("stage"),
                services_offered=json.dumps(p.get("services_offered", [])),
                target_customers=json.dumps(p.get("target_customers", [])),
                operational_needs=json.dumps(p.get("operational_needs", [])),
                strategic_gaps=json.dumps(p.get("strategic_gaps", [])),
                profile_confidence=p.get("profile_confidence", "MEDIUM"),
                last_extracted_at=now,
                extraction_source="seed",
            ))

        await session.flush()

        for pair in data.get("pairs", []):
            session.add(SynergyPair(
                company_a=pair["company_a"],
                company_b=pair["company_b"],
                service_bridge_score=pair.get("service_bridge_score"),
                shared_customer_score=pair.get("shared_customer_score"),
                co_dev_score=pair.get("co_dev_score"),
                composite_score=pair.get("composite_score"),
                synergy_types_triggered=json.dumps(pair.get("synergy_types_triggered", [])),
                match_explanation=pair.get("match_explanation"),
                value_creation_type=pair.get("value_creation_type"),
                value_estimate_label=pair.get("value_estimate_label"),
                action_suggestion=pair.get("action_suggestion"),
                confidence_level=pair.get("confidence_level"),
                created_at=now,
            ))

        for gap in data.get("gaps", []):
            session.add(SynergyGap(
                gap_label=gap["gap_label"],
                need_description=gap.get("need_description"),
                affected_companies=json.dumps(gap.get("affected_companies", [])),
                affected_count=gap.get("affected_count"),
                estimated_annual_spend=gap.get("estimated_annual_spend"),
                suggested_sector=gap.get("suggested_sector"),
                suggested_stage=gap.get("suggested_stage"),
                urgency_score=gap.get("urgency_score"),
                status=gap.get("status", "open"),
                created_at=now,
            ))

        await session.commit()


async def sync_monitor_from_pipeline():
    """Auto-enroll pursue/watch/soft_pass pipeline companies into Monitor using ESG composite as initial health score."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DealHistory).where(
                DealHistory.is_pipeline == True,   # noqa: E712
                DealHistory.decision.in_(["pursue", "watch", "soft_pass"]),
            )
        )
        for company in result.scalars().all():
            exists = await session.scalar(
                select(MonitorAgreement).where(
                    MonitorAgreement.startup_name == company.startup_name
                )
            )
            if exists:
                continue

            agreement = MonitorAgreement(
                startup_name=company.startup_name,
                deal_history_id=company.id,
                agreement_date=company.date_evaluated,
                agreement_duration_months=60,
                total_committed_tnd=0.0,
                categories=json.dumps([]),
                time_milestones=json.dumps([]),
                source_type="AUTO",
                is_seed_data=False,
            )
            session.add(agreement)
            await session.flush()

            health = company.esg_composite or 50
            session.add(MonitorLedgerSnapshot(
                agreement_id=agreement.id,
                startup_name=company.startup_name,
                snapshot_month=(company.date_evaluated or date.today().isoformat())[:7],
                months_elapsed=0,
                category_totals=json.dumps({}),
                total_spent_tnd=0.0,
                total_planned_to_date_tnd=0.0,
                unclassified_tnd=0.0,
                compliance_health_score=health,
                alert_count_active=0,
                alert_count_total=0,
            ))
            company.compliance_health_score = health

        await session.commit()


async def sync_synergy_from_pipeline():
    """Build SynergyProfiles for pursue/watch/soft_pass pipeline companies that don't have one yet.
    Uses CachedEvaluation fields to derive profile arrays. Pair scoring is left to the
    user-triggered 'Run Analysis' button in Synergy so startup is never blocked on Ollama.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DealHistory).where(
                DealHistory.is_pipeline == True,   # noqa: E712
                DealHistory.decision.in_(["pursue", "watch", "soft_pass"]),
            )
        )
        for company in result.scalars().all():
            exists = await session.scalar(
                select(SynergyProfile).where(
                    SynergyProfile.company_name == company.startup_name
                )
            )
            if exists:
                continue

            cached = await session.scalar(
                select(CachedEvaluation).where(
                    CachedEvaluation.startup_name == company.startup_name
                )
            )
            if cached:
                ev = json.loads(cached.evaluation_json)
                services = ev.get("top_strengths", [])[:3]
                needs    = ev.get("top_risks", [])[:3]
                gaps     = [
                    bs.get("risk") or bs.get("field", "")
                    for bs in ev.get("blind_spots", [])[:3]
                    if bs.get("risk") or bs.get("field")
                ]
                customers = [f"{company.sector or 'Tech'} clients"]
                if (company.stage or "").lower() in ("seed", "pre-seed"):
                    customers.append("Early adopters")
                else:
                    customers.append("Enterprise buyers")
            else:
                services = needs = gaps = customers = []

            arrays = [services, customers, needs, gaps]
            rich      = sum(1 for a in arrays if len(a) >= 2)
            populated = sum(1 for a in arrays if len(a) >= 1)
            confidence = "HIGH" if rich == 4 else ("MEDIUM" if populated >= 3 else "LOW")

            session.add(SynergyProfile(
                company_name=company.startup_name,
                deal_history_id=company.id,
                services_offered=json.dumps(services),
                target_customers=json.dumps(customers),
                operational_needs=json.dumps(needs),
                strategic_gaps=json.dumps(gaps),
                sector=company.sector,
                geography=company.geography,
                stage=company.stage,
                profile_confidence=confidence,
                last_extracted_at=datetime.utcnow().isoformat(),
                extraction_source="cached_evaluations",
            ))

        await session.commit()
