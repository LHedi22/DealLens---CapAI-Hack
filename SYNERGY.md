# SYNERGY.md — ConvictAI SynergyAI Build Instructions
> Third master reference for Claude Code. Read alongside CLAUDE.md and MONITORING.md before touching any synergy code.
> Every decision, every constraint, every data flow is defined here.
> This module is self-contained but reads from the existing ConvictAI database and integrates with the existing frontend.

---

## What You Are Building

**SynergyAI** — an AI-powered portfolio synergy matching engine that detects collaboration opportunities between companies already invested in by the PE fund, and hunts external startups to fill gaps when portfolio needs go unmet.

It reads existing ConvictAI deal files for every portfolio company, extracts a structured Synergy Profile for each, matches companies against each other across three synergy types, scores every pair, surfaces actionable collaboration opportunities, and — when a need cannot be satisfied internally — searches the web for real external startups the PE should consider investing in.

**One sentence:** The portfolio is already full of hidden value. SynergyAI finds it — and tells you what's still missing.

---

## The Business Problem — Read This Before Writing Any Logic

A PE fund with 10 portfolio companies has potentially 45 company pairs. Each pair is a possible partnership: a supplier-customer relationship, a shared go-to-market, a co-developed product. Today, these connections are discovered by accident — a founder mentions it in a quarterly meeting, an analyst notices it after 18 months.

The second problem is the inverse: every portfolio company has needs it pays for externally. When several companies share the same unmet need, that unmet need is also an investment signal — it tells the PE exactly what kind of company to invest in next, grounded in real demand from its own portfolio rather than cold market intuition.

**SynergyAI solves both:** find the value already inside the portfolio, and use the portfolio's blind spots to generate the next deal thesis.

---

## Hard Constraints — Never Violate These

- **Same tech stack as CLAUDE.md.** No new frameworks, no new databases, no new languages.
- **No paid APIs for LLM calls.** All Ollama calls go to `localhost:11434`. Same as the main system.
- **Gap hunting web search uses the Anthropic API.** The web search agent calls `api.anthropic.com/v1/messages` with the `web_search_20250305` tool. This is the only external API call allowed in this module.
- **SQLite only.** All synergy data lives in `convictai.db` alongside the existing tables.
- **No authentication.** Single-user local app. No login screen.
- **All 3 UI panels must render on demo day.** Network Graph, Synergy Pairs table, Gap Panel — no placeholders.
- **Synergy profiles are always derived from existing deal files.** Never ask the analyst to fill in synergy data manually. The extraction agent reads what is already in the DB.
- **The analyst approves or rejects every match.** SynergyAI never auto-connects two companies. Approve/Reject/Snooze must always be present on every synergy card.
- **Gap hunting shortlists are 3–5 companies per gap.** Never return fewer than 3 or more than 5.
- **Synergy score threshold for display is 55/100.** Pairs below 55 are computed but not shown. Do not make this configurable for the demo.
- **Model A** (`mistral` or `phi3:mini`) handles synergy profile extraction and pair scoring.
- **Web search results must include a Fit Score.** Every external company in a gap shortlist must have a computed Fit Score (0–100) and a plain-language reason for the score.

---

## New File Structure — Add to Existing `convictai/`

```
convictai/
├── backend/
│   ├── synergy/
│   │   ├── agents/
│   │   │   ├── profile_extractor.py     # Builds SynergyProfile from deal file text
│   │   │   ├── pair_scorer.py           # Scores every portfolio pair across 3 synergy types
│   │   │   ├── gap_detector.py          # Identifies unmet needs across the portfolio
│   │   │   └── gap_hunter.py            # Web search agent — finds real external startups
│   │   ├── engine/
│   │   │   ├── match_engine.py          # Orchestrates extraction → scoring → gap detection
│   │   │   ├── synergy_feedback.py      # Writes analyst decisions back to DB
│   │   │   └── synergy_trigger.py       # Called when portfolio_added = true on a deal
│   │   ├── routes/
│   │   │   └── synergy_routes.py        # All /api/synergy/* endpoints
│   │   └── seed/
│   │       └── demo_synergy_seed.json   # Pre-computed profiles + pairs for demo companies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── synergy/
│   │   │   │   ├── SynergyPage.jsx          # Full standalone Synergy page
│   │   │   │   ├── PortfolioGraph.jsx        # D3 or Recharts network graph
│   │   │   │   ├── SynergyPairTable.jsx      # Ranked pairs table with actions
│   │   │   │   ├── SynergyCard.jsx           # Expanded detail card per pair
│   │   │   │   ├── GapPanel.jsx              # Gap report + external shortlist side by side
│   │   │   │   ├── GapCard.jsx               # One card per detected gap
│   │   │   │   ├── ExternalStartupCard.jsx   # One card per web-sourced company
│   │   │   │   ├── SynergyTypeBadge.jsx      # SERVICE / CUSTOMER / CO-DEV badge
│   │   │   │   ├── SynergyScoreBar.jsx       # Composite score bar (color-coded)
│   │   │   │   └── SynergyMiniWidget.jsx     # Small widget shown on each company scorecard
```

