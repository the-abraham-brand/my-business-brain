# Decision gates

The brain makes the same small decisions over and over. Treat each one as a **bounded decision**: a fixed list of options, a choice, a confidence and the evidence. Use `scripts/decide.py` so every decision is checked, routed and logged, and so the brain learns how reliable it is.

## Decision types

| Type | Options | Asked when |
|---|---|---|
| `capture` | remember, skip | The user mentions something in passing: is it a business fact worth keeping? |
| `domain` | the brain's domains | Filing a new entry |
| `sensitivity` | public, internal, confidential | Labelling a new entry |
| `document_safety` | safe, suspicious | Before loading a document |
| `contract_qualifies` | yes, no | A contract is shared: does it get Contract Clocks? |
| `fact_status` | new, update, conflict, duplicate | New information meets the brain |

A business can add its own in `_system/decision-types.json`, for example `{"lead_quality": ["hot", "warm", "cold"]}`.

## The steps

1. **Rules first.** Run `decide.py rules <brain> --type T` with the context (`--text`, `--domain`, `--key`, `--start/--end`). If a rule settles it (salary or IBAN means confidential; a `price.` key belongs in pricing; a 20-day contract does not qualify; instruction-like text is suspicious; any rule the user has approved), use that answer. No judgement is needed.
2. **Otherwise judge, then record.** Decide, and give an honest confidence:
   - **0.95 and above:** the evidence states it plainly.
   - **0.8 to 0.95:** strong but indirect evidence.
   - **0.6 to 0.8:** a reasonable reading that could be wrong.
   - **Below 0.6:** a guess.

   When several options are plausible, pass a score for each (`--scores '{"sales":0.52,"marketing":0.46}'`) rather than one confidence.

   `decide.py record <brain> --type T --choice C --confidence P --subject <entry or item> --evidence "<why>" --auto <auto setting> --review <review setting>`
3. **Follow the route it returns:**
   - `apply`: do it, and mention it in the report back.
   - `confirm`: ask the user, showing the choice and the evidence. After they answer, run `decide.py confirm --id <id>`, or `decide.py correct --id <id> --actual <their answer>`.
   - `escalate`: for official information or anything high-stakes, use the `brain-checker` agent; otherwise ask the user. Record the outcome the same way.

   Two cases always come back as `confirm`: when the top two options are within 0.15 of each other, and when a rule disagrees with your choice.
4. **Never pick an option outside the list.** The script refuses it. If none fits, choose the closest, give it low confidence and ask.

The thresholds come from the plugin settings listed in the core skill (auto-apply and ask-me confidence; defaults 0.9 and 0.6). If `capture_mode` is `ask`, treat every `capture` decision as `confirm` regardless of confidence.

## Valid is not the same as correct

A decision can be a valid option and still wrong: filing a login bug under billing is valid, but wrong. That is why corrections are logged and measured.

- `decide.py stats <brain> --write` reports accuracy per decision type and how over-confident the brain has been. It then acts on the numbers:
  - accuracy below 90% (over 10 or more decisions): the auto-apply bar for that type is raised to 0.97;
  - accuracy below 75%: auto-apply stops for that type;
  - once accuracy recovers to 95% or better, the bar is restored.
- The same correction three or more times in one domain produces a **proposed rule** in `_system/decisions-needed.md`. When the user approves it, add it with `decide.py add-rule`. From then on the rule settles those cases automatically: the correction has become a rule.

Run the stats as part of every full health check.
