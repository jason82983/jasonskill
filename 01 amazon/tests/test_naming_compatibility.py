import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("resolver", ROOT / "scripts" / "resolve_amazon_ad_identity.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def test_cases_a_to_l():
    # A/B: current standard names parse with or without a scoped variant.
    a = resolver.parse_campaign_name("B8.M.SP-COR-EXA-01")
    b = resolver.parse_campaign_name("B8.SP-DIS-AUT-01")
    assert a == {**a, "status": "CURRENT_STANDARD"} and a["product_code"] == "B8" and a["var_code"] == "M" and a["sequence"] == "01"
    assert b["status"] == "CURRENT_STANDARD" and b["var_code"] is None and b["target_match"] == "AUT"
    # C/K: legacy names remain analyzable when real identity is resolved.
    identity = {"formal_product_code": "B8", "var_code": "M"}
    assert resolver.classify_campaign_name("姐妹礼物精准词", identity)["status"] == "LEGACY_RECOGNIZABLE"
    assert resolver.classify_campaign_name("姐妹礼物精准词")["status"] == "LEGACY_UNKNOWN"
    # D/J/L: a name is only a hint; identity conflict and unknown scope are explicit.
    assert resolver.classify_campaign_name("B8.M.SP-COR-EXA-01", {"formal_product_code": "B8", "var_code": "S"})["status"] == "NAME_IDENTITY_CONFLICT"
    assert resolver.classify_campaign_name("B8.M.SP-COR-EXA-01", {"formal_product_code": None, "var_code": None})["status"] == "CURRENT_STANDARD"
    # E/F/G: mutable settings and second-batch expansion do not change names.
    original = resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "M")
    assert original == resolver.format_campaign_name("B8", "SP", "COR", "EXA", "01", "M")
    assert resolver.format_campaign_name("B8", "SP", "EXP", "PHR", 1, "M") == "B8.M.SP-EXP-PHR-01"
    # H/I: independent second campaign and approved/prepared name drift.
    second = resolver.next_campaign_sequence([original], "B8", "SP", "EXP", "PHR", "M")
    assert second["name"] == "B8.M.SP-EXP-PHR-01"  # different role has its own sequence
    second = resolver.next_campaign_sequence([resolver.format_campaign_name("B8", "SP", "EXP", "PHR", 1, "M")], "B8", "SP", "EXP", "PHR", "M")
    assert second["name"].endswith("-02")
    assert "campaign_name" in resolver.diff_identity_fields({"campaign_name": original}, {"campaign_name": second["name"]})
