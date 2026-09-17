---
name: hzp-amz-6-3-advertising-data-report
description: 读取当前产品真实广告运行数据，生成带时间戳、可追溯的事实数据包与HTML/CSV报告；只做DATA，不做经营决策或广告写操作。
metadata:
  short-description: 广告运行事实数据层
---

# HZP Amazon 6-3｜广告运行事实数据报告

## 职责

6-3 是 Stage 6 的 DATA ONLY 层。它读取已验证的产品、变体、店铺、Marketplace 和广告身份，调用只读能力获取 Campaign、Ad Group、Keyword、Target、Search Term、Placement、Advertised Product、预算和表现事实，生成带 `RUN_ID` 与时间戳的完整 Run Package。

6-3 不判断广告好坏，不决定 Bid、Budget、Placement、Negative、暂停或扩词，也不调用 `prepare_change_plan`、`apply_change_plan`。经营判断交给 `hzp-amz-6-4-advertising-decision`；获批动作交给 `hzp-amz-6-5-advertising-optimization-action-executor`；产品级经营监控由 6-6 消费事实并路由。

## 输入与输出

- 输入：当前 Product Root、身份映射、SellerSpace/Amazon Ads 只读能力和明确的数据窗口。
- 输出目录：`[Product Root]/06_SKILL分析报告/6-3_广告运行事实数据/<YYYYMMDD_HHMMSS>/`。
- 使用共享 `scripts/ad_facts_package.py`，不得另建一套广告事实查询或身份解析层。
- 输出必须保留原始字段、字段语义、数据源、时间窗口、Freshness、聚合/去重状态和缺口；缺失值保持 NULL/明确缺失。
- 同一次运行的 JSON manifest、CSV 和 HTML 共用 `RUN_ID`、`RUN_TIMESTAMP`，历史包不覆盖。

## 路由

`6-1 PLAN → 6-2 BUILD → 6-3 DATA → 6-4 DECIDE → 人工批准/策略门 → 6-5 APPLY → 6-6 MONITOR`。

运行成功后调用 0-2 更新正式索引；事实包本身是 6-4 的核心输入。没有可靠身份或数据能力时报告证据缺口，不编造指标。
