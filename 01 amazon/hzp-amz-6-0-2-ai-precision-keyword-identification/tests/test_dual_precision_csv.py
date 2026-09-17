from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import importlib.util
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dual_precision_csv", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def _row(keyword, tags="", is_exact=None, proid=49727):
    return {
        "product_code": "B2",
        "erp_pro_id": proid,
        "keyword": keyword,
        "raw_fields": {
            "Keyword": keyword,
            "KeywordCn": "中文",
            "Tags": tags,
            "IsExact": is_exact,
            "SearchVolume30": 100,
            "SearchVolumeDaily": 4,
            "IsSold": 1,
            "ProId": proid,
        },
        "field_semantics": {
            "KeywordCn": {"status": "DOCUMENTED"},
            "SearchVolume30": {"status": "DOCUMENTED"},
            "SearchVolumeDaily": {"status": "DOCUMENTED"},
            "IsSold": {"status": "DOCUMENTED"},
        },
    }


def _read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_manual_path_uses_tags_and_ignores_isexact():
    rows = [
        _row("sister gift", "|1精准|", 0),
        _row("isexact only", "|2主|", 1),
        _row("null tagged", "|1精准|", None),
        _row("empty", "|1精准|", 1),
    ]
    rows[-1]["raw_fields"]["Keyword"] = ""
    rows[-1]["keyword"] = ""
    result = module.build_manual_rows(rows, product_code="B2", erp_pro_id=49727)
    assert [item["Keyword"] for item in result] == ["sister gift", "null tagged"]
    assert all(item["Manual_Is_Precision"] == "TRUE" for item in result)


def test_default_and_explicit_path_selection():
    assert module.select_paths() == ("ai", "high_precision")
    assert module.select_paths("高度精准") == ("high_precision",)
    assert module.select_paths("自动分类精准词") == ("ai", "high_precision")
    try:
        module.select_paths("手动分类精准词")
    except ValueError as exc:
        assert str(exc) == "6-0-2_MANUAL_PRECISION_OUTPUT_REMOVED"
    else:
        raise AssertionError("manual precision output must be removed")


def test_ai_blind_view_does_not_leak_tags_or_isexact():
    rows = [_row("sister gift", "|1精准|", 1), _row("wide gift", "|2主|", 0)]
    blind = module.build_ai_blind_rows(rows, product_code="B2", erp_pro_id=49727)
    encoded = json.dumps(blind, ensure_ascii=False)
    assert "Tags" not in encoded
    assert "IsExact" not in encoded
    assert "|1精准|" not in encoded
    assert len(blind) == 2


def test_ai_path_and_comparison_are_independent():
    rows = [_row("manual only", "|1精准|"), _row("ai only", "|2主|"), _row("both", "|1精准|")]
    blind = module.build_ai_blind_rows(rows, product_code="B2", erp_pro_id=49727)
    decisions = {
        "manual only": {"AI_Is_Precision": False},
        "ai only": {"AI_Is_Precision": True, "AI_Confidence": "HIGH", "AI_Reason": "直接产品购买意图", "Keyword_Search_Intent": {"Core_Intent": "ai only", "Product_Type": "product"}},
        "both": {"AI_Is_Precision": True, "AI_Confidence": "MEDIUM", "AI_Reason": "直接相关", "Keyword_Search_Intent": {"Core_Intent": "both", "Product_Type": "product"}},
    }
    context = {"Core_Product_Type": "manual ai both product", "Compatible_Search_Intents": ["manual only", "ai only", "both"]}
    ai = module.build_ai_classified_rows(blind, decisions, product_code="B2", erp_pro_id=49727, product_context=context)
    manual = module.build_manual_rows(rows, product_code="B2", erp_pro_id=49727)
    status = module.compare_precision_sets(manual, ai)
    assert status == {
        ("B2", "49727", "ai only"): "AI_ONLY",
        ("B2", "49727", "both"): "BOTH_PRECISION",
        ("B2", "49727", "manual only"): "MANUAL_ONLY",
    }
    assert all("AI_Reason" in item for item in ai)


def test_benchmark_evidence_is_separate_and_rank_requires_documented_semantics():
    benchmark_rows = [
        {
            "erp_pro_id": 49726,
            "keyword": "sister gift",
            "raw_fields": {"Keyword": "sister gift", "Tags": "|1精准|", "RankOra": 3},
            "field_semantics": {"RankOra": {"status": "DOCUMENTED", "meaning": "自然排名"}},
        },
        {
            "erp_pro_id": 49725,
            "keyword": "sister gift",
            "raw_fields": {"Keyword": "sister gift", "Tags": "|1精准|", "RankOra": 8},
            "field_semantics": {"RankOra": {"status": "DOCUMENTED", "meaning": "自然排名"}},
        },
    ]
    evidence = module.build_benchmark_evidence(
        [{"erp_pro_id": 49726, "rows": [benchmark_rows[0]]}, {"erp_pro_id": 49725, "rows": [benchmark_rows[1]]}],
        benchmark_erp_pro_ids=[49726, 49725],
    )
    assert evidence["sister gift"]["Benchmark_Count"] == 2
    assert evidence["sister gift"]["Benchmark_Keyword_Coverage"] == 1.0
    assert evidence["sister gift"]["Best_Benchmark_Organic_Rank"] == 3
    assert evidence["sister gift"]["Median_Benchmark_Organic_Rank"] == 5.5

    uncertain = module.build_benchmark_evidence(
        [{"erp_pro_id": 49726, "rows": [{
            "erp_pro_id": 49726,
            "keyword": "sister gift",
            "raw_fields": {"Keyword": "sister gift", "Tags": "|1精准|", "RankOra": 1},
            "field_semantics": {"RankOra": {"status": "SEMANTICS_UNCERTAIN", "meaning": None}},
        }]}],
        benchmark_erp_pro_ids=[49726],
    )
    assert uncertain["sister gift"]["Benchmark_Organic_Evidence"] == module.BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE


