# ConvictAI — Full Project Report & System Architecture
Generated: 2026-06-17
Author: Claude Code automated audit
Status: **Functional but in a degraded demo state.** All backend modules and frontend pages exist and import cleanly. However, the live SQLite DB is currently seeded ONLY with 12 history deals and ZERO pipeline deals, so the Dashboard, Monitor, and Synergy surfaces render empty until a live evaluation is run. Several "pre-seeded demo" guarantees claimed in the spec docs (5 pipeline startups, 3 monitored companies, 5 synergy profiles) are NOT met by the current seed file. The required `llama3.2:3b` model is not installed (Model B now points at `qwen2.5:3b`).
Project: CapAI Hackathon — pre-investment AI screening engine

---

## 0. Executive Summary

ConvictAI is a local-first, multi-agent AI engine for venture/PE deal screening. It ingests startup documents, runs them through a 7-agent pipeline (extraction → business + ESG → memory → aggregate → forecast + fix + portfolio), and produces an 8-card investment scorecard. It ships with two bolt-on post-investment modules: **Monitor** (SICAR compliance / bank-statement classification) and **Synergy** (portfolio collaboration matching + external gap hunting).

The codebase is complete and internally consistent: 8 FastAPI routers register cleanly, 13 SQLAlchemy models exist, all 7 evaluation agents are wired into `evaluate.py`, and every frontend page + card component is present. The architecture honours the core constraints (Ollama-only LLM, SQLite-only, faked OCR, no auth).

**The gap between spec and reality is in the SEED DATA and the live DB state, not the code:**

- `backend/seed/demo_deals.json` contains **12 history deals and an empty `pipeline_deals` array.** The spec (CLAUDE.md) calls for 6 history + 5 pipeline startups. Consequently the Dashboard pipeline table loads empty, and Monitor/Synergy — which now derive their data from pipeline pursue/watch companies via `sync_*_from_pipeline()` — also start empty.
- The live DB confirms this: `deal_history=12` (all history, `is_pipeline=False`), `portfolio_companies=0`, all `monitor_*=0`, all `synergy_*=0`, `entity_founders=0`, `cached_evaluations=1` (EduFlow only).
- The 2026-06-17 refactor replaced hardcoded Monitor/Synergy JSON seeding with pipeline-derived sync. Because there are no pipeline deals, those modules have nothing to sync from. The demo's "NovaPay/EduFlow/BuildSmart health scores" and "5 synergy profiles" no longer auto-populate.
- `MODEL_B = "qwen2.5:3b"` in `ollama_client.py`, but installed models are `mistral`, `phi3:mini`, `qwen2.5:3b`. So Model B IS available as `qwen2.5:3b` — but the spec/PROJECT_REPORT still references `llama3.2:3b`, which is **not installed**. This is a doc/code drift, not a runtime break.

**Bottom line:** the engine works for a live upload-and-evaluate flow (EduFlow is pre-cached for instant render). The "open the app and see a full pipeline / populated Monitor / populated Synergy" demo no longer works out-of-the-box because the seed file was emptied of pipeline rows.

---

## 1. Project Identity

- **Name:** ConvictAI (frontend brands itself "DealLens" in the sidebar logo)
- **One-liner:** "Every other AI tool forgets. Ours remembers."
- **Purpose:** Pre-investment screening engine that scores startups on Business + ESG, cross-references a memory of past deals to produce a conviction delta, forecasts trajectory, flags fixable problems, maps portfolio fit, and surfaces blind spots — delivered as 8 structured cards. Two post-investment modules extend it: Monitor (compliance) and Synergy (portfolio value creation).
- **Hackathon:** CapAI — pre-investment axis (+ post-investment monitoring and value-creation axes).
- **Constraints honoured:** Ollama-only LLM at `localhost:11434`; SQLite only; no auth; faked OCR (no Tesseract); local demo.
- **Repo root:** `C:\Hedi\Personal\SMU_SCHOLARSHIP\CAPAIHACK\ConvictAI`

---

## 2. Full System Architecture

### 2.1 The Five-Layer Model

1. **Layer 1 — Ingestion.** Multi-file upload (`POST /api/upload`) saves files to `uploads/{startup_id}/`. Parsers (`pdf_parser`/`docx_parser`/`xlsx_parser`) extract text; `merge_documents()` concatenates into one corpus.
2. **Layer 1.5 — Faked OCR.** Image uploads trigger a frontend animation (`OCRAnimationGate.jsx`) over a pre-parsed payload (`ocr_mock/scanned_result.json` = "EduTech Tunisia"). Confirmed via `POST /api/ocr-confirm`.
3. **Layer 2 — Memory.** SQLite tables (`deal_history`, `entity_sectors`, `entity_founders`, `portfolio_companies`, `cached_evaluations`) store every evaluation. `feedback_loop.write_deal_record()` writes back after each eval and updates sector stats.
4. **Layer 3 — Agents.** 7 agents orchestrated in `routers/evaluate.py`: extraction (gate) → business + ESG (parallel) → memory → aggregate + verdict → forecast + fix + portfolio (parallel) → feedback loop (fire-and-forget).
5. **Layer 4/5 — Output + Modules.** 8 result cards on the frontend; plus Monitor (compliance ledger + alerts) and Synergy (pair scoring + gap hunting), each with their own routers, agents, engines, and tables.

### 2.2 Architecture Diagram (ASCII)

