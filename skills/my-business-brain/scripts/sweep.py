#!/usr/bin/env python3
"""My Business Brain sweep: business facts mentioned in conversation but never saved.

At the end of a session (Claude Code and Cowork run this from the SessionEnd hook), the
user's own messages are scanned for sentences that look like business facts: a price, a
rate, a date, a term, a supplier, a policy, with a figure or a clear change. Anything the
brain already holds (same figures and at least one shared word) is skipped, and so is
anything marked private. The rest is written to _system/unsaved-facts.md, and the next
session brief asks the user whether to save them. Nothing is stored in the brain itself.

Usage:
  sweep.py <brain> --transcript session.jsonl     scan a Claude Code transcript
  sweep.py <brain> --text "message text"          scan one message (prints candidates)
  sweep.py <brain> --list                         show the unsaved facts waiting
  sweep.py <brain> --clear                        empty the list (after saving or dismissing)
Standard library only.
"""
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, fold, strip_private, words, today  # noqa: E402

KEYWORDS = (r"price|priced|pricing|cost|costs|charge|charges|fee|fees|rate|rates|discount|salary|salaries|rent|"
            r"contract|renew|renewal|notice|deadline|supplier|vendor|customer|client|policy|refund|payment terms|"
            r"invoice|vat|tax|licen[cs]e|headcount|hired|hire|office|bank|iban|margin|revenue|target|commission|"
            r"warranty|delivery|lead time|minimum order|moq|plan|package|subscription|retainer")
AR_KEYWORDS = ("سعر", "اسعار", "تكلفه", "رسوم", "خصم", "راتب", "رواتب", "ايجار", "عقد", "تجديد", "مورد", "عميل",
               "سياسه", "استرداد", "ضريبه", "رخصه", "موظف", "عموله", "فاتوره", "هامش", "ايرادات")
CHANGE = r"\b(now|from now|changed|change|new|moved|increase[sd]?|decrease[sd]?|raised|lowered|starting|effective|from \d)"
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
OFF_RECORD = re.compile(r"\b(off the record|don'?t (save|store|remember|record) (this|that|it)|do not (save|store|remember))\b"
                        r"|لا تحفظ|سري للغايه|خارج السجل", re.I)
KW = re.compile(r"\b(" + KEYWORDS + r")\b", re.I)


def sentences(text):
    text = strip_private(text or "")
    for s in re.split(r"(?<=[.!؟?])\s+|\n+", text):
        s = s.strip(" -*•\t")
        if 15 <= len(s) <= 300:
            yield s


def is_fact_like(s):
    if s.endswith(("?", "؟")):
        return False
    f = fold(s).lower()
    has_kw = bool(KW.search(f)) or any(k in f for k in AR_KEYWORDS)
    has_num = bool(NUMBER.search(f))
    has_change = bool(re.search(CHANGE, f)) or any(k in f for k in ("الان", "جديد", "اعتبارا", "تغير"))
    return has_kw and (has_num or has_change)


def off_record(text):
    return bool(OFF_RECORD.search(fold(text or "")))


def brain_numbers(root):
    out = []
    for e in load_brain(root):
        m = e["meta"]
        if not m or e["archived"]:
            continue
        txt = fold(str(m.get("value", "")) + " " + str(m.get("title", "")) + " " + e["body"])
        nums = {n.replace(",", "") for n in NUMBER.findall(txt)}
        out.append((nums, words(txt)))
    return out


def already_known(s, known):
    f = fold(s)
    nums = {n.replace(",", "") for n in NUMBER.findall(f)}
    w = words(f)
    for kn, kw in known:
        if nums and nums <= kn and (w & kw):
            return True
        if not nums and len(w & kw) >= max(3, len(w) // 2):
            return True
    return False


def candidates(root, texts):
    known = brain_numbers(root)
    seen, out = set(), []
    for t in texts:
        if off_record(t):
            continue
        for s in sentences(t):
            key = fold(s).lower()
            if key in seen or not is_fact_like(s) or already_known(s, known):
                continue
            seen.add(key)
            out.append(s)
    return out


def user_messages(transcript):
    """User-typed text from a Claude Code transcript (JSONL), skipping tool results."""
    msgs = []
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("type") != "user" or d.get("isMeta"):
                    continue
                c = (d.get("message") or {}).get("content")
                if isinstance(c, str):
                    msgs.append(c)
                elif isinstance(c, list):
                    msgs.extend(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
    except OSError:
        pass
    return [m for m in msgs if m and not m.lstrip().startswith("<command-")]


def list_path(root):
    return os.path.join(root, "_system", "unsaved-facts.md")


def pending(root):
    p = list_path(root)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [l.strip()[6:] for l in f if l.lstrip().startswith("- [ ]")]


def record(root, facts, when=None):
    if not facts:
        return 0
    have = {fold(x).lower() for x in pending(root)}
    new = [f for f in facts if fold(f).lower() not in have]
    if not new:
        return 0
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    p = list_path(root)
    head = "" if os.path.exists(p) else ("# Mentioned but not saved\n\nBusiness facts from past conversations that "
                                         "were never saved to the brain. Save, correct or dismiss each one.\n")
    with open(p, "a", encoding="utf-8") as f:
        f.write(head + f"\n## {(when or today()).isoformat()}\n\n" + "".join(f"- [ ] {x}\n" for x in new))
    return len(new)


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    if "--list" in args:
        items = pending(root)
        print("\n".join(f"- {x}" for x in items) or "Nothing waiting.")
        return 0
    if "--clear" in args:
        if os.path.exists(list_path(root)):
            os.replace(list_path(root), list_path(root) + ".done")
        print("Cleared.")
        return 0
    if "--text" in args:
        for s in candidates(root, [args[args.index("--text") + 1]]):
            print(f"- {s}")
        return 0
    if "--transcript" in args:
        facts = candidates(root, user_messages(args[args.index("--transcript") + 1]))
        n = record(root, facts)
        print(f"{n} unsaved fact(s) recorded in _system/unsaved-facts.md")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
