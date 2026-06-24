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

## Email approval automation (`email_blog/`)

Sends the current blog (`email_blog/blog.json`) to a reviewer by email for approval, then
**publishes it to the site on a "yes"**. Generation (above) is optional and separate; this
module handles the approve → publish → deploy step.

- **Send (SMTP):** emails `blog.json` to the reviewer with the subject "Weekly DPS Website Blog Check".
- **Replies (IMAP):** `--check-replies` reads the reviewer's reply — `yes`/`ok` → **approved**,
  `no` → rejected, a text/JSON **attachment** → corrected.
- **Publish:** on approval it converts the blog into the site's post schema, writes
  `src/content/posts/<slug>.json`, then **commits and pushes** so Cloudflare redeploys.

```powershell
cd email_blog
py -m pip install cryptography
py blogchecker.py --encrypt          # one-time: store the Gmail App Password (encrypted)
.\run.ps1 --once                     # send one approval email
.\run.ps1 --check-replies            # act on replies (schedule this, e.g. daily)
```

Notes:
- **Credentials never go in git.** The Gmail **App Password** is Fernet-encrypted in
  `app_password.enc` (git-ignored); the key lives only in the `BLOG_FERNET_KEY` environment
  variable. (For quick tests you can set `SENDER_APP_PASSWORD` and move `app_password.enc` aside.)
- **Run the scheduled job on a `main` checkout** — publishing commits to the current branch, and
  only `main` deploys. Set `BLOG_PUBLISH_GIT=0` to write a post without committing (testing).
- Schedule `--once` (send) and `--check-replies` (act) with Windows Task Scheduler.

## Deployment (Cloudflare)

The static build (`dist/`) is served by Cloudflare Workers static assets, configured in
[`wrangler.jsonc`](wrangler.jsonc). For the deploy to succeed, set these once in the Cloudflare
project dashboard (Workers & Pages → `dpsca-website` → Settings → Build):

- **Build command:** `npm install && npm run build`  *(required — produces `dist/`)*
- **Deploy command:** `npx wrangler versions upload`  *(already set)*
- **Branch control:** Production branch = `main`; **disable non-production / preview branch
  builds** so feature branches (e.g. `blog_email`) don't trigger failing builds.

End-to-end flow: the email tool publishes an approved post to `main` → Cloudflare runs the build
→ uploads `dist/` → the post is live at `dpsca.in/resources/<slug>/`.

## Notes before go-live

- Verify the firm email and the Google Maps embed URL in `src/data/site.js`.
- The contact form in `src/pages/contact.astro` is a placeholder — wire it to email/CRM.
- Set the production domain in `astro.config.mjs` (`site`) — currently `https://dpsca.in`.
