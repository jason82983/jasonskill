from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.advertising_state_reconciler import (
    ad_group_logical_id,
    build_desired_state_from_605,
    build_diff,
    campaign_logical_id,
    execute_approved_diff,
    execution_id,
    reconcile_live_state,
    stable_id,
    target_logical_id,
    translate_role,
    resolve_mode,
    reserve_campaign_sequences,
)


def campaign(**overrides):
    value = {
        "entity_type": "campaign", "logical_id": "campaign:B2|M|SBG|SP|COR|EXA|DEFAULT",
        "product_code": "B2", "var_code": "M", "intent_code": "SBG", "ad_type": "SP",
        "technical_role": "COR", "target_type": "KEYWORD", "match_type": "EXACT",
        "name": "B2.M.SP-COR-EXA-SBG-01", "daily_budget": 20.0,
        "placement": {"top": 50, "rest": 0, "product": 0}, "bidding_strategy": "DOWN_ONLY",
        "status": "ENABLED", "approved": True,
    }
    value.update(overrides)
    return value


def group(parent, **overrides):
    value = {"entity_type": "ad_group", "logical_id": "ad_group:campaign:B2|M|SBG|SP|COR|EXA|DEFAULT|G1",
             "parent_logical_id": parent, "name": "B2.M.COR-01", "default_bid": 1.25,
             "status": "ENABLED", "approved": True}
    value.update(overrides)
    return value


def target(parent, battle="BU-001", **overrides):
    value = {"entity_type": "target", "logical_id": f"target:{battle}", "battle_unit_id": battle,
             "parent_logical_id": parent, "target_type": "KEYWORD", "match_type": "EXACT",
             "value": "gift for sister", "bid": 1.25, "status": "ENABLED", "approved": True}
    value.update(overrides)
    return value


class FakeProvider:
    def __init__(self, changes=None, *, actual=None, wrong_preview=False, wrong_readback=False, identity_mismatch=False):
        self.changes = changes or []
        self.actual = deepcopy(actual or [])
        self.wrong_preview = wrong_preview
        self.wrong_readback = wrong_readback
        self.identity_mismatch = identity_mismatch
        self.applied = 0
        self.prepared = 0

    def prepare(self, changes, idempotency_key):
        from scripts.advertising_state_reconciler import exact_change_digest
        self.prepared += 1
        digest = "wrong" if self.wrong_preview else exact_change_digest(changes)
        return {"status": "PREPARED", "plan_id": "mock-plan-1", "change_digest": digest}

    def apply(self, plan_id, idempotency_key):
        self.applied += 1
        for row in self.changes:
            if row["action"] in {"CREATE", "UPDATE"}:
                self._upsert(row["desired"])
        return {"status": "APPLIED"}

    def _upsert(self, desired):
        actual = next((row for row in self.changes if row.get("logical_id") == desired["logical_id"] and row.get("amazon_id")), None)
        result = {key: value for key, value in desired.items() if key != "approved"}
        result["amazon_id"] = actual["amazon_id"] if actual else f"mock-{desired['entity_type']}-id"
        self.changes = [row for row in self.changes if row.get("logical_id") != desired["logical_id"]]
        self.changes.append(result)

    def read_back(self, logical_ids):
        rows = [row for row in self.changes if row.get("logical_id") in logical_ids]
        if self.wrong_readback and rows:
            rows[0] = {**rows[0], "status": "PAUSED"}
        if self.identity_mismatch and rows:
            rows[0] = {**rows[0], "advertised_asin": "B0BENCHMARK"}
        return deepcopy(rows)

    def query_actual(self):
        return deepcopy(self.actual)


def plan_bundle(battle_rows, *, run_id="605-run-1"):
    return {"status": "LATEST_VALID_RUN_BUNDLE_RESOLVED", "run_id": run_id,
            "assets": {"intent": {"rows": [{"确认状态": "APPROVED"}]},
                       "keyword": {"rows": [{"确认状态": "APPROVED"}]},
                       "battle": {"rows": battle_rows}}}


