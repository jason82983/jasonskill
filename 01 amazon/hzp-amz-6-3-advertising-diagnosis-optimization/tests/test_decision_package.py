import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import ad_decision_package as mod


def _row(kind, **values):
    row = {name: "" for name in mod.SCHEMAS[kind]}
    row.update(values)
    return row


def _tables():
    return {
        "intent": [_row("intent", IntentCode="I01", **{
            "精准泛词": "wide walking shoes", "决策成熟度": "继续观察", "决策结果": "继续观察",
            "决策原因": "近7日仅6次点击且无订单，归因仍可能回补。", "下一观察条件": "积累更多有效点击并确认归因成熟。", "确认状态": "待确认",
        })],
        "campaign": [_row("campaign", CampaignId="C1", CampaignName="B2.M.SP-COR-EXA-01", **{
            "当前Budget": "30", "建议Budget": "", "当前Placement": "DATA_NOT_AVAILABLE", "建议Placement": "",
            "决策成熟度": "可决策", "决策结果": "保持", "决策原因": "近14日预算利用未显示约束，当前维持原预算。", "下一观察条件": "预算利用或订单趋势明显变化时复核。", "确认状态": "待确认",
        })],
    "target": [_row("target", TargetId="T1", CampaignId="C1", IntentCode="I01", **{
            "当前Bid": "1.20", "建议Bid": "", "决策成熟度": "继续观察", "决策结果": "继续观察",
            "决策原因": "近3日点击样本不足，且无上次修改时间可核验。", "下一观察条件": "获得可解释的新增点击及转化后复核。", "确认状态": "待确认",
        })],
    "search_term": [_row("search_term", SearchTerm="irrelevant query", TargetId="T1", CampaignId="C1", **{
            "建议处理方式": "否定候选", "决策成熟度": "紧急处理", "决策结果": "否定候选",
            "决策原因": "即时异常：搜索词明确指向不相关商品类型，未出现目标产品需求。", "下一观察条件": "交人工/6-1确认后回读查询词覆盖状态。", "确认状态": "待确认",
        })],
    }


def _scope_inputs(run_id="6-2_B2_20260916_120000", tag="M"):
    return [{"Input_Skill": "hzp-amz-6-2-product-operations-monitoring", "Input_Run_ID": run_id,
             "ProductCode": "B2", "CampaignTag": tag, "CampaignPrefix": f"B2.{tag}."}]


def test_scope_filter_excludes_other_tags_and_only_keeps_joined_intents():
    scope = {"ProductCode": "B2", "CampaignTag": "M", "CampaignPrefix": "B2.M."}
    tables = {
        "campaign": [{"CampaignId": "c1", "CampaignName": "B2.M.SP-COR-EXA-01"}, {"CampaignId": "c2", "CampaignName": "B2.T.SP-COR-EXA-01"}],
        "target": [{"CampaignId": "c1", "CampaignName": "B2.M.SP-COR-EXA-01", "IntentCode": "I1"}, {"CampaignId": "c2", "CampaignName": "B2.T.SP-COR-EXA-01", "IntentCode": "I2"}],
        "search_term": [{"CampaignId": "c2", "CampaignName": "B2.T.SP-COR-EXA-01", "TargetId": "t2"}],
        "intent": [{"IntentCode": "I1"}, {"IntentCode": "I2"}],
    }
    scoped, issues = mod.filter_facts_to_campaign_scope(tables, scope)
    assert [row["CampaignId"] for row in scoped["campaign"]] == ["c1"]
    assert [row["IntentCode"] for row in scoped["intent"]] == ["I1"]
    assert not scoped["search_term"]
    assert issues == ["SCOPE_CONTAMINATION"]


def test_exact_schemas_mandatory_reasons_and_coverage():
    tables = _tables()
    expected = {"intent": [("I01",)], "campaign": [("C1",)], "target": [("T1",)], "search_term": [("irrelevant query", "T1")]}
    assert mod.validate_decision_tables(tables, expected_objects=expected) == {"intent": 1, "campaign": 1, "target": 1, "search_term": 1}
    tables["target"][0]["决策原因"] = ""
    try:
        mod.validate_decision_tables(tables)
    except mod.DecisionPackageError as exc:
        assert str(exc) == "DECISION_REASON_MISSING"
    else:
        raise AssertionError("empty rationale must fail")


