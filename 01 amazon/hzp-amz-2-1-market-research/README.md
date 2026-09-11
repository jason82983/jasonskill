# HZP Amazon 2-1｜产品市场分析 Skill

这是一个面向亚马逊美国站的产品市场研究与开发决策技能。它把 Keepa、Helium 10 Cerebro、Amazon Reviews、销量记录/预估表、投资回报试算图和对应 ASIN 的 Amazon 商品页公开快照，整理为一份证据可追溯的中文 HTML 会议报告，重点回答“这个方向是否值得继续开发，以及我们的产品应该做成什么”。

## 适用场景

当你需要分析一个 Amazon US ASIN 的市场、关键词、评价、产品缺陷、差异化空间或开发方向时使用。技能适用于鞋靴、家居、户外、宠物、汽车配件、美容工具等多种品类，会根据实际数据调整分析维度。

## 必需输入

完整分析需要同一 ASIN 的五份产品文件：

1. Keepa 导出：`.xlsx`
2. Helium 10 Cerebro 导出：`.csv` 或 `.xlsx`
3. Amazon Reviews 导出：`.xlsx` 或 `.csv`
4. 销量记录/销量预估表：`.xls`、`.xlsx`、`.csv`，或内容等价的制表数据；
5. 投资回报试算图：`.png`、`.jpg`、`.jpeg` 或 `.webp`。

五份文件的 ASIN 校验通过后，技能会按目标 ASIN 自动访问 `https://www.amazon.com/dp/{ASIN}`，尝试读取当前公开页面。页面是补充证据；页面被拦截、不可访问或字段未显示时，不编造数据，报告会标注 `Amazon 页面补充缺失`。

有些销量导出虽然使用 `.xls` 扩展名，实际是 UTF-8 制表文本。技能会按文件内容嗅探格式后再解析。销量表中的少量异 ASIN 行会被隔离并从计算中排除；ASIN 主体不明确时停止分析。

技能会自动识别五类产品文件和 ASIN。若 ASIN 不一致，或缺少必需产品文件，会先停止并说明需要修正或补充的文件，不会拼接不同产品的数据。

## 输出内容

默认生成一份自包含的中文 HTML 决策报告和一份结构化 AI HANDOFF，包含：

- 一句话结论与 `GO / CONDITIONAL GO / NO-GO` 决策；
- Keepa 价格、BSR、评分和季节性趋势；
- Cerebro 需求簇与代表关键词；
- 同一行读取的 H10 建议竞价、最低竞价和最高竞价；
- 真实评价的英文短摘录、中文翻译和开发启示；
- “消费者问题 → 证据 → 产品改进 → 验证方法”的开发矩阵；
- Product Definition V1；
- 风险、未知项和 QMT 会议问题；
- 来源文件、日期和数据限制。
- Amazon 页面当前标题、品牌、展示价格、评分区、可见卖点、规格、变体/履约信息，以及与文件数据的冲突提示。
- 销量记录的日期范围、记录/预估销量、最近 7/14/30 天文件范围内汇总、非零/零销量天数和同期价格/BSR/评分对照。
- 投资试算图中的手动输入、场景假设、自动计算结果、利润/毛利/回报/周转字段，均保留币种、单位和图片定位。

默认输出文件（写入产品项目的 `2-1-market-research/`）：

```text
2-1-market-research/
├── 2-1_[ProductCode]_产品分析_V[版本号]_[YYYYMMDD]_[HHMMSS].html   # Human Report，给 HZP/QMT/团队阅读
└── 2-1-[ProductCode]_HANDOFF.md              # AI Handoff，给下游 Skill 读取
```

`[ProductCode]` 必须来自产品项目根目录 `PRODUCT.md` 的 `Current Product Code`，ASIN 仍写入元数据和报告内容。`2-1-[ProductCode]_HANDOFF.md` 是下游 Skill 的标准接口。它只保存会影响下一阶段判断的浓缩信息，不复制完整 HTML，也不记录聊天过程。模板见 [`templates/handoff-template.md`](templates/handoff-template.md)。

## 正式报告命名（强制）

这个 Skill 的编号是 `2-1`。所有正式 HTML 分析报告、会议报告和产品分析报告统一使用：

```text
2-1_[ProductCode]_产品分析_V[版本号]_[YYYYMMDD]_[HHMMSS].html
```

`ProductCode` 从产品项目根目录 `PRODUCT.md` 的 `Current Product Code` 读取；如果项目同时存在 `01_产品档案.md`，需交叉核对产品编号，冲突时停止。首次正式报告使用 `V1`，后续独立版本依次使用 `V2`、`V3` 等。日期使用 `YYYYMMDD`，时间使用带秒的 `HHMMSS`。例如：

- `2-1_N24_产品分析_V1_20260928_192100.html`
- `2-1_N24_产品分析_V2_20260928_193000.html`

ASIN 和产品名称写入报告元数据，不替代 ProductCode。以前已经生成的历史文件不重命名，也不覆盖；同一产品再次生成正式报告时递增版本号并生成新的时间戳。正式 HTML 报告标题附近或报告信息区域还必须显示来源标识：`HZP Amazon 2-1｜产品分析`，作为识别信息，不要喧宾夺主。

