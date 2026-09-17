"""Static mock-contract checks for the two-level creation blueprint."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".py"})

def test_executive_approval_view():
    for term in ("Executive Approval View", "6-2 新品广告创建决策", "Initial Budget Allocation", "Initial Keyword Allocation", "Campaign 总览", "Planned Campaign Count", "AI Recommendation"):
        assert term in TEXT

def test_detailed_blueprint_fields():
    for term in ("Detailed Creation Blueprint", "Target-Level Bid", "Advertised Product｜Own Product", "Close Match", "Loose Match", "Substitutes", "Complements", "Product Target ASIN", "暂不预设大规模否词", "当前执行接口不支持"):
        assert term in TEXT

def test_checklist_and_field_diff():
    for term in ("Creation Checklist", "Ready with Known Limitations", "Approved Creation Blueprint", "Prepared Creation Plan", "Field-Level Diff", "Read-Back", "D. 查看完整广告明细"):
        assert term in TEXT
