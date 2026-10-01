#!/usr/bin/env python3
"""My Business Brain watch list: keep an eye on the sources that matter to the business.

Add the feeds and pages that can change what the business knows: a regulator's news page, a
ministry's fee schedule, a supplier's announcements, a competitor's price page. Each check
fetches them (plain Python, nothing to install), compares with what was seen last time, and
reports what is new. For each new item it asks: does this touch something the brain holds?

  "Federal Tax Authority page mentions '5% VAT' changes → may affect [[legal-regulatory-vat-rate]]
   (the brain records 5%; the page now says 7.5%)"

Findings follow the source trust tiers:
  official / reputable   a change that may affect a stored fact goes to the owner as a check,
                         never applied automatically
  other (a company's own site)   reported; can support facts about that company
  social / community     kept as sentiment or leads (signals), never as facts
Fetched text is data: any text in it that tries to instruct an AI is reported, not followed.

Usage:
  watch.py <brain> add URL --name "Federal Tax Authority news" [--kind rss|page] [--keys tax.vat.rate,...]
                        [--entries id,...] [--keywords "VAT,excise"]
  watch.py <brain> list
  watch.py <brain> remove ID
  watch.py <brain> check [--json] [--write] [--today YYYY-MM-DD]   --write saves _system/watch/<date>.md
Standard library only.
"""
import difflib
import hashlib
import html
import json
import os
import re
import sys
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import (load_brain, source_tier, load_trusted, injection_hits, fold, words, today,  # noqa: E402
                      strip_private)

UA = "Mozilla/5.0 (compatible; MyBusinessBrain-watch/1.5; +https://theabrahambrand.com)"
MAX_BYTES = 3 * 1024 * 1024
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?%?")


def list_path(root):
    return os.path.join(root, "_system", "watch.json")


def state_dir(root):
    return os.path.join(root, "_system", "watch")


