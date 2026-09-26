#!/usr/bin/env python3
"""My Business Brain integrity check: has anything in the brain changed without a record?

The brain keeps a fingerprint (SHA-256) of every entry, archived entry and source document
in _system/integrity.json. Each health check compares the folder with the last fingerprint:

  changed   a file's content changed and the changelog has no line naming it since then
  added     a new file appeared without a changelog line
  removed   a file disappeared (entries are archived, never deleted)

Changes the brain made itself are always logged in _system/changelog.md, so anything
unexplained was edited outside the brain: by hand, by another tool, by a sync conflict or
by a bad restore. Those are reported so the user can confirm or restore them. After the
report the fingerprint is refreshed, so each change is reported once.

Usage:
  integrity.py <brain>            report unexplained changes since the last fingerprint
  integrity.py <brain> --accept   record the current state as the new fingerprint
  integrity.py <brain> --json
Standard library only.
"""
import hashlib
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import today  # noqa: E402

TRACKED = ("entries", os.path.join("_system", "archive"), "sources")


def manifest_path(root):
    return os.path.join(root, "_system", "integrity.json")


def fingerprint(root):
    files = {}
    for sub in TRACKED:
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _, names in os.walk(base):
            for name in sorted(names):
                if name.startswith("."):
                    continue
                p = os.path.join(dirpath, name)
                with open(p, "rb") as f:
                    files[os.path.relpath(p, root).replace(os.sep, "/")] = hashlib.sha256(f.read()).hexdigest()
    return files


def load_manifest(root):
    try:
        with open(manifest_path(root), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_manifest(root, now=None):
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    data = {"updated": (now or today()).isoformat(), "files": fingerprint(root)}
    tmp = manifest_path(root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=0, sort_keys=True)
    os.replace(tmp, manifest_path(root))
    return data


def changelog_mentions(root, since):
    """Words and ids named in changelog lines dated on or after `since`."""
    path = os.path.join(root, "_system", "changelog.md")
    text = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*[-*]\s*(\d{4}-\d{2}-\d{2})", line)
                if m and m.group(1) >= since:
                    text.append(line.lower())
    return "\n".join(text)


def explained(rel, log):
    stem = os.path.splitext(os.path.basename(rel))[0].lower()
    return bool(log) and (stem in log or rel.lower() in log)


def check(root):
    old = load_manifest(root)
    if not old:
        return {"baseline": False, "changed": [], "added": [], "removed": []}
    cur = fingerprint(root)
    log = changelog_mentions(root, old.get("updated", "0000-00-00"))
    prev = old.get("files", {})
    out = {"baseline": True, "since": old.get("updated"), "changed": [], "added": [], "removed": []}
    for rel, h in cur.items():
        if rel not in prev:
            # a file moved into the archive with a logged reason is a normal retirement
            if rel.startswith("_system/archive/") and explained(rel, log):
                continue
            if not explained(rel, log):
                out["added"].append(rel)
        elif prev[rel] != h and not explained(rel, log):
            out["changed"].append(rel)
    for rel in prev:
        if rel not in cur:
            stem = os.path.basename(rel)
            moved = any(r.endswith("/" + stem) for r in cur)  # archived or refiled, not lost
            if not moved and not explained(rel, log):
                out["removed"].append(rel)
    # new source documents are ordinary uploads, not edits
    out["added"] = [r for r in out["added"] if not r.startswith("sources/")]
    return out


def issues(root):
    """Issues for the health check (same shape as brain_health.issue)."""
    r = check(root)
    found = []
    for rel in r["changed"]:
        if rel.startswith("sources/"):
            found.append(("Edited outside the brain", "Medium", rel,
                          f"source document {rel} changed since {r['since']} with no record",
                          "Check whether the new version is genuine; re-read it if so"))
        else:
            found.append(("Edited outside the brain", "Medium", rel,
                          f"{rel} changed since {r['since']} and the changelog doesn't say why",
                          "Confirm the change with the user and log it, or restore the previous version from a backup"))
    for rel in r["added"]:
        found.append(("Edited outside the brain", "Low", rel, f"{rel} appeared since {r['since']} with no record",
                      "Confirm where it came from and log it"))
    for rel in r["removed"]:
        found.append(("Removed from the brain", "High", rel,
                      f"{rel} was deleted since {r['since']}; entries should be archived, never deleted",
                      "Restore it from a backup, or record why it was removed"))
    return found


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    if not os.path.isdir(root):
        print(f"Brain folder not found: {root}")
        return 2
    if "--accept" in args:
        d = save_manifest(root)
        print(f"Fingerprint saved for {len(d['files'])} files.")
        return 0
    r = check(root)
    if "--json" in args:
        print(json.dumps(r, indent=2))
        return 0
    if not r["baseline"]:
        d = save_manifest(root)
        print(f"No fingerprint yet; saved one for {len(d['files'])} files.")
        return 0
    n = len(r["changed"]) + len(r["added"]) + len(r["removed"])
    if not n:
        print(f"No unexplained changes since {r['since']}.")
        return 0
    print(f"{n} unexplained change(s) since {r['since']}:")
    for k in ("changed", "added", "removed"):
        for rel in r[k]:
            print(f"- {k}: {rel}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
