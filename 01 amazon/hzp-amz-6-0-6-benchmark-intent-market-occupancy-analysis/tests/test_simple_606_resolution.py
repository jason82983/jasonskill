from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "benchmark_intent_occupancy.py"
spec = importlib.util.spec_from_file_location("occupancy", SCRIPT)
occupancy = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(occupancy)


def _write(path: Path, columns: tuple[str, ...], row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow(row)


def test_606_reads_data_files_without_manifest(tmp_path: Path) -> None:
    stamp = "20260917_100000"
    d603 = tmp_path / "06_SKILL分析报告" / "6-0-3_精准泛词提取" / "data"
    _write(d603 / f"6-0-3_精准泛词汇总_{stamp}.csv", occupancy.SUMMARY_COLUMNS,
           dict(zip(occupancy.SUMMARY_COLUMNS, ["x", "", "ROOT", "", "10", "10", "2", "5", "1"])))
    _write(d603 / f"6-0-3_词对应的精准泛词_{stamp}.csv", occupancy.MAPPING_MULTI_COLUMNS,
           dict(zip(occupancy.MAPPING_MULTI_COLUMNS, ["1", "kw", "", "10", "2", "5", "1", "1", "1", "x", ""])))
    d602 = tmp_path / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "data"
    _write(d602 / f"6-0-2_A1_高度精准词_{stamp}.csv", occupancy.BENCHMARK_HIGH_PRECISION_COLUMNS,
           dict(zip(occupancy.BENCHMARK_HIGH_PRECISION_COLUMNS, ["A1", "ASIN-A", "1", "kw", "", "10", "2", "5", "3", "高度精准", "fit"])))
    result = occupancy.resolve_inputs(tmp_path, "B2")
    assert result["run_timestamp"] == stamp
    assert result["benchmark_identities"] == {"A1": "ASIN-A"}
    assert result["summary"]["run_timestamp"] == stamp

