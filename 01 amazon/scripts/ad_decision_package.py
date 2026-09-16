"""Deterministic validation, evidence-context, history, and output helpers for 6-3 DECIDE.

This module does not query or mutate Amazon Ads. AI supplies the four decision
tables; this module validates them and writes an immutable, traceable package.
"""
from __future__ import annotations

import csv
import html
import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.stage6_artifact_contract import (  # noqa: E402
    assert_new_outputs,
    make_artifact_metadata,
    new_run_context,
    write_metadata_sidecar,
)
from scripts.campaign_scope_contract import CampaignScopeError, build_campaign_scope, campaign_is_in_scope
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_batch,
)

SKILL_ID = "hzp-amz-6-3-advertising-diagnosis-optimization"
OUTPUT_DIR = "6-3_广告诊断优化"
TABLE_FILES = {
    "intent": "意图市场优化决策",
    "campaign": "Campaign调整决策",
    "target": "投放目标优化决策",
    "search_term": "搜索词处理决策",
}
SCHEMAS: dict[str, tuple[str, ...]] = {
    "intent": (
        "IntentCode", "精准泛词", "当前作战任务", "当前控制方式", "当前阶段", "汇总搜索量", "意图机会比",
        "近3日Spend", "近7日Spend", "近14日Spend", "近30日Spend", "近7日Orders", "近14日Orders", "近30日Orders",
        "近7日Sales", "近14日Sales", "近30日Sales", "近7日ACoS", "近14日ACoS", "近30日ACoS",
        "近7日CVR", "近14日CVR", "近30日CVR", "距上次修改天数", "决策成熟度", "决策结果", "目标作战任务",
        "目标控制方式", "目标阶段", "决策原因", "下一观察条件", "确认状态",
    ),
    "campaign": (
        "CampaignId", "CampaignName", "AdType", "TechnicalRole", "TargetType", "控制方式", "IntentCode", "当前Budget",
        "当前Placement", "近3日Spend", "近7日Spend", "近14日Spend", "近30日Spend", "近7日Orders", "近14日Orders",
        "近30日Orders", "近7日ACoS", "近14日ACoS", "近30日ACoS", "距上次修改天数", "决策成熟度", "决策结果",
        "建议Budget", "建议Placement", "决策原因", "下一观察条件", "确认状态",
    ),
    "target": (
        "BattleUnitId", "TargetId", "CampaignId", "IntentCode", "精准泛词", "TargetType", "TargetValue", "MatchType",
        "当前Bid", "近3日Clicks", "近7日Clicks", "近14日Clicks", "近30日Clicks", "近3日Spend", "近7日Spend",
        "近14日Spend", "近30日Spend", "近7日Orders", "近14日Orders", "近30日Orders", "近7日Sales", "近14日Sales",
        "近30日Sales", "近7日ACoS", "近14日ACoS", "近30日ACoS", "距上次修改天数", "决策成熟度", "决策结果",
        "建议Bid", "目标控制方式", "决策原因", "下一观察条件", "确认状态",
    ),
    "search_term": (
        "SearchTerm", "TargetId", "BattleUnitId", "CampaignId", "IntentCode", "精准泛词", "SourceTarget", "MatchType",
        "FirstSeenDate", "LastSeenDate", "ActiveDays", "近7日Clicks", "近14日Clicks", "近30日Clicks", "近7日Spend",
        "近14日Spend", "近30日Spend", "近7日Orders", "近14日Orders", "近30日Orders", "近7日Sales", "近14日Sales",
        "近30日Sales", "决策成熟度", "决策结果", "建议处理方式", "决策原因", "下一观察条件", "确认状态",
    ),
}
MATURITY = {"可决策", "继续观察", "紧急处理"}
CONFIRMATION = {"待确认", "已批准", "暂缓"}
RESULTS = {
    "intent": {"保持", "继续观察", "放大", "收缩", "升级独立", "降级共享", "阶段升级", "阶段降级", "暂停候选"},
    "campaign": {"保持", "继续观察", "增加预算", "降低预算", "调整位置", "暂停候选"},
    "target": {"保持", "继续观察", "提高竞价", "降低竞价", "迁移候选", "暂停候选"},
    "search_term": {"保持观察", "收割候选", "否定候选"},
}


class DecisionPackageError(ValueError):
    """Stable decision-package error code in ``args[0]``."""


def _s(value: Any) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    return "" if value.upper() in {"NULL", "NONE", "DATA_NOT_AVAILABLE", "N/A"} else value


def _decimal(value: Any) -> Decimal | None:
    raw = _s(value).replace(",", "")
    if not raw:
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def read_csv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader.fieldnames or ()), list(reader)
    except (OSError, UnicodeError, csv.Error):
        raise DecisionPackageError("63_INPUT_SCHEMA_INVALID") from None


def _translate_upstream_error(exc: Exception, prefix: str) -> DecisionPackageError:
    code = str(exc).split(":", 1)[0]
    if code in {"CAMPAIGN_TAG_MISSING", "CAMPAIGN_TAG_INVALID", "CAMPAIGN_PREFIX_INVALID", "NO_CAMPAIGN_MATCHED", "RUNTIME_SCOPE_MISMATCH", "SCOPE_CONTAMINATION", "OUTSIDE_CAMPAIGN_SCOPE"}:
        return DecisionPackageError(code)
    if code in {"605_PLAN_NOT_APPROVED", "NO_APPROVED_BATTLE_PLAN", "605_PLAN_HAS_NO_APPROVED_BATTLE"}:
        return DecisionPackageError("EXECUTION_HANDOFF_INVALID")
    if isinstance(exc, FileNotFoundError) or code.endswith("NOT_FOUND") or "INCOMPLETE" in code:
        return DecisionPackageError("63_INPUT_NOT_FOUND")
    if "SCHEMA" in code:
        return DecisionPackageError("63_INPUT_SCHEMA_INVALID")
    if "MISMATCH" in code or "AMBIGUOUS" in code or "CONFLICT" in code:
        return DecisionPackageError("63_INPUT_RUN_MISMATCH")
    return DecisionPackageError(f"{prefix}:{code}")


