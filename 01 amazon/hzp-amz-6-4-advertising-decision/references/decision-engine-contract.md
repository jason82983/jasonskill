# 6-4 DECIDE 最终契约

本文件覆盖此前任何与职责冲突的旧段落。

## 唯一职责与链路

`6-1 PLAN → 6-2 BUILD → 6-3 DATA → 6-4 DECIDE → 人工批准(V1) → 6-5 APPLY → 6-6 REPORT`。

6-4 只回答：基于真实广告事实、原作战目的、市场价值、历史决策和实际执行，现在应该怎么办。6-4 不查询广告替代 6-3，不执行 Amazon Ads 写操作，不调用 `apply_change_plan`。所有获批动作交给 6-5。

## 输入优先级

1. 最新有效 6-3 DATA Run Package：Campaign、Ad Group、Target、Search Term、Performance、Bid、Budget、Placement、Status、时间窗口和数据完整性。
2. 6-1 最新适用且可追溯 PLAN：IntentCode、BattleUnitId、作战任务、阶段、投放方式、控制方式、目的、优先级、启动条件。
3. 最新有效 6-0-3：Intent Tree、Parent/Child、直接/汇总搜索量、平均竞品数、意图机会比和 Keyword→Intent。6-4 不重建 Intent。
4. 最新有效 6-0-6：Benchmark Occupancy、Consensus、TopN Coverage、Weighted Rank，仅作 Reality Evidence。
5. 当前 Scope 对象的历史 6-4 Decision History。
6. 真实成功执行时间和 Read-back 通过记录组成的 6-5 Execution History。

无法追溯时分别返回 `PLAN_LINEAGE_MISSING`、`HISTORY_JOIN_FAILED` 或 `EXECUTION_HISTORY_MISSING`，不得伪造缺失证据。

## Scope 与 Evidence Gate

6-4 继承 `ProductCode + CampaignTag → CampaignPrefix`，只对本次 6-3 Run 中属于当前 Prefix 的对象正式决策；Scope 外对象标记 `SCOPE_CONTAMINATION`。

每个对象第一问是“现在有资格做这个决定吗”。成熟度只能是：`可决策`、`继续观察`、`紧急处理`。不得用“运行满7天”机械判定成熟。

程序计算并传入：DaysSinceCreated、ActiveDataDays、DaysSinceLastChange、Impressions、Clicks、Spend、Orders、Sales、CTR、CPC、CVR、ACoS、ROAS、Attribution Maturity、Data Completeness、3D/7D/14D/30D/Since Last Change。缺字段保持 `UNKNOWN`/`DATA_GAP`。

每次 6-5 成功执行相关实质修改，Change Clock 从该次真实成功时间重新开始。Campaign 运行30天但 Bid 昨天修改时，只能用修改后的新证据判断。

## 四层决策

- **Intent**：保持、放大、收缩、继续观察、升级独立候选、降级共享候选、阶段升级/降级候选、暂停候选。
- **Campaign**：Budget、Placement、Campaign-level control。预算烧完不等于自动加预算。
- **Target**：保持/提高/降低 Bid、继续观察、暂停候选、迁移候选。所有参数动作都必须有 `CurrentValue → ProposedValue`、`ExpectedCurrent`、Why Now、Direction、Magnitude。
- **Search Term**：保持观察、收割候选、否定候选。精准但短期经济差的词不得机械 Negative。

不得使用 `ACoS 高→自动降 Bid`、`0 单→自动 Pause`、`ACoS 低→自动加 Bid` 的单指标规则；新品核心词不能因短期 ACoS 机械收缩。

## Decision Challenge 与一致性

Initial Judgment 不能直接成为 Final。Final 前必须检查：是否刚修改、归因是否成熟、是否被单日波动误导、是否只看 ACoS、是否忽略 CVR/流量质量、是否忽略原作战任务、603 市场价值、606 Reality Evidence、问题层级和更简单解释。反证推翻初判时必须修改 Final。

完成四层决策后执行 Cross-Level Consistency。Intent 放大与全体 Campaign/Target 收缩、或 Intent 收缩与所有对象放大等冲突，标记 `CROSS_LEVEL_DECISION_CONFLICT`，不得输出互相打架的 Final。

每个重要 Final 必须有 Reason Trace：Judgment、Primary Evidence、Supporting Evidence、Counter Evidence、Hard Constraint、Original Mission、Why Now、Why This Action、Why This Magnitude、Next Observation Condition。用户可见“决策原因”不得使用空话。

## No Action 与批准

`可决策 + 保持` 表示证据足够且主动选择不动；`继续观察 + 继续观察` 表示证据不足、暂不能动。两者不得合并为统一“不调整”。初始确认状态为 `待确认`，6-4 不自动批准自己。只有批准状态的 Decision Package 才能交给 6-5。

每个可执行 Decision 必须有稳定 DecisionId，并绑定 ProductCode、CampaignTag、ObjectType、Amazon Object ID、ActionType、DecisionRunId/Timestamp。6-5 执行前必须比较 ExpectedCurrent 与 Live Actual；不一致即阻断。

## 输出与报告

沿用仓库已锁定的四张决策 CSV Schema，不擅自增列；缺失字段按现有契约留空或标记缺失。每次 Run 的 CSV、HTML、manifest 共用同一 `DecisionRunId` 和时间戳。HTML 必须由同 Run CSV 生成，至少有 Executive Summary、Battle Status、Actions Proposed、No-Action Decisions、Observation Queue、Campaign Decisions、Target Decisions、Search Term Candidates、Decision Challenge、Cross-Level Consistency、Risk/Data Gaps、Approval Queue。

报告目录固定按当前 Skill 正式目录：`06_SKILL分析报告/6-4_广告经营决策/YYYYMMDD_HHMMSS/`；文件以 `6-4_` 开头并带同一时间戳。历史包保留，不跨 ProductCode、CampaignTag 或 Run 拼接。

## 异常

关键异常至少包括：`DECISION_INPUT_NOT_FOUND`、`DECISION_DATA_GAP`、`PLAN_LINEAGE_MISSING`、`RUNTIME_SCOPE_MISMATCH`、`SCOPE_CONTAMINATION`、`ATTRIBUTION_NOT_MATURE`、`EVIDENCE_NOT_MATURE`、`HISTORY_JOIN_FAILED`、`EXECUTION_HISTORY_MISSING`、`CROSS_LEVEL_DECISION_CONFLICT`、`EXPECTED_CURRENT_MISSING`、`DECISION_IDENTITY_INVALID`、`DECISION_PACKAGE_INCOMPLETE`、`REASON_TRACE_MISSING`。关键错误不得 FULL_SUCCESS。