def battle_unit(unit_id, intent, task, method, control="共享", **changes):
    row = {"作战单元ID": unit_id, "意图代码": intent, "作战任务": task,
           "控制方式": control, "计划阶段": "PHASE_1", "投放方式": method,
           "确认状态": "APPROVED", "词": f"term {unit_id}", "中文": "测试词"}
    row.update(changes)
    return row


def parameters(*, daily_budget=20, placement=None, bidding_strategy="DOWN_ONLY", bid=1.1,
               logical_group="DEFAULT", campaign_status="ENABLED"):
    return {"daily_budget": daily_budget, "placement": placement or {"top": 0, "rest": 0, "product": 0},
            "bidding_strategy": bidding_strategy, "target_bid": bid,
            "ad_group_default_bid": 1.0, "campaign_status": campaign_status,
            "ad_group_status": "ENABLED", "target_status": "ENABLED",
            "product_status": "ENABLED", "logical_group": logical_group}


def verified_identity():
    return {"identity_status": "ADVERTISING_IDENTITY_VERIFIED", "product_code": "B2", "var_code": "M",
            "own_asin": "B0OWN", "child_asin": "B0OWN", "advertised_asin": "B0OWN",
            "advertised_skus": ["B2-M-SKU"], "benchmark_asins": ["B0BENCHMARK"],
            "store": "Q2-US", "marketplace": "US", "portfolio_name": "B2", "portfolio_id": "p-1"}


def test_role_translation_only_maps_approved_business_language():
    assert translate_role("首攻", "EXACT") == ("COR", "EXA", "SP")
    assert translate_role("扩展", "PHRASE") == ("EXP", "PHR", "SP")
    assert translate_role("探索", "BROAD") == ("DIS", "BRO", "SP")
    assert translate_role("探索", "AUTO") == ("DIS", "AUT", "SP")
    assert translate_role("首攻", "ASIN") == ("COM", "ASI", "SP")
    assert translate_role("探索", "PT") == ("DIS", "PT", "SP")
    assert translate_role("探索", "CATEGORY") == ("CAT", "CAT", "SP")
    with pytest.raises(ValueError, match="ROLE_TRANSLATION_AMBIGUOUS"):
        translate_role("暂缓", "EXACT")


def test_stable_logical_ids_and_execution_id_ignore_wall_clock():
    campaign_id = campaign_logical_id("B2", "M", ["SBG"], "SP", "COR", "EXA")
    assert campaign_id == campaign_logical_id("B2", "M", ["SBG", "SBG"], "SP", "COR", "EXA")
    assert campaign_id != campaign_logical_id("B2", "M", ["WIDE"], "SP", "COR", "EXA")
    assert ad_group_logical_id(campaign_id, "G1") == stable_id("ad_group", campaign_id, "G1")
    assert target_logical_id("BU-001") == "target:BU-001"
    desired = [campaign()]
    assert execution_id("B2", "605-run-1", desired) == execution_id("B2", "605-run-1", desired)
    assert execution_id("B2", "605-run-1", desired) != execution_id("B2", "605-run-2", desired)
    assert campaign_logical_id("B2", "M", [], "SP", "DIS", "AUT").endswith("|NO_INTENT|SP|DIS|AUT|DEFAULT")


def test_control_mode_is_preserved_as_campaign_identity_boundary():
    independent = campaign_logical_id("B2", "M", ["SBG"], "SP", "COR", "EXA", control_mode="独立")
    shared = campaign_logical_id("B2", "M", ["SBG", "SG"], "SP", "EXP", "PHR", control_mode="共享")
    assert "SBG" in independent and independent.endswith("|独立")
    assert "NO_INTENT" in shared and "SBG" not in shared and shared.endswith("|共享")
    with pytest.raises(ValueError, match="NO_INVESTMENT_HAS_NO_CAMPAIGN"):
        campaign_logical_id("B2", "M", [], "SP", "COR", "EXA", control_mode="不投")


