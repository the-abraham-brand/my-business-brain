# Knowledge model

## Folder layout

```
business-brain/
  BRAIN.md                 business profile, how the brain is organised, owner
  INDEX.md                 generated: every active entry grouped by domain
  entries/
    <domain>/<id>.md       one entry per fact, policy, product, person, decision…
  contracts/
    register.md            generated: all contracts and their key dates
    calendar/<id>.ics      calendar files created by Contract Clocks
  analytics/
    <yyyy-mm-dd>-<topic>.md  saved analyses and recommendations
  sources/                 source documents the user wants kept, with a .md or .txt copy
                           of each so they can be searched and cited to the line
  _system/
    changelog.md           every add, update, supersede, archive: `- YYYY-MM-DD what and why [[id]]`
    health-report.md       latest health check
    decisions-needed.md    conflicts and questions waiting for the user
    lessons.md             adaptive learning: corrections and how to apply them
    preferences.md         how the user likes answers, terms, formats
    questions.md           questions asked, answered or not (for gap analysis)
    archive/               superseded or retired entries, never deleted
    integrity.json         fingerprints of every entry and source, to catch edits outside the brain
    unsaved-facts.md       facts mentioned in conversation but never saved (end-of-session sweep)
    resume.json            the resume card of an unfinished long job
    pack.json, pack-questions.md   the industry pack applied and its starting questions
    briefings/  journal/   topic briefings, onboarding packs and monthly journals
    dashboard.html         the one-page dashboard
    snapshots/  digests/   daily snapshots and weekly change digests
```

Domains (folders under `entries/`) start with: `company`, `products`, `pricing`, `customers`, `suppliers`, `people`, `policies`, `procedures`, `contracts`, `finance`, `metrics`, `marketing`, `sales`, `operations`, `legal-regulatory`, `decisions`, `glossary`. Add a domain only when an entry does not fit any existing one, and record it in `BRAIN.md`.

## Entry format

Each entry is a Markdown file with a front-matter header. Keep one fact, rule or record per entry so it can be updated, verified and cited on its own.

```markdown
---
id: pricing-growth-plan-monthly
title: Growth plan monthly price
type: price
domain: pricing
key: price.growth-plan.monthly
value: AED 14,999 per month
status: active
source: Pricing sheet v3, August 2026
source_type: internal-document
recorded_on: 2026-09-26
verified_on: 2026-09-26
review_by: 2027-03-26
owner: Abraham
confidence: high
sensitivity: public
supersedes: [pricing-growth-plan-monthly-2025]
related: [products-growth-plan, pricing-overage-rates]
tags: [pricing, plans]
---

The Growth plan is AED 14,999 per month and includes 5,000 minutes.

Overage beyond the included minutes is billed per [[pricing-overage-rates]].
```

### Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique, lowercase, hyphenated, in English letters (also for Arabic entries); also the file name |
| `title` | yes | Plain-language name, in the language of the source (an Arabic title may be followed by an English one) |
| `type` | yes | One of: fact, price, product, customer, supplier, person, policy, procedure, contract, decision, metric, goal, glossary, reference, lesson |
| `domain` | yes | Folder it lives in |
| `key` | for facts with a single value | Canonical identifier of *what* is being stated (e.g. `price.growth-plan.monthly`, `policy.refund.window-days`). Two active entries with the same key are a conflict or a duplicate |
| `value` | with `key` | The value in one line, with units and currency |
| `status` | yes | active, draft, disputed, superseded, archived |
| `source` | yes | Document name and version, person and date, or URL |
| `source_type` | yes | internal-document, user-stated, external-verified, calculated |
| `recorded_on` | yes | Date added |
| `verified_on` | for external-verified | Date the external source was last checked |
| `review_by` | yes | When to recheck. Defaults: prices, rates and official rules 6 months; policies and procedures 12 months; people and contacts 12 months; contracts on their own dates; decisions none (use `9999-12-31`) |
| `owner` | recommended | Who can confirm it |
| `confidence` | yes | high (documented or verified), medium (stated by the user without a document), low (inferred, needs confirmation) |
| `sensitivity` | yes | public, internal or confidential: where the fact may go (see `security-and-privacy.md`). Missing means `confidential` for people, contracts and finance, otherwise `internal` |
| `supersedes` | optional | ids this entry replaces |
| `related` | optional | ids of connected entries; also link inline as `[[id]]` |
| `tags` | optional | free labels |
| Contract fields | for `type: contract` | `counterparty`, `start_date`, `end_date`, `notice_deadline`, `auto_renewal`, `calendar`, `decision` (see `contract-clocks.md`) |

## Remembering (ingest)

1. **Read the material** and split it into atomic items: one fact, rule, price, person, commitment or decision per item.
2. **Classify** each item: type, domain, and a canonical `key` where it has a single value.
3. **Check the brain before writing**, for each item:
   - Same `key` exists, same value → no new entry; refresh `verified_on` or `source` if the new material is newer.
   - Same `key`, different value → **conflict**: do not overwrite. Add to `_system/decisions-needed.md` and ask the user (see `self-healing.md`).
   - **Exception: the owner confirms a change.** When the owner (not a document) states a new value and confirms it ("price list v4 is confirmed"), it is an **update**, not a conflict: supersede the old entry straight away and log it. An older document saying otherwise doesn't reopen the question; mention it, and flag it if it's suspicious.
   - No `key` match, but a similar title or overlapping content → **possible overlap**: propose merging or linking.
   - Nothing similar → new entry.
4. **Vet** any official information before storing it (see `trusted-sources.md`).
5. **Write** new and updated entries, link related ones with `[[id]]`, record everything in `_system/changelog.md`.
6. **Contracts**: also run Contract Clocks.
7. **Report back** in a short list: added, updated, needs a decision.

For many documents at once, use the bulk-load flow in `orchestration.md` (parallel readers, `scripts/ingest_plan.py` to merge and classify, coordinator writes).

Capture from conversation too: when the user states a business fact, decision or preference in passing ("we don't do refunds after 14 days"), offer to remember it, or remember it directly if the user has asked the brain to capture automatically (recorded in `_system/preferences.md`).

## Changing and retiring entries

- **Update** in place only for corrections of form (typos, formatting) or refreshed verification dates.
- **Supersede** when the fact changes (new price, new policy): create a new entry with `supersedes: [old-id]`, set the old one to `status: superseded`, and move it to `_system/archive/`. History is kept, so the brain can answer "what did we charge last year?"
- **Archive** entries that no longer apply, with a reason in the changelog.
- **Never delete** entries.

## INDEX.md

Regenerate after every change (`scripts/brain_index.py`): active entries grouped by domain, each with title, value (if any), review date, and file link; followed by counts per domain and the number of open decisions.
