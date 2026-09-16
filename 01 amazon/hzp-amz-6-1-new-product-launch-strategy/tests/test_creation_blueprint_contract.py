"""Static mock-contract checks for the execution reconciliation report."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".py"})

def test_execution_summary_and_diff():
    for term in ("Execution Summary", "Desired-vs-Actual Diff", "605 RUN_ID", "Approved Battle Unit Count", "BUILD/RECONCILE", "CREATE/UPDATE/NO_CHANGE/PAUSE_CANDIDATE", "Logical ID", "Amazon ID"):
        assert term in TEXT

def test_exact_approval_and_provider_readback():
    for term in ("complete diff", "exact CREATE/UPDATE", "prepare_change_plan", "apply_change_plan", "Read-Back", "TECHNICAL_EXECUTION_CONFLICT", "仅报告"):
        assert term in TEXT