def _asset_lineage(key: str, asset: Mapping[str, Any], skill: str) -> dict[str, Any]:
    meta = asset.get("metadata") or {}
    path = asset.get("path")
    return {
        "Input_Skill": skill,
        "Input_Report_Identity": meta.get("Report_Identity"),
        "Input_File_Name": Path(path).name if path else None,
        "Input_Run_ID": asset.get("run_id") or meta.get("RUN_ID"),
        "Input_Run_Timestamp": asset.get("run_timestamp") or meta.get("RUN_TIMESTAMP"),
        "Input_Generated_At": meta.get("Generated_At"),
        "Input_Record_Count": len(asset.get("rows") or []),
        "Input_Resolution_Method": asset.get("input_resolution_method") or asset.get("method") or "LATEST_VALID_RUN_BUNDLE",
        "Input_Key": key,
    }


def _load_606_resolver() -> Any:
    path = REPO_ROOT / "hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis" / "scripts" / "benchmark_intent_occupancy.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("hzp_606_benchmark_intent_occupancy", path)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def filter_facts_to_campaign_scope(tables: Mapping[str, Sequence[Mapping[str, Any]]], scope: Mapping[str, str]) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Keep only Campaign rows inside the exact prefix and child facts joined to their IDs."""
    campaigns = [dict(row) for row in tables.get("campaign", [])]
    allowed_ids = {str(row.get("CampaignId") or "") for row in campaigns
                   if campaign_is_in_scope(row.get("CampaignName"), scope["CampaignPrefix"])}
    issues = ["SCOPE_CONTAMINATION"] if len(allowed_ids) != len({str(row.get("CampaignId") or "") for row in campaigns}) else []
    scoped_campaigns = [row for row in campaigns if str(row.get("CampaignId") or "") in allowed_ids and campaign_is_in_scope(row.get("CampaignName"), scope["CampaignPrefix"])]
    scoped_targets = [dict(row) for row in tables.get("target", []) if str(row.get("CampaignId") or "") in allowed_ids and campaign_is_in_scope(row.get("CampaignName"), scope["CampaignPrefix"])]
    scoped_terms = [dict(row) for row in tables.get("search_term", []) if str(row.get("CampaignId") or "") in allowed_ids and campaign_is_in_scope(row.get("CampaignName"), scope["CampaignPrefix"])]
    intent_codes = {str(row.get("IntentCode") or "") for row in scoped_targets if row.get("IntentCode")}
    scoped_intents = [dict(row) for row in tables.get("intent", []) if str(row.get("IntentCode") or "") in intent_codes]
    if len(scoped_targets) != len(tables.get("target", [])) or len(scoped_terms) != len(tables.get("search_term", [])) or len(scoped_intents) != len(tables.get("intent", [])):
        if "SCOPE_CONTAMINATION" not in issues:
            issues.append("SCOPE_CONTAMINATION")
    return {"campaign": scoped_campaigns, "intent": scoped_intents, "target": scoped_targets, "search_term": scoped_terms}, issues


def filter_decision_tables_to_campaign_scope(tables: Mapping[str, Sequence[Mapping[str, Any]]], scope: Mapping[str, str]) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    campaigns = [dict(row) for row in tables.get("campaign", [])]
    allowed = {str(row.get("CampaignId") or "") for row in campaigns if campaign_is_in_scope(row.get("CampaignName"), scope["CampaignPrefix"])}
    issues = ["SCOPE_CONTAMINATION"] if len(allowed) != len({str(row.get("CampaignId") or "") for row in campaigns}) else []
    scoped_campaigns = [row for row in campaigns if str(row.get("CampaignId") or "") in allowed and campaign_is_in_scope(row.get("CampaignName"), scope["CampaignPrefix"])]
    scoped_targets = [dict(row) for row in tables.get("target", []) if str(row.get("CampaignId") or "") in allowed]
    scoped_terms = [dict(row) for row in tables.get("search_term", []) if str(row.get("CampaignId") or "") in allowed]
    intent_codes = {str(row.get("IntentCode") or "") for row in scoped_targets if row.get("IntentCode")}
    scoped_intents = [dict(row) for row in tables.get("intent", []) if str(row.get("IntentCode") or "") in intent_codes]
    if len(scoped_targets) != len(tables.get("target", [])) or len(scoped_terms) != len(tables.get("search_term", [])) or len(scoped_intents) != len(tables.get("intent", [])):
        if "SCOPE_CONTAMINATION" not in issues:
            issues.append("SCOPE_CONTAMINATION")
    return {"intent": scoped_intents, "campaign": scoped_campaigns, "target": scoped_targets, "search_term": scoped_terms}, issues


