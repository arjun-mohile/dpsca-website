# DPS & Co — Website (SEO + AEO build)

A fast, static, SEO/AEO-optimized site for DPS & Co, Chartered Accountants, Mumbai —
a revamp of dpsca.in. Plain static HTML (no framework), generated from one Python script.

## Build & preview
```bash
cd "D:\dpsca website"
py build.py                     # generates ./dist (HTML + sitemap.xml + robots.txt + llms.txt)
cd dist && py -m http.server 8080
# open http://localhost:8080/
```
Edit content in `build.py`, edit styling in `assets/styles.css`, then re-run `py build.py`.

## What's included
- **Pages (flat URLs):** `/`, `/services/`, 5 service pages (`/services/gst-registration/`, `…/income-tax-filing/`, `…/company-incorporation/`, `…/audit-assurance/`, `…/business-advisory/`), `/about/`, `/resources/` + 1 article, `/contact/`, and a `404.html`.
- **Per-page JSON-LD:** AccountingService + LocalBusiness (home/contact), Service (each service), FAQPage (every FAQ block, mirroring visible text), BreadcrumbList, Person (team), Article (blog).
- **SEO:** semantic HTML, one `<h1>`/page, canonical tags, title `{Service} in {Location} | {Firm}` (<60 chars), meta descriptions (<155), internal links between services + contact.
- **AEO:** answer-first first paragraph, question-style subheadings, short paragraphs, specific figures with **inline sources** (CGST Act / Income Tax Act / MCA + official portal links), "Last updated" stamp on the tax article, FAQ blocks.
- **Crawlability:** auto-generated `sitemap.xml`, `robots.txt` (standard + AI crawlers: GPTBot, PerplexityBot, ClaudeBot, Google-Extended, OAI-SearchBot, Applebot-Extended), and a root `llms.txt`.
- **Performance:** system fonts (no web-font fetch), no render-blocking JS (deferred), lazy-loaded map iframe, mobile-first responsive (tested to 360px).

## ⚠️ MUST replace before launch (placeholders in `build.py`, the `SITE` dict)
- **Phone, email, street address, PIN** — must match the Google Business Profile **character-for-character** (NAP consistency).
- **Google Map embed URL** — point to the verified office location.
- **Partner names + ICAI membership numbers** (in the `build()` function, `partners` list).
- **Contact form** — wire it to your email/CRM (it's currently a placeholder).

## Compliance (ICAI) — needs partner sign-off
Copy is written factually with **no superlatives** ("best/leading/No.1"), **no testimonials**, **no client names**, **no fee amounts**, and **no direct solicitation** — per ICAI's Code of Ethics. Before launch, the firm's compliance-responsible partner should review all wording. The footer carries an information-only / non-solicitation note.

## Deploy
`dist/` is a plain static site — host it on Netlify, Cloudflare Pages, GitHub Pages, S3+CloudFront, or any web host. Ensure HTTPS, then submit `https://dpsca.in/sitemap.xml` in Google Search Console.

## Post-launch (from the spec)
- Connect Google Search Console + submit the sitemap; set up GA4 (or a privacy-friendly analytics) with a goal on the contact form.
- Re-run Google's Rich Results Test after any schema change.
- Re-audit tax/regulatory content yearly (after the Union Budget) — update figures and the "Last updated" dates.
