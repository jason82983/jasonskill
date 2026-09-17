# HZP Amazon Skills

本目录集中维护 Amazon 行业 Skills。它们按产品工作流程衔接：

```text
产品文件结构 → 产品分析 → 细分市场分析 → 人工判断与 AI 同步 → 产品机会定义
0-1              2-1        2-2             2-3                 3-1
  页面与推广 → 5-1 → 5-2 → 5-3 → 5-4 → 6-0-1（对标自然排名关键词） → 6-0-2（精准关键词识别） → 6-0-3（当前产品 Intent Tree） → 6-0-6（对标自然占领 Reality Evidence，待6-0-5接入） → 6-0-5（新品作战规划｜PLAN） → 人工审批 → 6-1（新品广告初始架构｜BUILD） → 6-2（广告运行事实｜DATA） → 6-3（广告经营 AI 决策｜DECIDE，不写广告） → 人工批准 → 6-4（获批日常优化动作｜APPLY） → 下一轮 6-2
　　　　　　　　　　　　　　　　　　　　　　　　　　　　　↘ 6-0-4（AI精准词同步 ERP，仅受限写入）
报告型 Skill 生成正式 HTML 后，由 0-2 统一更新报告索引
```

每个 Skill 的详细使用说明，见对应目录中的 `README.md`；本文件只说明 Amazon 行业的基本分工和入口。

Stage 6 正式报告的最新有效输入选择、运行时间戳、不覆盖与输入血缘，统一遵守 [共享资产契约](references/stage6-artifact-contract.md)。

所有正式报告型 `hzp-amz-*` Skill 的目录分层、HTML 最新/历史归档、机器数据与
系统资产位置，统一遵守 [报告目录与归档契约](references/report-layout-contract.md)，
并复用 `scripts/hzp_amz_report_contract.py`，不在各 Skill 建立平行 Writer/Resolver。

## 公共产品身份接口

`00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx` 是 Amazon 产品与 SellerSpace 店铺身份映射主表。需要读取店铺真实数据的 Skill 先按 `Product Code` 读取这张表，再用 `SellerSpace_Store + Marketplace + ASIN + SKU` 做只读二次验证。统一规则见 [Amazon产品身份解析规则](<Amazon产品身份解析规则.md>)。映射表由人工维护，Skills 只读，不自动修改其中的数据。

## Skill 清单

