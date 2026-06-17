"""Static-site generator for the DPS & Co (Mumbai CA firm) website.

Run:  py build.py      -> writes the full site into ./dist (HTML + sitemap + robots + llms.txt)
Serve: cd dist && py -m http.server 8080   -> open http://localhost:8080/

Implements the SEO+AEO spec: flat URLs, semantic HTML, per-page JSON-LD
(Organization/LocalBusiness/Service/FAQPage/BreadcrumbList/Person), canonical
tags, auto-generated sitemap.xml, robots.txt (AI crawlers allowed), llms.txt.
"""

import glob
import json
import os
import shutil
from datetime import date

# ---------------------------------------------------------------------------
# Site config.  PLACEHOLDERS marked [...] MUST be replaced with the firm's real,
# verified details and must match the Google Business Profile EXACTLY (NAP).
# ---------------------------------------------------------------------------
SITE = {
    "name": "DPS & Co, Chartered Accountants",
    "short": "DPS & Co",
    "domain": "https://dpsca.in",
    "phone": "+91 22 4978 5313",                # landline (also 14 / 15)
    "phone_alt": "+91 99694 90502",
    "email": "info@dpsca.in",                   # [VERIFY — emails were masked on the live site]
    "street": "1903, 19th Floor, Naman Midtown, 'A' Wing, Senapati Bapat Marg, Prabhadevi (Elphinstone Road West)",
    "locality": "Mumbai",
    "region": "Maharashtra",
    "postal": "400013",
    "founded": "2016",
    "areas": ["Mumbai", "Thane", "Navi Mumbai"],
    "maps_embed": "https://www.google.com/maps?q=Naman+Midtown,+Senapati+Bapat+Marg,+Prabhadevi,+Mumbai+400013&output=embed",  # [REPLACE with verified Google Business Profile place URL]
}
TODAY = date.today().isoformat()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "dist")
POSTS_DIR = os.path.join(HERE, "content", "posts")   # approved auto-blog posts (JSON)


def load_posts() -> list[dict]:
    """Load approved blog posts (from the auto-blog pipeline) to render in Resources."""
    posts = []
    for fp in sorted(glob.glob(os.path.join(POSTS_DIR, "*.json"))):
        try:
            with open(fp, encoding="utf-8") as f:
                posts.append(json.load(f))
        except (OSError, json.JSONDecodeError):
            continue
    return posts

NAV = [
    ("Home", "/"),
    ("Practices", "/practices/"),
    ("Industries", "/industries/"),
    ("Resources", "/resources/"),
    ("About", "/about/"),
    ("Contact", "/contact/"),
]


# --------------------------- rendering helpers ----------------------------

def jsonld(obj: dict) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, separators=(",", ":")) + "</script>"


def breadcrumbs(crumbs: list[tuple[str, str]]):
    """crumbs: [(name, path), ...]. Returns (visible_html, schema)."""
    links = " &rsaquo; ".join(
        (f'<a href="{p}">{n}</a>' if p else f"<span>{n}</span>") for n, p in crumbs
    )
    schema = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             "item": SITE["domain"] + p} for i, (n, p) in enumerate(crumbs) if p
        ],
    }
    return f'<nav class="crumbs wrap" aria-label="Breadcrumb">{links}</nav>', schema


def faq_section(faqs: list[tuple[str, str]]):
    """Returns (visible_html, FAQPage schema). Schema mirrors visible text exactly."""
    items = "".join(
        f"<details><summary>{q}</summary><div class='a'>{a}</div></details>" for q, a in faqs
    )
    html = f'<section class="faq"><h2>Frequently asked questions</h2>{items}</section>'
    schema = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": _strip(a)}} for q, a in faqs
        ],
    }
    return html, schema


def _strip(html: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html).strip()


def page(path: str, title: str, description: str, body: str, schemas: list[dict],
         active: str = "", hero: str = "") -> None:
    """Render one page to dist/<path>/index.html (path '' -> root)."""
    canonical = SITE["domain"] + ("/" if path == "" else f"/{path}/")
    nav_links = "".join(
        f'<a href="{p}"{" aria-current=\"page\"" if (label == active) else ""}>{label}</a>'
        for label, p in NAV
    )
    ld = "".join(jsonld(s) for s in schemas if s)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="/assets/styles.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap">
  <a class="brand" href="/"><span class="mark">DP</span><span>{SITE['short']}<small>CHARTERED ACCOUNTANTS &middot; MUMBAI</small></span></a>
  <button class="nav-toggle" aria-expanded="false" aria-label="Menu">Menu</button>
  <nav class="main" aria-label="Primary">{nav_links}</nav>
  <a class="cta-btn" href="/contact/">Contact</a>
</div></header>
{hero}
<main id="main"><div class="wrap">
{body}
</div></main>
<footer class="site"><div class="wrap">
  <div class="grid">
    <div>
      <strong>{SITE['name']}</strong>
      <p class="muted" style="color:#9fb2cd">Tax, audit, assurance and advisory services for businesses and individuals across {", ".join(SITE['areas'])}. Established {SITE['founded']}.</p>
    </div>
    <div><h4>Practices</h4><ul>
      <li><a href="/practices/advisory/">Advisory</a></li>
      <li><a href="/practices/tax-regulatory/">Tax &amp; Regulatory</a></li>
      <li><a href="/practices/litigation/">Litigation</a></li>
      <li><a href="/practices/audit-assurance/">Audit &amp; Assurance</a></li>
    </ul></div>
    <div><h4>Services</h4><ul>
      <li><a href="/services/gst-registration/">GST Registration</a></li>
      <li><a href="/services/income-tax-filing/">Income Tax Filing</a></li>
      <li><a href="/services/company-incorporation/">Company Incorporation</a></li>
      <li><a href="/services/">All services</a></li>
    </ul></div>
    <div><h4>Firm</h4><ul>
      <li><a href="/industries/">Industries</a></li>
      <li><a href="/resources/">Resources</a></li>
      <li><a href="/about/">About &amp; Team</a></li>
      <li><a href="/contact/">Contact</a></li>
    </ul></div>
  </div>
  <div class="legal">
    <p>{SITE['street']}, {SITE['locality']}, {SITE['region']} {SITE['postal']} &middot; {SITE['phone']} &middot; {SITE['email']}</p>
    <p>&copy; {date.today().year} {SITE['name']}. This website is for information only and does not constitute solicitation or professional advice. <a href="/contact/">Get in touch</a> for advice specific to your situation.</p>
  </div>