---

## New SQLite Tables — Add to Existing `convictai.db`

### Table: synergy_profiles
One record per portfolio company. Regenerated when deal file is updated.

```sql
CREATE TABLE synergy_profiles (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name          TEXT NOT NULL,
  deal_history_id       INTEGER REFERENCES deal_history(id),
  services_offered      TEXT,   -- JSON array of strings
  target_customers      TEXT,   -- JSON array of strings
  operational_needs     TEXT,   -- JSON array of strings
  strategic_gaps        TEXT,   -- JSON array of strings
  sector                TEXT,
  geography             TEXT,
  stage                 TEXT,
  profile_confidence    TEXT,   -- HIGH / MEDIUM / LOW
  last_extracted_at     TEXT,   -- ISO datetime
  extraction_source     TEXT    -- 'deal_file' always for now
);
```

### Table: synergy_pairs
One record per evaluated company pair. Recomputed when any profile changes.

```sql
CREATE TABLE synergy_pairs (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  company_a               TEXT NOT NULL,
  company_b               TEXT NOT NULL,
  service_bridge_score    INTEGER,   -- 0–100
  shared_customer_score   INTEGER,   -- 0–100
  co_dev_score            INTEGER,   -- 0–100
  composite_score         INTEGER,   -- weighted composite 0–100
  synergy_types_triggered TEXT,      -- JSON array: ['SERVICE','CUSTOMER','CO_DEV']
  match_explanation       TEXT,      -- plain-language AI-generated explanation
  value_creation_type     TEXT,      -- 'cost_saving' | 'revenue_expansion' | 'new_market'
  value_estimate_label    TEXT,      -- e.g. "~180,000 TND annual savings"
  action_suggestion       TEXT,      -- e.g. "Introduce founders" / "Draft pilot agreement"
  confidence_level        TEXT,      -- HIGH / MEDIUM / LOW
  analyst_decision        TEXT,      -- NULL | 'approved' | 'rejected' | 'snoozed'
  decision_reason         TEXT,
  decision_at             TEXT,      -- ISO datetime
  snooze_until            TEXT,      -- ISO datetime, only if snoozed
  created_at              TEXT
);
```

### Table: synergy_gaps
One record per detected unmet need cluster.

```sql
CREATE TABLE synergy_gaps (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  gap_label             TEXT NOT NULL,   -- e.g. "B2B Payment Infrastructure"
  need_description      TEXT,            -- plain language description
  affected_companies    TEXT,            -- JSON array of company names
  affected_count        INTEGER,
  estimated_annual_spend TEXT,           -- e.g. "~180,000 TND"
  suggested_sector      TEXT,
  suggested_stage       TEXT,
  urgency_score         INTEGER,         -- 0–100 (frequency × cost × mandate fit)
  status                TEXT,            -- 'open' | 'hunting' | 'filled' | 'dismissed'
  created_at            TEXT
);
```

### Table: gap_shortlist
One record per external company found for a gap.

```sql
CREATE TABLE gap_shortlist (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  gap_id            INTEGER REFERENCES synergy_gaps(id),
  company_name      TEXT NOT NULL,
  website           TEXT,
  description       TEXT,
  fit_score         INTEGER,   -- 0–100
  fit_reason        TEXT,      -- why it fills the gap
  flags             TEXT,      -- JSON array of warning strings
  source_url        TEXT,      -- URL from web search result
  analyst_action    TEXT,      -- NULL | 'add_to_pipeline' | 'dismissed'
  added_at          TEXT
);
```

---

## Seed Data — Load on Startup

The demo uses the 5 pipeline companies already in `demo_deals.json` as the portfolio.
Add pre-computed synergy profiles and pairs for all 5 companies to `demo_synergy_seed.json`.

### Portfolio Companies for Demo

