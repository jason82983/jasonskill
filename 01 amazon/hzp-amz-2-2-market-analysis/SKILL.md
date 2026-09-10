---
name: hzp-amz-2-2-market-analysis
description: Run an evidence-based Amazon submarket decision process for a benchmark product. Automatically discover relevant files in the selected Product Root, execute the seven formally defined analysis stages continuously, and produce a Chinese HTML report with a final market-entry decision and downstream handoff context.
---

# HZP Amazon 2-2｜细分市场分析

## 核心任务

2-2 回答一个商业问题：

> 对标产品背后的真实 Amazon 市场，是否值得进入，以及是否存在明确、可验证的产品切入机会？

所有数据、指标和图表都服务于这个问题。阶段是分析组织方式，不能把旧指标平铺成互不相关的结论。

## 七阶段决策链

固定顺序为：

1. **市场定义与范围确认**：我们到底在分析哪个真实市场？
2. **真实市场需求验证**：市场是否存在足够真实、持续的消费者需求？【已正式设计】
3. **市场商业价值判断**：是否具有值得进入的销售与利润空间？【已正式设计】
4. **竞争强度与进入难度判断**：新产品有没有进入空间？【已正式设计】
5. **消费者未满足需求分析**：消费者真正不满意什么？【已正式设计】
6. **产品切入机会验证**：拟议改良是否对应市场需求并有商业意义？【已正式设计】
7. **市场进入决策**：综合前六阶段形成 GO / CONDITIONAL GO / NO-GO。【已正式设计】

完整因果链：市场定义 → 真实需求 → 商业价值 → 竞争难度 → 未满足需求 → 产品切入机会 → 市场进入决策。

## 正式运行方式：自动连续执行

用户通常只需提供 Skill、产品编号和 Products Root。运行时不要把阶段 Gate 当作用户交互步骤，也不要要求用户回复“通过”“继续”或“下一项”。

按以下顺序自动完成：

1. 识别并锁定 Products Root、Product Root 和 Product Code；
2. 读取当前 Product Root 的 `01_产品档案.md`，确认 Product Code、产品中文名称、对标 ASIN、已有角色和研究对象；产品中文名称不得根据 ASIN、Niche、文件名或经验猜测；
3. 只在当前 Product Root 内主动扫描 `05_分析源数据/` 的标准目录：`01_产品数据`、`02_细分市场数据`、`03_关键词数据`、`04_用户反馈`、`05_补充资料`；
4. 根据实际字段、内容和数据日期识别文件类型、ASIN、Niche、搜索词、头部商品、评论、退货、H10/Cerebro 和 Opportunity Explorer 证据；文件名只作线索；
5. 执行已经正式定义的阶段 1；
6. 执行已经正式定义的阶段 2（详见 [references/stage-2-real-demand-validation.md](references/stage-2-real-demand-validation.md)），按实际字段完成五项真实需求验证；
7. 执行已经正式定义的阶段 3（详见 [references/stage-3-commercial-value.md](references/stage-3-commercial-value.md)），按实际字段完成五项商业价值判断；
8. 执行已经正式定义的阶段 4（详见 [references/stage-4-competition-entry-difficulty.md](references/stage-4-competition-entry-difficulty.md)），按实际字段完成六项竞争强度与进入难度判断，并建立竞争壁垒地图和最低进入条件；
9. 执行已经正式定义的阶段 5（详见 [references/stage-5-unmet-consumer-needs.md](references/stage-5-unmet-consumer-needs.md)），完成六项消费者未满足需求分析；
10. 执行已经正式定义的阶段 6（详见 [references/stage-6-product-entry-opportunity.md](references/stage-6-product-entry-opportunity.md)），从阶段 5 的 P0/P1 未满足需求验证产品切入机会；
11. 执行已经正式定义的阶段 7（详见 [references/stage-7-market-entry-decision.md](references/stage-7-market-entry-decision.md)），综合阶段 1–6 形成最终市场进入决策；
12. 依据 [references/legacy-analysis-components.md](references/legacy-analysis-components.md) 选择仍然适用且有数据支持的旧组件作为辅助证据，连续完成当前版本能安全完成的市场分析；
13. 生成当前版本的正式 HTML 报告，并在报告中标明七阶段决策总览、最终决策和实际证据；
14. 正式 HTML 成功落盘后，调用 `$hzp-amz-0-2-report-index`，原样传递同一次运行锁定的 Product Code、Products Root、Product Root。

