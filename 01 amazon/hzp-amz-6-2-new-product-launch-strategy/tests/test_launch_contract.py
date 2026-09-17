"""Static contract checks for the 6-2 launch-goal and approval rules.

These tests read Skill instructions only; they do not run a product or call SellerSpace.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    path.read_text(encoding="utf-8")
    for path in ROOT.rglob("*")
    if path.is_file() and path.suffix in {".md", ".yaml"}
)


def test_new_launch_contracts():
    required = (
        "Launch Goal",
        "[系统默认目标]",
        "Standard Growth Launch",
        "Accelerated Launch",
        "Seasonal Sprint",
        "时间负责节奏，证据负责晋级",
        "Expected Orders",
        "首单验证",
        "初始化预案审批",
        "apply_change_plan",
        "Product Target ASIN",
        "own_asin",
        "benchmark_asin",
        "execution_id",
        "prepare_change_plan",
        "Material Difference",
        "Read-Back Verification",
        "旧广告未修改",
        "campaign.create",
        "idempotencyKey",
        "[执行计划与已批准预案存在重大差异｜需要重新确认]",
        "[新旧广告并行风险]",
        "[产品身份无法唯一确认｜禁止创建广告]",
        "[部分创建成功]",
        "Recovery Plan",
        "Actual Campaign IDs",
        "一次知情批准",
    )
    missing = [term for term in required if term not in TEXT]
    assert not missing, f"missing launch contract terms: {missing}"


def test_no_universal_click_or_campaign_thresholds():
    forbidden = (
        "所有新品28天",
        "20 clicks必须判断",
        "30 clicks必须暂停",
        "所有产品固定5个Campaign",
    )
    assert all(term not in TEXT for term in forbidden)
    assert "不能固定为 5 个" in TEXT
    assert "不能作为统一硬阈值" in TEXT


SCENARIO_TERMS = {
    "J": ("[系统默认目标]", "Standard Growth Launch"),
    "K": ("稳健验证", "风险"),
    "L": ("快速强攻", "不得同时无条件拉满"),
    "M": ("Seasonal Sprint", "不使用固定天数阈值"),
    "N": ("目标与当前资源/时间窗口存在冲突", "库存目标"),
    "O": ("提前晋级", "重复成交验证"),
    "P": ("数据不足｜继续收集", "不因到达某天数机械"),
    "Q": ("Expected Orders", "负向证据"),
    "R": ("1 click + 1 order", "首单验证"),
    "S": ("战略预案审批", "apply_change_plan"),
    "T": ("自动发现 Manual Keyword", "无证据不得编造"),
    "U": ("Own ASIN、Benchmark ASIN、Product Target ASIN", "不得用于 Own Product SellerSpace 身份查询"),
}


def test_case_j_to_u_contracts():
    missing = {
        case: [term for term in terms if term not in TEXT]
        for case, terms in SCENARIO_TERMS.items()
    }
    missing = {case: terms for case, terms in missing.items() if terms}
    assert not missing, f"missing J-U scenario terms: {missing}"


APPROVED_CASE_TERMS = {
    "A": ("一次知情批准", "prepare_change_plan", "apply_change_plan"),
    "B": ("Material Difference", "需要重新确认"),
    "C": ("Own ASIN", "Benchmark ASIN", "Advertised Product"),
    "D": ("旧广告未修改", "不 Pause、Archive、Delete"),
    "E": ("新旧广告并行风险", "不 Pause"),
    "F": ("部分创建成功", "Recovery Plan", "不重跑完整 Change Plan"),
    "G": ("execution_id", "不得造成第二套广告"),
    "H": ("Read-Back Verification", "实际参数与批准方案不一致"),
    "I": ("Actual Campaign IDs", "6-6"),
    "J": ("SellerSpace能力缺口", "不得假装创建成功"),
}


def test_approved_creation_cases_a_to_j():
    missing = {
        case: [term for term in terms if term not in TEXT]
        for case, terms in APPROVED_CASE_TERMS.items()
    }
    missing = {case: terms for case, terms in missing.items() if terms}
    assert not missing, f"missing approved-creation scenario terms: {missing}"


if __name__ == "__main__":
    test_new_launch_contracts()
    test_no_universal_click_or_campaign_thresholds()
    test_case_j_to_u_contracts()
    test_approved_creation_cases_a_to_j()
    print("6-2 static launch contract: PASS")

