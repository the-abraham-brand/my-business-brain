#!/usr/bin/env python3
"""My Business Brain ingest planner: merge candidate facts from one or many readers
(for example parallel sub-agents in a bulk load) and decide what happens to each.

Usage:
  python3 ingest_plan.py <brain-folder> candidates.json [more.json ...]
                         [--write] [--auto 0.9] [--today YYYY-MM-DD] [--json]

Each file holds a JSON list of candidates (the reader's output; readers never write
to the brain):
  {"title": "Growth plan monthly price", "type": "price", "domain": "pricing",
   "key": "price.growth-plan.monthly", "value": "AED 14,999 per month",
   "source": "Price list v3, Aug 2026", "source_type": "internal-document",
   "location": "p.2, table 1", "quote": "Growth ... AED 14,999 / month",
   "confidence": "high", "body": "optional detail", "related": ["products-growth-plan"],
   "tags": ["plans"], "sensitivity": "internal",
   "extra": {"counterparty": "...", "end_date": "2027-01-14"}}

Each candidate gets one action:
  new       nothing like it in the brain or the batch -> write it (with --write)
  refresh   same key and same value already stored -> refresh the existing entry's source/date
  conflict  same key, different value (in the brain, or between two candidates in the batch)
            -> never written; goes to _system/decisions-needed.md for the user
  overlap   similar title or wording to an existing entry but no shared key -> propose merge or link
  duplicate repeated within the batch with the same value -> folded into the first
  invalid   missing title, domain or source -> send back to the reader
  confirm   the reader's "certainty" (0-1) for this fact is below the auto-apply threshold
            (--auto, default 0.9) -> not written; shown to the user to confirm
  signal    the source is social or community (a post, thread, review or comment): never stored
            as a fact; kept as sentiment or a lead in _system/signals.md (with --write)
  private    the candidate was marked private (<private>...</private>): never stored
  quarantine the candidate contains text that tries to instruct an AI (possible prompt
            injection) -> never written; logged in decisions-needed for the user to see
With --write, "new" entries are created with review dates by type, conflicts are appended
to _system/decisions-needed.md, and every change is logged in _system/changelog.md.
Refreshes and overlaps are listed for the coordinator to apply or propose.
Standard library only.
"""
import json
import os
import re
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import read_text, load_brain, norm, words, jaccard, today, parse_date, SENSITIVITY, injection_hits, CONFIDENTIAL_DOMAINS, strip_private, has_private, source_tier, load_trusted

OVERLAP = 0.6
SIX_MONTH = {"price"}
SIX_MONTH_DOMAINS = {"pricing", "legal-regulatory", "finance"}


def slug(s, n=60):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")[:n].strip("-")


def add_months(d, n):
    import calendar
    from datetime import date
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def review_by(c, now):
    if c.get("type") == "decision":
        return "9999-12-31"
    extra = c.get("extra") or {}
    if c.get("type") == "contract" and parse_date(extra.get("notice_deadline")):
        return extra["notice_deadline"]
    if c.get("type") in SIX_MONTH or c.get("domain") in SIX_MONTH_DOMAINS \
            or c.get("source_type") == "external-verified":
        return add_months(now, 6).isoformat()
    return add_months(now, 12).isoformat()


