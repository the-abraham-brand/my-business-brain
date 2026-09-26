#!/usr/bin/env python3
"""My Business Brain snapshots and diff: what changed in the business's knowledge.

A snapshot is a compact record of every entry (key, value, status, sensitivity) and the
health score on a given day. Comparing the brain with an earlier snapshot shows what was
added, changed, superseded or archived, and flags unstable facts: values that keep changing,
or change and then change back, which usually means two sources disagree.

Usage:
  brain_diff.py snapshot <brain> [--today YYYY-MM-DD]          save _system/snapshots/<date>.json
  brain_diff.py diff <brain> [--since YYYY-MM-DD] [--write] [--json] [--today YYYY-MM-DD]
        compare the brain now with the snapshot on or before --since (default: 7 days ago,
        else the oldest); --write saves _system/digests/<date>-brain-diff.md
  brain_diff.py unstable <brain> [--json]                        facts that flip-flop across snapshots
The health check saves one snapshot a day automatically. Standard library only.
"""
import json
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, norm, sensitivity_of, today  # noqa: E402


def snap_dir(root):
    return os.path.join(root, "_system", "snapshots")


def capture(root, now, score=None):
    entries = {}
    for e in load_brain(root):
        m = e["meta"]
        if not m:
            continue
        eid = m.get("id") or e["file_id"]
        entries[eid] = {"title": m.get("title", ""), "key": m.get("key", ""), "value": m.get("value", ""),
                        "status": "archived" if e["archived"] and m.get("status") == "active" else m.get("status", "active"),
                        "domain": m.get("domain", ""), "sensitivity": sensitivity_of(m),
                        "review_by": m.get("review_by", "")}
    return {"date": now.isoformat(), "score": score, "entries": entries}


