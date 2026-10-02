"""Shared helpers for My Business Brain scripts. Standard library only."""
import os
import re
import sys
from datetime import date, datetime

# Brains hold Arabic and other non-Latin text: always write UTF-8, even to a Windows console or pipe.
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

REQUIRED = ["id", "title", "type", "domain", "status", "source", "source_type",
            "recorded_on", "review_by", "confidence"]
STATUSES = {"active", "draft", "disputed", "superseded", "archived"}
SOURCE_TYPES = {"internal-document", "user-stated", "external-verified", "calculated"}
CONFIDENCE = {"high", "medium", "low"}
DATE_FIELDS = ["recorded_on", "verified_on", "review_by"]
LINK_RE = re.compile(r"\[\[([a-z0-9][a-z0-9\-_.]*)\]\]")


def parse_value(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()] if inner else []
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1]
    return raw


def read_entry(path):
    """Return (meta, body) for a Markdown file with a front-matter header, or (None, text)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return None, text
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return None, text
    header = parts[0][3:]
    body = parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
    meta, last = {}, None
    for line in header.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith(("  - ", "- ")) and last:
            meta.setdefault(last, [])
            if not isinstance(meta[last], list):
                meta[last] = [meta[last]] if meta[last] else []
            meta[last].append(line.split("- ", 1)[1].strip().strip("'\""))
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            last = k.strip()
            meta[last] = parse_value(v) if v.strip() else []
    return meta, body


def as_list(v):
    if v is None or v == "":
        return []
    return v if isinstance(v, list) else [v]


def parse_date(v):
    if not v or isinstance(v, list):
        return None
    try:
        return datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def load_brain(root):
    """Load every entry under entries/ and _system/archive/. Returns list of dicts."""
    entries = []
    for sub in ("entries", os.path.join("_system", "archive")):
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base):
            for name in sorted(files):
                if not name.endswith(".md"):
                    continue
                path = os.path.join(dirpath, name)
                meta, body = read_entry(path)
                entries.append({
                    "path": os.path.relpath(path, root).replace(os.sep, "/"),
                    "file_id": name[:-3],
                    "folder": os.path.basename(dirpath),
                    "archived": sub != "entries",
                    "meta": meta,
                    "body": body,
                })
    return entries


# ---- Arabic ----
# Folding makes Arabic text comparable: Arabic-Indic digits become 0-9, the Arabic thousands and
# decimal separators become "," and ".", diacritics and tatweel are dropped, and letter variants
# that are spelled interchangeably are unified (alef forms, alef maqsura, taa marbuta).
_AR_FOLD = {**{0x0660 + i: str(i) for i in range(10)}, **{0x06F0 + i: str(i) for i in range(10)},
            0x066C: ",", 0x066B: ".", 0x060C: ",", 0x061B: ";", 0x061F: "?", 0x0640: None,
            0x0623: "\u0627", 0x0625: "\u0627", 0x0622: "\u0627", 0x0671: "\u0627",
            0x0649: "\u064A", 0x0629: "\u0647",
            **{c: None for c in range(0x064B, 0x0660)}, 0x0670: None}
AR_LETTERS = "\u0621-\u064A"
AR_STOP = {"في", "من", "على", "الى", "عن", "مع", "هذا", "هذه", "ذلك", "تلك", "التي", "الذي", "الذين",
           "او", "ثم", "كل", "بعد", "قبل", "عند", "حتى", "لكن", "هو", "هي", "هم", "نحن", "انا", "ما", "ماذا",
           "كم", "هل", "لا", "ان", "كان", "قد", "لنا", "لدينا", "و"}
_AR_PREFIXES = ("وبال", "وال", "بال", "كال", "فال", "لل", "ال")
_AR_SUFFIXES = ("ات", "ون", "ين", "ها", "هم", "كم", "نا", "يه", "ه")


def fold(s):
    """Fold Arabic text for comparison and search; Latin text passes through unchanged."""
    return str(s).translate(_AR_FOLD)


def ar_stem(w):
    """Light Arabic stemming: strip the definite article and common attached prefixes and suffixes."""
    for p in _AR_PREFIXES:
        if w.startswith(p) and len(w) - len(p) >= 3:
            w = w[len(p):]
            break
    for suf in _AR_SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def norm(s):
    return re.sub(r"[^a-z0-9" + AR_LETTERS + r"]+", " ", fold(s).lower()).strip()


def words(s):
    stop = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "is", "are", "be",
            "with", "by", "per", "at", "as", "it", "this", "that", "we", "our", "from"}
    out = set()
    for w in norm(s).split():
        if w in stop or w in AR_STOP:
            continue
        if re.match("[" + AR_LETTERS + "]", w):
            w = ar_stem(w)
        if len(w) > 2:
            out.add(w)
    return out


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def today(arg=None):
    return parse_date(arg) if arg else date.today()


# --- Sensitivity labels -------------------------------------------------------------
SENSITIVITY = ("public", "internal", "confidential")
# Domains whose entries default to confidential when no label is set: personal data and
# commercially sensitive terms.
CONFIDENTIAL_DOMAINS = {"people", "contracts", "finance"}


def sensitivity_of(meta):
    """Return the entry's sensitivity label, applying the default when it is missing."""
    s = str((meta or {}).get("sensitivity", "")).strip().lower()
    if s in SENSITIVITY:
        return s
    return "confidential" if (meta or {}).get("domain") in CONFIDENTIAL_DOMAINS else "internal"


