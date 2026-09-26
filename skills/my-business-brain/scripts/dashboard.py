#!/usr/bin/env python3
"""My Business Brain dashboard: the brain's state on one page.

Writes a single self-contained HTML file (no scripts, no internet needed) showing the health
score, contract dates coming up, decisions waiting, facts mentioned but not saved, past outputs
that used a changed fact, key answers that changed, any unfinished job, recent changes and the
top issues. Arabic text displays right to left. Light and dark mode follow the device.

Usage:
  dashboard.py <brain> [--out FILE] [--lang english|arabic|both] [--today YYYY-MM-DD]
Default output: _system/dashboard.html. Confidential values are not shown on the page.
Standard library only.
"""
import html
import json
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brainlib import load_brain, parse_date, today, sensitivity_of, strip_private  # noqa: E402
from brain_health import check, score  # noqa: E402

L = {
    "title": ("Business brain", "الدماغ التجاري"),
    "health": ("Health", "الصحة"),
    "facts": ("active facts", "حقيقة نشطة"),
    "deadlines": ("Contract dates coming up", "مواعيد العقود القادمة"),
    "decisions": ("Waiting for your decision", "بانتظار قرارك"),
    "unsaved": ("Mentioned but not saved", "ذُكرت ولم تُحفظ"),
    "impacts": ("Sent with an old value", "أُرسلت بقيمة قديمة"),
    "regress": ("Key answers that changed", "إجابات أساسية تغيّرت"),
    "job": ("Unfinished job", "مهمة غير مكتملة"),
    "recent": ("Changed this week", "تغييرات هذا الأسبوع"),
    "issues": ("Top issues", "أهم الملاحظات"),
    "none": ("Nothing here.", "لا شيء هنا."),
    "updated": ("Updated", "آخر تحديث"),
    "in_days": ("in {n} days", "بعد {n} يوم"),
    "ago": ("{n} days ago", "قبل {n} يوم"),
}


def t(key, lang, **kw):
    en, ar = L[key]
    en, ar = en.format(**kw), ar.format(**kw)
    return ar if lang == "arabic" else f'{en} · <bdi dir="rtl" lang="ar">{ar}</bdi>' if lang == "both" else en


_MASK = []


def esc(s):
    text = strip_private(str(s))
    for v in _MASK:  # values of confidential entries never appear on the page
        text = text.replace(v, "•••")
    return html.escape(text)


def card(title, items, lang, empty_ok=True, tone=""):
    body = "".join(f'<li dir="auto">{i}</li>' for i in items) if items else f'<li class="muted">{t("none", lang)}</li>'
    return f'<section class="card {tone}"><h2 dir="auto">{title} <span class="count">{len(items)}</span></h2><ul>{body}</ul></section>'


