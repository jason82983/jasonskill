import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("precision_execution", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


PROFILE = {
    "ProductType": "keepsake figurine",
    "PhysicalProductForm": "hand-painted resin figurine",
    "CoreFunctions": ["keepsake", "home decor"],
    "PrimaryPurchaseDriver": "GIFT_EMOTIONAL",
    "SecondaryPurchaseDrivers": ["AESTHETIC_DECOR"],
    "TargetAudience": "gift buyers",
    "Recipient": "sisters and friends",
    "RelationshipIntent": "sisterhood and friendship",
    "GiftMission": "meaningful relationship gift",
    "CorePurchaseMission": "buy a sisterhood keepsake gift",
    "PurchaseOccasions": ["birthday", "Christmas"],
    "Material": "resin",
    "Theme": "white moon and connection",
    "Style": "hand-painted",
    "UseCases": ["display", "gift"],
    "CriticalAttributes": ["greeting card"],
    "Compatibility": "NOT_APPLICABLE",
    "InstallationMethod": "NOT_APPLICABLE",
    "ExplicitExclusions": ["candle", "blanket", "jewelry"],
}


def _rows():
    words = [
        "sister birthday gifts", "friendship gifts for women", "big sister gift",
        "best friend gifts for women", "birthday gifts for women", "gifts for women",
        "birthday gifts", "gift", "sister", "friend christmas decorations",
        "women home decor", "jim shore angels figurines", "sister candles from sister funny",
        "sister blankets from sister", "mother and daughter statue", "ornaments for girlfriend",
        "small angel figurines",
    ] + [f"synthetic keyword {i}" for i in range(33)]
    return [{"所属产品编号": "BM-A", "对标ASIN": "ASIN-A", "Id": str(i), "词": word,
             "中文": "", "市场容量": "100", "自然排名": "3"} for i, word in enumerate(words)]


def _client(prompt):
    payload = json.loads(prompt)
    if payload["phase"] == "PRODUCT_PROFILE":
        return [PROFILE]
    ids = [item["JudgmentItemId"] for item in payload["keywords"]]
    if payload["phase"] == "B":
        return [{"JudgmentItemId": item_id, "BenchmarkRealityAssessment": "INSUFFICIENT"} for item_id in ids]
    return [{
        "JudgmentItemId": item_id,
        "SearcherPrimaryIntent": "明确购买任务",
        "ShoppingIntentStrength": "中",
        "PurchaseMissionConvergence": "MEDIUM",
        "PhysicalProductConvergence": "MEDIUM",
        "CompatibilityConvergence": "NOT_SPECIFIED",
        "ProductMissionFit": "CORE FIT",
        "HardConflictType": "NONE",
        "HardConflictReason": "无明确冲突",
        "InitialPrecision": "精准",
        "ChallengeResult": "CONFIRMED",
        "ChallengeReasonSummary": "独立按产品与购买任务判断",
        "FinalPrecision": "精准",
        "FinalPrecisionReason": "该词的购买任务与当前产品事实匹配",
        "JudgmentStatus": "SUCCESS",
    } for item_id in ids]


def test_smoke_50_keywords_uses_profile_and_real_model_contract():
    result = module.run_precision_brain(_rows(), {"product_text": "confirmed product text"}, client=_client, batch_size=16)
    assert len(result["keyword_units"]) == 50
    assert result["ProductProfileModelCallCount"] == 1
    assert result["PrecisionModelCallCount"] == 8  # 4 Phase A + 4 Phase B
    assert result["SuccessfulUniqueJudgmentCount"] == 50
    assert result["ReviewRequiredCount"] == 0
    assert result["FailedJudgmentCount"] == 0
    assert all(item["FinalPrecision"] == "精准" for item in result["judgments"].values())


def test_none_client_fails_closed_without_final_precision():
    try:
        module.run_precision_brain(_rows()[:1], {"product_text": "confirmed product text"})
    except RuntimeError as exc:
        assert str(exc) == module.AI_PRECISION_ENGINE_UNAVAILABLE
    else:
        raise AssertionError("missing AI client must not use a local precision fallback")


def test_caller_supplied_decisions_cannot_bypass_real_ai():
    try:
        module.run_current_602(Path("C:/nonexistent-product"), "B2", decisions={"x": {}})
    except ValueError as exc:
        assert str(exc) == module.EXTERNAL_DECISIONS_NOT_ALLOWED
    else:
        raise AssertionError("caller-supplied precision decisions must not bypass the Brain")


def test_profile_insufficient_stops_before_keyword_judgment():
    def bad_profile(prompt):
        assert json.loads(prompt)["phase"] == "PRODUCT_PROFILE"
        return [{"ProductType": module.DATA_NOT_AVAILABLE,
                 "PrimaryPurchaseDriver": module.DATA_NOT_AVAILABLE,
                 "CorePurchaseMission": module.DATA_NOT_AVAILABLE}]

    try:
        module.run_precision_brain(_rows()[:1], {"product_text": "insufficient"}, client=bad_profile)
    except ValueError as exc:
        assert str(exc) == module.PRODUCT_PROFILE_INSUFFICIENT
    else:
        raise AssertionError("incomplete Product Profile must stop the run")


def test_failed_judgment_does_not_become_weak_precision():
    level, reason = module._decision_signature({
        "FinalPrecision": module.DATA_NOT_AVAILABLE,
        "JudgmentStatus": "FAILED",
        "FinalPrecisionReason": "model timeout",
    })
    assert level == ""
    assert "timeout" in reason


def test_phase_b_ai_failure_keeps_final_precision_blank():
    calls = {"n": 0}

    def failing_phase_b(prompt):
        payload = json.loads(prompt)
        if payload["phase"] == "PRODUCT_PROFILE":
            return [PROFILE]
        calls["n"] += 1
        if payload["phase"] == "B":
            raise RuntimeError("provider timeout")
        ids = [item["JudgmentItemId"] for item in payload["keywords"]]
        return [{"JudgmentItemId": item_id, "FinalPrecision": "精准",
                 "FinalPrecisionReason": "具体购买任务与产品事实匹配",
                 "JudgmentStatus": "SUCCESS", "ChallengeResult": "CONFIRMED"}
                for item_id in ids]

    result = module.run_precision_brain(_rows()[:2], {"product_text": "confirmed"}, client=failing_phase_b, batch_size=2)
    assert all(item["JudgmentStatus"] == "REVIEW_REQUIRED" for item in result["judgments"].values())
    assert all(item["FinalPrecision"] == module.DATA_NOT_AVAILABLE for item in result["judgments"].values())
    assert result["ReviewRequiredCount"] == 2


def test_product_profile_provider_failure_is_explicit():
    def unavailable(_prompt):
        raise TimeoutError("provider unavailable")

    try:
        module.run_precision_brain(_rows()[:1], {"product_text": "confirmed"}, client=unavailable)
    except RuntimeError as exc:
        assert str(exc) == module.AI_PRECISION_ENGINE_UNAVAILABLE
    else:
        raise AssertionError("Product Profile provider failure must stop explicitly")


def test_prepare_package_contains_facts_only(monkeypatch):
    monkeypatch.setattr(module, "read_current_product_text_evidence", lambda _root: {
        "status": module.CURRENT_PRODUCT_TEXT_EVIDENCE_READY,
        "product_text": "confirmed product text", "text_path": "product.txt",
        "content_sha256": "abc", "content_size_bytes": 20,
    })
    rows = _rows()[:2]
    monkeypatch.setattr(module, "resolve_latest_601_keyword_output", lambda _root, product_code=None: {
        "status": module.SIX_0_1_KEYWORD_OUTPUT_READY, "rows": rows,
        "input_metadata": {"Benchmark_Codes": ["BM-A"], "Benchmark_ASINs": ["ASIN-A"], "BenchmarkProductCodes": {"ASIN-A": "BM-A"}},
        "file": "601.csv", "run_id": "R1", "run_timestamp": "20260917_120000",
    })
    prepared = module.prepare_602("C:/product", "B2")
    assert prepared["keyword_units"]
    assert "FinalPrecision" not in prepared
    assert "InitialPrecision" not in prepared
    assert "product_evidence_package" in prepared
