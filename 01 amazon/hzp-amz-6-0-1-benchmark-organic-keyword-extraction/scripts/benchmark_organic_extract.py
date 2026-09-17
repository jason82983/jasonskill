"""Read-only extraction of Benchmark organic-keyword records.

The module deliberately separates identity resolution (ASIN -> Product Root ->
ERP ProId) from row filtering.  It never infers a field meaning from a column
name and never de-duplicates records by Keyword.
"""
from __future__ import annotations

import argparse
import csv
import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import re
import statistics
import sys
import shutil
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.stage6_artifact_contract import (  # noqa: E402
    assert_new_outputs,
    make_artifact_metadata,
    new_run_context,
    timestamped_output_path,
    write_metadata_sidecar,
)
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_batch,
)

OUTPUT_COLUMNS = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名")
DETAIL_COLUMNS = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标编号", "对标ASIN", "自然排名")
POOL_COLUMNS = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数")
ORGANIC_SUMMARY_COLUMNS = tuple(column for column in DETAIL_COLUMNS if column != "对标编码") + ("ASIN", "产品编号")
SCHEMA_MAPPING_UNRESOLVED = "SCHEMA_MAPPING_UNRESOLVED"
BENCHMARK_NOT_FOUND = "BENCHMARK_NOT_FOUND"
DATA_SOURCE_UNAVAILABLE = "DATA_SOURCE_UNAVAILABLE"
DATA_DUPLICATION_WARNING = "DATA_DUPLICATION_WARNING"
PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
BENCHMARK_ASIN_MISSING = "BENCHMARK_ASIN_MISSING"
BENCHMARK_PROID_MISSING = "BENCHMARK_PROID_MISSING"
BENCHMARK_IDENTITY_CONFLICT = "BENCHMARK_IDENTITY_CONFLICT"
KEYWORD_ENTITY_ID_UNCONFIRMED = "KEYWORD_ENTITY_ID_UNCONFIRMED"
KEYWORD_ENTITY_ID_CONFLICT = "KEYWORD_ENTITY_ID_CONFLICT"
KEYWORD_MARKET_FACT_CONFLICT = "KEYWORD_MARKET_FACT_CONFLICT"
BENCHMARK_OBSERVATION_CONFLICT = "BENCHMARK_OBSERVATION_CONFLICT"
BENCHMARK_PRODUCT_CODE_MISSING = "BENCHMARK_PRODUCT_CODE_MISSING"
KEYWORD_CN_TRANSLATION_INCOMPLETE = "KEYWORD_CN_TRANSLATION_INCOMPLETE"

# The user confirmed that KwId is stable and unique for the same keyword
# across ProIds. `Id` remains the PickPwKView observation-row identity.
KEYWORD_ENTITY_ID_FIELD: str | None = "KwId"

# These mappings were explicitly confirmed for this ERP view and are used as
# defaults so routine Product_Code runs do not repeatedly ask for them.
CONFIRMED_FIELD_MAP = {
    "id": "Id",
    "keyword": "Keyword",
    "keyword_cn": "KeywordCn",
    "capacity": "SearchVolume30",
    "asin_quantity": "AsinQuantity",
    "organic_rank": "RankOra",
}


def build_keyword_translator() -> Any:
    return None


def ensure_keyword_chinese(keyword: Any, keyword_cn: Any, translator: Any = None) -> tuple[str, str]:
    """Return ``(Chinese, status)`` without overwriting a confirmed source value."""
    existing = str(keyword_cn or "").strip()
    if existing:
        return existing, "SOURCE"
    if translator is None:
        return "", "MISSING"
    translated = str(translator(keyword) or "").strip()
    return (translated, "TRANSLATED" if translated else "TRANSLATION_FAILED")


def backfill_keyword_cn_csv(path: str | Path, rows: list[dict[str, Any]], translator: Any) -> dict[str, Any]:
    """Translate blank KeywordCn cells and persist only those cells to the source CSV."""
    translated = 0
    failed = 0
    cache: dict[str, str] = {}
    for row in rows:
        if str(row.get("KeywordCn") or "").strip():
            continue
        keyword = str(row.get("Keyword") or "").strip()
        if not keyword:
            failed += 1
            continue
        if keyword not in cache:
            cache[keyword] = str(translator(keyword) if translator else "").strip()
        value = cache[keyword]
        if value:
            row["KeywordCn"] = value
            translated += 1
        else:
            failed += 1
    if translated:
        target = Path(path)
        headers = list(rows[0].keys()) if rows else []
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    return {"translated": translated, "failed": failed}


