from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "dual_precision_csv.py"
spec = importlib.util.spec_from_file_location("dual_precision", SCRIPT)
dual = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(dual)


def _write(path: Path, columns: tuple[str, ...], value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow({column: (value if column == "词" else "1") for column in columns})


def test_602_selects_newest_601_filename_without_registry(tmp_path: Path) -> None:
    folder = tmp_path / "06_SKILL分析报告" / dual.BENCHMARK_RAW_OUTPUT_DIR / "data"
    _write(folder / "6-0-1_所有对标自然排名关键词_20260916_100000.csv", dual.BENCHMARK_RAW_COLUMNS, "old")
    _write(folder / "6-0-1_所有对标自然排名关键词_20260917_100000.csv", dual.BENCHMARK_RAW_COLUMNS, "new")
    result = dual.resolve_benchmark_raw_csvs(tmp_path, "B2")
    assert result["status"] == "BENCHMARK_RAW_READY"
    assert result["run_timestamp"] == "20260917_100000"
    assert result["rows"][0]["词"] == "new"