def resolve_decision_inputs(product_root: str | Path, product_code: str, campaign_tag: str) -> dict[str, Any]:
    """Resolve current Product inputs using existing 6-2/605/603/606 contracts."""
    root = Path(product_root).resolve()
    try:
        scope = build_campaign_scope(product_code, campaign_tag)
    except CampaignScopeError as exc:
        raise DecisionPackageError(str(exc)) from None
    try:
        from scripts.ad_facts_package import resolve_latest_valid_62_package
        facts = resolve_latest_valid_62_package(root, product_code, campaign_tag)
    except Exception as exc:
        raise _translate_upstream_error(exc, "62") from None
    if facts.get("status") != "LATEST_VALID_62_PACKAGE_RESOLVED":
        if facts.get("status") == "RUNTIME_SCOPE_MISMATCH":
            raise DecisionPackageError("RUNTIME_SCOPE_MISMATCH")
        raise DecisionPackageError("63_INPUT_NOT_FOUND")
    if not all(facts.get("tables", {}).get(key) is not None for key in ("campaign", "intent", "target", "search_term")):
        raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
    if any((facts.get("metadata") or {}).get(key) != scope[key] for key in scope):
        raise DecisionPackageError("RUNTIME_SCOPE_MISMATCH")
    scope_issues: list[str] = []
    facts["tables"], scope_issues = filter_facts_to_campaign_scope(facts["tables"], scope)

    try:
        from scripts.new_product_battle_plan_contract import resolve_latest_approved_battle_plan
        plan = resolve_latest_approved_battle_plan(root, product_code)
    except Exception as exc:
        raise _translate_upstream_error(exc, "605/603") from None
    try:
        from scripts.new_product_battle_plan_contract import resolve_603_bundle
        market = resolve_603_bundle(root, product_code)
        market_status = "LATEST_VALID_603_BUNDLE_RESOLVED"
    except Exception:
        market = None
        market_status = "603_EVIDENCE_NOT_AVAILABLE"

    try:
        resolver = _load_606_resolver()
        benchmark = resolver.resolve_inputs(root, product_code) if resolver else None
        benchmark_status = "LATEST_VALID_606_INPUTS_RESOLVED" if benchmark else "606_EVIDENCE_NOT_AVAILABLE"
    except Exception as exc:
        benchmark = None
        benchmark_status = "606_EVIDENCE_NOT_AVAILABLE"

    lines: list[dict[str, Any]] = []
    fmeta = facts.get("metadata") or {}
    lines.append({"Input_Skill": "hzp-amz-6-2-product-operations-monitoring", "Input_Report_Identity": "ADVERTISING_FACT_PACKAGE", "Input_File_Name": Path(facts["directory"]).name, "Input_Run_ID": facts.get("run_id"), "Input_Run_Timestamp": fmeta.get("RUN_TIMESTAMP"), "Input_Generated_At": facts.get("generated_at"), "Input_Record_Count": {k: len(v) for k, v in facts["tables"].items()}, "Input_Resolution_Method": "LATEST_VALID_62_PACKAGE_RESOLVED", "ProductCode": fmeta.get("ProductCode"), "CampaignTag": fmeta.get("CampaignTag"), "CampaignPrefix": fmeta.get("CampaignPrefix")})
    for key, asset in (plan.get("assets") or {}).items():
        if key in {"intent", "keyword", "battle"}:
            lines.append(_asset_lineage(key, asset, "hzp-amz-6-0-5-new-product-advertising-battle-plan"))
    for key in ("summary", "mapping"):
        asset = (market or {}).get(key) or {}
        if asset:
            lines.append(_asset_lineage(key, asset, "hzp-amz-6-0-3-precision-broad-extraction"))
    if benchmark:
        lines.append({"Input_Skill": "hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis", "Input_Report_Identity": "BENCHMARK_INTENT_OCCUPANCY", "Input_File_Name": None, "Input_Run_ID": benchmark.get("summary", {}).get("run_id"), "Input_Run_Timestamp": benchmark.get("summary", {}).get("run_timestamp"), "Input_Generated_At": (benchmark.get("summary", {}).get("metadata") or {}).get("Generated_At"), "Input_Record_Count": {k: len(benchmark.get(f"{k}_rows") or []) for k in ("detail", "summary", "mapping")}, "Input_Resolution_Method": "LATEST_VALID_606_INPUTS_RESOLVED"})
    return {"product_root": str(root), "product_code": product_code, "CampaignTag": (scope or {}).get("CampaignTag"), "CampaignPrefix": (scope or {}).get("CampaignPrefix"), "scope_issues": scope_issues, "facts": facts, "plan": plan, "market": market, "market_status": market_status, "benchmark": benchmark, "benchmark_status": benchmark_status, "inputs": lines}


def _fact_key(kind: str, row: Mapping[str, Any]) -> tuple[str, ...] | None:
    fields = {
        "campaign": ("CampaignId",),
        "intent": ("IntentCode",),
        "target": ("TargetId",),
        "search_term": ("SearchTerm", "TargetId"),
    }[kind]
    values = tuple(_s(row.get(field)) for field in fields)
    return values if all(values) else None


def _additive_sum(rows: Sequence[Mapping[str, Any]], field: str) -> Decimal | None:
    if not rows:
        return None
    values = [_decimal(row.get(field)) for row in rows]
    if any(value is None for value in values):
        return None
    return sum((value for value in values if value is not None), Decimal(0))


def _ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    return numerator / denominator if numerator is not None and denominator not in (None, Decimal(0)) else None


