#!/usr/bin/env python3
"""My Business Brain journal: the month's story of the business, week by week.

For each ISO week of a month, the journal lists what the brain recorded:
  - What changed: facts added, changed, superseded or archived (snapshots and changelog);
  - What went out: proposals, quotes and answers sent, and to whom (answer log);
  - Decisions: calls made and corrections the user gave (decision log);
  - Still open: items carried forward from earlier weeks and new ones, so the story reads on
    from one week to the next instead of starting over.

The script writes the facts; Claude then adds a short plain-language paragraph at the top of
each week and of the month, using only what is listed (see references/journal-and-timeline.md).

Usage:
  journal.py <brain> --month 2026-09 [--write]      --write saves _system/journal/2026-09.md
Private passages are never included. Standard library only.
"""
import json
import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import strip_private, today  # noqa: E402
from brain_diff import list_snapshots, load_snapshot, compare, capture  # noqa: E402
from timeline import read_jsonl  # noqa: E402


def weeks_of(year, month):
    first = date(year, month, 1)
    last = (date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1))
    start = first - timedelta(days=first.weekday())
    out = []
    while start <= last:
        end = start + timedelta(days=6)
        out.append((max(start, first), min(end, last), start.isocalendar()[1]))
        start += timedelta(days=7)
    return out


def snapshot_on_or_before(root, day, snaps):
    c = [s for s in snaps if s <= day.isoformat()]
    return load_snapshot(root, c[-1]) if c else None


def build(root, year, month, now=None):
    now = now or today()
    snaps = list_snapshots(root)
    changelog = []
    cl = os.path.join(root, "_system", "changelog.md")
    if os.path.exists(cl):
        with open(cl, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*[-*]\s*(\d{4}-\d{2}-\d{2})\s*(.*)", line)
                if m:
                    changelog.append((m.group(1), strip_private(m.group(2).strip())))
    decisions = read_jsonl(os.path.join(root, "_system", "decisions.jsonl"))
    outputs = read_jsonl(os.path.join(root, "_system", "answer-log.jsonl"))
    open_before = set()
    chapters = []
    for start, end, wk in weeks_of(year, month):
        if start > now:
            break
        s, e = start.isoformat(), end.isoformat()
        chap = {"week": wk, "from": s, "to": e, "changed": [], "changelog": [], "outputs": [], "decisions": [],
                "corrections": 0, "carried": [], "new_open": []}
        old = snapshot_on_or_before(root, start - timedelta(days=1), snaps)
        new = snapshot_on_or_before(root, end, snaps)
        if end >= now:
            new = capture(root, now)
        if old and new and old.get("date") != new.get("date"):
            d = compare(old, new)
            chap["changed"] = ([f"added {a['title']}" + (f" = {a['value']}" if a["value"] else "") for a in d["added"]]
                               + [f"{c['title']}: {c['from']} → {c['to']}" for c in d["changed"]]
                               + [f"retired {r['title']}" for r in d["retired"] if not any(r['title'] == c['title'] for c in d["changed"])]
                               + [f"removed from the folder: {r['title']}" for r in d["removed"]])
        chap["changelog"] = [t for day, t in changelog if s <= day <= e]
        for r in outputs:
            if s <= r.get("at", "")[:10] <= e:
                chap["outputs"].append(f"{r.get('kind', 'output')}" + (f" to {r.get('recipient')}" if r.get("recipient") else "")
                                       + (f" ({strip_private(r.get('purpose', ''))})" if r.get("purpose") else ""))
        for d in decisions:
            if not (s <= d.get("at", "")[:10] <= e):
                continue
            if d.get("event") == "decision" and d.get("route") != "apply":
                chap["decisions"].append(f"{d.get('type')}: {d.get('choice')} for {d.get('subject') or 'an item'} ({d.get('route')})")
            elif d.get("event") == "correction":
                chap["corrections"] += 1
        # what is open at the end of this week: decisions waiting (by their date), unsaved facts
        open_now = set()
        dn = os.path.join(root, "_system", "decisions-needed.md")
        if os.path.exists(dn):
            with open(dn, encoding="utf-8") as f:
                for line in f:
                    m = re.match(r"\s*- \[ \]\s*(\d{4}-\d{2}-\d{2})?\s*(.*)", line)
                    if m and (not m.group(1) or m.group(1) <= e):
                        open_now.add(strip_private(m.group(2).strip())[:160])
        chap["carried"] = sorted(open_now & open_before)
        chap["new_open"] = sorted(open_now - open_before)
        open_before = open_now
        chapters.append(chap)
    return chapters


def render(year, month, chapters):
    name = date(year, month, 1).strftime("%B %Y")
    lines = [f"# Business journal: {name}", "",
             "_The month in two or three sentences: what changed, what went out, what is still open. "
             "Written from the facts below only._", ""]
    for c in chapters:
        lines += [f"## Week {c['week']} ({c['from']} to {c['to']})", "",
                  "_One short paragraph: the story of this week, following on from the last._", ""]
        facts = list(dict.fromkeys(c["changed"] + [t for t in c["changelog"] if not any(t in x for x in c["changed"])]))
        sections = [("What changed", facts), ("What went out", c["outputs"]),
                    ("Decisions that needed a person", c["decisions"] + ([f"{c['corrections']} correction(s) from the user"]
                                                                          if c["corrections"] else [])),
                    ("Still open from earlier weeks", c["carried"]), ("Newly open", c["new_open"])]
        empty = True
        for title, items in sections:
            if items:
                empty = False
                lines += [f"**{title}**", ""] + [f"- {i}" for i in items[:15]] + (
                    [f"- and {len(items) - 15} more"] if len(items) > 15 else []) + [""]
        if empty:
            lines += ["A quiet week: nothing recorded.", ""]
    return "\n".join(lines)


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-") or "--month" not in args:
        print(__doc__)
        return 2
    root = args[0]
    y, m = (int(x) for x in args[args.index("--month") + 1].split("-")[:2])
    now = today(args[args.index("--today") + 1]) if "--today" in args else today()
    md = render(y, m, build(root, y, m, now))
    if "--write" in args:
        d = os.path.join(root, "_system", "journal")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"{y:04d}-{m:02d}.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved _system/journal/{y:04d}-{m:02d}.md")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