| Company | Sector | Services Offered | Target Customers | Operational Needs | Strategic Gaps |
|---|---|---|---|---|---|
| **EduFlow** | EdTech | Online learning platform, curriculum tools | Schools, universities, corporate L&D | Payment processing, logistics for physical kits, HR tools | Distribution network, B2B sales team |
| **NovaPay** | FinTech | B2B payment gateway, invoicing, expense tracking | SMEs, startups, retailers | Marketing services, legal compliance tooling | Health/education vertical partnerships |
| **CargoZip** | Logistics | Last-mile delivery, warehousing, route optimization | E-commerce, retailers, food brands | Fleet insurance, driver HR, customer support tools | SaaS clients to expand B2B revenue |
| **HealthCore** | HealthTech | Patient management SaaS, clinic analytics | Clinics, hospitals, pharmacies | Payment processing, delivery for medical supplies, staff training | Data partnership, government contract support |
| **BuildSmart** | Construction Tech | Project management SaaS, supplier network | Construction firms, real estate developers | HR/payroll tools, financial reporting, marketing | International market entry support |

### Pre-Computed Demo Synergy Pairs (seed these into `synergy_pairs`)

| Company A | Company B | Service Bridge | Shared Customer | Co-Dev | Composite | Types | Explanation |
|---|---|---|---|---|---|---|---|
| NovaPay | EduFlow | 88 | 45 | 30 | 65 | SERVICE, CO_DEV | NovaPay's payment gateway eliminates EduFlow's external Stripe dependency. Co-dev opportunity: embedded payment + subscription billing inside EduFlow's LMS. |
| CargoZip | EduFlow | 72 | 20 | 15 | 44 | SERVICE | CargoZip can handle physical kit delivery for EduFlow's blended-learning courses. EduFlow currently uses third-party couriers at a ~40% cost premium. |
| NovaPay | HealthCore | 85 | 35 | 55 | 68 | SERVICE, CO_DEV | HealthCore needs payment processing for patient invoicing. NovaPay can serve this directly. Co-dev: a healthcare-compliant invoicing module built jointly. |
| CargoZip | HealthCore | 70 | 25 | 20 | 48 | SERVICE | CargoZip's last-mile logistics can cover medical supply delivery for HealthCore's clinic clients, replacing their expensive cold-chain vendor. |
| NovaPay | BuildSmart | 60 | 40 | 25 | 48 | SERVICE, CUSTOMER | BuildSmart's SME clients need payroll and financial reporting tools NovaPay already provides. Shared customer: construction SMEs. |
| EduFlow | HealthCore | 30 | 55 | 65 | 52 | CUSTOMER, CO_DEV | Both serve institutional B2B clients (schools, clinics). Co-dev potential: a staff training + health compliance certification platform for clinic admin staff. |
| EduFlow | BuildSmart | 25 | 45 | 50 | 40 | CUSTOMER, CO_DEV | Both target institutional buyers. Co-dev: safety and compliance training modules for construction firms, built on EduFlow's LMS. |

Only pairs with composite_score ≥ 55 appear in the UI by default. That gives **3 visible pairs**: NovaPay↔EduFlow (65), NovaPay↔HealthCore (68), and EduFlow↔HealthCore (52 — just below threshold, shown with a "borderline" label for demo richness).

### Pre-Computed Demo Gaps (seed into `synergy_gaps`)

| Gap Label | Affected Companies | Count | Urgency | Sector to Hunt |
|---|---|---|---|---|
| B2B Payment Infrastructure | EduFlow, HealthCore, BuildSmart | 3 | 82 | FinTech — already filled by NovaPay (auto-dismiss this gap if NovaPay pair is approved) |
| Last-Mile Medical & Physical Delivery | EduFlow, HealthCore | 2 | 71 | Logistics — partially filled by CargoZip |
| HR & Payroll Tooling | CargoZip, BuildSmart, HealthCore | 3 | 68 | HR Tech / Payroll SaaS |
| Legal & Regulatory Compliance Tooling | NovaPay, HealthCore, BuildSmart | 3 | 75 | LegalTech / RegTech |
| B2B Marketing & Growth Services | EduFlow, BuildSmart, CargoZip | 3 | 60 | Marketing SaaS / Growth Agency |

For the demo, use the **HR Tech gap** and **LegalTech gap** as the two gaps that trigger live web search, since those are clearly unmet by any current portfolio company.

---

## The Synergy Profile Extractor — Agent Logic

**File:** `backend/synergy/agents/profile_extractor.py`

**Input:** `deal_history_id` (reads the stored deal file text from `deal_history` table)
**Output:** A populated `synergy_profiles` row

