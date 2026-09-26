#!/usr/bin/env python3
"""My Business Brain answer log and impact alerts.

Every answer, email, proposal or report the brain helps produce is logged with the entries
and values it relied on (cite_check.py --log does this once the draft passes). When a fact
later changes (superseded, archived, value corrected), this script lists every past output
that used the old value: "3 proposals in September quoted the Scale plan at AED 14,999,
which has since been replaced by AED 15,999". The user can then follow up with the people
who received them.

Usage:
  impact.py <brain> [--json]                 list outputs that relied on facts that have since changed
  impact.py <brain> --ack ENTRY_ID           the user has dealt with those outputs: stop reporting them
  impact.py <brain> --log FILE.json          add a record by hand: {"kind","purpose","recipient","audience","citations":[ids]}
Standard library only.
"""
import hashlib
import json
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, norm, strip_private  # noqa: E402

KINDS = ("answer", "email", "proposal", "quote", "report", "post", "document", "other")


def log_path(root):
    return os.path.join(root, "_system", "answer-log.jsonl")


def acks_path(root):
    return os.path.join(root, "_system", "impact-acks.json")


def entry_hash(meta, body):
    return hashlib.sha256((str(meta.get("value", "")) + "\n" + body.strip()).encode("utf-8")).hexdigest()[:12]


def log_output(root, citations, kind="answer", purpose="", recipient="", audience="internal", when=None):
    """Record which entries (and their values at the time) an output relied on."""
    ents = {(e["meta"].get("id") or e["file_id"]): e for e in load_brain(root) if e["meta"]}
    cites = []
    for c in dict.fromkeys(citations):  # keep order, drop repeats
        if c.startswith("sources/") or "#L" in c:
            cites.append({"id": c})
            continue
        e = ents.get(c)
        if not e:
            continue
        m = e["meta"]
        cites.append({"id": c, "key": m.get("key", ""), "value": m.get("value", ""),
                      "status": m.get("status", "active"), "hash": entry_hash(m, e["body"])})
    purpose, recipient = strip_private(purpose or ""), strip_private(recipient or "")
    rec = {"id": "a-" + uuid.uuid4().hex[:10],
           "at": when or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "kind": kind if kind in KINDS else "other", "purpose": purpose[:200], "recipient": recipient[:120],
           "audience": audience, "citations": cites}
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    with open(log_path(root), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read_log(root):
    out = []
    if os.path.exists(log_path(root)):
        with open(log_path(root), encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def load_acks(root):
    try:
        with open(acks_path(root), encoding="utf-8") as f:
            return set(json.load(f))
    except (OSError, ValueError):
        return set()


def find_impacts(root):
    """Group past outputs by the cited entry whose fact has changed since."""
    entries = [e for e in load_brain(root) if e["meta"]]
    by_id = {(e["meta"].get("id") or e["file_id"]): e for e in entries}
    current_by_key = {}
    for e in entries:
        m = e["meta"]
        if m.get("key") and not e["archived"] and m.get("status", "active") in ("active", "disputed"):
            current_by_key[str(m["key"]).lower()] = e
    acks = load_acks(root)
    groups = defaultdict(lambda: {"outputs": []})
    for rec in read_log(root):
        for c in rec.get("citations", []):
            cid = c.get("id", "")
            if not c.get("hash") or f"{rec['id']}:{cid}" in acks:
                continue
            e = by_id.get(cid)
            m = (e or {}).get("meta") or {}
            reason, now_value, now_entry = None, None, None
            cur = current_by_key.get(str(c.get("key", "")).lower()) if c.get("key") else None
            if cur is not None and norm(cur["meta"].get("value", "")) != norm(c.get("value", "")):
                reason = "value changed"
                now_value, now_entry = cur["meta"].get("value", ""), cur["meta"].get("id")
            elif cur is not None and cur["meta"].get("id") != cid:
                pass  # replaced by a new entry with the same value: the output is still right
            else:
                if not e:
                    reason = "entry no longer exists"
                elif e["archived"] or m.get("status") in ("superseded", "archived"):
                    reason = f"entry {m.get('status', 'archived')} with no current replacement"
                elif m.get("status") == "disputed":
                    reason = "entry now disputed"
                elif entry_hash(m, e["body"]) != c["hash"] and norm(m.get("value", "")) != norm(c.get("value", "")):
                    reason = "value corrected"
                    now_value, now_entry = m.get("value", ""), cid
            if reason is None:
                continue
            g = groups[cid]
            g.update({"entry": cid, "title": m.get("title", cid), "old_value": c.get("value", ""),
                      "now_value": now_value, "now_entry": now_entry, "reason": reason})
            g["outputs"].append({"id": rec["id"], "at": rec["at"][:10], "kind": rec.get("kind"),
                                 "purpose": rec.get("purpose", ""), "recipient": rec.get("recipient", ""),
                                 "audience": rec.get("audience", "")})
    return sorted(groups.values(), key=lambda g: -len(g["outputs"]))


def ack(root, entry_id):
    acks = load_acks(root)
    n = 0
    for rec in read_log(root):
        for c in rec.get("citations", []):
            if c.get("id") == entry_id:
                acks.add(f"{rec['id']}:{entry_id}")
                n += 1
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    with open(acks_path(root), "w", encoding="utf-8") as f:
        json.dump(sorted(acks), f, indent=1)
    return {"acknowledged": n, "entry": entry_id}


def describe(g):
    who = "; ".join(f"{o['kind']}" + (f" to {o['recipient']}" if o["recipient"] else "") + f" ({o['at']})"
                    for o in g["outputs"][:5])
    more = f" and {len(g['outputs']) - 5} more" if len(g["outputs"]) > 5 else ""
    change = f"now {g['now_value']}" if g.get("now_value") else g["reason"]
    return (f"{len(g['outputs'])} past output(s) used {g['title']} = {g['old_value']} ({change}): {who}{more}")


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    if not os.path.isdir(root):
        print(f"Brain folder not found: {root}")
        return 2
    if "--ack" in args:
        print(json.dumps(ack(root, args[args.index("--ack") + 1]), indent=2))
        return 0
    if "--log" in args:
        with open(args[args.index("--log") + 1], encoding="utf-8") as f:
            spec = json.load(f)
        rec = log_output(root, spec.get("citations", []), spec.get("kind", "answer"), spec.get("purpose", ""),
                         spec.get("recipient", ""), spec.get("audience", "internal"), spec.get("at"))
        print(json.dumps(rec, indent=2, ensure_ascii=False))
        return 0
    groups = find_impacts(root)
    if "--json" in args:
        print(json.dumps(groups, indent=2, ensure_ascii=False))
    elif not groups:
        print("No past outputs rely on facts that have changed.")
    else:
        print(f"{sum(len(g['outputs']) for g in groups)} past output(s) rely on facts that have changed:")
        for g in groups:
            print("- " + describe(g))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