def test_ai_csv_keeps_benchmark_as_evidence_not_precision_label():
    blind = module.build_ai_blind_rows([_row("sister sculpture", "|1精准|")], product_code="B2", erp_pro_id=49727)
    evidence = {"sister sculpture": {
        "Benchmark_ERP_ProIds": "49726",
        "Benchmark_Count": 1,
        "Benchmark_Keyword_Coverage": 1.0,
        "Benchmark_Organic_Evidence": module.BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE,
        "Best_Benchmark_Organic_Rank": module.DATA_NOT_AVAILABLE,
        "Median_Benchmark_Organic_Rank": module.DATA_NOT_AVAILABLE,
        "Evidence_Summary": "benchmark only",
    }}
    ai = module.build_ai_classified_rows(
        blind,
        {"sister sculpture": {"AI_Is_Precision": True, "AI_Confidence": "HIGH", "AI_Reason": "姐妹纪念雕塑购买意图明确"}},
        product_code="B2",
        erp_pro_id=49727,
        benchmark_evidence=evidence,
        product_context=_sister_profile(),
    )
    assert ai[0]["AI_Is_Precision"] is True
    assert ai[0]["Current_ERP_ProId"] == 49727
    assert ai[0]["Benchmark_Count"] == 1
    assert ai[0]["Benchmark_Organic_Evidence"] == module.BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE
    assert "|1精准|" not in json.dumps(ai, ensure_ascii=False)


def test_ai_three_states_retain_all_keywords_and_join_manual_label_after_blind_classification():
    rows = [_row("sculpture precision", "|1精准|"), _row("not precision"), _row("sculpture needs review")]
    blind = module.build_ai_blind_rows(rows, product_code="B2", erp_pro_id=49727)
    decisions = {
        "sculpture precision": {"AI_Classification": "PRECISION", "AI_Confidence": "HIGH", "AI_Reason": "雕塑购买意图"},
        "not precision": {"AI_Classification": "NOT_PRECISION", "AI_Confidence": "HIGH", "AI_Reason": "产品不匹配"},
        "sculpture needs review": {"AI_Classification": "REVIEW_REQUIRED", "AI_Confidence": "LOW", "AI_Reason": "证据不足"},
    }
    result = module.build_ai_classified_rows(blind, decisions, product_code="B2", erp_pro_id=49727, source_rows=rows, product_context=_sister_profile())
    assert {row["AI_Classification"] for row in result} == {"PRECISION", "NOT_PRECISION", "REVIEW_REQUIRED"}
    by_keyword = {row["Keyword"]: row for row in result}
    assert by_keyword["sculpture precision"]["Manual_Precision_Label"] == "PRECISION"
    assert by_keyword["sculpture precision"]["Comparison_Status"] == "BOTH_PRECISION"
    assert by_keyword["not precision"]["Comparison_Status"] == "BOTH_NOT_PRECISION"
    assert by_keyword["sculpture needs review"]["Comparison_Status"] == "REVIEW_REQUIRED"
    # SearchVolume30 is inherited from the 6-0-1 market-fact row in the
    # canonical runtime, not from this legacy ERP-row helper.
    assert by_keyword["sculpture precision"]["SearchVolumeDaily"] == 4
    assert by_keyword["sculpture precision"]["Tags"] == "|1精准|"
    assert "|1精准|" not in json.dumps(blind, ensure_ascii=False)


def test_ai_missing_context_is_explicitly_unavailable():
    blind = module.build_ai_blind_rows([_row("one")], product_code="B2", erp_pro_id=49727)
    result = module.build_ai_classified_rows(
        blind, {"one": {"AI_Classification": "REVIEW_REQUIRED", "AI_Reason": "缺少产品画像"}},
        product_code="B2", erp_pro_id=49727,
    )
    assert result[0]["Marketplace"] == module.DATA_NOT_AVAILABLE
    assert result[0]["ASIN"] == module.DATA_NOT_AVAILABLE
    assert result[0]["Organic_Rank"] == module.DATA_NOT_AVAILABLE


def test_datetime_quality_evidence_is_serializable():
    row = _row("dated", "|1精准|")
    row["raw_fields"]["UpdateTime"] = datetime(2026, 9, 15, 12, 0, 0)
    row["field_semantics"]["UpdateTime"] = {"status": "DOCUMENTED"}
    blind = module.build_ai_blind_rows([row], product_code="B2", erp_pro_id=49727)
    result = module.build_ai_classified_rows(
        blind, {"dated": {"AI_Classification": "PRECISION", "AI_Reason": "直接意图"}},
        product_code="B2", erp_pro_id=49727, source_rows=[row],
        product_context={"Core_Product_Type": "dated product"},
    )
    assert "2026-09-15" in result[0]["Current_Product_ERP_Evidence"]


