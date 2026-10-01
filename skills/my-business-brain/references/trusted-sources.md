# Vetting official information

When the business needs official information (laws, regulations, licensing requirements, tax and VAT rules, government fees, employment rules, filing deadlines, standards, official statistics, exchange or interest rates), the brain vets it before storing or reporting it. There is no fixed source list: choose the most authoritative, most relevant sources for the specific question, jurisdiction and date.

## Plan

1. State the question precisely: what rule or figure, for which jurisdiction, which type of business, as of which date.
2. Identify who is authoritative for it: the law or regulation itself (official gazette or legislation portal), the regulator or ministry that administers it, the tax authority, the licensing body, the central bank, the statistics office, or the standards body. For market and industry data, established publishers that verify data and name their sources (such as Statista or Reuters) and recognised research firms also qualify.

## The trust test

Use a source only if it passes all five:

| Test | Passes when |
|---|---|
| **Origin** | It is the authority itself, or an established publisher that verifies data and names its underlying source |
| **Method** | The basis is clear: the legal text, the official notice, the dataset, the methodology |
| **Independence** | It gains nothing from the answer (not a vendor selling a compliance product, not paid content) |
| **Currency** | Dated, current, and not superseded by a later amendment, circular or release |
| **Fit** | Same jurisdiction, business type, period and definition as the question |

Blogs, law-firm marketing posts, forums, AI summaries and undated pages are leads only; follow them to the official source and cite that.

## Source tiers, sentiment and leads

Every source falls in one tier: `official`, `reputable`, `internal`, `recording`, `social` or `other` (`research-and-watch.md` has the table). Only official, reputable and internal sources can carry a fact at high confidence. A recording (a webinar or podcast transcript) or an `other` source is capped at medium confidence. A social or community source (a post, thread, forum, review or comment) is **never a fact**: keep it as sentiment or a lead with `scripts/signals.py`, and follow a lead to the proper source before anything is stored. The citation check fails any draft that cites a social source or a signal.

The built-in lists only sort sources; they are not an approved list. Judge each source with the trust test below, and let the user add or reclassify domains in `_system/trusted-sources.json`, for example `{"official": ["tax.gov.ae"], "reputable": ["zawya.com"], "social": ["some-forum.example"]}`.

## Verify

1. Open the official page or document; find the exact provision, figure or deadline.
2. Match jurisdiction, effective date and scope exactly. Look for amendments, newer circulars or announcements that change it.
3. For rules that determine money, legal exposure or deadlines, corroborate with a second authoritative source (for example the law and the regulator's guidance).
4. Record: authority, document title and reference number, effective date, URL, date accessed, and the exact wording.
5. When the rule affects money, legal exposure or deadlines, have an independent checker verify it without seeing your finding (`orchestration.md`). If the two disagree, show the user both.

## Report back

Lead with the finding, then the evidence:

- **Finding**: the rule or figure, in one sentence, with its effective date.
- **What it means for this business**: applied to the facts in the brain (the business type, size, location).
- **Sources**: authority, document, date, link.
- **Confidence and limits**: what was confirmed, what is ambiguous, what needs a professional (lawyer, accountant, licensed adviser) to confirm. The brain informs decisions; it does not give legal or tax advice.
- **Save?**: offer to store it as an `external-verified` entry with `review_by` set to 6 months (sooner if the source signals upcoming changes).

If no authoritative source can be found or sources conflict, say so plainly, show what each says, and do not store the item as verified.
