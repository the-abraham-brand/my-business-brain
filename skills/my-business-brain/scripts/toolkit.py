#!/usr/bin/env python3
"""My Business Brain toolkit: find the tools, skills and plugins this computer has, and use them.

The brain works on its own, but it gets better with helpers the business may already have
installed. This script looks for them, records what it found in _system/toolkit.json, and says
how the brain will use each one. It never installs, signs in, reads cookies or changes anything
outside the brain folder.

What it looks for:
  - command-line tools: Agent Reach (web, video, RSS and social reading), yt-dlp (video
    transcripts), GitHub CLI, pandoc and pdftotext (document conversion), ffmpeg;
  - Claude skills and plugins installed for this user or project (for example Top-Down Brief,
    Top-Down Verify, the pdf/docx/xlsx skills, Agent Reach's own skill);
  - anything the session reports it has that a script cannot see (claude.ai connectors and
    skills): record those with `note`.

Usage:
  toolkit.py <brain> detect [--probe] [--json]   look again and save; --probe also asks Agent Reach
                                                 which channels work (`agent-reach doctor --json`, read-only)
  toolkit.py <brain> show [--json]               what the brain can use now
  toolkit.py <brain> note NAME --kind skill|plugin|connector|tool [--use "what it's for"]
  toolkit.py <brain> has NAME                    exit 0 if available (for scripts)
Standard library only.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import today  # noqa: E402

# How the brain uses each known helper. Social reading through any tool still follows the trust
# tiers: social and community content becomes sentiment or leads, never facts.
KNOWN_TOOLS = {
    "agent-reach": {"use": "Read web pages, video transcripts, RSS feeds and GitHub for research and the watch list; "
                           "social platforms only as sentiment and leads", "role": "research"},
    "yt-dlp": {"use": "Download subtitles of talks and webinars so they can be saved as cited transcripts",
               "role": "transcripts"},
    "gh": {"use": "Read GitHub repositories and releases for the watch list", "role": "research"},
    "pandoc": {"use": "Convert Word and other documents to text for loading", "role": "documents"},
    "pdftotext": {"use": "Extract text from PDFs for loading", "role": "documents"},
    "ffmpeg": {"use": "Prepare audio for transcription tools", "role": "transcripts"},
}
KNOWN_SKILLS = {
    "top-down-brief": "Write answer-first emails, memos and reports from the brain's facts",
    "top-down-verify": "Fact-check a document against its sources before it goes out",
    "top-down-startup-pitch-deck": "Build an investor deck from what the business knows",
    "agent-reach": "Internet reading router: use it for research and the watch list, with the trust tiers",
    "pdf": "Read and create PDF files", "docx": "Read and create Word files",
    "xlsx": "Read and create spreadsheets", "pptx": "Read and create slide decks",
    "deep-research": "Multi-source research reports; findings are vetted before they are stored",
}


def state_path(root):
    return os.path.join(root, "_system", "toolkit.json")


def load(root):
    try:
        with open(state_path(root), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"tools": {}, "skills": {}, "notes": {}}


def save(root, data):
    os.makedirs(os.path.join(root, "_system"), exist_ok=True)
    tmp = state_path(root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, state_path(root))


def version_of(cmd):
    for flag in ("--version", "version", "-V"):
        try:
            p = subprocess.run([cmd, flag], capture_output=True, text=True, timeout=8)
        except (OSError, subprocess.SubprocessError):
            continue
        out = (p.stdout or p.stderr or "").strip().splitlines()
        if p.returncode == 0 and out:
            return out[0][:80]
    return ""


def skill_roots(extra=()):
    home = os.path.expanduser("~")
    roots = [os.path.join(home, ".claude", "skills"), os.path.join(home, ".claude", "plugins"),
             os.path.join(os.getcwd(), ".claude", "skills"), os.path.join(os.getcwd(), ".claude", "plugins")]
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        roots.append(os.path.dirname(plugin_root))
    return [r for r in list(roots) + list(extra) if os.path.isdir(r)]


def find_skills(roots, max_depth=5):
    """Name -> location for every SKILL.md and plugin manifest under the roots."""
    found = {}
    for root in roots:
        base_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, files in os.walk(root):
            if dirpath.count(os.sep) - base_depth >= max_depth:
                dirnames[:] = []
            dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "__pycache__", "data")]
            if "SKILL.md" in files:
                name = os.path.basename(dirpath)
                try:
                    with open(os.path.join(dirpath, "SKILL.md"), encoding="utf-8", errors="replace") as f:
                        m = re.search(r"^name:\s*(.+)$", f.read(4000), re.M)
                    name = m.group(1).strip().strip("'\"") if m else name
                except OSError:
                    pass
                found.setdefault(name, {"kind": "skill", "path": dirpath})
            if os.path.basename(dirpath) == ".claude-plugin" and "plugin.json" in files:
                try:
                    with open(os.path.join(dirpath, "plugin.json"), encoding="utf-8") as f:
                        man = json.load(f)
                    found.setdefault(man.get("name", os.path.basename(os.path.dirname(dirpath))),
                                     {"kind": "plugin", "path": os.path.dirname(dirpath),
                                      "version": man.get("version", "")})
                except (OSError, ValueError):
                    pass
    return found


def probe_agent_reach():
    """Ask Agent Reach which channels work. Read-only by its own design (doctor)."""
    try:
        p = subprocess.run(["agent-reach", "doctor", "--json"], capture_output=True, text=True, timeout=60)
        data = json.loads(p.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {}
    channels = data.get("channels", data) if isinstance(data, dict) else {}
    out = {}
    if isinstance(channels, dict):
        items = channels.items()
    else:
        items = ((c.get("name"), c) for c in channels if isinstance(c, dict))
    for name, c in items:
        if isinstance(c, dict):
            out[str(name)] = str(c.get("status", c.get("state", "")))
    return out


def detect(root, probe=False, extra_roots=(), now=None):
    old = load(root)
    data = {"checked": (now or today()).isoformat(), "tools": {}, "skills": {}, "notes": old.get("notes", {})}
    for cmd, info in KNOWN_TOOLS.items():
        path = shutil.which(cmd)
        if path:
            data["tools"][cmd] = {"path": path, "version": version_of(cmd), **info}
    if probe and "agent-reach" in data["tools"]:
        data["tools"]["agent-reach"]["channels"] = probe_agent_reach()
    for name, loc in find_skills(skill_roots(extra_roots)).items():
        key = name.split(":")[-1]
        if key == "my-business-brain":
            continue
        data["skills"][name] = {**loc, "use": KNOWN_SKILLS.get(key, "")}
    before = set(old.get("tools", {})) | set(old.get("skills", {}))
    after = set(data["tools"]) | set(data["skills"])
    data["new_since_last"] = sorted(after - before) if old.get("checked") else []
    data["gone_since_last"] = sorted(before - after) if old.get("checked") else []
    save(root, data)
    return data


def available(root, name):
    d = load(root)
    return name in d.get("tools", {}) or name in d.get("skills", {}) or name in d.get("notes", {})


def summary(d):
    lines = []
    known = [(n, t["use"]) for n, t in d.get("tools", {}).items()]
    known += [(n, s["use"]) for n, s in d.get("skills", {}).items() if s.get("use")]
    known += [(n, s.get("use", "")) for n, s in d.get("notes", {}).items()]
    for n, use in known:
        lines.append(f"- {n}: {use}" if use else f"- {n}")
    other = [n for n, s in d.get("skills", {}).items() if not s.get("use")]
    if other:
        lines.append(f"- Also installed: {', '.join(sorted(other)[:20])}" + (" and more" if len(other) > 20 else ""))
    if not lines:
        lines.append("- Nothing extra found. The brain works on its own; Claude's built-in web search and page "
                     "reading cover research.")
    missing = [t for t in ("agent-reach", "yt-dlp") if t not in d.get("tools", {})]
    if missing:
        lines.append("Optional helpers not installed: " + ", ".join(missing)
                     + " (the brain never installs them; the user can if they want them)")
    return "\n".join(lines)


def main(argv):
    args = argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    root, cmd = args[0], args[1]
    if cmd == "detect":
        d = detect(root, "--probe" in args)
        print(json.dumps(d, indent=2, ensure_ascii=False) if "--json" in args else summary(d))
        if d.get("new_since_last") and "--json" not in args:
            print("New since the last check: " + ", ".join(d["new_since_last"]))
        return 0
    if cmd == "show":
        d = load(root)
        print(json.dumps(d, indent=2, ensure_ascii=False) if "--json" in args else summary(d))
        return 0
    if cmd == "note" and len(args) > 2:
        d = load(root)
        kind = args[args.index("--kind") + 1] if "--kind" in args else "skill"
        use = args[args.index("--use") + 1] if "--use" in args else KNOWN_SKILLS.get(args[2], "")
        d.setdefault("notes", {})[args[2]] = {"kind": kind, "use": use, "noted": today().isoformat()}
        save(root, d)
        print(f"Noted {args[2]} ({kind}).")
        return 0
    if cmd == "has" and len(args) > 2:
        return 0 if available(root, args[2]) else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
