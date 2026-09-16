from pathlib import Path
import csv
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("broad", ROOT / "scripts" / "broad_seed_cluster.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)
ID, KW, CN, VOL, COMP_COUNT, RATIO, COVERAGE, BEST_RANK, MEDIAN_RANK, PREC, REASON = module.INPUT_COLUMNS
HIGH = bytes.fromhex("E9AB98E5BAA6E7B2BEE58786").decode()
AVG_COMP = module.SUMMARY_COLUMNS[6]
INTENT_RATIO = module.SUMMARY_COLUMNS[7]
DIRECT_COUNT = module.SUMMARY_COLUMNS[8]


def row(record_id, keyword, volume, cn="", precision=HIGH, competing="50", ratio="20.0000", coverage="1", best_rank="", median_rank=""):
    return {ID: record_id, KW: keyword, CN: cn, VOL: str(volume), COMP_COUNT: competing, RATIO: ratio, COVERAGE: coverage, BEST_RANK: best_rank, MEDIAN_RANK: median_rank, PREC: precision, REASON: "fit"}


def semantic_mapper(mapping):
    return lambda record: mapping[record[KW]]


def test_same_intent_maps_to_one_canonical_and_sums_programmatically():
    rows = [row("1", "sister birthday gifts", 18000), row("2", "gift for sister", 12000), row("3", "big sister gift", 4000), row("4", "best friend gifts", 9000)]
    mapping = {"sister birthday gifts": ("sister gifts", "cn1"), "gift for sister": ("sister gifts", "cn1"), "big sister gift": ("sister gifts", "cn1"), "best friend gifts": ("best friend gifts", "cn2")}
    mapped = module.build_mapping_rows(rows, semantic_mapper(mapping))
    summary = module.aggregate_mapping_rows(mapped)
    assert mapped[0][module.MAPPING_COLUMNS[9]] == mapped[1][module.MAPPING_COLUMNS[9]] == mapped[2][module.MAPPING_COLUMNS[9]] == "sister gifts"
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
    assert {r[module.MAPPING_COLUMNS[9]] for r in mapped} == {"sister gifts", "best friend gifts"}


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


def test_only_high_precision_companion_is_accepted(tmp_path):
    paths = module.input_paths(tmp_path, "B2")
    paths["high_precision"].parent.mkdir(parents=True, exist_ok=True)
    module.write_csv(paths["high_precision"], [row("1", "sister gifts", 10)], module.INPUT_COLUMNS)
    assert len(module.load_6_0_2_inputs(tmp_path, "B2")) == 1
    result = module.run(tmp_path, "B2", semantic_mapper({"sister gifts": ("sister gifts", "cn1")}))
    assert set(result) == {"mapping", "summary"}
    with result["mapping"].open(encoding="utf-8-sig", newline="") as handle:
        assert list(csv.DictReader(handle))[0][ID] == "1"


def test_non_high_precision_input_is_not_silently_mixed(tmp_path):
    paths = module.input_paths(tmp_path, "B2")
    paths["high_precision"].parent.mkdir(parents=True, exist_ok=True)
    module.write_csv(paths["high_precision"], [row("1", "sister gifts", 10, precision="bad")], module.INPUT_COLUMNS)
    try:
        module.load_6_0_2_inputs(tmp_path, "B2")
    except ValueError as exc:
        assert module.NON_HIGH_PRECISION_RECORD in str(exc)
    else:
        raise AssertionError("non-high input must be rejected")


def test_empty_high_precision_input_writes_two_headers(tmp_path):
    paths = module.input_paths(tmp_path, "B2")
    paths["high_precision"].parent.mkdir(parents=True, exist_ok=True)
    module.write_csv(paths["high_precision"], [], module.INPUT_COLUMNS)
    result = module.run(tmp_path, "B2")
    for path, columns in ((result["mapping"], module.MAPPING_COLUMNS), (result["summary"], module.SUMMARY_COLUMNS)):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            assert next(csv.reader(handle)) == list(columns)


def test_duplicate_input_ids_are_rejected(tmp_path):
    paths = module.input_paths(tmp_path, "B2")
    paths["high_precision"].parent.mkdir(parents=True, exist_ok=True)
    module.write_csv(paths["high_precision"], [row("1", "sister gifts", 10), row("1", "sister gifts", 20)], module.INPUT_COLUMNS)
    try:
        module.load_6_0_2_inputs(tmp_path, "B2")
    except ValueError as exc:
        assert module.DUPLICATE_RECORD_IDS in str(exc)
    else:
        raise AssertionError("duplicate Id must be rejected")


def test_competitor_passthrough_matches_602_by_id():
    source = [row("123", "sister birthday gifts", 27865, competing="8000", ratio="3.4831")]
    mapped = module.build_mapping_rows(source, semantic_mapper({"sister birthday gifts": ("sister birthday gifts", "姐妹生日礼物")}))
    assert mapped[0][COMP_COUNT] == "8000" and mapped[0][RATIO] == "3.4831"
    summary = module.aggregate_mapping_rows(mapped)
    assert module.data_integrity_check(source, mapped, summary)["passed"]


def test_three_benchmark_observations_do_not_multiply_unique_keyword_capacity():
    # 6-0-2 has collapsed the three observations to one stable KwId row.
    source = [row("KW-77", "sister birthday gifts", 20000, competing="8000", ratio="2.5000",
                  coverage="3", best_rank="3", median_rank="18")]
    mapped = module.build_mapping_rows(
        source, semantic_mapper({"sister birthday gifts": ("sister birthday gifts", "姐妹生日礼物")})
    )
    summary = module.aggregate_mapping_rows(mapped)
    assert len(mapped) == 1
    assert summary[0][module.SUMMARY_COLUMNS[5]] == 20000
    assert summary[0][DIRECT_COUNT] == 1
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
    assert any(module.MULTI_BENCHMARK_PASSTHROUGH_MISMATCH in error for error in module.data_integrity_check(source, mapped, summary)["errors"])
    mapped[0][COMP_COUNT] = "10"
    summary[0][AVG_COMP] = 9
    assert any(module.AVERAGE_COMPETITOR_MISMATCH in error for error in module.data_integrity_check(source, mapped, summary)["errors"])


def test_complete_schemas_and_run_readback_integrity(tmp_path):
    assert tuple(module.MAPPING_COLUMNS) == ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数", "精准泛词", "精准泛词中文")
    assert tuple(module.MAPPING_COLUMNS)[4:6] == ("竞争产品数", "供需比")
    assert tuple(module.SUMMARY_COLUMNS) == ("精准泛词", "中文", "层级", "父精准泛词", "直接搜索量", "汇总搜索量", "平均竞品数", "意图机会比", "直接对应词数")
    paths = module.input_paths(tmp_path, "B2")
    paths["high_precision"].parent.mkdir(parents=True, exist_ok=True)
    source = [row("123", "sister birthday gifts", 27865, competing="8000", ratio="3.4831")]
    module.write_csv(paths["high_precision"], source, module.INPUT_COLUMNS)
    outputs = module.run(tmp_path, "B2", semantic_mapper({"sister birthday gifts": ("sister birthday gifts", "姐妹生日礼物")}))
    assert module.data_integrity_check(source, module.read_csv(outputs["mapping"]), module.read_csv(outputs["summary"]))["passed"]


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
