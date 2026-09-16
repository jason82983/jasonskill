from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_identity_and_decide_only_pipeline():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: hzp-amz-6-3-advertising-diagnosis-optimization" in skill
    assert "6-3｜广告诊断优化" in skill
    assert "6-2 DATA → 6-3 DECIDE → human approval → 6-4 APPLY" in skill
    assert "never writes Amazon Ads" in skill
    assert "resolve_latest_valid_62_package" in skill
    assert "resolve_latest_approved_battle_plan" in skill
    assert "resolve_603_bundle" in skill
    assert "606_EVIDENCE_NOT_AVAILABLE" in skill
    assert "apply_change_plan" in skill  # Explicitly prohibited, not called.
    assert "scripts/ad_decision_package.py:write_decision_package" in skill


def test_html_is_four_csv_derived_and_observation_queue_is_required():
    text = (ROOT / "templates" / "report-outline.md").read_text(encoding="utf-8")
    for phrase in ("four CSVs", "继续观察清单", "紧急处理候选", "待确认变更", "6-3 DECIDES only"):
        assert phrase in text


def test_obsolete_apply_materials_do_not_remain_as_active_references():
    refs = ROOT / "references"
    assert not (refs / "auto-execution-policy.md").exists()
    assert not (refs / "authorization-adapter.md").exists()
    assert not (refs / "evidence-gated-keyword-expansion.md").exists()
    assert not (refs / "diagnosis-framework.md").exists()
