# HZP Amazon 3-1｜产品开发 Skill

这是产品开发阶段的 Skill，负责把 Amazon 产品市场研究结果转成可以打样、测试、改版和交接工厂的开发资料。它与市场研究 Skill 分工明确：市场研究回答“值不值得做”，本 Skill 回答“产品具体做成什么，以及如何验证”。

## 什么时候使用

- 已经有产品市场研究报告，需要继续做产品开发；
- 要把评论、退货、Q&A 或竞品缺陷转成产品改进；
- 要建立 Product Definition V1、产品需求规格书、样品计划或质量标准；
- 要评审样品，决定继续打样、改版、暂缓或停止；
- 要准备供应商/工厂交接资料。

## 与市场研究 Skill 的衔接

在通过产品项目根目录的 `PRODUCT.md` 读取 Current Product Code 后，如果 `2-1-market-research/2-1-[ProductCode]_HANDOFF.md` 存在，启动时必须先读取它；如果当前代码文件不存在但记录了 Previous Product Code，只查找并验证对应的旧代码 HANDOFF。随后检查可选的 `MANUAL_REQUIREMENTS.md` 和 `DECISIONS.md`，再按需读取 2-1 HTML 报告和 `0-source/` 原始资料。HANDOFF 是快速恢复上下文的标准接口，原始资料仍用于核实具体参数，不能只凭 HANDOFF 或人工要求编造技术规格。所有引用使用相对于产品项目根目录的路径。

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

> 请在当前产品项目中先读取 `PRODUCT.md`，确认 Current Product Code，再读取 `2-1-market-research/2-1-[ProductCode]_HANDOFF.md`；随后读取适用的 `MANUAL_REQUIREMENTS.md`，按需核对市场研究报告和 `0-source/` 原始资料，不要重新做完整市场分析。请生成 Product Definition V2、产品需求规格书、样品与测试计划、质量验收标准、开发变更记录和 `3-1-[ProductCode]_HANDOFF.md`；所有内容区分 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]`、`[DECISION]`、`[MANUAL-REQ]`，先停在打样验证，不下单、不量产、不联系供应商。

## 默认输出

在产品项目的 `3-1-product-development/` 中生成。任务开始时把当前工作目录切换到产品项目内任意位置，或明确提供项目目录；Skill 会向上搜索 `PRODUCT.md`，读取 Current Product Code、Current Stage 和生命周期 Status，检查可选的 `MANUAL_REQUIREMENTS.md` 与 `DECISIONS.md`，再递归读取 `0-source/` 和上游阶段资料。找不到 `PRODUCT.md`、Current Product Code 或 `0-source/` 时停止并请用户补齐，不猜测根目录，也不依赖员工电脑的盘符。阶段目录缺失时只创建 `3-1-product-development/`。

输出文件包括（正式输出统一以 `3-1-` 开头）：

1. `3-1-[ProductCode]_产品开发方案.html`（Human Report）
2. `3-1-[ProductCode]_产品需求规格书-vN-YYYYMMDD.md`
3. `3-1-[ProductCode]_样品与测试计划-vN-YYYYMMDD.md`
4. `3-1-[ProductCode]_质量验收标准-vN-YYYYMMDD.md`
5. `3-1-[ProductCode]_开发变更记录.md`
6. `3-1-[ProductCode]_HANDOFF.md`（AI Handoff）
7. `3-1-[ProductCode]_product-handoff-vN-YYYYMMDD.json`（兼容性补充）
8. `3-1-[ProductCode]_sources-used.txt`

`[ProductCode]` 始终使用 `PRODUCT.md` 中的 Current Product Code，ASIN 和 Product Name 放在元数据和报告内容中。只询问开发方向时，只生成一份合并结果和对应 HANDOFF，不创建空的占位文件。需要版本时，在扩展名前加入 `-vN-YYYYMMDD`；旧版本保留，不为套用新规则而重命名历史文件。若 N24 后改为 A7，新文件使用 A7，旧 N24 文件通过 Previous Product Code/Product Code History 追溯。

## 3-1 HANDOFF

`3-1-[ProductCode]_HANDOFF.md` 使用 [`templates/handoff-template.md`](templates/handoff-template.md)，是后续 `4-1 Sourcing & Production` 的标准输入，也可供未来 5 页面、6 推广、7 备货 Skill 读取。它必须包含 Product Definition V2、P0/P1/P2、样品要求、验证测试、材料/结构/规格、风险、Unknowns、决策事项、有效的 `Active Cross-Stage Requirements`、相对路径来源和下一阶段指令；不复制完整 HTML。

每条 HANDOFF 信息使用 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]` 或 `[DECISION]` 之一。如果新证据改变 2-1 方向，必须记录“上游结论 → 新证据 → 修改原因 → 新结论”。

