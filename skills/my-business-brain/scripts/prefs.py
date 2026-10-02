#!/usr/bin/env python3
"""My Business Brain preference pairs: learn the owner's taste from the choices they make.

Preference training (DPO) teaches a model from pairs: this answer was preferred over that one.
The Chief of Staff learns the same way, without any training run. Whenever the owner picks one
draft over another, or rewrites a draft before sending it, the pair is recorded with what made
them differ (length, bullets, greeting, contractions, exclamation marks, language). Once the same
difference wins three times or more, consistently, it is proposed as a rule. The owner accepts it
and it becomes part of the playbook every drafter reads.

Usage:
  prefs.py <brain> pair --chosen FILE --rejected FILE [--context email|memo|report|message] [--why "..."]
  prefs.py <brain> propose [--min 3]        rules the choices now support
  prefs.py <brain> accept RULE_ID           add a proposed rule to _system/preferences.md
  prefs.py <brain> list
Private passages are never stored. Standard library only.
"""
import json
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import strip_private, script_of, today  # noqa: E402

CONTEXTS = ("email", "memo", "report", "message", "proposal", "other")


def features(text):
    t = strip_private(text or "")
    words = re.findall(r"\w+", t, re.U)
    lines = [l for l in t.splitlines() if l.strip()]
    sentences = [s for s in re.split(r"[.!?؟]+\s", t) if s.strip()]
    first = lines[0].lower() if lines else ""
    return {
        "words": len(words),
        "bullets": sum(1 for l in lines if re.match(r"\s*([-*•]|\d+[.)])\s", l)),
        "headings": sum(1 for l in lines if l.lstrip().startswith("#")),
        "avg_sentence": round(len(words) / max(1, len(sentences)), 1),
        "contractions": len(re.findall(r"\b\w+'(s|re|ll|ve|d|t|m)\b", t, re.I)),
        "exclaim": t.count("!"),
        "greeting": bool(re.match(r"(hi|hello|dear|hey|good (morning|afternoon)|مرحبا|السلام|عزيزي)", first)),
        "pleasantry": bool(re.search(r"hope (this|you)|trust (this|you) (finds|are)|i hope", t, re.I)),
        "script": script_of(t) if t.strip() else "",
    }


def aspects(ch, rj):
    """What distinguishes the chosen text from the rejected one."""
    out = []
    if rj["words"] and ch["words"] <= 0.8 * rj["words"]:
        out.append("shorter")
    elif ch["words"] >= 1.25 * max(1, rj["words"]):
        out.append("longer")
    if ch["bullets"] > rj["bullets"]:
        out.append("more bullets")
    elif ch["bullets"] < rj["bullets"]:
        out.append("fewer bullets")
    if ch["avg_sentence"] <= 0.8 * rj["avg_sentence"]:
        out.append("shorter sentences")
    if ch["contractions"] == 0 and rj["contractions"] > 0:
        out.append("no contractions")
    elif ch["contractions"] > 0 and rj["contractions"] == 0:
        out.append("contractions")
    if ch["exclaim"] == 0 and rj["exclaim"] > 0:
        out.append("no exclamation marks")
    if rj["pleasantry"] and not ch["pleasantry"]:
        out.append("no pleasantries")
    if ch["greeting"] != rj["greeting"]:
        out.append("greeting" if ch["greeting"] else "no greeting")
    if ch["script"] and rj["script"] and ch["script"] != rj["script"]:
        out.append(f"in {ch['script']} script")
    return out


RULE_TEXT = {
    "shorter": "keep it short: the owner chose the shorter draft",
    "longer": "give more detail: the owner chose the fuller draft",
    "more bullets": "use bullet points for the supporting points",
    "fewer bullets": "write in prose rather than bullet points",
    "shorter sentences": "use short sentences",
    "no contractions": "write formally, without contractions (\"we will\", not \"we'll\")",
    "contractions": "write conversationally, with contractions",
    "no exclamation marks": "no exclamation marks",
    "no pleasantries": "skip opening pleasantries; start with the point",
    "greeting": "open with a greeting",
    "no greeting": "no greeting line; start with the point",
}