**Ollama system prompt:**
```
You are an investment analyst building a synergy profile for a portfolio company.
From the startup document below, extract:
- services_offered: what products or services the company provides (list of strings)
- target_customers: who they sell to — be specific (list of strings)
- operational_needs: things they currently buy externally, outsource, or struggle without (list of strings)
- strategic_gaps: capabilities or resources they want but don't have (list of strings)

Return ONLY a valid JSON object with exactly these four keys, each containing an array of strings.
If a field cannot be determined, return an empty array [].
No explanation. No markdown. No backticks.
```

**Profile confidence logic:**
- HIGH: all 4 arrays have ≥ 2 items each
- MEDIUM: at least 3 arrays have ≥ 1 item
- LOW: fewer than 3 arrays populated

**When to run:**
- On startup, for every company in `portfolio_companies` where no `synergy_profiles` row exists
- Whenever a deal's `portfolio_added` field is set to `true`
- Never on companies that are not in the portfolio (pipeline-only startups)

---

## The Pair Scorer — Agent Logic

**File:** `backend/synergy/agents/pair_scorer.py`

**Input:** Two `synergy_profiles` rows (Company A and Company B)
**Output:** A populated `synergy_pairs` row

Run for every possible pair of portfolio companies. With 5 companies, that is 10 pairs. With N companies: N×(N-1)/2 pairs.

### Score Computation

**Service Bridge Score (0–100)**
Prompt the LLM with both profiles and ask: does `services_offered[A]` satisfy any item in `operational_needs[B]` or `strategic_gaps[B]`? Does `services_offered[B]` satisfy any item in `operational_needs[A]` or `strategic_gaps[A]`? Score the strength and specificity of the match.

**Shared Customer Score (0–100)**
Prompt the LLM with both profiles and ask: how much overlap exists between `target_customers[A]` and `target_customers[B]`? Consider both explicit overlap and implicit overlap (e.g. "SMEs" and "construction firms" are a subset relationship).

**Co-Development Score (0–100)**
Prompt the LLM with both profiles and ask: could the combination of `services_offered[A]` and `services_offered[B]` enable a novel product or service that neither could build alone? Score by novelty, feasibility, and market size of the hypothetical joint offering.

**Composite Score:**
```
composite = (service_bridge × 0.40) + (shared_customer × 0.35) + (co_dev × 0.25)
```

**Ollama system prompt for all three scores:**
```
You are an investment analyst evaluating synergy potential between two portfolio companies.
Company A profile: {profile_a}
Company B profile: {profile_b}

Score the following on a scale of 0–100:
1. service_bridge_score: Can Company A's services satisfy Company B's operational needs or strategic gaps, or vice versa?
2. shared_customer_score: How much do their target customer segments overlap?
3. co_dev_score: Could they co-develop a new product or service together that neither could build alone?

Also return:
4. synergy_types_triggered: array containing any of ["SERVICE", "CUSTOMER", "CO_DEV"] where score > 40
5. match_explanation: one plain-language sentence describing the strongest synergy opportunity
6. value_creation_type: one of "cost_saving", "revenue_expansion", "new_market"
7. value_estimate_label: a rough estimate label like "~120,000 TND annual savings" (make reasonable estimates based on context)
8. action_suggestion: one concrete next step for the PE analyst (e.g. "Introduce founders", "Draft pilot agreement", "Conduct feasibility study")

Return ONLY a valid JSON object with exactly these 8 keys.
No explanation. No markdown. No backticks.
```

**Confidence logic:**
- HIGH: both profiles are HIGH confidence AND composite_score ≥ 70
- MEDIUM: at least one profile is MEDIUM confidence OR composite 55–69
- LOW: any profile is LOW confidence

---

## The Gap Detector — Agent Logic

**File:** `backend/synergy/agents/gap_detector.py`

**Input:** All `synergy_profiles` rows for current portfolio
**Output:** Populated `synergy_gaps` rows

**Step 1 — Collect all needs:**
Merge `operational_needs` and `strategic_gaps` across every portfolio company into one flat list, tagged by company name.

**Step 2 — Cluster similar needs:**
Use the LLM to group semantically similar needs into clusters. Each cluster becomes one gap.

```
You are analyzing the unmet needs of a portfolio of startups.
Below is a list of needs tagged by company name.
Group semantically similar needs into clusters.
For each cluster return:
- gap_label: a short descriptive name (3–6 words)
- need_description: one sentence explaining the need
- affected_companies: array of company names in this cluster

Return ONLY a valid JSON array of cluster objects.
No explanation. No markdown. No backticks.
```

