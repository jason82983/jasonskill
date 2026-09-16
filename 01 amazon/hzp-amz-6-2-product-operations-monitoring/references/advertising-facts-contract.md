# 6-2 Advertising Facts Contract

Each run is isolated by required ProductCode and opaque CampaignTag. Resolve the exact trailing-dot CampaignPrefix and select the live Campaign inventory before any child-object/performance query. Package construction filters fact layers to the matched Campaign IDs; rows rejected by the defensive check add `SCOPE_CONTAMINATION`. Metadata/HTML records ProductCode, CampaignTag, CampaignPrefix, AccountCampaignCount, PrefixMatchedCampaignCount, ExcludedCampaignCount, and MatchedCampaignIds; these fields do not alter the four CSV schemas. A downstream resolver must request the same CampaignTag.

## Grain and schemas

The four UTF-8-with-BOM CSVs are one immutable Run Package. Core row grain is one entity per date when the provider supplies real daily facts; otherwise rows retain the provider window grain and `Date` is empty. `DataCompleteness` is `COMPLETE_DAY`, `TODAY_PARTIAL`, or `SOURCE_WINDOW`. Unavailable provider fields remain empty/NULL. Preserve source values and provider lineage in the package metadata; never estimate a missing metric.

| Asset | Grain | Fixed columns, in order |
|---|---|---|
| `广告活动运行数据` | Campaign × Date/window | `Date, DataCompleteness, CampaignId, CampaignName, ProductCode, VariantCode, AdType, TechnicalRole, TargetType, ControlMode, IntentCode, Status, DailyBudget, Impressions, Clicks, CTR, CPC, Spend, Orders, Sales, CVR, ACoS, ROAS` |
| `意图市场运行数据` | Intent × Date/window | `Date, DataCompleteness, IntentCode, 精准泛词, 控制方式, Impressions, Clicks, CTR, CPC, Spend, Orders, Sales, CVR, ACoS, ROAS, TargetCount, SearchTermCount, ConvertingSearchTermCount` |
| `投放目标运行数据` | Target × Date/window | `Date, DataCompleteness, BattleUnitId, CampaignId, CampaignName, AdGroupId, AdGroupName, TargetId, IntentCode, 精准泛词, 控制方式, TargetType, TargetValue, MatchType, Bid, Status, Impressions, Clicks, CTR, CPC, Spend, Orders, Sales, CVR, ACoS, ROAS` |
| `搜索词运行数据` | Search Term × Target × Date/window | `Date, DataCompleteness, SearchTerm, CampaignId, CampaignName, AdGroupId, TargetId, BattleUnitId, IntentCode, 精准泛词, TargetType, TargetValue, MatchType, Impressions, Clicks, Spend, Orders, Sales, CTR, CPC, CVR, ACoS, ROAS` |

`DataCompleteness` is a factual partition marker needed to keep returned current-day facts apart from complete dates; it does not turn a partial source into a complete day. A window-only source cannot be partitioned into complete-day and today rows unless the provider itself supplies that distinction.

## Provider discovery and mapping

Before each provider integration or when its schema changes, use read-only capability/field discovery. Keep explicit canonical→provider field mappings; do not infer semantics from similar-looking names. Confirm units, currency, date field, row grain, aggregation behavior, IDs, and whether Orders/Sales/ratios are actually supplied. If the provider returns aggregate ratios, retain and reconcile against the formula only when a repository-configured tolerance exists. Missing tolerance is `METRIC_RECONCILIATION_TOLERANCE_UNRESOLVED`, not an arbitrary threshold.

The current discovery snapshot found SellerSpace read capabilities for Campaign, Ad Group, Product Ads, Keyword, Target, and Search Query. Query parameters allow date ranges and date grouping for supported entities. The discovered field dictionary confirmed Campaign impressions/clicks/cost and query dates; Search Query impressions/clicks/cost; and Target IDs, value, bid, impressions/clicks/cost. It did **not** establish one universal returned date field, Search Query→Target ID linkage, or all Orders/Sales fields. Therefore adapters must confirm them from actual entity responses/field semantics before mapping. If Search Terms lack Target ID, retain facts as UNMAPPED and record `SEARCH_TERM_GRAIN_UNSUPPORTED` / `INTENT_ATTRIBUTION_UNRESOLVED`.

## Attribution rules

1. Match provider Campaign/Ad Group/Target IDs to verified IDs in 6-1's append-only execution identity manifest.
2. For Target, read the event's exact `BattleUnitId` and join to one approved 6-0-5 Battle Plan row. Read Intent Code, Intent text, and Control Mode from that row.
3. Search Term inherits Intent only through its actual `TargetId` and the Target mapping.
4. If any key is absent, ambiguous, stale beyond the configured refresh rule, or conflicting, retain source fact and set `UNMAPPED`; do not infer from CampaignName or split totals.
5. Shared Campaign facts remain one Campaign row. Intent aggregates are built from Target facts, not copied Campaign totals. Unmapped Target metrics remain represented in an `UNMAPPED` Intent bucket.