def test_comparison_can_preserve_neither_from_complete_keyword_universe():
    status = module.compare_precision_sets(
        [{"Product_Code": "B2", "ERP_ProId": 49727, "Keyword": "manual"}],
        [{"Product_Code": "B2", "ERP_ProId": 49727, "Keyword": "ai"}],
        all_keywords=[
            {"Product_Code": "B2", "ERP_ProId": 49727, "Keyword": "manual"},
            {"Product_Code": "B2", "ERP_ProId": 49727, "Keyword": "ai"},
            {"Product_Code": "B2", "ERP_ProId": 49727, "Keyword": "neither"},
        ],
    )
    assert status[("B2", "49727", "neither")] == "NEITHER"


def test_comparison_key_isolates_same_keyword_across_products():
    status = module.compare_precision_sets(
        [{"Product_Code": "B2", "ERP_ProId": 49727, "Keyword": "chain gift"}],
        [{"Product_Code": "A3", "ERP_ProId": 812, "Keyword": "chain gift", "AI_Classification": "PRECISION"}],
    )
    assert status[("B2", "49727", "chain gift")] == "MANUAL_ONLY"
    assert status[("A3", "812", "chain gift")] == "AI_ONLY"


def test_complete_query_is_called_once_and_csv_has_bom(tmp_path):
    calls = []
    data = [_row("one", "|1精准|")]
    dual = module.build_dual_views(lambda: (calls.append(1) or data), product_code="B2", erp_pro_id=49727)
    assert len(calls) == 1
    paths = module.write_dual_csvs(tmp_path, "B2", dual["manual_rows"], dual["ai_blind_rows"])
    assert paths["ai"].name.startswith("6-0-2_精准判断所有词表_") and paths["ai"].suffix == ".csv"
    assert paths["high_precision"].name.startswith("6-0-2_筛选后的对标精准词_") and paths["high_precision"].suffix == ".csv"
    assert paths["deduplicated"].name.startswith("6-0-2_去对标去重_筛选后的精准词_") and paths["deduplicated"].suffix == ".csv"
    fixed = [paths[key] for key in ("ai", "high_precision", "deduplicated_benchmark", "deduplicated")]
    assert len({path.parent for path in fixed}) == 1
    assert len({path.stem.rsplit("_", 1)[-1] for path in fixed}) == 1
    for path in fixed:
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")
        assert not path.with_name(path.name + ".meta.json").exists()


def test_empty_result_keeps_only_final_header(tmp_path):
    paths = module.write_dual_csvs(tmp_path, "B2", [], [])
    observation_header = ",".join(module.OBSERVATION_FINAL_COLUMNS)
    deduplicated_header = ",".join(module.DEDUPLICATED_FINAL_COLUMNS)
    assert paths["ai"].read_text(encoding="utf-8-sig").splitlines() == [observation_header]
    assert paths["high_precision"].read_text(encoding="utf-8-sig").splitlines() == [observation_header]
    assert paths["deduplicated"].read_text(encoding="utf-8-sig").splitlines() == [deduplicated_header]


def test_output_paths_exclude_formal_index_root():
    paths = module.output_paths(r"E:\\Products\\B2", "B2")
    assert "manual" not in paths
    assert "06_SKILL分析报告" in str(paths["ai"])
    assert "6-0-2_AI精准关键词识别" in str(paths["ai"])
    assert paths["ai"].name.startswith("6-0-2_精准判断所有词表_") and paths["ai"].suffix == ".csv"
    assert paths["high_precision"].name.startswith("6-0-2_筛选后的对标精准词_") and paths["high_precision"].suffix == ".csv"
    assert paths["deduplicated"].name.startswith("6-0-2_去对标去重_筛选后的精准词_") and paths["deduplicated"].suffix == ".csv"
    fixed = [paths[key] for key in ("ai", "high_precision", "deduplicated_benchmark", "deduplicated")]
    assert len({path.parent for path in fixed}) == 1
    assert len({path.stem.rsplit("_", 1)[-1] for path in fixed}) == 1


