from pathlib import Path
import csv
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("broad", ROOT / "scripts" / "broad_seed_cluster.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)
ID, KW, CN, VOL, COMP_COUNT, RATIO, COVERAGE, BEST_RANK, MEDIAN_RANK, PREC, REASON = module.INPUT_COLUMNS
HIGH = "高度精准"
AVG_COMP = module.SUMMARY_COLUMNS[6]
INTENT_RATIO = module.SUMMARY_COLUMNS[7]
DIRECT_COUNT = module.SUMMARY_COLUMNS[8]


def row(record_id, keyword, volume, cn="", precision=HIGH, competing="50", ratio="20.0000"):
    return {ID: record_id, KW: keyword, CN: cn, VOL: str(volume), COMP_COUNT: competing, RATIO: ratio,
            COVERAGE: "1", BEST_RANK: "1", MEDIAN_RANK: "1", PREC: precision,
            REASON: "该关键词的购买意图与产品高度匹配"}


def _observation(source, index):
    return {
        "所属产品编号": "BM-1", "对标ASIN": "ASIN-1", "Id": source[ID],
        "词": source[KW], "中文": source[CN], "市场容量": source[VOL],
        "竞争产品数": source[COMP_COUNT], "供需比": source[RATIO],
        "自然排名": source[BEST_RANK], "精准度": source[PREC], "精准原因": source[REASON],
    }


def write_602_package(root, rows, stamp="20260916_184400", *, status="VALID", include_ai=True,
                      include_high=True, include_deduplicated=True, observations=None,
                      high_rows=None, deduplicated_rows=None):
    rows = list(rows)
    observations = list(observations) if observations is not None else [_observation(source, 0) for source in rows]
    high_rows = list(high_rows) if high_rows is not None else [source for source in observations if source["精准度"] == HIGH]
    deduplicated_rows = list(deduplicated_rows) if deduplicated_rows is not None else rows
    paths = module.input_paths(root, "B2", stamp)
    benchmark_codes = list(dict.fromkeys(str(row["所属产品编号"]) for row in observations)) or ["BM-1"]
    paths["benchmarks"] = {code: paths["ai"].parent / f"6-0-2_{code}_高度精准词_{stamp}.csv" for code in benchmark_codes}
    all_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated")] + list(paths["benchmarks"].values())
    paths["ai"].parent.mkdir(parents=True, exist_ok=True)
    if include_ai:
        module.write_csv(paths["ai"], observations, module.OBSERVATION_COLUMNS)
    if include_high:
        module.write_csv(paths["high_precision"], high_rows, module.OBSERVATION_COLUMNS)
    if include_deduplicated:
        module.write_csv(paths["deduplicated"], deduplicated_rows, module.INPUT_COLUMNS)
    for code, path in paths["benchmarks"].items():
        module.write_csv(path, [row for row in high_rows if str(row["所属产品编号"]) == code], module.OBSERVATION_COLUMNS)
    unique_input_count = len({module.normalize_broad_keyword(source["词"]) for source in observations})
    record_counts = {
        "Input Record Count": len(observations), "Input Observation Count": len(observations),
        "Input Unique Keyword Count": unique_input_count, "AI Record Count": len(observations),
        "High Precision Record Count": len(high_rows),
        "Unique High Precision Keyword Count": len(deduplicated_rows),
        "Benchmark File Count": len(benchmark_codes),
    }
    manifest = {
        "SkillId": "hzp-amz-6-0-2-ai-precision-keyword-identification",
        "Current Product": "B2", "RUN_ID": stamp, "RUN_TIMESTAMP": stamp,
        "GeneratedAt": "2026-09-16T18:44:00+08:00", "Input Source": "test fixture",
        "Input Skill": "hzp-amz-6-0-1-benchmark-organic-keyword-extraction",
        "Input Run ID": "20260916_160000", "Input RUN_TIMESTAMP": "20260916_160000",
        "Input Folder": str(root / "source-run"), "Input File": str(root / "source-run" / "source.csv"),
        "Product Text Input": {"path": str(root / "product.txt"), "size_bytes": 1, "sha256": "abc"},
        "Input Record Count": len(observations), "Input Observation Count": len(observations),
        "Input Unique Keyword Count": unique_input_count,
        "Output Folder": str(paths["ai"].parent), "Output Files": [path.name for path in all_paths],
        "Benchmark Count": len(benchmark_codes), "Expected Benchmark Count": len(benchmark_codes),
        "Benchmark Product Codes": benchmark_codes,
        "Benchmark Identities": {code: {"对标编码": f"CODE-{code}", "对标ASIN": next((row["对标ASIN"] for row in observations if row["所属产品编号"] == code), f"ASIN-{code}")} for code in benchmark_codes},
        "PerBenchmarkInputObservationCount": {code: sum(row["所属产品编号"] == code for row in observations) for code in benchmark_codes},
        "PerBenchmarkHighPrecisionRecordCount": {code: sum(row["所属产品编号"] == code for row in high_rows) for code in benchmark_codes},
        "Expected Benchmark Files": [paths["benchmarks"][code].name for code in benchmark_codes],
        "GeneratedBenchmarkFiles": [paths["benchmarks"][code].name for code in benchmark_codes],
        "Record Counts": record_counts,
        "Output Record Counts": {"AI Precision Observation Count": len(observations),
                                 "High Precision Observation Count": len(high_rows),
                                 "Unique High Precision Keyword Count": len(deduplicated_rows),
                                 "Benchmark File Count": len(benchmark_codes)},
        "Run Status": status,
    }
    (paths["ai"].parent / f"{module.INPUT_602_MANIFEST_PREFIX}{stamp}.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return paths


def semantic_mapper(mapping):
    return lambda record: mapping[record[KW]]


def test_same_intent_maps_to_one_canonical_and_sums_programmatically():
    rows = [row("1", "sister birthday gifts", 18000), row("2", "gift for sister", 12000), row("3", "big sister gift", 4000), row("4", "best friend gifts", 9000)]
    mapping = {"sister birthday gifts": ("sister gifts", "cn1"), "gift for sister": ("sister gifts", "cn1"), "big sister gift": ("sister gifts", "cn1"), "best friend gifts": ("best friend gifts", "cn2")}
    mapped = module.build_mapping_rows(rows, semantic_mapper(mapping))
    summary = module.aggregate_mapping_rows(mapped)
    assert mapped[0][module.MAPPING_COLUMNS[7]] == mapped[1][module.MAPPING_COLUMNS[7]] == mapped[2][module.MAPPING_COLUMNS[7]] == "sister gifts"
    assert summary[0][module.SUMMARY_COLUMNS[0]] == "sister gifts" and summary[0][module.SUMMARY_COLUMNS[1]] == "cn1" and summary[0][module.SUMMARY_COLUMNS[2]] == "L1" and summary[0][module.SUMMARY_COLUMNS[4]] == 34000 and summary[0][module.SUMMARY_COLUMNS[5]] == 34000 and summary[0][AVG_COMP] == 50 and summary[0][INTENT_RATIO] == 680 and summary[0][DIRECT_COUNT] == 3
    assert summary[1][module.SUMMARY_COLUMNS[0]] == "best friend gifts"


def test_parent_child_intents_keep_occasion_and_recursive_volume():
    rows = [row("1", "gift for sister", 15000), row("2", "sister birthday gifts", 20000), row("3", "birthday gifts for sister", 10000), row("4", "sister christmas gifts", 5000)]
    mapping = {
        "gift for sister": {"精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物"},
        "sister birthday gifts": {"精准泛词": "sister birthday gifts", "精准泛词中文": "姐妹生日礼物", "父精准泛词": "sister gifts"},
        "birthday gifts for sister": {"精准泛词": "sister birthday gifts", "精准泛词中文": "姐妹生日礼物", "父精准泛词": "sister gifts"},
        "sister christmas gifts": {"精准泛词": "sister christmas gifts", "精准泛词中文": "姐妹圣诞礼物", "父精准泛词": "sister gifts"},
    }
    summary = module.aggregate_mapping_rows(module.build_mapping_rows(rows, semantic_mapper(mapping)))
    parent = next(item for item in summary if item[module.SUMMARY_COLUMNS[0]] == "sister gifts")
    child = next(item for item in summary if item[module.SUMMARY_COLUMNS[0]] == "sister birthday gifts")
    assert parent[module.SUMMARY_COLUMNS[2]] == "L1" and parent[module.SUMMARY_COLUMNS[4]] == 15000 and parent[module.SUMMARY_COLUMNS[5]] == 50000
    assert parent[AVG_COMP] == 50 and parent[INTENT_RATIO] == 1000
    assert child[module.SUMMARY_COLUMNS[2]] == "L2" and child[module.SUMMARY_COLUMNS[3]] == "sister gifts" and child[module.SUMMARY_COLUMNS[4]] == 30000 and child[module.SUMMARY_COLUMNS[5]] == 30000 and child[AVG_COMP] == 50 and child[INTENT_RATIO] == 600


def test_parent_cycle_is_rejected():
    rows = [row("1", "a gift", 10), row("2", "b gift", 20)]
    mapping = {"a gift": {"精准泛词": "a gifts", "父精准泛词": "b gifts"}, "b gift": {"精准泛词": "b gifts", "父精准泛词": "a gifts"}}
    try:
        module.aggregate_mapping_rows(module.build_mapping_rows(rows, semantic_mapper(mapping)))
    except ValueError as exc:
        assert module.PARENT_CYCLE_DETECTED in str(exc)
    else:
        raise AssertionError("parent cycle must be rejected")


def test_orphan_parent_is_rejected():
    rows = [row("1", "a gift", 10)]
    mapping = {"a gift": {"精准泛词": "a gifts", "父精准泛词": "missing gifts"}}
    try:
        module.aggregate_mapping_rows(module.build_mapping_rows(rows, semantic_mapper(mapping)))
    except ValueError as exc:
        assert module.ORPHAN_PARENT_INTENT in str(exc)
    else:
        raise AssertionError("orphan parent must be rejected")


def test_different_relationship_intents_do_not_merge():
    rows = [row("1", "sister gifts", 100), row("2", "best friend gifts", 200)]
    mapped = module.build_mapping_rows(rows, semantic_mapper({"sister gifts": ("sister gifts", "cn1"), "best friend gifts": ("best friend gifts", "cn2")}))
    assert {r[module.MAPPING_COLUMNS[7]] for r in mapped} == {"sister gifts", "best friend gifts"}


def test_mapping_preserves_all_ids_and_same_keyword_multiple_ids():
    rows = [row("1001", "sister gifts", 10), row("1002", "sister gifts", 20)]
    mapped = module.build_mapping_rows(rows, semantic_mapper({"sister gifts": ("sister gifts", "cn1")}))
    assert [r[ID] for r in mapped] == ["1001", "1002"]
    assert module.aggregate_mapping_rows(mapped)[0][DIRECT_COUNT] == 2
    assert module.aggregate_mapping_rows(mapped)[0][module.SUMMARY_COLUMNS[4]] == 30


def test_competitor_fields_pass_through_without_intent_aggregation():
    rows = [row("1", "sister gifts", 100, competing="12", ratio="8.3333"), row("2", "gift for sister", 50, competing="20", ratio="2.5000")]
    mapping = {"sister gifts": ("sister gifts", "cn1"), "gift for sister": ("sister gifts", "cn1")}
    mapped = module.build_mapping_rows(rows, semantic_mapper(mapping))
    assert [(item[COMP_COUNT], item[RATIO]) for item in mapped] == [("12", "8.3333"), ("20", "2.5000")]
    summary = module.aggregate_mapping_rows(mapped)
    assert tuple(summary[0]) == module.SUMMARY_COLUMNS
    assert summary[0][module.SUMMARY_COLUMNS[4]] == 150
    assert summary[0][AVG_COMP] == 16 and summary[0][INTENT_RATIO] == 9.375


def test_partial_missing_volume_is_unavailable_and_sorted_last():
    rows = [row("1", "sister gifts", 100), row("2", "best friend gifts", "DATA_NOT_AVAILABLE")]
    mapped = module.build_mapping_rows(rows, semantic_mapper({"sister gifts": ("sister gifts", "cn1"), "best friend gifts": ("best friend gifts", "cn2")}))
    summary = module.aggregate_mapping_rows(mapped)
    assert summary[0][module.SUMMARY_COLUMNS[5]] == 100
    assert summary[1][module.SUMMARY_COLUMNS[5]] == "DATA_NOT_AVAILABLE"


def test_only_deduplicated_high_precision_asset_is_used(tmp_path):
    write_602_package(tmp_path, [row("1", "sister gifts", 10)])
    assert len(module.load_6_0_2_inputs(tmp_path, "B2")) == 1
    package = module.load_6_0_2_input_package(tmp_path, "B2")
    assert package["deduplicated_file"] == package["files"]["deduplicated"]
    assert package["input_unique_keyword_count"] == 1
    result = module.run(tmp_path, "B2", semantic_mapper({"sister gifts": ("sister gifts", "cn1")}))
    assert {"mapping", "summary", "run_folder", "run_manifest", "run_timestamp"}.issubset(result)
    assert Path(result["mapping"]).parent == Path(result["summary"]).parent == Path(result["run_folder"])
    manifest = json.loads(Path(result["run_manifest"]).read_text(encoding="utf-8"))
    assert manifest["Input Skill"] == "hzp-amz-6-0-2-ai-precision-keyword-identification"
    assert manifest["Input Report"] == "去对标去重 高度精准词"
    assert manifest["Input Report Identity"] == module.INPUT_REPORT_IDENTITY
    assert manifest["Input File"] == package["deduplicated_file"]
    assert manifest["Input RUN_TIMESTAMP"] == package["run_timestamp"]
    assert manifest["Input Record Count"] == manifest["Input Unique Keyword Count"] == 1
    with result["mapping"].open(encoding="utf-8-sig", newline="") as handle:
        assert list(csv.DictReader(handle))[0][ID] == "1"


def test_non_high_precision_input_is_blocked_with_contract_code(tmp_path):
    write_602_package(tmp_path, [row("1", "sister gifts", 10, precision="bad")])
    try:
        module.load_6_0_2_inputs(tmp_path, "B2")
    except ValueError as exc:
        assert module.NON_HIGH_PRECISION_RECORD in str(exc)
    else:
        raise AssertionError("non-high input must be rejected")


def test_empty_high_precision_input_writes_two_headers(tmp_path):
    write_602_package(tmp_path, [])
    result = module.run(tmp_path, "B2")
    for path, columns in ((result["mapping"], module.MAPPING_COLUMNS), (result["summary"], module.SUMMARY_COLUMNS)):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            assert next(csv.reader(handle)) == list(columns)


def test_duplicate_canonical_keyword_is_rejected(tmp_path):
    write_602_package(tmp_path, [row("1", "sister gifts", 10), row("1", "sister gifts", 20)])
    try:
        module.load_6_0_2_inputs(tmp_path, "B2")
    except ValueError as exc:
        assert module.DUPLICATE_CANONICAL_KEYWORDS in str(exc)
    else:
        raise AssertionError("duplicate canonical keyword must be rejected")



def test_603_uses_650_unique_rows_when_602_observation_companion_has_1000(tmp_path):
    unique = [row(f"KW-{i}", f"unique sister gift {i}", i + 1) for i in range(650)]
    observations = [_observation(source, i) for i, source in enumerate(unique)]
    observations.extend({**_observation(unique[i], i), "所属产品编号": "BM-2", "对标ASIN": "ASIN-2"}
                        for i in range(350))
    write_602_package(tmp_path, unique, observations=observations)
    package = module.load_6_0_2_input_package(tmp_path, "B2")
    assert len(package["rows"]) == 650
    assert len(module.read_csv(package["files"]["high_precision"])) == 1000
    assert Path(package["deduplicated_file"]).name.endswith("_20260916_184400.csv")


def test_unique_keyword_validation_uses_canonical_case_and_spacing():
    duplicated = [row("1", "Sister  Gifts", 10), row("2", "sister gifts", 20)]
    try:
        module._validate_high_precision_rows(duplicated)
    except ValueError as exc:
        assert str(exc).startswith(module.DUPLICATE_CANONICAL_KEYWORDS)
    else:
        raise AssertionError("canonical duplicates must be blocked")
    assert "所属产品编号" not in module.INPUT_COLUMNS
    assert module.INPUT_REPORT_IDENTITY == "去对标去重 高度精准词"
    assert module.INPUT_REPORT_KEY == "UNIQUE_HIGH_PRECISION_KEYWORDS"


def test_competitor_passthrough_matches_602_by_id():
    source = [row("123", "sister birthday gifts", 27865, competing="8000", ratio="3.4831")]
    mapped = module.build_mapping_rows(source, semantic_mapper({"sister birthday gifts": ("sister birthday gifts", "姐妹生日礼物")}))
    assert mapped[0][COMP_COUNT] == "8000" and mapped[0][RATIO] == "3.4831"
    summary = module.aggregate_mapping_rows(mapped)
    assert module.data_integrity_check(source, mapped, summary)["passed"]


def test_leaf_intent_competitor_average_and_ratio():
    source = [
        row("a", "sister birthday gift", 1000, competing="500"),
        row("b", "birthday gift for sister", 2000, competing="1500"),
    ]
    mapped = module.build_mapping_rows(source, semantic_mapper({
        "sister birthday gift": ("sister birthday gifts", "姐妹生日礼物"),
        "birthday gift for sister": ("sister birthday gifts", "姐妹生日礼物"),
    }))
    intent = module.aggregate_mapping_rows(mapped)[0]
    assert intent[module.SUMMARY_COLUMNS[5]] == 3000
    assert intent[AVG_COMP] == 1000
    assert intent[INTENT_RATIO] == 3


def test_intent_ratio_uses_aggregated_volume_divided_by_average_and_rounds_four_places():
    source = [
        row("a", "sister birthday gifts", 40000, competing="20000"),
        row("b", "birthday presents for sister", 43989, competing="30000"),
    ]
    mapped = module.build_mapping_rows(source, semantic_mapper({
        "sister birthday gifts": ("sister birthday gifts", "姐妹生日礼物"),
        "birthday presents for sister": ("sister birthday gifts", "姐妹生日礼物"),
    }))
    intent = module.aggregate_mapping_rows(mapped)[0]
    assert intent[module.SUMMARY_COLUMNS[5]] == 83989
    assert intent[AVG_COMP] == 25000
    assert str(intent[INTENT_RATIO]) == "3.3596"


def test_parent_average_uses_all_parent_and_descendant_source_records():
    source = [
        row("p", "sister gift", 1000, competing="1000"),
        row("c1", "sister birthday gifts", 2000, competing="2000"),
        row("c2", "birthday presents for sister", 3000, competing="3000"),
    ]
    mapped = module.build_mapping_rows(source, semantic_mapper({
        "sister gift": {"精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物"},
        "sister birthday gifts": {"精准泛词": "sister birthday gifts", "精准泛词中文": "姐妹生日礼物", "父精准泛词": "sister gifts"},
        "birthday presents for sister": {"精准泛词": "sister christmas gifts", "精准泛词中文": "姐妹圣诞礼物", "父精准泛词": "sister gifts"},
    }))
    summary = module.aggregate_mapping_rows(mapped)
    parent = next(item for item in summary if item[module.SUMMARY_COLUMNS[0]] == "sister gifts")
    assert parent[module.SUMMARY_COLUMNS[5]] == 6000
    assert parent[AVG_COMP] == 2000
    assert parent[INTENT_RATIO] == 3


def test_null_zero_and_invalid_competitor_counts_are_excluded():
    source = [
        row("1", "sister gift a", 1000, competing="1000"),
        row("2", "sister gift b", 1000, competing="NULL"),
        row("3", "sister gift c", 1000, competing="3000"),
        row("4", "sister gift d", 1000, competing="0"),
        row("5", "sister gift e", 1000, competing="not-a-number"),
    ]
    mapped = module.build_mapping_rows(source, semantic_mapper({
        keyword: ("sister gifts", "姐妹礼物") for keyword in (item[KW] for item in source)
    }))
    intent = module.aggregate_mapping_rows(mapped)[0]
    assert intent[AVG_COMP] == 2000
    assert intent[INTENT_RATIO] == 2.5

    unavailable = module.aggregate_mapping_rows([
        {**mapped[0], COMP_COUNT: "0"},
        {**mapped[1], "Id": "6", COMP_COUNT: "NULL"},
    ])[0]
    assert unavailable[AVG_COMP] == module.DATA_NOT_AVAILABLE
    assert unavailable[INTENT_RATIO] == module.DATA_NOT_AVAILABLE


def test_parent_competitor_average_is_not_average_of_child_averages():
    source = [
        row("p", "sister gifts broad", 10, competing="1000"),
        row("a", "sister birthday gifts", 10, competing="100"),
        row("b1", "sister christmas gifts", 10, competing="1000"),
        row("b2", "christmas presents for sister", 10, competing="1000"),
        row("b3", "sister xmas gifts", 10, competing="1000"),
    ]
    mapped = module.build_mapping_rows(source, semantic_mapper({
        "sister gifts broad": {"精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物"},
        "sister birthday gifts": {"精准泛词": "sister birthday gifts", "精准泛词中文": "姐妹生日礼物", "父精准泛词": "sister gifts"},
        "sister christmas gifts": {"精准泛词": "sister christmas gifts", "精准泛词中文": "姐妹圣诞礼物", "父精准泛词": "sister gifts"},
        "christmas presents for sister": {"精准泛词": "sister christmas gifts", "精准泛词中文": "姐妹圣诞礼物", "父精准泛词": "sister gifts"},
        "sister xmas gifts": {"精准泛词": "sister christmas gifts", "精准泛词中文": "姐妹圣诞礼物", "父精准泛词": "sister gifts"},
    }))
    parent = next(item for item in module.aggregate_mapping_rows(mapped) if item[module.SUMMARY_COLUMNS[0]] == "sister gifts")
    assert parent[AVG_COMP] == 820
    assert parent[AVG_COMP] != (100 + 1000) / 2


def test_integrity_check_detects_mapping_and_summary_metric_mismatch():
    source = [row("1", "sister gifts", 100, competing="10", ratio="10.0000")]
    mapped = module.build_mapping_rows(source, semantic_mapper({"sister gifts": ("sister gifts", "姐妹礼物")}))
    summary = module.aggregate_mapping_rows(mapped)
    mapped[0][COMP_COUNT] = "11"
    assert any(module.COMPETITOR_PASSTHROUGH_MISMATCH in error for error in module.data_integrity_check(source, mapped, summary)["errors"])
    mapped[0][COMP_COUNT] = "10"
    summary[0][AVG_COMP] = 9
    assert any(module.AVERAGE_COMPETITOR_MISMATCH in error for error in module.data_integrity_check(source, mapped, summary)["errors"])


def test_complete_schemas_and_run_readback_integrity(tmp_path):
    assert tuple(module.MAPPING_COLUMNS) == ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名", "精准泛词", "精准泛词中文")
    assert tuple(module.MAPPING_COLUMNS)[4:6] == ("竞争产品数", "供需比")
    assert tuple(module.SUMMARY_COLUMNS) == ("精准泛词", "中文", "层级", "父精准泛词", "直接搜索量", "汇总搜索量", "平均竞品数", "意图机会比", "直接对应词数")
    source = [row("123", "sister birthday gifts", 27865, competing="8000", ratio="3.4831")]
    write_602_package(tmp_path, source)
    outputs = module.run(tmp_path, "B2", semantic_mapper({"sister birthday gifts": ("sister birthday gifts", "姐妹生日礼物")}))
    mapped = module.read_csv(outputs["mapping"])
    assert mapped[0]["自然排名"] == source[0]["最佳自然排名"]
    assert module.data_integrity_check(source, mapped, module.read_csv(outputs["summary"]))["passed"]


def test_latest_valid_602_package_is_selected_and_incomplete_newest_falls_back(tmp_path):
    older_rows = [row("old", "sister gifts", 10)]
    newer_rows = [row("new", "sister birthday gifts", 20)]
    older = write_602_package(tmp_path, older_rows, "20260916_160000")
    write_602_package(tmp_path, newer_rows, "20260917_090000", status="FAILED")
    resolved = module.resolve_latest_valid_602_run_package(tmp_path, "B2")
    assert resolved["status"] == "LATEST_VALID_602_RUN_PACKAGE_READY"
    assert resolved["run_timestamp"] == "20260916_160000"
    assert Path(resolved["files"]["ai"]).parent == older["ai"].parent
    assert Path(resolved["files"]["deduplicated"]).parent == older["deduplicated"].parent
    assert resolved["invalid_runs"][0]["run_timestamp"] == "20260917_090000"


def test_602_run_package_resolves_without_per_csv_sidecars(tmp_path):
    paths = write_602_package(tmp_path, [row("one", "sister gifts", 10)])
    assert not list(paths["ai"].parent.glob("*.csv.meta.json"))
    resolved = module.resolve_latest_valid_602_run_package(tmp_path, "B2")
    assert resolved["status"] == "LATEST_VALID_602_RUN_PACKAGE_READY"


def test_legacy_602_manifest_prefix_remains_readable(tmp_path):
    paths = write_602_package(tmp_path, [row("one", "sister gifts", 10)])
    current = paths["ai"].parent / f"{module.INPUT_602_MANIFEST_PREFIX}20260916_184400.json"
    legacy = paths["ai"].parent / f"{module.LEGACY_INPUT_602_MANIFEST_PREFIX}20260916_184400.json"
    current.rename(legacy)
    resolved = module.resolve_latest_valid_602_run_package(tmp_path, "B2")
    assert resolved["status"] == "LATEST_VALID_602_RUN_PACKAGE_READY"



def test_invalid_output_declaration_is_skipped_and_older_valid_run_is_used(tmp_path):
    older = write_602_package(tmp_path, [row("old", "sister gifts", 10)], "20260916_160000")
    newer = write_602_package(tmp_path, [row("new", "sister birthday gifts", 20)], "20260917_090000")
    manifest_path = newer["ai"].parent / f"{module.INPUT_602_MANIFEST_PREFIX}20260917_090000.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["Output Files"].remove(newer["deduplicated"].name)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    resolved = module.resolve_latest_valid_602_run_package(tmp_path, "B2")
    assert resolved["run_timestamp"] == "20260916_160000"
    assert resolved["files"]["deduplicated"] == str(older["deduplicated"])
    assert resolved["invalid_runs"][0]["reason"] == "RUN_OUTPUT_DECLARATION_INVALID"


def test_single_csv_602_run_is_not_a_valid_package(tmp_path):
    valid = write_602_package(tmp_path, [row("good", "sister gifts", 10)], "20260916_160000")
    write_602_package(tmp_path, [row("bad", "sister birthday gifts", 20)], "20260917_090000", include_high=False)
    resolved = module.resolve_latest_valid_602_run_package(tmp_path, "B2")
    assert resolved["run_timestamp"] == "20260916_160000"
    assert Path(resolved["files"]["deduplicated"]).parent == valid["deduplicated"].parent


if __name__ == "__main__":
    test_same_intent_maps_to_one_canonical_and_sums_programmatically()
    test_parent_child_intents_keep_occasion_and_recursive_volume()
    test_parent_cycle_is_rejected()
    test_orphan_parent_is_rejected()
    test_different_relationship_intents_do_not_merge()
    test_mapping_preserves_all_ids_and_same_keyword_multiple_ids()
    test_competitor_fields_pass_through_without_intent_aggregation()
    test_partial_missing_volume_is_unavailable_and_sorted_last()
    test_competitor_passthrough_matches_602_by_id()
    test_leaf_intent_competitor_average_and_ratio()
    test_intent_ratio_uses_aggregated_volume_divided_by_average_and_rounds_four_places()
    test_parent_average_uses_all_parent_and_descendant_source_records()
    test_null_zero_and_invalid_competitor_counts_are_excluded()
    test_parent_competitor_average_is_not_average_of_child_averages()
    test_integrity_check_detects_mapping_and_summary_metric_mismatch()
    print("6-0-3 broad extraction tests: PASS")