The 6-1 manifest stores verified entity IDs. New verified Target events also persist `battle_unit_id`, `intent_code`, `control_mode`, `target_type`, `target_value`, and `match_type`. `intent_code` on the manifest is a trace field; the approved 605 Battle Plan row remains the Intent definition source. Existing events without the new identity fields remain usable for entity identity but cannot establish Intent mapping.

## Calculations and data checks

The program computes from raw numerators/denominators:

| Metric | Calculation | Zero/missing denominator |
|---|---|---|
| CTR | Clicks / Impressions | NULL |
| CPC | Spend / Clicks | NULL |
| CVR | Orders / Clicks | NULL |
| ACoS | Spend / Sales | NULL |
| ROAS | Sales / Spend | NULL |

Never sum or average precomputed ratios to make a higher-level ratio. Recompute from summed facts. Keep raw provider ratio values available for reconciliation. Required checks: nonnegative Impressions/Clicks/Orders/Spend/Sales; Clicks≤Impressions only where provider semantics support it; unique entity/date grain; no Target/Search Term conflation; correct Intent joins; no duplicated Campaign spend across Intents; four output schemas and Run IDs agree; HTML values rebuild from the same-run CSVs; partial dates are explicitly marked. Core data errors cannot yield `FULL_SUCCESS`.

## Time windows

The default stable cutoff is yesterday in the local calendar. HTML default window is Last 30 Complete Days; when the provider has less data, show its actual available range (and include it as Since Launch when metadata establishes launch date). Windows are Yesterday, 3D, 7D, 14D, 30D, and Since Launch. Filter only real dated rows. Keep source-window rows unsegmented and label their source range and grain. If the available range cannot answer a selected duration, disclose that limitation. Never fill missing days with zero or interpolation.

If the source includes today, mark those rows `TODAY_PARTIAL`, separate them from complete-day rows, and set `TodayPartialIncluded=true` in metadata. If window-grain source mixes today with prior dates and cannot separate it, do not assert a partial-day split; record the limit.

Attribution backfill reads `ATTRIBUTION_REFRESH_DAYS` only when configured. If repository/provider policy has no value, report `AttributionRefreshStatus=UNRESOLVED`; do not choose 7 or 14 days by convention.

## Run Package / latest-valid

Use `scripts/stage6_artifact_contract.py` for common run identity, timestamp, metadata and no-overwrite. Business-specific package resolution lives in `scripts/ad_facts_package.py` and requires all assets from one folder/run:

```text
06_SKILL分析报告/6-2_产品经营监控与诊断/YYYYMMDD_HHMMSS/
├─ 6-2_{ProductCode}_广告活动运行数据_{timestamp}.csv
├─ 6-2_{ProductCode}_意图市场运行数据_{timestamp}.csv
├─ 6-2_{ProductCode}_投放目标运行数据_{timestamp}.csv
├─ 6-2_{ProductCode}_搜索词运行数据_{timestamp}.csv
├─ 6-2_{ProductCode}_广告运行数据报告_{timestamp}.html
├─ 6-2_{ProductCode}_广告运行数据报告_{timestamp}.html.meta.json
└─ 6-2_RunPackage_YYYYMMDD_HHMMSS.json
```

The HTML renderer reads the four just-written CSVs, computes selected window aggregates, and embeds all required data. It uses no runtime `fetch`, remote CSV lookup, or Amazon request. Latest-valid package selection validates Current Product, Skill ID, `ADVERTISING_FACT_PACKAGE`, accepted status, all four exact headers, HTML + sidecar Run ID/timestamp, and every named asset. Downstream consumers read this package once; they never find four latest files independently.

The package manifest records identity, provider/query time, source date range/grain, stable cutoff, current-day inclusion, configured refresh window or unresolved state, row/attribution coverage counts, run status/issues, schemas and output assets. Preserve any provider request lineage needed to reproduce the read without storing secrets.

## Status codes

Use applicable stable codes including `62_DATA_SOURCE_UNAVAILABLE`, `62_QUERY_FAILED`, `62_EMPTY_DATA`, `62_SCHEMA_INVALID`, `62_DATE_RANGE_INVALID`, `62_RUN_PACKAGE_INCOMPLETE`, `CAMPAIGN_IDENTITY_UNRESOLVED`, `TARGET_IDENTITY_UNRESOLVED`, `BATTLE_UNIT_JOIN_FAILED`, `INTENT_ATTRIBUTION_UNRESOLVED`, `INTENT_ATTRIBUTION_INCOMPLETE`, `METRIC_RECONCILIATION_MISMATCH`, `SEARCH_TERM_GRAIN_UNSUPPORTED`, `HTML_SOURCE_RUN_MISMATCH`, and `HTML_DATA_RECONCILIATION_FAILED`. Do not claim complete success if a required coverage, schema, reconciliation, or lineage check fails.
