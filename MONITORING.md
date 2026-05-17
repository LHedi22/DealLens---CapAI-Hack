# MONITORING.md — ConvictAI Monitor Build Instructions
> Second master reference for Claude Code. Read alongside CLAUDE.md before touching any monitoring code.
> Every decision, every constraint, every phase is defined here.
> This module is self-contained but integrates with the existing ConvictAI database and frontend.

---

## What You Are Building

**ConvictAI Monitor** — an AI-powered post-investment compliance surveillance module for PE fund analysts operating under Tunisian SICAR/CDC government-supervised investment agreements.

It ingests signed investment agreement documents (once at deal signing), ingests monthly bank statement PDFs (uploaded by the startup each month), classifies every outgoing transaction by category using AI, compares cumulative spending against the agreement plan, detects anomalies and violations, and delivers a real-time compliance dashboard with an immediate alert system.

**One sentence:** You know at signing what the agreement says. ConvictAI Monitor tells you every month whether you're still living up to it.

---

## The SICAR Context — Read This Before Writing Any Logic

Under Tunisia's SICAR (Sociétés d'Investissement à Capital Risque) and CDC frameworks, a PE fund signs a legally binding investment agreement with a startup or SME. This agreement specifies:

- The total capital committed (e.g. 500,000 TND)
- Exact allocation per spending category (e.g. R&D: 200,000 TND, Construction: 150,000 TND, Equipment: 100,000 TND, Working Capital: 50,000 TND)
- Sometimes: time-phased milestones (e.g. "R&D spending must commence before month 18")
- Duration: 5 years from deal signing

At year 5, the government audits whether the PE respected the agreement. Non-compliance triggers tax clawbacks and financial sanctions. The PE fund — not the startup — bears this liability.

**This is the core pain the module solves:** the 5-year gap between signing and audit, during which the PE currently has no structured visibility into whether money is going where it was promised.

---

## Hard Constraints — Never Violate These

- **Same tech stack as CLAUDE.md.** No new frameworks, no new databases, no new languages.
- **No paid APIs.** All LLM calls go to Ollama at `localhost:11434`. Same as the main system.
- **Model A** (`mistral` or `phi3:mini`) handles all three classification agents.
- **OCR for bank statements is faked.** Same approach as Layer 1.5 in the main system — a frontend animation over a pre-loaded parsed result. Do not install Tesseract.
- **SQLite only.** All monitoring data lives in `convictai.db` alongside the existing tables.
- **No authentication.** Single-user local app. No login screen.
- **All 3 output cards must render.** No placeholders on demo day.
- **The compliance ledger must never lose data.** Every transaction ever uploaded is stored permanently. No overwrites, only appends.
- **Alert emails are simulated.** Log the alert to the DB and show it in-app. Do not integrate a real email provider for the demo.
- **Confidence threshold is fixed at 80%.** Any transaction classification below 80% confidence is flagged as `UNCLASSIFIED` and sent to the PE for manual review. Do not make this configurable for the demo.
- **Variance tolerance is fixed at ±15% per category.** Below 15% variance = green. 15–30% = amber warning. Above 30% = red alert. Do not make this configurable for the demo.

---

## New File Structure — Add to Existing `convictai/`

```
convictai/
├── backend/
│   ├── monitor/
│   │   ├── agents/
│   │   │   ├── agreement_parser.py     # Extracts allocation plan from contract PDF/DOCX
│   │   │   ├── statement_parser.py     # Extracts transactions from bank statement PDF
│   │   │   ├── category_agent.py       # Classifies each transaction by category (LLM)
│   │   │   ├── compliance_agent.py     # Compares spend vs plan, computes variance
│   │   │   └── anomaly_agent.py        # Detects violations and suspicious patterns
│   │   ├── engine/
│   │   │   ├── ledger.py               # Writes to and reads from compliance_ledger table
│   │   │   ├── alert_engine.py         # Fires alerts when thresholds are breached
│   │   │   └── monitor_feedback.py     # Updates ConvictAI memory layer with health score
│   │   ├── routes/
│   │   │   └── monitor_routes.py       # All /api/monitor/* endpoints
│   │   └── seed/
│   │       ├── demo_agreements.json    # 3 pre-loaded SICAR agreements for demo
│   │       ├── demo_transactions.json  # 24 months of simulated transactions per company
│   │       └── bank_statement_mock.json # Pre-parsed bank statement for OCR demo
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── monitor/
│   │   │   │   ├── ComplianceDashboard.jsx    # Per-startup compliance overview
│   │   │   │   ├── BudgetTracker.jsx          # Category-by-category spend vs plan
│   │   │   │   ├── TransactionLog.jsx         # Full transaction table with tags
│   │   │   │   ├── AlertPanel.jsx             # Active alerts with resolve actions
│   │   │   │   ├── TimelineChart.jsx          # 5-year spending pace vs expected
│   │   │   │   ├── ComplianceHealthBadge.jsx  # Score badge (0–100, color coded)
│   │   │   │   └── StatementUploader.jsx      # Monthly PDF upload + OCR animation
│   │   ├── pages/
│   │   │   └── Monitor.jsx                    # Full monitoring page per startup
```

