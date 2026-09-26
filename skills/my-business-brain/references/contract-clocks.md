# Contract Clocks

Every contract with a term longer than one month gets its key dates extracted, verified and put on the user's calendar with reminders 7 days, 3 days and 24 hours before each date, so no renewal, notice deadline or expiry is ever missed. It works in any chat where the plugin is installed: whenever a contract or agreement is shared, offer Contract Clocks.

## 1. Qualify the contract

- Identify the document as a contract or agreement (service agreement, lease, subscription, supply, employment, NDA with a term, SLA, licence, loan, insurance policy, tenancy).
- Determine the term: start date and end date, or start date plus duration. Include contracts that renew automatically even if each period is short, when the total commitment runs beyond one month.
- **Term longer than one month** → continue. One month or shorter, or no dates at all → tell the user briefly and stop (offer to store the contract in the brain anyway).

## 2. Extract the dates and terms

Capture, with the clause reference and the exact wording for each:

| Item | Notes |
|---|---|
| Parties | Legal names |
| Effective / start date | |
| End / expiry date | Or start + term |
| Auto-renewal | Yes/no, renewal period, how many times |
| Notice period to terminate or not renew | Length, calendar vs business days, form of notice (written, email, registered post), who to notify |
| **Notice deadline** | Calculated: end or renewal date minus notice period |
| Break / early-termination options | Dates and conditions |
| Price reviews, escalations, rate changes | Dates and formula |
| Payment schedule | First payment, frequency, due dates if fixed |
| Milestones and obligations with dates | Deliverables, audits, reports, insurance renewals |
| Warranty or guarantee expiry | |
| Governing law and dispute clause | For the record |

Compute every derived date with `scripts/contract_dates.py` (or careful date arithmetic): months are calendar months; "30 days" means calendar days unless the contract says business days; if the deadline falls on a weekend or public holiday and the contract doesn't say otherwise, flag it and suggest acting on the previous working day.

## 3. Verify before anything goes on a calendar

Show the user a short table: each date, what it is, the clause, and how it was calculated. Flag anything ambiguous (missing year, conflicting clauses, "within 30 days of" without an anchor, time zone). Ask the user to confirm or correct. Never add unconfirmed dates.

The **notice deadline** is the most important date: it is when the user loses the choice to exit or renegotiate. Make it stand out.

## 4. Add to the calendar

Ask once which calendar the user prefers, store the answer in `_system/preferences.md`, and use it from then on.

**Reminders for every event: 7 days, 3 days and 24 hours before.**

| Calendar | How |
|---|---|
| **Google Calendar** (connector available) | Create each event through the connector with custom popup reminders at 10,080, 4,320 and 1,440 minutes before, plus an email reminder at 10,080 minutes if the user wants it |
| **Microsoft Outlook / 365** (connector available) | Outlook events hold one reminder each: create the main event with a 24-hour reminder, plus two short reminder events 7 days and 3 days before, each linking to the main one; or use the calendar file below |
| **Apple Calendar, Thunderbird, Nextcloud, Proton, any CalDAV or open-source calendar** | Generate an `.ics` file with `scripts/make_ics.py` (three alarms per event), deliver it, and tell the user to open it to import. Google and Outlook can import it too |
| **No calendar connected** | Offer the `.ics` file, and suggest connecting their calendar in Claude for one-click adds next time |

Event format:

- **Title**: `⏰ [Notice deadline] Supplier X service agreement` (use the date type in brackets: Notice deadline, Renewal, Expiry, Price review, Payment due, Milestone).
- **Time**: 09:00 in the user's time zone on the date (or the time the contract states).
- **Description**: what happens on this date, what the user must do (e.g. "Send written notice to legal@supplierx.example to stop auto-renewal"), the clause reference, and the brain entry id.

Before creating events through a connector, show the list and get a clear yes. Creating calendar events is an action on the user's account.

## 5. Record in the brain

- One `contract` entry per contract in `entries/contracts/` with all extracted terms, dates, clause references, and `review_by` set to the notice deadline.
  Add these front-matter fields so the scripts can track it: `counterparty`, `value` (contract value), `start_date`, `end_date`, `notice_deadline`, `auto_renewal` (e.g. `yes, 12 months` or `no`), `calendar` (where and when the events were added, e.g. `google (added 2026-09-26)`), and `decision` once the user decides to renew, renegotiate or exit.
- Regenerate `contracts/register.md` with `scripts/brain_index.py`: every active contract, counterparty, value, end date, notice deadline, days remaining, auto-renewal and calendar status, soonest first.
- Save the `.ics` file in `contracts/calendar/`.
- When a contract is renewed, renegotiated or terminated, supersede the entry and update the calendar.

## 6. Keep watch

The health check flags notice deadlines within 30 days that have no recorded decision, and any contract whose dates have passed without an update. In the monthly brain review, list the next 90 days of contract dates.

The brain extracts and tracks dates; it does not interpret the contract's legal effect. For disputes or unclear terms, recommend the user confirm with a lawyer.
