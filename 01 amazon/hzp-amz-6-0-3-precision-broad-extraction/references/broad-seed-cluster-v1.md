# 6-0-3 Search Intent Market Map V3

## Input and identity

The only keyword input is the 6-0-2 C asset `去重去对标后 筛选后的精准词表` in
`06_SKILL分析报告/6-0-2_AI精准关键词识别/data/`. Select the maximum
`YYYYMMDD_HHMMSS` embedded in the exact filename and validate the minimum C schema.
RunPackage, Manifest, sidecar and file mtime are lineage aids only, not input gates.
A/B/D are never Intent inputs. Canonical keyword and Id must be unique; otherwise stop
with `INPUT_NOT_UNIQUE` or the corresponding input integrity error.

## Intent Brain

Phase A creates one semantic unit per keyword. Phase B globally reconciles candidate
clusters, merges equivalent Purchase Missions, keeps independently operable relationship,
occasion, product-type and compatibility tasks separate, assigns exactly one Primary Intent,
and creates at most one semantic parent. String containment, word count and common roots
cannot alone define an Intent or hierarchy. B is the source-of-truth mapping; A is derived
from B. Product context is loaded once when available and never invented.

## Program checks and metrics

The program validates Coverage and Aggregation Consistency, unique Ids, one primary per keyword, parent existence,
cycles (`PARENT_CYCLE_DETECTED`) and market-volume reconciliation. It computes direct and recursive subtree volume,
unique-source-record average competitor count, opportunity ratio, and all pass-through fields.
AI does not calculate market metrics. Parent and child totals overlap by containment and are
never summed across hierarchy levels.

## Outputs

Both UTF-8-BOM CSVs use the same timestamp and are published to the 6-0-3 `data/` directory;
previous valid batches remain under `历史数据/`.

Mapping B (`6-0-3_词对应的精准泛词_{timestamp}.csv`) fixed schema:

`Id｜词｜中文｜市场容量｜竞争产品数｜供需比｜自然排名｜精准泛词｜精准泛词中文｜PrimaryIntentId｜PrimaryIntentCode｜KeywordPurchaseMission｜Intent层级｜ParentIntentId｜父精准泛词｜IntentAssignmentReason｜ChallengeResult｜ChallengeReasonSummary`

Summary A (`6-0-3_精准泛词汇总_{timestamp}.csv`) fixed schema:

`精准泛词｜中文｜层级｜父精准泛词｜直接搜索量｜汇总搜索量｜平均竞品数｜意图机会比｜直接对应词数｜IntentId｜IntentCode｜IntentDefinition｜PrimaryPurchaseDriver｜ChallengeStatus｜ChallengeReasonSummary`

All mathematical fields are computed in code. The files are internal Search Intent evidence,
not Amazon sales share or a decision to launch advertising. 606 consumes the unified map for
Benchmark occupancy; 6-1 combines A/B with available 606 reality evidence.
