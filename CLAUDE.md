# CLAUDE.md — ConvictAI Build Instructions
> Master reference for Claude Code. Read this file before touching any code.
> Every decision, every constraint, every phase is defined here.
> Source of truth: CapAI_Project_Guide.md + ConvictAI_Architecture.txt

---

## Current Status — ALL PHASES COMPLETE (2026-05-17) | Bug fixes 2026-06-12 | Refactor 2026-06-17

All 6 core phases + Monitor module + Synergy module are fully implemented and demo-ready.
Do not re-implement anything. Read existing code before adding new logic.

### Refactor Applied 2026-06-17
- **database.py** — `seed_monitor_database()` and `seed_synergy_database()` replaced with
  `sync_monitor_from_pipeline()` and `sync_synergy_from_pipeline()`. Monitor and Synergy now
  derive all data from real `DealHistory` evaluations (pursue/watch only). Hardcoded seed JSON
  files (`demo_agreements.json`, `demo_transactions.json`, `demo_synergy_seed.json`) are no
  longer loaded on startup — they remain on disk but are bypassed.
- **feedback_loop.py** — `write_deal_record()` now auto-enrolls every new pursue/watch verdict
  into Monitor (`_enroll_in_monitor`) and Synergy (`_create_synergy_profile`) immediately after
  the main deal commit. Both helpers are idempotent and wrapped in try/except so failures never
  affect the primary deal write.
- **evaluate.py** — `"document_text"` added to the `write_deal_record()` dict so the feedback
  loop can pass raw document text to the Synergy Ollama extractor (`extract_synergy_profile`).
- **database.py (synergy customer heuristic)** — `sync_synergy_from_pipeline()` previously
  tried `ev.get("revenue_model")` which is not in `response_payload` (it lives in `extracted`
  only). Now derives the second customer segment from `company.stage` instead:
  seed/pre-seed → "Early adopters"; all other stages → "Enterprise buyers".

### Bug Fixes Applied 2026-06-12
- **monitor_routes.py** — `scalar_one_or_none()` → `.scalars().first()` in both `get_dashboard`
  and `get_portfolio_health`. `MonitorLedgerSnapshot` accumulates one row per statement upload;
  the strict "exactly one row" assertion crashed after any re-run.
- **evaluate.py** — `POST /evaluate` now upserts the full response into `cached_evaluations`
  via `db.merge()` immediately after every successful evaluation.
- **evaluate.py** — `GET /evaluate/cached/{name}` falls back to `deal_history` (is_pipeline=True)
  when no cache entry exists, returning a partial response with stored scores instead of 404.
  Partial responses carry `"is_partial": true`. `_esg_tier()` helper added to derive tier label.

---

## What You Are Building

**ConvictAI** — an AI-powered pre-investment screening engine for startup investors.

It ingests multiple startup documents, scores them across Business + ESG dimensions,
cross-references them against a memory of past deals, forecasts trajectory, identifies
fixable problems, maps portfolio fit, and delivers 8 structured output cards.

**One sentence:** Every other AI tool forgets. Ours remembers.

---

## Hard Constraints — Never Violate These

- **No paid APIs.** All LLM calls go to Ollama at `localhost:11434`. No OpenAI, no Anthropic, no internet calls during the demo.
- **Models:** Use `mistral` or `phi3:mini` (≤5B parameters). Two models max.
- **Demo runs on localhost.** No deployment needed.
- **All 8 output cards must render.** No placeholders on demo day.
- **Multi-file upload per startup.** Each startup can submit multiple documents.
- **OCR is faked.** Layer 1.5 is a frontend animation over a pre-loaded parsed result. Do not install Tesseract. Do not do real OCR.
- **SQLite only.** No PostgreSQL, no Redis, no external databases.
- **No authentication.** Single-user local app. No login screen.

---

## Tech Stack — Fixed, Do Not Change

