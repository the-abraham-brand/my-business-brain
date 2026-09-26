#!/usr/bin/env python3
"""My Business Brain timeline: what was happening around a fact, a topic or a date.

Pulls every dated trace the brain keeps into one chronological list:
  - the changelog (what was added, changed, superseded or archived, and why);
  - entries recorded or verified, and earlier values kept in the archive;
  - decisions made, confirmed and corrected (_system/decisions.jsonl);
  - answers, proposals and quotes that went out using the facts (_system/answer-log.jsonl);
  - contract dates coming up (notice deadlines, end dates).

Usage:
  timeline.py <brain> --entry ID            everything about one entry and its key's history
  timeline.py <brain> --key price.scale-plan.monthly
  timeline.py <brain> --topic "Supplier X"
  timeline.py <brain> --around 2026-09-15 [--days 14]   everything within a window
  add --json for machine-readable output
Private passages are never shown. Standard library only.
"""
import json
import os
import re
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, parse_date, strip_private, today  # noqa: E402


def read_jsonl(path):
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def collect(root):
    events = []
    entries = [e for e in load_brain(root) if e["meta"]]
    for e in entries:
        m = e["meta"]
        eid = m.get("id") or e["file_id"]
        base = {"entry": eid, "key": str(m.get("key", "")).lower(), "title": m.get("title", eid)}
        if parse_date(m.get("recorded_on")):
            what = (f"recorded {m.get('title')}" + (f" = {m.get('value')}" if m.get("value") else "")
                    + (f" (now {m.get('status')})" if e["archived"] or m.get("status") in ("superseded", "archived") else "")
                    + (f", source: {m.get('source')}" if m.get("source") else ""))
            events.append({**base, "date": str(m["recorded_on"])[:10], "kind": "entry", "text": what})
        if parse_date(m.get("verified_on")):
            events.append({**base, "date": str(m["verified_on"])[:10], "kind": "verified", "text": f"verified {m.get('title')}"})
        for field, label in (("notice_deadline", "notice deadline"), ("end_date", "contract ends"), ("start_date", "contract starts")):
            if parse_date(m.get(field)):
                events.append({**base, "date": str(m[field])[:10], "kind": "contract", "text": f"{m.get('title')}: {label}"})
    cl = os.path.join(root, "_system", "changelog.md")
    if os.path.exists(cl):
        with open(cl, encoding="utf-8") as f:
            for line in f:
                mm = re.match(r"\s*[-*]\s*(\d{4}-\d{2}-\d{2})\s*(.*)", line)
                if mm:
                    events.append({"date": mm.group(1), "kind": "change", "text": strip_private(mm.group(2).strip()),
                                   "entry": ",".join(re.findall(r"\[\[([^\]]+)\]\]", mm.group(2))), "key": "", "title": ""})
    for d in read_jsonl(os.path.join(root, "_system", "decisions.jsonl")):
        if d.get("event") == "decision":
            events.append({"date": d.get("at", "")[:10], "kind": "decision", "entry": str(d.get("subject", "")), "key": "",
                           "title": "", "text": f"decided {d.get('type')} = {d.get('choice')} for {d.get('subject') or 'an item'} "
                                                f"({d.get('route')}, confidence {d.get('confidence')})"})
        elif d.get("event") == "correction":
            events.append({"date": d.get("at", "")[:10], "kind": "decision", "entry": "", "key": "", "title": "",
                           "text": f"user corrected a {d.get('type')} decision from {d.get('was')} to {d.get('actual')}",
                           "decision_id": d.get("id")})
    for r in read_jsonl(os.path.join(root, "_system", "answer-log.jsonl")):
        ids = [c.get("id", "") for c in r.get("citations", [])]
        vals = [f"{c.get('id')} = {c.get('value')}" for c in r.get("citations", []) if c.get("value")]
        events.append({"date": r.get("at", "")[:10], "kind": "output", "entry": ",".join(ids),
                       "key": ",".join(str(c.get("key", "")).lower() for c in r.get("citations", [])), "title": "",
                       "text": f"{r.get('kind', 'output')} sent" + (f" to {r.get('recipient')}" if r.get("recipient") else "")
                               + (f" ({strip_private(r.get('purpose', ''))})" if r.get("purpose") else "")
                               + (f", using {'; '.join(vals)}" if vals else "")})
    return [e for e in events if parse_date(e["date"])]


def select(events, root, entry=None, key=None, topic=None, around=None, days=14):
    if entry:
        keys = {e["key"] for e in events if e.get("entry") == entry and e.get("key")}
        return [e for e in events if entry in str(e.get("entry", "")).split(",") or entry in e["text"]
                or (keys and any(k in str(e.get("key", "")).split(",") for k in keys))]
    if key:
        key = key.lower()
        return [e for e in events if key in str(e.get("key", "")).split(",") or key in e["text"].lower()]
    if topic:
        words = [w for w in re.findall(r"\w+", topic.lower()) if len(w) > 2]
        return [e for e in events if all(w in (e["text"] + " " + e.get("title", "")).lower() for w in words)]
    if around:
        c = parse_date(around)
        lo, hi = c - timedelta(days=days), c + timedelta(days=days)
        return [e for e in events if lo <= parse_date(e["date"]) <= hi]
    return events


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    val = lambda n: args[args.index(n) + 1] if n in args else None
    ev = select(collect(root), root, val("--entry"), val("--key"), val("--topic"), val("--around"),
                int(val("--days") or 14))
    ev.sort(key=lambda e: (e["date"], e["kind"]))
    seen, uniq = set(), []
    for e in ev:
        k = (e["date"], e["text"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    if "--json" in args:
        print(json.dumps(uniq, indent=2, ensure_ascii=False))
        return 0
    if not uniq:
        print("Nothing on record for that.")
        return 0
    now = today().isoformat()
    marked = False
    for e in uniq:
        if not marked and e["date"] > now:
            print(f"---- today ({now}) ----")
            marked = True
        cite = f" [[{e['entry'].split(',')[0]}]]" if "[[" not in e["text"] and e.get("entry") and re.match(r"^[a-z0-9][a-z0-9\-_.]*$", e["entry"].split(",")[0]) else ""
        print(f"{e['date']}  {e['kind']:8}  {e['text']}{cite}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
