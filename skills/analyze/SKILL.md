---
name: analyze
description: My Business Brain analysis. Runs consulting-grade business analysis on the user's own data: frames the decision, builds hypotheses and a MECE issue tree, computes with code, finds the 80/20, and delivers an answer-first recommendation with impact, owner, timing and risk. Covers health checks, revenue bridges, customer concentration, unit economics, retention, pricing, cost and break-even, cash, funnel, root cause, opportunity sizing, scenarios and competitive position. Use when the user runs /my-business-brain:analyze, or asks how the business is doing, why a number changed, what to do about something, or for a strategic recommendation.
---

# /my-business-brain:analyze

Analyse the business like a top-tier strategy consultant, from the business's own data.

1. Load the `my-business-brain` skill from this plugin (via the Skill tool). If it cannot be loaded, read `../my-business-brain/SKILL.md` and `../my-business-brain/references/analytics-playbook.md` directly.
2. Frame the decision in one sentence. With a vague request, run the Business Health Check.
3. State hypotheses and the issue tree; pick the modules from the analysis library.
4. Gather data from the brain first (search with `scripts/brain_search.py`), then the user's files; ask for anything missing in one batch. Vet any external benchmark. For outside research, use what the research toolkit lists (`scripts/toolkit.py <brain> show`: a research skill, Agent Reach, connectors) and install nothing. Customer and market chatter from social sources is sentiment: report it as such (`scripts/signals.py`), never as a finding's evidence.
5. Compute with code, reconcile totals, and find the 80/20.
6. Deliver answer first: conclusion, 2–4 findings with action titles, exhibits, recommendations (impact, effort, owner, timing, risk), assumptions and gaps, next steps. Offer it as a document and, when the data will be reused, a spreadsheet.
7. For a recommendation that changes pricing, spend, headcount or a contract, have the `brain-checker` agent re-derive the key numbers and conclusion without seeing yours (`references/orchestration.md`); show the user any disagreement.
8. Save to `analytics/<date>-<topic>.md`, store new metrics and decisions as entries, and log follow-up dates.
