from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from ad_facts_package import (  # noqa: E402
    CAMPAIGN_SCHEMA, INTENT_SCHEMA, OUTPUTS, SEARCH_SCHEMA, TARGET_SCHEMA,
    PackageError, _derive_metrics, build_fact_tables, create_run_package,
    default_stable_cutoff_date, map_provider_rows, resolve_latest_valid_62_package,
    select_runtime_campaign_scope,
)


def _event(kind, logical, amazon, **extra):
    return {"event": "ENTITY_IDENTITY_VERIFIED", "entity_type": kind,
            "logical_id": logical, "amazon_id": amazon, **extra}


def _shared_fixture(day):
    campaign = {"Date": day, "DataCompleteness": "COMPLETE_DAY", "CampaignId": "c1",
                "CampaignName": "shared campaign", "Spend": 90, "Sales": 180,
                "Orders": 9, "Clicks": 90, "Impressions": 900}
    targets = []
    terms = []
    events = [_event("campaign", "campaign:shared", "c1", control_mode="共享"),
              _event("ad_group", "group:1", "g1", parent_logical_id="campaign:shared", parent_amazon_id="c1")]
    units = []
    for i in range(1, 4):
        target_id, unit_id = f"t{i}", f"BU-{i}"
        targets.append({"Date": day, "DataCompleteness": "COMPLETE_DAY", "TargetId": target_id,
                        "CampaignId": "c1", "AdGroupId": "g1", "Impressions": 100,
                        "Clicks": 10, "Spend": 10, "Orders": 1, "Sales": 20})
        terms.append({"Date": day, "DataCompleteness": "COMPLETE_DAY", "SearchTerm": f"term {i}",
                      "CampaignId": "c1", "AdGroupId": "g1", "TargetId": target_id,
                      "Impressions": 20, "Clicks": 2, "Spend": 2, "Orders": 1, "Sales": 20})
        events.append(_event("target", f"target:{unit_id}", target_id, battle_unit_id=unit_id,
                             parent_logical_id="group:1", parent_amazon_id="g1",
                             control_mode="共享", target_type="KEYWORD", target_value=f"keyword {i}",
                             match_type="PHRASE"))
        units.append({"作战单元ID": unit_id, "意图代码": f"I{i}", "精准泛词": f"intent {i}",
                      "控制方式": "共享"})
    return campaign, targets, terms, events, units


def test_shared_campaign_metrics_are_not_duplicated_across_intents():
    day = (date.today() - timedelta(days=1)).isoformat()
    campaign, targets, terms, events, units = _shared_fixture(day)
    tables, result = build_fact_tables([campaign], targets, terms, identity_events=events,
                                       battle_units=units, metric_tolerance=0.0001)
    assert result["Run_Status"] == "FULL_SUCCESS"
    assert len(tables["campaign"]) == 1
    assert sum(row["Spend"] for row in tables["intent"]) == 30
    assert [row["Spend"] for row in tables["intent"]] == [10, 10, 10]
    assert all(row["IntentCode"] != "UNMAPPED" for row in tables["target"] + tables["search_term"])


def test_target_and_search_term_remain_distinct_and_search_terms_join_by_target_id():
    day = (date.today() - timedelta(days=1)).isoformat()
    campaign, targets, terms, events, units = _shared_fixture(day)
    terms.append({**terms[0], "SearchTerm": "second actual query"})
    tables, result = build_fact_tables([campaign], targets, terms, identity_events=events,
                                       battle_units=units, metric_tolerance=0.0001)
    assert len(tables["target"]) == 3
    assert len(tables["search_term"]) == 4
    assert {row["TargetId"] for row in tables["search_term"]} == {row["TargetId"] for row in targets}
    assert tables["search_term"][0]["SearchTerm"] != tables["target"][0]["TargetValue"]
    assert result["SearchTermRecordCount"] == 4


def test_daily_mapping_and_window_mapping_never_fabricate_dates():
    today = date.today().isoformat()
    daily = map_provider_rows([{"date_key": today, "impr": 1}], {"Impressions": "impr"},
                              source_grain="DAY", date_field="date_key")
    window = map_provider_rows([{"impr": 7}], {"Impressions": "impr"}, source_grain="WINDOW")
    assert daily[0]["Date"] == today and daily[0]["DataCompleteness"] == "TODAY_PARTIAL"
    assert window[0]["Date"] is None and window[0]["DataCompleteness"] == "SOURCE_WINDOW"


