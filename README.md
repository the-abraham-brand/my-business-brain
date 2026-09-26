# My Business Brain

**By [Abraham](https://theabrahambrand.com)**

A second brain for your business, inside Claude. It remembers what your business knows, keeps it correct as things change, and puts it to work.

## Why it exists

Business knowledge lives in price sheets, contracts, inboxes and people's heads. It drifts: two documents quote different prices, a policy changes but the old one is still in circulation, a notice deadline passes and a contract renews for another year. My Business Brain gathers that knowledge into one local, structured knowledge bank, checks it continuously, and tells you when something needs your decision.

## What it does

| Job | What you get |
|---|---|
| **Remember** | Documents, messages and decisions become one-fact entries, each with a source and a review date |
| **Answer** | Answers about your business, answer first, citing the entries used |
| **Heal** | Finds conflicts, duplicates, overlaps, stale and unsourced entries and broken links; fixes housekeeping itself and brings you each decision with a recommendation and a health score |
| **Vet** | Official information (laws, fees, tax rates, deadlines) checked against the most authoritative, current sources for your jurisdiction before it is stored |
| **Analyse** | Consulting-grade analysis: hypotheses, MECE issue trees, numbers computed in code, answer-first recommendations with impact, owner, timing and risk |
| **Contract Clocks** | Every contract longer than a month gets its end, renewal and notice dates extracted, confirmed with you, and added to Google, Outlook, Apple or any open-source calendar with reminders 7 days, 3 days and 24 hours before |

It learns as you use it: corrections become lessons it applies next time, your preferences are remembered, and questions it could not answer become suggestions for what to document.

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
  _system/  changelog, health report, decisions needed, lessons, preferences, questions, archive/
```

Entries are never deleted: when a fact changes, the new entry supersedes the old one, so the brain can also answer "what did we charge last year?"

Helper scripts (Python 3, standard library only) run the health check, rebuild the index and contract register, calculate contract dates and build calendar files.

## Rules it keeps

- Every fact has a source; every answer cites its entries.
- One truth per fact: contradictions are raised with you, never overwritten silently.
- It proposes; you decide. Only housekeeping is automatic.
- Official information is vetted against authoritative sources, not blogs or summaries.
- It says plainly when it does not know.
- It informs decisions; legal, tax and financial conclusions should be confirmed with a professional.

## Install

In Claude Code:

```
/plugin marketplace add the-abraham-brand/my-business-brain
/plugin install my-business-brain@my-business-brain
```

In the Claude app, add the plugin from the directory or upload the packaged `.plugin` file. The brain works best with a connected folder (so it can keep its files) and a connected calendar (for one-click Contract Clocks).

## Works well with

- [Top-Down Brief](https://github.com/the-abraham-brand/top-down-brief): answer-first official communications.
- [Top-Down Verify](https://github.com/the-abraham-brand/top-down-verify): fact-check any document before it goes out.
- [Top-Down Startup Pitch Deck](https://github.com/the-abraham-brand/top-down-startup-pitch-deck): research-backed investor decks.

## Credits

Created by [Abraham](https://theabrahambrand.com). MIT licence.