正式 HTML 报告标题附近或报告信息区显示来源标识：`HZP Amazon 3-1｜产品开发`。

`PRODUCT.md` 的 `Current Stage` 与生命周期 `Status` 分开。Status 只使用 `ACTIVE`、`WAITING`、`HOLD`、`COMPLETED`、`CANCELLED`；3-1 的开发闸门和结论不替代生命周期状态。`ACTIVE` 才是默认可推进状态，`WAITING` / `HOLD` 需要用户明确要求恢复；Skill 可以建议状态变化，但不能擅自将项目标记为 `COMPLETED` 或 `CANCELLED`。当前 HANDOFF 由 `Latest Handoff` 指向，不根据“最终版”“最新修改版”等文件名猜测；HANDOFF 必须记录 `Version`、`Status: CURRENT`、`Supersedes` 和 `Exit Gate`。

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

人工补充要求文件 `MANUAL_REQUIREMENTS.md` 可以不存在；存在时每条要求至少记录 ID、内容、提出人、提出日期、适用阶段、状态和备注。状态支持 `ACTIVE`、`TO-VERIFY`、`DONE`、`REJECTED`、`SUPERSEDED`；3-1 默认只读取适用的 `ACTIVE` / `TO-VERIFY`，并用 `[MANUAL-REQ]` 标记。冲突时同时展示人工要求、证据/事实、冲突、建议和需要确认的人，只把会影响后续阶段的有效要求摘要进 HANDOFF。

产品项目可以有一个 `DECISIONS.md`，只记录已经确认的重要正式决策，不记录普通建议、聊天或工作日志。3-1 Entry Gate 必须检查相关决策；如果新证据与决策冲突，保留冲突链并标记 `[TO-VERIFY]`，等待授权负责人确认。

`0-source/` 中的原始报价、测试、样品照片、Keepa、Cerebro、Reviews 等 Source Evidence 只读；新版证据另存为新文件，不覆盖历史原件。

### 3-1 Entry Gate

正式开发前必须确认 Product Code、PRODUCT.md、2-1 HANDOFF、2-1 Decision、Product Definition V1、P0/P1/P2、人工要求和相关正式决策均可读取。2-1 为 `NO-GO` 时默认 `BLOCKED`，除非用户明确要求继续研究或推翻上游结论。

### 3-1 Exit Gate

交付前必须确认 Product Definition V2、更新后的 P0/P1/P2、产品解决方案、打样要求、测试计划、风险、Unknowns、HANDOFF 和跨阶段人工要求均已形成。完整交付写 `READY FOR NEXT STAGE`，否则写 `NOT READY`。

便携式产品项目结构、Product Code 历史和人工要求规则见 [`references/product-directory-contract.md`](references/product-directory-contract.md)。详细 HANDOFF 模板见 [`templates/handoff-template.md`](templates/handoff-template.md)，JSON 兼容字段见 [`references/handoff-schema.md`](references/handoff-schema.md)，完整执行规则见 [`SKILL.md`](SKILL.md)。
