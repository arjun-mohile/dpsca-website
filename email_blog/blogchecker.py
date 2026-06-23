"""blogchecker.py — Weekly DPS Website Blog Check.

Sends an email every week to a fixed recipient. The email body is built from
``blog.json`` (placed alongside this script). The subject is always
"Weekly DPS Website Blog Check".

Usage
-----
One-time setup — encrypt your Gmail App Password (prompts securely, nothing is
echoed)::

    python blogchecker.py --encrypt

Run continuously (sends immediately, then once every 7 days)::

    python blogchecker.py

Send a single email and exit (use this with Windows Task Scheduler to run
weekly)::

    python blogchecker.py --once

Check Arjun's replies and act on his verdict (reply "yes" = approve, "no" =
reject, or attach corrected blog text). Run on a schedule, e.g. daily::

    python blogchecker.py --check-replies

Credentials
-----------
* Sender address is fixed below (SENDER_EMAIL).
* The Gmail *App Password* is stored **encrypted** in ``app_password.enc``
  using Fernet (AES-128-CBC + HMAC). It is encrypted by --encrypt and never
  written in plaintext.
* The Fernet key lives in the ``BLOG_FERNET_KEY`` environment variable, kept
  separate from the encrypted file. --encrypt generates one for you the first
  time and tells you how to persist it.

Get a Gmail App Password at https://myaccount.google.com/apppasswords
(a normal Gmail password will not work over SMTP).
"""

import argparse
import email
import getpass
import imaplib
import json
import logging
import os
import re
import smtplib
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler
from pathlib import Path

# --- Fixed settings ---------------------------------------------------------
SENDER_EMAIL = "thalia.tec.blog.ai@gmail.com"
RECIPIENT = "arjun.mohile@gmail.com"
SUBJECT = "Weekly DPS Website Blog Check"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # STARTTLS
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993  # SSL
SCRIPT_DIR = Path(__file__).resolve().parent
BLOG_FILE = SCRIPT_DIR / "blog.json"
SECRET_FILE = SCRIPT_DIR / "app_password.enc"
REPLIES_LOG = SCRIPT_DIR / "replies.log"
CORRECTED_DIR = SCRIPT_DIR / "corrected_blogs"
LOG_FILE = SCRIPT_DIR / "blogchecker.log"
KEY_ENV = "BLOG_FERNET_KEY"
WEEK_SECONDS = 7 * 24 * 60 * 60

# Reply classification keywords (matched against the leading word of the reply).
APPROVE_WORDS = {"yes", "y", "ok", "okay", "approve", "approved", "yep", "yeah"}
REJECT_WORDS = {"no", "n", "reject", "rejected", "nope"}
# Text-like attachment extensions we accept as a "corrected blog".
TEXT_ATTACH_EXTS = {".txt", ".md", ".json", ".text"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # console (stderr) — visible on manual runs
        RotatingFileHandler(      # persistent record — diagnoses scheduled-run failures
            LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        ),
    ],
)
log = logging.getLogger("blogchecker")


# --- Blog body --------------------------------------------------------------
def _format_post(post):
    """Turn one blog entry into readable text. Accepts a dict or a string."""
    if isinstance(post, str):
        return post.strip()

    if isinstance(post, dict):
        title = post.get("title") or post.get("heading")
        date = post.get("date") or post.get("published")
        author = post.get("author")
        # Body text can live under any of these common keys.
        body = (
            post.get("content")
            or post.get("body")
            or post.get("text")
            or post.get("summary")
            or ""
        )
        lines = []
        if title:
            lines.append(str(title))
        meta = " | ".join(str(x) for x in (date, author) if x)
        if meta:
            lines.append(meta)
        if lines:
            lines.append("")  # blank line before body
        lines.append(str(body).strip())
        return "\n".join(lines).strip()

    # Fallback: anything else (numbers, etc.) just stringified.
    return str(post).strip()


