#!/usr/bin/env python3
"""My Business Brain: the Sunday evening review and updates pack.

One command that runs the week's checks in order and writes one short report the owner can
read in five minutes:

  1. Watch list      what changed at the sources the business follows (official, reputable,
                     social); possible fact changes go to decisions-needed, social items to signals
  2. Health          problems in the brain (stale, conflicting, unsourced, suspicious)
  3. This week       what the brain learned and changed since the last review
  4. Impact          past answers and documents that relied on facts that have since changed
  5. Leads           open sentiment and leads waiting to be confirmed or dismissed
  6. Unsaved facts   things said in sessions that were never stored
  7. Golden answers  key answers that drifted
  8. Toolkit         tools, skills and plugins the brain can use now
  9. Dashboard       refreshed page; on the first review of a month, last month's journal too

Each step runs on its own: if one fails, the rest still run and the report says which failed.
Nothing is changed in the brain's facts. The watch list never stores anything as a fact.

Usage:
  weekly_review.py <brain> [--today YYYY-MM-DD] [--skip watch,toolkit,...] [--lang english|arabic|both]
Writes _system/reviews/<date>.md and prints it. Standard library only.
"""
import json
import os
import subprocess
import sys
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brainlib import today  # noqa: E402

STEPS = ("watch", "health", "diff", "impact", "signals", "promises", "agents", "sweep", "golden", "toolkit",
         "playbook", "dashboard", "journal")


