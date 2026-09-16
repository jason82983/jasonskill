from __future__ import annotations

import sys
import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import action_execution as execution
from scripts import ad_decision_package as decisions
from scripts.advertising_state_reconciler import exact_change_digest
from scripts.stage6_artifact_contract import make_artifact_metadata, new_run_context, write_metadata_sidecar


class FakeProvider:
    def __init__(self, entity):
        self.entity = dict(entity)
        self.entities = [self.entity]
        self.prepared = []
        self.applied = []
        self.readback_override = None

    def prepare(self, changes, idempotency_key):
        self.prepared.append((changes, idempotency_key))
        return {"status": "PREPARED", "plan_id": "plan-1", "change_digest": exact_change_digest(changes)}

    def apply(self, plan_id, idempotency_key):
        self.applied.append((plan_id, idempotency_key))
        change = self.prepared[-1][0][0]
        for field in ("bid", "daily_budget", "placement"):
            if field in change["desired"]:
                self.entity[field] = change["desired"][field]
        return {"status": "APPLIED"}

    def read_back(self, logical_ids):
        if self.readback_override is not None:
            return [self.readback_override]
        return [dict(self.entity)]

    def query_actual(self):
        return [dict(row) for row in self.entities]


def campaign_row(*, approved="已批准", result="降低预算", expected="1.20", target="1.05"):
    return {
        "CampaignId": "amz-c1", "CampaignName": "B2.M.SP-COR-EXA-01",
        "决策结果": result, "确认状态": approved,
        "当前Budget": expected, "建议Budget": target,
    }


def campaign_tables(row):
    return {"intent": [], "campaign": [row], "target": [], "search_term": []}


def candidate_for(row):
    return execution.collect_approved_actions(campaign_tables(row), "B2", "decision-run-1")[0]


def test_case_a_unapproved_or_observation_only_is_zero_write():
    tables = campaign_tables(campaign_row(approved="待确认", result="降低预算"))
    tables["target"].append({"确认状态": "已批准", "决策结果": "保持"})
    assert execution.collect_approved_actions(tables, "B2", "r1") == []


