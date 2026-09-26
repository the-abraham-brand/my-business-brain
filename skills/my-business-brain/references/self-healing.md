# Self-healing

The brain is only a support pillar if the user can trust it. Self-healing keeps it true, consistent and current without the user having to police it.

## When it runs

- **Quick check** after every session that changed the brain: only the entries touched and their neighbours.
- **Full check** on request (`/my-business-brain:heal`) and on a schedule. Offer the user a weekly scheduled task for the full check; set it up only if they agree.

Run `scripts/brain_health.py <brain-folder>` where code execution is available. It produces `_system/health-report.md` (with a score history) and `_system/health-issues.json`. Pass `--today YYYY-MM-DD` to check as of another date. Then run `scripts/brain_index.py <brain-folder>` to rebuild the index and contract register. Then apply the judgment steps below. Where scripts cannot run, perform the same checks by reading the entries.

## What it detects

| Issue | How it is detected | Severity |
|---|---|---|
| **Conflict** | Two active entries with the same `key` but different `value`; or statements in two entries that cannot both be true (e.g. refund window 14 days vs 30 days) | High |
| **Duplicate** | Same `key` and same value, or near-identical titles and content | Medium |
| **Overlap** | Different entries covering substantially the same ground (high content similarity) | Low–Medium |
| **Stale** | `review_by` date has passed | Medium (High for prices, official rules, contracts) |
| **Unsourced** | Missing `source`, or `source_type` external-verified without `verified_on` | Medium |
| **Low confidence** | `confidence: low` older than 30 days | Low |
| **Broken link** | `[[id]]` or `related` pointing to an id that does not exist | Low |
| **Orphan** | Active entry with no links to or from anything, in a domain where links are expected | Low |
| **Supersede chain error** | Superseded entry still marked active, or an active entry superseded by two different entries | Medium |
| **Contract deadline approaching** | A notice deadline within 30 days and no `decision` recorded on the contract entry | High |
| **Contract date passed** | A contract's notice deadline or end date has passed without an update | High |
| **Schema error** | Missing required fields, invalid dates, id not matching file name | Low |

## How it heals

**Automatic (no confirmation needed)**, because they don't change what the business knows:
- Rebuild `INDEX.md` and `contracts/register.md`.
- Fix formatting, field order, id/file name mismatches, and links whose target was renamed.
- Move entries already marked superseded into `_system/archive/`.

**Proposed, then applied on confirmation**, because they change the knowledge:
- **Conflicts**: show both entries side by side (value, source, date, confidence) and recommend which is likely current, with the reason (newer document, higher confidence, verified source). The user chooses; the loser is superseded, and the reason is logged. If the conflict involves official information, vet it first and show the finding.
- **Duplicates and overlaps**: propose a merged entry (keeping every source) or links between them.
- **Stale entries**: ask the user to confirm the value is still correct, or re-vet official information automatically and propose any update.
- **Unsourced / low confidence**: ask for the source or confirmation; offer to downgrade confidence if none exists.
- **Passed contract dates**: ask whether the contract was renewed, renegotiated or ended, and update accordingly.

Put every open item in `_system/decisions-needed.md`, newest first, and keep it short enough to act on: group similar items, and lead with High severity.

## Reporting

After a full check, give the user:

1. **Health score**: "Brain health: 92/100", with the method: start at 100, subtract 5 per open High issue, 2 per Medium, 0.5 per Low, floor 0.
2. **Fixed automatically**: one line with counts.
3. **Needs your decision**: the High and Medium items, each with a recommended resolution and a one-word answer the user can give ("Keep A", "Keep B", "Merge", "Still correct").
4. **Trend**: score versus the previous check, from `_system/health-report.md` history.

Record every resolution in `_system/changelog.md`, and every repeated type of mistake as a lesson in `_system/lessons.md` (see `adaptive-learning.md`).
