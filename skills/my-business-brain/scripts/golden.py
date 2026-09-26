#!/usr/bin/env python3
"""My Business Brain golden questions: catch knowledge regressions.

Golden questions are the questions the business relies on ("What is our refund window?",
"What does the Growth plan cost?"), each with the entry and value that should answer it.
Every health check replays them through the brain's search. If a bulk load, merge or edit
changes which entry answers a question, or changes the answer itself, it is reported as a
knowledge regression, so nothing the business depends on changes silently. No model calls:
the same brain always gives the same result.

Usage:
  golden.py add     <brain> --q "What is our refund window?" [--q "refund days"] --expect-entry ID [--expect-value "14 days"]
  golden.py list    <brain>
  golden.py check   <brain> [--json]          exit 1 when a regression is found
  golden.py accept  <brain> --id G            the change was intended: make the current answer the new baseline
  golden.py remove  <brain> --id G
  golden.py propose <brain> [--min 2]         suggest golden questions from the answer log
Standard library only.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, norm, today  # noqa: E402
from brain_search import search  # noqa: E402

TOP = 3


def path_of(root):
    return os.path.join(root, "_system", "golden-questions.json")


def load(root):
    try:
        with open(path_of(root), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def save(root, items):
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    with open(path_of(root), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def entries_by_id(root):
    return {(e["meta"].get("id") or e["file_id"]): e for e in load_brain(root) if e["meta"]}


def current_for_key(root, key):
    for e in load_brain(root):
        m = e["meta"]
        if m and not e["archived"] and str(m.get("key", "")).lower() == str(key).lower() \
                and m.get("status", "active") in ("active", "disputed"):
            return e
    return None


def add(root, queries, entry, value=None):
    items = load(root)
    ents = entries_by_id(root)
    if entry not in ents:
        return {"error": f"entry '{entry}' not found"}
    m = ents[entry]["meta"]
    gid = f"g{max([int(x['id'][1:]) for x in items if x['id'][1:].isdigit()] + [0]) + 1}"
    item = {"id": gid, "question": queries[0], "queries": queries, "expect_entry": entry,
            "expect_key": m.get("key", ""), "expect_value": value if value is not None else m.get("value", ""),
            "added": date.today().isoformat()}
    items.append(item)
    save(root, items)
    return {"added": item}


def check(root, now=None):
    now = now or today()
    ents = entries_by_id(root)
    results = []
    for g in load(root):
        res = search(root, g.get("queries") or [g["question"]], top=TOP, use_sources=False, now=now)
        top_ids = [r["id"] for r in res]
        exp = g["expect_entry"]
        e = ents.get(exp)
        m = (e or {}).get("meta") or {}
        problems = []
        now_answer = None
        if not e:
            problems.append(f"expected entry '{exp}' no longer exists")
        elif e["archived"] or m.get("status") in ("superseded", "archived"):
            problems.append(f"'{exp}' is now {m.get('status', 'archived')}")
        if g.get("expect_key"):
            cur = current_for_key(root, g["expect_key"])
            if cur is not None:
                now_answer = {"entry": cur["meta"].get("id"), "value": cur["meta"].get("value", "")}
                if cur["meta"].get("id") != exp:
                    problems.append(f"now answered by '{cur['meta'].get('id')}'")
                if g.get("expect_value") and norm(cur["meta"].get("value", "")) != norm(g["expect_value"]):
                    problems.append(f"answer changed from \"{g['expect_value']}\" to \"{cur['meta'].get('value', '')}\"")
            elif g.get("expect_key"):
                problems.append(f"no active entry holds '{g['expect_key']}' any more")
        elif e and g.get("expect_value") and norm(m.get("value", "")) != norm(g["expect_value"]):
            problems.append(f"answer changed from \"{g['expect_value']}\" to \"{m.get('value', '')}\"")
        target = now_answer["entry"] if now_answer else exp
        if target not in top_ids:
            problems.append(f"search no longer finds the answer in the top {TOP} (found: {', '.join(top_ids) or 'nothing'})")
        results.append({"id": g["id"], "question": g["question"], "expect_entry": exp,
                        "expect_value": g.get("expect_value", ""), "now": now_answer, "top": top_ids,
                        "regression": bool(problems), "problems": problems})
    return results


def accept(root, gid):
    items = load(root)
    for g in items:
        if g["id"] == gid:
            cur = current_for_key(root, g["expect_key"]) if g.get("expect_key") else None
            if cur is None:
                cur = entries_by_id(root).get(g["expect_entry"])
            if cur is None:
                return {"error": "nothing to accept: no current answer found"}
            g["expect_entry"] = cur["meta"].get("id")
            g["expect_value"] = cur["meta"].get("value", "")
            g["accepted"] = date.today().isoformat()
            save(root, items)
            return {"accepted": g}
    return {"error": f"golden question {gid} not found"}


def remove(root, gid):
    items = load(root)
    keep = [g for g in items if g["id"] != gid]
    save(root, keep)
    return {"removed": len(items) - len(keep)}


def propose(root, minimum=2):
    """Entries cited again and again in answers are what the business relies on."""
    log_path = os.path.join(root, "_system", "answer-log.jsonl")
    cited, questions = Counter(), defaultdict(Counter)
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                for c in rec.get("citations", []):
                    if c.get("id") and not c["id"].startswith("sources/"):
                        cited[c["id"]] += 1
                        if rec.get("purpose"):
                            questions[c["id"]][rec["purpose"]] += 1
    have = {g["expect_entry"] for g in load(root)}
    ents = entries_by_id(root)
    out = []
    for eid, n in cited.most_common():
        if n < minimum or eid in have or eid not in ents:
            continue
        m = ents[eid]["meta"]
        q = questions[eid].most_common(1)[0][0] if questions[eid] else f"What is our {m.get('title', eid).lower()}?"
        out.append({"entry": eid, "value": m.get("value", ""), "cited": n, "question": q,
                    "command": f"golden.py add <brain> --q \"{q}\" --expect-entry {eid}"})
    return out


def arg(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0] not in ("add", "list", "check", "accept", "remove", "propose"):
        print(__doc__)
        return 2
    cmd, root = args[0], args[1]
    if not os.path.isdir(root):
        print(f"Brain folder not found: {root}")
        return 2
    if cmd == "add":
        qs = [args[i + 1] for i, a in enumerate(args) if a == "--q" and i + 1 < len(args)]
        out = add(root, qs, arg(args, "--expect-entry"), arg(args, "--expect-value"))
    elif cmd == "list":
        out = load(root)
    elif cmd == "check":
        now = today(arg(args, "--today")) if "--today" in args else today()
        res = check(root, now)
        if "--json" in args:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            bad = [r for r in res if r["regression"]]
            print(f"Golden questions: {len(res) - len(bad)} of {len(res)} still answered as expected.")
            for r in bad:
                print(f"- [REGRESSION] {r['id']} \"{r['question']}\": " + "; ".join(r["problems"]))
        return 1 if any(r["regression"] for r in res) else 0
    elif cmd == "accept":
        out = accept(root, arg(args, "--id"))
    elif cmd == "remove":
        out = remove(root, arg(args, "--id"))
    else:
        out = propose(root, int(arg(args, "--min", 2)))
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if isinstance(out, dict) and "error" in out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
