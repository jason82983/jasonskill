"""Deterministic 6-0-6 Benchmark x Search Intent occupancy analysis."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from stage6_artifact_contract import resolve_latest_valid_report

SKILL_ID = "hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis"
RUN_MANIFEST = "run_manifest.json"
RUN_MANIFEST_PREFIX = "run_manifest_"
RUN_TIMESTAMP_RE = re.compile(r"^\d{8}_\d{6}$")
REPORT_ROOT = "6-0-6_对标意图市场占领分析"
INPUT_602_ROOT = "6-0-2_AI精准关键词识别"
INPUT_603_ROOT = "6-0-3_精准泛词提取"
DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"
DETAIL_COLUMNS = (
    "对标编码", "对标ASIN", "精准泛词", "中文", "层级", "父精准泛词", "汇总搜索量",
    "有效排名词数", "Top10关键词数", "Top20关键词数", "Top50关键词数", "Top100关键词数",
    "平均自然排名", "加权自然排名", "Top10占领搜索量", "Top10搜索量覆盖率",
    "Top20占领搜索量", "Top20搜索量覆盖率", "Top50占领搜索量", "Top50搜索量覆盖率",
    "Top100占领搜索量", "Top100搜索量覆盖率", "占领等级", "占领判断原因",
)
CONSENSUS_COLUMNS = (
    "精准泛词", "中文", "层级", "父精准泛词", "汇总搜索量", "对标总数", "有效覆盖对标数",
    "核心占领对标数", "强占领对标数", "核心/强占领对标数", "最佳对标编码", "最佳对标ASIN",
    "最佳Top20搜索量覆盖率", "Top20覆盖率中位数", "Top50覆盖率中位数",
    "多对标共识等级", "共识判断原因",
)
INPUT_602_COLUMNS = (
    "所属产品编号", "对标ASIN", "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名", "精准度", "精准原因",
)
INPUT_603_SUMMARY_COLUMNS = (
    "精准泛词", "中文", "层级", "父精准泛词", "直接搜索量", "汇总搜索量", "平均竞品数",
    "意图机会比", "直接对应词数",
)
INPUT_603_MAPPING_COLUMNS = (
    "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数",
    "最佳自然排名", "自然排名中位数", "精准泛词", "精准泛词中文",
)
INPUT_603_SINGLE_MAPPING_COLUMNS = (
    "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名", "精准泛词", "精准泛词中文",
)
OCCUPANCY_LEVELS = {"核心占领", "强占领", "中度占领", "弱占领"}
CONSENSUS_LEVELS = {"高共识", "中共识", "低共识", "单点验证", "单对标模式"}
THRESHOLDS = (10, 20, 50, 100)
EPSILON = Decimal("0.0000001")


class ContractError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def _decimal(value: Any, code: str, *, blank_ok: bool = False) -> Decimal | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if blank_ok:
            return None
        raise ContractError(code, "empty numeric field")
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        raise ContractError(code, f"not numeric: {value!r}") from None
    if not number.is_finite():
        raise ContractError(code, f"not finite: {value!r}")
    return number


def _number_text(value: Decimal | None, places: int = 4) -> str:
    if value is None:
        return DATA_NOT_AVAILABLE
    quantum = Decimal(1).scaleb(-places)
    result = value.quantize(quantum, rounding=ROUND_HALF_UP)
    return format(result.normalize(), "f") if result == result.to_integral() else format(result, "f").rstrip("0").rstrip(".")


def _rate_text(value: Decimal | None) -> str:
    if value is None:
        return DATA_NOT_AVAILABLE
    return f"{(value * Decimal(100)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)}%"


def _parse_rate(value: Any) -> Decimal | None:
    if value in (None, "", DATA_NOT_AVAILABLE):
        return None
    text = str(value).strip()
    if text.endswith("%"):
        return _decimal(text[:-1], "606_INPUT_SCHEMA_INVALID") / Decimal(100)
    return _decimal(text, "606_INPUT_SCHEMA_INVALID")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            return list(reader.fieldnames or []), list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ContractError("606_INPUT_NOT_FOUND", f"{path}: {type(exc).__name__}") from exc


def _manifest_outputs(manifest: Mapping[str, Any]) -> list[str]:
    return [Path(value).name for value in _manifest_output_values(manifest)]


def _manifest_output_values(manifest: Mapping[str, Any]) -> list[str]:
    outputs = manifest.get("Output Files") or manifest.get("output_files") or []
    if isinstance(outputs, dict):
        outputs = list(outputs.values())
    if not isinstance(outputs, list):
        return []
    return [str(value) for value in outputs]


def _valid_timestamp(value: str) -> bool:
    if not RUN_TIMESTAMP_RE.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y%m%d_%H%M%S")
        return True
    except ValueError:
        return False


def _read_manifest(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        return raw if isinstance(raw, dict) else None
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _validate_603_manifest_package(
    folder: Path, product_code: str, manifest: Mapping[str, Any],
    declared_values: list[str], files: Mapping[str, Path],
) -> None:
    stamp = str(manifest.get("RUN_TIMESTAMP") or "")
    if not _valid_timestamp(stamp):
        raise ContractError("603_RUN_TIMESTAMP_INVALID")
    if len(declared_values) != 2 or any(Path(value).name != value for value in declared_values):
        raise ContractError("603_RUN_OUTPUTS_INVALID", "expected exactly two local CSV filenames")
    if str(manifest.get("Current Product") or "").strip() != product_code:
        raise ContractError("603_PRODUCT_IDENTITY_MISMATCH")
    if Path(str(manifest.get("Output Folder") or "")).resolve() != folder.resolve():
        raise ContractError("603_OUTPUT_FOLDER_MISMATCH")
    required_fields = (
        "RUN_ID", "GeneratedAt", "Input Skill", "Input Run ID", "Input RUN_TIMESTAMP",
        "Input Folder", "Input File", "Input Record Count",
    )
    if any(manifest.get(field) in (None, "") for field in required_fields):
        raise ContractError("603_RUN_LINEAGE_MISSING")
    if manifest.get("Input Skill") != "hzp-amz-6-0-2-ai-precision-keyword-identification":
        raise ContractError("603_INPUT_SKILL_MISMATCH")
    if not _valid_timestamp(str(manifest.get("Input RUN_TIMESTAMP") or "")):
        raise ContractError("603_INPUT_TIMESTAMP_INVALID")
    input_folder = Path(str(manifest["Input Folder"]))
    input_file = Path(str(manifest["Input File"]))
    input_stamp = str(manifest["Input RUN_TIMESTAMP"])
    if input_file.parent.resolve() != input_folder.resolve() or not input_file.stem.endswith(f"_{input_stamp}"):
        raise ContractError("603_INPUT_RUN_PACKAGE_MISMATCH")
    expected_prefix = f"6-0-3_{product_code}_"
    declared_names = set(declared_values)
    if len(declared_names) != 2 or any(not name.startswith(expected_prefix) or not name.endswith(f"_{stamp}.csv") for name in declared_names):
        raise ContractError("603_RUN_FILENAME_TIMESTAMP_MISMATCH")
    run_csvs = {path.name for path in folder.glob(f"*_{stamp}.csv")} if folder.name != stamp else {path.name for path in folder.glob("*.csv")}
    if run_csvs != declared_names:
        raise ContractError("603_RUN_OUTPUT_PACKAGE_INCOMPLETE")
    if any(path.parent.resolve() != folder.resolve() or path.name not in declared_names or not path.is_file() for path in files.values()):
        raise ContractError("603_RUN_OUTPUT_PACKAGE_INCOMPLETE")
    counts = manifest.get("Output Record Counts") or {}
    try:
        declared_intents = int(counts["Intent Count"])
        declared_keywords = int(counts["Keyword Count"])
        declared_input_count = int(manifest["Input Record Count"])
    except (KeyError, TypeError, ValueError):
        raise ContractError("603_RUN_RECORD_COUNTS_MISSING") from None
    summary_headers, summary = _read_csv(files["summary"])
    mapping_headers, mapping = _read_csv(files["mapping"])
    _validate_headers(summary_headers, INPUT_603_SUMMARY_COLUMNS, "603 intent summary")
    if tuple(mapping_headers) not in (INPUT_603_MAPPING_COLUMNS, INPUT_603_SINGLE_MAPPING_COLUMNS):
        raise ContractError("603_RUN_MAPPING_SCHEMA_INVALID")
    if not summary or not mapping or len(summary) != declared_intents or len(mapping) != declared_keywords or len(mapping) != declared_input_count:
        raise ContractError("603_RUN_RECORD_COUNTS_MISMATCH")
    intents = [str(row.get("精准泛词") or "").strip() for row in summary]
    ids = [str(row.get("Id") or "").strip() for row in mapping]
    if any(not value for value in intents) or len(intents) != len(set(intents)):
        raise ContractError("603_RUN_INTENT_IDENTITY_INVALID")
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ContractError("603_RUN_KEYWORD_IDS_INVALID")
    intent_set = set(intents)
    direct_counts: dict[str, int] = {}
    for row in mapping:
        intent = str(row.get("精准泛词") or "").strip()
        if intent not in intent_set:
            raise ContractError("603_RUN_INTENT_COVERAGE_MISMATCH")
        direct_counts[intent] = direct_counts.get(intent, 0) + 1
    try:
        if any(int(row.get("直接对应词数") or "") != direct_counts.get(str(row.get("精准泛词") or "").strip(), 0) for row in summary):
            raise ContractError("603_RUN_DIRECT_COUNT_MISMATCH")
        _build_intent_tree(summary)
    except (ContractError, TypeError, ValueError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError("603_RUN_SUMMARY_INVALID", str(exc)) from exc


def _resolve_manifest_package(
    root: Path, skill_dir: str, product_code: str, skill_id: str, required_phrases: Mapping[str, str],
) -> dict[str, Any]:
    directory = root / "06_SKILL分析报告" / skill_dir
    if not directory.is_dir():
        raise ContractError("606_INPUT_NOT_FOUND", f"{directory}")
    manifests: list[tuple[str, Path, Path]] = []
    for manifest_path in directory.glob(f"{RUN_MANIFEST_PREFIX}*.json"):
        match = re.fullmatch(rf"{re.escape(RUN_MANIFEST_PREFIX)}(\d{{8}}_\d{{6}})\.json", manifest_path.name)
        if match:
            manifests.append((match.group(1), directory, manifest_path))
    for legacy in directory.iterdir():
        if legacy.is_dir() and _valid_timestamp(legacy.name):
            manifests.append((legacy.name, legacy, legacy / RUN_MANIFEST))
    manifests.sort(key=lambda item: item[0], reverse=True)
    candidates: list[tuple[str, Path, dict[str, Any], dict[str, Path]]] = []
    invalid: list[str] = []
    timestamp_mismatch = False
    for stamp, folder, manifest_path in manifests:
        manifest = _read_manifest(manifest_path)
        if not manifest:
            invalid.append(f"{stamp}:manifest")
            continue
        if str(manifest.get("SkillId") or "") != skill_id:
            continue
        if str(manifest.get("Run Status") or "").upper() != "VALID" or str(manifest.get("RUN_TIMESTAMP") or "") != stamp:
            invalid.append(f"{stamp}:status-or-timestamp")
            continue
        if str(manifest.get("Current Product") or "").strip() != product_code:
            continue
        declared_values = _manifest_output_values(manifest)
        roles = {}
        for role, phrase in required_phrases.items():
            matches = [
                Path(value).name for value in declared_values
                if Path(value).name == value and value.startswith(f"6-0-3_{product_code}_")
                and phrase in value and value.endswith(f"_{stamp}.csv")
            ]
            if len(matches) == 1:
                roles[role] = matches[0]
        if len(declared_values) != 2 or set(roles) != set(required_phrases):
            if len(declared_values) == 2 and all(
                any(phrase in value and value.startswith(f"6-0-3_{product_code}_") for value in declared_values)
                for phrase in required_phrases.values()
            ):
                timestamp_mismatch = True
                invalid.append(f"{stamp}:filename-timestamp-mismatch")
                continue
            invalid.append(f"{stamp}:declared-output-incomplete")
            continue
        files = {role: folder / name for role, name in roles.items()}
        run_csvs = {path.name for path in folder.glob(f"*_{stamp}.csv")} if folder == directory else {path.name for path in folder.glob("*.csv")}
        if run_csvs != set(roles.values()) or any(not path.is_file() for path in files.values()):
            invalid.append(f"{stamp}:output-file-missing-or-incomplete")
            continue
        try:
            _validate_603_manifest_package(folder, product_code, manifest, declared_values, files)
        except (ContractError, OSError, ValueError) as exc:
            invalid.append(f"{stamp}:{exc}")
            continue
        candidates.append((stamp, folder, manifest, files))
    if not candidates:
        reason = "no complete VALID upstream Run Package"
        if invalid:
            reason += "; rejected candidates: " + ", ".join(invalid[-5:])
        if timestamp_mismatch:
            raise ContractError("606_INPUT_RUN_MISMATCH", f"{skill_dir}: {reason}")
        raise ContractError("606_INPUT_NOT_FOUND", f"{skill_dir}: {reason}")
    stamp, folder, manifest, files = max(candidates, key=lambda row: row[0])
    return {
        "run_id": manifest.get("RUN_ID") or stamp,
        "run_timestamp": stamp,
        "folder": str(folder.resolve()),
        "files": {role: str(path.resolve()) for role, path in files.items()},
        "manifest": manifest,
    }


def resolve_latest_valid_602(product_root: str | Path, product_code: str) -> dict[str, Any]:
    skills_root = Path(__file__).resolve().parents[2]
    resolver_path = skills_root / "hzp-amz-6-0-3-precision-broad-extraction" / "scripts" / "broad_seed_cluster.py"
    if not resolver_path.is_file():
        raise ContractError("606_602_PACKAGE_RESOLVER_UNAVAILABLE")
    spec = importlib.util.spec_from_file_location("stage6_603_602_package_resolver_legacy", resolver_path)
    if spec is None or spec.loader is None:
        raise ContractError("606_602_PACKAGE_RESOLVER_UNAVAILABLE")
    resolver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(resolver)
    package = resolver.resolve_latest_valid_602_run_package(product_root, product_code)
    if package.get("status") != "LATEST_VALID_602_RUN_PACKAGE_READY":
        raise ContractError("606_INPUT_NOT_FOUND", "no complete valid 602 3+N package")
    return package


def resolve_latest_valid_603(product_root: str | Path, product_code: str) -> dict[str, Any]:
    return _resolve_manifest_package(
        Path(product_root), INPUT_603_ROOT, product_code,
        "hzp-amz-6-0-3-precision-broad-extraction",
        {"summary": "精准泛词汇总", "mapping": "词对应的精准泛词"},
    )


def _validate_headers(headers: list[str], expected: Iterable[str], label: str) -> None:
    if tuple(headers) != tuple(expected):
        raise ContractError("606_INPUT_SCHEMA_INVALID", f"{label} headers={headers!r}; expected={list(expected)!r}")


def _canonical_keyword(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _load_inputs(
    package_602: Mapping[str, Any], package_603: Mapping[str, Any],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    p_summary = Path(package_603["files"]["summary"])
    p_mapping = Path(package_603["files"]["mapping"])
    hs, summary = _read_csv(p_summary)
    hm, mapping = _read_csv(p_mapping)
    _validate_headers(hs, INPUT_603_SUMMARY_COLUMNS, "603 intent summary")
    _validate_headers(hm, INPUT_603_MAPPING_COLUMNS, "603 keyword mapping")
    if not summary or not mapping:
        raise ContractError("606_INPUT_EMPTY", "602 benchmark assets and both 603 files must contain records")
    for package, paths in ((package_602, [Path(path) for path in (package_602.get("files", {}).get("benchmarks") or {}).values()]),
                           (package_603, [p_summary, p_mapping])):
        stamp = str(package.get("run_timestamp") or "")
        if not _valid_timestamp(stamp) or any(not path.stem.endswith(f"_{stamp}") for path in paths):
            raise ContractError("606_INPUT_RUN_MISMATCH", f"package/file timestamp: {paths}")
    if p_summary.parent.resolve() != p_mapping.parent.resolve():
        raise ContractError("606_INPUT_RUN_MISMATCH", "603 summary and mapping are from different folders")
    if package_603.get("run_id") != package_603.get("run_timestamp"):
        # Existing Skills use timestamp as RUN_ID; an explicit opaque RUN_ID is also permitted
        # when both assets are in one manifested folder with the matching RUN_TIMESTAMP.
        declared_id = (package_603.get("manifest") or {}).get("RUN_ID")
        if declared_id != package_603.get("run_id"):
            raise ContractError("606_INPUT_RUN_MISMATCH", "603 RUN_ID does not match its manifest")
    identities_by_product_id = (package_602.get("manifest") or {}).get("Benchmark Identities") or {}
    if set(identities_by_product_id) != set((package_602.get("files", {}).get("benchmarks") or {})):
        raise ContractError("606_602_BENCHMARK_FILE_COUNT_MISMATCH")
    rows602: list[dict[str, str]] = []
    for product_id, filename in (package_602.get("files", {}).get("benchmarks") or {}).items():
        path = Path(filename)
        headers, rows = _read_csv(path)
        _validate_headers(headers, INPUT_602_COLUMNS, f"602 {product_id} high-precision file")
        identity = identities_by_product_id[product_id]
        code, asin = str(identity.get("对标编码") or "").strip(), str(identity.get("对标ASIN") or "").strip()
        seen: set[str] = set()
        for row in rows:
            canonical = " ".join(str(row.get("词") or "").casefold().split())
            if (not code or not asin or str(row.get("所属产品编号") or "").strip() != product_id
                    or str(row.get("对标ASIN") or "").strip() != asin
                    or row.get("精准度") != "高度精准" or not canonical or canonical in seen):
                raise ContractError("606_602_BENCHMARK_ASSET_INVALID", f"{path.name}")
            seen.add(canonical)
            rows602.append({
                "Id": row.get("Id", ""), "词": row.get("词", ""), "中文": row.get("中文", ""),
                "市场容量": row.get("市场容量", ""), "竞争产品数": row.get("竞争产品数", ""),
                "供需比": row.get("供需比", ""), "对标编码": code,
                "对标ASIN": row.get("对标ASIN", ""), "自然排名": row.get("自然排名", ""),
            })
    if not rows602:
        raise ContractError("606_INPUT_EMPTY", "602 has no high-precision benchmark observations")
    return rows602, summary, mapping


def _build_intent_tree(summary: list[dict[str, str]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    intents: dict[str, dict[str, Any]] = {}
    for source in summary:
        name = str(source["精准泛词"]).strip()
        if not name or name in intents:
            raise ContractError("606_INPUT_SCHEMA_INVALID", f"empty or duplicate Intent: {name!r}")
        parent = str(source.get("父精准泛词") or "").strip()
        volume = _decimal(source.get("汇总搜索量"), "INTENT_VOLUME_MISMATCH")
        if volume is None or volume < 0:
            raise ContractError("INTENT_VOLUME_MISMATCH", f"{name}: invalid 603 aggregate volume")
        direct = _decimal(source.get("直接搜索量"), "606_INPUT_SCHEMA_INVALID")
        if direct is None or direct < 0:
            raise ContractError("606_INPUT_SCHEMA_INVALID", f"{name}: invalid direct volume")
        intents[name] = {**source, "精准泛词": name, "父精准泛词": parent, "_volume": volume}
    for name, row in intents.items():
        parent = row["父精准泛词"]
        if parent and parent not in intents:
            raise ContractError("606_INPUT_SCHEMA_INVALID", f"{name}: orphan parent {parent}")
        if parent and row["_volume"] > intents[parent]["_volume"] + EPSILON:
            raise ContractError("INTENT_VOLUME_MISMATCH", f"{name}: child subtree volume exceeds parent {parent}")
    state: dict[str, int] = {}

    def visit(name: str) -> None:
        if state.get(name) == 1:
            raise ContractError("606_INPUT_SCHEMA_INVALID", f"Intent parent cycle at {name}")
        if state.get(name) == 2:
            return
        state[name] = 1
        parent = intents[name]["父精准泛词"]
        if parent:
            visit(parent)
        state[name] = 2

    for name in intents:
        visit(name)
    ancestors: dict[str, list[str]] = {}
    for name in intents:
        chain: list[str] = []
        cursor = name
        while cursor:
            chain.append(cursor)
            cursor = intents[cursor]["父精准泛词"]
        ancestors[name] = chain
    return intents, ancestors


def _validate_and_join(
    rows602: list[dict[str, str]], intents: Mapping[str, Mapping[str, Any]],
    ancestors: Mapping[str, list[str]], mapping: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    mappings: dict[str, dict[str, Any]] = {}
    for row in mapping:
        record_id = str(row["Id"]).strip()
        if not record_id or record_id in mappings:
            raise ContractError("606_INPUT_SCHEMA_INVALID", f"empty or duplicate 603 Id: {record_id!r}")
        intent = str(row["精准泛词"] or "").strip()
        if intent not in intents:
            raise ContractError("INTENT_MAPPING_MISSING", f"603 Id={record_id}, Intent={intent!r}")
        capacity = _decimal(row["市场容量"], "MISSING_MARKET_CAPACITY", blank_ok=True)
        if capacity is None or capacity < 0:
            raise ContractError("MISSING_MARKET_CAPACITY", f"603 Id={record_id}")
        mappings[record_id] = {**row, "_intent": intent, "_capacity": capacity}
    observations: list[dict[str, Any]] = []
    benchmarks: dict[str, str] = {}
    seen_ids: set[tuple[str, str]] = set()
    seen_terms: set[tuple[str, str]] = set()
    direct_capacity = {name: Decimal(0) for name in intents}
    subtree_capacity = {name: Decimal(0) for name in intents}
    for record in mappings.values():
        intent_name = record["_intent"]
        direct_capacity[intent_name] += record["_capacity"]
        for ancestor in ancestors[intent_name]:
            subtree_capacity[ancestor] += record["_capacity"]
    for name, intent in intents.items():
        direct = _decimal(intent.get("直接搜索量"), "INTENT_VOLUME_MISMATCH")
        if direct is None or direct_capacity[name] != direct or subtree_capacity[name] != intent["_volume"]:
            raise ContractError("INTENT_VOLUME_MISMATCH", f"603 direct/subtree capacity differs for {name}")
    null_rank_audit: list[dict[str, Any]] = []
    for row in rows602:
        code, asin, record_id = (str(row[key] or "").strip() for key in ("对标编码", "对标ASIN", "Id"))
        if not code or not asin:
            raise ContractError("BENCHMARK_IDENTITY_MISSING", f"Id={record_id}")
        if not record_id:
            raise ContractError("BENCHMARK_OBSERVATION_JOIN_FAILED", "602 high-precision Id is empty")
        if code in benchmarks and benchmarks[code] != asin:
            raise ContractError("BENCHMARK_IDENTITY_MISSING", f"{code}: conflicting ASINs")
        benchmarks[code] = asin
        if record_id not in mappings:
            continue
        pair = (code, record_id)
        canonical = _canonical_keyword(row["词"])
        if not canonical:
            raise ContractError("BENCHMARK_OBSERVATION_JOIN_FAILED", f"Id={record_id}: empty keyword")
        term = (code, canonical)
        if pair in seen_ids or term in seen_terms:
            raise ContractError("DUPLICATE_BENCHMARK_OBSERVATION", f"Benchmark={code}, Id={record_id}, keyword={row['词']!r}")
        seen_ids.add(pair)
        seen_terms.add(term)
        mapped = mappings[record_id]
        if _canonical_keyword(row["词"]) != _canonical_keyword(mapped["词"]):
            raise ContractError("BENCHMARK_OBSERVATION_JOIN_FAILED", f"Id={record_id}: keyword differs between 602 and 603")
        capacity = _decimal(row["市场容量"], "MISSING_MARKET_CAPACITY", blank_ok=True)
        if capacity is None or capacity < 0:
            raise ContractError("MISSING_MARKET_CAPACITY", f"602 Id={record_id}, Benchmark={code}")
        if abs(capacity - mapped["_capacity"]) > EPSILON:
            raise ContractError("INTENT_VOLUME_MISMATCH", f"602/603 capacity differs for Id={record_id}")
        rank_text = str(row.get("自然排名") or "").strip()
        rank: Decimal | None = None
        if not rank_text:
            null_rank_audit.append({"Id": record_id, "词": row["词"], "对标编码": code, "问题": "MISSING_ORGANIC_RANK"})
        else:
            rank = _decimal(rank_text, "INVALID_ORGANIC_RANK")
            if rank is None or rank <= 0:
                raise ContractError("INVALID_ORGANIC_RANK", f"Id={record_id}, Benchmark={code}, value={rank_text!r}")
        observations.append({
            **row, "_code": code, "_asin": asin, "_id": record_id, "_keyword": row["词"],
            "_intent": mapped["_intent"], "_capacity": capacity, "_rank": rank,
        })
    if not observations:
        raise ContractError("606_INPUT_EMPTY", "602 has no high-precision benchmark observations")
    observed_ids = {row["_id"] for row in observations}
    missing_ids = sorted(set(mappings) - observed_ids)
    if missing_ids:
        raise ContractError("BENCHMARK_OBSERVATION_JOIN_FAILED", f"603 Ids absent from 602 high-precision assets: {missing_ids[:10]}")
    no_observation_audit = [
        {"Id": record_id, "词": mapped["词"], "精准泛词": mapped["_intent"], "对标编码": code,
         "对标ASIN": asin, "问题": "NO_602_HIGH_PRECISION_OBSERVATION"}
        for code, asin in sorted(benchmarks.items())
        for record_id, mapped in mappings.items()
        if (code, record_id) not in seen_ids
    ]
    return observations, null_rank_audit, benchmarks, no_observation_audit


def calculate_individual_occupancy(
    observations: list[dict[str, Any]],
    intents: Mapping[str, Mapping[str, Any]],
    ancestors: Mapping[str, list[str]],
    benchmark_identities: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Calculate every Benchmark x Intent row, including zero-observation cells."""
    identities = dict(benchmark_identities or {row["_code"]: row["_asin"] for row in observations})
    benchmarks = sorted(identities)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for observation in observations:
        for intent_name in ancestors[observation["_intent"]]:
            grouped.setdefault((observation["_code"], intent_name), []).append(observation)

    detail: list[dict[str, Any]] = []
    for code in benchmarks:
        asin = identities[code]
        for intent_name, intent in intents.items():
            matches = grouped.get((code, intent_name), [])
            ranked = [row for row in matches if row["_rank"] is not None]
            volume = intent["_volume"]
            top: dict[int, tuple[int, Decimal]] = {}
            for threshold in THRESHOLDS:
                selected = [row for row in matches if row["_rank"] is not None and row["_rank"] <= threshold]
                top[threshold] = (len(selected), sum((row["_capacity"] for row in selected), Decimal(0)))

            capacities = [row["_capacity"] for row in ranked]
            rank_values = [row["_rank"] for row in ranked]
            average_rank = sum(rank_values, Decimal(0)) / len(rank_values) if rank_values else None
            weight_total = sum(capacities, Decimal(0))
            weighted_rank = (
                sum((row["_rank"] * row["_capacity"] for row in ranked), Decimal(0)) / weight_total
                if ranked and weight_total > 0 else None
            )
            rates: dict[int, Decimal | None] = {}
            previous_volume = Decimal(0)
            previous_rate = Decimal(0)
            for threshold in THRESHOLDS:
                count, occupied = top[threshold]
                if occupied + EPSILON < previous_volume:
                    raise ContractError("OCCUPANCY_MONOTONICITY_FAILED", f"{code}/{intent_name}/Top{threshold} volume")
                if occupied > volume + EPSILON:
                    raise ContractError("INTENT_VOLUME_MISMATCH", f"{code}/{intent_name}/Top{threshold}: {occupied}>{volume}")
                rate = occupied / volume if volume > 0 else None
                if rate is not None and (rate + EPSILON < previous_rate or rate > Decimal(1) + EPSILON):
                    raise ContractError("OCCUPANCY_MONOTONICITY_FAILED", f"{code}/{intent_name}/Top{threshold} rate")
                rates[threshold] = rate
                previous_volume, previous_rate = occupied, rate or Decimal(0)
            source = {
                "对标编码": code,
                "对标ASIN": asin,
                "精准泛词": intent_name,
                "中文": intent.get("中文") or "",
                "层级": intent.get("层级") or "",
                "父精准泛词": intent.get("父精准泛词") or "",
                "汇总搜索量": _number_text(volume),
                "有效排名词数": str(len(ranked)),
                "平均自然排名": _number_text(average_rank, 4),
                "加权自然排名": _number_text(weighted_rank, 4),
            }
            for threshold in THRESHOLDS:
                count, occupied = top[threshold]
                source[f"Top{threshold}关键词数"] = str(count)
                source[f"Top{threshold}占领搜索量"] = _number_text(occupied)
                source[f"Top{threshold}搜索量覆盖率"] = _rate_text(rates[threshold])
            detail.append(source)
    return detail


