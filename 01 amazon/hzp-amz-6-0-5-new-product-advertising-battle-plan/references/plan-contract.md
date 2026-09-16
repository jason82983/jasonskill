# 6-0-5 输入、决策与输出合同

## Inputs

The only formal analysis inputs are a same-run, latest-valid 6-0-3 bundle:

- `PRECISION_BROAD_SUMMARY`: `精准泛词, 中文, 层级, 父精准泛词, 直接搜索量, 汇总搜索量, 平均竞品数, 意图机会比, 直接对应词数`.
- `PRECISION_BROAD_MAPPING` modern: `Id, 词, 中文, 市场容量, 竞争产品数, 供需比, 对标覆盖数, 最佳自然排名, 自然排名中位数, 精准泛词, 精准泛词中文`.
- Legacy single-Benchmark mapping only: `Id, 词, 中文, 市场容量, 竞争产品数, 供需比, 自然排名, 精准泛词, 精准泛词中文`.

`Id` is the user-confirmed stable/unique `KwId` entity key. Preserve all facts exactly as read. Market capacity, competitor count and supply-demand ratio are one unique keyword market fact; Benchmark coverage/ranks are reality observations only. No 606 input is allowed in this version.

## AI decisions JSON

The AI supplies decisions only after examining resolved input rows and relevant known product facts. Script input format:

```json
{
  "intents": [
    {"精准泛词":"canonical intent", "作战任务":"首攻", "作战优先级":"P1",
     "作战方向":"why/where", "控制方式":"独立", "控制原因":"独立预算和Placement以验证首攻Intent",
     "决策原因":"qualitative evidence-led rationale"}
  ],
  "keywords": [
    {"Id":"KwId", "精准泛词":"canonical intent", "作战任务":"首攻",
     "当前状态":"首攻", "新品期是否投放":"是", "计划阶段":"PHASE_1",
     "计划投放方式":"EXACT", "控制方式":"独立", "控制原因":"明确说明关键词级例外；不变更时可省略并继承Intent",
     "启动条件":"", "暂不投放原因":"",
     "作战目的":"specific validation purpose"}
  ]
}
```

One decision per summary Intent and every mapping Id exactly once. Keyword Intent must match its 6-0-3 mapping. Supported task: `首攻/核心/扩展/探索/暂缓`; phase: `PHASE_1/PHASE_2/PHASE_3/SEASONAL/HOLD`; execution: `EXACT/PHRASE/BROAD/AUTO/ASIN/CATEGORY/blank`; current state: `首攻/布局/待扩张/季节等待/储备/暂缓`; priority: `P1/P2/P3/HOLD`. Unsupported/untraceable ASIN or Category targeting fails closed with `BATTLE_UNIT_SOURCE_MISSING` because the formal input has no such target identity.

Do not impose fixed weights. A Child may be the beachhead and its Parent the core. Birthday does not imply annual seasonality. If not starting a keyword, preserve it and provide a concrete trigger or reason; do not invent future dates. PHASE_1 defaults to one primary execution method per keyword.

## CSV schemas

Intent A, exact ordered schema:

`意图代码｜精准泛词｜中文｜层级｜父精准泛词｜直接搜索量｜汇总搜索量｜平均竞品数｜意图机会比｜直接对应词数｜作战任务｜作战优先级｜作战方向｜控制方式｜控制原因｜决策原因｜确认状态`

Keyword lifecycle C, modern multi-Benchmark schema:

`Id｜词｜中文｜精准泛词｜意图代码｜市场容量｜竞争产品数｜供需比｜对标覆盖数｜最佳自然排名｜自然排名中位数｜作战任务｜控制方式｜控制原因｜当前状态｜新品期是否投放｜计划阶段｜计划投放方式｜启动条件｜暂不投放原因｜确认状态`

Legacy single-Benchmark C substitutes one `自然排名` for the three modern rank-evidence columns.

Battle detail B is derived only from C PHASE_1 + `是`, never reselected. Modern:

