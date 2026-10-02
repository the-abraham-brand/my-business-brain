#!/usr/bin/env python3
"""My Business Brain role adapters and people profiles.

LoRA adapters are small overlays that change how a model behaves without retraining it. The
brain has the same idea: a role lens (CFO, operations, sales, people) changes what the Chief of
Staff asks, which specialists it leans on and how it reports, while the brain's facts and
identity stay the same. Lenses switch on and off; several can be used one after another.

People profiles do the same for readers: who a colleague is, which audience they belong to
(team by default, so confidential facts never reach them), the language and style they prefer,
and the areas they work in. A drafter writing for them gets the profile in its memo.

Usage:
  adapter.py <brain> list
  adapter.py <brain> show ID
  adapter.py <brain> use ID | off                 switch a lens on (one at a time) or off
  adapter.py <brain> active
  adapter.py <brain> profile add NAME --role "Operations manager" [--audience team|owner] [--language english|arabic]
                                     [--style "short, bullet points"] [--domains operations,suppliers]
  adapter.py <brain> profile show NAME | list
Standard library only.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import fold, strip_private, today  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED = os.path.join(os.path.dirname(HERE), "adapters")


def all_adapters(root):
    out = {}
    for d in (SHIPPED, os.path.join(root, "_system", "adapters")):
        if os.path.isdir(d):
            for n in sorted(os.listdir(d)):
                if n.endswith(".json") and n != "active.json":
                    try:
                        with open(os.path.join(d, n), encoding="utf-8") as f:
                            a = json.load(f)
                        out[a["id"]] = a
                    except (OSError, ValueError, KeyError):
                        continue
    return out


def active_path(root):
    return os.path.join(root, "_system", "adapters", "active.json")


def active(root):
    try:
        with open(active_path(root), encoding="utf-8") as f:
            aid = json.load(f).get("id")
        return all_adapters(root).get(aid)
    except (OSError, ValueError):
        return None


def use(root, aid):
    os.makedirs(os.path.dirname(active_path(root)), exist_ok=True)
    if aid == "off":
        if os.path.exists(active_path(root)):
            os.remove(active_path(root))
        return {"active": None}
    if aid not in all_adapters(root):
        return {"error": f"no lens '{aid}'. Available: {', '.join(all_adapters(root))}"}
    with open(active_path(root), "w", encoding="utf-8") as f:
        json.dump({"id": aid, "since": today().isoformat()}, f)
    return {"active": aid}


def active_brief(root):
    a = active(root)
    if not a:
        return ""
    return (f"{a['name']}: {a['summary']} Always ask: " + " ".join(a["always_ask"]) +
            f" Report shape: {a['report_shape']}")


def boosts(root):
    a = active(root)
    return dict(a.get("experts", {})) if a else {}


def ppath(root, name):
    slug = re.sub(r"[^a-z0-9]+", "-", fold(name).lower()).strip("-")[:60].strip("-") or "person"
    return os.path.join(root, "_system", "profiles", slug + ".json")


def profile_add(root, name, role="", audience="team", language="", style="", domains=""):
    name = re.sub(r"\s+", " ", strip_private(name or "")).strip()
    if not name:
        return {"error": "a name is needed"}
    if len(name) > 80:
        return {"error": "a name can be at most 80 characters"}
    if audience not in ("team", "owner"):
        return {"error": "audience must be team or owner (outsiders don't get profiles; use --audience external)"}
    rec = {"name": name, "role": strip_private(role)[:80], "audience": audience, "language": language,
           "style": strip_private(style)[:160], "domains": [d.strip() for d in domains.split(",") if d.strip()],
           "updated": today().isoformat()}
    os.makedirs(os.path.dirname(ppath(root, name)), exist_ok=True)
    with open(ppath(root, name), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    return rec


def profile(root, name):
    try:
        with open(ppath(root, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def find_profile(root, name):
    """The profile for a name: an exact match, or the only profile whose name starts with or
    contains it ("Omar" finds "Omar Haddad"). None if there is no match or more than one."""
    p = profile(root, name)
    if p:
        return p
    q = fold(strip_private(name or "")).lower().strip()
    if not q:
        return None
    hits = [x for x in profiles(root) if fold(x["name"]).lower().startswith(q)
            or q in fold(x["name"]).lower().split()]
    return hits[0] if len(hits) == 1 else None


def profiles(root):
    d = os.path.join(root, "_system", "profiles")
    out = []
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            if n.endswith(".json"):
                with open(os.path.join(d, n), encoding="utf-8") as f:
                    out.append(json.load(f))
    return out


def profile_brief(p):
    return (f"Writing for {p['name']}" + (f" ({p['role']})" if p["role"] else "") + f": audience {p['audience']}"
            + (f", in {p['language']}" if p["language"] else "") + (f", style: {p['style']}" if p["style"] else "")
            + (f", works on {', '.join(p['domains'])}" if p["domains"] else "") + ".")


def main(argv):
    args = argv[1:]
    if len(args) < 2 or args[0].startswith("-"):
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    val = lambda n, d="": args[args.index(n) + 1] if n in args and args.index(n) + 1 < len(args) else d
    if cmd == "list":
        cur = (active(root) or {}).get("id")
        for a in all_adapters(root).values():
            print(f"- {a['id']}{' (on)' if a['id'] == cur else ''}: {a['name']}: {a['summary']}")
        return 0
    if cmd == "show" and len(args) > 2:
        a = all_adapters(root).get(args[2])
        print(json.dumps(a, indent=2, ensure_ascii=False) if a else f"No lens '{args[2]}'.")
        return 0 if a else 1
    if cmd == "use" and len(args) > 2:
        out = use(root, args[2])
        print(json.dumps(out))
        return 1 if "error" in out else 0
    if cmd == "active":
        print(active_brief(root) or "No lens on.")
        return 0
    if cmd == "profile" and len(args) > 2:
        sub = args[2]
        if sub == "add" and len(args) > 3:
            out = profile_add(root, args[3], val("--role"), val("--audience", "team"), val("--language"),
                              val("--style"), val("--domains"))
            print(json.dumps(out, ensure_ascii=False))
            return 1 if "error" in out else 0
        if sub == "show" and len(args) > 3:
            p = profile(root, args[3])
            print(profile_brief(p) if p else f"No profile for {args[3]}.")
            return 0 if p else 1
        if sub == "list":
            print("\n".join("- " + profile_brief(p) for p in profiles(root)) or "No profiles yet.")
            return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