def plan(root, cands, now, auto=0.9):
    trusted = load_trusted(root)
    entries = [e for e in load_brain(root) if e["meta"] and not e["archived"]
               and e["meta"].get("status", "active") in ("active", "draft", "disputed")]
    by_key = {}
    for e in entries:
        k = str(e["meta"].get("key", "")).strip().lower()
        if k:
            by_key.setdefault(k, []).append(e)
    feats = [(e, words(e["meta"].get("title", "")), words(e["body"] + " " + str(e["meta"].get("value", ""))))
             for e in entries]
    taken = {e["meta"].get("id") or e["file_id"] for e in load_brain(root) if e["meta"]}
    batch_keys = {}
    out = []
    for n, c in enumerate(cands, 1):
        c = dict(c)
        c["_n"] = n
        # Off the record: private passages never reach the brain.
        private = [f for f in ("title", "value", "body", "quote", "location") if has_private(c.get(f))]
        for f in private:
            c[f] = strip_private(c[f]).strip()
        if private and not (c.get("value") or c.get("body")):
            out.append({"n": n, "title": "(private)", "key": "", "value": "", "domain": c.get("domain", ""),
                        "source": c.get("source", ""), "location": "", "reader": c.get("_file", ""),
                        "action": "private", "reason": "marked private: not stored"})
            continue
        row = {"n": n, "title": c.get("title", ""), "key": c.get("key", ""), "value": c.get("value", ""),
               "domain": c.get("domain", ""), "source": c.get("source", ""), "location": c.get("location", ""),
               "reader": c.get("_file", "")}
        if not c.get("title") or not c.get("domain") or not c.get("source"):
            row.update(action="invalid", reason="missing title, domain or source")
            out.append(row)
            continue
        hits = injection_hits(" ".join(str(c.get(f, "")) for f in
                                       ("title", "value", "body", "quote", "location", "source")))
        if hits:
            row.update(action="quarantine", reason=f"text that tries to instruct an AI: \"{hits[0][:100]}\"")
            out.append(row)
            continue
        tier = source_tier(c.get("source_url") or c.get("source"), trusted)
        doc = str(c.get("source_path") or c.get("location") or c.get("source") or "").split("#")[0].strip()
        if doc.startswith("sources/") and os.path.isfile(os.path.join(root, doc)):
            from brainlib import source_meta  # a transcript or saved page declares its own tier
            tier = source_meta(os.path.join(root, doc), trusted).get("tier") or tier
        row["tier"] = tier
        if tier == "social":
            row.update(action="signal", reason="social or community source: kept as "
                       + ("sentiment" if c.get("signal_kind") == "sentiment" else "a lead") + ", not stored as a fact",
                       _c=c)
            out.append(row)
            continue
        if tier in ("other", "recording") and str(c.get("confidence", "medium")) == "high":
            c["confidence"] = "medium"  # not an official or reputable source: never high confidence
        k = str(c.get("key", "")).strip().lower()
        v = norm(c.get("value", ""))
        if k and k in by_key:
            same = [e for e in by_key[k] if norm(e["meta"].get("value", "")) == v]
            if same:
                row.update(action="refresh", target=same[0]["meta"]["id"],
                           reason="same key and value already stored")
            else:
                ex = by_key[k][0]["meta"]
                row.update(action="conflict", target=ex["id"],
                           reason=f"brain has {ex.get('value')} (source: {ex.get('source')}, "
                                  f"recorded {ex.get('recorded_on')})")
            out.append(row)
            continue
        if k and k in batch_keys:
            versions = batch_keys[k]
            same = [r for r in versions if norm(r["value"]) == v]
            if same:
                row.update(action="duplicate", target=f"candidate {same[0]['n']}",
                           reason="same key and value earlier in this batch")
            else:
                others = "; ".join(f"{r['value']} ({r['source']})" for r in versions)
                row.update(action="conflict", target=f"candidate {versions[0]['n']}",
                           reason=f"other documents in this batch say {others}")
                for r in versions:
                    if r.get("action") == "new":
                        r["action"] = "conflict"
                        r["target"] = f"candidate {n}"
                        r["reason"] = f"another document in this batch says {c.get('value')} ({c.get('source')})"
                versions.append(row)
            out.append(row)
            continue
        tw, bw = words(c.get("title", "")), words(str(c.get("body", "")) + " " + str(c.get("value", "")))
        best, best_s = None, 0.0
        for e, et, eb in feats:
            s = max(jaccard(tw, et), jaccard(bw, eb) if len(bw | eb) >= 8 else 0)
            if s > best_s:
                best, best_s = e, s
        if best is not None and best_s >= OVERLAP:
            row.update(action="overlap", target=best["meta"]["id"],
                       reason=f"similar to existing entry ({best_s:.0%}); merge or link")
            out.append(row)
            continue
        base = f"{slug(c['domain'], 20)}-{slug(c['title'])}"
        eid, i = base, 2
        while eid in taken:
            eid, i = f"{base}-{i}", i + 1
        taken.add(eid)
        cert = c.get("certainty")
        if isinstance(cert, (int, float)) and cert < auto:
            row.update(action="confirm", reason=f"reader certainty {cert:.2f} is below the auto-apply threshold {auto:.2f}")
            out.append(row)
            continue
        row.update(action="new", id=eid, reason="nothing similar stored", _c=c)
        if k:
            batch_keys[k] = [row]
        out.append(row)
    return out


def yaml_val(v):
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    s = str(v).replace("\n", " ")
    return s


