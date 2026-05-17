from sqlalchemy import String, Integer, Float, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional


class Base(DeclarativeBase):
    pass


class DealHistory(Base):
    __tablename__ = "deal_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    startup_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(100))
    stage: Mapped[str] = mapped_column(String(50))
    geography: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_model_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_evaluated: Mapped[str] = mapped_column(String(20))
    business_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    esg_composite: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    esg_e: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    esg_s: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    esg_g: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_completeness: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_level: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    conviction_delta: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    red_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blind_spots: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fix_verdict: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compliance_health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_seed_data: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pipeline: Mapped[bool] = mapped_column(Boolean, default=False)


class EntitySector(Base):
    __tablename__ = "entity_sectors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sector_name: Mapped[str] = mapped_column(String(100), unique=True)
    total_evaluations: Mapped[int] = mapped_column(Integer, default=0)
    total_pursued: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_business_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_esg_score: Mapped[float] = mapped_column(Float, default=0.0)
    trend_direction: Mapped[str] = mapped_column(String(20), default="stable")


class EntityFounder(Base):
    __tablename__ = "entity_founders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    deals_seen_in: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sectors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prior_outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PortfolioCompany(Base):
    __tablename__ = "portfolio_companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(100))
    stage: Mapped[str] = mapped_column(String(50))
    geography: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_model_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    esg_tier: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    current_status: Mapped[str] = mapped_column(String(30), default="active")
    compliance_health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class MandateConfig(Base):
    __tablename__ = "mandate_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    sector_focus: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stage_preference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geography_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_esg_threshold: Mapped[int] = mapped_column(Integer, default=0)
    ticket_size_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ticket_size_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    esg_priority_axis: Mapped[str] = mapped_column(String(20), default="Balanced")


class CachedEvaluation(Base):
    __tablename__ = "cached_evaluations"

    startup_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    evaluation_json: Mapped[str] = mapped_column(Text)
    cached_at: Mapped[str] = mapped_column(String(30))


# ── Monitor Module ────────────────────────────────────────────────────────────

class MonitorAgreement(Base):
    __tablename__ = "monitor_agreements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    startup_name: Mapped[str] = mapped_column(String(255))
    deal_history_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    agreement_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    agreement_duration_months: Mapped[int] = mapped_column(Integer, default=60)
    total_committed_tnd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    categories: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_milestones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default="DIGITAL")
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_seed_data: Mapped[bool] = mapped_column(Boolean, default=False)


class MonitorTransaction(Base):
    __tablename__ = "monitor_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agreement_id: Mapped[int] = mapped_column(Integer)
    startup_name: Mapped[str] = mapped_column(String(255))
    statement_month: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    transaction_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    beneficiary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount_tnd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    human_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    alert_triggered: Mapped[int] = mapped_column(Integer, default=0)
    alert_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    alert_resolved: Mapped[int] = mapped_column(Integer, default=0)
    alert_resolved_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)


class MonitorLedgerSnapshot(Base):
    __tablename__ = "monitor_ledger_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agreement_id: Mapped[int] = mapped_column(Integer)
    startup_name: Mapped[str] = mapped_column(String(255))
    snapshot_month: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    months_elapsed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_totals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_spent_tnd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_planned_to_date_tnd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unclassified_tnd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    compliance_health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    alert_count_active: Mapped[int] = mapped_column(Integer, default=0)
    alert_count_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)


class MonitorAlert(Base):
    __tablename__ = "monitor_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agreement_id: Mapped[int] = mapped_column(Integer)
    startup_name: Mapped[str] = mapped_column(String(255))
    transaction_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    alert_type: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(20))
    alert_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alert_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fired_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    resolved: Mapped[int] = mapped_column(Integer, default=0)
    resolved_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    resolved_by_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
