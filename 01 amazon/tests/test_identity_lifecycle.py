import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("resolver", ROOT / "scripts" / "resolve_amazon_ad_identity.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def r(**kwargs):
    return kwargs


def full_fixture():
    mapping = [r(Product_Code="B8", Product_NewCode="N24", Product_Name="示例产品", 广告组合="组合示例", SellerSpace_Store="Store-A", Marketplace="US", ASIN="OWN-ASIN", SKU="B8-M-1", Status="ACTIVE")]
    prefixes = [r(SellerSpace_Store="Store-A", Product_Code_Prefix="B")]
    variants = [r(Product_Code="B8", Var_Code="M", Var_Name="主款", Child_ASIN="CHILD-M", Child_SKU="B8-M-1"), r(Product_Code="B8", Var_Code="S", Var_Name="次款", Child_ASIN="CHILD-S", Child_SKU="B8-S-1")]
    portfolios = [r(portfolioName="组合示例", portfolioId="PORTFOLIO-MOCK-1", sellerSpaceStore="Store-A", marketplace="US")]
    return mapping, prefixes, variants, portfolios


def test_cases_a_to_o_are_read_only_and_deterministic():
    mapping, prefixes, variants, portfolios = full_fixture()
    # A/E: research code without formal code is surfaced, never generated.
    no_formal = [r(Product_Code="", Product_NewCode="N24", SellerSpace_Store="Store-A", Marketplace="US", Status="ACTIVE")]
    a = resolver.resolve_advertising_identity("N24", no_formal, prefix_rows=prefixes)
    assert a["mapping_status"] == "FORMAL_PRODUCT_CODE_MISSING"
    assert a["prefix_status"] == "FORMAL_PRODUCT_CODE_MISSING"
    # B/C/M: new code resolves to formal code and prefix passes.
    good = resolver.resolve_advertising_identity("N24", mapping, portfolios, prefix_rows=prefixes, variant_rows=variants)
    assert good["formal_product_code"] == "B8" and good["product_new_code"] == "N24"
    assert good["prefix_status"] == "PREFIX_PASS" and good["portfolio_status"] == "PORTFOLIO_VERIFIED"
    assert good["variant_status"] == "VARIANT_MAPPING_VERIFIED"
    # D: store prefix conflict is explicit.
    bad_prefix = resolver.resolve_advertising_identity("B8", mapping, prefix_rows=[r(SellerSpace_Store="Store-A", Product_Code_Prefix="C")])
    assert bad_prefix["prefix_status"] == "PREFIX_CONFLICT"
    # F/G/H: campaign naming is formal-code and optional Var_Code based.
    assert resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1) == "B8.SP-COR-EXA-01"
    assert resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "M") == "B8.M.SP-COR-EXA-01"
    assert len(good["variants"]) == 2
    # I/J: Approved -> Prepared catches material identity drift.
    approved = {"product_code": "B8", "var_code": "M", "child_asin": "CHILD-M", "sku": "B8-M-1", "portfolio_id": "P1"}
    prepared = dict(approved, sku="WRONG")
    assert "sku" in resolver.diff_identity_fields(approved, prepared)
    # K: Read-Back catches wrong advertised child.
    assert resolver.verify_advertised_product(approved, dict(approved, child_asin="CHILD-S"))["status"] == "ADVERTISED_PRODUCT_MISMATCH"
    # L: Portfolio is never guessed when SellerSpace rows are unavailable.
    assert resolver.resolve_advertising_identity("B8", mapping)["portfolio_status"] == "MCP_PORTFOLIO_PENDING"
    # N: same shared resolver is consumed by all stage docs.
    for skill in ("hzp-amz-6-1-new-product-launch-strategy", "hzp-amz-6-2-advertising-diagnosis-optimization", "hzp-amz-6-3-product-operations-monitoring"):
        text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "resolve_advertising_identity" in text
    # O: workbook schema check is read-only.
    headers = {"产品店铺映射": resolver.REQUIRED_IDENTITY_SHEETS["产品店铺映射"], "填写说明": (), "产品对应变体": resolver.REQUIRED_IDENTITY_SHEETS["产品对应变体"], "店铺产品代码前缀": resolver.REQUIRED_IDENTITY_SHEETS["店铺产品代码前缀"]}
    assert resolver.validate_identity_workbook_schema(headers)["valid"]
