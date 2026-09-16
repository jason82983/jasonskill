"""Provider-boundary contract tests; no network or write calls."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("provider_boundary", ROOT / "scripts" / "amazon_provider_boundary.py")
provider = importlib.util.module_from_spec(spec)
assert spec.loader
import sys
sys.path.insert(0, str(ROOT / "scripts"))
sys.modules[spec.name] = provider
spec.loader.exec_module(provider)
import erp_keyword_adapter


def test_provider_raw_keys_are_mapped_without_core_provider_names():
    field_map = {
        "product_code": "pcode", "var_code": "vcode", "advertised_asin": "child",
        "mapped_skus": "sku_rows", "advertised_skus": "eligible", "store": "account",
        "marketplace": "site",
    }
    raw = {"pcode": "A3", "vcode": "S", "child": "B0GTL8JNZP", "sku_rows": ["A3-S-3", "A3-S-2"], "eligible": ["A3-S-2", "A3-S-3"], "account": "Store-A", "site": "US"}
    result = provider.canonicalize_identity(raw, field_map=field_map, provider="example")
    assert result["mapped_skus"] == ["A3-S-2", "A3-S-3"]
    assert result["advertised_skus"] == ["A3-S-2", "A3-S-3"]
    assert result["sku_count"] == 2
    assert result["provider"] == "example"
    assert provider.canonicalize_identity({"mapped_skus": "A3-S-3|A3-S-2"})["mapped_skus"] == ["A3-S-2", "A3-S-3"]


def test_capability_missing_is_explicit_and_never_guessed():
    result = provider.normalize_capabilities({"query_ads": "supported", "apply_change_plan": "not_supported"}, ["query_ads", "search_terms", "apply_change_plan"])
    assert result == {"query_ads": provider.SUPPORTED, "search_terms": provider.CAPABILITY_NOT_AVAILABLE, "apply_change_plan": provider.NOT_SUPPORTED}
    assert provider.normalize_capabilities({"query_ads": "mystery"}, ["query_ads"])["query_ads"] == provider.CAPABILITY_NOT_AVAILABLE


def test_erp_read_query_includes_documented_asin_quantity_without_connecting():
    query = erp_keyword_adapter.ERPKeywordAdapter._query()
    assert "[AsinQuantity]" in query
    assert "[ProId] = ?" in query
    assert erp_keyword_adapter.DOCUMENTED_FIELDS["AsinQuantity"].startswith("竞争产品数")
    with tempfile.TemporaryDirectory() as directory:
        schema = Path(directory) / erp_keyword_adapter.DEFAULT_SCHEMA_NAME
        schema.write_text("`AsinQuantity` is the competing product count.\n", encoding="utf-8")
        definitions = erp_keyword_adapter.load_field_definitions(directory)
        assert definitions["fields"]["AsinQuantity"]["status"] == "DOCUMENTED"


def test_metric_provenance_prevents_semantic_conflation():
    ad = provider.canonicalize_metric({"orders": 3, "grain": "campaign", "sem": "attributed orders", "attr": "ad"}, field_map={"value": "orders", "source_grain": "grain", "metric_semantics": "sem", "attribution_semantics": "attr"}, provider="seller-space", metric="Orders")
    product = provider.canonicalize_metric({"orders": 12, "grain": "asin", "sem": "total orders", "attr": "all"}, field_map={"value": "orders", "source_grain": "grain", "metric_semantics": "sem", "attribution_semantics": "attr"}, provider="amazon", metric="Orders")
    assert ad["value"] == 3 and ad["attribution_semantics"] == "ad"
    assert product["value"] == 12 and product["attribution_semantics"] == "all"
    assert ad["source_grain"] != product["source_grain"]


def test_safe_write_requires_prepare_diff_apply_readback():
    blocked = provider.validate_safe_write_capabilities({"prepare_change_plan": "SUPPORTED", "exact_diff": "SUPPORTED", "apply_change_plan": "SUPPORTED"})
    assert blocked["status"] == provider.SAFE_WRITE_CAPABILITY_NOT_AVAILABLE
    allowed = provider.validate_safe_write_capabilities({"prepare_change_plan": "SUPPORTED", "exact_diff": "SUPPORTED", "apply_change_plan": "SUPPORTED", "read_back": "SUPPORTED"})
    assert allowed["allowed"] is True


def test_provider_switch_does_not_change_naming_or_asin_first_contract():
    resolver = importlib.util.spec_from_file_location("resolver", ROOT / "scripts" / "resolve_amazon_ad_identity.py")
    module = importlib.util.module_from_spec(resolver)
    assert resolver.loader
    resolver.loader.exec_module(module)
    assert module.format_campaign_name("A3", "SP", "COR", "EXA", 1, "S") == "A3.S.SP-COR-EXA-01"
    assert provider.canonicalize_identity({"asin": "OWN", "mapped_skus": ["S-2", "S-3"]}, provider="seller-space")["advertised_asin"] == "OWN"
    assert provider.canonicalize_identity({"asin": "OWN", "mapped_skus": ["S-3", "S-2"]}, provider="amazon")["mapped_skus"] == ["S-2", "S-3"]
    ads_text = (ROOT / "hzp-amz-6-3-advertising-diagnosis-optimization" / "SKILL.md").read_text(encoding="utf-8")
    assert "Change Readiness" in ads_text and "AUTO_AD_PRODUCT_ALLOWLIST" in ads_text
    assert all(token in ads_text for token in ("prepare_change_plan", "apply_change_plan", "Read-back"))


def test_skill_docs_define_boundary_without_a_lingxing_implementation():
    for name in ("hzp-amz-6-1-new-product-launch-strategy", "hzp-amz-6-2-product-operations-monitoring", "hzp-amz-6-3-advertising-diagnosis-optimization", "hzp-amz-5-5-live-asin-page-audit"):
        text = (ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        assert "Provider Boundary" in text and "Canonical" in text
        assert "CAPABILITY_NOT_AVAILABLE" in text
    for name in ("hzp-amz-6-1-new-product-launch-strategy", "hzp-amz-6-3-advertising-diagnosis-optimization"):
        text = (ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        assert "SAFE_WRITE_CAPABILITY_NOT_AVAILABLE" in text
