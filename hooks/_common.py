"""Shared helpers for My Business Brain hooks. Standard library only; never raises."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "skills", "my-business-brain", "scripts")
sys.path.insert(0, SCRIPTS)

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".claude", "Library", "AppData"}


for _stream in (sys.stdout, sys.stderr):  # Windows consoles default to a legacy code page
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def read_event():
    """The hook's JSON input. Claude Code sends UTF-8; read bytes so Windows code pages can't garble it."""
    try:
        raw = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read().encode("utf-8")
        data = raw.decode("utf-8-sig", errors="replace")
        return json.loads(data) if data.strip() else {}
    except Exception:
        return {}


def option(name, default=""):
    return os.environ.get("CLAUDE_PLUGIN_OPTION_" + name.upper(), default).strip()


def find_brain(start):
    """Brain folder from the plugin setting, else near the working directory."""
    configured = option("brain_folder")
    if configured and os.path.isfile(os.path.join(configured, "BRAIN.md")):
        return configured
    start = start or os.getcwd()
    for cand in (start, os.path.join(start, "business-brain")):
        if os.path.isfile(os.path.join(cand, "BRAIN.md")):
            return cand
    # look two levels down, skipping heavy or hidden folders
    try:
        for name in sorted(os.listdir(start)):
            p = os.path.join(start, name)
            if name.startswith(".") or name in SKIP_DIRS or not os.path.isdir(p):
                continue
            if os.path.isfile(os.path.join(p, "BRAIN.md")):
                return p
            try:
                for sub in sorted(os.listdir(p)):
                    q = os.path.join(p, sub)
                    if not sub.startswith(".") and sub not in SKIP_DIRS and os.path.isfile(os.path.join(q, "BRAIN.md")):
                        return q
            except OSError:
                continue
    except OSError:
        pass
    return None


def brain_root_of(path):
    """Walk up from a file to the folder holding BRAIN.md (max 6 levels)."""
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(6):
        if os.path.isfile(os.path.join(d, "BRAIN.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def emit(event, text):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))
