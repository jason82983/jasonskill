from datetime import datetime
from pathlib import Path
import csv
import importlib.util
import json
import os
import sys
import time
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location("dual_precision_csv_benchmark", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)
from scripts.stage6_artifact_contract import make_artifact_metadata, new_run_context, write_metadata_sidecar


def _observation(ident="KW-101", keyword="sister sculpture", *, product="BM-A", asin="ASIN-A", rank="3", chinese="姐妹雕塑", volume="1200", competitors="80", ratio="15.0000"):
    return {"所属产品编号": product, "对标ASIN": asin, "Id": ident, "词": keyword, "中文": chinese,
            "市场容量": volume, "竞争产品数": competitors, "供需比": ratio, "自然排名": str(rank)}


def _write_csv(path: Path, rows, headers):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _write_601(root: Path, observations, stamp="20260915_120000"):
    folder = root / "06_SKILL分析报告" / module.BENCHMARK_RAW_OUTPUT_DIR / stamp
    detail_schema = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标编号", "对标ASIN", "自然排名")
    pool_schema = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数")
    summary_schema = detail_schema + ("ASIN", "产品编号")
    asins = sorted({row["对标ASIN"] for row in observations})
    product_codes = {row["对标ASIN"]: row["所属产品编号"] for row in observations}
    detail_rows = [{"Id": row["Id"], "词": row["词"], "中文": row["中文"], "市场容量": row["市场容量"],
        "竞争产品数": row["竞争产品数"], "供需比": row["供需比"], "对标编号": f"BM-{index + 1}",
        "对标ASIN": row["对标ASIN"], "自然排名": row["自然排名"]} for index, row in enumerate(observations)]
    summary_rows = [{**row, "ASIN": row["对标ASIN"], "产品编号": product_codes[row["对标ASIN"]]} for row in detail_rows]
    grouped = {}
    for row in observations:
        grouped.setdefault(row["Id"], []).append(row)
    pool_rows = []
    for ident, rows in grouped.items():
        ranks = [float(row["自然排名"]) for row in rows]
        first = rows[0]
        pool_rows.append({"Id": ident, "词": first["词"], "中文": first["中文"], "市场容量": first["市场容量"],
            "竞争产品数": first["竞争产品数"], "供需比": first["供需比"], "对标覆盖数": len(rows),
            "最佳自然排名": min(ranks), "自然排名中位数": median(ranks)})
    detail = folder / f"6-0-1_B2_多对标关键词排名明细_{stamp}.csv"
    pool = folder / f"6-0-1_B2_对标关键词母池_{stamp}.csv"
    all_observations = folder / f"所有对标自然排名关键词汇总_{stamp}.csv"
    _write_csv(detail, detail_rows, detail_schema)
    _write_csv(pool, pool_rows, pool_schema)
    raw_paths = {asin: folder / f"{asin}+关键词自然排名_{stamp}.csv" for asin in asins}
    for asin, path in raw_paths.items():
        _write_csv(path, [row for row in detail_rows if row["对标ASIN"] == asin], detail_schema)
    _write_csv(all_observations, summary_rows, summary_schema)
    outputs = [detail, pool, *[raw_paths[asin] for asin in asins], all_observations]
    raw_counts = {asin: sum(1 for row in summary_rows if row["ASIN"] == asin) for asin in asins}
    context = new_run_context("6-0-1", module.SIX_0_1_SKILL_ID, "B2", now=datetime.strptime(stamp, "%Y%m%d_%H%M%S").astimezone())
    benchmark_codes = {asin: f"BENCH-{index + 1}" for index, asin in enumerate(asins)}
    extra = {"BenchmarkASINs": asins, "Benchmark_ASINs": asins,
        "BenchmarkProductCodes": product_codes,
        "BenchmarkRawOrganicFileCount": len(asins), "BenchmarkRawOrganicFiles": [raw_paths[asin].name for asin in asins],
        "BenchmarkOrganicSummaryFile": all_observations.name, "BenchmarkOrganicSummaryRecordCount": len(summary_rows),
        "PerBenchmarkObservationCounts": raw_counts, "Keyword_Entity_ID_Field": "KwId",
        "OutputCFile": all_observations.name, "OutputCRecordCount": len(summary_rows),
        "Benchmark_Count": len(asins), "Benchmark_Codes": [benchmark_codes[asin] for asin in asins],
        "Benchmark_ERP_ProIds": [product_codes[asin] for asin in asins]}
    metadata_assets = [(detail, "BENCHMARK_KEYWORD_DETAIL", detail_schema, detail_rows),
        (pool, "BENCHMARK_KEYWORD_POOL", pool_schema, pool_rows)]
    metadata_assets.extend((raw_paths[asin], f"BENCHMARK_KEYWORD_RAW_{asin}", detail_schema,
        [row for row in detail_rows if row["对标ASIN"] == asin]) for asin in asins)
    metadata_assets.append((all_observations, "BENCHMARK_KEYWORD_ALL_OBSERVATIONS", summary_schema, summary_rows))
    for path, identity, schema, rows in metadata_assets:
        metadata = make_artifact_metadata(context, identity, run_status="FULL_SUCCESS", schema=schema,
            record_count=len(rows), output_assets=[str(item) for item in outputs], extra=extra)
        write_metadata_sidecar(path, metadata)
    return all_observations


