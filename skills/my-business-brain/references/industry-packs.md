# Industry packs

A pack is a starting point for a kind of business. `scripts/pack.py list` shows those available: clinic, agency or consultancy, trading, law firm, real estate, restaurant.

## What a pack brings

- **Key prefixes** that file facts in the right area (`fee.` → pricing, `practitioner.` → people). Decision rules use them, so the domain call is settled without judgement.
- **Confidential terms**: words that always make a fact confidential in that trade (patient, landed cost, client). The sensitivity rules use them.
- **Decision types** for the trade: appointment type, lead stage, scope change, claim risk. They're added to `_system/decision-types.json` without replacing anything already there.
- **Starting questions**: the facts every business of that kind should record, written to `_system/pack-questions.md` with the key, area and sensitivity for each answer.
- **What to watch** (licence renewals, lease notices) and common terms for the glossary.

## Applying a pack

`scripts/pack.py apply <brain> <id>`. It merges into what's there: settings the business already has win, and applying twice changes nothing. Several packs can be combined, such as a clinic that also sells products. It's logged in the changelog.

Then work through the starting questions with the owner, a few at a time. Each answer becomes an entry through the normal Remember flow and decision gates. After the first answers, propose golden questions from them.

## Building a pack with the owner

When no pack fits, interview the owner in one message:
- what they sell;
- who their customers and suppliers are;
- which licences and contracts they hold;
- what they consider confidential;
- which small calls come up again and again.

Draft the pack as JSON in the same shape as the files in `packs/`:
- `id`, `name`, `description`;
- `key_prefixes`, `confidential_terms`, `decision_types`;
- `fact_templates`, each with `key`, `title`, `domain`, `sensitivity` and `ask`;
- `watch`, `glossary`.

Save it and run `scripts/pack.py new <brain> --file <draft.json>`. That checks it (known areas, valid sensitivities, decision types that pass lint), saves it in `_system/packs/` and applies it. Fix anything it reports and try again.

Keep packs general. Don't put specific laws, fees or authority names in a pack. Those are official information and go through vetting (`trusted-sources.md`) when the owner's answers need them.
