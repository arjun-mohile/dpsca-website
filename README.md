# DPS & Co — Chartered Accountants, Mumbai

SEO/AEO-optimized website for DPS & Co, built with [Astro](https://astro.build).
Static output: flat URLs, per-page JSON-LD (Organization/LocalBusiness, Service,
FAQPage, BreadcrumbList, Person, Article), canonical tags, auto-generated sitemap,
`robots.txt` (allows AI crawlers) and `llms.txt`.

## Develop

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # outputs static site to dist/
npm run preview    # serve the production build locally
```

## Structure

```
src/
  data/        site config, icons, and content (services, practices, industries, articles)
  layouts/     Base.astro (head, header, footer, JSON-LD)
  components/  Breadcrumbs.astro, Faq.astro
  pages/       file-based routes (services/[slug], practices/[slug], resources/[slug], ...)
  content/posts/   approved blog posts (JSON), rendered under /resources/
public/        styles.css, main.js, robots.txt, llms.txt
```

## Weekly blog workflow (draft → review → publish)

Generates short, ICAI-compliant draft posts from trending/curated finance topics
via OpenRouter. Drafts are **not** auto-published — a partner reviews each one first.

```bash
py blog_pipeline.py generate          # create a draft in drafts/
py blog_pipeline.py list              # list drafts + published posts
py blog_pipeline.py approve <slug>    # move draft -> src/content/posts/
py blog_pipeline.py reject  <slug>    # discard a draft
npm run build                         # rebuild so the new post goes live
```

Set `OPENROUTER_API_KEY` in `.env` (copy from `.env.example`). `.env` is git-ignored.

## Notes before go-live

- Verify the firm email and the Google Maps embed URL in `src/data/site.js`.
- The contact form in `src/pages/contact.astro` is a placeholder — wire it to email/CRM.
- Set the production domain in `astro.config.mjs` (`site`) — currently `https://dpsca.in`.