### Backend
- **Python 3.11+**
- **FastAPI** — async REST API
- **SQLAlchemy 2.0** + **SQLite** — memory layer persistence
- **Pydantic v2** — all request/response schemas
- **PyMuPDF (fitz)** — PDF text extraction
- **python-docx** — DOCX parsing
- **openpyxl** — XLSX parsing
- **httpx** — async Ollama calls
- **asyncio.gather** — all 5 scoring agents run in parallel

### Frontend
- **React 18 + Vite**
- **All inline CSS** — CSS custom properties via `index.css`, NO Tailwind utility classes in components
- **Recharts** — ESG bar charts, sector pie chart, score gauges
- **React Dropzone** — multi-file upload
- **Framer Motion** — OCR animation sequence
- **Radix UI** — dialog, select, tabs, toast primitives

### LLM
- **Ollama** at `http://localhost:11434` (overridable via `OLLAMA_BASE_URL` env var)
- **Model A** (`mistral` or `phi3:mini`): Extraction + Business scoring + ESG scoring
- **Model B** (`llama3.2:3b` or `tinyllama`): Memory explanations + Blind spot questions + Fix analysis text
- All responses must be **structured JSON** — enforced via system prompts
- Wrap every Ollama call: if JSON parse fails, retry once, then return a safe default

