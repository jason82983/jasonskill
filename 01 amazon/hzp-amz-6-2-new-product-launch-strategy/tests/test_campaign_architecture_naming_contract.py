"""Contract checks for the 6-2 Role/Tool architecture and campaign naming."""
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
spec = importlib.util.spec_from_file_location(
    "resolver", REPO_ROOT / "scripts" / "resolve_amazon_ad_identity.py"
)
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def test_role_tool_dictionary_and_reference_architecture():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for term in ("Role/Target 翻译", "独立", "共享", "不投", "COR-EXA", "EXP-PHR", "DIS-BRO", "DIS-AUT", "COM-ASI", "CAT-CAT", "Campaign 格式固定", "CampaignTag"):
        assert term in text


def test_current_campaign_name_contract_and_legacy_parse():
    current = resolver.format_campaign_name(
        "B2", "SP", "COR", "EXA", 1, campaign_tag="M", intent_code="SG", control_mode="独立"
    )
    assert current == "B2.M.SP-COR-EXA-SG-01"
    parsed = resolver.parse_campaign_name(current)
    assert parsed["status"] == "CURRENT_STANDARD"
    assert (parsed["product_code"], parsed["campaign_tag"], parsed["var_code"], parsed["ad_type"], parsed["role"], parsed["target_match"], parsed["intent_code"], parsed["sequence"]) == ("B2", "M", None, "SP", "COR", "EXA", "SG", "01")

    shared = resolver.format_campaign_name(
        "B2", "SP", "EXP", "PHR", 1, campaign_tag="M", control_mode="共享"
    )
    assert shared == "B2.M.SP-EXP-PHR-01"
    assert resolver.parse_campaign_name(shared)["intent_code"] is None

    legacy = resolver.parse_campaign_name("B2.M-SP-COR-EXA-01")
    assert legacy["status"] == "LEGACY_STANDARD"
    assert resolver.classify_campaign_name("B2.M-SP-COR-EXA-01", {"formal_product_code": "B2", "var_code": "M"})["status"] == "LEGACY_RECOGNIZABLE"


def test_sequence_check_uses_current_and_legacy_names_without_renaming():
    result = resolver.next_campaign_sequence(
        ["B2.M.SP-COR-EXA-SG-01", "B2.M.SP-COR-EXA-SG-02"],
        "B2", "SP", "COR", "EXA", campaign_tag="M", intent_code="SG", control_mode="独立",
    )
    assert result["name"] == "B2.M.SP-COR-EXA-SG-03"
    assert result["collision"] is True

    shared = resolver.next_campaign_sequence(
        ["B2.M-SP-EXP-PHR-01"],
        "B2", "SP", "EXP", "PHR", campaign_tag="M", control_mode="共享",
    )
    assert shared["name"] == "B2.M.SP-EXP-PHR-02"


def test_control_mode_controls_intent_code_presence():
    try:
        resolver.format_campaign_name("B2", "SP", "COR", "EXA", 1, campaign_tag="M", control_mode="独立")
    except ValueError as exc:
        assert str(exc) == "INTENT_CODE_REQUIRED_FOR_INDEPENDENT_CAMPAIGN"
    else:
        raise AssertionError("independent Campaign must carry an Intent Code")

    try:
        resolver.format_campaign_name("B2", "SP", "EXP", "PHR", 1, campaign_tag="M", intent_code="SG", control_mode="共享")
    except ValueError as exc:
        assert str(exc) == "SHARED_CAMPAIGN_CANNOT_HAVE_INTENT_CODE"
    else:
        raise AssertionError("shared Campaign must omit Intent Code")


if __name__ == "__main__":
    test_role_tool_dictionary_and_reference_architecture()
    test_current_campaign_name_contract_and_legacy_parse()
    print("6-2 campaign architecture/naming contract: PASS")
