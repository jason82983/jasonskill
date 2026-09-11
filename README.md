# JasonSkill

这是 HZP 的个人与团队 Skill 仓库。根目录 README 只负责说明行业分类和 Skill 索引；每个具体 Skill 的详细用途、输入、输出和使用方法，写在自己的 `README.md` 中。

## 行业目录

| 行业 | 目录 | 当前状态 | 说明 |
|---|---|---|---|
| Amazon | [01 amazon](<01 amazon/README.md>) | 已建立 | Amazon 产品资料、市场分析和产品开发相关 Skills |
| 其他行业 | 待建立 | 未建立 | 后续按行业新增独立目录和行业 README |

## 当前 Skill 总览

| Skill | 所属行业 | 目标 |
|---|---|---|
| `hzp-amz-0-1-product-file-structure` | Amazon | 管理 Products Root 和 Product Root 的标准文件结构 |
| `hzp-amz-1-1-opportunity-discovery` | Amazon | 从真实市场信号发现可验证的候选商机并交接给 1-2 |
| `hzp-amz-1-2-product-screening` | Amazon | 基于 1-1 证据筛选值得进入 2-1 的候选商机 |
| `hzp-amz-2-1-market-research` | Amazon | 分析单个 Amazon 产品的市场表现、证据和开发可行性 |
| `hzp-amz-2-2-market-analysis` | Amazon | 判断细分市场范围、市场进入机会和改良开发价值 |
| `hzp-amz-3-1-product-opportunity-definition` | Amazon | 从前序市场证据和人工判断中收敛可验证的产品机会 |
| `hzp-amz-3-2-differentiated-product-development` | Amazon | 将产品机会转化为可评审、可打样的差异化产品方案 |
| `hzp-amz-3-3-product-plan-review` | Amazon | 评审产品方案是否具备打样验证条件 |
| `hzp-amz-4-1-sample-review` | Amazon | 基于真实样品证据评审样品并决定下一步 |
| `hzp-amz-4-2-preproduction-check` | Amazon | 核查量产冻结、供应链、质量与合规条件 |
| `hzp-amz-5-1-listing-page-strategy` | Amazon | 制定页面销售战略并交接给文案和视觉阶段 |
| `hzp-amz-5-2-listing-copywriting` | Amazon | 生成有证据约束的 Amazon US Listing 文案 |
| `hzp-amz-5-3-image-video-planning` | Amazon | 规划 Amazon 图片、A+ 与视频并守住产品真实性 |
| `hzp-amz-5-4-page-audit-optimization` | Amazon | 审核页面策略、文案、视觉和真实成品并输出修改优先级 |
| `hzp-amz-6-1-new-product-launch-strategy` | Amazon | 设计新品首阶段流量、广告测试、预算协同与验证规则 |
| `hzp-amz-6-2-advertising-diagnosis-optimization` | Amazon | 基于真实广告数据诊断问题并输出最小必要优化动作 |
| `hzp-amz-6-3-product-operations-monitoring` | Amazon | 持续监控产品经营健康并将异常路由到正确 Skill |
| `hzp-amz-7-1-replenishment-forecast` | Amazon | 基于真实库存、销售速度和 Lead Time 形成补货预测 |
| hzp-amz-7-2-inventory-risk-management | Amazon | 持续监控库存偏差、在途、老化和资金风险 |


## 使用约定

- 每个 Skill 都有独立目录和自己的 `SKILL.md`；
- 每个 Skill 都应提供面向使用者的 `README.md`；
- 行业目录 README 说明该行业的 Skill 体系和衔接关系；
- 根目录 README 只维护行业分类和基础索引，不重复具体 Skill 方法论；
- 修改 Skill 时，以本仓库对应目录为源版本，再同步到本机 Codex Skill 目录；
- 提交前运行 Skill 校验，避免把临时报告、原始业务数据或个人敏感信息加入仓库。

## 目录结构

```text
JasonSkill/
├─ README.md
└─ 01 amazon/
   ├─ README.md
   └─ hzp-amz-*/
      ├─ SKILL.md
      ├─ README.md
      ├─ agents/
      ├─ references/
      └─ templates/
```