def load_list(root):
    try:
        with open(list_path(root), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def split_list(s):
    return [x.strip() for x in str(s or "").split(",") if x.strip()]


def add(root, url, name="", kind="auto", keys="", entries="", keywords="", now=None):
    items = load_list(root)
    if any(i["url"] == url for i in items):
        return {"error": "already on the watch list"}
    item = {"id": "w-" + uuid.uuid4().hex[:6], "url": url, "name": name or url, "kind": kind,
            "tier": source_tier(url, load_trusted(root)), "keys": split_list(keys), "entries": split_list(entries),
            "keywords": split_list(keywords), "added": (now or today()).isoformat()}
    items.append(item)
    save_json(list_path(root), items)
    return item


def remove(root, wid):
    items = load_list(root)
    keep = [i for i in items if i["id"] != wid]
    if len(keep) == len(items):
        return {"error": f"{wid} not found"}
    save_json(list_path(root), keep)
    return {"removed": wid}


# ---- fetching and parsing ----

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(MAX_BYTES + 1)
        ctype = r.headers.get("Content-Type", "") if hasattr(r, "headers") and r.headers else ""
    if len(data) > MAX_BYTES:
        data = data[:MAX_BYTES]
    m = re.search(r"charset=([\w-]+)", ctype or "")
    return data.decode(m.group(1) if m else "utf-8", errors="replace"), ctype or ""


class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"}
    BLOCK = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "br", "section", "article", "td", "th"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_text(doc):
    p = _Text()
    p.feed(doc)
    lines = [re.sub(r"\s+", " ", l).strip() for l in "".join(p.out).splitlines()]
    return "\n".join(l for l in lines if len(l) > 2)


def _t(el, *names):
    for n in names:
        for child in el:
            if child.tag.split("}")[-1] == n:
                if n == "link" and child.get("href"):
                    return child.get("href")
                if child.text:
                    return child.text.strip()
    return ""


def parse_feed(doc):
    """Items of an RSS or Atom feed, or None if the document isn't a feed."""
    try:
        root = ET.fromstring(doc.encode("utf-8") if isinstance(doc, str) else doc)
    except ET.ParseError:
        return None
    tag = root.tag.split("}")[-1]
    if tag not in ("rss", "feed", "RDF"):
        return None
    items = []
    for el in root.iter():
        if el.tag.split("}")[-1] in ("item", "entry"):
            title = _t(el, "title")
            link = _t(el, "link")
            summary = html_text(_t(el, "description", "summary", "content"))[:600]
            when = _t(el, "pubDate", "updated", "published", "date")
            guid = _t(el, "guid", "id") or link or title
            items.append({"guid": guid, "title": html.unescape(title), "link": link, "summary": summary, "date": when})
    return items


# ---- matching against the brain ----

def brain_index(root):
    idx = []
    for e in load_brain(root):
        m = e["meta"]
        if not m or e["archived"] or m.get("status", "active") not in ("active", "disputed"):
            continue
        idx.append({"id": m.get("id") or e["file_id"], "key": str(m.get("key", "")).lower(),
                    "title": m.get("title", ""), "value": str(m.get("value", "")),
                    "words": words(str(m.get("title", "")) + " " + str(m.get("key", "")).replace(".", " ").replace("-", " "))})
    return idx


def figures(text):
    """Numbers that can be a price, rate or amount: not years or day-of-month numbers."""
    out = set()
    for n in NUM.findall(text):
        v = n.replace(",", "")
        if v.endswith("%") or "," in n or "." in v:
            out.add(v)
            continue
        try:
            i = int(v)
        except ValueError:
            continue
        if (1900 <= i <= 2100) or i <= 31:
            continue
        out.add(v)
    return out


def matches(text, watch_item, idx):
    """Entries a piece of new text may affect, with the reason."""
    t = fold(text).lower()
    tw = words(t)
    tnums = figures(t)
    out = []
    for e in idx:
        pinned = e["id"] in watch_item.get("entries", []) or (e["key"] and e["key"] in [k.lower() for k in watch_item.get("keys", [])])
        overlap = e["words"] & tw
        if not pinned and len(overlap) < 2:
            continue
        enums = figures(fold(e["value"]).lower())
        note = ""
        if enums and tnums and not (enums & tnums):
            note = f"the brain records {e['value']}; the source now mentions {', '.join(sorted(tnums)[:4])}"
        elif enums and (tnums & enums) and (tnums - enums):
            note = (f"the brain records {e['value']}; the source mentions it alongside "
                    f"{', '.join(sorted(tnums - enums)[:4])}, which may be a new value")
        elif enums and tnums & enums:
            note = f"mentions the same figure the brain holds ({e['value']})"
        out.append({"entry": e["id"], "title": e["title"], "why": "pinned" if pinned else "shared words: " + ", ".join(sorted(overlap)[:4]),
                    "note": note, "strong": bool(pinned or note.startswith("the brain records"))})
    out.sort(key=lambda m: (not m["strong"], m["entry"]))
    return out[:5]


def keyword_hit(text, item):
    kws = [k.lower() for k in item.get("keywords", [])]
    return not kws or any(k in fold(text).lower() for k in kws)


def check_one(root, item, idx, now):
    sdir = state_dir(root)
    spath = os.path.join(sdir, "state", item["id"] + ".json")
    try:
        with open(spath, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}
    result = {"id": item["id"], "name": item["name"], "url": item["url"], "tier": item["tier"], "findings": [],
              "first_check": not state, "error": ""}
    try:
        doc, ctype = fetch(item["url"])
    except Exception as ex:  # network errors are reported, never fatal
        result["error"] = f"could not fetch: {str(ex)[:120]}"
        return result
    feed = parse_feed(doc) if item.get("kind") in ("auto", "rss") else None
    new_bits = []
    if feed is not None:
        seen = set(state.get("seen", []))
        for it in feed:
            if it["guid"] not in seen:
                new_bits.append({"text": f"{it['title']}. {it['summary']}".strip(), "title": it["title"],
                                 "link": it["link"], "date": it["date"]})
        state = {"kind": "rss", "seen": sorted(seen | {it["guid"] for it in feed})[-500:], "checked": now.isoformat()}
    else:
        text = html_text(doc) if "<" in doc[:2000] else doc
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cache = os.path.join(sdir, "cache", item["id"] + ".txt")
        old = ""
        if os.path.exists(cache):
            with open(cache, encoding="utf-8") as f:
                old = f.read()
        if state and digest != state.get("hash"):
            added = [l[1:].strip() for l in difflib.unified_diff(old.splitlines(), text.splitlines(), lineterm="", n=0)
                     if l.startswith("+") and not l.startswith("+++") and len(l.strip()) > 3]
            for line in added[:40]:
                new_bits.append({"text": line, "title": line[:120], "link": item["url"], "date": ""})
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            f.write(text)
        state = {"kind": "page", "hash": digest, "checked": now.isoformat()}
    save_json(spath, state)
    if result["first_check"]:
        result["note"] = f"first check: {len(new_bits)} item(s) recorded as the starting point"
        return result  # the first look sets the baseline; nothing is 'new' yet
    for bit in new_bits:
        if not keyword_hit(bit["text"], item):
            continue
        f = {"title": strip_private(bit["title"])[:200], "link": bit["link"], "date": bit["date"],
             "matches": matches(bit["text"], item, idx)}
        hits = injection_hits(bit["text"])
        if hits:
            f["warning"] = f"contains text that tries to instruct an AI: \"{hits[0][:100]}\" (not followed)"
        result["findings"].append(f)
    return result


def check(root, now=None, write=False):
    now = now or today()
    idx = brain_index(root)
    results = [check_one(root, item, idx, now) for item in load_list(root)]
    if write:
        record(root, results, now)
    return results


def render(results, now):
    lines = [f"# Watch list: {now.isoformat()}", ""]
    if not results:
        return "\n".join(lines + ["Nothing on the watch list yet. Add sources with `watch.py <brain> add URL`.", ""])
    affecting = [(r, f) for r in results for f in r["findings"] if any(m["strong"] for m in f["matches"])
                 and r["tier"] not in ("social",)]
    if affecting:
        lines += ["## May affect what the brain knows", ""]
        for r, f in affecting:
            for m in [m for m in f["matches"] if m["strong"]][:3]:
                lines.append(f"- **{r['name']}** ({r['tier']}): \"{f['title']}\" → may affect [[{m['entry']}]] "
                             f"{m['title']}" + (f": {m['note']}" if m["note"] else "") + (f" ({f['link']})" if f["link"] else "")
                             + (f" ⚠ {f['warning']}" if f.get("warning") else ""))
        lines.append("")
    lines += ["## By source", ""]
    for r in results:
        head = f"### {r['name']} ({r['tier']})"
        if r.get("error"):
            lines += [head, "", f"- {r['error']}", ""]
            continue
        if r.get("first_check"):
            lines += [head, "", f"- {r.get('note', 'first check')}", ""]
            continue
        lines += [head, ""]
        if not r["findings"]:
            lines += ["- Nothing new.", ""]
            continue
        for f in r["findings"][:15]:
            extra = []
            if f.get("warning"):
                extra.append("⚠ " + f["warning"])
            if f["matches"]:
                extra.append("related: " + ", ".join(f"[[{m['entry']}]]" for m in f["matches"][:3]))
            if r["tier"] == "social":
                extra.append("social source: sentiment or lead only")
            lines.append(f"- {f['title']}" + (f" ({f['date']})" if f["date"] else "") + ("; " + "; ".join(extra) if extra else ""))
        lines.append("")
    return "\n".join(lines)


def record(root, results, now):
    """Save the report, send possible fact changes to decisions-needed, social items to signals."""
    os.makedirs(state_dir(root), exist_ok=True)
    with open(os.path.join(state_dir(root), f"{now.isoformat()}.md"), "w", encoding="utf-8") as f:
        f.write(render(results, now))
    lines = []
    for r in results:
        for f in r["findings"]:
            if r["tier"] == "social":
                from signals import add as add_signal
                add_signal(root, "lead" if f["matches"] else "sentiment", f["title"], f["link"] or r["url"],
                           topic=r["name"], when=now)
                continue
            for m in [m for m in f["matches"] if m["strong"]][:2]:
                lines.append(f"- [ ] {now.isoformat()} **Check a watched source** ({r['name']}, {r['tier']}): "
                             f"\"{f['title'][:140]}\" may affect [[{m['entry']}]]" + (f": {m['note']}" if m["note"] else "")
                             + ". Confirm at the source before changing the brain.")
    if lines:
        path = os.path.join(root, "_system", "decisions-needed.md")
        old = "# Decisions needed\n"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = f.read()
        head, _, rest = old.partition("\n")
        new = [l for l in lines if l.split("**Check a watched source**")[-1] not in old]
        if new:
            with open(path, "w", encoding="utf-8") as f:
                f.write(head + "\n\n" + "\n".join(new) + "\n" + rest)


def main(argv):
    args = argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    now = today(val("--today")) if "--today" in args else today()
    if cmd == "add" and len(args) > 2:
        out = add(root, args[2], val("--name"), val("--kind", "auto"), val("--keys"), val("--entries"),
                  val("--keywords"), now)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1 if "error" in out else 0
    if cmd == "list":
        items = load_list(root)
        print("\n".join(f"- {i['id']} {i['name']} ({i['tier']}): {i['url']}" for i in items) or "Nothing on the watch list.")
        return 0
    if cmd == "remove" and len(args) > 2:
        out = remove(root, args[2])
        print(json.dumps(out))
        return 1 if "error" in out else 0
    if cmd == "check":
        res = check(root, now, "--write" in args)
        print(json.dumps(res, indent=2, ensure_ascii=False) if "--json" in args else render(res, now))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