```
┌──────────────────────────────────────────────────────────────────────┐
│  FRONTEND  React 18 + Vite  :5173  (all-inline CSS + var(--*) tokens)  │
│  Sidebar nav: Dashboard · New Evaluation · Monitor · Synergy ·         │
│               Fund Mandate · Debug                                     │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  fetch → Vite proxy /api → :8000
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  BACKEND  FastAPI  :8000   (8 routers under /api)                      │
│                                                                        │
│  upload · startup · mandate · evaluate · ocr · debug                   │
│  monitor (/api/monitor/*) · synergy (/api/synergy/*)                   │
│                                                                        │
│  POST /api/evaluate ──► Extraction ─► [Business ∥ ESG] ─► Memory       │
│                         ─► Aggregate+Mandate+Verdict                   │
│                         ─► [Forecast ∥ Fix ∥ Portfolio]                │
│                         ─► feedback_loop (create_task, fire-forget)    │
│                            └─► auto-enroll Monitor + Synergy           │
└───────────────┬──────────────────┬───────────────────┬───────────────┘
                ▼                  ▼                   ▼
        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
        │  SQLite DB   │   │  Ollama      │   │  uploads/    │
        │ convictai.db │   │  :11434      │   │  (files)     │
        │  13 tables   │   │ mistral +    │   │              │
        │              │   │ qwen2.5:3b   │   │              │
        └──────────────┘   └──────────────┘   └──────────────┘
                                                  │
                                   Synergy gap_hunter ONLY →
                                   api.anthropic.com web_search
                                   (optional; falls back to seed)
```

### 2.3 Data Flow — Full Evaluation Request (`POST /api/evaluate`)

1. Guard: `check_ollama_available()` → 503 if Ollama down or `mistral` not pulled.
2. `reset_pipeline()` + emit debug log. Locate `uploads/{startup_id}` → 404 if missing, 400 if empty.
3. `merge_documents(file_paths)` → corpus; 422 if no extractable text.
4. **Extraction** (`run_extraction`, Model A `mistral`): 26-key JSON, `data_completeness` (0–100), `confidence_level`, hardcoded `blind_spots`.
5. **Business ∥ ESG** via `asyncio.gather(return_exceptions=True)`. Exceptions → `_DEFAULT_BUSINESS` / `_DEFAULT_ESG`. ESG red flags scanned in pure Python; LLM scores axes; deductions subtracted.
6. **Memory** (`run_memory_matching`): pure-Python similarity vs `is_pipeline=False` history, top-3, conviction delta (±20 cap); Model B generates delta explanation.
7. **Mandate load** (`MandateConfig` id=1) → `aggregate_scores()` → `generate_verdict()`. `final_score = (business+delta)×0.70 + esg×0.30`; mandate breach forces `final_score=0` + PASS.
8. Pre-fetch `portfolio_companies` + pipeline candidates (no DB calls inside agents).
9. **Forecast ∥ Fix ∥ Portfolio** via gather. Exceptions → respective `_default_*()`.
10. **Feedback loop** (`asyncio.create_task` fire-and-forget): writes `deal_history` row (`is_pipeline=True`), updates `entity_sectors`, and if verdict ∈ {pursue, watch} auto-enrolls into Monitor (`_enroll_in_monitor`) and Synergy (`_create_synergy_profile` → Ollama extract → `run_full_pipeline`).
11. `db.merge(CachedEvaluation(...))` upserts the full payload (overwrites on re-eval). Returns the response.

### 2.4 Monitor Module Architecture

- **Inputs:** signed agreement (PDF/DOCX, `parse_agreement` → Ollama) and monthly bank statement (PDF, `parse_statement` → Ollama). Faked OCR via `/api/monitor/ocr-mock` + `/api/monitor/ocr-confirm`.
- **Classification:** `category_agent.classify_batch` — keyword-first (French SICAR keyword library), LLM fallback for ambiguity, 0.80 confidence threshold → `AUTO_CLASSIFIED` / `UNCLASSIFIED`. Parallel via `asyncio.gather`.
- **Compliance:** `compliance_agent.compute_compliance` (pure Python) — per-category planned-to-date pro-ration, variance %, status (ON_TRACK/WARNING/CRITICAL/OVER_BUDGET). `compute_health_score`: base 100, −25 OVER_BUDGET, −20 CRITICAL, −10 WARNING, −5/active alert, −10 if unclassified > 10% of spend.
- **Anomalies:** `anomaly_agent.detect_anomalies` — OFF_PLAN, OVER_BUDGET, LARGE_UNKNOWN, REPEATED_UNCLASSIFIED, ROUND_LARGE, PACE_WARNING (NO_STATEMENT and UNCLASSIFIED handled elsewhere). LLM writes alert text with static fallback.
- **Ledger:** `ledger.py` — append-only `write_transactions` (flush, no commit), `compute_and_write_snapshot` (recompute + commit + `run_monitor_feedback`), `run_statement_pipeline` (anomalies → `fire_alerts` dedup → snapshot).
- **Feedback:** `monitor_feedback.run_monitor_feedback` — pushes health score to `deal_history` + `portfolio_companies`; if health < 50 nudges `entity_sectors.win_rate` down and sets trend "declining".
- **Routes:** `/api/monitor/*` — agreement upload/get, dashboard, portfolio-health, statement upload, transactions (paginated/filtered), reclassify, alerts, resolve, timeline, ocr-mock, ocr-confirm, critical-count, no-statement.

### 2.5 Synergy Module Architecture

- **Profiles:** `profile_extractor.extract_synergy_profile` — Ollama extracts services_offered / target_customers / operational_needs / strategic_gaps; confidence HIGH/MEDIUM/LOW by array population.
- **Pairs:** `pair_scorer.score_pair` — Ollama scores service_bridge/shared_customer/co_dev; composite = svc×0.40 + cust×0.35 + codev×0.25.
- **Match engine:** `match_engine.run_full_pipeline` — scores all unscored pairs (N·(N−1)/2), returns pairs (composite ≥ 55) + graph (nodes + edges ≥ 40).
- **Gaps:** `gap_detector.detect_gaps` — flattens needs+gaps, Ollama clusters them, computes urgency = (affected/total×40) + cost_intensity(0–30) + mandate_fit(0–30); internal-satisfaction check marks gaps filled.
- **Gap hunter:** `gap_hunter.hunt_gap` — the **only** external API: Anthropic `claude-sonnet-4-5-20251001` + `web_search_20250305`. Requires `ANTHROPIC_API_KEY`; without it, falls back to hardcoded `FALLBACK_COMPANIES` (Flouci/Konnect/Paymee, Expensya/Rekrute/Elyte, etc.) labelled "Simulated — Ollama demo mode".
- **Feedback:** `synergy_feedback.process_decision` (approve/reject/snooze + gap-fill) and `resurface_snoozed_pairs`. `synergy_trigger.schedule_synergy_run` fire-and-forget on new portfolio member.
- **Routes:** `/api/synergy/*` — status, run, pairs (+filter), pair detail, graph, decide, undo, gaps, gaps/detect, gaps/{id}/hunt, shortlist action, dismiss, company summary.

