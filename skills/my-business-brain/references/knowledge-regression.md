# Knowledge regression and impact

A brain can get worse quietly. A bulk load files a wrong value, a merge drops an entry, or a correction changes a price that proposals already quoted. Three tools catch this, and none of them calls a model.

## 1. Golden questions: the answers the business relies on

`_system/golden-questions.json` lists the questions that must keep giving the same answer, each with its expected entry and value.

- **Build the list.**
  - During setup and each monthly review, run `golden.py propose <brain>`. It suggests the entries cited most often in logged answers.
  - Also offer the obvious ones: headline prices, refund and payment terms, key contract dates, VAT rate.
  - Add the ones the user agrees to: `golden.py add <brain> --q "What is our refund window?" --q "refund days" --expect-entry policies-refund-window`.
- **Check them.** Every full health check replays them through the brain's search. A different answer, a different entry, or an answer search can no longer find becomes a High **knowledge regression**.
- **Resolve it with the user.**
  - If the change was intended (a new price list), run `golden.py accept <brain> --id g2` to make the current answer the new baseline.
  - If it wasn't, restore the right fact by superseding the wrong entry. Never quietly edit the golden file to make a warning go away.

## 2. Answer log and impact alerts: what did we tell whom?

- **Log what goes out.** When an answer, email, proposal, quote, report or post passes the citation check, log it:

  `cite_check.py <brain> <draft> --audience external --log "Scale plan proposal" --kind proposal --recipient "Gulf Retail LLC"`

  The log (`_system/answer-log.jsonl`) records the entries and values the output relied on. Log everything that leaves the business. For internal answers, log those the user acts on.
- **Report what changed.** When a fact changes, `impact.py <brain>` (also part of every health check) lists every logged output that used the old value, grouped by fact. For example: "2 past outputs used Scale plan monthly price = AED 14,999 (now AED 15,999): proposal to Gulf Retail LLC (2026-09-10); quote to Nour Clinics (2026-09-18)."
- **Act on it.** After any change to a price, policy, contract term or date, tell the user which outputs are affected. Offer to draft corrections or follow-ups, checked with the citation check and logged. When they have dealt with it, run `impact.py <brain> --ack <old entry id>`.

## 3. Snapshots and the weekly diff

- The health check saves one snapshot a day in `_system/snapshots/`.
- `brain_diff.py diff <brain>` shows what changed since the snapshot from a week ago (or `--since <date>`): added, changed, superseded or archived, relabelled, and anything removed from the folder, which should never happen. With `--write` it saves the digest to `_system/digests/`.
- **Unstable facts** are those whose value keeps changing, or changes and then changes back. They are flagged because they usually mean two sources disagree. Find the authoritative source, record it, and consider making it a golden question.

Include the weekly diff and the list of unacknowledged impacts in the weekly health check and the monthly brain review.