def build(root, lang="english", now=None):
    now = now or today()
    entries, active, issues = check(root, now)
    _MASK[:] = sorted({str(e["meta"].get("value")) for e in entries if e["meta"] and e["meta"].get("value")
                       and sensitivity_of(e["meta"]) == "confidential" and len(str(e["meta"].get("value"))) >= 3},
                      key=len, reverse=True)
    s = score(issues)
    deadlines = []
    for e in active:
        m = e["meta"]
        for field, label in (("notice_deadline", "notice"), ("end_date", "ends"), ("renewal_date", "renews")):
            d = parse_date(m.get(field))
            if d and -7 <= (d - now).days <= 90:
                n = (d - now).days
                when = t("in_days", lang, n=n) if n >= 0 else t("ago", lang, n=-n)
                deadlines.append((d, f"<b>{d.isoformat()}</b> {esc(m.get('title'))}: {label} <span class='muted'>({when})</span>"))
    deadlines = [x for _, x in sorted(deadlines)]

    def pending(name, prefix="- [ ]"):
        p = os.path.join(root, "_system", name)
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as f:
            return [esc(l.strip()[len(prefix):].strip()) for l in f if l.lstrip().startswith(prefix)]

    decisions = pending("decisions-needed.md")
    unsaved = pending("unsaved-facts.md")
    impacts = [esc(i["detail"]) for i in issues if i["type"] == "Outdated in past outputs"]
    regress = [esc(i["detail"]) for i in issues if i["type"] == "Knowledge regression"]
    job = []
    try:
        from resume import load, summary
        sm = summary(load(root))
        if sm:
            job = [esc(sm)]
    except Exception:
        pass
    recent = []
    cl = os.path.join(root, "_system", "changelog.md")
    if os.path.exists(cl):
        week_ago = (now - timedelta(days=7)).isoformat()
        with open(cl, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- ") and line[2:12] >= week_ago:
                    recent.append(esc(line[2:]))
    top = [f"<b>{esc(i['severity'])}</b> {esc(i['type'])}: {esc(i['detail'])[:220]}"
           for i in issues if i["severity"] in ("High", "Medium")
           and i["type"] not in ("Outdated in past outputs", "Knowledge regression")][:12]
    tone = "good" if s >= 90 else "warn" if s >= 70 else "bad"
    rtl = ' dir="rtl"' if lang == "arabic" else ""
    cards = [card(t("deadlines", lang), deadlines, lang), card(t("decisions", lang), decisions[:12], lang),
             card(t("unsaved", lang), unsaved[:12], lang), card(t("impacts", lang), impacts, lang, tone="alert" if impacts else ""),
             card(t("regress", lang), regress, lang, tone="alert" if regress else ""), card(t("job", lang), job, lang),
             card(t("recent", lang), recent[-12:], lang), card(t("issues", lang), top, lang)]
    return f"""<!doctype html>
<html lang="{'ar' if lang == 'arabic' else 'en'}"{rtl}><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t('title', lang)}</title>
<style>
:root {{ --bg:#f7f7f5; --card:#fff; --ink:#1d1d1b; --muted:#6b6b66; --line:#e4e4df;
        --good:#1f7a4d; --warn:#b26a00; --bad:#b3261e; --alert:#fff4e5; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#141413; --card:#1e1e1c; --ink:#ededea; --muted:#a3a39e;
        --line:#33332f; --good:#5cc28f; --warn:#f0a93b; --bad:#f28b82; --alert:#2b2418; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:24px 16px; background:var(--bg); color:var(--ink);
       font:15px/1.5 system-ui, -apple-system, "Segoe UI", "Noto Sans Arabic", sans-serif; }}
main {{ max-width:1100px; margin:0 auto; }}
header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:12px 24px; margin-bottom:20px; }}
h1 {{ font-size:22px; margin:0; }}
.score {{ font-size:34px; font-weight:700; }}
.score.good {{ color:var(--good); }} .score.warn {{ color:var(--warn); }} .score.bad {{ color:var(--bad); }}
.muted {{ color:var(--muted); }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:14px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; }}
.card.alert {{ background:var(--alert); }}
h2 {{ font-size:15px; margin:0 0 8px; display:flex; justify-content:space-between; gap:8px; }}
.count {{ color:var(--muted); font-weight:500; }}
ul {{ margin:0; padding-inline-start:18px; }} li {{ margin:4px 0; overflow-wrap:anywhere; }}
footer {{ margin-top:18px; font-size:13px; }}
</style></head><body><main>
<header><h1 dir="auto">{t('title', lang)}</h1>
<span class="score {tone}">{s:g}/100</span><span class="muted">{t('health', lang)}</span><span class="muted"><bdi>{len(active)}</bdi> {t('facts', lang)}</span></header>
<div class="grid">{''.join(cards)}</div>
<footer class="muted">{t('updated', lang)}: {now.isoformat()} · My Business Brain by Abraham</footer>
</main></body></html>
"""


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        return 2
    root = args[0]
    val = lambda n: args[args.index(n) + 1] if n in args else None
    lang = val("--lang") or os.environ.get("CLAUDE_PLUGIN_OPTION_LANGUAGE", "english")
    lang = lang if lang in ("english", "arabic", "both") else "english"
    now = today(val("--today")) if "--today" in args else today()
    out = val("--out") or os.path.join(root, "_system", "dashboard.html")
    page = build(root, lang, now)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Dashboard written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
