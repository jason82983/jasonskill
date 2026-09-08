# HZP Amazon 3-1｜产品开发 Skill

这是产品开发阶段的 Skill，负责把 Amazon 产品市场研究结果转成可以打样、测试、改版和交接工厂的开发资料。它与市场研究 Skill 分工明确：市场研究回答“值不值得做”，本 Skill 回答“产品具体做成什么，以及如何验证”。

## 什么时候使用

- 已经有产品市场研究报告，需要继续做产品开发；
- 要把评论、退货、Q&A 或竞品缺陷转成产品改进；
- 要建立 Product Definition V1、产品需求规格书、样品计划或质量标准；
- 要评审样品，决定继续打样、改版、暂缓或停止；
- 要准备供应商/工厂交接资料。

## 与市场研究 Skill 的衔接

如果产品目录中存在 `2-1-[ProductID]_HANDOFF.md`，启动时必须先读取它，再按需读取 2-1 HTML 报告和原始资料。HANDOFF 是快速恢复上下文的标准接口，原始资料仍用于核实具体参数，不能只凭 HANDOFF 编造技术规格。

市场研究 HANDOFF 中的内容会这样传入开发阶段：

| 市场研究内容 | 产品开发用途 |
| --- | --- |
| GO / CONDITIONAL GO / NO-GO | 开发闸门和范围 |
| 目标用户、使用场景 | 用户任务和非目标 |
| 评论摘录、痛点和缺陷 | 产品需求、失败模式和改进项 |
| Product Definition V1 | 初版产品定义和需求编号 |
| 开发矩阵 | P0/P1/P2 优先级 |
| 成本、价格和投资试算 | 待验证的成本/价格假设 |
| QMT 问题和未知项 | 供应链问题与测试计划 |

下游必须继承产品身份、市场结论、目标消费者、使用场景、JTBD、关键词需求簇、竞品成功原因、Review 痛点、产品机会、Product Definition V1、P0/P1/P2、价格约束、风险、Unknowns、待验证事项和 QMT/供应链待确认事项。`[INFERENCE]` 不得自动升级为 `[FACT]`，`[TO-VERIFY]` 不得当作已确认。

直接交接时，可以把下面这句话发给 Codex：

> 请先读取同一产品目录中的 `2-1-[ProductID]_HANDOFF.md`，再按需核对市场研究报告和原始资料；不要重新做完整市场分析。请生成 Product Definition V2、产品需求规格书、样品与测试计划、质量验收标准、开发变更记录和 `3-1-[ProductID]_HANDOFF.md`；所有内容区分 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]`、`[DECISION]`，先停在打样验证，不下单、不量产、不联系供应商。

## 默认输出

在确认的产品目录 `02 所有AI分析结果` 中生成。任务开始时必须同时提供产品根目录和产品相对目录，例如：

```text
产品根目录：E:\【所有产品目录专用】
产品相对目录：N24 置物架
```

Skill 会用代码确认 `产品根目录 / 产品相对目录`，递归读取 `01 产品分析所需数据`，然后把开发结果写入 `02 所有AI分析结果`。根目录变化时只替换参数，不改 Skill。

输出文件包括（正式输出统一以 `3-1-` 开头）：

1. `3-1-[ProductID]_产品开发方案.html`（Human Report）
2. `3-1-[ProductID]_产品需求规格书-vN-YYYYMMDD.md`
3. `3-1-[ProductID]_样品与测试计划-vN-YYYYMMDD.md`
4. `3-1-[ProductID]_质量验收标准-vN-YYYYMMDD.md`
5. `3-1-[ProductID]_开发变更记录.md`
6. `3-1-[ProductID]_HANDOFF.md`（AI Handoff）
7. `3-1-[ProductID]_product-handoff-vN-YYYYMMDD.json`（兼容性补充）
8. `3-1-[ProductID]_sources-used.txt`

有 ASIN 时用 ASIN 作为 `[ProductID]`，没有 ASIN 时使用稳定、简短、可识别的 Product ID。只询问开发方向时，只生成一份合并结果和对应 HANDOFF，不创建空的占位文件。需要版本时，在扩展名前加入 `-vN-YYYYMMDD`；旧版本保留，不为套用新规则而重命名历史文件。

## 3-1 HANDOFF

`3-1-[ProductID]_HANDOFF.md` 使用 [`templates/handoff-template.md`](templates/handoff-template.md)，是后续 `4-1 Sourcing & Production` 的标准输入，也可供未来 5 页面、6 推广、7 备货 Skill 读取。它必须包含 Product Definition V2、P0/P1/P2、样品要求、验证测试、材料/结构/规格、风险、Unknowns、决策事项、相对路径来源和下一阶段指令；不复制完整 HTML。

每条 HANDOFF 信息使用 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]` 或 `[DECISION]` 之一。如果新证据改变 2-1 方向，必须记录“上游结论 → 新证据 → 修改原因 → 新结论”。

正式 HTML 报告标题附近或报告信息区显示来源标识：`HZP Amazon 3-1｜产品开发`。

## 当前产品的重点

以大理石置物架为例，开发阶段应优先验证：

- 包装跌落、振动和边角保护；
- 泡沫能否无工具顺利取出；
- 产品重量、包装尺寸和实际履约成本；
- 双层结构稳定性、防滑和承重；
- 天然纹理、色差、边缘抛光和外观缺陷标准；
- 价格、实际成本、破损率和退货损耗是否支持原来的市场判断。

投资试算图只能作为场景模型，不能直接当作实际利润或量产预算。

## 边界

本 Skill 不会在没有单独授权的情况下下单、批准模具或量产、联系工厂、发布 Listing、启动广告或修改线上账户。材料性能、承重、防水、合规、专利和认证必须通过相应证据、测试或专业审核确认。

详细 HANDOFF 模板见 [`templates/handoff-template.md`](templates/handoff-template.md)，JSON 兼容字段见 [`references/handoff-schema.md`](references/handoff-schema.md)，完整执行规则见 [`SKILL.md`](SKILL.md)。