</div></footer>
<script src="/assets/main.js" defer></script>
</body>
</html>"""
    target_dir = OUT if path == "" else os.path.join(OUT, *path.split("/"))
    os.makedirs(target_dir, exist_ok=True)
    fname = "index.html"
    with open(os.path.join(target_dir, fname), "w", encoding="utf-8") as f:
        f.write(html)


# ------------------------------- content ----------------------------------

ORG_SCHEMA = {
    "@context": "https://schema.org", "@type": "AccountingService",
    "name": SITE["name"], "url": SITE["domain"], "telephone": SITE["phone"],
    "email": SITE["email"], "foundingDate": SITE["founded"],
    "address": {"@type": "PostalAddress", "streetAddress": SITE["street"],
                "addressLocality": SITE["locality"], "addressRegion": SITE["region"],
                "postalCode": SITE["postal"], "addressCountry": "IN"},
    "areaServed": SITE["areas"],
}

SERVICES = [
    {
        "slug": "gst-registration", "nav": "GST Registration",
        "h1": "GST Registration in Mumbai",
        "title": "GST Registration in Mumbai | DPS & Co",
        "desc": "End-to-end GST registration for Mumbai businesses, handled by Chartered Accountants. Contact us for a quote.",
        "answer": "GST registration is the process of obtaining a GSTIN so a business can legally collect GST and claim input tax credit. We handle the entire application, from documents to GSTIN, for businesses in Mumbai.",
        "what": "<p>Registration is mandatory once aggregate turnover exceeds <strong>₹40 lakh for goods</strong> or <strong>₹20 lakh for services</strong> in most states, and in certain cases (inter-state supply, e-commerce, casual taxable persons) regardless of turnover — as per the CGST Act, 2017. Voluntary registration is also permitted.</p>",
        "steps": ["Assess whether registration is required and the correct registration type.",
                   "Collect and verify documents (PAN, proof of business, address proof, bank details).",
                   "File the application on the GST portal and respond to any clarification.",
                   "Receive the GSTIN and registration certificate."],
        "docs": ["PAN of the business/proprietor", "Aadhaar of the proprietor/partners/directors",
                  "Proof of business address (electricity bill / rent agreement / NOC)",
                  "Bank account proof (cancelled cheque or statement)", "Photographs and constitution documents"],
        "timeline": "Typically 7–14 working days after complete documents, subject to GST department processing and any Aadhaar authentication.",
        "pricing": "Fees depend on entity type and complexity. Contact us for a quote.",
        "faqs": [
            ("When is GST registration mandatory?", "GST registration is mandatory once aggregate turnover exceeds ₹40 lakh for goods or ₹20 lakh for services in most states, and in specific cases such as inter-state supply or e-commerce regardless of turnover, as per the CGST Act, 2017."),
            ("How long does GST registration take?", "It usually takes about 7 to 14 working days after all documents are in order, depending on GST department processing and Aadhaar authentication."),
            ("Can I register voluntarily below the threshold?", "Yes. Voluntary GST registration is allowed and can help a business claim input tax credit and supply to GST-registered customers."),
            ("What is the official GST portal?", "The official portal is the Goods and Services Tax Network at gst.gov.in, operated under CBIC."),
        ],
        "related": [("Income Tax Filing", "/services/income-tax-filing/"), ("Company Incorporation", "/services/company-incorporation/")],
        "source": '<p class="src">Source: CGST Act, 2017 and CBIC notifications — <a href="https://www.gst.gov.in" rel="nofollow">gst.gov.in</a>. Thresholds vary for special-category states; we confirm the rule for your case.</p>',
    },
    {
        "slug": "income-tax-filing", "nav": "Income Tax Filing",
        "h1": "Income Tax Return (ITR) Filing in Mumbai",
        "title": "Income Tax Filing in Mumbai | DPS & Co",
        "desc": "ITR preparation and filing for individuals and businesses in Mumbai by Chartered Accountants. Contact us to file.",
        "answer": "Income tax return (ITR) filing is the annual reporting of income and tax to the Income Tax Department. We prepare and file the correct ITR form for salaried individuals, professionals, and businesses in Mumbai.",
        "what": "<p>For individuals not subject to audit, the ITR due date is generally <strong>31 July</strong> of the assessment year; for taxpayers requiring a tax audit it is generally <strong>31 October</strong> — as per the Income Tax Act, 1961. Choosing the right form (ITR-1 to ITR-7) and tax regime materially affects the outcome.</p>",
        "steps": ["Determine the applicable ITR form and tax regime (old vs new).",
                   "Collect income, deduction, and TDS details (Form 16, AIS, 26AS).",
                   "Compute total income, deductions, and tax; reconcile with TDS.",
                   "File the return and assist with e-verification and any notices."],
        "docs": ["PAN and Aadhaar", "Form 16 / salary details", "Bank interest, capital gains, other income",
                  "Investment and deduction proofs (80C, 80D, etc.)", "Form 26AS and Annual Information Statement (AIS)"],
        "timeline": "Most straightforward returns are filed within 2–5 working days of receiving complete information; complex cases take longer.",
        "pricing": "Fees vary by return type and complexity. Contact us for a quote.",
        "faqs": [
            ("What is the ITR filing due date?", "For individuals not requiring a tax audit, the due date is generally 31 July of the assessment year; for audit cases it is generally 31 October, as per the Income Tax Act, 1961. Dates can be extended by CBDT notification."),
            ("Which ITR form should I use?", "It depends on your income sources — for example, ITR-1 (Sahaj) suits most salaried individuals with income up to a limit, while business and capital-gains income use other forms. We determine the correct form for you."),
            ("Old regime or new regime — which is better?", "It depends on your deductions and income. We compute the tax under both and file under the one that results in lower tax for your situation."),
            ("What is the official income tax portal?", "The official e-filing portal is incometax.gov.in, operated by the Income Tax Department."),
        ],
        "related": [("GST Registration", "/services/gst-registration/"), ("Audit & Assurance", "/services/audit-assurance/")],
        "source": '<p class="src">Source: Income Tax Act, 1961 and CBDT — <a href="https://www.incometax.gov.in" rel="nofollow">incometax.gov.in</a>. Due dates may be extended by official notification; we confirm current dates at the time of filing.</p>',
    },
    {
        "slug": "company-incorporation", "nav": "Company Incorporation",
        "h1": "Company Incorporation in Mumbai",
        "title": "Company Incorporation in Mumbai | DPS & Co",
        "desc": "Private limited, LLP and OPC incorporation in Mumbai, end to end, by Chartered Accountants. Contact us to start.",
        "answer": "Company incorporation is the process of legally forming a company with the Ministry of Corporate Affairs (MCA). We handle private limited, LLP, and one-person company (OPC) formation in Mumbai, from name approval to the certificate of incorporation.",
        "what": "<p>Private limited companies and LLPs are incorporated through the MCA portal using the integrated <strong>SPICe+</strong> form, which also covers PAN, TAN, and (where applicable) GST and EPFO/ESIC registration — as prescribed by the Companies Act, 2013 and MCA rules.</p>",
        "steps": ["Advise on the right structure (Pvt Ltd, LLP, OPC) for your goals.",
                   "Obtain Digital Signature Certificates (DSC) and Director Identification Numbers (DIN).",
                   "Reserve the company name and prepare the MoA, AoA, and incorporation forms.",
                   "File SPICe+ with MCA and receive the Certificate of Incorporation, PAN, and TAN."],
        "docs": ["PAN and Aadhaar of all directors/partners", "Passport-size photographs",
                  "Proof of registered office (utility bill + NOC/rent agreement)",
                  "Identity and address proof of directors", "Proposed company names and main objects"],
        "timeline": "Generally 10–15 working days after documents and DSCs are ready, subject to MCA processing and name approval.",
        "pricing": "Government fees plus professional fees vary by structure and capital. Contact us for a quote.",
        "faqs": [
            ("How long does it take to incorporate a company?", "Generally 10 to 15 working days once documents and Digital Signature Certificates are ready, subject to MCA processing and name approval."),
            ("What is SPICe+?", "SPICe+ is the integrated incorporation form on the MCA portal that combines company registration with PAN, TAN, and other registrations, under the Companies Act, 2013."),
            ("Private limited or LLP — which should I choose?", "It depends on funding plans, compliance appetite, and liability. We advise on the structure that fits your business before filing."),
            ("What is the official portal for company registration?", "The official portal is the Ministry of Corporate Affairs at mca.gov.in."),
        ],
        "related": [("GST Registration", "/services/gst-registration/"), ("Business Advisory", "/services/business-advisory/")],
        "source": '<p class="src">Source: Companies Act, 2013 and MCA rules — <a href="https://www.mca.gov.in" rel="nofollow">mca.gov.in</a>.</p>',
    },
    {
        "slug": "audit-assurance", "nav": "Audit & Assurance",
        "h1": "Audit & Assurance Services in Mumbai",
        "title": "Audit & Assurance in Mumbai | DPS & Co",
        "desc": "Statutory, tax and internal audit and assurance for Mumbai businesses by Chartered Accountants. Contact us.",
        "answer": "Audit and assurance is the independent examination of financial records to confirm they give a true and fair view. We provide statutory audit, tax audit, internal audit, and related assurance for businesses in Mumbai.",
        "what": "<p>A tax audit under <strong>Section 44AB</strong> of the Income Tax Act is generally required where business turnover exceeds the prescribed limit; statutory audit applies to companies under the Companies Act, 2013. We scope each engagement to the applicable law.</p>",
        "steps": ["Determine the applicable audit (statutory, tax, internal) and scope.",
                   "Plan the audit and assess risks and controls.",
                   "Examine records, vouch transactions, and verify balances.",
                   "Report findings and file the required audit reports."],
        "docs": ["Books of account and trial balance", "Bank statements and reconciliations",
                  "GST and TDS returns", "Fixed asset register and stock records", "Prior-year financials and audit reports"],
        "timeline": "Depends on the size and readiness of records; we agree a timeline at the planning stage.",
        "pricing": "Fees depend on turnover, scope, and complexity. Contact us for a quote.",
        "faqs": [
            ("When is a tax audit required?", "A tax audit under Section 44AB of the Income Tax Act is generally required when business turnover exceeds the prescribed threshold; the limit and conditions are confirmed for each client."),
            ("What is the difference between statutory and internal audit?", "A statutory audit is a legally required independent examination of financial statements; an internal audit is an ongoing review of controls and processes carried out for management."),
            ("Do all companies need a statutory audit?", "Companies registered under the Companies Act, 2013 are generally required to have their accounts audited each year, regardless of turnover."),
        ],
        "related": [("Income Tax Filing", "/services/income-tax-filing/"), ("Business Advisory", "/services/business-advisory/")],
        "source": '<p class="src">Source: Income Tax Act, 1961 (Section 44AB) and Companies Act, 2013. We confirm applicable thresholds for your entity.</p>',
    },
    {
        "slug": "business-advisory", "nav": "Business Advisory",
        "h1": "Business Advisory Services in Mumbai",
        "title": "Business Advisory in Mumbai | DPS & Co",
        "desc": "Tax planning, transaction support, due diligence and CFO services for Mumbai businesses. Contact us.",
        "answer": "Business advisory covers strategic and financial guidance beyond compliance — tax planning, transaction support, due diligence, and outsourced CFO services. We work with businesses across Mumbai to support decisions and growth.",
        "what": "<p>Advisory engagements are tailored to the business — from structuring and tax efficiency within the law, to financial reporting support and management information. We provide advisory only in areas permitted to Chartered Accountants in practice.</p>",
        "steps": ["Understand the business, its goals, and the decision at hand.",
                   "Analyse financials, tax position, and options.",
                   "Recommend a course of action with the trade-offs explained.",
                   "Support implementation and ongoing review."],
        "docs": ["Recent financial statements", "Tax returns and assessments",
                  "Details of the transaction or decision", "Management accounts / projections (if available)"],
        "timeline": "Scoped per engagement and agreed in advance.",
        "pricing": "Fees are engagement-based. Contact us for a quote.",
        "faqs": [
            ("What does business advisory include?", "It includes tax planning, transaction support, due diligence, and outsourced CFO/financial reporting support — guidance beyond routine compliance, within the scope permitted to Chartered Accountants."),
            ("Do you provide CFO services?", "Yes. We offer outsourced CFO and financial-controller support, including management reporting and financial oversight, scoped to the engagement."),
            ("Can you help with due diligence for a transaction?", "Yes. We carry out financial and tax due diligence to help you understand risks before a transaction."),
        ],
        "related": [("Audit & Assurance", "/services/audit-assurance/"), ("Company Incorporation", "/services/company-incorporation/")],
        "source": '<p class="src">Advisory is provided within the scope permitted to members in practice under ICAI regulations.</p>',
    },
    {
        "slug": "gst-return-filing", "nav": "GST Return Filing",
        "h1": "GST Return Filing in Mumbai",
        "title": "GST Return Filing in Mumbai | DPS & Co",
        "desc": "Monthly, quarterly and annual GST return filing (GSTR-1, GSTR-3B, GSTR-9) for Mumbai businesses. Contact us.",
        "answer": "GST return filing is the periodic reporting of sales, purchases, and tax to the GST department. We prepare and file GSTR-1, GSTR-3B, and annual returns for businesses in Mumbai, and reconcile input tax credit.",
        "what": "<p>Regular taxpayers file <strong>GSTR-1</strong> (outward supplies) and <strong>GSTR-3B</strong> (summary and payment), monthly or quarterly under the QRMP scheme, plus the annual return <strong>GSTR-9</strong> where applicable — as per the CGST Act, 2017 and CBIC rules.</p>",
        "steps": ["Reconcile sales, purchases, and input tax credit (GSTR-2B).",
                   "Prepare and file GSTR-1 and GSTR-3B for the period.",
                   "Compute and arrange GST payment, if any.",
                   "File annual return (GSTR-9) and reconciliation where required."],
        "docs": ["Sales and purchase registers", "Issued tax invoices and credit/debit notes",
                  "Purchase invoices for input tax credit", "GST login credentials", "Bank statements for the period"],
        "timeline": "Returns are filed within each statutory cycle; we agree a recurring schedule so deadlines are never missed.",
        "pricing": "Fees depend on transaction volume and frequency. Contact us for a quote.",
        "faqs": [
            ("What is the GSTR-3B due date?", "GSTR-3B is generally due by the 20th of the following month for monthly filers (staggered dates apply for QRMP/quarterly filers), as per CBIC notifications. We confirm the exact date for your registration."),
            ("What is the difference between GSTR-1 and GSTR-3B?", "GSTR-1 reports the details of outward supplies (sales), while GSTR-3B is a summary return through which tax is paid. Both are filed by regular taxpayers."),
            ("What is the QRMP scheme?", "QRMP lets small taxpayers (turnover up to the prescribed limit) file GSTR-1 and GSTR-3B quarterly while paying tax monthly."),
        ],
        "related": [("GST Registration", "/services/gst-registration/"), ("Accounting & Outsourcing", "/services/accounting-outsourcing/")],
        "source": '<p class="src">Source: CGST Act, 2017 and CBIC — <a href="https://www.gst.gov.in" rel="nofollow">gst.gov.in</a>. Due dates can change by notification; we confirm current dates each cycle.</p>',
    },
    {
        "slug": "tds-return-filing", "nav": "TDS Return Filing",
        "h1": "TDS Return Filing in Mumbai",
        "title": "TDS Return Filing in Mumbai | DPS & Co",
        "desc": "TDS computation, payment and quarterly return filing (Form 24Q, 26Q) for Mumbai businesses. Contact us.",
        "answer": "TDS return filing is the quarterly reporting of tax deducted at source to the Income Tax Department. We compute TDS, arrange deposit, and file the quarterly returns (Form 24Q for salaries, 26Q for other payments) for businesses in Mumbai.",
        "what": "<p>TDS deducted must generally be <strong>deposited by the 7th</strong> of the following month, and quarterly returns are generally due by the <strong>end of the month following each quarter</strong> — as per the Income Tax Act, 1961. We also help issue Form 16 / 16A.</p>",
        "steps": ["Identify payments liable to TDS and the correct rates.",
                   "Compute TDS and arrange monthly deposit by challan.",
                   "Prepare and file the quarterly return (24Q / 26Q).",
                   "Generate and issue TDS certificates (Form 16 / 16A)."],
        "docs": ["Details of payments and deductees (PAN)", "TDS challans / payment details",
                  "Salary details (for 24Q)", "Previous TDS returns and TAN", "Vendor invoices where relevant"],
        "timeline": "Aligned to the statutory monthly deposit and quarterly filing cycle; we manage the schedule for you.",
        "pricing": "Fees depend on the number of deductees and frequency. Contact us for a quote.",
        "faqs": [
            ("When must TDS be deposited?", "TDS deducted is generally required to be deposited by the 7th of the following month, with a different date for March, as per the Income Tax Act, 1961."),
            ("What are the TDS return forms?", "Form 24Q is used for TDS on salaries and Form 26Q for TDS on most other payments to residents. We file the correct form for each case."),
            ("What is Form 16?", "Form 16 is the TDS certificate issued to employees summarising salary paid and tax deducted; Form 16A is issued for non-salary TDS."),
        ],
        "related": [("Income Tax Filing", "/services/income-tax-filing/"), ("Accounting & Outsourcing", "/services/accounting-outsourcing/")],
        "source": '<p class="src">Source: Income Tax Act, 1961 and CBDT — <a href="https://www.incometax.gov.in" rel="nofollow">incometax.gov.in</a> / TRACES.</p>',
    },
    {
        "slug": "tax-litigation", "nav": "Tax Litigation Support",
        "h1": "Tax Litigation Support in Mumbai",
        "title": "Tax Litigation Support in Mumbai | DPS & Co",
        "desc": "Support for direct and indirect tax notices, assessments and appeals in Mumbai. Strategy, drafting, representation. Contact us.",
        "answer": "Tax litigation support is help with tax disputes — responding to notices, assessments, and appeals for both direct tax (income tax) and indirect tax (GST). We frame strategy, draft and file submissions, and appear before the authorities.",
        "what": "<p>We handle representation at the levels permitted to Chartered Accountants and coordinate with counsel for matters beyond that scope. Engagements cover income-tax and GST notices, scrutiny assessments, and first-level appeals.</p>",
        "steps": ["Review the notice/order and the underlying facts.",
                   "Frame a response strategy and assess the merits.",
                   "Draft and file the reply, submission, or appeal.",
                   "Represent / appear before the relevant authority and coordinate with counsel where needed."],
        "docs": ["The notice or order received", "Relevant returns and financial records",
                  "Prior correspondence with the department", "Supporting evidence and documentation"],
        "timeline": "Driven by statutory response deadlines on the notice; we act quickly to protect your position.",
        "pricing": "Fees are engagement-based and depend on the forum and complexity. Contact us for a quote.",
        "faqs": [
            ("I received an income tax / GST notice — what should I do?", "Act before the response deadline on the notice. Share it with us; we review the facts, advise on the merits, and draft a timely, well-supported reply."),
            ("Can a CA represent me in tax matters?", "Chartered Accountants can represent clients before tax authorities at the levels permitted under the law; for matters beyond that scope we coordinate with legal counsel."),
            ("What does litigation support include?", "It includes strategy, drafting and filing replies and appeals, and appearance before the relevant tax authority for direct and indirect tax disputes."),
        ],
        "related": [("Income Tax Filing", "/services/income-tax-filing/"), ("GST Return Filing", "/services/gst-return-filing/")],
        "source": '<p class="src">Representation is provided within the scope permitted to members in practice under ICAI and applicable law.</p>',
    },
    {
        "slug": "accounting-outsourcing", "nav": "Accounting & Outsourcing",
        "h1": "Accounting & Bookkeeping Outsourcing in Mumbai",
        "title": "Accounting & Outsourcing in Mumbai | DPS & Co",
        "desc": "Outsourced bookkeeping, payroll and compliance for Mumbai businesses, handled by Chartered Accountants. Contact us.",
        "answer": "Accounting outsourcing means handing your bookkeeping, payroll, and routine compliance to us so your team can focus on running the business. We maintain the books, file returns, and provide regular management information for businesses in Mumbai.",
        "what": "<p>We set up or maintain your accounts, reconcile bank and ledgers, run payroll and statutory deductions, and keep GST and TDS compliance on schedule — with periodic management reports (MIS).</p>",
        "steps": ["Set up or take over the books and chart of accounts.",
                   "Record transactions and reconcile bank, debtors, and creditors.",
                   "Run payroll and statutory deductions (TDS, PF/ESIC where applicable).",
                   "File periodic returns and share management reports."],
        "docs": ["Bank statements and transaction records", "Sales and purchase invoices",
                  "Payroll inputs", "Existing accounting data / software access"],
        "timeline": "Set up as an ongoing monthly engagement; we agree reporting dates up front.",
        "pricing": "Fees depend on volume and scope. Contact us for a quote.",
        "faqs": [
            ("What does accounting outsourcing cover?", "It typically covers bookkeeping, bank and ledger reconciliation, payroll, GST and TDS compliance, and periodic management reporting, scoped to your needs."),
            ("Will I still get regular reports?", "Yes. We provide periodic management information (MIS) so you always have an up-to-date view of your finances."),
            ("Can you take over books mid-year?", "Yes. We can take over existing books, reconcile them, and continue maintenance going forward."),
        ],
        "related": [("GST Return Filing", "/services/gst-return-filing/"), ("TDS Return Filing", "/services/tds-return-filing/")],
        "source": '<p class="src">Services provided within the scope permitted to members in practice under ICAI regulations.</p>',
    },
]


def build_service(s: dict) -> None:
    crumbs_html, crumbs_schema = breadcrumbs(
        [("Home", "/"), ("Services", "/services/"), (s["nav"], "")])
    faq_html, faq_schema = faq_section(s["faqs"])
    steps = "".join(f"<li>{x}</li>" for x in s["steps"])
    docs = "".join(f"<li>{x}</li>" for x in s["docs"])
    related = "".join(f'<li><a href="{u}">{l}</a></li>' for l, u in s["related"])
    body = f"""
