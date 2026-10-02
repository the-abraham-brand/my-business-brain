#!/usr/bin/env python3
"""UserPromptSubmit hook: notice business facts (and "off the record") as the user types them.

If the user's message states something that looks like a business fact the brain doesn't
hold yet (a new price, a changed term, a supplier, a deadline), remind Claude to run the
capture decision, following the user's capture setting. If the user marks something private
or says it's off the record, remind Claude not to store it. Silent otherwise. Never blocks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import read_event, option, find_brain, emit  # noqa: E402


def main():
    event = read_event()
    prompt = event.get("prompt") or ""
    if len(prompt) < 15:
        return 0
    root = find_brain(event.get("cwd"))
    if not root:
        return 0
    from brainlib import has_private
    from sweep import candidates, off_record
    notes = []
    if has_private(prompt) or off_record(prompt):
        notes.append("The user marked part of this message private or off the record: do not store that part "
                     "anywhere (entries, logs, briefings), and don't repeat it in anything that leaves the conversation.")
    facts = [] if off_record(prompt) else candidates(root, [prompt])
    if facts:
        mode = option("capture_mode", "ask") or "ask"
        notes.append("This message may contain business facts the brain doesn't hold yet: "
                     + " | ".join(f'"{f[:140]}"' for f in facts[:3])
                     + f". Run the capture decision (capture_mode={mode}: "
                     + ("offer to remember them" if mode == "ask" else "remember them and say so") + ").")
    if not off_record(prompt):
        try:
            from commitments import scan
            promised = scan(prompt)
        except Exception:
            promised = []
        if promised:
            notes.append("This message mentions a promise: " + " | ".join(
                f'"{c["what"][:120]}"' + (f" (due {c['due']})" if c["due"] else "") for c in promised[:3])
                + ". Offer to record it as a commitment (scripts/commitments.py add), so it can't slip.")
    if notes:
        emit("UserPromptSubmit", "My Business Brain: " + " ".join(notes))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