def test_candidate_numeric_changes_require_current_and_proposed_values():
    tables = _tables()
    tables["target"][0].update({"决策成熟度": "可决策", "决策结果": "降低竞价", "建议Bid": "1.05", "决策原因": "近14日数据支持降低竞价，证据窗口为14日。"})
    mod.validate_decision_tables(tables)
    tables["target"][0]["当前Bid"] = ""
    try:
        mod.validate_decision_tables(tables)
    except mod.DecisionPackageError as exc:
        assert str(exc) == "PROPOSED_VALUE_MISSING"
    else:
        raise AssertionError("current value must be present")


def test_intent_target_mode_conflict_fails_closed():
    tables = _tables()
    tables["intent"][0].update({"决策成熟度": "可决策", "决策结果": "升级独立", "目标控制方式": "独立", "决策原因": "近30日稳定成交支持独立控制，依据窗口为近30日。"})
    tables["target"][0]["目标控制方式"] = "共享"
    try:
        mod.validate_decision_tables(tables)
    except mod.DecisionPackageError as exc:
        assert str(exc) == "DECISION_CONFLICT"
    else:
        raise AssertionError("cross-layer destination conflict must fail")


def test_synthetic_maturity_cases_do_not_use_fixed_day_or_click_thresholds():
    tables = _tables()
    target = tables["target"][0]
    # A: short evidence; B: longer elapsed time but still only a few clicks.
    for reason in ("近3日仅5次点击、0订单，样本不足。", "近14日仅6次点击、0订单，不能仅凭经过时间判成熟。"):
        target.update({"决策成熟度": "继续观察", "决策结果": "继续观察", "决策原因": reason})
        mod.validate_decision_tables(tables)
    # C: dense, stable short-window evidence can be decision-ready.
    target.update({"决策成熟度": "可决策", "决策结果": "保持", "决策原因": "近3日120次点击、15单，当前保持有充分证据。"})
    mod.validate_decision_tables(tables)
    # D: a recent Bid change is an observation confounder unless urgent.
    target.update({"决策成熟度": "继续观察", "决策结果": "继续观察", "决策原因": "近3日Bid修改仅2天，当前窗口尚不足以评价修改效果。"})
    mod.validate_decision_tables(tables)


def test_intent_upgrade_and_target_migration_share_one_desired_state():
    tables = _tables()
    tables["intent"][0].update({
        "决策成熟度": "可决策", "决策结果": "升级独立", "目标控制方式": "独立",
        "决策原因": "近30日重复成交且跨多个Search Term稳定，建议独立控制。",
    })
    tables["target"][0].update({
        "决策成熟度": "可决策", "决策结果": "迁移候选", "目标控制方式": "独立",
        "决策原因": "近30日稳定成交支持该Target迁移到独立控制。",
    })
    mod.validate_decision_tables(tables)


def test_reason_must_name_actual_window_or_immediate_anomaly():
    tables = _tables()
    tables["campaign"][0]["决策原因"] = "当前情况正常，所以保持。"
    try:
        mod.validate_decision_tables(tables)
    except mod.DecisionPackageError as exc:
        assert str(exc) == "DECISION_REASON_MISSING"
    else:
        raise AssertionError("rationale without an actual evidence window must fail")


def test_dated_windows_recompute_ratios_and_keep_source_window_separate():
    rows = [
        {"Date": "2026-09-14", "DataCompleteness": "COMPLETE_DAY", "CampaignId": "C1", "Clicks": "40", "Impressions": "500", "Spend": "40", "Orders": "4", "Sales": "100", "DailyBudget": "30"},
        {"Date": "2026-09-13", "DataCompleteness": "COMPLETE_DAY", "CampaignId": "C1", "Clicks": "30", "Impressions": "400", "Spend": "30", "Orders": "3", "Sales": "75", "DailyBudget": "30"},
        {"Date": "2026-09-12", "DataCompleteness": "TODAY_PARTIAL", "CampaignId": "C1", "Clicks": "500", "Impressions": "900", "Spend": "500", "Orders": "0", "Sales": "0", "DailyBudget": "30"},
        {"Date": "", "DataCompleteness": "SOURCE_WINDOW", "CampaignId": "C1", "Clicks": "999", "Spend": "999", "Orders": "999", "Sales": "999"},
    ]
    context = mod.aggregate_windows(rows, "campaign", "2026-09-14")["C1"]
    assert context["3D"]["Clicks"] == "70"
    assert context["3D"]["ACoS"] == "0.4"
    assert context["3D"]["observed_days"] == 2
    assert len(context["source_window_rows"]) == 1


