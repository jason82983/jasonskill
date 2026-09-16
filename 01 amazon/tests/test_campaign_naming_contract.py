import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("resolver", ROOT / "scripts" / "resolve_amazon_ad_identity.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def test_cases_a_to_q():
    # A/B/D: formal code and independent variant are visible and parseable.
    assert resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "M") == "B8.M.SP-COR-EXA-01"
    assert resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "S") == "B8.S.SP-COR-EXA-01"
    assert ".M.SP-" in resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "M")
    # C/H/I/J/K/L/O/P/Q: research code, portfolio, store, ASIN/SKU and mutable
    # operating parameters stay outside the stable name (or are represented in
    # the blueprint, not this helper).
    assert "N24" not in resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "M")
    name = resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, "M")
    assert all(x not in name for x in ("2026", "$", "TOS", "PPG", "ACOS", "ROAS", "CVR"))
    assert resolver.format_ad_group_name("B8", "COR", 1, "M") == "B8.M.COR-01"
    assert resolver.format_ad_group_name("B8", "COR", 1) == "B8.COR-01"
    # F/G/M: collision is resolved before approval and a new independent
    # sequence is explicit; an approved name drift is material.
    c = resolver.next_campaign_sequence([name], "B8", "SP", "COR", "EXA", "M")
    assert c["name"] == "B8.M.SP-COR-EXA-02" and c["collision"]
    assert resolver.next_campaign_sequence([], "B8", "SP", "COR", "EXA", "M")["name"].endswith("-01")
    assert "campaign_name" in resolver.diff_identity_fields({"campaign_name": name}, {"campaign_name": c["name"]})
    # E/N: shared-variant names are the caller's explicit MULTI_VARIANT choice;
    # old nonconforming campaigns remain untouched by these pure helpers.
    shared = resolver.format_campaign_name("B8", "SP", "DIS", "AUT", 1)
    assert shared == "B8.SP-DIS-AUT-01"
    assert resolver.verify_advertised_product({"product_code": "B8", "var_code": "M", "child_asin": "A", "sku": "S"}, {"product_code": "B8", "var_code": "M", "child_asin": "A", "sku": "S"})["ok"]
