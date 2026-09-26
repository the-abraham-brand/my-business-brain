#!/usr/bin/env python3
"""My Business Brain citation check: verify a drafted answer against the entries it cites.

Usage: python3 cite_check.py <brain-folder> <answer.md | -> [--audience internal|external]
                             [--log "what this is for"] [--kind answer|email|proposal|quote|report|post|document]
                             [--recipient "who receives it"] [--today YYYY-MM-DD] [--json]

With --log, a draft that passes is recorded in _system/answer-log.jsonl with the entries and
values it relied on, so that if any of those facts change later, impact.py can list the outputs
that used the old value.

Write the draft with a citation after each factual sentence, using entry ids or source
chunk references exactly as brain_search.py prints them:
    The Growth plan is AED 14,999 per month [[pricing-growth-plan-monthly]].
    Notice must be given 90 days before expiry [[sources/supplier-x.md#L40-L58]].
Mark figures you calculated (not stored) with [calc] and show the working in the answer:
    That leaves 20 days to give notice [calc] [[contracts-supplier-x]].

For every sentence the check confirms that:
  - each cited entry exists (or the cited source lines exist);
  - every number, amount, percentage and date in the sentence appears in the cited
    entries or source lines (ignoring [calc] sentences' derived figures);
  - every "quoted phrase" appears word for word;
  - cited entries are current: not superseded, archived, disputed, overdue or low confidence.
It also flags sentences that state figures without any citation.
With --audience external (an email, proposal, post or anything leaving the business),
citing a confidential entry is a failure and citing an internal one needs confirmation.
Exit code 0 = all supported, 1 = something to fix. Standard library only.
"""
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, parse_date, today, sensitivity_of, fold

CITE_RE = re.compile(r"\[\[([^\]]+)\]\]")
QUOTE_RE = re.compile(r"[\"“]([^\"”]{4,})[\"”]")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
# Month names as written in the Gulf (after folding: alef variants unified)
AR_MONTHS = {"يناير": 1, "فبراير": 2, "مارس": 3, "ابريل": 4, "مايو": 5, "يونيو": 6, "يوليو": 7,
             "اغسطس": 8, "سبتمبر": 9, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12}
MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), "ymd"),
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + MON + r",?\s+(\d{4})\b", re.I), "dmy"),
    (re.compile(r"\b" + MON + r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I), "mdy"),
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"), "slash"),
    (re.compile(r"(?<!\d)(\d{1,2})\s+(" + "|".join(AR_MONTHS) + r")\s+(\d{4})(?!\d)"), "dmy_ar"),
]
NUM_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?![\w])")


def find_dates(text):
    """Return (set of ISO dates, text with the dates blanked out)."""
    found = set()
    for rx, kind in DATE_PATTERNS:
        def repl(mt):
            g = mt.groups()
            try:
                if kind == "ymd":
                    d = date(int(g[0]), int(g[1]), int(g[2]))
                elif kind == "dmy":
                    d = date(int(g[2]), MONTHS[g[1][:3].lower()], int(g[0]))
                elif kind == "dmy_ar":
                    d = date(int(g[2]), AR_MONTHS[g[1]], int(g[0]))
                elif kind == "mdy":
                    d = date(int(g[2]), MONTHS[g[0][:3].lower()], int(g[1]))
                else:  # dd/mm/yyyy, the common convention outside the US
                    d = date(int(g[2]), int(g[1]), int(g[0]))
                found.add(d.isoformat())
            except (ValueError, KeyError):
                return mt.group(0)
            return " "
        text = rx.sub(repl, text)
    return found, text


def find_numbers(text):
    out = set()
    for mt in NUM_RE.finditer(text):
        whole = mt.group(1).replace(",", "")
        frac = mt.group(2)
        n = whole + ("." + frac.rstrip("0") if frac and frac.rstrip("0") else "")
        out.add(n.lstrip("0") or "0")
    return out


def facts(text):
    text = fold(text)  # Arabic-Indic digits and separators, Arabic month spellings
    dates, rest = find_dates(text)
    return dates, find_numbers(rest)


