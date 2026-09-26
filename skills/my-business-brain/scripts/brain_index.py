#!/usr/bin/env python3
"""Rebuild INDEX.md and contracts/register.md for a My Business Brain folder.

Usage: python3 brain_index.py <brain-folder> [--today YYYY-MM-DD]
Standard library only.
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, parse_date, today


def cell(v):
    if isinstance(v, list):
        v = ", ".join(v)
    return str(v or "").replace("|", "\\|").replace("\n", " ")


def open_decisions(root):
    path = os.path.join(root, "_system", "decisions-needed.md")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.lstrip().startswith("- [ ]"))


def build(root, now):
    entries = load_brain(root)
    active = [e for e in entries if e["meta"] and not e["archived"]
              and e["meta"].get("status", "active") in ("active", "disputed", "draft")]
    by_domain = defaultdict(list)
    for e in active:
        by_domain[e["meta"].get("domain") or e["folder"]].append(e)

    lines = ["# Brain index", "",
             f"Generated {now.isoformat()} by brain_index.py. Do not edit by hand.", "",
             f"{len(active)} active entries in {len(by_domain)} domains; "
             f"{sum(1 for e in entries if e['archived'])} archived; {open_decisions(root)} open decisions "
             f"(see `_system/decisions-needed.md`).", ""]
    for d in sorted(by_domain):
        lines += [f"## {d}", "", "| Entry | Value | Status | Review by | File |", "|---|---|---|---|---|"]
        for e in sorted(by_domain[d], key=lambda x: str(x["meta"].get("title", "")).lower()):
            m = e["meta"]
            rb = parse_date(m.get("review_by"))
            review = "" if not rb or rb.year >= 9999 else rb.isoformat() + (" ⚠ overdue" if rb < now else "")
            status = m.get("status", "active")
            lines.append(f"| {cell(m.get('title'))} | {cell(m.get('value'))} | {status} | {review} | [{e['file_id']}]({e['path']}) |")
        lines.append("")
    lines += ["## Counts", "", "| Domain | Active entries |", "|---|---|"]
    lines += [f"| {d} | {len(by_domain[d])} |" for d in sorted(by_domain)] + [""]
    with open(os.path.join(root, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    contracts = [e for e in active if e["meta"].get("type") == "contract"]
    rows = []
    for e in contracts:
        m = e["meta"]
        nd = parse_date(m.get("notice_deadline"))
        ed = parse_date(m.get("end_date"))
        nxt = min([d for d in (nd, ed) if d and d >= now], default=None)
        rows.append((nxt or parse_date("9999-12-31"), m, nd, ed, e))
    rows.sort(key=lambda r: r[0])
    reg = ["# Contract register", "",
           f"Generated {now.isoformat()} by brain_index.py. Sorted by the next key date.", ""]
    if rows:
        reg += ["| Contract | Counterparty | Value | End date | Notice deadline | Days to notice | Auto-renew | Calendar | Entry |",
                "|---|---|---|---|---|---|---|---|---|"]
        for _, m, nd, ed, e in rows:
            days = (nd - now).days if nd else None
            dtxt = "" if days is None else (f"{days}" if days >= 0 else f"passed ({-days} days ago)")
            if days is not None and 0 <= days <= 30:
                dtxt = f"**{days}** ⚠"
            reg.append(f"| {cell(m.get('title'))} | {cell(m.get('counterparty'))} | {cell(m.get('value'))} | "
                       f"{ed.isoformat() if ed else ''} | {nd.isoformat() if nd else ''} | {dtxt} | "
                       f"{cell(m.get('auto_renewal'))} | {cell(m.get('calendar'))} | [{e['file_id']}]({e['path']}) |")
    else:
        reg.append("No active contracts recorded yet.")
    reg.append("")
    os.makedirs(os.path.join(root, "contracts"), exist_ok=True)
    with open(os.path.join(root, "contracts", "register.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(reg))
    return len(active), len(contracts)


def main(argv):
    if len(argv) < 2 or argv[1].startswith("-"):
        print(__doc__)
        return 2
    root = argv[1]
    now = today(argv[argv.index("--today") + 1]) if "--today" in argv else today()
    if not os.path.isdir(root):
        print(f"Brain folder not found: {root}")
        return 1
    n, c = build(root, now)
    print(f"INDEX.md rebuilt: {n} active entries. contracts/register.md rebuilt: {c} contracts.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