不要无目的扫描整块硬盘，不要等待用户逐个指定 CSV、H10、Niche 或评论文件。

当导出 CSV 与截图/页面中的列语义冲突时，优先采用带有明确列标题的截图/页面口径，并把“商品点击量”和“搜索量”分别记录；不得把一个字段替换为另一个字段，也不得用旧字段推导未提供的市场份额。报告须标明实际采用的截图或页面文件及数据日期。

任何指标进入分析前必须完成“源文件定位 → 实际字段和值 → 原始字段名 → 字段含义 → 时间窗口/数据日期 → 统计对象和层级”的核验；无法确认时标记 `[字段含义待验证]`，不得进入关键计算或强结论。搜索量、商品点击量、市场点击量、搜索转化率、点击份额、商品/品牌点击份额和退货率含义不同，不得混用。

## 内部检查点与停止条件

Gate 只用于 AI 内部检查证据完整性和分析顺序，不用于暂停用户。每个已执行阶段或辅助分析项目都记录：实际数据、来源、过程、结论、证据状态和局限，然后自动进入下一个可执行项目。

可记录的 Gate 状态为：`【通过】`、`【有条件通过】`、`【证据不足】`、`【存在数据冲突】`。正常的非关键缺失使用 `【证据不足】` 或 `【待验证】` 标记并继续，不输出 `【等待用户确认】`。

只有以下情况才停止并要求补数据或澄清：

- Products Root、Product Root 或 Product Code 无法唯一确定；
- `01_产品档案.md` 中的产品代码或产品名称与当前 Product Root 身份发生冲突；必须输出 `[产品身份冲突]` 并说明冲突字段，不得自行选择；
- 对标 ASIN 身份发生无法消解的冲突；
- 没有任何可验证的对标市场关系，导致市场对象无法确认；
- 读取权限或文件损坏使核心证据无法安全解析。

其他缺失不得阻止报告：继续完成有证据支持的项目，在相应位置写明缺少什么、影响什么，并使用 `[数据不足]`、`[待验证]`、`[证据不足]` 或 `[数据冲突]`。如果 Product Code 已确认但 `01_产品档案.md` 没有产品中文名称，允许显示“产品：<Product Code> [产品名称缺失]”，并标记数据缺失；不编造名称、数字或参数。

## 当前正式定义：阶段 1｜市场定义与范围确认

阶段 1 的方法不变，详见 [references/stage-1-market-definition.md](references/stage-1-market-definition.md)。它负责确认：

`Benchmark 产品本质 → 候选市场池 → Benchmark 的 Niche 归属 → 主要竞品 Niche 归属 → Niche 头部商品 → Niche 搜索词/搜索意图 → 市场交叉验证 → 市场角色分类 → Primary Market`

阶段 1 必须输出 Benchmark 产品本质、候选市场池、交叉验证、搜索意图、主进入市场/相邻市场/排除市场、Primary Market 一句话结论、证据局限，并把结果写入研究状态。阶段 1 完成后直接进入已正式定义的阶段 2、阶段 3、阶段 4 和阶段 5，再进入当前版本可执行的辅助分析，不向用户发确认请求。

## 当前正式定义：阶段 2｜真实市场需求验证

阶段 2 的固定方法、字段语义核验、五项分析、证据链、结论标签和报告展示要求详见 [references/stage-2-real-demand-validation.md](references/stage-2-real-demand-validation.md)。阶段 2 在阶段 1 锁定的 Primary Market 上自动连续执行，普通缺失标记后继续；只有核心产品身份、ASIN 或市场对象无法安全确认时才停止。

阶段 2 只验证真实需求，不回答商业价值、竞争强度、消费者未满足需求、产品切入机会或最终 GO / NO-GO；竞品数量、需求竞争比、集中度、评论壁垒、CPC、价格、销售、利润和资金等不进入阶段 2 核心结论。Opportunity Explorer「占比数据」的原始 `搜索转化率` 才能作为搜索→购买转化字段；市场搜索点击率必须标记 `[推算指标]`，退货率不得代替搜索转化率。