def aggregate_windows(rows: Iterable[Mapping[str, Any]], kind: str, stable_cutoff: str | date) -> dict[str, dict[str, Any]]:
    """Aggregate dated 3/7/14/30-day facts; keep source-window facts unsegmented."""
    cutoff = date.fromisoformat(stable_cutoff) if isinstance(stable_cutoff, str) else stable_cutoff
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    source_window: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for original in rows:
        key = _fact_key(kind, original)
        if not key:
            continue
        row = dict(original)
        raw_date = _s(row.get("Date"))
        if _s(row.get("DataCompleteness")) == "SOURCE_WINDOW" or not raw_date:
            source_window[key].append(row)
            continue
        try:
            row_date = date.fromisoformat(raw_date[:10])
        except ValueError:
            continue
        if row_date <= cutoff and _s(row.get("DataCompleteness")) != "TODAY_PARTIAL":
            row["_parsed_date"] = row_date
            grouped[key].append(row)
    output: dict[str, dict[str, Any]] = {}
    for key in set(grouped) | set(source_window):
        record: dict[str, Any] = {"identity": list(key), "source_window_rows": source_window.get(key, [])}
        dated = grouped.get(key, [])
        for days in (3, 7, 14, 30):
            start = cutoff - timedelta(days=days - 1)
            selected = [row for row in dated if start <= row["_parsed_date"] <= cutoff]
            metrics = ("Impressions", "Clicks", "Spend", "Orders", "Sales")
            sums = {metric: _additive_sum(selected, metric) for metric in metrics}
            record[f"{days}D"] = {
                "start": start.isoformat(), "end": cutoff.isoformat(), "observed_days": len({r["_parsed_date"] for r in selected}),
                "row_count": len(selected), **{key: str(value) if value is not None else None for key, value in sums.items()},
                "CVR": str(_ratio(sums["Orders"], sums["Clicks"])) if _ratio(sums["Orders"], sums["Clicks"]) is not None else None,
                "ACoS": str(_ratio(sums["Spend"], sums["Sales"])) if _ratio(sums["Spend"], sums["Sales"]) is not None else None,
            }
        latest = max(dated, key=lambda row: row["_parsed_date"]) if dated else None
        current_fields = {"campaign": ("DailyBudget", "Status", "ControlMode", "IntentCode"), "intent": ("控制方式", "精准泛词"), "target": ("Bid", "Status", "IntentCode", "控制方式", "精准泛词"), "search_term": ("TargetValue", "MatchType", "IntentCode", "精准泛词")}[kind]
        record["current_values"] = {field: latest.get(field) for field in current_fields} if latest else {}
        record["first_seen_date"] = min((r["_parsed_date"] for r in dated), default=None).isoformat() if dated else None
        record["last_seen_date"] = max((r["_parsed_date"] for r in dated), default=None).isoformat() if dated else None
        record["active_days"] = len({r["_parsed_date"] for r in dated if any(_decimal(r.get(m)) not in (None, Decimal(0)) for m in ("Impressions", "Clicks", "Spend", "Orders"))})
        output["\x1f".join(key)] = record
    return output


def expected_decision_identities(facts: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, list[tuple[str, ...]]]:
    tables = facts["tables"]
    assets = plan.get("assets") or {}
    plan_intents = ((assets.get("intent") or {}).get("rows") or [])
    identity_sets: dict[str, set[tuple[str, ...]]] = {
        "intent": ({(_s(row.get("意图代码") or row.get("IntentCode")),) for row in plan_intents if _s(row.get("意图代码") or row.get("IntentCode"))}
                   | {key for row in tables.get("intent", []) if (key := _fact_key("intent", row))}),
        "campaign": {_fact_key("campaign", row) for row in tables.get("campaign", [])},
        "target": {_fact_key("target", row) for row in tables.get("target", [])},
        "search_term": {_fact_key("search_term", row) for row in tables.get("search_term", [])},
    }
    for kind in identity_sets:
        identity_sets[kind].discard(None)
    return {kind: sorted(values) for kind, values in identity_sets.items()}