def test_low_level_writer_writes_three_shared_assets_for_unscoped_rows(tmp_path):
    config = tmp_path / "01_公共资料" / "03_系统配置" / "生成精准词库的要求.txt"
    config.parent.mkdir(parents=True)
    config.write_text("高度精准\n精准\n", encoding="utf-8")
    rows = [
        {"Id": "1", "词": "high term", "中文": "高", "市场容量": "500", "竞争产品数": "50", "供需比": "10.0000", "对标覆盖数": "2", "最佳自然排名": "1", "自然排名中位数": "2", "精准度": "高度精准", "精准原因": "具体商品意图与产品事实高度匹配"},
        {"Id": "2", "词": "regular term", "中文": "普", "市场容量": "400", "竞争产品数": "40", "供需比": "10.0000", "对标覆盖数": "1", "最佳自然排名": "2", "自然排名中位数": "2", "精准度": "精准", "精准原因": "主要购买意图匹配但存在扩散"},
        {"Id": "3", "词": "weak term", "中文": "弱", "市场容量": "300", "竞争产品数": "30", "供需比": "10.0000", "对标覆盖数": "3", "最佳自然排名": "3", "自然排名中位数": "4", "精准度": "弱精准", "精准原因": "相关但商品类型未收敛"},
        {"Id": "4", "词": "wrong term", "中文": "错", "市场容量": "200", "竞争产品数": "20", "供需比": "10.0000", "对标覆盖数": "1", "最佳自然排名": "4", "自然排名中位数": "4", "精准度": "不精准", "精准原因": "商品类型冲突"},
    ]
    ai_path = module.write_full_ai_csv(tmp_path, "B2", rows, write_metadata=False)
    stamp = ai_path.stem[-15:]
    assert ai_path.parent == tmp_path / "06_SKILL分析报告" / module.OUTPUT_DIR / "data"
    high_precision_path = ai_path.with_name(ai_path.name.replace("精准判断所有词表", "筛选后的对标精准词"))
    deduplicated_benchmark_path = ai_path.with_name(ai_path.name.replace("精准判断所有词表", "去重_筛选后的对标精准词"))
    deduplicated_path = ai_path.with_name(ai_path.name.replace("精准判断所有词表", "去对标去重_筛选后的精准词"))
    assert ai_path.stem.endswith(f"_{stamp}")
    assert high_precision_path.is_file() and deduplicated_benchmark_path.is_file() and deduplicated_path.is_file()
    assert tuple(_read_csv(ai_path)[0]) == module.OBSERVATION_FINAL_COLUMNS
    high = _read_csv(high_precision_path)
    assert [row["词"] for row in high] == ["high term", "regular term"]
    unique = _read_csv(deduplicated_path)
    assert tuple(unique[0]) == module.DEDUPLICATED_FINAL_COLUMNS
    assert [row["词"] for row in unique] == ["high term", "regular term"]
    assert "所属产品编号" not in unique[0]

def test_final_ai_rows_sort_search_volume_descending_with_missing_last_and_stable_ties():
    rows = []
    for record_id, keyword, volume in (
        (1, "low", 10),
        (2, "tie-first", 100),
        (3, "missing", "not-a-number"),
        (4, "high", 300),
        (5, "tie-second", 100),
        (6, "empty", None),
    ):
        row = _row(keyword)
        row.update(record_id=record_id, record_id_status="DOCUMENTED_STABLE",
                   SearchVolume30=volume, AI_Classification="PRECISION",
                   AI_Reason="fit", AI_Precision_Score=80)
        rows.append(row)
    result = module.build_final_ai_rows(rows)
    assert [row["关键词"] for row in result] == [
        "high", "tie-first", "tie-second", "low", "missing", "empty"
    ]
    assert [row["搜索量"] for row in result[-2:]] == [module.DATA_NOT_AVAILABLE, module.DATA_NOT_AVAILABLE]


def test_final_manual_rows_use_the_same_stable_search_volume_sort():
    try:
        module.select_paths("manual")
    except ValueError as exc:
        assert str(exc) == "6-0-2_MANUAL_PRECISION_OUTPUT_REMOVED"
    else:
        raise AssertionError("manual precision CSV output is not part of the current contract")


def test_search_volume_sort_does_not_change_precision_classification():
    rows = []
    for record_id, keyword, volume, state in (
        (21, "precision-high", 900, "PRECISION"),
        (22, "not-precision-low", 1, "NOT_PRECISION"),
        (23, "precision-missing", None, "PRECISION"),
    ):
        row = _row(keyword)
        row.update(record_id=record_id, record_id_status="DOCUMENTED_STABLE",
                   SearchVolume30=volume, AI_Classification=state,
                   AI_Reason="reason", AI_Precision_Score=80)
        rows.append(row)
    result = module.build_final_ai_rows(rows)
    assert {row["关键词"] for row in result} == {"precision-high", "precision-missing"}
    assert [row["关键词"] for row in result] == ["precision-high", "precision-missing"]


def test_missing_keyword_cn_can_use_translation_and_score_is_bounded():
    rows = [{"Keyword": "sister gift", "SearchVolume30": 10, "AI_Classification": "PRECISION",
             "AI_Reason": "关系礼赠意图明确", "AI_Precision_Score": 101}]
    result = module.build_final_ai_rows(rows, translations={"sister gift": "姐妹礼物"})
    assert result == []


def test_record_id_never_guesses_raw_id_without_documented_identity():
    row = _row("duplicate term", "|1精准|")
    row["raw_fields"]["Id"] = 101
    row["raw_fields"]["KwId"] = 202
    assert module.build_final_manual_rows(module.build_manual_rows([row], product_code="B2", erp_pro_id=49727)) == []
    blind = module.build_ai_blind_rows([_row("same"), _row("same")], product_code="B2", erp_pro_id=49727)
    source = [_row("same"), _row("same")]
    result = module.build_ai_classified_rows(
        blind, {"same": {"AI_Classification": "PRECISION", "AI_Reason": "fit"}},
        product_code="B2", erp_pro_id=49727, source_rows=source,
    )
    assert result[0]["record_id_status"] == module.ERP_KEYWORD_RECORD_ID_UNCONFIRMED


