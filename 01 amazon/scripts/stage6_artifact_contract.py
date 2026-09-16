"""Shared Stage 6 run metadata, timestamped output, and latest-valid resolver.

Business-specific readers still provide the exact directory and candidate
paths.  This module owns the common identity, schema, status, timestamp,
fallback, and same-run rules so each Skill does not create its own resolver.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

RUN_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
RUN_TIMESTAMP_RE = re.compile(r"(?<!\d)(\d{8}_\d{6})(?!\d)")
DEFAULT_SUCCESS_STATUSES = {"FULL_SUCCESS", "SUCCESS", "COMPLETE"}


@dataclass(frozen=True)
class RunContext:
    skill_number: str
    skill_id: str
    product_code: str
    run_timestamp: str
    run_id: str
    generated_at: str
    timezone_name: str


def new_run_context(
    skill_number: str,
    skill_id: str,
    product_code: str,
    *,
    now: datetime | None = None,
) -> RunContext:
    """Create one timezone-aware context for every output in a Skill run."""
    instant = now or datetime.now().astimezone()
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("RUN_TIMESTAMP_REQUIRES_TIMEZONE_AWARE_DATETIME")
    local = instant.astimezone()
    stamp = local.strftime(RUN_TIMESTAMP_FORMAT)
    return RunContext(
        skill_number=skill_number,
        skill_id=skill_id,
        product_code=product_code,
        run_timestamp=stamp,
        run_id=f"{skill_number}_{product_code}_{stamp}",
        generated_at=local.isoformat(timespec="seconds"),
        timezone_name=str(local.tzinfo),
    )


def timestamped_output_path(
    directory: str | Path,
    skill_number: str,
    product_code: str,
    report_name: str,
    extension: str,
    run_timestamp: str,
) -> Path:
    """Build the shared `<skill>_<product>_<report>_<stamp>.<ext>` filename."""
    if not re.fullmatch(r"\d{8}_\d{6}", run_timestamp):
        raise ValueError(f"INVALID_RUN_TIMESTAMP:{run_timestamp}")
    ext = extension.lstrip(".")
    if not ext or not re.fullmatch(r"[A-Za-z0-9]+", ext):
        raise ValueError(f"INVALID_OUTPUT_EXTENSION:{extension}")
    name = f"{skill_number}_{product_code}_{report_name}_{run_timestamp}.{ext}"
    return Path(directory) / name


def assert_new_outputs(paths: Iterable[str | Path]) -> None:
    """Fail before writing if any proposed timestamped output already exists."""
    existing = [str(Path(path)) for path in paths if Path(path).exists()]
    if existing:
        raise FileExistsError("OUTPUT_WOULD_OVERWRITE: " + ", ".join(existing))


def metadata_sidecar_path(path: str | Path) -> Path:
    return Path(str(Path(path)) + ".meta.json")


def write_metadata_sidecar(path: str | Path, metadata: Mapping[str, Any]) -> Path:
    """Create, never overwrite, a JSON sidecar next to one formal artifact."""
    target = metadata_sidecar_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(metadata), ensure_ascii=False, indent=2) + "\n"
    with target.open("x", encoding="utf-8", newline="") as handle:
        handle.write(payload)
    return target


def make_artifact_metadata(
    context: RunContext,
    report_identity: str,
    *,
    run_status: str,
    schema: Sequence[str] | None = None,
    record_count: int | None = None,
    inputs: Sequence[Mapping[str, Any]] = (),
    output_assets: Sequence[str] = (),
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the common lineage manifest without adding columns to business CSVs."""
    result: dict[str, Any] = {
        "Skill_Number": context.skill_number,
        "Skill_ID": context.skill_id,
        "Product_Code": context.product_code,
        "Report_Identity": report_identity,
        "RUN_ID": context.run_id,
        "RUN_TIMESTAMP": context.run_timestamp,
        "Generated_At": context.generated_at,
        "Timezone": context.timezone_name,
        "Run_Status": run_status,
        "Schema": list(schema) if schema is not None else None,
        "Record_Count": record_count,
        "Inputs": [dict(item) for item in inputs],
        "Output_Assets": list(output_assets),
    }
    if extra:
        result.update(extra)
    return result


