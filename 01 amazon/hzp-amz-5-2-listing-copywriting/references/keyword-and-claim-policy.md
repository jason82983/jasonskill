# 5-2 关键词与 Claim 规则

## 关键词使用地图字段

| 字段 | 要求 |
|---|---|
| Keyword | 保留实际原词，不改写 |
| 中文含义 | 仅作理解辅助 |
| 搜索意图 | 由实际字段、上下文和产品相关性支持 |
| 数据来源 | 文件名、工作表/字段和日期 |
| 真实指标 | 仅列数据中实际存在的值 |
| 角色 | 核心产品词、购买意图、场景、属性、问题、长尾等 |
| 推荐位置 | Title、Bullet、Description、A+、后台或不建议 |
| 原词/变体 | 说明是否必须原词出现、是否可自然变体 |
| 风险/备注 | 相关性、品牌、政策和证据限制 |

文件名只能帮助发现候选文件；必须核对字段语义、数据日期和站点。缺少指标时写“未提供”，不写经验数字。

## Title、Item Highlights 与 Keyword Allocation

- 非 Media 类目当前按 Amazon Seller Central 2026-07-27 公告执行：Product Title ≤75 characters（包含空格），Item Highlights ≤125 characters（包含空格）。每次生成必须程序化计算字符数，并显示 `Characters: actual / limit`；超限不得标为最终版本。
- Title 回答“这是什么”；Item Highlights 补充材料、推荐用途或其他比较信息。两者必须联合检查无意义重复、关键词浪费、产品类型、用途、差异、移动端可读性和 Claim 风险。
- Keyword Allocation Map 必须记录原词、中文含义、意图、证据、优先级、推荐字段和状态；不能把所有词塞入 Title，也不能让重要关键词无理由失去 Listing 覆盖。

## Backend Search Terms

后台搜索词优先使用 H10、Cerebro、ABA、SQP、Amazon Search Term、Own historical Search Terms 和 Niche 的实际数据。缺少数据时可以输出语义候选，但必须标记 `[待关键词数据验证]`，不得伪造搜索量、排名、转化、点击份额或购买份额。生成前过滤与 Title/Item Highlights 的无意义重复、词形重复、无关词、竞品品牌/商标、ASIN、未确认材料/功能、夸大词和禁止词。平台当前长度/字节规则未从最新版资料确认时标记 `[需按当前Amazon后台字段规则复核]`。

## Listing Attributes 与 Core Selling Points

Listing Attributes 根据 Product Type 动态选择，字段至少包括 Attribute、Value、Source、Evidence Status、Amazon Use、Missing/Conflict；不得机械套用所有产品相同字段。Core Selling Points 是内部分析模块，使用 P0/P1/P2/P3 分级，必须写 Feature、Consumer Benefit、Reason to Buy、Evidence 和 Recommended Placement，不能与 Amazon Item Highlights 混称。

## Claim—Evidence 字段

每个重要 Claim 记录 Claim、使用位置、消费者价值、来源、证据类型、证据状态、建议表达、风险和最终处理。检查范围覆盖 Title、Item Highlights、Bullets、Description、Backend Search Terms、Attributes、A+ 和视觉/视频交接。状态只能是：`【可直接表达】`、`【建议弱化表达】`、`【需补证据】`、`【禁止表达】`。

表达强度依次受真实产品状态、实测/测试、正式文件、消费者证据、工程/供应商确认、项目主张和 AI 推断约束。`Certified`、`Patented`、`FDA Approved`、`100% Safe`、`Guaranteed`、`Best`、`#1` 等没有对应证据时不得写入正式 Listing。

真实评论引用必须保留原文来源和原意；AI 总结应明确为分析，不得放入引号。竞品品牌词除非有合法适用理由，不进入正式 Listing。