def _median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    values.sort()
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / Decimal(2)


def calculate_consensus(
    detail: list[dict[str, Any]], *, benchmark_count: int, judgments: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Rebuild every consensus numeric field from OUTPUT A rows."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in detail:
        grouped.setdefault(str(row["精准泛词"]), []).append(row)
    output: list[dict[str, Any]] = []
    for intent, rows in grouped.items():
        rows.sort(key=lambda row: str(row["对标编码"]))
        first = rows[0]
        effective_rows = [
            row for row in rows
            if int(row.get("有效排名词数") or 0) > 0
        ]
        core_count = sum(1 for row in rows if row.get("占领等级") == "核心占领")
        strong_count = sum(1 for row in rows if row.get("占领等级") == "强占领")
        core_strong_count = core_count + strong_count
        candidates = rows

        def best_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
            top20 = _parse_rate(row.get("Top20搜索量覆盖率"))
            top10 = _parse_rate(row.get("Top10搜索量覆盖率"))
            weighted = _decimal(row.get("加权自然排名"), "CONSENSUS_SOURCE_MISMATCH", blank_ok=True)
            return (
                -(top20 if top20 is not None else Decimal("-1")),
                -(top10 if top10 is not None else Decimal("-1")),
                weighted if weighted is not None else Decimal("Infinity"),
                str(row.get("对标编码") or ""),
            )

        best = min(candidates, key=best_key) if candidates else None
        top20_values = [value for row in rows if (value := _parse_rate(row.get("Top20搜索量覆盖率"))) is not None]
        top50_values = [value for row in rows if (value := _parse_rate(row.get("Top50搜索量覆盖率"))) is not None]
        judgment = (judgments or {}).get(intent, {})
        if benchmark_count == 1:
            grade = "单对标模式"
        else:
            grade = str(judgment.get("grade") or "")
            if grade not in {"高共识", "中共识", "低共识", "单点验证"}:
                raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"{intent}: invalid consensus grade {grade!r}")
        reason = str(judgment.get("reason") or "").strip()
        if not reason:
            raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"{intent}: missing AI consensus reason")
        if benchmark_count == 1:
            reason = f"当前仅有1个Benchmark，按单对标模式解释。{reason}"
        output.append({
            "精准泛词": intent,
            "中文": first.get("中文", ""),
            "层级": first.get("层级", ""),
            "父精准泛词": first.get("父精准泛词", ""),
            "汇总搜索量": first.get("汇总搜索量", ""),
            "对标总数": str(benchmark_count),
            "有效覆盖对标数": str(len(effective_rows)),
            "核心占领对标数": str(core_count),
            "强占领对标数": str(strong_count),
            "核心/强占领对标数": str(core_strong_count),
            "最佳对标编码": str(best.get("对标编码") if best else DATA_NOT_AVAILABLE),
            "最佳对标ASIN": str(best.get("对标ASIN") if best else DATA_NOT_AVAILABLE),
            "最佳Top20搜索量覆盖率": str(best.get("Top20搜索量覆盖率") if best else DATA_NOT_AVAILABLE),
            "Top20覆盖率中位数": _rate_text(_median(top20_values)),
            "Top50覆盖率中位数": _rate_text(_median(top50_values)),
            "多对标共识等级": grade,
            "共识判断原因": reason,
        })
    return output