def test_build_vs_reconcile_mode_is_derived_from_live_actual_state():
    assert resolve_mode([]) == "BUILD"
    assert resolve_mode([{"entity_type": "campaign", "amazon_id": "live-1"}]) == "RECONCILE"


def test_unapproved_and_proposed_entities_never_enter_desired_state():
    with pytest.raises(ValueError, match="INVALID_APPROVAL_STATE"):
        build_diff([campaign(approved=False)], [])


def test_build_creates_parent_before_child_and_target():
    c = campaign()
    g = group(c["logical_id"])
    t = target(g["logical_id"])
    actions = build_diff([t, g, c], [])
    assert [action["entity_type"] for action in actions] == ["campaign", "ad_group", "target"]
    assert [action["action"] for action in actions] == ["CREATE"] * 3


def test_reconcile_has_only_update_and_no_change_for_exact_logical_identity():
    desired = campaign()
    actual = {**desired, "approved": None, "amazon_id": "amz-campaign-1"}
    assert build_diff([desired], [actual])[0]["action"] == "NO_CHANGE"
    changed = build_diff([campaign(daily_budget=25.0)], [actual])[0]
    assert changed["action"] == "UPDATE"
    assert changed["amazon_id"] == "amz-campaign-1"
    assert changed["before"]["daily_budget"] == {"before": 20.0, "desired": 25.0}


def test_new_approved_battle_unit_creates_only_new_target():
    c, g = campaign(), group(campaign()["logical_id"])
    existing = [{**c, "approved": None, "amazon_id": "c1"},
                {**g, "approved": None, "amazon_id": "g1"},
                {**target(g["logical_id"], "BU-001"), "approved": None, "amazon_id": "t1"}]
    desired = [c, g, target(g["logical_id"], "BU-001"), target(g["logical_id"], "BU-002", value="new term")]
    assert [(row["logical_id"], row["action"]) for row in build_diff(desired, existing) if row["action"] != "NO_CHANGE"] == [("target:BU-002", "CREATE")]


def test_shared_benchmark_evidence_does_not_create_duplicate_product_architectures():
    one = campaign()
    # Benchmark observations are not identity inputs; the same Current Product
    # Intent/role/match produces one campaign identity.
    assert campaign_logical_id("B2", "M", ["SBG"], "SP", "COR", "EXA") == one["logical_id"]


def test_actual_without_stable_identity_is_rejected_instead_of_name_matched():
    with pytest.raises(ValueError, match="CAMPAIGN_IDENTITY_CONFLICT"):
        build_diff([campaign()], [{"entity_type": "campaign", "name": campaign()["name"], "amazon_id": "a1"}])


def test_same_logical_id_with_changed_advertised_identity_fails_closed():
    desired = campaign(advertised_asin="B0NEW")
    actual = {**campaign(advertised_asin="B0OLD"), "amazon_id": "a1"}
    with pytest.raises(ValueError, match="CAMPAIGN_IDENTITY_CONFLICT"):
        build_diff([desired], [actual])


def test_desired_state_requires_parent_entities_and_correct_parent_type():
    with pytest.raises(ValueError, match="DESIRED_STATE_INVALID"):
        build_diff([target("missing-group")], [])
    c = campaign()
    wrong_parent = target(c["logical_id"])
    with pytest.raises(ValueError, match="DESIRED_STATE_INVALID"):
        build_diff([c, wrong_parent], [])


def test_extraneous_actual_only_becomes_pause_candidate_and_is_never_executed():
    actual = {**campaign(), "approved": None, "amazon_id": "a1"}
    candidate = {**actual, "logical_id": "campaign:old", "name": "legacy"}
    actions = build_diff([], [candidate])
    assert actions[0]["action"] == "PAUSE_CANDIDATE"
    provider = FakeProvider(actions)
    result = execute_approved_diff(actions, provider, approved=True, idempotency_key="run-1")
    assert result["status"] == "NO_CHANGE"
    assert provider.prepared == provider.applied == 0


