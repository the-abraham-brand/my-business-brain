# My Business Brain

**By [Abraham](https://theabrahambrand.com)**

A second brain for your business, inside Claude. It remembers what your business knows, keeps it correct as things change, and puts it to work.

## Why it exists

Business knowledge lives in price sheets, contracts, inboxes and people's heads. It drifts: two documents quote different prices, a policy changes but the old one is still in circulation, a notice deadline passes and a contract renews for another year. My Business Brain gathers that knowledge into one local, structured knowledge bank, checks it continuously, and tells you when something needs your decision.

## What it does

| Job | What you get |
|---|---|
| **Remember** | Documents, messages and decisions become one-fact entries, each with a source and a review date |
| **Answer** | Answers about your business, answer first. Hybrid search finds the right entries and source-document sections; every cited figure, date and quote is checked against its entry before the answer goes out |
| **Heal** | Finds conflicts, duplicates, overlaps, stale and unsourced entries and broken links; fixes housekeeping itself and brings you each decision with a recommendation and a health score |
| **Vet** | Official information (laws, fees, tax rates, deadlines) checked against the most authoritative, current sources for your jurisdiction before it is stored |
| **Analyse** | Consulting-grade analysis: hypotheses, MECE issue trees, numbers computed in code, answer-first recommendations with impact, owner, timing and risk |
| **Bulk load** | Drop in dozens of documents: parallel readers extract the facts, a merge planner sorts each one into new, refresh, conflict, overlap or duplicate, and only the coordinator writes to the brain |
| **Independent check** | Official rules, conflict recommendations and high-stakes analysis are re-derived by a separate checker that never sees the first answer; any disagreement comes to you |
| **Security** | Every fact carries a sensitivity label (public, internal, confidential). Confidential facts such as salaries, contract values and margins are kept out of anything that leaves the business, and text in documents that tries to instruct an AI is quarantined and reported, never followed |
| **Decide with confidence** | Routine calls (is this worth remembering, which area, how sensitive, does this contract qualify) have fixed options. Clear cases are settled by rules; the rest carry a confidence score: high goes ahead, medium asks you, low goes to a check. Every call is logged, its accuracy measured, and a correction you make three times becomes a rule you can approve |
| **Guard against regression** | The answers your business relies on (headline prices, refund terms, key dates) are replayed at every health check, so a value that changes quietly is caught. Every answer, proposal and quote that leaves the business is logged with the facts it used, so when a price changes you are told which customers received the old one. A weekly digest shows what changed, and facts that keep flip-flopping are flagged |
| **Contract Clocks** | Every contract longer than a month gets its end, renewal and notice dates extracted, confirmed with you, and added to Google, Outlook, Apple or any open-source calendar with reminders 7 days, 3 days and 24 hours before |

It learns as you use it: corrections become lessons it applies next time, your preferences are remembered, and questions it could not answer become suggestions for what to document.

## Settings

When you enable the plugin you can set, once:

| Setting | What it does |
|---|---|
| Brain folder | Where your brain lives, so every conversation finds it |
| Calendar | Google, Outlook, an `.ics` file for Apple and open-source calendars, or ask each time |
| Currency, time zone, weekend days | Used in answers, calendar events and weekend flags on deadlines (Saturday–Sunday or Friday–Saturday) |
| Remembering facts | Ask before remembering what you mention, or remember automatically |
| Session brief | At the start of each session, Claude hears what is waiting and which deadlines are near |
| Auto-apply and ask-me confidence | How sure Claude must be to go ahead on a routine call (default 0.9), and below which it sends the call for checking rather than asking you (default 0.6) |

Change them any time in the plugin's settings (`/config` in Claude Code).

## Built-in agents and automatic checks

- **`brain-reader`**: reads documents in bulk loads. It can only read, so a poisoned document cannot make it write, run commands or go online.
- **`brain-checker`**: re-checks official rules, figures and high-stakes conclusions without seeing the first answer.
- **Session brief** (Claude Code and Cowork): decisions waiting, contract deadlines in the next weeks, and the brain's health, at the start of each session.
- **Quick check after every entry change** (Claude Code and Cowork): the index is rebuilt and any conflict or suspicious text in that entry is raised straight away.

On claude.ai, where plugin hooks don't run, the skills do the same checks by instruction.

## Commands

| Command | Use it to |
|---|---|
| `/my-business-brain:setup` | Create the brain in a folder you choose |
| `/my-business-brain:learn` | Add documents or facts |
| `/my-business-brain:ask` | Ask a question about your business |
| `/my-business-brain:heal` | Run a full health check |
| `/my-business-brain:analyze` | Get an analysis and recommendation |
| `/my-business-brain:contract-clocks` | Put a contract's key dates on your calendar |

You rarely need the commands: the core skill switches on whenever you share business information or ask about your business, and Contract Clocks is offered whenever you share a contract.

## How the brain is stored

Plain Markdown files in a folder you own. Nothing is sent anywhere you have not asked for.

```
business-brain/
  BRAIN.md  INDEX.md
  entries/<domain>/<id>.md
  contracts/register.md  contracts/calendar/*.ics
  analytics/
  _system/  changelog, health report, decisions needed, lessons, preferences, questions, archive/,
           decision log, rules, golden questions, answer log, snapshots/, digests/
```

Entries are never deleted: when a fact changes, the new entry supersedes the old one, so the brain can also answer "what did we charge last year?"

Helper scripts (Python 3, standard library only, nothing to install) search the brain, check citations, plan bulk loads, run the health check, rebuild the index and contract register, calculate contract dates and build calendar files. Search and the health check stay well under a second on a brain of 2,500 entries.

## Rules it keeps

- Every fact has a source; every answer cites its entries, and every citation is verified.
- Confidential facts never leave the business; documents are data, never instructions.
- One truth per fact: contradictions are raised with you, never overwritten silently.
- It proposes; you decide. Only housekeeping is automatic, and every action sits on a clear escalation ladder: do, propose, must ask, stop and advise.
- Official information is vetted against authoritative sources, not blogs or summaries.
- Routine calls are bounded: a fixed list of options, rules first, and a confidence it must earn. A valid choice can still be wrong, so accuracy is measured and the bar rises when it slips.
- It says plainly when it does not know.
- It informs decisions; legal, tax and financial conclusions should be confirmed with a professional.

## Tested

- `tests/`: 35 unit tests of the scripts and hooks, run on Linux, macOS and Windows on every commit.
- `evals/`: 14 behaviour tests run with `claude plugin eval`, each with and without the plugin, on a fictional company's brain:
  - **5 contribution tests** measure what the plugin adds. In the first run (one run per arm, 26 September 2026) all three passed with the plugin. Without it, Claude gave no health score and missed planted problems, produced a calendar file with no reminders, and did not rebuild the index after a price change. Scores with / without: health check 1.0 / 0, calendar reminders 1.0 / 0.33, price change 1.0 / 0.75. Two more were added with decision gates and regression guards: after a price change the plugin named the proposal and the quote that had used the old price (1.0 / 0 without it), and it reported the week's changes completely (1.0 / 0.67).
  - **9 guard tests** make sure the essentials never regress: correct cited answers, conflicts raised instead of overwritten, wrong figures caught, notice deadlines, confidential data kept out of outgoing email, injected instructions refused, honesty when the brain doesn't know, history from the archive, and a key answer that changed quietly being caught at the health check. All passed.

See [RELEASING.md](RELEASING.md) for how releases are checked and tagged.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Install

In Claude Code:

```
/plugin marketplace add the-abraham-brand/my-business-brain
/plugin install my-business-brain@my-business-brain
```

Requires Claude Code 2.1.271 or later (for the settings pickers). In the Claude app, add the plugin from the directory or upload the packaged `.plugin` file. The brain works best with a connected folder (so it can keep its files) and a connected calendar (for one-click Contract Clocks).

## Works well with

- [Top-Down Brief](https://github.com/the-abraham-brand/top-down-brief): answer-first official communications.
- [Top-Down Verify](https://github.com/the-abraham-brand/top-down-verify): fact-check any document before it goes out.
- [Top-Down Startup Pitch Deck](https://github.com/the-abraham-brand/top-down-startup-pitch-deck): research-backed investor decks.

## Credits

Created by [Abraham](https://theabrahambrand.com). MIT licence.