def _benchmark_result(pro_id, *keywords, rank=None, tags="|1精准|", record_ids=None):
    rows = []
    for index, keyword in enumerate(keywords):
        row = {
            "erp_pro_id": pro_id,
            "keyword": keyword,
            "raw_fields": {"Keyword": keyword, "KeywordCn": "中文", "Tags": tags, "IsExact": 1},
            "field_semantics": {},
        }
        if rank is not None:
            row["raw_fields"]["RankOra"] = rank
            row["field_semantics"]["RankOra"] = {"status": "DOCUMENTED", "meaning": "自然排名"}
        if record_ids:
            row["record_id"] = record_ids[index]
            row["record_id_status"] = "DOCUMENTED_STABLE"
        rows.append(row)
    return {"erp_pro_id": pro_id, "rows": rows}


def test_keyword_source_modes_cover_own_first_and_benchmark_fallback():
    own = [_row("own term")]
    benchmark = [_benchmark_result(49726, "bench term")]
    assert module.choose_keyword_source_mode(own, benchmark) == module.OWN_ONLY
    assert module.choose_keyword_source_mode([], benchmark) == module.BENCHMARK_FALLBACK
    assert module.choose_keyword_source_mode(own, benchmark, own_keywords_sufficient=False) == module.OWN_PLUS_BENCHMARK
    assert module.choose_keyword_source_mode([], []) == module.OWN_ONLY


def test_candidate_pool_marks_no_benchmark_data_insufficiency():
    pool = module.build_keyword_candidate_pool([], [], product_code="B2", erp_pro_id=49727)
    assert pool["status"] == module.KEYWORD_SOURCE_DATA_INSUFFICIENT
    assert pool["candidates"] == []
    assert module.keyword_source_summary(pool)["Keyword Source Status"] == module.KEYWORD_SOURCE_DATA_INSUFFICIENT


def test_benchmark_candidate_is_blind_and_never_leaks_precision_tags_or_id():
    pool = module.build_keyword_candidate_pool([], [_benchmark_result(49726, "bench term", record_ids=[2000])], product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726])
    candidate = pool["candidates"][0]
    encoded = json.dumps(candidate, ensure_ascii=False)
    assert candidate["record_id_status"] == "DOCUMENTED_STABLE"
    assert candidate["record_id"] == 2000
    assert "Tags" not in encoded and "IsExact" not in encoded and "raw_fields" not in encoded
    assert "|1精准|" not in encoded and "49726" not in str(candidate.get("record_id"))


def test_multi_benchmark_keywords_dedupe_and_retain_coverage():
    results = [_benchmark_result(49726, "Bench Term", rank=4, record_ids=[100]), _benchmark_result(49725, "bench  term", rank=9, record_ids=[200])]
    pool = module.build_keyword_candidate_pool([], results, product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726, 49725])
    assert len(pool["candidates"]) == 2
    assert pool["deduplicated_candidate_keywords"] == 1
    evidence = pool["benchmark_evidence"]["bench term"]
    assert evidence["Benchmark_Count"] == 2
    assert evidence["Benchmark_Keyword_Coverage"] == 1.0
    assert evidence["Best_Benchmark_Organic_Rank"] == 4


def test_candidate_pool_ignores_unconfigured_benchmark_results():
    results = [_benchmark_result(49726, "allowed term", record_ids=[10]), _benchmark_result(99999, "unbound term", record_ids=[20])]
    pool = module.build_keyword_candidate_pool([], results, product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726])
    assert [row["Keyword"] for row in pool["candidates"]] == ["allowed term"]


def test_benchmark_keyword_existing_in_own_pool_uses_current_record_id():
    own = _row("shared term")
    own["record_id"] = 321
    own["record_id_status"] = "DOCUMENTED_STABLE"
    pool = module.build_keyword_candidate_pool([own], [_benchmark_result(49726, "shared term")], product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726])
    candidate = pool["candidates"][0]
    assert candidate["record_id"] == 321
    assert candidate["record_id_status"] == "DOCUMENTED_STABLE"
    assert candidate["ERP_ProId"] == 49727


def test_same_keyword_own_and_benchmark_ids_are_both_retained_when_expanded():
    own = _row("shared term")
    own.update(record_id=321, record_id_status="DOCUMENTED_STABLE")
    benchmark = _benchmark_result(49726, "shared term", record_ids=[654])
    pool = module.build_keyword_candidate_pool([own], [benchmark], product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726], own_keywords_sufficient=False)
    assert {row["record_id"] for row in pool["candidates"]} == {321, 654}
    assert pool["deduplicated_candidate_keywords"] == 1


def test_same_record_id_and_keyword_is_not_duplicated_across_sources():
    own = _row("shared term")
    own.update(record_id=321, record_id_status="DOCUMENTED_STABLE")
    benchmark = _benchmark_result(49726, "shared term", record_ids=[321])
    pool = module.build_keyword_candidate_pool([own], [benchmark], product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726], own_keywords_sufficient=False)
    assert [row["record_id"] for row in pool["candidates"]] == [321]


