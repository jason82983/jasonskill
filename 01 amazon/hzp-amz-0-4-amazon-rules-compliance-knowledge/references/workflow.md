# 0-4 工作流程

## 分类

问题归入 Amazon 平台规则、FBA物流与包装、产品合规与认证、类目准入、广告规则、账户店铺或出口税务/跨境。对非 Amazon 管辖的问题，明确转到对应美国政府机构。

## 来源与时效

来源优先级：Seller Central Help、Amazon官方公告/Staff、Amazon Ads Documentation、Seller University、Amazon Global Selling、Compliance Reference、美国政府机构、可靠专业资料、第三方经验。记录 URL、页面标题、发布日期/更新时间（若有）、访问日期和 Marketplace。高变动主题优先重新核验。

## 去重与更新

先按 `knowledge_id`，再按主题、Marketplace 和关键词判断 Same Knowledge Topic。无实质变化时更新 `last_verified_at`/索引状态；实质变化或原报告错误时保留历史并生成新 `version`，旧条目写 `superseded_by` 和 `[已被新版替代]`。

## 输出

即时问题不强制 HTML。专项报告包含结论、适用范围、规则分层、操作、禁止事项、误区、风险、官方来源、影响 Skills/产品类型、最后核验日期、Change Risk、Knowledge Status 和复核建议；不适用章节可省略。

## 0-3接口

元数据预留 `affected_skills`、`affected_product_types`、`change_risk` 和 `last_verified_at`。0-3 可据此生成提醒，但 0-4 不自行调度或发送提醒。