def test_today_partial_is_marked_and_separate_from_complete_days():
    now = date.today().isoformat()
    mapped = map_provider_rows([{"d": now, "clicks": 2}, {"d": (date.today()-timedelta(days=1)).isoformat(), "clicks": 3}],
                               {"Clicks": "clicks"}, source_grain="DAY", date_field="d")
    assert [row["DataCompleteness"] for row in mapped] == ["TODAY_PARTIAL", "COMPLETE_DAY"]


def test_zero_denominators_return_null_without_infinity():
    issues = []
    result = _derive_metrics({"Clicks": 0, "Impressions": 0, "Spend": 0, "Orders": 0, "Sales": 0}, None, issues)
    assert all(result[key] is None for key in ("CTR", "CPC", "CVR", "ACoS", "ROAS"))
    assert not issues


def test_unknown_raw_metric_tolerance_is_disclosed_and_mismatch_is_not_full_success():
    issues = []
    _derive_metrics({"Clicks": 1, "Impressions": 10, "CTR": 0.2}, None, issues)
    assert "METRIC_RECONCILIATION_TOLERANCE_UNRESOLVED" in issues
    issues = []
    _derive_metrics({"Clicks": 1, "Impressions": 10, "CTR": 0.2}, 0.001, issues)
    assert "METRIC_RECONCILIATION_MISMATCH" in issues


def test_unresolvable_target_lineage_is_retained_as_unmapped():
    day = (date.today() - timedelta(days=1)).isoformat()
    target = {"Date": day, "DataCompleteness": "COMPLETE_DAY", "TargetId": "orphan", "Spend": 2}
    tables, result = build_fact_tables([], [target], [], identity_events=[], battle_units=[],
                                       metric_tolerance=None)
    assert tables["target"][0]["IntentCode"] == "UNMAPPED"
    assert tables["target"][0]["控制方式"] == "UNMAPPED"
    assert "INTENT_ATTRIBUTION_UNRESOLVED" in result["Issues"]
    assert result["Run_Status"] == "PARTIAL_SUCCESS"


def test_search_term_without_target_id_is_retained_and_flagged_unsupported():
    day = (date.today() - timedelta(days=1)).isoformat()
    term = {"Date": day, "DataCompleteness": "COMPLETE_DAY", "SearchTerm": "actual query", "Clicks": 1}
    tables, result = build_fact_tables([], [], [term], identity_events=[], battle_units=[], metric_tolerance=None)
    assert tables["search_term"][0]["SearchTerm"] == "actual query"
    assert tables["search_term"][0]["IntentCode"] == "UNMAPPED"
    assert "SEARCH_TERM_GRAIN_UNSUPPORTED" in result["Issues"]
    assert "INTENT_ATTRIBUTION_UNRESOLVED" in result["Issues"]


def test_search_term_cannot_cross_attribution_to_a_different_campaign():
    day = (date.today() - timedelta(days=1)).isoformat()
    campaign, targets, terms, events, units = _shared_fixture(day)
    terms[0]["CampaignId"] = "wrong-campaign"
    tables, result = build_fact_tables([campaign], targets, terms, identity_events=events,
                                       battle_units=units, metric_tolerance=0.0001)
    assert tables["search_term"][0]["IntentCode"] == "UNMAPPED"
    assert "INTENT_ATTRIBUTION_UNRESOLVED" in result["Issues"]


def test_converting_search_term_count_is_null_when_order_semantics_are_missing():
    day = (date.today() - timedelta(days=1)).isoformat()
    campaign, targets, terms, events, units = _shared_fixture(day)
    for term in terms:
        term.pop("Orders", None)
    tables, _ = build_fact_tables([campaign], targets, terms, identity_events=events,
                                  battle_units=units, metric_tolerance=0.0001)
    assert all(row["ConvertingSearchTermCount"] is None for row in tables["intent"])


