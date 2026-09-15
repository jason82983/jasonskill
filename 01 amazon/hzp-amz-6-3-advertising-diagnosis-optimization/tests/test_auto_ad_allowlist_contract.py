"""Static contract checks for Product_Code + Second_Code authorization."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml"} and "tests" not in p.parts)
FRAMEWORK = (ROOT / "references" / "diagnosis-framework.md").read_text(encoding="utf-8")


def test_workbook_sheet_and_columns_contract():
    for term in ("Amazon产品店铺映射表.xlsx", "实际 Workbook", "Product_Code", "Second_Code", "Status", "trim", "大小写规范化", "Second_Code 是 HZP 内部第二层广告管理代码", "不是 Amazon 真实 ASIN", "不是 SKU"):
        assert term in TEXT


def test_active_status_and_conflict_fail_closed():
    for term in ("Product_Code + Second_Code + ACTIVE", "Status=ACTIVE", "AUTO_AUTH_STATUS_ACTIVE", "[AUTO_AD_MAPPING_INVALID_ROW]", "[AUTO_AUTH_STATUS_INVALID]", "[AUTO_AD_MAPPING_NOT_FOUND]", "[AUTO_AD_MAPPING_SCHEMA_INVALID]", "[AUTO_AUTH_MAPPING_CONFLICT]", "不得第一行优先", "不得 ACTIVE 优先", "Fail Closed"):
        assert term in TEXT


def test_campaign_exact_namespace_and_multi_sku_boundary():
    for term in ("B2.M.*", "A6.M2.*", "A6.BW.*", "结构化 Parser", "Exact Match", "禁止 startswith/contains/substring", "[CAMPAIGN_AUTH_IDENTITY_UNRESOLVED]", "Campaign ID", "Advertised Own ASIN", "同一 ASIN 多 SKU", "不要求逐 SKU"):
        assert term in TEXT


def test_scope_and_legacy_txt_boundary():
    for term in ("6-3，ALL", "Excel ACTIVE 授权", "6-3，产品代码，Second_Code", "开自动的产品有.txt", "不参与 6-3 最高授权判断", "不与 Excel 形成双重授权", "不删除、不修改", "Boss 日报", "Authorization State"):
        assert term in TEXT


def test_all_required_authorization_cases_are_documented():
    assert "精确授权 Mock Test Contract 1–35" in FRAMEWORK
    table = FRAMEWORK.split("精确授权 Mock Test Contract 1–35", 1)[1]
    for case in range(1, 36):
        assert f"| {case} |" in table


def test_provider_and_write_boundary():
    for term in ("HZP Business Authorization Layer", "SellerSpace/优麦云仍是当前 Provider", "不得 apply_change_plan", "不执行真实 Amazon 广告写操作", "AUTO_EXECUTION_NOT_AUTHORIZED"):
        assert term in TEXT or term in FRAMEWORK