# --- Keeping confidential facts out of team and external work -----------------------
def confidential_markers(root):
    """What would give a confidential entry away: its id, its value and the figures in it
    (amounts, rates, numbers), for every confidential entry in the brain."""
    ids, phrases, figures = set(), set(), set()
    for e in load_brain(root):
        m = e["meta"] or {}
        if not m or sensitivity_of(m) != "confidential":
            continue
        ids.add(str(m.get("id") or e["file_id"]).lower())
        v = m.get("value")
        v = fold(str(v or "")).lower().strip() if not isinstance(v, list) else ""
        if len(v) >= 6:
            phrases.add(v)
        for n in re.findall(r"\d[\d,]*(?:\.\d+)?%?", fold(str(m.get("value", "")) + " " + e["body"])):
            n = n.replace(",", "").rstrip(".")
            if n.endswith("%"):
                figures.add(n)
                continue
            if len(n.replace(".", "")) >= 3 and not (len(n) == 4 and n.startswith(("19", "20"))):
                figures.add(n)
                try:
                    v = float(n)
                    if v >= 1000 and v % 100 == 0:  # 28000 is also "28k" and "28.0k"
                        figures.add(("%g" % (v / 1000)) + "k")
                except ValueError:
                    pass
    return {"ids": ids, "phrases": phrases, "figures": figures}


def mentions_confidential(text, markers):
    """True if text names a confidential entry, quotes its value or uses one of its figures."""
    t = fold(str(text or "")).lower()
    if not t.strip():
        return False
    if any(i in t for i in markers["ids"]) or any(p in t for p in markers["phrases"]):
        return True
    nums = {n.replace(",", "").rstrip(".") for n in re.findall(r"\d[\d,]*(?:\.\d+)?(?:%|k\b)?", t)}
    nums |= {n[:-1] for n in nums if n.endswith(("%", "k"))} - {""}
    return bool(nums & markers["figures"])


def entry_id_of(citation):
    """'[[id]]', ' id ', 'id#L3' or 'entries/x/id.md' -> 'id'."""
    c = str(citation or "").strip().strip("[]").strip()
    c = c.split("#")[0]
    if c.startswith(("entries/", "_system/archive/")) and c.endswith(".md"):
        c = os.path.basename(c)[:-3]
    return c.lower()


