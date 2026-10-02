#!/usr/bin/env python3
"""My Business Brain router: which specialists should handle a request, and how carefully.

A mixture-of-experts model has a small router that sends each token to the few experts best
suited to it. The Chief of Staff does the same with requests: it reads the request, recognises
the business things it mentions (through the lexicon), and picks the specialist agents for the
job, which of them can work in parallel, and whether the job needs a quick answer or a
deliberate one with an independent check (like a model's switch between answering directly
and thinking first).

It is a plain, explainable scorer: every choice comes with its reason, and every plan is logged
in _system/agents/routes.jsonl so the owner can see how work was routed.

Usage:
  router.py <brain> plan "request" [--json] [--audience owner|team|external] [--no-log]
  router.py <brain> experts                 the specialists and what each is for
Standard library only.
"""
import json
import os
import re
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import fold, strip_private, today  # noqa: E402

EXPERTS = {
    "brain": {"agent": None, "does": "answers from what the brain already knows (search, cite, check)",
              "words": ["what is", "what's", "how much", "how many", "when does", "when is", "do we", "did we",
                        "who is", "our price", "we charge", "remind me what", "كم", "ما هو", "متى", "هل"]},
    "researcher": {"agent": "brain-researcher", "does": "finds outside information from official and reputable sources; social talk comes back as leads",
                   "words": ["research", "look up", "find out", "latest", "regulation", "law", "rule", "official",
                             "competitor", "market", "industry", "benchmark", "news", "authority", "ministry",
                             "licen", "visa", "permit", "government", "بحث", "قانون", "لائحة", "منافس", "السوق"]},
    "analyst": {"agent": "brain-analyst", "does": "works the numbers: margins, trends, forecasts, comparisons, options",
                "words": ["analy", "margin", "revenue", "profit", "cost", "forecast", "budget", "trend", "compare",
                          "metric", "kpi", "growth", "churn", "cash", "pricing model", "scenario", "why did",
                          "should we", "which option", "options", "تحليل", "ارباح", "تكلفة", "ميزانية"]},
    "drafter": {"agent": "brain-drafter", "does": "drafts emails, replies, memos, proposals and announcements in the owner's voice",
                "words": ["draft", "write", "email", "reply", "respond", "memo", "letter", "proposal", "announce",
                          "message", "post", "note to", "tell ", "let them know", "اكتب", "رسالة", "بريد", "رد على", "مسودة"]},
    "clerk": {"agent": "brain-clerk", "does": "contracts, deadlines, renewals, commitments, follow-ups and reminders",
              "words": ["contract", "renew", "notice", "deadline", "due", "expire", "commitment", "promised",
                        "follow up", "follow-up", "remind", "calendar", "schedule", "meeting", "agenda", "prep",
                        "عقد", "تجديد", "موعد", "تذكير", "اجتماع"]},
    "reader": {"agent": "brain-reader", "does": "reads documents to load into the brain (read-only; the Chief of Staff writes)",
               "words": ["attached", "upload", "these documents", "load", "ingest", "read this", "remember this",
                         "add this to the brain", "مرفق", "احفظ"]},
}
DOMAIN_BOOST = {"contracts": "clerk", "pricing": "analyst", "finance": "analyst", "metrics": "analyst",
                "legal-regulatory": "researcher", "customers": "drafter", "suppliers": "clerk"}

