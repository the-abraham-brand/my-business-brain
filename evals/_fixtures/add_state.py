#!/usr/bin/env python3
"""Add history to the test brain built by make_brain.py, for the regression and impact evals.

  add_state.py <brain> answer-log   two logged outputs that quoted the Scale plan at AED 14,999
  add_state.py <brain> golden       golden questions + a snapshot a week ago, then a quiet change
                                    to the refund window (14 days -> 30 days) with no source
  add_state.py <brain> week         a snapshot a week ago, then a week of changes: Scale plan
                                    superseded (14,999 -> 15,999) and a new Enterprise add-on price
Standard library only; uses the plugin's own scripts to write the logs and snapshots.
"""
import json
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "my-business-brain", "scripts"))
import brain_diff  # noqa: E402
import impact  # noqa: E402

TODAY = date.today()
WEEK_AGO = TODAY - timedelta(days=7)


def entry(brain, domain, eid, meta, body):
    path = os.path.join(brain, "entries", domain, eid + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items()) + "\n---\n\n" + body + "\n")


def answer_log(brain):
    for days, kind, purpose, who in ((16, "proposal", "Scale plan proposal", "Gulf Retail LLC"),
                                     (8, "quote", "Scale plan quote, 12 months", "Nour Clinics")):
        when = (TODAY - timedelta(days=days)).isoformat() + "T09:00:00Z"
        impact.log_output(brain, ["pricing-scale-plan-monthly", "products-scale-plan"], kind, purpose, who,
                          "external", when)


def golden(brain):
    with open(os.path.join(brain, "_system", "golden-questions.json"), "w", encoding="utf-8") as f:
        json.dump([
            {"id": "g1", "question": "What is our refund window?", "queries": ["refund window", "refund days"],
             "expect_entry": "policies-refund-window", "expect_key": "policy.refund.window-days",
             "expect_value": "14 days", "added": WEEK_AGO.isoformat()},
            {"id": "g2", "question": "How much is the Scale plan?", "queries": ["Scale plan price"],
             "expect_entry": "pricing-scale-plan-monthly", "expect_key": "price.scale-plan.monthly",
             "expect_value": "AED 14,999 per month", "added": WEEK_AGO.isoformat()},
        ], f, indent=1)
    brain_diff.save_snapshot(brain, WEEK_AGO)
    # A bulk import quietly rewrote the refund window: no new source, no changelog line.
    p = os.path.join(brain, "entries", "policies", "policies-refund-window.md")
    with open(p, encoding="utf-8") as f:
        text = f.read()
    with open(p, "w", encoding="utf-8") as f:
        f.write(text.replace("14 days", "30 days"))


def week(brain):
    brain_diff.save_snapshot(brain, WEEK_AGO)
    old = os.path.join(brain, "entries", "pricing", "pricing-scale-plan-monthly.md")
    with open(old, encoding="utf-8") as f:
        text = f.read().replace("status: active", "status: superseded", 1)
    with open(os.path.join(brain, "_system", "archive", "pricing-scale-plan-monthly.md"), "w", encoding="utf-8") as f:
        f.write(text)
    os.remove(old)
    base = {"type": "price", "domain": "pricing", "status": "active", "source": "Price list v4, September 2026",
            "source_type": "internal-document", "recorded_on": (TODAY - timedelta(days=3)).isoformat(),
            "review_by": "2027-03-01", "confidence": "high", "sensitivity": "public"}
    entry(brain, "pricing", "pricing-scale-plan-monthly-v4",
          dict(id="pricing-scale-plan-monthly-v4", title="Scale plan monthly price", key="price.scale-plan.monthly",
               value="AED 15,999 per month", supersedes="[pricing-scale-plan-monthly]", **base),
          "From 1 October 2026 the Scale plan costs AED 15,999 per month, excluding VAT.")
    entry(brain, "pricing", "pricing-call-recording-addon",
          dict(id="pricing-call-recording-addon", title="Call recording add-on price",
               key="price.call-recording-addon.monthly", value="AED 299 per month", **base),
          "The call recording add-on costs AED 299 per month per account, excluding VAT.")


if __name__ == "__main__":
    brain, mode = sys.argv[1], sys.argv[2]
    {"answer-log": answer_log, "golden": golden, "week": week}[mode](brain)