def save_snapshot(root, now, score=None):
    os.makedirs(snap_dir(root), exist_ok=True)
    snap = capture(root, now, score)
    path = os.path.join(snap_dir(root), f"{now.isoformat()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False)
    return path


def list_snapshots(root):
    d = snap_dir(root)
    if not os.path.isdir(d):
        return []
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def load_snapshot(root, day):
    with open(os.path.join(snap_dir(root), f"{day}.json"), encoding="utf-8") as f:
        return json.load(f)


def compare(old, new):
    o, n = old["entries"], new["entries"]
    out = {"from": old["date"], "to": new["date"], "score_from": old.get("score"), "score_to": new.get("score"),
           "added": [], "changed": [], "retired": [], "restored": [], "relabelled": [], "removed": []}
    for eid, e in n.items():
        if eid not in o:
            if e["status"] in ("active", "draft", "disputed"):
                out["added"].append({"id": eid, "title": e["title"], "value": e["value"]})
            continue
        p = o[eid]
        if norm(p["value"]) != norm(e["value"]):
            out["changed"].append({"id": eid, "title": e["title"], "from": p["value"], "to": e["value"]})
        if p["status"] in ("active", "draft", "disputed") and e["status"] in ("superseded", "archived"):
            out["retired"].append({"id": eid, "title": e["title"], "value": e["value"], "status": e["status"]})
        elif p["status"] in ("superseded", "archived") and e["status"] in ("active", "draft", "disputed"):
            out["restored"].append({"id": eid, "title": e["title"]})
        if p["sensitivity"] != e["sensitivity"]:
            out["relabelled"].append({"id": eid, "title": e["title"], "from": p["sensitivity"], "to": e["sensitivity"]})
    for eid, p in o.items():
        if eid not in n:
            out["removed"].append({"id": eid, "title": p["title"]})
    # A key whose active value changed between the two snapshots (new entry superseding an old one)
    def active_by_key(entries):
        r = {}
        for eid, e in entries.items():
            if e["key"] and e["status"] in ("active", "disputed"):
                r[e["key"].lower()] = (eid, e)
        return r
    ok, nk = active_by_key(o), active_by_key(n)
    for k, (eid, e) in nk.items():
        if k in ok and norm(ok[k][1]["value"]) != norm(e["value"]) and ok[k][0] != eid:
            out["changed"].append({"id": eid, "title": e["title"], "from": ok[k][1]["value"], "to": e["value"],
                                   "replaces": ok[k][0]})
    replacing = {c["id"] for c in out["changed"] if c.get("replaces")}
    out["added"] = [a for a in out["added"] if a["id"] not in replacing]
    return out


def unstable(root, now):
    """Keys whose active value changed at least twice, or changed and changed back."""
    days = list_snapshots(root)
    series = {}
    snaps = [load_snapshot(root, d) for d in days] + [capture(root, now)]
    for s in snaps:
        for eid, e in s["entries"].items():
            if e["key"] and e["status"] in ("active", "disputed"):
                series.setdefault(e["key"].lower(), []).append((s["date"], e["value"], e["title"]))
    out = []
    for k, seq in series.items():
        vals = []
        for day, v, title in seq:
            if not vals or norm(vals[-1][1]) != norm(v):
                vals.append((day, v, title))
        changes = len(vals) - 1
        seen, flip = [], False
        for _, v, _ in vals:
            if norm(v) in seen and norm(v) != (seen[-1] if seen else None):
                flip = True
            seen.append(norm(v))
        if changes >= 2 or flip:
            out.append({"key": k, "title": vals[-1][2], "changes": changes, "flip_flop": flip,
                        "history": [{"date": d, "value": v} for d, v, _ in vals]})
    return out


def markdown(d, flips):
    lines = [f"# What changed in the brain: {d['from']} to {d['to']}", ""]
    if d.get("score_from") is not None and d.get("score_to") is not None:
        lines += [f"Health score: {d['score_from']:g} → {d['score_to']:g}", ""]
    def section(title, items, fmt):
        if items:
            lines.extend([f"## {title} ({len(items)})", ""] + [f"- {fmt(i)}" for i in items] + [""])
    section("Added", d["added"], lambda i: f"{i['title']}" + (f": {i['value']}" if i["value"] else ""))
    section("Changed", d["changed"], lambda i: f"{i['title']}: {i['from']} → {i['to']}")
    section("Superseded or archived", d["retired"], lambda i: f"{i['title']}" + (f" ({i['value']})" if i["value"] else ""))
    section("Sensitivity relabelled", d["relabelled"], lambda i: f"{i['title']}: {i['from']} → {i['to']}")
    section("Restored", d["restored"], lambda i: i["title"])
    section("Removed from the folder", d["removed"], lambda i: f"{i['title']} (entries should be archived, not deleted)")
    section("Unstable facts", flips, lambda f: f"{f['title']}: " + " → ".join(h["value"] for h in f["history"])
            + (" (changed back and forth: check which source is right)" if f["flip_flop"] else ""))
    if len(lines) <= 4:
        lines.append("No changes.")
    return "\n".join(lines) + "\n"


def arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0] not in ("snapshot", "diff", "unstable"):
        print(__doc__)
        return 2
    cmd, root = args[0], args[1]
    now = today(arg(args, "--today")) if "--today" in args else today()
    if not os.path.isdir(root):
        print(f"Brain folder not found: {root}")
        return 2
    if cmd == "snapshot":
        print(save_snapshot(root, now))
        return 0
    if cmd == "unstable":
        u = unstable(root, now)
        print(json.dumps(u, indent=2, ensure_ascii=False) if "--json" in args else
              ("\n".join(f"- {f['title']}: " + " → ".join(h['value'] for h in f['history']) for f in u) or "No unstable facts."))
        return 0
    days = [d for d in list_snapshots(root) if d < now.isoformat()] or list_snapshots(root)
    if not days:
        print("No snapshot yet. Run `brain_diff.py snapshot <brain>` (the health check also saves one a day).")
        return 1
    since = arg(args, "--since") or (now - timedelta(days=7)).isoformat()
    base = [d for d in days if d <= since]
    old = load_snapshot(root, base[-1] if base else days[0])
    new = capture(root, now)
    d = compare(old, new)
    flips = unstable(root, now)
    if "--json" in args:
        print(json.dumps({"diff": d, "unstable": flips}, indent=2, ensure_ascii=False))
    else:
        md = markdown(d, flips)
        print(md)
        if "--write" in args:
            out_dir = os.path.join(root, "_system", "digests")
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, f"{now.isoformat()}-brain-diff.md"), "w", encoding="utf-8") as f:
                f.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
