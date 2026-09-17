from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\qmhzp\.codex\skills")))

from scripts.new_product_battle_plan_contract import (
    MAPPING_MULTI_COLUMNS,
    SUMMARY_COLUMNS,
    resolve_603_bundle,
)


def _write(path: Path, columns: tuple[str, ...], row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow(row)


def test_603_uses_filename_timestamp_and_same_pair(tmp_path: Path) -> None:
    data = tmp_path / "06_SKILL分析报告" / "6-0-3_精准泛词提取" / "data"
    _write(data / "6-0-3_精准泛词汇总_20260916_100000.csv", SUMMARY_COLUMNS,
           dict(zip(SUMMARY_COLUMNS, ["old", "", "ROOT", "", "1", "1", "1", "1", "1"])))
    _write(data / "6-0-3_词对应的精准泛词_20260916_100000.csv", MAPPING_MULTI_COLUMNS,
           dict(zip(MAPPING_MULTI_COLUMNS, ["1", "old", "", "1", "1", "1", "1", "1", "1", "old", ""])))
    _write(data / "6-0-3_精准泛词汇总_20260917_100000.csv", SUMMARY_COLUMNS,
           dict(zip(SUMMARY_COLUMNS, ["new", "", "ROOT", "", "2", "2", "2", "1", "1"])))
    _write(data / "6-0-3_词对应的精准泛词_20260917_100000.csv", MAPPING_MULTI_COLUMNS,
           dict(zip(MAPPING_MULTI_COLUMNS, ["2", "new", "", "2", "2", "2", "1", "1", "1", "new", ""])))
    result = resolve_603_bundle(tmp_path, "B2")
    assert result["run_timestamp"] == "20260917_100000"
    assert result["summary"]["rows"][0]["精准泛词"] == "new"
    assert result["method"] == "FILENAME_TIMESTAMP_LATEST_EXACT_IDENTITY"
