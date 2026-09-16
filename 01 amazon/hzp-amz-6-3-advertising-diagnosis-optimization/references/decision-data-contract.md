# 6-3 Decision Package Data Contract

Runtime scope is inherited, never widened: ProductCode/CampaignTag must match the 6-2 manifest's exact `ProductCode.CampaignTag.` prefix. Only in-scope Campaign rows and child Target/SearchTerm rows joined by CampaignId may enter the decision context; Intent rows must be represented by scoped Targets. Mismatch returns `RUNTIME_SCOPE_MISMATCH`; contaminated rows are excluded and prevent `FULL_SUCCESS`.

## Decision enums

`决策成熟度` is exactly one of `可决策｜继续观察｜紧急处理`.

Intent results: `保持｜继续观察｜放大｜收缩｜升级独立｜降级共享｜阶段升级｜阶段降级｜暂停候选`.

Campaign results: `保持｜继续观察｜增加预算｜降低预算｜调整位置｜暂停候选`.

Target results: `保持｜继续观察｜提高竞价｜降低竞价｜迁移候选｜暂停候选`.

Search Term results: `保持观察｜收割候选｜否定候选`; `建议处理方式` repeats the corresponding allowed handling. Candidate does not mean an Amazon operation was executed.

`确认状态` is exactly `待确认｜已批准｜暂缓`. 6-3-created change candidates start `待确认`; the helper rejects an output that implies approval. Approval is a later human decision and never triggers an Amazon write from 6-3.

## Fixed CSV schemas

Headers and ordering are immutable:

**A. Intent — one row per Intent**

```text
IntentCode｜精准泛词｜当前作战任务｜当前控制方式｜当前阶段｜汇总搜索量｜意图机会比｜近3日Spend｜近7日Spend｜近14日Spend｜近30日Spend｜近7日Orders｜近14日Orders｜近30日Orders｜近7日Sales｜近14日Sales｜近30日Sales｜近7日ACoS｜近14日ACoS｜近30日ACoS｜近7日CVR｜近14日CVR｜近30日CVR｜距上次修改天数｜决策成熟度｜决策结果｜目标作战任务｜目标控制方式｜目标阶段｜决策原因｜下一观察条件｜确认状态
```

**B. Campaign — one row per Campaign**

```text
CampaignId｜CampaignName｜AdType｜TechnicalRole｜TargetType｜控制方式｜IntentCode｜当前Budget｜当前Placement｜近3日Spend｜近7日Spend｜近14日Spend｜近30日Spend｜近7日Orders｜近14日Orders｜近30日Orders｜近7日ACoS｜近14日ACoS｜近30日ACoS｜距上次修改天数｜决策成熟度｜决策结果｜建议Budget｜建议Placement｜决策原因｜下一观察条件｜确认状态
```

**C. Target — one row per Target**

```text
BattleUnitId｜TargetId｜CampaignId｜IntentCode｜精准泛词｜TargetType｜TargetValue｜MatchType｜当前Bid｜近3日Clicks｜近7日Clicks｜近14日Clicks｜近30日Clicks｜近3日Spend｜近7日Spend｜近14日Spend｜近30日Spend｜近7日Orders｜近14日Orders｜近30日Orders｜近7日Sales｜近14日Sales｜近30日Sales｜近7日ACoS｜近14日ACoS｜近30日ACoS｜距上次修改天数｜决策成熟度｜决策结果｜建议Bid｜目标控制方式｜决策原因｜下一观察条件｜确认状态
```

**D. Search Term — one row per SearchTerm × Source Target**

```text
SearchTerm｜TargetId｜BattleUnitId｜CampaignId｜IntentCode｜精准泛词｜SourceTarget｜MatchType｜FirstSeenDate｜LastSeenDate｜ActiveDays｜近7日Clicks｜近14日Clicks｜近30日Clicks｜近7日Spend｜近14日Spend｜近30日Spend｜近7日Orders｜近14日Orders｜近30日Orders｜近7日Sales｜近14日Sales｜近30日Sales｜决策成熟度｜决策结果｜建议处理方式｜决策原因｜下一观察条件｜确认状态
```

An unavailable source value is `NULL`/`DATA_NOT_AVAILABLE` according to the current file contract; never fabricate zero. If 6-2 supplies no Placement, modified-at, attribution or economic-boundary fact, preserve it as unavailable. The schema has no separate evidence-window column, so every `决策原因` must name the real date/window used (or say `即时异常` for a clearly urgent technical/relevance issue). Do not invent 6-2 modification timestamps; the current 6-2 fixed schemas do not include all `CreatedAt`, `LastModifiedAt`, `LastModifiedType`, `FirstImpressionDate`, `FirstClickDate`, `FirstOrderDate`, or placement facts.

## Required fields and candidate values

For every row in every table, `决策成熟度`, `决策结果`, `决策原因`, `下一观察条件`, and `确认状态` must be non-empty and from the allowed enum where applicable. A rationale must be specific to the row and cite its facts, relevant 605 purpose, and exact evidence window(s); generic copy is invalid.

When the decision changes a numeric value, include both current and proposed values:

- Campaign `增加预算` / `降低预算`: `当前Budget` and `建议Budget`.
- Campaign `调整位置`: `当前Placement` and `建议Placement`.
- Target `提高竞价` / `降低竞价`: `当前Bid` and `建议Bid`.

An Intent transition must state its destination in the appropriate `目标作战任务`, `目标控制方式`, and/or `目标阶段` field. Structural recommendations across Intent/Campaign/Target must describe one consistent destination state. No row is `APPROVED` merely because the model generated it.

## Coverage, identity, and history

The caller supplies an evaluated identity set per layer, derived from the resolved same-run inputs. The emitted decision identities must match those sets exactly; missing, duplicated, or extra evaluated objects fail with a coverage/schema error. A Target is keyed by TargetId; Campaign by CampaignId; Intent by IntentCode; Search Term by `(SearchTerm, TargetId)` at 6-2 grain. Missing identities remain a data-quality issue and cannot be guessed from names.

Decision history keys use these same stable IDs, not display names. Current output is one immutable run. Old decisions are input evidence only; never rewrite historical packages.

The 6-4 handoff is the subset of validated rows whose `确认状态=已批准`, with source Run IDs and proposed values. This is a structured daily-action request; 6-4 performs its own technical identity/permission/diff/read-back checks and does not repeat the business decision.
