import sys
from pathlib import Path

SCRIPTS = Path(r"C:\Users\qmhzp\.codex\skills")
sys.path.insert(0, str(SCRIPTS))
from scripts.advertising_state_reconciler import build_desired_state_from_6_1  # noqa: E402


def test_6_1_stops_when_creation_blueprint_is_not_ready():
    plan = {
        "status": "LATEST_VALID_RUN_BUNDLE_RESOLVED", "run_id": "run-1",
        "assets": {
            "intent": {"rows": [{"意图代码": "SG"}]},
            "keyword": {"rows": [{"Id": "1"}]},
            "battle": {"rows": [{"Id": "1", "作战单元ID": "u1", "确认状态": "APPROVED",
                                     "计划阶段": "PHASE_1", "控制方式": "独立"}]},
            "creation": {"rows": [{"Id": "1", "作战单元ID": "u1", "Parameter Status": "EXECUTION_NOT_READY"}]},
        },
    }
    try:
        build_desired_state_from_6_1(plan, {}, {}, product_code="B2", campaign_tag="M")
    except ValueError as exc:
        assert str(exc) == "CREATION_BLUEPRINT_NOT_READY"
    else:
        raise AssertionError("6-2 must not infer missing 6-1 creation parameters")

