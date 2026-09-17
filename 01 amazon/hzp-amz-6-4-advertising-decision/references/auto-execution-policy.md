# 6-4 Auto-Execution Policy

这是 6-4 风险门控自动执行策略的集中配置契约。默认关闭真实自动写入；实际数值须由 HZP 明确授权，AI 不得自行推导或扩大。

```yaml
auto_execution_enabled: false
product_overrides: {}
max_bid_change_pct: configurable
max_top_change_pp: configurable
max_budget_change_pct: configurable
max_daily_incremental_spend: configurable
minimum_confidence: HIGH
minimum_clicks_and_evidence: dynamic_by_role_and_economics
cooldown_rules: dynamic_by_action_and_window
economic_guardrails: required
inventory_guardrails: required
allowlist:
  - small_bid_change
  - small_top_change
  - small_budget_change
```

进入 `AUTO_EXECUTE` 必须同时通过身份、数据新鲜度、归因延迟、证据、根因、Confidence、Allowlist、授权幅度、经济、Cooldown、库存和页面/Offer 检查。Pause、Negative、结构、新 Campaign、大幅调整、ASIN、Mapped_SKUs[]/Advertised_SKUs[]/Var_Code/Portfolio 变化默认不在 Allowlist，转 `NEED_APPROVAL`。任何策略扩大必须由用户明确授权并留下版本记录。