---

## 3. Tech Stack

### 3.1 Backend Dependencies (`requirements.txt`, all confirmed installed)

| Library | Version | Purpose |
|---|---|---|
| fastapi | 0.111.0 | async REST API |
| uvicorn[standard] | 0.29.0 | ASGI server |
| sqlalchemy | 2.0.30 | async ORM |
| pydantic | 2.7.1 | request/response schemas |
| python-multipart | 0.0.9 | file uploads |
| httpx | 0.27.0 | async Ollama + Anthropic calls |
| PyMuPDF (fitz) | 1.24.3 | PDF text extraction |
| python-docx | 1.1.2 | DOCX parsing |
| openpyxl | 3.1.2 | XLSX parsing (dep `et_xmlfile` confirmed present) |
| aiosqlite | 0.20.0 | async SQLite driver |

### 3.2 Frontend Dependencies (`frontend/package.json`)

React 18.3.1, react-dom 18.3.1, react-router-dom 6.23.1, react-dropzone 14.2.3, framer-motion 11.2.10, recharts 2.12.7, lucide-react 0.383.0, clsx, tailwind-merge, class-variance-authority, and a full set of @radix-ui primitives (dialog, slot, tabs, progress, select, label, radio-group, checkbox, toast). Dev: @vitejs/plugin-react 4.3.0, vite 5.2.11, tailwindcss 3.4.4, postcss, autoprefixer.

**Styling reality:** Components are written with **inline `style={{}}` objects + CSS custom properties** from `index.css`. Tailwind is installed and `@tailwind` directives are present, and `Debug.jsx` is the one page that heavily uses Tailwind utility classes (slate/indigo palette). Everything else uses inline styles.

### 3.3 LLM Configuration

- **Endpoint:** `OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")`.
- **Model A** = `mistral` (extraction, business, ESG, forecasting revenue, agreement/statement parsing, category fallback, anomaly text, synergy profile/pair/gap).
- **Model B** = `qwen2.5:3b` (memory delta explanation, fix-action text).
- **Call wrapper** (`call_ollama`): `format:"json"`, `temperature:0.1`, `num_predict:1500`, **180s timeout**, `_extract_json` strips markdown fences, retry-once on parse failure, returns `{}` safe default. Emits debug logs + records each call for the Debug pipeline trace.
- **Availability check** verifies `mistral` is actually pulled, not just that the server responds.
- **Installed models:** `mistral:latest`, `phi3:mini`, `qwen2.5:3b`. **`llama3.2:3b` is NOT installed** (referenced in CLAUDE.md/PROJECT_REPORT but no longer used by code).

---

## 4. Database Schema — Complete (from `models.py`)

13 ORM models. SQLite at `sqlite+aiosqlite:///./convictai.db`. Two columns added via idempotent `ALTER TABLE` in `init_db` (`compliance_health_score` on `deal_history` and `portfolio_companies`).

**`deal_history`** — id, startup_name, sector, stage, geography?, business_model_type?, date_evaluated, business_score?, esg_composite?, esg_e?, esg_s?, esg_g?, data_completeness?, confidence_level?, conviction_delta?, final_score?, decision?, decision_reason?, red_flags?(JSON text), blind_spots?(JSON text), fix_verdict?, outcome?, outcome_notes?, compliance_health_score?, is_seed_data(bool), is_pipeline(bool).

**`entity_sectors`** — id, sector_name(unique), total_evaluations, total_pursued, win_rate(float), avg_business_score(float), avg_esg_score(float), trend_direction.

**`entity_founders`** — id, name, deals_seen_in?(JSON), sectors?(JSON), prior_outcomes?(JSON). *(Never populated — 0 rows.)*

**`portfolio_companies`** — id, company_name, sector, stage, geography?, business_model_type?, esg_tier?, current_status(default "active"), compliance_health_score?. *(0 rows.)*

**`mandate_config`** — id(default 1), sector_focus?(JSON), stage_preference?(JSON), geography_scope?(JSON), min_esg_threshold(int default 0), ticket_size_min?, ticket_size_max?, esg_priority_axis(default "Balanced").

**`cached_evaluations`** — startup_name(PK), evaluation_json(text), cached_at.

**`monitor_agreements`** — id, startup_name, deal_history_id?, agreement_date?, agreement_duration_months(60), total_committed_tnd?, categories?(JSON), time_milestones?(JSON), uploaded_at?, source_type(default "DIGITAL"; sync uses "AUTO"), ocr_confidence?, is_seed_data(bool).

**`monitor_transactions`** — id, agreement_id, startup_name, statement_month?, transaction_date?, beneficiary?, amount_tnd?, memo?, ai_category?, ai_confidence?, classification_status?, human_category?, alert_triggered(int), alert_type?, alert_resolved(int), alert_resolved_note?, uploaded_at?.

**`monitor_ledger_snapshots`** — id, agreement_id, startup_name, snapshot_month?, months_elapsed?, category_totals?(JSON), total_spent_tnd?, total_planned_to_date_tnd?, unclassified_tnd?, compliance_health_score?, alert_count_active(int), alert_count_total(int), created_at?.

