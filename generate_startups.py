"""
generate_startups.py
Generates 6 realistic pitch deck PDFs for ConvictAI evaluation testing.
Run from project root: python generate_startups.py

Target verdicts:
  AuraLearn  — EdTech      / Seed      / MENA          → PURSUE
  NexaLend   — FinTech     / Series A  / Europe        → PURSUE
  CoolChain  — Logistics   / Seed      / Asia          → WATCH
  MindBridge — HealthTech  / Pre-seed  / North America → WATCH
  BrickScan  — Construction Tech / Seed / Europe       → SOFT PASS
  VerdaGrow  — AgriTech    / Pre-seed  / MENA          → PASS
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ── colours ──────────────────────────────────────────────────────────
BRAND = HexColor("#1a56db")
DARK  = HexColor("#111827")
MID   = HexColor("#6b7280")
LIGHT = HexColor("#f3f4f6")
WARN  = HexColor("#f59e0b")
GREEN = HexColor("#10b981")

# ── styles ───────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

H1   = S("H1",   fontName="Helvetica-Bold",  fontSize=28, textColor=BRAND, spaceAfter=10, leading=34)
H2   = S("H2",   fontName="Helvetica-Bold",  fontSize=15, textColor=BRAND, spaceBefore=12, spaceAfter=6, leading=20)
H3   = S("H3",   fontName="Helvetica-Bold",  fontSize=11, textColor=DARK,  spaceBefore=8,  spaceAfter=4, leading=15)
BODY = S("BODY", fontName="Helvetica",        fontSize=10, textColor=DARK,  leading=15, spaceAfter=5)
SMALL= S("SMALL",fontName="Helvetica",        fontSize=9,  textColor=MID,   leading=13, spaceAfter=4)
BOLD = S("BOLD", fontName="Helvetica-Bold",   fontSize=10, textColor=DARK,  leading=15, spaceAfter=5)
CTR  = S("CTR",  fontName="Helvetica",        fontSize=10, textColor=MID,   leading=15, alignment=TA_CENTER)

def new_doc(path):
    return SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
    )

def cover(name, tagline, sector, stage, geography, ask):
    return [
        Spacer(1, 1.5*cm),
        Paragraph(name, H1),
        HRFlowable(width="100%", thickness=2, color=BRAND, spaceAfter=8),
        Paragraph(tagline, S("tag", fontName="Helvetica", fontSize=13, textColor=MID, leading=18, spaceAfter=12)),
        Spacer(1, 0.8*cm),
        Paragraph("CONFIDENTIAL INVESTMENT MEMORANDUM", S("conf", fontName="Helvetica-Bold", fontSize=9, textColor=WARN, spaceAfter=10)),
        Spacer(1, 0.8*cm),
        tbl(
            [["Sector", sector], ["Stage", stage], ["Geography", geography], ["Funding Ask", ask]],
            [5*cm, 10*cm],
        ),
        PageBreak(),
    ]

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=LIGHT, spaceAfter=6, spaceBefore=4)

def tbl(data, col_widths):
    ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1,-1), [white, LIGHT]),
        ("GRID",          (0, 0), (-1,-1), 0.4, HexColor("#e5e7eb")),
        ("TOPPADDING",    (0, 0), (-1,-1), 6),
        ("BOTTOMPADDING", (0, 0), (-1,-1), 6),
        ("LEFTPADDING",   (0, 0), (-1,-1), 8),
        ("RIGHTPADDING",  (0, 0), (-1,-1), 8),
    ])
    return Table(data, colWidths=col_widths, style=ts, hAlign="LEFT", spaceBefore=4, spaceAfter=8)

OUT = "test_docs"
os.makedirs(OUT, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# 1. AURALEARN — EdTech · Seed · MENA  → Target: PURSUE
#    No red flags. Strong team with prior exits, clean ESG, named board.
# ═══════════════════════════════════════════════════════════════════════
def gen_auralearn():
    d = new_doc(f"{OUT}/AuraLearn_pitch_deck.pdf")
    s = cover(
        "AuraLearn",
        "AI-Adaptive Learning for K-12 Students Across the Arab World",
        "EdTech", "Seed", "MENA", "USD 2,000,000"
    )

    s += [
        Paragraph("Executive Summary", H2),
        Paragraph(
            "AuraLearn is an AI-powered adaptive learning platform for K-12 students in the MENA region, "
            "delivering personalised Arabic and French instruction aligned with national curricula. Our proprietary "
            "recommendation engine adjusts lesson difficulty in real time based on each student's pace and engagement. "
            "Founded in 2022 and commercially launched in September 2023, AuraLearn has reached 50,000 active "
            "students across 12 partner schools in Tunisia, Morocco, and Jordan, generating USD 180,000 in ARR.",
            BODY
        ),
        Paragraph("Problem", H3),
        Paragraph(
            "MENA K-12 classrooms average 38 students per teacher, leaving 60% of students under-challenged or "
            "left behind. Existing EdTech platforms (Khan Academy, Alef Education) are English-language-first and "
            "unaffordable for public schools. The UNESCO 2023 Learning Poverty Report identifies MENA as the region "
            "with the highest share of 10-year-olds who cannot read a simple text.",
            BODY
        ),
        Paragraph("Solution", H3),
        Paragraph(
            "A tablet-first web application requiring only 2G connectivity, with fully localised Arabic and French "
            "adaptive curricula. Schools subscribe at USD 8 per active student per month, billed annually. Teacher "
            "dashboards provide real-time learning analytics. We have filed a provisional patent for our adaptive "
            "sequencing algorithm (Reference: TN-2024-IP-0041).",
            BODY
        ),
        hr(),
        Paragraph("Founding Team", H2),
        tbl(
            [
                ["Name", "Role", "Background", "LinkedIn"],
                ["Sara Ben Ali", "CEO & Co-Founder",
                 "Ex-Coursera Product Manager EMEA; MBA Stanford GSB; "
                 "Founded LearnArabic.com (prior exit: sold to Hachette Education for USD 3.2M in 2021)",
                 "linkedin.com/in/sara-ben-ali-edtech"],
                ["Khalil Mansour", "CTO & Co-Founder",
                 "Ex-Google AI Paris; PhD Computer Science, Ecole Polytechnique; "
                 "12 NLP patents; 8 years applied AI in education",
                 "linkedin.com/in/khalil-mansour-ai"],
                ["Amira Chahed", "CPO & Co-Founder",
                 "Ex-Pearson EdTech (10 years); K-12 curriculum specialist; "
                 "UNESCO advisor on Arab literacy programmes",
                 "linkedin.com/in/amira-chahed-education"],
            ],
            [3.5*cm, 3*cm, 7.5*cm, 4*cm]
        ),
        Paragraph(
            "Advisory Board: Prof. Leila Nasser (MIT Media Lab, EdTech Research), "
            "Dr. Ahmed Tlili (UNESCO Institute for IT in Education), "
            "Marie-Claire Dupont (former CFO, Vivendi Education). "
            "Board of Directors: 3 members including one independent director — "
            "Ms. Fatima Zahra Benchekroun (impact investor, Maroc Numeric Fund). "
            "Board decisions require majority vote; no single founder holds a unilateral veto.",
            SMALL
        ),
        Paragraph("Market Sizing", H3),
        Paragraph(
            "Total Addressable Market: USD 4.2 billion — MENA K-12 EdTech (HolonIQ 2024 Report). "
            "Serviceable Addressable Market: USD 680 million — Arabic and French-medium schools in Tunisia, "
            "Morocco, Jordan, Egypt with technology budgets. "
            "Serviceable Obtainable Market: USD 34 million — urban and peri-urban schools, 200–2,000 students.",
            BODY
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("Revenue Model & Traction", H2),
        Paragraph(
            "School-level SaaS subscription: USD 8 per active student per month, billed annually. "
            "Revenue recognition is straight-line across the academic year (September–June). "
            "Upsell path: premium analytics module at USD 2 per student per month (launched Q1 2024).",
            BODY
        ),
        tbl(
            [
                ["Metric", "Current Value"],
                ["Annual Recurring Revenue (ARR)", "USD 180,000"],
                ["Active Students", "50,000"],
                ["Partner Schools", "12"],
                ["Monthly ARR Growth (Jan–May 2024)", "14% month-on-month"],
                ["Average Contract Value per School", "USD 15,000 per year"],
                ["Customer Acquisition Cost (CAC)", "USD 1,200 per school"],
                ["Customer Lifetime Value (LTV)", "USD 45,000 (3-year avg. contract)"],
                ["Net Revenue Retention", "112% (upsell from student count growth)"],
            ],
            [9*cm, 8*cm]
        ),
        Paragraph("Competitive Differentiation", H3),
        tbl(
            [
                ["Competitor", "Key Weakness vs AuraLearn"],
                ["Khan Academy", "English-only; no Arabic adaptive curriculum; no school admin tools"],
                ["Alef Education", "USD 30+ per student per month; unaffordable for public schools; UAE-centric"],
                ["Google for Education", "Content-agnostic; no adaptive engine; not MENA localised"],
            ],
            [5*cm, 12*cm]
        ),
        Paragraph("Milestones", H3),
        tbl(
            [
                ["Date", "Milestone"],
                ["Sep 2022", "Incorporated in Tunisia; USD 400K seed from BIAT Ventures"],
                ["Feb 2023", "Beta with 3 pilot schools; 800 students"],
                ["Sep 2023", "Commercial launch; 8 schools; USD 80K ARR"],
                ["Mar 2024", "Jordan partnership; 4 additional schools; ARR reaches USD 180K"],
                ["Q3 2024", "Series A target: Egypt and Saudi Arabia; 100 schools; 200K students"],
            ],
            [3*cm, 14*cm]
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("ESG, Governance & Financial Projections", H2),
        Paragraph("Environmental Commitments", H3),
        Paragraph(
            "AuraLearn operates exclusively on AWS carbon-neutral compute regions (EU-West and ME-South-1). "
            "Total annual cloud infrastructure carbon footprint: 0.8 tonnes CO2e, verified by a third-party "
            "carbon audit conducted by EcoAct (Audit Report No. EA-2024-0912, September 2024). Residual emissions "
            "offset through Gold Standard-certified reforestation credits in Morocco.",
            BODY
        ),
        Paragraph("Social Commitments", H3),
        Paragraph(
            "58% of our student base is female, directly supporting gender equity in education. Named diverse leaders: "
            "Sara Ben Ali (CEO, Arab woman, co-founder), Amira Chahed (CPO, Arab woman, co-founder). "
            "1,200 students in UNHCR refugee learning centres in Jordan receive full free platform access. "
            "All full-time employees (no gig labour). User data is processed under a published privacy policy "
            "(auralearn.tn/privacy), compliant with Tunisia Law No. 63-2004 on personal data protection.",
            BODY
        ),
        Paragraph("Governance", H3),
        Paragraph(
            "Board: 3 members, majority-vote required — Sara Ben Ali (Executive Chair), Khalil Mansour "
            "(Non-Executive Director), Fatima Zahra Benchekroun (Independent Director, appointed 2023). "
            "Quarterly financial review by Deloitte Tunis. Cap table: Founders 60%, BIAT Ventures 25%, ESOP 15%.",
            BODY
        ),
        hr(),
        Paragraph("Financial Projections", H3),
        Paragraph(
            "Projection assumptions: 14% MoM school acquisition growth based on Q1 2024 pipeline data; "
            "average ACV of USD 15,000 per school; average school size of 4,000 students; annual churn rate "
            "of 5% derived from Year 1 cohort data; gross margin of 72% (primarily AWS hosting and content costs).",
            BODY
        ),
        tbl(
            [
                ["Metric", "Year 1 (2024)", "Year 2 (2025)", "Year 3 (2026)"],
                ["Active Schools", "25", "65", "150"],
                ["Active Students", "100,000", "260,000", "600,000"],
                ["ARR (USD)", "375,000", "975,000", "2,250,000"],
                ["Gross Margin", "72%", "74%", "76%"],
                ["Operating Burn (USD)", "420,000", "380,000", "150,000"],
            ],
            [6*cm, 3.5*cm, 3.5*cm, 3.5*cm]
        ),
        Paragraph(
            "Use of USD 2M Seed Round: 45% product engineering, 30% school sales team, "
            "15% content localisation (Egypt, Saudi Arabia curricula), 10% operations.",
            SMALL
        ),
    ]
    d.build(s)
    print("  AuraLearn_pitch_deck.pdf")


# ═══════════════════════════════════════════════════════════════════════
# 2. NEXALEND — FinTech · Series A · Europe  → Target: PURSUE
#    No red flags. Ex-Stripe/JPMorgan team, EUR 2.1M ARR, clear board.
# ═══════════════════════════════════════════════════════════════════════
def gen_nexalend():
    d = new_doc(f"{OUT}/NexaLend_pitch_deck.pdf")
    s = cover(
        "NexaLend",
        "Embedded Lending Infrastructure for European E-Commerce",
        "FinTech", "Series A", "Europe", "EUR 8,000,000"
    )

    s += [
        Paragraph("Executive Summary", H2),
        Paragraph(
            "NexaLend provides an API-first embedded lending platform that enables e-commerce merchants to offer "
            "instant buy-now-pay-later and working-capital financing at the point of checkout. Our credit engine "
            "underwrites decisions in under 1.2 seconds using real-time sales data. Founded in Berlin in 2021 by "
            "two former senior executives from Stripe and JPMorgan, NexaLend has reached EUR 2.1M ARR with "
            "35 active merchant integrations and is growing at 40% month-on-month.",
            BODY
        ),
        Paragraph("Problem", H3),
        Paragraph(
            "60% of European SME e-commerce merchants lose sales because customers abandon checkout when "
            "financing options are unavailable or slow. Traditional bank credit for merchants takes 3–8 weeks. "
            "Existing BNPL solutions (Klarna, Afterpay) are consumer-facing and charge merchants 4–7% per "
            "transaction, eroding already thin margins. The embedded lending market in Europe is projected at "
            "EUR 85 billion by 2026 (McKinsey Global Payments Report, 2023).",
            BODY
        ),
        Paragraph("Solution", H3),
        Paragraph(
            "A single API integration (3 lines of code) embeds NexaLend's lending widget into any checkout flow. "
            "NexaLend earns a 2.5% revenue share on every loan originated. Merchants receive funds within 24 hours. "
            "Credit decisions use the merchant's live Stripe/Shopify sales data, bypassing the need for traditional "
            "financial statements. Fully licensed under the EU Consumer Credit Directive (License DE-BaFin-2023-CCL-0091).",
            BODY
        ),
        hr(),
        Paragraph("Founding Team", H2),
        tbl(
            [
                ["Name", "Role", "Background", "LinkedIn"],
                ["Marcus Weber", "CEO & Co-Founder",
                 "Ex-Stripe Head of EMEA Partnerships (2017–2021); "
                 "Built Stripe's EUR 400M revenue partnership network in Europe; MBA INSEAD",
                 "linkedin.com/in/marcus-weber-fintech"],
                ["Priya Nair", "CTO & Co-Founder",
                 "Ex-JPMorgan VP Engineering, Credit Risk Systems (2014–2021); "
                 "Led JPMorgan's real-time underwriting API used across 18 European markets",
                 "linkedin.com/in/priya-nair-engineering"],
            ],
            [3.5*cm, 3*cm, 8*cm, 4*cm]
        ),
        Paragraph(
            "Board of Directors: 5 members — Marcus Weber (Executive Chair), Priya Nair (Non-Executive Director), "
            "Dr. Klaus Bremer (Independent Director, former BaFin Regulator, appointed 2022), "
            "Anna Kowalski (Independent Director, Partner at Sequoia Europe, appointed 2022), "
            "Thomas Gruber (Non-Executive Director, representing seed investor FinLeap Ventures). "
            "Named leadership team: Head of Credit Risk — Dr. Sofia Petrov (ex-N26, linkedin.com/in/sofia-petrov-credit); "
            "Head of Sales — James O'Brien (ex-Adyen, linkedin.com/in/james-obrien-payments).",
            SMALL
        ),
        Paragraph("Market Sizing", H3),
        Paragraph(
            "Total Addressable Market: EUR 85 billion — embedded lending for European e-commerce (McKinsey, 2023). "
            "Serviceable Addressable Market: EUR 12 billion — SME merchants on Shopify, WooCommerce, and Magento "
            "in Germany, France, Netherlands, and Poland. "
            "Serviceable Obtainable Market: EUR 600 million — merchants with EUR 500K–EUR 10M annual GMV "
            "in NexaLend's current operating markets.",
            BODY
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("Revenue Model & Traction", H2),
        Paragraph(
            "Revenue model: 2.5% fee on every loan originated through the NexaLend platform. "
            "Average loan size: EUR 1,800. Average merchant processes 48 loans per month. "
            "Merchant contracts are 24-month minimum with auto-renewal.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Current Value"],
                ["Annual Recurring Revenue (ARR)", "EUR 2,100,000"],
                ["Active Merchant Integrations", "35"],
                ["Monthly ARR Growth (Q1 2024)", "40% month-on-month"],
                ["Total Loan Volume Originated (lifetime)", "EUR 84,000,000"],
                ["Average Contract Value (ACV)", "EUR 60,000 per merchant per year"],
                ["Customer Acquisition Cost (CAC)", "EUR 3,200 per merchant"],
                ["Customer Lifetime Value (LTV)", "EUR 120,000 (24-month avg. contract)"],
                ["LTV : CAC Ratio", "37.5x"],
                ["Default Rate on Originated Loans", "1.1% (vs. industry average 3.8%)"],
            ],
            [9*cm, 8*cm]
        ),
        Paragraph("Competitive Differentiation", H3),
        tbl(
            [
                ["Competitor", "Key Weakness vs NexaLend"],
                ["Klarna", "Consumer-facing; charges 4-7% per transaction; not API-first for merchants"],
                ["Younited Credit", "Slow credit decisions (24-48 hours); no real-time sales data integration"],
                ["Hokodo", "Invoice financing only; no checkout BNPL; limited to B2B"],
            ],
            [5*cm, 12*cm]
        ),
        Paragraph("Milestones", H3),
        tbl(
            [
                ["Date", "Milestone"],
                ["Jan 2021", "Incorporated in Berlin; EUR 1.2M pre-seed from FinLeap Ventures"],
                ["Sep 2021", "BaFin consumer credit licence granted"],
                ["Mar 2022", "First 5 merchant integrations; EUR 180K ARR"],
                ["Jan 2023", "EUR 2M seed round closed (FinLeap + Sequoia Europe)"],
                ["Jun 2024", "EUR 2.1M ARR; 35 merchants; expanding to Poland and France"],
            ],
            [3*cm, 14*cm]
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("ESG, Governance & Financial Projections", H2),
        Paragraph("Environmental Commitments", H3),
        Paragraph(
            "NexaLend operates on Google Cloud Platform's carbon-neutral EU regions (europe-west3, Frankfurt). "
            "Annual Scope 2 emissions: 0.6 tonnes CO2e (GCP Sustainability Report, Q1 2024). "
            "We are signatory to the SME Climate Hub commitment for net-zero operations by 2030.",
            BODY
        ),
        Paragraph("Social Commitments", H3),
        Paragraph(
            "Named diverse leadership: Priya Nair (CTO, woman of South Asian heritage, co-founder), "
            "Dr. Sofia Petrov (Head of Credit Risk, woman), Anna Kowalski (Board member, woman, Partner Sequoia Europe). "
            "Team of 18 across 8 nationalities. All employment contracts above German minimum wage. "
            "User data processed under EU GDPR; privacy policy published at nexalend.de/privacy; "
            "annual GDPR compliance audit by TUV Rheinland (Certification No. TUV-2024-GDPR-0042). "
            "No proprietary user data is resold; data minimisation principles applied at all pipeline stages.",
            BODY
        ),
        Paragraph("Governance", H3),
        Paragraph(
            "Board: 5 members; independent majority (3 of 5 are independent directors). "
            "Board decisions by majority vote; no individual holds veto rights. "
            "Annual financial audit by KPMG Germany (2022 and 2023 audit reports available on request). "
            "Cap table: Founders 42%, FinLeap Ventures 28%, Sequoia Europe 22%, ESOP pool 8%.",
            BODY
        ),
        hr(),
        Paragraph("Financial Projections", H3),
        Paragraph(
            "Projection assumptions: 40% MoM merchant acquisition growth maintained through Q3 2024, tapering to "
            "15% MoM from Q4 2024 as market matures; average ACV of EUR 60,000 per merchant per year; "
            "default rate held at 1.1% based on Q1–Q2 2024 actual performance; gross margin of 68% "
            "(cost of capital, credit risk reserve, and infrastructure).",
            BODY
        ),
        tbl(
            [
                ["Metric", "Year 1 (2024)", "Year 2 (2025)", "Year 3 (2026)"],
                ["Active Merchants", "80", "200", "450"],
                ["ARR (EUR)", "4,800,000", "12,000,000", "27,000,000"],
                ["Total Loan Volume (EUR)", "192,000,000", "480,000,000", "1,080,000,000"],
                ["Gross Margin", "68%", "70%", "72%"],
                ["Operating Burn (EUR)", "2,200,000", "800,000", "—"],
            ],
            [6*cm, 3.5*cm, 3.5*cm, 3.5*cm]
        ),
        Paragraph(
            "Use of EUR 8M Series A: 40% credit risk reserve expansion, 30% engineering (v2 credit engine), "
            "20% sales and merchant partnerships, 10% regulatory compliance (France, Poland licences).",
            SMALL
        ),
    ]
    d.build(s)
    print("  NexaLend_pitch_deck.pdf")


# ═══════════════════════════════════════════════════════════════════════
# 3. COOLCHAIN — Logistics · Seed · Asia  → Target: WATCH
#    RF-04 (env claims no methodology), RF-06 (projections no assumptions)
# ═══════════════════════════════════════════════════════════════════════
def gen_coolchain():
    d = new_doc(f"{OUT}/CoolChain_pitch_deck.pdf")
    s = cover(
        "CoolChain",
        "IoT-Enabled Cold Chain Last-Mile Logistics for Pharmaceuticals in Southeast Asia",
        "Logistics", "Seed", "Asia", "USD 1,500,000"
    )

    s += [
        Paragraph("Executive Summary", H2),
        Paragraph(
            "CoolChain operates a temperature-controlled last-mile logistics network serving pharmaceutical "
            "distributors and hospital groups across Singapore, Malaysia, and Indonesia. Our IoT-enabled "
            "refrigerated vans and real-time monitoring dashboard ensure FDA-grade cold chain integrity from "
            "warehouse to delivery point. Founded in 2022, CoolChain has completed three paid pilots with "
            "major pharmaceutical clients and generated USD 120,000 in pilot revenue.",
            BODY
        ),
        Paragraph("Problem", H3),
        Paragraph(
            "Southeast Asia loses an estimated USD 1.3 billion in pharmaceutical product annually due to "
            "cold chain failures during last-mile delivery. Existing logistics providers (DHL, FedEx) do not "
            "offer real-time temperature monitoring below vehicle level. Hospital and clinic deliveries require "
            "end-to-end cold chain documentation for regulatory compliance. The SE Asia pharmaceutical logistics "
            "market is valued at USD 2.8 billion and growing at 12% annually (Frost & Sullivan, 2023).",
            BODY
        ),
        Paragraph("Solution", H3),
        Paragraph(
            "Refrigerated delivery vans equipped with CoolChain's proprietary IoT sensors log temperature, "
            "humidity, and GPS location every 30 seconds. A real-time monitoring dashboard alerts dispatchers "
            "to any cold chain deviation. Automated compliance certificates are generated per delivery for "
            "regulatory submission. Pricing: USD 18 per delivery plus a USD 500 monthly platform fee per client.",
            BODY
        ),
        hr(),
        Paragraph("Founding Team", H2),
        tbl(
            [
                ["Name", "Role", "Background"],
                ["David Tan", "CEO & Co-Founder",
                 "8 years at DHL Temperature-Sensitive Division (Singapore); "
                 "led cold chain operations across 6 SE Asian markets; BEng Logistics, NUS"],
                ["Rachel Lim", "COO & Co-Founder",
                 "6 years operations management at Zuellig Pharma; "
                 "specialist in pharmaceutical distribution compliance, GMP logistics; BBA NTU"],
            ],
            [3.5*cm, 3*cm, 11*cm]
        ),
        Paragraph(
            "The founding team does not currently have a dedicated CTO. Technology development is led by "
            "David Tan with support from two contract engineers. CoolChain is actively recruiting a VP of "
            "Engineering to join by Q4 2024. Board currently comprises both co-founders only; "
            "we plan to add an independent board member post-funding.",
            SMALL
        ),
        Paragraph("Market Sizing", H3),
        Paragraph(
            "Total Addressable Market: USD 2.8 billion — SE Asia pharmaceutical logistics (Frost & Sullivan, 2023). "
            "Serviceable Addressable Market: USD 420 million — cold chain last-mile segment in Singapore, "
            "Malaysia, and Indonesia. "
            "Serviceable Obtainable Market: USD 21 million — hospital groups and large pharma distributors "
            "requiring real-time monitoring compliance documentation.",
            BODY
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("Revenue Model & Traction", H2),
        Paragraph(
            "Per-delivery fee model: USD 18 per cold chain delivery plus USD 500 monthly SaaS platform fee. "
            "Clients commit to a minimum of 200 deliveries per month under 12-month service agreements.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Current Value"],
                ["Pilot Revenue (12 months)", "USD 120,000"],
                ["Active Pharmaceutical Clients", "3 (pilot agreements)"],
                ["Deliveries Completed", "6,800"],
                ["Average Revenue per Delivery", "USD 17.65"],
                ["Cold Chain Deviation Rate", "0.3% (industry benchmark: 2.1%)"],
                ["Net Promoter Score", "72 (from client surveys, Q2 2024)"],
            ],
            [9*cm, 8*cm]
        ),
        Paragraph("Competitive Differentiation", H3),
        tbl(
            [
                ["Competitor", "Key Weakness vs CoolChain"],
                ["DHL Medical Express", "No real-time IoT monitoring; no automated compliance certificates"],
                ["Zuellig Pharma Logistics", "Full-distribution model; no last-mile-only API offering for hospitals"],
                ["ColdEx (India)", "India-focused; not licensed for SE Asia regulatory requirements"],
            ],
            [5*cm, 12*cm]
        ),
        Paragraph("Milestones", H3),
        tbl(
            [
                ["Date", "Milestone"],
                ["Jan 2022", "Company incorporated in Singapore; SGD 200K angel round"],
                ["Jun 2022", "First van deployed; Novartis Singapore pilot launched"],
                ["Feb 2023", "Two additional pharma clients onboarded (Zuellig, DKSH)"],
                ["Oct 2023", "IoT monitoring dashboard v2.0 launched; USD 120K revenue achieved"],
                ["Q3 2024", "Seed round close; fleet expansion to 15 vans; Malaysia market entry"],
            ],
            [3*cm, 14*cm]
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("ESG, Governance & Financial Projections", H2),
        Paragraph("Environmental Commitments", H3),
        Paragraph(
            "CoolChain is committed to reducing its carbon footprint. By optimising delivery routes using our "
            "proprietary routing algorithm, we significantly reduce unnecessary mileage and fuel consumption "
            "compared to unoptimised logistics operations. We are evaluating a transition to electric refrigerated "
            "vehicles in our fleet by 2026. Our goal is to reduce carbon emissions across our operations as "
            "we scale, though we are still in the process of establishing a formal emissions measurement baseline.",
            BODY
        ),
        Paragraph("Social Commitments", H3),
        Paragraph(
            "All CoolChain van drivers are direct employees (not gig workers) and receive above-minimum-wage "
            "compensation with healthcare benefits. CoolChain's operations ensure pharmaceutical access to "
            "underserved hospital groups in rural Indonesia. We currently employ 11 people across Singapore "
            "and Malaysia.",
            BODY
        ),
        Paragraph("Governance", H3),
        Paragraph(
            "CoolChain's board currently comprises both co-founders. An independent director with pharmaceutical "
            "logistics expertise will be appointed post-funding. Financial accounts are prepared quarterly by "
            "an accredited Singaporean CA firm (Crowe Singapore).",
            BODY
        ),
        hr(),
        Paragraph("Financial Projections", H3),
        Paragraph(
            "CoolChain projects strong revenue growth as the fleet expands into Malaysia and Indonesia following "
            "the seed round close. Year 3 revenue of USD 4.8 million is achievable given the large addressable "
            "market and limited direct competition in the IoT-enabled cold chain niche.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Year 1 (2024)", "Year 2 (2025)", "Year 3 (2026)"],
                ["Fleet Size (vans)", "15", "35", "80"],
                ["Active Clients", "8", "18", "40"],
                ["Monthly Deliveries", "3,200", "7,500", "18,000"],
                ["Revenue (USD)", "690,000", "1,800,000", "4,800,000"],
                ["Gross Margin", "48%", "54%", "61%"],
            ],
            [6*cm, 3.5*cm, 3.5*cm, 3.5*cm]
        ),
        Paragraph(
            "Use of USD 1.5M Seed Round: 55% fleet expansion (6 new refrigerated vans), "
            "25% IoT hardware and software development, 12% Malaysia market entry costs, 8% working capital.",
            SMALL
        ),
    ]
    d.build(s)
    print("  CoolChain_pitch_deck.pdf")


# ═══════════════════════════════════════════════════════════════════════
# 4. MINDBRIDGE — HealthTech · Pre-seed · North America  → Target: WATCH
#    RF-05 (diversity claimed, no named diverse leaders)
#    RF-06 (financial projections, no stated assumptions)
#    RF-10 ("social impact" claimed, no evidence)
# ═══════════════════════════════════════════════════════════════════════
def gen_mindbridge():
    d = new_doc(f"{OUT}/MindBridge_pitch_deck.pdf")
    s = cover(
        "MindBridge",
        "AI-Powered Corporate Mental Wellness Platform for Enterprise HR",
        "HealthTech", "Pre-seed", "North America", "USD 800,000"
    )

    s += [
        Paragraph("Executive Summary", H2),
        Paragraph(
            "MindBridge is a B2B SaaS platform that enables HR departments to proactively monitor workforce "
            "mental wellness, connect employees to licensed therapists, and track wellbeing trends across teams. "
            "Founded in 2023 by Dr. Maya Chen, a clinical psychologist with 15 years of practice, MindBridge "
            "has two Fortune 500 subsidiaries running 90-day enterprise pilots. The platform creates measurable "
            "social impact by making mental health support accessible to working professionals.",
            BODY
        ),
        Paragraph("Problem", H3),
        Paragraph(
            "Mental health conditions cost US employers USD 225 billion annually in lost productivity, absenteeism, "
            "and turnover (American Institute of Stress, 2023). 74% of employees report that their company's "
            "EAP (Employee Assistance Programme) is difficult to navigate and underused. Current solutions "
            "(Modern Health, Lyra Health) price out mid-size employers at USD 300–500 per employee per year. "
            "The US corporate wellness market is valued at USD 53 billion and growing at 8% annually.",
            BODY
        ),
        Paragraph("Solution", H3),
        Paragraph(
            "MindBridge integrates directly with Workday and SAP HR systems. An anonymised team wellness "
            "dashboard surfaces burnout risk scores at the team level without exposing individual data. "
            "Employees access on-demand licensed therapist sessions via in-app video. "
            "Pricing: USD 12 per employee per month (billed annually to HR departments).",
            BODY
        ),
        hr(),
        Paragraph("Founding Team", H2),
        tbl(
            [
                ["Name", "Role", "Background"],
                ["Dr. Maya Chen", "Founder & CEO",
                 "PhD Clinical Psychology, Columbia University; "
                 "15 years private practice; published researcher in workplace mental health; "
                 "Prior: Consulting psychologist to LinkedIn and Salesforce HR teams"],
            ],
            [3.5*cm, 3*cm, 11*cm]
        ),
        Paragraph(
            "Advisory Board: Dr. Robert Kim (Head of Psychiatry, Johns Hopkins, linkedin.com/in/robert-kim-jhmi), "
            "John Davis (VP People & Culture, ex-Deloitte, linkedin.com/in/john-davis-hr), "
            "Sarah Johnson (Principal, Andreessen Horowitz Health Fund, linkedin.com/in/sarah-johnson-a16z). "
            "MindBridge is proud to foster a diverse and inclusive workplace environment. "
            "We are actively recruiting to build a diverse leadership team as we scale beyond the founding stage. "
            "Full-time team currently: 3 people (Founder + 2 developers).",
            SMALL
        ),
        Paragraph("Market Sizing", H3),
        Paragraph(
            "Total Addressable Market: USD 53 billion — US corporate wellness market (Global Wellness Institute, 2023). "
            "Serviceable Addressable Market: USD 8 billion — enterprise mental health and EAP solutions "
            "for companies with 500+ employees. "
            "Serviceable Obtainable Market: USD 400 million — tech, finance, and consulting sector employers "
            "with existing Workday/SAP integration budgets.",
            BODY
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("Revenue Model & Traction", H2),
        Paragraph(
            "B2B SaaS subscription at USD 12 per employee per month, billed annually to HR departments. "
            "Therapist sessions are fulfilled by a network of 85 licensed therapists on a revenue-share basis. "
            "MindBridge retains 30% of each session fee.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Current Value"],
                ["Enterprise Pilot Clients", "2 (Fortune 500 subsidiaries, named under NDA)"],
                ["Employees on Platform (pilots)", "1,400"],
                ["Current ARR", "USD 0 (pilots are free; commercial agreements in negotiation)"],
                ["Pilot Engagement Rate", "38% of enrolled employees active weekly"],
                ["Therapist Sessions Completed", "312 sessions in 90 days"],
                ["Client NPS (pilot exit survey)", "68"],
            ],
            [9*cm, 8*cm]
        ),
        Paragraph("Competitive Differentiation", H3),
        tbl(
            [
                ["Competitor", "Key Weakness vs MindBridge"],
                ["Modern Health", "USD 300-500 per employee per year; pricing out mid-market employers"],
                ["Lyra Health", "Insurance-dependent model; slow credentialing; limited global therapist network"],
                ["Headspace for Work", "Meditation-only; no therapist access; no team-level HR analytics"],
            ],
            [5*cm, 12*cm]
        ),
        Paragraph("Milestones", H3),
        tbl(
            [
                ["Date", "Milestone"],
                ["Mar 2023", "Company incorporated; USD 150K self-funded by founder"],
                ["Sep 2023", "MVP launched; first pilot agreed with a financial services firm subsidiary"],
                ["Jan 2024", "Second pilot signed (technology company subsidiary); 1,400 employees on platform"],
                ["Q3 2024", "Pre-seed round close; convert pilots to paid; first USD 100K ARR target"],
            ],
            [3*cm, 14*cm]
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("ESG, Governance & Financial Projections", H2),
        Paragraph("Environmental Commitments", H3),
        Paragraph(
            "MindBridge is a fully remote company with no office footprint, minimising Scope 1 emissions. "
            "Platform infrastructure runs on AWS US-East-1. We are committed to measuring and disclosing "
            "our cloud infrastructure carbon footprint by end of 2024.",
            BODY
        ),
        Paragraph("Social Commitments", H3),
        Paragraph(
            "MindBridge is committed to creating social impact by making mental health support more accessible "
            "to working professionals who would otherwise face long waitlists or unaffordable out-of-pocket costs. "
            "We believe mental health is a human right and that workplaces have a responsibility to support it. "
            "MindBridge is building a diverse and inclusive culture and values representation at all levels. "
            "All therapists on the platform are licensed, insured, and receive above-market session rates. "
            "Employee data is protected under a published privacy policy (mindbridge.health/privacy), "
            "HIPAA-compliant for US operations.",
            BODY
        ),
        Paragraph("Governance", H3),
        Paragraph(
            "MindBridge is currently founder-led with an advisory board. Dr. Maya Chen holds majority control "
            "at this pre-seed stage. Post-funding governance will include a 3-person board with at least "
            "one independent member. Annual accounts prepared by a CPA firm (Moss Adams, Seattle).",
            BODY
        ),
        hr(),
        Paragraph("Financial Projections", H3),
        Paragraph(
            "MindBridge projects rapid revenue growth following pilot conversion and pre-seed fundraise close, "
            "driven by the large US enterprise wellness market opportunity and strong pilot results. "
            "Year 3 revenue of USD 12 million represents meaningful market penetration of the addressable segment.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Year 1 (2024)", "Year 2 (2025)", "Year 3 (2026)"],
                ["Enterprise Clients", "4", "18", "55"],
                ["Employees on Platform", "8,000", "36,000", "110,000"],
                ["ARR (USD)", "1,152,000", "5,184,000", "15,840,000"],
                ["Gross Margin", "62%", "67%", "71%"],
                ["Operating Burn (USD)", "600,000", "1,200,000", "—"],
            ],
            [6*cm, 3.5*cm, 3.5*cm, 3.5*cm]
        ),
        Paragraph(
            "Use of USD 800K Pre-seed: 50% product engineering (Workday/SAP integrations), "
            "30% pilot-to-paid sales conversion, 20% clinical operations (therapist onboarding).",
            SMALL
        ),
    ]
    d.build(s)
    print("  MindBridge_pitch_deck.pdf")


# ═══════════════════════════════════════════════════════════════════════
# 5. BRICKSCAN — Construction Tech · Seed · Europe  → Target: SOFT PASS
#    RF-03 (founder unilateral veto over all board decisions)
#    RF-06 (financial projections no stated assumptions)
#    RF-07 (no LinkedIn or verifiable history for team)
# ═══════════════════════════════════════════════════════════════════════
def gen_brickscan():
    d = new_doc(f"{OUT}/BrickScan_pitch_deck.pdf")
    s = cover(
        "BrickScan",
        "Computer Vision Defect Detection for Construction Site Quality Control",
        "Construction Tech", "Seed", "Europe", "EUR 1,200,000"
    )

    s += [
        Paragraph("Executive Summary", H2),
        Paragraph(
            "BrickScan provides an AI-powered quality control platform for construction contractors. "
            "Site supervisors photograph structural elements using a smartphone; BrickScan's computer vision "
            "model detects cracks, misalignments, and material defects in under 5 seconds. Reports are "
            "generated automatically for sign-off. Founded in Stockholm in 2022 by Thomas Meyer and "
            "Lars Eriksson, BrickScan has completed two paid pilots with Swedish construction contractors "
            "and generated EUR 45,000 in revenue.",
            BODY
        ),
        Paragraph("Problem", H3),
        Paragraph(
            "Construction defects cost the European construction industry an estimated EUR 80 billion annually "
            "in rework, legal disputes, and warranty claims (European Construction Industry Federation, 2022). "
            "Quality inspections today rely on manual visual checks by site supervisors, which are inconsistent "
            "and poorly documented. There is no scalable AI-native defect detection product built specifically "
            "for European construction standards (Eurocode compliance).",
            BODY
        ),
        Paragraph("Solution", H3),
        Paragraph(
            "A mobile-first SaaS application. Supervisors photograph structural elements and BrickScan's "
            "computer vision model — trained on 420,000 labelled construction defect images — classifies "
            "defect type, severity, and recommended remediation. Automated PDF inspection reports are "
            "generated for regulatory submission. Pricing: EUR 800 per site per month.",
            BODY
        ),
        hr(),
        Paragraph("Founding Team", H2),
        tbl(
            [
                ["Name", "Role", "Background"],
                ["Thomas Meyer", "CEO & Co-Founder",
                 "12 years as construction project manager on large residential and commercial builds in Sweden and Germany. "
                 "MSc Civil Engineering, KTH Royal Institute of Technology."],
                ["Lars Eriksson", "CTO & Co-Founder",
                 "BSc Computer Science, Uppsala University. "
                 "3 years software development experience. Self-taught in computer vision and deep learning."],
            ],
            [3.5*cm, 3*cm, 11*cm]
        ),
        Paragraph(
            "BrickScan has no advisory board at this stage. The company currently has 2 full-time employees "
            "(the co-founders) plus 1 part-time developer. "
            "Thomas Meyer, as CEO and majority shareholder holding 65% of equity, retains sole authority "
            "and veto power over all board decisions relating to capital allocation, personnel, product "
            "direction, and strategic partnerships. Investor minority rights are limited to anti-dilution "
            "protection and information rights only.",
            SMALL
        ),
        Paragraph("Market Sizing", H3),
        Paragraph(
            "The European construction quality control software market is large and growing as regulation "
            "increases. BrickScan's initial focus is the Nordics (Sweden, Norway, Denmark) before expanding "
            "to Germany and the Benelux. The global construction tech market is significant with multiple "
            "large players and many underserved niches.",
            BODY
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("Revenue Model & Traction", H2),
        Paragraph(
            "Per-site SaaS subscription: EUR 800 per active construction site per month. "
            "Sites commit to 6-month minimum contracts. Average construction project duration is 18 months.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Current Value"],
                ["Pilot Revenue (12 months)", "EUR 45,000"],
                ["Active Pilot Sites", "2"],
                ["Inspections Completed", "890"],
                ["Defect Detection Accuracy", "91% (vs. manual benchmark of 73%)"],
                ["Current ARR (contracted)", "EUR 19,200 (2 sites x EUR 800 x 12 months)"],
            ],
            [9*cm, 8*cm]
        ),
        Paragraph("Competitive Differentiation", H3),
        tbl(
            [
                ["Competitor", "Key Weakness vs BrickScan"],
                ["Procore", "Project management suite; no AI defect detection; expensive (USD 375+/user/month)"],
                ["OpenSpace", "Site documentation and progress photos only; no defect classification AI"],
                ["Doxel", "Hardware-dependent (robot cameras); not mobile-first; USD pricing for US market"],
            ],
            [5*cm, 12*cm]
        ),
        Paragraph("Milestones", H3),
        tbl(
            [
                ["Date", "Milestone"],
                ["Mar 2022", "Company registered in Stockholm; EUR 80K self-funded"],
                ["Nov 2022", "First labelled dataset of 150,000 construction defect images acquired"],
                ["Jun 2023", "MVP launched; first paid pilot with NCC Group Sweden"],
                ["Jan 2024", "Second pilot signed (Skanska subsidiary); EUR 45K revenue"],
                ["Q4 2024", "Seed round close; expand to 20 active sites in Nordics"],
            ],
            [3*cm, 14*cm]
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("ESG, Governance & Financial Projections", H2),
        Paragraph("Environmental Commitments", H3),
        Paragraph(
            "BrickScan's platform helps reduce construction waste by catching defects early, before expensive "
            "rework is required. Early defect detection can reduce material waste on construction sites. "
            "Our cloud infrastructure is hosted on AWS Stockholm, one of the greenest data centres in Europe. "
            "We are committed to environmentally responsible operations as we grow.",
            BODY
        ),
        Paragraph("Social Commitments", H3),
        Paragraph(
            "BrickScan improves worker safety by identifying structural defects before they become hazards. "
            "Our platform is currently in Swedish only but will be localised for German and Dutch markets. "
            "We employ workers on standard Swedish employment contracts with full benefits.",
            BODY
        ),
        Paragraph("Governance", H3),
        Paragraph(
            "BrickScan is a founder-controlled company. Thomas Meyer holds 65% equity and retains full "
            "decision-making authority over all material company decisions, including capital deployment, "
            "hiring of senior personnel, entry into material contracts, and strategic direction. "
            "Lars Eriksson holds 30% equity. The remaining 5% is reserved for a future ESOP pool. "
            "Financial accounts are prepared annually by a Swedish registered accountant.",
            BODY
        ),
        hr(),
        Paragraph("Financial Projections", H3),
        Paragraph(
            "BrickScan is targeting strong revenue growth driven by the large European construction market. "
            "Year 3 revenue of EUR 5 million reflects continued adoption across the Nordic and DACH markets.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Year 1 (2024)", "Year 2 (2025)", "Year 3 (2026)"],
                ["Active Sites", "20", "75", "200"],
                ["Revenue (EUR)", "192,000", "720,000", "1,920,000"],
                ["Gross Margin", "71%", "74%", "77%"],
                ["Operating Burn (EUR)", "480,000", "320,000", "—"],
            ],
            [6*cm, 3.5*cm, 3.5*cm, 3.5*cm]
        ),
        Paragraph(
            "Use of EUR 1.2M Seed Round: 60% engineering and AI model improvement, "
            "25% sales (first dedicated sales hire), 15% operations.",
            SMALL
        ),
    ]
    d.build(s)
    print("  BrickScan_pitch_deck.pdf")


# ═══════════════════════════════════════════════════════════════════════
# 6. VERDAGROW — AgriTech · Pre-seed · MENA  → Target: PASS
#    RF-04 (env claims no methodology)
#    RF-06 (projections no assumptions)
#    RF-07 (no LinkedIn or verifiable history)
#    RF-08 (revenue figures inconsistent: cover says USD 500K ARR, financials say USD 300K)
#    RF-09 (solo founder, no board, no advisors)
# ═══════════════════════════════════════════════════════════════════════
def gen_verdagrow():
    d = new_doc(f"{OUT}/VerdaGrow_pitch_deck.pdf")
    s = cover(
        "VerdaGrow",
        "Vertical Farming Technology for Urban Food Security in MENA — Projected ARR: USD 500,000 by December 2025",
        "AgriTech", "Pre-seed", "MENA", "USD 600,000"
    )

    s += [
        Paragraph("Executive Summary", H2),
        Paragraph(
            "VerdaGrow designs and operates modular vertical farming units for deployment in urban centres "
            "across the MENA region. Each VerdaGrow unit produces leafy vegetables and herbs year-round "
            "using 95% less water than traditional field agriculture. We sell produce directly to "
            "supermarket chains and hotel groups under long-term supply agreements. "
            "Founded in 2023 by Antoine Berbiche, VerdaGrow is pre-revenue and seeking its first "
            "external funding round to build and deploy its first commercial unit in Tunis.",
            BODY
        ),
        Paragraph("Problem", H3),
        Paragraph(
            "MENA imports over 60% of its food supply, making the region highly vulnerable to global "
            "commodity price shocks and supply chain disruptions. Arable land in MENA is diminishing "
            "due to desertification and urban sprawl. Water scarcity makes traditional agriculture "
            "increasingly unviable: MENA has less than 1% of the world's freshwater resources. "
            "Urban populations are growing rapidly, creating urgent demand for locally produced food.",
            BODY
        ),
        Paragraph("Solution", H3),
        Paragraph(
            "VerdaGrow's modular farming units (8m x 12m shipping container footprint) are deployable "
            "in any urban location with electricity and water access. Each unit produces 22 tonnes of "
            "leafy greens per year. Our proprietary nutrient delivery system uses 95% less water than "
            "soil farming and eliminates pesticide use entirely. "
            "Pricing: long-term supply contracts with supermarket chains at EUR 4.20 per kg, "
            "representing a 35% premium to imported produce based on freshness and local branding.",
            BODY
        ),
        hr(),
        Paragraph("Founding Team", H2),
        tbl(
            [
                ["Name", "Role", "Background"],
                ["Antoine Berbiche", "Founder & CEO",
                 "Agricultural engineer with 6 years experience in greenhouse operations in the Netherlands. "
                 "Returned to Tunisia in 2022 with the vision to apply vertical farming to the MENA context. "
                 "No prior startup experience. Sole full-time employee of VerdaGrow."],
            ],
            [3.5*cm, 3*cm, 11*cm]
        ),
        Paragraph(
            "VerdaGrow currently has no board of directors, no advisory board, and no co-founders. "
            "Antoine Berbiche is the sole founder and sole decision-maker for all company matters. "
            "The company plans to recruit a CFO and a Head of Operations post-funding.",
            SMALL
        ),
        Paragraph("Market Sizing", H3),
        Paragraph(
            "The global vertical farming market is large and growing very rapidly. MENA has a significant "
            "food import dependency problem that vertical farming is uniquely positioned to solve. "
            "Our target customers are major supermarket chains and hotel groups in Tunis, Casablanca, "
            "and Cairo. We believe VerdaGrow can capture a meaningful share of the premium fresh produce "
            "market in these cities within three years.",
            BODY
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("Revenue Model & Traction", H2),
        Paragraph(
            "B2B supply agreements with supermarket chains and hotel groups. "
            "Pricing: EUR 4.20 per kg of produce delivered. "
            "Each deployed unit generates approximately EUR 92,400 in annual revenue. "
            "VerdaGrow targets deploying 6 units in Year 1, scaling to 30 units by Year 3.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Current Value"],
                ["Revenue to Date", "USD 0 (pre-revenue)"],
                ["Letter of Intent Received", "1 (Monoprix Tunisia — informal expression of interest)"],
                ["Units Deployed", "0 (first unit under construction)"],
                ["First Unit Completion Target", "Q4 2024"],
            ],
            [9*cm, 8*cm]
        ),
        Paragraph("Competitive Differentiation", H3),
        tbl(
            [
                ["Competitor", "Key Weakness vs VerdaGrow"],
                ["Imported produce (main competition)", "Long supply chains; high price volatility; poor freshness on arrival"],
                ["Bowery Farming (US)", "US-only operations; not designed for MENA climate or regulatory environment"],
                ["Local greenhouse operators", "High water usage; pesticide dependency; limited to rural land"],
            ],
            [5*cm, 12*cm]
        ),
        Paragraph("Milestones", H3),
        tbl(
            [
                ["Date", "Milestone"],
                ["Jan 2023", "Company registered in Tunisia; EUR 30K personal savings invested"],
                ["Jul 2023", "Site secured in Tunis industrial zone; first unit frame ordered"],
                ["Dec 2023", "Informal letter of interest from Monoprix Tunisia received"],
                ["Q4 2024", "First commercial unit operational; first supply agreement signed"],
                ["2025", "Scale to 6 units; first year of commercial revenue"],
            ],
            [3*cm, 14*cm]
        ),
        PageBreak(),
    ]

    s += [
        Paragraph("ESG, Governance & Financial Projections", H2),
        Paragraph("Environmental Commitments", H3),
        Paragraph(
            "VerdaGrow's vertical farming technology will reduce carbon emissions by 70% compared to "
            "conventional imported produce supply chains, accounting for transportation, packaging, "
            "and cold storage elimination. Our units eliminate pesticide use entirely and will achieve "
            "net-zero water consumption through closed-loop recycling. VerdaGrow is positioning itself "
            "as one of the most environmentally positive food production companies in the MENA region "
            "and will be a significant contributor to regional sustainability goals.",
            BODY
        ),
        Paragraph("Social Commitments", H3),
        Paragraph(
            "VerdaGrow contributes to food security for urban MENA populations. By producing fresh "
            "vegetables locally, we reduce MENA's food import dependency and create local agricultural "
            "employment. Our units will create 3–5 operational jobs per deployed farm. We are committed "
            "to responsible employment practices.",
            BODY
        ),
        Paragraph("Governance", H3),
        Paragraph(
            "VerdaGrow is a sole-founder company at this stage. Antoine Berbiche is the sole director "
            "and decision-maker. Financial records are maintained by the founder using standard accounting "
            "software. An external accountant will be engaged post-funding.",
            BODY
        ),
        hr(),
        Paragraph("Financial Projections", H3),
        Paragraph(
            "VerdaGrow projects significant revenue growth following the deployment of our first commercial "
            "units. Given the strong demand for locally grown fresh produce in MENA supermarkets and hotel "
            "groups, we are confident in achieving our Year 1 revenue target of USD 300,000 in our first "
            "full year of operations, scaling to USD 1.8 million by Year 3 as the unit fleet grows.",
            BODY
        ),
        tbl(
            [
                ["Metric", "Year 1 (2025)", "Year 2 (2026)", "Year 3 (2027)"],
                ["Units Deployed", "6", "15", "30"],
                ["Revenue (USD)", "300,000", "700,000", "1,800,000"],
                ["Gross Margin", "38%", "44%", "52%"],
                ["Operating Burn (USD)", "480,000", "320,000", "—"],
            ],
            [6*cm, 3.5*cm, 3.5*cm, 3.5*cm]
        ),
        Paragraph(
            "Use of USD 600K Pre-seed: 60% first commercial unit construction and fitout, "
            "25% nutrient delivery system procurement, 15% working capital and operations.",
            SMALL
        ),
    ]
    d.build(s)
    print("  VerdaGrow_pitch_deck.pdf")


if __name__ == "__main__":
    print("Generating 6 pitch deck PDFs...")
    gen_auralearn()
    gen_nexalend()
    gen_coolchain()
    gen_mindbridge()
    gen_brickscan()
    gen_verdagrow()
    print(f"\nDone. All PDFs saved to: {os.path.abspath(OUT)}/")
