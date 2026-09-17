import sys
from pathlib import Path

SCRIPTS = Path(r"C:\Users\qmhzp\.codex\skills\hzp-amz-6-1-new-product-advertising-battle-plan\scripts")
sys.path.insert(0, str(SCRIPTS))
import battle_plan as bp  # noqa: E402


def _fixture():
    tables = {"battle": [{
        "作战单元ID": "u1", "Id": "1", "精准泛词": "sister gifts", "意图代码": "SG",
        "作战任务": "首攻", "控制方式": "独立", "计划阶段": "PHASE_1",
        "投放方式": "EXACT", "目标类型": "KEYWORD", "目标值": "sister gifts", "作战目的": "验证核心意图",
    }]}
    architecture = {
        "campaigns": [{"Campaign Name": "B2.M.SP-COR-EXA-SG-01", "campaign_key": "独立-COR-EXA-SG",
                        "Technical Role": "COR-EXA", "广告类型": "SP", "source_ids": ["1"]}],
        "ad_groups": [{"Campaign Name": "B2.M.SP-COR-EXA-SG-01", "Ad Group Name": "B2.M.COR-01"}],
    }
    return tables, architecture


def test_blueprint_has_all_creation_fields_and_blocks_missing_values():
    tables, architecture = _fixture()
    rows = bp.creation_blueprint(tables, architecture, {"keywords": [{"Id": "1"}]})
    assert tuple(rows[0]) == bp.CREATION_COLUMNS
    assert rows[0]["Target Type"] == "KEYWORD"
    assert rows[0]["Target Value"] == "sister gifts"
    assert rows[0]["Parameter Status"] == "EXECUTION_NOT_READY"
    assert rows[0]["Daily Budget"] == "DATA_NOT_AVAILABLE"


def test_blueprint_uses_explicit_campaign_and_target_parameters_without_guessing():
    tables, architecture = _fixture()
    decisions = {
        "keywords": [{"Id": "1", "Campaign Status": "ENABLED", "Daily Budget": "20",
                       "Bidding Strategy": "DYNAMIC_DOWN_ONLY", "Top of Search": "50%",
                       "Rest of Search": "0%", "Product Pages": "0%", "Ad Group Default Bid": "1.20",
                       "Target Bid": "1.20", "Target Status": "ENABLED", "Advertised Own ASIN": "B0OWN", "Advertised SKU": "SKU1",
                       "Advertised Product Status": "ENABLED", "Ad Group Status": "ENABLED",
                       "Marketplace": "US", "SellerSpace Store": "Q2-US", "Portfolio Name": "B2",
                       "Portfolio ID": "P1", "Parameter Evidence": "approved economics"}],
        "campaign_parameters": {"独立-COR-EXA-SG": {"Initial Negative Targets": "NONE_SPECIFIED"}},
    }
    row = bp.creation_blueprint(tables, architecture, decisions)[0]
    assert row["Parameter Status"] == "READY_FOR_6_1"
    assert row["Bidding Strategy"] == "DYNAMIC_DOWN_ONLY"
    assert row["Top of Search"] == "50%"
    assert row["Advertised Own ASIN"] == "B0OWN"
