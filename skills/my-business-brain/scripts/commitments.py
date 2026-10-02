#!/usr/bin/env python3
"""My Business Brain commitments: every promise the business made, and every promise it is owed.

A Chief of Staff's first job is making sure nothing promised slips. Commitments run both ways:
  we-owe    "We'll send Supplier X our answer by Thursday"
  owed      "Sara will send the Q3 numbers by the 15th"

The scan reads a message or meeting notes and proposes commitments it finds ("I'll send the
revised quote by Friday"); nothing is recorded until the owner agrees.

Usage:
  commitments.py <brain> add --what "..." (--to NAME | --from NAME) [--due "Thursday" | --due 2026-10-15]
                             [--source "..."] [--entry ID]
  commitments.py <brain> list [--overdue] [--within 7] [--with NAME] [--all] [--json]   open ones unless --all
  commitments.py <brain> done ID [--note "..."]
  commitments.py <brain> cancel ID [--note "..."]
  commitments.py <brain> scan --text "..." | FILE    propose commitments found in text (stores nothing)
Private passages are never stored. Standard library only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import fold, strip_private, today  # noqa: E402
from ledger import Ledger, when, due_label, cli_today, cli_int  # noqa: E402

PROMISE = re.compile(
    r"\b(i'll|i will|we'll|we will|i can|we can|i'm going to|we're going to|let me|i promise|we promise)\s+"
    r"(send|share|get back|come back|confirm|deliver|call|email|reply|review|prepare|finish|pay|sign|update|follow up|check)"
    r"[^.!?\n]{0,120}", re.I)
OWED = re.compile(
    r"\b([A-Z][a-z]+|they|he|she|the supplier|the client)\s+(will|'ll|promised to|said (they|he|she)'d)\s+"
    r"(send|share|get back|confirm|deliver|call|email|reply|pay|sign|update)[^.!?\n]{0,120}")
AR_PROMISE = re.compile(r"(سأرسل|سنرسل|سأرد|سنرد|سأتصل|سنؤكد|سأؤكد|سنسلم|سأراجع)[^.!؟\n]{0,120}")


def ledger(root):
    return Ledger(root, "commitments", "c-")


def add(root, what, to="", frm="", due="", source="", entry="", now=None):
    now = now or today()
    what = strip_private(what or "").strip()
    if not what:
        return {"error": "say what was promised (--what)"}
    if bool(to) == bool(frm):
        return {"error": "give --to NAME (we owe them) or --from NAME (they owe us), not both"}
    d = when(due, now) if due else when(what, now)
    rec = {"id": ledger(root).new_id(), "what": what[:300], "direction": "we-owe" if to else "owed",
           "party": strip_private(to or frm).strip()[:80], "due": d.isoformat() if d else "",
           "source": strip_private(source)[:200], "entry": entry, "status": "open", "added": now.isoformat()}
    ledger(root).append(rec)
    render(root, now)
    return rec


def items(root, only_open=True, overdue=False, within=None, party="", now=None):
    now = now or today()
    out = []
    for r in ledger(root).read():
        if only_open and r.get("status") != "open":
            continue
        d = when(r.get("due"), now) if r.get("due") else None
        if overdue and not (d and d < now):
            continue
        if within is not None and not (d and (d - now).days <= within):
            continue
        if party and fold(party).lower() not in fold(r.get("party", "")).lower():
            continue
        out.append({**r, "due_label": due_label(d, now)})
    return sorted(out, key=lambda r: r.get("due") or "9999")


def render(root, now=None):
    now = now or today()
    rows = items(root, now=now)
    lines = ["# Commitments", "", "Promises the business made, and promises it is owed. Kept by the Chief of Staff.", ""]
    for direction, title in (("we-owe", "We owe"), ("owed", "Owed to us")):
        rs = [r for r in rows if r["direction"] == direction]
        lines += [f"## {title} ({len(rs)})", ""]
        lines += [f"- [{r['id']}] {r['what']} ({'to' if direction == 'we-owe' else 'from'} {r['party']}; "
                  f"{r['due'] or 'no date'}, {r['due_label']})" for r in rs] or ["- Nothing open."]
        lines.append("")
    with open(os.path.join(root, "_system", "commitments.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def scan(text, now=None):
    """Commitments a message seems to make or record. Proposals only."""
    now = now or today()
    text = strip_private(text or "")
    out = []
    for m in PROMISE.finditer(text):
        s = m.group(0).strip()
        d = when(s, now)
        out.append({"direction": "we-owe", "what": s, "due": d.isoformat() if d else ""})
    for m in AR_PROMISE.finditer(text):
        s = m.group(0).strip()
        d = when(s, now)
        out.append({"direction": "we-owe", "what": s, "due": d.isoformat() if d else ""})
    for m in OWED.finditer(text):
        s = m.group(0).strip()
        if s.lower().startswith(("i ", "we ")):
            continue
        d = when(s, now)
        out.append({"direction": "owed", "what": s, "party": m.group(1), "due": d.isoformat() if d else ""})
    seen, uniq = set(), []
    for c in out:
        if c["what"] not in seen:
            seen.add(c["what"])
            uniq.append(c)
    return uniq


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
        out = add(root, val("--what"), val("--to"), val("--from"), val("--due"), val("--source"), val("--entry"), now)
    elif cmd == "list":
        within = cli_int(args, "--within", None) if "--within" in args else None
        if "--within" in args and within is None:
            return 2
        rows = items(root, "--all" not in args, "--overdue" in args, within, val("--with"), now)
        if "--json" in args:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            print("\n".join(f"- [{r['id']}] {'We owe' if r['direction'] == 'we-owe' else 'Owed by'} {r['party']}: "
                            f"{r['what']} ({r['due_label']})" for r in rows) or "No open commitments.")
        return 0
    elif cmd in ("done", "cancel") and len(args) > 2:
        out = ledger(root).update(args[2], status="done" if cmd == "done" else "cancelled",
                                  note=strip_private(val("--note")), closed=now.isoformat())
        if "error" not in out:
            render(root, now)
    elif cmd == "scan":
        if "--text" in args:
            text = val("--text")
        elif len(args) > 2:
            try:
                with open(args[2], encoding="utf-8") as f:
                    text = f.read()
            except OSError as e:
                print(f"Cannot read {args[2]}: {e.strerror}")
                return 2
        else:
            print(__doc__)
            return 2
        print(json.dumps(scan(text, now), indent=2, ensure_ascii=False))
        return 0
    else:
        print(__doc__)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if "error" in out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