---

## New SQLite Tables — Add to Existing `convictai.db`

### Table: monitor_agreements
One record per invested startup. Created when PE uploads the signed agreement.

```sql
id                    INTEGER PRIMARY KEY AUTOINCREMENT,
startup_name          TEXT NOT NULL,
deal_history_id       INTEGER,          -- FK to deal_history.id (links to pre-investment record)
agreement_date        TEXT,             -- ISO date of signing
agreement_duration_months INTEGER DEFAULT 60,
total_committed_tnd   REAL,             -- Total capital in Tunisian Dinar
categories            TEXT,             -- JSON: [{ name, allocated_tnd, notes }]
time_milestones       TEXT,             -- JSON: [{ category, must_start_by_month, must_complete_by_month }]
uploaded_at           TEXT,
source_type           TEXT DEFAULT 'DIGITAL',   -- DIGITAL or PHYSICAL_SCAN
ocr_confidence        REAL,
is_seed_data          INTEGER DEFAULT 0
```

### Table: monitor_transactions
One record per transaction extracted from any bank statement. Append-only.

```sql
id                    INTEGER PRIMARY KEY AUTOINCREMENT,
agreement_id          INTEGER NOT NULL,   -- FK to monitor_agreements.id
startup_name          TEXT NOT NULL,
statement_month       TEXT,              -- ISO date: year-month of the bank statement
transaction_date      TEXT,             -- Date on the bank statement line
beneficiary           TEXT,             -- Who the payment went to
amount_tnd            REAL,             -- Amount in Tunisian Dinar (outgoing = positive)
memo                  TEXT,             -- Transaction description from bank statement
ai_category           TEXT,             -- Category assigned by category agent
ai_confidence         REAL,             -- 0.0–1.0
classification_status TEXT,             -- AUTO_CLASSIFIED / UNCLASSIFIED / HUMAN_VERIFIED
human_category        TEXT,             -- Set by PE analyst if they override AI
alert_triggered       INTEGER DEFAULT 0,
alert_type            TEXT,             -- NULL / OFF_PLAN / UNCLASSIFIED / ANOMALY / OVER_BUDGET
alert_resolved        INTEGER DEFAULT 0,
alert_resolved_note   TEXT,
uploaded_at           TEXT
```

### Table: monitor_ledger_snapshots
One record per statement upload. Tracks running totals at each point in time.

```sql
id                    INTEGER PRIMARY KEY AUTOINCREMENT,
agreement_id          INTEGER NOT NULL,
startup_name          TEXT NOT NULL,
snapshot_month        TEXT,             -- ISO year-month this snapshot covers
months_elapsed        INTEGER,          -- Months since agreement signing
category_totals       TEXT,             -- JSON: { category: { planned_tnd, spent_tnd, variance_pct } }
total_spent_tnd       REAL,
total_planned_to_date_tnd REAL,         -- Expected spend by this month (pro-rated)
unclassified_tnd      REAL,             -- Total TND still awaiting classification
compliance_health_score INTEGER,        -- 0–100
alert_count_active    INTEGER DEFAULT 0,
alert_count_total     INTEGER DEFAULT 0,
created_at            TEXT
```

### Table: monitor_alerts
One record per alert fired. Resolved or unresolved.

```sql
id                    INTEGER PRIMARY KEY AUTOINCREMENT,
agreement_id          INTEGER NOT NULL,
startup_name          TEXT NOT NULL,
transaction_id        INTEGER,          -- FK to monitor_transactions.id (null for non-tx alerts)
alert_type            TEXT NOT NULL,    -- OFF_PLAN / UNCLASSIFIED / ANOMALY / OVER_BUDGET / NO_STATEMENT / PACE_WARNING
severity              TEXT NOT NULL,    -- WARNING / CRITICAL
alert_summary         TEXT,            -- One-line AI-generated explanation
alert_detail          TEXT,            -- Full AI reasoning
fired_at              TEXT,
resolved              INTEGER DEFAULT 0,
resolved_at           TEXT,
resolved_by_note      TEXT
```

---

## Layer 1 — Two Inputs

### Input A: Investment agreement (uploaded once at deal signing)

Accepted formats: PDF, DOCX.
Trigger: PE navigates to a portfolio company's Monitor tab and clicks "Upload Agreement."

The agreement parser extracts:
- `total_committed_tnd` — total capital figure
- `categories` — each spending line item: name + allocated amount
- `time_milestones` — any phased requirements (start by month X, complete by month Y)
- `agreement_date` — signing date (sets the 5-year clock)
- `agreement_duration_months` — default 60, override if stated differently

If the document is an image or scan-only PDF: trigger the same OCR animation as Layer 1.5 in the main system. For the demo, use `bank_statement_mock.json` as the pre-parsed result.

**Standard SICAR categories to recognize (pre-loaded in the agent):**