def validate_consensus_rebuild(detail: list[dict[str, Any]], consensus: list[dict[str, Any]], benchmark_count: int) -> None:
    """Check OUTPUT B math against the saved OUTPUT A snapshot."""
    by_intent = {row["精准泛词"]: row for row in consensus}
    for intent in _group_detail(detail):
        if intent not in by_intent:
            raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"missing intent {intent}")
    judgments = {
        intent: {"grade": row.get("多对标共识等级", ""), "reason": row.get("共识判断原因", "")}
        for intent, row in by_intent.items()
    }
    rebuilt = {
        row["精准泛词"]: row
        for row in calculate_consensus(detail, benchmark_count=benchmark_count, judgments=judgments)
    }
    math_columns = tuple(column for column in CONSENSUS_COLUMNS if column not in {"多对标共识等级", "共识判断原因"})
    if set(rebuilt) != set(by_intent):
        raise ContractError("CONSENSUS_SOURCE_MISMATCH", "OUTPUT B Intent coverage differs from OUTPUT A")
    for intent, actual in by_intent.items():
        expected = rebuilt[intent]
        if any(str(actual.get(column, "")) != str(expected.get(column, "")) for column in math_columns):
            raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"{intent}: OUTPUT B math differs from OUTPUT A rebuild")
        if actual.get("多对标共识等级") not in CONSENSUS_LEVELS:
            raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"{intent}: invalid grade")


