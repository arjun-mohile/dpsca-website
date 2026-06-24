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

## Weekly blog workflow (generate → email-approve → publish)

The blog is fully chained: an AI **generates** a draft, it's **emailed to a partner
for approval**, and a one-word reply **publishes it live**. Nothing goes on the site
without a human "yes".

```
[1] blog_pipeline.py generate   ──>  writes email_blog/blog.json   (OpenRouter, keyword-driven topic)
[2] email_blog  --once          ──>  emails that post to the partner for approval
[3] partner replies "yes"       ──>  email_blog --check-replies publishes it -> git push -> Cloudflare redeploys
```

### 1. Generate (OpenRouter, keyword-driven)

`blog_pipeline.py` picks a fresh topic and writes a short, ICAI-compliant post into
`email_blog/blog.json` (the file the approval email reads). Topic selection is
keyword-driven: it pulls trending India finance terms from Google Trends (optional
`pytrends`) and keeps only on-topic ones using a keyword filter (gst, income tax,
tds, audit, msme, capital gain…), falling back to a curated list of ~20 evergreen
CA topics. Topics already drafted or published are skipped, so it never repeats.

```bash
py blog_pipeline.py generate          # pick a topic, write email_blog/blog.json
py blog_pipeline.py list              # show the queued post + published posts
```

Set `OPENROUTER_API_KEY` (and optional `MODEL`) in `.env` (copy from `.env.example`).
`.env` is git-ignored — never commit real keys.

> The legacy local-review commands (`approve <slug>` / `reject <slug>`) still operate
> on `./drafts` for anyone who prefers approving on disk instead of by email.

### 2 & 3. Email approval + auto-publish

The approval loop lives in `email_blog/` (see `email_blog/` for full setup). In short:

```bash
cd email_blog
.\run.ps1 --once            # email the current blog.json to the partner for approval
.\run.ps1 --check-replies   # read the reply: "yes" publishes, "no" skips, a .txt attachment replaces the post
```

On approval the post is written to `src/content/posts/<slug>.json`, committed and
pushed; Cloudflare redeploys the live site automatically.

One-time setup for the email step: `py email_blog/blogchecker.py --encrypt` (store the
Gmail App Password), then `setx BLOG_FERNET_KEY "<key>"`.

### Make it fully hands-off

Register the schedules once and the whole chain runs unattended:

```powershell
# weekly generation (Monday 8am): writes a fresh email_blog/blog.json
$a = New-ScheduledTaskAction -Execute "py" -Argument "blog_pipeline.py generate" -WorkingDirectory "D:\dpsca-astro"
Register-ScheduledTask -TaskName "DPS Blog - Generate" -Action $a `
  -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am)

# weekly send (Monday 9am) + reply-check (every 30 min): publishes on approval
cd email_blog ; .\schedule.ps1
```

Result: every Monday a new draft is generated at 8am, emailed at 9am, and the
partner's "yes" reply (or a `.txt` edit) goes live within ~30 minutes — no manual steps.

## Notes before go-live

- Verify the firm email and the Google Maps embed URL in `src/data/site.js`.
- The contact form in `src/pages/contact.astro` is a placeholder — wire it to email/CRM.
- Set the production domain in `astro.config.mjs` (`site`) — currently `https://dpsca.in`.
