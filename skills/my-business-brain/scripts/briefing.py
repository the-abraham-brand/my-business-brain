#!/usr/bin/env python3
"""My Business Brain topic briefings and onboarding packs.

Gathers everything the brain knows about one topic (a supplier, a product line, pricing, a
customer) into a single briefing, with a citation on every fact:

  - the current facts, grouped by area, with linked entries one step away;
  - the history: earlier values that were superseded or archived;
  - what went out: proposals, quotes and emails that used these facts (from the answer log);
  - what is open: decisions waiting and contract dates coming up.

Audiences decide what is included:
  owner     everything (the default)
  team      public and internal facts; confidential ones are withheld and counted
  external  public facts only, for material leaving the business
With --onboarding (no topic needed) it builds a starter pack for a new team member: the
public and internal facts of every area, or of the areas given with --domain.

Usage:
  briefing.py <brain> --topic "Supplier X" [--q "hosting contract"] [--audience owner|team|external]
  briefing.py <brain> --onboarding [--domain products --domain policies] [--audience team]
  add --write to save it in _system/briefings/, --today YYYY-MM-DD to fix the date
Private passages are never included. Standard library only.
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import (load_brain, sensitivity_of, strip_private, today, parse_date, LINK_RE,  # noqa: E402
                      as_list, approx_tokens)
from brain_search import search  # noqa: E402

ALLOWED = {"owner": {"public", "internal", "confidential"}, "team": {"public", "internal"}, "external": {"public"}}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:50] or "briefing"


def related_ids(e):
    ids = set(LINK_RE.findall(e["body"]))
    for f in ("related", "supersedes"):
        for v in as_list(e["meta"].get(f)):
            ids.update(x.strip(" []") for x in str(v).split(",") if x.strip(" []"))
    return ids


def gather(root, topic=None, queries=(), domains=(), audience="owner", onboarding=False, now=None):
    now = now or today()
    allowed = ALLOWED.get(audience, ALLOWED["owner"])
    everything = [e for e in load_brain(root) if e["meta"]]
    by_id = {(e["meta"].get("id") or e["file_id"]): e for e in everything}
    if onboarding:
        chosen = [e for e in everything if not e["archived"]
                  and e["meta"].get("status", "active") in ("active", "disputed")
                  and (not domains or e["meta"].get("domain") in domains)]
    else:
        hits = search(root, [topic] + list(queries), top=25, use_sources=False, now=now)
        top_score = max((h["score"] for h in hits if h["kind"] == "entry"), default=0)
        # keep clear matches only: a passing mention scores far below the real subject
        ids = [h["id"] for h in hits if h["kind"] == "entry" and h["score"] >= 0.5 * top_score]
        for i in list(ids):  # one step along the links
            if i in by_id:
                ids += [r for r in related_ids(by_id[i]) if r in by_id and r not in ids]
        chosen = [by_id[i] for i in dict.fromkeys(ids) if i in by_id and not by_id[i]["archived"]
                  and (not domains or by_id[i]["meta"].get("domain") in domains)]
    withheld = [e for e in chosen if sensitivity_of(e["meta"]) not in allowed]
    chosen = [e for e in chosen if sensitivity_of(e["meta"]) in allowed]
    keys = {str(e["meta"].get("key", "")).lower() for e in chosen if e["meta"].get("key")}
    history = [e for e in everything if e["archived"] and str(e["meta"].get("key", "")).lower() in keys
               and sensitivity_of(e["meta"]) in allowed]
    chosen_ids = {(e["meta"].get("id") or e["file_id"]) for e in chosen}
    outputs = []
    log = os.path.join(root, "_system", "answer-log.jsonl")
    if os.path.exists(log) and audience != "external":
        with open(log, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                used = [c for c in r.get("citations", []) if c.get("id") in chosen_ids]
                if used:
                    outputs.append({"at": r.get("at", "")[:10], "kind": r.get("kind", ""), "recipient": r.get("recipient", ""),
                                    "purpose": r.get("purpose", ""), "facts": [f"{c.get('id')} = {c.get('value')}" if c.get("value") else str(c.get("id")) for c in used]})
    dates = []
    for e in chosen:
        m = e["meta"]
        seen_days = set()
        for field, label in (("notice_deadline", "notice deadline"), ("end_date", "ends"), ("review_by", "review due")):
            d = parse_date(m.get(field))
            if d in seen_days:
                continue
            seen_days.add(d)
            if d and d >= now and (field != "review_by" or (d - now).days <= 60):
                dates.append((d.isoformat(), f"{m.get('title')}: {label}", m.get("id") or e["file_id"]))
    words = [w for w in re.findall(r"\w+", (topic or "").lower()) if len(w) > 2]
    waiting = []
    dn = os.path.join(root, "_system", "decisions-needed.md")
    if os.path.exists(dn) and not onboarding:
        with open(dn, encoding="utf-8") as f:
            for line in f:
                if line.lstrip().startswith("- [ ]") and (any(w in line.lower() for w in words)
                                                           or any(i in line for i in chosen_ids)):
                    waiting.append(strip_private(line.strip()[6:]))
    return {"topic": topic, "onboarding": onboarding, "audience": audience, "date": now.isoformat(),
            "facts": chosen, "withheld": len(withheld), "history": history, "outputs": outputs,
            "dates": sorted(dates), "waiting": waiting if audience == "owner" else []}


def render(b):
    title = "Onboarding pack" if b["onboarding"] else f"Briefing: {b['topic']}"
    aud = {"owner": "for the owner (includes confidential facts)", "team": "for the team (no confidential facts)",
           "external": "for people outside the business (public facts only)"}[b["audience"]]
    lines = [f"# {title}", "", f"{b['date']} · {aud}", "", "## In short", "",
             "_Write two or three sentences here: the answer a busy reader needs, drawn only from the facts below._", ""]
    groups = defaultdict(list)
    for e in b["facts"]:
        groups[e["meta"].get("domain", "other")].append(e)
    lines.append(f"## What we know ({len(b['facts'])} fact{'s' if len(b['facts']) != 1 else ''})")
    for dom in sorted(groups):
        lines += ["", f"### {dom.replace('-', ' ').capitalize()}", ""]
        for e in sorted(groups[dom], key=lambda x: x["meta"].get("title", "")):
            m = e["meta"]
            eid = m.get("id") or e["file_id"]
            head = f"- **{m.get('title', eid)}**" + (f": {m.get('value')}" if m.get("value") else "")
            flags = []
            if m.get("status") == "disputed":
                flags.append("disputed")
            if str(m.get("confidence", "")) == "low":
                flags.append("low confidence")
            if sensitivity_of(m) == "confidential":
                flags.append("confidential")
            body = strip_private(e["body"]).strip().split("\n")[0][:300]
            lines.append(head + (f" ({', '.join(flags)})" if flags else "") + f" [[{eid}]]")
            if body and body != str(m.get("value", "")):
                lines.append(f"  {body}")
    if b["withheld"]:
        lines += ["", f"_{b['withheld']} confidential fact(s) left out for this audience._"]
    if b["history"]:
        lines += ["", "## History", ""]
        for e in sorted(b["history"], key=lambda x: str(x["meta"].get("recorded_on", ""))):
            m = e["meta"]
            lines.append(f"- {m.get('recorded_on', '')}: {m.get('title')} was {m.get('value', '')} "
                         f"({m.get('status', 'archived')}) [[{m.get('id') or e['file_id']}]]")
    if b["outputs"]:
        lines += ["", "## What went out", ""]
        for o in b["outputs"][-15:]:
            lines.append(f"- {o['at']}: {o['kind']}" + (f" to {o['recipient']}" if o["recipient"] else "")
                         + (f" ({o['purpose']})" if o["purpose"] else "") + f", using {'; '.join(o['facts'])}")
    if b["dates"]:
        lines += ["", "## Coming up", ""] + [f"- {d}: {t} [[{i}]]" for d, t, i in b["dates"][:10]]
    if b["waiting"]:
        lines += ["", "## Waiting for a decision", ""] + [f"- {w}" for w in b["waiting"][:10]]
    lines += ["", "---", "Every fact above cites its entry. Built from the business brain; check anything "
              "marked disputed or low confidence before relying on it."]
    return "\n".join(lines) + "\n"


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-") or not ("--topic" in args or "--onboarding" in args):
        print(__doc__)
        return 2
    root = args[0]
    val = lambda n: args[args.index(n) + 1] if n in args else None
    now = today(val("--today")) if "--today" in args else today()
    queries = [args[i + 1] for i, a in enumerate(args) if a == "--q"]
    domains = [args[i + 1] for i, a in enumerate(args) if a == "--domain"]
    audience = val("--audience") or ("team" if "--onboarding" in args else "owner")
    if audience not in ALLOWED:
        print("--audience must be owner, team or external")
        return 2
    b = gather(root, val("--topic"), queries, domains, audience, "--onboarding" in args, now)
    md = render(b)
    if "--write" in args:
        d = os.path.join(root, "_system", "briefings")
        os.makedirs(d, exist_ok=True)
        name = f"{'onboarding' if b['onboarding'] else slug(b['topic'])}-{audience}-{b['date']}.md"
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved _system/briefings/{name} ({len(b['facts'])} facts, about {approx_tokens(md)} tokens)")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