`作战单元ID｜精准泛词｜意图代码｜作战任务｜作战优先级｜控制方式｜Id｜词｜中文｜市场容量｜竞争产品数｜供需比｜对标覆盖数｜最佳自然排名｜自然排名中位数｜计划阶段｜投放方式｜作战目的｜确认状态`

Legacy single-Benchmark B substitutes `自然排名` for the three modern rank-evidence columns. All source facts must pass through unchanged. All first outputs have `确认状态=PROPOSED`; manual review may later edit rows to `APPROVED` or `HOLD`. Control mode is one of `独立/共享/不投`; C inherits A unless a keyword-level exception is explicit and its reason is recorded. B only carries the C decision. `不投` cannot appear in B.

## Stable identities, run and approval

Stable Intent Codes persist in `intent-code-registry.json`; existing mappings are never reallocated. New codes derive deterministically from canonical intent tokens with collision resolution and then persist. Battle Unit ID deterministically incorporates Product Code, Variant Code, Intent Code, 6-0-3 KwId, execution method and phase; no UUID or row-order ID.

All four assets use one shared Stage 6 RunContext and timestamp (`YYYYMMDD_HHMMSS`), have sidecar metadata, and are created only if paths do not already exist. Metadata records both exact input filenames/identities, 6-0-3 RUN_ID/generated time, counts, resolver method, current product and output assets. CSVs do not receive lineage columns.

6-1 consumes only a resolver-validated same-run bundle where every A/C/B record has human `APPROVED` or `HOLD`; no `PROPOSED` row may be executed. Approved C PHASE_1 launch Ids and approved B Ids must match exactly. Human approval is not blanket permission to write Amazon ads; existing 6-1 approval/preflight safeguards still apply.

## Technical-only architecture preview

The program derives the preview from A/C/B. Role translation: `首攻/核心 + EXACT → COR-EXA`; `扩展 + PHRASE → EXP-PHR`; `探索 + BROAD → DIS-BRO`; `探索 + AUTO → DIS-AUT`; explicit target identities would be `COM-ASI` or `CAT-CAT` but are not created from this version's keyword-only source. Independent campaigns group by Intent Code plus compatible technical dimensions; shared pools group only by compatible AdType, Role, Target/Traffic Type, phase and planned budget/placement strategy; no-invest units are omitted. One independently controlled Intent may contain multiple Keywords; never make one Campaign per keyword. Small intents are not mechanically split into separate budgets. C determines control mode, with reason preserved; B does not redetermine it.

The control-aware formatter is `format_campaign_name(..., intent_code=..., control_mode=...)`. Naming is `{Product}.{Variant}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Sequence}`; independent includes one Intent Code, shared excludes it, and no-invest emits no campaign. Examples: `B2.M.SP-COR-EXA-SBG-01` and `B2.M.SP-EXP-PHR-01`. AdType remains in the fixed identity slot, including `SP/SB/SD`. 6-0-5 previews sequence `01` only; 6-1 resolves current collisions before apply and never renames existing names. Use shared `format_ad_group_name()` for Ad Groups. No Bid, Budget, Placement percentage, Bidding Strategy or actual target values are decided here.

## Failure states

Fail closed and do not claim FULL_SUCCESS for: `605_INPUT_NOT_FOUND`, `605_INPUT_RUN_MISMATCH`, `605_INPUT_SCHEMA_INVALID`, `605_INPUT_EMPTY`, `INTENT_CODE_CONFLICT`, `KEYWORD_LIFECYCLE_MISSING`, `DUPLICATE_KEYWORD_ID`, `INVALID_BATTLE_TASK`, `INVALID_PHASE`, `INVALID_EXECUTION_METHOD`, `BATTLE_UNIT_SOURCE_MISSING`, `BATTLE_UNIT_ID_CONFLICT`, `ARCHITECTURE_TRACE_MISMATCH`, `OUTPUT_COVERAGE_MISMATCH`, `605_PLAN_NOT_APPROVED`.
