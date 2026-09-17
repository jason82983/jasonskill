"""Mock contract tests for the COR-EXA new-product Initial Bid policy.

These checks read Skill instructions only; they never run a product or call SellerSpace.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    path.read_text(encoding="utf-8")
    for path in ROOT.rglob("*")
    if path.is_file() and path.suffix in {".md", ".yaml"}
)


def test_cor_exact_default_policy():
    required = (
        "CORE_HIGH_CONFIDENCE_EXACT",
        "COR-EXA",
        "Top of Search +50%",
        "Rest of Search 0%",
        "Product Pages 0%",
        "Dynamic Bids - Up and Down",
        "Top Placement Adjusted Bid",
        "Potential Maximum Effective Bid",
        "Break-even / Economic Risk",
        "Dynamic Upward Multiplier",
    )
    missing = [term for term in required if term not in TEXT]
    assert not missing, f"missing COR-EXA initial bid terms: {missing}"


def test_old_mechanical_twenty_percent_rule_is_overridden():
    assert "Base Bid × 1.20" in TEXT
    assert "不得把 `Base Bid × 1.20`" in TEXT
    assert "机械 `×1.20` 默认" in TEXT
    forbidden_active_rule = (
        "Base Bid × 1.20 作为默认启动",
        "Base Bid * 1.20 作为默认启动",
    )
    assert all(term not in TEXT for term in forbidden_active_rule)


def test_non_cor_roles_do_not_inherit_policy():
    for role in ("EXP-PHR", "DIS-BRO", "DIS-AUT", "COM-ASI"):
        assert role in TEXT
    assert "不得继承 COR-EXA 的 +50% 参考" in TEXT


def test_dynamic_risk_and_6_2_takeover():
    for term in (
        "动态上调上限未确认",
        "6-3 必须基于真实 Top",
        "不能机械加 Bid",
        "降低或取消 Top +50%",
    ):
        assert term in TEXT


if __name__ == "__main__":
    test_cor_exact_default_policy()
    test_old_mechanical_twenty_percent_rule_is_overridden()
    test_non_cor_roles_do_not_inherit_policy()
    test_dynamic_risk_and_6_2_takeover()
    print("COR-EXA initial bid mock contract: PASS")
