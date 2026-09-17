"""Static contract checks for history-driven Campaign change readiness."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file()
    and p.suffix in {".md", ".yaml"}
    and "tests" not in p.parts
)


def test_history_is_read_before_new_campaign_decision():
    for term in (
        "修改节奏与历史驱动决策",
        "必须先读取该 Campaign 自己的长期日志",
        "Last Real Change At",
        "Last Change ID",
        "Before/After",
        "Current Validation Status",
        "Previous Learning",
        "先读历史，再看现在，再决定要不要动",
    ):
        assert term in TEXT


def test_change_readiness_and_dynamic_evidence():
    for term in (
        "Change Readiness",
        "CAN_CHANGE_NOW",
        "WAIT_FOR_VALIDATION",
        "EMERGENCY_OVERRIDE",
        "NO_CHANGE",
        "INSUFFICIENT_EVIDENCE",
        "时间只是条件之一",
        "新证据量",
        "CHANGE_INTERACTION_CHECK",
        "CHANGE_SET_ID",
        "WAIT_FOR_MORE_EVIDENCE",
        "READY_TO_CHANGE",
        "NO_NEED_TO_CHANGE",
    ):
        assert term in TEXT


def test_emergency_and_learning_boundaries():
    for term in (
        "INTERRUPTED_BY_NEW_CHANGE",
        "Spend 快速失控",
        "库存/Offer/Listing 重大异常",
        "Confidence",
        "Evidence Window",
        "Applicable Context",
        "不当作永久规则",
        "不得无官方证据硬编码",
        "⚠ 紧急提前干预",
    ):
        assert term in TEXT


def test_daily_summary_only_contains_real_changes():
    for term in (
        "只有真实执行的新修改才进入",
        "WAIT_FOR_MORE_EVIDENCE",
        "不进入“已修改”清单",
        "每天更新日志/YYYY-MM-DD_广告修改汇总.md",
        "NO_CHANGE/OBSERVE",
    ):
        assert term in TEXT


def test_twenty_change_readiness_cases_are_documented():
    for term in (
        "Campaign 修改节奏 Mock Test Contract 1–20",
        "Pending + 新证据不足",
        "时间较短但证据充分",
        "同参数连续修改",
        "关联参数修改",
        "Top 后立即改 Base Bid",
        "历史 SUCCESS",
        "历史 NEGATIVE_EFFECT",
        "历史 Learning",
        "Emergency Override 真实修改",
        "权重理论",
    ):
        assert term in TEXT
