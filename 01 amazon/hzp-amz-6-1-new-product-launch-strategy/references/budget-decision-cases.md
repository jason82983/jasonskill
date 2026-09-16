> **Legacy strategic reference:** 6-0-5 is the sole PLAN authority and 6-1 only applies its latest approved plan. This file may retain historical planning examples; those examples do not authorize 6-1 to choose or expand Intent, Target, lifecycle, Launch Goal, or budget strategy. Follow `approved-battle-plan.md` and `execution-reconciliation.md` for current behavior.

# 6-1 预算决策 CASE K-R

这些用例只验证预算决策方向，不替代真实产品数据核验。

| CASE | 输入条件 | 预期处理 |
|---|---|---|
| K | 无人工预算，市场普通、证据一般 | 形成 AI 判断；可采用约 `$100/day` Fallback，但说明证据、置信度和待补数据。 |
| L | Benchmark 销量低、CPC 高、毛利低 | 主动建议低于 `$100/day` 或只做小规模验证；必要时建议暂不 Launch。 |
| M | Benchmark 销量高、市场大、Own CVR 强、库存足 | 允许建议高于 `$100/day`，同时列出资本依据、最大风险和释放门槛。 |
| N | 用户明确最大 `$80/day` | 标记 `[人工明确约束]`，不得突破 `$80/day`。 |
| O | 目标快速强攻但预算只有 `$20/day` | 输出 `[目标与预算约束冲突]`，说明当前预算无法合理支持的目标。 |
| P | 推荐总 Launch Budget `$3,000`，Phase 1 只释放 `$500` | 先只释放 `$500`；负向证据充分时停止，不因余额继续烧钱。 |
| Q | 前期 ACoS 高，但重复成交词、排名和自然单形成 | 不只按 ACoS 判失败；综合 Launch Asset Return 和经济边界决定是否继续。 |
| R | 广告亏损且无成交词/排名/自然单，市场容量也有限 | 不以“新品期”为理由继续投入；建议停止或回退。 |
