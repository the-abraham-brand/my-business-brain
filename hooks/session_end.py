#!/usr/bin/env python3
"""SessionEnd hook: list business facts mentioned in this session but never saved.

Reads the session transcript, finds the user's sentences that look like business facts the
brain doesn't hold, and adds them to _system/unsaved-facts.md. The next session brief asks
the user about them. Private passages and anything said off the record are skipped. Nothing
is written to the brain's entries. Never blocks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import read_event, find_brain  # noqa: E402


def main():
    event = read_event()
    transcript = event.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        return 0
    root = find_brain(event.get("cwd"))
    if not root:
        return 0
    from sweep import candidates, user_messages, record
    record(root, candidates(root, user_messages(transcript)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
