from pathlib import Path
import csv
import importlib.util
from datetime import datetime
import sys

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("precision", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from scripts.stage6_artifact_contract import make_artifact_metadata, new_run_context, write_metadata_sidecar


def source_rows():
    return [
        {"Id": "1", "词": "wide toe box shoes", "中文": "宽鞋头鞋", "市场容量": "100", "竞争产品数": "10", "供需比": "10.0000", "对标覆盖数": "2", "最佳自然排名": "4", "自然排名中位数": "12", "精准度": "", "精准原因": ""},
        {"Id": "2", "词": "gift", "中文": "礼物", "市场容量": "300", "竞争产品数": "20", "供需比": "15.0000", "对标覆盖数": "1", "最佳自然排名": "9", "自然排名中位数": "9", "精准度": "", "精准原因": ""},
        {"Id": "3", "词": "sister necklace", "中文": "姐妹项链", "市场容量": "100", "竞争产品数": "", "供需比": "", "对标覆盖数": "3", "最佳自然排名": "5", "自然排名中位数": "8", "精准度": "", "精准原因": ""},
    ]


def _write_601(root: Path, rows=None):
    raw_dir = root / "06_SKILL分析报告" / module.BENCHMARK_RAW_OUTPUT_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    run_dir = raw_dir / "20260915_120000"
    run_dir.mkdir(parents=True, exist_ok=True)
    raw = run_dir / "6-0-1_B2_对标关键词母池_20260915_120000.csv"
    with raw.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=module.BENCHMARK_RAW_COLUMNS)
        writer.writeheader()
        writer.writerows([{field: row.get(field) for field in module.BENCHMARK_RAW_COLUMNS} for row in (rows or source_rows())])
    context = new_run_context("6-0-1", module.SIX_0_1_SKILL_ID, "B2", now=datetime.strptime("20260915_120000", "%Y%m%d_%H%M%S").astimezone())
    detail = run_dir / "6-0-1_B2_多对标关键词排名明细_20260915_120000.csv"
    all_observations = run_dir / "所有对标自然排名关键词汇总_20260915_120000.csv"
    detail_schema = ["Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标编码", "对标ASIN", "自然排名"]
    c_schema = detail_schema + ["ASIN", "产品编号"]
    asins = ["ASIN-A", "ASIN-B", "ASIN-C"]
    raw_paths = [run_dir / f"{asin}+关键词自然排名_20260915_120000.csv" for asin in asins]
    for path, schema in ((detail, detail_schema), (all_observations, c_schema), *[(p, detail_schema) for p in raw_paths]):
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle).writerow(schema)
    assets = [str(detail), str(raw), *map(str, raw_paths), str(all_observations)]
    extras = {"Benchmark_Count": 3, "Benchmark_Codes": ["BM-A", "BM-B", "BM-C"],
              "Benchmark_ASINs": asins, "BenchmarkASINs": asins, "BenchmarkRawOrganicFiles": [p.name for p in raw_paths],
              "BenchmarkRawOrganicFileCount": 3, "BenchmarkOrganicSummaryFile": all_observations.name,
              "BenchmarkOrganicSummaryRecordCount": 0,
              "BenchmarkProductCodes": {asin: str(500 + index) for index, asin in enumerate(asins)},
              "PerBenchmarkObservationCounts": {asin: 0 for asin in asins},
              "Keyword_Entity_ID_Field": "KwId"}
    for path, identity, schema, count in ((detail, "BENCHMARK_KEYWORD_DETAIL", detail_schema, 0),
                                         (raw, module.SIX_0_1_REPORT_IDENTITY, module.BENCHMARK_RAW_COLUMNS, len(rows or source_rows())),
                                         *[(p, f"BENCHMARK_KEYWORD_RAW_{asin}", detail_schema, 0) for asin,p in zip(asins,raw_paths)],
                                         (all_observations, "BENCHMARK_KEYWORD_ALL_OBSERVATIONS", c_schema, 0)):
        write_metadata_sidecar(path, make_artifact_metadata(
            context, identity, run_status="FULL_SUCCESS", schema=schema, record_count=count,
            output_assets=assets, extra=extras,
        ))
    return raw


