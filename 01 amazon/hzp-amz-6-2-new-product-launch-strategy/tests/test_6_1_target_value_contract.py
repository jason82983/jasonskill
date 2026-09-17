"""Regression checks for the 6-1 B target type/value handoff."""

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from scripts.advertising_state_reconciler import _target_value  # noqa: E402
from scripts.new_product_battle_plan_contract import (  # noqa: E402
    BATTLE_MULTI_COLUMNS, BATTLE_SINGLE_COLUMNS, MAPPING_MULTI_COLUMNS, MAPPING_SINGLE_COLUMNS,
    _battle_target_validator,
)

spec = importlib.util.spec_from_file_location(
    "battle_plan",
    SKILLS_ROOT / "hzp-amz-6-1-new-product-advertising-battle-plan" / "scripts" / "battle_plan.py",
)
battle_plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(battle_plan)


def _bundle(multi=False):
    summary_row = {
        "精准泛词": "sister gifts", "中文": "姐妹礼物", "层级": "Child", "父精准泛词": "",
        "直接搜索量": "100", "汇总搜索量": "100", "平均竞品数": "20", "意图机会比": "5", "直接对应词数": "1",
    }
    mapping_row = {
        "Id": "k1", "词": "sister gifts", "中文": "姐妹礼物", "市场容量": "10000",
        "竞争产品数": "20", "供需比": "500", "自然排名": "5", "精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物",
    }
    if multi:
        mapping_row.update({"对标覆盖数": "2", "最佳自然排名": "5", "自然排名中位数": "10",
                            "精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物"})
    return {"summary": {"rows": [summary_row]}, "mapping": {"rows": [mapping_row]},
            "mapping_schema": MAPPING_MULTI_COLUMNS if multi else MAPPING_SINGLE_COLUMNS}


def _decisions(method="ASIN", target_type="ASIN", target_value="B0TARGET"):
    return {
        "intents": [{"精准泛词": "sister gifts", "作战任务": "首攻", "作战优先级": "P1",
                      "作战方向": "先验证场景词", "控制方式": "共享", "控制原因": "预算集中",
                      "决策原因": "产品匹配"}],
        "keywords": [{"Id": "k1", "精准泛词": "sister gifts", "作战任务": "首攻", "当前状态": "首攻",
                       "新品期是否投放": "是", "计划阶段": "PHASE_1", "计划投放方式": method,
                       "作战目的": "验证竞品定向", "目标类型": target_type, "目标值": target_value}],
    }


def test_6_1_b_emits_explicit_target_facts_for_asin(tmp_path):
    tables = battle_plan.build_tables(_bundle(), _decisions(), product_code="B2", registry_path=tmp_path / "registry.json")
    assert set(tables["battle"][0]) == set(BATTLE_SINGLE_COLUMNS)
    assert tables["battle"][0]["目标类型"] == "ASIN"
    assert tables["battle"][0]["目标值"] == "B0TARGET"


def test_6_1_multi_b_emits_the_same_target_contract(tmp_path):
    tables = battle_plan.build_tables(_bundle(multi=True), _decisions(), product_code="B2", registry_path=tmp_path / "registry.json")
    assert set(tables["battle"][0]) == set(BATTLE_MULTI_COLUMNS)
    assert (tables["battle"][0]["目标类型"], tables["battle"][0]["目标值"]) == ("ASIN", "B0TARGET")


def test_6_1_b_rejects_missing_non_keyword_target(tmp_path):
    with pytest.raises(ValueError, match="BATTLE_TARGET_VALUE_MISSING"):
        battle_plan.build_tables(_bundle(), _decisions(target_value=""), product_code="B2", registry_path=tmp_path / "registry.json")


@pytest.mark.parametrize(("method", "target_type", "target_value"), [
    ("PT", "PRODUCT", "B0PRODUCT"),
    ("CATEGORY", "CATEGORY", "apparel"),
])
def test_6_1_b_supports_product_and_category_targets(tmp_path, method, target_type, target_value):
    tables = battle_plan.build_tables(
        _bundle(), _decisions(method, target_type, target_value), product_code="B2", registry_path=tmp_path / f"{method}.json"
    )
    assert (tables["battle"][0]["目标类型"], tables["battle"][0]["目标值"]) == (target_type, target_value)
    preview = battle_plan.architecture_preview(tables, "B2", "M")
    assert preview["campaigns"][0]["投放方式"] == method


def test_resolver_and_61_preserve_target_type_and_value():
    row = {"投放方式": "ASIN", "目标类型": "ASIN", "目标值": "B0TARGET", "词": "sister gifts"}
    assert _battle_target_validator(Path("unused.csv"), [row], None) is None
    assert _target_value(row, "ASIN", {}) == ("ASIN", "B0TARGET")
    with pytest.raises(ValueError, match="TECHNICAL_EXECUTION_CONFLICT"):
        _target_value({**row, "目标类型": "CATEGORY"}, "ASIN", {})


def test_keyword_b_target_is_explicit_keyword():
    row = {"投放方式": "EXACT", "目标类型": "KEYWORD", "目标值": "sister gifts", "词": "sister gifts"}
    assert _battle_target_validator(Path("unused.csv"), [row], None) is None

