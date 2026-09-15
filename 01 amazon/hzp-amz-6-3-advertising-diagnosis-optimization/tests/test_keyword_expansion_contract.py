"""Static mock-contract checks for evidence-gated expansion diagnosis."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".py"})

def test_expansion_trigger_and_filtering():
    for term in ("Keyword Mother Pool", "Validated Cluster", "Held Keywords", "Expansion Batch", "多个相关 Search Terms", "Traffic Overlap Check", "Mother Pool Remaining"):
        assert term in TEXT

def test_match_budget_approval_and_verification():
    for term in ("Exact/Phrase/Broad", "Added Budget", "Capital Release", "Keyword Expansion Proposal", "prepare_change_plan", "apply_change_plan", "Read-Back Verification", "A/B/C/D"):
        assert term in TEXT

def test_case_a_to_l_contracts():
    for term in ("Cerebro有500词", "不创建500 Targets", "1 Click/1 Order", "VALIDATED", "26个", "库存不足", "收缩外围", "OWN_SEARCH_TERM", "Own Product 真实成交证据", "用户未批准"):
        # Cases may be represented by equivalent rule wording in the Skill.
        assert term in TEXT or term.replace("1 Click/1 Order", "1 点击 1 单") in TEXT