def build_decision_context(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Build factual decision context and exact coverage sets from resolved assets."""
    facts = resolved["facts"]
    stable_cutoff = (facts.get("metadata") or {}).get("StableCutoffDate")
    try:
        date.fromisoformat(str(stable_cutoff))
    except (TypeError, ValueError):
        raise DecisionPackageError("63_DATA_INSUFFICIENT") from None
    tables = facts.get("tables") or {}
    expected = expected_decision_identities(facts, resolved["plan"])
    windows = {kind: aggregate_windows(tables[kind], kind, str(stable_cutoff)) for kind in ("campaign", "intent", "target", "search_term")}
    plan_assets = resolved["plan"].get("assets") or {}
    return {
        "product_code": resolved.get("product_code"),
        "facts_run_id": facts.get("run_id"),
        "facts_metadata": facts.get("metadata"),
        "plan_run_id": (plan_assets.get("intent") or {}).get("run_id") or ((plan_assets.get("intent") or {}).get("metadata") or {}).get("RUN_ID"),
        "plan": {key: value.get("rows") or [] for key, value in plan_assets.items() if key in {"intent", "keyword", "battle"}},
        "market": resolved.get("market"),
        "benchmark": resolved.get("benchmark"),
        "benchmark_status": resolved.get("benchmark_status"),
        "market_status": resolved.get("market_status"),
        "windows": windows,
        "expected_objects": expected,
        "inputs": resolved.get("inputs", []),
    }


def _identity(kind: str, row: Mapping[str, Any]) -> tuple[str, ...] | None:
    fields = {"intent": ("IntentCode",), "campaign": ("CampaignId",), "target": ("TargetId",), "search_term": ("SearchTerm", "TargetId")}[kind]
    values = tuple(_s(row.get(field)) for field in fields)
    return values if all(values) else None


def validate_decision_tables(
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    expected_objects: Mapping[str, Sequence[Sequence[str]]] | None = None,
) -> dict[str, int]:
    """Validate exact contracts, full coverage, candidate values, and layer consistency."""
    if set(tables) != set(SCHEMAS):
        raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
    counts: dict[str, int] = {}
    indexed: dict[str, dict[tuple[str, ...], Mapping[str, Any]]] = {}
    for kind, schema in SCHEMAS.items():
        rows = list(tables[kind])
        counts[kind] = len(rows)
        by_id: dict[tuple[str, ...], Mapping[str, Any]] = {}
        for row in rows:
            if tuple(row.keys()) != schema:
                raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
            if not _s(row.get("决策成熟度")) or _s(row["决策成熟度"]) not in MATURITY:
                raise DecisionPackageError("DECISION_MATURITY_MISSING")
            if not _s(row.get("决策结果")) or _s(row["决策结果"]) not in RESULTS[kind]:
                raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
            if not _s(row.get("确认状态")) or _s(row["确认状态"]) not in CONFIRMATION:
                raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
            if not _s(row["决策原因"]):
                raise DecisionPackageError("DECISION_REASON_MISSING")
            if not re.search(r"(?:近\s*\d+\s*(?:日|天)|Since\s+Launch|自上线以来|即时异常)", _s(row["决策原因"]), flags=re.I):
                raise DecisionPackageError("DECISION_REASON_MISSING")
            if not _s(row["下一观察条件"]):
                raise DecisionPackageError("OBSERVATION_CONDITION_MISSING")
            row_id = _identity(kind, row)
            if row_id is None:
                raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
            if row_id in by_id:
                raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
            by_id[row_id] = row
            action = _s(row["决策结果"])
            if action in {"增加预算", "降低预算"} and (not _s(row.get("当前Budget")) or not _s(row.get("建议Budget"))):
                raise DecisionPackageError("PROPOSED_VALUE_MISSING")
            if action == "调整位置" and (not _s(row.get("当前Placement")) or not _s(row.get("建议Placement"))):
                raise DecisionPackageError("PROPOSED_VALUE_MISSING")
            if action in {"提高竞价", "降低竞价"} and (not _s(row.get("当前Bid")) or not _s(row.get("建议Bid"))):
                raise DecisionPackageError("PROPOSED_VALUE_MISSING")
            if action == "升级独立" and _s(row.get("目标控制方式")) != "独立":
                raise DecisionPackageError("DECISION_CONFLICT")
            if action == "降级共享" and _s(row.get("目标控制方式")) != "共享":
                raise DecisionPackageError("DECISION_CONFLICT")
            if action in {"放大", "收缩"} and not any(_s(row.get(field)) for field in ("目标作战任务", "目标控制方式", "目标阶段")):
                raise DecisionPackageError("PROPOSED_VALUE_MISSING")
            if action in {"阶段升级", "阶段降级"} and not _s(row.get("目标阶段")):
                raise DecisionPackageError("PROPOSED_VALUE_MISSING")
            if kind == "target" and action == "迁移候选" and not _s(row.get("目标控制方式")):
                raise DecisionPackageError("PROPOSED_VALUE_MISSING")
            if kind == "search_term" and _s(row.get("建议处理方式")) != action:
                raise DecisionPackageError("DECISION_CONFLICT")
            candidate = action not in {"保持", "继续观察", "保持观察"}
            if candidate and _s(row.get("确认状态")) == "已批准":
                raise DecisionPackageError("DECISION_CONFLICT")
        indexed[kind] = by_id
        if expected_objects is not None:
            expected = {tuple(str(part) for part in key) for key in expected_objects.get(kind, ())}
            if set(by_id) != expected:
                raise DecisionPackageError("63_DATA_INSUFFICIENT")

    intents = indexed["intent"]
    for intent_code, intent in intents.items():
        intent_result = _s(intent.get("决策结果"))
        if intent_result not in {"升级独立", "降级共享"}:
            continue
        destination = _s(intent.get("目标控制方式"))
        related_targets = [row for row in indexed["target"].values() if _s(row.get("IntentCode")) == intent_code[0]]
        if not related_targets or any(_s(row.get("目标控制方式")) != destination for row in related_targets):
            raise DecisionPackageError("DECISION_CONFLICT")
    for kind in ("campaign", "target"):
        for row in indexed[kind].values():
            intent_code = _s(row.get("IntentCode"))
            intent = intents.get((intent_code,)) if intent_code else None
            if not intent:
                continue
            intent_result = _s(intent.get("决策结果"))
            desired_mode = _s(intent.get("目标控制方式"))
            target_mode = _s(row.get("目标控制方式"))
            if intent_result in {"升级独立", "降级共享"} and kind == "target" and not target_mode:
                raise DecisionPackageError("DECISION_CONFLICT")
            if intent_result == "升级独立" and target_mode and target_mode != desired_mode:
                raise DecisionPackageError("DECISION_CONFLICT")
            if intent_result == "降级共享" and target_mode and target_mode != desired_mode:
                raise DecisionPackageError("DECISION_CONFLICT")
    return counts


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _render_table(kind: str, rows: Sequence[Mapping[str, Any]]) -> str:
    schema = SCHEMAS[kind]
    return _render_table_columns(schema, rows)


def _render_table_columns(schema: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> str:
    heads = "".join(f"<th>{html.escape(column)}</th>" for column in schema)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{html.escape(_s(row.get(column)))}</td>" for column in schema) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{heads}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def render_report_html(
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    metadata: Mapping[str, Any],
    decision_history: Mapping[str, Any] | None = None,
) -> str:
    """Render an offline dashboard whose decision details come only from CSV rows."""
    counts = {kind: len(tables[kind]) for kind in SCHEMAS}
    all_rows = [row for kind in SCHEMAS for row in tables[kind]]
    maturity = {label: sum(_s(row.get("决策成熟度")) == label for row in all_rows) for label in MATURITY}
    all_actions = [row for kind in SCHEMAS for row in tables[kind]]
    result_counts: dict[str, int] = defaultdict(int)
    for row in all_actions:
        result_counts[_s(row.get("决策结果"))] += 1
    names = {"intent": "Intent 决策", "campaign": "Campaign 决策", "target": "Target 决策", "search_term": "Search Term 决策"}
    sections = []
    for kind in SCHEMAS:
        sections.append(f'<section id="{kind}"><h2>{html.escape(names[kind])} <small>{counts[kind]} 项</small></h2>{_render_table(kind, tables[kind])}</section>')
    observe_items = []
    urgent_items = []
    pending_items = []
    for kind, rows in tables.items():
        key_fields = {"intent": "IntentCode", "campaign": "CampaignId", "target": "TargetId", "search_term": "SearchTerm"}[kind]
        for row in rows:
            item = f"{html.escape(_s(row.get(key_fields)))}：{html.escape(_s(row.get('决策结果')))}；原因：{html.escape(_s(row.get('决策原因')))}；下一步：{html.escape(_s(row.get('下一观察条件')))}"
            if _s(row.get("决策成熟度")) == "继续观察":
                observe_items.append(f"<li>{item}</li>")
            if _s(row.get("决策成熟度")) == "紧急处理":
                urgent_items.append(f"<li>{item}</li>")
            if _s(row.get("确认状态")) == "待确认" and _s(row.get("决策结果")) not in {"保持", "继续观察", "保持观察"}:
                pending_items.append(f"<li>{item}</li>")
    lineage = html.escape(json.dumps(metadata.get("Inputs", []), ensure_ascii=False, indent=2))
    history = (decision_history or {}).get("records") or {kind: [] for kind in SCHEMAS}
    history_fields = {"intent": ("IntentCode",), "campaign": ("CampaignId",), "target": ("TargetId",), "search_term": ("SearchTerm", "TargetId")}
    history_rows = []
    for kind in SCHEMAS:
        for row in history.get(kind, []):
            history_rows.append({"对象层": kind, "对象身份": " × ".join(_s(row.get(field)) for field in history_fields[kind]), "RUN_ID": row.get("RUN_ID"), "Generated_At": row.get("Generated_At"), "决策成熟度": row.get("决策成熟度"), "决策结果": row.get("决策结果"), "决策原因": row.get("决策原因"), "下一观察条件": row.get("下一观察条件")})
    history_schema = ("对象层", "对象身份", "RUN_ID", "Generated_At", "决策成熟度", "决策结果", "决策原因", "下一观察条件")
    history_table = _render_table_columns(history_schema, history_rows)
    payload = {"metadata": dict(metadata), "tables": {kind: [dict(row) for row in tables[kind]] for kind in SCHEMAS}, "decision_history": history_rows}
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广告优化决策报告</title><style>
    :root{{--ink:#182431;--muted:#607184;--line:#dce4eb;--panel:#fff;--bg:#f3f6f9;--blue:#2563a8;--amber:#9a5b00;--red:#a42929}}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 "Segoe UI",Arial,sans-serif}}main{{max-width:1600px;margin:auto;padding:26px}}h1{{font-size:28px;margin:0}}h2{{font-size:19px;margin:0 0 12px}}h2 small{{font-size:13px;color:var(--muted);font-weight:500}}h3{{font-size:15px;margin:20px 0 8px}}p,.muted{{color:var(--muted)}}.head,.card,section{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin:0 0 16px}}.head{{border-top:4px solid var(--blue)}}.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:10px;margin-top:15px}}.kpi{{border:1px solid var(--line);border-radius:8px;padding:11px}}.kpi b{{display:block;font-size:22px}}.kpi span{{color:var(--muted)}}.table-wrap{{overflow:auto;max-height:680px;border:1px solid var(--line);border-radius:7px}}table{{border-collapse:collapse;width:max-content;min-width:100%;font-size:12px}}th,td{{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top;max-width:360px;white-space:normal}}th{{position:sticky;top:0;background:#eef3f8;z-index:1}}tr:nth-child(even){{background:#fafcfe}}li{{margin:8px 0}}pre{{white-space:pre-wrap;word-break:break-word;color:#44566a;background:#f7f9fb;padding:12px;border-radius:7px}}.warn{{border-left:4px solid var(--amber);padding:10px 14px;background:#fff8e9}}.urgent{{border-left:4px solid var(--red);padding:10px 14px;background:#fff3f3}}@media print{{body{{background:#fff}}main{{max-width:none;padding:0}}.table-wrap{{overflow:visible;max-height:none}}th{{position:static}}section,.card,.head{{break-inside:avoid}}}}
    </style></head><body><main><header class="head"><h1>广告优化决策报告</h1><p>产品：{html.escape(_s(metadata.get('Product_Code')))}　｜　CampaignTag：{html.escape(_s(metadata.get('CampaignTag')))}　｜　范围：{html.escape(_s(metadata.get('CampaignPrefix')))}<br>RUN_ID：{html.escape(_s(metadata.get('RUN_ID')))}<br>生成时间：{html.escape(_s(metadata.get('Generated_At')))}<br>核心事实包：{html.escape(_s(metadata.get('6-2_RUN_ID')))}　｜　605作战计划：{html.escape(_s(metadata.get('605_RUN_ID')))}</p><p class="warn">6-3 只负责 DECIDE。本报告没有执行任何 Amazon Ads 写操作；候选动作须经确认并交由 6-1 执行。</p><div class="kpis"><div class="kpi"><b>{sum(counts.values())}</b><span>决策对象</span></div>{''.join(f'<div class="kpi"><b>{value}</b><span>{html.escape(label)}</span></div>' for label,value in maturity.items())}{''.join(f'<div class="kpi"><b>{value}</b><span>{html.escape(label)}</span></div>' for label,value in sorted(result_counts.items()))}</div></header>
    <section id="lineage"><h2>本次使用数据 / Input Lineage</h2><pre>{lineage}</pre><p>603状态：{html.escape(_s(metadata.get('603_Status')))}；606状态：{html.escape(_s(metadata.get('606_Status')))}。Organic Search Occupancy 是自然搜索占领证据，不是 Sales Market Share。</p></section>
    {''.join(sections)}
    <section id="observe"><h2>继续观察：为什么暂不调整、还在等什么</h2>{'<ul>'+''.join(observe_items)+'</ul>' if observe_items else '<p>本次没有继续观察对象。</p>'}</section>
    <section id="urgent"><h2>紧急处理候选</h2>{'<ul>'+''.join(urgent_items)+'</ul>' if urgent_items else '<p>本次没有紧急处理候选。</p>'}</section>
    <section id="pending"><h2>待确认变更 / 交给 6-1</h2>{'<ul>'+''.join(pending_items)+'</ul>' if pending_items else '<p>本次没有待确认执行候选。</p>'}</section>
    <section id="history"><h2>历史决策</h2><p>{html.escape(_s(metadata.get('Decision_History_Status')) or 'DECISION_HISTORY_UNAVAILABLE')}。历史以稳定 CampaignId、TargetId、IntentCode 或 SearchTerm × TargetId 关联，不覆盖既有运行包。</p>{history_table if history_rows else '<p>没有可用的先前运行决策。</p>'}</section>
    <section id="limits"><h2>数据局限与职责边界</h2><p>HTML 决策逐条来自本次四张 CSV；缺失值未补造。6-3 不重新查询广告表现，不调用 apply_change_plan，不创建、修改、暂停或否定广告。已批准的 Desired State 由 6-1 再做技术身份、权限、能力和实际状态校验。</p></section>
    <script id="decision-payload" type="application/json">{_json_for_script(payload)}</script></main></body></html>'''


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], schema: Sequence[str]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(schema), extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in schema})


def write_decision_package(
    product_root: str | Path,
    product_code: str,
    tables: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    campaign_tag: str,
    scope_issues: Sequence[str] = (),
    expected_objects: Mapping[str, Sequence[Sequence[str]]] | None = None,
    inputs: Sequence[Mapping[str, Any]] = (),
    market_status: str = "603_EVIDENCE_NOT_AVAILABLE",
    benchmark_status: str = "606_EVIDENCE_NOT_AVAILABLE",
    decision_history_status: str = "DECISION_HISTORY_UNAVAILABLE",
    now: datetime | None = None,
) -> dict[str, Any]:
    try:
        scope = build_campaign_scope(product_code, campaign_tag)
    except CampaignScopeError as exc:
        raise DecisionPackageError(str(exc)) from None
    facts_lineage = next((row for row in inputs if row.get("Input_Skill") == "hzp-amz-6-2-product-operations-monitoring"), None)
    if not facts_lineage or any(facts_lineage.get(field) != scope[field] for field in scope):
        raise DecisionPackageError("RUNTIME_SCOPE_MISMATCH")
    scoped_tables, found_scope_issues = filter_decision_tables_to_campaign_scope(tables, scope)
    scope_issues = sorted(set(scope_issues).union(found_scope_issues))
    tables = scoped_tables
    if expected_objects is None:
        raise DecisionPackageError("63_DATA_INSUFFICIENT")
    counts = validate_decision_tables(tables, expected_objects=expected_objects)
    decision_history = load_decision_history(product_root, product_code, campaign_tag)
    if decision_history["status"] == "DECISION_HISTORY_RESOLVED":
        decision_history_status = decision_history["status"]
    elif decision_history_status != "DECISION_HISTORY_UNAVAILABLE":
        decision_history["status"] = decision_history_status
    context = new_run_context("6-3", SKILL_ID, product_code, now=now)
    skill_dir = Path(__file__).resolve().parents[1] / "hzp-amz-6-3-advertising-diagnosis-optimization"
    report_root = resolve_skill_report_dir(product_root, skill_dir)
    folder = report_root / context.run_timestamp
    files = {key: folder / build_report_filename(skill_dir, name, context.run_timestamp, "csv") for key, name in TABLE_FILES.items()}
    html_path = folder / build_report_filename(skill_dir, "广告优化决策报告", context.run_timestamp, "html")
    manifest_path = folder / f"6-3_RunPackage_{context.run_timestamp}.json"
    paths = [*files.values(), html_path, manifest_path]
    report_error = validate_hzp_amz_report_batch(paths, product_root, skill_dir, timestamp=context.run_timestamp, allow_run_folder=True)
    if report_error:
        raise DecisionPackageError(report_error)
    assert_new_outputs(paths)
    folder.mkdir(parents=True, exist_ok=False)
    for key, path in files.items():
        _write_csv(path, tables[key], SCHEMAS[key])
    written_tables = {}
    for key, path in files.items():
        header, rows = read_csv(path)
        if tuple(header) != SCHEMAS[key]:
            raise DecisionPackageError("63_INPUT_SCHEMA_INVALID")
        written_tables[key] = rows
    meta = make_artifact_metadata(
        context, "ADVERTISING_DECISION_PACKAGE", run_status="FULL_SUCCESS",
        inputs=inputs, output_assets=[p.name for p in [*files.values(), html_path]],
        extra={"Package_Type": "ADVERTISING_DECISION_PACKAGE", "6-2_RUN_ID": _input_run_id(inputs, "hzp-amz-6-2-product-operations-monitoring"), "Source_6-2_Run_ID": _input_run_id(inputs, "hzp-amz-6-2-product-operations-monitoring"), "605_RUN_ID": _input_run_id(inputs, "hzp-amz-6-0-5-new-product-advertising-battle-plan"), "603_Status": market_status, "606_Status": benchmark_status, "Decision_History_Status": decision_history_status, "Decision_History_Package_Count": decision_history.get("package_count", 0), "Decision_Record_Counts": counts, "Decision_Schemas": {key: list(value) for key, value in SCHEMAS.items()}, "Amazon_Ads_Writes": False, "Scope_Issues": sorted(set(scope_issues)), **(dict(scope or {}))})
    if scope_issues:
        meta["Run_Status"] = "PARTIAL_SUCCESS"
    html_text = render_report_html(written_tables, meta, decision_history)
    with html_path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(html_text)
    for key, path in files.items():
        sidecar = make_artifact_metadata(context, f"ADVERTISING_DECISION_{key.upper()}", run_status=meta["Run_Status"], schema=SCHEMAS[key], record_count=counts[key], inputs=inputs, output_assets=[path.name], extra=dict(scope or {}))
        write_metadata_sidecar(path, sidecar)
    html_meta = make_artifact_metadata(context, "ADVERTISING_DECISION_REPORT", run_status=meta["Run_Status"], record_count=sum(counts.values()), inputs=inputs, output_assets=[html_path.name], extra={"Source_Decision_CSVs": [files[key].name for key in SCHEMAS], **dict(scope or {})})
    write_metadata_sidecar(html_path, html_meta)
    with manifest_path.open("x", encoding="utf-8", newline="") as handle:
        json.dump(meta, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return {"status": "DECISION_PACKAGE_WRITTEN", "run_id": context.run_id, "run_timestamp": context.run_timestamp, "directory": str(folder), "files": {**{key: str(path) for key, path in files.items()}, "html": str(html_path), "manifest": str(manifest_path)}, "metadata": meta}


def _input_run_id(inputs: Sequence[Mapping[str, Any]], skill_id: str) -> str | None:
    return next((str(row.get("Input_Run_ID")) for row in inputs if row.get("Input_Skill") == skill_id and row.get("Input_Run_ID")), None)


def load_decision_history(product_root: str | Path, product_code: str, campaign_tag: str | None = None) -> dict[str, Any]:
    """Read prior complete 6-3 packages; never modify history."""
    skill_dir = Path(__file__).resolve().parents[1] / "hzp-amz-6-3-advertising-diagnosis-optimization"
    parent = resolve_skill_report_dir(product_root, skill_dir)
    history: dict[str, list[dict[str, Any]]] = {kind: [] for kind in SCHEMAS}
    packages = []
    for folder in parent.iterdir() if parent.is_dir() else ():
        try:
            meta = json.loads((folder / f"6-3_RunPackage_{folder.name}.json").read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if meta.get("Skill_ID") != SKILL_ID or meta.get("Product_Code") != product_code or meta.get("Report_Identity") != "ADVERTISING_DECISION_PACKAGE" or meta.get("Run_Status") != "FULL_SUCCESS":
            continue
        if campaign_tag is not None and meta.get("CampaignTag") != campaign_tag:
            continue
        if meta.get("RUN_ID") != f"6-3_{product_code}_{folder.name}" or not re.fullmatch(r"\d{8}_\d{6}", folder.name):
            continue
        expected_assets = {build_report_filename(skill_dir, stem, folder.name, "csv") for stem in TABLE_FILES.values()}
        expected_assets.add(build_report_filename(skill_dir, "广告优化决策报告", folder.name, "html"))
        if not expected_assets.issubset(set(meta.get("Output_Assets") or [])):
            continue
        pkg_rows: dict[str, list[dict[str, str]]] = {}
        valid = True
        for kind, stem in TABLE_FILES.items():
            path = folder / build_report_filename(skill_dir, stem, folder.name, "csv")
            try:
                header, rows = read_csv(path)
                sidecar = json.loads(Path(f"{path}.meta.json").read_text(encoding="utf-8-sig"))
            except DecisionPackageError:
                valid = False
                break
            except (OSError, UnicodeError, json.JSONDecodeError):
                valid = False
                break
            if (
                tuple(header) != SCHEMAS[kind]
                or len(rows) != (meta.get("Decision_Record_Counts") or {}).get(kind)
                or sidecar.get("Skill_ID") != SKILL_ID
                or sidecar.get("Product_Code") != product_code
                or sidecar.get("RUN_ID") != meta.get("RUN_ID")
                or sidecar.get("RUN_TIMESTAMP") != meta.get("RUN_TIMESTAMP")
                or sidecar.get("Report_Identity") != f"ADVERTISING_DECISION_{kind.upper()}"
                or sidecar.get("Run_Status") != "FULL_SUCCESS"
                or sidecar.get("Schema") != list(SCHEMAS[kind])
                or sidecar.get("Record_Count") != len(rows)
                or sidecar.get("Output_Assets") != [path.name]
            ):
                valid = False
                break
            pkg_rows[kind] = rows
        if not valid:
            continue
        html_path = folder / build_report_filename(skill_dir, "广告优化决策报告", folder.name, "html")
        try:
            html_sidecar = json.loads(Path(f"{html_path}.meta.json").read_text(encoding="utf-8-sig"))
            html_path.stat()
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if (
            html_sidecar.get("Skill_ID") != SKILL_ID
            or html_sidecar.get("Product_Code") != product_code
            or html_sidecar.get("RUN_ID") != meta.get("RUN_ID")
            or html_sidecar.get("RUN_TIMESTAMP") != meta.get("RUN_TIMESTAMP")
            or html_sidecar.get("Report_Identity") != "ADVERTISING_DECISION_REPORT"
            or html_sidecar.get("Run_Status") != "FULL_SUCCESS"
            or html_sidecar.get("Output_Assets") != [html_path.name]
        ):
            continue
        try:
            generated = datetime.fromisoformat(str(meta["Generated_At"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        packages.append((generated, pkg_rows, meta))
    packages.sort(key=lambda item: item[0])
    for _, tables, meta in packages:
        for kind, rows in tables.items():
            for row in rows:
                history[kind].append({"RUN_ID": meta.get("RUN_ID"), "Generated_At": meta.get("Generated_At"), **row})
    return {"status": "DECISION_HISTORY_RESOLVED" if packages else "DECISION_HISTORY_UNAVAILABLE", "package_count": len(packages), "records": history}
