#!/usr/bin/env python3
"""My Business Brain distillation: condense what the brain has learned into a one-page playbook.

Distillation trains a small model to do what a large one does. The brain does the same with its
own experience: lessons from corrections, the owner's accepted preferences, what the agents keep
getting wrong, and the latest decisions are condensed into `_system/playbook.md`, short enough
that every tasking memo includes it and every agent reads it first.

It runs in the Sunday review and on request. The playbook is generated: edit the sources
(lessons, preferences, identity), not the playbook.

Usage:
  distill.py <brain> [--today YYYY-MM-DD] [--days 30] [--print]
Standard library only.
"""
import os
import re
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import read_text, strip_private, today  # noqa: E402

MAX_WORDS = 700


def lessons(root):
    text = read_text(os.path.join(root, "_system", "lessons.md"))
    rules = re.findall(r"^-\s*Rule:\s*(.+)$", text, re.M)
    if not rules:
        rules = [l[2:].strip() for l in text.splitlines() if l.startswith("- ") and len(l) > 12]
    return list(dict.fromkeys(r.strip() for r in rules))[-12:]


def preferences(root):
    text = read_text(os.path.join(root, "_system", "preferences.md"))
    out = []
    for l in text.splitlines():
        if l.startswith("- ") and len(l) > 6:
            out.append(re.sub(r"\s*<!--.*?-->", "", l[2:]).strip())
    return out[-15:]


def agent_notes(root):
    try:
        from delegate import scorecard
        sc = scorecard(root)
    except Exception:
        return []
    notes = []
    for r in sc:
        if r["common_problems"]:
            notes.append(f"{r['agent']}: watch for {', '.join(r['common_problems'])} (recent average {r['recent_average']:.0%})")
    return notes


def recent_decisions(root, now, days):
    text = read_text(os.path.join(root, "_system", "changelog.md"))
    since = (now - timedelta(days=days)).isoformat()
    out = []
    for l in text.splitlines():
        m = re.match(r"-\s*(\d{4}-\d{2}-\d{2})\s+(.*)", l.strip())
        if m and m.group(1) >= since and re.search(r"supersed|decid|confirm|approv|accepted|changed", m.group(2), re.I):
            out.append(f"{m.group(1)}: {m.group(2)[:160]}")
    return out[-10:]


def build(root, now=None, days=30):
    now = now or today()
    try:
        from identity import load as load_id
        ident = load_id(root)
    except Exception:
        ident = None
    L = ["# Playbook", "",
         f"_Distilled {now.isoformat()} from lessons, preferences, agent scorecards and recent decisions. "
         "Generated: change the sources, not this page._", ""]
    if ident:
        L += [f"**Who we are:** {ident['name']}, {ident['role']} to {ident['owner']}"
              + (f" at {ident['business']}" if ident["business"] else "") + f". Voice: {ident['voice']}.", ""]
    for title, items in (("House rules (from corrections)", lessons(root)),
                         ("How the owner likes things", preferences(root)),
                         ("Agent watch-outs", agent_notes(root)),
                         (f"Recent decisions (last {days} days)", recent_decisions(root, now, days))):
        if items:
            L += [f"## {title}", ""] + [f"- {strip_private(i)}" for i in items] + [""]
    text = "\n".join(L)
    words = text.split()
    if len(words) > MAX_WORDS:  # keep it short enough to read first, every time
        text = " ".join(words[:MAX_WORDS]) + " …"
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    with open(os.path.join(root, "_system", "playbook.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return text


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    from ledger import cli_today
    now = cli_today(args)
    if now is None:
        return 2
    from ledger import cli_int
    days = cli_int(args, "--days", 30)
    if days is None:
        return 2
    text = build(args[0], now, days)
    print(text if "--print" in args else f"Playbook written to _system/playbook.md ({len(text.split())} words).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