**Step 3 — Filter out internally satisfied needs:**
For each gap cluster, check if any portfolio company's `services_offered` satisfies it.
- If satisfied AND the corresponding synergy pair has `analyst_decision = 'approved'` → mark gap as `filled`, do not show.
- If satisfied but pair not yet approved → show gap with a note: "May be fillable by [Company]. Pending synergy approval."
- If not satisfied by any portfolio company → gap is `open`, eligible for gap hunting.

**Step 4 — Compute urgency score:**
```
urgency = (affected_count / total_portfolio_size × 40)
        + (cost_intensity_estimate × 30)   # LLM-estimated, 0–30
        + (mandate_fit_score × 30)         # does this sector fit PE mandate, 0–30
```
Clamp to 0–100.

---

## The Gap Hunter — Web Search Agent Logic

**File:** `backend/synergy/agents/gap_hunter.py`

**Input:** One `synergy_gaps` row (status = 'open')
**Output:** 3–5 `gap_shortlist` rows with real company data

**This agent uses the Anthropic API with web_search tool — not Ollama.**

```python
import httpx

async def hunt_gap(gap: dict) -> list[dict]:
    prompt = f"""
    You are an investment sourcing analyst. 
    A PE portfolio has this unmet need: "{gap['need_description']}"
    Affected companies: {gap['affected_companies']}
    Suggested sector: {gap['suggested_sector']}
    
    Search for 3 to 5 real startups or SMEs that could fill this need.
    For each company return:
    - company_name
    - website
    - description (one sentence)
    - fit_score (0–100, how well it fills the stated need)
    - fit_reason (one sentence)
    - flags (array of warning strings, e.g. "Early stage — limited traction data", "Foreign HQ — import complexity")
    - source_url (the URL where you found this information)
    
    Prioritize companies that are:
    - Active and recently funded
    - Relevant to the Tunisian or MENA market when possible
    - At Seed to Series A stage (ideal acquisition/investment target)
    
    Return ONLY a valid JSON array of company objects.
    """

    response = await httpx.AsyncClient().post(
        "https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json"},
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    text = "".join(b["text"] for b in data["content"] if b["type"] == "text")
    # Strip JSON fences if present
    clean = text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(clean)
```

**Error handling:** If the API call fails or JSON parse fails, return a pre-loaded fallback from `demo_synergy_seed.json` for the demo. Never crash. Never show an empty gap panel.

**Rate limit protection:** Only trigger gap hunting when the analyst explicitly clicks "Hunt for Startups" on a gap card. Do not auto-hunt all gaps on page load.

---

## The Match Engine — Orchestration

**File:** `backend/synergy/engine/match_engine.py`

Full pipeline triggered by `POST /api/synergy/run`:

```
1. For each portfolio company with no synergy_profile:
      → Run profile_extractor
2. For each possible pair with no synergy_pairs row:
      → Run pair_scorer
3. Run gap_detector on all profiles
4. Return:
      synergy_pairs (composite ≥ 55, sorted descending)
      synergy_gaps (status = open | partially_filled, sorted by urgency)
      portfolio_graph_data (nodes + edges for frontend graph)
```

**Portfolio graph data format:**
```json
{
  "nodes": [
    { "id": "EduFlow", "sector": "EdTech", "stage": "Seed" },
    ...
  ],
  "edges": [
    {
      "source": "NovaPay",
      "target": "EduFlow",
      "composite_score": 65,
      "types": ["SERVICE", "CO_DEV"],
      "analyst_decision": null
    },
    ...
  ]
}
```

**Auto-trigger:** When any deal is updated with `portfolio_added = true` (called by `synergy_trigger.py`), run the full pipeline silently in the background and store results. Show a notification badge on the Synergy nav item.

---

## API Endpoints

All endpoints under `/api/synergy/`.

```
GET  /api/synergy/status
     → { profiles_ready: int, pairs_computed: int, gaps_detected: int, last_run: ISO }

POST /api/synergy/run
     → Triggers full match engine. Returns synergy summary.

GET  /api/synergy/graph
     → Returns portfolio graph data (nodes + edges).

GET  /api/synergy/pairs
     → Returns all synergy_pairs with composite ≥ 55, sorted by composite desc.
     Query params: ?type=SERVICE|CUSTOMER|CO_DEV  ?decision=pending|approved|rejected

GET  /api/synergy/pairs/{pair_id}
     → Full detail for one pair.

POST /api/synergy/pairs/{pair_id}/decide
     Body: { decision: "approved"|"rejected"|"snoozed", reason: string, snooze_days: int }
     → Updates analyst_decision in DB. Triggers synergy_feedback.

GET  /api/synergy/gaps
     → Returns all synergy_gaps sorted by urgency desc.

POST /api/synergy/gaps/{gap_id}/hunt
     → Triggers gap_hunter web search agent. Returns gap_shortlist.

POST /api/synergy/gaps/{gap_id}/shortlist/{shortlist_id}/action
     Body: { action: "add_to_pipeline"|"dismissed" }
     → If add_to_pipeline: creates a new sourced lead entry in deal_history pipeline.

GET  /api/synergy/company/{company_name}/mini
     → Returns top 3 matches + gap count for a company. Used by SynergyMiniWidget.
```