def write(root, rows, now):
    written = []
    for r in rows:
        if r["action"] != "new":
            continue
        c = r["_c"]
        folder = os.path.join(root, "entries", slug(c["domain"], 40))
        os.makedirs(folder, exist_ok=True)
        meta = [("id", r["id"]), ("title", c["title"]), ("type", c.get("type", "fact")),
                ("domain", slug(c["domain"], 40))]
        if c.get("key"):
            meta += [("key", c["key"]), ("value", c.get("value", ""))]
        meta += [("status", "active"), ("source", c["source"] + (f", {c['location']}" if c.get("location") else "")),
                 ("source_type", c.get("source_type", "internal-document")),
                 ("recorded_on", now.isoformat())]
        if c.get("source_type") == "external-verified":
            meta.append(("verified_on", now.isoformat()))
        sens = str(c.get("sensitivity", "")).lower()
        if sens not in SENSITIVITY:
            sens = "confidential" if slug(c["domain"], 40) in CONFIDENTIAL_DOMAINS else "internal"
        meta += [("review_by", review_by(c, now)), ("confidence", c.get("confidence", "medium")),
                 ("sensitivity", sens)]
        for k2, v2 in (c.get("extra") or {}).items():
            meta.append((k2, v2))
        if c.get("related"):
            meta.append(("related", c["related"]))
        if c.get("tags"):
            meta.append(("tags", c["tags"]))
        body = str(c.get("body") or c.get("value") or c["title"]).strip()
        if c.get("quote"):
            body += f"\n\nSource wording: \"{c['quote']}\""
        text = "---\n" + "\n".join(f"{k}: {yaml_val(v)}" for k, v in meta) + "\n---\n\n" + body + "\n"
        with open(os.path.join(folder, r["id"] + ".md"), "w", encoding="utf-8") as f:
            f.write(text)
        written.append(r["id"])
    sysdir = os.path.join(root, "_system")
    os.makedirs(sysdir, exist_ok=True)
    signals = [r for r in rows if r["action"] == "signal"]
    if signals:
        from signals import add as add_signal
        for r in signals:
            c = r["_c"]
            summary = c.get("body") or (f"{c['title']}: {c['value']}" if c.get("value") else c["title"])
            add_signal(root, "sentiment" if c.get("signal_kind") == "sentiment" else "lead", summary,
                       c.get("source_url") or c["source"], topic=c.get("domain", ""), when=now)
    conflicts = [r for r in rows if r["action"] == "conflict"]
    quarantined = [r for r in rows if r["action"] == "quarantine"]
    if quarantined:
        path = os.path.join(sysdir, "decisions-needed.md")
        old = read_text(path, "# Decisions needed\n")
        head, _, rest = old.partition("\n")
        lines = [f"- [ ] {now.isoformat()} **Suspicious instructions** in {r['source'] or r['reader']}"
                 f"{', ' + r['location'] if r['location'] else ''}: {r['reason']}. Not stored and not followed. "
                 f"Check the document's origin." for r in quarantined]
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n\n" + "\n".join(lines) + "\n" + rest)
    if conflicts:
        groups = {}
        for r in conflicts:
            groups.setdefault(str(r["key"] or r["title"]).lower(), []).append(r)
        lines = []
        for key, grp in groups.items():
            versions = [f"{r['value']} ({r['source']}{', ' + r['location'] if r['location'] else ''})" for r in grp]
            brain = next((r["reason"] for r in grp if r["reason"].startswith("brain has")), "")
            lines.append(f"- [ ] {now.isoformat()} **Conflict** `{grp[0]['key'] or grp[0]['title']}`: "
                         + ("; ".join([brain] if brain else []) + ("; " if brain else ""))
                         + "new documents say " + "; ".join(versions) + ". Which is current?")
        path = os.path.join(sysdir, "decisions-needed.md")
        old = read_text(path, "# Decisions needed\n")
        head, _, rest = old.partition("\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n\n" + "\n".join(lines) + "\n" + rest)
    with open(os.path.join(sysdir, "changelog.md"), "a", encoding="utf-8") as f:
        d = now.isoformat()
        f.write(f"- {d} Bulk load: added {len(written)}"
                + (": " + ", ".join(f"[[{w}]]" for w in written) if written else "") + "\n")
        if conflicts:
            f.write(f"- {d} Bulk load: {len(conflicts)} conflict(s) sent to decisions-needed\n")
        if quarantined:
            f.write(f"- {d} Bulk load: {len(quarantined)} candidate(s) quarantined for suspicious instructions\n")
        if signals:
            f.write(f"- {d} Bulk load: {len(signals)} social or community item(s) kept as sentiment or leads\n")
    return written


def main(argv):
    args = argv[1:]
    files = [a for a in args[1:] if not a.startswith("--") and a.endswith(".json")]
    if len(args) < 2 or not files:
        print(__doc__)
        return 2
    root = args[0]
    now = today(args[args.index("--today") + 1]) if "--today" in args else today()
    cands = []
    for p in files:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        for c in data if isinstance(data, list) else data.get("candidates", []):
            c["_file"] = os.path.basename(p)
            cands.append(c)
    auto = float(args[args.index("--auto") + 1]) if "--auto" in args else 0.9
    rows = plan(root, cands, now, auto)
    written = write(root, rows, now) if "--write" in args else []
    counts = {}
    for r in rows:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    if "--json" in args:
        print(json.dumps({"counts": counts, "written": written,
                          "rows": [{k: v for k, v in r.items() if k != "_c"} for r in rows]},
                         indent=2, ensure_ascii=False))
        return 0
    print("Ingest plan: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
          + (f" | written {len(written)}" if "--write" in args else " | dry run (add --write to apply)"))
    for r in rows:
        if r["action"] == "new" and "--write" in args:
            continue
        tgt = f" -> {r.get('target') or r.get('id', '')}" if r.get("target") or r.get("id") else ""
        print(f"- [{r['action']}] #{r['n']} {r['title']}"
              + (f" = {r['value']}" if r["value"] else "") + tgt + f" ({r['reason']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
