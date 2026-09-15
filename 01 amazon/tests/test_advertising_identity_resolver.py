import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("resolver", ROOT / "scripts" / "resolve_amazon_ad_identity.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)
DOC_TEXT = "\n".join(
    (ROOT / name / file).read_text(encoding="utf-8")
    for name, file in (
        ("hzp-amz-6-1-new-product-launch-strategy", "SKILL.md"),
        ("hzp-amz-6-3-advertising-diagnosis-optimization", "SKILL.md"),
        ("hzp-amz-6-2-product-operations-monitoring", "SKILL.md"),
    )
)
SHARED_TEXT = (ROOT / "Amazon广告身份解析规则.md").read_text(encoding="utf-8")


def row(**kwargs):
    return kwargs


def test_cases_a_to_n():
    mapping = [row(Product_Code="PX1", Product_Name="演示产品", 广告组合="Portfolio Mock", SellerSpace_Store="Store-A", Marketplace="US", ASIN="OWN-MOCK", SKU="SKU-MOCK", Status="ACTIVE")]
    portfolios = [row(portfolioName="Portfolio Mock", portfolioId="PORTFOLIO-MOCK-1", sellerSpaceStore="Store-A", marketplace="US")]

    # A: unique mapping; B: portfolio name; C: read-only ID resolution; D: verified status.
    result = resolver.resolve_advertising_identity("PX1", mapping, portfolios)
    assert result["portfolio_status"] == "PORTFOLIO_VERIFIED"
    assert result["portfolio_id"] == "PORTFOLIO-MOCK-1"
    # E: missing MCP list; F: missing mapping Portfolio; G: unresolved ID.
    assert resolver.resolve_advertising_identity("PX1", mapping)["portfolio_status"] == "MCP_PORTFOLIO_PENDING"
    missing_name = [dict(mapping[0], 广告组合=None)]
    assert resolver.resolve_advertising_identity("PX1", missing_name, portfolios)["portfolio_status"] == "MAPPING_PORTFOLIO_MISSING"
    no_id = [row(portfolioName="Portfolio Mock", sellerSpaceStore="Store-A", marketplace="US")]
    assert resolver.resolve_advertising_identity("PX1", mapping, no_id)["portfolio_status"] == "PORTFOLIO_ID_UNRESOLVED"
    # H: approval/prepared and I: read-back are field-level checks owned by 6-1.
    assert result["own_asin"] != "BENCHMARK-MOCK"
    for term in (
        "字段级比对", "Read-Back Verification", "Expansion Batch", "继承 6-1",
        "Portfolio Identity Anomaly", "Portfolio Ad Sales", "Product Total Sales",
        "Legacy overlap", "禁止写入", "Mapped_SKUs[]", "MULTI_SKU_SAME_ASIN",
        "ASIN_AGGREGATION_UNCERTAIN",
    ):
        assert term in DOC_TEXT
    for term in ("[广告组合身份验证通过]", "[广告组合不存在]", "[广告组合数据源冲突]", "[存在多个有效广告组合映射｜需要人工确认]"):
        assert term in SHARED_TEXT
    # J: expansion inheritance, K: wrong scope, L: product-vs-portfolio sales are report rules.
    wrong_scope = [row(portfolioName="Portfolio Mock", portfolioId="PORTFOLIO-MOCK-2", sellerSpaceStore="Other", marketplace="US")]
    assert resolver.resolve_advertising_identity("PX1", mapping, wrong_scope)["portfolio_status"] == "PORTFOLIO_SCOPE_CONFLICT"
    # M: multiple active; N: legacy overlap is never silently migrated.
    duplicate = [mapping[0], dict(mapping[0], SKU="SKU-MOCK-2")]
    assert resolver.resolve_advertising_identity("PX1", duplicate, portfolios)["mapping_status"] == "MAPPING_MULTIPLE_ACTIVE"