### File Structure (Actual — as of 2026-05-17)
```
convictai/
├── backend/
│   ├── main.py                  # FastAPI app entry point — 8 routers registered
│   ├── database.py              # SQLAlchemy setup + seed loader (all 3 seed functions)
│   ├── models.py                # 13 SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic schemas (all of them)
│   ├── debug_state.py           # Pipeline state emitter for debug page
│   ├── agents/
│   │   ├── ollama_client.py     # httpx client, 90s timeout, retry, JSON parse
│   │   ├── extraction.py        # Layer 3 Step 1
│   │   ├── business.py          # Layer 3 Step 2A
│   │   ├── esg.py               # Layer 3 Step 2B
│   │   ├── memory.py            # Layer 3 Step 2C
│   │   ├── forecasting.py       # Layer 3 Step 2D
│   │   ├── fix_analysis.py      # Layer 3 Step 2E
│   │   └── portfolio.py         # Layer 3 Step 3
│   ├── engine/
│   │   ├── aggregator.py        # Layer 3 Step 6
│   │   ├── recommendation.py    # Layer 3 Step 7
│   │   └── feedback_loop.py     # Writes back to Layer 2 (is_pipeline=True)
│   ├── parsers/
│   │   ├── __init__.py          # exports merge_documents()
│   │   ├── pdf_parser.py        # PyMuPDF
│   │   ├── docx_parser.py       # python-docx
│   │   └── xlsx_parser.py       # openpyxl
│   ├── routers/
│   │   ├── upload.py            # POST /api/upload
│   │   ├── startup.py           # GET /api/pipeline (is_pipeline=True only)
│   │   ├── mandate.py           # GET/POST /api/mandate + POST /api/mandate/apply
│   │   ├── evaluate.py          # POST /api/evaluate (full 6-step pipeline)
│   │   ├── ocr.py               # GET /api/ocr-mock + POST /api/ocr-confirm
│   │   └── debug.py             # Pipeline state streaming
│   ├── monitor/
│   │   ├── routes/monitor_routes.py
│   │   ├── agents/              # agreement_parser, statement_parser, category_agent,
│   │   │                        # compliance_agent, anomaly_agent
│   │   ├── engine/              # ledger.py, alert_engine.py
│   │   └── seed/                # demo_agreements.json, demo_transactions.json,
│   │                            # bank_statement_mock.json
│   ├── synergy/
│   │   ├── routes/synergy_routes.py
│   │   ├── agents/              # profile_extractor, pair_scorer, gap_detector, gap_hunter
│   │   ├── engine/match_engine.py
│   │   └── seed/demo_synergy_seed.json
│   ├── seed/
│   │   └── demo_deals.json      # 6 history deals + 5 pipeline startups
│   └── ocr_mock/
│       └── scanned_result.json  # Pre-parsed EduTech Tunisia data
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── cards/
│   │   │   │   ├── ScorecardCard.jsx
│   │   │   │   ├── ESGCard.jsx
│   │   │   │   ├── MemoryInsightCard.jsx
│   │   │   │   ├── PortfolioFitCard.jsx
│   │   │   │   ├── ForecastCard.jsx
│   │   │   │   ├── FixAnalysisCard.jsx
│   │   │   │   └── BlindSpotCard.jsx
│   │   │   │   # NOTE: ComparisonTable.jsx does NOT exist — Dashboard.jsx
│   │   │   │   # builds its pipeline table inline (native HTML table)
│   │   │   ├── upload/
│   │   │   │   ├── FileUploader.jsx
│   │   │   │   └── OCRAnimationGate.jsx
│   │   │   ├── forms/
│   │   │   │   ├── StartupProfileForm.jsx
│   │   │   │   └── MandateConfigForm.jsx
│   │   │   ├── shared/
│   │   │   │   ├── ScoreGauge.jsx
│   │   │   │   ├── ConfidenceBadge.jsx
│   │   │   │   ├── ESGBar.jsx
│   │   │   │   ├── LoadingCards.jsx
│   │   │   │   ├── ScorePill.jsx     # scoreColor() + scoreBg() helpers
│   │   │   │   ├── VerdictBadge.jsx
│   │   │   │   └── DeltaBadge.jsx
│   │   │   ├── monitor/             # AlertPanel, BudgetTracker, ComplianceDashboard,
│   │   │   │                        # ComplianceHealthBadge, MonitorOCRAnimationGate,
│   │   │   │                        # StatementUploader, TimelineChart, TransactionLog
│   │   │   └── synergy/             # ExternalStartupCard, GapCard, GapPanel,
│   │   │                            # PortfolioGraph, SynergyCard, SynergyPairTable,
│   │   │                            # SynergyScoreBar, SynergyTypeBadge
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # Pipeline table (inline) + stat cards + synergy chips
│   │   │   ├── Evaluate.jsx     # Upload + form + 8 result cards + OCR gate
│   │   │   ├── Mandate.jsx      # Fund config + apply to pipeline
│   │   │   ├── Monitor.jsx      # Compliance monitoring hub
│   │   │   ├── Synergy.jsx      # Portfolio synergy map
│   │   │   └── Debug.jsx        # Pipeline state inspector
│   │   ├── lib/
│   │   │   └── api.js           # All fetch calls to FastAPI (28+ functions)
│   │   └── App.jsx
│   └── package.json
├── uploads/                     # Temp file storage (gitignored)
├── convictai.db                 # SQLite (auto-created, gitignored)
└── requirements.txt
```

---

## The Memory Layer — SQLite Schema

### Table: deal_history
```sql
id, startup_name, sector, stage, geography, business_model_type,
date_evaluated, business_score, esg_composite, esg_e, esg_s, esg_g,
data_completeness, confidence_level, conviction_delta, final_score,
decision, decision_reason, red_flags (JSON), blind_spots (JSON),
fix_verdict, outcome, outcome_notes, compliance_health_score,
is_seed_data, is_pipeline
```
- `is_pipeline=True` → shows in Dashboard pipeline table
- `is_pipeline=False` → history-only (used by memory agent, not shown in Dashboard)
- `is_seed_data=True` → both history deals AND pre-seeded pipeline deals

### Table: entity_sectors
```sql
sector_name, total_evaluations, total_pursued, win_rate,
avg_business_score, avg_esg_score, trend_direction
```

### Table: entity_founders
```sql
name, deals_seen_in (JSON), sectors (JSON), prior_outcomes (JSON)
```

### Table: portfolio_companies
```sql
company_name, sector, stage, geography, business_model_type,
esg_tier, current_status, compliance_health_score
```