def test_resolver_reads_601_all_observation_output_and_passes_identity_through(tmp_path):
    path = _write_601(tmp_path, [_observation(product="BM-A"), _observation(product="BM-B", asin="ASIN-B", rank="18")])
    resolved = module.resolve_benchmark_raw_csvs(tmp_path, product_code="B2")
    assert resolved["status"] == "BENCHMARK_RAW_READY"
    assert resolved["files"] == [str(path)]
    assert len(resolved["rows"]) == 2
    row = resolved["rows"][1]
    assert (row["所属产品编号"], row["对标ASIN"], row["Id"], row["自然排名"]) == ("BM-B", "ASIN-B", "KW-101", "18")
    assert row["keyword_entity_id"] == "KW-101"
    assert row["record_id"] is None
    assert row["record_id_status"] == module.ERP_KEYWORD_RECORD_ID_UNCONFIRMED


def test_resolver_selects_latest_valid_observation_package_not_by_mtime(tmp_path):
    old = _write_601(tmp_path, [_observation("KW-1", "old term")], "20260915_140000")
    new = _write_601(tmp_path, [_observation("KW-2", "new term")], "20260915_150000")
    os.utime(old, (time.time() + 200, time.time() + 200))
    os.utime(new, (time.time() - 200, time.time() - 200))
    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["status"] == module.SIX_0_1_KEYWORD_OUTPUT_READY
    assert resolved["file"] == str(new)
    assert [row["Id"] for row in resolved["rows"]] == ["KW-2"]


def test_resolver_orders_valid_batches_by_run_timestamp(tmp_path):
    older = _write_601(tmp_path, [_observation("KW-1", "older term")], "20260915_140000")
    newer = _write_601(tmp_path, [_observation("KW-2", "newer term")], "20260915_150000")
    older_meta_path = older.with_suffix(older.suffix + ".meta.json")
    older_meta = json.loads(older_meta_path.read_text(encoding="utf-8"))
    older_meta["Generated_At"] = "2026-09-20T15:00:00+08:00"
    older_meta_path.write_text(json.dumps(older_meta), encoding="utf-8")
    newer_meta_path = newer.with_suffix(newer.suffix + ".meta.json")
    newer_meta = json.loads(newer_meta_path.read_text(encoding="utf-8"))
    newer_meta["Generated_At"] = "2026-09-15T14:00:00+08:00"
    newer_meta_path.write_text(json.dumps(newer_meta), encoding="utf-8")

    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["run_timestamp"] == "20260915_150000"
    assert resolved["file"] == str(newer)


def test_resolver_rejects_mother_pool_and_timestampless_observation_csv(tmp_path):
    directory = tmp_path / "06_SKILL分析报告" / module.BENCHMARK_RAW_OUTPUT_DIR
    directory.mkdir(parents=True)
    (directory / "6-0-1_B2_对标关键词母池_20260915_150000.csv").write_text("Id,词\n", encoding="utf-8")
    (directory / "所有对标自然排名关键词汇总.csv").write_text("Id,词\n", encoding="utf-8")
    assert module.BENCHMARK_RAW_FILENAME_RE.fullmatch("6-0-1_所有对标自然排名关键词_20260915_150000.csv")
    assert not module.BENCHMARK_RAW_FILENAME_RE.fullmatch("所有对标自然排名关键词汇总.csv")

    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["status"] == module.SIX_0_1_KEYWORD_INPUT_NOT_FOUND


