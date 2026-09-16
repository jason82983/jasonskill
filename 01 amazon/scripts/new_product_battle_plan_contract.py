"""Shared 6-0-5 battle-plan CSV contract and latest approved bundle resolver."""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.stage6_artifact_contract import resolve_latest_valid_bundle  # noqa: E402

SKILL_ID = "hzp-amz-6-0-5-new-product-advertising-battle-plan"
OUTPUT_DIR = "6-0-5_新品广告作战规划"
INPUT_DIR = "6-0-3_精准泛词提取"
SUMMARY_IDENTITY = "PRECISION_BROAD_SUMMARY"
MAPPING_IDENTITY = "PRECISION_BROAD_MAPPING"

SUMMARY_COLUMNS = (
    "精准泛词", "中文", "层级", "父精准泛词", "直接搜索量", "汇总搜索量",
    "平均竞品数", "意图机会比", "直接对应词数",
)
MAPPING_MULTI_COLUMNS = (
    "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数",
    "最佳自然排名", "自然排名中位数", "精准泛词", "精准泛词中文",
)
MAPPING_SINGLE_COLUMNS = (
    "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名",
    "精准泛词", "精准泛词中文",
)

INTENT_COLUMNS = (
    "意图代码", "精准泛词", "中文", "层级", "父精准泛词", "直接搜索量",
    "汇总搜索量", "平均竞品数", "意图机会比", "直接对应词数", "作战任务",
    "作战优先级", "作战方向", "控制方式", "控制原因", "决策原因", "确认状态",
)
KEYWORD_MULTI_COLUMNS = (
    "Id", "词", "中文", "精准泛词", "意图代码", "市场容量", "竞争产品数",
    "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数", "作战任务", "控制方式", "控制原因",
    "当前状态", "新品期是否投放", "计划阶段", "计划投放方式", "启动条件",
    "暂不投放原因", "确认状态",
)
KEYWORD_SINGLE_COLUMNS = (
    "Id", "词", "中文", "精准泛词", "意图代码", "市场容量", "竞争产品数",
    "供需比", "自然排名", "作战任务", "控制方式", "控制原因", "当前状态", "新品期是否投放",
    "计划阶段", "计划投放方式", "启动条件", "暂不投放原因", "确认状态",
)
BATTLE_MULTI_COLUMNS = (
    "作战单元ID", "精准泛词", "意图代码", "作战任务", "作战优先级", "控制方式", "Id",
    "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数",
    "最佳自然排名", "自然排名中位数", "计划阶段", "投放方式", "作战目的", "确认状态",
)
BATTLE_SINGLE_COLUMNS = (
    "作战单元ID", "精准泛词", "意图代码", "作战任务", "作战优先级", "控制方式", "Id",
    "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名",
    "计划阶段", "投放方式", "作战目的", "确认状态",
)

OUTPUT_IDENTITIES = {
    "intent": "NEW_PRODUCT_INTENT_BATTLEFIELD",
    "keyword": "NEW_PRODUCT_KEYWORD_LIFECYCLE",
    "battle": "NEW_PRODUCT_BATTLE_UNITS",
    "html": "NEW_PRODUCT_ADVERTISING_BATTLE_PLAN",
}


def _candidate_paths(product_root: Path, product_code: str, stem: str) -> list[Path]:
    directory = product_root / "06_SKILL分析报告" / INPUT_DIR
    current = re.compile(rf"^{re.escape(stem)}_\d{{8}}_\d{{6}}\.csv$")
    legacy = re.compile(rf"^6-0-3_{re.escape(product_code)}_{re.escape(stem.removeprefix('6-0-3_'))}(?:_\d{{8}}_\d{{6}})?\.csv$")
    return [path for path in directory.glob("*.csv") if current.fullmatch(path.name) or legacy.fullmatch(path.name)] if directory.is_dir() else []


def _schema_validator(allowed: tuple[tuple[str, ...], ...]):
    def validate(path: Path, rows: list[dict[str, str]] | None, metadata: dict[str, Any] | None) -> str | None:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                header = tuple(next(csv.reader(handle), []))
        except (OSError, UnicodeError, csv.Error):
            return "605_INPUT_SCHEMA_INVALID"
        return None if header in allowed else "605_INPUT_SCHEMA_INVALID"
    return validate


def _approved_rows_validator(path: Path, rows: list[dict[str, str]] | None, metadata: dict[str, Any] | None) -> str | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = tuple(reader.fieldnames or ())
            materialized = list(reader)
    except (OSError, UnicodeError, csv.Error):
        return "605_PLAN_NOT_APPROVED"
    if "确认状态" not in fields or any(row.get("确认状态") not in {"APPROVED", "HOLD"} for row in materialized):
        return "605_PLAN_NOT_APPROVED"
    return None


