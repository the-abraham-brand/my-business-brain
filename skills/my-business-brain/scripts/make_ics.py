#!/usr/bin/env python3
"""Build an .ics calendar file for Contract Clocks, with reminders 7 days, 3 days and
24 hours before every event. Works with Apple Calendar, Google Calendar, Outlook,
Thunderbird, Nextcloud, Proton and any CalDAV calendar.

Usage: python3 make_ics.py events.json output.ics

events.json:
{
  "calendar_name": "Contract Clocks",
  "timezone": "Asia/Dubai",            # optional IANA zone; omitted = floating local time
  "events": [
    {"uid": "supplier-x-notice", "date": "2027-11-15", "time": "09:00",
     "duration_minutes": 30,
     "title": "⏰ [Notice deadline] Supplier X service agreement",
     "description": "Send written notice ... Clause 14.2. Brain entry: contracts-supplier-x",
     "reminders": ["P7D", "P3D", "PT24H"]}   # optional; this is the default
  ]
}
Standard library only.
"""
import json
import sys
from datetime import datetime, timedelta, timezone

DEFAULT_REMINDERS = ["P7D", "P3D", "PT24H"]
LABEL = {"P7D": "7 days", "P3D": "3 days", "PT24H": "24 hours", "P1D": "1 day"}


def esc(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n")


def fold(line):
    """Fold lines longer than 75 octets (RFC 5545 3.1)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > (75 if not parts else 74):
            parts.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)


def build(spec):
    tz = spec.get("timezone")
    zone = None
    if tz:
        try:
            from zoneinfo import ZoneInfo
            zone = ZoneInfo(tz)
        except Exception:
            print(f"Time zone '{tz}' not available; using floating local time.", file=sys.stderr)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//The Abraham Brand//My Business Brain Contract Clocks//EN",
           "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(spec.get('calendar_name', 'Contract Clocks'))}"]
    if tz:
        out.append(f"X-WR-TIMEZONE:{tz}")
    for i, ev in enumerate(spec["events"]):
        start = datetime.strptime(f"{ev['date']} {ev.get('time', '09:00')}", "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=int(ev.get("duration_minutes", 30)))
        fmt = "%Y%m%dT%H%M%S"
        if zone:
            # Convert to UTC so every calendar app shows the right local time without a VTIMEZONE block.
            dt = lambda d: ":" + d.replace(tzinfo=zone).astimezone(timezone.utc).strftime(fmt) + "Z"
        else:
            dt = lambda d: ":" + d.strftime(fmt)  # floating: 09:00 wherever the user is
        uid = ev.get("uid") or f"contract-clock-{i}-{start.strftime('%Y%m%d')}"
        out += ["BEGIN:VEVENT", f"UID:{uid}@my-business-brain", f"DTSTAMP:{stamp}",
                f"DTSTART{dt(start)}", f"DTEND{dt(end)}", f"SUMMARY:{esc(ev['title'])}"]
        if ev.get("description"):
            out.append(f"DESCRIPTION:{esc(ev['description'])}")
        out += ["CATEGORIES:Contract Clocks", "TRANSP:TRANSPARENT"]
        for r in ev.get("reminders", DEFAULT_REMINDERS):
            out += ["BEGIN:VALARM", "ACTION:DISPLAY", f"TRIGGER:-{r}",
                    f"DESCRIPTION:{esc('In ' + LABEL.get(r, r) + ': ' + ev['title'])}", "END:VALARM"]
        out.append("END:VEVENT")
    out.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in out) + "\r\n"


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    data = build(spec)
    with open(argv[2], "w", encoding="utf-8", newline="") as f:
        f.write(data)
    n = len(spec["events"])
    print(f"Wrote {argv[2]}: {n} event(s), {data.count('BEGIN:VALARM')} reminders.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
