from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("broad", ROOT / "scripts" / "broad_seed_cluster.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def test_equivalent_order_and_prepositions_merge_and_sum_once():
    rows = [
        {"自动编号": "[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]", "关键词": "sister birthday gifts", "搜索量": "18000", "中文名称": "姐妹生日礼物"},
        {"自动编号": "[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]", "关键词": "birthday gifts for sister", "搜索量": "12000", "中文名称": "给姐妹的生日礼物"},
        {"自动编号": "[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]", "关键词": "sister birthday gifts", "搜索量": "18000", "中文名称": "重复"},
    ]
    result = module.extract_broad_rows(rows)
    assert result == [{"词": "sister birthday gifts", "中文": "姐妹生日礼物", "同意思词的合并总量": 30000}]


def test_duplicate_keyword_volume_conflict_is_not_summed():
    result = module.extract_broad_rows([
        {"自动编号": "1001", "关键词": "sister gifts", "搜索量": "18000"},
        {"自动编号": "2001", "关键词": "sister gifts", "搜索量": "17500"},
    ])
    assert result == [{"词": "sister gifts", "中文": "DATA_NOT_AVAILABLE", "同意思词的合并总量": module.DUPLICATE_KEYWORD_VOLUME_CONFLICT}]


def test_distinct_scenarios_do_not_over_merge():
    result = module.extract_broad_rows([
        {"关键词": "sister birthday gifts", "搜索量": "100"},
        {"关键词": "sister christmas gifts", "搜索量": "200"},
    ])
    assert {row["词"] for row in result} == {"sister birthday gifts", "sister christmas gifts"}
    assert [row["同意思词的合并总量"] for row in result] == [200, 100]


def test_single_minimum_intent_and_missing_volume():
    result = module.extract_broad_rows([
        {"关键词": "sister graduation gifts", "搜索量": "DATA_NOT_AVAILABLE", "中文名称": "姐妹毕业礼物"},
        {"关键词": "sister", "搜索量": "999", "中文名称": "姐妹"},
    ])
    assert result == [{"词": "sister graduation gifts", "中文": "姐妹毕业礼物", "同意思词的合并总量": "DATA_NOT_AVAILABLE"}]


def test_input_and_output_contract(tmp_path):
    paths = module.input_paths(tmp_path, "B2")
    paths["ai"].parent.mkdir(parents=True)
    module.write_csv(paths["ai"], [{"自动编号": "[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]", "关键词": "sister gifts", "搜索量": "10", "中文名称": "姐妹礼物", "精准理由": "fit", "精准度": "90"}], ("自动编号", "关键词", "搜索量", "中文名称", "精准理由", "精准度"))
    assert len(module.load_6_0_1_inputs(tmp_path, "B2")) == 1
    out = module.run(tmp_path, "B2")
    assert out.name == "6-0-2_B2_精准泛词.csv"
    assert list(csv.DictReader(out.open(encoding="utf-8-sig"))) == [{"词": "sister gifts", "中文": "姐妹礼物", "同意思词的合并总量": "10"}]


def test_missing_input_is_explicit(tmp_path):
    try:
        module.load_6_0_1_inputs(tmp_path, "B2")
    except FileNotFoundError as exc:
        assert module.MISSING_INPUT in str(exc)
    else:
        raise AssertionError("missing input must stop 6-0-2")


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        test_equivalent_order_and_prepositions_merge_and_sum_once()
        test_distinct_scenarios_do_not_over_merge()
        test_single_minimum_intent_and_missing_volume()
        test_input_and_output_contract(Path(directory))
        test_missing_input_is_explicit(Path(directory) / "missing")
    print("6-0-2 broad extraction tests: PASS")
