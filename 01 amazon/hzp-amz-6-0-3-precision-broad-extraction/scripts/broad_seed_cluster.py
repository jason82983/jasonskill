"""Build 6-0-3 precision-broad mapping and aggregate assets.

The semantic mapping is supplied by the AI layer (``mapper``).  This module
keeps the 6-0-2 record identity and performs validation, aggregation, coverage
checks, sorting and CSV writing.
"""
from __future__ import annotations

import sys
import csv
import json
import os
import re
import tempfile
import hashlib
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.hzp_amz_report_contract import (  # noqa: E402
    governance_paths, publish_latest_valid_batch, resolve_latest_valid_data,
    resolve_skill_report_dir, skill_report_directory_path, validate_hzp_amz_report_batch,
)

MISSING_INPUT = "6-0-2_AI_HIGH_PRECISION_KEYWORD_INPUT_MISSING"
NON_HIGH_PRECISION_RECORD = "603_INPUT_NOT_ALL_HIGH_PRECISION"
DEFAULT_FILTERED_PRECISION_LEVELS = frozenset({"精准", "高度精准"})
FILTERED_PRECISION_LEVELS = DEFAULT_FILTERED_PRECISION_LEVELS
PRECISION_LEVEL_ALIASES = {"已精准": "精准"}
PRECISION_FILTER_CONFIG_RELATIVE = Path("01_公共资料") / "03_系统配置" / "生成精准词库的要求.txt"
HIGH_PRECISION_LEVEL = "高度精准"
DUPLICATE_CANONICAL_KEYWORDS = "603_INPUT_DUPLICATE_KEYWORD"
DUPLICATE_RECORD_IDS = "DUPLICATE_RECORD_IDS"
MISSING_RECORD_IDS = "MISSING_RECORD_IDS"
UNRESOLVED_MAPPING = "[PRECISION_BROAD_MAPPING_UNRESOLVED]"
DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"
PRIMARY_INTENT_MISSING = "PRIMARY_INTENT_MISSING"
MULTIPLE_PRIMARY_INTENTS = "MULTIPLE_PRIMARY_INTENTS"
PARENT_INTENT_MISSING = "PARENT_INTENT_MISSING"
MULTIPLE_DIRECT_PARENTS = "MULTIPLE_DIRECT_PARENTS"
ORPHAN_PARENT_INTENT = "ORPHAN_PARENT_INTENT"
PARENT_CYCLE_DETECTED = "PARENT_CYCLE_DETECTED"
AGGREGATION_MISMATCH = "AGGREGATION_MISMATCH"
ROOT_VOLUME_MISMATCH = "ROOT_VOLUME_MISMATCH"
OUTPUT_DIR = "6-0-3_\u7cbe\u51c6\u6cdb\u8bcd\u63d0\u53d6"
INPUT_REPORT_IDENTITY = "去重去对标后 筛选后的精准词表"
INPUT_REPORT_KEY = "UNIQUE_SELECTED_PRECISION_KEYWORDS"
HIGH_PRECISION_NAME = "6-0-2_筛选后的精准词表.csv"
DEDUPLICATED_NAME = "6-0-2_去重去对标后 筛选后的精准词表.csv"
AI_PRECISION_NAME = "6-0-2_精准判断所有词表.csv"
BENCHMARK_HIGH_PRECISION_NAME = "6-0-2_{product_code}_高度精准词.csv"
INPUT_RUN_DIR = "6-0-2_AI精准关键词识别"
INPUT_602_MANIFEST_PREFIX = "6-0-2_RunPackage_"
LEGACY_INPUT_602_MANIFEST_PREFIX = "run_manifest_"
RUN_MANIFEST_NAME = "run_manifest.json"
RUN_MANIFEST_PREFIX = "6-0-3_RunPackage_"
SKILL_ID = "hzp-amz-6-0-3-precision-broad-extraction"
RUN_TIMESTAMP_RE = re.compile(r"^\d{8}_\d{6}$")
MAPPING_STEM = "6-0-3_词对应的精准泛词"
SUMMARY_STEM = "6-0-3_精准泛词汇总"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
OBSERVATION_COLUMNS = ("所属产品编号", "对标ASIN", "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名", "精准度", "精准原因")
INPUT_COLUMNS = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数", "精准度", "精准原因")
MAPPING_COLUMNS = ("Id", "\u8bcd", "\u4e2d\u6587", "\u5e02\u573a\u5bb9\u91cf", "\u7ade\u4e89\u4ea7\u54c1\u6570", "\u4f9b\u9700\u6bd4", "\u81ea\u7136\u6392\u540d", "\u7cbe\u51c6\u6cdb\u8bcd", "\u7cbe\u51c6\u6cdb\u8bcd\u4e2d\u6587", "PrimaryIntentId", "PrimaryIntentCode", "KeywordPurchaseMission", "Intent\u5c42\u7ea7", "ParentIntentId", "\u7236\u7cbe\u51c6\u6cdb\u8bcd", "IntentAssignmentReason", "ChallengeResult", "ChallengeReasonSummary")
SUMMARY_COLUMNS = ("\u7cbe\u51c6\u6cdb\u8bcd", "\u4e2d\u6587", "\u5c42\u7ea7", "\u7236\u7cbe\u51c6\u6cdb\u8bcd", "\u76f4\u63a5\u641c\u7d22\u91cf", "\u6c47\u603b\u641c\u7d22\u91cf", "\u5e73\u5747\u7ade\u54c1\u6570", "\u610f\u56fe\u673a\u4f1a\u6bd4", "\u76f4\u63a5\u5bf9\u5e94\u8bcd\u6570", "IntentId", "IntentCode", "IntentDefinition", "PrimaryPurchaseDriver", "ChallengeStatus", "ChallengeReasonSummary")
COMPETITOR_PASSTHROUGH_MISMATCH = "COMPETITOR_COUNT_PASSTHROUGH_MISMATCH"
SUPPLY_DEMAND_PASSTHROUGH_MISMATCH = "SUPPLY_DEMAND_RATIO_PASSTHROUGH_MISMATCH"
AVERAGE_COMPETITOR_MISMATCH = "AVERAGE_COMPETITOR_COUNT_MISMATCH"
INTENT_RATIO_MISMATCH = "INTENT_SUPPLY_DEMAND_RATIO_MISMATCH"

STOP_WORDS = {"a", "an", "and", "for", "from", "in", "of", "on", "the", "to", "with"}
SECONDARY_MODIFIERS = {
    "best", "better", "buy", "cute", "great", "idea", "ideas", "unique",
    "perfect", "present", "presents", "birthday", "christmas", "graduation",
    "mother", "mothers", "wedding", "anniversary", "retirement", "thanksgiving",
    "valentine", "valentines", "women", "woman", "men", "man", "girl", "girls",
    "boy", "boys", "adult",
}
RELATION_PATTERNS = (
    (("best", "friend"), "best friend"),
    (("bestie",), "best friend"),
    (("friendship",), "friendship"),
    (("sister",), "sister"),
    (("friend",), "friend"),
)
OCCASION_PATTERNS = (
    (("mother", "day"), "mothers day"),
    (("valentines",), "valentines"),
    (("valentine",), "valentines"),
    (("christmas",), "christmas"),
    (("birthday",), "birthday"),
    (("graduation",), "graduation"),
    (("memorial",), "memorial"),
    (("wedding",), "wedding"),
    (("anniversary",), "anniversary"),
    (("retirement",), "retirement"),
    (("thanksgiving",), "thanksgiving"),
)
PRODUCT_ANCHORS = {
    "gift", "gifts", "figurine", "figurines", "statue", "statues", "sculpture",
    "sculptures", "keepsake", "keepsakes", "ornament", "ornaments", "decor",
    "decoration", "decorations", "plaque", "plaques",
}


def _precision_filter_config_path(product_root: str | Path) -> Path | None:
    product_path = Path(product_root).resolve()
    for ancestor in (product_path, *product_path.parents):
        candidate = ancestor / PRECISION_FILTER_CONFIG_RELATIVE
        if candidate.is_file():
            return candidate
    return None


def read_precision_filter_levels(product_root: str | Path) -> frozenset[str]:
    """Use the shared 6-0-2 precision selection when it is available.

    The compatibility fallback is retained for isolated unit fixtures that do
    not have a product root; real 6-0-2 runs fail closed before producing a
    package when this configuration is absent.
    """
    path = _precision_filter_config_path(product_root)
    if path is None:
        return FILTERED_PRECISION_LEVELS
    text = path.read_text(encoding="utf-8-sig")
    known = ("高度精准", "已精准", "精准", "弱精准", "不精准")
    labels: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "//", "<!--")):
            continue
        if line in known:
            labels.append(line)
        elif re.search(r"(?:筛选精准等级|精准级别|筛选等级|精准词库)\s*[：:=]", line):
            value = re.split(r"[：:=]", line, maxsplit=1)[1]
            labels.extend(re.findall("|".join(re.escape(item) for item in known), value))
    normalized = {PRECISION_LEVEL_ALIASES.get(label, label) for label in labels}
    if not normalized or not normalized.issubset({"高度精准", "精准", "弱精准", "不精准"}):
        raise ValueError(f"PRECISION_FILTER_CONFIG_INVALID: {path}")
    return frozenset(normalized)