**`monitor_alerts`** — id, agreement_id, startup_name, transaction_id?, alert_type, severity, alert_summary?, alert_detail?, fired_at?, resolved(int), resolved_at?, resolved_by_note?.

**`synergy_profiles`** — id, company_name, deal_history_id?, services_offered?(JSON), target_customers?(JSON), operational_needs?(JSON), strategic_gaps?(JSON), sector?, geography?, stage?, profile_confidence?, last_extracted_at?, extraction_source(default "deal_file").

**`synergy_pairs`** — id, company_a, company_b, service_bridge_score?, shared_customer_score?, co_dev_score?, composite_score?, synergy_types_triggered?(JSON), match_explanation?, value_creation_type?, value_estimate_label?, action_suggestion?, confidence_level?, analyst_decision?, decision_reason?, decision_at?, snooze_until?, created_at?.

**`synergy_gaps`** — id, gap_label, need_description?, affected_companies?(JSON), affected_count?, estimated_annual_spend?, suggested_sector?, suggested_stage?, urgency_score?, status(default "open"), created_at?.

**`gap_shortlist`** — id, gap_id?, company_name, website?, description?, fit_score?, fit_reason?, flags?(JSON), source_url?, analyst_action?, added_at?.

**Live row counts (audit):** deal_history=12, entity_sectors=15, entity_founders=0, mandate_config=1, portfolio_companies=0, cached_evaluations=1, all monitor_*=0, all synergy_*=0.

---

## 5. Backend — Complete File Inventory

### 5.1 Entry Point (`main.py`)
FastAPI app with lifespan that `mkdir uploads` + `await init_db()`. CORS for `:5173`/`:3000`. Registers 8 routers under `/api`: upload, startup, mandate, evaluate, ocr, debug, monitor, synergy. `GET /api/health` returns `{status, service, ollama}`.

### 5.2 Database Layer (`database.py`)
`init_db` creates all tables, runs ALTER migrations, then `seed_database()` → `sync_monitor_from_pipeline()` → `sync_synergy_from_pipeline()`.
- `seed_database()` loads `demo_deals.json` (idempotent insert by name), re-syncs `_SCORE_FIELDS` for seed rows, seeds 15 `entity_sectors` + one `MandateConfig` on first run. Cached evals: loads `backend/seed/cached_evals/*.json` if the dir exists, else falls back to a large hardcoded `_EDUFLOW_CACHE` dict (full 8-card payload for EduFlow).
- `sync_monitor_from_pipeline()`: for pipeline pursue/watch companies w/o an agreement, creates a zero-value `MonitorAgreement` + initial snapshot (health = esg_composite or 50). **No-op today (0 pipeline rows).**
- `sync_synergy_from_pipeline()`: builds a `SynergyProfile` per pipeline pursue/watch company from its CachedEvaluation (services=top_strengths, needs=top_risks, gaps=blind_spot risks, customers derived from `company.stage`). **No-op today.**

### 5.3 Core Agents (`backend/agents/`)
- `ollama_client.py` — `call_ollama`, `check_ollama_available`, MODEL_A/MODEL_B, `_extract_json`.
- `extraction.py` — gate agent; 26-key schema; `_compute_completeness` (team/revenue_model/tam/revenue_type 20 pts each, traction/competitors/revenue 5 pts, supporting 1–2 pts, −10/inconsistency); `_compute_confidence`; `_generate_blind_spots` (deterministic {field, risk, question}).
- `business.py` — 6-dim weighted composite (team 25/market 20/revenue 20/traction 15/moat 10/scalability 10), clamps, strengths/risks.
- `esg.py` — `RED_FLAGS` (RF-01..RF-10 with pattern/negative keywords), `_scan_red_flags` pure Python, LLM E/S/G scores, axis deductions subtracted, composite = E×0.30+S×0.35+G×0.35, tier + verifiability + flag details.
- `memory.py` — similarity weights (sector 30/stage 20/model 15/revenue 10/geo 10/team 10/esg_tier 5), `compute_conviction_delta` (POSITIVE/NEGATIVE outcome buckets, ±20 cap), Model B explanation, sector conviction from `entity_sectors`. NOTE: revenue & team_profile sub-scores are hardcoded 0.5 (not actually computed).
- `forecasting.py` — sector base rates + benchmarks; LLM revenue trajectory (base/optimistic/conservative) with deterministic fallbacks; deterministic success probability (base + 5 adjustment rules); ROI from comparable DB exits (acquired=9×, performing=4.5×); sector trend signal.
- `fix_analysis.py` — `KNOWN_FIXES` + `STRUCTURAL_PROBLEMS` libraries; pure-Python problem detection (dim<50, RF flags, missing governance); priority = severity×fix_score/time; Model B enriches action text; conditional_score capped 100; 4 verdicts (invest_fix/condition/fix_first/structural_pass).
- `portfolio.py` — pure Python; sector concentration (>35% overweight), stage balance (≤80%), geo (>60%), ESG shift via `ESG_TIER_SCORE`, correlation risk (same sector+model ≥2), fit verdict, brute-force 2-startup pipeline optimizer. Safe-default on any error.

### 5.4 Engine (`backend/engine/`)
- `aggregator.py` — `aggregate_scores`: delta clamp, adjusted business, `final = adj×0.70 + esg×0.30`, mandate breach checks (sector/stage/min_esg/ticket×3), `force_pass` zeroes final score.
- `recommendation.py` — `generate_verdict`: force_pass→PASS; else 75+/60+/45+/else → pursue/watch/soft_pass/pass.
- `feedback_loop.py` — `write_deal_record` (own session, try/except/rollback), `_update_sector_entity` (win_rate, trend), `_enroll_in_monitor`, `_create_synergy_profile` (Ollama extract + `run_full_pipeline`). All idempotent & error-isolated.

