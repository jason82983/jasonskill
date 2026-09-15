from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "hzp-amz-6-2-product-operations-monitoring"
ADS = ROOT / "hzp-amz-6-3-advertising-diagnosis-optimization"

def test_skill_directories_and_identity():
    assert (OPS / "SKILL.md").is_file()
    assert (ADS / "SKILL.md").is_file()
    assert "name: hzp-amz-6-2-product-operations-monitoring" in (OPS / "SKILL.md").read_text(encoding="utf-8")
    assert "name: hzp-amz-6-3-advertising-diagnosis-optimization" in (ADS / "SKILL.md").read_text(encoding="utf-8")

def test_operating_routes_ads_and_preserves_periods():
    text = (OPS / "SKILL.md").read_text(encoding="utf-8")
    assert "广告专项诊断" in text and "6-3" in text
    periods = (OPS / "references/periods-and-charts.md").read_text(encoding="utf-8")
    for token in ("3天", "7天", "14天", "30天", "上周"):
        assert token in periods

def test_ad_skill_reads_operating_and_returns_handoff():
    text = (ADS / "SKILL.md").read_text(encoding="utf-8")
    assert "最新有效 6-2 产品经营监控与诊断正式 HTML" in text
    assert "《6-2输入交接包》" in text
    assert "Dynamic Bids" in text or "Top" in text

def test_reports_keep_log_boundary():
    for path in (OPS / "SKILL.md", ADS / "SKILL.md"):
        text = path.read_text(encoding="utf-8")
        assert "广告表现汇报优化日志" in text
        assert "不扫描、生成、排序、维护" in text

def test_no_historical_product_reports_touched_by_swap():
    # This repository contains only Skill/manual changes; no product-root HTML is under the repo.
    assert not any(ROOT.glob("**/06_SKILL分析报告/**/N24*.html"))


def test_stage6_role_swap_contract_matrix():
    ops = (OPS / "SKILL.md").read_text(encoding="utf-8")
    ads = (ADS / "SKILL.md").read_text(encoding="utf-8")
    assert "6-2 是产品级经营总监控入口" in ops
    assert "允许状态：`NO_CHANGE`" in ops or "无需动作" in ops
    assert "6-3 处理广告" in ads
    assert "Top of Search" in ads
    assert "apply_change_plan" in ads
    assert "用户批准" in ads
    assert "6-3" in ops and "6-2" in ads
    index = (ROOT / "HZP_Amazon_Skills_全部技能_输入输出数据总表_20260911.html").read_text(encoding="utf-8")
    assert '<section id="s6_2"><h3>6-2｜产品经营监控与诊断' in index
    assert '<section id="s6_3"><h3>6-3｜广告诊断优化' in index
