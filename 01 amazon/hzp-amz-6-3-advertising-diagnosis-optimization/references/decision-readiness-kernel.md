# 6-3 Decision Readiness Kernel

6-3 asks two separate questions for each object: **is evidence mature enough for this particular action?** and **what decision best serves the approved 605 purpose now?** Do not collapse these into one score or a fixed number of days.

## Evidence to inspect

Use only facts present in the resolved 6-2 Run Package and its metadata, 605 approved purpose, and valid supporting 603/606 assets. Consider, where actually available:

- object age, active-data days, first observed activity and days since last real change;
- impressions and clicks; spend and current Bid/Budget or budget utilization;
- orders, sales, CVR, ACoS and ROAS;
- dated 3/7/14/30-day or since-launch direction from real dated rows;
- source-window grain, attribution maturity/backfill and data completeness;
- 605 task, phase, intended traffic method and control mode;
- 603 search volume, opportunity ratio and Parent/Child relationship;
- 606 Benchmark occupancy evidence when available;
- the risk and reversibility of the proposed action.

Do not imply those facts are present merely because this list names them. The current 6-2 fixed CSV schemas contain daily/window performance, but do not carry all creation/last-change/attribution/placement or product economic-boundary values. Missing values remain unknown and can make an action `继续观察` or `待人工补充`; do not reconstruct them from Campaign names, inferred launch dates, HTML, or memory.

## Action-specific evidence

Treat these as judgment prompts, not numeric thresholds:

- A clearly irrelevant query, wrong object, duplicate delivery or technical error can require prompt candidate handling without waiting for conversion volume.
- A concrete budget cap that is demonstrably constraining a validated plan can be reviewed sooner than a strategy-level change.
- Another Bid decision normally needs meaningful evidence since the last Bid change. Another Placement change needs traffic gathered since the last Placement change.
- Pausing a Target, demoting an Intent, or changing shared/independent control requires stronger and more persistent evidence than holding or making a small reversible adjustment.
- Relevant but unconverted Search Terms are not automatically negatives. A new-product core term may merit continued strategic observation despite short-term efficiency weakness.
- A 14-day object with six clicks may be less decision-ready than a 3-day object with 120 clicks and 15 orders. Conversely, short windows with incomplete attribution or unstable direction may still need observation.

Do not use `7 days = decided`, `X clicks + zero orders = pause`, `ACoS high = lower Bid`, or `ACoS low = increase Budget`. Diagnose across available windows and consider sample volume, spend, attribution maturity, post-change data, 605 purpose, market context and reversibility. If economics are required but no validated margin/CPA/ACoS boundary exists, flag `ECONOMIC_BOUNDARY_UNAVAILABLE`; do not invent break-even values.

## Modification and post-change observation

Use explicit 6-2 change timestamps and change type only when present in the actual input/metadata. Treat a material change by 6-4 (Bid, Budget, Placement, Target state, or structural migration) as the start of a new observation context for affected objects. Avoid changing another correlated variable before enough relevant post-change evidence accrues, unless a clearly urgent error justifies interruption. State the interrupted validation context in the reason.

Pick windows appropriate to the question and source grain. Dated daily data may support 3/7/14/30-day totals; a `SOURCE_WINDOW` record cannot be split into those windows. Every row's reason must state which actual window it relies on; for immediate technical or irrelevant-traffic issues state `即时异常` and cite the observed fact. Next observation conditions describe a measurable event or evidence threshold, not an arbitrary date promise—for example, enough post-change clicks/spend/orders, attribution completion, repeated converting Search Terms, or a material change in budget utilization.

## Maturity interpretation

- `可决策`: enough relevant, sufficiently stable evidence exists for the specific decision being considered. This can mean deliberately keeping the current state.
- `继续观察`: evidence is immature, incomplete, confounded by recent changes, or insufficient for the action's risk. Name what is missing and what observation would resolve it.
- `紧急处理`: a concrete technical/identity/relevance/safety issue warrants immediate containment. This does not authorize execution; output a candidate decision for review/6-4.

Output `可决策 + 保持` when sufficient evidence supports no change, with its reason and re-evaluation condition. Output `继续观察 + 继续观察/保持观察` when the evidence is not sufficient. Every execution candidate is `待确认`; 6-3 does not execute it.
