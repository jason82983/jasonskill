"""Deterministic preflight, approval-gated execution and output package for 6-4.

This module never connects to Amazon/SellerSpace. A thin caller uses the
existing SellerSpace MCP and supplies a provider adapter that normalizes its
prepare/apply/read-back results. Tests use only synthetic rows and MockProvider.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import ad_decision_package as decisions  # noqa: E402
from scripts.stage6_artifact_contract import (  # noqa: E402
    assert_new_outputs,
    make_artifact_metadata,
    new_run_context,
    resolve_latest_valid_bundle,
    write_metadata_sidecar,
)
from scripts.advertising_state_reconciler import exact_change_digest  # noqa: E402
from scripts.campaign_scope_contract import CampaignScopeError, build_campaign_scope, campaign_is_in_scope  # noqa: E402
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_batch,
)

SKILL_ID = "hzp-amz-6-4-advertising-optimization-action-executor"
OUTPUT_DIR = "6-4_广告优化动作执行"
ASSET_NAMES = {
    "intent": decisions.TABLE_FILES["intent"],
    "campaign": decisions.TABLE_FILES["campaign"],
    "target": decisions.TABLE_FILES["target"],
    "search_term": decisions.TABLE_FILES["search_term"],
}
EXECUTION_SCHEMA = (
    "执行ID", "6-3决策RunID", "对象类型", "对象ID", "对象名称", "IntentCode", "BattleUnitId",
    "决策结果", "确认状态", "执行前预期值", "执行时实际值", "目标值", "执行动作", "执行结果",
    "AmazonId", "失败/冲突原因", "执行时间", "ReadBack结果",
)
MIGRATION_SCHEMA = (
    "MigrationId", "6-3决策RunID", "IntentCode", "迁移类型", "旧CampaignId", "旧CampaignName",
    "新CampaignId", "新CampaignName", "新结构创建结果", "新Target创建结果", "新结构ReadBack",
    "旧Target处理动作", "旧Target处理结果", "迁移状态", "失败/冲突原因", "执行时间",
)
EXECUTION_RESULTS = {"执行成功", "无需执行", "状态冲突", "执行失败", "等待人工", "已执行过"}


class ExecutionError(ValueError):
    """Stable execution error code in ``args[0]``."""


class Provider(Protocol):
    def query_actual(self) -> list[dict[str, Any]]: ...
    def prepare(self, changes: list[dict[str, Any]], idempotency_key: str) -> Mapping[str, Any]: ...
    def apply(self, plan_id: str, idempotency_key: str) -> Mapping[str, Any]: ...
    def read_back(self, logical_ids: list[str]) -> list[dict[str, Any]]: ...


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        value = value.strip()
        return "" if value.upper() in {"NULL", "NONE", "DATA_NOT_AVAILABLE", "N/A"} else value
    return str(value).strip()


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _parse_current(field: str, value: Any) -> Any:
    if field in {"daily_budget", "bid"}:
        text = _text(value).replace("$", "").replace(",", "")
        try:
            number = Decimal(text)
        except InvalidOperation:
            raise ExecutionError("64_EXPECTED_VALUE_MISSING") from None
        if not number.is_finite():
            raise ExecutionError("64_EXPECTED_VALUE_MISSING")
        return number
    if field == "placement":
        if isinstance(value, Mapping):
            return dict(value)
        try:
            parsed = json.loads(_text(value))
        except (json.JSONDecodeError, TypeError):
            raise ExecutionError("64_EXPECTED_VALUE_MISSING") from None
        if not isinstance(parsed, Mapping):
            raise ExecutionError("64_EXPECTED_VALUE_MISSING")
        return dict(parsed)
    return value


def _parse_target(field: str, value: Any) -> Any:
    if field in {"daily_budget", "bid"}:
        text = _text(value).replace("$", "").replace(",", "")
        try:
            number = Decimal(text)
        except InvalidOperation:
            raise ExecutionError("64_PROPOSED_VALUE_MISSING") from None
        if not number.is_finite() or number <= 0:
            raise ExecutionError("64_PROPOSED_VALUE_MISSING")
        return number
    if field == "placement":
        if isinstance(value, Mapping):
            return dict(value)
        try:
            parsed = json.loads(_text(value))
        except (json.JSONDecodeError, TypeError):
            raise ExecutionError("64_PROPOSED_VALUE_MISSING") from None
        if not isinstance(parsed, Mapping):
            raise ExecutionError("64_PROPOSED_VALUE_MISSING")
        return dict(parsed)
    if not _text(value):
        raise ExecutionError("64_PROPOSED_VALUE_MISSING")
    return value


def resolve_latest_approved_decisions(product_root: str | Path, product_code: str, campaign_tag: str) -> dict[str, Any]:
    """Resolve the latest same-run, valid four-table 6-3 package."""
    root = Path(product_root).resolve()
    parent = resolve_skill_report_dir(root, ROOT / "hzp-amz-6-3-advertising-diagnosis-optimization")
    candidate_sets: dict[str, list[Path]] = {}
    for kind, stem in ASSET_NAMES.items():
        candidate_sets[kind] = sorted(parent.glob(f"*/6-3_{stem}_*.csv")) if parent.is_dir() else []
    try:
        scope = build_campaign_scope(product_code, campaign_tag)
    except CampaignScopeError as exc:
        raise ExecutionError(str(exc)) from None
    bundle = resolve_latest_valid_bundle(
        root,
        "hzp-amz-6-3-advertising-diagnosis-optimization",
        candidate_sets,
        product_code=product_code,
        report_identities={kind: f"ADVERTISING_DECISION_{kind.upper()}" for kind in ASSET_NAMES},
        required_schemas=decisions.SCHEMAS,
        required_status=("FULL_SUCCESS",),
        expected_metadata=scope or {},
    )
    if bundle.get("status") != "LATEST_VALID_RUN_BUNDLE_RESOLVED" or not bundle.get("run_id"):
        code = "64_INPUT_NOT_FOUND" if not any(candidate_sets.values()) else ("RUNTIME_SCOPE_MISMATCH" if scope else "64_INPUT_RUN_MISMATCH")
        raise ExecutionError(code)
    files = {kind: Path(asset["file"]).resolve() for kind, asset in bundle["assets"].items()}
    parents = {path.parent for path in files.values()}
    if set(files) != set(ASSET_NAMES) or len(parents) != 1:
        raise ExecutionError("64_INPUT_RUN_MISMATCH")
    run_folder = next(iter(parents))
    manifest_path = run_folder / f"6-3_RunPackage_{run_folder.name}.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ExecutionError("64_INPUT_SCHEMA_INVALID") from None
    required_assets = {path.name for path in files.values()}
    html_name = build_report_filename(ROOT / "hzp-amz-6-3-advertising-diagnosis-optimization", "广告优化决策报告", run_folder.name, "html")
    if (
        manifest.get("Skill_ID") != "hzp-amz-6-3-advertising-diagnosis-optimization"
        or manifest.get("Product_Code") != product_code
        or manifest.get("Report_Identity") != "ADVERTISING_DECISION_PACKAGE"
        or manifest.get("Run_Status") != "FULL_SUCCESS"
        or manifest.get("RUN_ID") != bundle["run_id"]
        or manifest.get("RUN_TIMESTAMP") != bundle.get("run_timestamp")
        or not required_assets.union({html_name}).issubset(set(manifest.get("Output_Assets") or []))
        or not (run_folder / html_name).is_file()
    ):
        raise ExecutionError("64_INPUT_RUN_MISMATCH")
    if scope and any(manifest.get(key) != scope[key] for key in scope):
        raise ExecutionError("RUNTIME_SCOPE_MISMATCH")
    tables = {kind: list(bundle["assets"][kind]["rows"] or []) for kind in ASSET_NAMES}
    for kind, rows in tables.items():
        expected_count = (manifest.get("Decision_Record_Counts") or {}).get(kind)
        if expected_count is None or len(rows) != expected_count:
            raise ExecutionError("64_INPUT_SCHEMA_INVALID")
    return {
        "status": "LATEST_VALID_63_DECISIONS_RESOLVED",
        "product_code": product_code,
        "run_id": bundle["run_id"],
        "run_timestamp": bundle.get("run_timestamp"),
        "run_folder": str(run_folder),
        "manifest": manifest,
        "scope": scope,
        "files": {kind: str(path) for kind, path in files.items()},
        "tables": tables,
    }


def execution_id(product_code: str, decision_run_id: str, kind: str, row: Mapping[str, Any], action: str, expected: Any, target: Any) -> str:
    stable = {
        "product_code": product_code,
        "decision_run_id": decision_run_id,
        "kind": kind,
        "object_id": row.get("CampaignId") or row.get("TargetId") or row.get("IntentCode") or row.get("SearchTerm"),
        "target_id": row.get("TargetId"),
        "action": action,
        "expected": expected,
        "target": target,
    }
    digest = hashlib.sha256(_stable_json(stable).encode("utf-8")).hexdigest()[:24]
    return f"6-4:{product_code}:{digest}"


def _candidate(kind: str, row: Mapping[str, Any], decision_run_id: str, product_code: str) -> dict[str, Any] | None:
    if _text(row.get("确认状态")) != "已批准":
        return None
    result = _text(row.get("决策结果"))
    mapping: dict[tuple[str, str], tuple[str, str, str, str]] = {
        ("intent", "放大"): ("UNSUPPORTED", "unsupported", "", ""),
        ("intent", "收缩"): ("UNSUPPORTED", "unsupported", "", ""),
        ("campaign", "增加预算"): ("UPDATE", "daily_budget", "当前Budget", "建议Budget"),
        ("campaign", "降低预算"): ("UPDATE", "daily_budget", "当前Budget", "建议Budget"),
        ("campaign", "调整位置"): ("UPDATE", "placement", "当前Placement", "建议Placement"),
        ("target", "提高竞价"): ("UPDATE", "bid", "当前Bid", "建议Bid"),
        ("target", "降低竞价"): ("UPDATE", "bid", "当前Bid", "建议Bid"),
        ("campaign", "暂停候选"): ("PAUSE", "status", "当前Status", "目标Status"),
        ("target", "暂停候选"): ("PAUSE", "status", "当前Status", "目标Status"),
        ("search_term", "否定候选"): ("NEGATIVE", "negative", "SourceTarget", "NegativeTarget"),
        ("search_term", "收割候选"): ("HARVEST", "target", "SourceTarget", "目标投放"),
        ("target", "迁移候选"): ("MIGRATION", "target", "当前控制方式", "目标控制方式"),
        ("intent", "升级独立"): ("MIGRATION", "campaign", "当前控制方式", "目标控制方式"),
        ("intent", "降级共享"): ("MIGRATION", "campaign", "当前控制方式", "目标控制方式"),
        ("intent", "阶段升级"): ("UNSUPPORTED", "unsupported", "", ""),
        ("intent", "阶段降级"): ("UNSUPPORTED", "unsupported", "", ""),
    }
    details = mapping.get((kind, result))
    if details is None:
        if result in {"保持", "继续观察", "保持观察"}:
            return None
        details = ("UNSUPPORTED", "unsupported", "", "")
    action, field, expected_field, target_field = details
    expected_raw, target_raw = row.get(expected_field), row.get(target_field)
    code = None
    expected = target = None
    if action == "UPDATE":
        if not _text(expected_raw):
            code = "64_EXPECTED_VALUE_MISSING"
        elif not _text(target_raw):
            code = "64_PROPOSED_VALUE_MISSING"
        else:
            try:
                expected = _parse_current(field, expected_raw)
                target = _parse_target(field, target_raw)
            except ExecutionError as exc:
                code = str(exc)
    else:
        expected = _text(expected_raw)
        target = _text(target_raw)
        if action == "UNSUPPORTED":
            code = "64_ACTION_MAPPING_UNSUPPORTED"
        elif action == "PAUSE" and (not expected or not target):
            code = "64_EXPECTED_VALUE_MISSING" if not expected else "64_PROPOSED_VALUE_MISSING"
        elif action in {"NEGATIVE", "HARVEST"}:
            # 6-3's present CSV lacks negative scope/match type and complete
            # destination targeting parameters. Never infer them here.
            code = "64_TECHNICAL_EXECUTION_CONFLICT" if action == "NEGATIVE" else "64_HARVEST_EXECUTION_INCOMPLETE"
        elif action == "MIGRATION":
            code = "64_MIGRATION_FAILED"
    object_id = row.get({"campaign": "CampaignId", "target": "TargetId", "search_term": "TargetId", "intent": "IntentCode"}[kind])
    if not _text(object_id) and code is None:
        code = "64_IDENTITY_CONFLICT"
    exec_id = execution_id(product_code, decision_run_id, kind, row, action, expected_raw, target_raw)
    return {
        "执行ID": exec_id,
        "6-3决策RunID": decision_run_id,
        "对象类型": {"intent": "Intent", "campaign": "Campaign", "target": "Target", "search_term": "Search Term"}[kind],
        "对象ID": _text(object_id),
        "对象名称": _text(row.get("CampaignName") or row.get("TargetValue") or row.get("SearchTerm") or row.get("精准泛词")),
        "IntentCode": _text(row.get("IntentCode")),
        "BattleUnitId": _text(row.get("BattleUnitId")),
        "决策结果": result,
        "确认状态": "已批准",
        "执行前预期值": _stable_json(expected) if expected is not None else "",
        "执行时实际值": "",
        "目标值": _stable_json(target) if target is not None else "",
        "执行动作": action,
        "执行结果": "等待人工" if code else "等待人工",
        "AmazonId": _text(row.get("CampaignId") or row.get("TargetId")),
        "失败/冲突原因": code or "WAITING_FOR_LIVE_STATE_PREFLIGHT",
        "执行时间": "",
        "ReadBack结果": "未执行",
        "_kind": kind,
        "_field": field,
        "_expected": expected if code is None else None,
        "_target": target if code is None else None,
        "_error": code,
        "_source": dict(row),
    }


def collect_approved_actions(tables: Mapping[str, Sequence[Mapping[str, Any]]], product_code: str, decision_run_id: str) -> list[dict[str, Any]]:
    """Build approved actionable candidates only; non-actions remain zero-write."""
    result: list[dict[str, Any]] = []
    for kind in decisions.SCHEMAS:
        for row in tables.get(kind, []):
            candidate = _candidate(kind, row, decision_run_id, product_code)
            if candidate is not None:
                result.append(candidate)
    return sorted(result, key=lambda item: (_execution_priority(item["执行动作"]), item["执行ID"]))


def _execution_priority(action: str) -> int:
    return {"CREATE_DESTINATION": 0, "UPDATE": 1, "PAUSE": 2, "NEGATIVE": 2, "HARVEST": 0, "MIGRATION": 0}.get(action, 3)


def compare_expected_current(expected: Any, actual: Any) -> bool:
    return _stable_json(expected) == _stable_json(actual)


def _live_in_campaign_scope(entity: Mapping[str, Any], actual_entities: Sequence[Mapping[str, Any]], campaign_prefix: str) -> bool:
    kind = _text(entity.get("entity_type")).casefold()
    if kind == "campaign":
        return campaign_is_in_scope(entity.get("name") or entity.get("CampaignName"), campaign_prefix)
    if kind != "target":
        return False
    group_id = _text(entity.get("parent_ad_group_id") or entity.get("AdGroupId"))
    groups = [row for row in actual_entities if _text(row.get("amazon_id") or row.get("AdGroupId")) == group_id and _text(row.get("entity_type")).casefold() in {"ad_group", "adgroup"}]
    if len(groups) != 1:
        return False
    campaign_id = _text(groups[0].get("campaign_id") or groups[0].get("parent_campaign_id") or groups[0].get("CampaignId"))
    campaigns = [row for row in actual_entities if _text(row.get("amazon_id") or row.get("CampaignId")) == campaign_id and _text(row.get("entity_type")).casefold() == "campaign"]
    return len(campaigns) == 1 and campaign_is_in_scope(campaigns[0].get("name") or campaigns[0].get("CampaignName"), campaign_prefix)


def mark_actual_and_conflicts(candidates: Sequence[Mapping[str, Any]], actual_entities: Sequence[Mapping[str, Any]], *, identity_verified: bool, campaign_prefix: str | None = None) -> list[dict[str, Any]]:
    """Join by verified Amazon ID, compare Expected Current and return report rows."""
    if not identity_verified:
        raise ExecutionError("64_IDENTITY_CONFLICT")
    output: list[dict[str, Any]] = []
    for original in candidates:
        action = dict(original)
        if action.get("_error"):
            continue_row(action, action["_error"])
            output.append(action)
            continue
        matches = [row for row in actual_entities if str(row.get("amazon_id", "")) == action["AmazonId"]]
        if len(matches) != 1:
            continue_row(action, "64_IDENTITY_CONFLICT")
            output.append(action)
            continue
        live = dict(matches[0])
        expected_type = {"Campaign": "campaign", "Target": "target"}.get(action["对象类型"])
        if not live.get("logical_id") or (expected_type and live.get("entity_type") != expected_type):
            continue_row(action, "64_IDENTITY_CONFLICT")
            output.append(action)
            continue
        if campaign_prefix and not _live_in_campaign_scope(live, actual_entities, campaign_prefix):
            continue_row(action, "OUTSIDE_CAMPAIGN_SCOPE")
            output.append(action)
            continue
        field = action["_field"]
        actual_value = live.get(field)
        action["执行时实际值"] = _stable_json(actual_value)
        action["_live"] = live
        if action["执行动作"] == "UPDATE":
            try:
                parsed_actual = _parse_current(field, actual_value)
            except ExecutionError as exc:
                continue_row(action, str(exc))
            else:
                if compare_expected_current(action["_target"], parsed_actual):
                    action["执行结果"] = "无需执行"
                    action["失败/冲突原因"] = "ACTUAL_ALREADY_EQUALS_TARGET"
                    action["ReadBack结果"] = "已确认当前值等于目标值，无写入"
                elif not compare_expected_current(action["_expected"], parsed_actual):
                    continue_row(action, "64_STATE_CONFLICT")
        elif action["执行动作"] == "PAUSE":
            if not _text(action["_expected"]):
                continue_row(action, "64_EXPECTED_VALUE_MISSING")
            elif not compare_expected_current(action["_expected"], actual_value):
                continue_row(action, "64_STATE_CONFLICT")
        elif action["执行动作"] in {"NEGATIVE", "HARVEST", "MIGRATION"}:
            if action["_error"]:
                continue_row(action, action["_error"])
        output.append(action)
    return output


def continue_row(action: dict[str, Any], code: str) -> None:
    action["执行结果"] = "状态冲突" if code == "64_STATE_CONFLICT" else "等待人工"
    action["失败/冲突原因"] = code
    action["ReadBack结果"] = "未执行"


def provider_change(action: Mapping[str, Any]) -> dict[str, Any]:
    """Translate one validated parameter action to the shared provider shape."""
    if action.get("执行动作") != "UPDATE" or action.get("_error") or not action.get("_live") or action.get("执行结果") == "无需执行":
        raise ExecutionError("64_ACTION_MAPPING_UNSUPPORTED")
    live = dict(action["_live"])
    field = str(action["_field"])
    entity = str(live.get("entity_type"))
    allowed = {"campaign": {"daily_budget", "placement"}, "target": {"bid"}}
    if field not in allowed.get(entity, set()):
        raise ExecutionError("64_ACTION_MAPPING_UNSUPPORTED")
    proposed = action["_target"]
    desired = {**live, field: proposed}
    return {
        "action": "UPDATE",
        "entity_type": entity,
        "logical_id": live["logical_id"],
        "amazon_id": live["amazon_id"],
        "before": {field: {"before": live.get(field), "desired": proposed}},
        "desired": desired,
    }


def _verify_provider_live_scope(provider: Provider, amazon_id: str, campaign_prefix: str) -> bool:
    query = getattr(provider, "query_actual", None)
    if not callable(query):
        return False
    entities = [dict(row) for row in query()]
    matches = [row for row in entities if _text(row.get("amazon_id") or row.get("CampaignId") or row.get("TargetId")) == amazon_id]
    return len(matches) == 1 and _live_in_campaign_scope(matches[0], entities, campaign_prefix)


def prepare_exact_action(action: Mapping[str, Any], provider: Provider, *, campaign_prefix: str | None = None) -> dict[str, Any]:
    if campaign_prefix and not _verify_provider_live_scope(provider, str(action.get("AmazonId", "")), campaign_prefix):
        return {"status": "OUTSIDE_CAMPAIGN_SCOPE", "error": "OUTSIDE_CAMPAIGN_SCOPE"}
    change = provider_change(action)
    key = str(action["执行ID"])
    try:
        preview = dict(provider.prepare([change], key))
    except Exception as exc:
        return {"status": "64_TECHNICAL_EXECUTION_CONFLICT", "error": str(exc), "change": change}
    digest = exact_change_digest([change])
    if preview.get("status") not in {"PREPARED", "SUCCESS"} or preview.get("change_digest") != digest or not preview.get("plan_id"):
        return {"status": "64_TECHNICAL_EXECUTION_CONFLICT", "preview": preview, "change": change}
    return {"status": "PREPARED", "plan_id": str(preview["plan_id"]), "idempotency_key": key, "change_digest": digest, "change": change, "preview": preview}


def apply_confirmed_action(action: Mapping[str, Any], prepared: Mapping[str, Any], provider: Provider, *, exact_preview_confirmed: bool, campaign_prefix: str | None = None) -> dict[str, Any]:
    """Apply a previously prepared exact diff only after the preview confirmation."""
    if not exact_preview_confirmed:
        return {"status": "WAITING_FOR_USER_CONFIRMATION", "read_back": None}
    if prepared.get("status") != "PREPARED" or prepared.get("change_digest") != exact_change_digest([prepared.get("change", {})]):
        return {"status": "64_TECHNICAL_EXECUTION_CONFLICT", "read_back": None}
    if campaign_prefix and not _verify_provider_live_scope(provider, str(prepared.get("change", {}).get("amazon_id", "")), campaign_prefix):
        return {"status": "OUTSIDE_CAMPAIGN_SCOPE", "read_back": None}
    try:
        applied = dict(provider.apply(str(prepared["plan_id"]), str(prepared["idempotency_key"])))
    except Exception as exc:
        return {"status": "64_UPDATE_FAILED", "error": str(exc), "read_back": None}
    if applied.get("status") not in {"APPLIED", "SUCCESS"}:
        return {"status": "64_UPDATE_FAILED", "apply": applied, "read_back": None}
    desired = dict(prepared["change"]["desired"])
    logical_id = str(prepared["change"]["logical_id"])
    try:
        observed = provider.read_back([logical_id])
    except Exception as exc:
        return {"status": "64_READBACK_FAILED", "error": str(exc), "read_back": None}
    matches = [dict(row) for row in observed if str(row.get("logical_id")) == logical_id]
    if len(matches) != 1:
        return {"status": "64_READBACK_FAILED", "read_back": observed}
    actual = matches[0]
    fields = {"daily_budget", "placement", "bid"}
    expected_fields = [field for field in fields if field in desired and field in prepared["change"].get("before", {})]
    if (
        not actual.get("amazon_id")
        or actual.get("amazon_id") != prepared["change"].get("amazon_id")
        or actual.get("entity_type") != prepared["change"].get("entity_type")
        or any(not compare_expected_current(desired.get(field), actual.get(field)) for field in expected_fields)
    ):
        return {"status": "64_READBACK_FAILED", "read_back": actual}
    return {"status": "EXECUTION_SUCCESS", "read_back": actual, "amazon_id": actual["amazon_id"]}


def migration_stages(*, destination_actions: Sequence[Mapping[str, Any]], old_action: Mapping[str, Any], campaign_prefix: str | None = None) -> list[dict[str, Any]]:
    """Make the create→verify→old-handle order explicit; reject incomplete migration specs."""
    if not destination_actions or not old_action or not old_action.get("expected_current") or not old_action.get("action"):
        raise ExecutionError("64_MIGRATION_FAILED")
    if campaign_prefix and any(not campaign_is_in_scope((row.get("desired") or row).get("name") or (row.get("desired") or row).get("CampaignName"), campaign_prefix) for row in destination_actions if _text(row.get("entity_type") or (row.get("desired") or {}).get("entity_type")) == "campaign"):
        raise ExecutionError("OUTSIDE_CAMPAIGN_SCOPE")
    return [
        {"stage": "CREATE_DESTINATION", "actions": list(destination_actions)},
        {"stage": "VERIFY_DESTINATION", "required": True},
        {"stage": "HANDLE_OLD", "action": dict(old_action)},
        {"stage": "VERIFY_OLD", "required": True},
    ]


def migration_next_stage(stages: Sequence[Mapping[str, Any]], completed: Sequence[str]) -> dict[str, Any] | None:
    """Return the next migration stage; old state cannot be handled before destination read-back."""
    done = set(completed)
    for stage in stages:
        name = str(stage["stage"])
        if name == "HANDLE_OLD" and "VERIFY_DESTINATION" not in done:
            return None
        if name not in done:
            return dict(stage)
    return None


def prior_successful_execution_ids(product_root: str | Path, product_code: str, decision_run_id: str, campaign_tag: str | None = None) -> set[str]:
    skill_dir = Path(__file__).resolve().parents[1]
    parent = resolve_skill_report_dir(product_root, skill_dir)
    done: set[str] = set()
    for folder in parent.iterdir() if parent.is_dir() else ():
        try:
            meta = json.loads((folder / f"6-4_RunPackage_{folder.name}.json").read_text(encoding="utf-8-sig"))
            if meta.get("Skill_ID") != SKILL_ID or meta.get("Product_Code") != product_code or meta.get("Decision_Run_ID") != decision_run_id or not meta.get("Run_Status") or (campaign_tag is not None and meta.get("CampaignTag") != campaign_tag):
                continue
            execution_path = folder / build_report_filename(skill_dir, "广告优化执行结果", folder.name, "csv")
            with execution_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            done.update(row["执行ID"] for row in rows if row.get("执行结果") in {"执行成功", "无需执行", "已执行过"} and row.get("执行ID"))
        except (OSError, UnicodeError, json.JSONDecodeError, csv.Error):
            continue
    return done


def output_row(candidate: Mapping[str, Any], status: str, *, actual: Any = "", failure: str = "", readback: Any = "", when: str = "") -> dict[str, Any]:
    if status not in EXECUTION_RESULTS:
        raise ValueError("64_INPUT_SCHEMA_INVALID")
    row = {key: candidate.get(key, "") for key in EXECUTION_SCHEMA}
    row.update({"执行时实际值": _stable_json(actual) if actual != "" else candidate.get("执行时实际值", ""), "执行结果": status,
                "失败/冲突原因": failure or candidate.get("失败/冲突原因", ""), "ReadBack结果": _stable_json(readback) if isinstance(readback, Mapping) else (readback or candidate.get("ReadBack结果", "")), "执行时间": when})
    return row


def migration_candidate_row(candidate: Mapping[str, Any], *, when: str = "") -> dict[str, Any]:
    """Keep underspecified but approved structural work visible in the migration ledger."""
    action = _text(candidate.get("执行动作"))
    source = dict(candidate.get("_source") or {})
    if action not in {"MIGRATION", "HARVEST"}:
        raise ExecutionError("64_ACTION_MAPPING_UNSUPPORTED")
    if action == "HARVEST":
        migration_type = "收割迁移"
    elif candidate.get("决策结果") == "升级独立":
        migration_type = "共享转独立"
    elif candidate.get("决策结果") == "降级共享":
        migration_type = "独立转共享"
    else:
        migration_type = "其他正式支持类型"
    digest = hashlib.sha256(_stable_json({"exec_id": candidate.get("执行ID"), "migration_type": migration_type}).encode("utf-8")).hexdigest()[:24]
    return {
        "MigrationId": f"6-4:migration:{digest}",
        "6-3决策RunID": candidate.get("6-3决策RunID", ""),
        "IntentCode": candidate.get("IntentCode", ""),
        "迁移类型": migration_type,
        "旧CampaignId": source.get("CampaignId", ""),
        "旧CampaignName": source.get("CampaignName", ""),
        "新CampaignId": "",
        "新CampaignName": "",
        "新结构创建结果": "未执行",
        "新Target创建结果": "未执行",
        "新结构ReadBack": "未执行",
        "旧Target处理动作": "未执行",
        "旧Target处理结果": "未执行",
        "迁移状态": "等待人工",
        "失败/冲突原因": candidate.get("_error") or "64_MIGRATION_FAILED",
        "执行时间": when,
    }


def render_execution_html(metadata: Mapping[str, Any], executions: Sequence[Mapping[str, Any]], migrations: Sequence[Mapping[str, Any]]) -> str:
    counts = Counter(_text(row.get("执行结果")) for row in executions)
    def table(schema: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> str:
        heads = "".join(f"<th>{html.escape(field)}</th>" for field in schema)
        body = "".join("<tr>" + "".join(f"<td>{html.escape(_text(row.get(field)))}</td>" for field in schema) + "</tr>" for row in rows)
        return f"<div class='table'><table><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div>"
    lineage = html.escape(json.dumps(metadata.get("Inputs", []), ensure_ascii=False, indent=2))
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广告优化执行报告</title><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#f4f6f9;color:#1f2937;font:14px/1.55 "Segoe UI",Arial,sans-serif}}main{{max-width:1500px;margin:auto;padding:24px}}header,section{{background:#fff;border:1px solid #dbe2ea;border-radius:9px;padding:18px;margin-bottom:15px}}h1{{margin:0;font-size:26px}}h2{{font-size:18px}}.cards{{display:flex;flex-wrap:wrap;gap:9px}}.card{{min-width:115px;padding:9px;border:1px solid #dbe2ea;border-radius:7px}}.card b{{display:block;font-size:20px}}.table{{overflow:auto;max-height:650px}}table{{border-collapse:collapse;width:max-content;min-width:100%;font-size:12px}}th,td{{padding:7px;border-bottom:1px solid #e4e9ef;text-align:left;vertical-align:top;max-width:350px;overflow-wrap:anywhere}}th{{position:sticky;top:0;background:#edf2f7}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}@media print{{body{{background:#fff}}main{{max-width:none;padding:0}}.table{{overflow:visible;max-height:none}}th{{position:static}}section,header{{break-inside:avoid}}}}
    </style></head><body><main><header><h1>广告优化执行报告</h1><p>产品：{html.escape(_text(metadata.get('Product_Code')))}　｜　CampaignTag：{html.escape(_text(metadata.get('CampaignTag')))}　｜　范围：{html.escape(_text(metadata.get('CampaignPrefix')))}<br>6-3 Run：{html.escape(_text(metadata.get('Decision_Run_ID')))}<br>6-4 Run：{html.escape(_text(metadata.get('RUN_ID')))}　｜　执行窗口：{html.escape(_text(metadata.get('Execution_Start')))} 至 {html.escape(_text(metadata.get('Execution_End')))}</p><div class="cards">{''.join(f'<div class="card"><b>{value}</b>{html.escape(label)}</div>' for label, value in [("批准动作", metadata.get("Approved_Action_Count", 0)), ("执行成功", counts["执行成功"]), ("无需执行", counts["无需执行"]), ("状态冲突", counts["状态冲突"]), ("执行失败", counts["执行失败"]), ("等待人工", counts["等待人工"]), ("迁移数", metadata.get("Migration_Count", len(migrations))), ("回读失败", metadata.get("ReadBackFailure_Count", 0))])}</div><p>本报告仅说明已批准动作的实际执行与回读结果，不重新评价广告经营表现。</p></header><section><h2>输入血缘</h2><pre>{lineage}</pre></section><section><h2>广告优化执行结果</h2>{table(EXECUTION_SCHEMA, executions)}</section><section><h2>广告结构迁移结果</h2>{table(MIGRATION_SCHEMA, migrations)}</section><section><h2>待处理 / 状态冲突 / 失败</h2>{table(EXECUTION_SCHEMA, [row for row in executions if row.get("执行结果") in {"状态冲突", "执行失败", "等待人工"}])}</section></main></body></html>'''


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], schema: Sequence[str]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(schema), extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in schema})


def write_execution_package(product_root: str | Path, product_code: str, decision_run_id: str, executions: Sequence[Mapping[str, Any]], migrations: Sequence[Mapping[str, Any]] = (), *, campaign_tag: str | None = None, inputs: Sequence[Mapping[str, Any]] = (), run_status: str = "FULL_SUCCESS", metrics: Mapping[str, Any] | None = None, now: datetime | None = None) -> dict[str, Any]:
    unresolved_execution = any(row.get("执行结果") in {"状态冲突", "执行失败", "等待人工"} for row in executions)
    unresolved_migration = any(row.get("迁移状态") in {"失败", "等待人工", "状态冲突"} for row in migrations)
    if run_status == "FULL_SUCCESS" and (unresolved_execution or unresolved_migration):
        raise ExecutionError("64_PARTIAL_RUN_CANNOT_BE_FULL_SUCCESS")
    try:
        scope = build_campaign_scope(product_code, campaign_tag)
    except CampaignScopeError as exc:
        raise ExecutionError(str(exc)) from None
    context = new_run_context("6-4", SKILL_ID, product_code, now=now)
    skill_dir = Path(__file__).resolve().parents[1]
    report_root = resolve_skill_report_dir(product_root, skill_dir)
    folder = report_root / context.run_timestamp
    paths = {"execution": folder / build_report_filename(skill_dir, "广告优化执行结果", context.run_timestamp, "csv"),
             "migration": folder / build_report_filename(skill_dir, "广告结构迁移结果", context.run_timestamp, "csv"),
             "html": folder / build_report_filename(skill_dir, "广告优化执行报告", context.run_timestamp, "html"),
             "manifest": folder / f"6-4_RunPackage_{context.run_timestamp}.json"}
    report_error = validate_hzp_amz_report_batch(list(paths.values()), product_root, skill_dir,
                                                  timestamp=context.run_timestamp, allow_run_folder=True)
    if report_error:
        raise ExecutionError(report_error)
    assert_new_outputs(list(paths.values()))
    folder.mkdir(parents=True, exist_ok=False)
    _write_csv(paths["execution"], executions, EXECUTION_SCHEMA)
    _write_csv(paths["migration"], migrations, MIGRATION_SCHEMA)
    readback = {}
    for key, schema in (("execution", EXECUTION_SCHEMA), ("migration", MIGRATION_SCHEMA)):
        with paths[key].open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != tuple(schema):
                raise ExecutionError("64_OUTPUT_READBACK_SCHEMA_MISMATCH")
            readback[key] = list(reader)
    if len(readback["execution"]) != len(executions) or len(readback["migration"]) != len(migrations):
        raise ExecutionError("64_OUTPUT_READBACK_MISMATCH")
    metadata = make_artifact_metadata(
        context, "ADVERTISING_OPTIMIZATION_EXECUTION_PACKAGE", run_status=run_status,
        inputs=inputs, output_assets=[paths["execution"].name, paths["migration"].name, paths["html"].name],
        extra={"Decision_Run_ID": decision_run_id, "Execution_Record_Count": len(executions), "Migration_Record_Count": len(migrations), "Execution_Schema": list(EXECUTION_SCHEMA), "Migration_Schema": list(MIGRATION_SCHEMA), "Amazon_Ads_Writes": bool(any(row.get("执行结果") == "执行成功" for row in executions)), **(dict(scope or {})), **dict(metrics or {})},
    )
    html_text = render_execution_html(metadata, readback["execution"], readback["migration"])
    with paths["html"].open("x", encoding="utf-8", newline="") as handle:
        handle.write(html_text)
    for key, schema, count in (("execution", EXECUTION_SCHEMA, len(executions)), ("migration", MIGRATION_SCHEMA, len(migrations))):
        sidecar = make_artifact_metadata(context, f"ADVERTISING_OPTIMIZATION_{key.upper()}", run_status=run_status, schema=schema, record_count=count, inputs=inputs, output_assets=[paths[key].name], extra={"Decision_Run_ID": decision_run_id})
        write_metadata_sidecar(paths[key], sidecar)
    html_sidecar = make_artifact_metadata(context, "ADVERTISING_OPTIMIZATION_EXECUTION_REPORT", run_status=run_status, record_count=len(executions) + len(migrations), inputs=inputs, output_assets=[paths["html"].name], extra={"Decision_Run_ID": decision_run_id})
    write_metadata_sidecar(paths["html"], html_sidecar)
    with paths["manifest"].open("x", encoding="utf-8", newline="") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return {"status": "EXECUTION_PACKAGE_WRITTEN", "run_id": context.run_id, "run_timestamp": context.run_timestamp, "directory": str(folder), "files": {key: str(value) for key, value in paths.items()}, "metadata": metadata}