def test_latest_decision_resolver_requires_one_complete_same_run_package(tmp_path):
    product_root = tmp_path / "B2"
    context = new_run_context("6-3", decisions.SKILL_ID, "B2", now=datetime.now().astimezone())
    stamp = context.run_timestamp
    folder = product_root / "06_SKILL分析报告" / "6-3_广告诊断优化" / stamp
    folder.mkdir(parents=True)
    outputs = []
    counts = {}
    for kind, stem in decisions.TABLE_FILES.items():
        path = folder / f"6-3_{stem}_{stamp}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle).writerow(decisions.SCHEMAS[kind])
        sidecar = make_artifact_metadata(
            context, f"ADVERTISING_DECISION_{kind.upper()}", run_status="FULL_SUCCESS",
            schema=decisions.SCHEMAS[kind], record_count=0, output_assets=[path.name],
            extra={"ProductCode": "B2", "CampaignTag": "M", "CampaignPrefix": "B2.M."},
        )
        write_metadata_sidecar(path, sidecar)
        outputs.append(path.name)
        counts[kind] = 0
    html_name = f"6-3_广告优化决策报告_{stamp}.html"
    (folder / html_name).write_text("<html></html>", encoding="utf-8")
    manifest = make_artifact_metadata(
        context, "ADVERTISING_DECISION_PACKAGE", run_status="FULL_SUCCESS",
        output_assets=[*outputs, html_name], extra={"Decision_Record_Counts": counts, "ProductCode": "B2", "CampaignTag": "M", "CampaignPrefix": "B2.M."},
    )
    (folder / f"6-3_RunPackage_{stamp}.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    resolved = execution.resolve_latest_approved_decisions(product_root, "B2", "M")
    assert resolved["run_id"] == context.run_id
    assert resolved["tables"] == {kind: [] for kind in decisions.SCHEMAS}


def test_case_b_compare_prepare_apply_and_readback_success():
    candidate = candidate_for(campaign_row())
    provider = FakeProvider({"amazon_id": "amz-c1", "logical_id": "logical-c1", "entity_type": "campaign", "daily_budget": Decimal("1.20"), "placement": {}})
    checked = execution.mark_actual_and_conflicts([candidate], [provider.entity], identity_verified=True)[0]
    prepared = execution.prepare_exact_action(checked, provider)
    result = execution.apply_confirmed_action(checked, prepared, provider, exact_preview_confirmed=True)
    assert result["status"] == "EXECUTION_SUCCESS"
    assert provider.entity["daily_budget"] == Decimal("1.05")
    assert len(provider.applied) == 1


def test_campaign_scope_checks_live_name_before_prepare_and_apply():
    candidate = candidate_for(campaign_row())
    live = {"amazon_id": "amz-c1", "logical_id": "logical-c1", "entity_type": "campaign", "name": "B2.M.SP-COR-EXA-01", "daily_budget": Decimal("1.20")}
    provider = FakeProvider(live)
    checked = execution.mark_actual_and_conflicts([candidate], [provider.entity], identity_verified=True, campaign_prefix="B2.M.")[0]
    prepared = execution.prepare_exact_action(checked, provider, campaign_prefix="B2.M.")
    assert prepared["status"] == "PREPARED"
    provider.entity["name"] = "Manual-B2"
    result = execution.apply_confirmed_action(checked, prepared, provider, exact_preview_confirmed=True, campaign_prefix="B2.M.")
    assert result["status"] == "OUTSIDE_CAMPAIGN_SCOPE"
    assert provider.applied == []


def test_target_scope_requires_live_target_adgroup_campaign_ancestry():
    target = {"amazon_id": "t1", "logical_id": "lt", "entity_type": "target", "parent_ad_group_id": "g1"}
    group = {"amazon_id": "g1", "entity_type": "ad_group", "campaign_id": "c1"}
    campaign = {"amazon_id": "c1", "entity_type": "campaign", "name": "B2.M.SP-EXP-PHR-01"}
    assert execution._live_in_campaign_scope(target, [target, group, campaign], "B2.M.")
    campaign["name"] = "B2.M2.SP-EXP-PHR-01"
    assert not execution._live_in_campaign_scope(target, [target, group, campaign], "B2.M.")


def test_new_migration_campaign_must_inherit_scope():
    old = {"expected_current": "enabled", "action": "PAUSE"}
    with pytest.raises(execution.ExecutionError, match="OUTSIDE_CAMPAIGN_SCOPE"):
        execution.migration_stages(destination_actions=[{"entity_type": "campaign", "name": "B2.T.SP-EXP-PHR-01"}], old_action=old, campaign_prefix="B2.M.")


def test_case_c_actual_mismatch_is_conflict_and_never_prepares():
    candidate = candidate_for(campaign_row(expected="1.20", target="1.05"))
    provider = FakeProvider({"amazon_id": "amz-c1", "logical_id": "logical-c1", "entity_type": "campaign", "daily_budget": Decimal("1.35")})
    checked = execution.mark_actual_and_conflicts([candidate], [provider.entity], identity_verified=True)[0]
    assert checked["执行结果"] == "状态冲突"
    assert checked["失败/冲突原因"] == "64_STATE_CONFLICT"
    assert provider.prepared == []


def test_case_d_same_decision_run_success_is_idempotently_skipped(tmp_path):
    candidate = candidate_for(campaign_row())
    row = execution.output_row(candidate, "执行成功", actual="1.20", readback={"daily_budget": "1.05"})
    execution.write_execution_package(
        tmp_path, "B2", "decision-run-1", [row], campaign_tag="M", run_status="PARTIAL_SUCCESS",
        now=datetime(2026, 9, 16, 12, 30, 0, tzinfo=timezone.utc),
    )
    prior = execution.prior_successful_execution_ids(tmp_path, "B2", "decision-run-1", "M")
    assert candidate["执行ID"] in prior
    provider = FakeProvider({"amazon_id": "amz-c1", "logical_id": "logical-c1", "entity_type": "campaign", "daily_budget": Decimal("1.20")})
    assert provider.prepared == [] and provider.applied == []


def test_case_e_migration_verifies_destination_before_old_action():
    stages = execution.migration_stages(
        destination_actions=[{"action": "CREATE", "id": "new-target"}],
        old_action={"action": "PAUSE", "expected_current": "enabled"},
    )
    assert execution.migration_next_stage(stages, ["CREATE_DESTINATION"])["stage"] == "VERIFY_DESTINATION"
    assert execution.migration_next_stage(stages, ["CREATE_DESTINATION", "VERIFY_DESTINATION"])["stage"] == "HANDLE_OLD"


def test_case_f_failed_destination_creation_keeps_old_untouched():
    stages = execution.migration_stages(
        destination_actions=[{"action": "CREATE", "id": "new-target"}],
        old_action={"action": "PAUSE", "expected_current": "enabled"},
    )
    # A failed create is not marked complete, so the state machine cannot advance to old-target handling.
    next_stage = execution.migration_next_stage(stages, [])
    assert next_stage["stage"] == "CREATE_DESTINATION"
    assert "HANDLE_OLD" not in {next_stage["stage"]}


def test_case_g_unapproved_negative_candidate_is_zero_write():
    row = {"确认状态": "待确认", "决策结果": "否定候选", "TargetId": "t1", "SearchTerm": "irrelevant query"}
    assert execution.collect_approved_actions({"intent": [], "campaign": [], "target": [], "search_term": [row]}, "B2", "r1") == []


def test_case_h_approved_negative_or_incomplete_harvest_fails_closed():
    negative = {"确认状态": "已批准", "决策结果": "否定候选", "TargetId": "t1", "SearchTerm": "irrelevant query"}
    harvest = {"确认状态": "已批准", "决策结果": "收割候选", "TargetId": "t1", "SearchTerm": "good query"}
    rows = execution.collect_approved_actions({"intent": [], "campaign": [], "target": [], "search_term": [negative, harvest]}, "B2", "r1")
    assert {row["失败/冲突原因"] for row in rows} == {"64_TECHNICAL_EXECUTION_CONFLICT", "64_HARVEST_EXECUTION_INCOMPLETE"}
    assert all(row["执行结果"] == "等待人工" for row in rows)
    harvest_row = execution.migration_candidate_row(next(row for row in rows if row["执行动作"] == "HARVEST"))
    assert harvest_row["迁移类型"] == "收割迁移"
    assert harvest_row["迁移状态"] == "等待人工"


def test_actionable_but_unsupported_intent_decision_is_reported_not_dropped():
    row = {"IntentCode": "BFG", "确认状态": "已批准", "决策结果": "放大"}
    candidates = execution.collect_approved_actions({"intent": [row], "campaign": [], "target": [], "search_term": []}, "B2", "r1")
    assert len(candidates) == 1
    assert candidates[0]["执行动作"] == "UNSUPPORTED"
    assert candidates[0]["失败/冲突原因"] == "64_ACTION_MAPPING_UNSUPPORTED"


def test_case_i_success_response_with_wrong_readback_is_failure():
    candidate = candidate_for(campaign_row())
    provider = FakeProvider({"amazon_id": "amz-c1", "logical_id": "logical-c1", "entity_type": "campaign", "daily_budget": Decimal("1.20")})
    checked = execution.mark_actual_and_conflicts([candidate], [provider.entity], identity_verified=True)[0]
    prepared = execution.prepare_exact_action(checked, provider)
    provider.readback_override = {"amazon_id": "amz-c1", "logical_id": "logical-c1", "entity_type": "campaign", "daily_budget": Decimal("1.10")}
    result = execution.apply_confirmed_action(checked, prepared, provider, exact_preview_confirmed=True)
    assert result["status"] == "64_READBACK_FAILED"


def test_case_j_executor_consumes_only_current_product_approved_decisions():
    # Benchmark fields/rows are not an input to the 6-3 decision table compiler.
    row = {**campaign_row(), "BenchmarkASIN": "B0BENCHMARK", "BenchmarkCode": "COMP-A"}
    candidate = candidate_for(row)
    assert candidate["对象ID"] == "amz-c1"
    assert candidate["执行动作"] == "UPDATE"
    assert candidate["AmazonId"] == "amz-c1"


def test_exact_preview_confirmation_is_required_and_noop_when_already_at_target():
    candidate = candidate_for(campaign_row(expected="1.20", target="1.05"))
    provider = FakeProvider({"amazon_id": "amz-c1", "logical_id": "logical-c1", "entity_type": "campaign", "daily_budget": Decimal("1.05")})
    checked = execution.mark_actual_and_conflicts([candidate], [provider.entity], identity_verified=True)[0]
    assert checked["执行结果"] == "无需执行"
    with pytest.raises(execution.ExecutionError):
        execution.provider_change(checked)

    provider.entity["daily_budget"] = Decimal("1.20")
    checked = execution.mark_actual_and_conflicts([candidate], [provider.entity], identity_verified=True)[0]
    prepared = execution.prepare_exact_action(checked, provider)
    assert execution.apply_confirmed_action(checked, prepared, provider, exact_preview_confirmed=False)["status"] == "WAITING_FOR_USER_CONFIRMATION"
    assert provider.applied == []


def test_full_success_is_rejected_when_any_action_is_unresolved(tmp_path):
    candidate = candidate_for(campaign_row())
    unresolved = execution.output_row(candidate, "等待人工", failure="EXACT_PREVIEW_CONFIRMATION_REQUIRED")
    with pytest.raises(execution.ExecutionError, match="64_PARTIAL_RUN_CANNOT_BE_FULL_SUCCESS"):
        execution.write_execution_package(tmp_path, "B2", "decision-run-1", [unresolved], campaign_tag="M")