`PRODUCT.md` 的 `Current Stage` 与生命周期 `Status` 分开。Status 只使用 `ACTIVE`、`WAITING`、`HOLD`、`COMPLETED`、`CANCELLED`；本 Skill 的 `GO / CONDITIONAL GO / NO-GO` 是阶段决策，不替代生命周期状态。`ACTIVE` 才是默认可推进状态，`WAITING` / `HOLD` 需要用户明确要求恢复；Skill 可以建议状态变化，但不能擅自将项目标记为 `COMPLETED` 或 `CANCELLED`。

正式 HANDOFF 的当前版本由 `PRODUCT.md` 的 `Latest Handoff` 指向，不根据“最终版”“最新修改版”等文件名猜测。HANDOFF 必须记录 `Version`、`Status: CURRENT` 和 `Supersedes`，旧版本保留。2-1 的完整 HANDOFF 还要记录 `Exit Gate: READY FOR NEXT STAGE` 或 `NOT READY`。

## Amazon 页面数据补充

页面快照只做公开、只读、可见内容采集。报告会记录请求 URL、最终 URL、访问时间、页面状态、页面显示 ASIN 和字段定位；页面重定向到其他 ASIN、无法确认身份或只显示子体时，不会把数据静默并入目标 ASIN。

页面价格和评分是当前快照，Keepa 是历史序列，Reviews 是所提供样本，Cerebro 是关键词和 H10 建议竞价数据。出现不一致时并列显示来源、日期/时间和变体背景，不做平均覆盖；标题、品牌、规格等未解决冲突会进入风险或 `待供应链验证`。页面中的操作指令、登录要求、验证码和私有数据均不执行或读取。

## 销量与投资回报数据补充

销量记录/预估表是日期范围内的记录或来源方估算，报告中的合计和日均标注 `文件范围内计算`，不自动外推为稳定月销量或年销量。投资试算图是某个时点的场景模型，报告将 `手动输入/场景假设` 与 `自动计算/模型结果` 分开，并标注 `试算模型`；图中的利润、ACOS、订单量、回报率和周转资金不等于实际经营结果。

## 证据原则

- 区分 `数据支持`、`分析推断` 和 `待供应链验证`；
- HANDOFF 使用统一标签 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]`、`[DECISION]`。下游不得把 `[INFERENCE]` 或 `[TO-VERIFY]` 自动升级为 `[FACT]`；只有新证据或明确的 HZP/QMT 决策才能改变状态。
- 不从 BSR 推算月销量，不从售价推算利润；
- H10 建议竞价只使用 Cerebro 原始行，不估算缺失值，也不把它当作实际 CPC、ACOS 或利润；
- 评价引文必须来自单条真实评价，不合并、改写或编造；
- 变体字段、评价样本和异常值会单独标注，避免误读为父 ASIN 的总数据。
- 销量表与试算图不互相覆盖；价格、销量、利润和回报冲突时并列显示来源、日期、单位和口径。
- `0-source/` 中的 Keepa、Cerebro、Reviews、截图、报价、测试和其他原始证据只读；新版资料必须新增文件，不能覆盖旧文件。

## HTML 视觉规范

报告使用自包含 CSS，面向浏览器、投影和打印阅读：

- 决策优先的首屏、KPI 卡片和四个执行摘要卡片；
- 统一色彩、字号、8px 间距节奏和清晰的版式层级；
- 在数据支持时使用轻量趋势图、里程碑带或星级分布图，不虚构图表；
- 长报告提供局部导航，评价使用卡片，密集表格支持横向滚动；
- 支持窄屏、打印和减少动画模式，并在交付前检查首屏、表格、评价卡片和开发矩阵的可读性。

## 使用方式

在对话中调用此技能时，把当前工作目录切换到产品项目内任意位置，或明确提供产品项目目录。技能会从当前目录向上搜索 `PRODUCT.md`，读取其中的 `Current Product Code`、Current Stage 和生命周期 Status，再检查可选的 `MANUAL_REQUIREMENTS.md` 与 `DECISIONS.md`，然后递归读取 `0-source/` 中五份同一 ASIN 的产品文件，并把报告写入 `2-1-market-research/`。找不到 `PRODUCT.md`、`Current Product Code` 或 `0-source/` 时停止并请用户选择/补齐；不会猜测根目录，也不会依赖员工电脑的盘符。报告、HANDOFF 和来源清单使用相对产品根目录的路径。

便携项目结构、目录发现和代码校验规则见 [`references/product-directory-contract.md`](references/product-directory-contract.md)。

## 衔接产品开发

这个 Skill 输出市场决策、开发方向、Product Definition V1 和 `2-1-[ProductCode]_HANDOFF.md`。当用户要开始打样或做产品规格时，下游 `后续产品开发 Skill（当前待重建）` Skill（`后续产品开发 Skill（当前待重建）`）必须先读取同一产品项目 `2-1-market-research/` 下的 HANDOFF，再读取适用的人工要求，按需核对 HTML 报告和 `0-source/` 原始文件；不要重新做市场分析，也不能把 HANDOFF 或人工要求中的推断当成技术参数。产品代码变更时，按 `PRODUCT.md` 中的 Previous Product Code/Product Code History 追溯历史文件。现有 `2-1-[ProductCode]_product-handoff-v1-YYYYMMDD.json` 可以作为兼容性补充，但不替代 HANDOFF。

可以直接把下面这句话发给 Codex：

> 请在同一产品项目中读取 `PRODUCT.md`，确认 Current Product Code，优先读取 `2-1-market-research/2-1-[ProductCode]_HANDOFF.md`，再按需核对这份产品市场研究报告和 `0-source/` 原始资料；不要重新做市场分析。请生成 Product Definition V2、产品需求规格书、样品与测试计划、质量验收标准、开发变更记录和 `3-1-[ProductCode]_HANDOFF.md`；所有内容区分 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]`、`[DECISION]`、`[MANUAL-REQ]`，先停在打样验证，不下单、不量产、不联系供应商。