def validate_601_run_package(candidate_path: str | Path, metadata: Mapping[str, Any] | None) -> str | None:
    """Validate the fixed 6-0-1 assets and per-ASIN observation package."""
    from collections import Counter

    detail_schema = ["Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标编号", "对标ASIN", "自然排名"]
    expected = {
        "BENCHMARK_KEYWORD_DETAIL": detail_schema,
        "BENCHMARK_KEYWORD_POOL": ["Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数"],
        "BENCHMARK_KEYWORD_ALL_OBSERVATIONS": [column for column in detail_schema if column != "对标编码"] + ["ASIN", "产品编号"],
    }
    if not metadata or metadata.get("Run_Status") != "FULL_SUCCESS":
        return "601_PACKAGE_METADATA_MISSING"
    outputs = metadata.get("Output_Assets")
    asins = metadata.get("BenchmarkASINs")
    product_codes = metadata.get("BenchmarkProductCodes")
    if (not isinstance(asins, list) or not asins or len(set(asins)) != len(asins)
            or not isinstance(product_codes, dict) or set(product_codes) != set(asins)):
        return "601_PACKAGE_BENCHMARK_IDENTITY_INVALID"
    if any(not str(value or "").strip() for value in product_codes.values()):
        return "BENCHMARK_PRODUCT_CODE_MISSING"
    if metadata.get("BenchmarkRawOrganicFileCount") != len(asins):
        return "601_PACKAGE_RAW_FILE_COUNT_INVALID"
    if not isinstance(outputs, list) or len(outputs) != len(asins) + 3:
        return "601_PACKAGE_ASSET_LIST_INVALID"
    paths = [Path(item) for item in outputs]
    if Path(candidate_path).resolve() not in {path.resolve() for path in paths} or len({path.parent.resolve() for path in paths}) != 1:
        return "601_PACKAGE_FOLDER_MISMATCH"
    from scripts.hzp_amz_report_contract import resolve_skill_report_dir, validate_hzp_amz_report_batch
    skill_dir = Path(__file__).resolve().parents[1] / "hzp-amz-6-0-1-benchmark-organic-keyword-extraction"
    product_root = paths[0].resolve().parents[2]
    expected_dir = resolve_skill_report_dir(product_root, skill_dir)
    if paths[0].parent.resolve() != expected_dir.resolve():
        return "HZP_SKILL_REPORT_DIR_INVALID"
    report_error = validate_hzp_amz_report_batch(
        [*paths], product_root, skill_dir, timestamp=str(metadata.get("RUN_TIMESTAMP") or ""),
    )
    if report_error:
        return report_error
    by_identity: dict[str, tuple[Path, list[dict[str, str]], dict[str, Any]]] = {}
    for path in paths:
        sidecar = metadata_sidecar_path(path)
        if not path.is_file() or not sidecar.is_file():
            return "601_PACKAGE_ASSET_MISSING"
        try:
            with sidecar.open("r", encoding="utf-8-sig") as handle:
                asset_meta = json.load(handle)
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                schema = list(reader.fieldnames or ())
        except (OSError, UnicodeError, csv.Error, json.JSONDecodeError):
            return "601_PACKAGE_ASSET_UNREADABLE"
        identity = asset_meta.get("Report_Identity")
        if identity not in expected and isinstance(identity, str) and identity.startswith("BENCHMARK_KEYWORD_RAW_"):
            asin = identity.removeprefix("BENCHMARK_KEYWORD_RAW_")
            if asin in asins:
                expected[identity] = detail_schema
        if identity not in expected or identity in by_identity or schema != expected[identity]:
            return "601_PACKAGE_SCHEMA_OR_IDENTITY_INVALID"
        if (asset_meta.get("RUN_ID") != metadata.get("RUN_ID")
                or asset_meta.get("RUN_TIMESTAMP") != metadata.get("RUN_TIMESTAMP")
                or asset_meta.get("Run_Status") != "FULL_SUCCESS"
                or asset_meta.get("Schema") != schema
                or asset_meta.get("Record_Count") != len(rows)
                or asset_meta.get("Skill_ID") != metadata.get("Skill_ID")
                or asset_meta.get("Product_Code") != metadata.get("Product_Code")
                or asset_meta.get("Output_Assets") != outputs
                or asset_meta.get("BenchmarkASINs") != asins
                or asset_meta.get("BenchmarkProductCodes") != product_codes):
            return "601_PACKAGE_LINEAGE_INVALID"
        by_identity[identity] = (path, rows, asset_meta)
    expected_raw_identities = {f"BENCHMARK_KEYWORD_RAW_{asin}" for asin in asins}
    required_identities = {"BENCHMARK_KEYWORD_DETAIL", "BENCHMARK_KEYWORD_POOL", "BENCHMARK_KEYWORD_ALL_OBSERVATIONS"} | expected_raw_identities
    if set(by_identity) != required_identities:
        return "601_PACKAGE_ASSET_SET_INVALID"
    detail_rows = by_identity["BENCHMARK_KEYWORD_DETAIL"][1]
    summary_path, summary_rows, summary_meta = by_identity["BENCHMARK_KEYWORD_ALL_OBSERVATIONS"]
    if (summary_meta.get("BenchmarkOrganicSummaryFile") != summary_path.name
            or summary_meta.get("BenchmarkOrganicSummaryRecordCount") != len(summary_rows)
            or len(summary_rows) != len(detail_rows)):
        return "601_PACKAGE_SUMMARY_COUNT_INVALID"
    counts = Counter(str(row.get("ASIN") or "").strip() for row in summary_rows)
    if "" in counts or any(
        str(row.get("产品编号") or "").strip() != str(product_codes.get(str(row.get("ASIN") or "")) or "").strip()
        for row in summary_rows
    ):
        return "BENCHMARK_PRODUCT_CODE_MISSING"
    expected_counts = summary_meta.get("PerBenchmarkObservationCounts")
    if (summary_meta.get("BenchmarkRawOrganicFileCount") != len(asins)
            or summary_meta.get("BenchmarkRawOrganicFiles") != [by_identity[f"BENCHMARK_KEYWORD_RAW_{asin}"][0].name for asin in asins]
            or not isinstance(expected_counts, dict)
            or summary_meta.get("BenchmarkProductCodes") != product_codes):
        return "601_PACKAGE_BENCHMARK_COVERAGE_MISSING"
    if not set(counts).issubset(set(asins)) or {asin: counts.get(asin, 0) for asin in asins} != expected_counts:
        return "601_PACKAGE_BENCHMARK_COVERAGE_MISMATCH"
    summary_detail_schema = [column for column in detail_schema if column != "对标编码"]
    base_summary_rows = [{key: row[key] for key in summary_detail_schema} for row in summary_rows]
    expected_summary_rows = [{key: row[key] for key in summary_detail_schema} for row in detail_rows]
    if base_summary_rows != expected_summary_rows:
        return "601_PACKAGE_OBSERVATION_SUMMARY_MISMATCH"
    for asin in asins:
        raw_path, raw_rows, raw_meta = by_identity[f"BENCHMARK_KEYWORD_RAW_{asin}"]
        matching_summary_rows = [{key: row[key] for key in detail_schema} for row in detail_rows if row["对标ASIN"] == asin]
        if (raw_path.name != f"6-0-1_{asin}_关键词自然排名_{metadata.get('RUN_TIMESTAMP')}.csv"
                or raw_meta.get("Report_Identity") != f"BENCHMARK_KEYWORD_RAW_{asin}"
                or raw_rows != matching_summary_rows
                or len(raw_rows) != expected_counts.get(asin)):
            return "601_PACKAGE_PER_ASIN_COVERAGE_MISMATCH"
    return None


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or ()), list(reader)


