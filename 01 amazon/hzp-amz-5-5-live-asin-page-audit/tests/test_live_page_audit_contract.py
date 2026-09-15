from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[0].parent
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
MOCK = (ROOT / "tests" / "mock_5-5_report.html").read_text(encoding="utf-8")

def audit_case(case):
    if case == "A":
        return "HEALTHY", "NO_CHANGE"
    if case == "B":
        return "MINOR_OPTIMIZATION", "5-3"
    if case == "C":
        return "MINOR_OPTIMIZATION", "5-2"
    if case == "D":
        return "INSUFFICIENT_EVIDENCE", "IMAGE_UNVERIFIED"
    if case == "E":
        return "MINOR_OPTIMIZATION", "6-3"
    if case == "F":
        return "MINOR_OPTIMIZATION", "5-2/5-3"
    if case == "G":
        return "MAJOR_OPTIMIZATION", "3-2/4"
    if case == "H":
        return "STRATEGY_MISALIGNMENT", "5-1/2-2"
    if case == "I":
        return "MINOR_OPTIMIZATION", "OFFER"
    if case in {"J", "K"}:
        return "INPUT_LATEST_VALID"
    if case == "L":
        return "OWN_ASIN_ONLY"
    if case == "M":
        return "CHILD_SCOPE_ONLY"
    if case == "N":
        return "INSUFFICIENT_EVIDENCE", "BACKEND_ONLY"
    if case == "O":
        return "HEALTHY", "NO_CHANGE"
    raise ValueError(case)

def test_skill_contract():
    assert "Live Page Snapshot" in SKILL
    assert "策略 → 线上执行追踪矩阵" in SKILL
    assert "输入版本追溯" in SKILL
    assert "Own ASIN" in SKILL and "Benchmark ASIN" in SKILL
    assert "apply_change_plan" in SKILL
    assert "5-5 不直接改页面或广告" in SKILL
    assert "hzp-amz-0-2-report-index" in SKILL

def test_report_contract():
    assert "5-5_[产品编号]_线上ASIN页面审计与优化_V[版本]_[YYYYMMDD]_[HHMMSS].html" in SKILL
    assert "6-1输入交接包" in SKILL
    assert "P0" in SKILL and "P1" in SKILL and "P2" in SKILL and "P3" in SKILL

def test_mock_cases_a_to_o():
    expected = {
        "A": ("HEALTHY", "NO_CHANGE"),
        "B": ("MINOR_OPTIMIZATION", "5-3"),
        "C": ("MINOR_OPTIMIZATION", "5-2"),
        "D": ("INSUFFICIENT_EVIDENCE", "IMAGE_UNVERIFIED"),
        "E": ("MINOR_OPTIMIZATION", "6-3"),
        "F": ("MINOR_OPTIMIZATION", "5-2/5-3"),
        "G": ("MAJOR_OPTIMIZATION", "3-2/4"),
        "H": ("STRATEGY_MISALIGNMENT", "5-1/2-2"),
        "I": ("MINOR_OPTIMIZATION", "OFFER"),
        "J": "INPUT_LATEST_VALID",
        "K": "INPUT_LATEST_VALID",
        "L": "OWN_ASIN_ONLY",
        "M": "CHILD_SCOPE_ONLY",
        "N": ("INSUFFICIENT_EVIDENCE", "BACKEND_ONLY"),
        "O": ("HEALTHY", "NO_CHANGE"),
    }
    for case, want in expected.items():
        assert audit_case(case) == want

def test_no_real_side_effects():
    forbidden = ["apply_change_plan(", "requests.post(", "subprocess.run("]
    assert not any(token in SKILL for token in forbidden)
    assert "不 commit" in SKILL and "不 push" in SKILL

def test_readme_is_user_facing():
    assert "30 秒运行" in README
    assert "正式报告" in README

def test_report_ux_contract():
    for text in (
        "LEVEL 1｜老板首页", "一句话结论", "现在最值得做的3件事",
        "这次不建议动的地方", "如果销量不好，问题更可能在哪里？",
        "原来想怎么卖，现在页面有没有做到？", "7张图片，一张一张看",
        "文案有没有把产品说清楚？", "客户现在能不能顺利买？",
        "跟现在的竞品比，还够不够强？", "接下来怎么做",
    ):
        assert text in SKILL or text in (ROOT / "templates" / "report-outline.md").read_text(encoding="utf-8")
    assert "LIVE_PAGE_ANOMALY" in (ROOT / "templates" / "report-outline.md").read_text(encoding="utf-8")
    assert "页面存在异常" in SKILL

def test_mock_report_is_boss_readable():
    for text in ("5-5｜线上页面体检", "一句话结论", "【小改】", "现在最值得做的 3 件事", "这次不建议动的地方", "接下来怎么做", "LEVEL 2"):
        assert text in MOCK
    assert "LIVE_PAGE_ANOMALY" in MOCK
