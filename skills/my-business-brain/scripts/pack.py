#!/usr/bin/env python3
"""My Business Brain industry packs: a ready-made starting point for a kind of business.

A pack brings what a clinic, an agency or a trading company usually needs to know:
  - key prefixes that file facts in the right area (fee. -> pricing, practitioner. -> people);
  - words that always make a fact confidential (patient, landed cost, client);
  - decision types for that trade (appointment type, lead stage, scope change);
  - fact templates: the questions to ask the owner to fill the brain's first facts;
  - what to watch (licence renewals, lease notices) and common terms.

Usage:
  pack.py list
  pack.py show ID
  pack.py apply <brain> ID            merge the pack into the brain (keeps anything already there)
  pack.py new <brain> --file pack.json  check a custom pack, save it in _system/packs/ and apply it
  pack.py applied <brain>
Standard library only.
"""
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from decide import DOMAINS, lint_types  # noqa: E402
from brainlib import SENSITIVITY  # noqa: E402

PACK_DIR = os.path.join(os.path.dirname(HERE), "packs")
REQUIRED = ("id", "name", "description")


def available(root=None):
    dirs = [PACK_DIR] + ([os.path.join(root, "_system", "packs")] if root else [])
    out = {}
    for d in dirs:
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".json"):
                    with open(os.path.join(d, f), encoding="utf-8") as fh:
                        p = json.load(fh)
                    out[p.get("id", f[:-5])] = p
    return out


def validate(p):
    errs = [f"missing '{k}'" for k in REQUIRED if not p.get(k)]
    for prefix, dom in (p.get("key_prefixes") or {}).items():
        if dom not in DOMAINS:
            errs.append(f"key prefix '{prefix}' points to unknown area '{dom}'")
        if not str(prefix).endswith("."):
            errs.append(f"key prefix '{prefix}' should end with a dot")
    for t in p.get("fact_templates") or []:
        if t.get("domain") not in DOMAINS:
            errs.append(f"template '{t.get('title')}' has unknown area '{t.get('domain')}'")
        if t.get("sensitivity") not in SENSITIVITY:
            errs.append(f"template '{t.get('title')}' has sensitivity '{t.get('sensitivity')}'")
        if not t.get("ask") or not t.get("key"):
            errs.append(f"template '{t.get('title')}' needs a key and a question to ask")
    for i in lint_types(p.get("decision_types") or {}):
        if i["severity"] == "error":
            errs.append(f"decision type '{i['type']}': {i['message']}")
    return errs


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def apply(root, p, today_=None):
    errs = validate(p)
    if errs:
        return {"error": "pack is not valid", "problems": errs}
    sysd = os.path.join(root, "_system")
    state = load_json(os.path.join(sysd, "pack.json"), {})
    applied = [a for a in state.get("applied", []) if a != p["id"]] + [p["id"]]
    prefixes = dict(p.get("key_prefixes") or {})
    prefixes.update(state.get("key_prefixes") or {})  # anything the business already set wins
    terms = list(dict.fromkeys((state.get("confidential_terms") or []) + (p.get("confidential_terms") or [])))
    names = [n for n in [state.get("name")] if n] + [p["name"]]
    write_json(os.path.join(sysd, "pack.json"), {"applied": applied, "name": " + ".join(dict.fromkeys(names)),
                                                  "key_prefixes": prefixes, "confidential_terms": terms,
                                                  "watch": list(dict.fromkeys((state.get("watch") or []) + (p.get("watch") or []))),
                                                  "glossary": list(dict.fromkeys((state.get("glossary") or []) + (p.get("glossary") or [])))})
    types = load_json(os.path.join(sysd, "decision-types.json"), {})
    added_types = [k for k in (p.get("decision_types") or {}) if k not in types]
    for k in added_types:
        types[k] = p["decision_types"][k]
    if added_types:
        write_json(os.path.join(sysd, "decision-types.json"), types)
    qpath = os.path.join(sysd, "pack-questions.md")
    if os.path.exists(qpath):
        with open(qpath, encoding="utf-8") as fh:
            have = fh.read()
    else:
        have = ("# Questions to fill the brain\n\nStarting facts suggested by your industry pack. "
                "Answer them in conversation; each answer becomes an entry.\n")
    lines = [f"- [ ] {t['ask']} (key `{t['key']}`, {t['domain']}, {t['sensitivity']})"
             for t in p.get("fact_templates") or [] if f"`{t['key']}`" not in have]
    if lines:
        with open(qpath, "w", encoding="utf-8") as f:
            f.write(have.rstrip("\n") + f"\n\n## {p['name']} ({(today_ or date.today()).isoformat()})\n\n" + "\n".join(lines) + "\n")
    with open(os.path.join(sysd, "changelog.md"), "a", encoding="utf-8") as f:
        f.write(f"- {(today_ or date.today()).isoformat()} Applied industry pack '{p['name']}' "
                f"({len(added_types)} decision types, {len(lines)} starting questions).\n")
    return {"applied": p["id"], "decision_types_added": added_types, "questions_added": len(lines),
            "key_prefixes": len(prefixes), "confidential_terms": len(terms)}


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    if cmd == "list":
        for pid, p in available().items():
            print(f"{pid:12} {p['name']}: {p['description']}")
        return 0
    if cmd == "show" and len(args) > 1:
        p = available().get(args[1])
        print(json.dumps(p, indent=2, ensure_ascii=False) if p else f"No pack '{args[1]}'. Try: pack.py list")
        return 0 if p else 1
    if len(args) < 2 or not os.path.isdir(args[1]):
        print(__doc__)
        return 2
    root = args[1]
    if cmd == "applied":
        print(json.dumps(load_json(os.path.join(root, "_system", "pack.json"), {}), indent=2, ensure_ascii=False))
        return 0
    if cmd == "apply" and len(args) > 2:
        p = available(root).get(args[2])
        if not p:
            print(f"No pack '{args[2]}'. Try: pack.py list")
            return 1
        out = apply(root, p)
    elif cmd == "new" and "--file" in args:
        p = load_json(args[args.index("--file") + 1], None)
        if not isinstance(p, dict):
            print("The pack file must be a JSON object.")
            return 1
        errs = validate(p)
        if errs:
            out = {"error": "pack is not valid", "problems": errs}
        else:
            write_json(os.path.join(root, "_system", "packs", f"{p['id']}.json"), p)
            out = apply(root, p)
    else:
        print(__doc__)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 1 if "error" in out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
