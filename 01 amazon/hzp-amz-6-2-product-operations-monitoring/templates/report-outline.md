# 广告运行数据报告

> 本报告为CSV事实数据的人类阅读快照，不作经营判断或优化建议。

## Executive Data Summary

显示Product Code、Marketplace、实际Source Range/Grain、稳定截止日、Query Time、Run ID，以及Spend、Sales、Orders、Impressions、Clicks、CTR、CPC、CVR、ACoS、ROAS的实际值。分母为零/缺失时显示NULL。

## Campaign Data

展示同Run Campaign事实、Status、Budget和Provider实际返回的广告指标。共享Campaign只出现其源事实粒度，不按Intent复制。

## Intent Data

按经Target/Battle Unit/605 Plan确认的Intent显示聚合事实；包含UNMAPPED bucket，不做意图价值评价。

## Target Data

展示真实Target ID/Type/Value、Bid、Status、父级和运行指标。

## Search Term Data

展示消费者实际Search Term及其真实Target ID/匹配方式和源指标。Target和Search Term保留为不同层级。

## Data Coverage

列出日期范围、Source Grain、四层记录数、Mapped/UNMAPPED数量、数据质量Issue和Today Partial状态。

## Data Source / Lineage

列出实际只读Provider、实体、已确认字段映射、Query Time、Current Product身份、6-1身份清单、605计划Run、6-2 Run ID、来源窗口、Attribution Refresh Days或UNRESOLVED。
