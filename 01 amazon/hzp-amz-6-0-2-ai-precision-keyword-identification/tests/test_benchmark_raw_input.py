from datetime import datetime
from pathlib import Path
import csv
import importlib.util
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location("dual_precision_csv_benchmark", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)
from scripts.stage6_artifact_contract import make_artifact_metadata, new_run_context, write_metadata_sidecar


def _pool_row(ident="KW-101", keyword="sister sculpture", chinese="姐妹雕塑", volume="1200", competitors="80", ratio="15.0000", coverage="3", best="3", median="18"):
    return {
        "Id": ident, "词": keyword, "中文": chinese, "市场容量": volume,
        "竞争产品数": competitors, "供需比": ratio, "对标覆盖数": coverage,
        "最佳自然排名": best, "自然排名中位数": median,
    }


def _write_csv(path: Path, rows, headers=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers or module.BENCHMARK_RAW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest(path: Path, stamp: str, count: int, identity: str, schema, outputs, extra):
    context = new_run_context(
        "6-0-1", module.SIX_0_1_SKILL_ID, "B2",
        now=datetime.strptime(stamp, "%Y%m%d_%H%M%S").astimezone(),
    )
    metadata = make_artifact_metadata(
        context, identity, run_status="FULL_SUCCESS", schema=schema, record_count=count,
        output_assets=[str(item) for item in outputs],
        extra={"Benchmark_Count": 3, "Benchmark_Codes": ["BM-A", "BM-B", "BM-C"],
               "Benchmark_ASINs": ["ASIN-A", "ASIN-B", "ASIN-C"], "BenchmarkASINs": ["ASIN-A", "ASIN-B", "ASIN-C"],
               "Keyword_Entity_ID_Field": "KwId", "Benchmark_ERP_ProIds": ["500", "501", "502"], **extra},
    )
    write_metadata_sidecar(path, metadata)


def _write_pool(root: Path, rows, stamp="20260915_120000"):
    directory = root / "06_SKILL分析报告" / module.BENCHMARK_RAW_OUTPUT_DIR
    path = directory / stamp / f"6-0-1_B2_对标关键词母池_{stamp}.csv"
    detail_schema = ["Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标编码", "对标ASIN", "自然排名"]
    c_schema = detail_schema + ["ASIN", "产品编号"]
    detail_path = path.parent / f"6-0-1_B2_多对标关键词排名明细_{stamp}.csv"
    c_path = path.parent / f"所有对标自然排名关键词汇总_{stamp}.csv"
    asins = ["ASIN-A", "ASIN-B", "ASIN-C"]
    codes = ["BM-A", "BM-B", "BM-C"]
    detail_rows, c_rows = [], []
    for row in rows:
        for code, asin, rank in zip(codes, asins, (3, 18, 30)):
            item = {"Id": row["Id"], "词": row["词"], "中文": row["中文"], "市场容量": row["市场容量"],
                    "竞争产品数": row["竞争产品数"], "供需比": row["供需比"], "对标编码": code,
                    "对标ASIN": asin, "自然排名": rank}
            detail_rows.append(item)
            c_rows.append({**item, "ASIN": asin, "产品编号": str(500 + asins.index(asin))})
    _write_csv(path, rows)
    _write_csv(detail_path, detail_rows, detail_schema)
    _write_csv(c_path, c_rows, c_schema)
    raw_paths = [path.parent / f"{asin}+关键词自然排名_{stamp}.csv" for asin in asins]
    for asin, raw_path in zip(asins, raw_paths):
        _write_csv(raw_path, [row for row in detail_rows if row["对标ASIN"] == asin], detail_schema)
    outputs = [detail_path, path, *raw_paths, c_path]
    counts = {asin: len(rows) for asin in asins}
    metadata_assets = [
        (detail_path, "BENCHMARK_KEYWORD_DETAIL", detail_schema, len(detail_rows)),
        (path, module.SIX_0_1_REPORT_IDENTITY, list(module.BENCHMARK_RAW_COLUMNS), len(rows)),
        *[(raw_path, f"BENCHMARK_KEYWORD_RAW_{asin}", detail_schema, counts[asin]) for asin, raw_path in zip(asins, raw_paths)],
        (c_path, "BENCHMARK_KEYWORD_ALL_OBSERVATIONS", c_schema, len(c_rows)),
    ]
    extra = {
        "BenchmarkRawOrganicFiles": [raw_path.name for raw_path in raw_paths],
        "BenchmarkRawOrganicFileCount": len(asins), "BenchmarkOrganicSummaryFile": c_path.name,
        "BenchmarkOrganicSummaryRecordCount": len(c_rows), "BenchmarkProductCodes": {asin: str(500 + index) for index, asin in enumerate(asins)},
        "PerBenchmarkObservationCounts": counts,
    }
    for asset_path, identity, schema, count in metadata_assets:
        _write_manifest(asset_path, stamp, count, identity, schema, outputs, extra)
    return path


def test_resolver_accepts_unique_keyword_pool_and_keeps_kwid_separate_from_record_id(tmp_path):
    path = _write_pool(tmp_path, [_pool_row()])
    resolved = module.resolve_benchmark_raw_csvs(tmp_path, product_code="B2")
    assert resolved["status"] == "BENCHMARK_RAW_READY"
    assert resolved["files"] == [str(path)]
    row = resolved["rows"][0]
    assert row["Id"] == row["keyword_entity_id"] == "KW-101"
    assert row["keyword_entity_id_status"] == "USER_CONFIRMED_STABLE_ACROSS_PROID"
    assert row["record_id"] is None
    assert row["record_id_status"] == module.ERP_KEYWORD_RECORD_ID_UNCONFIRMED
    assert row["SearchVolume30"] == "1200"
    assert row["对标覆盖数"] == "3" and row["最佳自然排名"] == "3" and row["自然排名中位数"] == "18"


def test_resolver_selects_latest_valid_pool_by_metadata_not_mtime(tmp_path):
    old = _write_pool(tmp_path, [_pool_row("KW-1", "old term")], "20260915_140000")
    new = _write_pool(tmp_path, [_pool_row("KW-2", "new term")], "20260915_150000")
    os.utime(old, (time.time() + 200, time.time() + 200))
    os.utime(new, (time.time() - 200, time.time() - 200))
    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["status"] == module.SIX_0_1_KEYWORD_OUTPUT_READY
    assert resolved["file"] == str(new)
    assert [row["Id"] for row in resolved["rows"]] == ["KW-2"]


def test_wrong_schema_candidate_is_skipped_and_latest_valid_pool_is_used(tmp_path):
    valid = _write_pool(tmp_path, [_pool_row()], "20260915_120000")
    bad = valid.parent / "6-0-1_B2_对标关键词母池_20260915_130000.csv"
    _write_csv(bad, [{"Id": "KW-X", "词": "bad"}], headers=["Id", "词"])
    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["status"] == module.SIX_0_1_KEYWORD_OUTPUT_READY
    assert resolved["file"] == str(valid)
    assert any(item["status"] == "SCHEMA_MISMATCH" for item in resolved["invalid_files"])


def test_pool_without_kwid_identity_metadata_is_rejected(tmp_path):
    path = _write_pool(tmp_path, [_pool_row()])
    manifest_path = path.with_suffix(path.suffix + ".meta.json")
    metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata.pop("Keyword_Entity_ID_Field", None)
    manifest_path.write_text(json.dumps(metadata), encoding="utf-8")
    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["status"] == "NO_VALID_UPSTREAM_REPORT"
    assert any(item["status"] == "KEYWORD_ENTITY_ID_METADATA_UNCONFIRMED" for item in resolved["invalid_files"])


def test_602_pool_to_ai_view_judges_one_kwid_once_and_keeps_rank_as_reality_evidence(tmp_path):
    _write_pool(tmp_path, [_pool_row("KW-1", "sister sculpture"), _pool_row("KW-2", "sister figurine")])
    views = module.build_dual_views_from_601_output(tmp_path, product_code="B2")
    assert views["status"] == "READY" and views["source_row_count"] == 2
    assert [row["Id"] for row in views["ai_blind_rows"]] == ["KW-1", "KW-2"]
    assert all(row["record_id"] is None for row in views["ai_blind_rows"])
    reality = views["ai_blind_rows"][0]["Benchmark_Reality_Evidence"]
    assert reality == {"对标覆盖数": "3", "最佳自然排名": "3", "自然排名中位数": "18"}
    prompt_material = str(views["ai_blind_rows"])
    assert "市场容量" not in prompt_material and "竞争产品数" not in prompt_material and "供需比" not in prompt_material


def test_benchmark_candidate_pool_uses_pool_without_second_erp_query(tmp_path):
    _write_pool(tmp_path, [_pool_row()])
    resolved = module.resolve_benchmark_raw_csvs(tmp_path, product_code="B2")
    candidates = module.build_keyword_candidate_pool(
        [], product_code="B2", erp_pro_id=900,
        benchmark_erp_pro_ids=[500, 501, 502], benchmark_raw_input=resolved,
    )
    assert candidates["mode"] == module.BENCHMARK_FALLBACK
    assert len(candidates["candidates"]) == 1
    assert candidates["candidates"][0]["keyword_entity_id"] == "KW-101"
    assert candidates["candidates"][0]["record_id"] is None
    assert candidates["candidates"][0]["record_id_status"] == module.ERP_KEYWORD_RECORD_ID_UNCONFIRMED


def test_missing_pool_fails_closed_without_erp_fallback(tmp_path):
    resolved = module.resolve_benchmark_raw_csvs(tmp_path, product_code="B2")
    assert resolved["status"] == module.BENCHMARK_RAW_NOT_FOUND
    candidates = module.build_keyword_candidate_pool(
        [], product_code="B2", erp_pro_id=900, benchmark_raw_input=resolved,
    )
    assert candidates["status"] == module.BENCHMARK_RAW_NOT_FOUND
    assert candidates["candidates"] == []
