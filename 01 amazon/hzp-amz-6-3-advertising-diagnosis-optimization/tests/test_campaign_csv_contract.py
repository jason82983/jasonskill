"""Static contract checks for the CSV + MD Campaign log simplification."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    p.read_text(encoding="utf-8")
    for p in ROOT.rglob("*")
    if p.is_file() and p.suffix in {".md", ".yaml"} and "tests" not in p.parts
)


def test_csv_md_responsibility_split_and_schema():
    for term in (
        "CSV负责结构化数据",
        "MD负责判断、Change、Validation、Learning",
        "原始广告文件负责完整证据",
        "[完整 Campaign Name].csv",
        "[完整 Campaign Name].md",
        "Campaign ID 必须同时写入 CSV 字段和 MD 正文",
        "Campaign CSV 稳定 Schema",
        "Run_ID",
        "Impressions_7D",
        "ACoS_7D",
        "PostChange_Clicks",
        "Change_Readiness",
        "Mapped_SKUs",
        "Advertised_SKUs",
        "SKU_Count",
        "ASIN_AGGREGATION_UNCERTAIN",
    ):
        assert term in TEXT


def test_window_and_maturity_contract():
    for term in (
        "最近 7 个完整自然日",
        "Today/Intraday 只做风险检查",
        "3D 看短期变化",
        "14D/30D 看背景",
        "Since Last Change",
        "CONVERSION_DATA_NOT_MATURE",
        "[不可可靠比较]",
        "不把短期 ACoS 当成最终失败",
    ):
        assert term in TEXT


def test_idempotent_integrity_and_daily_boundary():
    for term in (
        "WRITE_BLOCKED_FOR_LOG_INTEGRITY",
        "同一 Run_ID 重试不得重复追加",
        "只有 apply_change_plan 成功且 read-back PASS",
        "不增加每日汇总 CSV",
        "Modified Campaigns",
        "Executed Changes",
        "不进入 0-2 formal report index/latest-valid selector",
    ):
        assert term in TEXT


def test_forty_csv_simplification_cases_are_documented():
    framework = (ROOT / "references" / "diagnosis-framework.md").read_text(encoding="utf-8")
    assert "Campaign CSV Simplification Mock Test Contract 1–40" in framework
    table = framework.split("Campaign CSV Simplification Mock Test Contract 1–40", 1)[1]
    for case in range(1, 41):
        assert f"| {case} |" in table
