#!/usr/bin/env python3
"""My Business Brain morning brief: what the owner needs to know before the day starts.

The Chief of Staff's daily rhythm, alongside the Sunday evening review. It ranks the day's three
priorities (overdue promises first, then near deadlines, then decisions waiting) and lists what
is due this week, what others owe the business, what the agents brought back, and anything the
watch list or leads raised. It reads the brain; it changes nothing.

Usage:
  morning.py <brain> [--today YYYY-MM-DD] [--days 7] [--write] [--json]
--write saves _system/briefs/<date>.md. Standard library only.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, parse_date, today  # noqa: E402
from ledger import due_label  # noqa: E402


def contract_dates(root, now, days=30):
    out = []
    for e in load_brain(root):
        m = e["meta"] or {}
        if e["archived"] or m.get("status") != "active" or m.get("type") != "contract":
            continue
        for field, label in (("notice_deadline", "notice deadline"), ("end_date", "ends"), ("renewal_date", "renews")):
            d = parse_date(m.get(field))
            if d and -7 <= (d - now).days <= days:
                out.append({"date": d.isoformat(), "what": f"{m.get('title')}: {label}", "entry": m.get("id"),
                            "label": due_label(d, now), "decided": bool(str(m.get("decision", "")).strip())})
    return sorted(out, key=lambda x: x["date"])


def gather(root, now, days=7):
    from commitments import items as commits
    from delegations import items as dels
    b = {"date": now.isoformat()}
    c = commits(root, now=now)
    b["we_owe_overdue"] = [r for r in c if r["direction"] == "we-owe" and r.get("due") and r["due"] < now.isoformat()]
    b["we_owe_soon"] = [r for r in c if r["direction"] == "we-owe" and r.get("due") and
                        now.isoformat() <= r["due"] and (parse_date(r["due"]) - now).days <= days]
    b["owed_to_us"] = [r for r in c if r["direction"] == "owed" and r.get("due") and (parse_date(r["due"]) - now).days <= days]
    d = dels(root, now=now)
    b["delegations_overdue"] = [r for r in d if r["overdue"]]
    b["delegations_soon"] = [r for r in d if not r["overdue"] and r.get("due") and (parse_date(r["due"]) - now).days <= days]
    b["contracts"] = contract_dates(root, now)
    dn = os.path.join(root, "_system", "decisions-needed.md")
    b["decisions"] = []
    if os.path.exists(dn):
        with open(dn, encoding="utf-8") as f:
            b["decisions"] = [l.strip()[6:] for l in f if l.lstrip().startswith("- [ ]")]
    try:
        from signals import read as read_signals
        b["leads"] = [r for r in read_signals(root) if r.get("kind") == "lead" and r.get("status") == "open"]
    except Exception:
        b["leads"] = []
    try:
        from delegate import listing
        b["agent_reports"] = [t for t in listing(root) if t.get("status") in ("returned", "partial", "blocked")
                              and t.get("returned", "") >= (now.replace(day=1)).isoformat() and not t.get("reviewed")]
    except Exception:
        b["agent_reports"] = []
    # three priorities, most urgent first
    pri = []
    pri += [f"Overdue promise to {r['party']}: {r['what']} (due {r['due']})" for r in b["we_owe_overdue"]]
    pri += [f"{x['what']} {x['date']} ({x['label']})" + ("" if x["decided"] else ", no decision yet")
            for x in b["contracts"] if "notice" in x["what"] and not x["decided"]]
    pri += [f"Promise due {r['due_label']}: {r['what']} (to {r['party']})" for r in b["we_owe_soon"]]
    pri += [f"Decision waiting: {x[:120]}" for x in b["decisions"][:3]]
    pri += [f"Chase {r['owner']}: {r['task']} ({r['due_label']})" for r in b["delegations_overdue"]]
    b["priorities"] = pri[:3]
    return b


def render(b, ident=None):
    who = f"{ident['name']} for {ident['owner']}" if ident else "Your Chief of Staff"
    L = [f"# Morning brief: {b['date']}", "", f"_{who}_", "", "## Today's three"]
    L += [f"{i}. {p}" for i, p in enumerate(b["priorities"], 1)] or ["Nothing urgent. A good day to get ahead."]
    L += ["", "## Coming up"]
    rows = [f"- We owe {r['party']}: {r['what']} ({r['due_label']})" for r in b["we_owe_overdue"] + b["we_owe_soon"]]
    rows += [f"- {x['what']}: {x['date']} ({x['label']})" for x in b["contracts"]]
    rows += [f"- {r['owner']}: {r['task']} ({r['due_label']})" for r in b["delegations_overdue"] + b["delegations_soon"]]
    L += rows or ["- Nothing due."]
    L += ["", "## Waiting on others"]
    L += [f"- {r['party']}: {r['what']} ({r['due_label']})" for r in b["owed_to_us"]] or ["- Nobody owes us anything this week."]
    L += ["", "## Also"]
    also = []
    if b["decisions"]:
        also.append(f"- {len(b['decisions'])} decision(s) waiting in `_system/decisions-needed.md`")
    if b["leads"]:
        also.append(f"- {len(b['leads'])} open lead(s) to confirm or dismiss (not facts)")
    if b["agent_reports"]:
        also.append(f"- {len(b['agent_reports'])} agent report(s) back for review: "
                    + ", ".join(f"{t['id']} ({t['agent']}, score {t.get('score', '?')})" for t in b["agent_reports"][:4]))
    L += also or ["- Nothing else."]
    L += ["", "Nothing here was sent, paid or changed. Say the word and I'll draft, chase or prepare any of it."]
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
    from ledger import cli_int
    days = cli_int(args, "--days", 7)
    if days is None:
        return 2
    b = gather(root, now, days)
    try:
        from identity import load as load_id
        ident = load_id(root)
    except Exception:
        ident = None
    if "--json" in args:
        print(json.dumps(b, indent=2, ensure_ascii=False))
        return 0
    text = render(b, ident)
    if "--write" in args:
        d = os.path.join(root, "_system", "briefs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{now.isoformat()}.md"), "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