<h1>{s['h1']}</h1>
<p class="lede">{s['answer']}</p>
{s['what']}
<h2>What is the process?</h2>
<ol class="steps">{steps}</ol>
<h2>What documents are required?</h2>
<ul class="ticks">{docs}</ul>
<div class="metarow">
  <div><span class="k">Typical timeline</span>{s['timeline']}</div>
  <div><span class="k">Fees</span>{s['pricing']}</div>
</div>
{s['source']}
<p><a class="cta-btn" href="/contact/">Request a quote</a></p>
{faq_html}
<h2>Related services</h2>
<ul class="ticks">{related}<li><a href="/contact/">Talk to us about your requirement</a></li></ul>
"""
    service_schema = {
        "@context": "https://schema.org", "@type": "Service",
        "name": s["nav"], "serviceType": s["nav"],
        "provider": {"@type": "AccountingService", "name": SITE["name"], "url": SITE["domain"]},
        "areaServed": SITE["areas"], "url": SITE["domain"] + f"/services/{s['slug']}/",
        "description": s["desc"],
    }
    page(f"services/{s['slug']}", s["title"], s["desc"],
         crumbs_html + body, [service_schema, faq_schema, crumbs_schema], active="Services")


ARTICLES = [
    {
        "slug": "itr-filing-deadlines", "card": "Income tax return deadlines", "crumb": "ITR deadlines",
        "headline": "Income tax return deadlines in India",
        "h1": "Income tax return deadlines in India",
        "title": "Income Tax Return Deadlines in India | DPS & Co",
        "desc": "ITR due dates explained: 31 July for individuals, 31 October for audit cases. Reviewed annually.",
        "lede": "For most individuals not subject to a tax audit, the income tax return (ITR) due date is 31 July of the assessment year. For taxpayers requiring a tax audit, it is generally 31 October.",
        "body": "<h2>Why do the dates differ?</h2><p>The due date depends on whether your accounts must be audited. Non-audit individuals file by 31 July; audit cases get additional time to 31 October because the audit must be completed first — as per the Income Tax Act, 1961.</p><h2>What happens if you miss the deadline?</h2><p>A belated return can usually still be filed by 31 December of the assessment year, but late fees and interest may apply, and some benefits (such as carrying forward certain losses) can be lost.</p>",
        "faqs": [
            ("What is the ITR due date for individuals?", "For individuals not requiring a tax audit, the income tax return due date is generally 31 July of the assessment year, as per the Income Tax Act, 1961, unless extended by CBDT."),
            ("What is the due date for audit cases?", "For taxpayers who require a tax audit, the return due date is generally 31 October of the assessment year."),
        ],
        "source": 'Source: Income Tax Act, 1961 and CBDT — <a href="https://www.incometax.gov.in" rel="nofollow">incometax.gov.in</a>. Dates may be extended by official notification; confirm the current year\'s dates before filing.',
        "cta": "/services/income-tax-filing/", "cta_label": "See our ITR filing service",
    },
    {
        "slug": "gst-return-due-dates", "card": "GST return due dates", "crumb": "GST due dates",
        "headline": "GST return due dates in India",
        "h1": "GST return due dates (GSTR-1 and GSTR-3B)",
        "title": "GST Return Due Dates (GSTR-1 & GSTR-3B) | DPS & Co",
        "desc": "GST due dates explained: GSTR-3B by the 20th, GSTR-1 by the 11th for monthly filers; QRMP and annual dates too.",
        "lede": "For monthly filers, GSTR-3B is generally due by the 20th of the following month and GSTR-1 by the 11th. Small taxpayers under the QRMP scheme follow staggered quarterly dates.",
        "body": "<h2>Monthly filers</h2><p>GSTR-1 (outward supplies) is generally due by the 11th of the following month, and GSTR-3B (summary and payment) by the 20th — as per CBIC notifications.</p><h2>Quarterly (QRMP) filers</h2><p>Small taxpayers under the Quarterly Return Monthly Payment scheme file GSTR-1 and GSTR-3B quarterly, with GSTR-3B due on the 22nd or 24th of the month following the quarter depending on the state group, while paying tax monthly.</p><h2>Annual return</h2><p>The annual return GSTR-9 is generally due by 31 December of the following financial year, where applicable.</p>",
        "faqs": [
            ("What is the GSTR-3B due date?", "For monthly filers, GSTR-3B is generally due by the 20th of the following month. QRMP/quarterly filers follow staggered dates (22nd or 24th) by state group, as per CBIC."),
            ("When is GSTR-1 due?", "For monthly filers, GSTR-1 is generally due by the 11th of the following month."),
            ("When is the GST annual return due?", "GSTR-9, where applicable, is generally due by 31 December of the following financial year."),
        ],
        "source": 'Source: CGST Act, 2017 and CBIC — <a href="https://www.gst.gov.in" rel="nofollow">gst.gov.in</a>. Due dates can change by notification; confirm current dates each cycle.',
        "cta": "/services/gst-return-filing/", "cta_label": "See our GST return filing service",
    },
    {
        "slug": "tds-due-dates", "card": "TDS payment & return due dates", "crumb": "TDS due dates",
        "headline": "TDS payment and return due dates",
        "h1": "TDS payment and return due dates",
        "title": "TDS Due Dates: Payment & Return Filing | DPS & Co",
        "desc": "TDS due dates: deposit by the 7th of the next month; quarterly returns by 31 Jul, 31 Oct, 31 Jan and 31 May.",
        "lede": "TDS deducted is generally deposited by the 7th of the following month. Quarterly TDS returns are generally due on 31 July, 31 October, 31 January, and 31 May.",
        "body": "<h2>When must TDS be deposited?</h2><p>TDS deducted is generally payable by the 7th of the following month, with a separate date for March (generally 30 April) — as per the Income Tax Act, 1961.</p><h2>Quarterly return due dates</h2><p>Returns (Form 24Q / 26Q) are generally due as follows: Q1 (April–June) by 31 July; Q2 (July–September) by 31 October; Q3 (October–December) by 31 January; Q4 (January–March) by 31 May.</p><h2>TDS certificates</h2><p>Form 16 (salary) is generally issued by 15 June after the financial year; Form 16A (non-salary) is issued quarterly.</p>",
        "faqs": [
            ("When must TDS be deposited?", "TDS deducted is generally required to be deposited by the 7th of the following month, with a separate date for March, as per the Income Tax Act, 1961."),
            ("What are the TDS return due dates?", "Quarterly TDS returns are generally due on 31 July, 31 October, 31 January, and 31 May for Q1 to Q4 respectively."),
        ],
        "source": 'Source: Income Tax Act, 1961 and CBDT — <a href="https://www.incometax.gov.in" rel="nofollow">incometax.gov.in</a> / TRACES. Confirm current dates before filing.',
        "cta": "/services/tds-return-filing/", "cta_label": "See our TDS return filing service",
    },
]


def build_article(a: dict) -> None:
    d = a.get("date", TODAY)
    crumbs_html, crumbs_schema = breadcrumbs(
        [("Home", "/"), ("Resources", "/resources/"), (a["crumb"], "")])
    faq_html, faq_schema = faq_section([tuple(x) for x in a["faqs"]])
    article_schema = {
        "@context": "https://schema.org", "@type": "Article", "headline": a["headline"],
        "datePublished": d, "dateModified": d,
        "author": {"@type": "Organization", "name": SITE["name"]},
        "publisher": {"@type": "Organization", "name": SITE["name"]},
        "url": SITE["domain"] + f"/resources/{a['slug']}/",
    }
    body = crumbs_html + f"""
