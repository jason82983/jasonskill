"""Static contract checks for Campaign snapshots, evidence clocks, and daily summaries."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in {".md", ".yaml"} and "tests" not in p.parts
)


def test_snapshot_fields_and_missing_data_contract():
    for term in (
        "Campaign 运行快照与历史驱动闭环",
        "Campaign经营快照",
        "Impressions",
        "Clicks",
        "CTR",
        "Spend",
        "CPC",
        "Orders",
        "Sales",
        "CVR",
        "ACoS",
        "CPA",
        "ROAS",
        "[数据未获取]",
        "[不可可靠比较]",
        "AI数据判断",
    ):
        assert term in TEXT


def test_dynamic_change_and_emergency_contract():
    for term in (
        "今天发生了什么",
        "主要原因是什么",
        "今天要不要动",
        "为什么现在可以/不能动",
        "REFERENCE WINDOW",
        "PENDING Change + 新证据不足",
        "WAIT_FOR_MORE_EVIDENCE",
        "CHANGE_INTERACTION_CHECK",
        "CHANGE_SET_ID",
        "EMERGENCY_OVERRIDE",
        "INTERRUPTED_BY_NEW_CHANGE",
        "NO_NEED_TO_CHANGE",
        "Confidence",
        "Evidence Window",
        "Applicable Context",
        "不无证据硬编码",
    ):
        assert term in TEXT


def test_daily_summary_success_boundary():
    for term in (
        "每天更新日志/YYYY-MM-DD_广告修改汇总.md",
        "同一产品同一自然日只有一份",
        "apply_change_plan 成功且 read-back 确认",
        "Modified Campaigns",
        "Executed Changes",
        "0 修改极简记录",
        "不进入 0-2 formal report index",
        "紧急提前干预",
    ):
        assert term in TEXT


def test_runtime_contract_cases_one_to_sixty_are_documented():
    framework = (ROOT / "references" / "diagnosis-framework.md").read_text(encoding="utf-8")
    assert "Campaign Runtime Evidence Mock Test Contract 1–60" in framework
    table = framework.split("Campaign Runtime Evidence Mock Test Contract 1–60", 1)[1]
    for case in range(1, 61):
        assert f"| {case} |" in table
