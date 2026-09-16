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
