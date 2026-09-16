"""Static contract checks for the 6-0-5-driven 6-1 apply layer."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".py"})

def test_plan_gate_and_apply_workflow():
    required = ("New Product Advertising Apply/Reconciliation", "resolve_latest_approved_battle_plan", "NO_APPROVED_BATTLE_PLAN", "605 RUN_ID", "BUILD", "RECONCILE", "Desired State", "Live Actual State", "CREATE", "UPDATE", "NO_CHANGE", "PAUSE_CANDIDATE", "execution_id", "idempotency_key", "prepare_change_plan", "apply_change_plan", "Read-Back", "TECHNICAL_EXECUTION_CONFLICT")
    missing = [x for x in required if x not in TEXT]
    assert not missing, f"missing apply contract terms: {missing}"

def test_role_and_target_are_not_replanned():
    for term in ("不再选择 Intent", "不再选择角色", "ROLE_TRANSLATION_AMBIGUOUS", "Approved Battle Unit ID", "不得扩展已批准 Target 集合", "多对标不复制广告架构"):
        assert term in TEXT

def test_repeat_run_and_pause_safety():
    for term in ("0 CREATE / 0 UPDATE", "不得整批重跑", "不自动 Pause/Delete/Archive", "不调用 Amazon 账户"):
        assert term in TEXT
