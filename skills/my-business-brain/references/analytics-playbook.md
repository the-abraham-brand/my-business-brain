# Analytics playbook

The brain analyses the business the way a top-tier strategy consultant would: start from the decision, be hypothesis-driven, structure the problem so nothing overlaps or is missed, quantify everything, and lead with the answer and the "so what".

## The method

1. **Frame the decision.** What decision does this analysis serve, who makes it, and by when? Restate the question as one sentence ("Should we raise Growth plan prices by 10% in Q1?"). If the question is vague ("how are we doing?"), run the Business Health Check.
2. **Form hypotheses.** State 2–4 testable hypotheses up front ("Churn rose because of the March price change"). They focus the work; the data confirms or kills them.
3. **Structure the problem as an issue tree.** Break the question into parts that are mutually exclusive and collectively exhaustive (MECE): e.g. profit = revenue − cost; revenue = customers × purchases per customer × average price. Every branch ends in something measurable.
4. **Gather the data.** From the brain first (metrics, prices, customers, costs), then the user's files (exports, spreadsheets, accounts). Record what is missing and ask for it in one batch. External benchmarks are vetted (see `trusted-sources.md`).
5. **Analyse with code.** Compute with Python or spreadsheet formulas, never mental arithmetic. Show the calculation. Check totals reconcile to the source data.
6. **Find the 80/20.** Which few customers, products, costs or causes drive most of the result?
7. **Synthesise, answer first.** One governing conclusion, 2–4 supporting findings, each with evidence. Every exhibit title states its takeaway ("Three customers generate 61% of revenue"), not its topic ("Revenue by customer").
8. **Recommend.** Specific actions with expected impact (quantified, with the assumption), effort, owner, timing, and the risk if wrong. Rank by impact over effort.
9. **Stress-test.** Sensitivity on the two or three assumptions that matter most; state what would change the recommendation.
10. **Save and learn.** Save to `analytics/<date>-<topic>.md`; store new metrics and decisions in the brain; note follow-up dates.

## Analysis library

Pick the modules that fit the question.

| Module | Answers | Core outputs |
|---|---|---|
| **Business Health Check** | How are we doing? | KPI scorecard vs target and prior period (revenue, gross margin, cash, pipeline, churn, NPS if available); red/amber/green with the reason; top 3 issues and opportunities |
| **Revenue bridge** | Why did revenue change? | Change split into volume, price and mix effects, and new vs existing customers |
| **Customer concentration & Pareto** | How dependent are we on a few customers? | Share of revenue from top 1/5/10 customers; concentration risk; long-tail profitability |
| **Unit economics** | Does each sale make money? | Contribution margin per unit/customer, CAC, LTV, LTV/CAC, payback months |
| **Retention & cohorts** | Are customers staying? | Cohort retention curves, churn and its drivers, net revenue retention |
| **Pricing review** | Are we priced right? | Price vs value delivered, competitor price points (vetted), discount leakage, price-volume sensitivity |
| **Cost structure & break-even** | Where does the money go? | Fixed vs variable, cost per unit trends, break-even volume, savings opportunities ranked |
| **Cash & working capital** | Will we run short? | Runway, burn, DSO/DPO/inventory days, cash conversion cycle, 13-week cash view |
| **Sales funnel** | Where do deals leak? | Stage conversion rates, cycle time, win/loss reasons, pipeline coverage vs target |
| **Root cause** | Why did X happen? | Issue tree of possible causes, evidence for and against each, confirmed cause(s) |
| **Opportunity sizing** | Is this worth pursuing? | Bottom-up size (customers × price × adoption), investment, payback, risks |
| **Scenario & sensitivity** | What if? | Base/upside/downside with explicit assumptions; tornado of key drivers |
| **Competitive position** | How do we compare? | Comparison on buyer criteria with vetted, dated competitor facts |

## Output format

1. **Answer**: the conclusion and recommendation in two or three sentences.
2. **Key findings**: 2–4, each an action title plus evidence (number, source entry or file).
3. **Exhibits**: charts or tables, each with a takeaway title; data and calculations in an appendix or file.
4. **Recommendations**: table of action, impact, effort, owner, timing, risk.
5. **Assumptions and data gaps**: what was assumed, what would change the answer, what to collect next.
6. **Next steps and review date.**

Deliver as a document the user can keep (and as a spreadsheet when the data should be reused). Use charts where they make the point faster than a table.

## Standards

- No number without a source (brain entry, file, or vetted external source).
- Distinguish facts, calculations, assumptions and opinions.
- Be decisive where the evidence is strong, explicit about uncertainty where it isn't.
- Never present external benchmarks as the business's own data.
- Financial, legal and tax conclusions inform decisions; recommend professional confirmation where the stakes require it.