def _write_text(root: Path, text="产品是用于姐妹纪念场景的装饰雕塑。"):
    path = root / module.CURRENT_PRODUCT_TEXT_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_product_text_reader_reads_complete_text():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as directory:
        root = Path(directory)
        path = _write_text(root, "第一行\n产品结构与使用方式\n最后一行")
        result = module.read_current_product_text_evidence(root)
        assert result["status"] == module.CURRENT_PRODUCT_TEXT_EVIDENCE_READY
        assert result["product_text"] == path.read_text(encoding="utf-8")
        assert result["fully_read"] is True
        assert result["source_paths"] == [str(path)]
        assert result["sources"][0]["kind"] == "CURRENT_PRODUCT_TEXT_EVIDENCE"


def test_product_text_missing_empty_and_read_failed_statuses():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as directory:
        root = Path(directory)
        assert module.read_current_product_text_evidence(root)["status"] == module.CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND
        _write_text(root, "   \n")
        assert module.read_current_product_text_evidence(root)["status"] == module.CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY
        _write_text(root, "valid")
        original = Path.read_text
        try:
            Path.read_text = lambda self, *args, **kwargs: (_ for _ in ()).throw(OSError("denied"))
            assert module.read_current_product_text_evidence(root)["status"] == module.CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED
        finally:
            Path.read_text = original


def test_501_absence_does_not_block_runtime(tmp_path):
    _write_text(tmp_path)
    _write_601(tmp_path)
    decisions = {row["Id"]: {"精准度": "精准", "精准原因": "该词的搜索意图与当前产品事实经过逐词核验"} for row in source_rows()}
    result = module.run_current_602(tmp_path, "B2", decisions)
    assert result["input_record_count"] == result["output_record_count"] == 3
    assert result["status"] == "FULL_SUCCESS"
    assert result["data_integrity"]["status"] == "PASS"
    assert result["product_text_source"].endswith("产品识别 - 文本文案.txt")
    assert not list((tmp_path / "06_SKILL分析报告").glob("5-0-1_*.html"))


def test_missing_product_text_stops_before_601(tmp_path):
    _write_601(tmp_path)
    try:
        module.run_current_602(tmp_path, "B2", {})
    except FileNotFoundError as exc:
        assert str(exc) == module.CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND
    else:
        raise AssertionError("missing product text must stop precision judgment")


def test_missing_601_returns_formal_input_status(tmp_path):
    _write_text(tmp_path)
    try:
        module.run_current_602(tmp_path, "B2", {})
    except FileNotFoundError as exc:
        assert str(exc) == "6-0-1_KEYWORD_INPUT_NOT_FOUND"
    else:
        raise AssertionError("missing 6-0-1 must return formal input status")


def test_full_judgment_preserves_all_ids_and_sorts_stably():
    decisions = {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
        "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
        "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
    }
    result = module.finalize_ai_judgments(source_rows(), decisions)
    assert result["coverage"]["status"] == "PASS"
    assert result["coverage"]["input_record_count"] == result["coverage"]["output_record_count"] == 3
    assert [row["Id"] for row in result["rows"]] == ["2", "1", "3"]
    assert tuple(result["rows"][0]) == module.FULL_FINAL_COLUMNS


def test_full_writer_is_utf8_bom_and_exactly_nine_columns(tmp_path):
    result = module.finalize_ai_judgments(source_rows(), {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
        "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
        "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
    })
    path = module.write_full_ai_csv(tmp_path, "B2", result["rows"])
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        assert tuple(csv.reader(handle).__next__()) == module.FULL_FINAL_COLUMNS