def parse_number(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _decimal_value(value: Any) -> Decimal | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        return None
    return number if number.is_finite() else None


def _supply_demand_ratio(capacity: Any, asin_quantity: Any) -> str | None:
    market_capacity = _decimal_value(capacity)
    competitor_count = _decimal_value(asin_quantity)
    if market_capacity is None or competitor_count is None or competitor_count <= 0:
        return None
    ratio = (market_capacity / competitor_count).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return format(ratio, ".4f")


def filter_and_sort_records(
    rows: Iterable[Mapping[str, Any]],
    *,
    field_map: Mapping[str, str],
    translator: Any = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Filter every source row and return all matches in deterministic order.

    ``field_map`` must be explicitly supplied by a confirmed Schema mapping;
    no fallback is made from familiar-looking field names.
    """
    required = ("id", "keyword", "keyword_cn", "capacity", "asin_quantity", "organic_rank")
    missing = [key for key in required if not field_map.get(key)]
    if missing:
        return [], {"status": SCHEMA_MAPPING_UNRESOLVED, "missing_fields": missing}

    source = list(rows)
    matched: list[dict[str, Any]] = []
    invalid_capacity = 0
    invalid_rank = 0
    zero_asin_quantity_ids: list[str] = []
    translated_keyword_cn_records = 0
    missing_keyword_cn_records = 0
    translation_failures = 0
    for row in source:
        capacity = parse_number(row.get(field_map["capacity"]))
        rank = parse_number(row.get(field_map["organic_rank"]))
        if capacity is None:
            invalid_capacity += 1
        if rank is None:
            invalid_rank += 1
        if capacity is None or rank is None or rank < 1 or capacity <= 100:
            continue
        asin_quantity = row.get(field_map["asin_quantity"])
        if _decimal_value(asin_quantity) == 0:
            zero_asin_quantity_ids.append(str(row.get(field_map["id"])))
        keyword_cn, translation_status = ensure_keyword_chinese(
            row.get(field_map["keyword"]), row.get(field_map["keyword_cn"]), translator,
        )
        if translation_status == "TRANSLATED":
            translated_keyword_cn_records += 1
        elif translation_status == "MISSING":
            missing_keyword_cn_records += 1
        elif translation_status == "TRANSLATION_FAILED":
            missing_keyword_cn_records += 1
            translation_failures += 1
        matched.append({
            "Id": row.get(field_map["id"]),
            "词": row.get(field_map["keyword"]),
            "中文": keyword_cn,
            "市场容量": row.get(field_map["capacity"]),
            "竞争产品数": asin_quantity,
            "供需比": _supply_demand_ratio(row.get(field_map["capacity"]), asin_quantity),
            "自然排名": row.get(field_map["organic_rank"]),
        })

    duplicate_warning = len({str(item["词"]).strip().lower() for item in matched}) < len(matched)
    matched.sort(key=lambda item: (
        -float(parse_number(item["市场容量"])),
        float(parse_number(item["自然排名"])),
        str(item["Id"]),
    ))
    status = DATA_DUPLICATION_WARNING if duplicate_warning else "OK"
    return matched, {
        "status": status,
        "source_records": len(source),
        "matched_records": len(matched),
        "invalid_capacity_records": invalid_capacity,
        "invalid_rank_records": invalid_rank,
        "metadata": {
            "COMPETING_PRODUCT_SOURCE_VIEW": "PickPwKView",
            "COMPETING_PRODUCT_SOURCE_FIELD": "AsinQuantity",
        },
        "asin_quantity_zero_records": len(zero_asin_quantity_ids),
        "asin_quantity_zero_ids": zero_asin_quantity_ids,
        "translated_keyword_cn_records": translated_keyword_cn_records,
        "missing_keyword_cn_records": missing_keyword_cn_records,
        "translation_failures": translation_failures,
        "warnings": ([{"code": "ASIN_QUANTITY_ZERO", "record_ids": zero_asin_quantity_ids}]
                     if zero_asin_quantity_ids else []),
    }


def write_csv(path: str | Path, records: Iterable[Mapping[str, Any]]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    values = list(records)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(values)
    return target


def write_asset_csv(path: str | Path, records: Iterable[Mapping[str, Any]], columns: Iterable[str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    return target


def extract_rows(
    rows: Iterable[Mapping[str, Any]],
    output_path: str | Path,
    *,
    field_map: Mapping[str, str],
    translator: Any = None,
) -> dict[str, Any]:
    values, summary = filter_and_sort_records(rows, field_map=field_map, translator=translator)
    if summary.get("status") == SCHEMA_MAPPING_UNRESOLVED:
        return summary | {"csv_records": 0, "output": None}
    path = write_csv(output_path, values)
    summary = dict(summary)
    summary["csv_records"] = len(values)
    summary["output"] = str(path)
    summary["matched_equals_csv"] = summary["matched_records"] == summary["csv_records"]
    return summary


def _same_market_value(left: Any, right: Any) -> bool:
    left_number = _decimal_value(left)
    right_number = _decimal_value(right)
    if left_number is None or right_number is None:
        return left_number is None and right_number is None
    return left_number == right_number


def build_multi_benchmark_assets(
    benchmark_records: Iterable[Mapping[str, Any]],
    *,
    keyword_entity_id_field: str | None,
    benchmark_product_codes: Mapping[str, Any] | None = None,
    translator: Any = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, Any]]:
    """Split one Keyword Market Fact from its Benchmark Rank Observations.

    Each input record is one already-filtered PickPwKView row annotated with
    `Benchmark_Code` and `Benchmark_ASIN`. The stable entity field is supplied
    explicitly by the confirmed field contract (`KwId`); source `Id` and `KwId`
    are never assumed to be interchangeable.
    """
    if not keyword_entity_id_field:
        return [], [], {}, [], {"status": KEYWORD_ENTITY_ID_UNCONFIRMED, "conflicts": []}
    if not isinstance(benchmark_product_codes, Mapping):
        return [], [], {}, [], {"status": BENCHMARK_PRODUCT_CODE_MISSING, "conflicts": []}

    grouped: dict[str, dict[str, Any]] = {}
    observations: dict[tuple[str, str], dict[str, Any]] = {}
    fact_conflicts: list[dict[str, Any]] = []
    identity_conflicts: list[dict[str, Any]] = []
    observation_conflicts: list[dict[str, Any]] = []

    for source in benchmark_records:
        raw = source.get("raw_fields", source)
        entity_id = str(raw.get(keyword_entity_id_field) or "").strip()
        if not entity_id:
            identity_conflicts.append({"field": keyword_entity_id_field, "row_id": raw.get("Id")})
            continue
        benchmark_code = str(source.get("Benchmark_Code") or "").strip()
        benchmark_asin = str(source.get("Benchmark_ASIN") or "").strip()
        keyword = str(raw.get("Keyword") or "").strip()
        rank = parse_number(raw.get("RankOra"))
        capacity = raw.get("SearchVolume30")
        competitors = raw.get("AsinQuantity")
        keyword_cn, _translation_status = ensure_keyword_chinese(
            keyword, raw.get("KeywordCn"), translator,
        )
        if not benchmark_code:
            return [], [], {}, [], {"status": BENCHMARK_IDENTITY_CONFLICT, "conflicts": [{"row_id": raw.get("Id")}]}
        if not benchmark_asin or not keyword or rank is None or rank < 1:
            continue

        key = entity_id
        market_fact = {
            "Id": entity_id,
            "词": keyword,
            "中文": keyword_cn,
            "市场容量": capacity,
            "竞争产品数": competitors,
            "供需比": _supply_demand_ratio(capacity, competitors),
        }
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = {"fact": market_fact, "ranks": {}, "source_order": len(grouped)}
        else:
            fact = existing["fact"]
            if str(fact["词"]).strip() != keyword:
                identity_conflicts.append({"entity_id": entity_id, "keywords": [fact["词"], keyword]})
                continue
            if not _same_market_value(fact["市场容量"], capacity) or not _same_market_value(fact["竞争产品数"], competitors):
                fact_conflicts.append({
                    "entity_id": entity_id,
                    "benchmark_code": benchmark_code,
                    "benchmark_asin": benchmark_asin,
                    "left": {"市场容量": fact["市场容量"], "竞争产品数": fact["竞争产品数"]},
                    "right": {"市场容量": capacity, "竞争产品数": competitors},
                })
                continue
            if not fact.get("中文") and keyword_cn:
                fact["中文"] = keyword_cn

        observation_key = (entity_id, benchmark_code)
        previous = observations.get(observation_key)
        if previous is not None:
            if parse_number(previous["自然排名"]) != rank or str(previous["Id"]) != str(raw.get("Id")):
                observation_conflicts.append({"entity_id": entity_id, "benchmark_code": benchmark_code})
            continue
        observation = {
            # Contract `Id` is the stable keyword entity (KwId). The source
            # PickPwKView.Id remains an observation-row key used only to detect
            # duplicate/conflicting rows inside this extraction run.
            "Id": entity_id,
            "词": keyword,
            "中文": keyword_cn,
            "市场容量": capacity,
            "竞争产品数": competitors,
            "供需比": _supply_demand_ratio(capacity, competitors),
            "对标编号": str(benchmark_product_codes.get(benchmark_asin) or "").strip(),
            "对标ASIN": benchmark_asin,
            "自然排名": raw.get("RankOra"),
        }
        observations[observation_key] = observation
        grouped[key]["ranks"][benchmark_code] = rank

    conflicts = []
    if identity_conflicts:
        conflicts.append({"code": KEYWORD_ENTITY_ID_CONFLICT, "records": identity_conflicts})
    if fact_conflicts:
        conflicts.append({"code": KEYWORD_MARKET_FACT_CONFLICT, "records": fact_conflicts})
    if observation_conflicts:
        conflicts.append({"code": BENCHMARK_OBSERVATION_CONFLICT, "records": observation_conflicts})
    if conflicts:
        return [], [], {}, [], {"status": "UNRESOLVED", "conflicts": conflicts}

    detail_rows = list(observations.values())
    detail_rows.sort(key=lambda row: (
        -float(parse_number(row["市场容量"])),
        float(parse_number(row["自然排名"])),
        str(row["对标编号"]),
    ))
    pool_rows: list[dict[str, Any]] = []
    for entity_id, data in grouped.items():
        fact = data["fact"]
        ranks = list(data["ranks"].values())
        if not ranks:
            continue
        pool_rows.append({
            **fact,
            "对标覆盖数": len(ranks),
            "最佳自然排名": min(ranks),
            "自然排名中位数": statistics.median(ranks),
            "_source_order": data["source_order"],
        })
    pool_rows.sort(key=lambda row: (
        -float(parse_number(row["市场容量"])),
        row["_source_order"],
    ))
    for row in pool_rows:
        row.pop("_source_order", None)

    detail_entity_ids = {str(entity_id) for entity_id, data in grouped.items() if data["ranks"]}
    pool_entity_ids = {str(row.get("Id") or "") for row in pool_rows}
    if detail_entity_ids != pool_entity_ids:
        return [], [], {}, [], {"status": "KEYWORD_ENTITY_COVERAGE_MISMATCH", "conflicts": []}
    raw_by_asin: dict[str, list[dict[str, Any]]] = {}
    summary_rows: list[dict[str, Any]] = []
    for row in detail_rows:
        asin = str(row["对标ASIN"])
        product_number = str(benchmark_product_codes.get(asin) or "").strip()
        if not product_number:
            return [], [], {}, [], {"status": BENCHMARK_PRODUCT_CODE_MISSING, "conflicts": [{"asin": asin}]}
        raw_by_asin.setdefault(asin, []).append(dict(row))
        summary_rows.append({key: value for key, value in row.items() if key != "对标编码"} | {"ASIN": asin, "产品编号": product_number})
    return detail_rows, pool_rows, raw_by_asin, summary_rows, {
        "status": "OK",
        "detail_records": len(detail_rows),
        "unique_keyword_entities": len(pool_rows),
        "benchmark_observations": len(detail_rows),
        "market_fact_conflicts": 0,
        "coverage": "PASS",
    }


def _read_product_identity(archive: Path) -> tuple[str | None, str | None]:
    product_code = erp_id = None
    for line in archive.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("产品编号："):
            product_code = line.split("：", 1)[1].strip()
        elif line.startswith("ERP编号："):
            erp_id = line.split("：", 1)[1].strip()
    return product_code, erp_id


def _read_benchmark_fields(archive: Path) -> dict[str, Any]:
    """Read explicit ASIN/ERP pairs from the product archive, preserving order."""
    text = archive.read_text(encoding="utf-8-sig")
    in_benchmark_section = False
    benchmarks: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    malformed: list[str] = []

    def save_current() -> None:
        nonlocal current
        if current:
            if not current.get("ASIN") or not current.get("ERP_ProId"):
                malformed.append(str(current))
            else:
                benchmarks.append(current)
        current = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### 对标产品"):
            in_benchmark_section = True
            continue
        if in_benchmark_section and stripped.startswith("### "):
            break
        if not in_benchmark_section:
            continue
        asin_match = re.match(r"^-?\s*ASIN\s*[:：]\s*([A-Za-z0-9]+)\s*$", stripped, re.I)
        if asin_match:
            save_current()
            current = {"ASIN": asin_match.group(1).strip()}
            continue
        if current is None:
            continue
        code_match = re.match(r"^-?\s*(?:对标编码|Benchmark\s*Code)\s*[:：]\s*([A-Za-z0-9_-]+)\s*$", stripped, re.I)
        if code_match:
            current["Benchmark_Code"] = code_match.group(1).strip()
            continue
        pro_match = re.match(
            r"^-?\s*(?:对标\s*)?(?:ERP\s*)?(?:产品)?(?:编号|ProId)\s*[:：]\s*(.+?)\s*$",
            stripped,
            re.I,
        )
        if pro_match and ("对标" in stripped or "benchmark" in stripped.lower()):
            value = pro_match.group(1).strip().strip("`[]()")
            if re.fullmatch(r"[A-Za-z0-9_-]+", value):
                current["ERP_ProId"] = value
            else:
                malformed.append(stripped)
    save_current()
    asins = [item["ASIN"] for item in benchmarks]
    duplicate_asins = len(asins) != len(set(asins))
    return {
        "status": "BENCHMARK_CONFIG_INVALID" if malformed or duplicate_asins else "OK",
        "benchmarks": benchmarks,
        "asins": asins,
        "pro_ids": [item["ERP_ProId"] for item in benchmarks],
        "malformed": malformed,
        "duplicate_asins": duplicate_asins,
    }


def resolve_product_code_identity(
    product_code: str,
    *,
    products_root: str | Path,
) -> dict[str, Any]:
    """Resolve Product_Code to its archive's explicit benchmark identity."""
    matches: list[tuple[Path, str | None]] = []
    for archive in Path(products_root).rglob("01_产品档案.md"):
        archive_code, _erp_id = _read_product_identity(archive)
        if archive_code == product_code:
            matches.append((archive, archive_code))
    if len(matches) != 1:
        return {"status": PRODUCT_NOT_FOUND, "product_code": product_code, "candidate_archives": [str(path) for path, _ in matches]}
    archive = matches[0][0]
    benchmark = _read_benchmark_fields(archive)
    if not benchmark["asins"]:
        return {"status": BENCHMARK_ASIN_MISSING, "product_code": product_code, "product_archive": str(archive)}
    if benchmark.get("status") != "OK":
        return {"status": "BENCHMARK_IDENTITY_CONFLICT", "product_code": product_code,
                "product_archive": str(archive), "benchmark_config": benchmark}
    if not benchmark["pro_ids"]:
        return {"status": BENCHMARK_PROID_MISSING, "product_code": product_code, "product_archive": str(archive)}
    benchmark_items = [
        {
            "benchmark_code": item.get("Benchmark_Code") or f"ASIN_{item['ASIN']}",
            "benchmark_asin": item["ASIN"],
            "benchmark_erp_pro_id": item["ERP_ProId"],
        }
        for item in benchmark["benchmarks"]
    ]
    codes = [item["benchmark_code"] for item in benchmark_items]
    if len(codes) != len(set(codes)):
        return {"status": BENCHMARK_IDENTITY_CONFLICT, "product_code": product_code,
                "product_archive": str(archive), "benchmark_codes": codes}
    return {
        "status": "IDENTITY_RESOLVED",
        "product_code": product_code,
        "product_archive": str(archive),
        "benchmarks": benchmark_items,
        # Backward-compatible fields are populated only for the single-benchmark form.
        "benchmark_asin": benchmark_items[0]["benchmark_asin"] if len(benchmark_items) == 1 else None,
        "erp_pro_id": benchmark_items[0]["benchmark_erp_pro_id"] if len(benchmark_items) == 1 else None,
        "benchmark_erp_pro_id": benchmark_items[0]["benchmark_erp_pro_id"] if len(benchmark_items) == 1 else None,
    }


def resolve_benchmark_identity(
    benchmark_asin: str,
    *,
    products_root: str | Path,
    mapping_workbook: str | Path,
) -> dict[str, Any]:
    """Resolve ASIN via the read-only workbook, then archive ERP编号.

    The workbook is an identity map only; PickPwKView is still queried by the
    archive's ERP编号.  This function requires ``openpyxl`` at runtime and
    returns an explicit failure status when the mapping is unavailable.
    """
    try:
        import openpyxl  # type: ignore
    except Exception:
        return {"status": DATA_SOURCE_UNAVAILABLE, "reason": "openpyxl unavailable"}
    try:
        workbook = openpyxl.load_workbook(mapping_workbook, read_only=True, data_only=True)
    except Exception as exc:
        return {"status": DATA_SOURCE_UNAVAILABLE, "reason": type(exc).__name__}
    matches: list[tuple[str, str | None]] = []
    for sheet in workbook.worksheets:
        rows = sheet.iter_rows(values_only=True)
        try:
            headers = list(next(rows))
        except StopIteration:
            continue
        header_index = {str(value).strip(): i for i, value in enumerate(headers) if value is not None}
        if "ASIN" not in header_index or "Product_Code" not in header_index:
            continue
        for values in rows:
            asin = str(values[header_index["ASIN"]] or "").strip()
            if asin != benchmark_asin:
                continue
            status = values[header_index.get("Status", -1)] if "Status" in header_index else None
            if status not in (None, "", "ACTIVE"):
                continue
            code = str(values[header_index["Product_Code"]] or "").strip()
            matches.append((code, str(status or "").strip() or None))
    codes = list(dict.fromkeys(code for code, _ in matches if code))
    if len(codes) != 1:
        return {"status": BENCHMARK_NOT_FOUND, "candidate_product_codes": codes}
    code = codes[0]
    archives = []
    for archive in Path(products_root).rglob("01_产品档案.md"):
        archive_code, erp_id = _read_product_identity(archive)
        if archive_code == code:
            archives.append((archive, erp_id))
    if len(archives) != 1 or not archives[0][1]:
        return {"status": SCHEMA_MAPPING_UNRESOLVED, "reason": "unique Product Root/ERP编号 unavailable", "product_code": code}
    archive, erp_id = archives[0]
    return {"status": "IDENTITY_RESOLVED", "product_code": code, "erp_pro_id": erp_id, "product_archive": str(archive), "benchmark_asin": benchmark_asin}


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Benchmark organic keywords")
    identity_group = parser.add_mutually_exclusive_group(required=True)
    identity_group.add_argument("--benchmark-asin")
    identity_group.add_argument("--product-code")
    parser.add_argument("--products-root", required=True)
    parser.add_argument("--mapping-workbook")
    parser.add_argument("--output", help="Optional destination directory; output is always timestamped")
    parser.add_argument("--config-dir")
    parser.add_argument("--id-field")
    parser.add_argument("--keyword-field")
    parser.add_argument("--keyword-cn-field")
    parser.add_argument("--capacity-field")
    parser.add_argument("--organic-rank-field")
    parser.add_argument("--input-csv", required=True, help="ERP导出的对标 PickPwKView CSV")
    args = parser.parse_args()
    if args.product_code:
        identity = resolve_product_code_identity(args.product_code, products_root=args.products_root)
        benchmarks = identity.get("benchmarks") or []
    else:
        if not args.mapping_workbook:
            print({"status": BENCHMARK_NOT_FOUND, "reason": "--mapping-workbook is required with --benchmark-asin"})
            return 2
        identity = resolve_benchmark_identity(args.benchmark_asin, products_root=args.products_root, mapping_workbook=args.mapping_workbook)
        benchmarks = ([{
            "benchmark_code": f"ASIN_{identity['benchmark_asin']}",
            "benchmark_asin": identity["benchmark_asin"],
            "benchmark_erp_pro_id": identity["erp_pro_id"],
        }] if identity.get("status") == "IDENTITY_RESOLVED" else [])
    if identity.get("status") != "IDENTITY_RESOLVED":
        print(identity)
        return 2
    if not str(identity.get("product_code") or "").strip():
        print({"status": BENCHMARK_PRODUCT_CODE_MISSING, "product_archive": identity.get("product_archive")})
        return 2
    if not benchmarks:
        print({"status": BENCHMARK_ASIN_MISSING, "product_code": identity.get("product_code")})
        return 2
    benchmark_product_codes = {
        str(item.get("benchmark_asin") or "").strip(): str(item.get("benchmark_erp_pro_id") or "").strip()
        for item in benchmarks
    }
    if any(not asin or not pro_id for asin, pro_id in benchmark_product_codes.items()):
        print({"status": BENCHMARK_PRODUCT_CODE_MISSING, "benchmark_product_codes": benchmark_product_codes})
        return 2
    field_map = {
        "id": args.id_field or CONFIRMED_FIELD_MAP["id"],
        "keyword_entity_id": KEYWORD_ENTITY_ID_FIELD,
        "keyword": args.keyword_field or CONFIRMED_FIELD_MAP["keyword"],
        "keyword_cn": args.keyword_cn_field or CONFIRMED_FIELD_MAP["keyword_cn"],
        "capacity": args.capacity_field or CONFIRMED_FIELD_MAP["capacity"],
        "asin_quantity": CONFIRMED_FIELD_MAP["asin_quantity"],
        "organic_rank": args.organic_rank_field or CONFIRMED_FIELD_MAP["organic_rank"],
    }
    try:
        keyword_translator = build_keyword_translator()
        with open(args.input_csv, encoding="utf-8-sig", newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
        observation_rows: list[dict[str, Any]] = []
        query_summaries: list[dict[str, Any]] = []
        for benchmark in benchmarks:
            result = {"status": "ERP_KEYWORD_DATA_READY", "rows": [{"raw_fields": row} for row in csv_rows]}
            if result.get("status") != "ERP_KEYWORD_DATA_READY":
                print({
                    "status": DATA_SOURCE_UNAVAILABLE,
                    "benchmark_code": benchmark["benchmark_code"],
                    "benchmark_asin": benchmark["benchmark_asin"],
                    "provider_status": result.get("status"),
                })
                return 2
            fetched = list(result.get("rows", []))
            raw_by_id = {str(row.get("raw_fields", row).get(field_map["id"]) or ""): row.get("raw_fields", row) for row in fetched}
            if len(raw_by_id) != len(fetched):
                print({"status": DATA_DUPLICATION_WARNING, "benchmark_code": benchmark["benchmark_code"], "reason": "PickPwKView.Id is not unique in fetched rows"})
                return 2
            source_rows = [row.get("raw_fields", row) for row in fetched]
            filtered, filter_summary = filter_and_sort_records(
                source_rows, field_map=field_map, translator=keyword_translator,
            )
            if filter_summary.get("status") == SCHEMA_MAPPING_UNRESOLVED:
                print(filter_summary)
                return 2
            eligible_ids = {str(row.get("Id") or "") for row in filtered}
            for row_id in eligible_ids:
                observation_rows.append({
                    "raw_fields": raw_by_id[row_id],
                    "Benchmark_Code": benchmark["benchmark_code"],
                    "Benchmark_ASIN": benchmark["benchmark_asin"],
                })
            query_summaries.append({
                "benchmark_code": benchmark["benchmark_code"],
                "benchmark_asin": benchmark["benchmark_asin"],
                "erp_pro_id": benchmark["benchmark_erp_pro_id"],
                "source_records": len(fetched),
                "matched_records": len(filtered),
            })
    except Exception as exc:
        print({"status": DATA_SOURCE_UNAVAILABLE, "reason": type(exc).__name__})
        return 2
    detail_rows, pool_rows, raw_rows_by_asin, summary_rows, aggregation = build_multi_benchmark_assets(
        observation_rows,
        keyword_entity_id_field=field_map["keyword_entity_id"],
        benchmark_product_codes=benchmark_product_codes,
        translator=keyword_translator,
    )
    if aggregation.get("status") != "OK":
        print(aggregation)
        return 2
    product_root = Path(identity["product_archive"]).parent
    context = new_run_context("6-0-1", "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", identity["product_code"])
    if args.output and Path(args.output).suffix.lower() == ".csv":
        supplied = Path(args.output)
        output_dir = supplied.parent
    else:
        output_dir = Path(args.output) if args.output else product_root / "06_SKILL分析报告" / "6-0-1_对标自然排名关键词提取"
    run_folder = resolve_skill_report_dir(product_root, Path(__file__).resolve().parents[1])
    detail_path = run_folder / build_report_filename(Path(__file__).resolve().parents[1], "多对标关键词排名明细", context.run_timestamp, "csv")
    pool_path = run_folder / build_report_filename(Path(__file__).resolve().parents[1], "对标关键词母池", context.run_timestamp, "csv")
    raw_paths = {
        item["benchmark_asin"]: run_folder / build_report_filename(Path(__file__).resolve().parents[1], f"{item['benchmark_asin']}_关键词自然排名", context.run_timestamp, "csv")
        for item in benchmarks
    }
    organic_summary_path = run_folder / build_report_filename(Path(__file__).resolve().parents[1], "所有对标自然排名关键词", context.run_timestamp, "csv")
    # Keep generated assets ordered and easy to inspect in file explorers.
    detail_path = detail_path.with_name(detail_path.name.replace("6-0-1_", "6-0-1_01_", 1))
    pool_path = pool_path.with_name(pool_path.name.replace("6-0-1_", "6-0-1_02_", 1))
    raw_paths = {asin: path.with_name(path.name.replace("6-0-1_", f"6-0-1_{index:02d}_", 1)) for index, (asin, path) in enumerate(raw_paths.items(), 3)}
    organic_summary_path = organic_summary_path.with_name(organic_summary_path.name.replace("6-0-1_", f"6-0-1_{len(raw_paths) + 3:02d}_", 1))
    all_asset_paths = [detail_path, pool_path, *raw_paths.values(), organic_summary_path]
    report_contract_error = validate_hzp_amz_report_batch(
        all_asset_paths, product_root, Path(__file__).resolve().parents[1], timestamp=context.run_timestamp,
    )
    if report_contract_error:
        print({"status": report_contract_error})
        return 2
    assert_new_outputs([*all_asset_paths, *(str(path) + ".meta.json" for path in all_asset_paths)])
    write_asset_csv(detail_path, detail_rows, DETAIL_COLUMNS)
    write_asset_csv(pool_path, pool_rows, POOL_COLUMNS)
    for asin, path in raw_paths.items():
        write_asset_csv(path, raw_rows_by_asin.get(asin, []), DETAIL_COLUMNS)
    write_asset_csv(organic_summary_path, summary_rows, ORGANIC_SUMMARY_COLUMNS)
    matched_records = sum(item["matched_records"] for item in query_summaries)
    per_benchmark_counts = {item["benchmark_asin"]: sum(
        1 for row in summary_rows if row["ASIN"] == item["benchmark_asin"]
    ) for item in query_summaries}
    coverage_pass = (
        aggregation.get("coverage") == "PASS"
        and len(detail_rows) == matched_records
        and len(summary_rows) == len(detail_rows)
        and all(len(raw_rows_by_asin.get(item["benchmark_asin"], [])) == item["matched_records"] == per_benchmark_counts[item["benchmark_asin"]] for item in query_summaries)
        and all(str(row.get("产品编号") or "").strip() == benchmark_product_codes.get(str(row.get("ASIN") or "")) for row in summary_rows)
        and all(str(row.get("ASIN") or "").strip() for row in summary_rows)
    )
    inputs = [{
        "Input_Skill": "LIVE_QUERY",
        "Input_Report_Identity": "PICKPWKVIEW_BENCHMARK_ROWS",
        "Input_File_Name": None,
        "Input_Run_Timestamp": None,
        "Input_Generated_At": context.generated_at,
        "Input_Record_Count": item["source_records"],
        "Input_Resolution_Method": "LIVE_QUERY",
        "Benchmark_Code": item["benchmark_code"],
        "Benchmark_ASIN": item["benchmark_asin"],
        "ERP_ProId": item["erp_pro_id"],
    } for item in query_summaries]
    outputs = [str(path) for path in all_asset_paths]
    benchmark_codes = [item["benchmark_code"] for item in benchmarks]
    metadata_assets = [
        (detail_path, "BENCHMARK_KEYWORD_DETAIL", DETAIL_COLUMNS, detail_rows),
        (pool_path, "BENCHMARK_KEYWORD_POOL", POOL_COLUMNS, pool_rows),
        *[(raw_paths[item["benchmark_asin"]], f"BENCHMARK_KEYWORD_RAW_{item['benchmark_asin']}", DETAIL_COLUMNS, raw_rows_by_asin.get(item["benchmark_asin"], [])) for item in benchmarks],
        (organic_summary_path, "BENCHMARK_KEYWORD_ALL_OBSERVATIONS", ORGANIC_SUMMARY_COLUMNS, summary_rows),
    ]
    benchmark_asins = [item["benchmark_asin"] for item in benchmarks]
    common_extra = {
        "Benchmark_Count": len(benchmarks), "Benchmark_Codes": benchmark_codes,
        "Benchmark_ASINs": benchmark_asins,
        "BenchmarkASINs": benchmark_asins,
        "Benchmark_ERP_ProIds": [item["benchmark_erp_pro_id"] for item in benchmarks],
        "Keyword_Entity_ID_Field": KEYWORD_ENTITY_ID_FIELD,
        "BenchmarkRawOrganicFiles": [raw_paths[asin].name for asin in benchmark_asins],
        "BenchmarkRawOrganicFileCount": len(benchmarks),
        "BenchmarkOrganicSummaryFile": organic_summary_path.name,
        "BenchmarkOrganicSummaryRecordCount": len(summary_rows),
        "PerBenchmarkObservationCounts": per_benchmark_counts,
        "BenchmarkProductCodes": benchmark_product_codes,
    }
    for path, report_identity, schema, rows in metadata_assets:
        metadata = make_artifact_metadata(
            context, report_identity,
            run_status="FULL_SUCCESS" if coverage_pass else "INCOMPLETE",
            schema=schema, record_count=len(rows), inputs=inputs,
            output_assets=outputs,
            extra=common_extra,
        )
        write_metadata_sidecar(path, metadata)
    # Keep every timestamped CSV directly visible at the Skill report root so
    # people can inspect historical runs without opening the canonical data
    # layer. The canonical Run Package remains in its normal output directory.
    visible_dir = product_root / "06_SKILL分析报告" / "6-0-1_对标自然排名关键词提取"
    visible_dir.mkdir(parents=True, exist_ok=True)
    visible_outputs: list[str] = []
    for source_path in all_asset_paths:
        visible_path = visible_dir / source_path.name
        if visible_path.exists():
            raise FileExistsError(f"VISIBLE_OUTPUT_ALREADY_EXISTS: {visible_path.name}")
        shutil.copyfile(source_path, visible_path)
        shutil.copyfile(Path(str(source_path) + ".meta.json"), Path(str(visible_path) + ".meta.json"))
        visible_outputs.append(str(visible_path))
    summary = {
        "status": "FULL_SUCCESS" if coverage_pass else "INCOMPLETE",
        "product_code": identity["product_code"],
        "benchmark_count": len(benchmarks),
        "benchmark_codes": benchmark_codes,
        "query_summaries": query_summaries,
        "matched_observations": len(detail_rows),
        "unique_keyword_entities": len(pool_rows),
        "observation_coverage": aggregation.get("coverage"),
        "market_fact_conflicts": aggregation.get("market_fact_conflicts"),
        "detail_output": str(detail_path),
        "pool_output": str(pool_path),
        "benchmark_raw_organic_files": [str(raw_paths[asin]) for asin in benchmark_asins],
        "benchmark_organic_summary_output": str(organic_summary_path),
        "visible_outputs": visible_outputs,
        "benchmark_organic_summary_record_count": len(summary_rows),
        "per_benchmark_observation_counts": per_benchmark_counts,
        "run_id": context.run_id,
        "run_timestamp": context.run_timestamp,
    }
    print(summary)
    return 0 if coverage_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())

