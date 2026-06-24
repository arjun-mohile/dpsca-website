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
- The Gmail account needs **IMAP enabled** for `--check-replies` to read replies.

### Editing the draft by email (reply with a `.txt`)

To change the post, **reply to the approval email and attach a plain-text file** (`.txt`/`.md`).
The reply is treated as a "corrected" submission and published in place of `blog.json`.

Format the file like this — **the first line becomes the blog title** (and the page URL),
then leave a blank line and write the body, separating paragraphs with blank lines:

```
Understanding GST Late Fees

Late filing of GST returns attracts a late fee under the CGST Act...

A second paragraph here...
```

A plain `.txt` produces a basic post (title + paragraphs); for FAQs, a custom description or
sub-headings, attach a **`.json`** file in the post schema instead (same fields as
`src/content/posts/*.json`). Non-text attachments (e.g. `.pdf`, `.docx`) are saved to
`corrected_blogs/` for manual handling and are **not** auto-published.

### Full automation (zero manual steps)

After the one-time encrypted-password setup, register the scheduled tasks so sends and reply
publishing run on their own:

```powershell
cd email_blog
.\schedule.ps1     # registers two Windows scheduled tasks (see below)
```

`schedule.ps1` creates:
- **"DPS Blog Email - Send"** — weekly, runs `run.ps1 --once` (sends the approval email).
- **"DPS Blog Email - Replies"** — every 30 minutes, runs `run.ps1 --check-replies` (reads
  replies and, on approval or a `.txt`/`.json` edit, publishes to the site and pushes → deploys).

Once registered, the loop is fully hands-off: a reply with a `.txt` is picked up within 30
minutes, converted, committed to `main`, and deployed by Cloudflare — it then shows on the site.
Keep this working copy on the **`main`** branch so published posts deploy.

## Deployment (Cloudflare)

The static build (`dist/`) is served by Cloudflare Workers static assets, configured in
[`wrangler.jsonc`](wrangler.jsonc). The build runs **automatically**: a `postinstall` script
(`astro build`) executes during Cloudflare's dependency install, so `dist/` exists before the
deploy command runs — **no "Build command" needs to be set in the dashboard**. The deploy
command `npx wrangler versions upload` (already set) then uploads `dist/`.

Recommended (optional) dashboard setting: under Workers & Pages → `dpsca-website` → Settings →
Build, set the **Production branch to `main`** and **disable non-production / preview branch
builds**, so feature branches (e.g. `blog_email`) don't trigger builds.

End-to-end flow: the email tool publishes an approved post to `main` → Cloudflare installs deps
(which builds `dist/` via `postinstall`) → uploads `dist/` → the post is live at
`dpsca.in/resources/<slug>/`.

> Note: `postinstall` also means a local `npm install` runs a build. If you'd rather avoid that,
> remove the `postinstall` script and instead set the dashboard **Build command** to `npm run build`.

## Notes before go-live

- Verify the firm email and the Google Maps embed URL in `src/data/site.js`.
- The contact form in `src/pages/contact.astro` is a placeholder — wire it to email/CRM.
- Set the production domain in `astro.config.mjs` (`site`) — currently `https://dpsca.in`.