def load_blog_body():
    """Read blog.json and return the email body text.

    Tolerant of a few likely shapes:
      * a single object:  {"title": ..., "content": ...}
      * a plain string:   "the blog text"
      * a list of posts:  [ {...}, {...} ]
      * an object wrapping posts: {"blogs": [...]} or {"posts": [...]}

    Raises FileNotFoundError / ValueError on a missing or invalid file so the
    caller can decide whether to skip this run.
    """
    if not BLOG_FILE.exists():
        raise FileNotFoundError(f"{BLOG_FILE} not found")

    with BLOG_FILE.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Unwrap a container object if present.
    if isinstance(data, dict):
        for key in ("blogs", "posts", "entries"):
            if isinstance(data.get(key), list):
                data = data[key]
                break

    if isinstance(data, list):
        if not data:
            raise ValueError("blog.json contains an empty list")
        parts = [_format_post(p) for p in data]
        body = "\n\n---\n\n".join(p for p in parts if p)
    else:
        body = _format_post(data)

    if not body:
        raise ValueError("No blog content could be read from blog.json")
    return body


# --- Encrypted app password -------------------------------------------------
def _get_fernet(key=None):
    """Return a Fernet instance from the given key or BLOG_FERNET_KEY env var."""
    from cryptography.fernet import Fernet  # imported lazily

    key = key or os.environ.get(KEY_ENV)
    if not key:
        raise RuntimeError(
            f"{KEY_ENV} environment variable is not set. Run "
            "`python blogchecker.py --encrypt` first."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def load_app_password():
    """Return the decrypted Gmail app password.

    Primary path: decrypt app_password.enc with the key in BLOG_FERNET_KEY.
    Fallback: a plaintext SENDER_APP_PASSWORD env var (handy for quick tests).
    Returns None (and logs) if no usable credential is found.
    """
    if SECRET_FILE.exists():
        try:
            token = SECRET_FILE.read_bytes()
            return _get_fernet().decrypt(token).decode("utf-8")
        except Exception as exc:  # InvalidToken, missing key, etc.
            log.error("Could not decrypt %s: %s", SECRET_FILE.name, exc)
            return None

    fallback = os.environ.get("SENDER_APP_PASSWORD")
    if fallback:
        log.warning("Using plaintext SENDER_APP_PASSWORD env var (not encrypted).")
        return fallback

    log.error(
        "No app password found. Run `python blogchecker.py --encrypt` to set one."
    )
    return None


def encrypt_password():
    """One-time setup: prompt for the app password and store it encrypted."""
    from cryptography.fernet import Fernet  # imported lazily

    key = os.environ.get(KEY_ENV)
    generated = False
    if not key:
        key = Fernet.generate_key().decode()
        generated = True

    pw = getpass.getpass("Enter the Gmail App Password (input hidden): ").strip()
    if not pw:
        log.error("No password entered; aborting.")
        return 1

    token = _get_fernet(key).encrypt(pw.encode("utf-8"))
    SECRET_FILE.write_bytes(token)
    log.info("Encrypted app password written to %s", SECRET_FILE)

    if generated:
        print("\nA new encryption key was generated. Keep it safe and out of\n"
              "version control. Set it as an environment variable so the\n"
              "script can decrypt the password:\n")
        print("  This session (PowerShell):")
        print(f'    $env:{KEY_ENV} = "{key}"\n')
        print("  Persist for future sessions (PowerShell):")
        print(f'    setx {KEY_ENV} "{key}"\n')
        print("(After `setx`, open a new terminal for it to take effect.)")
    return 0


# --- Email ------------------------------------------------------------------
def send_email(body):
    """Send the weekly email. Returns True on success, False otherwise."""
    password = load_app_password()
    if not password:
        return False

    msg = EmailMessage()
    msg["Subject"] = SUBJECT
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        log.error("Failed to send email: %s", exc)
        return False

    log.info("Email sent from %s to %s", SENDER_EMAIL, RECIPIENT)
    return True


def run_once():
    """Build the body and send a single email. Returns True on success."""
    try:
        body = load_blog_body()
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        log.error("Could not read blog: %s — skipping this send.", exc)
        return False
    return send_email(body)


# --- Website upload (STUB) --------------------------------------------------
def upload_blog(content, source):
    """Placeholder for pushing an approved blog to the website.

    NOT IMPLEMENTED YET — this is the single extension point for the future
    website-upload code. ``source`` is "approved" (Arjun said yes, ``content``
    is the current blog.json text) or "corrected" (``content`` is Arjun's
    attached corrected text).
    """
    length = len(content) if isinstance(content, str) else len(str(content))
    log.info(
        "TODO upload (%s): website upload not yet implemented (blog is %d chars).",
        source, length,
    )
    # Future: publish `content` to the DPS website here.


# --- Reply processing -------------------------------------------------------
_QUOTE_BOUNDARY = re.compile(
    r"^\s*On .+wrote:\s*$"          # Gmail: "On <date> <name> <addr> wrote:"
    r"|^-+\s*Original Message\s*-+" # Outlook-style separator
    r"|^_{5,}\s*$"                   # underscore separator
    r"|^\s*From:\s",                # forwarded/quoted header block
    re.IGNORECASE,
)


def _decode_part(part):
    """Decode a message part's payload to text using its declared charset."""
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:  # unknown charset name
        return payload.decode("utf-8", errors="replace")


def _strip_quoted(text):
    """Return only the new reply text, dropping the quoted original below it."""
    out = []
    for line in text.splitlines():
        if _QUOTE_BOUNDARY.search(line) or line.lstrip().startswith(">"):
            break
        out.append(line)
    return "\n".join(out).strip()


def _extract_reply_text(msg):
    """Pull the plain-text body of a reply, minus quoted history."""
    raw = ""
    if msg.is_multipart():
        for part in msg.walk():
            disp = str(part.get("Content-Disposition", "")).lower()
            if part.get_content_type() == "text/plain" and "attachment" not in disp:
                raw = _decode_part(part)
                break
    else:
        raw = _decode_part(msg)
    return _strip_quoted(raw)


def _get_text_attachment(msg):
    """Return (filename, text_or_None, raw_bytes) for the first attachment.

    ``text`` is the decoded content for text-like attachments (.txt/.md/.json
    or a text/* type), or None for anything else (which is saved raw for manual
    handling). Returns None when the message has no attachment.
    """
    if not msg.is_multipart():
        return None
    for part in msg.walk():
        disp = str(part.get("Content-Disposition", "")).lower()
        if "attachment" not in disp:
            continue
        filename = part.get_filename() or "attachment"
        raw = part.get_payload(decode=True)
        if raw is None:
            continue
        ext = Path(filename).suffix.lower()
        if ext in TEXT_ATTACH_EXTS or part.get_content_type().startswith("text/"):
            return (filename, _decode_part(part), raw)
        log.warning("Attachment '%s' (%s) is not text — will save raw for manual handling.",
                    filename, part.get_content_type())
        return (filename, None, raw)
    return None


def classify_reply(text, has_attachment):
    """Classify a reply as approved / rejected / corrected / unknown."""
    if has_attachment:
        return "corrected"
    words = text.strip().split()
    if not words:
        return "unknown"
    first = words[0].lower().strip(".,!?:;'\"()")
    if first in APPROVE_WORDS:
        return "approved"
    if first in REJECT_WORDS:
        return "rejected"
    return "unknown"


def _save_correction(filename, raw):
    """Save a corrected-blog attachment under CORRECTED_DIR. Returns the path."""
    CORRECTED_DIR.mkdir(exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename) or "correction.txt"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = CORRECTED_DIR / f"{stamp}_{safe}"
    dest.write_bytes(raw)
    log.info("Saved corrected blog attachment to %s", dest)
    return dest


def handle_reply(decision, reply_text, attachment):
    """Act on a classified reply. Returns True if the message should be marked read."""
    if decision == "approved":
        log.info("Reply APPROVED — uploading current blog.")
        try:
            content = load_blog_body()
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            log.error("Approved, but could not read blog.json to upload: %s", exc)
            return True
        upload_blog(content, source="approved")
        return True

    if decision == "rejected":
        log.info("Reply REJECTED — no action taken.")
        return True

    if decision == "corrected":
        filename, text, raw = attachment
        _save_correction(filename, raw)
        if text is not None:
            log.info("Reply CORRECTED — using attached '%s'.", filename)
            upload_blog(text, source="corrected")
        else:
            log.warning("Corrected attachment '%s' is not text — saved for manual handling, "
                        "not uploaded.", filename)
        return True

    # unknown — leave unread so it surfaces again for manual review.
    log.warning("Reply UNRECOGNIZED (no clear yes/no/attachment) — leaving unread: %r",
                reply_text[:80])
    return False


def _append_reply_log(reply_date, from_addr, subject, decision, body):
    """Append one tab-separated audit line per processed reply to replies.log.

    Columns: reply date | from | subject | decision | body. ``body`` is the
    reply text with whitespace collapsed to a single line so each reply stays
    one greppable record; the processing time is prepended for ordering.
    """
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    one_line = re.sub(r"\s+", " ", body).strip() or "(no text body)"
    with REPLIES_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp}\t{reply_date}\t{from_addr}\t{subject}\t{decision}\t{one_line}\n")


