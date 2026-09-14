# 6-2 诊断框架

进入 SellerSpace 查询前，统一读取 Amazon 行业共享文件 `Amazon产品身份解析规则.md`，从 Products Root 的 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx` 解析唯一 ACTIVE 的 Store + Marketplace + ASIN + SKU，并只读二次验证。身份异常按共享规则处理；本文件不复制身份解析逻辑。

## 版本与窗口

- 读取同一 Product Root 的 `01_产品档案.md`、`04_产品推广思路.md` 和最新有效 6-1 正式报告。
- 版本化文件按 `Product Code + Skill 编号` 匹配，最大 V 优先；同 V 按文件名 `YYYYMMDD_HHMMSS` 最新。不得按 filesystem 时间、目录顺序或 first found 选取。
- 排除 `index.html`、失败、incomplete、invalid、deprecated、draft、preview、temp、test 和非正式报告。有效性不确定时标记 `[上游报告有效性无法确认]`，不静默回退旧版。
- 广告数据必须写明实际窗口和产品阶段；不同窗口不可无说明混比。

## 广告数据发现

主动扫描 `05_分析源数据` 中的 Campaign、Search Term、Targeting、Advertised Product、Placement、Purchased Product、Budget、Keyword、ASIN Targeting 等导出，并检查 `07_产品资料` 的价格、Offer、Review、Rating、库存、Buy Box、页面/价格/促销变化和运营记录。以真实字段为准，不因文件名猜测语义。

## 漏斗断点

先判主要断点：曝光 → 点击 → 转化 → 广告经济性 → 流量规模。

- 无曝光：资格、索引/相关性、状态、Target、Match Type、Budget、Bid、搜索量、库存、Buy Box 和竞争环境。
- 有曝光没点击：意图、主图、Title、价格、Rating、Review、Offer、Placement 和竞争页面。
- 有点击无订单：先区分流量错与页面接不住，再查产品、价格、Review、Offer 和竞争。
- 高 ACoS：按 Campaign 原始目的、流量质量、商业价值、数据量和可放大性解释；不机械降 Bid。
- 赚钱不等于能放量：检查流量规模、曝光份额、Bid/Budget、Organic Rank、页面承接和库存。

## 下钻字段

Campaign、Ad Group、Keyword/Target、Search Term 和 Placement 分层记录实际存在的 Campaign、Match Type、ASIN、Status、Budget、Bid、Impressions、Clicks、CTR、CPC、Spend、Orders、Sales、CVR、ACoS、ROAS。Campaign 平均只能作为入口，必要时必须下钻 Search Term。

## 动作与证据

诊断状态只用 `【证据充分】`、`【初步信号】`、`【证据不足】`。动作优先级是广告优化专用的 `【P0｜立即处理】`、`【P1｜高优先级】`、`【P2｜观察/优化】`；不是产品或页面阶段优先级。

允许动作：暂不调整/继续收集、继续观察、扩大验证、提高/降低 Bid、转 Exact、Negative 候选、暂停、进入页面诊断、进入结构调整、进入资格排查。任何 Bid 或 Budget 动作都要说明要解决的问题和依据。0 订单不自动 Negative；意图错误或证据充分长期无价值才提出 Negative 候选。

不得统一使用 10/20/30 点击停词阈值；结合售价、毛利、CPC、测试目的、关键词价值、样本量和风险承受能力。一次优先只改一个可解释变量；最小问题做最小修改。

## 时间波动与路由

单日波动检查曝光、点击、CPC、Spend、Budget、Search Term、Placement、CVR、Organic、价格、Coupon、Review、库存、Buy Box、页面和竞争变化。严重资格/商品状态异常先标记 `[广告资格待排查]`。多个核心高意图流量同时出现明确 CTR/CVR 承接问题，才标记 `【页面承接问题明显｜返回5-4优化】`；单个词失败不推倒整页。


## 阶段6闭环补充

6-2 必须把一次诊断闭环记录为：真实数据 → AI诊断 → 最小必要动作 → 人工批准/修改/否决 → MCP或人工执行 → 1天/3天/7天复盘。运行日志统一保存到 `06_SKILL分析报告/广告表现汇报优化日志/`，默认不进入 0-2 正式报告索引，也不参与最新版正式报告选择。

- 先输出每日调整状态：`【今天不建议调整】`、`【局部优化】`、`【需要明显调整】`、`【需要重构部分广告】`、`【优先排查广告资格/账户/商品状态】` 或 `【数据不足，继续观察】`。不机械套点击阈值。
- Search Term 生命周期可记录为：候选词 → 探索词 → 首单词 → 重复成交词 → 核心成交词 → 核心排名词 → 自然流量资产；淘汰路径为高曝光无点击、点击无转化、高成本低转化、低相关或错误意图 → 降级/否定/停止。1 点击 1 单不能自动升级为核心词。
- 每个动作使用操作卡：对象、当前数据、问题、建议动作、幅度、原因、预期结果、验证周期、成功/失败标准、风险、是否需要人工批准。动作可为保持、Bid/Budget 调整、Pause/Resume、转 Exact、Negative、Placement 调整或结构调整。
- 默认流程是 AI 读取 → AI 诊断 → AI 建议 → 人工批准/部分批准/修改后批准/否决/延后观察 → MCP或人工执行。没有写入能力时只能输出建议并明确未执行。
- 验证必须比较调整前与调整后，至少覆盖 CPC、CTR、CVR、Orders、Spend、ACoS、Search Term、Keyword、Organic order 和 Rank（有数据时），并标记【调整有效】、【基本有效】、【无明显效果】、【调整错误】或【证据不足】。
- 外部接口按读取/写入能力审计；缺少写入能力时只输出建议并明确未执行，禁止假装完成 Bid、Budget、Pause、Negative 或结构修改。


## Evidence-Gated Keyword Expansion

6-2 先读取 6-1 的 Mother Pool、Semantic/Purchase Intent Clusters、Initial Released Keywords、Held Keywords 与成熟度。没有值得放大的成交语义方向时不扩词。1 Click/1 Order 只能是 `FIRST_ORDER_VALIDATED`；Cluster 升级 `VALIDATED` 必须结合多个相关 Search Terms/重复成交、CVR、CPA、ACoS、相关性、时间、库存和自然证据动态判断，不使用固定死门槛。

验证成功后只回查同方向的 Held Keywords，继续按相关性、意图、Search Volume、Rank、Bid、竞争、覆盖和经济边界筛选 Expansion Batch。每批必须做 Traffic Overlap Check、自动选择 Exact/Phrase/Broad、联动 Added Budget 和 Capital Release，并有批准、验证和停止条件。扩词失败时保留已验证核心、收缩外围，不静默判整个 Cluster 失败。

Auto 新成交 Search Term 可追加到 Mother Pool，标记 `OWN_SEARCH_TERM`；H10 更新追加来源和日期，不覆盖 Own 真实成交历史。扩词提案获用户批准前不得调用写接口，批准后沿用 prepare_change_plan → 比对 → apply_change_plan → Read-Back Verification。
## Portfolio 范围与写入边界

Campaign、Ad Group、Keyword/Target、Search Term 和 Placement 诊断表增加 `Portfolio Name`、`Portfolio ID`、`Portfolio Status`。先验证映射表 `广告组合` 与 SellerSpace 只读 Portfolio，再检查 Campaign 的 Own ASIN/SKU 关系。Portfolio 不匹配可以保留为只读证据，但不得生成可执行写入；扩词、竞品 Product Target 和预算扩展必须继承已验证 Portfolio。

诊断同时沿共享解析器的 `Product_NewCode → Product_Code → Portfolio → Var_Code → Campaign` 关系展开；变体 Child ASIN/SKU 无法唯一映射时只读并标记 `【变体广告身份映射不完整】`，不得跨变体合并或扩展。
