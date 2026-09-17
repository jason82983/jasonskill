"""Static contract checks for one-Campaign-one-continuous-log behavior."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file()
    and p.suffix in {".md", ".yaml"}
    and "tests" not in p.parts
)


def test_campaign_identity_and_separate_history():
    for term in (
        "Campaign 独立运营日志",
        "一个 Campaign 一份持续日志",
        "Campaign Name",
        "Campaign ID",
        "不同 Campaign 的 Decision、Action、Change、Validation 和 Learning 不得混写",
        "Campaign ID 是内部稳定归属键",
        "不按日期拆散",
    ):
        assert term in TEXT


def test_run_records_and_validation_writeback():
    for term in (
        "Run Record",
        "NO_CHANGE",
        "OBSERVE",
        "AUTO_EXECUTE",
        "Before/After",
        "Change ID",
        "Change Validation",
        "Validation Status",
        "Campaign-specific Learning",
        "PENDING",
        "Source Decision ID",
    ):
        assert term in TEXT


def test_object_actions_and_evidence_isolation():
    for term in (
        "Keyword、Target、Search Term、Placement、Ad Group",
        "所属 Campaign 日志",
        "OWN_CAMPAIGN_EVIDENCE",
        "PRODUCT_PORTFOLIO_CONTEXT",
        "Campaign A 的历史",
        "Campaign B 的自身历史证据",
        "ALL 多 Campaign",
        "6-4 AI广告运营日报",
        "Campaign 详细日志",
        "0-2 formal report index",
    ):
        assert term in TEXT


def test_campaign_log_filename_and_legacy_safety():
    for term in (
        "[完整 Campaign Name].csv",
        "[完整 Campaign Name].md",
        "固定文件对",
        "不追加 Campaign ID",
        "不追加日期",
        "B2.M-SP-COR-EXA-01.md",
        "Windows 非法字符",
        "Campaign Name 变化时先通过 Campaign ID 找回原日志",
        "只有 6-4 合法执行 Campaign Rename 后",
        "Previous Campaign Name",
        "Current Campaign Name",
        "不修改历史正式 HTML 报告",
    ):
        assert term in TEXT


def test_daily_summary_is_separate_from_campaign_log():
    for term in (
        "每天更新日志",
        "YYYY-MM-DD_广告修改汇总.md",
        "每日产品汇总",
        "不与 Campaign 详细日志混写",
        "Campaign 详细日志与每日汇总都不进入 0-2 正式索引",
    ):
        assert term in TEXT