def test_exact_csv_schemas_and_package_latest_validation(tmp_path):
    day = (date.today() - timedelta(days=1)).isoformat()
    rows = {
        "campaign": [{"Date": day, "DataCompleteness": "COMPLETE_DAY", "CampaignId": "c1", "CampaignName": "B2.M.SP-COR-EXA-01", "Spend": 4, "Sales": 8, "Orders": 1, "Impressions": 10, "Clicks": 2, "CTR": .2, "CPC": 2, "CVR": .5, "ACoS": .5, "ROAS": 2}],
        "intent": [{"Date": day, "DataCompleteness": "COMPLETE_DAY", "IntentCode": "I1", "Spend": 4, "Sales": 8, "Orders": 1, "Impressions": 10, "Clicks": 2, "CTR": .2, "CPC": 2, "CVR": .5, "ACoS": .5, "ROAS": 2}],
        "target": [{"Date": day, "DataCompleteness": "COMPLETE_DAY", "TargetId": "t1", "Spend": 4}],
        "search_term": [{"Date": day, "DataCompleteness": "COMPLETE_DAY", "SearchTerm": "query", "TargetId": "t1", "Spend": 4}],
    }
    result = {"Run_Status": "FULL_SUCCESS", "CampaignRecordCount": 1, "IntentRecordCount": 1,
              "TargetRecordCount": 1, "SearchTermRecordCount": 1}
    output = create_run_package(tmp_path, "B2", {"ProductName": "synthetic", "Marketplace": "US"},
                                rows, result, data_source="MOCK", query_time="synthetic",
                                data_start_date=day, data_end_date=day, stable_cutoff_date=day,
                                today_partial_included=False, source_grain_by_layer={k: "DAY" for k in OUTPUTS},
                                attribution_refresh_days=None,
                                campaign_scope={"ProductCode": "B2", "CampaignTag": "M", "CampaignPrefix": "B2.M."},
                                scope_coverage={"ProductCode": "B2", "CampaignTag": "M", "CampaignPrefix": "B2.M.", "AccountCampaignCount": 3, "PrefixMatchedCampaignCount": 1, "ExcludedCampaignCount": 2, "MatchedCampaignIds": ["c1"]},
                                now=datetime(2026, 9, 15, 12, tzinfo=timezone.utc))
    assert len(list(Path(output["directory"]).glob("*.csv"))) == 4
    assert len(list(Path(output["directory"]).glob("*.html"))) == 1
    html = Path(output["files"]["html"]).read_text(encoding="utf-8")
    assert 'id="fact-payload"' in html and "fetch(" not in html
    inline_scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    assert len(inline_scripts) == 1
    js = tmp_path / "inline.js"
    js.write_text(inline_scripts[0], encoding="utf-8")
    checked = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    package = resolve_latest_valid_62_package(tmp_path, "B2", "M")
    assert package["status"] == "LATEST_VALID_62_PACKAGE_RESOLVED"
    assert set(package["tables"]) == set(OUTPUTS)
    assert package["metadata"]["AttributionRefreshStatus"] == "UNRESOLVED"
    assert package["metadata"]["CampaignPrefix"] == "B2.M."
    assert resolve_latest_valid_62_package(tmp_path, "B2", "T")["status"] == "RUNTIME_SCOPE_MISMATCH"
    with pytest.raises(PackageError, match="62_RUN_PACKAGE_INCOMPLETE"):
        create_run_package(tmp_path, "B2", {}, {"campaign": []}, result, data_source="MOCK",
                           query_time="q", data_start_date=None, data_end_date=None,
                           stable_cutoff_date=day, today_partial_included=False,
                           source_grain_by_layer={}, attribution_refresh_days=None)


def test_default_cutoff_is_yesterday():
    assert default_stable_cutoff_date(date(2026, 9, 16)) == date(2026, 9, 15)


def test_every_schema_contains_explicit_current_day_marker():
    assert CAMPAIGN_SCHEMA[1] == INTENT_SCHEMA[1] == TARGET_SCHEMA[1] == SEARCH_SCHEMA[1] == "DataCompleteness"


def test_scope_prefix_has_trailing_dot_and_excludes_near_matches():
    matched, coverage = select_runtime_campaign_scope([
        {"CampaignId": "1", "CampaignName": "B2.M.SP-COR-EXA-01"},
        {"CampaignId": "2", "CampaignName": "B2.M.SP-EXP-PHR-01"},
        {"CampaignId": "3", "CampaignName": "B2.M2.SP-COR-EXA-01"},
        {"CampaignId": "4", "CampaignName": "B2.MANUAL.SP-COR-EXA-01"},
        {"CampaignId": "5", "CampaignName": "Manual-B2"},
    ], "B2", "M")
    assert [row["CampaignId"] for row in matched] == ["1", "2"]
    assert coverage == {"ProductCode": "B2", "CampaignTag": "M", "CampaignPrefix": "B2.M.", "AccountCampaignCount": 5, "PrefixMatchedCampaignCount": 2, "ExcludedCampaignCount": 3, "MatchedCampaignIds": ["1", "2"]}


@pytest.mark.parametrize("tag,expected", [("", "CAMPAIGN_TAG_MISSING"), ("M-1", "CAMPAIGN_TAG_INVALID")])
def test_invalid_campaign_tag_fails_closed(tag, expected):
    with pytest.raises(PackageError, match=expected):
        select_runtime_campaign_scope([], "B2", tag)