def run(script, *args, timeout=600):
    """Run a sibling script; return (exit code, output). Never raises."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, script), *args], capture_output=True,
                           timeout=timeout, env=env)
        out = (p.stdout or b"").decode("utf-8", "replace").strip()
        err = (p.stderr or b"").decode("utf-8", "replace").strip()
        return p.returncode, out if out else err
    except Exception as e:  # timeout, missing interpreter
        return 99, f"{type(e).__name__}: {e}"


def short(text, lines=25):
    rows = [l for l in text.splitlines() if l.strip()]
    return "\n".join(rows[:lines]) + (f"\n… ({len(rows) - lines} more lines in the full report)" if len(rows) > lines else "")


def last_review(root, now):
    d = os.path.join(root, "_system", "reviews")
    if not os.path.isdir(d):
        return None
    days = sorted(f[:10] for f in os.listdir(d) if f.endswith(".md") and f[:10] < now.isoformat())
    return days[-1] if days else None


def review(root, now, skip=(), lang="english"):
    d = now.isoformat()
    since = last_review(root, now) or (now - timedelta(days=7)).isoformat()
    sections, failed, headline = [], [], {}

    def step(name, title, script, *args, ok=(0,), lines=25, keep=None):
        if name in skip:
            return None
        code, out = run(script, root, *args) if script not in ("brain_diff.py", "toolkit.py") else run(script, *args)
        if code not in ok:
            failed.append(f"{title} (exit {code})")
            sections.append(f"## {title}\n\n_Did not run cleanly:_ {short(out, 5)}\n")
            return None
        body = keep(out) if keep else out
        sections.append(f"## {title}\n\n{short(body, lines) or 'Nothing to report.'}\n")
        return out

    # 1. watch list
    out = step("watch", "Watch list", "watch.py", "check", "--write", "--today", d, lines=30)
    if out is not None:
        headline["watch"] = sum(1 for l in out.splitlines() if l.lstrip().startswith("- "))
    # 2. health (writes the report, fingerprint and today's snapshot)
    out = step("health", "Brain health", "brain_health.py", "--today", d)
    if out is not None:
        for l in out.splitlines():
            if l.startswith("Brain health:"):
                headline["health"] = l.split("|")[0].replace("Brain health:", "").strip()
    # 3. what changed since the last review
    step("diff", "This week in the brain", "brain_diff.py", "diff", root, "--since", since, "--write", "--today", d)
    # 4. impact
    step("impact", "Past work affected by changes", "impact.py")
    # 5. open leads and sentiment
    if "signals" not in skip:
        sys.path.insert(0, HERE)
        from signals import read as read_signals
        rows = [r for r in read_signals(root) if r.get("status") == "open"]
        leads = [r for r in rows if r["kind"] == "lead"]
        new = [r for r in rows if r.get("date", "") > since]
        headline["leads"] = len(leads)
        body = [f"{len(leads)} open lead(s), {len(rows) - len(leads)} sentiment note(s); {len(new)} new since {since}.",
                "Leads are not facts: confirm each at an official or reputable source, or dismiss it.", ""]
        body += [f"- [{r['id']}] {r['kind']}: {r['summary'][:160]} ({r.get('source', '')})"
                 + (" ⚠ " + r["warning"] if r.get("warning") else "") for r in (leads + [r for r in rows if r not in leads])[:15]]
        sections.append("## Sentiment and leads\n\n" + "\n".join(body) + "\n")
    # Chief of Staff: promises both ways, delegated work, how the agents did
    if "promises" not in skip:
        try:
            from commitments import items as commits
            from delegations import items as dels
            cs, ds = commits(root, now=now), dels(root, now=now)
            late = [c for c in cs if c.get("due") and c["due"] < d]
            headline["promises_late"] = len([c for c in late if c["direction"] == "we-owe"])
            body = [f"{len([c for c in cs if c['direction'] == 'we-owe'])} promise(s) we owe, "
                    f"{len([c for c in cs if c['direction'] == 'owed'])} owed to us, {len(ds)} delegated task(s) open."]
            body += [f"- {'We owe' if c['direction'] == 'we-owe' else 'Owed by'} {c['party']}: {c['what'][:120]} ({c['due_label']})"
                     for c in cs[:12]]
            body += [f"- Delegated to {x['owner']}: {x['task'][:120]} ({x['status']}, {x['due_label']})" for x in ds[:8]]
            sections.append("## Promises and delegations\n\n" + "\n".join(body) + "\n")
        except Exception as e:
            failed.append(f"Promises and delegations ({type(e).__name__})")
    if "agents" not in skip:
        code, out = run("delegate.py", root, "scorecard")
        if code == 0:
            sections.append(f"## How the agents did\n\n{short(out, 10)}\n")
    # 6. unsaved facts
    step("sweep", "Unsaved facts", "sweep.py", "--list")
    # 7. golden questions (exit 1 means a regression was found: that is a result, not a failure)
    if "golden" not in skip:
        code, out = run("golden.py", "check", root)
        if code in (0, 1):
            headline["golden"] = "drifted" if code == 1 else "steady"
            sections.append(f"## Golden answers\n\n{short(out) or 'No golden questions set yet.'}\n")
        else:
            failed.append(f"Golden answers (exit {code})")
    # 8. toolkit
    step("toolkit", "Research toolkit", "toolkit.py", root, "detect", lines=15)
    # the week's lessons, preferences and decisions, distilled into the playbook every agent reads first
    step("playbook", "Playbook refreshed", "distill.py", "--today", d, lines=2)
    # 9. dashboard, and the journal on the first review of a month
    step("dashboard", "Dashboard", "dashboard.py", "--lang", lang, "--today", d, lines=3)
    if "journal" not in skip and now.day <= 7:
        prev = (now.replace(day=1) - timedelta(days=1))
        month = f"{prev.year}-{prev.month:02d}"
        jpath = os.path.join(root, "_system", "journal", f"{month}.md")
        if not os.path.exists(jpath):
            code, out = run("journal.py", root, "--month", month, "--write")
            sections.append(f"## Journal for {month}\n\n" + ("Written to `_system/journal/%s.md`." % month if code == 0
                                                             else "_Did not run cleanly._ " + short(out, 3)) + "\n")

    top = [f"# Sunday review: {d}", "", f"Covers {since} to {d}."]
    bits = []
    if "health" in headline:
        bits.append(f"health {headline['health']}")
    if "watch" in headline:
        bits.append(f"{headline['watch']} watch-list item(s)")
    if "leads" in headline:
        bits.append(f"{headline['leads']} open lead(s)")
    if headline.get("promises_late"):
        bits.append(f"{headline['promises_late']} overdue promise(s)")
    if "golden" in headline:
        bits.append(f"golden answers {headline['golden']}")
    if bits:
        top.append("At a glance: " + ", ".join(bits) + ".")
    if failed:
        top.append("Steps that did not run cleanly: " + "; ".join(failed) + ".")
    top += ["", "Nothing in this review changes a fact. Anything that might is listed in "
            "`_system/decisions-needed.md` for the owner to confirm.", ""]
    report = "\n".join(top) + "\n" + "\n".join(sections)
    os.makedirs(os.path.join(root, "_system", "reviews"), exist_ok=True)
    path = os.path.join(root, "_system", "reviews", f"{d}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return {"path": path, "since": since, "headline": headline, "failed": failed, "report": report}


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    if not os.path.isdir(root):
        print(f"Brain folder not found: {root}")
        return 1
    val = lambda n, dflt="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else dflt
    from ledger import cli_today
    now = cli_today(args)
    if now is None:
        return 2
    skip = {s.strip() for s in val("--skip").split(",") if s.strip()}
    res = review(root, now, skip, val("--lang", "english"))
    if "--json" in args:
        print(json.dumps({k: v for k, v in res.items() if k != "report"}, indent=2, ensure_ascii=False))
    else:
        print(res["report"])
        print(f"Saved to {res['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