def _group_detail(detail: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in detail:
        grouped.setdefault(str(row["精准泛词"]), []).append(row)
    return grouped


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _write_csv_atomic(path: Path, rows: list[Mapping[str, Any]], columns: tuple[str, ...]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def _read_output_csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    headers, rows = _read_csv(path)
    if tuple(headers) != columns:
        raise ContractError("606_RUN_PACKAGE_INCOMPLETE", f"output schema mismatch: {path.name}")
    return rows


def _write_manifest(folder: Path, manifest: Mapping[str, Any]) -> None:
    stamp = str(manifest.get("RUN_TIMESTAMP") or "")
    if not _valid_timestamp(stamp):
        raise ContractError("606_TIMESTAMP_MISMATCH", f"invalid RUN_TIMESTAMP {stamp}")
    _write_json_atomic(folder / f"{RUN_MANIFEST_PREFIX}{stamp}.json", manifest)


def _create_run_folder(product_root: Path, timestamp: str) -> Path:
    if not _valid_timestamp(timestamp):
        raise ContractError("606_TIMESTAMP_MISMATCH", f"invalid RUN_TIMESTAMP {timestamp}")
    root = product_root / "06_SKILL分析报告" / REPORT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / f"{RUN_MANIFEST_PREFIX}{timestamp}.json"
    evidence = root / f"working_evidence_{timestamp}.json"
    outputs = [root / f"{name}_{timestamp}.{extension}" for name, extension in (
        ("对标意图市场占领明细", "csv"), ("意图多对标占领共识", "csv"), ("对标意图市场占领分析报告", "html"),
    )]
    if any(path.exists() for path in [manifest, evidence, *outputs]):
        raise FileExistsError("606_RUN_ALREADY_EXISTS")
    return root


def prepare_run(product_root: str | Path, product_code: str, run_timestamp: str | None = None) -> dict[str, Any]:
    """Resolve upstream packages and persist deterministic evidence for AI review."""
    root = Path(product_root).resolve()
    started_at = datetime.now().astimezone()
    timestamp = run_timestamp or started_at.strftime("%Y%m%d_%H%M%S")
    folder = _create_run_folder(root, timestamp)
    manifest: dict[str, Any] = {
        "SkillId": SKILL_ID, "Current Product": product_code, "RUN_ID": timestamp,
        "RUN_TIMESTAMP": timestamp, "GeneratedAt": started_at.isoformat(timespec="seconds"),
        "Input Source": "LATEST VALID 602 + 603 RUN PACKAGES",
        "602 Input Run ID": None, "602 Input Timestamp": None, "602 Input Folder": None, "602 Input Files": [],
        "603 Input Run ID": None, "603 Input Timestamp": None, "603 Input Folder": None, "603 Input Files": [],
        "Benchmark Count": None, "Benchmark Codes": [], "Benchmark ASINs": [],
        "Input Keyword Count": None, "Input Intent Count": None,
        "Output Folder": str(folder), "Output Files": [], "Output Record Counts": {},
        "Run Status": "RUNNING",
    }
    _write_manifest(folder, manifest)
    try:
        package602 = resolve_latest_valid_602(root, product_code)
        package603 = resolve_latest_valid_603(root, product_code)
        rows602, summary, mapping = _load_inputs(package602, package603)
        intents, ancestors = _build_intent_tree(summary)
        observations, null_rank_audit, benchmark_identities, no_observation_audit = _validate_and_join(rows602, intents, ancestors, mapping)
        detail = calculate_individual_occupancy(observations, intents, ancestors, benchmark_identities)
        benchmarks = sorted(benchmark_identities)
        manifest.update({
            "602 Input Run ID": package602["run_id"], "602 Input Timestamp": package602["run_timestamp"],
            "602 Input Folder": package602["run_folder"], "602 Input Files": list(package602["files"]["benchmarks"].values()),
            "603 Input Run ID": package603["run_id"], "603 Input Timestamp": package603["run_timestamp"],
            "603 Input Folder": package603["folder"], "603 Input Files": list(package603["files"].values()),
            "Benchmark Count": len(benchmarks), "Benchmark Codes": benchmarks,
            "Benchmark ASINs": [benchmark_identities[code] for code in benchmarks],
            "Input Keyword Count": len(mapping), "Input Intent Count": len(intents),
            "Output Record Counts": {"对标意图市场占领明细": len(detail), "意图多对标占领共识": len(intents)},
            "Validation": {
                "Missing Organic Rank Count": len(null_rank_audit),
                "Missing Organic Rank Audit": null_rank_audit,
                "No 602 High-Precision Observation Count": len(no_observation_audit),
                "No 602 High-Precision Observation Audit": no_observation_audit,
                "Input Package Status": "LATEST_VALID_602_AND_603",
            },
        })
        evidence = {
            "SkillId": SKILL_ID, "Product Code": product_code, "RUN_ID": timestamp, "RUN_TIMESTAMP": timestamp,
            "Output Folder": str(folder), "602 Package": package602, "603 Package": package603,
            "Benchmark Count": len(benchmarks), "Benchmark Codes": benchmarks,
            "Input Keyword Count": len(mapping), "Input Intent Count": len(intents),
            "Null Organic Rank Audit": null_rank_audit, "No 602 High-Precision Observation Audit": no_observation_audit,
            "Detail Evidence": detail,
            "Intent Rows": [
                {key: row[key] for key in ("精准泛词", "中文", "层级", "父精准泛词", "汇总搜索量")}
                for row in summary
            ],
        }
        _write_json_atomic(folder / f"working_evidence_{timestamp}.json", evidence)
        _write_manifest(folder, manifest)
        return {
            "status": "606_AI_REVIEW_REQUIRED", "run_id": timestamp, "run_timestamp": timestamp,
            "run_folder": str(folder), "benchmark_count": len(benchmarks),
            "keyword_count": len(mapping), "intent_count": len(intents),
            "missing_rank_count": len(null_rank_audit), "detail_evidence": detail,
            "no_observation_count": len(no_observation_audit),
            "no_observation_audit": no_observation_audit,
            "intent_rows": evidence["Intent Rows"],
        }
    except Exception as exc:
        manifest["Run Status"] = "FAILED"
        manifest["Failure"] = {"status": getattr(exc, "code", type(exc).__name__), "message": str(exc)}
        _write_manifest(folder, manifest)
        raise


def finalize_run(
    product_root: str | Path, product_code: str, run_timestamp: str, judgments_path: str | Path,
) -> dict[str, Any]:
    """Attach AI-only qualitative judgments, write and verify the complete package."""
    root = Path(product_root).resolve()
    folder = root / "06_SKILL分析报告" / REPORT_ROOT
    manifest_path = folder / f"{RUN_MANIFEST_PREFIX}{run_timestamp}.json"
    manifest = _read_manifest(manifest_path)
    if not _valid_timestamp(run_timestamp) or not folder.is_dir() or not manifest:
        raise ContractError("606_RUN_PACKAGE_INCOMPLETE", f"run not found: {folder}")
    if manifest.get("Run Status") != "RUNNING" or manifest.get("RUN_TIMESTAMP") != run_timestamp:
        raise ContractError("606_RUN_PACKAGE_INCOMPLETE", "run is not awaiting AI judgments")
    if str(manifest.get("Current Product") or "") != product_code:
        raise ContractError("606_RUN_PACKAGE_INCOMPLETE", "product identity mismatch")
    try:
        evidence_path = folder / f"working_evidence_{run_timestamp}.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        judgments = json.loads(Path(judgments_path).read_text(encoding="utf-8-sig"))
        individual = judgments.get("individual")
        consensus_judgments = judgments.get("consensus")
        if not isinstance(individual, list) or not isinstance(consensus_judgments, list):
            raise ContractError("606_RUN_PACKAGE_INCOMPLETE", "judgment JSON requires individual[] and consensus[]")
        expected_pairs = {(row["对标编码"], row["精准泛词"]) for row in evidence["Detail Evidence"]}
        indexed: dict[tuple[str, str], dict[str, Any]] = {}
        for entry in individual:
            pair = (str(entry.get("benchmark_code") or ""), str(entry.get("intent") or ""))
            if pair in indexed or pair not in expected_pairs:
                raise ContractError("606_RUN_PACKAGE_INCOMPLETE", f"unknown or duplicate individual judgment: {pair}")
            if entry.get("grade") not in OCCUPANCY_LEVELS or not str(entry.get("reason") or "").strip():
                raise ContractError("606_RUN_PACKAGE_INCOMPLETE", f"invalid occupancy judgment: {pair}")
            indexed[pair] = entry
        if set(indexed) != expected_pairs:
            missing = sorted(expected_pairs - set(indexed))
            raise ContractError("606_RUN_PACKAGE_INCOMPLETE", f"missing individual judgments: {missing[:5]}")
        detail: list[dict[str, Any]] = []
        for base in evidence["Detail Evidence"]:
            row = dict(base)
            judgment = indexed[(row["对标编码"], row["精准泛词"])]
            row["占领等级"] = judgment["grade"]
            row["占领判断原因"] = str(judgment["reason"]).strip()
            detail.append(row)
        actual_pairs = {(row["对标编码"], row["精准泛词"]) for row in detail}
        if len(detail) != len(expected_pairs) or actual_pairs != expected_pairs:
            raise ContractError("606_RUN_PACKAGE_INCOMPLETE", "OUTPUT A is not a complete Benchmark x Intent matrix")
        intents_seen = {row["精准泛词"] for row in detail}
        consensus_index: dict[str, dict[str, Any]] = {}
        for entry in consensus_judgments:
            intent = str(entry.get("intent") or "")
            if intent in consensus_index or intent not in intents_seen:
                raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"unknown or duplicate consensus judgment: {intent}")
            if not str(entry.get("reason") or "").strip():
                raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"{intent}: missing reason")
            if evidence["Benchmark Count"] > 1 and entry.get("grade") not in {"高共识", "中共识", "低共识", "单点验证"}:
                raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"{intent}: invalid consensus grade")
            consensus_index[intent] = entry
        if set(consensus_index) != intents_seen:
            raise ContractError("CONSENSUS_SOURCE_MISMATCH", f"missing consensus judgments: {sorted(intents_seen - set(consensus_index))[:5]}")
        consensus = calculate_consensus(
            detail, benchmark_count=int(evidence["Benchmark Count"]), judgments=consensus_index,
        )
        validate_consensus_rebuild(detail, consensus, int(evidence["Benchmark Count"]))
        detail_path = folder / f"对标意图市场占领明细_{run_timestamp}.csv"
        consensus_path = folder / f"意图多对标占领共识_{run_timestamp}.csv"
        html_path = folder / f"对标意图市场占领分析报告_{run_timestamp}.html"
        _write_csv_atomic(detail_path, detail, DETAIL_COLUMNS)
        _write_csv_atomic(consensus_path, consensus, CONSENSUS_COLUMNS)
        readback_detail = _read_output_csv(detail_path, DETAIL_COLUMNS)
        readback_consensus = _read_output_csv(consensus_path, CONSENSUS_COLUMNS)
        validate_consensus_rebuild(readback_detail, readback_consensus, int(evidence["Benchmark Count"]))
        from report_renderer import read_embedded_snapshot, render_report
        render_report(readback_detail, readback_consensus, html_path, run_timestamp, evidence)
        if not html_path.is_file():
            raise ContractError("606_RUN_PACKAGE_INCOMPLETE", "HTML renderer did not create report")
        html_text = html_path.read_text(encoding="utf-8")
        for required in ("Executive Summary", "Benchmark Overview", "Search Intent Occupancy Matrix", "Sources and Boundaries"):
            if required not in html_text:
                raise ContractError("606_RUN_PACKAGE_INCOMPLETE", f"HTML section missing: {required}")
        snapshot = read_embedded_snapshot(html_text)
        if snapshot.get("run_timestamp") != run_timestamp or snapshot.get("detail") != readback_detail or snapshot.get("consensus") != readback_consensus:
            raise ContractError("HTML_DATA_RECONCILIATION_FAILED", "HTML embedded snapshot differs from same-run CSV readback")
        output_files = [detail_path.name, consensus_path.name, html_path.name]
        if any(not Path(name).stem.endswith(f"_{run_timestamp}") for name in output_files):
            raise ContractError("606_TIMESTAMP_MISMATCH", "output filename timestamp mismatch")
        manifest["Output Files"] = output_files
        manifest["Output Record Counts"] = {
            "对标意图市场占领明细": len(readback_detail), "意图多对标占领共识": len(readback_consensus),
        }
        manifest["Validation"] = {
            **(manifest.get("Validation") or {}),
            "CSV Schema": "PASS", "Consensus Rebuild": "PASS",
            "HTML Data Source": "same-run OUTPUT A and OUTPUT B readback",
            "HTML Self Contained": "PASS",
        }
        manifest["Run Status"] = "VALID"
        _write_manifest(folder, manifest)
        evidence_path.unlink(missing_ok=True)
        package = validate_606_package(folder, product_code, run_timestamp, manifest_path)
        if not package.get("valid"):
            raise ContractError("606_RUN_PACKAGE_INCOMPLETE", str(package.get("reason")))
        return {
            "status": "FULL_SUCCESS", "run_id": run_timestamp, "run_timestamp": run_timestamp,
            "run_folder": str(folder), "files": output_files,
            "detail_rows": len(readback_detail), "consensus_rows": len(readback_consensus),
        }
    except Exception as exc:
        manifest["Run Status"] = "FAILED"
        manifest["Failure"] = {"status": getattr(exc, "code", type(exc).__name__), "message": str(exc)}
        try:
            _write_manifest(folder, manifest)
        except OSError:
            pass
        raise


