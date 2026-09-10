# 旧 2-2 分析组件（辅助证据库）

本文件用于保存可复用的方法和计算定义。它们不构成阶段 7 的替代方法，也不恢复旧的指标平铺流程。当前运行完成已正式定义的阶段 1–7 后，可以根据实际字段、数据日期和证据匹配度，选择仍然有效的组件作为辅助分析并写入正式报告。

## 保留组件

- `cerebro-organic-coverage.md`：阶段 4.4 使用的 H10 自然排名 1–5、1–10、1–50、自然词数、搜索量、平均竞品数量和需求竞争比定义；
- `keyword-click-conversion.md`：Opportunity Explorer Niche 搜索词点击、订单和点击转化推算；
- `market-analysis-framework.md`：市场质量、竞争结构、需求与趋势的旧分析框架；
- `data-readiness.md`、`data-location-map.md`、`evidence-priority.md`：数据就绪、路径和证据优先级；
- `asin-niche-discovery.md`、`market-scope-validation.md`：ASIN→Niche 关系和市场范围验证辅助规则；
- `benchmark-vs-leader.md`：Benchmark、Leader、Market 三角比较；
- `consumer-need-analysis.md`：阶段 5 使用的正负面反馈、退货与消费者需求地图证据整理规则；阶段 6 只承接其已确认的 P0/P1 需求；
- `improvement-opportunity-validation.md`：改良机会的市场验证与 P0/P1/P2 分类；
- `html-data-visualization.md`、`report-language.md`、`terminology-glossary.md`：正式报告视觉、中文显示和术语说明；
- `decision-framework.md`：最终 GO / CONDITIONAL GO / NO-GO 判定框架；
- `templates/report-outline.md`、`templates/html-report-style.md`、`templates/handoff-template.md`：正式报告与下游接口模板；当前只按可用证据选择相关部分，不得整套恢复为平铺模块。

## 使用边界

1. 阶段 1 只能使用与市场定义直接相关的产品本质、Niche 归属、头部商品和搜索意图证据；
2. 阶段 1、阶段 2、阶段 3、阶段 4、阶段 5、阶段 6 完成后，按阶段边界选择组件为辅助证据：阶段 2 只可使用搜索需求、关键词结构、同口径搜索→点击、Opportunity Explorer「占比数据」搜索转化率和真实趋势等需求证据；阶段 3 可使用真实销售/价格/新品/成本与利润资料；阶段 4 正式使用商品/品牌点击集中、头部壁垒、H10 自然覆盖、新品进入门槛和付费流量证据；阶段 5 正式使用评论、主题、退货、搜索意图、跨 ASIN 共性、解决程度和商业信号证据；阶段 6 正式使用阶段 5 P0/P1 需求、竞品解决程度、产品/供应链/IP/合规资料和消费者可感知性证据。缺失或不匹配时标记并继续，不用经验数字填空；
3. 辅助组件必须服务于完整商业问题，按主题组织，不能恢复旧的“看到什么指标就平铺什么指标”的报告结构；
4. 辅助组件不得被表述为阶段 7 的正式决策依据，也不得替代阶段 7 已定义的市场进入决策规则；
5. 不得因为旧 HTML 报告或旧模板已经存在，就跳过数据核验、静默消除冲突或把推断升级为事实；
6. 组件中的推断仍必须保留 `[数据支持]`、`[分析推断]`、`[待验证]`、`[证据不足]`、`[数据冲突]` 状态。