| Category key | Common labels found in agreements |
|---|---|
| `rd` | R&D, Recherche et Développement, Frais de recherche |
| `construction` | Construction, Génie civil, Travaux, Bâtiment |
| `equipment` | Équipement, Matériel, Machines, Investissement matériel |
| `salaries` | Salaires, Masse salariale, Personnel, Rémunérations |
| `working_capital` | Fonds de roulement, BFR, Trésorerie |
| `marketing` | Marketing, Communication, Commercialisation |
| `training` | Formation, Renforcement des capacités |
| `other` | Everything else — triggers manual review |

### Input B: Monthly bank statement PDF (uploaded each month by startup)

Accepted format: PDF only.
Trigger: PE or startup uploads from the Monitor page for that company.

The statement parser extracts from each page:
- Transaction date
- Beneficiary name (the "to" field)
- Amount (outgoing only — filter for debits)
- Memo / reference field

Bank statements from Tunisian banks (STB, BNA, BIAT, Attijari, UIB, BH) follow standard formats. The parser handles both French and Arabic column headers. If text extraction fails or confidence is low: OCR animation + investor review gate.

---

## Layer 2 — Three Parallel AI Agents

All three run via `asyncio.gather` after the parsers complete. Same Ollama call pattern as the main system. All return structured JSON. Wrap every call: if JSON parse fails, retry once, then return a safe default.

### Agent A — Category classifier

**Input:** One transaction at a time (beneficiary, amount, memo).
**Output:** `{ category, confidence, reasoning_note }`

Classification logic:
- Match beneficiary name against known entity patterns (universities → `rd`, leasing companies → `equipment`, construction firms → `construction`)
- Match memo keywords against category keyword library (see below)
- Use amount patterns as a signal (very large round amounts to unknown entities = anomaly flag)
- If confidence ≥ 0.80: `classification_status = AUTO_CLASSIFIED`
- If confidence < 0.80: `classification_status = UNCLASSIFIED`, fire `UNCLASSIFIED` alert

**Keyword library (hardcoded in agent — never call Ollama for this):**

```python
CATEGORY_KEYWORDS = {
    "rd": ["recherche", "développement", "r&d", "laboratoire", "brevet", "prototype",
           "université", "bureau d'études", "ingénierie", "innovation", "test", "analyse"],
    "construction": ["construction", "génie civil", "travaux", "bâtiment", "maçonnerie",
                     "entrepreneur", "chantier", "fondation", "rénovation", "aménagement"],
    "equipment": ["équipement", "matériel", "machine", "leasing", "location financière",
                  "achat matériel", "mobilier", "informatique", "serveur", "véhicule"],
    "salaries": ["salaire", "rémunération", "cnss", "irpp", "paie", "personnel",
                 "virement salaire", "traitement", "charges sociales"],
    "working_capital": ["fournisseur", "matière première", "stock", "approvisionnement",
                        "achat marchandise", "crédit fournisseur"],
    "marketing": ["publicité", "marketing", "communication", "salon", "foire", "impression",
                  "agence", "média", "réseaux sociaux"],
    "training": ["formation", "séminaire", "conférence", "certification", "coaching",
                 "renforcement capacités"]
}
```

The LLM is only called when keyword matching is inconclusive. Pass the top 2 candidate categories and the transaction details — the LLM resolves the ambiguity and returns the winner with a confidence score and a one-sentence reasoning note.

**Human override:** When a PE analyst manually sets `human_category`, update `classification_status` to `HUMAN_VERIFIED`. Store both `ai_category` and `human_category`. The human category is what counts in all ledger calculations.

### Agent B — Compliance comparator

**Input:** All transactions for this agreement up to and including current month, categorized. Plus the agreement's allocation plan. Plus months elapsed since signing.
**Output:** `{ category_totals, total_spent, total_planned_to_date, variance_flags, compliance_health_score }`

For each category, computes:
- `spent_tnd` — sum of all AUTO_CLASSIFIED and HUMAN_VERIFIED transactions in this category
- `planned_tnd` — total allocation from agreement
- `planned_to_date_tnd` — pro-rated expected spend: `(months_elapsed / 60) × planned_tnd`
- `variance_pct` — `((spent_tnd - planned_to_date_tnd) / planned_to_date_tnd) × 100`
- `status` — `ON_TRACK / WARNING / CRITICAL`

**Variance rules:**
```
variance_pct between -15% and +15%  →  ON_TRACK   (green)
variance_pct between -30% and -16%
  OR between +16% and +30%          →  WARNING    (amber) → fire WARNING alert
variance_pct < -30% OR > +30%      →  CRITICAL   (red)   → fire CRITICAL alert
spent_tnd > planned_tnd            →  OVER_BUDGET (red)   → fire CRITICAL alert immediately
```

**Compliance health score (0–100):**
```
Base score: 100
For each category in WARNING:    -10 points
For each category in CRITICAL:   -20 points
For each OVER_BUDGET category:   -25 points
For each active unresolved alert: -5 points
Unclassified_tnd > 10% of total_spent: -10 points
Score floor: 0
```