def norm_ws(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def sentences(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    parts = []
    for block in re.split(r"\n\s*\n|\n(?=\s*[-*]|\s*\d+\.\s|\s*\|)", text):
        block = block.strip()
        if not block:
            continue
        # split on sentence ends that are followed by a capital letter, keeping citations attached
        for s in re.split(r"(?<=[.!?؟])\s+(?=[A-Z\"“\u0621-\u064A])", block):
            s = s.strip()
            if s:
                parts.append(s)
    return parts


def load_sources(root):
    cache = {}

    def get(ref):
        mt = re.match(r"(.+?)#L(\d+)-L(\d+)$", ref)
        path, a, b = (mt.group(1), int(mt.group(2)), int(mt.group(3))) if mt else (ref, None, None)
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            return None
        if full not in cache:
            with open(full, encoding="utf-8", errors="replace") as f:
                cache[full] = f.read().splitlines()
        lines = cache[full]
        if a is None:
            return "\n".join(lines)
        if a < 1 or a > len(lines):
            return None
        return "\n".join(lines[a - 1:b])
    return get


def entry_text(e):
    m = e["meta"] or {}
    parts = [f"{k}: {v if not isinstance(v, list) else ', '.join(v)}" for k, v in m.items()
             if k not in ("id", "recorded_on", "verified_on", "review_by", "related", "supersedes", "tags")]
    return "\n".join(parts) + "\n" + e["body"]


def check(root, text, now, audience="internal"):
    entries = {}
    for e in load_brain(root):
        if e["meta"]:
            entries[e["meta"].get("id") or e["file_id"]] = e
    get_source = load_sources(root)
    results = []
    for s in sentences(text):
        cites = CITE_RE.findall(s)
        body = CITE_RE.sub(" ", s)
        is_calc = "[calc]" in body.lower()
        body = re.sub(r"\[calc\]", " ", body, flags=re.I)
        body_md = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", body)  # drop list markers
        s_dates, s_nums = facts(body_md)
        quotes = QUOTE_RE.findall(body_md)
        row = {"sentence": s.strip(), "citations": cites, "status": "ok", "problems": [], "warnings": []}
        if not cites:
            if s_dates or s_nums:
                row["status"] = "uncited"
                row["problems"].append("states figures or dates without a citation")
            else:
                continue
            results.append(row)
            continue
        support = []
        for c in cites:
            c = c.strip()
            if "#L" in c or c.startswith("sources/"):
                t = get_source(c)
                if t is None:
                    row["problems"].append(f"cited source '{c}' not found (check path and line numbers)")
                else:
                    support.append(t)
                    if audience == "external":
                        row["warnings"].append(f"'{c}' is an internal document: confirm it may be shared")
                continue
            e = entries.get(c)
            if not e:
                row["problems"].append(f"cited entry '{c}' does not exist")
                continue
            support.append(entry_text(e))
            m = e["meta"]
            sens = sensitivity_of(m)
            if audience == "external" and sens == "confidential":
                row["problems"].append(f"'{c}' is confidential: it must not be used in material leaving the business")
            elif audience == "external" and sens == "internal":
                row["warnings"].append(f"'{c}' is internal: confirm it may be shared")
            if e["archived"] or m.get("status") in ("superseded", "archived"):
                row["warnings"].append(f"'{c}' is {m.get('status', 'archived')}: say it is historical or cite the current entry")
            if m.get("status") in ("disputed", "draft"):
                row["warnings"].append(f"'{c}' is {m['status']}: say so in the answer")
            if m.get("confidence") == "low":
                row["warnings"].append(f"'{c}' is low confidence: say so in the answer")
            rb = parse_date(m.get("review_by"))
            if rb and rb < now:
                row["warnings"].append(f"'{c}' was due for review on {rb.isoformat()}: say so or re-check")
        if support:
            sup_text = "\n".join(support)
            sup_dates, sup_nums = facts(sup_text)
            missing_d = sorted(s_dates - sup_dates)
            missing_n = sorted(s_nums - sup_nums, key=lambda x: float(x))
            if is_calc:
                if missing_d or missing_n:
                    row["warnings"].append("calculated figures (show the working): "
                                           + ", ".join(missing_d + missing_n))
            else:
                if missing_d:
                    row["problems"].append("date(s) not in cited sources: " + ", ".join(missing_d))
                if missing_n:
                    row["problems"].append("figure(s) not in cited sources: " + ", ".join(missing_n))
            sup_norm = norm_ws(sup_text)
            for q in quotes:
                if norm_ws(q) not in sup_norm:
                    row["problems"].append(f'quote not found word for word: "{q}"')
        if row["problems"]:
            row["status"] = "fail"
        elif row["warnings"]:
            row["status"] = "warn"
        results.append(row)
    return results


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0].startswith("-"):
        print(__doc__)
        return 2
    root, src = args[0], args[1]
    if not os.path.isdir(root):
        print(f"Brain folder not found: {root}")
        return 2
    text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    now = today(args[args.index("--today") + 1]) if "--today" in args else today()
    audience = args[args.index("--audience") + 1] if "--audience" in args else "internal"
    res = check(root, text, now, audience)
    fails = [r for r in res if r["status"] in ("fail", "uncited")]
    warns = [r for r in res if r["status"] == "warn"]
    oks = [r for r in res if r["status"] == "ok"]
    logged = None
    if "--log" in args and not fails:
        from impact import log_output
        cites = [c.strip() for r in res for c in r.get("citations", [])]
        opt = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
        logged = log_output(root, cites, opt("--kind", "answer"), opt("--log"), opt("--recipient"), audience)
    if "--json" in args:
        print(json.dumps({"supported": len(oks), "warnings": len(warns), "failures": len(fails),
                          "sentences": res, "logged": logged["id"] if logged else None}, indent=2, ensure_ascii=False))
    else:
        print(f"Citation check: {len(oks)} supported, {len(warns)} with warnings, {len(fails)} to fix.")
        for r in fails + warns:
            label = {"fail": "FIX", "uncited": "FIX", "warn": "NOTE"}[r["status"]]
            print(f"\n[{label}] {r['sentence'][:300]}")
            for p in r["problems"]:
                print(f"   - {p}")
            for w in r["warnings"]:
                print(f"   - {w}")
        if logged:
            print(f"\nLogged as {logged['id']}: {len(logged['citations'])} cited entries recorded for impact alerts.")
        elif "--log" in args:
            print("\nNot logged: fix the failures first.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
