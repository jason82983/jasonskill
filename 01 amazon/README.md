# HZP Amazon Skills

本目录集中维护 Amazon 行业 Skills。它们按产品工作流程衔接：

```text
产品文件结构 → 产品分析 → 细分市场分析 → 人工判断与 AI 同步 → 产品机会定义
0-1              2-1        2-2             2-3                 3-1
页面与推广 → 5-1 → 5-2 → 5-3 → 5-4 → 6-1
报告型 Skill 生成正式 HTML 后，由 0-2 统一更新报告索引
```

每个 Skill 的详细使用说明，见对应目录中的 `README.md`；本文件只说明 Amazon 行业的基本分工和入口。

## Skill 清单

| 编号 | Skill | 用途 | 下一步 |
|---|---|---|---|
| 0-1 | `hzp-amz-0-1-product-file-structure` | 建立、检查和整理产品资料目录，保护原始数据 | 进入分析 |
| 0-2 | `hzp-amz-0-2-report-index` | 扫描正式 HTML 报告并维护当前产品的 `06_SKILL分析报告/index.html` | 随报告自动调用 |
| 1-1 | `hzp-amz-1-1-opportunity-discovery` | 从真实市场信号发现需求—产品候选商机 | 进入 1-2 |
| 1-2 | `hzp-amz-1-2-product-screening` | 基于 1-1 证据快速筛选值得进入 2-1 的候选商机 | 进入 2-1 |
| 2-1 | `hzp-amz-2-1-market-research` | 分析单个 Amazon 产品、需求、竞品、评论和开发可行性 | 进入 2-2 |
| 2-2 | `hzp-amz-2-2-market-analysis` | 判断产品所属细分市场、市场机会和改良开发价值 | 进入 2-3 |
| 2-3 | `hzp-amz-2-3-human-ai-sync` | 对照人工开发思路与 2-1/2-2 证据，识别冲突并整理后续产品开发输入 | 产品开发 Skill 待重建 |
| 3-1 | `hzp-amz-3-1-product-opportunity-definition` | 从 2-1、2-2、2-3 证据中收敛产品机会，明确 WHAT、WHY 与 3-2 验证输入 | 进入 3-2 |
| 3-2 | `hzp-amz-3-2-differentiated-product-development` | 将产品机会转化为可评审、可打样的差异化产品方案 | 进入 3-3 |
| 3-3 | `hzp-amz-3-3-product-plan-review` | 评审产品方案是否具备打样验证条件 | 进入 4-1 |
| 4-1 | `hzp-amz-4-1-sample-review` | 基于真实样品证据评审样品并决定下一步 | 进入 4-2 |
| 4-2 | `hzp-amz-4-2-preproduction-check` | 核查量产冻结、供应链、质量与合规条件 | 进入页面阶段 |
| 5-1 | `hzp-amz-5-1-listing-page-strategy` | 制定页面销售战略并交接给文案和视觉阶段 | 进入 5-2 |
| 5-2 | `hzp-amz-5-2-listing-copywriting` | 生成有证据约束的 Amazon US Listing 文案 | 进入 5-3/5-4 |
| 5-3 | `hzp-amz-5-3-image-video-planning` | 规划 Amazon 图片、A+ 与视频并守住产品真实性 | 进入 5-4 |
| 5-4 | `hzp-amz-5-4-page-audit-optimization` | 审核页面策略、文案、视觉和真实成品并输出修改优先级 | 进入 6-1 |
| 6-1 | `hzp-amz-6-1-new-product-launch-strategy` | 设计新品首阶段推广、广告验证、预算和继续/停止规则 | 进入 6-2 |
| 6-2 | `hzp-amz-6-2-advertising-diagnosis-optimization` | 诊断真实广告数据并输出最小必要优化动作 | 进入 6-3 |
| 6-3 | `hzp-amz-6-3-product-operations-monitoring` | 监控产品经营健康并将异常路由到广告、页面、产品、供应链或库存 Skill | 进入 7 阶段 |
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
- [1-1 商机发现](<hzp-amz-1-1-opportunity-discovery/README.md>)
- [1-2 选品初筛](<hzp-amz-1-2-product-screening/README.md>)
- [2-1 产品市场分析](<hzp-amz-2-1-market-research/README.md>)
- [2-2 细分市场分析](<hzp-amz-2-2-market-analysis/README.md>)
- [2-3 人工判断与 AI 同步](<hzp-amz-2-3-human-ai-sync/README.md>)
- [3-1 产品机会定义](<hzp-amz-3-1-product-opportunity-definition/README.md>)
- [3-2 差异化产品开发](<hzp-amz-3-2-differentiated-product-development/README.md>)
- [3-3 产品方案评审](<hzp-amz-3-3-product-plan-review/README.md>)
- [4-1 打样评审](<hzp-amz-4-1-sample-review/README.md>)
- [4-2 量产前检查](<hzp-amz-4-2-preproduction-check/README.md>)
- [5-1 页面策略](<hzp-amz-5-1-listing-page-strategy/README.md>)
- [5-2 Listing文案](<hzp-amz-5-2-listing-copywriting/README.md>)
- [5-3 图片视频策划](<hzp-amz-5-3-image-video-planning/README.md>)
- [5-4 页面审核优化](<hzp-amz-5-4-page-audit-optimization/README.md>)
- [6-1 新品推广方案](<hzp-amz-6-1-new-product-launch-strategy/README.md>)
- [6-2 广告诊断优化](<hzp-amz-6-2-advertising-diagnosis-optimization/README.md>)
- [6-3 产品运营监控](<hzp-amz-6-3-product-operations-monitoring/README.md>)
- [7-1 补货预测](<hzp-amz-7-1-replenishment-forecast/README.md>)
- [7-2 库存风险管理](<hzp-amz-7-2-inventory-risk-management/README.md>)