### Table: cached_evaluations
```sql
startup_name (PK), evaluation_json, cached_at
```
EduFlow is pre-cached for instant demo render.
Every successful `POST /evaluate` upserts a row here via `db.merge()` (overwrites on re-eval).
`GET /evaluate/cached/{name}` falls back to `deal_history` when no cache row exists, returning
a partial response (`is_partial=true`) instead of 404. Never call `.scalar_one_or_none()` on
snapshot/ledger tables — use `.scalars().first()` since these tables accumulate rows over time.

### Monitor Tables
```sql
monitor_agreements, monitor_transactions, monitor_ledger_snapshots, monitor_alerts
```

### Synergy Tables
```sql
synergy_profiles, synergy_pairs, synergy_gaps, gap_shortlist
```

---

## Seed Data — Load on Startup

Pre-load these 6 deals into `deal_history` on first run (is_seed_data=True, is_pipeline=False):

| startup_name | sector | stage | business_score | esg_composite | decision | outcome |
|---|---|---|---|---|---|---|
| AlphaLearn | EdTech | Seed | 76 | 68 | pursue | Stalled at Series A — founder-led sales |
| PayFlow | FinTech | Seed | 81 | 52 | pursue | Invested — performing |
| GreenHaul | Logistics | Series A | 69 | 44 | pass | Failed — gig labor regulatory risk |
| MedTrack | HealthTech | Seed | 74 | 79 | pursue | Invested — performing |
| BuildBot | Construction Tech | Pre-seed | 58 | 61 | pass | Unknown — still operating |
| DataVault | SaaS | Seed | 83 | 71 | pursue | Invested — acquired |

Also pre-load 5 pipeline startups (is_seed_data=True, is_pipeline=True):

| startup_name | sector | stage | business_score | esg_composite | conviction_delta | final_score | decision |
|---|---|---|---|---|---|---|---|
| EduFlow | EdTech | Seed | 78 | 61 | -6 | 72 | watch |
| NovaPay | FinTech | Pre-seed | 82 | 74 | +4 | 80 | pursue |
| CargoZip | Logistics | Series A | 65 | 42 | -8 | 54 | soft_pass |
| HealthCore | HealthTech | Seed | 71 | 80 | +2 | 76 | pursue |
| BuildSmart | Construction Tech | Seed | 66 | 63 | 0 | 68 | watch |

---

## Layer 3 — Agent Logic Reference

### Extraction Agent (gates all others)
- Parse all uploaded files → merge text into one corpus
- Use Ollama to extract: team, market, revenue, traction, competition, financials, ESG fields
- Compute data_completeness (0–100%):
  - Critical fields (team, product, market, revenue model): each = 20 pts
  - Important fields (traction, competition, financials): each = 5 pts
  - Inconsistency detected: -10 pts per flag
- Confidence: ≥75% = HIGH, 45–74% = MEDIUM, <45% = LOW

### Business Scoring Agent (parallel)
Weights: Team 25%, Market 20%, Revenue 20%, Traction 15%, Moat 10%, Scalability 10%
Output: score per dimension + weighted composite + top 3 strengths + top 3 risks

### ESG Scoring Agent (parallel)
- E score (30%) + S score (35%) + G score (35%) = composite
- Scan for 10 red flag patterns (see ESG Knowledge Base)
- Tier: 80–100=Strong, 60–79=Adequate, 40–59=Weak, 0–39=Critical
- Verifiability: High/Medium/Low

### Memory Matching Agent (parallel)
Similarity weights: sector 30%, stage 20%, model 15%, revenue 10%, geography 10%, team 10%, ESG tier 5%
Conviction delta: average of top 3 matches, capped at ±20

### Forecasting Agent (parallel)
- Revenue trajectory: base/optimistic/conservative (12-month)
- Success probability: sector base rate + adjustments
- ROI estimate: from comparable exits in memory (with disclaimer)
- Sector trend signal

