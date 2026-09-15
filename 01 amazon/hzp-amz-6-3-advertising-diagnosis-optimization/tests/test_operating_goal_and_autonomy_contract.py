"""Static contract checks for the senior-operator and current-goal rules."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in {".md", ".yaml"}
)


def test_current_goal_is_reread_and_parsed():
    for term in (
        "04_产品推广思路.md", "《当前经营目标》", "不使用上次运行缓存",
        "生效日期", "[经营目标无法确认]", "可选字段缺失时合理降级",
        "A｜验证优先", "B｜增长优先", "C｜增长利润平衡",
        "D｜利润优先", "E｜收缩/库存保护", "产品经济数据不足",
        "临时采用 E 的库存保护执行逻辑",
    ):
        assert term in TEXT


def test_product_campaign_object_reconciliation():
    for term in (
        "Product Level", "Campaign Level", "Object Level", "Portfolio/Product Reconciliation",
        "每个广告独立判断", "产品统一目标", "Rejected Alternatives",
        "根因", "候选动作", "幅度",
    ):
        assert term in TEXT


def test_autonomous_execution_and_guardrails():
    for term in (
        "自主执行", "AUTO_EXECUTION_ENABLED=true", "prepare_change_plan",
        "business semantics check", "read-back", "Identity", "经济",
        "库存", "Cooldown", "Portfolio reconciliation", "Kill Switch",
        "AI 不能修改经营目标", "AI 不能自行扩大权限",
    ):
        assert term in TEXT


def test_role_target_and_goal_switch_contract():
    for term in (
        "COR=核心", "EXP=拓词", "DIS=挖词", "COM=竞品", "CAT=类目", "DEF=防守",
        "EXA=精准", "PHR=词组", "BRO=广泛", "AUT=自动", "ASI=ASIN",
        "DIS-AUT", "COM-AUTO", "A→B", "B→C", "C→D",
        "不得自动永久修改", "Product Advertising Learning",
    ):
        assert term in TEXT


def test_no_fixed_threshold_and_data_priority_contract():
    for term in (
        "不是固定阈值规则工具", "不能用", "任何单一 ACoS",
        "自有历史", "Own Product Real Evidence", "最新有效", "Benchmark ASIN",
        "不得作为自有广告身份",
    ):
        assert term in TEXT


def test_thirty_regression_contract_items():
    terms = (
        "《当前经营目标》", "A｜验证优先", "B｜增长优先", "C｜增长利润平衡",
        "D｜利润优先", "E｜收缩/库存保护", "不使用上次运行缓存", "生效日期",
        "[经营目标无法确认]", "[产品经济数据不足]", "Product Level", "Campaign Level",
        "Object Level", "Portfolio/Product Reconciliation", "每个广告独立判断",
        "任何单一 ACoS", "NO_CHANGE", "OBSERVE", "AUTO_EXECUTE", "WRITE_BLOCKED",
        "Identity", "Cooldown", "Kill Switch", "DIS-AUT", "COM-AUTO", "A→B",
        "不得自动永久修改", "最新有效", "Benchmark ASIN", "apply_change_plan",
    )
    assert len(terms) == 30
    for term in terms:
        assert term in TEXT