def resolve_603_bundle(product_root: str | Path, product_code: str) -> dict[str, Any]:
    """Resolve the exact same-run 6-0-3 summary + mapping pair."""
    root = Path(product_root).resolve()
    assets = {
        "summary": _candidate_paths(root, product_code, "6-0-3_精准泛词汇总"),
        "mapping": _candidate_paths(root, product_code, "6-0-3_词对应的精准泛词"),
    }
    if not assets["summary"] or not assets["mapping"]:
        raise FileNotFoundError("605_INPUT_NOT_FOUND")
    resolved = resolve_latest_valid_bundle(
        root, "hzp-amz-6-0-3-precision-broad-extraction", assets,
        product_code=product_code,
        report_identities={"summary": SUMMARY_IDENTITY, "mapping": MAPPING_IDENTITY},
        required_schemas={"summary": None, "mapping": None},
        validators={
            "summary": _schema_validator((SUMMARY_COLUMNS,)),
            "mapping": _schema_validator((MAPPING_MULTI_COLUMNS, MAPPING_SINGLE_COLUMNS)),
        },
    )
    if resolved.get("status") != "LATEST_VALID_RUN_BUNDLE_RESOLVED":
        raise ValueError("605_INPUT_RUN_MISMATCH")
    if not resolved.get("run_id") or not resolved.get("run_timestamp"):
        raise ValueError("605_INPUT_RUN_MISMATCH")
    selected = resolved["assets"]
    summary, mapping = selected["summary"], selected["mapping"]
    if not summary.get("rows") or not mapping.get("rows"):
        raise ValueError("605_INPUT_EMPTY")
    mapping_schema = tuple(mapping["rows"][0].keys())
    if mapping_schema not in (MAPPING_MULTI_COLUMNS, MAPPING_SINGLE_COLUMNS):
        raise ValueError("605_INPUT_SCHEMA_INVALID")
    ids = [str(row.get("Id", "")).strip() for row in mapping["rows"]]
    if any(not item for item in ids):
        raise ValueError("BATTLE_UNIT_SOURCE_MISSING")
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_KEYWORD_ID")
    return {"status": resolved["status"], "method": resolved.get("input_resolution_method"),
            "run_id": resolved.get("run_id"), "run_timestamp": resolved.get("run_timestamp"),
            "summary": summary, "mapping": mapping, "mapping_schema": mapping_schema}