def test_normalized_keyword_uses_one_ai_decision_for_multiple_records():
    rows = []
    for record_id, keyword in ((101, "shared term"), (201, "Shared  term")):
        row = _row(keyword)
        row.update(record_id=record_id, record_id_status="DOCUMENTED_STABLE")
        rows.append(row)
    blind = module.build_ai_blind_rows(rows, product_code="B2", erp_pro_id=49727)
    classified = module.build_ai_classified_rows(
        blind,
        {"shared term": {"AI_Classification": "PRECISION", "AI_Precision_Score": 88, "AI_Reason": "one judgment", "Keyword_Search_Intent": {"Core_Intent": "shared term", "Product_Type": "product"}}},
        product_code="B2", erp_pro_id=49727, source_rows=rows,
        product_context={"Core_Product_Type": "shared term product"},
    )
    assert len(classified) == 2
    assert {row["AI_Classification"] for row in classified} == {"PRECISION"}


def test_benchmark_record_id_is_retained_even_when_proid_differs():
    pool = module.build_keyword_candidate_pool([], [_benchmark_result(49726, "bench term", record_ids=[2001])], product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726])
    candidate = pool["candidates"][0]
    assert candidate["record_id"] == 2001
    assert candidate["ERP_ProId"] == "49726"
    assert candidate["Current_ERP_ProId"] == 49727


def test_benchmark_only_precision_keeps_missing_current_record_marker_in_final_csv():
    pool = module.build_keyword_candidate_pool([], [_benchmark_result(49726, "bench term")], product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726])
    ai = module.build_ai_classified_rows(pool["unresolved_candidates"], {"bench term": {"AI_Classification": "PRECISION", "AI_Precision_Score": 80, "AI_Reason": "意图匹配", "Keyword_Search_Intent": {"Core_Intent": "bench term", "Product_Type": "product"}}}, product_code="B2", erp_pro_id=49727, benchmark_evidence=pool["benchmark_evidence"])
    assert ai[0]["record_id_status"] == module.ERP_KEYWORD_RECORD_ID_UNCONFIRMED
    assert module.build_final_ai_rows(ai) == []


def test_duplicate_own_keyword_ids_are_retained_as_distinct_records():
    first = _row("duplicate")
    second = _row("duplicate")
    first.update(record_id=1, record_id_status="DOCUMENTED_STABLE")
    second.update(record_id=2, record_id_status="DOCUMENTED_STABLE")
    pool = module.build_keyword_candidate_pool([first, second], [], product_code="B2", erp_pro_id=49727)
    assert {row["record_id"] for row in pool["candidates"]} == {1, 2}


def test_same_record_id_different_keywords_is_blocked_from_normal_candidates():
    first = _row("first")
    second = _row("second")
    first.update(record_id=9, record_id_status="DOCUMENTED_STABLE")
    second.update(record_id=9, record_id_status="DOCUMENTED_STABLE")
    pool = module.build_keyword_candidate_pool([first, second], [], product_code="B2", erp_pro_id=49727)
    assert pool["identity_conflicts"] == ["9"]
    assert pool["candidates"] == []


def test_same_keyword_multiple_record_ids_emit_multiple_final_rows():
    rows = []
    for record_id in (1001, 2001, 3001):
        row = _row("sister birthday gifts")
        row.update(record_id=record_id, record_id_status="DOCUMENTED_STABLE")
        row["AI_Classification"] = "PRECISION"
        row["AI_Reason"] = "意图匹配"
        row["AI_Precision_Score"] = 90
        rows.append(row)
    final = module.build_final_ai_rows(rows)
    assert [row["自动编号"] for row in final] == ["1001", "2001", "3001"]


def test_same_record_id_conflict_is_blocked_across_ai_states():
    precision = _row("precision term")
    precision.update(record_id=77, record_id_status="DOCUMENTED_STABLE", AI_Classification="PRECISION", AI_Precision_Score=90, AI_Reason="match")
    rejected = _row("different term")
    rejected.update(record_id=77, record_id_status="DOCUMENTED_STABLE", AI_Classification="NOT_PRECISION", AI_Precision_Score=10, AI_Reason="mismatch")
    assert module.build_final_ai_rows([precision, rejected]) == []


def test_source_summary_counts_benchmark_precision_without_record_id():
    pool = module.build_keyword_candidate_pool([], [_benchmark_result(49726, "bench term")], product_code="B2", erp_pro_id=49727, benchmark_erp_pro_ids=[49726])
    ai = module.build_ai_classified_rows(pool["unresolved_candidates"], {"bench term": {"AI_Classification": "PRECISION", "AI_Reason": "明确商品购买意图与事实匹配", "Keyword_Search_Intent": {"Core_Intent": "bench term", "Product_Type": "product"}}}, product_code="B2", erp_pro_id=49727, benchmark_evidence=pool["benchmark_evidence"], product_context={"Core_Product_Type": "bench term product"})
    summary = module.keyword_source_summary(pool, ai)
    assert summary["Keyword Source Mode"] == module.BENCHMARK_FALLBACK
    assert summary["Benchmark Precision Candidates Without ERP Record ID"] == 1


def test_no_sql_write_tokens_or_benchmark_id_writeback_path():
    source = (ROOT / "scripts" / "dual_precision_csv.py").read_text(encoding="utf-8-sig").upper()
    assert "INSERT INTO PICKPWK" not in source
    assert "UPDATE PICKPWK" not in source
    assert "DELETE FROM PICKPWK" not in source
    assert "BENCHMARK_ERP_PROID" in source