**Pace projection:** Also compute whether, at the current monthly burn rate, each category will be fully spent by month 60. If a category is severely under-spent with only 12 months remaining, it's a compliance risk — the government may view unspent allocated funds as non-fulfillment. Flag this as a `PACE_WARNING` alert.

### Agent C — Anomaly detector

**Input:** All transactions for this agreement. The agreement's allocation plan. The full alert history.
**Output:** `{ anomalies: [{ transaction_id, anomaly_type, severity, explanation }] }`

Checks in order (stop at first match per transaction — do not double-fire):

| Anomaly type | Trigger condition | Severity |
|---|---|---|
| `OFF_PLAN` | Transaction category has zero allocation in agreement | CRITICAL |
| `OVER_BUDGET` | Category cumulative spend has exceeded its total allocation | CRITICAL |
| `LARGE_UNKNOWN` | Amount > 20,000 TND AND beneficiary not previously seen AND memo unclear | WARNING |
| `REPEATED_UNCLASSIFIED` | Same beneficiary appears ≥3 times with `UNCLASSIFIED` status | WARNING |
| `ROUND_LARGE` | Amount is a round number ≥ 50,000 TND (e.g. 100,000.000) — may indicate a transfer, not a purchase | WARNING |
| `NO_STATEMENT` | No statement uploaded for this month by day 10 of the following month | WARNING |
| `PACE_WARNING` | Months remaining < 12 AND underspent category > 20% of its allocation | WARNING |
| `ZERO_ACTIVITY` | Statement uploaded but zero outgoing transactions | WARNING |

For each anomaly, the LLM generates:
- `alert_summary` — one sentence, plain language (e.g. "Payment of 85,000 TND to an unknown beneficiary with no memo — not classifiable under any agreement category.")
- `alert_detail` — 2–3 sentences explaining the risk and what the PE should do (e.g. "This transaction has no matching allocation in the signed agreement. If this represents an off-plan expenditure, it may constitute a SICAR compliance breach. Request an invoice and written justification from the startup before the next statement cycle.")

---

## Layer 3 — The Compliance Ledger

`ledger.py` is the single source of truth for all compliance state. It is called after every statement upload.

**Ledger write sequence (called after every agent run):**
1. Write all new transactions to `monitor_transactions`
2. Fire any alerts from Agent C to `monitor_alerts`
3. Compute new snapshot (Agent B output) and write to `monitor_ledger_snapshots`
4. Update `portfolio_companies` in the main ConvictAI database: set `compliance_health_score` field

**Ledger read (called by dashboard on load):**
- Latest snapshot for this agreement
- All transactions (paginated, 50 per page)
- All unresolved alerts
- All snapshots (for timeline chart)

**Immutability rule:** Never update or delete rows in `monitor_transactions`. If the PE analyst reclassifies a transaction, write the new human category to `human_category` and update `classification_status`. The original `ai_category` is preserved for audit purposes.

---

## Layer 4 — Alert Engine

`alert_engine.py` fires when Agent B or Agent C produces a flag. For the demo, alerts are in-app only (no real email). Log to `monitor_alerts` and add a notification badge to the Monitor nav item.

**Alert payload written to DB:**
```python
{
  "agreement_id": int,
  "startup_name": str,
  "transaction_id": int or None,
  "alert_type": str,           # OFF_PLAN / UNCLASSIFIED / ANOMALY / OVER_BUDGET / NO_STATEMENT / PACE_WARNING
  "severity": str,             # WARNING / CRITICAL
  "alert_summary": str,        # One sentence
  "alert_detail": str,         # 2–3 sentences
  "fired_at": str              # ISO datetime
}
```

**In-app display rules:**
- CRITICAL alerts: red banner at top of the startup's Monitor page, stays until resolved
- WARNING alerts: amber badge in the alert panel, dismissible
- Unresolved alert count shown as a red badge on the Monitor nav item in the sidebar
- Resolved alerts move to a collapsible "Resolved" section — never deleted

**Resolve flow:** PE analyst clicks "Resolve" on an alert → modal appears with a free-text field for a resolution note → on confirm: `alert_resolved = 1`, `resolved_at = now()`, `resolved_by_note = text`. Score recalculates on next dashboard load.

---

## Layer 5 — Monitor Feedback to ConvictAI Memory

`monitor_feedback.py` runs after every ledger write. It updates the main ConvictAI system with real post-investment performance data.

**What it writes:**
- In `deal_history`: updates `outcome_if_invested` and `outcome_notes` with the current compliance health score and any CRITICAL alerts fired to date
- In `entity_sectors`: updates sector-level win rate with compliance signal (a startup with health score < 50 counts as a negative outcome signal for the sector)

This closes the feedback loop: pre-investment memory now learns from post-investment compliance reality. A sector that keeps producing SICAR compliance violations will show a declining conviction signal in future pre-investment evaluations.

---

## API Endpoints — All under `/api/monitor/`

