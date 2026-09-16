"""DATA ONLY builder for complete Stage 6-2 advertising fact packages.

Provider adapters must supply explicit canonical field mappings from their
discovered schema. This module never queries Amazon and never makes decisions.
"""
from __future__ import annotations

import csv
import html
import json
import math
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from stage6_artifact_contract import (
    assert_new_outputs,
    make_artifact_metadata,
    new_run_context,
    timestamped_output_path,
    write_metadata_sidecar,
)
from scripts.campaign_scope_contract import CampaignScopeError, build_campaign_scope, campaign_is_in_scope, select_campaigns
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_batch,
)

SKILL_ID = "hzp-amz-6-2-product-operations-monitoring"
OUTPUT_ROOT = "6-2_产品经营监控与诊断"

METRICS = ("Impressions", "Clicks", "Spend", "Orders", "Sales")
RATIOS = ("CTR", "CPC", "CVR", "ACoS", "ROAS")
CAMPAIGN_SCHEMA = ["Date", "DataCompleteness", "CampaignId", "CampaignName", "ProductCode", "VariantCode", "AdType", "TechnicalRole", "TargetType", "ControlMode", "IntentCode", "Status", "DailyBudget", "Impressions", "Clicks", "CTR", "CPC", "Spend", "Orders", "Sales", "CVR", "ACoS", "ROAS"]
INTENT_SCHEMA = ["Date", "DataCompleteness", "IntentCode", "精准泛词", "控制方式", "Impressions", "Clicks", "CTR", "CPC", "Spend", "Orders", "Sales", "CVR", "ACoS", "ROAS", "TargetCount", "SearchTermCount", "ConvertingSearchTermCount"]
TARGET_SCHEMA = ["Date", "DataCompleteness", "BattleUnitId", "CampaignId", "CampaignName", "AdGroupId", "AdGroupName", "TargetId", "IntentCode", "精准泛词", "控制方式", "TargetType", "TargetValue", "MatchType", "Bid", "Status", "Impressions", "Clicks", "CTR", "CPC", "Spend", "Orders", "Sales", "CVR", "ACoS", "ROAS"]
SEARCH_SCHEMA = ["Date", "DataCompleteness", "SearchTerm", "CampaignId", "CampaignName", "AdGroupId", "TargetId", "BattleUnitId", "IntentCode", "精准泛词", "TargetType", "TargetValue", "MatchType", "Impressions", "Clicks", "Spend", "Orders", "Sales", "CTR", "CPC", "CVR", "ACoS", "ROAS"]
OUTPUTS = {
    "campaign": ("广告活动运行数据", CAMPAIGN_SCHEMA),
    "intent": ("意图市场运行数据", INTENT_SCHEMA),
    "target": ("投放目标运行数据", TARGET_SCHEMA),
    "search_term": ("搜索词运行数据", SEARCH_SCHEMA),
}


class PackageError(ValueError):
    """Stable error code as .args[0]."""


