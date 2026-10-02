#!/usr/bin/env python3
"""My Business Brain meeting prep: one page before you meet someone.

Gathers what the brain knows about the person or company, the promises open in both
directions, what was sent to them before (from the answer log), decisions and leads that
mention them, contract dates coming up, and a suggested agenda. Confidential facts are marked;
use --audience team when the pack is for a colleague.

Usage:
  meeting_prep.py <brain> --with "Supplier X" [--topic "renewal"] [--audience owner|team] [--today YYYY-MM-DD] [--write]
--write saves _system/briefings/meeting-<name>-<date>.md. Standard library only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import fold, strip_private, today  # noqa: E402


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", fold(s).lower()).strip("-")[:40] or "meeting"


def mentions(text, name):
    return fold(name).lower() in fold(str(text)).lower()


def prep(root, who, topic="", audience="owner", now=None):
    now = now or today()
    who = strip_private(who or "").strip()
    if not who:
        return {"error": "say who the meeting is with (--with)"}
    audience = str(audience or "owner").strip().lower()
    if audience not in ("owner", "team", "external"):
        return {"error": "audience must be owner, team or external"}
    p = {"with": who, "topic": topic, "date": now.isoformat(), "audience": audience}
    from brain_search import search
    from lexicon import find
    hits = find(root, who + " " + topic)
    ids = {e for h in hits for e in h["entries"]}
    aud = {"owner": "internal", "team": "team", "external": "external"}[audience]
    res = search(root, [q for q in (who, f"{who} {topic}".strip(), topic) if q], top=10, audience=aud)
    facts = [r for r in res if r["kind"] == "entry"]
    for r in facts:
        ids.add(r["id"])
    p["facts"] = [{"id": r["id"], "title": r["title"], "value": r.get("value", ""), "flags": r.get("flags", []),
                   "sensitivity": r.get("sensitivity", "")} for r in facts]
    from commitments import items as commits
    p["we_owe"] = [r for r in commits(root, now=now) if r["direction"] == "we-owe" and mentions(r["party"] + " " + r["what"], who)]
    p["they_owe"] = [r for r in commits(root, now=now) if r["direction"] == "owed" and mentions(r["party"] + " " + r["what"], who)]
    try:
        from impact import read_log
        p["sent_before"] = [{"date": r["at"][:10], "kind": r["kind"], "purpose": r["purpose"]}
                            for r in read_log(root) if mentions(r.get("recipient", ""), who)][-5:]
    except Exception:
        p["sent_before"] = []
    dn = os.path.join(root, "_system", "decisions-needed.md")
    p["decisions"] = []
    if os.path.exists(dn):
        with open(dn, encoding="utf-8") as f:
            p["decisions"] = [l.strip()[6:] for l in f if l.lstrip().startswith("- [ ]") and
                              (mentions(l, who) or any(i in l for i in ids))]
    try:
        from signals import read as read_signals
        p["leads"] = [r for r in read_signals(root) if r.get("status") == "open" and
                      (mentions(r.get("summary", "") + " " + r.get("topic", ""), who))]
    except Exception:
        p["leads"] = []
    from morning import contract_dates
    p["dates"] = [x for x in contract_dates(root, now, 120) if x["entry"] in ids or mentions(x["what"], who)]
    if audience != "owner":
        # a pack for a colleague or an outsider: nothing that would give a confidential fact away
        from brainlib import confidential_markers, mentions_confidential
        mk = confidential_markers(root)
        safe = lambda *parts: not mentions_confidential(" ".join(str(x) for x in parts), mk)
        p["facts"] = [f for f in p["facts"] if f["sensitivity"] != "confidential" and safe(f["id"], f["value"])]
        p["we_owe"] = [r for r in p["we_owe"] if safe(r["what"], r.get("entry", ""))]
        p["they_owe"] = [r for r in p["they_owe"] if safe(r["what"], r.get("entry", ""))]
        p["decisions"] = [d for d in p["decisions"] if safe(d)]
        p["sent_before"] = [x for x in p["sent_before"] if safe(x["purpose"])]
        p["leads"] = [r for r in p["leads"] if safe(r.get("summary", ""))]
        p["dates"] = [x for x in p["dates"] if (x["entry"] or "").lower() not in mk["ids"] and safe(x["what"])]
        if audience == "external":
            p["decisions"], p["leads"], p["sent_before"] = [], [], []
    agenda = []
    agenda += [f"Our promise: {r['what']} ({r['due_label']})" for r in p["we_owe"]]
    agenda += [f"Their promise: {r['what']} ({r['due_label']})" for r in p["they_owe"]]
    agenda += [f"{x['what']} on {x['date']}: decide before the meeting ends" for x in p["dates"] if "notice" in x["what"]]
    agenda += [f"Decision: {d[:120]}" for d in p["decisions"][:3]]
    agenda += [f"Check quietly: {r['summary'][:100]} (a lead, not confirmed)" for r in p["leads"][:2]]
    if topic:
        agenda.append(f"Topic: {topic}")
    agenda.append("Agree next steps, owners and dates (I'll record them as commitments)")
    p["agenda"] = agenda
    return p


def render(p):
    L = [f"# Meeting prep: {p['with']}" + (f" ({p['topic']})" if p["topic"] else ""), "",
         f"Prepared {p['date']} for the {p['audience']}." + (" Confidential facts are marked; don't share this page."
                                                              if p["audience"] == "owner" else
                                                              " Confidential facts have been left out."), "",
         "## Suggested agenda"] + [f"{i}. {a}" for i, a in enumerate(p["agenda"], 1)]
    L += ["", "## What the brain knows"]
    L += [f"- [[{f['id']}]] {f['title']}" + (f" = {f['value']}" if f["value"] else "")
          + (" (confidential)" if f["sensitivity"] == "confidential" else "") for f in p["facts"]] or ["- Nothing yet."]
    L += ["", "## Promises"]
    L += [f"- We owe: {r['what']} ({r['due_label']})" for r in p["we_owe"]]
    L += [f"- They owe: {r['what']} ({r['due_label']})" for r in p["they_owe"]]
    if not (p["we_owe"] or p["they_owe"]):
        L.append("- None open.")
    if p["dates"]:
        L += ["", "## Dates"] + [f"- {x['what']}: {x['date']} ({x['label']})" for x in p["dates"]]
    if p["sent_before"]:
        L += ["", "## Sent to them before"] + [f"- {s['date']} {s['kind']}: {s['purpose']}" for s in p["sent_before"]]
    if p["leads"]:
        L += ["", "## Leads (not confirmed)"] + [f"- {r['summary']} ({r.get('source', '')})" for r in p["leads"]]
    return "\n".join(L) + "\n"


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    from ledger import cli_today
    now = cli_today(args)
    if now is None:
        return 2
    p = prep(root, val("--with"), val("--topic"), val("--audience", "owner"), now)
    if "error" in p:
        print(json.dumps(p))
        return 1
    if "--json" in args:
        print(json.dumps(p, indent=2, ensure_ascii=False))
        return 0
    text = render(p)
    if "--write" in args:
        d = os.path.join(root, "_system", "briefings")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"meeting-{slug(p['with'])}-{now.isoformat()}.md"), "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
