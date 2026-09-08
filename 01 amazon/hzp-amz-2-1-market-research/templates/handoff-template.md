# HZP AMAZON SKILL HANDOFF

> 这是给下游 Skill 读取的浓缩接口，不是聊天记录，也不是 HTML 报告副本。只保留会影响下一阶段判断的信息。每条陈述必须使用一个证据状态标签：`[FACT]`、`[INFERENCE]`、`[TO-VERIFY]` 或 `[DECISION]`。

## Metadata

- Current Product Code: `[FACT] <产品项目根目录 PRODUCT.md 中的当前 Product Code>`
- Previous Product Code: `[FACT] <如有代码迁移则填写；没有时写 未确认/不适用>`
- Product Code History: `[FACT] <相对于 PRODUCT.md 的代码历史摘要；没有时写 无>`
- Current Stage: `[FACT] 2-1`
- Product Status: `[FACT] ACTIVE / WAITING / HOLD / COMPLETED / CANCELLED`
- ASIN: `[FACT] <ASIN；无法确认时写 未确认>`
- Product Name: `[FACT] <产品名称；来源或用户确认>`
- Marketplace: `[FACT] Amazon US`
- Source Skill: `[FACT] hzp-amz-2-1-market-research`
- Source Skill Name: `[FACT] HZP Amazon 2-1｜产品市场分析`
- Generated Date: `[FACT] <YYYY-MM-DD>`
- Version: `[FACT] <整数版本，例如 1>`
- Status: `[FACT] CURRENT`
- Supersedes: `[FACT] <Version N 或 无>`
- Next Recommended Skill: `[INFERENCE] 3-1 Product Development（Skill：hzp-amz-3-1-product-development；若 HZP 明确确认，再标记为 [DECISION]）`

## Decision

- 当前阶段结论: `[INFERENCE] GO / CONDITIONAL GO / NO-GO / HOLD`
- 结论依据: `[INFERENCE] <一句话说明；不要把 AI 推断写成已确认决策>`
- HZP/QMT 已确认决策: `<有明确确认时使用 [DECISION]；没有则使用 [TO-VERIFY] 未确认>`

## Confirmed Facts

- `[FACT] <仅写来源文件、Amazon 页面或用户确认直接支持的事实>`

## Key Findings

- `[INFERENCE] <市场、需求、竞争、评论和页面证据形成的关键结论>`

## Requirements For Next Stage

- 目标消费者: `[FACT] / [INFERENCE] <用户群>`
- 核心使用场景: `[FACT] / [INFERENCE] <场景>`
- JTBD / 母需求: `[INFERENCE] <用户要完成的任务>`
- 产品要求与约束: `[FACT] / [INFERENCE] / [TO-VERIFY] <只写会影响开发的要求>`
- 目标价格带: `[FACT] / [INFERENCE] / [TO-VERIFY] <有证据才填写>`
- P0 必须解决: `[INFERENCE] / [TO-VERIFY] <要求和证据>`
- P1 重要差异化: `[INFERENCE] / [TO-VERIFY] <要求和证据>`
- P2 加分项: `[INFERENCE] / [TO-VERIFY] <要求和证据>`
- 不建议做 / 避免过度承诺: `[INFERENCE] / [TO-VERIFY] <边界>`
- Product Definition V1: `[INFERENCE] <产品概念、核心承诺、目标用户、场景和验证前提的浓缩版本>`

## Active Cross-Stage Requirements

- `[MANUAL-REQ] <只写状态为 ACTIVE 或 TO-VERIFY、且会影响后续阶段的人工要求；保留内容、提出人、日期、适用阶段和状态>`

## Risks

- `[FACT] / [INFERENCE] / [TO-VERIFY] <已观察或推断的主要风险>`

## Unknowns

- `[TO-VERIFY] <当前仍不知道、不能假设的信息>`

## Validation Required

- `[TO-VERIFY] <下一阶段必须验证的问题、方法和通过标准>`

## User / QMT / Supplier Decisions Required

- `[TO-VERIFY] <需要 HZP、QMT、供应商或其他负责人确认的事项>`

## Source Files

- `[FACT] <相对于产品项目根目录的原始文件路径、报告路径、数据日期和用途，例如 0-source/... 或 2-1-market-research/...>`
- Manual Requirements: `[FACT] MANUAL_REQUIREMENTS.md（如不存在则写 不存在）`
- Decisions: `[FACT] DECISIONS.md（如不存在则写 不存在）`

## Next Stage Instructions

- 继承: `[DECISION] / [FACT] <下一 Skill 必须继续使用的身份、事实、需求、约束和已确认决策>`
- 不要重新假设: `[FACT] <不得把推断或待验证项当作事实，也不得重新拼接不同 ASIN 的数据>`
- 优先解决: `[TO-VERIFY] <按 P0、风险和验证阻塞项排序>`
- 仅为推断: `[INFERENCE] <明确哪些结论来自分析而非直接数据>`
- 必须重新验证: `[TO-VERIFY] <技术参数、成本、合规、耐久、供应商能力和其他需新证据确认的事项>`

## Exit Gate

- Result: `READY FOR NEXT STAGE` / `NOT READY`
- Reason: `[FACT] / [INFERENCE] / [TO-VERIFY] <说明 HANDOFF、证据和决策是否足以进入下一阶段>`

### Conflict update format

当新证据改变上游结论时，必须保留变更链：

```text
上游结论: [INFERENCE] <原结论>
新证据: [FACT] <新数据、测试、供应商确认或 HZP/QMT 决策>
为什么修改: [INFERENCE] <冲突如何被解释>
新结论: [INFERENCE] / [DECISION] <更新后的结论及其状态>
```