### Fix Analysis Agent (parallel)
- Problems: any dimension <50, any red flag, any blind spot
- Fix score 1–5 per problem
- Conditional score = final_score + top 3 fix deltas
- Verdict: invest_fix / condition / fix_first / structural_pass

### Score Aggregator
```
adjusted_business = business_score + conviction_delta
final_score = (adjusted_business × 0.70) + (esg_composite × 0.30)
```
Apply mandate hard-pass conditions before issuing verdict.

### Verdict Mapping
- 75–100 → PURSUE
- 60–74 → WATCH
- 45–59 → SOFT PASS
- 0–44 → PASS
- Mandate breach → PASS regardless

---

## ESG Red Flag Library (10 patterns — hardcoded)

| Code | Pattern | Axis | Deduction |
|---|---|---|---|
| RF-01 | "proprietary data" or "user data" without privacy policy | S | -10 |
| RF-02 | Supply chain in jurisdictions with labor violations | S | -8 |
| RF-03 | Founder unilateral veto over all board decisions | G | -15 |
| RF-04 | Environmental claims with no methodology cited | E | -10 |
| RF-05 | Diversity mentioned, no named diverse leaders | S | -5 |
| RF-06 | Financial projections with no stated assumptions | G | -8 |
| RF-07 | Team section, no LinkedIn or verifiable history | G | -7 |
| RF-08 | Revenue figures inconsistent between documents | G | -10 |
| RF-09 | Solo founder, no board, no advisors | G | -15 |
| RF-10 | "Impact" or "social good" claimed, no evidence | S | -5 |

---

## The OCR Demo (Faked — Layer 1.5)

When user uploads an IMAGE file (jpg/png):
1. Frontend detects image extension
2. Triggers `OCRAnimationGate` component:
   - Step 1: "Quality check" — progress bar fills over 1.5s
   - Step 2: "Pre-processing" — 4 operations appear one by one (deskew, binarize, denoise, normalize)
   - Step 3: "OCR scanning" — extracted text lines appear line by line with a cursor effect
   - Step 4: "Structuring document" — section headers appear (Team, Market, Revenue, etc.)
   - Step 5: Investor review gate — all sections shown as editable fields with confidence badges
3. "Confirm and Analyse" button → sends `scanned_result.json` payload to backend as if it were a normal extraction
4. Backend processes it through all agents normally

The pre-loaded `scanned_result.json` is for **"EduTech Tunisia"** — a fictional EdTech startup pitch photo. This is the startup uploaded live during the pitch demo.

---

## Demo Flow (8 Minutes — Rehearse This)

1. **(0:30)** Open dashboard — show comparison table with 5 pre-loaded startups
2. **(0:45)** Click EduFlow — show all 8 cards rendered (instant — pre-cached)
3. **(0:30)** Point to conviction delta card — explain -6 from AlphaLearn match
4. **(0:30)** Show forecast card — 52% success probability, sector trend
5. **(0:45)** Show fix analysis — conditional score jump from 72 → 81 with 3 fixes
6. **(0:30)** Show portfolio fit — sector concentration warning
7. **(0:30)** Show blind spot report — read one question aloud
8. **(1:00)** Upload phone photo of "EduTech Tunisia" — run OCR animation
9. **(0:30)** Investor review gate — edit one field live
10. **(0:30)** Confirm → show full scorecard generated from physical doc
11. **(0:30)** Change mandate ESG threshold — watch a startup flip to PASS
12. **(0:30)** Wrap

---

## Ollama Call Pattern — Use This Everywhere

```python
import httpx
import json
import os

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_A = "mistral"   # or phi3:mini
MODEL_B = "llama3.2:3b"  # or tinyllama

async def call_ollama(model: str, system: str, user: str) -> dict:
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "stream": False,
                "format": "json"
            }
        )
        content = response.json()["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Retry once
            response2 = await client.post(...)
            try:
                return json.loads(response2.json()["message"]["content"])
            except:
                return {}  # Safe default — never crash the pipeline
```

