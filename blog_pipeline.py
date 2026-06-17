"""Weekly auto-blog pipeline for DPS & Co (DRAFT-and-review workflow).

Topics: trending finance/accountancy terms (Google Trends, optional) filtered
against a curated India tax/finance list, with the curated list as fallback.
Generation: OpenRouter (your key). Output: a DRAFT JSON in ./drafts for a partner
to review. Approving moves it to ./src/content/posts where Astro renders it live.

Commands:
    py blog_pipeline.py generate          # create one new draft from a fresh topic
    py blog_pipeline.py list              # show drafts (pending) and published posts
    py blog_pipeline.py approve <slug>    # move a draft -> src/content/posts (then run: npm run build)
    py blog_pipeline.py reject  <slug>    # delete a draft

Config (.env or environment): OPENROUTER_API_KEY, MODEL (default a free model).
"""

import json
import os
import re
import sys
import time
from datetime import date

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS = os.path.join(HERE, "drafts")
POSTS = os.path.join(HERE, "src", "content", "posts")
TODAY = date.today().isoformat()


def _load_env() -> None:
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = os.environ.get("MODEL", "nex-agi/nex-n2-pro:free")

# Curated India accountancy/finance topics (evergreen + seasonal search demand).
CURATED = [
    "GST input tax credit rules", "GSTR-3B late fees and interest", "e-invoicing under GST",
    "new vs old income tax regime", "Section 80C deductions explained", "HRA exemption calculation",
    "advance tax due dates and calculation", "presumptive taxation 44AD and 44ADA",
    "tax audit applicability under 44AB", "capital gains tax on property sale",
    "TDS on rent under section 194I", "Form 26AS and AIS explained",
    "MSME Udyam registration benefits", "LLP vs private limited company",
    "professional tax in Maharashtra", "PF and ESIC compliance for employers",
    "belated and revised income tax return", "GST registration for e-commerce sellers",
    "TDS on purchase of property 194IA", "presumptive scheme for freelancers",
]
# Keywords used to keep trending terms on-topic.
TOPIC_FILTER = ["gst", "income tax", "itr", "tds", "tax", "audit", "msme", "company",
                "llp", "capital gain", "budget", "compliance", "invoice", "deduction",
                "filing", "return", "pf", "esic", "advance tax", "regime"]


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60]


def _existing_slugs() -> set[str]:
    slugs = set()
    for d in (DRAFTS, POSTS):
        if os.path.isdir(d):
            slugs |= {os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".json")}
    return slugs


def _trending_topics() -> list[str]:
    """Try Google Trends (pytrends) for India finance terms; filter to on-topic.
    Returns [] on any failure so the curated list is used."""
    try:
        from pytrends.request import TrendReq
    except Exception:
        return []
    try:
        py = TrendReq(hl="en-IN", tz=330)
        out = []
        for seed in ["income tax", "GST"]:
            py.build_payload([seed], geo="IN", timeframe="now 7-d")
            rq = py.related_queries().get(seed, {})
            rising = rq.get("rising")
            if rising is not None:
                out += [q for q in rising["query"].tolist()]
            time.sleep(1)
        on_topic = [q for q in out if any(k in q.lower() for k in TOPIC_FILTER)]
        return on_topic
    except Exception:
        return []


def _pick_topic() -> str:
    used = _existing_slugs()
    trending = _trending_topics()
    # Prefer a fresh trending on-topic term, else a fresh curated topic.
    for cand in trending + CURATED:
        if _slugify(cand) not in used:
            return cand
    return CURATED[0]


