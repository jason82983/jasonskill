---
name: hzp-amz-6-5-advertising-optimization-action-executor
description: 消费已批准的6-4广告经营决策包，校验身份、权限、能力和精确差异后执行并回读获批Amazon Ads动作；不重新决策。
metadata:
  short-description: 广告优化动作执行层
---

# HZP Amazon 6-5｜广告优化动作执行

## 职责边界

6-5 是 APPLY ONLY 层。它只消费最新有效、明确批准的 `hzp-amz-6-4-advertising-decision` 决策包和其中的精确动作，不重判经营策略、不新增目标、不自行扩词、不把建议当批准。新品初始广告创建仍由 6-2 BUILD 负责。

执行顺序固定为：解析批准包 → 再验证 Product/Var/ASIN/SKU/Store/Marketplace/Portfolio 与 Campaign ID → 检查 Provider capability → `prepare_change_plan` → Approved vs Prepared diff → 仅在授权条件满足时 `apply_change_plan` → read-back → 写入 Campaign 私有日志和每日汇总。任何身份冲突、Material Difference、权限不足或能力语义不明都必须阻断。

## 输出与审计

每个动作记录 Change ID、批准状态、变更前后值、Provider返回、read-back结果、失败原因和验证窗口；不修改历史报告。执行日志写入 `06_SKILL分析报告/广告表现汇报优化日志/`，不进入 0-2 正式报告索引。没有写能力时只报告“未执行”，不得假装成功。

## 路由

`6-3 DATA → 6-4 DECIDE → 6-5 APPLY → 6-6 MONITOR`。6-5 不替代 6-4 的经营判断，也不替代 6-6 的产品级监控。