---

## Frontend — UI Specification

### Navigation
Add **"Synergy"** as a new item in the main ConvictAI sidebar, between "Monitor" and "Mandate."
Show a **purple dot badge** when new synergy matches are pending analyst review.

---

### SynergyPage.jsx — Full Page Layout

**Tab 1: Portfolio Synergies**

Top half (40% of viewport): **PortfolioGraph.jsx**
- Each portfolio company is a circular node. Node color = sector color (consistent with Dashboard).
- Edges between matched pairs. Edge thickness = composite score / 20 (so score 100 = thickness 5, score 55 = thickness 2.75).
- Edge color: SERVICE = blue, CUSTOMER = green, CO_DEV = orange. Multi-type edges = purple.
- Approved pairs: solid line. Pending: dashed. Rejected: hidden by default (toggle to show).
- Clicking an edge opens the SynergyCard drawer for that pair.
- Clicking a node highlights all its connections and dims others.

Bottom half (60% of viewport): **SynergyPairTable.jsx**
- Columns: Company A | Company B | Types | Composite Score | Confidence | Value Type | Action
- Sortable by composite score (default: descending).
- Filter buttons: All | Service Bridge | Shared Customer | Co-Dev | Pending Review
- Each row has inline buttons: **Approve** (green) | **Reject** (red) | **Snooze** (gray)
- Clicking a row expands the SynergyCard inline below it.

**SynergyCard (expanded):**
- Header: Company A ↔ Company B, composite score badge, confidence badge
- Three score bars: Service Bridge / Shared Customer / Co-Dev (color coded, with labels)
- Match explanation paragraph (AI-generated)
- Value creation type chip + estimate label
- Action suggestion (bold)
- Approve / Reject / Snooze buttons with reason input field
- Footer: "Last computed: [datetime]"

---

**Tab 2: Gap Intelligence**

Two-column layout:

**Left column — Gap Report (GapPanel.jsx)**
- Header: "X unmet needs detected across the portfolio"
- One GapCard per gap, sorted by urgency score descending.

**GapCard:**
- Gap label (bold)
- Need description (one line)
- Affected companies (avatar/chip row)
- Urgency score bar (color coded: red ≥ 75, amber 50–74, green < 50)
- Estimated annual spend label
- Status badge: OPEN | HUNTING | PARTIALLY FILLED | FILLED | DISMISSED
- "Hunt for Startups →" button (triggers web search agent, shows loading spinner)
- "Dismiss" button

**Right column — Shortlist (ExternalStartupCard.jsx)**
- Appears after "Hunt" is clicked and results return.
- Header: "Found X companies for: [gap label]"
- One ExternalStartupCard per result.

**ExternalStartupCard:**
- Company name (bold) + website link
- Description (one line)
- Fit Score bar (color coded)
- Fit reason paragraph
- Flags: each flag is an amber warning chip
- "Add to Pipeline →" button → creates a deal entry in ConvictAI pipeline with source = 'synergy_gap_hunt'
- "Dismiss" button

---

### SynergyMiniWidget.jsx — Embedded in Existing Pages

Shown on each company's scorecard page (Evaluate.jsx) when `portfolio_added = true`.

```
┌─────────────────────────────────────────┐
│  🔗 Synergy Opportunities               │
│                                         │
│  NovaPay ↔ EduFlow        65  SERVICE  │
│  NovaPay ↔ HealthCore     68  SERVICE  │
│  + 1 pending gap                        │
│                                         │
│  [View All Synergies →]                 │
└─────────────────────────────────────────┘
```

Clicking "View All Synergies" navigates to SynergyPage with that company's node highlighted.

---

### Integration with Existing Dashboard.jsx

Add a **"Synergy"** column to the ComparisonTable. For each portfolio company:
- Show the count of approved synergies as a green chip (e.g. "2 active")
- Show the count of pending synergies as an amber chip (e.g. "1 pending")
- For non-portfolio pipeline startups, show a gray "—"

---

## The Feedback Loop