def input_paths(
    product_root: str | Path,
    product_code: str,
    run_timestamp: str | None = None,
) -> dict[str, Path]:
    stamp = run_timestamp or datetime.now().strftime(TIMESTAMP_FORMAT)
    if not RUN_TIMESTAMP_RE.fullmatch(stamp):
        raise ValueError(f"INVALID_INPUT_RUN_TIMESTAMP: {stamp}")
    try:
        datetime.strptime(stamp, TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ValueError(f"INVALID_INPUT_RUN_TIMESTAMP: {stamp}") from exc
    directory = Path(product_root) / "06_SKILL分析报告" / INPUT_RUN_DIR / "data"
    names = {"ai": AI_PRECISION_NAME, "high_precision": HIGH_PRECISION_NAME,
             "deduplicated": DEDUPLICATED_NAME}
    return {key: directory / f"{Path(template).stem}_{stamp}.csv" for key, template in names.items()}


def _read_602_formal_csv(path: Path, expected_columns: tuple[str, ...] = INPUT_COLUMNS) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_columns:
            raise ValueError(f"{MISSING_INPUT}: invalid 6-0-2 schema")
        return list(reader)


def _validate_602_run_package(
    folder: Path, product_code: str, run_timestamp: str | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    stamp = run_timestamp or (folder.name if RUN_TIMESTAMP_RE.fullmatch(folder.name) else "")
    try:
        if not RUN_TIMESTAMP_RE.fullmatch(stamp):
            raise ValueError
        datetime.strptime(stamp, TIMESTAMP_FORMAT)
    except ValueError:
        return {"valid": False, "reason": "RUN_TIMESTAMP_INVALID"}
    if manifest_path is None:
        if folder.name == "data":
            governed = folder.parent / "_system" / "manifests" / f"{INPUT_602_MANIFEST_PREFIX}{stamp}.json"
            legacy = folder / f"{INPUT_602_MANIFEST_PREFIX}{stamp}.json"
            manifest_path = governed if governed.is_file() else legacy
        else:
            manifest_path = folder / f"{INPUT_602_MANIFEST_PREFIX}{stamp}.json"
    if not manifest_path.is_file():
        return {"valid": False, "reason": "RUN_MANIFEST_MISSING"}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"valid": False, "reason": "RUN_MANIFEST_INVALID"}
    if (manifest.get("SkillId") != "hzp-amz-6-0-2-ai-precision-keyword-identification"
            or manifest.get("Run Status") != "VALID" or manifest.get("RUN_TIMESTAMP") != stamp):
        return {"valid": False, "reason": "RUN_NOT_VALID"}
    if str(manifest.get("Current Product") or "").strip() != str(product_code).strip():
        return {"valid": False, "reason": "CURRENT_PRODUCT_MISMATCH"}
    try:
        configured_precision_levels = read_precision_filter_levels(folder.parents[1])
    except (OSError, UnicodeError, ValueError) as exc:
        return {"valid": False, "reason": "PRECISION_FILTER_CONFIG_INVALID", "detail": str(exc)}
    declared_precision_levels = manifest.get("Precision Filter Levels")
    if declared_precision_levels not in (None, ""):
        if not isinstance(declared_precision_levels, (list, tuple, set)):
            return {"valid": False, "reason": "PRECISION_FILTER_LEVELS_METADATA_INVALID"}
        declared = frozenset(PRECISION_LEVEL_ALIASES.get(str(value).strip(), str(value).strip())
                             for value in declared_precision_levels)
        if declared != configured_precision_levels:
            return {"valid": False, "reason": "PRECISION_FILTER_LEVELS_CONFIG_MISMATCH"}
    declared_folder = Path(str(manifest.get("Output Folder") or "")).resolve()
    if not declared_folder or (declared_folder != folder.resolve() and folder.name != "data"):
        return {"valid": False, "reason": "RUN_FOLDER_DECLARATION_MISMATCH"}
    required = ("RUN_ID", "GeneratedAt", "Input Source", "Input Skill", "Input Run ID",
                "Input RUN_TIMESTAMP", "Input Folder", "Input File", "Product Text Input",
                "Input Record Count", "Input Unique Keyword Count", "Output Folder", "Output Files")
    if any(manifest.get(key) in (None, "") for key in required):
        return {"valid": False, "reason": "RUN_LINEAGE_METADATA_MISSING"}

    benchmark_codes = manifest.get("Benchmark Product Codes")
    benchmark_identities = manifest.get("Benchmark Identities")
    if (not isinstance(benchmark_codes, list) or not benchmark_codes
            or any(not isinstance(code, str) or not code.strip() for code in benchmark_codes)
            or len(benchmark_codes) != len(set(benchmark_codes))
            or not isinstance(benchmark_identities, dict)
            or set(benchmark_identities) != set(benchmark_codes)
            or any(not isinstance(value, dict) or not value.get("对标编码") or not value.get("对标ASIN")
                   for value in benchmark_identities.values())):
        return {"valid": False, "reason": "RUN_BENCHMARK_IDENTITY_INVALID"}

    paths = {
        "ai": folder / f"{Path(AI_PRECISION_NAME).stem}_{stamp}.csv",
        "high_precision": folder / f"{Path(HIGH_PRECISION_NAME).stem}_{stamp}.csv",
        "deduplicated": folder / f"{Path(DEDUPLICATED_NAME).stem}_{stamp}.csv",
    }
    benchmark_paths = {
        code: folder / f"6-0-2_{code}_高度精准词_{stamp}.csv"
        for code in benchmark_codes
    }
    expected_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated")] + list(benchmark_paths.values())
    expected_names = {path.name for path in expected_paths}
    declared = manifest.get("Output Files")
    if (not isinstance(declared, list) or len(declared) != 3 + len(benchmark_codes)
            or set(declared) != expected_names):
        return {"valid": False, "reason": "RUN_OUTPUT_DECLARATION_INVALID"}
    if any(path.parent.resolve() != folder.resolve() or not path.is_file()
           or not path.stem.endswith(f"_{stamp}") for path in expected_paths):
        return {"valid": False, "reason": "RUN_OUTPUT_INCOMPLETE_OR_TIMESTAMP_MISMATCH"}
    actual_csvs = {path.name for path in folder.glob(f"*_{stamp}.csv")}
    # During the terminology migration, an open legacy B/C alias may remain beside the corrected asset.
    # Ignore only these exact timestamp-matched aliases; all required corrected assets and any other extras remain strict.
    legacy_aliases = {
        f"6-0-2_高度精准词表_{stamp}.csv",
        f"6-0-2_去对标去重 高度精准词_{stamp}.csv",
    }
    if (actual_csvs - legacy_aliases) != expected_names:
        return {"valid": False, "reason": "RUN_OUTPUT_PACKAGE_INCOMPLETE"}

    try:
        ai_rows = _read_602_formal_csv(paths["ai"], OBSERVATION_COLUMNS)
        high_rows = _read_602_formal_csv(paths["high_precision"], OBSERVATION_COLUMNS)
        unique_rows = _read_602_formal_csv(paths["deduplicated"], INPUT_COLUMNS)
        benchmark_rows = {code: _read_602_formal_csv(path, OBSERVATION_COLUMNS)
                          for code, path in benchmark_paths.items()}
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        return {"valid": False, "reason": "RUN_OUTPUT_SCHEMA_INVALID", "detail": str(exc)}

    if any("所属产品编号" in row or "对标ASIN" in row or "对标编码" in row for row in unique_rows):
        return {"valid": False, "reason": "DEDUPLICATED_ASSET_HAS_BENCHMARK_FIELDS"}
    expected_selected = [row for row in ai_rows if row.get("精准度") in configured_precision_levels]
    if high_rows != expected_selected:
        return {"valid": False, "reason": "HIGH_PRECISION_DERIVATION_MISMATCH"}
    try:
        _validate_high_precision_rows(unique_rows, precision_levels=configured_precision_levels)
    except ValueError as exc:
        return {"valid": False, "reason": str(exc)}
    input_codes = {str(row.get("所属产品编号") or "").strip() for row in ai_rows}
    if not input_codes.issubset(set(benchmark_codes)):
        return {"valid": False, "reason": "RUN_BENCHMARK_IDENTITY_INVALID"}
    for code, asset_rows in benchmark_rows.items():
        expected_rows = [row for row in high_rows
                         if str(row.get("所属产品编号") or "").strip() == code
                         and row.get("精准度") == HIGH_PRECISION_LEVEL]
        canonical = [normalize_broad_keyword(row.get("词")) for row in asset_rows]
        expected_asin = str(benchmark_identities[code]["对标ASIN"])
        if (asset_rows != expected_rows
                or any(str(row.get("所属产品编号") or "").strip() != code
                       or str(row.get("对标ASIN") or "").strip() != expected_asin
                       or row.get("精准度") != HIGH_PRECISION_LEVEL for row in asset_rows)
                or len(canonical) != len(set(canonical))):
            return {"valid": False, "reason": "BENCHMARK_HIGH_PRECISION_DERIVATION_MISMATCH"}
    high_only_count = sum(row.get("精准度") == HIGH_PRECISION_LEVEL for row in high_rows)
    if sum(len(rows) for rows in benchmark_rows.values()) != high_only_count:
        return {"valid": False, "reason": "BENCHMARK_HIGH_PRECISION_COVERAGE_MISMATCH"}

    high_keywords = {normalize_broad_keyword(row.get("词")) for row in high_rows}
    input_keywords = {normalize_broad_keyword(row.get("词")) for row in unique_rows}
    if input_keywords != high_keywords:
        return {"valid": False, "reason": "DEDUPLICATED_KEYWORD_COVERAGE_MISMATCH"}
    for canonical in high_keywords:
        source = [row for row in high_rows if normalize_broad_keyword(row.get("词")) == canonical]
        if len({(row.get("精准度"), row.get("精准原因")) for row in source}) != 1:
            return {"valid": False, "reason": "KEYWORD_JUDGMENT_INCONSISTENT"}
        target = next(row for row in unique_rows if normalize_broad_keyword(row.get("词")) == canonical)
        if target.get("精准原因") != source[0].get("精准原因"):
            return {"valid": False, "reason": "DEDUPLICATED_JUDGMENT_MISMATCH"}

    counts = manifest.get("Record Counts") or {}
    output_counts = manifest.get("Output Record Counts") or {}
    try:
        input_count = int(manifest["Input Record Count"])
        unique_input_count = int(manifest["Input Unique Keyword Count"])
        observation_count = int(counts["Input Observation Count"])
        unique_source_count = int(counts["Input Unique Keyword Count"])
        ai_count = int(counts["AI Record Count"])
        high_count = int(counts["High Precision Record Count"])
        unique_high_count = int(counts["Unique High Precision Keyword Count"])
        output_ai_count = int(output_counts["AI Precision Observation Count"])
        output_high_count = int(output_counts["High Precision Observation Count"])
        output_unique_count = int(output_counts["Unique High Precision Keyword Count"])
        expected_benchmark_count = int(manifest["Expected Benchmark Count"])
        benchmark_count = int(manifest["Benchmark Count"])
        benchmark_file_count = int(counts["Benchmark File Count"])
    except (KeyError, TypeError, ValueError):
        return {"valid": False, "reason": "RUN_RECORD_COUNTS_MISSING"}
    actual_input_keywords = {normalize_broad_keyword(row.get("词")) for row in ai_rows}
    actual_per_input = {code: sum(str(row.get("所属产品编号") or "").strip() == code for row in ai_rows)
                        for code in benchmark_codes}
    actual_per_high = {code: len(benchmark_rows[code]) for code in benchmark_codes}
    if (input_count != len(ai_rows) or observation_count != len(ai_rows) or ai_count != len(ai_rows)
            or output_ai_count != len(ai_rows) or high_count != len(high_rows) or output_high_count != len(high_rows)
            or unique_input_count != len(actual_input_keywords) or unique_source_count != len(actual_input_keywords)
            or unique_high_count != len(unique_rows) or output_unique_count != len(unique_rows)
            or expected_benchmark_count != len(benchmark_codes) or benchmark_count != len(benchmark_codes)
            or benchmark_file_count != len(benchmark_codes)
            or manifest.get("Expected Benchmark Files") != [path.name for path in benchmark_paths.values()]
            or manifest.get("GeneratedBenchmarkFiles") != [path.name for path in benchmark_paths.values()]
            or manifest.get("PerBenchmarkInputObservationCount") != actual_per_input
            or manifest.get("PerBenchmarkHighPrecisionRecordCount") != actual_per_high):
        return {"valid": False, "reason": "RUN_RECORD_COUNT_MISMATCH"}
    return {
        "valid": True, "manifest": manifest, "run_id": manifest.get("RUN_ID"),
        "run_timestamp": stamp, "run_folder": str(folder),
        "files": {
            "ai": str(paths["ai"]), "high_precision": str(paths["high_precision"]),
            "deduplicated": str(paths["deduplicated"]),
            "benchmarks": {code: str(path) for code, path in benchmark_paths.items()},
        },
        "input_record_count": len(unique_rows), "input_unique_keyword_count": len(unique_rows),
    }
def resolve_latest_valid_602_run_package(product_root: str | Path, product_code: str) -> dict[str, Any]:
    """Resolve the newest formal 602 C asset by filename timestamp.

    The legacy Registry/Manifest resolver remains a compatibility fallback only;
    V3 input selection is governed by the C filename and its minimum schema.
    """
    simple = _resolve_602_c_by_filename(product_root, product_code)
    if simple.get("status") == "LATEST_VALID_602_RUN_PACKAGE_READY":
        return simple
    c_dir = Path(product_root).resolve() / "06_SKILL分析报告" / INPUT_RUN_DIR / "data"
    if any(c_dir.glob("6-0-2_去重去对标后 筛选后的精准词表_*.csv")):
        return simple
    report_dir = Path(product_root).resolve() / "06_SKILL分析报告" / INPUT_RUN_DIR
    current = resolve_latest_valid_data(report_dir)
    if current.get("status") != "LATEST_VALID_DATA":
        return _resolve_602_c_by_filename(product_root, product_code)
    data_dir = Path(current["data_dir"])
    stamp = str(current.get("run_timestamp") or "")
    manifest_dir = report_dir / "_system" / "manifests"
    manifest_path = manifest_dir / f"{INPUT_602_MANIFEST_PREFIX}{stamp}.json"
    if not manifest_path.is_file():
        legacy = manifest_dir / f"{LEGACY_INPUT_602_MANIFEST_PREFIX}{stamp}.json"
        manifest_path = legacy if legacy.is_file() else manifest_path
    package = _validate_602_run_package(data_dir, product_code, stamp, manifest_path)
    if not package.get("valid"):
        # V3 accepts the formal C asset selected by filename timestamp even
        # when an older registry/manifest package is absent or incomplete.
        reason = str(package.get("reason") or "")
        if reason.startswith("603_INPUT_DUPLICATE_KEYWORD"):
            return {"status": DUPLICATE_CANONICAL_KEYWORDS, "invalid_runs": [{"run_timestamp": stamp, "reason": reason}]}
        if reason.startswith("603_INPUT_NOT_ALL_HIGH_PRECISION"):
            return {"status": NON_HIGH_PRECISION_RECORD, "invalid_runs": [{"run_timestamp": stamp, "reason": reason}]}
        return _resolve_602_c_by_filename(product_root, product_code)
    deduplicated = package["files"]["deduplicated"]
    rows = _read_602_formal_csv(Path(deduplicated), INPUT_COLUMNS)
    _validate_high_precision_rows(rows)
    package["status"] = "LATEST_VALID_602_RUN_PACKAGE_READY"
    package["run_folder"] = str(data_dir)
    package["files"] = {"deduplicated": deduplicated}
    package["assets"] = {"deduplicated": {"file": deduplicated, "rows": rows,
                                              "schema": list(INPUT_COLUMNS), "run_timestamp": stamp}}
    package["input_record_count"] = len(rows)
    package["input_unique_keyword_count"] = len(rows)
    package["input_resolution_method"] = "REGISTRY_MANIFEST_LATEST_VALID"
    package["manifest"] = package.get("manifest") or {}
    return package

def output_paths(
    product_root: str | Path,
    product_code: str,
    generated_at: str | datetime | None = None,
    *,
    output_directory: str | Path | None = None,
) -> dict[str, Path]:
    """Return both formal CSV paths inside one timestamped package root."""
    if generated_at is None:
        stamp = format_run_timestamp()
    elif isinstance(generated_at, datetime):
        stamp = generated_at.strftime(TIMESTAMP_FORMAT)
    else:
        stamp = str(generated_at).strip()
    if not RUN_TIMESTAMP_RE.fullmatch(stamp):
        raise ValueError(f"INVALID_OUTPUT_TIMESTAMP: {stamp}")
    try:
        datetime.strptime(stamp, TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ValueError(f"INVALID_OUTPUT_TIMESTAMP: {stamp}") from exc
    directory = Path(output_directory) if output_directory is not None else governance_paths(output_root(product_root))["data"]
    return {
        "mapping": directory / f"{MAPPING_STEM}_{stamp}.csv",
        "summary": directory / f"{SUMMARY_STEM}_{stamp}.csv",
    }


def format_run_timestamp(now: datetime | None = None) -> str:
    stamp = (now or datetime.now().astimezone()).strftime(TIMESTAMP_FORMAT)
    if not RUN_TIMESTAMP_RE.fullmatch(stamp):
        raise ValueError("RUN_TIMESTAMP must match YYYYMMDD_HHMMSS")
    return stamp


def output_root(product_root: str | Path) -> Path:
    return resolve_skill_report_dir(product_root, Path(__file__).resolve().parents[1])


def create_run_folder(product_root: str | Path, run_timestamp: str) -> Path:
    if not RUN_TIMESTAMP_RE.fullmatch(run_timestamp):
        raise ValueError("RUN_TIMESTAMP must match YYYYMMDD_HHMMSS")
    try:
        datetime.strptime(run_timestamp, TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ValueError("RUN_TIMESTAMP must be a valid YYYYMMDD_HHMMSS value") from exc
    folder = output_root(product_root)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def run_manifest_path(folder: str | Path, run_timestamp: str, *, legacy: bool = False) -> Path:
    if not RUN_TIMESTAMP_RE.fullmatch(run_timestamp):
        raise ValueError("RUN_TIMESTAMP must match YYYYMMDD_HHMMSS")
    return Path(folder) / (RUN_MANIFEST_NAME if legacy else f"{RUN_MANIFEST_PREFIX}{run_timestamp}.json")


def _available_run_timestamp(product_root: str | Path, product_code: str, run_timestamp: str) -> str:
    candidate = datetime.strptime(run_timestamp, TIMESTAMP_FORMAT)
    root = output_root(product_root)
    while True:
        stamp = candidate.strftime(TIMESTAMP_FORMAT)
        if not run_manifest_path(root, stamp).exists() and not any(path.exists() for path in output_paths(product_root, product_code, stamp).values()):
            return stamp
        candidate += timedelta(seconds=1)


def write_run_manifest(run_folder: str | Path, manifest: Mapping[str, Any]) -> Path:
    target = run_manifest_path(run_folder, str(manifest.get("RUN_TIMESTAMP") or ""))
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, target)
    return target


def _read_603_formal_csv(path: Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_columns:
            raise ValueError(f"603_OUTPUT_SCHEMA_INVALID: {path.name}")
        return list(reader)


def _validate_603_output_package(
    folder: Path, product_code: str, run_timestamp: str | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    legacy_folder = bool(RUN_TIMESTAMP_RE.fullmatch(folder.name))
    stamp = run_timestamp or (folder.name if legacy_folder else "")
    if not RUN_TIMESTAMP_RE.fullmatch(stamp):
        return {"valid": False, "reason": "RUN_TIMESTAMP_INVALID"}
    if manifest_path is None:
        manifest_path = ((folder.parent / "_system" / "manifests") if folder.name == "data" else folder) / (RUN_MANIFEST_NAME if legacy_folder else f"{RUN_MANIFEST_PREFIX}{stamp}.json")
    if not manifest_path.is_file():
        return {"valid": False, "reason": "RUN_MANIFEST_MISSING"}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"valid": False, "reason": "RUN_MANIFEST_INVALID"}
    if manifest.get("SkillId") != SKILL_ID:
        return {"valid": False, "reason": "RUN_SKILL_ID_MISMATCH"}
    if manifest.get("Run Status") != "VALID" or manifest.get("RUN_TIMESTAMP") != stamp:
        return {"valid": False, "reason": "RUN_NOT_VALID"}
    if str(manifest.get("Current Product") or "").strip() != str(product_code).strip():
        return {"valid": False, "reason": "CURRENT_PRODUCT_MISMATCH"}
    try:
        configured_precision_levels = read_precision_filter_levels(folder.parents[1])
    except (OSError, UnicodeError, ValueError) as exc:
        return {"valid": False, "reason": "PRECISION_FILTER_CONFIG_INVALID", "detail": str(exc)}
    run_fields = ("RUN_ID", "GeneratedAt", "Input Source", "Input Skill", "Input Report", "Input Report Identity", "Input Run ID", "Input RUN_TIMESTAMP", "Input Folder", "Input File", "Input Record Count", "Input Unique Keyword Count")
    if any(manifest.get(field) in (None, "") for field in run_fields):
        return {"valid": False, "reason": "RUN_LINEAGE_METADATA_MISSING"}
    input_fields = ("Input Skill", "Input Run ID", "Input RUN_TIMESTAMP", "Input Folder", "Input File")
    if any(not manifest.get(field) for field in input_fields) or manifest.get("Input Skill") != "hzp-amz-6-0-2-ai-precision-keyword-identification":
        return {"valid": False, "reason": "INPUT_LINEAGE_MISSING_OR_INVALID"}
    if not RUN_TIMESTAMP_RE.fullmatch(str(manifest.get("Input RUN_TIMESTAMP") or "")):
        return {"valid": False, "reason": "INPUT_RUN_TIMESTAMP_INVALID"}
    input_folder = Path(str(manifest["Input Folder"]))
    input_file = Path(str(manifest["Input File"]))
    if input_file.parent.resolve() != input_folder.resolve() or not input_file.stem.endswith(f"_{manifest['Input RUN_TIMESTAMP']}") or input_file.name != Path(DEDUPLICATED_NAME.format(product_code=product_code)).stem + f"_{manifest['Input RUN_TIMESTAMP']}.csv":
        return {"valid": False, "reason": "INPUT_RUN_PACKAGE_MISMATCH"}
    declared_folder = str(manifest.get("Output Folder") or "")
    if (not declared_folder
            or (Path(declared_folder).resolve() != folder.resolve() and folder.name != "data")):
        return {"valid": False, "reason": "RUN_FOLDER_DECLARATION_MISMATCH"}
    paths = {
        "mapping": folder / f"{MAPPING_STEM}_{stamp}.csv",
        "summary": folder / f"{SUMMARY_STEM}_{stamp}.csv",
    }
    expected_names = {path.name for path in paths.values()}
    declared = manifest.get("Output Files")
    if not isinstance(declared, list) or len(declared) != 2 or not all(isinstance(name, str) for name in declared) or set(declared) != expected_names:
        return {"valid": False, "reason": "RUN_OUTPUT_DECLARATION_INVALID"}
    if any(path.parent.resolve() != folder.resolve() or not path.is_file() or not path.stem.endswith(f"_{stamp}") for path in paths.values()):
        return {"valid": False, "reason": "RUN_OUTPUT_INCOMPLETE_OR_TIMESTAMP_MISMATCH"}
    run_csvs = {path.name for path in folder.glob(f"*_{stamp}.csv")} if not legacy_folder else {path.name for path in folder.glob("*.csv")}
    if run_csvs != expected_names:
        return {"valid": False, "reason": "RUN_OUTPUT_PACKAGE_INCOMPLETE"}
    try:
        mapping_rows = _read_603_formal_csv(paths["mapping"], MAPPING_COLUMNS)
        summary_rows = _read_603_formal_csv(paths["summary"], SUMMARY_COLUMNS)
        input_rows = _read_602_formal_csv(Path(str(manifest["Input File"])), INPUT_COLUMNS)
        _validate_high_precision_rows(input_rows, precision_levels=configured_precision_levels)
        input_package = _validate_602_run_package(input_folder, product_code, str(manifest["Input RUN_TIMESTAMP"]))
        simple_ok = input_file.is_file() and input_file.stem.endswith(f"_{manifest['Input RUN_TIMESTAMP']}")
        if (not input_package.get("valid") and not simple_ok) or manifest.get("Input Report") != INPUT_REPORT_IDENTITY or manifest.get("Input Report Identity") != INPUT_REPORT_IDENTITY:
            raise ValueError("603_INPUT_602_RUN_PACKAGE_INVALID")
    except (KeyError, OSError, UnicodeError, csv.Error, ValueError) as exc:
        return {"valid": False, "reason": "RUN_OUTPUT_SCHEMA_OR_INPUT_INVALID", "detail": str(exc)}
    counts = manifest.get("Output Record Counts") or {}
    try:
        input_count = int(manifest["Input Record Count"])
        input_unique_count = int(manifest["Input Unique Keyword Count"])
        mapping_count = int(counts["Keyword Count"])
        summary_count = int(counts["Intent Count"])
    except (KeyError, TypeError, ValueError):
        return {"valid": False, "reason": "RUN_RECORD_COUNTS_MISSING"}
    if (len(input_rows) != input_count or input_count != input_unique_count
            or len(input_rows) != input_unique_count or len(mapping_rows) != mapping_count
            or len(summary_rows) != summary_count):
        return {"valid": False, "reason": "RUN_RECORD_COUNT_MISMATCH"}
    if input_count != mapping_count:
        return {"valid": False, "reason": "RUN_INPUT_OUTPUT_COVERAGE_MISMATCH"}
    try:
        _validate_high_precision_rows(input_rows, precision_levels=configured_precision_levels)
    except ValueError as exc:
        return {"valid": False, "reason": "RUN_INPUT_INVALID", "detail": str(exc)}
    integrity = data_integrity_check(input_rows, mapping_rows, summary_rows)
    if not integrity["passed"]:
        return {"valid": False, "reason": "RUN_DATA_INTEGRITY_FAILED", "errors": integrity["errors"]}
    return {
        "valid": True,
        "manifest": manifest,
        "run_id": manifest.get("RUN_ID"),
        "run_timestamp": stamp,
        "run_folder": str(folder),
        "files": {key: str(path) for key, path in paths.items()},
        "input_record_count": input_count,
        "input_unique_keyword_count": input_unique_count,
        "output_record_counts": {"Keyword Count": mapping_count, "Intent Count": summary_count},
    }


def resolve_latest_valid_603_run_package(product_root: str | Path, product_code: str) -> dict[str, Any]:
    """Resolve the newest complete VALID 6-0-3 Run Package with fallback."""
    directory = output_root(product_root)
    if not directory.is_dir():
        return {"status": "603_RUN_PACKAGE_NOT_FOUND", "invalid_runs": []}
    candidates: list[tuple[str, Path, Path]] = []
    data_dir = directory / "data"
    manifest_dir = directory / "_system" / "manifests"
    registry_stamp = None
    registry_path = directory / "_system" / "registry" / "latest.json"
    if registry_path.is_file():
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8-sig"))
            registry_stamp = str(payload.get("RUN_TIMESTAMP") or "")
        except (OSError, UnicodeError, json.JSONDecodeError):
            registry_stamp = None
    for manifest in manifest_dir.glob(f"{RUN_MANIFEST_PREFIX}*.json"):
        match = re.fullmatch(rf"{re.escape(RUN_MANIFEST_PREFIX)}(\d{{8}}_\d{{6}})\.json", manifest.name)
        if match and data_dir.is_dir() and (not registry_stamp or match.group(1) == registry_stamp):
            candidates.append((match.group(1), data_dir, manifest))
    candidates.sort(key=lambda item: (item[0], item[1].name == directory.name), reverse=True)
    invalid_runs: list[dict[str, str]] = []
    for stamp, folder, manifest in candidates:
        package = _validate_603_output_package(folder, product_code, stamp, manifest)
        if package.get("valid"):
            return {"status": "LATEST_VALID_603_RUN_PACKAGE_READY", **package, "invalid_runs": invalid_runs}
        invalid_runs.append({"run_folder": str(folder), "run_timestamp": stamp, "reason": str(package.get("reason"))})
    return {"status": "603_RUN_PACKAGE_NOT_FOUND", "invalid_runs": invalid_runs}


def latest_output_paths(product_root: str | Path, product_code: str) -> dict[str, Path]:
    """Return the two files from the single latest VALID 6-0-3 package."""
    package = resolve_latest_valid_603_run_package(product_root, product_code)
    if package.get("status") != "LATEST_VALID_603_RUN_PACKAGE_READY":
        raise FileNotFoundError(f"LATEST_VALID_603_OUTPUT_NOT_FOUND: {product_code}")
    return {key: Path(value) for key, value in package["files"].items()}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _validate_high_precision_rows(rows: list[dict[str, str]], *, precision_levels: Iterable[Any] | None = None) -> None:
    selected_levels = frozenset(precision_levels or FILTERED_PRECISION_LEVELS)
    headers = tuple(rows[0]) if rows else INPUT_COLUMNS
    if headers != INPUT_COLUMNS:
        raise ValueError(f"{MISSING_INPUT}: invalid unique-keyword schema")
    non_selected = [row.get("Id", "") for row in rows if row.get("精准度", "") not in selected_levels]
    if non_selected:
        raise ValueError(f"{NON_HIGH_PRECISION_RECORD}: {','.join(non_selected)}")
    keywords = [normalize_broad_keyword(row.get("词")) for row in rows]
    if any(not keyword for keyword in keywords):
        raise ValueError(f"{MISSING_INPUT}: blank canonical keyword")
    duplicates = sorted(keyword for keyword, count in Counter(keywords).items() if count > 1)
    if duplicates:
        raise ValueError(f"{DUPLICATE_CANONICAL_KEYWORDS}: {','.join(duplicates)}")
    ids = [str(row.get("Id") or "").strip() for row in rows]
    if any(not record_id for record_id in ids):
        raise ValueError(f"{MISSING_RECORD_IDS}: blank Id")
    duplicate_ids = sorted(record_id for record_id, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"{DUPLICATE_RECORD_IDS}: {','.join(duplicate_ids)}")


def load_6_0_2_input_package(product_root: str | Path, product_code: str) -> dict[str, Any]:
    """Load only the deduplicated high-precision CSV from one VALID 6-0-2 package."""
    package = resolve_latest_valid_602_run_package(product_root, product_code)
    if package.get("status") not in {DUPLICATE_CANONICAL_KEYWORDS, NON_HIGH_PRECISION_RECORD,
                                      "LATEST_VALID_602_RUN_PACKAGE_READY"}:
        package = _resolve_602_c_by_filename(product_root, product_code)
    if package.get("status") != "LATEST_VALID_602_RUN_PACKAGE_READY":
        if package.get("status") in {DUPLICATE_CANONICAL_KEYWORDS, NON_HIGH_PRECISION_RECORD}:
            raise ValueError(package["status"])
        raise FileNotFoundError(f"{MISSING_INPUT}: {package.get('invalid_runs', [])}")
    input_file = package["files"]["deduplicated"]
    rows = _read_602_formal_csv(Path(input_file), INPUT_COLUMNS)
    _validate_high_precision_rows(rows)
    return {**package, "rows": rows, "input_record_count": len(rows),
            "input_unique_keyword_count": len(rows), "deduplicated_file": input_file}


def _resolve_602_c_by_filename(product_root: str | Path, product_code: str) -> dict[str, Any]:
    """V3 simple handoff: select newest C asset by filename timestamp only."""
    directory = Path(product_root).resolve() / "06_SKILL分析报告" / INPUT_RUN_DIR / "data"
    candidates = []
    for path in directory.glob("6-0-2_去重去对标后 筛选后的精准词表_*.csv"):
        match = re.search(r"_(\d{8}_\d{6})\.csv$", path.name)
        if path.is_file() and match:
            candidates.append((match.group(1), path))
    if not candidates:
        return {"status": MISSING_INPUT, "invalid_runs": [{"reason": "602_C_NOT_FOUND"}]}
    stamp, path = max(candidates, key=lambda item: item[0])
    try:
        rows = _read_602_formal_csv(path, INPUT_COLUMNS)
        _validate_high_precision_rows(rows)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        reason = str(exc)
        status = DUPLICATE_CANONICAL_KEYWORDS if "603_INPUT_DUPLICATE_KEYWORD" in reason else (
            NON_HIGH_PRECISION_RECORD if "603_INPUT_NOT_ALL_HIGH_PRECISION" in reason else MISSING_INPUT
        )
        return {"status": status, "invalid_runs": [{"run_timestamp": stamp, "reason": reason}]}
    return {"status": "LATEST_VALID_602_RUN_PACKAGE_READY", "run_id": stamp, "run_timestamp": stamp,
            "run_folder": str(directory), "files": {"deduplicated": str(path)}, "deduplicated_file": str(path),
            "rows": rows, "input_record_count": len(rows), "input_unique_keyword_count": len(rows),
            "input_resolution_method": "FILENAME_TIMESTAMP_MAX", "manifest": {}}


def load_6_0_2_inputs(product_root: str | Path, product_code: str) -> list[dict[str, str]]:
    """Load UNIQUE_SELECTED_PRECISION_KEYWORDS from the latest complete VALID 6-0-2 package."""
    return load_6_0_2_input_package(product_root, product_code)["rows"]


def _tokens(keyword: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", keyword.lower().replace("-", " "))


def normalize_broad_keyword(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _volume(value: Any) -> float | None:
    if value in (None, "", "NULL", DATA_NOT_AVAILABLE):
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _format_volume(value: float | None) -> Any:
    if value is None:
        return DATA_NOT_AVAILABLE
    return int(value) if value.is_integer() else round(value, 2)


def _positive_decimal(value: Any) -> Decimal | None:
    if value in (None, "", "NULL", "null", DATA_NOT_AVAILABLE):
        return None
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number.is_finite() and number > 0 else None


def _average_competitor_count(records: Iterable[Mapping[str, Any]]) -> Decimal | str:
    """Average valid source-record counts; null, invalid and zero values are excluded."""
    values = [
        number
        for record in records
        if (number := _positive_decimal(record.get("\u7ade\u4e89\u4ea7\u54c1\u6570"))) is not None
    ]
    if not values:
        return DATA_NOT_AVAILABLE
    return (sum(values, Decimal("0")) / Decimal(len(values))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _intent_supply_demand_ratio(aggregate_volume: float | None, average_competitors: Any) -> Decimal | str:
    average = _positive_decimal(average_competitors)
    if aggregate_volume is None or average is None:
        return DATA_NOT_AVAILABLE
    volume = Decimal(str(aggregate_volume))
    if not volume.is_finite() or volume < 0:
        return DATA_NOT_AVAILABLE
    return (volume / average).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _metric_matches(actual: Any, expected: Any) -> bool:
    if expected == DATA_NOT_AVAILABLE:
        return actual == DATA_NOT_AVAILABLE
    try:
        actual_decimal = Decimal(str(actual).replace(",", "").strip())
        expected_decimal = Decimal(str(expected))
    except (InvalidOperation, TypeError, ValueError):
        return False
    return actual_decimal.is_finite() and expected_decimal.is_finite() and actual_decimal == expected_decimal


def _find_dimension(tokens: list[str], patterns: tuple[tuple[tuple[str, ...], str], ...]) -> str:
    for pattern, label in patterns:
        for start in range(len(tokens) - len(pattern) + 1):
            if tuple(tokens[start:start + len(pattern)]) == pattern:
                return label
    return ""


def default_semantic_mapper(row: Mapping[str, Any]) -> dict[str, str]:
    """Conservative local fallback returning a primary intent and its parent.

    Production runs may inject a richer AI mapper with the same keys.  The
    fallback preserves an occasion only when it forms a meaningful child
    intent; numeric and promotional modifiers remain compressed.
    """
    keyword = str(row.get("\u8bcd") or "").strip()
    tokens = _tokens(keyword)
    relation = _find_dimension(tokens, RELATION_PATTERNS)
    occasion = _find_dimension(tokens, OCCASION_PATTERNS)
    anchors = [token for token in tokens if token in PRODUCT_ANCHORS]
    if relation and anchors:
        anchor = "gifts" if any(token in {"gift", "gifts", "present", "presents"} for token in anchors) else anchors[0]
        broad = f"{relation} {occasion} {anchor}" if occasion and anchor == "gifts" else f"{relation} {anchor}"
        parent = f"{relation} {anchor}" if occasion and anchor == "gifts" else ""
    else:
        core = [token for token in tokens if token not in STOP_WORDS and token not in SECONDARY_MODIFIERS]
        broad = " ".join(core[:3])
        parent = ""
    return {
        "\u7cbe\u51c6\u6cdb\u8bcd": normalize_broad_keyword(broad),
        "\u7cbe\u51c6\u6cdb\u8bcd\u4e2d\u6587": str(row.get("\u4e2d\u6587") or "").strip(),
        "\u7236\u7cbe\u51c6\u6cdb\u8bcd": normalize_broad_keyword(parent),
    }


def _stable_intent_identity(intent: str) -> tuple[str, str]:
    canonical = normalize_broad_keyword(intent)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12].upper()
    return f"INTENT-{digest}", f"INTENT_{digest}"


def adaptive_semantic_batches(units: list[Mapping[str, Any]], *, profile_chars: int = 0,
                              target_chars: int = 24000) -> list[list[Mapping[str, Any]]]:
    """Split semantic units by estimated prompt size, not a fixed row count."""
    budget = max(4000, target_chars - max(0, int(profile_chars)))
    batches: list[list[Mapping[str, Any]]] = []
    current: list[Mapping[str, Any]] = []
    current_chars = 0
    for unit in units:
        estimate = len(json.dumps(unit, ensure_ascii=False)) + 32
        if current and current_chars + estimate > budget:
            batches.append(current)
            current, current_chars = [], 0
        current.append(unit)
        current_chars += estimate
    if current:
        batches.append(current)
    return batches


def load_current_product_profile(product_root: str | Path) -> dict[str, Any]:
    """Load the shared current-product text once for Intent interpretation."""
    path = Path(product_root).resolve() / "05_分析源数据" / "01_产品数据" / "本产品" / "产品识别 - 文本文案.txt"
    if not path.is_file():
        return {"status": "PRODUCT_PROFILE_NOT_FOUND", "path": str(path), "text": ""}
    try:
        text = path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError):
        return {"status": "PRODUCT_PROFILE_READ_FAILED", "path": str(path), "text": ""}
    return {"status": "READY" if text else "PRODUCT_PROFILE_EMPTY", "path": str(path), "text": text}


def build_intent_brain_mapping(rows: Iterable[Mapping[str, Any]], *, client: Callable[[str], Iterable[Mapping[str, Any]]] | None = None,
                               product_profile: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Two-phase local/host Intent Brain with global reconciliation.

    Phase A creates one semantic unit per unique keyword. Phase B reconciles
    candidate intents globally, so batches cannot create duplicate identities.
    A host may replace the semantic mapper through ``client``; the fallback is
    conservative and does not use market metrics to make semantic decisions.
    """
    source = list(rows)
    units = []
    for row in source:
        keyword = normalize_broad_keyword(row.get("词"))
        units.append({"Id": str(row.get("Id") or "").strip(), "Keyword": keyword,
                      "KeywordCn": str(row.get("中文") or "").strip()})
    if client is not None:
        semantic = []
        profile_text = str((product_profile or {}).get("text") or "")
        for batch in adaptive_semantic_batches(units, profile_chars=len(profile_text)):
            payload = json.dumps({"phase": "A", "units": batch,
                                  "current_product_profile": profile_text,
                                  "global_reconciliation_required": True}, ensure_ascii=False)
            semantic.extend(list(client(payload)))
        by_id = {str(item.get("Id") or item.get("JudgmentItemId") or "").strip(): item for item in semantic if isinstance(item, Mapping)}
        if len(by_id) != len(units):
            raise ValueError("SEMANTIC_BATCH_FAILED")
        candidates = [by_id[unit["Id"]] for unit in units]
    else:
        candidates = [default_semantic_mapper(row) for row in source]
    output = []
    for row, result in zip(source, candidates):
        broad, chinese, parent = _mapping_result(result, row)
        intent_id, intent_code = _stable_intent_identity(broad)
        parent_id, _ = _stable_intent_identity(parent) if parent else ("", "")
        challenge_value = result.get("ChallengeResult") if isinstance(result, Mapping) else None
        reason_value = result.get("IntentAssignmentReason") if isinstance(result, Mapping) else None
        challenge_reason_value = result.get("ChallengeReasonSummary") if isinstance(result, Mapping) else None
        output.append({"_result": result, "_broad": broad, "_chinese": chinese or DATA_NOT_AVAILABLE,
                       "_parent": parent, "_intent_id": intent_id, "_intent_code": intent_code,
                       "_parent_id": parent_id, "_reason": str(reason_value or "基于Purchase Mission与关系/场景维度完成全局Intent归并"),
                       "_challenge": str(challenge_value or "CONFIRMED"),
                       "_challenge_reason": str(challenge_reason_value or "未发现把公共字符串误当Intent的证据")})
    return output


def _mapping_result(result: Any, row: Mapping[str, Any]) -> tuple[str, str, str]:
    if isinstance(result, Mapping):
        primary_intents = result.get("primary_intents")
        if isinstance(primary_intents, (list, tuple)) and len(primary_intents) != 1:
            raise ValueError(f"{MULTIPLE_PRIMARY_INTENTS}: {row.get('Id', '')}")
        broad = result.get("\u7cbe\u51c6\u6cdb\u8bcd") or result.get("broad_keyword") or result.get("keyword")
        chinese = result.get("\u7cbe\u51c6\u6cdb\u8bcd\u4e2d\u6587") or result.get("chinese") or result.get("\u4e2d\u6587")
        parent_value = result.get("\u7236\u7cbe\u51c6\u6cdb\u8bcd") or result.get("parent") or ""
        if isinstance(parent_value, (list, tuple)):
            if len(parent_value) > 1:
                raise ValueError(f"{MULTIPLE_DIRECT_PARENTS}: {row.get('Id', '')}")
            parent_value = parent_value[0] if parent_value else ""
        parent = parent_value
    elif isinstance(result, (tuple, list)):
        broad = result[0] if result else ""
        chinese = result[1] if len(result) > 1 else row.get("\u4e2d\u6587")
        parent = result[2] if len(result) > 2 else ""
    else:
        broad, chinese = result, row.get("\u4e2d\u6587")
        parent = ""
    normalized_broad = normalize_broad_keyword(broad)
    if not normalized_broad:
        raise ValueError(f"{PRIMARY_INTENT_MISSING}: {row.get('Id', '')}")
    return normalized_broad, str(chinese or "").strip(), normalize_broad_keyword(parent)


def build_mapping_rows(
    rows: Iterable[Mapping[str, Any]],
    mapper: Callable[[Mapping[str, Any]], Any] | None = None,
    *,
    product_profile: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Map every input record once, preserving Id and input order."""
    source = list(rows)
    brain_results = build_intent_brain_mapping(source, product_profile=product_profile) if mapper is None else None
    map_fn = mapper or default_semantic_mapper
    output: list[dict[str, Any]] = []
    for index, row in enumerate(source):
        brain = brain_results[index] if brain_results is not None else {}
        broad, chinese, parent = (brain["_broad"], brain["_chinese"], brain["_parent"]) if brain else _mapping_result(map_fn(row), row)
        if len(_tokens(broad)) < 2:
            broad = UNRESOLVED_MAPPING
            chinese = DATA_NOT_AVAILABLE
            parent = ""
        output.append({
            "Id": str(row.get("Id") or "").strip(),
            "\u8bcd": str(row.get("\u8bcd") or "").strip(),
            "\u4e2d\u6587": str(row.get("\u4e2d\u6587") or "").strip(),
            "\u5e02\u573a\u5bb9\u91cf": str(row.get("\u5e02\u573a\u5bb9\u91cf") or "").strip(),
            "\u7ade\u4e89\u4ea7\u54c1\u6570": row.get("\u7ade\u4e89\u4ea7\u54c1\u6570"),
            "\u4f9b\u9700\u6bd4": row.get("\u4f9b\u9700\u6bd4"),
            "\u81ea\u7136\u6392\u540d": str(row.get("\u6700\u4f73\u81ea\u7136\u6392\u540d", row.get("\u81ea\u7136\u6392\u540d")) or "").strip(),
            "\u7cbe\u51c6\u6cdb\u8bcd": broad,
            "\u7cbe\u51c6\u6cdb\u8bcd\u4e2d\u6587": chinese or DATA_NOT_AVAILABLE,
            "PrimaryIntentId": brain.get("_intent_id", _stable_intent_identity(broad)[0]),
            "PrimaryIntentCode": brain.get("_intent_code", _stable_intent_identity(broad)[1]),
            "KeywordPurchaseMission": broad,
            "Intent\u5c42\u7ea7": "L2" if parent else "L1",
            "ParentIntentId": brain.get("_parent_id", _stable_intent_identity(parent)[0] if parent else ""),
            "\u7236\u7cbe\u51c6\u6cdb\u8bcd": parent,
            "IntentAssignmentReason": brain.get("_reason", "外部Intent映射结果"),
            "ChallengeResult": brain.get("_challenge", "DATA_NOT_AVAILABLE"),
            "ChallengeReasonSummary": brain.get("_challenge_reason", DATA_NOT_AVAILABLE),
            "_parent": parent,
        })
    return output


def _validate_parent_tree(mapping_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    intents = {normalize_broad_keyword(row.get("\u7cbe\u51c6\u6cdb\u8bcd")) for row in mapping_rows if row.get("\u7cbe\u51c6\u6cdb\u8bcd")}
    parents: dict[str, str] = {}
    for row in mapping_rows:
        intent = normalize_broad_keyword(row.get("\u7cbe\u51c6\u6cdb\u8bcd"))
        parent = normalize_broad_keyword(row.get("_parent"))
        if not intent:
            raise ValueError(PRIMARY_INTENT_MISSING)
        if parent:
            if intent in parents and parents[intent] != parent:
                raise ValueError(f"{MULTIPLE_DIRECT_PARENTS}: {intent}")
            parents[intent] = parent
            if parent not in intents:
                raise ValueError(f"{ORPHAN_PARENT_INTENT}: {intent}->{parent}")
    state: dict[str, int] = {}
    def visit(node: str) -> None:
        if state.get(node) == 1:
            raise ValueError(f"{PARENT_CYCLE_DETECTED}: {node}")
        if state.get(node) == 2:
            return
        state[node] = 1
        if node in parents:
            visit(parents[node])
        state[node] = 2
    for intent in intents:
        visit(intent)
    levels: dict[str, int] = {}
    def level(node: str) -> int:
        if node not in parents:
            return 1
        if node not in levels:
            levels[node] = level(parents[node]) + 1
        return levels[node]
    for intent in intents:
        levels[intent] = level(intent)
    return {"intents": intents, "parents": parents, "levels": levels}


def aggregate_mapping_rows(mapping_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build the Intent Tree and calculate volume and competitor metrics in code."""
    rows = list(mapping_rows)
    tree = _validate_parent_tree(rows)
    groups: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    for row in rows:
        record_id = str(row.get("Id") or "").strip()
        if not record_id:
            raise ValueError(f"{MISSING_RECORD_IDS}: blank Id")
        if record_id in seen_ids:
            raise ValueError(f"{DUPLICATE_RECORD_IDS}: {record_id}")
        seen_ids.add(record_id)
        key = normalize_broad_keyword(row.get("\u7cbe\u51c6\u6cdb\u8bcd")) or UNRESOLVED_MAPPING
        group = groups.setdefault(key, {
            "\u7cbe\u51c6\u6cdb\u8bcd": key,
            "\u4e2d\u6587": str(row.get("\u7cbe\u51c6\u6cdb\u8bcd\u4e2d\u6587") or DATA_NOT_AVAILABLE),
            "volumes": [],
            "source_records": [],
            "\u76f4\u63a5\u5bf9\u5e94\u8bcd\u6570": 0,
            "first_index": len(groups),
            "IntentId": row.get("PrimaryIntentId") or _stable_intent_identity(key)[0],
            "IntentCode": row.get("PrimaryIntentCode") or _stable_intent_identity(key)[1],
            "IntentDefinition": row.get("KeywordPurchaseMission") or key,
            "PrimaryPurchaseDriver": row.get("PrimaryPurchaseDriver") or DATA_NOT_AVAILABLE,
            "ChallengeStatus": row.get("ChallengeResult") or DATA_NOT_AVAILABLE,
            "ChallengeReasonSummary": row.get("ChallengeReasonSummary") or DATA_NOT_AVAILABLE,
        })
        group["volumes"].append(_volume(row.get("\u5e02\u573a\u5bb9\u91cf")))
        group["source_records"].append({
            "Id": record_id,
            "\u7ade\u4e89\u4ea7\u54c1\u6570": row.get("\u7ade\u4e89\u4ea7\u54c1\u6570"),
        })
        group["\u76f4\u63a5\u5bf9\u5e94\u8bcd\u6570"] += 1
        if group["\u4e2d\u6587"] == DATA_NOT_AVAILABLE and row.get("\u7cbe\u51c6\u6cdb\u8bcd\u4e2d\u6587"):
            group["\u4e2d\u6587"] = str(row["\u7cbe\u51c6\u6cdb\u8bcd\u4e2d\u6587"])
    direct: dict[str, float | None] = {}
    for key, group in groups.items():
        direct[key] = sum(group["volumes"]) if group["volumes"] and all(value is not None for value in group["volumes"]) else None
    children: dict[str, list[str]] = {intent: [] for intent in tree["intents"]}
    for child, parent in tree["parents"].items():
        children[parent].append(child)
    subtree_records: dict[str, dict[str, Mapping[str, Any]]] = {}
    def records_for(intent: str) -> dict[str, Mapping[str, Any]]:
        if intent in subtree_records:
            return subtree_records[intent]
        records = {
            str(record["Id"]): record
            for record in groups.get(intent, {}).get("source_records", [])
        }
        for child in children.get(intent, []):
            records.update(records_for(child))
        subtree_records[intent] = records
        return records
    for intent in tree["intents"]:
        records_for(intent)
    aggregate: dict[str, float | None] = {}
    def total(intent: str) -> float | None:
        if intent in aggregate:
            return aggregate[intent]
        values = [direct.get(intent)] + [total(child) for child in children.get(intent, [])]
        aggregate[intent] = sum(values) if all(value is not None for value in values) else None
        return aggregate[intent]
    for intent in tree["intents"]:
        total(intent)
    if sum(group["\u76f4\u63a5\u5bf9\u5e94\u8bcd\u6570"] for group in groups.values()) != len(rows):
        raise ValueError(AGGREGATION_MISMATCH)
    for intent in tree["intents"]:
        if aggregate[intent] is not None and direct.get(intent) is not None and aggregate[intent] < direct[intent]:
            raise ValueError(AGGREGATION_MISMATCH)
        if not children.get(intent) and aggregate[intent] != direct.get(intent):
            raise ValueError(AGGREGATION_MISMATCH)
        if children.get(intent) and direct.get(intent) is not None and all(aggregate.get(child) is not None for child in children[intent]) and aggregate[intent] != direct[intent] + sum(aggregate[child] for child in children[intent]):
            raise ValueError(AGGREGATION_MISMATCH)
    source_volumes = [_volume(row.get("\u5e02\u573a\u5bb9\u91cf")) for row in rows]
    roots = [intent for intent in tree["intents"] if intent not in tree["parents"]]
    if all(value is not None for value in source_volumes) and all(aggregate[root] is not None for root in roots):
        if sum(aggregate[root] for root in roots) != sum(source_volumes):
            raise ValueError(ROOT_VOLUME_MISMATCH)
    output: list[dict[str, Any]] = []
    for key, group in groups.items():
        average_competitors = _average_competitor_count(subtree_records.get(key, {}).values())
        output.append({
            "\u7cbe\u51c6\u6cdb\u8bcd": key,
            "\u4e2d\u6587": group["\u4e2d\u6587"],
            "\u5c42\u7ea7": f"L{tree['levels'].get(key, 1)}",
            "\u7236\u7cbe\u51c6\u6cdb\u8bcd": tree["parents"].get(key, ""),
            "\u76f4\u63a5\u641c\u7d22\u91cf": _format_volume(direct.get(key)),
            "\u6c47\u603b\u641c\u7d22\u91cf": _format_volume(aggregate.get(key)),
            "\u5e73\u5747\u7ade\u54c1\u6570": average_competitors,
            "\u610f\u56fe\u673a\u4f1a\u6bd4": _intent_supply_demand_ratio(aggregate.get(key), average_competitors),
            "\u76f4\u63a5\u5bf9\u5e94\u8bcd\u6570": group["\u76f4\u63a5\u5bf9\u5e94\u8bcd\u6570"],
            "IntentId": group["IntentId"],
            "IntentCode": group["IntentCode"],
            "IntentDefinition": group["IntentDefinition"],
            "PrimaryPurchaseDriver": group["PrimaryPurchaseDriver"],
            "ChallengeStatus": group["ChallengeStatus"],
            "ChallengeReasonSummary": group["ChallengeReasonSummary"],
            "_first_index": group["first_index"],
        })
    output.sort(key=lambda row: (
        int(row["\u5c42\u7ea7"][1:]),
        row["\u6c47\u603b\u641c\u7d22\u91cf"] == DATA_NOT_AVAILABLE,
        -(float(row["\u6c47\u603b\u641c\u7d22\u91cf"]) if row["\u6c47\u603b\u641c\u7d22\u91cf"] != DATA_NOT_AVAILABLE else 0),
        row["_first_index"],
    ))
    for row in output:
        row.pop("_first_index", None)
    return output


def coverage_check(input_rows: Iterable[Mapping[str, Any]], mapping_rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    input_ids = [str(row.get("Id") or "").strip() for row in input_rows]
    output_ids = [str(row.get("Id") or "").strip() for row in mapping_rows]
    missing = sorted(set(input_ids) - set(output_ids))
    extra = sorted(set(output_ids) - set(input_ids))
    duplicate_output = sorted(record_id for record_id, count in Counter(output_ids).items() if count > 1)
    return {
        "passed": not missing and not extra and not duplicate_output and len(input_ids) == len(output_ids),
        "input_count": len(input_ids),
        "mapping_count": len(output_ids),
        "missing_ids": missing,
        "extra_ids": extra,
        "duplicate_output_ids": duplicate_output,
    }


def data_integrity_check(
    input_rows: Iterable[Mapping[str, Any]],
    mapping_rows: Iterable[Mapping[str, Any]],
    summary_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Check source pass-through and intent metrics against unique source records."""
    source = list(input_rows)
    mapping = list(mapping_rows)
    summary = list(summary_rows)
    errors: list[str] = []
    coverage = coverage_check(source, mapping)
    if not coverage["passed"]:
        errors.append(f"{MISSING_RECORD_IDS}: {coverage}")

    def raw(value: Any) -> str:
        return "" if value is None else str(value)

    source_by_id = {str(row.get("Id") or "").strip(): row for row in source}
    mapping_by_id = {str(row.get("Id") or "").strip(): row for row in mapping}
    for record_id in source_by_id.keys() & mapping_by_id.keys():
        source_row = source_by_id[record_id]
        mapping_row = mapping_by_id[record_id]
        if raw(source_row.get("\u7ade\u4e89\u4ea7\u54c1\u6570")) != raw(mapping_row.get("\u7ade\u4e89\u4ea7\u54c1\u6570")):
            errors.append(f"{COMPETITOR_PASSTHROUGH_MISMATCH}: {record_id}")
        if raw(source_row.get("\u4f9b\u9700\u6bd4")) != raw(mapping_row.get("\u4f9b\u9700\u6bd4")):
            errors.append(f"{SUPPLY_DEMAND_PASSTHROUGH_MISMATCH}: {record_id}")

    summary_by_intent: dict[str, Mapping[str, Any]] = {}
    for item in summary:
        intent = normalize_broad_keyword(item.get("\u7cbe\u51c6\u6cdb\u8bcd"))
        if intent in summary_by_intent:
            errors.append(f"DUPLICATE_SUMMARY_INTENT: {intent}")
        summary_by_intent[intent] = item
    records_by_intent: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in mapping:
        intent = normalize_broad_keyword(row.get("\u7cbe\u51c6\u6cdb\u8bcd")) or UNRESOLVED_MAPPING
        record_id = str(row.get("Id") or "").strip()
        if not record_id:
            errors.append(f"{MISSING_RECORD_IDS}: blank Id")
            continue
        records = records_by_intent.setdefault(intent, {})
        if record_id in records:
            errors.append(f"{DUPLICATE_RECORD_IDS}: {record_id}")
        records[record_id] = row

    summary_tree_rows = [
        {
            "\u7cbe\u51c6\u6cdb\u8bcd": intent,
            "_parent": item.get("\u7236\u7cbe\u51c6\u6cdb\u8bcd"),
        }
        for intent, item in summary_by_intent.items()
    ]
    try:
        tree = _validate_parent_tree(summary_tree_rows)
    except ValueError as exc:
        errors.append(f"SUMMARY_TREE_INVALID: {exc}")
        tree = {"intents": set(), "parents": {}}
    expected_intents = set(records_by_intent)
    if expected_intents != set(summary_by_intent):
        errors.append("SUMMARY_INTENT_COVERAGE_MISMATCH")

    children: dict[str, list[str]] = {intent: [] for intent in tree["intents"]}
    for child, parent in tree["parents"].items():
        children[parent].append(child)
    subtree_cache: dict[str, dict[str, Mapping[str, Any]]] = {}

    def records_for(intent: str) -> dict[str, Mapping[str, Any]]:
        if intent in subtree_cache:
            return subtree_cache[intent]
        records = dict(records_by_intent.get(intent, {}))
        for child in children.get(intent, []):
            records.update(records_for(child))
        subtree_cache[intent] = records
        return records

    for intent, item in summary_by_intent.items():
        subtree = records_for(intent)
        expected_average = _average_competitor_count(subtree.values())
        if not _metric_matches(item.get("\u5e73\u5747\u7ade\u54c1\u6570"), expected_average):
            errors.append(f"{AVERAGE_COMPETITOR_MISMATCH}: {intent}")
        expected_ratio = _intent_supply_demand_ratio(
            _volume(item.get("\u6c47\u603b\u641c\u7d22\u91cf")),
            expected_average,
        )
        if not _metric_matches(item.get("\u610f\u56fe\u673a\u4f1a\u6bd4"), expected_ratio):
            errors.append(f"{INTENT_RATIO_MISMATCH}: {intent}")
    return {"passed": not errors, "errors": errors}


def write_csv(path: str | Path, rows: Iterable[Mapping[str, Any]], columns: Iterable[str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    values = list(rows)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="", dir=target.parent,
            prefix=f".{target.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary_name = handle.name
            writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
            writer.writeheader()
            writer.writerows(values)
        os.replace(temporary_name, target)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return target


def run(
    product_root: str | Path,
    product_code: str,
    mapper: Callable[[Mapping[str, Any]], Any] | None = None,
    generated_at: str | datetime | None = None,
) -> dict[str, Any]:
    input_package = load_6_0_2_input_package(product_root, product_code)
    rows = input_package["rows"]
    if isinstance(generated_at, str):
        try:
            started_at = datetime.strptime(generated_at, TIMESTAMP_FORMAT).astimezone()
        except ValueError as exc:
            raise ValueError(f"INVALID_OUTPUT_TIMESTAMP: {generated_at}") from exc
    else:
        started_at = generated_at or datetime.now().astimezone()
        started_at = started_at.astimezone()
    run_timestamp = _available_run_timestamp(product_root, product_code, format_run_timestamp(started_at))
    report_root = output_root(product_root)
    build_folder = governance_paths(report_root)["staging"] / f"{run_timestamp}_build"
    build_folder.mkdir(parents=True, exist_ok=False)
    run_folder = build_folder
    paths = output_paths(product_root, product_code, generated_at=run_timestamp, output_directory=build_folder)
    manifest_path = run_manifest_path(run_folder, run_timestamp)
    report_error = validate_hzp_amz_report_batch(
        [*paths.values(), manifest_path], product_root, Path(__file__).resolve().parents[1],
        timestamp=run_timestamp, allow_run_folder=True,
    )
    if report_error:
        raise ValueError(report_error)
    product_profile = load_current_product_profile(product_root)
    manifest: dict[str, Any] = {
        "SkillId": SKILL_ID,
        "Current Product": product_code,
        "RUN_ID": run_timestamp,
        "RUN_TIMESTAMP": run_timestamp,
        "GeneratedAt": started_at.isoformat(timespec="seconds"),
        "Input Source": f"6-0-2 data / filename timestamp max / {INPUT_REPORT_IDENTITY}",
        "Input Report": INPUT_REPORT_IDENTITY,
        "Input Report Identity": INPUT_REPORT_IDENTITY,
        "Input Skill": "hzp-amz-6-0-2-ai-precision-keyword-identification",
        "Input Run ID": input_package.get("run_id"),
        "Input RUN_TIMESTAMP": input_package.get("run_timestamp"),
        "Input Folder": input_package.get("run_folder"),
        "Input File": input_package.get("deduplicated_file"),
        "Input Resolution Method": input_package.get("input_resolution_method"),
        "Current Product Profile": product_profile.get("path"),
        "Current Product Profile Status": product_profile.get("status"),
        "Input Record Count": len(rows),
        "Input Unique Keyword Count": len(rows),
        "Output Folder": str(run_folder),
        "Output Files": [paths["summary"].name, paths["mapping"].name],
        "Output Record Counts": {"Intent Count": None, "Keyword Count": None},
        "Run Status": "RUNNING",
    }
    try:
        write_run_manifest(run_folder, manifest)
        mapping = build_mapping_rows(rows, mapper=mapper, product_profile=product_profile)
        coverage = coverage_check(rows, mapping)
        if not coverage["passed"]:
            raise ValueError(f"{MISSING_RECORD_IDS}: {coverage}")
        summary = aggregate_mapping_rows(mapping)
        integrity = data_integrity_check(rows, mapping, summary)
        if not integrity["passed"]:
            raise ValueError(f"603_DATA_INTEGRITY_CHECK_FAILED: {integrity['errors']}")
        write_csv(paths["summary"], summary, SUMMARY_COLUMNS)
        write_csv(paths["mapping"], mapping, MAPPING_COLUMNS)
        readback_mapping = _read_603_formal_csv(paths["mapping"], MAPPING_COLUMNS)
        readback_summary = _read_603_formal_csv(paths["summary"], SUMMARY_COLUMNS)
        readback_integrity = data_integrity_check(rows, readback_mapping, readback_summary)
        if not readback_integrity["passed"]:
            raise ValueError(f"603_OUTPUT_READBACK_INTEGRITY_CHECK_FAILED: {readback_integrity['errors']}")
        if any(path.parent.resolve() != run_folder.resolve() or not path.stem.endswith(f"_{run_timestamp}") for path in paths.values()):
            raise ValueError("603_RUN_FOLDER_FILE_TIMESTAMP_MISMATCH")
        if {path.name for path in run_folder.glob(f"*_{run_timestamp}.csv")} != {path.name for path in paths.values()}:
            raise ValueError("603_RUN_OUTPUT_PACKAGE_INCOMPLETE")
        manifest["Output Record Counts"] = {"Intent Count": len(readback_summary), "Keyword Count": len(readback_mapping)}
        manifest["Validation"] = {"Coverage": coverage, "Data Integrity": integrity, "Readback Integrity": readback_integrity}
        manifest["Run Status"] = "VALID"
        write_run_manifest(run_folder, manifest)
        package = _validate_603_output_package(run_folder, product_code, run_timestamp, manifest_path)
        if not package.get("valid"):
            raise ValueError(f"603_RUN_VALIDATION_FAILED: {package.get('reason')}")
        published = publish_latest_valid_batch(
            report_root,
            run_timestamp,
            list(paths.values()),
            manifest_files=[manifest_path],
            registry_payload={
                "Skill_ID": SKILL_ID,
                "Product_Code": product_code,
                "RUN_ID": run_timestamp,
                "RUN_TIMESTAMP": run_timestamp,
                "Report_Identities": ["PRECISION_BROAD_MAPPING", "PRECISION_BROAD_SUMMARY"],
                "Files": [path.name for path in paths.values()],
            },
            move_sources=True,
        )
        import shutil
        shutil.rmtree(build_folder, ignore_errors=True)
        manifest_target = Path(report_root) / "_system" / "manifests" / manifest_path.name
        try:
            published_manifest = json.loads(manifest_target.read_text(encoding="utf-8-sig"))
            published_manifest["Output Folder"] = str(Path(published["data_dir"]))
            manifest_target.write_text(json.dumps(published_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise ValueError("603_RUN_MANIFEST_PUBLISH_UPDATE_FAILED")
        return {
            **{key: Path(published["data_dir"]) / path.name for key, path in paths.items()},
            "run_id": run_timestamp,
            "run_timestamp": run_timestamp,
            "run_folder": Path(published["data_dir"]),
            "run_manifest": Path(report_root) / "_system" / "manifests" / manifest_path.name,
            "input_run_id": input_package.get("run_id"),
            "input_run_timestamp": input_package.get("run_timestamp"),
            "input_folder": input_package.get("run_folder"),
            "input_file": input_package.get("deduplicated_file"),
            "input_unique_keyword_count": len(rows),
            "input_record_count": len(rows),
        }
    except Exception as exc:
        manifest["Run Status"] = "FAILED"
        manifest["Failure"] = {"status": type(exc).__name__, "message": str(exc)}
        write_run_manifest(run_folder, manifest)
        raise


def extract_broad_rows(rows: Iterable[Mapping[str, Any]], mapper: Callable[[Mapping[str, Any]], Any] | None = None) -> list[dict[str, Any]]:
    """Compatibility helper returning the new aggregate rows."""
    return aggregate_mapping_rows(build_mapping_rows(rows, mapper=mapper))

