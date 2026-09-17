"""Static contract checks for the 6-2 V2 Search Intent decision model.

These tests inspect the Skill package only; they do not run a product, call
SellerSpace, or perform Amazon Ads writes.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    path.read_text(encoding="utf-8")
    for path in ROOT.rglob("*")
    if path.is_file() and path.suffix in {".md", ".yaml", ".py"}
)


def test_v2_position_and_decision_chain():
    required = (
        "Search Intent Investment Decision",
        "Initial Traffic Breakthrough Plan",
        "Campaign Architecture should follow Search Intent Architecture",
        "Search Intent → Opportunity → Advertising Role → Target → Match Type",
        "Launch Search Intent Map",
        "Known Demand Engine",
        "Unknown Demand Engine",
    )
    missing = [term for term in required if term not in TEXT]
    assert not missing, f"missing V2 decision terms: {missing}"


def test_v2_opportunity_roles_and_dynamic_toolbox():
    required = (
        "PRIMARY_LAUNCH_INTENT",
        "SECONDARY_GROWTH_INTENT",
        "PRECISION_LONGTAIL_HARVEST",
        "DISCOVERY_INTENT",
        "DEFER",
        "Intent-Constrained Discovery",
        "COR-EXA",
        "EXP-PHR",
        "DIS-BRO",
        "DIS-AUT",
        "COM-ASI",
        "CAT-CAT",
    )
    missing = [term for term in required if term not in TEXT]
    assert not missing, f"missing V2 toolbox terms: {missing}"
    assert "不是强制 4+1 套餐" in TEXT


def test_v2_com_lifecycle_and_maturity():
    for term in (
        "DISCOVERY → VALIDATION → CORE",
        "Product Target Lifecycle State",
        "一次订单不自动升级 CORE",
        "STRATEGIC_RANKING_INTENT",
        "PROFITABLE_HARVEST_INTENT",
        "LOW_OPPORTUNITY_INTENT",
        "UNTESTED",
        "TESTING",
        "不得因 6-0-2 精准度直接写成 `VALIDATED`",
    ):
        assert term in TEXT


def test_v2_safety_boundaries_preserved():
    for term in (
        "prepare_change_plan",
        "apply_change_plan",
        "Read-Back Verification",
        "Own ASIN",
        "Benchmark ASIN",
        "Product Target ASIN",
        "Mapped_SKUs[]",
        "广告结构服从购买意图结构",
        "旧广告不自动修改",
    ):
        assert term in TEXT


if __name__ == "__main__":
    test_v2_position_and_decision_chain()
    test_v2_opportunity_roles_and_dynamic_toolbox()
    test_v2_com_lifecycle_and_maturity()
    test_v2_safety_boundaries_preserved()
    print("6-2 V2 launch decision contract: PASS")
