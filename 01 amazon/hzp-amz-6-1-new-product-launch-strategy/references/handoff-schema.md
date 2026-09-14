# 6-2 输入交接包字段

正式报告在满足页面状态门并形成可执行或受控小规模验证方案时，生成《6-2输入交接包》。它不是广告优化结果，而是未来诊断所需的原始上下文。

至少包括：

- 产品身份、Product Code、Product Root、Marketplace；身份主表映射来源、SellerSpace Store、`own_asin`、SKU、`Status`、MCP 二次验证状态和任何冲突标签；单独列出 `benchmark_asin` 及其市场研究用途
- 6-1 正式报告文件名、版本和生成时间
- 运行模式（Pipeline Mode 或 Direct Launch Mode）；如实际读取 5-4，再记录其输入报告及最终状态；未读取时明确标记“无 5-4 输入”，不得虚构
- Direct Launch Mode 的最低必要推广前检查结果（身份、Listing/可售、页面最低承接、库存、经济边界）
- Launch Goal、目标来源（人工目标或系统默认目标）、Launch Window、Standard/Accelerated/Seasonal Sprint 判断和季节性状态
- 库存目标、每日/周期预算约束、最大允许投入/亏损、经济边界状态
- 当前阶段、阶段开始日期、阶段目标、验证标准、晋级/提前晋级、延长、加速、停止/回退标准
- 《6-1 新品广告初始化预案》摘要及战略审批状态；
- Approved Creation Blueprint 摘要：Executive Approval View、Campaign 总览、Initial Budget/Keyword Allocation、Creation Readiness 和完整清单路径；明确战略审批与初始广告创建授权合并的条件：完整创建清单展示后用户明确批准；批准前不写入，批准后仅创建清单内新广告
- 当前推广状态和预算/库存约束
- 新品推广核心战略与核心消费者
- 核心购买理由、页面 P0/P1/P2、核心差异化
- 关键词、关键词角色、证据状态和流量—页面承接关系
- 每个 Campaign/Ad Group 的类型、投放对象、目的、对应假设、Bid 来源、预算逻辑、继续/暂停条件
- 当前价格、Coupon/Promotion/Vine 状态；没有资料则标记待确认
- Break-even ACoS（只有真实成本充分时）
- 每个假设的成功信号、失败信号和预计需要收集的数据
- 未来 6-2 要重点诊断的无曝光、点击贵、点击无单、ACoS、搜索词、流量质量和结构问题
- 禁止错误解释的指标：建议 Bid≠真实 CPC，搜索量≠销量，单一 ACoS/CTR/CVR 不等于完整结论
- SellerSpace MCP 数据摘要（如可用）：sellerId、Marketplace、查询时间、数据窗口、实际调用的 Tool/Entity、字段、返回状态和同步限制
- 本地广告原始数据摘要（如有）：`05_分析源数据/06_广告数据下载/` 文件名、数据日期、覆盖窗口和读取字段；不复制原始文件内容
- H10/Cerebro 与 SellerSpace 推荐的来源交叉验证：关键词、Search Volume、Organic/Sponsored Rank、H10 Bid/Range、平台建议 Bid/Range、来源标签和冲突项
- Keyword Mother Pool：关键词、中文理解、来源、来源 ASIN、日期、Search Volume、Rank、Bid/Range、相关性、购买意图、语义主题、成熟度和 release_status
- Semantic Cluster / Purchase Intent Cluster：cluster_id、名称、意图、词数、代表词、证据、成熟度、已释放词、Held Keywords 和风险
- Initial Released Keywords 与 Held Keywords；Held 状态可为 `HELD_FOR_EXPANSION`、`WAITING_CLUSTER_VALIDATION`、`LOW_PRIORITY`、`INSUFFICIENT_EVIDENCE`、`DO_NOT_LAUNCH`
- Expansion Rules、Expansion Budget Rules、Promotion Rules、Stop Rules；明确 6-2 何时回查母词池及不得一次释放全部剩余词
- Search Term/Target 成熟度定义与当前状态；Initial Campaign Architecture、Keyword roles、Product Target roles、关键假设和关键风险
- 数据性质标签：`[真实运行事实]`、`[平台/工具推荐]`、`[第三方原始推荐数据]`、`[人工目标]`、`[AI策略建议]`、`[待验证]`

若状态为 `【上游页面状态不满足推广条件｜返回5-4】`、`【关键页面或产品条件不足｜暂不建议启动推广】`、商品不可售或身份无法确认，不生成该交接包；在报告中说明原因。缺少 5-4 但最低必要条件基本满足时，仍可生成标注待验证项的受控小规模验证交接包。


## 阶段6闭环字段

交给 6-2 时补充：产品阶段、上线时间/Review/库存状态（如有）、当前目标、次要目标、允许风险、Keyword/Seed/benchmark_asin 分组、Campaign/Ad Group/Target 任务、Match Type、初始 Bid/Budget/Placement 依据、Price/Coupon、验证窗口、成功/失败信号、允许 6-2 建议的动作、必须人工批准的动作和关键未知项。分别列出 H10建议Bid、平台建议Bid、历史实际CPC、当前实际Bid和AI建议启动Bid，禁止混写。

6-1 运行后产生的日志字段：Product Code、ASIN、日期、Skill、目标、数据窗口、来源、Campaign、Ad Group、Keyword、Search Term、当前指标、AI判断、建议、人工决策、最终动作、执行方式、1天/3天/7天结果和最终验证结论；保存到 `06_SKILL分析报告/广告表现汇报优化日志/`。


## 初始广告创建结果（如已批准执行）

- execution_id、approved_at、prepared_at、applied_at、verification_at、planId
- Actual Campaign IDs/名称、Ad Group、Advertised Product、Keyword/Target、Bid、Budget、Placement、Bidding Strategy、Status
- Read-Back Verification 状态、非关键差异、部分失败对象及 Recovery Plan
- 旧广告处理：`[旧广告未修改｜由用户人工处理]`
