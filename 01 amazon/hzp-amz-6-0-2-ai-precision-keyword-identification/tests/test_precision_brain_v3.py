import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("precision_v3", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _rows():
    return [
        {"所属产品编号": "BM-A", "对标ASIN": "A", "Id": "1", "词": "sister birthday gifts", "中文": "姐妹生日礼物", "市场容量": "100", "自然排名": "3"},
        {"所属产品编号": "BM-B", "对标ASIN": "B", "Id": "1", "词": "sister birthday gifts", "中文": "姐妹生日礼物", "市场容量": "100", "自然排名": "18"},
        {"所属产品编号": "BM-A", "对标ASIN": "A", "Id": "2", "词": "gift", "中文": "礼物", "市场容量": "90", "自然排名": "7"},
    ]


def _phase_a(ids):
    return [{
        "JudgmentItemId": item_id,
        "SearcherPrimaryIntent": "明确送礼购买任务",
        "ShoppingIntentStrength": "强",
        "PurchaseMissionConvergence": "HIGH",
        "PhysicalProductConvergence": "MEDIUM",
        "CompatibilityConvergence": "NOT_SPECIFIED",
        "ProductMissionFit": "CORE FIT",
        "HardConflictType": "NONE",
        "HardConflictReason": "无明确冲突",
        "InitialPrecision": "高度精准",
        "BenchmarkRealityAssessment": "INSUFFICIENT",
        "ChallengeResult": "CONFIRMED",
        "ChallengeReasonSummary": "去掉排名后语义判断仍成立",
        "FinalPrecision": "高度精准",
        "FinalPrecisionReason": "该词表达姐妹生日送礼购买任务，当前产品事实与关系和场景直接匹配",
        "JudgmentStatus": "SUCCESS",
    } for item_id in ids]


def _profile():
    return [{
        "ProductType": "keepsake figurine",
        "PhysicalProductForm": "hand-painted figurine",
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
    }]


def test_brain_deduplicates_and_runs_two_reveal_phases():
    calls = []

    def client(prompt):
        calls.append(prompt)
        payload = __import__("json").loads(prompt)
        if payload["phase"] == "PRODUCT_PROFILE":
            return _profile()
        ids = [item["JudgmentItemId"] for item in payload["keywords"]]
        if payload["phase"] == "A":
            return _phase_a(ids)
        return [{"JudgmentItemId": item_id, "BenchmarkRealityAssessment": "SUPPORTS"} for item_id in ids]

    result = module.run_precision_brain(_rows(), {"product_text": "姐妹生日纪念雕塑"}, client=client, batch_size=8)
    assert len(result["keyword_units"]) == 2
    assert len(result["decisions"]) == 2
    assert result["ai_call_count"] == 2
    assert result["ProductProfileModelCallCount"] == 1
    assert __import__("json").loads(calls[0])["phase"] == "PRODUCT_PROFILE"
    assert "HIDDEN_IN_PHASE_A" in calls[1]
    assert "HIDDEN_IN_PHASE_A" not in calls[2]


def test_legacy_precision_labels_are_not_structured_final_precision():
    ids = ["J-1"]
    try:
        module.validate_structured_judgments([{"JudgmentItemId": "J-1", "FinalPrecision": "PRECISION", "JudgmentStatus": "SUCCESS", "ChallengeResult": "CONFIRMED", "FinalPrecisionReason": "具体理由足够长"}], ids)
    except ValueError as exc:
        assert str(exc) == "STRUCTURED_JUDGMENT_SCHEMA_INVALID"
    else:
        raise AssertionError("legacy PRECISION must not be accepted as FinalPrecision")


def test_phase_b_cannot_replace_phase_a_semantic_level():
    def client(prompt):
        payload = __import__("json").loads(prompt)
        if payload["phase"] == "PRODUCT_PROFILE":
            return _profile()
        ids = [item["JudgmentItemId"] for item in payload["keywords"]]
        if payload["phase"] == "A":
            return _phase_a(ids)
        return [{"JudgmentItemId": item_id, "BenchmarkRealityAssessment": "CONTRADICTS", "FinalPrecision": "不精准"} for item_id in ids]

    result = module.run_precision_brain(_rows()[:1], {"product_text": "姐妹生日纪念雕塑"}, client=client)
    decision = next(iter(result["decisions"].values()))
    assert decision["FinalPrecision"] == "高度精准"
    assert decision["BenchmarkRealityAssessment"] == "CONTRADICTS"


def test_judgment_item_ids_are_stable_for_repeated_observations():
    first = module.build_keyword_judgment_units(_rows())
    second = module.build_keyword_judgment_units(list(reversed(_rows())))
    assert {row["Canonical_Keyword"]: row["JudgmentItemId"] for row in first} == {row["Canonical_Keyword"]: row["JudgmentItemId"] for row in second}


def test_single_item_brain_failure_is_retained_for_review():
    def broken_client(prompt):
        if __import__("json").loads(prompt)["phase"] == "PRODUCT_PROFILE":
            return _profile()
        return []

    result = module.run_precision_brain(_rows()[:1], {"product_text": "姐妹生日纪念雕塑"}, client=broken_client)
    decision = next(iter(result["decisions"].values()))
    assert decision["FinalPrecision"] == module.DATA_NOT_AVAILABLE
    assert decision["JudgmentStatus"] == "FAILED"


def test_runner_can_start_without_external_decisions(tmp_path):
    import csv
    config_path = tmp_path / module.PRECISION_FILTER_CONFIG_RELATIVE
    config_path.parent.mkdir(parents=True)
    config_path.write_text("高度精准\n精准\n", encoding="utf-8")
    text_path = tmp_path / module.CURRENT_PRODUCT_TEXT_RELATIVE
    text_path.parent.mkdir(parents=True)
    text_path.write_text("姐妹生日纪念雕塑", encoding="utf-8")
    data_dir = tmp_path / "06_SKILL分析报告" / module.BENCHMARK_RAW_OUTPUT_DIR / "data"
    data_dir.mkdir(parents=True)
    path = data_dir / "6-0-1_所有对标自然排名关键词_20260917_120000.csv"
    row = {key: "" for key in module.BENCHMARK_RAW_COLUMNS}
    row.update({"Id": "1", "词": "sister birthday gifts", "中文": "姐妹生日礼物", "市场容量": "100", "竞争产品数": "10", "供需比": "10", "对标ASIN": "ASIN-A", "自然排名": "3", "ASIN": "ASIN-A", "产品编号": "BM-A"})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=module.BENCHMARK_RAW_COLUMNS)
        writer.writeheader(); writer.writerow(row)
    try:
        module.run_current_602(tmp_path, "B2")
    except RuntimeError as exc:
        assert str(exc) == module.AGENT_JUDGMENT_UNAVAILABLE
    else:
        raise AssertionError("production runner must fail closed without the current Agent judge")