def _parse_datetime(value: Any, local_tz: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        raw = str(value).strip()
        if re.fullmatch(r"\d{8}_\d{6}", raw):
            parsed = datetime.strptime(raw, RUN_TIMESTAMP_FORMAT)
        else:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=local_tz)
    return parsed


def _metadata(path: Path) -> dict[str, Any] | None:
    sidecar = metadata_sidecar_path(path)
    if not sidecar.is_file():
        return None
    try:
        with sidecar.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"_invalid_metadata": True}
    return value if isinstance(value, dict) else {"_invalid_metadata": True}


def _filename_timestamp(path: Path, local_tz: Any) -> datetime | None:
    match = RUN_TIMESTAMP_RE.search(path.name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), RUN_TIMESTAMP_FORMAT).replace(tzinfo=local_tz)
    except ValueError:
        return None


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _inspect_candidate(
    path: Path,
    *,
    product_root: Path,
    skill_id: str,
    report_identity: str,
    product_code: str,
    required_schema: Sequence[str] | None,
    required_status: Iterable[str],
    expected_metadata: Mapping[str, Any],
    now: datetime,
    validator: Callable[[Path, list[dict[str, str]] | None, Mapping[str, Any] | None], str | None] | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "valid": False, "reason": None}
    if not _is_within(path, product_root):
        result["reason"] = "PRODUCT_ROOT_SCOPE_MISMATCH"
        return result
    if not path.is_file():
        result["reason"] = "FILE_NOT_FOUND"
        return result
    try:
        if path.stat().st_size == 0:
            result["reason"] = "EMPTY_FILE"
            return result
    except OSError:
        result["reason"] = "FILE_READ_FAILED"
        return result

    local_now = now.astimezone()
    meta = _metadata(path)
    generated = None
    if meta and not meta.get("_invalid_metadata"):
        timestamp_value = next((meta.get(key) for key in ("Generated_At", "Run_Timestamp", "Created_At") if meta.get(key) not in (None, "")), None)
        generated = _parse_datetime(timestamp_value, local_now.tzinfo)
        if timestamp_value is not None and generated is None:
            result["reason"] = "METADATA_TIMESTAMP_INVALID"
            return result
        if timestamp_value is None:
            result["reason"] = "METADATA_TIMESTAMP_MISSING"
            return result
    if generated is None:
        generated = _filename_timestamp(path, local_now.tzinfo)
    result["generated_at"] = generated
    if meta and meta.get("_invalid_metadata"):
        result["reason"] = "METADATA_INVALID"
        return result
    if meta:
        for field, expected in {
            "Skill_ID": skill_id,
            "Product_Code": product_code,
            "Report_Identity": report_identity,
        }.items():
            actual = meta.get(field)
            if actual != expected:
                result["reason"] = f"{field.upper()}_MISMATCH"
                return result
        for field, expected in expected_metadata.items():
            if meta.get(field) != expected:
                result["reason"] = f"{field.upper()}_MISMATCH"
                return result
        if meta.get("RUN_TIMESTAMP") not in (None, "") and not re.fullmatch(r"\d{8}_\d{6}", str(meta["RUN_TIMESTAMP"])):
            result["reason"] = "RUN_TIMESTAMP_INVALID"
            return result
        if meta.get("RUN_ID") not in (None, "") and not str(meta["RUN_ID"]).strip():
            result["reason"] = "RUN_ID_INVALID"
            return result
        allowed = {str(value).upper() for value in required_status}
        if str(meta.get("Run_Status") or "").upper() not in allowed:
            result["reason"] = "RUN_STATUS_NOT_CONSUMABLE"
            return result

    rows: list[dict[str, str]] | None = None
    schema: list[str] | None = None
    if path.suffix.lower() == ".csv":
        try:
            schema, rows = _read_csv(path)
        except (OSError, UnicodeError, csv.Error):
            result["reason"] = "CSV_READ_FAILED"
            return result
        if required_schema is not None and schema != list(required_schema):
            result["reason"] = "SCHEMA_MISMATCH"
            result["actual_schema"] = schema
            return result
    if required_schema is not None and meta and meta.get("Schema") not in (None, list(required_schema)):
        result["reason"] = "METADATA_SCHEMA_MISMATCH"
        return result
    if meta and rows is not None and meta.get("Record_Count") not in (None, len(rows)):
        result["reason"] = "RECORD_COUNT_MISMATCH"
        return result

    if generated and generated > local_now:
        result["reason"] = "FUTURE_TIMESTAMP_DETECTED"
        return result

    if validator:
        error = validator(path, rows, meta)
        if error:
            result["reason"] = error
            return result

    run_id = meta.get("RUN_ID") if meta else None
    run_timestamp = meta.get("RUN_TIMESTAMP") if meta else None
    if not run_timestamp and generated:
        run_timestamp = generated.strftime(RUN_TIMESTAMP_FORMAT)
    result.update(
        valid=True,
        reason=None,
        metadata=dict(meta or {}),
        generated_at=generated,
        run_id=run_id,
        run_timestamp=run_timestamp,
        schema=schema,
        record_count=len(rows) if rows is not None else (meta or {}).get("Record_Count"),
        resolution_method=("LATEST_VALID_REPORT" if meta else "FILENAME_TIMESTAMP_FALLBACK" if generated else "LEGACY_FIXED_NAME_FALLBACK"),
        rows=rows,
    )
    return result


