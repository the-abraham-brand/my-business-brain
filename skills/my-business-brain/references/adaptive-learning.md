# Adaptive learning

The brain gets better the more it is used. It learns from corrections, preferences and questions, and it tells the user what it has learned so nothing changes silently. Everything it learns is stored as plain text in the brain folder, where the user can read, edit or delete it.

## 1. Learn from corrections → `_system/lessons.md`

Whenever the user corrects an answer, an entry, an extraction or an analysis:

1. Fix the item (and supersede the entry if the fact changed).
2. Record a lesson: date, what went wrong, the rule to apply next time, and where it applies.

```markdown
## 2026-09-26: Prices are quoted excluding VAT
- What happened: I reported the Growth plan as AED 14,999 including VAT.
- Rule: All prices in this business are stated excluding VAT unless the entry says otherwise.
- Applies to: pricing, proposals, analytics.
```

3. Before answering or writing in an area, read the lessons that apply to it.
4. If the same kind of mistake happens twice, strengthen the rule and add a check to the health report.

## 2. Learn preferences → `_system/preferences.md`

Record how the user likes to work, when they state it or show it consistently:

- Answer style (length, format, tables vs prose), currency and units, date format, fiscal year.
- Terminology: the business's own words for things (add them to the `glossary` domain).
- Capture mode: ask before remembering, or remember business facts automatically.
- Preferred calendar for Contract Clocks, and reminder preferences.
- Recurring reports and the day they want them.

Confirm a new preference once ("I'll quote prices excluding VAT from now on"), then apply it.

## 3. Learn from questions → `_system/questions.md`

Log each business question: date, question, answered from the brain (yes/partly/no), entries used.

Use the log to:

- **Spot knowledge gaps**: a question asked two or more times that the brain couldn't answer → suggest documenting it ("You've asked about supplier lead times three times; want to add them?").
- **Prioritise freshness**: entries used often get checked first when their review date nears.
- **Suggest structure**: recurring topics without a domain → propose one.

## 4. Calibrate confidence

- Entries confirmed by the user or re-verified move up in confidence; entries the user corrected, or that caused a conflict, move down until reconfirmed.
- When answering from medium or low confidence entries, say so.

## 5. Brain review (monthly, or on request)

Offer a short review, as a scheduled task if the user wants it:

- What the brain learned this month (new entries, lessons, preferences).
- Health score trend.
- Top knowledge gaps and the questions behind them.
- Entries due for review in the next 30 days.
- Upcoming contract dates.
- One recommended improvement to how the business captures knowledge.

## Boundaries

- Learn only about the business and how the user wants to work. Do not build profiles of third parties beyond the business facts needed (a supplier's contact and terms, not their personal life).
- Everything learned is visible and editable in the brain folder; nothing is hidden.
- If the user says "forget X", archive the relevant entries and lessons and confirm.
