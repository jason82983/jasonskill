from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "broad_seed_cluster.py"
spec = importlib.util.spec_from_file_location("broad_seed", SCRIPT)
broad = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(broad)


def test_603_reads_c_csv_without_runpackage(tmp_path: Path) -> None:
    folder = tmp_path / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "data"
    folder.mkdir(parents=True)
    path = folder / "6-0-2_去重去对标后 筛选后的精准词表_20260917_100000.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=broad.INPUT_COLUMNS)
        writer.writeheader()
        writer.writerow({"Id": "1", "词": "specific product", "中文": "", "市场容量": "10",
                         "竞争产品数": "2", "供需比": "5", "对标覆盖数": "1",
                         "最佳自然排名": "1", "自然排名中位数": "1", "精准度": "高度精准", "精准原因": "fit"})
    result = broad.resolve_latest_valid_602_run_package(tmp_path, "B2")
    assert result["status"] == "LATEST_VALID_602_RUN_PACKAGE_READY"
    assert result["run_timestamp"] == "20260917_100000"