HIGH_STAKES = [
    (r"\b(sign(s|ed|ing)?|terminat(e|es|ed|ing|ion)|cancel(s|led|ling|lation)?|renew(s|ed|ing|al)?|hir(e|es|ed|ing)|"
     r"fir(e|es|ed|ing)|dismiss(al|ed|ing)?|lay(ing)? off|sue|lawsuit|legal|lawyer|tax(es)?|vat|audit(s|or)?|fines?|"
     r"penalt(y|ies)|regulators?|compliance)\b", "legal, tax, contract or people decision"),
    (r"\b(investors?|board meeting|the board|board paper|banks?|loans?|valuation|acquisition|merger|"
     r"raise (capital|funds|funding|money|a round))\b", "goes to investors, the board or a bank"),
    (r"\b(should we|decide|decision|which option|recommend)\b", "a decision to recommend"),
    (r"(aed|usd|eur|gbp|sar|\$|€|£)\s?(\d{1,3}(,\d{3})+|\d{5,})|(\d{1,3}(,\d{3})+|\d{5,})\s?(aed|usd|eur|gbp|sar)",
     "a large sum of money"),
    (r"(عقد|ضريب|قانون|محام|إنهاء|انهاء|توظيف|فصل)", "legal, tax, contract or people decision"),
]
EXTERNAL = (r"\b(customer|client|supplier|vendor|partner|investor|regulator|authority|bank|landlord|press|public|linkedin|website)\w*"
            r"|(عميل|العميل|العملاء|مورد|المورد|شريك|مستثمر|المستثمر|البنك)")
TEAM = r"\b(team|staff|employee|new hire|onboard|handover|all-hands|everyone)\w*"
ACTIONS = [(r"\b(send|email it|post|publish|announce)\b", "sending or publishing"),
           (r"\b(pay|transfer|buy|order|purchase)\b", "spending money"),
           (r"\b(book|schedule a meeting|invite)\b", "booking or inviting"),
           (r"\b(sign|accept|agree)\b", "signing or agreeing"),
           (r"\b(update the price|change the (price|policy|fact)|correct the brain)\b", "changing a fact")]
ORDER = ["reader", "researcher", "analyst", "clerk", "drafter"]   # drafter writes from what the others found


def score(text, hits):
    t = " " + fold(text).lower() + " "
    out = {}
    for name, ex in EXPERTS.items():
        s, why = 0.0, []
        for w in ex["words"]:
            if fold(w).lower() in t:
                s += 1.0
                why.append(f"'{w.strip()}'")
        out[name] = [s, why]
    for h in hits:
        for d in h.get("domains", []):
            if d in DOMAIN_BOOST:
                out[DOMAIN_BOOST[d]][0] += 0.5
                out[DOMAIN_BOOST[d]][1].append(f"mentions {h['term']} ({d})")
    return out


def scorecard_weak(root):
    """Agents whose recent work scored low: their output gets an independent check."""
    p = os.path.join(root, "_system", "agents", "scorecard.jsonl")
    by = {}
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                by.setdefault(r.get("agent"), []).append(float(r.get("score", 0)))
    except OSError:
        return set()
    return {a for a, xs in by.items() if len(xs) >= 3 and sum(xs[-10:]) / len(xs[-10:]) < 0.7}


