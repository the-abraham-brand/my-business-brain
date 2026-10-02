#!/usr/bin/env python3
"""My Business Brain options memo: score a group of options against each other, then recommend.

Group-relative training (GRPO) doesn't judge one answer on its own: it samples several and
scores each against the group's average. The Chief of Staff does the same for decisions. It
lays out two to four options, scores every one on the same weighted criteria, and recommends the
option that beats the group by the widest margin. It shows the runner-up and says which
criterion would have to change for the answer to flip.

Input (JSON file):
  {"question": "Renew Supplier X or switch?",
   "criteria": [{"name": "annual cost", "weight": 0.4, "better": "lower"},
                {"name": "migration risk", "weight": 0.3, "better": "lower"},
                {"name": "service quality", "weight": 0.3, "better": "higher"}],
   "options": [{"name": "Renew", "scores": {"annual cost": 66000, "migration risk": 1, "service quality": 3},
                "notes": "...", "citations": ["contracts-supplier-x-hosting"]}, ...]}

Usage:
  options.py <brain> score FILE [--write] [--json]
--write saves analytics/<date>-options-<slug>.md. Standard library only.
"""
import json
import os
import re
import sys
from statistics import mean, pstdev

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import strip_private, today  # noqa: E402


def normalise(values, better):
    """Score each value against the best in the group, keeping proportions: a cost of 50,001
    against 50,000 is 99.99% as good, not 0%. Falls back to min-max when values aren't all positive."""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    if lo > 0:
        return [v / hi for v in values] if better == "higher" else [lo / v for v in values]
    return [((v - lo) / (hi - lo)) if better == "higher" else ((hi - v) / (hi - lo)) for v in values]


def totals(opts, crits):
    tot = [0.0] * len(opts)
    wsum = sum(float(c.get("weight", 1)) for c in crits) or 1.0
    for c in crits:
        vals = [float(o["scores"][c["name"]]) for o in opts]
        for i, n in enumerate(normalise(vals, c.get("better", "higher"))):
            tot[i] += n * float(c.get("weight", 1)) / wsum
    return tot


def score(data):
    opts, crits = data.get("options", []), data.get("criteria", [])
    if len(opts) < 2:
        return {"error": "give at least two options"}
    if not crits:
        return {"error": "give at least one criterion"}
    for c in crits:
        c["better"] = str(c.get("better", "higher")).strip().lower()
        if c["better"] not in ("higher", "lower"):
            return {"error": f"criterion '{c.get('name')}': better must be 'higher' or 'lower'"}
        try:
            c["weight"] = float(c.get("weight", 1))
        except (TypeError, ValueError):
            return {"error": f"criterion '{c.get('name')}': weight must be a number"}
    if not any(c["weight"] > 0 for c in crits) or any(c["weight"] < 0 for c in crits):
        return {"error": "weights must be zero or more, and at least one must be above zero"}
    for o in opts:
        miss = [c["name"] for c in crits if c["name"] not in o.get("scores", {})]
        if miss:
            return {"error": f"option '{o.get('name')}' has no score for: {', '.join(miss)}"}
        for c in crits:
            try:
                float(o["scores"][c["name"]])
            except (TypeError, ValueError):
                return {"error": f"option '{o.get('name')}': the score for '{c['name']}' must be a number"}
    tot = totals(opts, crits)
    mu, sd = mean(tot), pstdev(tot)
    adv = [round((t - mu) / (sd + 1e-9), 2) if sd > 0 else 0.0 for t in tot]
    order = sorted(range(len(opts)), key=lambda i: -tot[i])
    win, run = order[0], order[1]
    flips = []
    for k, c in enumerate(crits):
        for factor in (2.0, 0.5):
            cc = [dict(x) for x in crits]
            cc[k]["weight"] = float(cc[k].get("weight", 1)) * factor
            t2 = totals(opts, cc)
            w2 = max(range(len(opts)), key=lambda i: t2[i])
            if w2 != win:
                flips.append(f"if '{c['name']}' mattered {'twice as much' if factor == 2 else 'half as much'}, "
                             f"'{opts[w2]['name']}' would win")
                break
    margin = round((tot[win] - tot[run]) * 100, 1)
    return {"question": data.get("question", ""), "ranking": [
        {"name": opts[i]["name"], "score": round(tot[i] * 100, 1), "advantage": adv[i],
         "notes": opts[i].get("notes", ""), "citations": opts[i].get("citations", [])} for i in order],
        "recommend": opts[win]["name"], "runner_up": opts[run]["name"], "margin": margin,
        "close_call": margin < 10, "would_flip": flips, "criteria": crits}


def render(r):
    L = [f"# Options: {r['question']}", "",
         f"**Recommendation: {r['recommend']}**, ahead of {r['runner_up']} by {r['margin']} points out of 100"
         + (" (a close call: worth a conversation)" if r["close_call"] else "") + ".", "",
         "| Option | Score | vs the group | Notes |", "|---|---|---|---|"]
    for o in r["ranking"]:
        L.append(f"| {o['name']} | {o['score']} | {o['advantage']:+} | {o['notes']}"
                 + (" " + " ".join(f"[[{c}]]" for c in o["citations"]) if o["citations"] else "") + " |")
    L += ["", "**Criteria:** " + "; ".join(f"{c['name']} (weight {c.get('weight', 1)}, {c.get('better', 'higher')} is better)"
                                          for c in r["criteria"]), ""]
    L += ["**What would change the answer:** " + ("; ".join(r["would_flip"]) if r["would_flip"]
                                                   else "no single criterion doubling or halving would change it") + ".", "",
          "Scores are relative: on each criterion an option is measured against the best in the group. The owner decides."]
    return "\n".join(L) + "\n"


def main(argv):
    args = argv[1:]
    if len(args) < 3 or args[1] != "score":
        print(__doc__)
        return 2
    root = args[0]
    try:
        with open(args[2], encoding="utf-8") as f:
            data = json.loads(strip_private(f.read()))
    except (OSError, ValueError) as e:
        print(json.dumps({"error": f"cannot read {args[2]} as JSON: {e}"}))
        return 1
    if not isinstance(data, dict):
        print(json.dumps({"error": "the file must hold one JSON object with question, criteria and options"}))
        return 1
    r = score(data)
    if "error" in r:
        print(json.dumps(r))
        return 1
    if "--json" in args:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0
    text = render(r)
    if "--write" in args:
        os.makedirs(os.path.join(root, "analytics"), exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", r["question"].lower()).strip("-")[:40] or "decision"
        with open(os.path.join(root, "analytics", f"{today().isoformat()}-options-{slug}.md"), "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
