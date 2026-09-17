"""Static contract checks for the product-owner daily advertising summary."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in {".md", ".yaml", ".py"}
)


def test_owner_daily_entry_and_counts():
    for term in (
        "老板每日主要入口",
        "Scanned Campaigns",
        "Modified Campaigns",
        "Executed Changes",
        "今日 Campaign 总览",
        "今日真实修改",
        "未修改 Campaign",
        "同一产品同一自然日",
        "不生成 `_01`/`_02`",
    ):
        assert term in TEXT


def test_owner_status_and_trend_translation():
    for term in (
        "READY_TO_CHANGE→可以调整",
        "WAIT_FOR_MORE_EVIDENCE→等待验证",
        "EMERGENCY_OVERRIDE→紧急干预",
        "NO_NEED_TO_CHANGE→正常/无需调整",
        "INSUFFICIENT_DATA→证据不足",
        "WRITE_BLOCKED→已阻止执行",
        "COM-ASI",
        "竞品｜ASIN",
        "? 证据不足",
        "单日 ACoS",
    ):
        assert term in TEXT


def test_only_verified_changes_expand_and_count():
    for term in (
        "apply_change_plan SUCCESS",
        "read-back PASS",
        "Modified=1，Executed=N",
        "执行状态异常/待确认",
        "历史 Change Validation",
        "Rejected Alternatives",
        "Campaign CSV/MD",
        "不进入 0-2",
    ):
        assert term in TEXT


def test_daily_owner_summary_cases_one_to_thirty_eight_are_documented():
    framework = (ROOT / "references" / "diagnosis-framework.md").read_text(
        encoding="utf-8"
    )
    marker = "Daily Owner Summary Mock Test Contract 1–38"
    assert marker in framework
    table = framework.split(marker, 1)[1]
    for case in range(1, 39):
        assert f"| {case} |" in table