def test_prepare_apply_readback_success_and_failure_are_verified():
    actions = build_diff([campaign()], [])
    provider = FakeProvider(actions)
    result = execute_approved_diff(actions, provider, approved=True, idempotency_key="run-1")
    assert result["status"] == "FULL_SUCCESS"
    assert result["read_back"][0]["amazon_id"] == "mock-campaign-id"

    provider = FakeProvider(actions, wrong_readback=True)
    assert execute_approved_diff(actions, provider, approved=True, idempotency_key="run-1")["status"] == "READBACK_FAILED"


def test_update_failure_is_reported_as_update_and_readback_failure_is_explicit():
    desired = campaign(daily_budget=25.0)
    actual = {**campaign(), "amazon_id": "c1"}
    actions = build_diff([desired], [actual])

    class FailedApply(FakeProvider):
        def apply(self, plan_id, idempotency_key):
            return {"status": "FAILED"}

    assert execute_approved_diff(actions, FailedApply(actions), approved=True, idempotency_key="u1")["status"] == "UPDATE_FAILED"

    class FailedReadBack(FakeProvider):
        def read_back(self, logical_ids):
            raise RuntimeError("mock read-back unavailable")

    assert execute_approved_diff(actions, FailedReadBack(actions), approved=True, idempotency_key="u2")["status"] == "READBACK_FAILED"


def test_material_prepare_diff_blocks_apply_and_unapproved_diff_is_read_only():
    actions = build_diff([campaign()], [])
    provider = FakeProvider(actions, wrong_preview=True)
    result = execute_approved_diff(actions, provider, approved=True, idempotency_key="run-1")
    assert result["status"] == "TECHNICAL_EXECUTION_CONFLICT"
    assert provider.applied == 0

    provider = FakeProvider(actions)
    assert execute_approved_diff(actions, provider, approved=False, idempotency_key="run-2")["status"] == "EXECUTION_NOT_READY"
    assert provider.prepared == provider.applied == 0


def test_second_run_is_zero_writes_after_readback_actual_state():
    desired = [campaign()]
    first_actions = build_diff(desired, [])
    provider = FakeProvider(first_actions)
    assert execute_approved_diff(first_actions, provider, approved=True, idempotency_key="stable-run")["status"] == "FULL_SUCCESS"
    actual = [{key: value for key, value in row.items() if key != "approved"} for row in provider.changes]
    second_actions = build_diff(desired, actual)
    assert [row["action"] for row in second_actions] == ["NO_CHANGE"]
    assert execute_approved_diff(second_actions, provider, approved=True, idempotency_key="stable-run")["status"] == "NO_CHANGE"
    assert provider.applied == 1


def test_605_approved_units_create_control_aware_desired_state_and_stable_campaigns():
    rows = [battle_unit(f"BU-{n:03d}", "SBG", "首攻", "EXACT", "独立") for n in range(1, 9)]
    rows += [battle_unit("BU-101", "WIDE", "扩展", "PHRASE"),
             battle_unit("BU-102", "GIFT", "扩展", "PHRASE"),
             battle_unit("BU-201", "DISC", "探索", "BROAD"),
             battle_unit("BU-999", "HOLD", "探索", "BROAD", "不投")]
    params = {row["作战单元ID"]: parameters() for row in rows}
    state = build_desired_state_from_605(plan_bundle(rows), verified_identity(), params, product_code="B2", campaign_tag="M")
    campaigns = [row for row in state["entities"] if row["entity_type"] == "campaign"]
    targets = [row for row in state["entities"] if row["entity_type"] == "target"]
    assert len(campaigns) == 3
    assert any(row["name"] == "B2.M.SP-COR-EXA-SBG-01" for row in campaigns)
    assert any(row["name"] == "B2.M.SP-EXP-PHR-01" for row in campaigns)
    assert any(row["name"] == "B2.M.SP-DIS-BRO-01" for row in campaigns)
    assert len([row for row in targets if row["battle_unit_id"].startswith("BU-00")]) == 8
    assert "BU-999" not in {row["battle_unit_id"] for row in targets}
    assert all(row["advertised_asin"] == "B0OWN" for row in state["entities"] if row["entity_type"] == "advertised_product")