## 当前正式定义：阶段 3｜市场商业价值判断

阶段 3 的固定方法、五项分析、成本缺失边界、项目商业目标规则和结论等级详见 [references/stage-3-commercial-value.md](references/stage-3-commercial-value.md)。阶段 3 在阶段 1、阶段 2 完成后自动执行，不等待用户确认；普通缺失继续标记，不能用 BSR、价格或行业平均成本制造精确结论。

阶段 3 只判断市场商业价值与本产品利润空间，不提前正式判断竞争强度、评论/品牌壁垒、广告/CPC、点击集中度或最终 GO / NO-GO。阶段 4 的正式方法详见 [references/stage-4-competition-entry-difficulty.md](references/stage-4-competition-entry-difficulty.md)；阶段 5 按 [references/stage-5-unmet-consumer-needs.md](references/stage-5-unmet-consumer-needs.md) 执行，阶段 6 按 [references/stage-6-product-entry-opportunity.md](references/stage-6-product-entry-opportunity.md) 执行，阶段 7 按 [references/stage-7-market-entry-decision.md](references/stage-7-market-entry-decision.md) 执行。辅助组件可以提供数据证据和当前版本的补充判断，但不能替代已正式定义的七阶段方法。

## 当前正式定义：阶段 4｜竞争强度与进入难度判断

阶段 4 的固定方法、六项竞争分析、H10 三档搜索流量竞争、竞争壁垒地图、最低进入条件和证据边界详见 [references/stage-4-competition-entry-difficulty.md](references/stage-4-competition-entry-difficulty.md)。阶段 4 在阶段 1–3 完成后自动执行，不等待用户确认；普通缺失继续标记，不能用经验值、BSR 或人为评分补齐。

阶段 4.1–4.3 分别判断商品竞争集中度、品牌竞争集中度和头部产品壁垒；阶段 4.4 正式承接原“1 市场需求竞争比”，必须保留自然排名 1–5、1–10、1–50 三档和 `[HZP推算指标]` 标签；阶段 4.5 判断新品进入难度并形成最低进入条件；阶段 4.6 判断广告与付费流量压力，严格区分 H10 建议竞价、实际 CPC、ACoS 与广告盈利能力。商品/品牌点击份额只能判断流量集中度，不能写成销售额集中度。阶段 5、阶段 6、阶段 7 按各自正式规则继续执行。

## 当前正式定义：阶段 5｜消费者未满足需求分析

阶段 5 的固定方法、证据链、六项分析、P0/P1/P2 优先级、未满足需求地图、真实评论引用、退货边界、商业信号和 HTML 展示要求详见 [references/stage-5-unmet-consumer-needs.md](references/stage-5-unmet-consumer-needs.md)。阶段 5 在阶段 1–4 完成后自动执行，不等待用户确认；普通缺失继续标记，只有核心身份、市场对象或证据无法安全解析时才停止。

阶段 5 只判断消费者需求是否仍未被充分满足，不直接设计产品规格或方案，也不输出最终 GO / CONDITIONAL GO / NO-GO。阶段 6 按 [references/stage-6-product-entry-opportunity.md](references/stage-6-product-entry-opportunity.md) 执行，阶段 7 按 [references/stage-7-market-entry-decision.md](references/stage-7-market-entry-decision.md) 执行。

## 当前正式定义：阶段 6｜产品切入机会验证

阶段 6 的固定方法、六项分析、产品化可行性、可超越程度、消费者可感知性、购买理由、工程/供应链风险、《产品切入机会池》《产品切入机会地图》、Top 1–3 筛选、假机会检查和关键验证项详见 [references/stage-6-product-entry-opportunity.md](references/stage-6-product-entry-opportunity.md)。阶段 6 只承接阶段 5 的 P0/P1 未满足需求，不从零脑暴创意，不完成详细产品工程设计，也不输出最终 GO / CONDITIONAL GO / NO-GO。阶段 7 按 [references/stage-7-market-entry-decision.md](references/stage-7-market-entry-decision.md) 执行。

## 当前正式定义：阶段 7｜市场进入决策