<h1>{a['h1']}</h1>
<p class="updated">Last updated: {d}</p>
<p class="lede">{a['lede']}</p>
{a['body']}
{faq_html}
<p class="src">{a['source']}</p>
<p><a class="cta-btn" href="{a['cta']}">{a['cta_label']}</a></p>
"""
    page(f"resources/{a['slug']}", a["title"], a["desc"], body,
         [article_schema, faq_schema, crumbs_schema], active="Resources")


def _svg(inner: str) -> str:
    return ('<svg class="ic-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + inner + "</svg>")


# Lucide-style inline SVG icons (no emojis).
ICONS = {
    "trending-up": _svg('<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>'),
    "receipt": _svg('<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1Z"/><path d="M8 7h8M8 11h8M8 15h5"/>'),
    "scale": _svg('<path d="M12 3v18"/><path d="M6 7h12"/><path d="m4 7 3 7H1l3-7Z"/><path d="m20 7 3 7h-6l3-7Z"/><path d="M7 21h10"/>'),
    "shield-check": _svg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>'),
    "building": _svg('<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4M10 10h4M10 14h4M10 18h4"/>'),
    "landmark": _svg('<line x1="3" y1="22" x2="21" y2="22"/><line x1="6" y1="18" x2="6" y2="11"/><line x1="10" y1="18" x2="10" y2="11"/><line x1="14" y1="18" x2="14" y2="11"/><line x1="18" y1="18" x2="18" y2="11"/><polygon points="12 2 20 7 4 7"/>'),
    "monitor": _svg('<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>'),
    "factory": _svg('<path d="M2 20h20V8l-6 4V8l-6 4V4H2v16Z"/><path d="M6 16h.01M10 16h.01M14 16h.01M18 16h.01"/>'),
    "plane": _svg('<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2Z"/>'),
    "shield": _svg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>'),
    "zap": _svg('<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'),
    "truck": _svg('<path d="M10 17h4V5H2v12h3"/><path d="M20 17h2v-3.34a4 4 0 0 0-1.17-2.83L19 9h-5v8h1"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>'),
    "gem": _svg('<path d="M6 3h12l4 6-10 13L2 9Z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/>'),
    "shirt": _svg('<path d="M20.4 3.5 16 2a4 4 0 0 1-8 0L3.6 3.5a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.17a1 1 0 0 0 .99-.84l.58-3.47A2 2 0 0 0 20.4 3.5Z"/>'),
    "cog": _svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 2.6 1.65 1.65 0 0 0 10 1.09V1a2 2 0 0 1 4 0v.09A1.65 1.65 0 0 0 15 2.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 21.4 7H22a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/>'),
    "heart-pulse": _svg('<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.29 1.51 4.04 3 5.5l7 7Z"/><path d="M3.2 12H9l.5-1 2 4.5 2-7 1.5 3.5h4.3"/>'),
}

PRACTICES = [
    {
        "slug": "advisory", "name": "Advisory", "eyebrow": "Strategy & finance", "icon": ICONS["trending-up"],
        "title": "Advisory Services in Mumbai | DPS & Co",
        "desc": "Business advisory, management consultancy, transaction support, due diligence and CFO services in Mumbai.",
        "intro": "Our advisory practice supports business decisions beyond compliance — from structuring and tax efficiency within the law to transaction support and outsourced finance leadership.",
        "items": [("Business Advisory", "/services/business-advisory/"), ("Management Consultancy", ""),
                   ("Tax Optimization", ""), ("Transaction Support", ""), ("Due Diligence", ""),
                   ("CFO Services", "/services/business-advisory/")],
        "related": [("Business Advisory", "/services/business-advisory/"), ("Company Incorporation", "/services/company-incorporation/")],
    },
    {
        "slug": "tax-regulatory", "name": "Tax & Regulatory", "eyebrow": "Direct & indirect tax", "icon": ICONS["receipt"],
        "title": "Tax & Regulatory Services in Mumbai | DPS & Co",
        "desc": "Direct and indirect tax advisory, GST and income tax compliance, company law and outsourcing in Mumbai.",
        "intro": "We handle the full direct and indirect tax lifecycle — advisory, planning, and routine compliance — alongside company law and outsourcing support.",
        "items": [("Direct Tax Advisory", "/services/income-tax-filing/"), ("Indirect Tax Advisory (GST)", "/services/gst-registration/"),
                   ("Tax Planning", ""), ("Tax Compliance (GST & TDS)", "/services/gst-return-filing/"),
                   ("Company Law Services", "/services/company-incorporation/"), ("Accounting & Outsourcing", "/services/accounting-outsourcing/")],
        "related": [("GST Registration", "/services/gst-registration/"), ("Income Tax Filing", "/services/income-tax-filing/"), ("TDS Return Filing", "/services/tds-return-filing/")],
    },
    {
        "slug": "litigation", "name": "Litigation Support", "eyebrow": "Disputes & representation", "icon": ICONS["scale"],
        "title": "Tax Litigation Support in Mumbai | DPS & Co",
        "desc": "Support for direct and indirect tax disputes — strategy, drafting, filing and representation — in Mumbai.",
        "intro": "We support clients through tax disputes end to end: framing strategy, drafting and filing submissions, and appearing before the authorities, coordinating with counsel where matters go beyond a Chartered Accountant's scope.",
        "items": [("Direct Tax Litigation Support", "/services/tax-litigation/"), ("Indirect Tax Litigation Support", "/services/tax-litigation/"),
                   ("Framing Strategy", ""), ("Drafting & Filing", ""), ("Appearance", ""), ("Coordinating with Counsels", "")],
        "related": [("Tax Litigation Support", "/services/tax-litigation/"), ("Income Tax Filing", "/services/income-tax-filing/")],
    },
    {
        "slug": "audit-assurance", "name": "Audit & Assurance", "eyebrow": "Independent assurance", "icon": ICONS["shield-check"],
        "title": "Audit & Assurance Services in Mumbai | DPS & Co",
        "desc": "Statutory and tax audit, internal audit, IFC review, inspections, compliance and stock audit in Mumbai.",
        "intro": "Our assurance practice provides independent examination and review — statutory and tax audit, internal audit, and specialised reviews — each scoped to the applicable law.",
        "items": [("Statutory / Tax Audit", "/services/audit-assurance/"), ("Internal Audit", "/services/audit-assurance/"),
                   ("Internal Financial Controls Review", ""), ("Inspections", ""), ("Compliance Audits", ""), ("Stock Audit", "")],
        "related": [("Audit & Assurance", "/services/audit-assurance/"), ("Business Advisory", "/services/business-advisory/")],
    },
]

INDUSTRIES = [
    ("Real Estate & Infrastructure", ICONS["building"], "Developers, contractors, and infrastructure projects."),
    ("Financial Services", ICONS["landmark"], "NBFCs, intermediaries, and finance businesses."),
    ("Information Technology", ICONS["monitor"], "IT, software, and technology-enabled services."),
    ("Manufacturing", ICONS["factory"], "Manufacturers across industrial and consumer goods."),
    ("Travel & Tourism", ICONS["plane"], "Travel, hospitality, and tourism operators."),
    ("Insurance", ICONS["shield"], "Insurers and insurance intermediaries."),
    ("Power & Energy", ICONS["zap"], "Power generation, distribution, and energy."),
    ("Logistics", ICONS["truck"], "Logistics, transport, and supply-chain businesses."),
    ("Gems & Jewellery", ICONS["gem"], "Gems, jewellery, and allied trades."),
    ("Textiles", ICONS["shirt"], "Textile manufacturing and trading."),
    ("Engineering & Technology", ICONS["cog"], "Engineering, EPC, and technology firms."),
    ("Healthcare & Hospitality", ICONS["heart-pulse"], "Healthcare providers and hospitality businesses."),
]


def build_practice(p: dict) -> None:
    crumbs_html, crumbs_schema = breadcrumbs([("Home", "/"), ("Practices", "/practices/"), (p["name"], "")])
    items = "".join(
        (f'<li><a href="{u}">{l}</a></li>' if u else f"<li>{l}</li>") for l, u in p["items"])
    related = "".join(f'<a class="tile" href="{u}"><h3>{l}</h3><p>View service &rsaquo;</p></a>' for l, u in p["related"])
    body = crumbs_html + f"""
