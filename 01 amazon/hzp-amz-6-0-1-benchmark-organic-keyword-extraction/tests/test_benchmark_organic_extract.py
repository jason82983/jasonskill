import csv
import tempfile
from pathlib import Path
import sys
import csv
import json
import re
import types

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import benchmark_organic_extract as module  # noqa: E402
from benchmark_organic_extract import (  # noqa: E402
    DATA_DUPLICATION_WARNING,
    SCHEMA_MAPPING_UNRESOLVED,
    extract_rows,
    filter_and_sort_records,
    _supply_demand_ratio,
)


FIELD_MAP = {
    "id": "Id",
    "keyword": "Keyword",
    "keyword_cn": "KeywordCn",
    "capacity": "MarketCapacity",
    "asin_quantity": "AsinQuantity",
    "organic_rank": "OrganicRank",
}


def test_filters_strict_boundaries_and_keeps_all_records():
    rows = [
        {"Id": 1, "Keyword": "a", "KeywordCn": "A", "MarketCapacity": 1000, "AsinQuantity": 100, "OrganicRank": 1},
        {"Id": 2, "Keyword": "b", "KeywordCn": "B", "MarketCapacity": 101, "AsinQuantity": 5, "OrganicRank": 5},
        {"Id": 3, "Keyword": "c", "KeywordCn": "C", "MarketCapacity": 100, "AsinQuantity": 2, "OrganicRank": 1},
        {"Id": 4, "Keyword": "d", "KeywordCn": "D", "MarketCapacity": 5000, "AsinQuantity": 10, "OrganicRank": 0},
        {"Id": 5, "Keyword": "e", "KeywordCn": "E", "MarketCapacity": 10000, "AsinQuantity": 10, "OrganicRank": None},
    ]
    values, summary = filter_and_sort_records(rows, field_map=FIELD_MAP)
    assert [row["Id"] for row in values] == [1, 2]
    assert summary["source_records"] == 5
    assert summary["matched_records"] == 2


def test_capacity_desc_then_rank_then_id_and_duplicate_warning():
    rows = [
        {"Id": 10, "Keyword": "same", "KeywordCn": "", "MarketCapacity": 10000, "AsinQuantity": 100, "OrganicRank": 15},
        {"Id": 2, "Keyword": "same", "KeywordCn": "", "MarketCapacity": 10000, "AsinQuantity": 80, "OrganicRank": 3},
        {"Id": 1, "Keyword": "other", "KeywordCn": "", "MarketCapacity": 5000, "AsinQuantity": 50, "OrganicRank": 1},
    ]
    values, summary = filter_and_sort_records(rows, field_map=FIELD_MAP)
    assert [row["Id"] for row in values] == [2, 10, 1]
    assert summary["status"] == DATA_DUPLICATION_WARNING


def test_schema_unresolved_fails_closed():
    values, summary = filter_and_sort_records([], field_map={})
    assert values == []
    assert summary["status"] == SCHEMA_MAPPING_UNRESOLVED