def _connect_imap(password, attempts=3):
    """Connect and log in to IMAP, retrying transient failures.

    Returns a logged-in IMAP4_SSL connection, or None if every attempt failed.
    Network blips (OSError) and IMAP errors are both retried with exponential
    backoff, so a single daily run does not fail on a momentary hiccup (the
    kind that caused the 6 PM run to exit 1 with nothing actually wrong).
    """
    delay = 3
    for attempt in range(1, attempts + 1):
        imap = None
        try:
            imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=30)
            imap.login(SENDER_EMAIL, password)
            return imap
        except (OSError, imaplib.IMAP4.error) as exc:
            if imap is not None:
                try:
                    imap.logout()
                except Exception:
                    pass
            if attempt < attempts:
                log.warning(
                    "IMAP connect/login attempt %d/%d failed (%s); retrying in %ds.",
                    attempt, attempts, exc, delay,
                )
                time.sleep(delay)
                delay *= 2
            else:
                log.error(
                    "IMAP connect/login failed after %d attempts (network down, or "
                    "is IMAP enabled in Gmail?): %s", attempts, exc,
                )
    return None


def check_replies():
    """Fetch unread replies from Arjun, classify and act on each. One-shot."""
    password = load_app_password()
    if not password:
        return False

    imap = _connect_imap(password)
    if imap is None:
        return False

    try:
        imap.select("INBOX")
        criteria = ["UNSEEN", "FROM", f'"{RECIPIENT}"', "SUBJECT", f'"{SUBJECT}"']
        typ, data = imap.search(None, *criteria)
        if typ != "OK":
            log.error("IMAP search failed: %s", typ)
            return False

        ids = data[0].split()
        if not ids:
            log.info("No new replies from %s.", RECIPIENT)
            return True

        log.info("Found %d new repl%s to process.", len(ids), "y" if len(ids) == 1 else "ies")
        for num in ids:
            typ, msg_data = imap.fetch(num, "(BODY.PEEK[])")
            if typ != "OK" or not msg_data or not msg_data[0]:
                log.error("Failed to fetch message %s", num.decode(errors="replace"))
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject", "")
            from_addr = msg.get("From", "")
            reply_date = msg.get("Date", "")
            attachment = _get_text_attachment(msg)
            reply_text = _extract_reply_text(msg)
            decision = classify_reply(reply_text, attachment is not None)
            mark_seen = handle_reply(decision, reply_text, attachment)
            # For a corrected reply the meaningful content is the attachment, so
            # note its filename in the body record alongside any typed text.
            logged_body = reply_text
            if decision == "corrected" and attachment is not None:
                logged_body = f"{reply_text} [attachment: {attachment[0]}]".strip()
            _append_reply_log(reply_date, from_addr, subject, decision, logged_body)
            if mark_seen:
                imap.store(num, "+FLAGS", "\\Seen")
        return True
    except imaplib.IMAP4.error as exc:
        log.error("IMAP error while processing replies: %s", exc)
        return False
    finally:
        try:
            imap.close()
        except Exception:
            pass
        try:
            imap.logout()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Weekly DPS Website Blog Check emailer.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--once",
        action="store_true",
        help="Send a single email and exit (use with an external scheduler).",
    )
    group.add_argument(
        "--encrypt",
        action="store_true",
        help="One-time: prompt for the Gmail App Password and store it encrypted.",
    )
    group.add_argument(
        "--check-replies",
        action="store_true",
        help="Read Arjun's replies (yes/no/corrected attachment) and act on them, then exit.",
    )
    args = parser.parse_args()

    if args.encrypt:
        raise SystemExit(encrypt_password())

    if args.check_replies:
        raise SystemExit(0 if check_replies() else 1)

    if args.once:
        raise SystemExit(0 if run_once() else 1)

    # Continuous mode: send now, then once every 7 days.
    log.info("Starting weekly blog checker (sending now, then every 7 days). "
             "Press Ctrl+C to stop.")
    while True:
        run_once()
        try:
            time.sleep(WEEK_SECONDS)
        except KeyboardInterrupt:
            log.info("Stopped.")
            break


if __name__ == "__main__":
    main()