**File:** `backend/synergy/engine/synergy_feedback.py`

Called every time an analyst makes a decision (approve/reject/snooze).

**On Approve:**
- Set `analyst_decision = 'approved'` in `synergy_pairs`.
- Check if this pair satisfies any open `synergy_gaps` → if yes, update gap status to `filled`.
- Log to a `synergy_decisions` audit trail (company_a, company_b, decision, reason, decided_at).
- Future pair scoring for similar company profiles gets a signal: approved pairs in the same sector combination increase confidence of similar matches.

**On Reject:**
- Set `analyst_decision = 'rejected'` + store reason.
- The pair is hidden from the default table view (shown only if analyst toggles "Show Rejected").
- Rejection reason is used to weight down similar future matches (e.g. "founders clashed" → reduce team-culture compatibility factor).

**On Snooze:**
- Set `analyst_decision = 'snoozed'` + `snooze_until` date.
- Show a "Snoozed" badge on the pair. Re-surface automatically after `snooze_until` passes.

---

## Build Phases

### PHASE S1 — Profile Extraction + Data Layer
**Goal:** Every portfolio company has a SynergyProfile in the DB. Seed data loaded.
**Done when:** `GET /api/synergy/status` returns `profiles_ready = 5`.

Tasks:
- [ ] Create `synergy_profiles`, `synergy_pairs`, `synergy_gaps`, `gap_shortlist` tables in `database.py`
- [ ] `profile_extractor.py` — Ollama extraction + confidence logic
- [ ] `synergy_routes.py` — basic route setup
- [ ] `GET /api/synergy/status` endpoint
- [ ] Load `demo_synergy_seed.json` on startup (profiles + pre-computed pairs)
- [ ] Verify all 5 demo company profiles populate correctly

---

### PHASE S2 — Pair Scoring + Network Graph
**Goal:** All pairs scored. Graph renders with correct edges. Pairs table shows ranked matches.
**Done when:** PortfolioGraph and SynergyPairTable both render with real data.

Tasks:
- [ ] `pair_scorer.py` — 3-score Ollama prompt + composite formula
- [ ] `match_engine.py` — orchestration pipeline
- [ ] `POST /api/synergy/run` endpoint
- [ ] `GET /api/synergy/pairs` endpoint with filter support
- [ ] `GET /api/synergy/graph` endpoint
- [ ] `SynergyPage.jsx` scaffold with two tabs
- [ ] `PortfolioGraph.jsx` — D3 force-directed graph (nodes + edges, color + thickness)
- [ ] `SynergyPairTable.jsx` — sortable/filterable table
- [ ] `SynergyCard.jsx` — expanded pair detail drawer
- [ ] `SynergyTypeBadge.jsx` + `SynergyScoreBar.jsx` shared components
- [ ] Add "Synergy" to sidebar nav with badge

---

### PHASE S3 — Analyst Decisions + Feedback Loop
**Goal:** Approve/Reject/Snooze work. Decisions persist. Graph updates live.
**Done when:** Approving a pair turns its edge solid. Rejecting hides it. DB persists across reload.

Tasks:
- [ ] `POST /api/synergy/pairs/{pair_id}/decide` endpoint
- [ ] `synergy_feedback.py` — decision logging + gap status update
- [ ] Approve/Reject/Snooze buttons in SynergyCard with reason input
- [ ] Graph edge style updates after decision (dashed → solid on approve, hidden on reject)
- [ ] `SynergyMiniWidget.jsx` — embedded in Evaluate.jsx scorecard for portfolio companies
- [ ] Dashboard.jsx Synergy column integration

---

### PHASE S4 — Gap Detection + Gap Panel
**Goal:** Gap panel shows all open gaps with urgency scores. GapCards render correctly.
**Done when:** Gap tab shows ≥ 3 gaps with urgency scores and affected company chips.

Tasks:
- [ ] `gap_detector.py` — need clustering + internal satisfaction filter + urgency scoring
- [ ] `GET /api/synergy/gaps` endpoint
- [ ] `GapPanel.jsx` — gap list sorted by urgency
- [ ] `GapCard.jsx` — gap detail with status badge and actions
- [ ] Gap status updates when a related synergy pair is approved
- [ ] Dismiss action on GapCard

---

### PHASE S5 — Gap Hunter + External Shortlist
**Goal:** Clicking "Hunt for Startups" returns a real shortlist from web search. Add to Pipeline works.
**Done when:** One gap hunt returns ≥ 3 external companies with Fit Scores. "Add to Pipeline" pushes a new deal record.