SYSTEM = """You are a Chartered Accountant writing a short, factual blog post for an Indian CA firm's website (audience: Indian business owners and individuals).

STRICT RULES (compliance — ICAI):
- Be factual and neutral. NO superlatives ("best", "leading", "No.1"), NO marketing claims, NO testimonials, NO direct solicitation.
- Cite the relevant law/authority inline where you state a rule (e.g. "as per the Income Tax Act" / "CGST Act" / CBDT / CBIC / MCA).
- Use Indian context, rupees, and current general rules. Do NOT invent specific figures you are unsure of; keep figures general and tell the reader to confirm current rates.
- Answer-first: the first sentence of each section directly answers the heading. Short paragraphs.

Return ONLY a JSON object (no markdown, no prose) with exactly these keys:
{
 "title": "<SEO title under 60 chars, includes the topic>",
 "card": "<short card label>",
 "crumb": "<very short breadcrumb label>",
 "headline": "<article headline>",
 "h1": "<h1, same intent as headline>",
 "desc": "<meta description under 155 chars>",
 "lede": "<one-paragraph answer-first summary>",
 "body": "<HTML using <h2> question-style subheadings and <p> paragraphs; 250-450 words; no <h1>>",
 "faqs": [["Question?", "Answer."], ["Question?", "Answer."], ["Question?", "Answer."]]
}"""


def generate() -> None:
    if not OPENROUTER_KEY:
        print("ERROR: set OPENROUTER_API_KEY in .env"); return
    topic = _pick_topic()
    slug = _slugify(topic)
    print(f"Topic: {topic}\nSlug:  {slug}\nGenerating with {MODEL} ...")
    user = f"Write the blog post about: {topic} (India). Make it genuinely useful and current."
    try:
        resp = httpx.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={"model": MODEL, "temperature": 0.4,
                  "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]},
            timeout=120)
        if resp.status_code != 200:
            print(f"Model error {resp.status_code}: {resp.text[:200]}"); return
        content = resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        print(f"Request failed: {exc}"); return

    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        print("Model did not return JSON. Raw output:\n", content[:400]); return
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        print("Could not parse JSON:", e); return

    # Assemble the draft in the structure Astro expects, plus a compliance footer.
    post = {
        "slug": slug, "date": TODAY,
        "card": data.get("card", topic), "crumb": data.get("crumb", topic[:20]),
        "headline": data.get("headline", topic), "h1": data.get("h1", topic),
        "title": data.get("title", topic)[:60], "desc": data.get("desc", "")[:155],
        "lede": data.get("lede", ""), "body": data.get("body", ""),
        "faqs": data.get("faqs", []),
        "source": "This article is general information, not advice. Tax rules and figures change — confirm current provisions with the official portals (incometax.gov.in / gst.gov.in) or contact us before acting.",
        "cta": "/contact/", "cta_label": "Talk to our team",
        "_status": "DRAFT — needs partner review before publishing",
    }
    os.makedirs(DRAFTS, exist_ok=True)
    out = os.path.join(DRAFTS, f"{slug}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(post, f, indent=2, ensure_ascii=False)
    print(f"\nDRAFT written: {out}")
    print("Review it, edit if needed, then:  py blog_pipeline.py approve", slug)


def list_all() -> None:
    drafts = [f[:-5] for f in os.listdir(DRAFTS)] if os.path.isdir(DRAFTS) else []
    posts = [f[:-5] for f in os.listdir(POSTS)] if os.path.isdir(POSTS) else []
    print("DRAFTS (pending review):")
    for s in drafts: print("  -", s)
    print("PUBLISHED (live after build):")
    for s in posts: print("  -", s)


def approve(slug: str) -> None:
    src = os.path.join(DRAFTS, f"{slug}.json")
    if not os.path.exists(src):
        print("No draft:", slug); return
    with open(src, encoding="utf-8") as f:
        post = json.load(f)
    post.pop("_status", None)
    os.makedirs(POSTS, exist_ok=True)
    with open(os.path.join(POSTS, f"{slug}.json"), "w", encoding="utf-8") as f:
        json.dump(post, f, indent=2, ensure_ascii=False)
    os.remove(src)
    print(f"Approved -> {POSTS}\\{slug}.json\nNow rebuild:  npm run build")


def reject(slug: str) -> None:
    p = os.path.join(DRAFTS, f"{slug}.json")
    if os.path.exists(p):
        os.remove(p); print("Deleted draft:", slug)
    else:
        print("No draft:", slug)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "generate"
    arg = sys.argv[2] if len(sys.argv) > 2 else ""
    {"generate": generate, "list": list_all,
     "approve": lambda: approve(arg), "reject": lambda: reject(arg)}.get(cmd, generate)()
