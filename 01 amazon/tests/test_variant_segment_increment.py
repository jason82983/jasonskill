import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("resolver", Path(__file__).resolve().parents[1] / "scripts" / "resolve_amazon_ad_identity.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def test_only_variant_segment_is_added():
    old = "B8.SP-COR-EXA-01"
    new = resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "M")
    assert new == "B8.M.SP-COR-EXA-01"
    assert new == "B8.M.SP-COR-EXA-01"
    parsed = resolver.parse_campaign_name(new)
    assert parsed["product_code"] == "B8"
    assert parsed["var_code"] == "M"
    assert parsed["ad_type"] == "SP"
    assert parsed["role"] == "COR"
    assert parsed["target_match"] == "EXA"
    assert parsed["sequence"] == "01"