All agent system prompts must end with:
`"Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks."`

---

## Parallel Agent Execution Pattern

```python
import asyncio

async def run_evaluation(extracted_data, mandate, memory_context):
    results = await asyncio.gather(
        business_agent(extracted_data),
        esg_agent(extracted_data, mandate),
        memory_agent(extracted_data, memory_context),
        forecasting_agent(extracted_data, memory_context),
        fix_agent(extracted_data),
        return_exceptions=True  # never let one agent crash everything
    )
    business, esg, memory, forecast, fix = results
    return aggregate(business, esg, memory, forecast, fix, mandate)
```

---

## Frontend Streaming — Prevent Blank Screen

The demo must never show a blank screen while Ollama thinks.

Pattern: SSE (Server-Sent Events) or polling.
- Backend: after each agent completes, emit a partial result
- Frontend: render each card as its data arrives
- Show skeleton cards with a pulsing animation while waiting
- Cards "snap in" with a fade + slide animation when data arrives (Framer Motion)

Loading sequence visible to judges:
```
[Extracting documents...]        → skeleton cards appear
[Scoring business...]            → Scorecard card snaps in (partial)
[Analysing ESG...]               → ESG card snaps in
[Checking memory...]             → Memory Insight card snaps in
[Forecasting trajectory...]      → Forecast card snaps in
[Analysing fix worthiness...]    → Fix Analysis card snaps in
[Mapping portfolio fit...]       → Portfolio Fit card snaps in
[Generating blind spots...]      → Blind Spot card snaps in
[Generating recommendation...]   → verdict finalised
```

---

## Phase Breakdown

---

### PHASE 1 — Foundation ✅ COMPLETE (2026-05-16)
**Goal:** Running app skeleton, file upload works, SQLite seeded, forms functional.

Tasks:
- [x] Initialize FastAPI app with CORS, static files, health check endpoint
- [x] SQLAlchemy models + SQLite setup + auto-create tables on startup
- [x] Seed loader: runs once on startup, inserts 6 history + 5 pipeline records
- [x] Multi-file upload endpoint: `/api/upload` → saves to `/uploads/{startup_id}/`
- [x] Startup profile form endpoint: `/api/startup/profile`
- [x] Mandate config endpoint: `/api/mandate` (GET + POST, persists to SQLite)
- [x] React + Vite + Tailwind + shadcn setup
- [x] `FileUploader.jsx` — drag-drop, multiple files, progress bar
- [x] `StartupProfileForm.jsx` — 6 fields, dropdown selects
- [x] `MandateConfigForm.jsx` — fund config, persists
- [x] `Dashboard.jsx` — pipeline table (inline), loads 5 pre-seeded pipeline startups
- [x] `api.js` — all fetch wrapper functions

---

### PHASE 2 — AI Engine Core ✅ COMPLETE (2026-05-16)
**Goal:** Extraction + Business + ESG agents working. First scorecard renders.

Tasks:
- [x] `parsers/pdf_parser.py` — PyMuPDF text extraction
- [x] `parsers/docx_parser.py` — python-docx extraction
- [x] `parsers/xlsx_parser.py` — openpyxl extraction
- [x] Document merger: combine text from all uploaded files for one startup
- [x] `agents/extraction.py` — Ollama call → normalized JSON schema + completeness score + blind spots
- [x] `agents/business.py` — 6 dimensions → weighted score + strengths + risks
- [x] `agents/esg.py` — E/S/G scoring + red flag scan + tier + verifiability
- [x] `engine/aggregator.py` — partial aggregation (business + ESG only, no delta yet)
- [x] `engine/recommendation.py` — verdict + reasoning
- [x] `/api/evaluate` endpoint — orchestrates full pipeline
- [x] `ScorecardCard.jsx`, `ESGCard.jsx`, shared components
- [x] `Evaluate.jsx` page — upload → form → loading → cards rendered

