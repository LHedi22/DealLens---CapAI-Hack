"""Generate 10 realistic startup pitch documents for NeuralCare AI."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUT = os.path.join(os.path.dirname(__file__), "test_docs", "NeuralCare")
os.makedirs(OUT, exist_ok=True)

W, H = A4
MARGIN = 2 * cm

BRAND = colors.HexColor("#1a56db")
DARK  = colors.HexColor("#111827")
GRAY  = colors.HexColor("#6b7280")
LIGHT = colors.HexColor("#f3f4f6")
GREEN = colors.HexColor("#059669")
RED   = colors.HexColor("#dc2626")

styles = getSampleStyleSheet()

def S(base_name, **kw):
    base = styles[base_name] if base_name in styles else styles["Normal"]
    return ParagraphStyle(f"custom_{base_name}_{id(kw)}", parent=base, **kw)

H1  = S("Heading1", fontSize=22, textColor=BRAND, spaceAfter=10, fontName="Helvetica-Bold")
H2  = S("Heading2", fontSize=15, textColor=DARK,  spaceAfter=8,  fontName="Helvetica-Bold", spaceBefore=14)
H3  = S("Heading3", fontSize=12, textColor=BRAND, spaceAfter=6,  fontName="Helvetica-Bold", spaceBefore=10)
BODY = S("Normal",  fontSize=10, textColor=DARK,  spaceAfter=6,  leading=15, alignment=TA_JUSTIFY)
SMALL= S("Normal",  fontSize=9,  textColor=GRAY,  spaceAfter=4,  leading=13)
CTR  = S("Normal",  fontSize=11, textColor=DARK,  alignment=TA_CENTER, spaceAfter=4)
SUB  = S("Normal",  fontSize=13, textColor=GRAY,  alignment=TA_CENTER, spaceAfter=6)
BOLD = S("Normal",  fontSize=10, textColor=DARK,  fontName="Helvetica-Bold", spaceAfter=4)

def doc(filename):
    path = os.path.join(OUT, filename)
    return SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=MARGIN, rightMargin=MARGIN,
                             topMargin=MARGIN, bottomMargin=MARGIN)

def cover(title, subtitle=""):
    return [
        Spacer(1, 3*cm),
        Paragraph("NeuralCare AI", H1),
        Paragraph(title, S("Heading2", fontSize=18, textColor=DARK, fontName="Helvetica-Bold")),
        Paragraph(subtitle, SUB) if subtitle else Spacer(1, 0.2*cm),
        HRFlowable(width="100%", thickness=2, color=BRAND, spaceAfter=20),
        Paragraph("Confidential — For Investor Use Only", SMALL),
        Paragraph("June 2026 | Singapore", SMALL),
        PageBreak(),
    ]

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=8, spaceBefore=8)

def table(data, col_widths=None, header_bg=BRAND):
    t = Table(data, colWidths=col_widths)
    style = [
        ("BACKGROUND", (0,0), (-1,0), header_bg),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#d1d5db")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]
    t.setStyle(TableStyle(style))
    return t

# ─── DOC 1: Executive Summary ───────────────────────────────────────────────
def doc1():
    d = doc("01_executive_summary.pdf")
    story = cover("Executive Summary", "Seed Round — $2.5M")
    story += [
        Paragraph("Company Overview", H2),
        Paragraph(
            "NeuralCare AI is a Singapore-headquartered HealthTech startup delivering an AI-powered "
            "mental health platform designed for Southeast Asia. We combine clinically validated "
            "Cognitive Behavioural Therapy (CBT) modules with intelligent therapist-matching to make "
            "quality mental healthcare accessible, affordable, and culturally relevant across SEA's "
            "700 million population.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("The Problem", H2),
        Paragraph(
            "Southeast Asia faces a severe mental health crisis. Over 60 million people suffer from "
            "depression or anxiety disorders, yet 9 in 10 receive no treatment. The psychiatrist-to-"
            "patient ratio is 1:200,000 — compared to 1:8,000 in high-income countries. Cultural "
            "stigma, language barriers, and cost prevent the majority from seeking help. The average "
            "therapy session costs SGD 180–250, putting it out of reach for most of the region.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Our Solution", H2),
        Paragraph(
            "NeuralCare AI delivers a three-layer solution: (1) an AI-guided self-help app with "
            "CBT exercises, mood tracking, and crisis detection in 8 languages; (2) an on-demand "
            "therapist marketplace connecting users with licensed professionals at 60% below market "
            "rates; (3) a B2B enterprise wellness dashboard for HR teams to monitor workforce mental "
            "health at scale.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Key Metrics at a Glance", H2),
        table([
            ["Metric", "Value"],
            ["Annual Recurring Revenue (ARR)", "SGD 380,000 (~USD 280,000)"],
            ["Monthly Active Users (MAU)", "14,200"],
            ["Paying Subscribers", "3,100"],
            ["Therapist Network", "180 licensed professionals (SG, MY, TH, ID)"],
            ["Enterprise Clients", "12 (incl. 2 Fortune 500 regional offices)"],
            ["Monthly Revenue Growth (6-mo avg)", "18%"],
            ["Net Promoter Score (NPS)", "71"],
            ["Session Completion Rate", "84%"],
        ], col_widths=[9*cm, 8*cm]),
        Spacer(1, 0.5*cm),
        Paragraph("Funding Ask", H2),
        Paragraph(
            "We are raising SGD 3.4M (USD 2.5M) in Seed funding. Proceeds will be deployed across "
            "product development (35%), market expansion into Indonesia and Thailand (40%), clinical "
            "partnerships (15%), and operations (10%). This runway extends 24 months and targets "
            "SGD 2.1M ARR and 50,000 MAU by Q4 2027.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Why Now", H2),
        Paragraph(
            "Post-pandemic mental health awareness has reached an inflection point in SEA. Google "
            "searches for 'online therapy' grew 340% in the region between 2021 and 2025. Singapore's "
            "National Mental Health Blueprint (2023–2028) mandates employer mental health programmes, "
            "creating immediate B2B demand. Meanwhile, GPT-4-class language models now enable "
            "culturally nuanced, multilingual CBT delivery at near-zero marginal cost.", BODY),
    ]
    d.build(story)
    print("[OK] 01_executive_summary.pdf")

# ─── DOC 2: Business Plan ────────────────────────────────────────────────────
def doc2():
    d = doc("02_business_plan.pdf")
    story = cover("Business Plan", "FY2026–FY2028")
    story += [
        Paragraph("Mission & Vision", H2),
        Paragraph(
            "<b>Mission:</b> To make evidence-based mental healthcare accessible to every person in "
            "Southeast Asia, regardless of income, language, or location.", BODY),
        Paragraph(
            "<b>Vision:</b> To become the default mental health infrastructure layer for SEA — "
            "powering consumer apps, employer programmes, and healthcare systems alike.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Business Model", H2),
        Paragraph("NeuralCare operates three revenue streams:", BODY),
        table([
            ["Stream", "Model", "Price Point", "FY2026 Revenue Share"],
            ["B2C Subscription", "Monthly/Annual SaaS", "SGD 19.90/mo or SGD 179/yr", "42%"],
            ["B2B Enterprise", "Per-seat annual licence", "SGD 72/employee/yr", "38%"],
            ["Therapist Marketplace", "15% commission per session", "SGD 90–120/session", "20%"],
        ], col_widths=[4.5*cm, 4*cm, 4.5*cm, 3.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Go-to-Market Strategy", H2),
        Paragraph(
            "<b>Phase 1 (2025–2026) — Singapore Beachhead:</b> Establish product-market fit in "
            "Singapore. Partner with 3 corporate HR platforms (Workday, Infor, SAP SuccessFactors "
            "resellers). Run clinical validation study with NUS Yong Soo Lin School of Medicine.", BODY),
        Paragraph(
            "<b>Phase 2 (2026–2027) — Regional Expansion:</b> Launch localised apps in Bahasa "
            "Indonesia and Thai. Partner with Malaysian Employers Federation and Indonesian Ministry "
            "of Health digital wellness initiative. Target 10 large Indonesian enterprise clients "
            "through Gojek and Tokopedia HR channel partnerships.", BODY),
        Paragraph(
            "<b>Phase 3 (2027–2028) — Platform & API:</b> Open NeuralCare API to third-party health "
            "apps. Launch white-label product for insurance companies. File for regulatory approvals "
            "as a Class I medical device under Singapore HSA and Indonesia BPOM.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Operational Model", H2),
        Paragraph(
            "NeuralCare operates an asset-light model. All therapists are independent contractors "
            "onboarded through a rigorous 3-stage credentialling process (licence verification, "
            "skills assessment, supervised sessions). Clinical oversight is maintained by our Medical "
            "Advisory Board, chaired by Dr. Tan Wei Ling (former MOH Singapore Chief Psychiatrist). "
            "Infrastructure runs on AWS Singapore with data residency compliance for each market.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Key Milestones — 24-Month Roadmap", H2),
        table([
            ["Quarter", "Milestone"],
            ["Q3 2026", "Close SGD 3.4M Seed round; hire Head of Indonesia & Head of Clinical"],
            ["Q4 2026", "Launch Indonesian Bahasa app; sign 5 new enterprise clients"],
            ["Q1 2027", "Reach 25,000 MAU; publish NUS clinical validation results"],
            ["Q2 2027", "Launch Thailand; onboard 300 therapists across 5 countries"],
            ["Q3 2027", "Hit SGD 1.6M ARR; begin Series A preparation"],
            ["Q4 2027", "SGD 2.1M ARR; 50,000 MAU; file HSA Class I device application"],
        ], col_widths=[4*cm, 12.5*cm]),
        Spacer(1, 0.3*cm),
        Paragraph("Risk Factors & Mitigations", H2),
        table([
            ["Risk", "Likelihood", "Mitigation"],
            ["Regulatory change on digital health", "Medium", "Engaged MCI advisory panel; modular compliance architecture"],
            ["Therapist supply constraint", "Medium", "University partnerships (NUS, NTU, UM) for fresh graduates"],
            ["Competition from well-funded global apps", "High", "SEA language + cultural advantage; local clinical credibility"],
            ["AI model hallucination in crisis scenarios", "Low", "Hard-coded crisis escalation; no AI substitutes licensed therapy"],
            ["Data breach / privacy incident", "Low", "ISO 27001 in progress; data never leaves country of origin"],
        ], col_widths=[5.5*cm, 2.5*cm, 8.5*cm]),
    ]
    d.build(story)
    print("[OK] 02_business_plan.pdf")

# ─── DOC 3: Financial Projections ────────────────────────────────────────────
def doc3():
    d = doc("03_financial_projections.pdf")
    story = cover("Financial Projections", "FY2026 – FY2028 (3-Year Model)")
    story += [
        Paragraph("Assumptions", H2),
        Paragraph("All figures in SGD unless noted. Exchange rate: 1 USD = 1.36 SGD.", BODY),
        table([
            ["Assumption", "FY2026", "FY2027", "FY2028"],
            ["B2C MAU growth (MoM avg)", "18%", "14%", "10%"],
            ["B2C conversion rate (MAU→paid)", "21%", "23%", "25%"],
            ["B2B enterprise clients", "22", "55", "110"],
            ["Avg seats per enterprise client", "320", "380", "420"],
            ["Therapist session volume (monthly)", "2,800", "8,200", "18,500"],
            ["Blended gross margin", "68%", "72%", "75%"],
            ["Monthly burn rate (SGD)", "138,000", "210,000", "265,000"],
        ], col_widths=[7*cm, 3.5*cm, 3.5*cm, 2.5*cm]),
        Spacer(1, 0.5*cm),
        Paragraph("Revenue Projections (SGD)", H2),
        table([
            ["Revenue Line", "FY2026", "FY2027", "FY2028"],
            ["B2C Subscription",      "520,000",   "1,340,000", "2,980,000"],
            ["B2B Enterprise",        "470,000",   "1,590,000", "3,326,400"],
            ["Therapist Marketplace", "248,000",   "738,000",   "1,665,000"],
            ["TOTAL REVENUE",         "1,238,000", "3,668,000", "7,971,400"],
            ["YoY Growth",            "—",         "+196%",     "+117%"],
        ], col_widths=[7*cm, 3.5*cm, 3.5*cm, 2.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Cost Structure (SGD)", H2),
        table([
            ["Cost Line", "FY2026", "FY2027", "FY2028"],
            ["COGS (hosting, therapist payouts)", "396,160",   "1,027,040", "1,992,850"],
            ["Gross Profit",                      "841,840",   "2,640,960", "5,978,550"],
            ["Sales & Marketing",                 "420,000",   "880,000",   "1,594,280"],
            ["R&D / Engineering",                 "480,000",   "720,000",   "960,000"],
            ["G&A",                               "144,000",   "252,000",   "318,000"],
            ["Total OpEx",                        "1,044,000", "1,852,000", "2,872,280"],
            ["EBITDA",                            "(202,160)", "788,960",   "3,106,270"],
            ["EBITDA Margin",                     "-16%",      "+22%",      "+39%"],
        ], col_widths=[7*cm, 3.5*cm, 3.5*cm, 2.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Cash Flow & Runway", H2),
        Paragraph(
            "With SGD 3.4M Seed funding and current burn of SGD 138K/month, NeuralCare has "
            "24.6 months of runway. The model reaches EBITDA breakeven in Q2 FY2027 without "
            "requiring additional capital. A Series A of SGD 8–12M is projected for Q3 FY2027 "
            "to accelerate Indonesia and Thailand expansion.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Unit Economics", H2),
        table([
            ["Metric", "B2C", "B2B (per seat)"],
            ["Customer Acquisition Cost (CAC)", "SGD 28", "SGD 180 (per account: SGD 57,600)"],
            ["Average Revenue Per User (ARPU)", "SGD 179/yr (annual)", "SGD 72/yr"],
            ["Gross Margin per User", "82%", "79%"],
            ["LTV (3-year retention basis)", "SGD 420", "SGD 185/seat"],
            ["LTV : CAC Ratio", "15.0x", "18.2x (account-level)"],
            ["Payback Period", "1.9 months", "3.2 months"],
        ], col_widths=[7*cm, 4*cm, 5.5*cm]),
        Spacer(1, 0.3*cm),
        Paragraph(
            "Disclaimer: Projections are based on management estimates and historical growth rates. "
            "They are not guarantees of future performance. Actual results may differ materially "
            "from projections due to market, regulatory, and operational factors.", SMALL),
    ]
    d.build(story)
    print("[OK] 03_financial_projections.pdf")

# ─── DOC 4: Market Research ──────────────────────────────────────────────────
def doc4():
    d = doc("04_market_research.pdf")
    story = cover("Market Research & TAM Analysis", "Southeast Asia Mental Health Technology")
    story += [
        Paragraph("Market Context", H2),
        Paragraph(
            "Mental health disorders are the leading cause of disability-adjusted life years (DALYs) "
            "in Southeast Asia, accounting for 13% of total disease burden (WHO, 2024). Despite this, "
            "the region allocates less than 1% of national health budgets to mental health. This "
            "structural gap represents an extraordinary commercial opportunity for technology-enabled "
            "care delivery.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Total Addressable Market (TAM)", H2),
        table([
            ["Geography", "Population (M)", "Diagnosed MH cases (M)", "Digital health penetration", "TAM (USD B)"],
            ["Singapore",   "6",   "0.54", "78%", "0.31"],
            ["Malaysia",    "34",  "3.06", "52%", "0.88"],
            ["Thailand",    "72",  "6.48", "45%", "1.62"],
            ["Indonesia",   "278", "25.0", "38%", "5.25"],
            ["Vietnam",     "99",  "8.9",  "31%", "1.54"],
            ["Philippines", "115", "10.4", "28%", "1.62"],
            ["TOTAL SEA",   "604", "54.4", "—",   "11.22"],
        ], col_widths=[3.5*cm, 3*cm, 3.5*cm, 3*cm, 2.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Serviceable Addressable Market (SAM)", H2),
        Paragraph(
            "NeuralCare's SAM comprises English, Malay, Indonesian, and Thai-speaking smartphone "
            "users aged 18–45 with diagnosed or self-identified mild-to-moderate mental health "
            "concerns, plus mid-to-large enterprises (500+ employees) seeking workforce wellness "
            "solutions. This segment is estimated at USD 2.8B across SG, MY, TH, and ID.", BODY),
        Paragraph("Serviceable Obtainable Market (SOM)", H2),
        Paragraph(
            "Within a 5-year horizon, NeuralCare targets 2.3% SAM capture, equivalent to "
            "USD 64M in annual revenue. This is consistent with comparable digital health platforms "
            "in analogous markets (Headspace captured 2.1% of US addressable market by Year 5; "
            "Wysa captured 1.8% of UK SAM by Year 4).", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Market Drivers", H2),
        table([
            ["Driver", "Evidence"],
            ["Post-pandemic demand surge", "Google searches for 'online therapy' +340% SEA (2021–2025)"],
            ["Employer mandate (Singapore)", "National Mental Health Blueprint mandates EAPs by 2026"],
            ["Smartphone penetration", "82% SEA smartphone adoption rate (GSMA, 2025)"],
            ["Teletherapy regulation clarity", "MOH SG and KKM MY issued digital therapy guidelines (2024)"],
            ["Gen Z mental health openness", "73% of SEA Gen Z willing to use app-based therapy (YouGov, 2025)"],
            ["AI cost reduction", "LLM APIs reduce content personalisation cost by ~94% vs. human authoring"],
        ], col_widths=[5*cm, 11.5*cm]),
        Spacer(1, 0.3*cm),
        Paragraph("Regulatory Landscape", H2),
        Paragraph(
            "Singapore's HSA classifies AI-driven mental health apps as Class I medical devices "
            "requiring notification (not approval), enabling rapid market entry. Malaysia's MDA "
            "follows a similar framework. Indonesia's BPOM requires registration for apps with "
            "clinical claims — NeuralCare's Indonesia launch avoids clinical claims in v1.0, "
            "filing for Class I status in Q2 2027.", BODY),
    ]
    d.build(story)
    print("[OK] 04_market_research.pdf")

# ─── DOC 5: Team Profiles ────────────────────────────────────────────────────
def doc5():
    d = doc("05_team_profiles.pdf")
    story = cover("Team & Founders", "Leadership Profiles")
    story += [
        Paragraph("Co-Founders", H2),
        hr(),
        Paragraph("Dr. Aisha Rahman — Co-Founder & CEO", H3),
        table([
            ["Education", "MBBS (NUS Medicine, 2014) | MRCPsych (Royal College of Psychiatrists, 2018) | MSc Machine Learning (Imperial College London, 2020)"],
            ["LinkedIn", "linkedin.com/in/aisha-rahman-md"],
            ["Prior Role", "Consultant Psychiatrist, Singapore General Hospital (2018–2023)"],
            ["Prior Exits", "None — first-time founder"],
        ], col_widths=[3.5*cm, 13*cm]),
        Paragraph(
            "Dr. Rahman brings 9 years of clinical psychiatry experience combined with a machine "
            "learning postgraduate degree. She led the IMH-SGH telepsychiatry pilot (2021–2022) "
            "reaching 4,200 patients, which directly inspired NeuralCare. She holds 2 patents on "
            "AI-assisted mood disorder detection (filed NUS TTO). Named in Forbes 30 Under 30 Asia "
            "Healthcare (2024). Fluent in English, Malay, and Tamil.", BODY),
        Spacer(1, 0.3*cm),
        hr(),
        Paragraph("Marcus Tan Jia Wei — Co-Founder & CTO", H3),
        table([
            ["Education", "BEng Computer Engineering (NTU, 2013) | Stanford ML Certificate (2019)"],
            ["LinkedIn", "linkedin.com/in/marcus-tan-jw"],
            ["Prior Role", "Staff Engineer — Recommendations, Grab (2015–2023)"],
            ["Prior Exits", "Acquired startup (Shuttl — logistics ML): acq. by Grab 2017"],
        ], col_widths=[3.5*cm, 13*cm]),
        Paragraph(
            "Marcus built Grab's driver-matching ML pipeline serving 8M daily requests. He "
            "architected NeuralCare's real-time mood inference engine (sub-100ms inference latency) "
            "and crisis detection classifier (96.2% recall on held-out clinical dataset). He manages "
            "a team of 4 engineers and leads all infrastructure decisions. Active OSS contributor "
            "(3,200 GitHub stars on mental-health NLP toolkit).", BODY),
        Spacer(1, 0.3*cm),
        hr(),
        Paragraph("Priya Nair — Co-Founder & COO", H3),
        table([
            ["Education", "BA Economics (University of Delhi, 2012) | MBA (INSEAD, 2016)"],
            ["LinkedIn", "linkedin.com/in/priya-nair-sg"],
            ["Prior Role", "Engagement Manager — Healthcare Practice, McKinsey & Company (2016–2023)"],
            ["Prior Exits", "None — first-time founder"],
        ], col_widths=[3.5*cm, 13*cm]),
        Paragraph(
            "Priya led McKinsey engagements for MOH Singapore, IHH Healthcare, and Prudential's "
            "regional health insurance division. She designed the employee assistance programme for "
            "a 12,000-person SEA enterprise that reduced sick days by 23%. At NeuralCare, she owns "
            "B2B sales, clinical partnerships, and regulatory strategy. She closed all 12 current "
            "enterprise accounts personally.", BODY),
        Spacer(1, 0.4*cm),
        Paragraph("Key Hires & Advisors", H2),
        table([
            ["Name", "Role", "Background"],
            ["Dr. Tan Wei Ling", "Medical Advisor (Board)", "Former Chief Psychiatrist, MOH Singapore"],
            ["Prof. James Lim", "Clinical Advisor", "Head of Psychiatry, NUS Medicine"],
            ["Sarah Okonkwo", "Head of Product", "Ex-Calm (Senior PM, 4 yrs); NUS Psychology"],
            ["Ahmad Fauzi", "Country Lead — Indonesia", "Ex-Halodoc Head of Partnerships"],
            ["Li Mei Zhang", "Data Scientist", "PhD NLP, NTU; ex-A*STAR"],
        ], col_widths=[4*cm, 4*cm, 8.5*cm]),
        Spacer(1, 0.3*cm),
        Paragraph("Board Composition", H2),
        Paragraph(
            "The NeuralCare board currently comprises the 3 co-founders plus Dr. Tan Wei Ling "
            "(independent medical director). Two board seats are reserved for lead Seed investors. "
            "The company has adopted a Founders' Agreement with equal equity split between co-"
            "founders subject to a 4-year vesting schedule with a 1-year cliff. No unilateral "
            "veto rights exist — all material decisions require board majority.", BODY),
    ]
    d.build(story)
    print("[OK] 05_team_profiles.pdf")

# ─── DOC 6: Product Overview ─────────────────────────────────────────────────
def doc6():
    d = doc("06_product_overview.pdf")
    story = cover("Product & Technology Overview", "Platform Architecture & Roadmap")
    story += [
        Paragraph("Product Suite", H2),
        Paragraph(
            "NeuralCare delivers three interconnected products on a shared AI backbone:", BODY),
        Paragraph("<b>1. NeuralCare App (B2C)</b>", BOLD),
        Paragraph(
            "A mobile-first (iOS & Android) self-guided mental wellness app featuring: daily CBT "
            "micro-sessions (5–12 minutes), adaptive mood journalling with NLP sentiment analysis, "
            "breathing and mindfulness exercises, and a crisis escalation pathway that routes severe "
            "users to a licensed therapist within 4 hours. Available in English, Malay, Bahasa "
            "Indonesia, Thai, Mandarin, Tamil, Tagalog, and Vietnamese.", BODY),
        Paragraph("<b>2. TherapyMatch (B2C add-on)</b>", BOLD),
        Paragraph(
            "An on-demand therapist marketplace integrated into the app. NeuralCare's matching "
            "algorithm pairs users with therapists based on presenting concern, language preference, "
            "cultural background, therapist availability, and session history. Video, voice, and "
            "text-chat sessions are supported. Average wait time to first session: 2.3 hours.", BODY),
        Paragraph("<b>3. NeuralCare for Teams (B2B)</b>", BOLD),
        Paragraph(
            "An HR dashboard providing anonymised, aggregate workforce mental health analytics. "
            "Employers see department-level mood trends, absenteeism risk scores, and EAP utilisation "
            "rates — without any individual employee data. Includes an admin portal to manage "
            "licences, push wellness challenges, and access monthly clinical reports.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Technology Architecture", H2),
        table([
            ["Layer", "Technology"],
            ["Mobile App",         "React Native (iOS/Android); offline-capable CBT modules"],
            ["Backend API",        "FastAPI (Python 3.11); async; deployed on AWS ECS Fargate"],
            ["AI / NLP Engine",    "Fine-tuned Llama-3.1-8B on 220K anonymised therapy transcripts"],
            ["Crisis Classifier",  "Custom BERT model; 96.2% recall, 91.4% precision (clinical holdout)"],
            ["Database",           "PostgreSQL (RDS); Redis (ElastiCache) for session state"],
            ["Data Residency",     "Per-country S3 buckets; no cross-border data transfer"],
            ["Security",           "AES-256 at rest; TLS 1.3 in transit; ISO 27001 audit in progress"],
            ["Therapist Video",    "Daily.co WebRTC; end-to-end encrypted"],
        ], col_widths=[5*cm, 11.5*cm]),
        Spacer(1, 0.3*cm),
        Paragraph("Proprietary AI Assets", H2),
        Paragraph(
            "NeuralCare's core IP is its fine-tuned clinical language model, trained on a dataset "
            "of 220,000 anonymised therapy session transcripts obtained under IRB approval from "
            "SGH and IMH. The model is evaluated quarterly by our clinical advisory board against "
            "validated psychometric instruments (PHQ-9, GAD-7, PCL-5). It is NOT used for diagnosis "
            "— only for psychoeducation content personalisation and engagement nudges.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Product Roadmap — Next 18 Months", H2),
        table([
            ["Timeline", "Feature"],
            ["Q3 2026", "NeuralCare API v1 (third-party integrations); iOS widget for mood check-in"],
            ["Q4 2026", "Indonesian Bahasa full localisation; offline mode for low-bandwidth regions"],
            ["Q1 2027", "Wearable integration (Fitbit, Apple Watch) for physiological mood signals"],
            ["Q2 2027", "AI session summarisation for therapists (auto-SOAP notes); Thailand launch"],
            ["Q3 2027", "White-label product for insurance partners; Group therapy feature"],
            ["Q4 2027", "HSA Class I device application submission; research publication pipeline"],
        ], col_widths=[3.5*cm, 13*cm]),
    ]
    d.build(story)
    print("[OK] 06_product_overview.pdf")

# ─── DOC 7: ESG Policy ───────────────────────────────────────────────────────
def doc7():
    d = doc("07_esg_policy.pdf")
    story = cover("ESG Policy Document", "Environmental, Social & Governance Framework")
    story += [
        Paragraph(
            "NeuralCare AI is committed to responsible business practices across Environmental, "
            "Social, and Governance dimensions. This document outlines our current policies, "
            "targets, and accountability mechanisms as of June 2026.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("E — Environmental", H2),
        Paragraph(
            "NeuralCare is a software-first business with a minimal direct environmental footprint. "
            "Our primary environmental impact comes from cloud computing energy consumption.", BODY),
        table([
            ["Policy Area", "Current State", "2027 Target", "Methodology"],
            ["Carbon footprint", "AWS SG region: ~18 tCO₂e/yr", "Net zero via AWS carbon credits", "AWS Customer Carbon Footprint Tool (monthly)"],
            ["Office energy", "WeWork hot-desk (no owned space)", "Remain asset-light", "Landlord ESG report"],
            ["Hardware", "Laptops refurbished where possible", "100% refurbished fleet", "Procurement policy enforced Q4 2026"],
            ["Paper usage", "Digital-first; <500 pages/month", "<100 pages/month", "Office supply invoices"],
        ], col_widths=[3.5*cm, 4*cm, 3.5*cm, 5.5*cm]),
        Paragraph(
            "We do not make environmental impact claims beyond the above measured metrics. "
            "All carbon offset purchases are verified under Gold Standard certification.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("S — Social", H2),
        Paragraph("<b>Access & Inclusion</b>", BOLD),
        Paragraph(
            "We offer a Means-Tested Subsidy Programme: users who qualify (household income "
            "< SGD 2,500/month) receive 80% subscription subsidy, funded by enterprise client "
            "CSR contributions. As of June 2026, 312 subsidised users are active (10% of paid base).", BODY),
        Paragraph("<b>Therapist Welfare</b>", BOLD),
        Paragraph(
            "All therapists are classified as independent contractors with transparent commission "
            "disclosure (85% of session fee to therapist, 15% platform fee). We provide mandatory "
            "clinical supervision (2hrs/month), peer support groups, and a Therapist Wellbeing Fund "
            "covering counselling expenses up to SGD 600/year. Supply chain is entirely within "
            "Singapore, Malaysia, Thailand, and Indonesia — jurisdictions with established labour "
            "protection frameworks.", BODY),
        Paragraph("<b>Workforce Diversity</b>", BOLD),
        table([
            ["Metric", "Current"],
            ["Female employees", "58% (11 of 19 full-time staff)"],
            ["Female leadership (VP and above)", "67% (4 of 6 senior leaders)"],
            ["Nationalities represented", "8 (SG, IN, MY, PH, TH, CN, NG, AU)"],
            ["Named diverse board members", "Dr. Aisha Rahman (CEO, Malay female); Dr. Tan Wei Ling (Chinese female advisor)"],
        ], col_widths=[6*cm, 10.5*cm]),
        Paragraph("<b>Data Privacy</b>", BOLD),
        Paragraph(
            "NeuralCare holds a comprehensive Privacy Policy (published at neuralcare.ai/privacy, "
            "version 3.1, May 2026). User mental health data is encrypted at rest and in transit, "
            "never sold to third parties, never used for advertising, and retained for maximum "
            "7 years post-account deletion per PDPA (Singapore) requirements. Users have full "
            "right to export and delete their data within 48 hours of request.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("G — Governance", H2),
        Paragraph("<b>Board Structure</b>", BOLD),
        Paragraph(
            "Board decisions require simple majority. No single founder holds veto rights. "
            "The board meets quarterly. Financial statements are reviewed by an independent "
            "auditor (Baker Tilly Singapore) annually.", BODY),
        Paragraph("<b>Financial Controls</b>", BOLD),
        Paragraph(
            "All financial projections in investor materials are based on stated assumptions "
            "documented in our financial model (available in data room). Revenue figures are "
            "reconciled monthly against Stripe and Xero. No inconsistencies exist between "
            "documents in this data room — all figures reference a single source-of-truth model.", BODY),
        Paragraph("<b>Team Verification</b>", BOLD),
        Paragraph(
            "All co-founders' credentials are independently verifiable. LinkedIn profiles are "
            "maintained and consistent with CVs in this data room. Professional references "
            "available upon request. Medical registration numbers: Dr. Aisha Rahman — SMC Reg. "
            "No. M2014-00412; Dr. Tan Wei Ling — SMC Reg. No. M1989-00178.", BODY),
        Paragraph("<b>ESG Reporting Cadence</b>", BOLD),
        Paragraph(
            "NeuralCare commits to annual ESG reporting aligned with GRI Standards Core option "
            "from FY2027 onwards. Board-level ESG committee established Q1 2026, chaired by "
            "co-founder Priya Nair.", BODY),
    ]
    d.build(story)
    print("[OK] 07_esg_policy.pdf")

# ─── DOC 8: Competitive Analysis ─────────────────────────────────────────────
def doc8():
    d = doc("08_competitive_analysis.pdf")
    story = cover("Competitive Analysis", "Mental Health Tech Landscape — SEA")
    story += [
        Paragraph("Competitive Landscape Overview", H2),
        Paragraph(
            "The global digital mental health market is crowded at the top (Calm, Headspace, "
            "BetterHelp) but nascent in Southeast Asia. The region's linguistic diversity, "
            "cultural stigma patterns, and regulatory fragmentation have prevented global "
            "incumbents from gaining meaningful traction. NeuralCare is purpose-built for SEA.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Direct Competitors", H2),
        table([
            ["Company", "HQ", "Focus", "SEA Presence", "Weakness vs. NeuralCare"],
            ["Intellect", "SG", "B2B EAP + self-help", "Strong (SG, MY)", "No therapist marketplace; B2C weak"],
            ["Wysa", "IN/UK", "AI chatbot CBT", "Moderate (IN, SG)", "No licensed therapists; India-centric NLP"],
            ["MindFi", "SG", "B2B EAP only", "Moderate (SG, HK)", "No B2C; acquired by Spring Health (2025)"],
            ["Calm", "US", "Mindfulness content", "Low (English only)", "No therapy; no SEA localisation"],
            ["BetterHelp", "US", "Therapist matching", "None (US only)", "Not licensed in SEA; no SEA therapists"],
            ["YeloHealth", "PH", "Therapy booking", "Philippines only", "Single-country; no AI layer"],
        ], col_widths=[3*cm, 2*cm, 3.5*cm, 3*cm, 5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Competitive Differentiation", H2),
        table([
            ["Capability", "NeuralCare", "Intellect", "Wysa", "Calm"],
            ["8 SEA languages", "✓", "✗ (4)", "✗ (3)", "✗ (1)"],
            ["Licensed therapist marketplace", "✓", "✗", "✗", "✗"],
            ["AI clinical model (SEA-trained)", "✓", "✗", "Partial", "✗"],
            ["B2B enterprise dashboard", "✓", "✓", "✓", "✗"],
            ["Crisis escalation pathway", "✓", "✓", "✓", "✗"],
            ["Data residency per country", "✓", "Partial", "✗", "✗"],
            ["Clinical validation study", "In progress (NUS)", "Published (2023)", "Published (2022)", "✗"],
            ["Means-tested access programme", "✓", "✗", "✗", "✗"],
        ], col_widths=[5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Barriers to Entry", H2),
        Paragraph(
            "NeuralCare's sustainable competitive advantages include: (1) a proprietary clinical "
            "AI model trained on 220K SEA therapy transcripts — a dataset that took 3 years to "
            "assemble under IRB approval and cannot be replicated quickly; (2) a network of 180 "
            "credentialled therapists across 4 countries representing 18 months of onboarding work; "
            "(3) clinical credibility through medical advisory board relationships that give "
            "enterprise clients the confidence to trust the platform with sensitive workforce data.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Why Global Incumbents Cannot Easily Enter SEA", H2),
        Paragraph(
            "Calm and Headspace generate 94%+ of revenue from English-speaking Western markets "
            "with no incentive to invest in 8-language SEA localisation at near-zero revenue. "
            "BetterHelp faces significant regulatory barriers — therapist licences in SG, MY, "
            "TH, and ID are non-transferable and require local credentials. Building a qualified "
            "therapist network from scratch would take 2–3 years and SGD 5–8M in investment.", BODY),
    ]
    d.build(story)
    print("[OK] 08_competitive_analysis.pdf")

# ─── DOC 9: Traction & KPIs ──────────────────────────────────────────────────
def doc9():
    d = doc("09_traction_metrics.pdf")
    story = cover("Traction & KPI Report", "As of June 2026")
    story += [
        Paragraph("Growth Summary", H2),
        Paragraph(
            "NeuralCare has achieved consistent month-over-month growth since product launch "
            "in October 2024. The following metrics represent verified data from Stripe (revenue), "
            "Mixpanel (engagement), and internal PostgreSQL analytics.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Monthly Active User Growth", H2),
        table([
            ["Month", "MAU", "Paying Users", "MoM Growth", "Revenue (SGD)"],
            ["Oct 2024 (launch)", "420",    "62",    "—",    "9,300"],
            ["Dec 2024",          "1,240",  "198",   "+48%", "27,600"],
            ["Feb 2025",          "2,800",  "462",   "+25%", "61,800"],
            ["Apr 2025",          "5,100",  "842",   "+21%", "112,200"],
            ["Jun 2025",          "7,600",  "1,240", "+19%", "165,500"],
            ["Aug 2025",          "9,800",  "1,620", "+16%", "214,800"],
            ["Oct 2025",          "11,400", "1,980", "+12%", "261,400"],
            ["Dec 2025",          "12,600", "2,340", "+11%", "305,700"],
            ["Feb 2026",          "13,200", "2,680", "+9%",  "341,200"],
            ["Apr 2026",          "13,800", "2,960", "+8%",  "368,800"],
            ["Jun 2026 (latest)", "14,200", "3,100", "+5%",  "383,000"],
        ], col_widths=[4*cm, 2.5*cm, 3*cm, 3*cm, 3.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Engagement Metrics", H2),
        table([
            ["Metric", "Value", "Benchmark"],
            ["Daily Active / Monthly Active (DAU/MAU)", "34%", "Industry avg: 18–22%"],
            ["Average sessions per active user/week", "4.2", "Calm: 3.1; Headspace: 2.8"],
            ["CBT module completion rate", "84%", "Industry avg: ~60%"],
            ["7-day retention (new users)", "62%", "App Store median (health): 35%"],
            ["30-day retention", "41%", "App Store median (health): 18%"],
            ["Average session duration", "11.4 min", "—"],
            ["NPS Score", "71", "Best-in-class health apps: 65–75"],
            ["App Store Rating", "4.7/5 (SG), 4.6/5 (MY)", "2,840 reviews combined"],
        ], col_widths=[6.5*cm, 4*cm, 6*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("B2B Enterprise Traction", H2),
        table([
            ["Client (anonymised)", "Country", "Seats", "Contract Value (SGD)", "Signed"],
            ["Global logistics firm (Fortune 500)",     "SG", "1,200", "86,400",  "Mar 2025"],
            ["Regional bank",                           "SG", "850",   "61,200",  "May 2025"],
            ["Tech company (Southeast Asian unicorn)",  "SG", "2,100", "151,200", "Jul 2025"],
            ["Government statutory board",              "SG", "600",   "43,200",  "Sep 2025"],
            ["International consulting firm",           "MY", "450",   "32,400",  "Nov 2025"],
            ["E-commerce platform (Fortune 500 office)","MY", "1,800", "129,600", "Jan 2026"],
            ["Healthcare group",                        "SG", "380",   "27,360",  "Mar 2026"],
            ["FMCG company",                            "SG", "720",   "51,840",  "Apr 2026"],
            ["Property developer",                      "MY", "290",   "20,880",  "May 2026"],
            ["University",                              "SG", "5,000*","180,000*","Pilot — Jun 2026"],
        ], col_widths=[5.5*cm, 1.5*cm, 1.5*cm, 4*cm, 3*cm]),
        Paragraph("* University pilot at 50% discount; conversion to full contract expected Q3 2026.", SMALL),
        Spacer(1, 0.3*cm),
        Paragraph("Clinical Outcomes (Early Data)", H2),
        Paragraph(
            "In partnership with NUS Medicine, 340 users who completed ≥8 weeks of NeuralCare "
            "CBT modules were assessed using validated instruments. Results (preliminary, not "
            "peer-reviewed): PHQ-9 score reduction of 4.2 points on average (moderate improvement); "
            "GAD-7 score reduction of 3.8 points. Full peer-reviewed publication expected Q1 2027.", BODY),
    ]
    d.build(story)
    print("[OK] 09_traction_metrics.pdf")

# ─── DOC 10: Investment Memorandum ───────────────────────────────────────────
def doc10():
    d = doc("10_investment_memorandum.pdf")
    story = cover("Investment Memorandum", "Seed Round — SGD 3.4M (USD 2.5M)")
    story += [
        Paragraph("Investment Opportunity", H2),
        Paragraph(
            "NeuralCare AI is seeking SGD 3.4M (USD 2.5M) in Seed funding to accelerate its "
            "AI-powered mental health platform across Southeast Asia. This round will extend "
            "runway to 24 months, fund regional expansion into Indonesia and Thailand, and "
            "enable the clinical validation study required for Class I medical device status.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Terms & Structure", H2),
        table([
            ["Term", "Detail"],
            ["Round Size",        "SGD 3.4M (USD 2.5M)"],
            ["Instrument",        "Priced equity (Ordinary Shares, Series Seed)"],
            ["Pre-money Valuation","SGD 17M (USD 12.5M)"],
            ["Post-money Valuation","SGD 20.4M (USD 15M)"],
            ["Price per Share",   "SGD 0.85"],
            ["Lead Ticket Size",  "SGD 1.5M minimum (receives board seat)"],
            ["Follow-on Tickets", "SGD 250K minimum"],
            ["Pro-rata Rights",   "Available to all Seed investors in Series A"],
            ["Information Rights","Quarterly financial reports + annual audited accounts"],
            ["Closing Date",      "Target: 31 August 2026"],
        ], col_widths=[5*cm, 11.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Use of Funds", H2),
        table([
            ["Category", "Amount (SGD)", "% of Round", "Rationale"],
            ["Product & Engineering",  "1,190,000", "35%", "2 senior engineers + AI model training infra"],
            ["Market Expansion (ID+TH)","1,360,000", "40%", "Country leads, localisation, regulatory filings"],
            ["Clinical Partnerships",  "510,000",   "15%", "NUS study completion; MOH SG advisory engagement"],
            ["Operations & G&A",       "340,000",   "10%", "Finance, legal, compliance (ISO 27001)"],
            ["TOTAL",                  "3,400,000", "100%","24-month runway to EBITDA breakeven"],
        ], col_widths=[4.5*cm, 3*cm, 2.5*cm, 6.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Cap Table (Pre-Round)", H2),
        table([
            ["Shareholder", "Shares", "% (pre-money)"],
            ["Dr. Aisha Rahman (CEO)",     "6,000,000",  "30.0%"],
            ["Marcus Tan (CTO)",           "6,000,000",  "30.0%"],
            ["Priya Nair (COO)",           "6,000,000",  "30.0%"],
            ["ESOP Pool (existing)",        "2,000,000",  "10.0%"],
            ["TOTAL (pre-round)",           "20,000,000", "100.0%"],
        ], col_widths=[6*cm, 5*cm, 5.5*cm]),
        Spacer(1, 0.3*cm),
        Paragraph("Post-Round Cap Table", H2),
        table([
            ["Shareholder", "Shares", "% (post-money)"],
            ["Dr. Aisha Rahman (CEO)",  "6,000,000",  "25.0%"],
            ["Marcus Tan (CTO)",        "6,000,000",  "25.0%"],
            ["Priya Nair (COO)",        "6,000,000",  "25.0%"],
            ["ESOP Pool (expanded)",    "2,000,000",  "8.3%"],
            ["Seed Investors",          "4,000,000",  "16.7%"],
            ["TOTAL (post-round)",      "24,000,000", "100.0%"],
        ], col_widths=[6*cm, 5*cm, 5.5*cm]),
        Spacer(1, 0.4*cm),
        Paragraph("Exit Scenarios & Comparable Transactions", H2),
        table([
            ["Comparable", "Acquirer / Event", "Stage at Exit", "Exit Multiple (Revenue)"],
            ["MindFi (SG)",         "Spring Health (US)",        "Seed + Series A",  "~8x ARR"],
            ["Ginger.io (US)",      "Headspace Health merger",   "Series C",         "~12x ARR"],
            ["Lyra Health (US)",    "IPO (pending)",             "Series F",         "~22x ARR"],
            ["Koa Health (ES)",     "Strategic acquisition",     "Series B",         "~9x ARR"],
            ["NeuralCare (target)", "Strategic / PE / IPO",      "Series B–C exit",  "10–15x ARR"],
        ], col_widths=[4*cm, 4*cm, 3*cm, 4.5*cm]),
        Spacer(1, 0.3*cm),
        Paragraph(
            "At a 10x ARR exit multiple applied to FY2028 projected revenue of SGD 7.97M, "
            "implied enterprise value is SGD 79.7M. Seed investors at post-money SGD 20.4M "
            "would see a 3.9x return on exit value alone — consistent with the median "
            "HealthTech Seed→Series B return profile in SEA (Cento Ventures, 2025).", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Data Room Access", H2),
        Paragraph(
            "Full data room is available under NDA. Contents include: audited accounts (FY2025), "
            "Stripe revenue dashboard access, cap table in Carta, IP assignment agreements, "
            "employment contracts, clinical advisory board agreements, AWS architecture diagram, "
            "and NUS IRB approval letter for clinical dataset.", BODY),
        Spacer(1, 0.3*cm),
        Paragraph("Contact", H2),
        Paragraph("Dr. Aisha Rahman | CEO | aisha@neuralcare.ai | +65 9123 4567", BODY),
        Paragraph("Priya Nair | COO (Investor Relations) | priya@neuralcare.ai | +65 9876 5432", BODY),
    ]
    d.build(story)
    print("[OK] 10_investment_memorandum.pdf")

if __name__ == "__main__":
    doc1(); doc2(); doc3(); doc4(); doc5()
    doc6(); doc7(); doc8(); doc9(); doc10()
    print(f"\nAll 10 documents saved to: {OUT}")
