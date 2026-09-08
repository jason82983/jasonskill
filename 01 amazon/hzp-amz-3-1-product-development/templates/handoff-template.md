# HZP AMAZON SKILL HANDOFF

> 这是给下游 Skill 的精简接口，不是聊天记录，也不是 HTML 报告副本。每条陈述只使用一个证据状态：`[FACT]`、`[INFERENCE]`、`[TO-VERIFY]` 或 `[DECISION]`。

## Metadata

- Current Product Code: `[FACT] <产品项目根目录 PRODUCT.md 中的当前 Product Code>`
- Previous Product Code: `[FACT] <如有代码迁移则填写；没有时写 未确认/不适用>`
- Product Code History: `[FACT] <相对于 PRODUCT.md 的代码历史摘要；没有时写 无>`
- Current Stage: `[FACT] 3-1`
- Product Status: `[FACT] ACTIVE / WAITING / HOLD / COMPLETED / CANCELLED`
- ASIN: `[FACT] <ASIN；没有则写 未确认>`
- Product Name: `[FACT] <产品名称>`
- Marketplace: `[FACT] Amazon US`
- Source Skill: `[FACT] 3-1`
- Source Skill Name: `[FACT] HZP Amazon 3-1｜产品开发`
- Generated Date: `[FACT] <YYYY-MM-DD>`
- Version: `[FACT] <整数版本，例如 1>`
- Status: `[FACT] CURRENT`
- Supersedes: `[FACT] <Version N 或 无>`
- Next Recommended Skill: `[INFERENCE] 4-1 Sourcing & Production`

## Decision

- 当前开发阶段状态: `[INFERENCE] GO / CONDITIONAL GO / HOLD / NO-GO`
- 状态依据: `[INFERENCE] <当前闸门和主要依据>`
- HZP/QMT/负责人已确认决策: `<有明确确认时使用 [DECISION]；没有则使用 [TO-VERIFY] 未确认>`

## Product Definition V2

- `[INFERENCE] <当前最新产品定义；说明相对 V1 的开发变化>`

## Target Customer

- `[FACT] / [INFERENCE] <目标消费者；最终内容只保留一个标签>`

## Use Cases

- `[FACT] / [INFERENCE] <核心使用场景；最终内容只保留一个标签>`

## Confirmed Product Requirements

- `[FACT] / [DECISION] <已经被资料或明确决策确认的要求；最终内容只保留一个标签>`

## P0 Requirements

- `[INFERENCE] / [TO-VERIFY] <必须做到的要求、证据和验证方式；最终内容只保留一个标签>`

## P1 Differentiators

- `[INFERENCE] / [TO-VERIFY] <核心差异化、证据和验证方式；最终内容只保留一个标签>`

## P2 Enhancements

- `[INFERENCE] / [TO-VERIFY] <加分项、证据和验证方式；最终内容只保留一个标签>`

## Active Cross-Stage Requirements

- `[MANUAL-REQ] <只写状态为 ACTIVE 或 TO-VERIFY、且会影响后续阶段的人工要求；保留内容、提出人、日期、适用阶段和状态>`

## Materials / Structure / Specifications

- `[FACT] / [DECISION] <已确认的材料、结构、尺寸、厚度、硬度、工艺或性能；最终内容只保留一个标签>`
- `[TO-VERIFY] <上游没有证据的参数不能自行填写>`

## Sample Requirements

- `[INFERENCE] / [TO-VERIFY] <下一轮样品版本、修改项和通过前提；最终内容只保留一个标签>`

## Validation / Testing

- `[TO-VERIFY] <测试项目、方法、样本量、阈值、负责人、结果和复测规则>`

## Risks

- `[FACT] / [INFERENCE] / [TO-VERIFY] <当前主要产品风险；最终内容只保留一个标签>`

## Unknowns

- `[TO-VERIFY] <仍然未知、不能假设的信息>`

## Decisions Required

- `[TO-VERIFY] <需要 HZP / QMT / 供应商确认的问题、负责人和闸门>`

## Changes From 2-1

如果 3-1 修改了 2-1 的产品方向，必须保留变更链：

```text
上游结论: [INFERENCE] <2-1 原结论>
新证据: [FACT] <新数据、测试、供应商确认或 HZP/QMT 决策>
修改原因: [INFERENCE] <为什么需要修改>
新结论: [INFERENCE] / [DECISION] <最终状态；只保留一个标签>
```

没有修改时写：`[FACT] 未改变 2-1 的产品方向`。

## Source Files

- `[FACT] <上游 2-1 HANDOFF、HTML 报告、本阶段资料的相对产品项目路径、日期和用途，例如 2-1-market-research/...、0-source/...>`
- Manual Requirements: `[FACT] MANUAL_REQUIREMENTS.md（如不存在则写 不存在）`
- Decisions: `[FACT] DECISIONS.md（如不存在则写 不存在）`

## Next Stage Instructions

- 哪些规格已经确认: `[FACT] / [DECISION] <最终内容只保留一个标签>`
- 哪些不能改变: `[DECISION] / [TO-VERIFY] <明确边界；最终内容只保留一个标签>`
- 哪些仍需工厂确认: `[TO-VERIFY] <材料、结构、工艺、成本、MOQ、交期或能力>`
- 哪些需要报价: `[TO-VERIFY] <报价项和币种>`
- 哪些需要生产测试: `[TO-VERIFY] <测试项目和通过标准>`
- 哪些风险必须重点控制: `[FACT] / [INFERENCE] / [TO-VERIFY] <风险与控制点；最终内容只保留一个标签>`

## Exit Gate

- Result: `READY FOR NEXT STAGE` / `NOT READY`
- Reason: `[FACT] / [INFERENCE] / [TO-VERIFY] <说明规格、测试、决策和证据是否足以进入下一阶段>`