def test_wrong_schema_candidate_is_skipped_and_latest_valid_observation_package_is_used(tmp_path):
    valid = _write_601(tmp_path, [_observation()], "20260915_120000")
    bad = valid.parent.parent / "20260915_130000" / "6-0-1_B2_所有对标自然排名关键词_20260915_130000.csv"
    _write_csv(bad, [{"Id": "KW-X", "词": "bad"}], headers=("Id", "词"))
    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["status"] == module.SIX_0_1_KEYWORD_OUTPUT_READY
    assert resolved["file"] == str(valid)
    assert resolved["invalid_files"]
    assert resolved["input_resolution_method"] == "LATEST_INVALID_FALLBACK_USED"


def test_observation_input_without_kwid_identity_metadata_is_rejected(tmp_path):
    path = _write_601(tmp_path, [_observation()])
    metadata_path = path.with_suffix(path.suffix + ".meta.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.pop("Keyword_Entity_ID_Field", None)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    resolved = module.resolve_latest_601_keyword_output(tmp_path, product_code="B2")
    assert resolved["status"] == "NO_VALID_UPSTREAM_REPORT"
    assert any(item["status"] == "KEYWORD_ENTITY_ID_METADATA_UNCONFIRMED" for item in resolved["invalid_files"])


def test_602_builds_one_ai_judgment_unit_with_aggregated_rank_evidence(tmp_path):
    _write_601(tmp_path, [_observation(product="BM-A", rank="3"), _observation(product="BM-B", asin="ASIN-B", rank="18")])
    views = module.build_dual_views_from_601_output(tmp_path, product_code="B2")
    assert views["status"] == "READY" and views["source_row_count"] == 2 and views["unique_keyword_count"] == 1
    assert len(views["ai_blind_rows"]) == 1
    reality = views["ai_blind_rows"][0]["Benchmark_Reality_Evidence"]
    assert reality["Benchmark_Coverage_Count"] == 2
    assert reality["Best_Benchmark_Organic_Rank"] == 3.0
    assert reality["Median_Benchmark_Organic_Rank"] == 10.5
    prompt_material = str(views["ai_blind_rows"])
    assert "市场容量" not in prompt_material and "竞争产品数" not in prompt_material and "供需比" not in prompt_material


def test_benchmark_candidate_pool_uses_resolved_observation_without_second_erp_query(tmp_path):
    _write_601(tmp_path, [_observation(product="BM-A", rank="3"), _observation(product="BM-B", asin="ASIN-B", rank="18")])
    resolved = module.resolve_benchmark_raw_csvs(tmp_path, product_code="B2")
    candidates = module.build_keyword_candidate_pool([], product_code="B2", erp_pro_id=900,
        benchmark_erp_pro_ids=[500], benchmark_raw_input=resolved)
    assert candidates["mode"] == module.BENCHMARK_FALLBACK
    assert len(candidates["candidates"]) == 1
    assert candidates["candidates"][0]["keyword_entity_id"] == "KW-101"
    assert candidates["candidates"][0]["record_id"] is None
    reality = candidates["benchmark_evidence"]["sister sculpture"]
    assert reality["Benchmark_Count"] == 2
    assert reality["Best_Benchmark_Organic_Rank"] == 3
    assert reality["Median_Benchmark_Organic_Rank"] == 10.5


def test_missing_observation_package_fails_closed_without_erp_fallback(tmp_path):
    resolved = module.resolve_benchmark_raw_csvs(tmp_path, product_code="B2")
    assert resolved["status"] == module.BENCHMARK_RAW_NOT_FOUND
    candidates = module.build_keyword_candidate_pool([], product_code="B2", erp_pro_id=900, benchmark_raw_input=resolved)
    assert candidates["status"] == module.BENCHMARK_RAW_NOT_FOUND
    assert candidates["candidates"] == []
