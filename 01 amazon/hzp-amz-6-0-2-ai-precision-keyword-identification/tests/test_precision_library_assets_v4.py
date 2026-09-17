from pathlib import Path
import importlib.util

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("precision_v4", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def _config(root: Path, text: str):
    path = root / "01_公共资料" / "03_系统配置" / "生成精准词库的要求.txt"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")


def _rows():
    rows = []
    levels = ["高度精准", "精准", "弱精准", "不精准"]
    for index, level in enumerate(levels, 1):
        for code in ("B1", "B2"):
            rows.append({
                "所属产品编号": code, "对标ASIN": f"ASIN-{code}", "Id": str(index),
                "词": f"keyword {index}", "中文": f"词{index}", "市场容量": str(1000 - index),
                "竞争产品数": "10", "供需比": "100", "自然排名": str(index),
                "精准度": level, "精准原因": f"reason {index}",
            })
    return rows


def test_config_alias_and_strict_errors(tmp_path):
    _config(tmp_path, "把下面精准级别，放到已挑选的词库：\n高度精准\n已精准\n")
    result = module.read_precision_filter_config(tmp_path, require=True)
    assert result["raw_levels"] == ["高度精准", "已精准"]
    assert result["levels"] == ["高度精准", "精准"]

    missing = tmp_path.parent / (tmp_path.name + "_missing")
    with pytest.raises(ValueError, match="PRECISION_LIBRARY_CONFIG_NOT_FOUND"):
        module.read_precision_filter_config(missing, require=True)

    _config(missing, "精准级别：超级精准\n")
    with pytest.raises(ValueError, match="CONFIG_PRECISION_LEVEL_INVALID"):
        module.read_precision_filter_config(missing, require=True)


def test_five_asset_derivation_and_all_four_levels(tmp_path):
    _config(tmp_path, "高度精准\n精准\n弱精准\n不精准\n")
    rows = _rows()
    selected = module.build_high_precision_rows(rows, precision_levels=module.read_precision_filter_config(tmp_path, require=True)["levels"])
    benchmark_unique = module.build_deduplicated_benchmark_rows(selected)
    unique = module.build_deduplicated_high_precision_rows(selected, precision_levels=module.PRECISION_LEVELS)
    assert len(selected) == len(rows)
    assert len(benchmark_unique) == len(rows)
    assert len(unique) == 4
    assert {row["精准度"] for row in selected} == set(module.PRECISION_LEVELS)
    assert {row["所属产品编号"] for row in benchmark_unique} == {"B1", "B2"}


def test_output_paths_and_review_status_are_separate(tmp_path):
    context = module.new_602_run_context(tmp_path, "B2")
    paths = module.output_paths(tmp_path, "B2", context, benchmark_product_codes=["B1", "B2"])
    assert paths["ai"].name.startswith("6-0-2_精准判断所有词表_")
    assert "筛选后的对标精准词" in paths["high_precision"].name
    assert "去重_筛选后的对标精准词" in paths["deduplicated_benchmark"].name
    assert "去对标去重_筛选后的精准词" in paths["deduplicated"].name
    assert all("_筛选后的精准词" in path.name for path in paths["benchmarks"].values())
    assert module._precision_level("REVIEW_REQUIRED") == module.PRECISION_LEVEL_NOT_AVAILABLE


def test_five_asset_writeback_validation(tmp_path):
    _config(tmp_path, "高度精准\n精准\n弱精准\n不精准\n")
    rows = _rows()
    context = module.new_602_run_context(tmp_path, "B2")
    paths = module.output_paths(tmp_path, "B2", context, benchmark_product_codes=["B1", "B2"])
    module._write_ai_asset_pair(rows, paths, context, precision_levels=module.PRECISION_LEVELS)
    validation = module.validate_written_outputs(rows, paths, precision_levels=module.PRECISION_LEVELS)
    assert validation["status"] == "PASS"
    assert validation["file_a"]["output_observation_count"] == len(rows)
    assert validation["file_c"]["output_unique_benchmark_keyword_count"] == len(rows)
    assert validation["file_d"]["output_unique_keyword_count"] == 4
    assert set(validation["file_e"]) == {"B1", "B2"}