<p class="eyebrow">{p['eyebrow']}</p>
<h1>{p['name']} services in Mumbai</h1>
<p class="lede">{p['intro']}</p>
<h2>What this practice covers</h2>
<ul class="ticks">{items}</ul>
<h2>Related services</h2>
<div class="grid cols-3">{related}</div>
<div class="ctaband"><h2>Discuss your requirement</h2><p>Tell us what you need and we'll point you to the right service and team.</p><a class="cta-btn" href="/contact/">Contact us</a></div>
"""
    service_schema = {
        "@context": "https://schema.org", "@type": "Service", "name": p["name"],
        "provider": {"@type": "AccountingService", "name": SITE["name"], "url": SITE["domain"]},
        "areaServed": SITE["areas"], "url": SITE["domain"] + f"/practices/{p['slug']}/", "description": p["desc"],
    }
    page(f"practices/{p['slug']}", p["title"], p["desc"], body,
         [service_schema, crumbs_schema], active="Practices")


# ------------------------------- the build --------------------------------

def build() -> None:
    # Tolerant clean: build even while a preview server (http.server) holds the dir.
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    # assets (overwrite if present)
    shutil.copytree(os.path.join(os.path.dirname(OUT), "assets"), os.path.join(OUT, "assets"), dirs_exist_ok=True)

    # --- Home ---
    hero = f"""<section class="hero"><div class="wrap">
      <p class="eyebrow">Tax &middot; Audit &middot; Advisory</p>
      <h1>Chartered Accountants in Mumbai</h1>
      <p>{SITE['name']} works with businesses and individuals across {", ".join(SITE['areas'])} — combining technical depth with a partner-led, personal approach.</p>
      <div class="actions"><a class="cta-btn" href="/practices/">Explore our practices</a><a class="ghost" href="/contact/">Talk to us</a></div>
      <div class="stat-cards">
        <div class="stat"><div class="n">{SITE['founded']}</div><div class="l">Year established</div></div>
        <div class="stat"><div class="n">39+ yrs</div><div class="l">Founding partner experience</div></div>
        <div class="stat"><div class="n">5</div><div class="l">Partners</div></div>
        <div class="stat"><div class="n">Mumbai</div><div class="l">Thane &amp; Navi Mumbai</div></div>
      </div>
    </div></section>"""
    practice_tiles = "".join(
        f'<a class="tile" href="/practices/{p["slug"]}/"><div class="ic">{p["icon"]}</div><h3>{p["name"]}</h3><p>{p["desc"]}</p></a>'
        for p in PRACTICES)
    home_body = f"""
