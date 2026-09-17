from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kernel", ROOT / "scripts" / "dual_precision_csv.py")
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)


def b2_profile():
    return {
        "Core_Product_Type": "sister friendship resin keepsake figurine",
        "Recipient": "sister friendship",
        "Relationship_Intent": "sister friendship",
        "Purchase_Occasions": ["birthday", "gift giving"],
        "Compatible_Search_Intents": ["sister gifts", "sister birthday gifts", "friendship gifts"],
        "Core_Attributes": ["two sisters resin sculpture", "white moon keepsake"],
        "Hard_Intent_Conflicts": ["not personalized"],
    }


def decide(keyword):
    return kernel.evaluate_product_search_intent_fit(
        b2_profile(), {"Core_Intent": keyword}, keyword=keyword
    )


def test_gift_led_and_product_led_calibration_boundary():
    assert decide("sister birthday gifts")["AI_Classification"] == "PRECISION"
    assert decide("gift for sister")["AI_Classification"] == "PRECISION"
    assert decide("best friend gifts for women")["AI_Classification"] == "PRECISION"
    assert decide("friendship gifts for women")["AI_Classification"] == "PRECISION"
    assert decide("sister")["AI_Classification"] == "PRECISION"
    assert decide("sister figurine")["AI_Classification"] == "PRECISION"
    assert decide("birthday gifts for women")["Product_Intent_Fit"] == "CAN_SERVE"
    assert decide("gift for women")["Product_Intent_Fit"] == "CAN_SERVE"
    assert decide("gift")["AI_Classification"] == "NOT_PRECISION"


def test_hard_modifiers_veto_core_fit():
    for keyword in ("3 sisters figurine", "4 sisters figurine", "5 sisters figurine", "wooden sisters figurine", "sister birthday card", "personalized gifts for women"):
        assert decide(keyword)["AI_Classification"] == "NOT_PRECISION"


def test_purchase_driver_and_gift_mission_evidence_are_adaptive():
    high = decide("sister birthday gifts")
    broad = decide("birthday gifts for women")
    relation_only = decide("sister")
    assert high["PrimaryPurchaseDriver"] == "GIFT_EMOTIONAL"
    assert high["GiftMissionFit"] == "HIGH"
    assert high["PurchaseMissionConvergence"] == "HIGH"
    assert high["PhysicalProductConvergence"] != "HIGH"
    assert high["FinalPrecision"] == "高度精准"
    assert broad["FinalPrecision"] == "弱精准"
    assert relation_only["FinalPrecision"] == "精准"


def test_golden_regression_detects_compression_and_broad_gift_overreach():
    cases = [
        {"Keyword": "sister birthday gifts", "ExpectedPrecision": "高度精准", "CaseType": "GIFT_HIGH_MISSION_FIT"},
        {"Keyword": "friendship gifts for women", "ExpectedPrecision": "高度精准", "CaseType": "GIFT_HIGH_MISSION_FIT"},
        {"Keyword": "birthday gifts for women", "ExpectedPrecision": "弱精准", "CaseType": "GIFT_BROAD_INTENT"},
        {"Keyword": "sister", "ExpectedPrecision": "精准", "CaseType": "GIFT_RELATIONSHIP_ONLY"},
    ]
    metrics = kernel.run_precision_brain_regression(b2_profile(), cases)
    assert metrics["ExactPrecisionMatch"] == 4
    assert metrics["MismatchCount"] == 0
    assert metrics["HighPrecisionRecall"] == 1.0
    assert metrics["GiftHighMissionFitRecall"] == 1.0
    assert metrics["GradeCompression"] == []


def test_regression_resolves_product_driver_once_per_run(monkeypatch):
    calls = []
    original = kernel.build_product_purchase_driver

    def counted(profile):
        calls.append(profile)
        return original(profile)

    monkeypatch.setattr(kernel, "build_product_purchase_driver", counted)
    kernel.run_precision_brain_regression(
        b2_profile(),
        [{"Keyword": "sister birthday gifts", "ExpectedPrecision": "高度精准", "CaseType": "GIFT_HIGH_MISSION_FIT"},
         {"Keyword": "birthday gifts for women", "ExpectedPrecision": "弱精准", "CaseType": "GIFT_BROAD_INTENT"}],
    )
    assert len(calls) == 1


def test_functional_driver_does_not_use_gift_mission_as_core_fit():
    profile = {
        "PrimaryPurchaseDriver": "FUNCTIONAL",
        "Core_Product_Type": "wireless phone charger",
        "Core_Functions": ["charge mobile phones"],
        "Recipient": "sister",
    }
    result = kernel.evaluate_product_search_intent_fit(
        profile, {"Core_Intent": "gift for sister"}, keyword="gift for sister"
    )
    assert result["PrimaryPurchaseDriver"] == "FUNCTIONAL"
    assert result["GiftMissionFit"] == "NOT_SPECIFIED"
    assert result["AI_Classification"] != "PRECISION"


def test_hybrid_primary_match_is_not_penalized_by_unexpressed_secondary_driver():
    profile = {
        "PrimaryPurchaseDriver": "HYBRID",
        "SecondaryPurchaseDrivers": ["GIFT_EMOTIONAL"],
        "Core_Product_Type": "furniture anti-tip anchor",
        "Core_Functions": ["anchor furniture to wall"],
        "Compatible_Search_Intents": ["furniture anchor"],
    }
    result = kernel.evaluate_product_search_intent_fit(
        profile, {"Core_Intent": "furniture anchor"}, keyword="furniture anchor"
    )
    assert result["AI_Classification"] == "PRECISION"
    assert result["GiftMissionFit"] == "NOT_SPECIFIED"
    assert result["FinalPrecision"] != "弱精准"


def test_kernel_reference_and_agent_instruction_are_active():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
    agent = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8-sig")
    ref = (ROOT / "references" / "precision-judgment-kernel.md").read_text(encoding="utf-8-sig")
    for text in (skill, agent, ref):
        assert "Searcher Intent" in text
        assert "CORE FIT" in text
        assert "CAN SERVE" in text
        assert "Hard Modifier" in text
    assert "precision-judgment-kernel.md" in skill


def test_full_b2_601_dataset_is_available_for_regression():
    product_root = Path(r"E:\【所有产品目录专用】\B2 姐妹礼物")
    if not product_root.exists():
        return
    resolved = kernel.resolve_latest_601_keyword_output(product_root)
    assert resolved["status"] == kernel.SIX_0_1_KEYWORD_OUTPUT_READY
    assert len(resolved["rows"]) == 3294
    assert all(row.get("record_id") for row in resolved["rows"])
