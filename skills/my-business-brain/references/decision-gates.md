# Decision gates

Not every question needs a paragraph. The brain makes the same small decisions over and over, and each one needs a decision, not an essay. Treat each as a **typed decision**: a fixed question, a bounded answer, a confidence and the evidence. Use `scripts/decide.py` so every decision is checked, routed and logged, and so the brain learns how reliable it is.

## Three kinds of decision

| Kind | The answer | Example |
|---|---|---|
| **choice** | One option from a fixed set, each option with a one-line description. Answer with a probability per option (`scores`), or a choice and a confidence | Which domain does this belong to? |
| **score** | A level on an ordered rubric (0 to N). Answer with a probability per level (`dist`); the script reports the expected level | How urgent is this? |
| **noul** | Yes or no, answered with the probability that it is yes (`p`) | Is this official information that must be vetted? |

## Built-in decision types

| Type | Kind | Answers | Rule that can settle it |
|---|---|---|---|
| `capture` | choice | remember, skip | none: judge it |
| `domain` | choice | the brain's domains | key prefix (`price.` → pricing, `tax.` → legal-regulatory, …) |
| `sensitivity` | choice | public, internal, confidential | salary, IBAN, passport, margin and similar, in English or Arabic; people, contracts and finance entries |
| `document_safety` | choice | safe, suspicious | instruction-like text, in English or Arabic |
| `contract_qualifies` | noul | yes, no | the term from start and end dates |
| `fact_status` | choice | new, update, conflict, duplicate | none: compare with the brain |
| `urgency` | score | 0 no deadline · 1 this quarter · 2 within 14 days · 3 within 3 days or late | the due date (`--due`) |
| `stakes` | score | 0 housekeeping · 1 internal · 2 customer-facing or money · 3 legal, contractual or large sums | tax, legal and contract keys (3); prices and policies (2) |
| `official_check` | noul | yes, no | tax and legal keys; mentions of VAT, ministries, decrees, government fees and similar |

A business can add its own in `_system/decision-types.json`:

```json
{
  "lead_quality": {"kind": "choice", "question": "How ready is this lead to buy?",
                   "criteria": {"hot": "asked for a quote or a start date", "warm": "interested, no timeline", "cold": "no intent shown"}},
  "deal_risk": {"kind": "score", "question": "How likely is this deal to slip?", "levels": ["low", "medium", "high"]},
  "will_renew": {"kind": "noul", "question": "Will this customer renew?"}
}
```

Run `decide.py lint <brain>` after editing it. The health check does too. What lint checks:
- A choice has 20 options at most; split bigger ones into two questions.
- A choice never uses yes/no labels; make that a noul.
- A score has 2 to 7 levels, each with a description.
- A noul question is phrased positively ("Will they renew?", not "Will they not renew?").

## One input, several questions: the question sheet

When a new item arrives (a message, a document, a fact the user mentions), ask all the small questions about it together rather than one at a time:

1. **Get the sheet:** `decide.py questions <brain> --types capture,domain,sensitivity,urgency,stakes,official_check --text "<the item>" [--key K] [--due YYYY-MM-DD]`. Questions a rule settles come back already answered, so no judgement is needed for those. The rest come back with their options or rubric.
2. **Answer the rest in one pass**, with honest probabilities:
   - **0.95 and above:** the evidence states it plainly.
   - **0.8 to 0.95:** strong but indirect evidence.
   - **0.6 to 0.8:** a reasonable reading that could be wrong.
   - **Below 0.6:** a guess.

   Give probabilities for every plausible option rather than one number when more than one fits.
3. **Record them together:**

   `decide.py batch <brain> --subject <entry or item> --types <same list> --text "<the item>" --answers '{"capture": {"scores": {"remember": 0.9, "skip": 0.1}}, "urgency": {"dist": {"0": 0.1, "1": 0.2, "2": 0.6, "3": 0.1}}, "official_check": {"p": 0.2}}' --auto <auto setting> --review <review setting>`

   Types that a rule settled are recorded from the rule; you don't repeat them.
4. **Follow the route** of each answer. The batch also gives the strictest route overall, and `ask_user` lists what to confirm. Put all the confirmations to the user in one question.

For a single decision, `decide.py record` takes the same answer shapes: `--scores`, `--dist`, `--p`, or `--choice` with `--confidence`.

## Routes

- `apply`: do it, and mention it in the report back.
- `confirm`: ask the user, showing the choice and the evidence. After they answer, run `decide.py confirm --id <id>`, or `decide.py correct --id <id> --actual <their answer>`.
- `escalate`: for official information or anything high-stakes, use the `brain-checker` agent; otherwise ask the user. Record the outcome the same way.

These cases always come back as `confirm`:
- The top two options are within 0.15 of each other. Ask the user to pick between the two.
- A rule disagrees with your answer.
- A document is judged suspicious.
- The text is in a script the brain has not been calibrated on (see below).

**Never answer outside the schema.** The script refuses an option that isn't listed, a level off the rubric, and a probability outside 0 to 1. It rescales probabilities that add up to more than 1. If nothing fits, choose the closest, give it low confidence and ask.

The thresholds come from the plugin settings listed in the core skill (auto-apply and ask-me confidence; defaults 0.9 and 0.6). If `capture_mode` is `ask`, treat every `capture` decision as `confirm` regardless of confidence.

**Use urgency and stakes to order work.** List decisions for the user and health-check findings most urgent first. Anything with stakes 3 goes on the escalation ladder's "must ask" step, whatever the confidence.

## Valid is not the same as correct: calibration

A decision can be a valid option and still wrong. Filing a login bug under billing is valid, but wrong. So every outcome is measured. A confirmed decision was right, a corrected one was wrong, and an auto-applied decision nobody corrected counts as right.

`decide.py stats <brain> --write` reports, per decision type:
- accuracy, mean confidence and over-confidence;
- **Brier score** (lower is better);
- **calibration error (ECE)**: the average gap between the confidence stated and how often it was right;
- for scores, the mean distance between the expected level and the real one.

It then acts on the numbers:
- **Temperature.** With 20 or more checked decisions of a type, a temperature is fitted that best matches stated confidence to real accuracy. From then on every new confidence of that type is corrected by it before routing. A judge who says 0.95 but is right 70% of the time is read as 0.70, so it asks instead of acting. The log keeps both numbers.
- **Threshold.** Below 90% accuracy (over 10 or more decisions), the auto-apply bar for that type rises to 0.97. Below 75%, auto-apply stops for that type. It is restored at 95%.
- **Rules.** The same correction three or more times in one domain produces a **proposed rule** in `_system/decisions-needed.md`. When the user approves it, add it with `decide.py add-rule`. From then on the rule settles those cases automatically.

## Languages

Rules and calibration built on English text don't carry over to other scripts. A model can be confidently wrong on text unlike what it was checked on. So every decision records the script of its input (latin, arabic and others).
- Arabic has its own rules for confidential data and for instructions hidden in documents.
- On any script other than Latin, nothing is auto-applied until 20 decisions on that script have been checked. Until then those decisions come back as `confirm`, unless a rule settles them.
- Judge Arabic and other text in its own language. Don't translate first and judge the translation.

Run the stats as part of every full health check.