# --- Prompt-injection screening ------------------------------------------------------
# Documents are data. Text inside them that tries to instruct an AI is flagged, never
# followed. These patterns catch the common forms; the reader and coordinator still
# apply judgment (see references/security-and-privacy.md).
INJECTION_PATTERNS = [
    r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b(previous|prior|above|earlier|all|any|system|your)\b[^.\n]{0,20}\b(instructions?|rules|prompts?|guidelines|directions)\b",
    r"\b(system|developer)\s+prompt\b",
    r"\byou\s+are\s+(now\s+)?(an?\s+)?(ai|assistant|language model|chatbot|claude|chatgpt|gpt)\b",
    r"\b(new|updated|revised|hidden)\s+instructions?\s*:",
    r"<\s*/?\s*(system|instructions?|prompt)\s*>",
    r"\b(do\s+not|don'?t|never)\s+(tell|inform|mention|show|alert|notify)\s+(the\s+)?(user|owner|human)\b",
    r"\b(send|forward|email|e-mail|upload|post|exfiltrate|transmit|leak)\b[^.\n]{0,40}\b(business brain|the brain|brain (folder|entries|contents)|knowledge base|contents of (this|the|your) (brain|folder|conversation|context|memory)|conversation history|credentials?|passwords?|api keys?|secret keys?)\b",
    r"\b(run|execute|eval)\s+(the\s+following|this)\s+(command|code|script|shell)\b",
    r"\bact\s+as\s+(an?\s+)?(ai|assistant|admin|administrator|system|developer)\b",
    r"\bwhen\s+(an?\s+)?(ai|assistant|llm|claude|model)\s+(reads|sees|processes)\b",
    # Arabic: "ignore (all) previous instructions", "do not tell the user", "you are now an assistant"
    r"(تجاهل|تجاهلي|انس|انسى|تخط)[^.\n]{0,30}(التعليمات|الأوامر|التوجيهات|القواعد)",
    r"(لا|ولا)\s+(تخبر|تخبري|تبلغ|تعلم|تُعلم)\s+(المستخدم|المالك)",
    r"أنت\s+الآن\s+(مساعد|نموذج|ذكاء)",
    r"(أرسل|ارسل|حوّل|حول)[^.\n]{0,40}(محتوى|محتويات)\s+(الدماغ|المجلد|المحادثة|قاعدة المعرفة)",
]
_INJ = [re.compile(p, re.I) for p in INJECTION_PATTERNS]


# ---- Source trust tiers ----
# Only official and reputable sources (and the business's own documents or the owner's word) can
# back a stored fact. Social and community sources are kept as signals: sentiment or leads.
TIERS = ("official", "reputable", "internal", "recording", "social", "other")
FACT_TIERS = {"official", "reputable", "internal"}
_OFFICIAL_SUFFIXES = (".gov", ".mil", ".int", ".europa.eu", ".un.org", ".who.int", ".worldbank.org", ".imf.org",
                      ".oecd.org")
_OFFICIAL_PARTS = ("gov", "gouv", "gob", "go", "govt", "admin", "mil")
_REPUTABLE = ("reuters.com", "apnews.com", "bloomberg.com", "ft.com", "wsj.com", "economist.com", "bbc.com",
              "bbc.co.uk", "statista.com", "nytimes.com", "theguardian.com", "cnbc.com", "forbes.com",
              "mckinsey.com", "pwc.com", "deloitte.com", "ey.com", "kpmg.com", "gartner.com", "nature.com",
              "sciencedirect.com", "ssrn.com", "arxiv.org")
_SOCIAL = ("x.com", "twitter.com", "reddit.com", "facebook.com", "instagram.com", "tiktok.com", "linkedin.com",
           "quora.com", "medium.com", "substack.com", "t.me", "telegram.org", "whatsapp.com", "discord.com",
           "threads.net", "pinterest.com", "xiaohongshu.com", "bilibili.com", "v2ex.com", "weibo.com",
           "trustpilot.com", "tripadvisor.com", "glassdoor.com", "yelp.com", "snapchat.com")
_RECORDING = ("youtube.com", "youtu.be", "vimeo.com", "podcasts.apple.com", "open.spotify.com", "soundcloud.com")
_URL_HOST = re.compile(r"https?://([^/\s:]+)", re.I)


