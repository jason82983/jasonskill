from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_final_decide_contract_is_explicit():
    text = (ROOT / "references" / "decision-engine-contract.md").read_text(encoding="utf-8")
    for term in (
        "6-3 DATA → 6-4 DECIDE → 人工批准(V1) → 6-5 APPLY → 6-6 REPORT",
        "Evidence Gate",
        "DaysSinceLastChange",
        "Change Clock",
        "Decision Challenge",
        "Cross-Level Consistency",
        "Reason Trace",
        "ExpectedCurrent",
        "DECISION_PACKAGE_INCOMPLETE",
        "SCOPE_CONTAMINATION",
    ):
        assert term in text


def test_decide_writer_has_no_amazon_write_call():
    script = (Path(__file__).resolve().parents[2] / "scripts" / "ad_decision_package.py").read_text(encoding="utf-8")
    assert "does not query or mutate Amazon Ads" in script
    assert "apply_change_plan(" not in script
    assert 'Amazon_Ads_Writes": False' in script


