# My Business Brain

**By [Abraham](https://theabrahambrand.com)**

**My Business Brain gives your business one memory it can trust. It keeps what your company knows in one place, keeps it right as things change, and puts it to work in English and Arabic. Every answer, proposal and deadline can be traced back to where it came from.**

Most businesses keep their knowledge in price sheets, contracts, inboxes and a few people's heads. Over time it drifts. Two documents quote different prices. A policy changes, but the old version is still being sent to customers. A notice deadline slips past and a contract you meant to cancel renews for another year.

My Business Brain lives inside Claude and deals with this in four ways.

## 1. It remembers what your business knows, in English or Arabic

- Share a document, a message or a decision and it becomes a set of short entries, one fact each. Every entry says where it came from, when to check it again, and who is allowed to see it.
- Drop in a folder of documents and it reads them in parallel. Each fact is sorted as new, an update, a duplicate, or something that clashes with what the brain already knows. Nothing is written until that's done.
- Mention something in passing ("we've moved the Scale plan to AED 15,999") and it offers to remember it, or just remembers it if you prefer.
- Everything is plain text in a folder you own. Nothing goes anywhere you haven't asked it to.

## 2. It keeps that knowledge right as the business changes

- A regular health check finds clashing facts, duplicates, stale entries and missing sources. It tidies up on its own and brings you the real decisions, each with a recommendation and a health score.
- When a fact changes, the old one is kept as history rather than overwritten, so you can still ask "what did we charge last year?"
- The answers you rely on most, like headline prices, refund terms and key dates, are re-checked every time. If one changes quietly, you hear about it.
- It keeps a log of every answer, proposal and quote that goes out and the facts each one used. When a price changes, it tells you which customers were sent the old one.
- A weekly summary shows what changed, and it flags facts that keep flipping back and forth.
- Laws, fees, tax rates and official deadlines are checked against the most authoritative current sources before they're stored. For anything important, a second, independent checker works it out again without seeing the first answer.

## 3. It puts that knowledge to work

- Ask it anything about your business and you get the answer first, with its sources. Every figure, date and quote is checked against the brain before you see it. If the brain doesn't know, it says so.
- Ask for an analysis and you get what a good consultant would give you. That means a clear recommendation up front, the numbers worked out properly, and the impact, owner, timing and risks spelled out.
- Share a contract and it pulls out the end, renewal and notice dates, confirms them with you, and puts them in Google, Outlook, Apple or any other calendar. You get reminders 7 days, 3 days and 24 hours before each date.
- At the start of each session it gives Claude a short brief: what's waiting for you and which deadlines are close.

## 4. It stays safe and accountable

- Every fact is marked public, internal or confidential. Salaries, contract values, margins and bank details never end up in anything that leaves the business.
- Documents can't give it orders. If a file contains hidden text trying to instruct an AI, that text is set aside and shown to you, never followed.
- The small calls it makes all day, like which area a fact belongs to or how urgent something is, have fixed answers to choose from. Clear cases are settled by simple rules. For the rest, it tracks how often it gets them right and adjusts how sure it lets itself be. When it's confident it goes ahead, when it's unsure it asks you, and when it's guessing it gets a second opinion. Correct it the same way three times and it suggests a rule you can approve.
- It proposes and you decide. Only housekeeping happens automatically. Anything that changes what the business knows is checked with you first.

## Arabic, built in

If you do business in the Gulf or anywhere Arabic is spoken, Arabic isn't an afterthought. It's handled all the way through.

| Where | What it does |
|---|---|
| Conversation | Replies in whichever language you write in, and stores each fact in the language it came in |
| Search | Reads Arabic entries and documents, and copes with spelling variations (أ, إ and آ, or ة and ه) and attached words like the article, so استرداد finds الاسترداد |
| Figures and dates | Understands Arabic-Indic numbers (٣٢٬٠٠٠ is 32,000) and Arabic month names (١ أكتوبر ٢٠٢٦), so it catches a wrong figure in an Arabic draft and doesn't mistake the same price in different numerals for a clash |
| Confidentiality | Recognises salaries, IBANs, account numbers, passports, Emirates IDs, profit margins, passwords and commission in Arabic, and keeps them confidential |
| Security | Spots instructions hidden in Arabic documents, like تجاهل التعليمات السابقة ("ignore previous instructions") or لا تخبر المستخدم ("don't tell the user") |
| Judgement | Asks you before acting on Arabic text until it has proven itself on Arabic, because rules and confidence learned in English don't automatically carry over |

It also gets better as you use it. Corrections become lessons, your preferences stick, and questions it couldn't answer become suggestions for what to write down next.

**Getting started:** install the plugin (see [Install](#install)), run `/my-business-brain:setup`, and pick the folder where your brain should live.

## Settings

You set these once when you enable the plugin, and can change them any time (`/config` in Claude Code).

| Setting | What it's for |
|---|---|
| Brain folder | Where your brain lives, so every conversation can find it |
| Calendar | Google, Outlook, an `.ics` file for Apple and open-source calendars, or ask each time |
| Currency, time zone, weekend | Used in answers, calendar events and weekend warnings on deadlines (Saturday–Sunday or Friday–Saturday) |
| Remembering facts | Ask before remembering things you mention, or remember them automatically |
| Session brief | Whether Claude hears what's waiting and which deadlines are near at the start of each session |
| Auto-apply and ask-me confidence | How sure it must be before going ahead on a routine call (default 0.9), and below which it gets a second opinion instead of asking you (default 0.6). These are compared with its measured track record, not just its own say-so |

## Commands

| Command | What it does |
|---|---|
| `/my-business-brain:setup` | Creates the brain in a folder you choose |
| `/my-business-brain:learn` | Adds documents or facts |
| `/my-business-brain:ask` | Answers a question about your business |
| `/my-business-brain:heal` | Runs a full health check |
| `/my-business-brain:analyze` | Gives you an analysis and a recommendation |
| `/my-business-brain:contract-clocks` | Puts a contract's key dates on your calendar |

You'll rarely need them. The brain switches on by itself when you share business information or ask about your business, and it offers Contract Clocks whenever you share a contract.

## What's under the hood

- **Two helper agents.** `brain-reader` reads documents during bulk loads and can only read, so a booby-trapped file can't make it write, run commands or go online. `brain-checker` double-checks official rules, figures and big conclusions without seeing the first answer.
- **Automatic checks** in Claude Code and Cowork: a brief at the start of each session, and a quick check every time an entry changes. On claude.ai, where plugins can't run these hooks, the skills do the same checks themselves.
- **Plain files.** The brain is a folder of Markdown files:

  ```
  business-brain/
    BRAIN.md  INDEX.md
    entries/<area>/<fact>.md
    contracts/register.md  contracts/calendar/*.ics
    analytics/
    _system/  changelog, health report, decisions waiting, lessons, preferences, questions,
             archive/, decision log, rules, key questions, answer log, snapshots/, weekly digests/
  ```

- **No installs.** The helper scripts use plain Python 3 with nothing extra. Search and the health check take well under a second, even with 2,500 entries.

## The rules it lives by

- Every fact has a source, and every answer shows its sources after checking them.
- Confidential facts stay inside the business. Documents are information, never instructions.
- There is one truth per fact. When two sources disagree, you're asked; nothing is quietly overwritten.
- It proposes, you decide.
- Official information comes from official sources, not blogs or summaries.
- It earns its confidence, and it measures whether it deserved it.
- It says so when it doesn't know.
- It helps you decide. For legal, tax and financial conclusions, check with a professional.

## How it's tested

- **43 unit tests** of the scripts and hooks, run on Linux, macOS and Windows with every change.
- **15 behaviour tests**, each run with and without the plugin on a made-up company's brain.
  - **5 show what the plugin adds.** With it, all five passed. Without it, Claude:
    - gave no health score and missed the problems planted for it;
    - made a calendar file with no reminders;
    - didn't rebuild the index after a price change;
    - couldn't say which customers had been quoted an old price;
    - missed part of the week's changes.
  - **10 make sure the basics never slip:**
    - answers cite the right facts;
    - clashes are raised, not overwritten;
    - wrong figures in a draft are caught;
    - notice deadlines are worked out correctly;
    - confidential details stay out of emails;
    - hidden instructions are refused;
    - it admits when it doesn't know;
    - past prices come from the archive;
    - a quietly changed answer is spotted;
    - pay details in an Arabic HR note stay out of a public post.

    All passed.

See [RELEASING.md](RELEASING.md) for how releases are checked, and [CHANGELOG.md](CHANGELOG.md) for what changed in each version.

## Install

In Claude Code:

```
/plugin marketplace add the-abraham-brand/my-business-brain
/plugin install my-business-brain@my-business-brain
```

You'll need Claude Code 2.1.271 or later for the settings menus. In the Claude app, add it from the plugin directory or upload the `.plugin` file from the [latest release](https://github.com/the-abraham-brand/my-business-brain/releases/latest). It works best with a connected folder, so it can keep its files, and a connected calendar, for one-click Contract Clocks.

## Works well with

All by [Abraham](https://theabrahambrand.com), and made to work together:

- [Top-Down Brief](https://github.com/the-abraham-brand/top-down-brief) turns your brain's facts into clear, answer-first emails, memos and reports.
- [Top-Down Verify](https://github.com/the-abraham-brand/top-down-verify) fact-checks any document before it goes out.
- [Top-Down Startup Pitch Deck](https://github.com/the-abraham-brand/top-down-startup-pitch-deck) builds a research-backed investor deck from what your business knows.

## Credits

Made by [Abraham](https://theabrahambrand.com). MIT licence.
