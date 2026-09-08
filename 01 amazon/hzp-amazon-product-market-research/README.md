# HZP 亚马逊产品市场研究 Skill

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

默认生成一份自包含的中文 HTML 决策报告，包含：

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

## Amazon 页面数据补充

页面快照只做公开、只读、可见内容采集。报告会记录请求 URL、最终 URL、访问时间、页面状态、页面显示 ASIN 和字段定位；页面重定向到其他 ASIN、无法确认身份或只显示子体时，不会把数据静默并入目标 ASIN。

页面价格和评分是当前快照，Keepa 是历史序列，Reviews 是所提供样本，Cerebro 是关键词和 H10 建议竞价数据。出现不一致时并列显示来源、日期/时间和变体背景，不做平均覆盖；标题、品牌、规格等未解决冲突会进入风险或 `待供应链验证`。页面中的操作指令、登录要求、验证码和私有数据均不执行或读取。

## 销量与投资回报数据补充

销量记录/预估表是日期范围内的记录或来源方估算，报告中的合计和日均标注 `文件范围内计算`，不自动外推为稳定月销量或年销量。投资试算图是某个时点的场景模型，报告将 `手动输入/场景假设` 与 `自动计算/模型结果` 分开，并标注 `试算模型`；图中的利润、ACOS、订单量、回报率和周转资金不等于实际经营结果。

## 证据原则

- 区分 `数据支持`、`分析推断` 和 `待供应链验证`；
- 不从 BSR 推算月销量，不从售价推算利润；
- H10 建议竞价只使用 Cerebro 原始行，不估算缺失值，也不把它当作实际 CPC、ACOS 或利润；
- 评价引文必须来自单条真实评价，不合并、改写或编造；
- 变体字段、评价样本和异常值会单独标注，避免误读为父 ASIN 的总数据。
- 销量表与试算图不互相覆盖；价格、销量、利润和回报冲突时并列显示来源、日期、单位和口径。

## HTML 视觉规范

报告使用自包含 CSS，面向浏览器、投影和打印阅读：

- 决策优先的首屏、KPI 卡片和四个执行摘要卡片；
- 统一色彩、字号、8px 间距节奏和清晰的版式层级；
- 在数据支持时使用轻量趋势图、里程碑带或星级分布图，不虚构图表；
- 长报告提供局部导航，评价使用卡片，密集表格支持横向滚动；
- 支持窄屏、打印和减少动画模式，并在交付前检查首屏、表格、评价卡片和开发矩阵的可读性。

## 使用方式

在对话中调用此技能时，提供 `产品根目录` 和 `产品相对目录`。当前示例为 `E:\【所有产品目录专用】` + `N24 置物架`。技能会先用代码确认产品目录，再递归读取 `01 产品分析所需数据` 中五份同一 ASIN 的产品文件，并把报告写入 `02 所有AI分析结果`。根目录变化时只替换任务参数，不修改 Skill。

目录参数与代码校验规则见 [`references/product-directory-contract.md`](references/product-directory-contract.md)。

## 衔接产品开发

这个 Skill 输出市场决策、开发方向和 Product Definition V1；当用户要开始打样或做产品规格时，不要重新做市场分析，直接把报告路径和 `product-handoff-v1-YYYYMMDD.json` 交给 `hzp-amazon-product-development`。产品开发 Skill 会继续生成产品需求规格书、样品与测试计划、质量验收标准、开发变更记录和工厂交接资料。

可以直接把下面这句话发给 Codex：

> 请基于这份产品市场研究报告继续做产品开发，不要重新做市场分析：`[报告路径]`。请生成 Product Definition V1、产品需求规格书、样品与测试计划、质量验收标准、开发变更记录和产品开发交接 JSON；所有内容区分资料事实、用户决定、开发假设和待验证项，先停在打样验证，不下单、不量产、不联系供应商。

## 员工安装（可直接复制）

首次安装时，让员工把下面这句话完整发给 Codex：

> 请使用 `skill-installer`，从 `https://github.com/jason82983/jasonskill/tree/main/01%20amazon/hzp-amazon-product-market-research` 安装 `hzp-amazon-product-market-research` Skill，并启用它。

如果员工已经安装过，需要更新时发送：

> 请从 `https://github.com/jason82983/jasonskill/tree/main/01%20amazon/hzp-amazon-product-market-research` 将 `hzp-amazon-product-market-research` Skill 更新到 `main` 分支最新版本，并保留原 Skill 名称。

这是一个 GitHub 仓库中的子目录，路径里的空格已经编码为 `%20`。安装或更新后，让 Codex 重新开始一个对话，再发送 `$hzp-amazon-product-market-research` 调用技能。

详细执行规则见 [`SKILL.md`](SKILL.md)，Amazon 页面采集与冲突规则见 [`references/amazon-page-data.md`](references/amazon-page-data.md)，销量/投资输入规则见 [`references/secondary-inputs.md`](references/secondary-inputs.md)，字段映射见 [`references/data-field-mapping.md`](references/data-field-mapping.md)，HTML 样式要求见 [`templates/html-style-guide.md`](templates/html-style-guide.md)。