<section><p class="eyebrow">What we do</p><h2>Our practice areas</h2>
<p class="lede">Four practice areas, each with focused services beneath it.</p>
<div class="grid cols-2" style="margin-top:20px">{practice_tiles}</div>
<p style="margin-top:18px"><a class="more" href="/services/">Browse all services &rsaquo;</a></p>
</section>
<section class="trust" style="margin:48px -22px 0"><div class="wrap"><div class="grid">
  <div><div class="n">{SITE['founded']}</div><div class="muted">Established</div></div>
  <div><div class="n">ICAI</div><div class="muted">Chartered Accountants</div></div>
  <div><div class="n">5</div><div class="muted">Partners</div></div>
  <div><div class="n">Mumbai</div><div class="muted">{", ".join(SITE['areas'])}</div></div>
</div></div></section>
<section style="margin-top:48px"><p class="eyebrow">Sectors</p><h2>Industries we serve</h2>
<p class="lede">We work with clients across real estate, financial services, IT, manufacturing, and more.</p>
<p style="margin-top:10px"><a class="more" href="/industries/">See all industries &rsaquo;</a></p></section>
<div class="ctaband"><h2>Let's talk</h2><p>Tell us about your business and the support you need. We serve clients across {", ".join(SITE['areas'])}.</p><a class="cta-btn" href="/contact/">Contact us</a></div>
"""
    local_schema = {**ORG_SCHEMA, "@type": ["AccountingService", "LocalBusiness"]}
    page("", "Chartered Accountants in Mumbai | DPS & Co",
         "Mumbai Chartered Accountants offering GST, income tax, company incorporation, audit and advisory. Established 2016. Contact us.",
         home_body, [local_schema], active="Home", hero=hero)

    # --- Practices index + practice pages ---
    p_tiles = "".join(
        f'<a class="tile" href="/practices/{p["slug"]}/"><div class="ic">{p["icon"]}</div><h3>{p["name"]}</h3><p>{p["desc"]}</p></a>'
        for p in PRACTICES)
    pi_html, pi_schema = breadcrumbs([("Home", "/"), ("Practices", "")])
    page("practices", "Practice Areas | DPS & Co Chartered Accountants, Mumbai",
         "Our practice areas: Advisory, Tax & Regulatory, Litigation Support, and Audit & Assurance — for Mumbai businesses.",
         pi_html + '<p class="eyebrow">What we do</p><h1>Our practice areas</h1>'
         + '<p class="lede">Four practice areas covering the full range of tax, audit, assurance, and advisory work, with focused services under each.</p>'
         + f'<div class="grid cols-2" style="margin-top:22px">{p_tiles}</div>', [pi_schema], active="Practices")
    for p in PRACTICES:
        build_practice(p)

    # --- Industries ---
    ind_tiles = "".join(
        f'<div class="tile"><div class="ic">{ic}</div><h3>{n}</h3><p>{b}</p></div>' for n, ic, b in INDUSTRIES)
    ii_html, ii_schema = breadcrumbs([("Home", "/"), ("Industries", "")])
    page("industries", "Industries We Serve | DPS & Co Chartered Accountants, Mumbai",
         "DPS & Co serves clients across real estate, financial services, IT, manufacturing, and many other sectors in Mumbai.",
         ii_html + '<p class="eyebrow">Sectors</p><h1>Industries we serve</h1>'
         + '<p class="lede">We have experience advising clients across a broad range of sectors in Mumbai, Thane, and Navi Mumbai.</p>'
         + f'<div class="grid cols-3" style="margin-top:22px">{ind_tiles}</div>'
         + '<div class="ctaband"><h2>Work in one of these sectors?</h2><p>Get in touch to discuss tax, audit, or advisory support for your business.</p><a class="cta-btn" href="/contact/">Contact us</a></div>',
         [ii_schema], active="Industries")

    # --- Services index ---
    cards = "".join(
        f'<a class="card cardlink" href="/services/{s["slug"]}/"><h3>{s["nav"]}</h3><p class="muted">{s["desc"]}</p><span class="more">Learn more &rsaquo;</span></a>'
        for s in SERVICES)
    sc_html, sc_schema = breadcrumbs([("Home", "/"), ("Services", "")])
    page("services", "Services | DPS & Co Chartered Accountants, Mumbai",
         "GST, income tax, company incorporation, audit and assurance, and business advisory services in Mumbai.",
         sc_html + "<h1>Our services</h1><p class='lede'>Compliance and advisory services for businesses and individuals in Mumbai. Choose a service to see the process, documents, and timelines.</p>"
         + f'<div class="grid cols-2">{cards}</div>', [sc_schema], active="Services")

    for s in SERVICES:
        build_service(s)

    # --- About / Team ---
    partners = [
        ("CA Dhirendra Sangoi", "Founding &amp; Managing Partner", "Chartered Accountant (ICAI) &middot; 39+ years in practice", "Assurance, tax &amp; advisory"),
        ("CA Shreyas Sangoi", "Partner", "Chartered Accountant (ICAI) &middot; Accredited GST Trainer (NACIN)", "Indirect tax (GST)"),
        ("CA Vishesh Sangoi", "Partner", "Chartered Accountant (ICAI)", "Direct tax &amp; advisory"),
        ("CA Nilesh Gada", "Partner", "Chartered Accountant (ICAI) &middot; 21+ years with the firm", "Audit &amp; assurance"),
        ("CA Mittal Gala", "Partner &amp; Operations Head", "Chartered Accountant (ICAI) &middot; with the firm since 2007", "Operations &amp; compliance"),
    ]
    team_cards = "".join(
        f'<div class="card"><h3>{n}</h3><p class="muted">{role} &middot; {cred}</p><p>Specialisation: {spec}</p></div>'
        for n, role, cred, spec in partners)
    person_schemas = [{
        "@context": "https://schema.org", "@type": "Person", "name": n, "jobTitle": role,
        "worksFor": {"@type": "AccountingService", "name": SITE["name"]},
        "hasCredential": {"@type": "EducationalOccupationalCredential",
                          "credentialCategory": "ICAI Membership", "name": cred},
    } for n, role, cred, spec in partners]
    ab_html, ab_schema = breadcrumbs([("Home", "/"), ("About", "")])
    about_body = ab_html + f"""
