# ConvictAI — Full Project Report
**Generated:** 2026-06-09  
**Status:** All phases complete. Demo-ready.  
**Built for:** CapAI Hackathon — pre-investment axis

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Database Schema](#4-database-schema)
5. [Backend — Modules & Endpoints](#5-backend--modules--endpoints)
6. [Agent Pipeline](#6-agent-pipeline)
7. [Frontend — Pages & Components](#7-frontend--pages--components)
8. [Monitor Module](#8-monitor-module)
9. [Synergy Module](#9-synergy-module)
10. [Seed Data](#10-seed-data)
11. [OCR Demo Flow](#11-ocr-demo-flow)
12. [Demo Script (8 Minutes)](#12-demo-script-8-minutes)
13. [How to Run](#13-how-to-run)
14. [Diagnostic & Fixes Applied](#14-diagnostic--fixes-applied)
15. [File Tree](#15-file-tree)

---

## 1. Project Overview

**ConvictAI** is an AI-powered pre-investment screening engine for startup investors. It takes multiple uploaded documents (pitch decks, financials, one-pagers) and runs them through a multi-agent AI pipeline that produces 8 structured output cards.

**Core differentiator:** Memory. Every evaluation is stored in SQLite. Future evaluations are cross-referenced against past deals to produce a **conviction delta** — a score adjustment based on how similar deals performed historically.

**One sentence:** Every other AI tool forgets. Ours remembers.

### What It Does

| Feature | Description |
|---------|-------------|
| Document ingestion | PDF, DOCX, XLSX multi-file upload per startup |
| Business scoring | 6-dimension weighted score (Team, Market, Revenue, Traction, Moat, Scalability) |
| ESG scoring | E/S/G axes + 10 red flag patterns + tier classification |
| Memory matching | Similarity search against all historical deals → conviction delta |
| Forecasting | 3-scenario revenue trajectory, success probability, ROI estimate |
| Fix analysis | Identifies fixable problems, conditional score improvement |
| Portfolio fit | Sector concentration, stage balance, ESG shift, correlation risk |
| Blind spots | Missing data fields + due diligence questions for investor meetings |
| Mandate enforcement | Fund-level hard-pass conditions applied before every verdict |
| OCR demo | Faked 5-step animation for physical document uploads |
| Compliance monitoring | Post-investment agreement tracking + bank statement classification |
| Synergy mapping | Portfolio company capability matching + gap detection |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND  React 18 + Vite  :5173                               │
│  Dashboard · Evaluate · Mandate · Monitor · Synergy · Debug     │
└─────────────────────────┬───────────────────────────────────────┘
                          │ fetch (REST)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND  FastAPI  :8000                                        │
│                                                                 │
│  POST /api/evaluate  ──►  Layer 3 Pipeline:                     │
│                           Step 1: Extraction Agent              │
│                           Step 2: Business + ESG (parallel)     │
│                           Step 3: Memory Matching               │
│                           Step 4: Aggregate + Mandate Filter    │
│                           Step 5: Forecast + Fix + Portfolio    │
│                                   (parallel)                    │
│                           Step 6: Feedback Loop (fire-forget)   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌─────────────┐  ┌──────────┐  ┌─────────────┐
   │  SQLite DB  │  │  Ollama  │  │  /uploads/  │
   │ convictai.db│  │ :11434   │  │  (files)    │
   └─────────────┘  └──────────┘  └─────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite only | No external dependencies, runs on any laptop |
| Ollama + local models | No paid API, works offline during demo |
| asyncio.gather for agents | All 5 scoring agents run in parallel — 5× faster |
| Fire-and-forget DB write | DB write never blocks the API response |
| Pre-cached EduFlow | Instant render on demo day — no Ollama wait |
| is_pipeline flag | Separates history deals from active pipeline in Dashboard |
| Faked OCR | No Tesseract install needed, animation is more impressive anyway |

---

## 3. Tech Stack

### Backend
| Library | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.111.0 | Async REST API |
| uvicorn | 0.29.0 | ASGI server |
| SQLAlchemy | 2.0.30 | ORM + async sessions |
| aiosqlite | 0.20.0 | Async SQLite driver |
| Pydantic | 2.7.1 | Request/response schemas |
| httpx | 0.27.0 | Async Ollama HTTP calls |
| PyMuPDF | 1.24.3 | PDF text extraction |
| python-docx | 1.1.2 | DOCX parsing |
| openpyxl | 3.1.2 | XLSX parsing |
| python-multipart | 0.0.9 | File upload handling |

### Frontend
| Library | Version | Purpose |
|---------|---------|---------|
| React | 18.3.1 | UI framework |
| Vite | 5.2.11 | Build tool + dev server |
| react-router-dom | 6.23.1 | Client-side routing |
| framer-motion | 11.2.10 | OCR animation, card stagger |
| recharts | 2.12.7 | ESG bars, sector pie chart |
| react-dropzone | 14.2.3 | Multi-file upload |
| @radix-ui/* | various | Dialog, Select, Tabs, Toast |
| lucide-react | 0.383.0 | Icons |

**Styling:** All inline CSS with CSS custom properties (`var(--s-green)`, `var(--surface-1)`, etc.). No Tailwind utility classes in components.

### LLM
| Model | Role | Used by |
|-------|------|---------|
| mistral | Model A — structured extraction + scoring | extraction, business, esg agents |
| llama3.2:3b | Model B — narrative text generation | memory, forecasting, fix_analysis agents |

Ollama endpoint: `http://localhost:11434` (overridable via `OLLAMA_BASE_URL` env var)  
Timeout: 90 seconds per call  
Retry: once on JSON parse failure, then safe default `{}`

---

## 4. Database Schema

### deal_history
Primary storage for all evaluated startups.

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| startup_name | TEXT | |
| sector | TEXT | |
| stage | TEXT | Seed / Pre-seed / Series A |
| geography | TEXT | nullable |
| business_model_type | TEXT | nullable |
| date_evaluated | TEXT | ISO date string |
| business_score | INTEGER | 0–100 |
| esg_composite | INTEGER | 0–100 |
| esg_e | INTEGER | nullable |
| esg_s | INTEGER | nullable |
| esg_g | INTEGER | nullable |
| data_completeness | INTEGER | 0–100 |
| confidence_level | TEXT | HIGH / MEDIUM / LOW |
| conviction_delta | INTEGER | –20 to +20 |
| final_score | INTEGER | 0–100 |
| decision | TEXT | pursue / watch / soft_pass / pass |
| decision_reason | TEXT | nullable |
| red_flags | TEXT | JSON array of RF codes |
| blind_spots | TEXT | JSON array |
| fix_verdict | TEXT | nullable |
| outcome | TEXT | nullable — filled after investment |
| outcome_notes | TEXT | nullable |
| compliance_health_score | INTEGER | nullable — filled by Monitor module |
| is_seed_data | BOOLEAN | True for all pre-loaded records |
| is_pipeline | BOOLEAN | True = shows in Dashboard; False = history only |

### entity_sectors
Tracks sector-level conviction signals.

| Column | Type |
|--------|------|
| sector_name | TEXT UNIQUE |
| total_evaluations | INTEGER |
| total_pursued | INTEGER |
| win_rate | FLOAT |
| avg_business_score | FLOAT |
| avg_esg_score | FLOAT |
| trend_direction | TEXT (improving / stable / declining) |

### portfolio_companies
Current fund portfolio for concentration analysis.

| Column | Type |
|--------|------|
| company_name | TEXT |
| sector | TEXT |
| stage | TEXT |
| geography | TEXT |
| business_model_type | TEXT |
| esg_tier | TEXT |
| current_status | TEXT |
| compliance_health_score | INTEGER |

### mandate_config
Single row (id=1). Fund investment mandate.

| Column | Type |
|--------|------|
| sector_focus | TEXT (JSON array) |
| stage_preference | TEXT (JSON array) |
| geography_scope | TEXT (JSON array) |
| min_esg_threshold | INTEGER |
| ticket_size_min | INTEGER |
| ticket_size_max | INTEGER |
| esg_priority_axis | TEXT |

### cached_evaluations
Pre-computed full evaluation results for instant demo renders.

| Column | Type |
|--------|------|
| startup_name | TEXT PK |
| evaluation_json | TEXT (full response JSON) |
| cached_at | TEXT |

EduFlow is pre-cached here for the demo (instant render without Ollama).

### Monitor Tables

**monitor_agreements** — Investment agreements uploaded per portfolio company  
**monitor_transactions** — Bank statement line items, classified by AI  
**monitor_ledger_snapshots** — Monthly compliance snapshots per company  
**monitor_alerts** — Triggered compliance alerts (off-plan spending, overbudget, etc.)

### Synergy Tables

**synergy_profiles** — Capability profiles extracted from deal documents  
**synergy_pairs** — Scored company pairs (service bridge, shared customers, co-dev)  
**synergy_gaps** — Portfolio-wide needs not met by any current company  
**gap_shortlist** — External companies shortlisted to fill a gap

---

## 5. Backend — Modules & Endpoints

### Core Routers

#### `POST /api/upload`
Upload files for a startup. Saves to `/uploads/{startup_id}/`.

**Body:** `multipart/form-data` — `startup_id`, one or more files  
**Returns:** `{ startup_id, files_saved, file_names }`

---

#### `GET /api/pipeline`
Returns all `is_pipeline=True` deals ordered by final_score descending.  
Used by Dashboard to populate the comparison table.

**Returns:** `List[DealSummary]` — 5 pre-seeded + any newly evaluated startups

> **Critical:** Must always filter `WHERE is_pipeline = True`. The 6 history deals (AlphaLearn, PayFlow, etc.) have `is_pipeline=False` and must never appear in this list.

---

#### `POST /api/evaluate`
Main evaluation endpoint. Full 6-step pipeline.

**Body:**
```json
{
  "startup_name": "string",
  "startup_id": "string",
  "sector": "string",
  "stage": "string",
  "geography": "string",
  "business_model_type": "string",
  "funding_asked": 500000
}
```

**Pipeline:**
1. Merge uploaded files → document text
2. Extraction agent → structured fields + completeness + blind spots
3. Business + ESG agents in parallel
4. Memory matching → conviction delta
5. Load mandate → aggregate scores → generate verdict
6. Forecast + Fix + Portfolio agents in parallel
7. Fire-and-forget: write deal record to DB

**Returns:** Full evaluation payload (all 8 card data sections)

**Errors:**
- `503` — Ollama not running
- `404` — No uploaded files found for startup_id
- `422` — Files uploaded but no text could be extracted

---

#### `GET /api/evaluate/cached/{startup_name}`
Returns pre-cached evaluation JSON. Used by Dashboard row clicks.

---

#### `GET /api/mandate` / `POST /api/mandate`
Get or update fund mandate configuration.

#### `POST /api/mandate/apply`
Re-evaluates all pipeline startups against the current mandate. Flips decision to "pass" for any breaches. Called after mandate save.

---

#### `GET /api/ocr-mock`
Returns the pre-parsed `scanned_result.json` for EduTech Tunisia.

#### `POST /api/ocr-confirm`
Receives the investor-reviewed OCR data and runs it through the full evaluation pipeline (skips extraction step — data already structured).

---

#### `GET /api/health`
Returns `{ status: "ok", service: "ConvictAI", ollama: true/false }`.

---

### Monitor Router (`/api/monitor/...`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/monitor/agreement/upload` | POST | Upload investment agreement PDF/DOCX, Ollama extracts structure |
| `/monitor/dashboard/{name}` | GET | Full compliance dashboard for one company |
| `/monitor/portfolio-health` | GET | Summary health scores for all monitored companies |
| `/monitor/statement/upload` | POST | Upload bank statement, classify transactions |
| `/monitor/statement/no-statement` | POST | Mark a month as no-statement-available |
| `/monitor/transactions/{name}` | GET | Paginated transaction log with filters |
| `/monitor/transaction/{id}/classify` | PATCH | Re-classify a single transaction |
| `/monitor/ocr-mock` | GET | Pre-parsed bank statement for OCR demo |
| `/monitor/ocr-confirm` | POST | Confirm OCR-reviewed transactions |

---

### Synergy Router (`/api/synergy/...`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/synergy/status` | GET | Overview: profiles ready, pairs scored, gaps found |
| `/synergy/pairs` | GET | All scored company pairs |
| `/synergy/pair/{id}/decide` | PATCH | Analyst approve/dismiss/snooze a pair |
| `/synergy/gaps` | GET | All portfolio gaps |
| `/synergy/gap/{id}/shortlist` | GET | External companies shortlisted for a gap |
| `/synergy/company/{name}/summary` | GET | Synergy summary for one company (counts) |

---

## 6. Agent Pipeline

### Execution Flow

```
POST /api/evaluate
       │
       ▼
  ┌─────────────────────────┐
  │  check_ollama_available │ ──► 503 if down
  └─────────────────────────┘
       │
       ▼
  ┌─────────────────────────┐
  │  merge_documents()      │  PDF + DOCX + XLSX → single text corpus
  └─────────────────────────┘
       │
       ▼
  ┌─────────────────────────┐
  │  run_extraction()       │  Ollama Model A
  │  → extracted fields     │  → data_completeness (0–100)
  │  → blind_spots          │  → confidence_level
  └─────────────────────────┘
       │
       ▼  asyncio.gather
  ┌────────────┐  ┌────────────┐
  │ business() │  │   esg()    │  Both call Ollama Model A in parallel
  └────────────┘  └────────────┘
       │
       ▼
  ┌─────────────────────────┐
  │  run_memory_matching()  │  Pure Python similarity (no Ollama)
  │  → top 3 matches        │  Weights: sector 30%, stage 20%,
  │  → conviction_delta     │  model 15%, revenue 10%, geo 10%,
  │  → sector_conviction    │  team 10%, ESG tier 5%
  └─────────────────────────┘
       │
       ▼
  ┌─────────────────────────┐
  │  aggregate_scores()     │  adjusted_business = business + delta
  │  generate_verdict()     │  final = (adj_business × 0.70) + (esg × 0.30)
  └─────────────────────────┘
       │
       ▼  asyncio.gather
  ┌────────────┐  ┌────────┐  ┌────────────┐
  │ forecast() │  │ fix()  │  │ portfolio()│
  └────────────┘  └────────┘  └────────────┘
       │
       ▼  asyncio.create_task (fire-and-forget)
  ┌─────────────────────────┐
  │  write_deal_record()    │  Saves to deal_history (is_pipeline=True)
  │  _update_sector_entity()│  Updates entity_sectors win_rate + trend
  └─────────────────────────┘
       │
       ▼
  Return full response payload
```

### Agent Details

#### Extraction Agent (`agents/extraction.py`)
- **Model:** Model A (mistral)
- **Input:** Merged document text
- **Output:** 24 structured fields + data_completeness + confidence_level + blind_spots
- **Completeness scoring:**
  - Critical fields (team, product, market, revenue model): 20 pts each
  - Important fields (traction, competition, financials): 5 pts each
  - Inconsistency flag: –10 pts per flag
- **Confidence:** ≥75% = HIGH, 45–74% = MEDIUM, <45% = LOW

#### Business Scoring Agent (`agents/business.py`)
- **Model:** Model A (mistral)
- **Weights:** Team 25%, Market 20%, Revenue 20%, Traction 15%, Moat 10%, Scalability 10%
- **Output:** 6 dimension scores + composite + top 3 strengths + top 3 risks

#### ESG Scoring Agent (`agents/esg.py`)
- **Model:** Model A (mistral)
- **Weights:** E 30%, S 35%, G 35%
- **Red flags:** 10 hardcoded patterns (RF-01 to RF-10)
- **Tiers:** Strong (80–100), Adequate (60–79), Weak (40–59), Critical Risk (0–39)
- **Output:** E/S/G scores + composite + tier + red_flags_triggered + verifiability

#### Memory Matching Agent (`agents/memory.py`)
- **Model:** Model B (llama3.2:3b) — for explanation text only; matching is pure Python
- **Similarity weights:** Sector 30%, Stage 20%, Model 15%, Revenue 10%, Geography 10%, Team 10%, ESG tier 5%
- **Delta calculation:** Average of top 3 match deltas, capped at ±20
- **Output:** top_matches + conviction_delta + sector_conviction + delta_explanation

#### Forecasting Agent (`agents/forecasting.py`)
- **Model:** Model A for revenue trajectory; success probability is deterministic Python
- **Revenue trajectory:** Base / Optimistic / Conservative (12-month)
- **Success probability:** Sector base rate + 5 adjustments
- **ROI estimate:** From comparable DB exits (with mandatory disclaimer)
- **Disclaimer:** "AI-reasoned estimates. Not a financial model. Use for directional comparison only."

#### Fix Analysis Agent (`agents/fix_analysis.py`)
- **Model:** Model B for action text; problem detection is pure Python
- **Problem detection:** Any dimension <50, any ESG red flag, any blind spot
- **Fix score:** 1–5 per problem
- **Conditional score:** final_score + top 3 fix deltas (capped at 100)
- **Verdicts:** invest_fix / condition / fix_first / structural_pass

#### Portfolio Agent (`agents/portfolio.py`)
- **No Ollama calls** — entirely pure Python
- **Sector concentration:** Warns if any sector >35% of portfolio
- **ESG shift:** Calculates weighted average ESG before/after adding new startup
- **Correlation risk:** Flags startups with same sector + same business model
- **Pipeline optimizer:** Suggests best 2-startup combination from pursue/watch deals

### Score Aggregation Formula

```
adjusted_business = business_score + conviction_delta
final_score = (adjusted_business × 0.70) + (esg_composite × 0.30)
```

### Verdict Mapping

| Score Range | Verdict |
|-------------|---------|
| 75–100 | PURSUE |
| 60–74 | WATCH |
| 45–59 | SOFT PASS |
| 0–44 | PASS |
| Mandate breach | PASS (regardless of score) |

---

## 7. Frontend — Pages & Components

### Pages

#### `Dashboard.jsx`
- Loads all `is_pipeline=True` deals via `GET /api/pipeline`
- Shows 4 stat cards: Total / Pursue / Watch / Pass
- Inline HTML table with sortable columns: Company, Sector, Stage, Business, ESG, Δ Memory, Score, Verdict, Confidence, Synergy
- Each row navigates to `/evaluate?cached={startup_name}` on click
- Synergy chips (green=approved, amber=pending, purple=gaps) per company — fetched in parallel via `getCompanySummary()`
- Skeleton rows during loading; friendly error if backend unreachable

#### `Evaluate.jsx`
- **Upload phase:** FileUploader (react-dropzone) + StartupProfileForm (6 fields)
- **OCR gate:** Detects image uploads → triggers OCRAnimationGate instead of normal flow
- **Loading phase:** 9-step progress messages + 7 skeleton cards (Framer Motion pulse)
- **Ollama offline:** Shows OllamaOfflineCard with setup instructions + retry button
- **90s timeout warning:** Shown if evaluation takes longer than expected
- **Results phase:** All 8 cards rendered with Framer Motion stagger (0.08s delay each)
- **Mandate banner:** Red = force_pass breach; Amber = advisory flags
- **Physical scan banner:** Shown when source_type = PHYSICAL_SCAN

#### `Mandate.jsx`
- MandateConfigForm with all mandate fields
- On save: calls `POST /api/mandate` then `POST /api/mandate/apply`
- Shows reclassification result toast (N startups re-evaluated)

#### `Monitor.jsx`
- Sidebar navigation: one entry per monitored company
- Tabs: Dashboard / Transactions / Upload
- ComplianceDashboard: RadialBar health score, BudgetTracker, TimelineChart, AlertPanel
- TransactionLog: table with inline reclassification dropdown for UNCLASSIFIED items
- StatementUploader: image detection → MonitorOCRAnimationGate fork

#### `Synergy.jsx`
- Portfolio graph visualization (PortfolioGraph)
- SynergyPairTable: all scored pairs with analyst decision buttons
- GapPanel: portfolio gaps + external shortlist per gap

#### `Debug.jsx`
- Real-time pipeline state inspector
- Shows agent status, Ollama call log, timing per step

### 8 Output Cards

| Card | Component | Data Source |
|------|-----------|-------------|
| Scorecard | `ScorecardCard.jsx` | final_score, dimension_scores, verdict, top_strengths/risks |
| ESG | `ESGCard.jsx` | esg_e/s/g, tier, red_flag_details, verifiability |
| Memory Insight | `MemoryInsightCard.jsx` | conviction_delta, top_memory_matches, sector_conviction |
| Forecast | `ForecastCard.jsx` | forecast.revenue_trajectory, success_probability, roi_estimate |
| Fix Analysis | `FixAnalysisCard.jsx` | fix_analysis.top_priority_actions, conditional_score, fix_verdict |
| Portfolio Fit | `PortfolioFitCard.jsx` | portfolio.sector_distribution, esg_shift, correlated_companies |
| Blind Spot | `BlindSpotCard.jsx` | blind_spots[].field + .risk + .question |

### Shared Components

| Component | Purpose |
|-----------|---------|
| `ScorePill.jsx` | Colored score badge; exports `scoreColor(n)` and `scoreBg(n)` helpers |
| `VerdictBadge.jsx` | pursue/watch/soft_pass/pass badge with semantic colors |
| `ConfidenceBadge.jsx` | HIGH/MEDIUM/LOW with colored dot + optional completeness % |
| `DeltaBadge.jsx` | +N / –N conviction delta with green/red coloring |
| `ESGBar.jsx` | E/S/G horizontal bar with color coding |
| `ScoreGauge.jsx` | Circular gauge for overall score |
| `LoadingCards.jsx` | 7 skeleton placeholder cards (pulse animation) |

### CSS Design System

All colors defined as CSS custom properties in `index.css`:

```css
--s-green:   #12B76A   /* scores 75+ */
--s-amber:   #F5A524   /* scores 60–74 */
--s-orange:  #EF6820   /* scores 45–59 */
--s-red:     #F04438   /* scores 0–44 */
--surface-1: #FFFFFF   /* card backgrounds */
--border:    #E7E9EE
--tx-1:      #111318   /* primary text */
--tx-2:      #3D4754   /* secondary text */
--tx-3:      #64748B   /* labels / disabled */
--gold:      #6E56CF   /* brand purple */
```

Fonts:
- **Outfit** — page headers
- **Inter** — body text
- **JetBrains Mono** — all numerical data

### API Client (`lib/api.js`)

28+ functions covering all backend endpoints. Base path `/api` (resolved via Vite proxy to `:8000`). Error handling: catch returns `{}` to prevent UI crash.

Key functions:
- `getPipeline()` — Dashboard table data
- `evaluateStartup(payload)` — POST /api/evaluate
- `getCachedEvaluation(name)` — instant row-click render
- `getMandate()` / `saveMandate(data)` / `applyMandate()` — mandate management
- `getOcrMock()` / `confirmOcr(data)` — OCR demo flow
- `getMonitorOcrMock()` / `confirmMonitorOcr(data)` — Monitor OCR demo
- `getCompanySummary(name)` — synergy chips in Dashboard

---

## 8. Monitor Module

Post-investment compliance monitoring system. Tracks how portfolio companies spend invested funds against their signed investment agreements.

### How It Works

1. **Upload agreement** — Investor uploads signed investment agreement (PDF/DOCX). `agreement_parser.py` uses Ollama to extract: total committed amount, budget categories with planned allocations, time milestones.

2. **Upload bank statement** — Monthly bank statement (PDF) uploaded by portfolio company. `statement_parser.py` extracts transactions. `category_agent.py` classifies each line item (keyword-first, 0.80 threshold, Ollama fallback).

3. **Ledger snapshot** — After each statement upload, `ledger.py` computes a monthly snapshot: category totals vs plan, compliance health score (0–100), alert count.

4. **Alerts** — `alert_engine.py` fires alerts for: OFF_PLAN spending, OVER_BUDGET category, UNCLASSIFIED transactions above threshold, MILESTONE_BREACH.

5. **Compliance health score** — Written back to `deal_history.compliance_health_score` for display in Dashboard.

### Pre-seeded Data (Demo)

| Company | Health Score | Alerts |
|---------|-------------|--------|
| NovaPay | 87 (Green) | 0 active |
| EduFlow | 61 (Amber) | 2 active |
| BuildSmart | 34 (Red) | 4 active |

BuildSmart is pre-seeded with 17 transactions and 4 active alerts — ideal for demo purposes.

### OCR Demo (Monitor)

`MonitorOCRAnimationGate.jsx` — 5-step bank statement OCR animation (mirrors the main OCR flow). Triggered when investor uploads an image of a bank statement instead of a PDF.

---

## 9. Synergy Module

Portfolio synergy detection system. Finds collaboration opportunities between portfolio companies and identifies market gaps that could be filled by new investments.

### How It Works

1. **Profile extraction** — `profile_extractor.py` uses Ollama to extract from deal documents: services offered, target customers, operational needs, strategic gaps.

2. **Pair scoring** — `pair_scorer.py` scores every company pair on 3 axes: service bridge (can A serve B?), shared customers (do they target the same market?), co-development potential. Composite score 0–100.

3. **Gap detection** — `gap_detector.py` analyzes operational_needs across all profiles to find common unmet needs — portfolio-wide gaps no current company fills.

4. **Gap hunting** — `gap_hunter.py` (uses Ollama) suggests external startup archetypes that could fill each gap, generating a shortlist.

### Pre-seeded Data (Demo)

- 5 company profiles (NovaPay, EduFlow, HealthCore, CargoZip, BuildSmart)
- 7 scored company pairs
- 5 portfolio gaps
- Gap shortlist fallback for offline demos

---

## 10. Seed Data

### History Deals (is_pipeline=False, is_seed_data=True)
Used only by memory matching agent. Never shown in Dashboard.

| Company | Sector | Score | ESG | Decision | Outcome |
|---------|--------|-------|-----|----------|---------|
| AlphaLearn | EdTech | 74 | 68 | pursue | Stalled at Series A |
| PayFlow | FinTech | 72 | 52 | pursue | Invested — performing |
| GreenHaul | Logistics | 63 | 44 | pass | Failed — regulatory risk |
| MedTrack | HealthTech | 76 | 79 | pursue | Invested — performing |
| BuildBot | Construction Tech | 59 | 61 | pass | Unknown — still operating |
| DataVault | SaaS | 79 | 71 | pursue | Invested — acquired |

### Pipeline Startups (is_pipeline=True, is_seed_data=True)
Shown in Dashboard on load.

| Company | Sector | Score | ESG | Δ | Decision |
|---------|--------|-------|-----|---|----------|
| EduFlow | EdTech | 72 | 61 | -6 | watch |
| NovaPay | FinTech | 80 | 74 | +4 | pursue |
| CargoZip | Logistics | 54 | 42 | -8 | soft_pass |
| HealthCore | HealthTech | 76 | 80 | +2 | pursue |
| BuildSmart | Construction Tech | 68 | 63 | 0 | watch |

### Cached Evaluation
**EduFlow** is pre-cached in `cached_evaluations` with a full, rich evaluation payload. Clicking EduFlow in the Dashboard renders all 8 cards instantly without any Ollama call.

---

## 11. OCR Demo Flow

### Steps (Triggered by image upload in Evaluate.jsx)

```
Step 1: Quality Check
  └─ Progress bar fills over 1.5s
  └─ "Checking image resolution and clarity..."

Step 2: Pre-processing
  └─ 4 operations appear one by one:
     Deskew → Binarize → Denoise → Normalize

Step 3: OCR Scanning
  └─ Extracted text lines appear line-by-line with cursor effect

Step 4: Structuring Document
  └─ Section headers appear: Team · Market · Revenue · Governance · ESG

Step 5: Investor Review Gate
  └─ All fields shown as editable inputs
  └─ Confidence badges (HIGH/MEDIUM/UNCLEAR) per field
  └─ "Confirm and Analyse" button
```

### Pre-loaded Data
`scanned_result.json` contains extracted data for **EduTech Tunisia** — a fictional EdTech startup. This is submitted to the full evaluation pipeline when the investor confirms.

Physical scan notice appears on the resulting scorecard: "This evaluation was generated from a physically scanned document."

---

## 12. Demo Script (8 Minutes)

| Time | Action |
|------|--------|
| 0:30 | Open Dashboard — 5 pre-loaded startups visible |
| 0:45 | Click EduFlow — all 8 cards render instantly (pre-cached) |
| 0:30 | Point to Memory Insight card — explain -6 from AlphaLearn match |
| 0:30 | Show Forecast card — 52% success probability, sector trend POSITIVE |
| 0:45 | Show Fix Analysis — conditional score jump from 72 → 81 with 3 fixes |
| 0:30 | Show Portfolio Fit — FinTech concentration warning |
| 0:30 | Show Blind Spot — read one due diligence question aloud |
| 1:00 | Upload phone photo of "EduTech Tunisia" — OCR animation plays |
| 0:30 | Investor review gate — edit one field live (e.g. funding ask) |
| 0:30 | Confirm → full 8-card scorecard renders from physical doc |
| 0:30 | Change mandate ESG threshold to 75 → CargoZip flips to PASS |
| 0:30 | Wrap |

---

## 13. How to Run

### Prerequisites
```powershell
# Pull required models (one-time)
ollama pull mistral
ollama pull llama3.2:3b
```

### Terminal 1 — Ollama
```powershell
ollama serve
# Runs at http://localhost:11434
```

### Terminal 2 — Backend
```powershell
# From project root: C:\Hedi\Personal\SMU_SCHOLARSHIP\CAPAIHACK\ConvictAI
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

First start auto-creates `convictai.db` and seeds all data.

### Terminal 3 — Frontend
```powershell
cd frontend
npm run dev
# Runs at http://localhost:5173
```

### URLs
| URL | Purpose |
|-----|---------|
| http://localhost:5173 | App (Dashboard) |
| http://localhost:5173/evaluate | New evaluation |
| http://localhost:5173/mandate | Fund config |
| http://localhost:5173/monitor | Compliance monitoring |
| http://localhost:5173/synergy | Portfolio synergy |
| http://localhost:8000/api/health | Backend health + Ollama status |
| http://localhost:8000/docs | Swagger API docs |

### Clean Re-seed
```powershell
# Delete DB to force fresh seed on next backend start
Remove-Item convictai.db
```

### Environment Variables (Optional)
```
OLLAMA_BASE_URL=http://localhost:11434   # default; override if Ollama on different host
```

---

## 14. Diagnostic & Fixes Applied

A full codebase audit was run on 2026-06-09. Findings:

### False Alarms (Audit Was Wrong)

| Finding | Reality |
|---------|---------|
| "ComparisonTable.jsx MISSING — Dashboard will crash" | Not imported anywhere. Dashboard builds its table inline with native HTML. No bug. |
| "Fire-and-forget DB write is a silent failure" | `feedback_loop.py` already has `try/except` with `logger.error` + `db.rollback()`. Errors are logged. |

### Real Bugs Fixed

#### Bug 1 — Pipeline endpoint returned all 11 records
**File:** `backend/routers/startup.py` line 22  
**Symptom:** Dashboard would show 6 history deals (AlphaLearn, PayFlow, etc.) mixed with the 5 pipeline startups — 11 rows instead of 5.  
**Root cause:** `select(DealHistory)` had no WHERE clause. Seed correctly sets `is_pipeline=False` for history deals, but the query ignored this flag.  
**Fix applied:**
```python
# Before
select(DealHistory).order_by(DealHistory.final_score.desc())

# After
select(DealHistory)
.where(DealHistory.is_pipeline == True)  # noqa: E712
.order_by(DealHistory.final_score.desc())
```

#### Fix 2 — Ollama URL env var (improvement)
**File:** `backend/agents/ollama_client.py`  
**Change:** `OLLAMA_BASE = "http://localhost:11434"` → `OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")`  
**Impact:** Zero behavior change by default. Allows running Ollama on a different host without code changes.

### Confirmed Non-Issues

- All 8 routers present and importable
- All 7 agents present and correctly wired in evaluate.py
- All 3 parsers functional with proper merge_documents() function
- All 7 frontend card components present in Evaluate.jsx
- feedback_loop.py sets `is_pipeline=True` correctly on new evaluations
- `node_modules` already installed, no `npm install` needed
- Vite proxy correctly configured to `:8000`
- All seed data idempotent (safe for repeated restarts)

---

### Final Validation Run — 2026-06-12

End-to-end demo walkthrough across all 3 modules. 13 of 13 functional steps passed. 1 bonus step not implemented.

#### Fixes Applied (this session)

**Fix A — Monitor nav CRITICAL badge**  
**Files:** `backend/monitor/routes/monitor_routes.py`, `frontend/src/lib/api.js`, `frontend/src/App.jsx`  
Added `GET /api/monitor/critical-count` endpoint (counts unresolved CRITICAL alerts). Added `getMonitorCriticalCount()` in api.js. Added `useCriticalAlerts` hook in App.jsx (30s polling with cleanup). Red badge renders on Monitor nav item when count > 0.

**Fix B — Color consistency (13 files)**  
**Files:** 12 component files + ScorePill.jsx (already correct)  
Batch-replaced incorrect Tailwind hex values with brand design system values:

| Wrong | Correct | Meaning |
|-------|---------|---------|
| `#22c55e` | `#12B76A` | `var(--s-green)` |
| `#f59e0b` | `#F5A524` | `var(--s-amber)` |
| `#f97316` | `#EF6820` | `var(--s-orange)` |
| `#ef4444` | `#F04438` | `var(--s-red)` |

Affected: `StatementUploader.jsx`, `ExternalStartupCard.jsx`, `GapCard.jsx`, `PortfolioGraph.jsx`, `SynergyCard.jsx`, `SynergyPairTable.jsx`, `SynergyScoreBar.jsx`, `SynergyTypeBadge.jsx`, `Dashboard.jsx`, `Debug.jsx`, `Monitor.jsx`, `Synergy.jsx`

**Fix C — compliance_health_score missing from pipeline API**  
**Files:** `backend/schemas.py`, `backend/database.py`  
`DealSummary` Pydantic schema was missing `compliance_health_score: Optional[int] = None`. Added the field so the pipeline endpoint serialises it.  
Root cause 2: `seed_monitor_database()` never propagated `MonitorLedgerSnapshot.compliance_health_score` back to `DealHistory`. Added a sync loop at the end of `seed_monitor_database()` that runs an `UPDATE deal_history SET compliance_health_score = ...` for each seeded company (NovaPay=87, EduFlow=61, BuildSmart=34).

**Fix D — Dashboard compliance column**  
**File:** `frontend/src/pages/Dashboard.jsx`  
Added `compliance_health_score` column to the pipeline table. Implemented inline `CompliancePill` component with 4-tier colour coding (≥75 green, ≥50 amber, ≥25 orange, <25 red) using brand hex values.

#### Validation Scorecard

| # | Step | Endpoint / Component | Result |
|---|------|----------------------|--------|
| 1 | Dashboard shows 5 pipeline startups | `GET /api/pipeline` | ✅ |
| 2 | EduFlow cached result renders instantly | `GET /api/evaluate/cached/EduFlow` | ✅ |
| 3 | OCR animation (5 steps) + editable review gate | `OCRAnimationGate.jsx` + `GET /api/ocr-mock` | ✅ |
| 4 | Mandate ESG=45 flips CargoZip (ESG=42) to PASS | `POST /api/mandate` + `POST /api/mandate/apply` | ✅ |
| 5 | Monitor dashboard loads per company (health scores visible) | `GET /api/monitor/dashboard/{name}` | ✅ |
| 6 | Transaction reclassification — EduFlow has 1 UNCLASSIFIED | `PATCH /api/monitor/transaction/{id}/classify` | ✅ |
| 7 | Monitor OCR animation — NovaPay bank statement (12 tx) | `GET /api/monitor/ocr-mock` | ✅ |
| 8 | Resolve CRITICAL alert → badge count drops (3 → 2) | `PATCH /api/monitor/alert/{id}/resolve` | ✅ |
| 9 | Portfolio graph: NovaPay↔HealthCore scores (85/35/55) | `GET /api/synergy/graph` + `GET /api/synergy/pairs/3` | ✅ |
| 10 | Approve pair → edge turns solid (analyst_decision=approved) | `POST /api/synergy/pairs/3/decide` | ✅ |
| 11 | Gap Intelligence: 5 gaps with correct urgency scores | `GET /api/synergy/gaps` | ✅ |
| 12 | Hunt HR gap → 3 candidates (Expensya 70, Rekrute 65, Elyte 60) | `POST /api/synergy/gaps/3/hunt` | ✅ |
| 13 | Add to Pipeline dedup — 2nd add returns `already_exists` | `POST /api/synergy/gaps/3/shortlist/1/action` | ✅ |
| 14 | SynergyMiniWidget in Evaluate results (bonus) | Not implemented | ❌ |

#### Known Demo-Day Limitations

- **Mandate apply is one-directional.** Lowering `min_esg_threshold` does not restore previously-flipped startups. After showing the mandate flip demo (CargoZip → PASS), the DB must be deleted and restarted to show it again.
- **Compliance badge polling.** The sidebar critical-alert badge polls every 30 seconds. After resolving an alert in the Monitor tab, the badge count will update within 30s — not instantly. This is expected behaviour and acceptable for demo pacing.
- **SynergyMiniWidget not implemented.** The bonus Step 14 (a synergy chip in the Evaluate results page linking to matching portfolio companies) was not built. All 13 required steps pass.

---

## 15. File Tree

```
ConvictAI/
├── CLAUDE.md                          # Master build reference (updated 2026-06-09)
├── PROJECT_REPORT.md                  # This file
├── requirements.txt
├── .gitignore
├── .venv/                             # Python virtual environment
├── backend/
│   ├── __init__.py
│   ├── main.py                        # FastAPI app, 8 routers
│   ├── database.py                    # Engine, sessions, init_db, seed functions
│   ├── models.py                      # 13 SQLAlchemy models
│   ├── schemas.py                     # All Pydantic schemas
│   ├── debug_state.py                 # Pipeline state emitter
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ollama_client.py           # httpx client, retry, JSON parse
│   │   ├── extraction.py
│   │   ├── business.py
│   │   ├── esg.py
│   │   ├── memory.py
│   │   ├── forecasting.py
│   │   ├── fix_analysis.py
│   │   └── portfolio.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── aggregator.py
│   │   ├── recommendation.py
│   │   └── feedback_loop.py
│   ├── parsers/
│   │   ├── __init__.py                # exports merge_documents()
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   └── xlsx_parser.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py
│   │   ├── startup.py                 # FIXED: is_pipeline filter
│   │   ├── mandate.py
│   │   ├── evaluate.py
│   │   ├── ocr.py
│   │   └── debug.py
│   ├── monitor/
│   │   ├── routes/
│   │   │   └── monitor_routes.py
│   │   ├── agents/
│   │   │   ├── agreement_parser.py
│   │   │   ├── statement_parser.py
│   │   │   ├── category_agent.py
│   │   │   ├── compliance_agent.py
│   │   │   └── anomaly_agent.py
│   │   ├── engine/
│   │   │   ├── ledger.py
│   │   │   └── alert_engine.py
│   │   └── seed/
│   │       ├── demo_agreements.json
│   │       ├── demo_transactions.json
│   │       └── bank_statement_mock.json
│   ├── synergy/
│   │   ├── routes/
│   │   │   └── synergy_routes.py
│   │   ├── agents/
│   │   │   ├── profile_extractor.py
│   │   │   ├── pair_scorer.py
│   │   │   ├── gap_detector.py
│   │   │   └── gap_hunter.py
│   │   ├── engine/
│   │   │   └── match_engine.py
│   │   └── seed/
│   │       └── demo_synergy_seed.json
│   ├── seed/
│   │   └── demo_deals.json            # 6 history + 5 pipeline deals
│   └── ocr_mock/
│       └── scanned_result.json        # EduTech Tunisia pre-parsed data
├── frontend/
│   ├── package.json
│   ├── vite.config.js                 # proxy → :8000
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                    # BrowserRouter, 6 routes, sidebar nav
│       ├── index.css                  # CSS custom properties, fonts
│       ├── lib/
│       │   └── api.js                 # 28+ fetch functions
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Evaluate.jsx
│       │   ├── Mandate.jsx
│       │   ├── Monitor.jsx
│       │   ├── Synergy.jsx
│       │   └── Debug.jsx
│       └── components/
│           ├── cards/
│           │   ├── ScorecardCard.jsx
│           │   ├── ESGCard.jsx
│           │   ├── MemoryInsightCard.jsx
│           │   ├── ForecastCard.jsx
│           │   ├── FixAnalysisCard.jsx
│           │   ├── PortfolioFitCard.jsx
│           │   └── BlindSpotCard.jsx
│           ├── upload/
│           │   ├── FileUploader.jsx
│           │   └── OCRAnimationGate.jsx
│           ├── forms/
│           │   ├── StartupProfileForm.jsx
│           │   └── MandateConfigForm.jsx
│           ├── shared/
│           │   ├── ScorePill.jsx
│           │   ├── VerdictBadge.jsx
│           │   ├── ConfidenceBadge.jsx
│           │   ├── DeltaBadge.jsx
│           │   ├── ESGBar.jsx
│           │   ├── ScoreGauge.jsx
│           │   └── LoadingCards.jsx
│           ├── monitor/
│           │   ├── AlertPanel.jsx
│           │   ├── BudgetTracker.jsx
│           │   ├── ComplianceDashboard.jsx
│           │   ├── ComplianceHealthBadge.jsx
│           │   ├── MonitorOCRAnimationGate.jsx
│           │   ├── StatementUploader.jsx
│           │   ├── TimelineChart.jsx
│           │   └── TransactionLog.jsx
│           └── synergy/
│               ├── ExternalStartupCard.jsx
│               ├── GapCard.jsx
│               ├── GapPanel.jsx
│               ├── PortfolioGraph.jsx
│               ├── SynergyCard.jsx
│               ├── SynergyPairTable.jsx
│               ├── SynergyScoreBar.jsx
│               └── SynergyTypeBadge.jsx
├── uploads/                           # gitignored — temp file storage
└── convictai.db                       # gitignored — auto-created SQLite
```

---

*Report generated 2026-06-09 via full codebase audit.*  
*ConvictAI — Built for CapAI Hackathon, pre-investment axis.*