def plan(root, request, audience=None, log=True):
    request = strip_private(request or "").strip()
    if not os.path.isdir(root):
        return {"error": f"Brain folder not found: {root}"}
    try:
        from lexicon import find
        hits = find(root, request)
    except Exception:
        hits = []
    sc = score(request, hits)
    try:  # an active role lens leans on its own specialists, but only for work the request already touches
        from adapter import boosts
        for name, b in boosts(root).items():
            if name in sc and sc[name][0] > 0:
                sc[name][0] += b
                sc[name][1].append(f"lens +{b:g}")
    except Exception:
        pass
    chosen = [n for n in ORDER if sc[n][0] >= 1.0]
    low = " " + fold(request).lower() + " "
    if not chosen:
        chosen = ["brain"]
    # depth: quick by default, deliberate when the stakes are high
    reasons = sorted({why for pat, why in HIGH_STAKES if re.search(pat, low)})
    depth = "deliberate" if reasons else "quick"
    weak = scorecard_weak(root) & {EXPERTS[n]["agent"] for n in chosen}
    if weak:
        depth = "deliberate"
        reasons.append("recent work by " + ", ".join(sorted(weak)) + " scored low")
    try:  # a lens that works deliberately (CFO, people) keeps its own specialists on deliberate depth
        from adapter import active
        lens = active(root)
        if lens and lens.get("default_depth") == "deliberate" and set(lens.get("experts", {})) & set(chosen):
            depth = "deliberate"
            reasons.append(f"the {lens['name']} works deliberately")
    except Exception:
        pass
    if not audience:
        audience = "external" if ("drafter" in chosen and re.search(EXTERNAL, low)) else \
                   "team" if re.search(TEAM, low) else "owner"
        if audience == "owner":
            try:  # a colleague with a profile is a team reader
                from adapter import profiles
                for pr in profiles(root):
                    first = fold(pr["name"]).lower().split()[0]
                    if re.search(r"(?<!\w)" + re.escape(first) + r"(?!\w)", low):
                        audience = "team"
                        break
            except Exception:
                pass
    approvals = sorted({why for pat, why in ACTIONS if re.search(pat, low)})
    steps, before = [], []
    for n in chosen:
        ex = EXPERTS[n]
        after = list(before) if n == "drafter" else (["reader"] if n != "reader" and "reader" in chosen else [])
        steps.append({"expert": n, "agent": ex["agent"], "does": ex["does"],
                      "why": ", ".join(sc[n][1][:4]) or "default: the brain answers what it already knows",
                      "after": [a for a in after if a != n]})
        if n != "drafter":
            before.append(n)
    if depth == "deliberate":
        finders = [s["expert"] for s in steps if s["expert"] not in ("drafter", "brain")]
        # the checker re-derives what the others found; the draft waits for it. With nothing to
        # re-derive first, it checks the draft itself.
        steps.append({"expert": "checker", "agent": "brain-checker", "does": "re-derives the key finding independently, without seeing the others' answers",
                      "why": "; ".join(reasons), "after": finders or [s["expert"] for s in steps if s["expert"] == "drafter"]})
        if finders:
            for s in steps:
                if s["expert"] == "drafter":
                    s["after"] = list(dict.fromkeys(s["after"] + ["checker"]))
        if "a decision to recommend" in reasons:
            steps.append({"expert": "options", "agent": None, "does": "options memo: 2-3 options scored on one rubric (options.py)",
                          "why": "a decision to recommend", "after": [s["expert"] for s in steps if s["expert"] not in ("drafter", "options")]})
    parallel = [s["expert"] for s in steps if not s["after"] and s["agent"]]
    out = {"id": "r-" + uuid.uuid4().hex[:8], "request": request[:500], "terms": [h["term"] for h in hits],
           "entries": sorted({e for h in hits for e in h["entries"]}), "steps": steps, "parallel": parallel,
           "depth": depth, "depth_reasons": reasons, "audience": audience,
           "needs_owner_approval": approvals}
    if log and os.path.isdir(root):
        d = os.path.join(root, "_system", "agents")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "routes.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), **{k: out[k] for k in
                                ("id", "request", "terms", "depth", "audience", "needs_owner_approval")},
                                "experts": [s["expert"] for s in steps]}, ensure_ascii=False) + "\n")
    return out


def describe(p):
    lines = [f"Plan {p['id']}: {p['depth']} ({'; '.join(p['depth_reasons']) or 'routine'}), audience {p['audience']}."]
    if p["terms"]:
        lines.append("About: " + ", ".join(p["terms"]))
    for s in p["steps"]:
        who = s["agent"] or "the Chief of Staff"
        lines.append(f"- {s['expert']} ({who}): {s['does']}. Why: {s['why']}"
                     + (f". After: {', '.join(s['after'])}" if s["after"] else ""))
    if len(p["parallel"]) > 1:
        lines.append("Run in parallel: " + ", ".join(p["parallel"]))
    if p["needs_owner_approval"]:
        lines.append("Owner approval needed before: " + ", ".join(p["needs_owner_approval"]))
    return "\n".join(lines)


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0].startswith("-"):
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    if cmd == "plan" and len(args) > 2:
        p = plan(root, args[2], val("--audience") or None, "--no-log" not in args)
        if "error" in p:
            print(p["error"])
            return 1
        print(json.dumps(p, indent=2, ensure_ascii=False) if "--json" in args else describe(p))
        return 0
    if cmd == "experts":
        for n, ex in EXPERTS.items():
            print(f"- {n} ({ex['agent'] or 'the Chief of Staff'}): {ex['does']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
