import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("resolver", ROOT / "scripts" / "resolve_amazon_ad_identity.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def row(**kwargs):
    return kwargs


def test_same_asin_multiple_skus_is_legal_and_order_independent():
    variants = [
        row(Product_Code="A3", Var_Code="S", Var_Name="银色款", Child_ASIN="B0GTL8JNZP", Child_SKU="A3-S-3"),
        row(Product_Code="A3", Var_Code="S", Var_Name="银色款", Child_ASIN="B0GTL8JNZP", Child_SKU="A3-S-2"),
    ]
    first = resolver._variant_records("A3", variants)
    second = resolver._variant_records("A3", list(reversed(variants)))
    assert first == second
    records, conflicts, status = first
    assert not conflicts
    assert status == "VARIANT_MAPPING_VERIFIED"
    assert records == [{
        "var_code": "S", "var_name": "银色款", "child_asin": "B0GTL8JNZP",
        "mapped_skus": ["A3-S-2", "A3-S-3"], "sku_count": 2, "sku": None,
        "primary_advertised_sku": None, "identity_status": "MULTI_SKU_SAME_ASIN", "mapping_incomplete": False,
    }]
    assert resolver.serialize_skus(["A3-S-3", "A3-S-2", "A3-S-2"]) == "A3-S-2|A3-S-3"
    assert resolver.serialize_skus("A3-S-2") == "A3-S-2"


def test_resolver_exposes_asin_first_arrays_without_promoting_a_primary_sku():
    mapping = [row(Product_Code="A3", Product_Name="示例", 广告组合="组合", SellerSpace_Store="Store-A", Marketplace="US", ASIN="PARENT", SKU="LEGACY", Status="ACTIVE")]
    portfolios = [row(portfolioName="组合", portfolioId="P1", sellerSpaceStore="Store-A", marketplace="US")]
    variants = [
        row(Product_Code="A3", Var_Code="S", Var_Name="银色款", Child_ASIN="B0GTL8JNZP", Child_SKU="A3-S-3"),
        row(Product_Code="A3", Var_Code="S", Var_Name="银色款", Child_ASIN="B0GTL8JNZP", Child_SKU="A3-S-2"),
    ]
    result = resolver.resolve_advertising_identity("A3", mapping, portfolios, variant_rows=variants)
    assert result["mapped_skus"] == ["A3-S-2", "A3-S-3"]
    assert result["sku_count"] == 2
    assert result["primary_advertised_sku"] is None
    assert result["variants"][0]["identity_status"] == "MULTI_SKU_SAME_ASIN"


def test_variant_asin_conflict_fails_closed():
    variants = [
        row(Product_Code="A3", Var_Code="S", Child_ASIN="B0GTL8JNZP", Child_SKU="A3-S-3"),
        row(Product_Code="A3", Var_Code="S", Child_ASIN="B0XXXXXXXX", Child_SKU="A3-S-2"),
    ]
    records, conflicts, status = resolver._variant_records("A3", variants)
    assert status == "VARIANT_ASIN_MAPPING_CONFLICT"
    assert conflicts and "multiple ASINs" in conflicts[0]
    assert records == []


def test_advertised_sku_decisions_are_eligibility_driven():
    mapped = ["A3-S-3", "A3-S-2"]
    assert resolver.decide_advertised_skus(mapped, mapped)["action"] == "ADD_BOTH"
    assert resolver.decide_advertised_skus(mapped, mapped)["status"] == "SKU_ELIGIBILITY_VERIFIED"
    assert resolver.decide_advertised_skus(mapped, ["A3-S-2"])["action"] == "ADD_ELIGIBLE_SKU_ONLY"
    assert resolver.decide_advertised_skus(mapped, ["A3-S-2"])["status"] == "SKU_ELIGIBILITY_PARTIAL"
    assert resolver.decide_advertised_skus(mapped, [])["action"] == "ADVERTISED_PRODUCT_NOT_ELIGIBLE"
    assert resolver.decide_advertised_skus(mapped, mapped, asin_deduped=True)["action"] == "ADD_ONCE"
    assert resolver.select_primary_advertised_sku(mapped, required=True) is None
    assert resolver.select_primary_advertised_sku(["A3-S-2"], required=True) == "A3-S-2"


def test_asin_aggregation_and_inventory_semantics_are_explicit():
    rows = [row(sku="A3-S-2", orders=3, available=65), row(sku="A3-S-3", orders=4, available=121)]
    assert resolver.aggregate_metric_to_asin(rows, "orders", source_grain="SKU")["value"] == 7
    assert resolver.aggregate_metric_to_asin(rows, "orders", source_grain="SKU")["deduplication_check"] == "PASS"
    assert resolver.aggregate_metric_to_asin([row(orders=7)], "orders", source_grain="ASIN", already_asin_aggregate=True)["method"] == "DIRECT_ASIN"
    assert resolver.aggregate_metric_to_asin(rows + [row(sku="A3-S-2", orders=1)], "orders", source_grain="SKU")["status"] == "ASIN_AGGREGATION_UNCERTAIN"
    inventory = resolver.summarize_inventory_by_asin(rows, quantity_field="available", source_grain="SKU")
    assert inventory["asin_total"] == 186
    assert inventory["source_grain"] == "SKU" and inventory["deduplication_check"] == "PASS"
    assert len(inventory["sku_breakdown"]) == 2


def test_stage_docs_use_asin_first_contract():
    docs = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in (
            "hzp-amz-6-1-new-product-launch-strategy/SKILL.md",
            "hzp-amz-6-2-product-operations-monitoring/SKILL.md",
            "hzp-amz-6-3-advertising-diagnosis-optimization/SKILL.md",
            "hzp-amz-5-5-live-asin-page-audit/SKILL.md",
            "Amazon广告身份解析规则.md",
        )
    )
    for term in (
        "Mapped_SKUs[]", "Advertised_SKUs[]", "MULTI_SKU_SAME_ASIN",
        "SKU_ELIGIBILITY_PARTIAL", "ASIN_AGGREGATION_SEMANTICS_CHECK",
        "ASIN_AGGREGATION_UNCERTAIN", "不生成重复 SKU 报告", "只形成一个 ASIN 经营视图",
    ):
        assert term in docs
    csv_schema = (ROOT / "hzp-amz-6-3-advertising-diagnosis-optimization/SKILL.md").read_text(encoding="utf-8")
    assert "Advertised_ASIN, Mapped_SKUs, Advertised_SKUs, SKU_Count" in csv_schema