def resolve_latest_approved_battle_plan(product_root: str | Path, product_code: str) -> dict[str, Any]:
    """Resolve a complete same-run 6-0-5 output bundle; reject any non-approved business row."""
    root = Path(product_root).resolve()
    directory = root / "06_SKILL分析报告" / OUTPUT_DIR
    specs = {
        "intent": ("新品意图市场作战表", INTENT_COLUMNS),
        "keyword": ("新品关键词阶段规划表", None),
        "battle": ("新品关键词作战明细", None),
        "html": ("新品广告作战规划报告", None),
    }
    assets: dict[str, list[Path]] = {}
    validators: dict[str, Any] = {}
    schemas: dict[str, tuple[str, ...] | None] = {}
    for key, (name, schema) in specs.items():
        extension = "html" if key == "html" else "csv"
        pattern = re.compile(rf"^6-0-5_{re.escape(name)}_\d{{8}}_\d{{6}}\.{extension}$")
        assets[key] = [path for path in directory.glob("*") if pattern.fullmatch(path.name)] if directory.is_dir() else []
        if key == "keyword":
            allowed = (KEYWORD_MULTI_COLUMNS, KEYWORD_SINGLE_COLUMNS)
            validators[key] = lambda path, rows, metadata, allowed=allowed: (
                _schema_validator(allowed)(path, rows, metadata) or _approved_rows_validator(path, rows, metadata)
            )
            schemas[key] = None
        elif key == "battle":
            allowed = (BATTLE_MULTI_COLUMNS, BATTLE_SINGLE_COLUMNS)
            validators[key] = lambda path, rows, metadata, allowed=allowed: (
                _schema_validator(allowed)(path, rows, metadata) or _approved_rows_validator(path, rows, metadata)
            )
            schemas[key] = None
        elif key == "intent":
            validators[key] = lambda path, rows, metadata: (
                _schema_validator((INTENT_COLUMNS,))(path, rows, metadata)
                or _approved_rows_validator(path, rows, metadata)
            )
            schemas[key] = None
        else:
            schemas[key] = schema
    if any(not paths for paths in assets.values()):
        raise FileNotFoundError("605_INPUT_NOT_FOUND")
    resolver_args = dict(
        product_code=product_code,
        report_identities=OUTPUT_IDENTITIES, required_schemas=schemas,
    )
    resolved = resolve_latest_valid_bundle(
        root, SKILL_ID, assets, required_status={"FULL_SUCCESS", "SUCCESS", "COMPLETE"},
        validators=validators, **resolver_args,
    )
    if resolved.get("status") != "LATEST_VALID_RUN_BUNDLE_RESOLVED":
        # Distinguish a complete but still-proposed latest plan from missing or split inputs.
        proposal_check = resolve_latest_valid_bundle(
            root, SKILL_ID, assets, required_status={"FULL_SUCCESS", "SUCCESS", "COMPLETE"},
            validators={
                "intent": _schema_validator((INTENT_COLUMNS,)),
                "keyword": _schema_validator((KEYWORD_MULTI_COLUMNS, KEYWORD_SINGLE_COLUMNS)),
                "battle": _schema_validator((BATTLE_MULTI_COLUMNS, BATTLE_SINGLE_COLUMNS)),
            }, **resolver_args,
        )
        if proposal_check.get("status") == "LATEST_VALID_RUN_BUNDLE_RESOLVED":
            raise ValueError("605_PLAN_NOT_APPROVED")
        raise ValueError("605_INPUT_RUN_MISMATCH")
    if not resolved.get("run_id") or not resolved.get("run_timestamp"):
        raise ValueError("605_INPUT_RUN_MISMATCH")
    selected = resolved["assets"]
    # Approval is a row-level human edit; check exact accepted values before 6-1 consumes it.
    for key in ("intent", "keyword", "battle"):
        rows = selected[key].get("rows") or []
        if any(str(row.get("确认状态", "")).strip() not in {"APPROVED", "HOLD"} for row in rows):
            raise ValueError("605_PLAN_NOT_APPROVED")
    keyword_rows = selected["keyword"].get("rows") or []
    battle_rows = selected["battle"].get("rows") or []
    intent_rows = selected["intent"].get("rows") or []
    if any(row.get("控制方式") not in {"独立", "共享", "不投"} or not str(row.get("控制原因", "")).strip() for row in intent_rows):
        raise ValueError("INVALID_CONTROL_DECISION")
    keyword_by_id = {str(row.get("Id", "")).strip(): row for row in keyword_rows}
    if any(row.get("控制方式") not in {"独立", "共享", "不投"} or not str(row.get("控制原因", "")).strip() for row in keyword_rows):
        raise ValueError("INVALID_CONTROL_DECISION")
    if any(row.get("控制方式") == "不投" and row.get("新品期是否投放") == "是" for row in keyword_rows):
        raise ValueError("NO_INVESTMENT_CANNOT_ENTER_BATTLE_PLAN")
    if any(row.get("控制方式") not in {"独立", "共享"} for row in battle_rows):
        raise ValueError("NO_INVESTMENT_CANNOT_ENTER_BATTLE_PLAN")
    if any(keyword_by_id.get(str(row.get("Id", "")).strip(), {}).get("控制方式") != row.get("控制方式") for row in battle_rows):
        raise ValueError("CONTROL_MODE_PASSTHROUGH_MISMATCH")
    shared_meta = selected["keyword"].get("metadata") or {}
    if (len(intent_rows) != shared_meta.get("Input_Intent_Count")
            or len(keyword_rows) != shared_meta.get("Input_Keyword_Count")):
        raise ValueError("OUTPUT_COVERAGE_MISMATCH")
    keyword_multi = "对标覆盖数" in (selected["keyword"].get("schema") or [])
    battle_multi = "对标覆盖数" in (selected["battle"].get("schema") or [])
    if keyword_multi != battle_multi:
        raise ValueError("605_INPUT_SCHEMA_INVALID")
    approved_ids = {str(row.get("Id", "")).strip() for row in keyword_rows
                    if row.get("计划阶段") == "PHASE_1" and row.get("新品期是否投放") == "是" and row.get("控制方式") != "不投" and row.get("确认状态") == "APPROVED"}
    actual_ids = [str(row.get("Id", "")).strip() for row in battle_rows if row.get("确认状态") == "APPROVED"]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != approved_ids:
        raise ValueError("OUTPUT_COVERAGE_MISMATCH")
    if not actual_ids:
        raise ValueError("605_PLAN_HAS_NO_APPROVED_BATTLE")
    return resolved