def test_competitor_count_and_ratio_are_passed_through_unchanged():
    source = source_rows()
    before = {row["Id"]: (row["竞争产品数"], row["供需比"]) for row in source}
    decisions = {row["Id"]: {"精准度": "精准", "精准原因": "合成测试判断理由足以说明该记录的购买意图"} for row in source}
    result = module.finalize_ai_judgments(source, decisions)
    after = {row["Id"]: (row["竞争产品数"], row["供需比"]) for row in result["rows"]}
    assert after == before
    assert tuple(result["rows"][0]) == module.FULL_FINAL_COLUMNS
    case_a = [{"Id": "123", "词": "wide toe walking shoes", "中文": "宽头步行鞋", "市场容量": "27865",
               "竞争产品数": "8000", "供需比": "3.4831", "自然排名": "12"}]
    case_a_result = module.finalize_ai_judgments(case_a, {
        "123": {"精准度": "高度精准", "精准原因": "该关键词的购买需求与当前产品鞋类功能直接匹配"},
    })
    case_a_row = case_a_result["rows"][0]
    assert (case_a_row["Id"], case_a_row["竞争产品数"], case_a_row["供需比"], case_a_row["精准度"]) == ("123", "8000", "3.4831", "高度精准")
    assert module.build_high_precision_rows(case_a_result["rows"])[0]["供需比"] == "3.4831"


def test_null_competitor_count_and_ratio_remain_null_and_blank_in_csv(tmp_path):
    source = [dict(source_rows()[0], 竞争产品数=None, 供需比=None)]
    result = module.finalize_ai_judgments(source, {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
    })
    assert result["rows"][0]["竞争产品数"] is None
    assert result["rows"][0]["供需比"] is None
    written = module.write_full_ai_csv(tmp_path, "B2", result["rows"])
    paths = {"ai": written, "high_precision": written.with_name(written.name.replace("AI精准词", "AI高度精准词"))}
    for path in paths.values():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            row = next(csv.DictReader(handle))
        assert row["竞争产品数"] == ""
        assert row["供需比"] == ""


def test_competitor_fields_do_not_change_precision_decisions():
    decisions = {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
        "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
        "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
    }
    original = source_rows()
    changed = [dict(row) for row in original]
    for row in changed:
        row["竞争产品数"] = "0"
        row["供需比"] = "999999.0000"
    before = module.finalize_ai_judgments(original, decisions)
    after = module.finalize_ai_judgments(changed, decisions)
    assert {row["Id"]: row["精准度"] for row in before["rows"]} == {
        row["Id"]: row["精准度"] for row in after["rows"]
    }


def test_data_integrity_check_reports_file_a_and_file_b_field_mismatches():
    source = source_rows()
    decisions = {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
        "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
        "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
    }
    output_a = module.finalize_ai_judgments(source, decisions)["rows"]
    output_b = module.build_high_precision_rows(output_a)
    assert module.data_integrity_check(source, output_a, output_b)["status"] == "PASS"

    bad_a = [dict(row) for row in output_a]
    next(row for row in bad_a if row["Id"] == "1")["竞争产品数"] = "8001"
    result_a = module.data_integrity_check(source, bad_a, module.build_high_precision_rows(bad_a))
    assert result_a["status"] == "FAIL"
    assert module.COMPETING_PRODUCTS_PASSTHROUGH_MISMATCH in result_a["error_codes"]

    bad_b = [dict(row) for row in output_b]
    bad_b[0]["供需比"] = "3.4832"
    result_b = module.data_integrity_check(source, output_a, bad_b)
    assert result_b["status"] == "FAIL"
    assert module.SUPPLY_DEMAND_RATIO_PASSTHROUGH_MISMATCH in result_b["error_codes"]

    missing_a = output_a[:-1]
    result_missing_a = module.data_integrity_check(source, missing_a, module.build_high_precision_rows(missing_a))
    assert module.FILE_A_RECORD_COVERAGE_MISMATCH in result_missing_a["error_codes"]
    missing_b = output_b[:-1]
    result_missing_b = module.data_integrity_check(source, output_a, missing_b)
    assert module.FILE_B_RECORD_COVERAGE_MISMATCH in result_missing_b["error_codes"]


def test_run_current_602_does_not_report_full_success_after_readback_mismatch(tmp_path):
    _write_text(tmp_path)
    _write_601(tmp_path)
    original_writer = module.write_full_ai_csv

    def corrupt_high_precision_output(root, product_code, rows, *, run_context=None, write_metadata=True):
        path = original_writer(root, product_code, rows, run_context=run_context, write_metadata=write_metadata)
        paths = module.output_paths(root, product_code, run_context)
        high_rows = module._read_formal_csv(paths["high_precision"])
        high_rows[0]["竞争产品数"] = "999"
        module.write_csv(paths["high_precision"], high_rows, columns=module.FULL_FINAL_COLUMNS)
        return path

    module.write_full_ai_csv = corrupt_high_precision_output
    try:
        result = module.run_current_602(tmp_path, "B2", {
            "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
            "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
            "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
        })
    finally:
        module.write_full_ai_csv = original_writer
    assert result["status"] == "DATA_INTEGRITY_FAILED"
    assert module.COMPETING_PRODUCTS_PASSTHROUGH_MISMATCH in result["data_integrity"]["error_codes"]