### 5.5 Parsers (`backend/parsers/`)
`__init__.py` exports `parse_file` + `merge_documents` (handles .pdf/.docx/.doc/.xlsx/.xls/.txt; images → "" handled by OCR mock). `pdf_parser` (PyMuPDF), `docx_parser` (paragraphs + tables), `xlsx_parser` (read_only, data_only). All wrapped in try/except → "".

### 5.6 Routers (`backend/routers/`)
- `upload.py` — `POST /upload` (multipart, multi-file).
- `startup.py` — `POST /startup/profile` (echo), `GET /pipeline` (**correctly filters `is_pipeline==True`**), `GET /pipeline/{id}`.
- `mandate.py` — `GET/POST /mandate`, `POST /mandate/apply` (flips breaching pipeline deals to pass, invalidates their cached eval).
- `evaluate.py` — `POST /evaluate` (full pipeline + cache upsert), `GET /evaluate/cached/{name}` (cache first, then `deal_history` fallback with `is_partial=true`, `_esg_tier` helper).
- `ocr.py` — `GET /ocr-mock`, `POST /ocr-confirm` (skips extraction; runs business+ESG+memory+forecast+fix+portfolio; `source_type=PHYSICAL_SCAN`; fire-and-forget write). NOTE: ocr-confirm's `write_deal_record` dict does NOT include `document_text`, so a live OCR-confirmed pursue/watch deal will attempt a synergy profile from empty text.
- `debug.py` — `/debug/logs` (+SSE stream), `/debug/pipeline` (+SSE stream), `/debug/graph` (table counts + samples + relationships), `/debug/db/reseed`, `/debug/db/reset`.

### 5.7 Monitor Module (`backend/monitor/`)
routes/`monitor_routes.py` (14 endpoints; uses `.scalars().first()` on snapshot/ledger queries per the 2026-06-12 fix), agents/(agreement_parser, statement_parser, category_agent, compliance_agent, anomaly_agent), engine/(ledger, alert_engine, monitor_feedback), seed/(demo_agreements.json, demo_transactions.json, bank_statement_mock.json — **on disk but bypassed by the refactor**).

### 5.8 Synergy Module (`backend/synergy/`)
routes/`synergy_routes.py` (16 endpoints), agents/(profile_extractor, pair_scorer, gap_detector, gap_hunter), engine/(match_engine, synergy_feedback, synergy_trigger), seed/demo_synergy_seed.json (**bypassed**).

---

## 6. Frontend — Complete File Inventory

### 6.1 App Shell (`App.jsx`)
BrowserRouter + 6 routes (Dashboard, Evaluate, Monitor, Synergy, Mandate, Debug). Fixed 220px sidebar branded "DealLens". `usePendingSynergy` (one-shot synergy status badge) and `useCriticalAlerts` (30s polling for Monitor critical-count badge). `refreshKey` propagates Dashboard refreshes after eval/mandate apply.

### 6.2 API Layer (`lib/api.js`)
~35 fetch wrappers, base `/api` (Vite proxy → `:8000`). Core (pipeline, deal, upload, profile, mandate get/save/apply, evaluate, cached, ocr-mock/confirm), Monitor (statement upload, transactions, reclassify, alerts, resolve, timeline, ocr-mock/confirm, no-statement, critical-count), Synergy (status, run, pairs, graph, decide, undo, gaps, detect, hunt, shortlist action, dismiss, company summary). `getMonitorCriticalCount` swallows errors → 0.

### 6.3 Pages
- `Dashboard.jsx` — inline native HTML table (11 columns incl. Compliance + Synergy), 4 stat cards, sortable, skeleton rows, synergy chips fetched in parallel via `getCompanySummary`, rows navigate to `/evaluate?cached=`. (No separate ComparisonTable component.)
- `Evaluate.jsx` — phases setup/ocr/loading/error/results/cached. FileUploader + StartupProfileForm, OCRAnimationGate fork on image, 9 loading-step messages, 7 skeleton cards, OllamaOfflineCard, 6-min (360s) timeout warning, mandate breach/advisory banners, PhysicalScanBanner, Framer-Motion staggered reveal of the 7 card components.
- `Mandate.jsx` — MandateConfigForm; on save calls `applyMandate()` (best-effort) and shows reclassification toast.
- `Monitor.jsx` — sidebar of monitored startups (default selection "BuildSmart"), 5 tabs (Overview/Budget/Transactions/Alerts/Timeline), critical banner, statement uploader + transaction log. Uses absolute `http://localhost:8000` URLs (not the proxy).
- `Synergy.jsx` — 3 tabs (Synergy Pairs / Network Graph / Gap Intelligence), "Run Analysis" + "Detect Gaps" + "Hunt" actions, stat chips, uses GapPanel/PortfolioGraph/SynergyPairTable.
- `Debug.jsx` — Tailwind-styled dark console: live SSE logs (filter by level/text), pipeline trace (agent flow + Ollama call table + raw text), static knowledge-graph viz + live DB table counts, Clear/Reseed/Reset DB controls.

