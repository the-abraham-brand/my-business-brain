"""Shared helpers for My Business Brain scripts. Standard library only."""
import os
import re
from datetime import date, datetime

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


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def words(s):
    stop = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "is", "are", "be",
            "with", "by", "per", "at", "as", "it", "this", "that", "we", "our", "from"}
    return {w for w in norm(s).split() if len(w) > 2 and w not in stop}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def today(arg=None):
    return parse_date(arg) if arg else date.today()