def test_writer_emits_full_and_high_precision_assets_only(tmp_path):
    result = module.finalize_ai_judgments(source_rows(), {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
        "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
        "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
    })
    written = module.write_full_ai_csv(tmp_path, "B2", result["rows"])
    paths = {"ai": written, "high_precision": written.with_name(written.name.replace("AI精准词", "AI高度精准词"))}
    assert set(paths) == {"ai", "high_precision"}
    assert paths["ai"].exists() and paths["high_precision"].exists()
    with paths["high_precision"].open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == module.FULL_FINAL_COLUMNS
        high = list(reader)
    assert [row["精准度"] for row in high] == ["高度精准"]
    assert not (paths["ai"].parent / "6-0-2_B2_手动分类精准词.csv").exists()


def test_precision_level_is_direct_and_numeric_is_rejected():
    try:
        module.finalize_ai_judgments(source_rows(), {
            "1": {"精准度": 91, "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
            "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
            "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
        })
    except ValueError as exc:
        assert str(exc) == "AI_PRECISION_LEVEL_REQUIRED"
    else:
        raise AssertionError("numeric precision must not be accepted by canonical runtime")


def test_output_uses_only_four_precision_levels():
    result = module.finalize_ai_judgments(source_rows(), {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
        "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
        "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
    })
    assert {row["精准度"] for row in result["rows"]} <= set(module.PRECISION_LEVELS)


def test_golden_calibration_levels_are_preserved_as_direct_ai_decisions():
    cases = [
        ("best friend gifts for women", "高度精准"),
        ("sister birthday gifts", "高度精准"),
        ("friendship gifts for women", "高度精准"),
        ("big sister gift", "高度精准"),
        ("sister", "精准"),
        ("birthday gifts for women", "弱精准"),
        ("gifts for women", "弱精准"),
        ("friends", "弱精准"),
        ("gift", "不精准"),
        ("personalized gifts for women", "不精准"),
    ]
    rows = [{"Id": str(i), "词": keyword, "中文": "", "市场容量": str(1000 - i), "自然排名": ""} for i, (keyword, _) in enumerate(cases)]
    decisions = {str(i): {"精准度": level, "精准原因": f"{keyword}的搜索意图与当前产品事实决定该等级"} for i, (keyword, level) in enumerate(cases)}
    result = module.finalize_ai_judgments(rows, decisions)
    by_keyword = {row["词"]: row["精准度"] for row in result["rows"]}
    assert by_keyword == dict(cases)
    source = (ROOT / "scripts" / "dual_precision_csv.py").read_text(encoding="utf-8-sig")
    assert "if keyword ==" not in source and "elif keyword ==" not in source


def test_old_online_report_resolver_is_removed_from_runtime():
    source = (ROOT / "scripts" / "dual_precision_csv.py").read_text(encoding="utf-8-sig")
    assert "resolve_latest_501_online_report" not in source
    assert "discover_current_product_evidence" not in source
    assert "FIVE_0_1_PRODUCT_EVIDENCE" not in source


if __name__ == "__main__":
    from tempfile import TemporaryDirectory
    test_competitor_count_and_ratio_are_passed_through_unchanged()
    test_competitor_fields_do_not_change_precision_decisions()
    test_data_integrity_check_reports_file_a_and_file_b_field_mismatches()
    with TemporaryDirectory() as directory:
        test_501_absence_does_not_block_runtime(Path(directory))
        test_null_competitor_count_and_ratio_remain_null_and_blank_in_csv(Path(directory))
        test_run_current_602_does_not_report_full_success_after_readback_mismatch(Path(directory))
    print("6-0-2 full judgment tests: PASS")