```
POST   /api/monitor/agreement/upload          # Upload signed agreement PDF/DOCX
GET    /api/monitor/agreement/{startup_name}  # Get agreement for a startup
POST   /api/monitor/statement/upload          # Upload monthly bank statement PDF
GET    /api/monitor/dashboard/{startup_name}  # Full dashboard data (latest snapshot + alerts)
GET    /api/monitor/transactions/{startup_name} # Paginated transaction log
PATCH  /api/monitor/transaction/{id}/classify # PE manually sets category on UNCLASSIFIED tx
GET    /api/monitor/alerts/{startup_name}     # All alerts (unresolved first)
PATCH  /api/monitor/alert/{id}/resolve        # Resolve an alert with a note
GET    /api/monitor/timeline/{startup_name}   # All snapshots for timeline chart
GET    /api/monitor/portfolio-health          # Compliance health score for all monitored startups
POST   /api/monitor/ocr-mock                  # Returns bank_statement_mock.json (demo only)
```

---

## Seed Data — Load on Startup

Pre-load 3 simulated monitored startups into `monitor_agreements`, `monitor_transactions`, and `monitor_ledger_snapshots` on first run (`is_seed_data = true`).

### Agreement 1 — NovaPay (FinTech, performing)

```json
{
  "startup_name": "NovaPay",
  "agreement_date": "2023-01-15",
  "total_committed_tnd": 500000,
  "categories": [
    { "name": "rd",           "allocated_tnd": 200000 },
    { "name": "equipment",    "allocated_tnd": 150000 },
    { "name": "salaries",     "allocated_tnd": 100000 },
    { "name": "working_capital","allocated_tnd": 50000 }
  ]
}
```

Simulate 28 months of transactions. NovaPay is compliant — health score 87. One resolved WARNING (a large equipment purchase that initially looked anomalous). Good demo of a green state.

### Agreement 2 — EduFlow (EdTech, drifting)

```json
{
  "startup_name": "EduFlow",
  "agreement_date": "2023-06-01",
  "total_committed_tnd": 300000,
  "categories": [
    { "name": "rd",           "allocated_tnd": 150000 },
    { "name": "equipment",    "allocated_tnd": 80000  },
    { "name": "training",     "allocated_tnd": 40000  },
    { "name": "salaries",     "allocated_tnd": 30000  }
  ]
}
```

Simulate 22 months of transactions. EduFlow is drifting — over-spending on salaries (+38% variance), under-spending on R&D (-29% variance). Health score 61. Two active WARNING alerts. One UNCLASSIFIED transaction pending PE review. Good demo of an amber state and the classification review flow.

### Agreement 3 — BuildSmart (Construction Tech, in violation)

```json
{
  "startup_name": "BuildSmart",
  "agreement_date": "2022-11-01",
  "total_committed_tnd": 750000,
  "categories": [
    { "name": "construction", "allocated_tnd": 400000 },
    { "name": "equipment",    "allocated_tnd": 200000 },
    { "name": "rd",           "allocated_tnd": 100000 },
    { "name": "salaries",     "allocated_tnd": 50000  }
  ]
}
```

Simulate 30 months of transactions. BuildSmart has a problem — one OFF_PLAN transaction (marketing spend, which has zero allocation) and construction spending has exceeded its allocation. Health score 34. One unresolved CRITICAL alert. No statement uploaded for the most recent month (triggers `NO_STATEMENT` alert). Good demo of a red state and the audit risk narrative.

---

## Frontend Components

### Monitor.jsx (page)

Full-page layout with a left sidebar listing all monitored startups with their health score badge. Right panel shows the selected startup's dashboard. On load: fetch `/api/monitor/dashboard/{startup_name}` for the default startup (BuildSmart — worst case, most demo-worthy).

Tabs inside the right panel:
1. Overview (ComplianceDashboard)
2. Budget tracker (BudgetTracker)
3. Transactions (TransactionLog)
4. Alerts (AlertPanel)
5. Timeline (TimelineChart)

### ComplianceDashboard.jsx

Top section: three stat cards — Total committed, Total spent to date, Months elapsed (e.g. "28 of 60 months").
Middle: ComplianceHealthBadge — large score (0–100) with color coding and label.
Bottom: mini BudgetTracker showing just the category variance bars (no full table).

### BudgetTracker.jsx

One row per agreement category. Each row shows:
- Category name (pill badge with category color)
- Progress bar: spent / planned (color: green/amber/red based on variance)
- Spent TND amount
- Planned TND amount
- Variance percentage with up/down arrow
- Status badge (ON_TRACK / WARNING / CRITICAL / OVER_BUDGET)

### TransactionLog.jsx

Full paginated table. Columns: Date, Beneficiary, Amount (TND), Memo, Category (editable badge), Status, Alert.

Category badge is clickable when status is `UNCLASSIFIED` — opens an inline dropdown for the PE to select the correct category. On save: calls `PATCH /api/monitor/transaction/{id}/classify`.

Filter bar at top: by category, by status, by month, by alert type.

### AlertPanel.jsx

Two sections: Active alerts (sorted by severity, CRITICAL first), Resolved alerts (collapsed by default).