### 6.4 Components (all present on disk)
- **cards/** (7): ScorecardCard, ESGCard, MemoryInsightCard, ForecastCard, FixAnalysisCard, PortfolioFitCard, BlindSpotCard. *(No ComparisonCard.)*
- **upload/**: FileUploader, OCRAnimationGate.
- **forms/**: StartupProfileForm, MandateConfigForm.
- **shared/** (7): ScoreGauge, ConfidenceBadge, ESGBar, LoadingCards, ScorePill (`scoreColor`/`scoreBg` helpers), VerdictBadge, DeltaBadge.
- **monitor/** (8): ComplianceDashboard, ComplianceHealthBadge, AlertPanel, BudgetTracker, TransactionLog, TimelineChart, StatementUploader, MonitorOCRAnimationGate.
- **synergy/** (8): GapPanel, GapCard, ExternalStartupCard, PortfolioGraph, SynergyCard, SynergyPairTable, SynergyScoreBar, SynergyTypeBadge. *(GapPanel.jsx DOES exist — the pre-audit note that it was missing is incorrect.)*

---

## 7. Seed Data

**`backend/seed/demo_deals.json` (THE KEY ISSUE):**
- `history_deals`: **12 deals** — AlphaLearn, PayFlow, GreenHaul, MedTrack, BuildBot, DataVault, AgroSense, PixelBridge, CleanPower, CyberShield, PropVault, InsureQuick. (Spec called for 6; the file was expanded to 12.) All loaded `is_seed_data=True, is_pipeline=False`.
- `pipeline_deals`: **empty array `[]`.** The 5 pipeline startups described in CLAUDE.md/PROJECT_REPORT (EduFlow, NovaPay, CargoZip, HealthCore, BuildSmart) are **NOT in the seed file.** This is why the Dashboard pipeline table, Monitor, and Synergy all start empty.

**`ocr_mock/scanned_result.json`:** "EduTech Tunisia" — full parsed document, parsing_metadata (PHYSICAL_SCAN, ocr_confidence 0.71), 7 review_sections with per-section confidence, 3 blind spots. Used by the OCR demo. Well-formed and demo-ready.

**EduFlow cache:** `_EDUFLOW_CACHE` hardcoded in `database.py` is seeded into `cached_evaluations` (1 row in live DB) — so clicking EduFlow renders 8 cards instantly even though EduFlow is not a pipeline row. (But EduFlow won't appear in the Dashboard table since the pipeline is empty; it's reachable only via a direct `?cached=EduFlow` URL.)

**Bypassed seeds (on disk, not loaded):** `monitor/seed/demo_agreements.json`, `monitor/seed/demo_transactions.json`, `synergy/seed/demo_synergy_seed.json`. `monitor/seed/bank_statement_mock.json` IS still used by `/api/monitor/ocr-mock`.

**`entity_sectors`:** 15 sectors seeded (`_ALL_SECTORS`). Live DB shows 15 rows. ✔.

---

## 8. Agent Pipeline — Detailed Logic

| Step | Agent | Model | Nature | Key output |
|---|---|---|---|---|
| 1 | Extraction (gate) | A mistral | LLM + Python | 26 fields, completeness, confidence, blind_spots |
| 2a | Business | A mistral | LLM + Python clamp | 6 dims + composite + strengths/risks |
| 2b | ESG | A mistral | Python flags + LLM | E/S/G, composite, tier, RF list, verifiability |
| 3 | Memory | B qwen2.5:3b | Python similarity + LLM text | top-3, conviction_delta(±20), sector conviction |
| 4 | Aggregate+Verdict | — | Pure Python | final_score, mandate breach, verdict |
| 5a | Forecast | A mistral | LLM + Python | 3-scenario revenue, P(success), ROI, trend |
| 5b | Fix | B qwen2.5:3b | Python + LLM text | problems, conditional_score, verdict |
| 5c | Portfolio | — | Pure Python | concentration, ESG shift, fit, optimizer |
| 6 | Feedback | A (synergy extract) | DB write + enroll | deal_history row, sector update, Monitor+Synergy enroll |

Scoring math: `adjusted_business = clamp(business + clamp(delta,±20))`; `final = round(adjusted×0.70 + esg×0.30)`; mandate breach → final 0 + PASS. Verdict bands 75/60/45.

---

## 9. OCR Demo Flow

1. Image upload in `Evaluate.jsx` → `handleImageDetected` → phase `ocr` → `OCRAnimationGate`.
2. Animation (5 steps): quality check → pre-processing (deskew/binarize/denoise/normalize) → OCR scan (line-by-line) → structuring (section headers) → investor review gate (editable fields + confidence badges).
3. Confirm → `POST /api/ocr-confirm` with the reviewed `confirmed_document`. Backend skips extraction, runs business+ESG+memory+aggregate+forecast+fix+portfolio, returns `source_type=PHYSICAL_SCAN`, `ocr_confidence=0.71`.
4. `PhysicalScanBanner` shows on the resulting scorecard.
- Monitor has a parallel flow: `MonitorOCRAnimationGate` + `/api/monitor/ocr-mock` + `/api/monitor/ocr-confirm` over `bank_statement_mock.json` (NovaPay statement). NOTE: ocr-confirm requires an existing `MonitorAgreement` for the startup — which currently does not exist for any company (0 agreements), so the Monitor OCR confirm path 404s until a deal is evaluated/enrolled.

---

## 10. Known Gaps & Issues

**Seed / data-state gaps (highest impact):**
1. **`demo_deals.json` has 0 pipeline deals** → Dashboard pipeline table loads empty; `GET /api/pipeline` returns `[]`.
2. **`portfolio_companies` = 0 rows.** Nothing ever inserts into this table (no seed, no code path writes it). The portfolio agent therefore always runs against an empty portfolio (uses safe defaults / "no existing companies").
3. **Monitor tables all 0 rows.** `sync_monitor_from_pipeline()` finds no pursue/watch pipeline companies, so no agreements/snapshots are created. The Monitor page sidebar will be empty and `Monitor.jsx`'s default selection "BuildSmart" 404s on dashboard fetch.
4. **Synergy tables all 0 rows.** Same root cause — no pipeline companies to build profiles from. Synergy page shows "No pairs scored yet."
5. **`entity_founders` = 0 rows, ever.** Model exists and is referenced in memory weights/debug graph, but no code populates it. The memory agent's `team_profile` similarity is hardcoded 0.5.

**Model / config gaps:**
6. **`llama3.2:3b` not installed.** Code actually uses `qwen2.5:3b` for Model B (which IS installed), but CLAUDE.md / PROJECT_REPORT / "How to Run" still say `ollama pull llama3.2:3b`. Doc drift; the `ollama pull` instructions are wrong.
7. **Spec/code count mismatch:** CLAUDE.md says "6 history + 5 pipeline"; the file ships 12 history + 0 pipeline.

**Code-level issues found during inspection:**
8. **`ocr.py` omits `document_text` from `write_deal_record`.** For a pursue/watch OCR-confirmed deal, `_create_synergy_profile` calls `extract_synergy_profile("")` → empty profile. (Non-fatal; wrapped in try/except.)
9. **`memory.py` similarity uses fixed 0.5 for `revenue` and `team_profile` sub-scores** — those two dimensions (20% combined weight) are not actually computed from data.
10. **`gap_detector` uses an INSERT-OR-IGNORE-by-label scheme** but recomputes urgency each run; re-running with `force=false` returns early so stale gaps persist.
11. **`Monitor.jsx` hardcodes `http://localhost:8000`** instead of using the Vite proxy/`api.js`. Works on localhost demo only; would break behind a different host/port.
12. **Mandate apply is one-directional** (raising the ESG threshold flips deals to pass; lowering it does not restore them) — acknowledged in PROJECT_REPORT.
13. **`compliance_agent` OFF_PLAN status** is set when `planned==0 && spent>0`, but `compute_health_score` only penalizes WARNING/CRITICAL/OVER_BUDGET — OFF_PLAN categories incur no direct category penalty (only via the fired alert's −5).
14. **Two large `_default_*` blocks duplicated** across `evaluate.py` and `ocr.py` (maintenance smell, not a bug).

**Spec-vs-tree (claimed-missing files):** ComparisonTable.jsx, SynergyPage.jsx, SynergyMiniWidget.jsx genuinely do not exist (Dashboard builds its table inline; Synergy.jsx is the page; the mini-widget was never built — flagged "not implemented" in PROJECT_REPORT). **GapPanel.jsx DOES exist** (contrary to the pre-audit note). `MonitorOCRAnimationGate.jsx`, `monitor_feedback.py`, `synergy_feedback.py`, `synergy_trigger.py` all exist.

---

## 11. How to Run

```powershell
# Prereqs (one-time) — NOTE: code uses qwen2.5:3b, not llama3.2:3b
ollama pull mistral
ollama pull qwen2.5:3b            # Model B (docs incorrectly say llama3.2:3b)

# Terminal 1
ollama serve

# Terminal 2 — backend from project root
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000

# Terminal 3 — frontend
cd frontend
npm run dev
```
Open `http://localhost:5173`. Health: `http://localhost:8000/api/health`. Swagger: `http://localhost:8000/docs`.
To restore a fully-populated demo you must either (a) re-add the 5 pipeline startups to `demo_deals.json` and delete `convictai.db`, or (b) run live evaluations to populate pipeline → which then auto-enrolls Monitor + Synergy.

---

## 12. Demo Script Reference (intended 8-minute flow per CLAUDE.md)

1. (0:30) Open Dashboard — pipeline table. **Currently empty — needs pipeline seed.**
2. (0:45) Click EduFlow → 8 cards instant (pre-cached). **Works only via `?cached=EduFlow` since EduFlow isn't a table row.**
3. (0:30) Memory card — −6 conviction delta vs AlphaLearn.
4. (0:30) Forecast card — 52% success probability.
5. (0:45) Fix Analysis — conditional score 72 → 81.
6. (0:30) Portfolio Fit — FinTech concentration warning.
7. (0:30) Blind Spot — read a due-diligence question.
8. (1:00) Upload EduTech Tunisia photo → OCR animation.
9. (0:30) Investor review gate — edit a field.
10. (0:30) Confirm → 8-card scorecard from physical doc. **Works.**
11. (0:30) Change mandate ESG threshold → a startup flips to PASS. **Needs pipeline deals to demo.**
12. (0:30) Wrap. Monitor (4-min) + Synergy (3.5-min) extensions exist but **need pipeline-derived data first.**

---

## 13. Full File Tree (annotated)

```
ConvictAI/
├── CLAUDE.md                       # master spec (claims all phases complete)
├── MONITORING.md / SYNERGY.md      # module specs
├── PROJECT_REPORT.md               # prior report (2026-06-09)
├── FULL_REPORT.md                  # this file
├── requirements.txt
├── backend/
│   ├── main.py                     # 8 routers, lifespan init_db
│   ├── database.py                 # seed + sync_monitor/synergy (pipeline-derived)
│   ├── models.py                   # 13 ORM models
│   ├── schemas.py                  # Pydantic schemas
│   ├── debug_state.py              # pipeline state + log store (referenced)
│   ├── agents/  ollama_client, extraction, business, esg, memory,
│   │            forecasting, fix_analysis, portfolio
│   ├── engine/  aggregator, recommendation, feedback_loop
│   ├── parsers/ __init__(merge_documents), pdf_parser, docx_parser, xlsx_parser
│   ├── routers/ upload, startup, mandate, evaluate, ocr, debug
│   ├── monitor/ routes/monitor_routes
│   │            agents/(agreement_parser, statement_parser, category_agent,
│   │                    compliance_agent, anomaly_agent)
│   │            engine/(ledger, alert_engine, monitor_feedback)
│   │            seed/(demo_agreements*, demo_transactions*, bank_statement_mock)
│   ├── synergy/ routes/synergy_routes
│   │            agents/(profile_extractor, pair_scorer, gap_detector, gap_hunter)
│   │            engine/(match_engine, synergy_feedback, synergy_trigger)
│   │            seed/demo_synergy_seed*       (* bypassed by refactor)
│   ├── seed/demo_deals.json        # 12 history + 0 pipeline ⚠
│   └── ocr_mock/scanned_result.json
├── frontend/
│   ├── package.json / vite.config.js (proxy → :8000)
│   └── src/
│       ├── App.jsx / index.css / main.jsx
│       ├── lib/api.js              # ~35 fetch wrappers
│       ├── pages/  Dashboard, Evaluate, Mandate, Monitor, Synergy, Debug
│       └── components/
│           ├── cards/  Scorecard, ESG, MemoryInsight, Forecast,
│           │           FixAnalysis, PortfolioFit, BlindSpot
│           ├── upload/ FileUploader, OCRAnimationGate
│           ├── forms/  StartupProfileForm, MandateConfigForm
│           ├── shared/ ScoreGauge, ConfidenceBadge, ESGBar, LoadingCards,
│           │           ScorePill, VerdictBadge, DeltaBadge
│           ├── monitor/ ComplianceDashboard, ComplianceHealthBadge, AlertPanel,
│           │            BudgetTracker, TransactionLog, TimelineChart,
│           │            StatementUploader, MonitorOCRAnimationGate
│           └── synergy/ GapPanel, GapCard, ExternalStartupCard, PortfolioGraph,
│                        SynergyCard, SynergyPairTable, SynergyScoreBar,
│                        SynergyTypeBadge
├── uploads/  (gitignored)
└── convictai.db  (gitignored; live: 12 deals, empty pipeline/monitor/synergy)
```

---

## 14. CSS Design System (`index.css`)

Imports Google Fonts: **Outfit** (display/headers), **Inter** (body), **JetBrains Mono** (numerics). Tailwind base/components/utilities directives present.

CSS custom properties actually defined in `:root`:
- Surfaces: `--bg #FAFAFB`, `--surface-1 #FFFFFF`, `--surface-2 #F4F5F7`, `--surface-3 #EDEEF2`
- Borders: `--border #E7E9EE`, `--border-med #D0D4DC`, `--border-hi #B4BAC8`
- Text: `--tx-1 #111318`, `--tx-2 #3D4754`, `--tx-3 #64748B`
- Brand: `--primary #6E56CF`, `--primary-soft #8B7CFF`, `--primary-glow #B8A9FF`, `--primary-bg rgba(110,86,207,0.08)`, `--primary-border rgba(110,86,207,0.20)`
- Gold alias: `--gold #6E56CF`, `--gold-bg rgba(110,86,207,0.08)`
- Score palette: `--s-green #12B76A`, `--s-amber #F5A524`, `--s-orange #EF6820`, `--s-red #F04438`
- Legacy aliases: `--score-green/amber/orange/red` (= score palette), `--accent #6E56CF`, `--bg-primary #FAFAFB`, `--bg-card #FFFFFF`, `--bg-border #E7E9EE`, `--text-primary #111318`, `--text-muted #3D4754`

Score color thresholds (`ScorePill.scoreColor`): ≥75 green, ≥60 amber, ≥45 orange, else red. Animations: `shimmer` (skeleton), `fillBar`. Styled inputs/selects/textareas with purple focus ring.

---

## 15. Appendix — Spec vs Implementation Delta

| Spec claim (CLAUDE.md / MONITORING.md / SYNERGY.md / PROJECT_REPORT) | Actual |
|---|---|
| 6 history + 5 pipeline seed deals | **12 history + 0 pipeline** in `demo_deals.json` |
| Dashboard shows 5 pre-loaded startups | Dashboard loads empty (no pipeline rows) |
| Monitor pre-seeded: NovaPay 87 / EduFlow 61 / BuildSmart 34 | **0 monitor rows** (sync finds no pipeline companies; JSON seed bypassed) |
| Synergy pre-seeded: 5 profiles / 7 pairs / 5 gaps | **0 synergy rows** (sync finds no pipeline companies; JSON seed bypassed) |
| Model B = `llama3.2:3b` (or tinyllama) | Code uses `qwen2.5:3b`; `llama3.2:3b` not installed |
| `ollama pull llama3.2:3b` in run instructions | Should be `ollama pull qwen2.5:3b` |
| EduFlow pre-cached for instant render | ✔ `cached_evaluations` has EduFlow (1 row) — but not visible in pipeline table |
| 8 output cards render | ✔ 7 card components + scorecard cover all 8 sections; all wired in Evaluate.jsx |
| `is_pipeline=True` filter on Dashboard query | ✔ `startup.py` filters correctly |
| ComparisonTable.jsx component | Does not exist — Dashboard builds table inline (consistent with spec note) |
| SynergyMiniWidget.jsx | Not implemented (PROJECT_REPORT also flags this) |
| SynergyPage.jsx | Does not exist; `Synergy.jsx` is the page |
| GapPanel.jsx "missing" (pre-audit note) | **Exists** — pre-audit note was wrong |
| MonitorOCRAnimationGate / monitor_feedback / synergy_feedback / synergy_trigger | All exist ✔ |
| `entity_founders` populated | **Never populated — 0 rows**; `team_profile` similarity hardcoded 0.5 |
| `portfolio_companies` drives portfolio agent | **0 rows** — portfolio agent always runs on empty portfolio |
| Monitor/Synergy auto-enroll on pursue/watch eval | ✔ wired in `feedback_loop.py` (works once a live eval produces a pursue/watch pipeline deal) |
| Cache upsert on every `/evaluate` via `db.merge` | ✔ confirmed |
| `.scalars().first()` on snapshot/ledger queries | ✔ applied in `monitor_routes.py` |
| All 8 routers register | ✔ confirmed in `main.py` |

**Net assessment:** The application is architecturally complete and the live upload→evaluate→8-cards→auto-enroll path is functional and well-guarded. The headline regression is that `demo_deals.json` no longer ships pipeline startups, so the "open it and everything is populated" demo (Dashboard table, Monitor health scores, Synergy graph) is empty on a fresh DB. Restoring the 5 pipeline seed rows (and aligning the `ollama pull` docs to `qwen2.5:3b`) would return the project to the demo-ready state the spec describes.
