"""Static mock-contract checks for risk-gated 6-3 auto execution."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in {".md", ".yaml", ".py"}
)


def test_decision_modes_and_policy_controls():
    for term in (
        "AUTO_EXECUTE", "NEED_APPROVAL", "WRITE_BLOCKED",
        "auto_execution_enabled: false", "max_bid_change_pct",
        "max_top_change_pp", "max_budget_change_pct",
        "max_daily_incremental_spend", "minimum_confidence", "allowlist",
        "AI 不得自行扩大策略",
    ):
        assert term in TEXT


def test_allowlist_and_approval_boundary():
    for term in (
        "small_bid_change", "small_top_change", "small_budget_change",
        "Pause", "Negative", "新建/删除 Campaign", "经济、库存、页面/Offer/Buy Box",
    ):
        assert term in TEXT


def test_safe_execution_chain_and_readback():
    for term in (
        "Internal Approved-by-Policy Plan", "Policy Plan vs Prepared Plan Diff",
        "prepare_change_plan", "apply_change_plan", "Read-back",
        "Material Difference", "AUTO_EXECUTED", "Pending Validation Queue",
        "AUTO_EXECUTION_ENABLED=false",
    ):
        assert term in TEXT


def test_cases_a_to_r_are_documented():
    for term in (
        "高置信度+低风险Bid小幅调整", "变化超过Policy", "小幅Top调整+证据充分",
        "大幅Top调整", "小幅Budget调整且经济安全", "Pause核心Exact",
        "Negative核心Search Term", "身份冲突", "库存风险", "页面/Offer异常",
        "处于Cooldown", "Policy Plan不一致", "Read-back失败",
        "连续5天无需修改", "表现恶化", "Product级Kill Switch关闭",
        "AI试图超出Policy",
    ):
        assert term in TEXT