def test_full_success_run_package_embeds_same_csv_rows_and_history(tmp_path):
    from datetime import datetime
    tables = _tables()
    expected = {"intent": [("I01",)], "campaign": [("C1",)], "target": [("T1",)], "search_term": [("irrelevant query", "T1")]}
    written = mod.write_decision_package(
        tmp_path, "B2", tables, campaign_tag="M", expected_objects=expected,
        inputs=_scope_inputs(),
        now=datetime(2026, 9, 16, 13, 5, 7, tzinfo=timezone.utc),
    )
    assert written["status"] == "DECISION_PACKAGE_WRITTEN"
    for kind, path in written["files"].items():
        if kind in mod.SCHEMAS:
            assert Path(path).read_bytes().startswith(b"\xef\xbb\xbf")
    html_text = Path(written["files"]["html"]).read_text(encoding="utf-8")
    start = html_text.index('<script id="decision-payload" type="application/json">') + len('<script id="decision-payload" type="application/json">')
    end = html_text.index("</script>", start)
    payload = json.loads(html_text[start:end])
    assert payload["tables"] == tables
    assert written["metadata"]["RUN_TIMESTAMP"] in written["files"]["html"]
    history = mod.load_decision_history(tmp_path, "B2", "M")
    assert history["status"] == "DECISION_HISTORY_RESOLVED"
    assert len(history["records"]["target"]) == 1


def test_history_missing_is_nonblocking(tmp_path):
    assert mod.load_decision_history(tmp_path, "B2")["status"] == "DECISION_HISTORY_UNAVAILABLE"


def test_second_run_html_contains_only_prior_complete_decision_history(tmp_path):
    from datetime import datetime
    expected = {"intent": [("I01",)], "campaign": [("C1",)], "target": [("T1",)], "search_term": [("irrelevant query", "T1")]}
    first = mod.write_decision_package(
        tmp_path, "B2", _tables(), campaign_tag="M", expected_objects=expected, inputs=_scope_inputs(),
        now=datetime(2026, 9, 16, 13, 5, 7, tzinfo=timezone.utc),
    )
    second = mod.write_decision_package(
        tmp_path, "B2", _tables(), campaign_tag="M", expected_objects=expected, inputs=_scope_inputs(),
        now=datetime(2026, 9, 16, 13, 6, 7, tzinfo=timezone.utc),
    )
    assert second["metadata"]["Decision_History_Status"] == "DECISION_HISTORY_RESOLVED"
    assert second["metadata"]["Decision_History_Package_Count"] == 1
    html_text = Path(second["files"]["html"]).read_text(encoding="utf-8")
    start = html_text.index('<script id="decision-payload" type="application/json">') + len('<script id="decision-payload" type="application/json">')
    end = html_text.index("</script>", start)
    payload = json.loads(html_text[start:end])
    assert len(payload["decision_history"]) == 4
    assert {row["RUN_ID"] for row in payload["decision_history"]} == {first["run_id"]}
    assert "irrelevant query × T1" in html_text


def test_incomplete_historical_package_is_ignored(tmp_path):
    from datetime import datetime
    expected = {"intent": [("I01",)], "campaign": [("C1",)], "target": [("T1",)], "search_term": [("irrelevant query", "T1")]}
    first = mod.write_decision_package(
        tmp_path, "B2", _tables(), campaign_tag="M", expected_objects=expected, inputs=_scope_inputs(),
        now=datetime(2026, 9, 16, 13, 5, 7, tzinfo=timezone.utc),
    )
    Path(first["files"]["html"]).unlink()
    history = mod.load_decision_history(tmp_path, "B2", "M")
    assert history["status"] == "DECISION_HISTORY_UNAVAILABLE"
    assert history["records"]["target"] == []
