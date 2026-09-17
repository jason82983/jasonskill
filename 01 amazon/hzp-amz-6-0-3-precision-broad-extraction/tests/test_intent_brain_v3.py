import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("broad_v3", ROOT / "scripts" / "broad_seed_cluster.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(record_id, keyword, volume):
    return {"Id": record_id, "词": keyword, "中文": "", "市场容量": str(volume),
            "竞争产品数": "10", "供需比": "1", "最佳自然排名": "1", "精准度": "高度精准"}


def test_internal_intent_brain_reconciles_synonyms_and_keeps_relationships_separate():
    mapped = module.build_mapping_rows([
        row("1", "sister birthday gifts", 100),
        row("2", "birthday gifts for sister", 200),
        row("3", "best friend gifts", 300),
    ])
    assert mapped[0]["PrimaryIntentCode"] == mapped[1]["PrimaryIntentCode"]
    assert mapped[0]["PrimaryIntentCode"] != mapped[2]["PrimaryIntentCode"]
    assert len({item["PrimaryIntentId"] for item in mapped}) == 2


def test_internal_intent_brain_builds_parent_child_and_reconciles_volume():
    mapped = module.build_mapping_rows([
        row("1", "sister gifts", 100),
        row("2", "sister birthday gifts", 200),
    ])
    summary = module.aggregate_mapping_rows(mapped)
    parent = next(item for item in summary if item["精准泛词"] == "sister gifts")
    child = next(item for item in summary if item["精准泛词"] == "sister birthday gifts")
    assert parent["汇总搜索量"] == 300
    assert child["汇总搜索量"] == 200
    assert parent["IntentCode"] and child["IntentCode"]


def test_intent_brain_output_contains_trace_fields_without_market_math_from_ai():
    mapped = module.build_mapping_rows([row("1", "sister gifts", 100)])
    assert mapped[0]["IntentAssignmentReason"]
    assert mapped[0]["ChallengeResult"] == "CONFIRMED"
    summary = module.aggregate_mapping_rows(mapped)[0]
    assert summary["直接搜索量"] == 100
    assert summary["平均竞品数"] == 10
    assert summary["意图机会比"] == 10


def test_v3_mapping_has_parent_identity_and_stable_intent_identity():
    mapped = module.build_mapping_rows([
        row("1", "sister gifts", 100),
        row("2", "sister birthday gifts", 200),
    ])
    assert "ParentIntentId" in mapped[1]
    assert mapped[1]["ParentIntentId"]
    assert mapped[0]["PrimaryIntentId"] == module._stable_intent_identity("sister gifts")[0]
    assert mapped[0]["PrimaryIntentCode"] == module._stable_intent_identity("sister gifts")[1]


def test_v3_adaptive_batches_are_prompt_size_based():
    units = [{"Id": str(i), "Keyword": "x" * 100} for i in range(30)]
    batches = module.adaptive_semantic_batches(units, target_chars=800)
    assert len(batches) > 1
    assert sum(len(batch) for batch in batches) == len(units)


def test_v3_profile_missing_is_explicit(tmp_path):
    profile = module.load_current_product_profile(tmp_path)
    assert profile["status"] == "PRODUCT_PROFILE_NOT_FOUND"
    assert profile["text"] == ""