Tasks:
- [ ] `gap_hunter.py` — Anthropic API call with web_search tool
- [ ] Fallback to `demo_synergy_seed.json` shortlist if API call fails
- [ ] `POST /api/synergy/gaps/{gap_id}/hunt` endpoint
- [ ] `ExternalStartupCard.jsx` — company name, website, fit score bar, flags, actions
- [ ] Right-column shortlist render in GapPanel after hunt completes
- [ ] `POST /api/synergy/gaps/{gap_id}/shortlist/{id}/action` endpoint
- [ ] Add-to-pipeline: creates `deal_history` record with `source = 'synergy_gap_hunt'`, `decision = NULL`, appears in ComparisonTable as new pipeline entry

---

### PHASE S6 — Auto-Trigger + Demo Polish
**Goal:** New portfolio company triggers synergy run automatically. Demo flow works end to end.
**Done when:** Full demo narrative runs without surprises in under 4 minutes.

Tasks:
- [ ] `synergy_trigger.py` — watch for `portfolio_added = true` events, auto-run match engine
- [ ] Purple badge on Synergy nav item when pending decisions exist
- [ ] Loading states for all async operations (graph, pair scoring, gap hunting)
- [ ] Error state: Ollama not running → graceful fallback to seed data, show notice
- [ ] Error state: web search fails → use pre-loaded shortlist, show "Simulated results" label
- [ ] Snooze auto-resurface logic (check snooze_until on page load)
- [ ] Final visual polish: consistent color coding, spacing, typography

---

## Demo Flow — 3.5 Minutes

```
(0:00–0:30)  Open Synergy tab → Portfolio Graph renders with 5 nodes and 3 visible edges
             "SynergyAI has analyzed our 5 portfolio companies and found 3 collaboration opportunities."

(0:30–1:00)  Click the NovaPay ↔ HealthCore edge → SynergyCard opens
             "NovaPay's payment gateway eliminates HealthCore's external invoicing vendor.
              Co-dev opportunity: a healthcare-compliant billing module."
             Click Approve → edge turns solid, graph updates live

(1:00–1:30)  Scroll to Pairs Table → show ranked list, filter by "Service Bridge"
             "Every match has three dimensions scored independently."

(1:30–2:00)  Switch to Gap Intelligence tab → show 4 gap cards sorted by urgency
             "These are the needs our portfolio pays for externally every year."

(2:00–2:45)  Click "Hunt for Startups" on the HR Tech gap → loading spinner →
             3 external companies appear with Fit Scores
             "In real time, SynergyAI searched the web and found 3 real companies
              that could fill this gap. This is our next deal thesis — generated by the portfolio itself."

(2:45–3:00)  Click "Add to Pipeline" on the top-scored company →
             Switch to Dashboard → company appears in ComparisonTable as a new sourced lead
             "One click — it's now in our screening pipeline."

(3:00–3:30)  Show SynergyMiniWidget on NovaPay's scorecard
             "Every invested company now shows its active synergies.
              The portfolio is no longer a list. It's a network."
```

---

## Score Color Coding — Same as CLAUDE.md

Use the exact same thresholds everywhere:
```
75–100  →  green   (#22c55e)
60–74   →  amber   (#f59e0b)
45–59   →  orange  (#f97316)
0–44    →  red     (#ef4444)
```

Synergy Type badge colors:
```
SERVICE   →  blue   (#3b82f6)
CUSTOMER  →  green  (#22c55e)
CO_DEV    →  orange (#f97316)
MULTI     →  purple (#a855f7)
```

Gap urgency colors:
```
75–100  →  red    (critical)
50–74   →  amber  (moderate)
0–49    →  green  (low)
```

---

## What Claude Code Must Never Do

- Never run the pair scorer on non-portfolio companies (pipeline-only startups have no synergy_profile)
- Never auto-approve a synergy match — the analyst button is always required
- Never trigger gap hunting on page load — only on explicit analyst click
- Never crash if the Anthropic web search API fails — always fall back to seed shortlist data
- Never display a gap as "FILLED" unless the corresponding synergy pair has `analyst_decision = 'approved'`
- Never show a composite score without also showing the three component scores
- Never omit the Fit Score on ExternalStartupCard — it is mandatory for every shortlist result
- Never let the "Add to Pipeline" action create a duplicate deal_history record for the same company

---

*This file is the single source of truth for Claude Code — SynergyAI module.*
*Do not improvise architecture. Follow the phases in order.*
*Read CLAUDE.md and MONITORING.md first — this module inherits all constraints defined there.*
*Built for the CapAI Hackathon — post-investment value creation axis.*
