#!/usr/bin/env python3
"""Contract Clocks date calculator.

Usage:
  python3 contract_dates.py --start 2026-01-15 --term 12m [--notice 60d] [--renewal 12m]
                            [--end 2027-01-14] [--end-inclusive|--end-exclusive] [--today YYYY-MM-DD]
                            [--weekend sat,sun | fri,sat] [--json]

Terms and notice periods: <n>d (calendar days), <n>bd (business days), <n>w, <n>m, <n>y.
By default a 12-month term starting 15 Jan ends on 14 Jan the following year (the day
before the anniversary), the common drafting convention; pass --end-exclusive to use the
anniversary itself, or --end to give the contract's stated end date.
The notice deadline is the last day notice can be given: end date minus the notice period.
Weekend days default to Saturday and Sunday; use --weekend fri,sat for Friday-Saturday weekends.
Public holidays are not known to this script: check them for the jurisdiction.
"""
import argparse
import calendar
import json
import re
import sys
from datetime import date, timedelta

DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def add_months(d, n):
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def parse_period(s):
    mt = re.fullmatch(r"\s*(\d+)\s*(bd|d|w|m|y)\s*", s.lower())
    if not mt:
        raise ValueError(f"Bad period '{s}': use e.g. 30d, 10bd, 6w, 12m, 1y")
    return int(mt.group(1)), mt.group(2)


def shift(d, period, weekend, sign=1):
    n, unit = parse_period(period)
    if unit == "d":
        return d + timedelta(days=sign * n)
    if unit == "w":
        return d + timedelta(weeks=sign * n)
    if unit == "m":
        return add_months(d, sign * n)
    if unit == "y":
        return add_months(d, sign * 12 * n)
    cur, left = d, n
    while left:
        cur += timedelta(days=sign)
        if cur.weekday() not in weekend:
            left -= 1
    return cur


def term_longer_than_month(start, end):
    """True when the term runs beyond one calendar month (end after start + 1 month - 1 day)."""
    return end > add_months(start, 1) - timedelta(days=1)


def prev_working_day(d, weekend):
    while d.weekday() in weekend:
        d -= timedelta(days=1)
    return d


def main(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", required=True)
    p.add_argument("--term")
    p.add_argument("--end")
    p.add_argument("--notice")
    p.add_argument("--renewal", help="auto-renewal period, e.g. 12m")
    p.add_argument("--renewals", type=int, default=3, help="how many renewal cycles to project (default 3)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--end-inclusive", action="store_true", default=True)
    g.add_argument("--end-exclusive", action="store_true")
    p.add_argument("--weekend", default="sat,sun")
    p.add_argument("--today")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    weekend = {DAYS[x.strip()[:3].lower()] for x in a.weekend.split(",")}
    start = date.fromisoformat(a.start)
    if a.end:
        end = date.fromisoformat(a.end)
    elif a.term:
        end = shift(start, a.term, weekend)
        if not a.end_exclusive:
            end -= timedelta(days=1)
    else:
        p.error("give --term or --end")
    now = date.fromisoformat(a.today) if a.today else date.today()

    def describe(d):
        info = {"date": d.isoformat(), "weekday": d.strftime("%A"), "days_from_today": (d - now).days}
        if d.weekday() in weekend:
            info["weekend"] = True
            info["act_by"] = prev_working_day(d, weekend).isoformat()
        return info

    out = {"start": describe(start), "end": describe(end),
           "term_days": (end - start).days + 1,
           "qualifies_for_contract_clocks": term_longer_than_month(start, end) or bool(a.renewal)}
    if a.notice:
        out["notice_period"] = a.notice
        out["notice_deadline"] = describe(shift(end, a.notice, weekend, sign=-1))
    if a.renewal:
        cycles, cur_end = [], end
        for _ in range(a.renewals):
            nxt_start = cur_end + timedelta(days=1)
            nxt_end = shift(nxt_start, a.renewal, weekend) - timedelta(days=1)
            c = {"renewal_start": describe(nxt_start), "renewal_end": describe(nxt_end)}
            if a.notice:
                c["notice_deadline"] = describe(shift(nxt_end, a.notice, weekend, sign=-1))
            cycles.append(c)
            cur_end = nxt_end
        out["renewals"] = cycles
    out["note"] = "Public holidays not checked; confirm for the contract's jurisdiction."

    if a.json:
        print(json.dumps(out, indent=2))
        return 0
    print(f"Start:            {out['start']['date']} ({out['start']['weekday']})")
    print(f"End:              {out['end']['date']} ({out['end']['weekday']}), term {out['term_days']} days")
    print(f"Qualifies (>1 month or auto-renewing): {'yes' if out['qualifies_for_contract_clocks'] else 'no'}")
    if a.notice:
        nd = out["notice_deadline"]
        flag = f"  WEEKEND: act by {nd['act_by']}" if nd.get("weekend") else ""
        print(f"Notice deadline:  {nd['date']} ({nd['weekday']}), {nd['days_from_today']} days from today{flag}")
    for i, c in enumerate(out.get("renewals", []), 1):
        extra = f", notice by {c['notice_deadline']['date']}" if "notice_deadline" in c else ""
        print(f"Renewal {i}:        {c['renewal_start']['date']} to {c['renewal_end']['date']}{extra}")
    print(out["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