Each alert card shows: severity badge (red/amber), alert type, startup name, one-line summary, date fired, transaction link (if applicable), and a Resolve button.

Resolve button opens a modal with a free-text field. On submit: calls `PATCH /api/monitor/alert/{id}/resolve`.

### TimelineChart.jsx

Recharts AreaChart. X-axis: months 1–60. Y-axis: TND.
Three lines: Total planned (dashed gray), Total spent actual (solid blue), Projected pace (dotted amber — extrapolated from current burn rate to month 60).
Vertical red line at current month.
Hover tooltip shows: month, planned, actual, variance.

### ComplianceHealthBadge.jsx

Large circular gauge (Recharts RadialBarChart). Number in center (0–100). Color:
```
75–100  →  green   (#22c55e)
50–74   →  amber   (#f59e0b)
25–49   →  orange  (#f97316)
0–24    →  red     (#ef4444)
```
Label below score: COMPLIANT / AT RISK / IN BREACH.

### StatementUploader.jsx

Same drag-drop zone as FileUploader.jsx in the main system. Accepts PDF only.
If file is image or scan-only PDF: triggers OCRAnimationGate (same component, reused).
On upload: calls `POST /api/monitor/statement/upload`.
Shows progress and card-by-card result reveal (Framer Motion stagger) — same pattern as main evaluation flow.

---

## Ollama System Prompts — Templates

### Agreement Parser Agent
```
You are a legal document analyst specializing in Tunisian investment agreements (SICAR framework).
Extract the investment allocation plan from the following document.
Return ONLY a valid JSON object with these exact keys:
  total_committed_tnd (number or null),
  agreement_date (ISO date string or null),
  agreement_duration_months (integer, default 60 if not stated),
  categories (array of objects: { name (one of: rd/construction/equipment/salaries/working_capital/marketing/training/other), allocated_tnd (number), notes (string or null) }),
  time_milestones (array of objects: { category, must_start_by_month (integer or null), must_complete_by_month (integer or null) } — empty array if none stated).
If a field is not found, use null.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks.
```

### Statement Parser Agent
```
You are a bank statement analyst.
Extract all outgoing transactions (debits) from the following Tunisian bank statement.
Return ONLY a valid JSON object with these exact keys:
  statement_month (ISO year-month string, e.g. "2024-03"),
  transactions (array of objects: { transaction_date (ISO date), beneficiary (string), amount_tnd (positive number — outgoing only), memo (string or null) }).
Ignore incoming credits. Ignore balance lines. Ignore headers and footers.
If the document contains no outgoing transactions, return an empty transactions array.
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks.
```

### Category Classifier Agent (called only when keyword matching is inconclusive)
```
You are a compliance analyst for Tunisian SICAR investment agreements.
Classify the following bank transaction into the most appropriate spending category.
Agreement categories available: rd, construction, equipment, salaries, working_capital, marketing, training, other.
Transaction: beneficiary = "{beneficiary}", amount = {amount} TND, memo = "{memo}".
Top candidate categories from keyword matching: {candidate_1} ({score_1}%), {candidate_2} ({score_2}%).
Return ONLY a valid JSON object with these exact keys:
  category (string — one of the categories listed above),
  confidence (float between 0.0 and 1.0),
  reasoning_note (string — one sentence explaining your classification).
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks.
```

### Anomaly Explanation Agent
```
You are a compliance risk analyst for a Tunisian PE fund operating under SICAR agreements.
A compliance anomaly has been detected. Write a clear, plain-language alert for the fund analyst.
Anomaly type: {anomaly_type}.
Details: {anomaly_details}.
Return ONLY a valid JSON object with these exact keys:
  alert_summary (string — one sentence, maximum 120 characters, plain language),
  alert_detail (string — 2 to 3 sentences: what happened, why it is a risk, what the analyst should do next).
Respond ONLY with a valid JSON object. No explanation. No markdown. No backticks.
```

---

## Demo Flow — Monitor Module (4 Minutes)

Integrate into the main 8-minute pitch as an extension, or present as a standalone 4-minute demo.

1. **(0:20)** Navigate to Monitor tab in the ConvictAI sidebar
2. **(0:20)** Show the portfolio health overview — 3 startups listed: NovaPay (87, green), EduFlow (61, amber), BuildSmart (34, red)
3. **(0:30)** Click BuildSmart — show the CRITICAL alert banner at top ("OFF_PLAN transaction detected — marketing spend has no allocation in the signed SICAR agreement")
4. **(0:30)** Show the Budget Tracker — construction over-budget bar in red, R&D severely under-spent bar in amber
5. **(0:20)** Show the Timeline chart — actual spend line diverging from planned line at month 18
6. **(0:30)** Click the unresolved CRITICAL alert — show the alert detail panel ("This transaction constitutes an off-plan expenditure. Request written justification before the next audit cycle.")
7. **(1:00)** Upload a phone photo of a printed bank statement — OCR animation plays → transactions appear line by line → classification badges appear on each transaction → one transaction flagged UNCLASSIFIED
8. **(0:30)** Click the UNCLASSIFIED transaction — dropdown appears → PE selects "R&D" → transaction reclassifies → health score updates live
9. **(0:20)** Show that EduFlow's health score just dropped by 5 points in the sidebar (simulated — salary over-spend triggered a new WARNING)

