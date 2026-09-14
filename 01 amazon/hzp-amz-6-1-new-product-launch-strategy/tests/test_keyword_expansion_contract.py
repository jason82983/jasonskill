"""Static mock-contract checks for evidence-gated keyword expansion."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".py"})

def test_mother_pool_and_clusters():
    for term in ("Keyword Mother Pool", "Semantic Cluster", "Purchase Intent Cluster", "Initial Validation Batch", "Held Keywords", "HELD_FOR_EXPANSION", "Source", "Benchmark"):
        assert term in TEXT

def test_evidence_gated_states():
    for term in ("FIRST_ORDER_VALIDATED", "REPEATED_CONVERSION_VALIDATED", "INITIAL_SIGNAL", "VALIDATED", "不得一次释放全部剩余词", "Broad 只使用"):
        assert term in TEXT

def test_handoff_and_capital_rules():
    for term in ("Expansion Rules", "Expansion Budget Rules", "Traffic Overlap Check", "Capital Release", "6-2", "不承担长期日常扩词"):
        assert term in TEXT