def _sister_profile():
    return {
        "Core_Product_Type": "sister gift sculpture",
        "Recipient": "sister",
        "Relationship_Intent": "sister",
        "Purchase_Occasions": ["birthday", "gift giving"],
        "Compatible_Search_Intents": ["sister gifts", "sister birthday gifts"],
        "Core_Attributes": ["sculpture", "keepsake"],
    }


def test_semantic_sister_gifts_is_gift_led_core_fit():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister gifts", "Recipient": "sister"})
    assert result["AI_Classification"] == "PRECISION"


def test_semantic_sister_birthday_gifts_is_gift_led_core_fit():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister birthday gifts", "Purchase_Occasions": "birthday"})
    assert result["AI_Classification"] == "PRECISION"


def test_generic_gift_and_recipient_terms_follow_current_kernel():
    profile = _sister_profile()
    for keyword, expected in (("gift", "NOT_PRECISION"), ("sister", "PRECISION"), ("birthday gifts", "NOT_PRECISION")):
        result = module.evaluate_product_search_intent_fit(profile, {"Core_Intent": keyword}, keyword=keyword)
        assert result["AI_Classification"] == expected


def test_concrete_single_product_term_can_be_precision():
    result = module.evaluate_product_search_intent_fit(
        _sister_profile(), {"Core_Intent": "sculpture"}, keyword="sculpture"
    )
    assert result["AI_Classification"] == "PRECISION"
    assert "sculpture" in result["AI_Reason"]


def test_broad_use_case_does_not_pass_intrinsic_precision():
    profile = {
        "Core_Product_Type": "furniture anti-tip anchor",
        "Core_Use_Cases": ["baby proofing"],
        "Core_Functions": ["anchor furniture to wall"],
    }
    result = module.evaluate_product_search_intent_fit(
        profile, {"Core_Intent": "baby proofing"}, keyword="baby proofing"
    )
    assert result["AI_Classification"] == "REVIEW_REQUIRED"


def test_benchmark_rank_supports_but_does_not_create_precision():
    profile = {"Core_Product_Type": "furniture anti-tip anchor"}
    support = {"Benchmark_Organic_Evidence": "AVAILABLE", "Benchmark_Organic_Rank_Count": 3}
    result = module.evaluate_product_search_intent_fit(
        profile, {"Core_Intent": "dresser wall anchor"}, keyword="dresser wall anchor",
        supporting_evidence=support,
    )
    assert result["AI_Classification"] == "PRECISION"

    broad = module.evaluate_product_search_intent_fit(
        profile, {"Core_Intent": "baby proofing"}, keyword="baby proofing",
        supporting_evidence={"Benchmark_Organic_Evidence": "AVAILABLE", "Benchmark_Organic_Rank_Count": 3},
    )
    assert broad["AI_Classification"] == "REVIEW_REQUIRED"


def test_semantic_benchmark_conflict_enters_review_without_flipping_to_precision():
    profile = {"Core_Product_Type": "furniture anti-tip anchor"}
    result = module.evaluate_product_search_intent_fit(
        profile, {"Core_Intent": "dresser wall anchor"}, keyword="dresser wall anchor",
        supporting_evidence={"Benchmark_Organic_Evidence": "CONTRADICTING", "Benchmark_Organic_Rank_Count": 0},
    )
    assert result["AI_Classification"] == "PRECISION"
    assert result["Product_Intent_Fit"] == "CORE_FIT"


def test_semantic_wrong_card_type_is_hard_conflict():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister birthday card", "Product_Type": "card"})
    assert result["AI_Classification"] == "NOT_PRECISION"
    assert "Product Type Conflict" in result["AI_Reason"]


def test_semantic_no_drill_conflicts_with_drilling_product():
    profile = {"Core_Product_Type": "furniture anchor", "Hard_Intent_Conflicts": ["product requires drilling"]}
    result = module.evaluate_product_search_intent_fit(profile, {"Core_Intent": "no drill furniture anchor", "Installation_Method": "no drill"})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_semantic_function_conflict_is_hard_conflict():
    profile = {"Core_Product_Type": "gift", "Core_Functions": ["display keepsake"]}
    result = module.evaluate_product_search_intent_fit(profile, {"Core_Intent": "gift", "Core_Functions": "wireless charging"})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_semantic_compatibility_conflict_is_hard_conflict():
    profile = {"Core_Product_Type": "phone case", "Compatibility": ["iPhone 15"]}
    result = module.evaluate_product_search_intent_fit(profile, {"Core_Intent": "phone case", "Compatibility": "iPhone 17"})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_high_volume_wrong_intent_stays_not_precision():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister birthday card", "Product_Type": "card"}, supporting_evidence={"SearchVolume30": 100000})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_low_volume_high_fit_stays_precision():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister sculpture"}, supporting_evidence={"SearchVolume30": 20})
    assert result["AI_Classification"] == "PRECISION"


def test_high_cpc_does_not_override_semantic_fit():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister sculpture"}, supporting_evidence={"CPC": 9})
    assert result["AI_Classification"] == "PRECISION"


def test_high_acos_does_not_override_semantic_fit():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister sculpture"}, supporting_evidence={"ACoS": 2.5})
    assert result["AI_Classification"] == "PRECISION"


