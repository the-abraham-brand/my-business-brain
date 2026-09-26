#!/usr/bin/env python3
"""My Business Brain: fetch full entries by id, the second step of layered search.

Search with `brain_search.py --brief` to get a short index, pick the ids that matter, then:

  brain_get.py <brain> ID [ID ...] [--audience internal|team|external] [--json]

Prints each entry in full (its fields and text) with its citation. Source sections can be
fetched by their reference (sources/file.md#L10-L24). With --audience external, confidential
entries are withheld. Private passages are never shown. Standard library only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, sensitivity_of, strip_private, approx_tokens  # noqa: E402


def source_lines(root, ref):
    m = re.match(r"(sources/[^#]+)#L(\d+)-L(\d+)$", ref)
    if not m:
        return None
    path = os.path.join(root, m.group(1))
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    a, b = int(m.group(2)), int(m.group(3))
    return "\n".join(lines[a - 1:b])


def get(root, ids, audience="internal"):
    by_id = {}
    for e in load_brain(root):
        if e["meta"]:
            by_id[e["meta"].get("id") or e["file_id"]] = e
    out = []
    for i in ids:
        if i.startswith("sources/"):
            text = source_lines(root, i)
            out.append({"id": i, "found": text is not None, "text": strip_private(text or ""), "cite_as": f"[[{i}]]"})
            continue
        e = by_id.get(i)
        if not e:
            out.append({"id": i, "found": False})
            continue
        m = e["meta"]
        if audience in ("team", "external") and sensitivity_of(m) == "confidential":
            out.append({"id": i, "found": True, "withheld": "confidential: for the owner only"})
            continue
        out.append({"id": i, "found": True, "path": e["path"], "archived": e["archived"],
                    "meta": {k: v for k, v in m.items()}, "text": strip_private(e["body"]), "cite_as": f"[[{i}]]"})
    return out


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    audience = args[args.index("--audience") + 1] if "--audience" in args else "internal"
    skip = {"--audience", audience, "--json"}
    ids = [a for a in args[1:] if a not in skip]
    res = get(root, ids, audience)
    if "--json" in args:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0
    for r in res:
        if not r["found"]:
            print(f"## {r['id']}: not found\n")
            continue
        if r.get("withheld"):
            print(f"## {r['id']}: withheld ({r['withheld']})\n")
            continue
        print(f"## {r['cite_as']}" + (f" ({r['path']}{', archived' if r.get('archived') else ''})" if r.get("path") else ""))
        for k, v in (r.get("meta") or {}).items():
            print(f"{k}: {v}")
        print("\n" + r["text"].strip() + "\n")
    print(f"(about {sum(approx_tokens(r.get('text', '')) for r in res)} tokens)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