def _host(s):
    s = str(s or "").strip()
    m = _URL_HOST.search(s)
    host = (m.group(1) if m else (s if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", s.lower()) else "")).lower()
    return host[4:] if host.startswith("www.") else host


def _matches(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)


def source_tier(source, custom=None):
    """Trust tier of a source (a URL, a domain or a source description).

    custom: {"official": [...domains], "reputable": [...], "social": [...]} from the brain's
    _system/trusted-sources.json, which wins over the built-in lists."""
    host = _host(source)
    custom = custom or {}
    if host:
        for tier in ("official", "reputable", "social", "recording"):
            if _matches(host, [str(d).lower() for d in custom.get(tier, [])]):
                return tier
        if host.endswith(_OFFICIAL_SUFFIXES) or any(p in _OFFICIAL_PARTS for p in host.split(".")[1:-1]) \
                or host.split(".")[-2:-1] in (["gov"], ["gouv"], ["gob"]):
            return "official"
        if _matches(host, _SOCIAL) or "forum" in host or host.startswith(("community.", "forums.")):
            return "social"
        if _matches(host, _RECORDING):
            return "recording"
        if _matches(host, _REPUTABLE):
            return "reputable"
        return "other"
    low = str(source or "").lower()
    if not low:
        return "other"
    if any(w in low for w in ("tweet", "reddit", "linkedin post", "facebook", "instagram", "whatsapp group",
                              "forum", "tiktok", "social media", "online review", "review site")):
        return "social"
    if any(w in low for w in ("webinar", "podcast", "video", "recording", "youtube")):
        return "recording"
    return "internal"


def load_trusted(root):
    try:
        import json as _json
        with open(os.path.join(root, "_system", "trusted-sources.json"), encoding="utf-8") as f:
            return _json.load(f)
    except (OSError, ValueError):
        return {}


def source_meta(path, custom=None):
    """Header of a source document (title, url, tier, ...) if it starts with a --- block."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(4000)
    except OSError:
        return {}
    if not head.startswith("---"):
        return {}
    end = head.find("\n---", 3)
    meta = {}
    for line in head[3:end if end > 0 else 0].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    if meta:
        declared = meta.get("tier")
        meta["tier"] = declared if declared in TIERS else source_tier(meta.get("url") or meta.get("source"), custom)
    return meta


# ---- Private (off the record) ----
# Anything the user wraps in <private>...</private> (or <خاص>...</خاص>) is never stored: not in an
# entry, not in a log, not in a briefing. An unclosed tag hides everything after it.
_PRIVATE_BLOCK = re.compile(r"<\s*(private|خاص)\s*>.*?<\s*/\s*\1\s*>", re.S | re.I)
_PRIVATE_OPEN = re.compile(r"<\s*(private|خاص)\s*>.*", re.S | re.I)


def strip_private(text):
    """Remove private passages. Returns the text with each one replaced by nothing."""
    if not text:
        return text
    out = _PRIVATE_BLOCK.sub("", str(text))
    return _PRIVATE_OPEN.sub("", out)


def read_text(path, default=""):
    """The whole file as text, or `default` if it doesn't exist (closes the file)."""
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return f.read()


def has_private(text):
    return bool(text) and bool(_PRIVATE_OPEN.search(str(text)))


def approx_tokens(text):
    """Rough reading cost of a text in tokens (about 4 characters each; Arabic about 2.5)."""
    t = str(text or "")
    ar = sum(1 for ch in t if "\u0600" <= ch <= "\u06FF")
    return int(round((len(t) - ar) / 4 + ar / 2.5))


_SCRIPTS = (("arabic", ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))),
            ("latin", ((0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F))),
            ("cyrillic", ((0x0400, 0x04FF),)),
            ("devanagari", ((0x0900, 0x097F),)),
            ("cjk", ((0x3040, 0x30FF), (0x4E00, 0x9FFF), (0xAC00, 0xD7AF))))


def script_of(text):
    """The main writing system of a text: latin, arabic, cyrillic, devanagari, cjk, other, mixed or none.

    English-only rules and a model calibrated on English text are out of their depth on other
    scripts (Laya's English checkpoint scores 0 on Khmer at 95% confidence), so decisions record
    the script and are calibrated per script."""
    counts = {}
    for ch in str(text or ""):
        if not ch.isalpha():
            continue
        o, name = ord(ch), "other"
        for s, ranges in _SCRIPTS:
            if any(a <= o <= b for a, b in ranges):
                name = s
                break
        counts[name] = counts.get(name, 0) + 1
    total = sum(counts.values())
    if not total:
        return "none"
    top, n = max(counts.items(), key=lambda kv: kv[1])
    return top if n / total >= 0.8 else "mixed"


def injection_hits(text):
    """Return the suspicious passages found in text (empty list when clean)."""
    hits = []
    for rx in _INJ:
        for mt in rx.finditer(str(text or "")):
            start = max(0, mt.start() - 30)
            hits.append(str(text)[start:mt.end() + 30].replace("\n", " ").strip())
    return hits