| 编号 | Skill | 用途 | 下一步 |
|---|---|---|---|
| 0-1 | `hzp-amz-0-1-product-file-structure` | 建立、检查和整理产品资料目录，保护原始数据 | 进入分析 |
| 0-2 | `hzp-amz-0-2-report-index` | 扫描正式 HTML 报告并维护当前产品的 `06_SKILL分析报告/index.html` | 随报告自动调用 |
| 0-3 | `hzp-amz-0-3-amazon-business-calendar-alerts` | 维护 Amazon 经营日历、季节/Launch 倒排、每日预警和 Skill 路由 | 按需调用 |
| 0-4 | hzp-amz-0-4-amazon-rules-compliance-knowledge | 查询、核验并沉淀 Amazon 平台规则、FBA、合规与官方帮助知识 | 被其他 Skill 按需查询 |
| 0-5 | `hzp-amz-0-5-management-decision-brief` | 发现需要上级决策的经营事项，生成决策周报并记录路由 | 管理决策 |
| 1-1 | `hzp-amz-1-1-opportunity-discovery` | 从真实市场信号发现需求—产品候选商机 | 进入 1-2 |
| 1-2 | `hzp-amz-1-2-product-screening` | 基于 1-1 证据快速筛选值得进入 2-1 的候选商机 | 进入 2-1 |
| 2-1 | `hzp-amz-2-1-product-analysis` | 分析单个 Amazon 产品、需求、竞品、评论和开发可行性 | 进入 2-2 |
| 2-2 | `hzp-amz-2-2-market-analysis` | 判断产品所属细分市场、市场机会和改良开发价值 | 进入 2-3 |
| 2-3 | `hzp-amz-2-3-human-ai-sync` | 对照人工开发思路与 2-1/2-2 证据，识别冲突并整理后续产品开发输入 | 产品开发 Skill 待重建 |
| 3-1 | `hzp-amz-3-1-product-opportunity-definition` | 从 2-1、2-2、2-3 证据中收敛产品机会，明确 WHAT、WHY 与 3-2 验证输入 | 进入 3-2 |
| 3-2 | `hzp-amz-3-2-differentiated-product-development` | 将产品机会转化为可评审、可打样的差异化产品方案 | 进入 3-3 |
| 3-3 | `hzp-amz-3-3-product-plan-review` | 评审产品方案是否具备打样验证条件 | 进入 4-1 |
| 4-1 | `hzp-amz-4-1-sample-review` | 基于真实样品证据评审样品并决定下一步 | 进入 4-2 |
| 4-2 | `hzp-amz-4-2-preproduction-check` | 核查量产冻结、供应链、质量与合规条件 | 进入页面阶段 |
| 5-0-1 | `hzp-amz-5-0-1-product-online-information-retrieval` | 根据产品编码获取当前 Amazon 线上商品证据并生成正式 HTML | 供 6-0-2 使用 |
| 5-1 | `hzp-amz-5-1-listing-page-strategy` | 制定页面销售战略并交接给文案和视觉阶段 | 进入 5-2 |
| 5-2 | `hzp-amz-5-2-listing-copywriting` | 生成有证据约束的 Amazon US Listing 文案 | 进入 5-3/5-4 |
| 5-3 | `hzp-amz-5-3-image-video-planning` | 规划 Amazon 图片、A+ 与视频并守住产品真实性 | 进入 5-4 |
| 5-4 | `hzp-amz-5-4-page-audit-optimization` | 审核页面策略、文案、视觉和真实成品并输出修改优先级 | 进入 6-1 |
| 5-5 | hzp-amz-5-5-live-asin-page-audit | 审计真实线上 ASIN 页面与策略执行，诊断根因并路由优化 | 进入 6-1/按需回路 |
| 6-0-1 | `hzp-amz-6-0-1-benchmark-organic-keyword-extraction` | 提取对标 ASIN 自然排名与市场容量关键词原始 CSV | 作为 Benchmark Organic Keyword 原始证据，由上层按需消费 |
| 6-0-2 | `hzp-amz-6-0-2-ai-precision-keyword-identification` | 识别 ERP 人工/AI 精准词并生成双轨 CSV 资产 | 精准词资产进入 6-0-3 |
| 6-0-3 | `hzp-amz-6-0-3-precision-broad-extraction` | 从 6-0-2 高度精准词构建 Search Intent 层级并递归汇总搜索量 | 新品作战规划进入 6-0-5 |
| 6-0-4 | `hzp-amz-6-0-4-ai-precision-keyword-erp-sync` | 按 6-0-2 自动编号将 AI 精准词受限追加到 ERP `PickPwK.Tags` | 仅预检后受限同步；结果回到 6-0-2 |
| 6-0-5 | `hzp-amz-6-0-5-new-product-advertising-battle-plan` | 读取同次有效 6-0-3 资产，规划首攻市场、全量关键词生命周期及待审批广告架构；只 PLAN | 人工审批后交 6-1 |
| 6-0-6 | `hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis` | 将 601 Benchmark 自然排名投影到 603 Intent Tree，计算单对标自然占领深度与多对标共识；仅提供 Reality Evidence，不代表销量份额或广告决策 | 待 6-0-5 接入为辅助证据 |
| 6-1 | `hzp-amz-6-1-new-product-advertising-battle-plan` | 消费最新已批准 6-0-5 作战表，生成 Desired State，与实时广告状态对账；负责新品初始广告架构 BUILD 与 Read-back，不消费 6-3 日常决策 | 进入 6-2 |
| 6-2 | `hzp-amz-6-3-advertising-data-report` | DATA ONLY：采集并打包 Campaign、Intent、Target、Search Term 同Run广告运行事实；不诊断或建议 | 6-3读取完整有效Run Package后独立决策 |
| 6-3 | `hzp-amz-6-4-advertising-decision` | DECIDE：读取完整 6-2 事实包和批准的 6-0-5 作战目的，对 Intent/Campaign/Target/Search Term 逐项形成证据化决策包；不写 Amazon Ads | 人工批准后由 6-4 执行 |
| 6-4 | `hzp-amz-6-5-advertising-optimization-action-executor` | APPLY：只执行 6-3 已批准日常动作；先对比实时状态并检查精确 Prepare 预览，执行后按 Amazon ID 回读并留存审计包 | 执行后进入下一轮 6-2 |
| 7-1 | `hzp-amz-7-1-replenishment-forecast` | 基于真实库存、销售速度和完整 Lead Time 形成补货预测 | 进入 7-2 |
| 7-2 | hzp-amz-7-2-inventory-risk-management | 持续监控库存风险、补货偏差、在途、老化和资金占用 | 运营持续监控 |


## 基本使用方式

通常告诉 Codex：

```text
使用 [Skill名称]
产品：P001
Products Root：E:\【产品总目录】
```

Skill 会根据标准 Product Root 结构自动查找资料。具体数据位置、输入要求和输出文件名，以对应 Skill 的 README 为准。

