"""Static contract checks for Product_Code + Second_Code scope safety."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml"} and "tests" not in p.parts)


def test_scope_resolution_and_fail_closed_rules():
    for term in ("Fail Closed, Never Expand Scope", "ALL 必须显式指定", "空 Scope 不能代表 ALL", "RUN_SCOPE=ALL_ACTIVE_AUTHORIZED_ADS", "[MISSING_SCOPE]", "[MISSING_SECOND_CODE]", "[MISSING_PRODUCT_CODE]", "[INVALID_SCOPE_FORMAT]", "[SCOPE_RESOLUTION_FAILED]", "[SCOPE_CONFLICT]", "6-3，ALL", "6-3，B2，M", "6-3，A6，M2", "Product_Code", "Second_Code", "Second_Code 是 HZP 内部第二层广告管理代码"):
        assert term in TEXT


def test_second_code_namespace_is_exact_and_multi_sku_safe():
    for term in ("B2.M.*", "A6.M2.*", "A6.BW.*", "Exact Match", "startswith", "A6.M20.*", "A6.M2X.*", "一个 Second_Code 可以对应一个或多个 SKU", "不要求唯一 SKU/ASIN", "Campaign_Structure"):
        assert term in TEXT


def test_scope_mock_contract_is_documented():
    framework = (ROOT / "references" / "diagnosis-framework.md").read_text(encoding="utf-8")
    assert "Scope Mock Test Contract 1–31" in framework
    for term in ("Scope=B2/M", "MISSING_SECOND_CODE", "不扫描 A6/BW", "不得误匹配 M20", "ALL 与具体参数混用", "不执行真实 Amazon 广告写操作"):
        assert term in framework


def test_product_only_scope_is_rejected():
    assert "EXPLICIT_PRODUCT_ONLY" not in TEXT
    assert "MISSING_SECOND_CODE" in TEXT