def _candidate_paths(candidates: Iterable[str | Path]) -> list[Path]:
    return sorted({Path(item) for item in candidates}, key=lambda item: str(item).casefold())


def resolve_latest_valid_report(
    product_root: str | Path,
    skill_id: str,
    report_identity: str,
    candidates: Iterable[str | Path],
    *,
    product_code: str,
    required_schema: Sequence[str] | None = None,
    required_status: Iterable[str] = DEFAULT_SUCCESS_STATUSES,
    expected_metadata: Mapping[str, Any] | None = None,
    validator: Callable[[Path, list[dict[str, str]] | None, Mapping[str, Any] | None], str | None] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Select the newest valid candidate using metadata, then filename time.

    Candidate discovery remains scoped to the caller's formal input directory;
    mtime is never a business-time signal.  Legacy fixed names are accepted
    only as a single-file fallback when no timestamped valid candidate exists.
    """
    root = Path(product_root)
    instant = now or datetime.now().astimezone()
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("RESOLUTION_TIME_REQUIRES_TIMEZONE_AWARE_DATETIME")
    inspected = [
        _inspect_candidate(
            path,
            product_root=root,
            skill_id=skill_id,
            report_identity=report_identity,
            product_code=product_code,
            required_schema=required_schema,
            required_status=required_status,
            expected_metadata=expected_metadata or {},
            now=instant,
            validator=validator,
        )
        for path in _candidate_paths(candidates)
    ]
    valid = [item for item in inspected if item["valid"]]
    timestamped = [item for item in valid if item.get("generated_at") is not None]
    if timestamped:
        timestamped.sort(key=lambda item: (item["generated_at"], Path(item["path"]).name.casefold()), reverse=True)
        selected = timestamped[0]
        newer_invalid = [
            item for item in inspected
            if not item["valid"] and item.get("generated_at") and item["generated_at"] > selected["generated_at"]
        ]
        method = "LATEST_INVALID_FALLBACK_USED" if newer_invalid else selected["resolution_method"]
        return {
            "status": "LATEST_VALID_REPORT_RESOLVED",
            "file": selected["path"],
            "rows": selected.get("rows"),
            "metadata": selected.get("metadata", {}),
            "run_id": selected.get("run_id"),
            "run_timestamp": selected.get("run_timestamp"),
            "generated_at": selected.get("generated_at").isoformat(timespec="seconds"),
            "record_count": selected.get("record_count"),
            "schema": selected.get("schema"),
            "input_resolution_method": method,
            "skipped_candidates": [item for item in inspected if not item["valid"]],
        }
    legacy = [item for item in valid if item.get("generated_at") is None]
    if len(legacy) == 1:
        selected = legacy[0]
        timestamped_invalid = [item for item in inspected if not item["valid"] and item.get("generated_at")]
        return {
            "status": "LATEST_VALID_REPORT_RESOLVED",
            "file": selected["path"],
            "rows": selected.get("rows"),
            "metadata": selected.get("metadata", {}),
            "run_id": selected.get("run_id"),
            "run_timestamp": None,
            "generated_at": None,
            "record_count": selected.get("record_count"),
            "schema": selected.get("schema"),
            "input_resolution_method": "LATEST_INVALID_FALLBACK_USED" if timestamped_invalid else "LEGACY_FIXED_NAME_FALLBACK",
            "skipped_candidates": [item for item in inspected if not item["valid"]],
        }
    status = "NO_VALID_UPSTREAM_REPORT" if inspected else "UPSTREAM_REPORT_NOT_FOUND"
    if len(legacy) > 1:
        status = "LEGACY_REPORT_TIME_AMBIGUOUS"
    return {"status": status, "file": None, "rows": None, "skipped_candidates": inspected}


def resolve_latest_valid_bundle(
    product_root: str | Path,
    skill_id: str,
    assets: Mapping[str, Iterable[str | Path]],
    *,
    product_code: str,
    report_identities: Mapping[str, str],
    required_schemas: Mapping[str, Sequence[str] | None] | None = None,
    required_status: Iterable[str] = DEFAULT_SUCCESS_STATUSES,
    expected_metadata: Mapping[str, Any] | None = None,
    validators: Mapping[str, Callable[[Path, list[dict[str, str]] | None, Mapping[str, Any] | None], str | None]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Resolve the newest complete multi-asset run, requiring a shared run key."""
    instant = now or datetime.now().astimezone()
    required_schemas = required_schemas or {}
    validators = validators or {}
    inspected_by_asset: dict[str, list[dict[str, Any]]] = {}
    for asset, candidates in assets.items():
        inspected_by_asset[asset] = [
            _inspect_candidate(
                path,
                product_root=Path(product_root),
                skill_id=skill_id,
                report_identity=report_identities[asset],
                product_code=product_code,
                required_schema=required_schemas.get(asset),
                required_status=required_status,
                expected_metadata=expected_metadata or {},
                now=instant,
                validator=validators.get(asset),
            )
            for path in _candidate_paths(candidates)
        ]
    keyed: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    legacy_by_asset: dict[str, list[dict[str, Any]]] = {}
    for asset, inspected in inspected_by_asset.items():
        for item in inspected:
            if not item["valid"]:
                continue
            # Old timestamped files can still be bundled by their filename
            # Run_Timestamp; legacy names without a timestamp cannot prove that
            # several files came from the same run.
            run_stamp = item.get("run_timestamp") or (item.get("generated_at").strftime(RUN_TIMESTAMP_FORMAT) if item.get("generated_at") else None)
            run_key = (str(item.get("run_id") or ""), str(run_stamp or ""))
            if any(run_key):
                keyed.setdefault(run_key, {})[asset] = item
            else:
                legacy_by_asset.setdefault(asset, []).append(item)
    complete = [
        (run_key, bundle)
        for run_key, bundle in keyed.items()
        if set(bundle) == set(assets)
    ]
    if not complete and set(legacy_by_asset) == set(assets) and all(len(legacy_by_asset[asset]) == 1 for asset in assets):
        legacy = {asset: legacy_by_asset[asset][0] for asset in assets}
        has_timestamped_invalid = any(
            not item["valid"] and item.get("generated_at") is not None
            for inspected in inspected_by_asset.values() for item in inspected
        )
        return {
            "status": "LATEST_VALID_RUN_BUNDLE_RESOLVED",
            "run_key": "LEGACY_FIXED_NAME",
            "run_id": None,
            "run_timestamp": None,
            "input_resolution_method": "LATEST_INVALID_FALLBACK_USED" if has_timestamped_invalid else "LEGACY_FIXED_NAME_FALLBACK",
            "assets": {
                asset: {
                    "file": item["path"],
                    "rows": item.get("rows"),
                    "metadata": item.get("metadata", {}),
                    "generated_at": None,
                    "record_count": item.get("record_count"),
                    "schema": item.get("schema"),
                }
                for asset, item in legacy.items()
            },
            "skipped_candidates": inspected_by_asset,
        }
    if not complete:
        return {
            "status": "NO_RUN_CONSISTENT_UPSTREAM_BUNDLE",
            "assets": {},
            "skipped_candidates": inspected_by_asset,
        }
    complete.sort(
        key=lambda pair: max(
            (item.get("generated_at") or datetime.min.replace(tzinfo=instant.tzinfo))
            for item in pair[1].values()
        ),
        reverse=True,
    )
    run_key, selected = complete[0]
    max_selected_time = max(
        (item.get("generated_at") or datetime.min.replace(tzinfo=instant.tzinfo))
        for item in selected.values()
    )
    newer_invalid = any(
        not item["valid"] and item.get("generated_at") and item["generated_at"] > max_selected_time
        for inspected in inspected_by_asset.values() for item in inspected
    )
    return {
        "status": "LATEST_VALID_RUN_BUNDLE_RESOLVED",
        "run_key": "|".join(run_key),
        "run_id": next((item.get("run_id") for item in selected.values() if item.get("run_id")), None),
        "run_timestamp": next((item.get("run_timestamp") for item in selected.values() if item.get("run_timestamp")), None),
        "input_resolution_method": "LATEST_INVALID_FALLBACK_USED" if newer_invalid else "LATEST_VALID_RUN_BUNDLE",
        "assets": {
            asset: {
                "file": item["path"],
                "rows": item.get("rows"),
                "metadata": item.get("metadata", {}),
                "generated_at": item.get("generated_at").isoformat(timespec="seconds") if item.get("generated_at") else None,
                "record_count": item.get("record_count"),
                "schema": item.get("schema"),
            }
            for asset, item in selected.items()
        },
        "skipped_candidates": inspected_by_asset,
    }