def test_campaign_tag_is_opaque_and_separate_from_real_variant():
    row = battle_unit("BU-1", "SBG", "首攻", "EXACT", "独立")
    state = build_desired_state_from_605(plan_bundle([row]), verified_identity(), {"BU-1": parameters()}, product_code="B2", campaign_tag="X1")
    campaign = next(row for row in state["entities"] if row["entity_type"] == "campaign")
    assert campaign["name"] == "B2.X1.SP-COR-EXA-SBG-01"
    assert campaign["campaign_tag"] == "X1"
    assert campaign["var_code"] == "M"
    assert state["CampaignPrefix"] == "B2.X1."


def test_existing_matching_logical_campaign_renamed_outside_scope_fails_closed():
    row = battle_unit("BU-1", "SBG", "首攻", "EXACT", "独立")
    actual = [{"entity_type": "campaign", "logical_id": campaign_logical_id("B2", "M", ["SBG"], "SP", "COR", "EXA", "PHASE_1:DEFAULT", "独立", "M"), "name": "Manual-B2"}]
    with pytest.raises(ValueError, match="OUTSIDE_CAMPAIGN_SCOPE"):
        build_desired_state_from_605(plan_bundle([row]), verified_identity(), {"BU-1": parameters()}, product_code="B2", campaign_tag="M", actual_entities=actual)


def test_shared_group_requires_campaign_level_budget_placement_compatibility():
    rows = [battle_unit("BU-1", "I1", "扩展", "PHRASE"), battle_unit("BU-2", "I2", "扩展", "PHRASE")]
    params = {"BU-1": parameters(daily_budget=20), "BU-2": parameters(daily_budget=30)}
    with pytest.raises(ValueError, match="SHARED_GROUP_INCOMPATIBLE"):
        build_desired_state_from_605(plan_bundle(rows), verified_identity(), params, product_code="B2", campaign_tag="M")


def test_605_target_without_explicit_target_value_fails_instead_of_guessing():
    row = battle_unit("BU-PT", "PT1", "探索", "PT", target_value="")
    with pytest.raises(ValueError, match="TECHNICAL_EXECUTION_CONFLICT"):
        build_desired_state_from_605(plan_bundle([row]), verified_identity(), {"BU-PT": parameters()}, product_code="B2", campaign_tag="M")


def test_sequence_registry_is_reserved_append_only_and_reused():
    from pathlib import Path
    import tempfile
    row = battle_unit("BU-1", "SBG", "首攻", "EXACT", "独立")
    bundle = plan_bundle([row])
    desired = build_desired_state_from_605(bundle, verified_identity(), {"BU-1": parameters()}, product_code="B2", campaign_tag="M")
    with tempfile.TemporaryDirectory() as temp:
        manifest = Path(temp) / "campaign-sequences.jsonl"
        persisted = reserve_campaign_sequences(manifest, desired)
        rerun = build_desired_state_from_605(bundle, verified_identity(), {"BU-1": parameters()}, product_code="B2", campaign_tag="M",
                                             sequence_registry=persisted)
        assert persisted == rerun["sequence_registry"]
        assert [row["name"] for row in desired["entities"] if row["entity_type"] == "campaign"] == [
            row["name"] for row in rerun["entities"] if row["entity_type"] == "campaign"]
        lines_before = manifest.read_text(encoding="utf-8").splitlines()
        reserve_campaign_sequences(manifest, rerun)
        assert manifest.read_text(encoding="utf-8").splitlines() == lines_before


