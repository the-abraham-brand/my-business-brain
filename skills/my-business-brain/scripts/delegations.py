#!/usr/bin/env python3
"""My Business Brain delegation queue: work handed to people or to the brain's agents, with owners
and due dates, so the Chief of Staff can follow up before anything stalls.

Usage:
  delegations.py <brain> add --task "..." --owner "Sara" [--due "Thursday"] [--plan r-xxxx] [--note "..."]
  delegations.py <brain> list [--overdue] [--owner NAME] [--all] [--json]   open ones unless --all
  delegations.py <brain> update ID --status open|in-progress|blocked|done [--note "..."]
  delegations.py <brain> nudges            overdue or blocked items, with a suggested follow-up line each
Private passages are never stored. Standard library only.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import fold, strip_private, today  # noqa: E402
from ledger import Ledger, when, due_label, cli_today, cli_int  # noqa: E402

STATUSES = ("open", "in-progress", "blocked", "done")


def ledger(root):
    return Ledger(root, "delegations", "d-")


def add(root, task, owner, due="", plan="", note="", now=None):
    now = now or today()
    task, owner = strip_private(task or "").strip(), strip_private(owner or "").strip()
    if not task or not owner:
        return {"error": "a task and an owner are needed"}
    d = when(due, now) if due else None
    rec = {"id": ledger(root).new_id(), "task": task[:300], "owner": owner[:80], "due": d.isoformat() if d else "",
           "plan": strip_private(plan or "")[:40], "status": "open", "added": now.isoformat(), "note": strip_private(note)[:300]}
    ledger(root).append(rec)
    render(root, now)
    return rec


def items(root, only_open=True, overdue=False, owner="", now=None):
    now = now or today()
    out = []
    for r in ledger(root).read():
        if only_open and r.get("status") == "done":
            continue
        d = when(r.get("due"), now) if r.get("due") else None
        if overdue and not (d and d < now):
            continue
        if owner and fold(owner).lower() not in fold(r.get("owner", "")).lower():
            continue
        out.append({**r, "due_label": due_label(d, now), "overdue": bool(d and d < now)})
    return sorted(out, key=lambda r: (r.get("due") or "9999", r["owner"]))


def nudges(root, now=None):
    out = []
    for r in items(root, now=now):
        if r["overdue"] or r.get("status") == "blocked":
            line = (f"Hi {r['owner'].split()[0]}, where are we on \"{r['task'][:80]}\"? It was due {r['due']}. "
                    "Anything you need from me?") if r["overdue"] else \
                   (f"Hi {r['owner'].split()[0]}, you flagged \"{r['task'][:80]}\" as blocked. What would unblock it?")
            out.append({**r, "suggested_follow_up": line})
    return out


def render(root, now=None):
    rows = items(root, now=now)
    lines = ["# Delegations", "", "Work handed to people or agents, with owners and due dates.", ""]
    lines += [f"- [{r['id']}] {r['task']}: {r['owner']}, {r['status']}, {r['due'] or 'no date'} ({r['due_label']})"
              for r in rows] or ["- Nothing open."]
    with open(os.path.join(root, "_system", "delegations.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0].startswith("-"):
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    now = cli_today(args)
    if now is None:
        return 2
    if cmd == "add":
        out = add(root, val("--task"), val("--owner"), val("--due"), val("--plan"), val("--note"), now)
    elif cmd == "list":
        rows = items(root, "--all" not in args, "--overdue" in args, val("--owner"), now)
        if "--json" in args:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            print("\n".join(f"- [{r['id']}] {r['owner']}: {r['task']} ({r['status']}, {r['due_label']})" for r in rows)
                  or "Nothing delegated and open.")
        return 0
    elif cmd == "update" and len(args) > 2:
        st = val("--status")
        if st not in STATUSES:
            print(json.dumps({"error": f"status must be one of {STATUSES}"}))
            return 1
        out = ledger(root).update(args[2], status=st, note=strip_private(val("--note")), updated=now.isoformat())
        if "error" not in out:
            render(root, now)
    elif cmd == "nudges":
        print(json.dumps(nudges(root, now), indent=2, ensure_ascii=False))
        return 0
    else:
        print(__doc__)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if "error" in out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