---

### PHASE 3 — Memory Layer ✅ COMPLETE (2026-05-16)
**Goal:** Memory matching works. Conviction delta shows on scorecard. Feedback loop writes to DB.

Tasks:
- [x] `agents/memory.py` — similarity computation + conviction delta calculation
- [x] Sector conviction signal from `entity_sectors` table
- [x] Update `engine/aggregator.py` — apply conviction delta to final score formula
- [x] `engine/feedback_loop.py` — write complete deal record to SQLite after eval (is_pipeline=True)
- [x] Update `entity_sectors` table after each evaluation
- [x] `MemoryInsightCard.jsx` — delta number, top 3 similar deals, sector conviction
- [x] `Dashboard.jsx` — live comparison table with newly evaluated startups appearing

---

### PHASE 4 — Forecasting + Fix Analysis ✅ COMPLETE (2026-05-16)
**Goal:** Forecast card and Fix Analysis card fully rendered with AI-generated content.

Tasks:
- [x] `agents/forecasting.py` — revenue trajectory (3 scenarios) + success probability + ROI + sector trend
- [x] `agents/fix_analysis.py` — problem detection + fix scores + conditional score + prioritized actions + verdict
- [x] Update parallel `asyncio.gather` call to include forecasting + fix agents
- [x] `ForecastCard.jsx` — 3 revenue scenarios, probability %, ROI estimate, disclaimer banner
- [x] `FixAnalysisCard.jsx` — current vs conditional score, verdict badge, 3 priority actions

---

### PHASE 5 — Portfolio Engine + Remaining Cards ✅ COMPLETE (2026-05-16)
**Goal:** All 8 output cards rendered. Portfolio fit works. Blind spot report complete.

Tasks:
- [x] `agents/portfolio.py` — sector concentration + stage balance + ESG shift + risk correlation + fit verdict
- [x] Pipeline optimizer (if ≥2 pursue/watch in DB)
- [x] `PortfolioFitCard.jsx` — concentration chart (Recharts pie), stage map, ESG shift, warnings
- [x] `BlindSpotCard.jsx` — numbered list, risk per blind spot, meeting question per blind spot
- [x] Mandate filter: apply hard-pass conditions in aggregator
- [x] POST `/api/mandate/apply` — re-checks all pipeline startups against new mandate

---

### PHASE 6 — OCR Animation + Demo Prep ✅ COMPLETE (2026-05-17)
**Goal:** OCR demo sequence works. App is demo-ready. All edge cases handled.

Tasks:
- [x] `ocr_mock/scanned_result.json` — pre-parsed EduTech Tunisia startup data
- [x] `/api/ocr-mock` + `/api/ocr-confirm` endpoints
- [x] `OCRAnimationGate.jsx` — 5-step animated sequence (Framer Motion)
- [x] Physical scan notice on scorecard when source = PHYSICAL_SCAN
- [x] Pre-cached EduFlow result for instant demo render
- [x] Mandate change demo: lower ESG threshold → NovaPay flips to PASS live
- [x] Framer Motion stagger card reveal
- [x] Ollama offline detection → friendly error card, not crash
- [x] 90s timeout warning in Evaluate.jsx

---

### MONITOR MODULE ✅ COMPLETE (2026-05-17)
Post-investment compliance monitoring. Tracks fund agreements, classifies bank statements,
detects off-plan spending, computes compliance health score per portfolio company.

Key files: `backend/monitor/`, `frontend/src/components/monitor/`, `frontend/src/pages/Monitor.jsx`

Pre-seeded: NovaPay (health=87), EduFlow (health=61), BuildSmart (health=34)

---

### SYNERGY MODULE ✅ COMPLETE (2026-05-17)
Portfolio synergy detection. Extracts capability profiles from deal documents, scores
company pairs on service bridge / shared customers / co-dev potential, detects portfolio gaps.