def test_low_cvr_does_not_override_semantic_fit():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister sculpture"}, supporting_evidence={"CVR": 0.01})
    assert result["AI_Classification"] == "PRECISION"


def test_one_accidental_order_does_not_override_wrong_intent():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister birthday card", "Product_Type": "card"}, supporting_evidence={"Orders": 1})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_benchmark_precision_tag_is_not_a_label():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister sculpture"}, supporting_evidence={"Tags": "|1精准|"})
    assert result["AI_Classification"] == "PRECISION"
    assert result["AI_Reason"] != "|1精准|"


def test_benchmark_rank_is_supporting_only():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister birthday card", "Product_Type": "card"}, supporting_evidence={"Best_Benchmark_Organic_Rank": 1})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_multiple_benchmarks_do_not_vote_precision():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister birthday card", "Product_Type": "card"}, supporting_evidence={"Benchmark_Count": 5})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_unspecified_product_type_can_still_be_precision():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister sculpture", "Recipient": "sister"})
    assert result["AI_Classification"] == "PRECISION"


def test_explicit_wrong_product_type_is_blocked():
    result = module.evaluate_product_search_intent_fit(_sister_profile(), {"Core_Intent": "sister gifts", "Product_Type": "card"})
    assert result["AI_Classification"] == "NOT_PRECISION"


def test_unknown_required_attribute_requires_review():
    result = module.evaluate_product_search_intent_fit({"Core_Product_Type": "sister gift"}, {"Core_Intent": "sister gifts", "Attributes": ["waterproof"]})
    assert result["AI_Classification"] == "REVIEW_REQUIRED"


def test_duplicate_ids_share_one_semantic_judgment_and_expand_rows():
    profile = _sister_profile()
    fit = module.evaluate_product_search_intent_fit(profile, {"Core_Intent": "sister sculpture"})
    assert fit["AI_Classification"] == "PRECISION"
    assert fit["AI_Classification"] == module.evaluate_product_search_intent_fit(profile, {"Core_Intent": "sister sculpture"})["AI_Classification"]


def test_multiple_real_ids_remain_output_rows():
    rows = []
    for record_id in (11, 12):
        row = _row("sister gifts")
        row.update(record_id=record_id, record_id_status="DOCUMENTED_STABLE", AI_Classification="PRECISION", AI_Reason="核心赠礼意图匹配", AI_Precision_Score=90)
        rows.append(row)
    assert [r["自动编号"] for r in module.build_final_ai_rows(rows)] == ["11", "12"]


def test_benchmark_record_id_is_allowed_after_independent_semantic_fit():
    row = _row("sister gifts", proid=700)
    row.update(record_id=55, record_id_status="DOCUMENTED_STABLE", AI_Classification="PRECISION", AI_Reason="核心赠礼意图匹配", AI_Precision_Score=90)
    assert module.build_final_ai_rows([row])[0]["自动编号"] == "55"


def test_semantic_guardrail_vetoes_precision_claim_on_hard_conflict():
    row = _row("sister card")
    row.update(record_id=91, record_id_status="DOCUMENTED_STABLE")
    blind = module.build_ai_blind_rows([row], product_code="B2", erp_pro_id=49727)
    decision = {"sister card": {"AI_Classification": "PRECISION", "AI_Reason": "candidate", "Keyword_Search_Intent": {"Core_Intent": "sister card", "Product_Type": "card"}}}
    classified = module.build_ai_classified_rows(blind, decision, product_code="B2", erp_pro_id=49727, product_context=_sister_profile(), source_rows=[row])
    assert classified[0]["AI_Classification"] == "NOT_PRECISION"


def test_generic_precision_reason_is_reviewed_instead_of_accepted():
    row = _row("gift")
    row.update(record_id=92, record_id_status="DOCUMENTED_STABLE")
    blind = module.build_ai_blind_rows([row], product_code="B2", erp_pro_id=49727)
    decision = {"gift": {"AI_Classification": "PRECISION", "AI_Precision_Score": 92,
                          "AI_Reason": "核心搜索意图与产品语义画像在购买对象/场景/功能上直接匹配"}}
    classified = module.build_ai_classified_rows(
        blind, decision, product_code="B2", erp_pro_id=49727,
        product_context=_sister_profile(), source_rows=[row],
    )
    assert classified[0]["AI_Classification"] == "NOT_PRECISION"


def test_semantic_guardrail_does_not_use_sql_write():
    source = (ROOT / "scripts" / "dual_precision_csv.py").read_text(encoding="utf-8-sig").upper()
    assert all(token not in source for token in ("INSERT INTO", "UPDATE PICKPWK", "DELETE FROM"))


if __name__ == "__main__":
    test_manual_path_uses_tags_and_ignores_isexact()
    test_ai_blind_view_does_not_leak_tags_or_isexact()
    test_ai_path_and_comparison_are_independent()
    test_ai_three_states_retain_all_keywords_and_join_manual_label_after_blind_classification()
    test_ai_missing_context_is_explicitly_unavailable()
    with TemporaryDirectory() as directory:
        test_complete_query_is_called_once_and_csv_has_bom(Path(directory))
        test_empty_result_keeps_only_final_header(Path(directory))
    test_output_paths_exclude_formal_index_root()
    print("6-0-2 dual precision CSV tests: PASS")




