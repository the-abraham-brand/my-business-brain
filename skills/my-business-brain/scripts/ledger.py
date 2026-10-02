"""Shared helpers for the Chief of Staff's ledgers (commitments, delegations): an append-only
JSON-lines store where later lines update earlier ones, and a plain-language date reader.
Standard library only."""
import json
import os
import re
import uuid
from datetime import date, timedelta

from brainlib import fold, parse_date, today

_FULL = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
         "november", "december")
MONTHS = {**{m: i for i, m in enumerate(_FULL, 1)}, **{m[:3]: i for i, m in enumerate(_FULL, 1)}, "sept": 9}
_MON = "|".join(sorted(MONTHS, key=len, reverse=True))
AR_MONTHS = {"يناير": 1, "فبراير": 2, "مارس": 3, "ابريل": 4, "مايو": 5, "يونيو": 6, "يوليو": 7,
             "اغسطس": 8, "سبتمبر": 9, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12}
WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
            "الاثنين": 0, "الثلاثاء": 1, "الاربعاء": 2, "الخميس": 3, "الجمعه": 4, "السبت": 5, "الاحد": 6}


class Ledger:
    def __init__(self, root, name, prefix):
        self.root, self.name, self.prefix = root, name, prefix
        self.path = os.path.join(root, "_system", name + ".jsonl")

    def read(self):
        merged = {}
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(r, dict) and r.get("id"):
                        merged.setdefault(r["id"], {}).update(r)
        return list(merged.values())

    def append(self, rec):
        if not os.path.isdir(self.root):
            raise SystemExit(f"Brain folder not found: {self.root}")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def new_id(self):
        return self.prefix + uuid.uuid4().hex[:6]

    def update(self, rid, **fields):
        if not any(r["id"] == rid for r in self.read()):
            return {"error": f"{rid} not found"}
        return self.append({"id": rid, **fields})


def when(text, now=None):
    """Read a due date from plain words: 2026-10-15, 15 October, Oct 15, tomorrow, Thursday,
    next week, end of month, in 3 days, and the Arabic equivalents. None if there isn't one."""
    now = now or today()
    t = fold(str(text or "")).lower()
    d = parse_date(re.search(r"\d{4}-\d{2}-\d{2}", t).group(0)) if re.search(r"\d{4}-\d{2}-\d{2}", t) else None
    if d:
        return d
    m = re.search(r"(?<!\d)(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + _MON + r")\b\.?(?:,?\s+(\d{4}))?", t)
    if m:
        return _ymd(m.group(3), MONTHS[m.group(2)], int(m.group(1)), now)
    m = re.search(r"\b(" + _MON + r")\b\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?!\d)(?:,?\s+(\d{4}))?", t)
    if m:
        return _ymd(m.group(3), MONTHS[m.group(1)], int(m.group(2)), now)
    for name, num in AR_MONTHS.items():
        m = re.search(r"(\d{1,2})\s+" + name + r"(?:\s+(\d{4}))?", t)
        if m:
            return _ymd(m.group(2), num, int(m.group(1)), now)
    if re.search(r"\b(today|tonight|eod|end of (the )?day)\b|اليوم", t):
        return now
    if re.search(r"\btomorrow\b|غدا|بكره", t):
        return now + timedelta(days=1)
    m = re.search(r"\bin (\d{1,3}) (day|week)s?\b", t)
    if m:
        return now + timedelta(days=int(m.group(1)) * (7 if m.group(2) == "week" else 1))
    if re.search(r"\bnext week\b|الاسبوع (القادم|المقبل)", t):
        return now + timedelta(days=7)
    if re.search(r"\b(end of (the )?month|month[- ]end)\b|نهايه الشهر", t):
        nxt = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
        return nxt - timedelta(days=1)
    if re.search(r"\b(end of (the )?week|eow)\b|نهايه الاسبوع", t):
        return now + timedelta(days=(3 - now.weekday()) % 7)  # Thursday: the Gulf's last working day
    for name, num in WEEKDAYS.items():
        if re.search(r"(?<![\w])" + name + r"(?![\w])", t):
            return now + timedelta(days=(num - now.weekday()) % 7 or 7)
    return None


def _ymd(y, mo, d, now):
    """With no year given, the first matching date from a month ago onwards: on 3 January, "Dec 28"
    is last week; on 1 October, "10 January" is next year."""
    try:
        if y:
            return date(int(y), mo, d)
        for year in (now.year - 1, now.year, now.year + 1):
            try:
                c = date(year, mo, d)
            except ValueError:
                continue
            if c >= now - timedelta(days=31):
                return c
    except ValueError:
        return None
    return None


def cli_today(args):
    """--today YYYY-MM-DD from a command line, today's date without it; None (and a message) if it's invalid."""
    if "--today" not in args:
        return today()
    i = args.index("--today")
    d = parse_date(args[i + 1]) if i + 1 < len(args) else None
    if d is None:
        print("--today needs a date as YYYY-MM-DD")
    return d


def cli_int(args, name, default):
    """An integer option, or None (and a message) if it isn't one."""
    if name not in args:
        return default
    i = args.index(name)
    try:
        return int(args[i + 1])
    except (IndexError, ValueError):
        print(f"{name} needs a whole number")
        return None


def due_label(d, now=None):
    now = now or today()
    if not d:
        return "no date"
    n = (d - now).days
    return "today" if n == 0 else "tomorrow" if n == 1 else f"in {n} days" if n > 1 else \
        "yesterday" if n == -1 else f"{-n} days overdue"
