"""Static contract checks for the 6-4 daily diagnosis and approval loop."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in {".md", ".yaml", ".py"}
)


def test_daily_run_decisions_and_boundary():
    for term in (
        "Daily Run ≠ Daily Change",
        "Identity Validation",
        "Data Freshness Check",
        "Previous Change Validation",
        "NO_CHANGE",
        "OBSERVE",
        "CHANGE_RECOMMENDED",
        "URGENT_CHANGE_RECOMMENDED",
        "INSUFFICIENT_DATA",
        "WRITE_BLOCKED",
        "今天广告要不要动",
        "广告表现汇报优化日志",
    ):
        assert term in TEXT


def test_action_card_cooldown_validation_and_approval():
    for term in (
        "Current Value",
        "Proposed Value",
        "Change %",
        "Validation Window",
        "Change ID",
        "Minimum Observation Window",
        "SUCCESS",
        "PARTIAL_SUCCESS",
        "NO_CLEAR_EFFECT",
        "NEGATIVE_EFFECT",
        "prepare_change_plan",
        "Approved/Prepared diff",
        "Read-Back",
        "Material Difference",
        "【等待你的确认】",
    ):
        assert term in TEXT


def test_root_cause_evidence_and_cor_exact():
    for term in (
        "页面承接 → 5-5",
        "经营总诊断 → 6-5",
        "库存 → 7-1/7-2",
        "市场 → 2-2",
        "少量点击 0 单不能直接暂停核心词",
        "重复成交 Search Term",
        "Dynamic Bids - Up and Down",
        "Top +50%",
        "Product Advertising Learning",
    ):
        assert term in TEXT


def test_cases_a_to_t_are_documented():
    cases = {
        "A": "NO_CHANGE",
        "B": "窗口内默认不重复修改",
        "C": "Top +50%",
        "D": "真实 Placement/CVR/CPA/ACoS 优先",
        "E": "Exact 晋级",
        "F": "少量点击 0 单不能直接暂停核心词",
        "G": "连续高 Spend+足够 Clicks+0 Order",
        "H": "预算",
        "I": "单日 ACoS 峰值不能单独大幅降 Bid",
        "J": "页面承接 → 5-5",
        "K": "库存 → 7-1/7-2",
        "L": "prepare_change_plan",
        "M": "只执行第1项",
        "N": "Material Difference",
        "O": "PARTIAL_FAILURE",
        "P": "调整前后",
        "Q": "每天一条日志",
        "R": "WRITE_BLOCKED",
        "S": "INSUFFICIENT_DATA",
        "T": "今日广告决策清单",
    }
    for term in cases.values():
        assert term in TEXT, f"missing contract term: {term}"