def test_csv_has_exact_seven_columns_and_count_matches():
    rows = [{"Id": 1, "Keyword": "baby proofing", "KeywordCn": "婴儿防护", "MarketCapacity": 50000, "AsinQuantity": 1000, "OrganicRank": 6}]
    with tempfile.TemporaryDirectory() as directory:
        result = extract_rows(rows, Path(directory) / "out.csv", field_map=FIELD_MAP)
        assert result["matched_records"] == result["csv_records"] == 1
        with open(result["output"], encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            assert next(reader) == ["Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名"]
            assert next(reader)[1] == "baby proofing"


def _one(capacity, rank, ident=1, keyword="kw", asin_quantity=10):
    return [{"Id": ident, "Keyword": keyword, "KeywordCn": "", "MarketCapacity": capacity, "AsinQuantity": asin_quantity, "OrganicRank": rank}]


def test_rank_one_capacity_1000_is_kept():
    values, _ = filter_and_sort_records(_one(1000, 1), field_map=FIELD_MAP)
    assert len(values) == 1


def test_rank_five_capacity_101_is_kept():
    values, _ = filter_and_sort_records(_one(101, 5), field_map=FIELD_MAP)
    assert len(values) == 1


def test_capacity_100_is_dropped_strictly():
    values, _ = filter_and_sort_records(_one(100, 1), field_map=FIELD_MAP)
    assert values == []


def test_rank_zero_is_dropped():
    values, _ = filter_and_sort_records(_one(5000, 0), field_map=FIELD_MAP)
    assert values == []


def test_null_rank_is_dropped():
    values, _ = filter_and_sort_records(_one(10000, None), field_map=FIELD_MAP)
    assert values == []


def test_rank_25_capacity_3000_is_kept():
    values, _ = filter_and_sort_records(_one(3000, 25), field_map=FIELD_MAP)
    assert len(values) == 1


def test_capacity_is_primary_sort_key():
    rows = _one(10000, 20, 1, "a") + _one(5000, 1, 2, "b")
    values, _ = filter_and_sort_records(rows, field_map=FIELD_MAP)
    assert [row["Id"] for row in values] == [1, 2]


def test_equal_capacity_uses_organic_rank_ascending():
    rows = _one(10000, 15, 10, "a") + _one(10000, 3, 2, "b")
    values, _ = filter_and_sort_records(rows, field_map=FIELD_MAP)
    assert [row["Id"] for row in values] == [2, 10]


def test_generic_baby_proofing_is_kept_without_ai_cleaning():
    values, _ = filter_and_sort_records(_one(50000, 6, keyword="baby proofing"), field_map=FIELD_MAP)
    assert values[0]["词"] == "baby proofing"


def test_all_matched_records_are_written():
    rows = [_one(1000 + i, 1, i, f"kw-{i}")[0] for i in range(17)]
    values, summary = filter_and_sort_records(rows, field_map=FIELD_MAP)
    assert summary["matched_records"] == len(values) == 17


def test_supply_demand_ratio_is_calculated_from_same_source_record():
    record = {"Id": 101, "Keyword": "wide walking shoes", "KeywordCn": "宽版步行鞋", "MarketCapacity": "27,865", "AsinQuantity": "8,000", "OrganicRank": 4}
    values, summary = filter_and_sort_records([record], field_map=FIELD_MAP)
    assert values[0]["Id"] == 101
    assert values[0]["竞争产品数"] == "8,000"
    assert values[0]["供需比"] == "3.4831"
    assert summary["metadata"] == {
        "COMPETING_PRODUCT_SOURCE_VIEW": "PickPwKView",
        "COMPETING_PRODUCT_SOURCE_FIELD": "AsinQuantity",
    }


def test_null_and_zero_asin_quantity_are_not_replaced_or_divided():
    rows = [
        {"Id": "null", "Keyword": "null count", "KeywordCn": "", "MarketCapacity": 2000, "AsinQuantity": None, "OrganicRank": 1},
        {"Id": "zero", "Keyword": "zero count", "KeywordCn": "", "MarketCapacity": 3000, "AsinQuantity": 0, "OrganicRank": 2},
    ]
    values, summary = filter_and_sort_records(rows, field_map=FIELD_MAP)
    by_id = {row["Id"]: row for row in values}
    assert by_id["null"]["竞争产品数"] is None and by_id["null"]["供需比"] is None
    assert by_id["zero"]["竞争产品数"] == 0 and by_id["zero"]["供需比"] is None
    assert summary["asin_quantity_zero_records"] == 1
    assert summary["warnings"] == [{"code": "ASIN_QUANTITY_ZERO", "record_ids": ["zero"]}]
    with tempfile.TemporaryDirectory() as directory:
        result = extract_rows(rows, Path(directory) / "null-zero.csv", field_map=FIELD_MAP)
        with open(result["output"], encoding="utf-8-sig", newline="") as handle:
            serialized = {row["Id"]: row for row in csv.DictReader(handle)}
        assert serialized["null"]["竞争产品数"] == serialized["null"]["供需比"] == ""
        assert serialized["zero"]["竞争产品数"] == "0" and serialized["zero"]["供需比"] == ""


def test_missing_market_capacity_keeps_ratio_empty():
    assert _supply_demand_ratio(None, 5) is None
    values, _ = filter_and_sort_records(_one("not available", 1, asin_quantity=5), field_map=FIELD_MAP)
    assert values == []  # Existing 601 filter excludes records without valid market capacity.


def test_runtime_requeries_live_erp_and_writes_timestamped_manifest(tmp_path, monkeypatch):
    product_root = tmp_path / "B2"
    output_dir = product_root / "06_SKILL分析报告" / "6-0-1_对标自然排名关键词提取"
    output_dir.mkdir(parents=True)
    stale = output_dir / "6-0-1_B2_ASIN_对标自然排名关键词_20260915_120000.csv"
    stale.write_text("Id,词,中文,市场容量,竞争产品数,供需比,自然排名\n1,stale term,旧,1000,10,100,1\n", encoding="utf-8-sig")
    identity = {
        "status": "IDENTITY_RESOLVED", "product_code": "B2",
        "benchmarks": [{"benchmark_code": "BM-A", "benchmark_asin": "ASIN-A", "benchmark_erp_pro_id": "500"}],
        "product_archive": str(product_root / "01_产品档案.md"),
    }
    monkeypatch.setattr(module, "resolve_product_code_identity", lambda *_args, **_kwargs: identity)
    calls = []
    fake_adapter_module = types.ModuleType("scripts.erp_keyword_adapter")

    class FakeERPKeywordAdapter:
        def __init__(self, _config_dir):
            pass

        def fetch(self, *_args, **_kwargs):
            calls.append("LIVE_QUERY")
            return {"status": "ERP_KEYWORD_DATA_READY", "rows": [{"raw_fields": {
                "Id": "99", "Keyword": "live term", "KeywordCn": "实时词",
                "KwId": "KW-99", "SearchVolume30": 2000, "AsinQuantity": 20, "RankOra": 2,
            }}]}

    fake_adapter_module.ERPKeywordAdapter = FakeERPKeywordAdapter
    monkeypatch.setitem(sys.modules, "scripts.erp_keyword_adapter", fake_adapter_module)
    monkeypatch.setattr(sys, "argv", ["benchmark_organic_extract", "--product-code", "B2", "--products-root", str(tmp_path)])
    assert module.main() == 0
    assert calls == ["LIVE_QUERY"]
    outputs = [path for path in output_dir.rglob("*.csv") if path != stale]
    assert len(outputs) == 4
    assert all(re.search(r"_\d{8}_\d{6}$", output.stem) for output in outputs)
    assert all(output.parent == output_dir for output in outputs)
    assert all(output.name.startswith("6-0-1_") for output in outputs)
    detail = next(path for path in outputs if "排名明细" in path.name)
    pool = next(path for path in outputs if "母池" in path.name)
    raw = next(path for path in outputs if "6-0-1_ASIN-A_关键词自然排名" in path.name)
    all_observations = next(path for path in outputs if "6-0-1_所有对标自然排名关键词" in path.name)
    with detail.open(encoding="utf-8-sig", newline="") as handle:
        assert next(csv.DictReader(handle))["Id"] == "KW-99"
    with pool.open(encoding="utf-8-sig", newline="") as handle:
        assert next(csv.DictReader(handle))["词"] == "live term"
    with all_observations.open(encoding="utf-8-sig", newline="") as handle:
        output_c = list(csv.DictReader(handle))
        assert list(output_c[0]) == list(module.ORGANIC_SUMMARY_COLUMNS)
        assert output_c[0]["ASIN"] == "ASIN-A"
        assert output_c[0]["产品编号"] == "500"
        assert output_c[0]["自然排名"] == "2"
    with raw.open(encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.DictReader(handle))
        assert len(raw_rows) == 1 and raw_rows[0]["对标ASIN"] == "ASIN-A"
    manifests = [json.loads(Path(str(output) + ".meta.json").read_text(encoding="utf-8")) for output in outputs]
    assert manifests[0]["Inputs"][0]["Input_Resolution_Method"] == "LIVE_QUERY"
    assert len({item["RUN_ID"] for item in manifests}) == 1
    assert manifests[0]["BenchmarkOrganicSummaryFile"] == all_observations.name
    assert manifests[0]["BenchmarkOrganicSummaryRecordCount"] == 1
    assert manifests[0]["BenchmarkRawOrganicFiles"] == [raw.name]
    assert manifests[0]["BenchmarkRawOrganicFileCount"] == 1
    assert manifests[0]["BenchmarkProductCodes"] == {"ASIN-A": "500"}
    assert manifests[0]["PerBenchmarkObservationCounts"] == {"ASIN-A": 1}


def _multi_rows(ranks=(3, 18, 76), *, capacities=None, competitor_counts=None):
    capacities = capacities or [20000] * len(ranks)
    competitor_counts = competitor_counts or [8000] * len(ranks)
    return [
        {
            "Benchmark_Code": f"BM-{index + 1}", "Benchmark_ASIN": f"ASIN-{index + 1}",
            "raw_fields": {
                "Id": f"VIEW-{index + 1}", "KwId": "KW-1", "Keyword": "sister birthday gifts",
                "KeywordCn": "姐妹生日礼物", "SearchVolume30": capacity,
                "AsinQuantity": competitors, "RankOra": rank,
            },
        }
        for index, (rank, capacity, competitors) in enumerate(zip(ranks, capacities, competitor_counts))
    ]


def test_three_benchmark_observations_create_one_market_fact():
    detail, pool, raw, output_c, summary = module.build_multi_benchmark_assets(
        _multi_rows(), keyword_entity_id_field="KwId", benchmark_product_codes={f"ASIN-{i}": f"ERP-{i}" for i in (1, 2, 3)}
    )
    assert summary["status"] == "OK" and summary["coverage"] == "PASS"
    assert len(detail) == len(output_c) == 3 and len(pool) == 1
    assert len(raw) == 3 and all(len(rows) == 1 for rows in raw.values())
    assert {row["产品编号"] for row in output_c} == {"ERP-1", "ERP-2", "ERP-3"}
    assert [row["ASIN"] for row in output_c] == ["ASIN-1", "ASIN-2", "ASIN-3"]
    assert [row["自然排名"] for row in detail] == [3, 18, 76]
    assert pool[0]["Id"] == "KW-1"
    assert pool[0]["对标覆盖数"] == 3
    assert pool[0]["最佳自然排名"] == 3
    assert pool[0]["自然排名中位数"] == 18
    assert (pool[0]["市场容量"], pool[0]["竞争产品数"], pool[0]["供需比"]) == (20000, 8000, "2.5000")


def test_partial_benchmark_coverage_counts_only_valid_observations():
    detail, pool, raw, output_c, summary = module.build_multi_benchmark_assets(
        _multi_rows((3, 18)), keyword_entity_id_field="KwId", benchmark_product_codes={"ASIN-1": "ERP-1", "ASIN-2": "ERP-2"}
    )
    assert summary["coverage"] == "PASS"
    assert len(detail) == len(output_c) == 2 and pool[0]["对标覆盖数"] == 2
    assert sum(len(rows) for rows in raw.values()) == len(output_c)


def test_market_fact_conflict_fails_closed():
    detail, pool, raw, output_c, summary = module.build_multi_benchmark_assets(
        _multi_rows(capacities=[20000, 19000, 20000]), keyword_entity_id_field="KwId", benchmark_product_codes={f"ASIN-{i}": f"ERP-{i}" for i in (1, 2, 3)}
    )
    assert detail == [] and pool == [] and raw == {} and output_c == [] and summary["status"] == "UNRESOLVED"
    assert module.KEYWORD_MARKET_FACT_CONFLICT in {item["code"] for item in summary["conflicts"]}


def test_distinct_kwids_with_same_text_are_not_text_deduplicated():
    rows = _multi_rows((3,)) + _multi_rows((7,))
    rows[1]["Benchmark_Code"] = "BM-2"
    rows[1]["Benchmark_ASIN"] = "ASIN-2"
    rows[1]["raw_fields"]["KwId"] = "KW-2"
    detail, pool, raw, output_c, summary = module.build_multi_benchmark_assets(rows, keyword_entity_id_field="KwId", benchmark_product_codes={"ASIN-1": "ERP-1", "ASIN-2": "ERP-2"})
    assert summary["status"] == "OK" and len(detail) == len(output_c) == len(pool) == 2
    assert {row["Id"] for row in pool} == {"KW-1", "KW-2"}


def test_output_c_preserves_same_keyword_once_per_benchmark_without_text_dedup():
    rows = _multi_rows((3, 18))
    detail, pool, raw, output_c, summary = module.build_multi_benchmark_assets(rows, keyword_entity_id_field="KwId", benchmark_product_codes={"ASIN-1": "49726", "ASIN-2": "51497"})
    assert summary["status"] == "OK"
    assert len(pool) == 1 and len(detail) == len(output_c) == 2
    assert [row["Id"] for row in output_c] == ["KW-1", "KW-1"]
    assert [row["ASIN"] for row in output_c] == ["ASIN-1", "ASIN-2"]
    assert [row["产品编号"] for row in output_c] == ["49726", "51497"]
    assert set(raw) == {"ASIN-1", "ASIN-2"}
    assert all(row["对标ASIN"] == asin for asin, rows in raw.items() for row in rows)


def test_output_c_requires_benchmark_product_code():
    rows = _multi_rows((3,))
    rows[0]["Benchmark_Code"] = ""
    _detail, _pool, raw, output_c, _summary = module.build_multi_benchmark_assets(rows, keyword_entity_id_field="KwId", benchmark_product_codes={"ASIN-1": ""})
    assert output_c == []
    assert raw == {}
    _detail, _pool, _raw, _summary_rows, missing_code = module.build_multi_benchmark_assets(rows, keyword_entity_id_field="KwId")
    assert missing_code["status"] == module.BENCHMARK_PRODUCT_CODE_MISSING


def test_output_c_write_failure_leaves_run_without_valid_metadata(tmp_path, monkeypatch):
    product_root = tmp_path / "B2"
    output_dir = product_root / "06_SKILL分析报告" / "6-0-1_对标自然排名关键词提取"
    identity = {
        "status": "IDENTITY_RESOLVED", "product_code": "B2",
        "benchmarks": [{"benchmark_code": "BM-A", "benchmark_asin": "ASIN-A", "benchmark_erp_pro_id": "500"}],
        "product_archive": str(product_root / "01_产品档案.md"),
    }
    monkeypatch.setattr(module, "resolve_product_code_identity", lambda *_args, **_kwargs: identity)
    fake_adapter_module = types.ModuleType("scripts.erp_keyword_adapter")

    class FakeERPKeywordAdapter:
        def __init__(self, _config_dir):
            pass

        def fetch(self, *_args, **_kwargs):
            return {"status": "ERP_KEYWORD_DATA_READY", "rows": [{"raw_fields": {
                "Id": "VIEW-1", "Keyword": "term", "KeywordCn": "词", "KwId": "KW-1",
                "SearchVolume30": 1200, "AsinQuantity": 80, "RankOra": 2,
            }}]}

    fake_adapter_module.ERPKeywordAdapter = FakeERPKeywordAdapter
    monkeypatch.setitem(sys.modules, "scripts.erp_keyword_adapter", fake_adapter_module)
    monkeypatch.setattr(sys, "argv", ["benchmark_organic_extract", "--product-code", "B2", "--products-root", str(tmp_path)])
    original_writer = module.write_asset_csv

    def fail_c(path, rows, columns):
        if "所有对标自然排名关键词" in Path(path).name:
            raise OSError("simulated C write failure")
        return original_writer(path, rows, columns)

    monkeypatch.setattr(module, "write_asset_csv", fail_c)
    try:
        module.main()
        assert False, "expected C write failure"
    except OSError as exc:
        assert "simulated C write failure" in str(exc)
    csvs = list(output_dir.rglob("*.csv"))
    assert len(csvs) == 3
    assert not list(output_dir.rglob("*.meta.json"))


if __name__ == "__main__":
    for test in (test_filters_strict_boundaries_and_keeps_all_records,
                 test_capacity_desc_then_rank_then_id_and_duplicate_warning,
                 test_schema_unresolved_fails_closed,
                 test_csv_has_exact_seven_columns_and_count_matches,
                 test_rank_one_capacity_1000_is_kept,
                 test_rank_five_capacity_101_is_kept,
                 test_capacity_100_is_dropped_strictly,
                 test_rank_zero_is_dropped,
                 test_null_rank_is_dropped,
                 test_rank_25_capacity_3000_is_kept,
                 test_capacity_is_primary_sort_key,
                 test_equal_capacity_uses_organic_rank_ascending,
                 test_generic_baby_proofing_is_kept_without_ai_cleaning,
                 test_all_matched_records_are_written,
                 test_supply_demand_ratio_is_calculated_from_same_source_record,
                 test_null_and_zero_asin_quantity_are_not_replaced_or_divided,
                 test_missing_market_capacity_keeps_ratio_empty):
        test()
    print("6-0-1 extraction tests: PASS")