<h1>About {SITE['name']}</h1>
<p class="lede">DPS &amp; Co is a Mumbai-based Chartered Accountancy firm in practice since {SITE['founded']}, offering tax, audit, assurance, and advisory services to businesses and individuals.</p>
<p>The firm is a multi-disciplinary practice with partners and a team of qualified professionals across direct tax, indirect tax (GST), audit and assurance, company law, litigation support, and advisory. The founding partner has over 39 years of professional experience. We work with clients across a range of sectors in Mumbai, Thane, and Navi Mumbai.</p>
<h2>Our partners</h2>
<div class="grid cols-3">{team_cards}</div>
<p class="muted">ICAI membership numbers can be added to each partner profile where required.</p>
<h2>Areas of specialisation</h2>
<ul class="ticks"><li>Direct taxation and income tax</li><li>Indirect taxation (GST)</li><li>Statutory, tax and internal audit</li><li>Company law and incorporation</li><li>Business and transaction advisory</li></ul>
"""
    page("about", "About & Team | DPS & Co Chartered Accountants, Mumbai",
         "DPS & Co is a Mumbai Chartered Accountancy firm in practice since 1981. Meet the partners and learn about our areas of specialisation.",
         about_body, [ab_schema] + person_schemas, active="About")

    # --- Resources index + articles (curated + approved auto-blog posts) ---
    all_articles = ARTICLES + load_posts()
    rc_html, rc_schema = breadcrumbs([("Home", "/"), ("Resources", "")])
    art_cards = "".join(
        f'<a class="card cardlink" href="/resources/{a["slug"]}/"><h3>{a["card"]}</h3>'
        f'<p class="muted">{a["desc"]}</p><span class="more">Read &rsaquo;</span></a>'
        for a in all_articles)
    page("resources", "Resources | DPS & Co Chartered Accountants, Mumbai",
         "Tax and compliance notes for Mumbai businesses and individuals — ITR, GST and TDS due dates, and more.",
         rc_html + '<h1>Resources</h1><p class="lede">Plain-language notes on tax and compliance for Mumbai businesses and individuals. We review these at least once a year, after the Union Budget.</p>'
         + f'<div class="grid cols-2">{art_cards}</div>', [rc_schema], active="Resources")
    for a in all_articles:
        build_article(a)

    # --- Contact ---
    co_html, co_schema = breadcrumbs([("Home", "/"), ("Contact", "")])
    contact_body = co_html + f"""
