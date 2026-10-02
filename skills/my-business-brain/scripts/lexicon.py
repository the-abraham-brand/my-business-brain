#!/usr/bin/env python3
"""My Business Brain lexicon: the business's own vocabulary.

A language model can't read anything until its tokenizer turns text into the units it knows.
The lexicon does the same job for the Chief of Staff and its agents: it turns a request into the
business's own things (the Scale plan, Supplier X, the refund window), so every agent works from
the same words and the router knows which part of the brain a request is about.

It is built from the brain itself: entry titles, glossary terms, keys and aliases, in English and
Arabic. The owner can add aliases ("SX" means Supplier X, "الباقة الكبيرة" means the Scale plan).

Usage:
  lexicon.py <brain> build                         rebuild _system/lexicon.json from the entries
  lexicon.py <brain> find "text" [--json]          which business things does this text mention?
  lexicon.py <brain> alias TERM --means ENTRY_ID   teach a new word or abbreviation
  lexicon.py <brain> show
Standard library only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, fold, as_list, strip_private  # noqa: E402

STOP_TERMS = {"the", "a", "an", "and", "of", "our", "plan", "policy", "price", "monthly"}


def path(root, name="lexicon.json"):
    return os.path.join(root, "_system", name)


def norm_term(t):
    t = fold(str(t)).lower()
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r"[^\w\s\-]", " ", t, flags=re.U)
    return re.sub(r"\s+", " ", t).strip()


def load_aliases(root):
    try:
        with open(path(root, "lexicon-aliases.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def build(root):
    terms = {}

    def add(term, eid, domain, kind):
        t = norm_term(term)
        if len(t) < 2 or t in STOP_TERMS:
            return
        rec = terms.setdefault(t, {"entries": [], "domains": [], "kind": kind})
        if eid not in rec["entries"]:
            rec["entries"].append(eid)
        if domain and domain not in rec["domains"]:
            rec["domains"].append(domain)

    for e in load_brain(root):
        m = e["meta"] or {}
        if e["archived"] or m.get("status") not in ("active", "disputed", "draft", None, ""):
            continue
        eid, dom = m.get("id") or e["file_id"], m.get("domain") or e["folder"]
        title = str(m.get("title", ""))
        add(title, eid, dom, "glossary" if m.get("type") == "glossary" else "title")
        short = re.split(r"\s+[\(:—-]\s*|\s*\(", title)[0]
        if short and short != title:
            add(short, eid, dom, "title")
        # "Scale plan monthly price" also answers to "Scale plan"
        mm = re.match(r"(.+?\bplan)\b", title, re.I)
        if mm:
            add(mm.group(1), eid, dom, "title")
        for a in as_list(m.get("aliases")) + as_list(m.get("tags")):
            add(a, eid, dom, "alias")
        key = str(m.get("key", ""))
        if key:
            add(key, eid, dom, "key")
    for term, eid in load_aliases(root).items():
        e = next((x for x in load_brain(root) if (x["meta"] or {}).get("id") == eid), None)
        add(term, eid, (e["meta"].get("domain") if e else ""), "alias")
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    with open(path(root), "w", encoding="utf-8") as f:
        json.dump({"terms": terms}, f, ensure_ascii=False, indent=1)
    return terms


def load(root):
    try:
        with open(path(root), encoding="utf-8") as f:
            return json.load(f)["terms"]
    except (OSError, ValueError, KeyError):
        return build(root)


def find(root, text, terms=None):
    """Business things the text mentions, longest match first, no overlaps."""
    terms = terms if terms is not None else load(root)
    t = " " + norm_term(text) + " "
    hits, taken = [], []
    for term in sorted(terms, key=len, reverse=True):
        for m in re.finditer(r"(?<=[\s\-])" + re.escape(term) + r"(?=[\s\-])", t):
            span = (m.start(), m.end())
            if any(not (span[1] <= a or span[0] >= b) for a, b in taken):
                continue
            taken.append(span)
            hits.append({"term": term, **terms[term]})
            break
    return hits


def alias(root, term, eid):
    term = strip_private(term).strip()
    if not term or not eid:
        return {"error": "give a term and --means ENTRY_ID"}
    if not any((e["meta"] or {}).get("id") == eid for e in load_brain(root)):
        return {"error": f"no entry {eid}"}
    a = load_aliases(root)
    a[term] = eid
    with open(path(root, "lexicon-aliases.json"), "w", encoding="utf-8") as f:
        json.dump(a, f, ensure_ascii=False, indent=1)
    build(root)
    return {"alias": term, "means": eid}


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0].startswith("-"):
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    if cmd == "build":
        print(f"Lexicon: {len(build(root))} terms.")
        return 0
    if cmd == "find" and len(args) > 2:
        hits = find(root, args[2])
        print(json.dumps(hits, indent=2, ensure_ascii=False) if "--json" in args else
              "\n".join(f"- {h['term']} -> {', '.join(h['entries'])}" for h in hits) or "No business terms found.")
        return 0
    if cmd == "alias" and len(args) > 2:
        out = alias(root, args[2], val("--means"))
        print(json.dumps(out, ensure_ascii=False))
        return 1 if "error" in out else 0
    if cmd == "show":
        for t, r in sorted(load(root).items()):
            print(f"- {t} ({r['kind']}): {', '.join(r['entries'])}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
