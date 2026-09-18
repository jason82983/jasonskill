import csv
import importlib.util
from datetime import datetime
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "precision_keyword.py"
SPEC = importlib.util.spec_from_file_location("precision_keyword", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def source_rows():
    return [
        {"Id": "10", "词": "Sister Gift", "中文": "姐妹礼物", "市场容量": "100", "竞争产品数": "20", "供需比": "5", "对标编号": "A", "对标ASIN": "ASINA", "自然排名": "5"},
        {"Id": "10", "词": "sister   gift", "中文": "姐妹礼物", "市场容量": "100", "竞争产品数": "20", "供需比": "5", "对标编号": "B", "对标ASIN": "ASINB", "自然排名": "15"},
        {"Id": "11", "词": "angel statue", "中文": "天使雕像", "市场容量": "80", "竞争产品数": "40", "供需比": "2", "对标编号": "A", "对标ASIN": "ASINA", "自然排名": "9"},
    ]


def judgments():
    common = {"SearcherPurchaseMission": "mission", "MissionFit": "fit", "HardConflict": "NONE", "BenchmarkReality": "support", "DecisionChallenge": "checked"}
    return [
        dict(common, KeywordId="10", CanonicalKeyword="sister gift", InitialPrecision="高度精准", FinalPrecision="高度精准", ShortReason="姐妹赠礼任务与产品一致"),
        dict(common, KeywordId="11", CanonicalKeyword="angel statue", InitialPrecision="不精准", FinalPrecision="不精准", ShortReason="天使产品类型冲突"),
    ]


def test_latest_601_uses_filename_timestamp_not_mtime(tmp_path):
    folder = tmp_path / "06_SKILL分析报告" / module.SOURCE_601_DIR / "data"
    older = folder / f"{module.SOURCE_601_IDENTITY}_20260917_120000.csv"
    newer = folder / f"{module.SOURCE_601_IDENTITY}_20260918_090000.csv"
    write_csv(older, source_rows())
    write_csv(newer, source_rows())
    older.touch()
    assert module.resolve_latest_601(tmp_path) == newer


def test_canonical_unique_and_observation_backfill():
    normalized = []
    for row in source_rows():
        normalized.append({"所属产品编号": row["对标编号"], "对标ASIN": row["对标ASIN"], "Id": row["Id"], "词": row["词"], "中文": row["中文"], "市场容量": row["市场容量"], "竞争产品数": row["竞争产品数"], "供需比": row["供需比"], "自然排名": row["自然排名"]})
    unique = module.prepare_unique_keyword_evidence(normalized)
    assert len(unique) == 2
    validated = module.validate_ai_judgments(unique, judgments())
    output = module.build_all_observation_output(normalized, validated)
    assert len(output) == 3
    assert [row["精准度"] for row in output[:2]] == ["高度精准", "高度精准"]


def test_config_alias_and_batch(tmp_path):
    selection = tmp_path / "selection.txt"
    selection.write_text("高度精准\n已精准\n", encoding="utf-8")
    batch = tmp_path / "batch.txt"
    batch.write_text("512", encoding="utf-8")
    assert module.read_precision_selection_config(selection) == ("高度精准", "精准")
    assert module.read_preferred_batch_size(batch) == 512
    batch.write_text("0", encoding="utf-8")
    with pytest.raises(module.PrecisionContractError, match="INVALID"):
        module.read_preferred_batch_size(batch)


def test_run_sequence_scans_history(tmp_path):
    (tmp_path / "历史数据").mkdir()
    (tmp_path / "历史html").mkdir()
    (tmp_path / "6-0-2_003_x_20260917_100000.csv").write_text("x", encoding="utf-8")
    (tmp_path / "历史数据" / "6-0-2_008_x_20260917_100000.csv").write_text("x", encoding="utf-8")
    (tmp_path / "历史html" / "6-0-2_007_x_20260917_100000.html").write_text("x", encoding="utf-8")
    assert module.allocate_run_sequence(tmp_path) == 9


def test_publish_four_asset_classes_and_archive(tmp_path):
    product_root = tmp_path / "B2 Product"
    report = product_root / "06_SKILL分析报告" / module.REPORT_DIR_NAME
    report.mkdir(parents=True)
    prior_csv = report / "6-0-2_001_精准判断所有词表_20260917_100000.csv"
    prior_html = report / "6-0-2_001_AI精准关键词识别_20260917_100000.html"
    prior_csv.write_text("old", encoding="utf-8")
    prior_html.write_text("old", encoding="utf-8")
    selection = tmp_path / "selection.txt"
    selection.write_text("高度精准\n", encoding="utf-8")
    normalized = [{"所属产品编号": r["对标编号"], "对标ASIN": r["对标ASIN"], "Id": r["Id"], "词": r["词"], "中文": r["中文"], "市场容量": r["市场容量"], "竞争产品数": r["竞争产品数"], "供需比": r["供需比"], "自然排名": r["自然排名"]} for r in source_rows()]
    unique = module.prepare_unique_keyword_evidence(normalized)
    result = module.publish_complete_run("B2", product_root, Path("source601.csv"), normalized, unique, judgments(), selection, datetime(2026, 9, 18, 10, 15, 22))
    assert result["Status"] == "COMPLETE"
    assert result["RunSequence"] == "002"
    names = [path.name for path in result["OutputPaths"]]
    assert len(names) == 5  # all + unique + two Benchmark files + HTML
    assert all(name.startswith("6-0-2_002_") and "20260918_101522" in name for name in names)
    assert (report / "历史数据" / prior_csv.name).is_file()
    assert (report / "历史html" / prior_html.name).is_file()
    assert not list(report.glob("*.json"))


def test_incomplete_judgment_blocks_publish():
    normalized = [{"所属产品编号": r["对标编号"], "对标ASIN": r["对标ASIN"], "Id": r["Id"], "词": r["词"], "中文": r["中文"], "市场容量": r["市场容量"], "竞争产品数": r["竞争产品数"], "供需比": r["供需比"], "自然排名": r["自然排名"]} for r in source_rows()]
    unique = module.prepare_unique_keyword_evidence(normalized)
    with pytest.raises(module.PrecisionContractError, match="COVERAGE_MISMATCH"):
        module.validate_ai_judgments(unique, judgments()[:1])


def test_precision_brain_v2_boundary_contract_is_documented():
    guide = Path(__file__).parents[1] / "references" / "precision-guide.md"
    text = guide.read_text(encoding="utf-8")
    assert "Hard Conflict Gate" in text
    assert "NATURAL_CORE_ANSWER" in text
    assert "REASONABLE_ANSWER" in text
    assert "ONE_OF_MANY_POSSIBLE_ANSWERS" in text
    assert "NOT_A_VALID_ANSWER" in text
    assert "counterfactual" in text
    assert "many ordinary products" in text
