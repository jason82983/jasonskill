"""Static mock-contract checks that 6-1 cannot expand 6-0-5 targets."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".py"})

def test_605_is_only_target_authority():
    for term in ("605 Approved Target Boundary", "Approved Battle Unit ID", "未批准", "不能增加目标", "不再建立、扩展或筛选 Keyword Mother Pool"):
        assert term in TEXT

def test_other_keyword_sources_cannot_add_targets():
    for term in ("H10", "Benchmark", "SellerSpace 建议 Bid", "不能改变 Keyword/Target 集合"):
        assert term in TEXT
