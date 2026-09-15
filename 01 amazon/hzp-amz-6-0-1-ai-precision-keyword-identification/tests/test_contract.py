from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
README = (ROOT / "README.md").read_text(encoding="utf-8-sig")
REF = (ROOT / "references" / "precision-keyword-v1.md").read_text(encoding="utf-8-sig")


def test_precision_identification_boundary():
    assert "只负责“精准词识别与数据资产生成”" in SKILL
    assert "PickPwKView" in SKILL and "ERP_ProId" in SKILL
    assert "|1精准|" in SKILL
    assert "IsExact" in SKILL and "严禁用于 ERP 精准词判定" in SKILL
    assert "精准泛词提取" in SKILL
    assert "hzp-amz-6-0-2-precision-broad-extraction" in SKILL


def test_dual_csv_and_blind_contract():
    for term in ("手动分类精准词.csv", "AI精准词.csv", "AI_Classification", "PRECISION", "NOT_PRECISION", "REVIEW_REQUIRED", "SearchVolume30", "Benchmark_Count", "Benchmark_Organic_Evidence", "raw_fields", "自动编号", "ERP_KEYWORD_RECORD_ID_UNCONFIRMED", "关键词", "精准度"):
        assert term in SKILL
    for term in ("OWN_ONLY", "OWN_PLUS_BENCHMARK", "BENCHMARK_FALLBACK", "ERP_KEYWORD_RECORD_IDENTITY_CONFLICT", "ERP_KEYWORD_RECORD_ID_UNCONFIRMED", "CURRENT_KEYWORDS_UNAVAILABLE_NO_BENCHMARK"):
        assert term in SKILL and term in REF
    assert "Product_Code + ERP_ProId + Keyword" in REF
    assert "REVIEW_REQUIRED" in REF
    assert "UTF-8 with BOM" in REF


def test_no_strategy_ownership():
    assert "不得在 6-0-1 报告内生成精准泛词、关键词族、Broad Seed" in (ROOT / "templates" / "report-outline.md").read_text(encoding="utf-8-sig")


def test_semantic_judgment_engine_contract():
    source = (ROOT / "scripts" / "dual_precision_csv.py").read_text(encoding="utf-8-sig")
    for term in ("build_product_semantic_profile", "evaluate_product_search_intent_fit", "Hard_Intent_Conflicts", "Product–Search Intent Fit", "REVIEW_REQUIRED"):
        assert term in source or term in SKILL or term in REF
    assert "固定维度加权" in SKILL
    assert "辅助证据" in REF


if __name__ == "__main__":
    test_precision_identification_boundary()
    test_dual_csv_and_blind_contract()
    test_no_strategy_ownership()
    print("6-0-1 precision-identification contract tests: PASS")