def _decimal(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise PackageError("62_SCHEMA_INVALID") from None
    if not math.isfinite(result):
        raise PackageError("62_SCHEMA_INVALID")
    return result


def _sum(values: Iterable[Any]) -> float | None:
    items = list(values)
    if not items or any(_decimal(value) is None for value in items):
        return None
    return sum(float(value) for value in items)


def _ratio(numerator: Any, denominator: Any) -> float | None:
    a, b = _decimal(numerator), _decimal(denominator)
    return None if a is None or b in (None, 0) else a / b


def default_stable_cutoff_date(today: date | None = None) -> date:
    """Return yesterday in the caller's local calendar context."""
    return (today or date.today()) - timedelta(days=1)


def _derive_metrics(row: Mapping[str, Any], tolerance: float | None, issues: list[str]) -> dict[str, Any]:
    result = dict(row)
    computed = {
        "CTR": _ratio(row.get("Clicks"), row.get("Impressions")),
        "CPC": _ratio(row.get("Spend"), row.get("Clicks")),
        "CVR": _ratio(row.get("Orders"), row.get("Clicks")),
        "ACoS": _ratio(row.get("Spend"), row.get("Sales")),
        "ROAS": _ratio(row.get("Sales"), row.get("Spend")),
    }
    for key, derived in computed.items():
        raw = _decimal(row.get(key))
        if raw is not None and derived is not None:
            if tolerance is None:
                issues.append("METRIC_RECONCILIATION_TOLERANCE_UNRESOLVED")
            elif abs(raw - derived) > tolerance:
                issues.append("METRIC_RECONCILIATION_MISMATCH")
        result[key] = raw if raw is not None else derived
    return result


def _validate_fact(row: Mapping[str, Any], *, clicks_le_impressions: bool = True) -> None:
    for metric in METRICS:
        value = _decimal(row.get(metric))
        if value is not None and value < 0:
            raise PackageError("62_DATA_INTEGRITY_FAILED")
    impressions, clicks = _decimal(row.get("Impressions")), _decimal(row.get("Clicks"))
    if clicks_le_impressions and impressions is not None and clicks is not None and clicks > impressions:
        raise PackageError("62_DATA_INTEGRITY_FAILED")


def map_provider_rows(
    rows: Iterable[Mapping[str, Any]],
    field_map: Mapping[str, str],
    *,
    source_grain: str,
    date_field: str | None = None,
) -> list[dict[str, Any]]:
    """Map discovered provider fields to canonical names; no aliases are guessed."""
    if source_grain not in {"DAY", "WINDOW"}:
        raise PackageError("62_SCHEMA_INVALID")
    mapped = []
    for source in rows:
        row = {canonical: source.get(provider) for canonical, provider in field_map.items()}
        if source_grain == "DAY":
            if not date_field or date_field not in source:
                raise PackageError("62_SCHEMA_INVALID")
            try:
                row_date = date.fromisoformat(str(source[date_field])[:10])
                row["Date"] = row_date.isoformat()
                row["DataCompleteness"] = "TODAY_PARTIAL" if row_date == date.today() else "COMPLETE_DAY"
            except (TypeError, ValueError):
                raise PackageError("62_SCHEMA_INVALID") from None
        else:
            row["Date"] = None
            row["SourceGrain"] = "WINDOW"
            row["DataCompleteness"] = "SOURCE_WINDOW"
        mapped.append(row)
    return mapped


def build_attribution_indexes(
    identity_events: Iterable[Mapping[str, Any]],
    battle_units: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    """Resolve Amazon IDs via verified 6-1 manifest then exact 605 BattleUnitId."""
    unit_index: dict[str, dict[str, Any]] = {}
    for row in battle_units:
        unit_id = str(row.get("作战单元ID") or row.get("BattleUnitId") or "").strip()
        if not unit_id or unit_id in unit_index:
            raise PackageError("BATTLE_UNIT_JOIN_FAILED")
        unit_index[unit_id] = {
            "intent_code": str(row.get("意图代码") or row.get("IntentCode") or "").strip(),
            "intent_term": str(row.get("精准泛词") or "").strip(),
            "control_mode": str(row.get("控制方式") or "").strip(),
        }
    targets: dict[str, dict[str, Any]] = {}
    adgroups: dict[str, dict[str, Any]] = {}
    campaigns: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    event_rows = [event for event in identity_events if event.get("event") == "ENTITY_IDENTITY_VERIFIED"]
    for event in event_rows:
        if str(event.get("entity_type") or "").casefold() == "ad_group":
            amazon_id = str(event.get("amazon_id") or "").strip()
            if amazon_id:
                adgroups[amazon_id] = {"logical_id": event.get("logical_id"), "campaign_id": event.get("parent_amazon_id"), "campaign_logical_id": event.get("parent_logical_id")}
    for event in event_rows:
        if str(event.get("entity_type") or "").casefold() == "campaign":
            amazon_id = str(event.get("amazon_id") or "").strip()
            if amazon_id:
                campaigns[amazon_id] = {"intent_code": event.get("intent_code"), "control_mode": event.get("control_mode"), "logical_id": event.get("logical_id"), "product_code": event.get("product_code"), "var_code": event.get("var_code"), "ad_type": event.get("ad_type"), "technical_role": event.get("technical_role"), "target_type": event.get("target_type")}
    for event in event_rows:
        amazon_id = str(event.get("amazon_id") or "").strip()
        if not amazon_id:
            errors.append("CAMPAIGN_IDENTITY_UNRESOLVED")
            continue
        kind = str(event.get("entity_type") or "").casefold()
        if kind == "target":
            battle_id = str(event.get("battle_unit_id") or "").strip()
            facts = unit_index.get(battle_id)
            group_id = str(event.get("parent_amazon_id") or "").strip()
            group = adgroups.get(group_id)
            campaign_id = str(group.get("campaign_id") or "").strip() if group else ""
            if facts and facts["intent_code"] and group and campaign_id in campaigns and group.get("logical_id") == event.get("parent_logical_id"):
                value = {**facts, "battle_unit_id": battle_id, "control_mode": event.get("control_mode") or facts["control_mode"], "target_type": event.get("target_type"), "target_value": event.get("target_value"), "match_type": event.get("match_type"), "logical_id": event.get("logical_id"), "ad_group_id": group_id, "campaign_id": campaign_id}
                if amazon_id in targets and targets[amazon_id] != value:
                    errors.append("TARGET_IDENTITY_UNRESOLVED")
                targets[amazon_id] = value
            else:
                errors.extend(["BATTLE_UNIT_JOIN_FAILED", "TARGET_IDENTITY_UNRESOLVED"])
    return targets, campaigns, errors


def _attrib(row: Mapping[str, Any], target_index: Mapping[str, Mapping[str, Any]], *, id_key: str = "TargetId") -> dict[str, Any]:
    result = dict(row)
    target_id = str(row.get(id_key) or "").strip()
    identity = target_index.get(target_id)
    if identity:
        mismatched_parent = any(row.get(key) not in (None, "", expected) for key, expected in (("CampaignId", identity.get("campaign_id")), ("AdGroupId", identity.get("ad_group_id"))))
        if mismatched_parent:
            result.update({"BattleUnitId": None, "IntentCode": "UNMAPPED", "精准泛词": "UNMAPPED", "控制方式": "UNMAPPED", "AttributionStatus": "INTENT_ATTRIBUTION_UNRESOLVED"})
            return result
        if result.get("CampaignId") in (None, ""):
            result["CampaignId"] = identity.get("campaign_id")
        if result.get("AdGroupId") in (None, ""):
            result["AdGroupId"] = identity.get("ad_group_id")
        result.update({"BattleUnitId": identity["battle_unit_id"], "IntentCode": identity["intent_code"], "精准泛词": identity["intent_term"], "控制方式": identity["control_mode"], "TargetType": result.get("TargetType") or identity.get("target_type"), "TargetValue": result.get("TargetValue") or identity.get("target_value"), "MatchType": result.get("MatchType") or identity.get("match_type"), "AttributionStatus": "MAPPED"})
    else:
        result.update({"BattleUnitId": None, "IntentCode": "UNMAPPED", "精准泛词": "UNMAPPED", "控制方式": "UNMAPPED", "AttributionStatus": "INTENT_ATTRIBUTION_UNRESOLVED"})
    return result


def _aggregate_metric(rows: Sequence[Mapping[str, Any]], key: str, tolerance: float | None, issues: list[str]) -> Any:
    total = _sum(row.get(key) for row in rows)
    return total


def _unique(rows: Sequence[Mapping[str, Any]], key: Any) -> list[dict[str, Any]]:
    seen: set[Any] = set()
    result = []
    for source in rows:
        row = dict(source)
        identity = key(row)
        if identity in seen:
            raise PackageError("62_DATA_INTEGRITY_FAILED")
        seen.add(identity)
        result.append(row)
    return result


def _intent_rows(target_rows: Sequence[Mapping[str, Any]], search_rows: Sequence[Mapping[str, Any]], tolerance: float | None, issues: list[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    term_grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        grouped[(row.get("Date"), row.get("IntentCode"), row.get("精准泛词"), row.get("控制方式"))].append(dict(row))
    for row in search_rows:
        term_grouped[(row.get("Date"), row.get("IntentCode"), row.get("精准泛词"), row.get("控制方式"))].append(dict(row))
    result = []
    for key, items in grouped.items():
        if len({row.get("DataCompleteness") for row in items}) > 1:
            raise PackageError("62_DATA_INTEGRITY_FAILED")
        sums = {metric: _aggregate_metric(items, metric, tolerance, issues) for metric in METRICS}
        aggregate = _derive_metrics(sums, tolerance, issues)
        terms = term_grouped.get(key, [])
        unique_terms = {(row.get("SearchTerm"), row.get("TargetId")) for row in terms}
        converting_count = _converting_search_term_count(terms)
        result.append({"Date": key[0], "DataCompleteness": items[0].get("DataCompleteness"), "IntentCode": key[1], "精准泛词": key[2], "控制方式": key[3], **sums, **{name: aggregate.get(name) for name in RATIOS}, "TargetCount": len({row.get("TargetId") for row in items}), "SearchTermCount": len(unique_terms), "ConvertingSearchTermCount": converting_count})
    for key, terms in term_grouped.items():
        if key not in grouped:
            if len({row.get("DataCompleteness") for row in terms}) > 1:
                raise PackageError("62_DATA_INTEGRITY_FAILED")
            # Search-term facts can exist without Target-level metrics; do not invent them.
            result.append({"Date": key[0], "DataCompleteness": terms[0].get("DataCompleteness"), "IntentCode": key[1], "精准泛词": key[2], "控制方式": key[3], **{metric: None for metric in METRICS}, **{ratio: None for ratio in RATIOS}, "TargetCount": 0, "SearchTermCount": len({(row.get("SearchTerm"), row.get("TargetId")) for row in terms}), "ConvertingSearchTermCount": _converting_search_term_count(terms)})
    return sorted(result, key=lambda row: (str(row.get("Date") or ""), str(row.get("IntentCode") or "")))


def _converting_search_term_count(rows: Sequence[Mapping[str, Any]]) -> int | None:
    if not rows:
        return 0
    orders = [_decimal(row.get("Orders")) for row in rows]
    if any(value is None for value in orders):
        return None
    return sum(1 for value in orders if value > 0)


def _project(rows: Sequence[Mapping[str, Any]], schema: Sequence[str]) -> list[dict[str, Any]]:
    return [{name: row.get(name) for name in schema} for row in rows]


def build_fact_tables(
    campaign_rows: Iterable[Mapping[str, Any]],
    target_rows: Iterable[Mapping[str, Any]],
    search_term_rows: Iterable[Mapping[str, Any]],
    *,
    identity_events: Iterable[Mapping[str, Any]],
    battle_units: Iterable[Mapping[str, Any]],
    metric_tolerance: float | None,
    clicks_le_impressions_supported: bool = True,
    campaign_scope: Mapping[str, str] | None = None,
    scope_coverage: Mapping[str, Any] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    issues: list[str] = []
    t_index, campaign_index, identity_issues = build_attribution_indexes(identity_events, battle_units)
    issues.extend(identity_issues)
    campaigns = _unique([dict(row) for row in campaign_rows], lambda row: (row.get("Date"), row.get("CampaignId")))
    targets0 = _unique([dict(row) for row in target_rows], lambda row: (row.get("Date"), row.get("TargetId")))
    terms0 = _unique([dict(row) for row in search_term_rows], lambda row: (row.get("Date"), row.get("SearchTerm"), row.get("TargetId")))
    scope_meta: dict[str, Any] = {}
    if campaign_scope:
        if not scope_coverage or any(scope_coverage.get(key) != campaign_scope.get(key) for key in ("ProductCode", "CampaignTag", "CampaignPrefix")):
            raise PackageError("RUNTIME_SCOPE_MISMATCH")
        matched_ids = {str(value) for value in scope_coverage.get("MatchedCampaignIds", [])}
        if not matched_ids:
            raise PackageError("NO_CAMPAIGN_MATCHED")
        before = (len(campaigns), len(targets0), len(terms0))
        campaigns = [row for row in campaigns if str(row.get("CampaignId")) in matched_ids and campaign_is_in_scope(row.get("CampaignName"), campaign_scope["CampaignPrefix"])]
        targets0 = [row for row in targets0 if str(row.get("CampaignId")) in matched_ids]
        terms0 = [row for row in terms0 if str(row.get("CampaignId")) in matched_ids]
        if before != (len(campaigns), len(targets0), len(terms0)):
            issues.append("SCOPE_CONTAMINATION")
        scope_meta = dict(scope_coverage)
    if not campaigns and not targets0 and not terms0:
        issues.append("62_EMPTY_DATA")
    targets = [_attrib(row, t_index) for row in targets0]
    terms = [_attrib(row, t_index) for row in terms0]
    if any(not row.get("TargetId") for row in terms):
        issues.append("SEARCH_TERM_GRAIN_UNSUPPORTED")
    allowed_intents = {facts["intent_code"] for facts in t_index.values() if facts.get("intent_code")}
    # Campaign attribution is copied only from verified Campaign ID lineage.
    # A shared campaign remains a single shared fact row; no CampaignName parsing.
    campaign_identity_index = campaign_index
    for row in campaigns:
        identity = campaign_identity_index.get(str(row.get("CampaignId") or ""))
        if not identity:
            issues.append("CAMPAIGN_IDENTITY_UNRESOLVED")
            row.update({"ControlMode": "UNMAPPED", "IntentCode": "UNMAPPED"})
            continue
        for output_key, identity_key in (("ProductCode", "product_code"), ("VariantCode", "var_code"), ("AdType", "ad_type"), ("TechnicalRole", "technical_role"), ("TargetType", "target_type")):
            if identity.get(identity_key) is not None:
                row[output_key] = identity[identity_key]
        if identity and identity.get("control_mode") == "共享":
            row.update({"ControlMode": "共享", "IntentCode": "SHARED"})
        elif identity and identity.get("control_mode") == "独立" and identity.get("intent_code") in allowed_intents:
            row.update({"ControlMode": "独立", "IntentCode": identity["intent_code"]})
        else:
            row.update({"ControlMode": "UNMAPPED", "IntentCode": "UNMAPPED"})
    for rows in (campaigns, targets, terms):
        for row in rows:
            _validate_fact(row, clicks_le_impressions=clicks_le_impressions_supported)
    campaigns = [_derive_metrics(row, metric_tolerance, issues) for row in campaigns]
    targets = [_derive_metrics(row, metric_tolerance, issues) for row in targets]
    terms = [_derive_metrics(row, metric_tolerance, issues) for row in terms]
    intents = _intent_rows(targets, terms, metric_tolerance, issues)
    tables = {
        "campaign": _project(campaigns, CAMPAIGN_SCHEMA),
        "intent": _project(intents, INTENT_SCHEMA),
        "target": _project(targets, TARGET_SCHEMA),
        "search_term": _project(terms, SEARCH_SCHEMA),
    }
    unmapped_targets = sum(1 for row in targets if row.get("IntentCode") == "UNMAPPED")
    mapped_targets = len(targets) - unmapped_targets
    unmapped_terms = sum(1 for row in terms if row.get("IntentCode") == "UNMAPPED")
    mapped_terms = len(terms) - unmapped_terms
    if unmapped_targets or unmapped_terms:
        issues.extend(["INTENT_ATTRIBUTION_INCOMPLETE", "INTENT_ATTRIBUTION_UNRESOLVED"])
    if unmapped_targets:
        issues.append("TARGET_IDENTITY_UNRESOLVED")
    counts = {"CampaignRecordCount": len(campaigns), "IntentRecordCount": len(intents), "TargetRecordCount": len(targets), "SearchTermRecordCount": len(terms), "UnmappedTargetCount": unmapped_targets, "MappedTargetCount": mapped_targets, "UnmappedSearchTermCount": unmapped_terms, "MappedSearchTermCount": mapped_terms}
    status = "FULL_SUCCESS" if not issues else "PARTIAL_SUCCESS"
    return tables, {"Run_Status": status, "Issues": sorted(set(issues)), **counts, "CampaignIdentityCount": len(campaign_index), **scope_meta}


def select_runtime_campaign_scope(campaign_inventory: Iterable[Mapping[str, Any]], product_code: str, campaign_tag: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Filter the live Campaign inventory before any child-entity/performance query."""
    try:
        scope = build_campaign_scope(product_code, campaign_tag)
        return select_campaigns(campaign_inventory, scope)
    except CampaignScopeError as exc:
        raise PackageError(str(exc)) from None


def filter_fact_tables_to_scope(tables: Mapping[str, Sequence[Mapping[str, Any]]], scope: Mapping[str, str], matched_campaign_ids: Iterable[str]) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    allowed = {str(value) for value in matched_campaign_ids}
    campaigns0 = [dict(row) for row in tables.get("campaign", [])]
    campaigns = [row for row in campaigns0 if str(row.get("CampaignId") or "") in allowed and campaign_is_in_scope(row.get("CampaignName"), scope["CampaignPrefix"])]
    targets0 = [dict(row) for row in tables.get("target", [])]
    terms0 = [dict(row) for row in tables.get("search_term", [])]
    targets = [row for row in targets0 if str(row.get("CampaignId") or "") in allowed]
    terms = [row for row in terms0 if str(row.get("CampaignId") or "") in allowed]
    intent_codes = {str(row.get("IntentCode") or "") for row in targets if row.get("IntentCode")}
    intents0 = [dict(row) for row in tables.get("intent", [])]
    intents = [row for row in intents0 if str(row.get("IntentCode") or "") in intent_codes]
    changed = (len(campaigns), len(targets), len(terms), len(intents)) != (len(campaigns0), len(targets0), len(terms0), len(intents0))
    return {"campaign": campaigns, "intent": intents, "target": targets, "search_term": terms}, (["SCOPE_CONTAMINATION"] if changed else [])


def _csv_bytes(path: Path, schema: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=schema, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) if row.get(key) is not None else "" for key in schema})


def _sum_display(rows: Sequence[Mapping[str, Any]], key: str) -> float | None:
    return _sum(row.get(key) for row in rows)


def _window_views(tables: Mapping[str, Sequence[Mapping[str, Any]]], stable_cutoff: date) -> dict[str, Any]:
    names = {"YESTERDAY": 1, "3D": 3, "7D": 7, "14D": 14, "30D": 30, "SINCE_LAUNCH": None}
    views = {}
    all_dates = []
    layer_dates: dict[str, list[date]] = {}
    for rows in tables.values():
        for row in rows:
            raw = row.get("Date")
            if raw:
                try:
                    all_dates.append(date.fromisoformat(str(raw)[:10]))
                except ValueError:
                    continue
    min_date = min(all_dates) if all_dates else None
    for key, rows in tables.items():
        layer_dates[key] = []
        for row in rows:
            if row.get("Date"):
                try:
                    layer_dates[key].append(date.fromisoformat(str(row["Date"])[:10]))
                except ValueError:
                    continue
    for name, days in names.items():
        start = min_date if days is None else stable_cutoff - timedelta(days=days - 1)
        def pick(key, rows):
            # Window-grain facts remain available as their own source window;
            # they are never split into invented days.
            if not layer_dates[key]:
                return [dict(row) for row in rows]
            return [dict(row) for row in rows if row.get("Date") and start <= date.fromisoformat(str(row["Date"])[:10]) <= stable_cutoff]
        selected = {key: pick(key, rows) for key, rows in tables.items()}
        campaign = selected["campaign"]
        totals = {key: _sum_display(campaign, key) for key in METRICS}
        totals.update({"CTR": _ratio(totals.get("Clicks"), totals.get("Impressions")), "CPC": _ratio(totals.get("Spend"), totals.get("Clicks")), "CVR": _ratio(totals.get("Orders"), totals.get("Clicks")), "ACoS": _ratio(totals.get("Spend"), totals.get("Sales")), "ROAS": _ratio(totals.get("Sales"), totals.get("Spend"))})
        grains = {key: "DAY" if layer_dates[key] else "SOURCE_WINDOW" for key in tables}
        views[name] = {"start": start.isoformat() if all_dates and start else None, "end": stable_cutoff.isoformat() if all_dates else None, "availableStart": min_date.isoformat() if min_date else None, "availableEnd": max(all_dates).isoformat() if all_dates else None, "grain": "DAY" if all_dates and all(grain == "DAY" for grain in grains.values()) else ("SOURCE_WINDOW" if not all_dates else "MIXED"), "grainByLayer": grains, "kpi": totals, "tables": selected}
    partial = {key: [dict(row) for row in rows if row.get("DataCompleteness") == "TODAY_PARTIAL"] for key, rows in tables.items()}
    if any(partial.values()):
        campaign = partial.get("campaign", [])
        totals = {key: _sum_display(campaign, key) for key in METRICS}
        totals.update({"CTR": _ratio(totals.get("Clicks"), totals.get("Impressions")), "CPC": _ratio(totals.get("Spend"), totals.get("Clicks")), "CVR": _ratio(totals.get("Orders"), totals.get("Clicks")), "ACoS": _ratio(totals.get("Spend"), totals.get("Sales")), "ROAS": _ratio(totals.get("Sales"), totals.get("Spend"))})
        views["TODAY_PARTIAL"] = {"start": date.today().isoformat(), "end": date.today().isoformat(), "availableStart": date.today().isoformat(), "availableEnd": date.today().isoformat(), "grain": "TODAY_PARTIAL", "grainByLayer": {key: "TODAY_PARTIAL" if partial[key] else "NO_TODAY_DATA" for key in tables}, "kpi": totals, "tables": partial}
    return views


def _render_html(title: str, payload: Mapping[str, Any]) -> str:
    safe_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>body{{font:14px/1.5 system-ui,'Microsoft YaHei',sans-serif;margin:24px;color:#1f2937;background:#f7f8fa}}h1,h2{{margin:0 0 12px}}section{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:18px;margin:16px 0;overflow:auto}}.bar{{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}}button{{padding:7px 12px;background:white;border:1px solid #cbd5e1;border-radius:5px;cursor:pointer}}button[aria-pressed=true]{{background:#e8eef6}}.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}}.kpi{{border:1px solid #e5e7eb;padding:10px;border-radius:6px}}.label{{color:#64748b;font-size:12px}}.value{{font-size:18px;font-variant-numeric:tabular-nums}}table{{border-collapse:collapse;width:100%;white-space:nowrap}}th,td{{border-bottom:1px solid #e5e7eb;padding:7px 9px;text-align:left}}th{{background:#f1f5f9}}.muted{{color:#64748b}}@media print{{body{{background:white;margin:0}}button{{display:none}}section{{break-inside:avoid}}}}</style></head><body>
<header><h1>{html.escape(title)}</h1><div id="lineage" class="muted"></div></header><nav class="bar" id="windows"></nav><section><h2>Executive Data Summary</h2><div id="period" class="muted"></div><div class="kpis" id="kpis"></div></section>
<section><h2>Campaign Data</h2><div id="campaign"></div></section><section><h2>Intent Data</h2><div id="intent"></div></section><section><h2>Target Data</h2><div id="target"></div></section><section><h2>Search Term Data</h2><div id="search_term"></div></section><section><h2>Data Coverage / Source / Lineage</h2><pre id="coverage"></pre></section>
<script id="fact-payload" type="application/json">{safe_json}</script><script>
const D=JSON.parse(document.getElementById('fact-payload').textContent);let active='30D';const labels={{YESTERDAY:'Yesterday','3D':'Last 3D','7D':'Last 7D','14D':'Last 14D','30D':'Last 30D',SINCE_LAUNCH:'Since Launch',TODAY_PARTIAL:'Today Partial'}};
function esc(v){{return String(v??'').replace(/[&<>\"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[c]))}}
function table(key){{const rows=(D.views[active].tables[key]||[]),schema=D.schemas[key];if(!rows.length)return '<p class="muted">No records for this window.</p>';return '<table><thead><tr>'+schema.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+schema.map(k=>'<td>'+esc(r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}}
function render(){{const v=D.views[active];document.getElementById('period').textContent=v.grain==='SOURCE_WINDOW'?`Source window ${{D.metadata.DataStartDate||'unknown'}} to ${{D.metadata.DataEndDate||'unknown'}} · day-level filtering unavailable · grain ${{v.grain}}`:v.grain==='MIXED'?`${{labels[active]}} · date-filtered range ${{v.start||'unknown'}} to ${{v.end||'unknown'}} · layer grains ${{JSON.stringify(v.grainByLayer)}} · source-window rows remain unsplit`:`${{labels[active]}} · ${{v.start||'source range'}} to ${{v.end}} · available ${{v.availableStart||'unknown'}} to ${{v.availableEnd||'unknown'}} · grain ${{v.grain}}`;
document.getElementById('kpis').innerHTML=['Spend','Sales','Orders','Impressions','Clicks','CTR','CPC','CVR','ACoS','ROAS'].map(k=>'<div class="kpi"><div class="label">'+esc(k)+'</div><div class="value">'+esc(v.kpi[k])+'</div></div>').join('');for(const k of ['campaign','intent','target','search_term'])document.getElementById(k).innerHTML=table(k);document.getElementById('coverage').textContent=JSON.stringify(D.metadata,null,2);document.querySelectorAll('button[data-window]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.window===active))}}
for(const [k,v] of Object.entries(labels)){{if(k==='TODAY_PARTIAL'&&!D.views[k])continue;const b=document.createElement('button');b.type='button';b.dataset.window=k;b.textContent=v;b.addEventListener('click',()=>{{active=k;render()}});document.getElementById('windows').appendChild(b)}}
document.getElementById('lineage').textContent=`Product ${{D.metadata.ProductCode}} · Marketplace ${{D.metadata.Marketplace}} · Run ${{D.metadata['6-2 Run ID']}} · Data source ${{D.metadata.DataSource}} · Query ${{D.metadata.QueryTime}}`;render();
</script></body></html>"""


def create_run_package(
    product_root: str | Path,
    product_code: str,
    identity: Mapping[str, Any],
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    run_result: Mapping[str, Any],
    *,
    data_source: str,
    query_time: str,
    data_start_date: str | None,
    data_end_date: str | None,
    stable_cutoff_date: str,
    today_partial_included: bool,
    source_grain_by_layer: Mapping[str, str],
    attribution_refresh_days: int | None,
    inputs: Sequence[Mapping[str, Any]] = (),
    campaign_scope: Mapping[str, str] | None = None,
    scope_coverage: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if set(tables) != set(OUTPUTS):
        raise PackageError("62_RUN_PACKAGE_INCOMPLETE")
    if not campaign_scope or not scope_coverage:
        raise PackageError("CAMPAIGN_TAG_MISSING")
    if campaign_scope:
        if campaign_scope.get("ProductCode") != product_code or not scope_coverage or any(scope_coverage.get(key) != campaign_scope.get(key) for key in ("ProductCode", "CampaignTag", "CampaignPrefix")):
            raise PackageError("RUNTIME_SCOPE_MISMATCH")
    root = Path(product_root)
    cutoff = date.fromisoformat(stable_cutoff_date)
    if cutoff > date.today():
        raise PackageError("62_DATE_RANGE_INVALID")
    tables, contamination = filter_fact_tables_to_scope(tables, campaign_scope, scope_coverage.get("MatchedCampaignIds", []))
    run_result = dict(run_result)
    if contamination:
        run_result["Issues"] = sorted(set(run_result.get("Issues", [])).union(contamination))
        run_result["Run_Status"] = "PARTIAL_SUCCESS"
    count_keys = {"campaign": "CampaignRecordCount", "intent": "IntentRecordCount", "target": "TargetRecordCount", "search_term": "SearchTermRecordCount"}
    for key, result_key in count_keys.items():
        run_result[result_key] = len(tables[key])
    context = new_run_context("6-2", SKILL_ID, product_code, now=now)
    skill_dir = Path(__file__).resolve().parents[1] / "hzp-amz-6-2-product-operations-monitoring"
    report_root = resolve_skill_report_dir(root, skill_dir)
    folder = report_root / context.run_timestamp
    paths: dict[str, Path] = {}
    for key, (report_name, _) in OUTPUTS.items():
        paths[key] = folder / build_report_filename(skill_dir, report_name, context.run_timestamp, "csv")
    html_path = folder / build_report_filename(skill_dir, "广告运行数据报告", context.run_timestamp, "html")
    manifest_path = folder / f"6-2_RunPackage_{context.run_timestamp}.json"
    report_error = validate_hzp_amz_report_batch([*paths.values(), html_path, manifest_path], root, skill_dir,
                                                  timestamp=context.run_timestamp, allow_run_folder=True)
    if report_error:
        raise PackageError(report_error)
    assert_new_outputs([*paths.values(), html_path, Path(str(html_path) + ".meta.json"), manifest_path])
    folder.mkdir(parents=True, exist_ok=False)
    schemas = {key: value[1] for key, value in OUTPUTS.items()}
    actual_today_partial = any(row.get("DataCompleteness") == "TODAY_PARTIAL" for rows in tables.values() for row in rows)
    if bool(today_partial_included) != actual_today_partial:
        raise PackageError("62_DATA_INTEGRITY_FAILED")
    for key, rows in tables.items():
        if key not in schemas:
            raise PackageError("62_SCHEMA_INVALID")
        for row in rows:
            if row.get("Date"):
                try:
                    row_date = date.fromisoformat(str(row["Date"])[:10])
                except ValueError:
                    raise PackageError("62_SCHEMA_INVALID") from None
                expected_completeness = "TODAY_PARTIAL" if row_date == date.today() else "COMPLETE_DAY"
                if row.get("DataCompleteness") != expected_completeness:
                    raise PackageError("62_DATA_INTEGRITY_FAILED")
            elif row.get("DataCompleteness") not in {"SOURCE_WINDOW", None}:
                raise PackageError("62_DATA_INTEGRITY_FAILED")
        _csv_bytes(paths[key], schemas[key], rows)
    # The human snapshot is built by reading back the just-written CSVs.
    csv_tables = {}
    for key, path in paths.items():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            csv_tables[key] = list(csv.DictReader(handle))
    views = _window_views(csv_tables, cutoff)
    metadata = {
        "Current Product": identity.get("ProductName"), "ProductCode": product_code,
        **(dict(campaign_scope or {})),
        **({key: scope_coverage.get(key) for key in ("AccountCampaignCount", "PrefixMatchedCampaignCount", "ExcludedCampaignCount", "MatchedCampaignIds")} if scope_coverage else {}),
        "Marketplace": identity.get("Marketplace"), "DataSource": data_source, "QueryTime": query_time,
        "DataStartDate": data_start_date, "DataEndDate": data_end_date,
        "StableCutoffDate": stable_cutoff_date, "TodayPartialIncluded": bool(today_partial_included),
        "AttributionRefreshDays": attribution_refresh_days,
        "AttributionRefreshStatus": "CONFIGURED" if attribution_refresh_days is not None else "UNRESOLVED",
        "CampaignRecordCount": run_result.get("CampaignRecordCount", 0), "IntentRecordCount": run_result.get("IntentRecordCount", 0),
        "TargetRecordCount": run_result.get("TargetRecordCount", 0), "SearchTermRecordCount": run_result.get("SearchTermRecordCount", 0),
        "UnmappedTargetCount": run_result.get("UnmappedTargetCount", 0), "MappedTargetCount": run_result.get("MappedTargetCount", 0),
        "UnmappedSearchTermCount": run_result.get("UnmappedSearchTermCount", 0), "MappedSearchTermCount": run_result.get("MappedSearchTermCount", 0),
        "6-2 Run ID": context.run_id, "GeneratedAt": context.generated_at,
        "SourceGrainByLayer": dict(source_grain_by_layer), "RunStatus": run_result.get("Run_Status"),
        "Issues": list(run_result.get("Issues") or []), "OutputFiles": [p.name for p in paths.values()] + [html_path.name],
    }
    payload = {"metadata": metadata, "schemas": schemas, "views": views}
    html_text = _render_html("广告运行数据报告", payload)
    with html_path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(html_text)
    package_meta = make_artifact_metadata(context, "ADVERTISING_FACT_PACKAGE", run_status=str(run_result.get("Run_Status") or "PARTIAL_SUCCESS"), inputs=inputs, output_assets=[p.name for p in paths.values()] + [html_path.name], extra={"DataStartDate": data_start_date, "DataEndDate": data_end_date, "StableCutoffDate": stable_cutoff_date, "SourceGrainByLayer": dict(source_grain_by_layer), "RunResult": dict(run_result), "CurrentIdentity": dict(identity)})
    package_meta.update(metadata)
    package_meta["Package_Schemas"] = schemas
    with manifest_path.open("x", encoding="utf-8", newline="") as handle:
        json.dump(package_meta, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    write_metadata_sidecar(html_path, package_meta)
    return {"status": "RUN_PACKAGE_WRITTEN", "run_id": context.run_id, "run_timestamp": context.run_timestamp, "directory": str(folder), "files": {**{k: str(v) for k, v in paths.items()}, "html": str(html_path), "manifest": str(manifest_path)}, "metadata": package_meta}


def resolve_latest_valid_62_package(product_root: str | Path, product_code: str, campaign_tag: str) -> dict[str, Any]:
    """Resolve a whole package by manifest Generated_At; never mix CSV runs."""
    skill_dir = Path(__file__).resolve().parents[1] / "hzp-amz-6-2-product-operations-monitoring"
    parent = resolve_skill_report_dir(product_root, skill_dir)
    candidates = []
    other_scope_candidates = []
    for folder in parent.iterdir() if parent.is_dir() else ():
        manifest = folder / f"6-2_RunPackage_{folder.name}.json"
        try:
            meta = json.loads(manifest.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if meta.get("Skill_ID") != SKILL_ID or meta.get("Product_Code") != product_code or meta.get("Report_Identity") != "ADVERTISING_FACT_PACKAGE" or meta.get("Run_Status") not in {"FULL_SUCCESS", "PARTIAL_SUCCESS"}:
            continue
        try:
            scope = build_campaign_scope(product_code, campaign_tag)
        except CampaignScopeError as exc:
            raise PackageError(str(exc)) from None
        scope_match = not any(meta.get(key) != scope[key] for key in scope)
        try:
            generated = datetime.fromisoformat(str(meta["Generated_At"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        asset_names = list(meta.get("Output_Assets") or [])
        stamp = str(meta.get("RUN_TIMESTAMP") or "")
        if not re.fullmatch(r"\d{8}_\d{6}", stamp) or folder.name != stamp or meta.get("RUN_ID") != f"6-2_{product_code}_{stamp}" or meta.get("Package_Schemas") != {key: value[1] for key, value in OUTPUTS.items()}:
            continue
        expected_names = {build_report_filename(skill_dir, display, stamp, "csv")
                          for display, _ in OUTPUTS.values()}
        expected_names.add(build_report_filename(skill_dir, "广告运行数据报告", stamp, "html"))
        if set(asset_names) != expected_names:
            continue
        by_kind = {}
        valid = True
        for key, (display, schema) in OUTPUTS.items():
            filename = next((name for name in asset_names if display in name and name.lower().endswith(".csv")), None)
            if not filename or not (folder / filename).is_file():
                valid = False
                break
            with (folder / filename).open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if list(reader.fieldnames or []) != schema:
                    valid = False
                    break
                by_kind[key] = list(reader)
        html_names = [name for name in asset_names if "广告运行数据报告" in name and name.lower().endswith(".html")]
        if not valid or len(html_names) != 1 or not (folder / html_names[0]).is_file() or not all((folder / name).is_file() for name in asset_names):
            continue
        expected_counts = {"campaign": meta.get("CampaignRecordCount"), "intent": meta.get("IntentRecordCount"), "target": meta.get("TargetRecordCount"), "search_term": meta.get("SearchTermRecordCount")}
        if any(expected_counts[key] is None or len(by_kind[key]) != int(expected_counts[key]) for key in OUTPUTS):
            continue
        try:
            sidecar = json.loads((folder / (html_names[0] + ".meta.json")).read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if sidecar.get("RUN_ID") != meta.get("RUN_ID") or sidecar.get("RUN_TIMESTAMP") != meta.get("RUN_TIMESTAMP"):
            continue
        try:
            html_text = (folder / html_names[0]).read_text(encoding="utf-8")
            match = re.search(r'<script id="fact-payload" type="application/json">(.*?)</script>', html_text, flags=re.S)
            embedded = json.loads(match.group(1)) if match else None
            cutoff = date.fromisoformat(str(meta["StableCutoffDate"]))
            rebuilt_views = _window_views(by_kind, cutoff)
        except (OSError, UnicodeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(embedded, dict) or embedded.get("schemas") != {key: value[1] for key, value in OUTPUTS.items()} or embedded.get("metadata", {}).get("6-2 Run ID") != meta.get("RUN_ID") or embedded.get("views") != rebuilt_views:
            continue
        (candidates if scope_match else other_scope_candidates).append((generated, folder, meta, by_kind))
    if not candidates:
        if other_scope_candidates:
            return {"status": "RUNTIME_SCOPE_MISMATCH", "package": None}
        return {"status": "62_RUN_PACKAGE_INCOMPLETE", "package": None}
    candidates.sort(key=lambda item: (item[0], item[1].name.casefold()), reverse=True)
    generated, folder, meta, tables = candidates[0]
    return {"status": "LATEST_VALID_62_PACKAGE_RESOLVED", "directory": str(folder), "run_id": meta.get("RUN_ID"), "generated_at": generated.isoformat(timespec="seconds"), "metadata": meta, "tables": tables}


def configured_attribution_refresh_days(value: str | None = None) -> int | None:
    """Read the configured source rule; never impose an arbitrary attribution window."""
    raw = value if value is not None else os.getenv("ATTRIBUTION_REFRESH_DAYS")
    if raw in (None, ""):
        return None
    try:
        days = int(raw)
    except (TypeError, ValueError):
        raise PackageError("ATTRIBUTION_REFRESH_CONFIG_INVALID") from None
    if days < 0:
        raise PackageError("ATTRIBUTION_REFRESH_CONFIG_INVALID")
    return days
