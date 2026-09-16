from pathlib import Path
import importlib.util
ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
README = (ROOT / "README.md").read_text(encoding="utf-8-sig")
REF = (ROOT / "references" / "precision-keyword-v1.md").read_text(encoding="utf-8-sig")
spec = importlib.util.spec_from_file_location("precision", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)
def test_identity_and_scope_contract():
    assert "hzp-amz-6-0-2-ai-precision-keyword-identification" in SKILL
    assert "6-0-1" in SKILL and "Id" in SKILL
    assert "CURRENT_PRODUCT_TEXT_EVIDENCE" in SKILL
    assert "产品识别 - 文本文案.txt" in SKILL
    assert "Product–Search Intent Fit" in SKILL and "Query Specificity" in SKILL
    assert "6-0-3" in SKILL and "6-0-4" in SKILL
def test_full_output_contract():
    for term in ("Id", "\u8bcd", "\u4e2d\u6587", "\u5e02\u573a\u5bb9\u91cf", "\u7ade\u4e89\u4ea7\u54c1\u6570", "\u4f9b\u9700\u6bd4", "\u81ea\u7136\u6392\u540d", "\u7cbe\u51c6\u5ea6", "\u7cbe\u51c6\u539f\u56e0"):
        assert term in SKILL and term in README and term in REF
    assert "\u7ade\u4e89\u4ea7\u54c1\u6570" in module.AI_EXCLUDED_FIELDS
    assert "\u4f9b\u9700\u6bd4" in module.AI_EXCLUDED_FIELDS
    assert len(module.FULL_FINAL_COLUMNS) == 11
    assert tuple(module.FULL_FINAL_COLUMNS[:9]) == module.BENCHMARK_RAW_COLUMNS
    assert "do not pass the raw 6-0-1 rows to the judgment prompt" in SKILL
    assert "This AI blind view omits `\u7ade\u4e89\u4ea7\u54c1\u6570` and `\u4f9b\u9700\u6bd4`" in SKILL
    assert "data_integrity_check" in (ROOT / "scripts" / "dual_precision_csv.py").read_text(encoding="utf-8-sig")
    assert module.COMPETING_PRODUCTS_PASSTHROUGH_MISMATCH == "COMPETING_PRODUCTS_PASSTHROUGH_MISMATCH"
    assert module.SUPPLY_DEMAND_RATIO_PASSTHROUGH_MISMATCH == "SUPPLY_DEMAND_RATIO_PASSTHROUGH_MISMATCH"
    assert module.FILE_A_RECORD_COVERAGE_MISMATCH == "FILE_A_RECORD_COVERAGE_MISMATCH"
    assert module.FILE_B_RECORD_COVERAGE_MISMATCH == "FILE_B_RECORD_COVERAGE_MISMATCH"
    assert "INPUT_RECORD_COUNT" in SKILL and "OUTPUT_RECORD_COUNT" in SKILL
    assert "Coverage Check" in SKILL
    assert "UTF-8 with BOM" in README
    for level in ("高度精准", "精准", "弱精准", "不精准"):
        assert level in SKILL and level in README
    assert "Do not use string matches" in SKILL
    assert "AI直接裁决" in SKILL
    assert "0–100" in SKILL
    assert "CURRENT_PRODUCT_UNDERSTANDING" in SKILL
    assert "calibration-cases.md" in SKILL
    assert "AI高度精准词.csv" in SKILL
    assert "No manual-precision CSV is generated" in SKILL
def test_semantic_guardrails():
    for term in ("gift", "sister", "\u6cdb\u793c\u7269", "\u6cdb\u5bf9\u8c61", "\u641c\u7d22\u91cf", "Benchmark"):
        assert term in SKILL
    assert "\u4e0d\u5f97\u590d\u5236\u901a\u7528\u7406\u7531" in SKILL
    assert "REVIEW_REQUIRED" in SKILL
    calibration = (ROOT / "references" / "calibration-cases.md").read_text(encoding="utf-8-sig")
    for keyword, level in (("best friend gifts for women", "高度精准"), ("sister", "精准"), ("birthday gifts for women", "弱精准"), ("gift", "不精准"), ("personalized gifts for women", "不精准")):
        assert keyword in calibration and level in calibration
def test_no_strategy_ownership():
    assert "6-0-3" in SKILL and "6-0-4" in SKILL
    assert "never performs ERP" in SKILL
def test_api_symbols():
    source=(ROOT / "scripts" / "dual_precision_csv.py").read_text(encoding="utf-8-sig")
    for term in ("resolve_latest_601_keyword_output", "read_current_product_text_evidence", "finalize_ai_judgments", "coverage_check", "write_full_ai_csv", "write_high_precision_csv", "build_high_precision_rows", "FULL_FINAL_COLUMNS"):
        assert term in source
    assert "resolve_latest_501_online_report" not in source
    assert "discover_current_product_evidence" not in source
if __name__ == "__main__":
    test_identity_and_scope_contract(); test_full_output_contract(); test_semantic_guardrails(); test_no_strategy_ownership(); test_api_symbols(); print("PASS")
