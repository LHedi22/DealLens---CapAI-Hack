from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class StartupProfile(BaseModel):
    startup_name: str
    sector: str
    stage: str
    geography: str
    funding_asked: Optional[int] = None
    business_model_type: str


class MandateConfigIn(BaseModel):
    sector_focus: Optional[List[str]] = None
    stage_preference: Optional[List[str]] = None
    geography_scope: Optional[List[str]] = None
    min_esg_threshold: int = 0
    ticket_size_min: Optional[int] = None
    ticket_size_max: Optional[int] = None
    esg_priority_axis: str = "Balanced"


class MandateConfigOut(MandateConfigIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DealSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    startup_name: str
    sector: str
    stage: str
    business_score: Optional[int] = None
    esg_composite: Optional[int] = None
    conviction_delta: Optional[int] = None
    final_score: Optional[int] = None
    decision: Optional[str] = None
    confidence_level: Optional[str] = None
    fix_verdict: Optional[str] = None
    is_pipeline: bool


class DealDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    startup_name: str
    sector: str
    stage: str
    geography: Optional[str] = None
    business_model_type: Optional[str] = None
    date_evaluated: str
    business_score: Optional[int] = None
    esg_composite: Optional[int] = None
    esg_e: Optional[int] = None
    esg_s: Optional[int] = None
    esg_g: Optional[int] = None
    data_completeness: Optional[int] = None
    confidence_level: Optional[str] = None
    conviction_delta: Optional[int] = None
    final_score: Optional[int] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    red_flags: Optional[str] = None
    blind_spots: Optional[str] = None
    fix_verdict: Optional[str] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None
    is_seed_data: bool
    is_pipeline: bool


class UploadResponse(BaseModel):
    startup_id: str
    files_received: int
    file_names: List[str]
    message: str


class EvaluationRequest(BaseModel):
    startup_id: str
    startup_name: str
    sector: str
    stage: str
    geography: str
    funding_asked: Optional[int] = None
    business_model_type: str


# ── Phase 5 additions ────────────────────────────────────────────────────────

class BlindSpot(BaseModel):
    field: str
    risk: str
    question: str


class PortfolioResult(BaseModel):
    sector_distribution: dict
    concentration_warning: bool
    overweight_sectors: List[str]
    stage_distribution: dict
    stage_balance_ok: bool
    geo_distribution: dict
    geo_warning: bool
    portfolio_esg_before: float
    portfolio_esg_after: float
    esg_shift: float
    esg_degradation_flag: bool
    correlated_companies: List[str]
    correlation_risk: bool
    fit_verdict: str
    fit_summary: str
    best_pair: List[str]
    optimizer_reason: str


class MandateApplyResult(BaseModel):
    changed_startups: List[dict]
    message: str


class OCRCorrection(BaseModel):
    section_name: str
    original_value: str
    corrected_value: str


class OCRConfirmRequest(BaseModel):
    confirmed_document: dict
    corrections: List[OCRCorrection] = []
    sector: str = "EdTech"
    stage: str = "Pre-seed"
    geography: str = "MENA"
    business_model_type: str = "B2B SaaS"
    funding_asked: Optional[int] = 400000