Key files: `backend/synergy/`, `frontend/src/components/synergy/`, `frontend/src/pages/Synergy.jsx`

Pre-seeded: 5 profiles, 7 pairs, 5 gaps.

---

## Score Color Coding — Use Everywhere

```
75–100  →  green   (#22c55e)  var(--s-green)
60–74   →  amber   (#f59e0b)  var(--s-amber)
45–59   →  orange  (#f97316)  var(--s-orange)
0–44    →  red     (#ef4444)  var(--s-red)
```

Confidence badges:
```
HIGH    →  green pill
MEDIUM  →  yellow pill
LOW     →  red pill
```

ESG Tier badges:
```
Strong        →  green
Adequate      →  blue
Weak          →  orange
Critical Risk →  red
```

---

## Ollama System Prompts — Templates

### Extraction Agent
```
You are a document analysis AI for investment screening.
Extract structured information from the following startup documents.
Return ONLY a valid JSON object with these exact keys:
founder_names, team_size, domain_expertise, prior_exits,
tam_stated, tam_source, growth_rate, revenue_model,
current_revenue, projected_revenue_y1, unit_economics,
user_count, customer_count, traction_evidence,
competitors_named, differentiation, ip_mentioned,
labor_model, env_claims, governance_docs, board_named,
diversity_claimed, funding_ask, inconsistencies.
If a field is not found, use null.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks.
```

### Business Scoring Agent
```
You are an investment analyst scoring a startup across 6 dimensions.
Score each from 0–100. Return ONLY a valid JSON object with:
team_score, market_score, revenue_score, traction_score,
moat_score, scalability_score, composite_score,
top_strengths (array of 3 strings), top_risks (array of 3 strings).
Scoring weights: team=25%, market=20%, revenue=20%, traction=15%, moat=10%, scalability=10%.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks.
```

### ESG Scoring Agent
```
You are an ESG analyst evaluating a startup for responsible investment screening.
Score Environmental (0–100), Social (0–100), Governance (0–100).
Check for these red flags: [list all 10 RF codes and patterns].
Return ONLY a valid JSON object with:
e_score, s_score, g_score, composite,
tier (Strong/Adequate/Weak/Critical Risk),
red_flags_triggered (array of RF codes),
verifiability (High/Medium/Low),
most_critical_flag (string or null).
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks.
```

---

## What Claude Code Must Never Do

- Never use `time.sleep()` — use `asyncio.sleep()` instead
- Never block the event loop — all I/O must be async
- Never crash if Ollama returns malformed JSON — always return a safe default
- Never hardcode the startup name "EduFlow" in the AI logic — it comes from the DB
- Never skip the mandate filter — it must run before every verdict
- Never display a confidence of HIGH when data_completeness < 75%
- Never show forecast numbers without the disclaimer
- Never let the portfolio agent crash if portfolio_companies table is empty
- Never query `DealHistory` for the pipeline without `WHERE is_pipeline = True` — the 6 history deals must stay hidden from the Dashboard

---

## How to Run

### Prerequisites
```powershell
ollama pull mistral
ollama pull llama3.2:3b
```

### Terminal 1 — Ollama
```powershell
ollama serve
```

### Terminal 2 — Backend (from project root)
```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

### Terminal 3 — Frontend
```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`. Health check: `http://localhost:8000/api/health`

To force a clean re-seed, delete `convictai.db` before starting the backend.

---

## Requirements File

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
pydantic==2.7.1
python-multipart==0.0.9
httpx==0.27.0
PyMuPDF==1.24.3
python-docx==1.1.2
openpyxl==3.1.2
aiosqlite==0.20.0
```

---

*This file is the single source of truth for Claude Code.*
*All phases are complete. Do not re-implement. Read existing code before adding.*
*Built for the CapAI Hackathon — pre-investment axis.*
