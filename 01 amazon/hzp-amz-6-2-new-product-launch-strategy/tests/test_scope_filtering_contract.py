"""Regression checks for scope filtering before 6-2 mode/diff calculation."""

import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1].parent
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from scripts.advertising_state_reconciler import reconcile_live_state  # noqa: E402


class FakeProvider:
    def __init__(self, actual):
        self.actual = actual

    def query_actual(self):
        return list(self.actual)

    def prepare(self, changes, idempotency_key):
        raise AssertionError("scope tests must not write")

    def apply(self, plan_id, idempotency_key):
        raise AssertionError("scope tests must not write")

    def read_back(self, logical_ids):
        raise AssertionError("scope tests must not write")


def _desired_campaign():
    return {
        "entity_type": "campaign",
        "logical_id": "campaign:new",
        "product_code": "B2",
        "campaign_tag": "M",
        "campaign_prefix": "B2.M.",
        "name": "B2.M.SP-COR-EXA-SG-01",
        "daily_budget": 1,
        "placement": {},
        "bidding_strategy": "manual",
        "status": "enabled",
        "approved": True,
    }


def test_outside_scope_campaign_does_not_change_mode_or_create_pause_candidate():
    result = reconcile_live_state(
        [_desired_campaign()],
        FakeProvider([
            {"entity_type": "campaign", "logical_id": "campaign:old", "amazon_id": "A1", "name": "B2.SP-COR-EXA-01"},
            {"entity_type": "ad_group", "logical_id": "adgroup:old", "amazon_id": "A2", "parent_logical_id": "campaign:old", "name": "B2.SP-COR-EXA-01"},
        ]),
        approved=False,
        idempotency_key="scope-test",
    )
    assert result["execution_mode"] == "BUILD"
    assert [row["action"] for row in result["actions"]] == ["CREATE"]


def test_in_scope_campaign_still_selects_reconcile():
    result = reconcile_live_state(
        [_desired_campaign()],
        FakeProvider([
            {"entity_type": "campaign", "logical_id": "campaign:new", "amazon_id": "A3", "name": "B2.M.SP-COR-EXA-SG-01", "campaign_prefix": "B2.M."},
            {"entity_type": "campaign", "logical_id": "campaign:old", "amazon_id": "A1", "name": "B2.SP-COR-EXA-01"},
        ]),
        approved=False,
        idempotency_key="scope-test",
    )
    assert result["execution_mode"] == "RECONCILE"
    assert all(row.get("logical_id") != "campaign:old" for row in result["actions"])