def path(root, name):
    return os.path.join(root, "_system", name)


def read_pairs(root):
    try:
        with open(path(root, "preference-pairs.jsonl"), encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        return []


def pair(root, chosen, rejected, context="other", why=""):
    if context not in CONTEXTS:
        context = "other"
    ch, rj = features(chosen), features(rejected)
    rec = {"id": "p-" + uuid.uuid4().hex[:6], "date": today().isoformat(), "context": context,
           "aspects": aspects(ch, rj), "why": strip_private(why)[:200], "chosen": ch, "rejected": rj}
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    with open(path(root, "preference-pairs.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


OPPOSITE = {"shorter": "longer", "longer": "shorter", "more bullets": "fewer bullets", "fewer bullets": "more bullets",
            "no contractions": "contractions", "contractions": "no contractions", "greeting": "no greeting",
            "no greeting": "greeting"}


def propose(root, minimum=3):
    pairs = read_pairs(root)
    accepted = accepted_rules(root)
    out = []
    for ctx in sorted({p["context"] for p in pairs}):
        ps = [p for p in pairs if p["context"] == ctx]
        counts = {}
        for p in ps:
            for a in p["aspects"]:
                counts[a] = counts.get(a, 0) + 1
        for a, n in counts.items():
            against = counts.get(OPPOSITE.get(a, ""), 0)
            if n >= minimum and n / (n + against) >= 0.75 and a in RULE_TEXT:
                rid = f"{ctx}:{a}"
                if rid in accepted:
                    continue
                out.append({"id": rid, "context": ctx, "rule": f"{ctx.capitalize()}s: {RULE_TEXT[a]}",
                            "support": n, "against": against, "pairs": len(ps)})
    return sorted(out, key=lambda r: -r["support"])


def accepted_rules(root):
    p = path(root, "preferences.md")
    if not os.path.exists(p):
        return set()
    with open(p, encoding="utf-8") as f:
        return set(re.findall(r"<!-- pref:(\S+) -->", f.read()))


def accept(root, rid):
    rule = next((r for r in propose(root, 3) if r["id"] == rid), None)
    if not rule:
        return {"error": f"no proposed rule {rid} (a rule needs at least three consistent choices)"}
    p = path(root, "preferences.md")
    text = ""
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            text = f.read()
    if "## Learned from your choices" not in text:
        text = text.rstrip() + "\n\n## Learned from your choices\n"
    text = text.rstrip() + f"\n- {rule['rule']} (from {rule['support']} choices) <!-- pref:{rid} -->\n"
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    with open(path(root, "changelog.md"), "a", encoding="utf-8") as f:
        f.write(f"\n- {today().isoformat()} Preference learned and accepted: {rule['rule']} (_system/preferences.md)")
    return {"accepted": rule}


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0].startswith("-"):
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    if cmd == "pair":
        try:
            with open(val("--chosen"), encoding="utf-8") as f:
                ch = f.read()
            with open(val("--rejected"), encoding="utf-8") as f:
                rj = f.read()
        except OSError as e:
            print(json.dumps({"error": str(e)}))
            return 1
        out = pair(root, ch, rj, val("--context", "other"), val("--why"))
        print(json.dumps({k: out[k] for k in ("id", "context", "aspects")}, ensure_ascii=False))
        return 0
    if cmd == "propose":
        try:
            minimum = int(val("--min", "3"))
        except ValueError:
            print("--min needs a whole number")
            return 2
        rules = propose(root, minimum)
        print("\n".join(f"- [{r['id']}] {r['rule']} ({r['support']} of {r['pairs']} choices)" for r in rules)
              or "No consistent preference yet.")
        return 0
    if cmd == "accept" and len(args) > 2:
        out = accept(root, args[2])
        print(json.dumps(out, ensure_ascii=False))
        return 1 if "error" in out else 0
    if cmd == "list":
        for p in read_pairs(root):
            print(f"- {p['date']} {p['context']}: {', '.join(p['aspects']) or 'no clear difference'}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
