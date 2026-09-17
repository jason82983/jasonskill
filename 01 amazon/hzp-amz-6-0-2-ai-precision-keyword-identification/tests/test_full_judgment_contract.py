from pathlib import Path
import csv
import importlib.util
import sys

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("precision", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
_benchmark_spec = importlib.util.spec_from_file_location("benchmark_fixture", ROOT / "tests" / "test_benchmark_raw_input.py")
_benchmark_fixture = importlib.util.module_from_spec(_benchmark_spec)
_benchmark_spec.loader.exec_module(_benchmark_fixture)


def source_rows():
    return [
        {"Id": "1", "词": "wide toe box shoes", "中文": "宽鞋头鞋", "市场容量": "100", "竞争产品数": "10", "供需比": "10.0000", "对标覆盖数": "2", "最佳自然排名": "4", "自然排名中位数": "12", "精准度": "", "精准原因": ""},
        {"Id": "2", "词": "gift", "中文": "礼物", "市场容量": "300", "竞争产品数": "20", "供需比": "15.0000", "对标覆盖数": "1", "最佳自然排名": "9", "自然排名中位数": "9", "精准度": "", "精准原因": ""},
        {"Id": "3", "词": "sister necklace", "中文": "姐妹项链", "市场容量": "100", "竞争产品数": "", "供需比": "", "对标覆盖数": "3", "最佳自然排名": "5", "自然排名中位数": "8", "精准度": "", "精准原因": ""},
    ]


def _write_601(root: Path, rows=None):
    observations = []
    for row in rows or source_rows():
        observations.append({
            "所属产品编号": "BM-A", "对标ASIN": "ASIN-A", "Id": row["Id"],
            "词": row["词"], "中文": row["中文"], "市场容量": row["市场容量"],
            "竞争产品数": row["竞争产品数"], "供需比": row["供需比"],
            "自然排名": row["最佳自然排名"],
        })
    return _benchmark_fixture._write_601(root, observations)


def _reader(path):
    handle = Path(path).open(encoding="utf-8-sig", newline="")
    return csv.DictReader(handle)


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
        assert result["content_sha256"] == module.hashlib.sha256(result["product_text"].encode("utf-8")).hexdigest()
        assert result["content_size_bytes"] == len(result["product_text"].encode("utf-8"))
        assert result["modified_at_ns"] == path.stat().st_mtime_ns


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
    paths = {key: Path(result[f"{key}_output_file"] if key != "ai" else result["output_file"])
             for key in ("ai", "high_precision", "deduplicated")}
    assert len({path.parent for path in paths.values()}) == 1
    stamp = paths["ai"].stem[-15:]
    assert paths["ai"].parent == tmp_path / "06_SKILL分析报告" / module.OUTPUT_DIR
    assert all(path.stem.endswith(f"_{stamp}") for path in paths.values())
    assert paths["ai"].name.startswith("6-0-2_精准判断所有词表_")
    assert paths["high_precision"].name.startswith("6-0-2_高度精准词表_")
    assert paths["deduplicated"].name.startswith("6-0-2_去对标去重 高度精准词_")
    assert set(result["benchmark_output_files"]) == {"BM-A"}
    assert Path(result["benchmark_output_files"]["BM-A"]).name.startswith("6-0-2_BM-A_高度精准词_")
    package_files = [*paths.values(), *(Path(path) for path in result["benchmark_output_files"].values())]
    assert all(not path.with_name(path.name + ".meta.json").exists() for path in package_files)
    assert Path(result["run_manifest"]).is_file()
    assert result["input_unique_keyword_count"] == 3
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
        assert tuple(csv.reader(handle).__next__()) == module.OBSERVATION_FINAL_COLUMNS


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
    paths = {"ai": written, "high_precision": written.with_name(written.name.replace("精准判断所有词表", "高度精准词表"))}
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
    original_writer = module._write_ai_asset_pair

    def corrupt_high_precision_output(rows, paths, context, **kwargs):
        written = original_writer(rows, paths, context, **kwargs)
        high_rows = module._read_formal_csv(paths["high_precision"], module.OBSERVATION_FINAL_COLUMNS)
        high_rows[0]["竞争产品数"] = "999"
        module.write_csv(paths["high_precision"], high_rows, columns=module.OBSERVATION_FINAL_COLUMNS)
        return written

    module._write_ai_asset_pair = corrupt_high_precision_output
    try:
        result = module.run_current_602(tmp_path, "B2", {
            "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
            "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
            "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
        })
    finally:
        module._write_ai_asset_pair = original_writer
    assert result["status"] == "DATA_INTEGRITY_FAILED"
    assert "HIGH_PRECISION_FILTER_MISMATCH" in result["data_integrity"]["error_codes"]
    import json
    manifest_path = Path(result["run_folder"]) / f"{module.RUN_MANIFEST_PREFIX}{result['run_timestamp']}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["Run Status"] == "FAILED"


def test_low_level_writer_emits_three_shared_assets_for_unscoped_rows(tmp_path):
    result = module.finalize_ai_judgments(source_rows(), {
        "1": {"精准度": "高度精准", "精准原因": "具体鞋类购买意图与产品鞋头结构和穿着功能直接匹配"},
        "2": {"精准度": "弱精准", "精准原因": "仅表达泛礼物意图，未指向当前产品类别或可承接功能"},
        "3": {"精准度": "不精准", "精准原因": "搜索者明确寻找项链，和当前产品鞋类事实发生类别冲突"},
    })
    written = module.write_full_ai_csv(tmp_path, "B2", result["rows"])
    stamp = written.stem[-15:]
    paths = {
        "ai": written,
        "high_precision": written.with_name(f"6-0-2_高度精准词表_{stamp}.csv"),
        "deduplicated": written.with_name(f"6-0-2_去对标去重 高度精准词_{stamp}.csv"),
    }
    assert paths["ai"].parent == tmp_path / "06_SKILL分析报告" / module.OUTPUT_DIR
    assert all(path.exists() and path.parent == paths["ai"].parent and path.stem.endswith(f"_{stamp}") for path in paths.values())
    assert tuple(_reader(paths["ai"]).fieldnames or ()) == module.OBSERVATION_FINAL_COLUMNS
    high_reader = _reader(paths["high_precision"])
    assert tuple(high_reader.fieldnames or ()) == module.OBSERVATION_FINAL_COLUMNS
    high = list(high_reader)
    assert [row["精准度"] for row in high] == ["高度精准"]
    unique_reader = _reader(paths["deduplicated"])
    assert tuple(unique_reader.fieldnames or ()) == module.DEDUPLICATED_FINAL_COLUMNS
    unique = list(unique_reader)
    assert len(unique) == 1 and unique[0]["精准度"] == "高度精准"
    assert "所属产品编号" not in unique_reader.fieldnames
    assert not (paths["ai"].parent / "6-0-2_B2_手动分类精准词.csv").exists()



def test_one_keyword_judgment_expands_to_observations_and_deduplicates_market_facts():
    observations = [
        {"所属产品编号": "BM-A", "对标ASIN": "ASIN-A", "Id": "KW-1", "词": "sister sculpture",
         "中文": "姐妹雕塑", "市场容量": "1200", "竞争产品数": "80", "供需比": "15.0000", "自然排名": "3"},
        {"所属产品编号": "BM-B", "对标ASIN": "ASIN-B", "Id": "KW-1", "词": "sister sculpture",
         "中文": "姐妹雕塑", "市场容量": "1200", "竞争产品数": "80", "供需比": "15.0000", "自然排名": "18"},
    ]
    decision = {"精准度": "高度精准", "精准原因": "该关键词的购买需求与当前产品核心用途和商品类型直接匹配"}
    result = module.finalize_observation_judgments(observations, {"sister sculpture": decision})
    assert len(result["rows"]) == len(result["high_precision_rows"]) == 2
    assert len(result["deduplicated_rows"]) == 1
    assert {row["精准度"] for row in result["rows"]} == {"高度精准"}
    assert len({row["精准原因"] for row in result["rows"]}) == 1
    unique = result["deduplicated_rows"][0]
    assert unique["市场容量"] == "1200"
    assert unique["竞争产品数"] == "80" and unique["供需比"] == "15.0000"
    assert unique["对标覆盖数"] == 2 and unique["最佳自然排名"] == 3.0 and unique["自然排名中位数"] == 10.5
    assert "所属产品编号" not in unique


def test_run_602_uses_observation_batch_once_and_records_input_lineage(tmp_path):
    import json

    text_path = _write_text(tmp_path)
    source_file = _benchmark_fixture._write_601(tmp_path, [
        {"所属产品编号": "BM-A", "对标ASIN": "ASIN-A", "Id": "KW-SISTER", "词": "sister gifts",
         "中文": "姐妹礼物", "市场容量": "20000", "竞争产品数": "1200", "供需比": "16.6667", "自然排名": "5"},
        {"所属产品编号": "BM-B", "对标ASIN": "ASIN-B", "Id": "KW-SISTER", "词": "sister gifts",
         "中文": "姐妹礼物", "市场容量": "20000", "竞争产品数": "1200", "供需比": "16.6667", "自然排名": "18"},
    ])
    result = module.run_current_602(tmp_path, "B2", {
        "sister gifts": {"精准度": "高度精准", "精准原因": "搜索者正在寻找姐妹礼物且当前产品与该核心购买对象和场景直接匹配"},
    })

    output_a = list(_reader(result["output_file"]))
    output_b = list(_reader(result["high_precision_output_file"]))
    output_c = list(_reader(result["deduplicated_output_file"]))
    assert result["input_file"] == str(source_file)
    assert result["input_record_count"] == 2 and result["input_unique_keyword_count"] == 1
    assert len(result["keyword_units"]) == len(result["trace"]) == 1
    assert len(output_a) == len(output_b) == 2
    assert {row["所属产品编号"] for row in output_a} == {"BM-A", "BM-B"}
    assert {row["所属产品编号"] for row in output_b} == {"BM-A", "BM-B"}
    assert {row["精准度"] for row in output_a + output_b} == {"高度精准"}
    assert len(output_c) == 1
    assert output_c[0]["市场容量"] == "20000"
    assert output_c[0]["对标覆盖数"] == "2"
    assert output_c[0]["最佳自然排名"] == "5.0"
    assert output_c[0]["自然排名中位数"] == "11.5"
    assert "所属产品编号" not in output_c[0]

    manifest_path = Path(result["run_manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["Input Report Identity"] == "BENCHMARK_KEYWORD_ALL_OBSERVATIONS"
    assert manifest["Input Report Name"] == "所有对标自然排名关键词"
    assert manifest["Input RUN_TIMESTAMP"] == "20260915_120000"
    assert manifest["Input Observation Count"] == 2
    assert manifest["Input Unique Keyword Count"] == 1
    assert manifest["Expected Benchmark Count"] == 2
    assert len(manifest["Output Files"]) == len(manifest["GeneratedBenchmarkFiles"]) + 3 == 5
    assert sum(manifest["PerBenchmarkHighPrecisionRecordCount"].values()) == len(output_b)
    assert all(Path(path).exists() for path in result["benchmark_output_files"].values())
    for path in result["benchmark_output_files"].values():
        assert Path(path).stem.endswith(f"_{result['run_timestamp']}")
        assert len(list(_reader(path))) == 1
    assert manifest["Product Text Input"] == str(text_path)
    assert manifest["Product Text Input Version"]["SHA256"] == module.hashlib.sha256(text_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    assert manifest["Run Status"] == "VALID"


def test_duplicate_keyword_judgment_decisions_must_agree():
    observations = [
        {"所属产品编号": "BM-A", "对标ASIN": "ASIN-A", "Id": "KW-1", "词": "sister sculpture", "自然排名": "3"},
        {"所属产品编号": "BM-B", "对标ASIN": "ASIN-B", "Id": "KW-1", "词": "sister sculpture", "自然排名": "18"},
    ]
    try:
        module.finalize_observation_judgments(observations, {
            "KW-1": {"精准度": "高度精准", "精准原因": "该关键词购买意图与当前产品用途和商品类型直接匹配"},
            "sister sculpture": {"精准度": "精准", "精准原因": "该关键词与产品有相关性但未充分对齐核心购买用途"},
        })
    except ValueError as exc:
        assert str(exc) == "KEYWORD_JUDGMENT_INCONSISTENT"
    else:
        raise AssertionError("all observations of one canonical keyword must share one judgment")


def test_duplicate_canonical_keyword_within_one_benchmark_is_blocked():
    try:
        module._validate_benchmark_observation_uniqueness([
            {"所属产品编号": "BM-A", "词": "sister gifts"},
            {"所属产品编号": "BM-A", "词": "Sister   Gifts"},
        ])
    except ValueError as exc:
        assert str(exc) == "DUPLICATE_KEYWORD_WITHIN_BENCHMARK"
    else:
        raise AssertionError("duplicate Benchmark keyword observations must fail")


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

