#!/usr/bin/env python3
"""My Business Brain resume card: pick up a long job exactly where it stopped.

A bulk load of 40 documents or a full review can outlast the conversation's memory: when a
long session is compacted, the details of what was done and what is left are lost. The resume
card keeps them on disk, in _system/resume.json. The session brief (Claude Code and Cowork)
shows it at the start of every session, including right after compaction; elsewhere, check it
with `show` before continuing a job.

Usage:
  resume.py <brain> start --task "Load the supplier contracts" [--items a.pdf,b.pdf,...]
  resume.py <brain> done ITEM [--note "..."]      tick an item off (repeatable)
  resume.py <brain> note "text"                   anything the next session must know
  resume.py <brain> decision "text"               a question waiting for the user
  resume.py <brain> show [--json]
  resume.py <brain> finish                        close the card (kept in _system/resume-history.jsonl)
Standard library only.
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import strip_private  # noqa: E402


def path(root):
    return os.path.join(root, "_system", "resume.json")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(root):
    try:
        with open(path(root), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save(root, card):
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    card["updated"] = now()
    tmp = path(root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path(root))
    return card


def start(root, task, items):
    return save(root, {"task": strip_private(task), "started": now(), "items": items, "done": [],
                       "notes": [], "decisions": []})


def _end(s):
    return s if s.endswith((".", "?", "!", "؟")) else s + "."


def summary(card):
    if not card:
        return None
    left = [i for i in card["items"] if i not in card["done"]]
    parts = [f"Unfinished job: {card['task']} (started {card['started'][:10]})."]
    if card["items"]:
        parts.append(f"{len(card['done'])} of {len(card['items'])} done"
                     + (f"; next: {', '.join(left[:3])}" + (f" and {len(left) - 3} more" if len(left) > 3 else "")
                        if left else "; all items done, finish the wrap-up") + ".")
    elif card["done"]:
        parts.append(f"Done so far: {', '.join(card['done'][-3:])}.")
    if card["decisions"]:
        parts.append(_end("Waiting for the user: " + " | ".join(card["decisions"][-3:])))
    if card["notes"]:
        parts.append(_end("Notes: " + " | ".join(card["notes"][-3:])))
    return " ".join(parts)


def main(argv):
    args = argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    card = load(root)
    if cmd == "start":
        task = args[args.index("--task") + 1] if "--task" in args else "Unnamed job"
        items = [i.strip() for i in (args[args.index("--items") + 1] if "--items" in args else "").split(",") if i.strip()]
        card = start(root, task, items)
    elif cmd == "show":
        if "--json" in args:
            print(json.dumps(card, indent=2, ensure_ascii=False))
        else:
            print(summary(card) or "No unfinished job.")
        return 0
    elif not card:
        print("No unfinished job. Start one with: resume.py <brain> start --task \"...\"")
        return 1
    elif cmd == "done":
        for item in [a for a in args[2:] if not a.startswith("--") and a != (args[args.index("--note") + 1] if "--note" in args else None)]:
            if item not in card["done"]:
                card["done"].append(item)
        if "--note" in args:
            card["notes"].append(strip_private(args[args.index("--note") + 1]))
        save(root, card)
    elif cmd in ("note", "decision"):
        card["notes" if cmd == "note" else "decisions"].append(strip_private(" ".join(args[2:])))
        save(root, card)
    elif cmd == "finish":
        card["finished"] = now()
        with open(os.path.join(root, "_system", "resume-history.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
        os.replace(path(root), path(root) + ".done")
        print("Job closed.")
        return 0
    else:
        print(__doc__)
        return 2
    print(summary(load(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