## 目录约定

```text
[Products Root]/
├─ 00_产品公用数据/
└─ [Product Root]/
   ├─ 01_产品档案.md
   ├─ 05_分析源数据/
   └─ 06_SKILL分析报告/
```

不同员工或电脑可以使用不同的 Products Root；Skill 应依靠产品身份和标准相对路径定位资料，不依赖固定盘符。

## 衔接原则

- 0-1 负责资料结构和产品身份；
- 2-1 负责单个产品证据和市场表现；
- 2-2 负责细分市场和进入机会；
- 2-3 负责把人工开发思路与前序 AI 证据并列同步，不替人工或市场阶段作最终决策；
- 3-1 负责把市场机会收敛为可验证的产品机会定义；
- 0-2 是唯一的报告索引责任方，报告型 Skill 成功生成正式 HTML 后调用它更新 `index.html`；
- 上一个 Skill 的正式报告和 `HANDOFF.md` 是下一个 Skill 的优先输入；
- 下游 Skill 可以验证、修正或否定上游推断，但必须保留证据来源和变化原因。

## 具体 Skill 说明

- [0-1 产品文件结构管理](<hzp-amz-0-1-product-file-structure/README.md>)
- [0-2 分析报告索引](<hzp-amz-0-2-report-index/README.md>)
- [0-3 Amazon经营日历与预警](<hzp-amz-0-3-amazon-business-calendar-alerts/README.md>)
- [0-4 Amazon规则、合规与官方知识](<hzp-amz-0-4-amazon-rules-compliance-knowledge/README.md>)
- [0-5 上级决策与经营问询](<hzp-amz-0-5-management-decision-brief/README.md>)
- [1-1 商机发现](<hzp-amz-1-1-opportunity-discovery/README.md>)
- [1-2 选品初筛](<hzp-amz-1-2-product-screening/README.md>)
- [2-1 产品市场分析](<hzp-amz-2-1-product-analysis/README.md>)
- [2-2 细分市场分析](<hzp-amz-2-2-market-analysis/README.md>)
- [2-3 人工判断与 AI 同步](<hzp-amz-2-3-human-ai-sync/README.md>)
- [3-1 产品机会定义](<hzp-amz-3-1-product-opportunity-definition/README.md>)
- [3-2 差异化产品开发](<hzp-amz-3-2-differentiated-product-development/README.md>)
- [3-3 产品方案评审](<hzp-amz-3-3-product-plan-review/README.md>)
- [4-1 打样评审](<hzp-amz-4-1-sample-review/README.md>)
- [4-2 量产前检查](<hzp-amz-4-2-preproduction-check/README.md>)
- [5-1 页面策略](<hzp-amz-5-1-listing-page-strategy/README.md>)
- [5-0-1 产品线上信息获取](<hzp-amz-5-0-1-product-online-information-retrieval/README.md>)
- [5-2 Listing文案](<hzp-amz-5-2-listing-copywriting/README.md>)
- [5-3 图片视频策划](<hzp-amz-5-3-image-video-planning/README.md>)
- [5-4 页面审核优化](<hzp-amz-5-4-page-audit-optimization/README.md>)
- [5-5 线上 ASIN 页面审计与优化](<hzp-amz-5-5-live-asin-page-audit/README.md>)
- [6-0-1 对标自然排名关键词提取](<hzp-amz-6-0-1-benchmark-organic-keyword-extraction/README.md>)
- [6-0-2 精准关键词识别](<hzp-amz-6-0-2-ai-precision-keyword-identification/README.md>)
- [6-0-3 精准泛词提取](<hzp-amz-6-0-3-precision-broad-extraction/README.md>)
- [6-0-4 AI精准词同步 ERP](<hzp-amz-6-0-4-ai-precision-keyword-erp-sync/README.md>)
- [6-0-5 新品广告作战规划](<hzp-amz-6-0-5-new-product-advertising-battle-plan/README.md>)
- [6-0-6 对标意图市场占领分析](<hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis/README.md>)
  - [6-1 新品推广方案](<hzp-amz-6-1-new-product-advertising-battle-plan/README.md>)
  - [6-2 广告运行事实数据层](<hzp-amz-6-3-advertising-data-report/README.md>)
  - [6-3 广告诊断优化](<hzp-amz-6-4-advertising-decision/README.md>)
  - [6-4 广告优化动作执行](<hzp-amz-6-5-advertising-optimization-action-executor/README.md>)
- [7-1 补货预测](<hzp-amz-7-1-replenishment-forecast/README.md>)
- [7-2 库存风险管理](<hzp-amz-7-2-inventory-risk-management/README.md>)