**Key demo talking point for step 7:** *"Every month, the startup uploads their bank statement. Our agent reads every transaction, classifies it against the signed SICAR agreement, and tells the PE analyst in seconds whether the money is going where it was promised. No more waiting for year 5 to find out."*

**Key demo talking point for step 9:** *"This isn't just a dashboard. It's an early warning system. The PE knows about a compliance drift at month 22 — not at the government audit at month 60."*

---

## Integration Points with Main ConvictAI System

### Navigation
Add "Monitor" as a new item in the main sidebar nav between "Dashboard" and "Mandate." Show a red badge with the total count of unresolved CRITICAL alerts across all monitored startups.

### Dashboard.jsx (existing)
Add a `Compliance` column to the ComparisonTable. For startups that have a monitor agreement, show their ComplianceHealthBadge (small version). For startups not yet invested, show a gray "—" placeholder.

### deal_history table (existing)
Add one column: `compliance_health_score INTEGER DEFAULT NULL`. Populated by `monitor_feedback.py` after every ledger write for invested startups.

### portfolio_companies table (existing)
Add one column: `compliance_health_score INTEGER DEFAULT NULL`. Same.

### Monitor tab on Evaluate.jsx (existing)
When a startup has `decision = pursue` and `portfolio_added = true` in deal_history, show a "View Compliance Monitor" button on their scorecard page. Navigates to `Monitor.jsx` with that startup pre-selected.

---

## Compliance Health Score — Color Coding

Use everywhere in the monitor module. Consistent with main ConvictAI score colors.

```
75–100  →  green   (#22c55e)   label: COMPLIANT
50–74   →  amber   (#f59e0b)   label: AT RISK
25–49   →  orange  (#f97316)   label: DRIFTING
0–24    →  red     (#ef4444)   label: IN BREACH
```

Alert severity badges:
```
CRITICAL  →  red pill
WARNING   →  amber pill
```

Category status badges:
```
ON_TRACK       →  green pill
WARNING        →  amber pill
CRITICAL       →  orange pill
OVER_BUDGET    →  red pill
```

Classification status badges:
```
AUTO_CLASSIFIED  →  blue pill
HUMAN_VERIFIED   →  green pill
UNCLASSIFIED     →  red pill (requires PE action)
```

---

## What Claude Code Must Never Do (Monitor Module)

- Never delete or overwrite rows in `monitor_transactions` — append only
- Never auto-resolve an alert — only the PE analyst can resolve alerts
- Never calculate compliance health score without including unresolved alerts in the penalty
- Never show a health score of green (≥75) when any CRITICAL alert is unresolved
- Never classify a transaction with confidence < 0.80 as AUTO_CLASSIFIED — it must be UNCLASSIFIED
- Never crash the ledger write if Agent C returns no anomalies — an empty anomaly list is valid
- Never show BuildSmart as compliant — it is the demo's red-state example
- Never skip the `monitor_feedback.py` write after a ledger update — the main ConvictAI memory must stay in sync
- Never block the event loop — all parser and agent calls must be async
- Never show forecast-style language ("this company will breach compliance") — only state what has been observed, not predictions, to stay responsible

---

## Additional Requirements (add to existing requirements.txt)

No new packages needed. All parsing uses PyMuPDF (already installed). All LLM calls use httpx + Ollama (already installed). All data storage uses SQLAlchemy + SQLite (already installed).

---

## Phase Breakdown

---

### PHASE M1 — Monitor Foundation
**Goal:** New tables created. Agreement upload works. Seed data loaded.
**Done when:** Navigate to Monitor page, see 3 pre-loaded startups with agreements, click one and see its data.

Tasks:
- [ ] Add 4 new tables to `models.py`: `monitor_agreements`, `monitor_transactions`, `monitor_ledger_snapshots`, `monitor_alerts`
- [ ] Add `compliance_health_score` column to `deal_history` and `portfolio_companies`
- [ ] Seed loader: on startup, insert 3 agreements + their transactions + snapshots from `demo_agreements.json` and `demo_transactions.json`
- [ ] `monitor_routes.py` — register all `/api/monitor/*` endpoints in `main.py`
- [ ] `POST /api/monitor/agreement/upload` — parse PDF/DOCX via agreement parser, write to `monitor_agreements`
- [ ] `GET /api/monitor/dashboard/{startup_name}` — return latest snapshot + active alerts
- [ ] `Monitor.jsx` page — sidebar list of monitored startups, right panel skeleton
- [ ] `ComplianceDashboard.jsx` — 3 stat cards + ComplianceHealthBadge
- [ ] `ComplianceHealthBadge.jsx` — radial gauge, color coded, label

