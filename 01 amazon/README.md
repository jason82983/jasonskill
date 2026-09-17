# HZP Amazon Skills

本目录是 JasonSkill 的 Amazon 技能集合。每个技能的 SKILL.md 是执行契约，README.md 是面向使用者的当前说明；两者必须保持一致。

## 当前技能

- [hzp-amz-0-1-product-file-structure](<hzp-amz-0-1-product-file-structure/README.md>)：Create, check, organize, and safely migrate an Amazon Products Root Shared Data area or individual Product Root to the HZP Directory V1 structure while preserving original evidence and separating human input from Skill-generated analysis.
- [hzp-amz-0-2-report-index](<hzp-amz-0-2-report-index/README.md>)：Scan a product project's formal Amazon Skill HTML reports and rebuild its offline 06_SKILL分析报告/index.html. Use when a user wants to create, refresh, repair, or inspect the report index; do not analyze products, edit reports, or change source data.
- [hzp-amz-0-3-amazon-business-calendar-alerts](<hzp-amz-0-3-amazon-business-calendar-alerts/README.md>)：Provide Amazon US business-calendar reminders, product seasonal and launch reverse scheduling, daily operational forecasts, risk alerts, and routing to the appropriate HZP Amazon Skill without changing Amazon data or performing specialist analysis.
- [hzp-amz-0-4-amazon-rules-compliance-knowledge](<hzp-amz-0-4-amazon-rules-compliance-knowledge/README.md>)：查询、核验并沉淀 Amazon US 平台规则、FBA要求、产品合规与官方帮助知识；按来源和时效区分平台规则、美国法规、物流要求与公司经验。
- [hzp-amz-0-5-management-decision-brief](<hzp-amz-0-5-management-decision-brief/README.md>)：发现 Amazon 经营链路中真正需要上级方向、资本、资源、风险或继续/停止决策的问题，生成增量式中文决策周报、A/B/C/D问询、Decision Register 和执行路由；不替代专业 Skill 作日常操作或最终老板决策。
- [hzp-amz-0-6-skill-sync-github](<hzp-amz-0-6-skill-sync-github/README.md>)：同步 HZP Amazon 技能：输入 1 时将 .codex/skills 下 hzp-amz-* 技能镜像到 JasonSkill，删除旧技能，更新所有 README，并提交推送 GitHub；空输入不执行。
- [hzp-amz-1-1-opportunity-discovery](<hzp-amz-1-1-opportunity-discovery/README.md>)：从真实 Amazon 搜索、消费者、竞争、趋势、价格、供应链和团队能力信号中发现可验证的候选产品商机，形成证据化候选池并交接给 1-2 初筛；不替代产品分析、细分市场分析或最终 GO/NO-GO 决策。
- [hzp-amz-1-2-product-screening](<hzp-amz-1-2-product-screening/README.md>)：基于 1-1 商机发现交接和真实市场证据，快速筛选值得继续投入 2-1 深度分析的候选商机；检查需求、硬风险、竞争进入、差异化、商业空间、物流、供应链、团队、IP/合规、生命周期和失败成本，但不替代 2-1/2-2 或输出最终 GO/NO-GO。
- [hzp-amz-2-1-product-analysis](<hzp-amz-2-1-product-analysis/README.md>)：Analyze one Amazon US product in a portable PRODUCT.md-marked project from matching Keepa, Helium 10 Cerebro, Amazon Reviews, sales-record/estimate, investment-return-calculation image inputs, and a public Amazon product-page snapshot, then produce an evidence-grounded Chinese HTML decision report and downstream HANDOFF. The report must use H10 bid data directly, distinguish recorded sales from modeled returns, quote short real reviews with Chinese translations, reconcile current page facts with historical/file evidence, emphasize Product Definition V1, distinguish facts/inference/supply-chain validation, and use QMT terminology only. Never invent missing metrics or merge reviews.
- [hzp-amz-2-2-market-analysis](<hzp-amz-2-2-market-analysis/README.md>)：Run an evidence-based Amazon submarket decision process for a benchmark product. Automatically discover relevant files in the selected Product Root, execute the seven formally defined analysis stages continuously, and produce a Chinese HTML report with a final market-entry decision and downstream handoff context.
- [hzp-amz-2-3-human-ai-sync](<hzp-amz-2-3-human-ai-sync/README.md>)：将人工产品开发判断与 2-1、2-2 的 AI 分析证据进行分类、对照、冲突识别和 3-1 交接，并生成中文正式 HTML 报告；不重新执行前序研究，也不替人工或市场阶段作最终决策。
- [hzp-amz-3-1-product-opportunity-definition](<hzp-amz-3-1-product-opportunity-definition/README.md>)：从 2-1、2-2、2-3 的 Amazon 项目证据中收敛可验证的产品机会定义，明确消费者价值、购买理由、项目边界与交给 3-2 的验证输入；不重做市场研究或详细工程设计。
- [hzp-amz-3-2-differentiated-product-development](<hzp-amz-3-2-differentiated-product-development/README.md>)：将 3-1 已确认的 Amazon 产品机会转化为可评审、可打样、可验证的差异化产品方案 V1；覆盖设计目标、候选方案、追溯、BOM V1、Amazon 可表达差异点、风险验证和 3-3 交接，不重做市场分析、不替代工程定版或量产批准。
- [hzp-amz-3-3-product-plan-review](<hzp-amz-3-3-product-plan-review/README.md>)：评审当前产品最新的 3-2 差异化产品方案，判断是否值得进入真实打样验证，并在满足条件时生成 4-1 输入交接包；不重新做市场分析、机会定义或完整产品设计。
- [hzp-amz-4-1-sample-review](<hzp-amz-4-1-sample-review/README.md>)：基于 3-3 已批准的产品方案和真实样品证据，评审样品是否实现核心目标并决定进入 4-2、修改后重打、退回 3-2 或暂不决策；没有可靠样品证据时不得假装完成评审。
- [hzp-amz-4-2-preproduction-check](<hzp-amz-4-2-preproduction-check/README.md>)：在 4-1 样品评审通过或条件已满足后，核查 Amazon 产品的量产冻结、BOM、规格、材料、成本、供应链、质量、包装、IP/合规/安全与量产风险，并决定是否允许进入正式量产；不重新开发产品或替代最终验货。
- [hzp-amz-5-0-1-product-online-information-retrieval](<hzp-amz-5-0-1-product-online-information-retrieval/README.md>)：Product-code-only retrieval of the current Amazon detail page, preserving raw online evidence and a clearly labelled AI semantic profile in a formal HTML report.
- [hzp-amz-5-1-listing-page-strategy](<hzp-amz-5-1-listing-page-strategy/README.md>)：将已确认的 Amazon 产品价值、消费者问题、差异化和证据转化为页面销售战略，定义信息优先级、购买逻辑、页面载体和 5-2/5-3 交接；不直接完成最终 Listing、图片或视频。
- [hzp-amz-5-2-listing-copywriting](<hzp-amz-5-2-listing-copywriting/README.md>)：基于最新 5-1 页面策略、真实产品事实和关键词证据，生成 Amazon US Listing 文案、A+ 文字基础及 5-3/5-4 交接，并审核 Claim 证据；不重新定义页面战略、不制作图片或视频。
- [hzp-amz-5-3-image-video-planning](<hzp-amz-5-3-image-video-planning/README.md>)：将 5-1 页面战略与 5-2 Listing 文案转化为 Amazon 图片、A+ 和视频的执行蓝图，规划每个视觉资产的任务、真实素材、Claim 证据和 AI 出图边界；不重新定义页面战略、不制作成片。
- [hzp-amz-5-4-page-audit-optimization](<hzp-amz-5-4-page-audit-optimization/README.md>)：综合审核 Amazon 页面策略、Listing 文案、图片视频策划与真实页面成品，识别战略、购买路径、Claim、真实性、可读性和转化问题，并输出按优先级和责任 Skill 分流的修改清单；不重新开发产品或替代 5-2/5-3 制作。
- [hzp-amz-5-5-live-asin-page-audit](<hzp-amz-5-5-live-asin-page-audit/README.md>)：审计真实上线的 Amazon ASIN 页面，核对 5-1 至 5-4 的策略、文案和视觉是否被正确执行，诊断页面、Offer、流量、产品等根因并输出有证据的优化优先级和 Skill 路由；不直接修改 Listing、价格、Coupon 或广告。
- [hzp-amz-6-0-1-benchmark-organic-keyword-extraction](<hzp-amz-6-0-1-benchmark-organic-keyword-extraction/README.md>)：对当前产品档案中配置的 1..N 个 Benchmark 分别读取 PickPwKView 自然排名数据，输出多对标明细、唯一关键词母池、逐 ASIN 原始表和 Observation 汇总表；不做语义判断或写操作。
- [hzp-amz-6-0-2-ai-precision-keyword-identification](<hzp-amz-6-0-2-ai-precision-keyword-identification/README.md>)：读取当前产品识别文本与6-0-1全部对标自然排名Observation，按Canonical Keyword只判断一次精准度，输出三张公共表及每个对标一张高度精准表；不查询ERP或执行写操作。
- [hzp-amz-6-0-3-precision-broad-extraction](<hzp-amz-6-0-3-precision-broad-extraction/README.md>)：Read only the 6-0-2去对标去重 高度精准词 asset from its latest complete VALID Run Package, organize each unique high-precision keyword into a semantic Search Intent hierarchy, and produce traceable mapping and hierarchy summary CSVs. Never rejudge precision or execute ad writes.
- [hzp-amz-6-0-4-ai-precision-keyword-erp-sync](<hzp-amz-6-0-4-ai-precision-keyword-erp-sync/README.md>)：将 6-0-2 AI 精准词 CSV 通过系统级受限 PickPwK Writer 能力安全追加到 ERP Tags；支持预检、幂等、事务、并发保护和回读，不重新判断精准词。
- [hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis](<hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis/README.md>)：将多个Benchmark自然排名映射到当前产品603 Search Intent Tree，计算各Benchmark在各Intent中的自然搜索占领深度、需求覆盖与多对标共识，生成CSV和HTML Reality Evidence；不表示销量份额、不决定广告策略、不写入广告或ERP。
- [hzp-amz-6-1-new-product-advertising-battle-plan](<hzp-amz-6-1-new-product-advertising-battle-plan/README.md>)：Plan which precise Amazon search intents and keywords a new product should advertise first, how each should be controlled, and what initial campaign structure to review before 6-2 execution. Never writes Amazon ads.
- [hzp-amz-6-2-new-product-launch-strategy](<hzp-amz-6-2-new-product-launch-strategy/README.md>)：将 6-1 最新有效且已批准的 Amazon 广告作战计划转为 Desired State，与实时广告状态对账，并在精确差异获批后安全应用、回读和审计；不重判投放战略或关键词。
- [hzp-amz-6-3-advertising-data-report](<hzp-amz-6-3-advertising-data-report/README.md>)：读取当前产品真实广告运行数据，生成带时间戳、可追溯的事实数据包与HTML/CSV报告；只做DATA，不做经营决策或广告写操作。
- [hzp-amz-6-4-advertising-decision](<hzp-amz-6-4-advertising-decision/README.md>)：作为 Amazon 广告经营决策层，读取6-3广告运行事实数据，形成可追溯的决策包和待执行动作，交由6-5执行；本Skill不执行Amazon Ads写操作。
- [hzp-amz-6-5-advertising-optimization-action-executor](<hzp-amz-6-5-advertising-optimization-action-executor/README.md>)：消费已批准的6-4广告经营决策包，校验身份、权限、能力和精确差异后执行并回读获批Amazon Ads动作；不重新决策。
- [hzp-amz-6-6-product-operations-monitoring](<hzp-amz-6-6-product-operations-monitoring/README.md>)：持续监控单个 Amazon 产品的真实经营数据，区分正常波动与明确异常，并将问题路由到 6-4、页面、产品、供应链或 7 阶段 Skill；无可靠数据时明确证据不足，不编造指标。
- [hzp-amz-7-1-replenishment-forecast](<hzp-amz-7-1-replenishment-forecast/README.md>)：基于真实销售速度、库存结构、在途状态和完整 Lead Time，形成带情景、条件和风险说明的 Amazon 补货预测；缺少关键库存或供应链证据时不硬算。
- [hzp-amz-7-2-inventory-risk-management](<hzp-amz-7-2-inventory-risk-management/README.md>)：持续监控 Amazon 产品库存偏差、老化、在途和资金风险，判断是否重算 7-1，并将问题路由到供应链、推广、页面或产品阶段；缺少真实数据时不硬判。

## 工作链路

产品资料与身份 → 产品分析与市场判断 → 产品开发 → Listing → 关键词与广告规划 → 广告创建与运行事实 → 广告诊断与动作执行 → 补货与库存风险。

各阶段按自身 Skill 的交接契约传递证据，不跨阶段臆测或混用旧报告。

## 目录与报告约定

- 产品根目录默认位于 E:\【所有产品目录专用】，具体输入以当前产品档案为准。
- 正式报告统一写入产品的  6_SKILL分析报告，遵守共享报告目录与命名契约。
- hzp-amz-0-6-skill-sync-github 负责将 .codex 中的 hzp-amz-* 技能同步到本目录，删除旧技能，并在发布时同步更新本文件与仓库根目录 README。

## 使用

请直接调用对应 Skill，并提供产品编号或产品根目录。详细输入、输出、限制和示例以该 Skill 当前 SKILL.md 与 README.md 为准。