阶段 7 的固定方法、六阶段决策总览、硬否决检查、GO / CONDITIONAL GO / NO-GO / INSUFFICIENT EVIDENCE 规则、正反方检查、市场进入决策书和下一步行动规则详见 [references/stage-7-market-entry-decision.md](references/stage-7-market-entry-decision.md)。阶段 7 只继承并裁决阶段 1–6 已有证据，不重新发明评分模型或静默修改前序结论。

## 产品项目与主动数据发现

优先使用用户提供的 Products Root、Product Root 和产品编号；否则按 [references/data-location-map.md](references/data-location-map.md) 从当前目录向上定位。产品上下文在一次运行中只确认一次，后续不得重新猜测、替换或搜索其他产品目录。

## 产品身份与正式报告显示

从已锁定 Product Root 的 `01_产品档案.md` 读取并保存 Product Code 与产品中文名称。正式 HTML 的主标题必须显示“细分市场分析｜<产品代码> <产品中文名称>”；顶部身份字段必须使用中文“产品：<产品代码> <产品中文名称>”，并将 `Benchmark ASIN` 显示为“对标产品 ASIN”。产品名称缺失时显示“产品：<产品代码> [产品名称缺失]”，同时标记数据缺失。任何代码/名称冲突都触发 `[产品身份冲突]`，停止正式报告生成。

标准相对目录包括：

- `05_分析源数据/01_产品数据/`：Benchmark、竞品和头部 ASIN 资料；
- `05_分析源数据/02_细分市场数据/所有细分市场/`：ASIN→Niche 发现；
- `05_分析源数据/02_细分市场数据/[Niche]/`：候选 Niche 的商品、搜索词和反馈证据；
- `05_分析源数据/03_关键词数据/`、`04_用户反馈/`、`05_补充资料/`：按商业问题需要读取。

对每个候选文件先读取字段、内容和日期，再判断它能够支持什么结论。原始资料只读，不修改、删除、移动或复制。

## 证据与冲突

材料性陈述必须标注：`[数据支持]`、`[分析推断]`、`[待验证]`、`[证据不足]`、`[数据冲突]`。`[分析推断]` 不得自动升级为事实，`[待验证]` 不得当作已确认参数。

若上游结论与新证据冲突，明确列出上游结论、新证据、修改原因和新结论。Amazon Niche 是市场证据，不等于自动目标市场；产品名称、材质词、泛需求或单个搜索交叉不能单独决定 Primary Market。

## 研究状态与续跑

每次运行把锁定的上下文和当前进度保存到：

```text
06_SKILL分析报告/2-2_细分市场分析/2-2_[产品编号]_RESEARCH_STATE.md
```

状态文件记录 Product Code、Products Root、Product Root、Benchmark ASIN、当前阶段、已完成阶段、辅助分析项目、结论、市场角色、缺失数据、冲突和报告状态；不写入 `01_产品档案.md` 或原始数据目录。再次运行先读取并核对同一产品上下文，状态冲突时停止。

## 正式 HTML 与 0-2 接口

当前版本完成七个已定义阶段和可用辅助分析后，直接生成正式 HTML：

```text
06_SKILL分析报告/2-2_细分市场分析/2-2_[产品编号]_细分市场分析_V[版本号]_[YYYYMMDD]_[HHMMSS].html
```

报告必须显示当前 2-2 框架版本、阶段 1–7 结论、六阶段决策总览、硬否决检查、正反方检查、最终裁决逻辑、市场进入决策书、阶段 5 的消费者未满足需求地图与证据、阶段 6 的产品切入机会池/地图与验证项、实际使用的数据与证据、辅助分析标识及缺失/冲突说明。

正式 HTML 成功生成并确认文件存在后，调用 `$hzp-amz-0-2-report-index`，传递本次运行已锁定的 Product Code、Products Root、Product Root。2-2 不生成、不扫描、不维护 `index.html`；索引实现唯一归 0-2。报告失败不调用 0-2；0-2 失败时保留正式报告并分别报告两项状态。

## 当前边界

本次只增量正式加入阶段 7｜市场进入决策；不重新设计阶段 1–6，不修改 2-1、0-1、0-2、原始数据或产品目录结构。