**End state:** Monitor page loads. 3 startups in sidebar. Click BuildSmart → see health score 34 in red.

---

### PHASE M2 — Statement Upload + Classification
**Goal:** Upload a bank statement PDF → transactions appear in log with AI categories.
**Done when:** Upload the demo statement → TransactionLog populates → UNCLASSIFIED badge appears on flagged transactions.

Tasks:
- [ ] `statement_parser.py` — PyMuPDF extraction of transaction rows from PDF
- [ ] `category_agent.py` — keyword matching first, LLM fallback for ambiguous transactions
- [ ] `POST /api/monitor/statement/upload` — orchestrate: parse → classify → write transactions → trigger compliance + anomaly agents
- [ ] `ledger.py` — write all transactions, compute snapshot, write snapshot
- [ ] `GET /api/monitor/transactions/{startup_name}` — paginated with filters
- [ ] `PATCH /api/monitor/transaction/{id}/classify` — PE manual classification
- [ ] `TransactionLog.jsx` — table with classification badges, inline reclassification dropdown
- [ ] `StatementUploader.jsx` — drag-drop PDF upload, reuse OCRAnimationGate for image input

**End state:** Upload PDF → transactions appear with category badges → UNCLASSIFIED one highlighted → PE clicks and reclassifies.

---

### PHASE M3 — Compliance Engine + Alerts
**Goal:** Compliance agent and anomaly agent run. Alerts fire. Budget tracker shows variances.
**Done when:** BuildSmart shows CRITICAL alert banner. BudgetTracker shows over-budget bar in red.

Tasks:
- [ ] `compliance_agent.py` — variance calculation per category, health score computation
- [ ] `anomaly_agent.py` — all 8 anomaly checks, LLM-generated explanations
- [ ] `alert_engine.py` — writes to `monitor_alerts`, fires in-app notification
- [ ] `GET /api/monitor/alerts/{startup_name}` — unresolved first, resolved collapsed
- [ ] `PATCH /api/monitor/alert/{id}/resolve` — resolve with note
- [ ] `BudgetTracker.jsx` — per-category rows with variance bars and status badges
- [ ] `AlertPanel.jsx` — CRITICAL banners, WARNING cards, resolve modal
- [ ] Nav badge: red count of unresolved CRITICALs across all monitored startups

**End state:** BuildSmart page opens with CRITICAL banner. Click alert → detail panel. Click resolve → modal → dismiss.

---

### PHASE M4 — Timeline + Portfolio Health + Feedback Loop
**Goal:** Timeline chart works. Portfolio overview shows all 3 health scores. Memory feedback loop writes to main DB.
**Done when:** TimelineChart renders 28 months of BuildSmart data. Dashboard.jsx shows compliance column.

Tasks:
- [ ] `GET /api/monitor/timeline/{startup_name}` — all snapshots for chart
- [ ] `GET /api/monitor/portfolio-health` — health scores for all monitored startups
- [ ] `TimelineChart.jsx` — Recharts AreaChart, planned vs actual vs projected
- [ ] `monitor_feedback.py` — write health score to `deal_history` and `portfolio_companies`
- [ ] Update `Dashboard.jsx` ComparisonTable — add Compliance column with health badge
- [ ] Monitor nav item: badge with CRITICAL alert count
- [ ] "View Compliance Monitor" button on invested startup scorecards in Evaluate.jsx
- [ ] `GET /api/monitor/portfolio-health` powering sidebar score list in Monitor.jsx

**End state:** Full 4-minute demo flow works end to end. All cards visible. Feedback loop active.

---

### PHASE M5 — OCR Demo + Final Polish
**Goal:** Phone photo of bank statement triggers OCR animation and feeds the pipeline. Monitor is demo-ready.
**Done when:** Full monitor demo sequence runs without surprises.

Tasks:
- [ ] `bank_statement_mock.json` — pre-parsed NovaPay monthly statement (12 transactions, one UNCLASSIFIED)
- [ ] `POST /api/monitor/ocr-mock` — returns mock data, triggers normal processing pipeline
- [ ] Reuse `OCRAnimationGate.jsx` for statement upload — adapt step labels for bank statement context
  - "Reading document quality..." (1.5s progress bar)
  - "Identifying transaction rows..." (rows appear one by one)
  - "Extracting amounts and beneficiaries..." (data populates)
  - "Classifying transactions..." (category badges appear)
  - Review gate: PE confirms or corrects before ledger write
- [ ] Error states: no statement this month → NO_STATEMENT alert fires automatically
- [ ] Visual polish: consistent color coding, badge alignment, table spacing
- [ ] Pre-cache BuildSmart result for instant render on demo
- [ ] Rehearse full 4-minute monitor demo flow

**End state:** Demo-ready. Phone photo → OCR animation → classified transactions → live health score update.

---

*This file is the second source of truth for Claude Code.*
*Read CLAUDE.md first. Read this file second. Do not improvise.*
*The monitor module follows every constraint in CLAUDE.md unless explicitly overridden here.*
*Built for the CapAI Hackathon — post-investment monitoring axis.*