def validate_606_package(
    folder: Path, product_code: str, run_timestamp: str | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    legacy_folder = _valid_timestamp(folder.name)
    timestamp = run_timestamp or (folder.name if legacy_folder else "")
    target_manifest = manifest_path or folder / (RUN_MANIFEST if legacy_folder else f"{RUN_MANIFEST_PREFIX}{timestamp}.json")
    manifest = _read_manifest(target_manifest)
    if not _valid_timestamp(timestamp) or not manifest:
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    if manifest.get("SkillId") != SKILL_ID or manifest.get("Run Status") != "VALID":
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    if manifest.get("Current Product") != product_code or manifest.get("RUN_TIMESTAMP") != timestamp:
        return {"valid": False, "reason": "606_TIMESTAMP_MISMATCH"}
    if not manifest.get("RUN_ID") or not manifest.get("GeneratedAt"):
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    if Path(str(manifest.get("Output Folder") or "")).resolve() != folder.resolve():
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    expected = {
        "detail": folder / f"对标意图市场占领明细_{timestamp}.csv",
        "consensus": folder / f"意图多对标占领共识_{timestamp}.csv",
        "html": folder / f"对标意图市场占领分析报告_{timestamp}.html",
    }
    declared = _manifest_output_values(manifest)
    run_csvs = (
        {path.name for path in folder.glob(f"*_{timestamp}.csv")}
        if not legacy_folder else {path.name for path in folder.glob("*.csv")}
    )
    run_html = (
        {path.name for path in folder.glob(f"*_{timestamp}.html")}
        if not legacy_folder else {path.name for path in folder.glob("*.html")}
    )
    if (
        len(declared) != 3
        or any(Path(value).name != value for value in declared)
        or set(declared) != {path.name for path in expected.values()}
        or run_csvs != {expected["detail"].name, expected["consensus"].name}
        or run_html != {expected["html"].name}
    ):
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    if any(not path.is_file() for path in expected.values()):
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    try:
        detail_rows = _read_output_csv(expected["detail"], DETAIL_COLUMNS)
        consensus_rows = _read_output_csv(expected["consensus"], CONSENSUS_COLUMNS)
        html = expected["html"].read_text(encoding="utf-8")
        from report_renderer import read_embedded_snapshot
        snapshot = read_embedded_snapshot(html)
    except (ContractError, OSError, UnicodeError, ValueError) as exc:
        return {"valid": False, "reason": str(exc)}
    counts = manifest.get("Output Record Counts") or {}
    if counts.get("对标意图市场占领明细") != len(detail_rows) or counts.get("意图多对标占领共识") != len(consensus_rows):
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    benchmark_codes = manifest.get("Benchmark Codes") or []
    detail_pairs = {(row["对标编码"], row["精准泛词"]) for row in detail_rows}
    expected_pairs = {
        (str(code), str(intent))
        for code in benchmark_codes for intent in {row["精准泛词"] for row in detail_rows}
    }
    try:
        benchmark_count = int(manifest.get("Benchmark Count"))
    except (TypeError, ValueError):
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    if (
        len(detail_pairs) != len(detail_rows)
        or detail_pairs != expected_pairs
        or len(consensus_rows) != len({row["精准泛词"] for row in detail_rows})
        or benchmark_count != len(benchmark_codes)
    ):
        return {"valid": False, "reason": "606_RUN_PACKAGE_INCOMPLETE"}
    if (
        "Organic Search Occupancy" not in html or "fetch(" in html
        or timestamp not in html
        or snapshot.get("run_timestamp") != timestamp
        or snapshot.get("detail") != detail_rows
        or snapshot.get("consensus") != consensus_rows
    ):
        return {"valid": False, "reason": "HTML_DATA_RECONCILIATION_FAILED"}
    return {
        "valid": True, "run_id": manifest.get("RUN_ID"), "run_timestamp": timestamp,
        "run_folder": str(folder.resolve()), "manifest_file": str(target_manifest.resolve()), "manifest": manifest,
        "detail_file": str(expected["detail"].resolve()),
        "consensus_file": str(expected["consensus"].resolve()),
        "html_file": str(expected["html"].resolve()),
    }


def resolve_latest_valid_606(product_root: str | Path, product_code: str) -> dict[str, Any]:
    root = Path(product_root) / "06_SKILL分析报告" / REPORT_ROOT
    if not root.is_dir():
        return {"status": "606_EVIDENCE_NOT_AVAILABLE", "invalid_runs": []}
    invalid: list[dict[str, str]] = []
    candidates: list[tuple[str, Path, Path]] = []
    for manifest in root.glob(f"{RUN_MANIFEST_PREFIX}*.json"):
        match = re.fullmatch(rf"{re.escape(RUN_MANIFEST_PREFIX)}(\d{{8}}_\d{{6}})\.json", manifest.name)
        if match:
            candidates.append((match.group(1), root, manifest))
    for legacy in root.iterdir():
        if legacy.is_dir() and _valid_timestamp(legacy.name):
            candidates.append((legacy.name, legacy, legacy / RUN_MANIFEST))
    candidates.sort(key=lambda item: item[0], reverse=True)
    for timestamp, folder, manifest_path in candidates:
        package = validate_606_package(folder, product_code, timestamp, manifest_path)
        if package.get("valid"):
            return {"status": "LATEST_VALID_606_RUN_PACKAGE_READY", **package, "invalid_runs": invalid}
        invalid.append({"run_folder": str(folder), "reason": str(package.get("reason"))})
    return {"status": "606_EVIDENCE_NOT_AVAILABLE", "invalid_runs": invalid}


def main() -> int:
    parser = argparse.ArgumentParser(description="6-0-6 Benchmark Intent Market Occupancy Analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="resolve latest valid 602/603 packages and calculate occupancy evidence")
    prepare.add_argument("--product-root", required=True)
    prepare.add_argument("--product-code", required=True)
    prepare.add_argument("--run-timestamp")
    finalize = sub.add_parser("finalize", help="write final Run Package using the AI judgment JSON")
    finalize.add_argument("--product-root", required=True)
    finalize.add_argument("--product-code", required=True)
    finalize.add_argument("--run-timestamp", required=True)
    finalize.add_argument("--judgments-json", required=True)
    resolve = sub.add_parser("resolve-latest-606", help="return the latest complete valid 606 package")
    resolve.add_argument("--product-root", required=True)
    resolve.add_argument("--product-code", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_run(args.product_root, args.product_code, args.run_timestamp)
        elif args.command == "finalize":
            result = finalize_run(args.product_root, args.product_code, args.run_timestamp, args.judgments_json)
        else:
            result = resolve_latest_valid_606(args.product_root, args.product_code)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result.get("status") not in {"606_EVIDENCE_NOT_AVAILABLE"} else 1
    except ContractError as exc:
        print(json.dumps({"status": "FAILED", "error_code": exc.code, "detail": exc.detail}, ensure_ascii=False, indent=2))
        return 2
    except FileExistsError:
        print(json.dumps({
            "status": "FAILED", "error_code": "606_TIMESTAMP_MISMATCH",
            "detail": "RUN_TIMESTAMP already exists; retry with a new timestamp.",
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