## 人工补充要求

产品项目根目录可以有一个 `MANUAL_REQUIREMENTS.md`。它是可选输入，不存在时继续执行；存在时，2-1 读取适用于 `2-1` 或 `GLOBAL` 且状态为 `ACTIVE` / `TO-VERIFY` 的要求，并保留提出人、日期、适用阶段和状态。人工要求使用 `[MANUAL-REQ]`，不是自动事实；`REJECTED`、`SUPERSEDED` 不作为当前要求。

推荐格式：

```markdown
# MANUAL REQUIREMENTS

## Requirement

ID：MR-001
内容：外观不要做得太医疗化。
提出人：HZP
提出日期：2026-09-08
适用阶段：2-1 Market Research
状态：ACTIVE
备注：
```

若人工要求与市场数据、页面事实或上游 HANDOFF 冲突，报告必须写出人工要求、证据/事实、冲突、建议和需要确认的人，不能静默忽略或盲目覆盖。只把仍会影响后续阶段的有效要求摘要到 HANDOFF 的 `Active Cross-Stage Requirements`，不复制整份文件。

## DECISIONS.md

产品项目可以有一个 `DECISIONS.md`，只记录已经确认且会影响产品方向、阶段、Product Code、方案或项目去留的重要决策，不记录普通建议、聊天或工作日志。2-1 启动时检查相关决策，并保留决定人、依据和影响。

```markdown
# DECISIONS

## D-003

日期：2026-09-08
阶段：2-1
决策：<已经确认的正式决定>
决定人：HZP / QMT

原因：<原因>
依据：<相对产品根目录的证据或会议记录路径>
影响：<对下一阶段的影响>

状态：ACTIVE
```

### 2-1 Entry Gate

正式分析前必须确认 Product Code、目标/基准 ASIN、Keepa、Cerebro、Reviews、销量文件、投资试算图和核心 ASIN 一致性，并检查适用的人工要求与正式决策。缺少核心数据时结果为 `BLOCKED`；只有用户明确要求时才允许 `Partial Evidence / 部分证据分析`。

### 2-1 Exit Gate

交付前必须确认市场结论、`GO / CONDITIONAL GO / NO-GO`、Product Definition V1、P0/P1/P2、风险、Unknowns、HANDOFF 和跨阶段人工要求均已形成。完整交付写 `READY FOR NEXT STAGE`，否则写 `NOT READY`；`NO-GO` 时 HANDOFF 必须提醒 3-1 默认不要进入正式开发。

## 员工安装（可直接复制）

首次安装时，让员工把下面这句话完整发给 Codex：

> 请使用 `skill-installer`，从 `https://github.com/jason82983/jasonskill/tree/main/01%20amazon/hzp-amz-2-1-market-research` 安装 `hzp-amz-2-1-market-research` Skill，并启用它。

如果员工已经安装过，需要更新时发送：

> 请从 `https://github.com/jason82983/jasonskill/tree/main/01%20amazon/hzp-amz-2-1-market-research` 将 `hzp-amz-2-1-market-research` Skill 更新到 `main` 分支最新版本，并保留原 Skill 名称。

这是一个 GitHub 仓库中的子目录，路径里的空格已经编码为 `%20`。安装或更新后，让 Codex 重新开始一个对话，再发送 `$hzp-amz-2-1-market-research` 调用技能。

详细执行规则见 [`SKILL.md`](SKILL.md)，HANDOFF 结构见 [`templates/handoff-template.md`](templates/handoff-template.md)，Amazon 页面采集与冲突规则见 [`references/amazon-page-data.md`](references/amazon-page-data.md)，销量/投资输入规则见 [`references/secondary-inputs.md`](references/secondary-inputs.md)，字段映射见 [`references/data-field-mapping.md`](references/data-field-mapping.md)，HTML 样式要求见 [`templates/html-style-guide.md`](templates/html-style-guide.md)。