def test_shared_to_independent_moves_target_without_deleting_or_updating_old_target():
    old_campaign = campaign(logical_id="campaign:shared", control_mode="共享", intent_code=None,
                            name="B2.M.SP-EXP-PHR-01", technical_role="EXP", target_type="PHR")
    old_group = group(old_campaign["logical_id"], logical_id="ad_group:shared")
    old_target = target(old_group["logical_id"], "BU-MOVE", logical_id=target_logical_id("BU-MOVE", old_campaign["logical_id"]),
                        control_mode="共享", intent_code="SBG")
    actual = [{**row, "approved": None, "amazon_id": f"live-{index}"}
              for index, row in enumerate((old_campaign, old_group, old_target), 1)]
    new_campaign = campaign(logical_id="campaign:independent", name="B2.M.SP-COR-EXA-SBG-01",
                            technical_role="COR", target_type="EXA", control_mode="独立", intent_code="SBG")
    new_group = group(new_campaign["logical_id"], logical_id="ad_group:independent")
    new_target = target(new_group["logical_id"], "BU-MOVE",
                        logical_id=target_logical_id("BU-MOVE", new_campaign["logical_id"]),
                        control_mode="独立", intent_code="SBG")
    actions = build_diff([new_campaign, new_group, new_target], actual)
    assert next(row for row in actions if row["logical_id"] == new_target["logical_id"])["action"] == "CREATE"
    assert next(row for row in actions if row["logical_id"] == old_target["logical_id"])["action"] == "MIGRATION_CANDIDATE"
    assert not any(row["action"] in {"DELETE", "ARCHIVE"} for row in actions)


def test_readback_verifies_advertised_product_identity_not_only_mutable_fields():
    c = campaign()
    g = group(c["logical_id"], logical_id="group:B2-M")
    product = {"entity_type": "advertised_product", "logical_id": "product:B2-M", "parent_logical_id": g["logical_id"],
               "product_code": "B2", "var_code": "M", "own_asin": "B0OWN", "advertised_asin": "B0OWN",
               "sku": "B2-M-SKU", "name": "B2-M-SKU", "status": "ENABLED", "approved": True}
    actual = [{**c, "approved": None, "amazon_id": "c1"}, {**g, "approved": None, "amazon_id": "g1"}]
    actions = build_diff([c, g, product], actual)
    result = execute_approved_diff(actions, FakeProvider(actions, identity_mismatch=True), approved=True, idempotency_key="r1")
    assert result["status"] == "READBACK_FAILED"


def test_verified_identity_manifest_preserves_target_to_battle_unit_lineage(tmp_path):
    import json
    from scripts.advertising_state_reconciler import append_verified_entities
    manifest = tmp_path / "identities.jsonl"
    append_verified_entities(manifest, [{"entity_type": "target", "logical_id": "target:BU-1",
        "amazon_id": "target-7", "parent_logical_id": "group-1", "battle_unit_id": "BU-1",
        "intent_code": "I-1", "control_mode": "共享", "target_type": "KEYWORD",
        "value": "wide walking shoes", "match_type": "PHRASE"}], run_id="run-1",
        generated_at="2026-09-16T10:00:00+08:00")
    event = json.loads(manifest.read_text(encoding="utf-8").strip())
    assert event["amazon_id"] == "target-7"
    assert event["battle_unit_id"] == "BU-1"
    assert event["intent_code"] == "I-1"
    assert event["target_value"] == "wide walking shoes"
    assert event["match_type"] == "PHRASE"


def test_live_reconcile_requeries_after_uncertain_apply_and_returns_recovery_diff():
    desired = [campaign()]

    class TimeoutAfterApply(FakeProvider):
        def __init__(self):
            super().__init__([])
            self.queries = 0

        def query_actual(self):
            self.queries += 1
            if self.queries == 1:
                return []
            return [{**campaign(), "approved": None, "amazon_id": "c1"}]

        def apply(self, plan_id, idempotency_key):
            raise TimeoutError("uncertain apply")

    provider = TimeoutAfterApply()
    result = reconcile_live_state(desired, provider, approved=True, idempotency_key="reconcile-1")
    assert result["status"] == "CREATE_FAILED"
    assert result["recovery_diff"][0]["action"] == "NO_CHANGE"
    assert provider.queries == 2
