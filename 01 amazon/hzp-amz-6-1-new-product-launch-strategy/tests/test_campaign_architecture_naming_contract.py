"""Contract checks for 6-1 approved task translation and additive Campaign naming."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
spec = importlib.util.spec_from_file_location("resolver", REPO_ROOT / "scripts" / "resolve_amazon_ad_identity.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)

def test_role_translation_and_apply_boundary():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for term in ("6-0-5", "ROLE_TRANSLATION_AMBIGUOUS", "COR-EXA", "EXP-PHR", "DIS-BRO", "DIS-AUT", "COM-ASI", "CAT-CAT", "只按 605 已批准的"):
        assert term in text
    assert "不再选择角色" in text

def test_current_campaign_name_contract_and_legacy_parse():
    current = resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, "M")
    assert current == "B2.M.SP-COR-EXA-01"
    parsed = resolver.parse_campaign_name(current)
    assert parsed["status"] == "CURRENT_STANDARD"
    assert (parsed["product_code"], parsed["var_code"], parsed["ad_type"], parsed["role"], parsed["target_match"], parsed["sequence"]) == ("B2", "M", "SP", "COR", "EXA", "01")
    legacy = resolver.parse_campaign_name("B2.M.SP-COR-EXA-01")
    assert legacy["status"] == "CURRENT_STANDARD"
    assert resolver.classify_campaign_name("B2.M.SP-COR-EXA-01", {"formal_product_code": "B2", "var_code": "M"})["status"] == "CURRENT_STANDARD"

def test_optional_intent_segment_and_sequence():
    name = resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, "M", "SBG")
    assert name == "B2.M.SP-COR-EXA-SBG-01"
    parsed = resolver.parse_campaign_name(name)
    assert parsed["intent_code"] == "SBG"
    assert resolver.next_campaign_sequence([name], "B2", "SP", "COR", "EXA", "M", "SBG")["name"] == "B2.M.SP-COR-EXA-SBG-02"
    assert resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, "M") == "B2.M.SP-COR-EXA-01"
    no_variant = resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1)
    assert no_variant == "B8.SP-COR-EXA-01"
    assert resolver.parse_campaign_name(no_variant)["product_code"] == "B8"
    assert resolver.format_campaign_name("B8", "SP", "COR", "EXA", 1, intent_code="SBG") == "B8.SP-COR-EXA-SBG-01"

def test_control_aware_naming_and_historical_compatibility():
    independent = resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, "M", "SBG", "独立")
    shared = resolver.format_campaign_name("B2", "SP", "EXP", "PHR", 1, "M", control_mode="共享")
    assert independent == "B2.M.SP-COR-EXA-SBG-01"
    assert shared == "B2.M.SP-EXP-PHR-01"
    assert resolver.parse_campaign_name(independent)["intent_code"] == "SBG"
    assert resolver.parse_campaign_name(shared)["intent_code"] is None
    assert resolver.next_campaign_sequence([independent], "B2", "SP", "COR", "EXA", "M", "SBG", "独立")["name"] == "B2.M.SP-COR-EXA-SBG-02"
    with pytest.raises(ValueError, match="INTENT_CODE_REQUIRED"):
        resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, "M", control_mode="独立")
    with pytest.raises(ValueError, match="SHARED_CAMPAIGN_MUST_NOT"):
        resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, "M", "SBG", "共享")
    with pytest.raises(ValueError, match="NO_INVESTMENT_HAS_NO_CAMPAIGN"):
        resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, "M", control_mode="不投")
    old = resolver.parse_campaign_name("B2.M-SP-COR-EXA-01")
    assert old["status"] in {"CURRENT_STANDARD", "LEGACY_STANDARD"} and old["intent_code"] is None
    assert resolver.format_campaign_name("B2", "SB", "COR", "EXA", 1, "M", "SBG", "独立") == "B2.M.SB-COR-EXA-SBG-01"
    assert resolver.format_campaign_name("B2", "SD", "DIS", "BRO", 1, "M", control_mode="共享") == "B2.M.SD-DIS-BRO-01"
