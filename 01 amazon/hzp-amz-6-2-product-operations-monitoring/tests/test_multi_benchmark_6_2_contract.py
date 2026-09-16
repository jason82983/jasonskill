"""Old filename retained; verifies that benchmark evidence is not ad runtime fact."""
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
CONTRACT = Path(__file__).resolve().parents[1] / "references" / "erp-keyword-analysis.md"


def test_data_only_scope_excludes_benchmark_and_business_judgments():
    text = SKILL.read_text(encoding="utf-8")
    assert "DATA ONLY" in text
    assert "must not assess performance" in text
    assert "Never call a write capability" in text
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "ERP PickPwKView" in contract and "does not query" in contract
