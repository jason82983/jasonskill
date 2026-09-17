import csv
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("occupancy_analysis", ROOT / "scripts" / "occupancy_analysis.py")
occupancy = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(occupancy)

PRODUCT = "TST01"


def _write_csv(path: Path, columns, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def _write_603_package(root: Path, stamp: str, *, include_mapping: bool = True, single_benchmark: bool = False):
    folder = root / "06_SKILL分析报告" / occupancy.INPUT_603_ROOT / stamp
    folder.mkdir(parents=True)
    summary_name = f"6-0-3_{PRODUCT}_精准泛词汇总_{stamp}.csv"
    mapping_name = f"6-0-3_{PRODUCT}_词对应的精准泛词_{stamp}.csv"
    summary = [{
        "精准泛词": "sister gifts", "中文": "姐妹礼物", "层级": "L1", "父精准泛词": "",
        "直接搜索量": "10", "汇总搜索量": "10", "平均竞品数": "5",
        "意图机会比": "2", "直接对应词数": "1",
    }]
    mapping = [{
        "Id": "k1", "词": "sister gifts", "中文": "姐妹礼物", "市场容量": "10",
        "竞争产品数": "5", "供需比": "2", "精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物",
    }]
    if single_benchmark:
        mapping[0]["自然排名"] = "10"
    else:
        mapping[0].update({"对标覆盖数": "1", "最佳自然排名": "10", "自然排名中位数": "10"})
    _write_csv(folder / summary_name, occupancy.INPUT_603_SUMMARY_COLUMNS, summary)
    if include_mapping:
        columns = occupancy.INPUT_603_SINGLE_MAPPING_COLUMNS if single_benchmark else occupancy.INPUT_603_MAPPING_COLUMNS
        _write_csv(folder / mapping_name, columns, mapping)
    (folder / occupancy.RUN_MANIFEST).write_text(json.dumps({
        "SkillId": "hzp-amz-6-0-3-precision-broad-extraction",
        "Current Product": PRODUCT,
        "RUN_ID": stamp,
        "RUN_TIMESTAMP": stamp,
        "GeneratedAt": "2026-09-16T18:44:00+08:00",
        "Input Skill": "hzp-amz-6-0-2-ai-precision-keyword-identification",
        "Input Run ID": "602-run",
        "Input RUN_TIMESTAMP": "20260916_170000",
        "Input Folder": str(root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "20260916_170000"),
        "Input File": str(root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "20260916_170000" / "6-0-2_TST01_AI高度精准词_20260916_170000.csv"),
        "Input Record Count": 1,
        "Output Folder": str(folder),
        "Output Files": [summary_name, mapping_name],
        "Output Record Counts": {"Intent Count": 1, "Keyword Count": 1},
        "Run Status": "VALID",
    }, ensure_ascii=False), encoding="utf-8")
    return folder


def test_603_resolver_returns_both_files_from_one_latest_valid_package(tmp_path):
    folder = _write_603_package(tmp_path, "20260916_184400")
    package = occupancy.resolve_latest_valid_603(tmp_path, PRODUCT)
    assert Path(package["folder"]) == folder.resolve()
    assert Path(package["files"]["summary"]).parent == Path(package["files"]["mapping"]).parent
    assert all(path.name.endswith("_20260916_184400.csv") for path in map(Path, package["files"].values()))


def test_603_resolver_skips_incomplete_newest_and_falls_back(tmp_path):
    older = _write_603_package(tmp_path, "20260916_184400")
    _write_603_package(tmp_path, "20260917_090000", include_mapping=False)
    package = occupancy.resolve_latest_valid_603(tmp_path, PRODUCT)
    assert Path(package["folder"]) == older.resolve()
    assert package["run_timestamp"] == "20260916_184400"


def test_603_resolver_selects_latest_valid_package_before_consumer_schema_check(tmp_path):
    _write_603_package(tmp_path, "20260916_184400")
    newest = _write_603_package(tmp_path, "20260917_090000", single_benchmark=True)
    package = occupancy.resolve_latest_valid_603(tmp_path, PRODUCT)
    assert Path(package["folder"]) == newest.resolve()
    assert package["run_timestamp"] == "20260917_090000"
    observations = tmp_path / "6-0-2_500_高度精准词_20260916_100000.csv"
    _write_csv(observations, occupancy.INPUT_602_COLUMNS, [{
        "所属产品编号": "500", "对标ASIN": "B0TEST01", "Id": "k1", "词": "sister gifts",
        "中文": "姐妹礼物", "市场容量": "10", "竞争产品数": "5", "供需比": "2",
        "自然排名": "10", "精准度": "高度精准", "精准原因": "符合产品购买意图",
    }])
    package_602 = {
        "files": {"benchmarks": {"500": str(observations)}},
        "run_timestamp": "20260916_100000", "run_id": "602-20260916_100000",
        "manifest": {"RUN_ID": "602-20260916_100000", "Benchmark Identities": {
            "500": {"对标编码": "A", "对标ASIN": "B0TEST01"},
        }},
    }
    with pytest.raises(occupancy.ContractError, match="606_INPUT_SCHEMA_INVALID"):
        occupancy._load_inputs(package_602, package)


def test_603_resolver_does_not_accept_root_level_csv_pair(tmp_path):
    directory = tmp_path / "06_SKILL分析报告" / occupancy.INPUT_603_ROOT
    directory.mkdir(parents=True)
    stamp = "20260916_184400"
    _write_csv(directory / f"6-0-3_{PRODUCT}_精准泛词汇总_{stamp}.csv", occupancy.INPUT_603_SUMMARY_COLUMNS, [])
    _write_csv(directory / f"6-0-3_{PRODUCT}_词对应的精准泛词_{stamp}.csv", occupancy.INPUT_603_MAPPING_COLUMNS, [])
    with pytest.raises(occupancy.ContractError, match="606_INPUT_NOT_FOUND"):
        occupancy.resolve_latest_valid_603(tmp_path, PRODUCT)