<h1>Contact us</h1>
<p class="lede">Get in touch to discuss GST, income tax, incorporation, audit, or advisory for your business. We serve clients across {", ".join(SITE['areas'])}.</p>
<div class="grid cols-2">
  <div>
    <h2>Office</h2>
    <p>{SITE['name']}<br>{SITE['street']}<br>{SITE['locality']}, {SITE['region']} {SITE['postal']}</p>
    <p><strong>Phone:</strong> {SITE['phone']} / 14 / 15 &middot; {SITE['phone_alt']}<br><strong>Email:</strong> {SITE['email']}</p>
    <p class="muted">Serving Mumbai, Thane, and Navi Mumbai.</p>
    <iframe title="Office location" src="{SITE['maps_embed']}" width="100%" height="260" style="border:0;border-radius:12px" loading="lazy"></iframe>
  </div>
  <div>
    <h2>Send an enquiry</h2>
    <form class="enquiry" action="#" method="post" aria-label="Enquiry form">
      <label>Name <input type="text" name="name" required></label>
      <label>Email <input type="email" name="email" required></label>
      <label>Phone <input type="tel" name="phone"></label>
      <label>How can we help? <textarea name="message" rows="4" required></textarea></label>
      <button class="cta-btn" type="submit">Send enquiry</button>
      <p class="muted">This form is a placeholder — connect it to your email/CRM before launch.</p>
    </form>
  </div>
</div>
"""
    page("contact", "Contact | DPS & Co Chartered Accountants, Mumbai",
         "Contact DPS & Co, Chartered Accountants in Mumbai, for GST, income tax, incorporation, audit and advisory. Phone, email and office address.",
         contact_body, [co_schema, {**ORG_SCHEMA, "@type": ["AccountingService", "LocalBusiness"]}], active="Contact")

    # --- 404 ---
    page_404 = """<h1>Page not found</h1><p class="lede">Sorry, that page doesn't exist.</p>
<ul class="ticks"><li><a href="/">Go to the home page</a></li><li><a href="/services/">Browse our services</a></li><li><a href="/contact/">Contact us</a></li></ul>"""
    # 404 lives at dist/404.html (not a folder)
    _write_404(page_404)

    _write_robots()
    _write_llms()
    _write_sitemap()
    print(f"Built site into {OUT}")


def _write_404(body_inner: str) -> None:
    # Reuse the template but write to /404.html
    tmp = "__404tmp__"
    page(tmp, "Page not found | DPS & Co", "The page you requested could not be found.", body_inner, [])
    src = os.path.join(OUT, tmp, "index.html")
    with open(src, encoding="utf-8") as f:
        html = f.read()
    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8") as f:
        f.write(html)
    shutil.rmtree(os.path.join(OUT, tmp))


def _all_paths() -> list[str]:
    paths = ["", "practices", "industries", "services", "about", "resources", "contact"]
    paths += [f"practices/{p['slug']}" for p in PRACTICES]
    paths += [f"services/{s['slug']}" for s in SERVICES]
    paths += [f"resources/{a['slug']}" for a in ARTICLES]
    paths += [f"resources/{a['slug']}" for a in load_posts()]
    return paths


def _write_sitemap() -> None:
    urls = "".join(
        f"<url><loc>{SITE['domain']}/{p + '/' if p else ''}</loc><lastmod>{TODAY}</lastmod></url>"
        for p in _all_paths())
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)


def _write_robots() -> None:
    crawlers = ["GPTBot", "PerplexityBot", "ClaudeBot", "Google-Extended", "OAI-SearchBot", "Applebot-Extended"]
    allow_ai = "\n\n".join(f"User-agent: {c}\nAllow: /" for c in crawlers)
    txt = (f"User-agent: *\nAllow: /\n\n{allow_ai}\n\nSitemap: {SITE['domain']}/sitemap.xml\n")
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(txt)


def _write_llms() -> None:
    txt = f"""# {SITE['name']}

> A Chartered Accountancy firm in Mumbai, India, in practice since {SITE['founded']}, offering tax, audit, assurance, and advisory services to businesses and individuals across Mumbai, Thane, and Navi Mumbai.

## Services
- [GST Registration]({SITE['domain']}/services/gst-registration/): GST registration and compliance for Mumbai businesses.
- [Income Tax Filing]({SITE['domain']}/services/income-tax-filing/): ITR preparation and filing for individuals and businesses.
- [Company Incorporation]({SITE['domain']}/services/company-incorporation/): Private limited, LLP and OPC formation.
- [Audit & Assurance]({SITE['domain']}/services/audit-assurance/): Statutory, tax and internal audit.
- [Business Advisory]({SITE['domain']}/services/business-advisory/): Tax planning, transaction support and CFO services.

## Key pages
- [About & Team]({SITE['domain']}/about/)
- [Resources]({SITE['domain']}/resources/)
- [Contact]({SITE['domain']}/contact/)

## Contact
Phone: {SITE['phone']} — Email: {SITE['email']} — Location: {SITE['locality']}, {SITE['region']}, India
"""
    with open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(txt)


if __name__ == "__main__":
    build()
