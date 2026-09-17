"""Dual-track precision-keyword views for Stage 6-0-2.

The normal 6-0-2 inputs are the complete current-product text evidence file
and the all-observation CSV from the latest valid, timestamped 6-0-1 batch. This
module remains provider-agnostic and never opens an ERP connection or writes
ERP/Amazon data.  The lower-level row helpers accept already supplied mappings
for compatibility, while the 6-0-1 entry helper is the runtime path for
current runs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterable, Mapping
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from codex_cli_judge import CodexCliError, codex_login_status, codex_version, run_codex_cli_judge  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.stage6_artifact_contract import (  # noqa: E402
    assert_new_outputs,
    new_run_context,
    resolve_latest_valid_report,
    timestamped_output_path,
    validate_601_run_package,
)
from scripts.hzp_amz_report_contract import (  # noqa: E402
    governance_paths, publish_latest_valid_batch, resolve_latest_valid_data,
    resolve_skill_report_dir, validate_hzp_amz_report_batch,
)

PRECISION_TAG = "|1\u7cbe\u51c6|"
AI_FILENAME = "6-0-2_{product_code}_AI\u7cbe\u51c6\u8bcd.csv"
HIGH_PRECISION_FILENAME = "6-0-2_{product_code}_AI\u9ad8\u5ea6\u7cbe\u51c6\u8bcd.csv"
OUTPUT_DIR = "6-0-2_AI\u7cbe\u51c6\u5173\u952e\u8bcd\u8bc6\u522b"
FINAL_COLUMNS = ("\u81ea\u52a8\u7f16\u53f7", "\u5173\u952e\u8bcd", "\u641c\u7d22\u91cf", "\u4e2d\u6587\u540d\u79f0", "\u7cbe\u51c6\u7406\u7531", "\u7cbe\u51c6\u5ea6")  # legacy projection
FULL_FINAL_COLUMNS = ("Id", "\u8bcd", "\u4e2d\u6587", "\u5e02\u573a\u5bb9\u91cf", "\u7ade\u4e89\u4ea7\u54c1\u6570", "\u4f9b\u9700\u6bd4", "\u5bf9\u6807\u8986\u76d6\u6570", "\u6700\u4f73\u81ea\u7136\u6392\u540d", "\u81ea\u7136\u6392\u540d\u4e2d\u4f4d\u6570", "\u7cbe\u51c6\u5ea6", "\u7cbe\u51c6\u539f\u56e0")
ERP_KEYWORD_RECORD_ID_UNCONFIRMED = "[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]"
OBSERVATION_FINAL_COLUMNS = ("所属产品编号", "对标ASIN", "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名", "精准度", "精准原因")
DEDUPLICATED_FINAL_COLUMNS = FULL_FINAL_COLUMNS
ERP_KEYWORD_RECORD_ID_AMBIGUOUS = "[ERP_KEYWORD_RECORD_ID_AMBIGUOUS]"
ERP_KEYWORD_RECORD_IDENTITY_CONFLICT = "[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]"

QUALITY_FIELDS = (
    "KeywordCn", "IsMain", "IsLongTail", "IsGoodCvt", "IsSold",
    "SearchVolumeDaily", "SearchGrowthRate30", "IQScore",
    "SearchSoldSum", "SearchCvtRate", "SearchHitSum", "SearchHitRate",
    "abarank", "UpdateTime", "RecordDate",
)
AI_EXCLUDED_FIELDS = {"IsExact", "raw_fields", "AsinQuantity", "SupplyDemandRatio", "\u7ade\u4e89\u4ea7\u54c1\u6570", "\u4f9b\u9700\u6bd4", "\u5e02\u573a\u5bb9\u91cf", "SearchVolume30"}
COMPETING_PRODUCTS_PASSTHROUGH_MISMATCH = "COMPETING_PRODUCTS_PASSTHROUGH_MISMATCH"
SUPPLY_DEMAND_RATIO_PASSTHROUGH_MISMATCH = "SUPPLY_DEMAND_RATIO_PASSTHROUGH_MISMATCH"
MULTI_BENCHMARK_PASSTHROUGH_MISMATCH = "MULTI_BENCHMARK_PASSTHROUGH_MISMATCH"
FILE_A_RECORD_COVERAGE_MISMATCH = "FILE_A_RECORD_COVERAGE_MISMATCH"
FILE_B_RECORD_COVERAGE_MISMATCH = "FILE_B_RECORD_COVERAGE_MISMATCH"
OUTPUT_READBACK_FAILED = "OUTPUT_READBACK_FAILED"
OUTPUT_SCHEMA_MISMATCH = "OUTPUT_SCHEMA_MISMATCH"
AI_CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
# Legacy input labels retained only for isolated historical compatibility;
# they are never valid FinalPrecision values in the V3 structured contract.
LEGACY_AI_CLASSIFICATIONS = {"PRECISION", "NOT_PRECISION", "REVIEW_REQUIRED"}
JUDGMENT_STATUSES = {"SUCCESS", "REVIEW_REQUIRED", "FAILED"}
PRECISION_LEVELS = ("高度精准", "精准", "弱精准", "不精准")
# Runtime 6-0-2 runs load the selected levels from the shared system
# configuration.  Keep this compatibility value for low-level callers and
# historical tests that supply rows directly without a product root.
DEFAULT_FILTERED_PRECISION_LEVELS = frozenset({"高度精准"})
FILTERED_PRECISION_LEVELS = DEFAULT_FILTERED_PRECISION_LEVELS
PRECISION_LABEL_ALIASES = {"已精准": "精准"}
PRECISION_FILTER_CONFIG_RELATIVE = Path("01_公共资料") / "03_系统配置" / "生成精准词库的要求.txt"
PRECISION_FILTER_CONFIG_FILENAME = PRECISION_FILTER_CONFIG_RELATIVE.name
PRECISION_LEVEL_NOT_AVAILABLE = "PRECISION_LEVEL_NOT_AVAILABLE"
DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"
BENCHMARK_ERP_PROID_NOT_AVAILABLE = "BENCHMARK_ERP_PROID_NOT_AVAILABLE"
BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE = "BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE"
OWN_ONLY = "OWN_ONLY"
OWN_PLUS_BENCHMARK = "OWN_PLUS_BENCHMARK"
BENCHMARK_FALLBACK = "BENCHMARK_FALLBACK"
KEYWORD_SOURCE_DATA_INSUFFICIENT = "CURRENT_KEYWORDS_UNAVAILABLE_NO_BENCHMARK"
BENCHMARK_RAW_OUTPUT_DIR = "6-0-1_\u5bf9\u6807\u81ea\u7136\u6392\u540d\u5173\u952e\u8bcd\u63d0\u53d6"
BENCHMARK_RAW_FILENAME_RE = re.compile(r"^6-0-1_(?:\d{2}_)?所有对标自然排名关键词_\d{8}_\d{6}\.csv$", re.I)
BENCHMARK_RAW_COLUMNS = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标ASIN", "自然排名", "ASIN", "产品编号")
SIX_0_1_SKILL_ID = "hzp-amz-6-0-1-benchmark-organic-keyword-extraction"
SIX_0_1_REPORT_IDENTITY = "BENCHMARK_KEYWORD_ALL_OBSERVATIONS"
SIX_0_2_SKILL_ID = "hzp-amz-6-0-2-ai-precision-keyword-identification"
BENCHMARK_RAW_NOT_FOUND = "6-0-1 Benchmark Organic Keyword Raw CSV not found."
BENCHMARK_RAW_SCHEMA_INVALID = "6-0-1 Benchmark Organic Keyword Raw CSV schema invalid."
SIX_0_1_KEYWORD_OUTPUT_READY = "SIX_0_1_KEYWORD_OUTPUT_READY"
SIX_0_1_KEYWORD_INPUT_NOT_FOUND = "6-0-1_KEYWORD_INPUT_NOT_FOUND"
# Backward-compatible symbol; the formal returned status is the input status above.
SIX_0_1_KEYWORD_OUTPUT_NOT_FOUND = SIX_0_1_KEYWORD_INPUT_NOT_FOUND
CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND = "CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND"
CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY = "CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY"
CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED = "CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED"
CURRENT_PRODUCT_TEXT_EVIDENCE_READY = "CURRENT_PRODUCT_TEXT_EVIDENCE_READY"
CURRENT_PRODUCT_TEXT_RELATIVE = Path("05_分析源数据") / "01_产品数据" / "本产品" / "产品识别 - 文本文案.txt"
AI_PRECISION_ENGINE_UNAVAILABLE = "AI_PRECISION_ENGINE_UNAVAILABLE"
PRODUCT_PROFILE_INSUFFICIENT = "PRODUCT_PROFILE_INSUFFICIENT"
PRODUCT_PROFILE_OUTPUT_INVALID = "PRODUCT_PROFILE_OUTPUT_INVALID"
EXTERNAL_DECISIONS_NOT_ALLOWED = "EXTERNAL_DECISIONS_NOT_ALLOWED"
AGENT_JUDGMENT_UNAVAILABLE = "AGENT_JUDGMENT_UNAVAILABLE"
AI_PRECISION_JUDGMENT_UNAVAILABLE = "AI_PRECISION_JUDGMENT_UNAVAILABLE"
PRODUCTION_CHECKPOINT_SCHEMA = "6-0-2_PRODUCTION_JUDGMENT_CHECKPOINT_V1"
V4_CHECKPOINT_SCHEMA = "6-0-2_V4_INTERRUPTION_CHECKPOINT_V1"
# Probe values are defaults for adaptive calibration, not a production limit.
DEFAULT_SAFE_BATCH_PROBES = (32, 64, 128, 256, 512)
RUN_MANIFEST_NAME = "run_manifest.json"
RUN_MANIFEST_PREFIX = "6-0-2_RunPackage_"
SEMANTIC_PROFILE_FIELDS = (
    "Core_Product_Type", "Physical_Product_Form", "Core_Purchase_Mission", "Target_Customer", "Recipient", "Core_Functions",
    "Core_Use_Cases", "Purchase_Occasions", "Relationship_Intent",
    "Core_Attributes", "Material", "Theme", "Style", "Important_Differentiators", "Compatibility",
    "Compatible_Search_Intents", "Incompatible_Search_Intents",
    "Excluded_Product_Types", "Hard_Intent_Conflicts", "Installation_Method",
)
PRODUCT_PROFILE_REQUIRED_FIELDS = ("Core_Product_Type", "PrimaryPurchaseDriver", "Core_Purchase_Mission")
PRODUCT_PROFILE_OUTPUT_FIELDS = (
    "ProductType", "PhysicalProductForm", "CoreFunctions", "PrimaryPurchaseDriver",
    "SecondaryPurchaseDrivers", "TargetAudience", "Recipient", "RelationshipIntent",
    "GiftMission", "CorePurchaseMission", "PurchaseOccasions", "Material", "Theme",
    "Style", "UseCases", "CriticalAttributes", "Compatibility", "InstallationMethod",
    "ExplicitExclusions",
)
PURCHASE_DRIVERS = ("FUNCTIONAL", "COMPATIBILITY", "GIFT_EMOTIONAL", "AESTHETIC_DECOR", "OCCASION", "HYBRID")
PURCHASE_DRIVER_EVIDENCE_FIELDS = (
    "GiftIntentPresent", "GiftMissionFit", "PurchaseMissionFit", "RecipientFit", "RelationshipFit",
    "OccasionFit", "EmotionalMessageFit",
)
CONVERGENCE_FIELDS = ("PhysicalProductConvergence", "PurchaseMissionConvergence", "CompatibilityConvergence")
DECISION_CHALLENGE_RESULTS = ("CONFIRMED", "DOWNGRADED", "UPGRADED", "RECONSIDERED_NO_CHANGE")
_GENERIC_PRODUCT_TYPES = {"gift", "gifts", "product", "products", "item", "items"}
_GENERIC_QUERY_TOKENS = _GENERIC_PRODUCT_TYPES | {
    "present", "presents", "idea", "ideas", "thing", "things", "stuff",
}
_RECIPIENT_QUERY_TOKENS = {
    "sister", "sisters", "brother", "brothers", "mom", "moms", "mother", "mothers",
    "dad", "dads", "father", "fathers", "daughter", "daughters", "son", "sons",
    "wife", "wives", "husband", "husbands", "girlfriend", "boyfriend", "friend", "friends",
    "family", "families", "woman", "women", "man", "men", "aunt", "aunts", "uncle", "uncles",
    "cousin", "cousins", "niece", "nieces", "nephew", "nephews", "child", "children", "kids",
}
_OCCASION_QUERY_TOKENS = {
    "birthday", "birthdays", "christmas", "valentine", "valentines", "wedding", "weddings",
    "anniversary", "anniversaries", "graduation", "graduations", "easter", "retirement",
    "thanksgiving", "holiday", "holidays", "bridal", "shower", "showers",
}
_QUERY_STOPWORDS = {"a", "an", "and", "for", "from", "her", "his", "my", "the", "to", "your"}
_PRODUCT_INTENT_TOKENS = {
    "figurine", "figurines", "statue", "statues", "sculpture", "sculptures",
    "keepsake", "keepsakes", "ornament", "ornaments", "decor", "decoration",
    "decorations", "collectible", "collectibles", "card", "cards", "necklace",
    "necklaces", "jewelry", "bracelet", "blanket", "candle", "mug", "shoes",
    "anchor", "anchors",
}
_RELATIONSHIP_INTENT_TOKENS = {
    "sister", "sisters", "sisterhood", "friend", "friends", "friendship",
    "bestie", "besties", "daughter", "daughters", "family", "cousin", "cousins",
    "mom", "mother", "mothers", "women", "woman", "girl", "girls",
}
_GIFT_PURPOSE_TOKENS = {
    "gift", "gifts", "present", "presents", "birthday", "christmas", "holiday",
    "holidays", "graduation", "wedding", "anniversary", "memorial", "remembrance",
    "valentine", "valentines", "friendship",
}
_BROAD_DEMOGRAPHIC_TOKENS = {"women", "woman", "girls", "girl", "men", "man", "people"}
_HARD_PRODUCT_TYPE_TOKENS = {
    "card", "cards", "necklace", "necklaces", "jewelry", "bracelet", "blanket",
    "candle", "mug", "shoes", "shoe", "bag", "bags", "purse", "purses",
}
_MATERIAL_TOKENS = {"wooden": "wood", "wood": "wood", "resin": "resin", "metal": "metal", "glass": "glass"}
_GENERIC_PRECISION_REASON = "核心搜索意图与产品语义画像在购买对象/场景/功能上直接匹配"

AI_REQUIRED_OUTPUT = (
    "Product_Code", "ERP_ProId", "Current_ERP_ProId", "Marketplace", "ASIN",
    "Keyword", "KeywordCn", "AI_Classification", "AI_Is_Precision",
    "AI_Confidence", "AI_Reason", "Product_Intent_Fit", "Search_Intent",
    "Matched_Product_Attributes", "Conflicting_Product_Attributes",
    "Manual_Precision_Label", "Comparison_Status", "SearchVolume30",
    "SearchVolumeDaily", "SearchGrowthRate30", "abarank", "IsSold",
    "SearchSoldSum", "SearchCvtRate", "SearchHitSum", "SearchHitRate",
    "IsGoodCvt", "IQScore", "AsinQuantity", "AsinQuantityAdv", "Cpr8",
    "CprDaily", "Benchmark_ERP_ProIds", "Benchmark_Count",
    "Benchmark_Keyword_Coverage", "Benchmark_Organic_Rank_Count",
    "Benchmark_Organic_Evidence", "Best_Benchmark_Organic_Rank",
    "Median_Benchmark_Organic_Rank", "Benchmark_Evidence_Summary", "Evidence_Summary", "Impressions",
    "Clicks", "CTR", "Spend", "CPC", "Orders", "Sales", "CVR", "CPA",
    "ACoS", "Organic_Rank", "Organic_Rank_Trend", "Provider", "Source_Grain",
    "Metric_Semantics", "Attribution_Semantics", "Data_Through", "Freshness",
    "Tags", "RecordDate", "UpdateTime", "Result_Status",
)
RESULT_STATUS_FIELD = "Result_Status"


def build_product_semantic_profile(source: Mapping[str, Any] | None) -> dict[str, Any]:
    """Copy a product semantic profile from verified product materials only.

    This helper deliberately does not infer attributes from a Keyword.  The
    caller must populate the profile from the product record, specifications,
    or approved upstream materials; absent fields remain explicit unknowns.
    """
    source = source if isinstance(source, Mapping) else {}
    return {
        field: source.get(field, DATA_NOT_AVAILABLE)
        if source.get(field) not in (None, "", [], {}) else DATA_NOT_AVAILABLE
        for field in SEMANTIC_PROFILE_FIELDS
    }


def _semantic_values(value: Any) -> list[str]:
    if value in (None, "", DATA_NOT_AVAILABLE):
        return []
    if isinstance(value, Mapping):
        values: list[str] = []
        for key, item in value.items():
            values.extend(_semantic_values(key))
            values.extend(_semantic_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for item in value:
            values.extend(_semantic_values(item))
        return values
    return [" ".join(str(value).strip().lower().split())]


def _semantic_overlap(left: Any, right: Any) -> bool:
    left_values = _semantic_values(left)
    right_values = _semantic_values(right)
    return any(a == b or a in b or b in a for a in left_values for b in right_values)


def _meaningful_token_overlap(left: Any, right: Any) -> bool:
    """Compare intent phrases without letting ``gift`` substring-match everything."""
    left_tokens = {_token_stem(t) for t in _query_tokens(left)
                   if t not in _GENERIC_QUERY_TOKENS and t not in _QUERY_STOPWORDS}
    right_tokens = {_token_stem(t) for t in _query_tokens(right)
                    if t not in _GENERIC_QUERY_TOKENS and t not in _QUERY_STOPWORDS}
    return bool(left_tokens and right_tokens and left_tokens & right_tokens)


def _profile_relationship_values(profile: Mapping[str, Any]) -> list[Any]:
    values: list[Any] = []
    for field in ("Relationship_Intent", "Recipient", "Compatible_Search_Intents", "Core_Use_Cases", "Core_Product_Type"):
        values.extend(_semantic_values(profile.get(field)))
    return values


def _relationship_fit(left: Any, right: Any) -> bool:
    left_tokens = {_token_stem(t) for t in _query_tokens(left)}
    right_tokens = {_token_stem(t) for t in _query_tokens(right)}
    if "friend" in left_tokens and "friendship" in right_tokens:
        return True
    if "friendship" in left_tokens and "friend" in right_tokens:
        return True
    return bool(left_tokens & right_tokens)


def _query_tokens(value: Any) -> list[str]:
    """Tokenize a query without treating substrings as product evidence."""
    text = " ".join(_semantic_values(value))
    return re.findall(r"[a-z0-9]+", text.lower())


def _token_stem(token: str) -> str:
    """Apply only a conservative plural normalization for intent matching."""
    return token[:-1] if len(token) > 4 and token.endswith("s") else token


def _query_specificity(profile: Mapping[str, Any], intent: Mapping[str, Any], keyword: str | None = None) -> dict[str, Any]:
    """Reconstruct the search mode before comparing it with the product.

    Product-type explicitness is only one source of precision.  A relationship
    gift query can be a CORE FIT when the relationship and gift purpose are the
    product's defining reason to buy.  Broad demographic/occasion queries stay
    CAN SERVE or unresolved.  This helper is a guardrail for an AI decision;
    it does not assign a final four-level label.
    """
    query = keyword or intent.get("Core_Intent") or " ".join(_explicit_intent_values(intent))
    tokens = [_token_stem(token) for token in _query_tokens(query)]
    token_set = set(tokens)
    if not tokens:
        return {"ok": False, "search_mode": "UNRESOLVED", "core_fit": "UNKNOWN",
                "reason": "搜索词本身不可用，无法确认购买意图", "matched_tokens": []}
    explicit_product = token_set & _PRODUCT_INTENT_TOKENS
    relationships = token_set & _RELATIONSHIP_INTENT_TOKENS
    gift_purpose = token_set & _GIFT_PURPOSE_TOKENS
    broad_only = token_set <= (_QUERY_STOPWORDS | _GENERIC_QUERY_TOKENS | _BROAD_DEMOGRAPHIC_TOKENS
                               | _OCCASION_QUERY_TOKENS | _GIFT_PURPOSE_TOKENS)
    if intent.get("Product_Type") not in (None, "", DATA_NOT_AVAILABLE):
        explicit_product.add("structured_product_type")
    strong_relationships = relationships - _BROAD_DEMOGRAPHIC_TOKENS
    if strong_relationships and gift_purpose:
        mode = "GIFT_LED"
        reason = "关系对象与送礼目的共同构成购买意图"
        return {"ok": True, "search_mode": mode, "core_fit": "CANDIDATE_CORE_FIT",
                "reason": reason, "matched_tokens": sorted(strong_relationships | gift_purpose)}
    if relationships and gift_purpose and relationships & _BROAD_DEMOGRAPHIC_TOKENS:
        return {"ok": True, "search_mode": "BROAD_GIFT", "core_fit": "CAN_SERVE",
                "reason": "仅有宽泛人群/场景，产品只是众多礼物答案之一", "matched_tokens": sorted(relationships | gift_purpose)}
    if relationships and not gift_purpose and not explicit_product:
        return {"ok": True, "search_mode": "RELATIONSHIP_ONLY", "core_fit": "CANDIDATE_CORE_FIT",
                "reason": "关系意图与产品主题一致，但没有明确商品或送礼目的", "matched_tokens": sorted(relationships)}
    if broad_only:
        return {"ok": True, "search_mode": "BROAD_GIFT", "core_fit": "CAN_SERVE",
                "reason": f"搜索词“{query}”主要表达泛礼物、对象或场景，未收敛到单一商品答案", "matched_tokens": []}
    if explicit_product:
        return {"ok": True, "search_mode": "PRODUCT_LED", "core_fit": "CANDIDATE_CORE_FIT",
                "reason": f"搜索词明确表达了商品类型（{', '.join(sorted(explicit_product))}），再与产品事实核对", "matched_tokens": sorted(explicit_product)}
    return {"ok": False, "search_mode": "UNRESOLVED", "core_fit": "UNKNOWN",
            "reason": f"搜索词“{query}”的主要购买对象和商品类型仍不清楚", "matched_tokens": []}


def _purchase_driver_evidence(
    profile: Mapping[str, Any], intent: Mapping[str, Any], keyword: str, specificity: Mapping[str, Any],
    *, purchase_driver: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Return qualitative gift and convergence evidence without numeric scoring."""
    query_tokens = set(_token_stem(token) for token in _query_tokens(keyword or intent.get("Core_Intent")))
    resolved_driver = purchase_driver or build_product_purchase_driver(profile)
    driver = resolved_driver.get("PrimaryPurchaseDriver")
    secondary_drivers = set(resolved_driver.get("SecondaryPurchaseDrivers") or ())
    gift_driver_active = driver == "GIFT_EMOTIONAL" or (driver == "HYBRID" and "GIFT_EMOTIONAL" in secondary_drivers)
    compatibility_driver_active = driver == "COMPATIBILITY" or (driver == "HYBRID" and "COMPATIBILITY" in secondary_drivers)
    gift_present = bool(query_tokens & _GIFT_PURPOSE_TOKENS)
    relationship_tokens = query_tokens & _RELATIONSHIP_INTENT_TOKENS
    recipient = intent.get("Recipient") or intent.get("Relationship")
    occasion = intent.get("Purchase_Occasions") or intent.get("Occasion")
    profile_recipient = profile.get("Recipient") or profile.get("Relationship_Intent")
    profile_occasion = profile.get("Purchase_Occasions")
    occasion_present = bool(query_tokens & _OCCASION_QUERY_TOKENS)
    relation_fit = _relationship_fit(recipient or relationship_tokens, _profile_relationship_values(profile)) if (recipient or relationship_tokens) else False
    occasion_fit = _semantic_overlap(occasion, profile_occasion) if occasion not in (None, "", DATA_NOT_AVAILABLE) else bool(query_tokens & _OCCASION_QUERY_TOKENS and _semantic_overlap(query_tokens & _OCCASION_QUERY_TOKENS, profile_occasion))
    mission_fit = "NOT_SPECIFIED"
    if gift_driver_active:
        if specificity.get("search_mode") == "BROAD_GIFT":
            mission_fit = "LOW"
        elif specificity.get("search_mode") == "GIFT_LED" and gift_present and relation_fit and (occasion_fit or not occasion_present):
            mission_fit = "HIGH"
        elif gift_present and (relation_fit or occasion_fit):
            mission_fit = "MEDIUM"
        elif gift_present:
            mission_fit = "LOW"
        elif relationship_tokens and relation_fit:
            mission_fit = "MEDIUM"
    emotional_fit = "HIGH" if mission_fit == "HIGH" and ("friendship" in query_tokens or relationship_tokens) else ("MEDIUM" if gift_present else "NOT_SPECIFIED")
    physical = "HIGH" if specificity.get("search_mode") == "PRODUCT_LED" and bool(specificity.get("matched_tokens")) else ("MEDIUM" if specificity.get("search_mode") == "GIFT_LED" else "LOW")
    purchase = mission_fit if gift_driver_active else ("HIGH" if specificity.get("core_fit") == "CANDIDATE_CORE_FIT" else "MEDIUM")
    compatibility = "HIGH" if compatibility_driver_active and _semantic_overlap(intent.get("Compatibility"), profile.get("Compatibility")) else ("NOT_SPECIFIED" if not compatibility_driver_active else "LOW")
    return {
        "GiftIntentPresent": "HIGH" if gift_present else "NOT_SPECIFIED",
        "GiftMissionFit": mission_fit,
        "PurchaseMissionFit": mission_fit,
        "RecipientFit": "HIGH" if relation_fit else ("LOW" if recipient not in (None, "", DATA_NOT_AVAILABLE) else "NOT_SPECIFIED"),
        "RelationshipFit": "HIGH" if relation_fit else ("LOW" if relationship_tokens else "NOT_SPECIFIED"),
        "OccasionFit": "HIGH" if occasion_fit else ("LOW" if occasion not in (None, "", DATA_NOT_AVAILABLE) else "NOT_SPECIFIED"),
        "EmotionalMessageFit": emotional_fit,
        "PhysicalProductConvergence": physical,
        "PurchaseMissionConvergence": purchase,
        "CompatibilityConvergence": compatibility,
    }


def _decision_challenge(
    driver: Mapping[str, Any], specificity: Mapping[str, Any], evidence: Mapping[str, str],
    *, conflict: str | None = None, initial_precision: str = DATA_NOT_AVAILABLE,
) -> dict[str, Any]:
    """Challenge a proposed precision level before finalizing it."""
    primary = driver.get("PrimaryPurchaseDriver")
    secondary = set(driver.get("SecondaryPurchaseDrivers") or ())
    gift_driver_active = primary == "GIFT_EMOTIONAL" or (primary == "HYBRID" and "GIFT_EMOTIONAL" in secondary)
    checks = {
        "PhysicalShapeOverweightedForGift": bool(gift_driver_active and evidence.get("PurchaseMissionConvergence") == "HIGH" and evidence.get("PhysicalProductConvergence") != "HIGH"),
        "WrongDriverEvidence": bool(not gift_driver_active and evidence.get("GiftMissionFit") == "HIGH"),
        "BroadGiftOverestimated": bool(specificity.get("search_mode") == "BROAD_GIFT"),
        "RelationshipOnlyOverestimated": bool(specificity.get("search_mode") == "RELATIONSHIP_ONLY" and evidence.get("GiftMissionFit") != "HIGH"),
        "HardConflictPreserved": bool(conflict),
    }
    if conflict:
        # A confirmed conflict vetoes a positive proposal.  If the proposal
        # was already negative, the challenge confirms that outcome instead
        # of reporting a misleading reconsideration.
        result = "DOWNGRADED" if initial_precision in {"高度精准", "精准"} else "CONFIRMED"
    elif checks["PhysicalShapeOverweightedForGift"]:
        result = "CONFIRMED"
    elif checks["BroadGiftOverestimated"] or checks["RelationshipOnlyOverestimated"]:
        result = "RECONSIDERED_NO_CHANGE"
    else:
        result = "CONFIRMED"
    return {"ChallengeResult": result, "ChallengeChecks": checks}


def _lexical_hard_modifier_conflict(profile: Mapping[str, Any], keyword: str) -> str | None:
    """Detect explicit keyword modifiers that the confirmed profile cannot meet."""
    tokens = set(_query_tokens(keyword))
    if not tokens:
        return None
    product_type = str(profile.get("Core_Product_Type") or "").lower()
    excluded = " ".join(_semantic_values(profile.get("Excluded_Product_Types"))).lower()
    if tokens & _HARD_PRODUCT_TYPE_TOKENS:
        requested = sorted(tokens & _HARD_PRODUCT_TYPE_TOKENS)[0]
        if requested not in product_type and requested not in excluded:
            return f"Product Type Conflict: keyword requires {requested}, confirmed product type is {product_type or DATA_NOT_AVAILABLE}"
    if "personalized" in tokens or "custom" in tokens or "personalized" in excluded:
        profile_text = " ".join(_semantic_values(profile.get("Core_Attributes")) + _semantic_values(profile.get("Hard_Intent_Conflicts"))).lower()
        if "personal" not in profile_text or "not personal" in profile_text or "non-personal" in profile_text:
            return "Required Feature Conflict: keyword requires personalization, but confirmed support is unavailable"
    for token, normalized in _MATERIAL_TOKENS.items():
        if token in tokens:
            profile_text = " ".join(_semantic_values(profile.get("Core_Attributes")) + _semantic_values(profile.get("Core_Product_Type"))).lower()
            if normalized not in profile_text:
                return f"Material Conflict: keyword requires {token}, confirmed material evidence is {profile_text or DATA_NOT_AVAILABLE}"
    number_match = re.search(r"\b([2-9]|two|three|four|five|six|seven|eight|nine)\s+(?:sister|sisters|people|person|figures?)\b", keyword.lower())
    if number_match:
        requested = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}.get(number_match.group(1), int(number_match.group(1)) if number_match.group(1).isdigit() else None)
        profile_text = " ".join(_semantic_values(profile.get("Core_Attributes")) + _semantic_values(profile.get("Core_Product_Type"))).lower()
        profile_number = re.search(r"\b([2-9]|two|three|four|five|six|seven|eight|nine)\s+(?:sister|sisters|people|person|figures?)\b", profile_text)
        if profile_number:
            actual = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}.get(profile_number.group(1), int(profile_number.group(1)) if profile_number.group(1).isdigit() else None)
            if actual is not None and requested is not None and actual != requested:
                return f"Representation Conflict: keyword requires {requested} represented figures, confirmed product evidence specifies {actual}"
    return None


def _explicit_intent_values(intent: Mapping[str, Any]) -> list[str]:
    fields = (
        "Core_Intent", "Product_Type", "Target_Customer", "Recipient",
        "Core_Functions", "Use_Cases", "Purchase_Occasions", "Relationship",
        "Attributes", "Compatibility", "Installation_Method", "Quantity",
    )
    values: list[str] = []
    for field in fields:
        values.extend(_semantic_values(intent.get(field)))
    return values


def _hard_conflict(profile: Mapping[str, Any], intent: Mapping[str, Any]) -> str | None:
    """Return an explicit conflict reason; never infer a missing attribute."""
    product_type = intent.get("Product_Type")
    profile_type = profile.get("Core_Product_Type")
    if product_type not in (None, "", DATA_NOT_AVAILABLE) and profile_type not in (None, "", DATA_NOT_AVAILABLE):
        intent_types = set(_semantic_values(product_type)) - _GENERIC_PRODUCT_TYPES
        profile_types = set(_semantic_values(profile_type)) - _GENERIC_PRODUCT_TYPES
        if intent_types and profile_types and not _semantic_overlap(intent_types, profile_types):
            return f"Product Type Conflict: keyword requires {product_type}, product profile is {profile_type}"
    if product_type not in (None, "", DATA_NOT_AVAILABLE) and _semantic_overlap(product_type, profile.get("Excluded_Product_Types")):
        return f"Excluded Product Type Conflict: {product_type}"
    if _semantic_overlap(intent.get("Core_Intent"), profile.get("Incompatible_Search_Intents")):
        return "Incompatible Search Intent Conflict"
    for label, intent_field, profile_field in (
        ("Function", "Core_Functions", "Core_Functions"),
        ("Compatibility", "Compatibility", "Compatibility"),
    ):
        required = intent.get(intent_field)
        supported = profile.get(profile_field)
        if required not in (None, "", DATA_NOT_AVAILABLE) and supported not in (None, "", DATA_NOT_AVAILABLE):
            if not _semantic_overlap(required, supported):
                return f"{label} Conflict: keyword requires {required}, product profile is {supported}"
    relationship = intent.get("Relationship") or intent.get("Recipient")
    profile_relationship = _profile_relationship_values(profile)
    if relationship not in (None, "", DATA_NOT_AVAILABLE) and profile_relationship not in (None, "", DATA_NOT_AVAILABLE):
        if not _relationship_fit(relationship, profile_relationship):
            return f"Relationship/Recipient Conflict: keyword requires {relationship}, product profile is {profile_relationship}"
    intent_install = " ".join(_semantic_values(intent.get("Installation_Method")))
    for conflict in _semantic_values(profile.get("Hard_Intent_Conflicts")):
        if ("no drill" in intent_install and "drill" in conflict) or (
            "requires drilling" in intent_install and "no drill" in conflict
        ):
            return f"Hard Installation Conflict: {conflict}"
    attributes = intent.get("Attributes")
    profile_attributes = profile.get("Core_Attributes")
    if attributes not in (None, "", DATA_NOT_AVAILABLE):
        if profile_attributes in (None, "", DATA_NOT_AVAILABLE):
            return None
        if not _semantic_overlap(attributes, profile_attributes):
            return f"Core Attribute Conflict: keyword requires {attributes}, product profile is {profile_attributes}"
    return None


def _benchmark_reality_check(evidence: Mapping[str, Any] | None) -> str:
    """Classify Benchmark organic-rank evidence as support, conflict, or unknown."""
    if not isinstance(evidence, Mapping) or not evidence:
        return "UNKNOWN"
    status = str(evidence.get("Benchmark_Organic_Evidence") or "").upper()
    if status in {"CONTRADICTING", "CONFLICT", "AVAILABLE_NO_RANK", "NO_MATCH"}:
        return "CONFLICT"
    if status == "AVAILABLE":
        try:
            rank_count = int(evidence.get("Benchmark_Organic_Rank_Count") or 0)
        except (TypeError, ValueError):
            rank_count = 0
        return "SUPPORT" if rank_count > 0 else "CONFLICT"
    if status == BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE:
        return "UNKNOWN"
    return "UNKNOWN"


def _evaluate_product_search_intent_fit_core(
    product_profile: Mapping[str, Any] | None,
    keyword_intent: Mapping[str, Any] | None,
    *,
    keyword: str | None = None,
    supporting_evidence: Mapping[str, Any] | None = None,
    purchase_driver: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply semantic guardrails to an AI's holistic Product–Search Intent judgment.

    Hard conflicts explicitly confirmed by the product profile veto Precision.
    Search mode, CORE FIT/CAN SERVE and Query Specificity are checked after an
    independent intent reconstruction. Volume, advertising metrics, rank,
    orders, and Benchmark labels are retained only as supporting evidence and
    cannot alter the semantic classification.
    """
    profile = build_product_semantic_profile(product_profile)
    intent = keyword_intent if isinstance(keyword_intent, Mapping) else {}
    resolved_driver = purchase_driver or build_product_purchase_driver({**profile, **(product_profile or {})})
    driver_primary = resolved_driver.get("PrimaryPurchaseDriver")
    driver_secondary = set(resolved_driver.get("SecondaryPurchaseDrivers") or ())
    gift_driver_active = driver_primary == "GIFT_EMOTIONAL" or (
        driver_primary == "HYBRID" and "GIFT_EMOTIONAL" in driver_secondary
    )
    conflict = _hard_conflict(profile, intent) or _lexical_hard_modifier_conflict(profile, keyword or str(intent.get("Core_Intent") or ""))
    if conflict:
        return {
            "AI_Classification": "NOT_PRECISION",
            "AI_Is_Precision": False,
            "AI_Confidence": "HIGH",
            "AI_Reason": conflict,
            "Product_Intent_Fit": "HARD_CONFLICT",
            "Conflicting_Product_Attributes": conflict,
            "Supporting_Evidence": dict(supporting_evidence or {}),
        }
    explicit_attributes = intent.get("Attributes")
    if explicit_attributes not in (None, "", DATA_NOT_AVAILABLE) and profile.get("Core_Attributes") == DATA_NOT_AVAILABLE:
        return {
            "AI_Classification": "REVIEW_REQUIRED",
            "AI_Is_Precision": None,
            "AI_Confidence": "LOW",
            "AI_Reason": "关键属性未能从产品资料确认，不能假设满足",
            "Product_Intent_Fit": "UNKNOWN_PRODUCT_SUPPORT",
            "Supporting_Evidence": dict(supporting_evidence or {}),
        }
    specificity = _query_specificity(profile, intent, keyword)
    if not specificity["ok"]:
        return {
            "AI_Classification": "REVIEW_REQUIRED",
            "AI_Is_Precision": None,
            "AI_Confidence": "LOW",
            "AI_Reason": specificity["reason"],
            "Product_Intent_Fit": "INSUFFICIENT_QUERY_SPECIFICITY",
            "Supporting_Evidence": dict(supporting_evidence or {}),
        }
    compatible = profile.get("Compatible_Search_Intents")
    intent_core = intent.get("Core_Intent")
    matched = _meaningful_token_overlap(intent_core, compatible)
    mode = specificity.get("search_mode")
    if mode == "BROAD_GIFT":
        matched = False
        core_tokens = set(_query_tokens(intent_core)) - _GENERIC_QUERY_TOKENS - _QUERY_STOPWORDS - _OCCASION_QUERY_TOKENS
        if not core_tokens and set(_query_tokens(intent_core)) & {"gift", "gifts", "present", "presents"}:
            return {
                "AI_Classification": "NOT_PRECISION",
                "AI_Is_Precision": False,
                "AI_Confidence": "HIGH",
                "AI_Reason": "只有泛礼物词，没有足够购买对象或商品约束",
                "Product_Intent_Fit": "NO_PRODUCT_INTENT",
                "Supporting_Evidence": dict(supporting_evidence or {}),
            }
    relationships = set(specificity.get("matched_tokens") or []) & _RELATIONSHIP_INTENT_TOKENS
    profile_relationship = _profile_relationship_values(profile)
    relationship_fit = bool(relationships and _relationship_fit(relationships, profile_relationship))
    # Gift-led relationship intent is a CORE FIT when the product's confirmed
    # reason to buy is that relationship, even without a figurine/statue token.
    if mode in {"GIFT_LED", "RELATIONSHIP_ONLY"} and relationship_fit and gift_driver_active:
        matched = True
    if mode == "PRODUCT_LED" and specificity["matched_tokens"]:
        matched = matched or bool(specificity["matched_tokens"])
    # When the caller has supplied a complete core intent, an unrelated
    # recipient/function overlap must not promote the keyword.  Dimension-only
    # matching is reserved for intents whose core expression is absent.
    if not matched and not intent_core:
        for field in ("Recipient", "Relationship", "Core_Functions", "Use_Cases", "Purchase_Occasions"):
            if _semantic_overlap(intent.get(field), profile.get(field)):
                matched = True
                break
    if matched:
        # Benchmark organic rank is a reality check only.  It never vetoes or
        # promotes a semantic judgment.
        return {
            "AI_Classification": "PRECISION",
            "AI_Is_Precision": True,
            "AI_Confidence": "HIGH",
            "AI_Reason": f"{specificity['reason']}；当前产品与该购买意图属于CORE FIT",
            "Product_Intent_Fit": "CORE_FIT",
            "Matched_Product_Attributes": "Product–Search Intent Fit",
            "Supporting_Evidence": dict(supporting_evidence or {}),
        }
    if specificity.get("core_fit") == "CAN_SERVE":
        return {
            "AI_Classification": "REVIEW_REQUIRED",
            "AI_Is_Precision": None,
            "AI_Confidence": "MEDIUM",
            "AI_Reason": f"{specificity['reason']}；当前产品最多属于CAN SERVE，不足以直接判定精准",
            "Product_Intent_Fit": "CAN_SERVE",
            "Supporting_Evidence": dict(supporting_evidence or {}),
        }
    return {
        "AI_Classification": "REVIEW_REQUIRED",
        "AI_Is_Precision": None,
        "AI_Confidence": "LOW",
        "AI_Reason": "产品语义画像与搜索意图的核心匹配仍需人工/AI复核",
        "Product_Intent_Fit": "INSUFFICIENT_SEMANTIC_EVIDENCE",
        "Supporting_Evidence": dict(supporting_evidence or {}),
    }


def evaluate_product_search_intent_fit(
    product_profile: Mapping[str, Any] | None,
    keyword_intent: Mapping[str, Any] | None,
    *,
    keyword: str | None = None,
    supporting_evidence: Mapping[str, Any] | None = None,
    purchase_driver: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate intent and attach adaptive Purchase Driver evidence.

    The existing conservative evaluator remains the decision core.  This
    wrapper adds product-level driver evidence and a qualitative Decision
    Challenge without changing the formal CSV contract.
    """
    profile = build_product_semantic_profile(product_profile)
    intent = keyword_intent if isinstance(keyword_intent, Mapping) else {}
    query = keyword or str(intent.get("Core_Intent") or "")
    driver = dict(purchase_driver) if isinstance(purchase_driver, Mapping) else build_product_purchase_driver({**profile, **(product_profile or {})})
    gift_driver_active = driver.get("PrimaryPurchaseDriver") == "GIFT_EMOTIONAL" or (
        driver.get("PrimaryPurchaseDriver") == "HYBRID" and "GIFT_EMOTIONAL" in set(driver.get("SecondaryPurchaseDrivers") or ())
    )
    specificity = _query_specificity(profile, intent, query)
    conflict = _hard_conflict(profile, intent) or _lexical_hard_modifier_conflict(profile, query)
    evidence = _purchase_driver_evidence(profile, intent, query, specificity, purchase_driver=driver)
    result = _evaluate_product_search_intent_fit_core(
        product_profile, keyword_intent, keyword=keyword,
        supporting_evidence=supporting_evidence,
        purchase_driver=driver,
    )
    # This helper is a validator/diagnostic only. It deliberately does not
    # assign a precision level; FinalPrecision belongs exclusively to the
    # injected model response handled by PrecisionJudgmentEngine.
    challenge = _decision_challenge(driver, specificity, evidence, conflict=conflict, initial_precision=DATA_NOT_AVAILABLE)
    final_reason = str(result.get("AI_Reason") or "").strip()
    result.update({
        "PrimaryPurchaseDriver": driver.get("PrimaryPurchaseDriver", DATA_NOT_AVAILABLE),
        "SecondaryPurchaseDrivers": driver.get("SecondaryPurchaseDrivers", []),
        "PurchaseDriverReason": driver.get("PurchaseDriverReason", DATA_NOT_AVAILABLE),
        **evidence,
        "ChallengeResult": challenge["ChallengeResult"],
        "DecisionChallenge": challenge,
        "AI_Reason": final_reason,
        "Supporting_Evidence": {**dict(supporting_evidence or {}), "PurchaseDriver": driver, **evidence, "DecisionChallenge": challenge},
    })
    return result


STRUCTURED_JUDGMENT_FIELDS = (
    "JudgmentItemId", "SearcherPrimaryIntent", "ShoppingIntentStrength",
    "PurchaseMissionConvergence", "PhysicalProductConvergence",
    "CompatibilityConvergence", "ProductMissionFit", "HardConflictType",
    "HardConflictReason", "InitialPrecision", "BenchmarkRealityAssessment",
    "ChallengeResult", "ChallengeReasonSummary", "FinalPrecision",
    "FinalPrecisionReason", "JudgmentStatus",
)


def build_current_product_profile(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Build one product Ground Truth object without deriving facts from keywords."""
    text = str(evidence.get("product_text") or "").strip()
    profile = dict(evidence.get("product_profile") or {}) if isinstance(evidence, Mapping) else {}
    profile.setdefault("ProductProfileId", evidence.get("content_sha256") or DATA_NOT_AVAILABLE)
    profile.setdefault("Product_Text_Evidence", text or DATA_NOT_AVAILABLE)
    profile.setdefault("EvidenceSource", evidence.get("text_path") or DATA_NOT_AVAILABLE)
    return profile


def build_product_profile_prompt(product_text: str) -> str:
    """Create the one-per-run Product Understanding request for the model."""
    return json.dumps({
        "phase": "PRODUCT_PROFILE",
        "product_text": product_text,
        "required_fields": list(PRODUCT_PROFILE_OUTPUT_FIELDS),
        "allowed_primary_purchase_drivers": list(PURCHASE_DRIVERS),
        "unknown_value": DATA_NOT_AVAILABLE,
        "not_applicable_value": "NOT_APPLICABLE",
        "instructions": "Use only confirmed facts in product_text; do not infer from future keywords.",
    }, ensure_ascii=False)


def validate_product_profile(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize a model-produced Product Profile.

    This is a schema/ground-truth validator only. It never derives a profile
    from keyword tokens and never assigns a precision level.
    """
    if not isinstance(raw, Mapping):
        raise ValueError(PRODUCT_PROFILE_OUTPUT_INVALID)
    source = raw.get("ProductProfile") if isinstance(raw.get("ProductProfile"), Mapping) else raw
    aliases = {
        "ProductType": "Core_Product_Type", "PhysicalProductForm": "Physical_Product_Form",
        "CoreFunctions": "Core_Functions", "TargetAudience": "Target_Customer",
        "RelationshipIntent": "Relationship_Intent", "CorePurchaseMission": "Core_Purchase_Mission",
        "PurchaseOccasions": "Purchase_Occasions", "UseCases": "Core_Use_Cases",
        "CriticalAttributes": "Core_Attributes", "InstallationMethod": "Installation_Method",
        "ExplicitExclusions": "Excluded_Product_Types", "GiftMission": "Gift_Mission",
    }
    profile: dict[str, Any] = {}
    for key, value in source.items():
        profile[aliases.get(key, key)] = value
    for field in SEMANTIC_PROFILE_FIELDS:
        value = profile.get(field)
        if value in (None, "", [], {}):
            profile[field] = DATA_NOT_AVAILABLE
    driver = str(profile.get("PrimaryPurchaseDriver") or "").strip().upper()
    if driver not in PURCHASE_DRIVERS:
        profile["PrimaryPurchaseDriver"] = DATA_NOT_AVAILABLE
    else:
        profile["PrimaryPurchaseDriver"] = driver
    secondary = profile.get("SecondaryPurchaseDrivers") or []
    if isinstance(secondary, str):
        secondary = [secondary]
    profile["SecondaryPurchaseDrivers"] = [
        str(item).strip().upper() for item in secondary
        if str(item).strip().upper() in PURCHASE_DRIVERS and str(item).strip().upper() != driver
    ]
    profile["ProductType"] = profile.get("Core_Product_Type", DATA_NOT_AVAILABLE)
    profile["CorePurchaseMission"] = profile.get("Core_Purchase_Mission", DATA_NOT_AVAILABLE)
    if any(profile.get(field) in (None, "", DATA_NOT_AVAILABLE) for field in PRODUCT_PROFILE_REQUIRED_FIELDS):
        raise ValueError(PRODUCT_PROFILE_INSUFFICIENT)
    return profile


def build_structured_product_profile(product_evidence: Mapping[str, Any], client: Callable[[str], Iterable[Mapping[str, Any]]]) -> dict[str, Any]:
    """Call the real model exactly once to understand the current product."""
    if client is None:
        raise RuntimeError(AI_PRECISION_ENGINE_UNAVAILABLE)
    text = str(product_evidence.get("product_text") or "").strip()
    try:
        response = client(build_product_profile_prompt(text))
    except Exception as exc:
        raise RuntimeError(AI_PRECISION_ENGINE_UNAVAILABLE) from exc
    if isinstance(response, Mapping):
        response = [response]
    items = list(response or [])
    if len(items) != 1:
        raise ValueError(PRODUCT_PROFILE_OUTPUT_INVALID)
    return validate_product_profile(items[0])


def build_precision_brain_prompt(product_profile: Mapping[str, Any], units: Iterable[Mapping[str, Any]], *, phase: str) -> str:
    """Create a structured business-evidence prompt for an AI adapter."""
    payload = {
        "phase": phase,
        "product_profile": dict(product_profile),
        "keywords": [{
            "JudgmentItemId": item.get("JudgmentItemId"),
            "Keyword": item.get("词") or item.get("Keyword"),
            "KeywordCn": item.get("中文") or item.get("KeywordCn"),
            "BenchmarkRealityEvidence": item.get("Benchmark_Reality_Evidence") if phase == "B" else "HIDDEN_IN_PHASE_A",
        } for item in units],
        "required_fields": list(STRUCTURED_JUDGMENT_FIELDS),
        "final_precision_levels": list(PRECISION_LEVELS),
        "judgment_statuses": sorted(JUDGMENT_STATUSES),
    }
    return json.dumps(payload, ensure_ascii=False)


def validate_structured_judgments(judgments: Iterable[Mapping[str, Any]], expected_ids: Iterable[str], *, phase: str = "A") -> dict[str, dict[str, Any]]:
    """Validate typed Brain output and join by stable JudgmentItemId."""
    expected = {str(item).strip() for item in expected_ids}
    result: dict[str, dict[str, Any]] = {}
    for raw in judgments:
        if not isinstance(raw, Mapping):
            raise ValueError("STRUCTURED_JUDGMENT_INVALID")
        item_id = str(raw.get("JudgmentItemId") or "").strip()
        if not item_id or item_id not in expected or item_id in result:
            raise ValueError("STRUCTURED_JUDGMENT_ID_INVALID")
        if phase == "B":
            assessment = str(raw.get("BenchmarkRealityAssessment") or "").strip().upper()
            if assessment not in {"SUPPORTS", "WEAKLY_SUPPORTS", "NEUTRAL", "CONTRADICTS", "INSUFFICIENT"}:
                raise ValueError("STRUCTURED_BENCHMARK_ASSESSMENT_INVALID")
        else:
            final = _precision_level(raw.get("FinalPrecision"))
            status = str(raw.get("JudgmentStatus") or "").strip().upper()
            challenge = str(raw.get("ChallengeResult") or "").strip()
            if status not in JUDGMENT_STATUSES:
                raise ValueError("STRUCTURED_JUDGMENT_SCHEMA_INVALID")
            if (status == "SUCCESS" and final == PRECISION_LEVEL_NOT_AVAILABLE) or (status in {"REVIEW_REQUIRED", "FAILED"} and final != PRECISION_LEVEL_NOT_AVAILABLE):
                raise ValueError("STRUCTURED_JUDGMENT_SCHEMA_INVALID")
            if challenge not in {"CONFIRMED", "DOWNGRADED", "UPGRADED", "RECONSIDERED_NO_CHANGE", DATA_NOT_AVAILABLE}:
                raise ValueError("STRUCTURED_JUDGMENT_SCHEMA_INVALID")
            if not _specific_reason(raw.get("FinalPrecisionReason") or raw.get("精准原因")):
                raise ValueError("STRUCTURED_JUDGMENT_REASON_MISSING")
        result[item_id] = dict(raw)
    if set(result) != expected:
        raise ValueError("STRUCTURED_JUDGMENT_COVERAGE_FAILED")
    return result


def _local_precision_brain_judgment(unit: Mapping[str, Any], product_profile: Mapping[str, Any], driver: Mapping[str, Any]) -> dict[str, Any]:
    """Disabled: 602 requires a real AI judgment provider."""
    raise RuntimeError(AI_PRECISION_ENGINE_UNAVAILABLE)


class PrecisionJudgmentEngine:
    """Run the two-stage structured Precision Brain over unique keywords."""

    def __init__(self, client: Callable[[str], Iterable[Mapping[str, Any]]] | None = None, *, batch_size: int | None = None):
        self.client = client
        self.batch_size = batch_size
        self.calls = 0
        self.external_model_calls = 0
        self.retry_count = 0

    def _call(self, prompt: str, units: list[Mapping[str, Any]], product_profile: Mapping[str, Any], driver: Mapping[str, Any], phase: str) -> list[Mapping[str, Any]]:
        self.calls += 1
        if self.client is not None:
            self.external_model_calls += 1
            return list(self.client(prompt))
        raise RuntimeError(AI_PRECISION_ENGINE_UNAVAILABLE)

    def judge(self, units: list[Mapping[str, Any]], product_profile: Mapping[str, Any], driver: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        if not units:
            return {}
        batch_size = self.batch_size or max(1, min(32, 32000 // max(800, len(str(product_profile)) + 120)))
        output: dict[str, Mapping[str, Any]] = {}
        for start in range(0, len(units), batch_size):
            batch = units[start:start + batch_size]
            ids = [str(item["JudgmentItemId"]) for item in batch]
            try:
                phase_a = self._call(build_precision_brain_prompt(product_profile, batch, phase="A"), batch, product_profile, driver, "A")
            except Exception:
                for item_id in ids:
                    output[item_id] = {
                        "JudgmentItemId": item_id,
                        "FinalPrecision": DATA_NOT_AVAILABLE,
                        "FinalPrecisionReason": "Phase A真实AI判断失败，必须人工复核，未生成精准度",
                        "JudgmentStatus": "FAILED",
                        "ChallengeResult": DATA_NOT_AVAILABLE,
                    }
                continue
            try:
                validated = validate_structured_judgments(phase_a, ids)
            except ValueError:
                smaller = max(1, len(batch) // 2)
                if len(batch) > smaller:
                    self.retry_count += 1
                    nested = self.__class__(self.client, batch_size=smaller)
                    nested_result = nested.judge(batch, product_profile, driver)
                    self.calls += nested.calls
                    self.external_model_calls += nested.external_model_calls
                    self.retry_count += nested.retry_count
                    output.update(nested_result)
                    continue
                failed_id = ids[0]
                validated = {failed_id: {"JudgmentItemId": failed_id, "FinalPrecision": DATA_NOT_AVAILABLE,
                    "FinalPrecisionReason": "结构化AI判断重试后仍失败，必须人工复核，未生成语义等级",
                    "JudgmentStatus": "FAILED", "ChallengeResult": DATA_NOT_AVAILABLE}}
                output[failed_id] = validated[failed_id]
                continue
            try:
                phase_b = self._call(build_precision_brain_prompt(product_profile, batch, phase="B"), batch, product_profile, driver, "B")
            except Exception:
                phase_b = []
            try:
                final = validate_structured_judgments(phase_b, ids, phase="B")
            except ValueError:
                # A missing/invalid Phase B response means the two-phase
                # judgment is incomplete; never publish the Phase A level as
                # if the final AI decision had succeeded.
                for item_id in ids:
                    failed = dict(validated[item_id])
                    failed.update({
                        "BenchmarkRealityAssessment": "INSUFFICIENT",
                        "JudgmentStatus": "REVIEW_REQUIRED",
                        "FinalPrecision": DATA_NOT_AVAILABLE,
                        "FinalPrecisionReason": "Phase B真实AI判断失败，必须人工复核，未生成精准度",
                        "ChallengeResult": DATA_NOT_AVAILABLE,
                    })
                    output[item_id] = failed
                continue
            for item_id, judgment in final.items():
                # Phase A semantic decision is authoritative; Phase B only adds Reality Assessment.
                merged = dict(validated[item_id])
                merged["BenchmarkRealityAssessment"] = judgment.get("BenchmarkRealityAssessment", "INSUFFICIENT")
                output[item_id] = merged
        return output


def run_precision_brain(
    observation_rows: Iterable[Mapping[str, Any]],
    product_evidence: Mapping[str, Any],
    *,
    client: Callable[[str], Iterable[Mapping[str, Any]]] | None = None,
    batch_size: int | None = None,
) -> dict[str, Any]:
    """Build unique units, call the structured Brain, and return canonical decisions."""
    rows = list(observation_rows)
    units = build_keyword_judgment_units(rows)
    if client is None:
        raise RuntimeError(AI_PRECISION_ENGINE_UNAVAILABLE)
    base_profile = build_current_product_profile(product_evidence)
    profile = {**base_profile, **build_structured_product_profile(product_evidence, client)}
    profile_call_count = 1
    driver = build_product_purchase_driver(profile)
    engine = PrecisionJudgmentEngine(client, batch_size=batch_size)
    judgments = engine.judge(units, profile, driver)
    by_canonical: dict[str, Mapping[str, Any]] = {}
    for unit in units:
        judgment = dict(judgments[unit["JudgmentItemId"]])
        # The projection layer uses the existing CSV contract; these fields
        # remain in the internal trace and are never silently treated as labels.
        judgment["精准度"] = judgment["FinalPrecision"]
        judgment["精准原因"] = judgment["FinalPrecisionReason"]
        judgment["JudgmentStatus"] = judgment.get("JudgmentStatus", "SUCCESS")
        by_canonical[unit["Canonical_Keyword"]] = judgment
    return {"decisions": by_canonical, "keyword_units": units, "judgments": judgments,
            "purchase_driver": driver, "product_profile": profile, "ai_call_count": engine.calls,
            "ExecutionMode": "EXTERNAL_AGENT",
            "ExternalModelCallCount": engine.external_model_calls,
            "ProductProfileModelCallCount": profile_call_count,
            "PrecisionModelCallCount": engine.external_model_calls,
            "SuccessfulUniqueJudgmentCount": sum(1 for item in judgments.values() if item.get("JudgmentStatus") == "SUCCESS"),
            "ReviewRequiredCount": sum(1 for item in judgments.values() if item.get("JudgmentStatus") == "REVIEW_REQUIRED"),
            "FailedJudgmentCount": sum(1 for item in judgments.values() if item.get("JudgmentStatus") == "FAILED"),
            "RetryCount": engine.retry_count,
            "LocalBrainFallback": False}


def run_precision_brain_regression(
    product_profile: Mapping[str, Any] | None,
    golden_cases: Iterable[Mapping[str, Any]],
    *,
    client: Callable[[str], Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Run Golden Cases through the injected real Brain; never the local judge."""
    if client is None:
        raise RuntimeError(AI_PRECISION_ENGINE_UNAVAILABLE)
    cases = list(golden_cases)
    rows = []
    for index, case in enumerate(cases):
        keyword = str(case.get("Keyword") or case.get("keyword") or "").strip()
        expected = str(case.get("ExpectedPrecision") or case.get("期望等级") or "").strip()
        item_id = f"GOLDEN-{index + 1}"
        prompt = build_precision_brain_prompt({**(product_profile or {})}, [{"JudgmentItemId": item_id, "词": keyword}], phase="A")
        raw = validate_structured_judgments(list(client(prompt)), [item_id], phase="A")[item_id]
        predicted = str(raw.get("FinalPrecision") or "").strip()
        case_type = str(case.get("CaseType") or "").strip()
        rows.append({
            "Keyword": keyword,
            "CaseType": case_type,
            "PrimaryPurchaseDriver": (product_profile or {}).get("PrimaryPurchaseDriver", DATA_NOT_AVAILABLE),
            "ExpectedPrecision": expected,
            "PredictedPrecision": predicted,
            "ExactMatch": predicted == expected,
            "GiftMissionFit": raw.get("GiftMissionFit", DATA_NOT_AVAILABLE),
            "PurchaseMissionFit": raw.get("PurchaseMissionFit", raw.get("GiftMissionFit", DATA_NOT_AVAILABLE)),
            "PhysicalProductConvergence": raw.get("PhysicalProductConvergence", DATA_NOT_AVAILABLE),
            "PurchaseMissionConvergence": raw.get("PurchaseMissionConvergence", DATA_NOT_AVAILABLE),
            "ChallengeResult": raw.get("ChallengeResult", DATA_NOT_AVAILABLE),
        })
    high = {"高度精准"}
    expected_high = [row for row in rows if row["ExpectedPrecision"] in high]
    predicted_high = [row for row in rows if row["PredictedPrecision"] in high]
    tp = sum(row["PredictedPrecision"] in high and row["ExpectedPrecision"] in high for row in rows)
    gift_high = [row for row in expected_high if row["CaseType"] == "GIFT_HIGH_MISSION_FIT"]
    gift_tp = sum(row["PredictedPrecision"] in high for row in gift_high)
    broad = [row for row in rows if row["CaseType"] == "GIFT_BROAD_INTENT"]
    broad_fp = sum(row["PredictedPrecision"] in high for row in broad)
    false_high = sum(row["PredictedPrecision"] in high and row["ExpectedPrecision"] not in high for row in rows)
    compression = [row["Keyword"] for row in expected_high if row["PredictedPrecision"] != "高度精准"]
    return {
        "ExactPrecisionMatch": sum(row["ExactMatch"] for row in rows),
        "MismatchCount": sum(not row["ExactMatch"] for row in rows),
        "FalseHighPrecision": false_high,
        "HighPrecisionRecall": (tp / len(expected_high)) if expected_high else None,
        "GiftHighMissionFitRecall": (gift_tp / len(gift_high)) if gift_high else None,
        "FalseHighPrecisionRate": (false_high / len(predicted_high)) if predicted_high else 0.0,
        "BroadGiftFalseHighPrecisionRate": (broad_fp / len(broad)) if broad else 0.0,
        "GradeCompression": compression,
        "Cases": rows,
    }


def select_paths(mode: str | None = None) -> tuple[str, ...]:
    """Resolve the default or explicit Chinese short-command suffix."""
    normalized = str(mode or "").strip().lower()
    if not normalized:
        return ("ai", "high_precision")
    if normalized in {"自动分类精准词", "AI精准词", "ai", "auto", "全部判断"}:
        return ("ai", "high_precision")
    if normalized in {"高度精准", "AI高度精准词", "high", "high_precision"}:
        return ("high_precision",)
    if normalized in {"手动分类精准词", "manual"}:
        raise ValueError("6-0-2_MANUAL_PRECISION_OUTPUT_REMOVED")
    raise ValueError(f"unsupported 6-0-2 precision path: {mode}")


def _raw(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("raw_fields")
    return value if isinstance(value, Mapping) else row


def _keyword(row: Mapping[str, Any]) -> str:
    raw = _raw(row)
    return str(row.get("keyword") or raw.get("Keyword") or "").strip()


def _record_id(row: Mapping[str, Any]) -> str:
    """Return only a schema-confirmed stable ERP record identity.

    PickPwKView currently documents neither ``Id`` nor ``KwId`` as a stable
    writable identity.  Raw columns therefore remain evidence only and are
    never guessed into the public CSV contract.
    """
    status = str(row.get("record_id_status") or "").strip()
    if status == ERP_KEYWORD_RECORD_ID_AMBIGUOUS:
        return ERP_KEYWORD_RECORD_ID_AMBIGUOUS
    if status != "DOCUMENTED_STABLE":
        return ERP_KEYWORD_RECORD_ID_UNCONFIRMED
    value = row.get("record_id")
    return str(value).strip() if value not in (None, "") else ERP_KEYWORD_RECORD_ID_UNCONFIRMED


def _semantics(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("field_semantics")
    return value if isinstance(value, Mapping) else {}


def _documented_quality(row: Mapping[str, Any]) -> dict[str, Any]:
    raw = _raw(row)
    semantics = _semantics(row)
    values: dict[str, Any] = {}
    for field in QUALITY_FIELDS:
        definition = semantics.get(field)
        if isinstance(definition, Mapping) and definition.get("status") == "DOCUMENTED":
            values[field] = row.get(field, raw.get(field))
    return values


def _identity(row: Mapping[str, Any], product_code: str | None = None) -> dict[str, Any]:
    raw = _raw(row)
    return {
        "Product_Code": product_code or row.get("product_code"),
        "ERP_ProId": row.get("erp_pro_id") or raw.get("ProId"),
        "Keyword": _keyword(row),
        "KeywordCn": raw.get("KeywordCn"),
    }


def _filename_timestamp(path: Path) -> str | None:
    match = re.search(r"_(\d{8}_\d{6})\.csv$", path.name, re.I)
    return match.group(1) if match else None


def resolve_benchmark_raw_csvs(product_root: str | Path, product_code: str | None = None) -> dict[str, Any]:
    """Resolve 6-0-1 all-observation input through its current Registry/Manifest."""
    report_dir = Path(product_root).resolve() / "06_SKILL分析报告" / BENCHMARK_RAW_OUTPUT_DIR
    current = resolve_latest_valid_data(report_dir)
    if current.get("status") != "LATEST_VALID_DATA":
        return _resolve_601_by_filename_timestamp(product_root)
    stamp = str(current.get("run_timestamp") or "")
    registry = current.get("registry") or {}
    manifest = {}
    manifest_path = report_dir / "_system" / "manifests" / f"6-0-1_RunPackage_{current.get('run_timestamp')}.json"
    if manifest_path.is_file():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            if isinstance(payload, dict):
                manifest = payload
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                    "invalid_files": [{"reason": "INPUT_MANIFEST_INVALID"}]}
    if manifest and (str(manifest.get("RUN_TIMESTAMP") or "") != stamp or str(manifest.get("Run_Status") or "").upper() not in {"FULL_SUCCESS", "VALID"}):
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                "invalid_files": [{"reason": "INPUT_MANIFEST_NOT_VALID"}]}
    identities = registry.get("Report_Identities") or manifest.get("Report_Identities") or []
    if identities and SIX_0_1_REPORT_IDENTITY not in identities:
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                "invalid_files": [{"reason": "REPORT_IDENTITY_MISSING"}]}
    declared = registry.get("Files") or []
    names = {Path(str(value)).name for value in declared if str(value).strip()}
    expected_stem = f"所有对标自然排名关键词_{stamp}.csv"
    data_dir = Path(current["data_dir"])
    matches = [candidate for candidate in data_dir.glob(f"6-0-1_*{expected_stem}") if candidate.is_file()]
    if len(matches) != 1:
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                "invalid_files": [{"reason": "CURRENT_ASSET_AMBIGUOUS", "file": expected_stem}]}
    path = matches[0]
    if path.name not in names and declared:
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                "invalid_files": [{"reason": "REGISTRY_FILE_NOT_DECLARED", "file": path.name}]}
    if not path.is_file():
        return {"status": BENCHMARK_RAW_NOT_FOUND, "files": [], "rows": [],
                "invalid_files": [{"reason": "CURRENT_ASSET_MISSING", "file": str(path)}]}
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = tuple(reader.fieldnames or ())
            if not set(BENCHMARK_RAW_COLUMNS).issubset(headers):
                raise ValueError("INPUT_SCHEMA_INVALID")
            source_rows = list(reader)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                "invalid_files": [{"path": str(path), "reason": str(exc)}]}
    if not source_rows:
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                "invalid_files": [{"path": str(path), "reason": "INPUT_EMPTY"}]}
    rows: list[dict[str, Any]] = []
    for source_index, raw in enumerate(source_rows):
        rows.append({
            "所属产品编号": raw.get("所属产品编号") or raw.get("产品编号"),
            "对标ASIN": raw.get("对标ASIN") or raw.get("ASIN"),
            "Id": str(raw.get("Id") or "").strip() or None,
            "词": raw.get("词"), "中文": raw.get("中文"),
            "市场容量": raw.get("市场容量"), "Keyword": str(raw.get("词") or "").strip(),
            "KeywordCn": raw.get("中文"), "SearchVolume30": raw.get("市场容量"),
            "竞争产品数": raw.get("竞争产品数"), "供需比": raw.get("供需比"),
            "自然排名": raw.get("自然排名"),
            "keyword_entity_id": str(raw.get("Id") or "").strip() or None,
            "keyword_entity_id_status": "USER_CONFIRMED_STABLE_ACROSS_PROID",
            "record_id": None, "record_id_status": ERP_KEYWORD_RECORD_ID_UNCONFIRMED,
            "field_semantics": {
                "SearchVolume30": {"status": "DOCUMENTED", "meaning": "30天搜索量"},
                "竞争产品数": {"status": "DOCUMENTED", "meaning": "仅透传，不参与精准判断"},
                "供需比": {"status": "DERIVED_SOURCE_VALUE", "meaning": "仅透传，不参与精准判断"},
                "自然排名": {"status": "DOCUMENTED", "meaning": "仅作Reality Evidence"},
            },
            "source_file": str(path), "source_row": source_index + 2,
            "source_type": "BENCHMARK_6_0_1_KEYWORD_OBSERVATION",
        })
    if any(not row["Id"] or not row["Keyword"] for row in rows):
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": [],
                "invalid_files": [{"path": str(path), "reason": "INPUT_SCHEMA_INVALID"}]}
    return {"status": "BENCHMARK_RAW_READY", "files": [str(path)], "rows": rows,
            "invalid_files": [], "source_schema": list(BENCHMARK_RAW_COLUMNS),
            "run_timestamp": stamp, "input_resolution_method": "REGISTRY_DATA_LATEST_VALID",
            "input_metadata": manifest or registry}

def _product_code_from_root(product_root: str | Path) -> str:
    """Return the exact Product_Code from this already-resolved Product Root."""
    archive = Path(product_root) / "01_产品档案.md"
    try:
        for line in archive.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("产品编号："):
                return line.split("：", 1)[1].strip()
    except OSError:
        pass
    # Legacy Product Root callers did not pass a Product_Code. The directory
    # resolver remains root-scoped; the caller-supplied code is used where
    # available through resolve_latest_601_keyword_output below.
    return ""


def resolve_latest_601_keyword_output(product_root: str | Path, product_code: str | None = None) -> dict[str, Any]:
    """Resolve one latest-valid 6-0-1 asset; never fall back to ERP/SQL."""
    resolved = resolve_benchmark_raw_csvs(product_root, product_code=product_code)
    if resolved.get("status") != "BENCHMARK_RAW_READY":
        resolved = _resolve_601_by_filename_timestamp(product_root)
    files = list(resolved.get("files") or [])
    if resolved.get("status") != "BENCHMARK_RAW_READY" or not files:
        status = (SIX_0_1_KEYWORD_OUTPUT_NOT_FOUND
                  if resolved.get("status") == BENCHMARK_RAW_NOT_FOUND
                  else resolved.get("status") or SIX_0_1_KEYWORD_OUTPUT_NOT_FOUND)
        return {
            "status": status,
            "file": None,
            "rows": [],
            "invalid_files": list(resolved.get("invalid_files") or []),
            "source_schema": list(BENCHMARK_RAW_COLUMNS),
        }
    latest = files[0]
    rows = list(resolved.get("rows") or ())
    return {
        "status": SIX_0_1_KEYWORD_OUTPUT_READY,
        "file": str(latest),
        "rows": rows,
        "invalid_files": list(resolved.get("invalid_files") or []),
        "source_schema": list(BENCHMARK_RAW_COLUMNS),
        "run_id": resolved.get("run_timestamp"),
        "run_timestamp": resolved.get("run_timestamp"),
        "generated_at": None,
        "input_resolution_method": resolved.get("input_resolution_method"),
        "input_metadata": resolved.get("input_metadata") or {},
    }


def _resolve_601_by_filename_timestamp(product_root: str | Path) -> dict[str, Any]:
    """Minimal analysis handoff: newest exact 6-0-1 filename, no package gate."""
    data_dir = Path(product_root).resolve() / "06_SKILL分析报告" / BENCHMARK_RAW_OUTPUT_DIR
    paths = [p for p in data_dir.glob("6-0-1_*所有对标自然排名关键词_*.csv") if p.is_file() and _filename_timestamp(p)]
    if not paths:
        return {"status": SIX_0_1_KEYWORD_INPUT_NOT_FOUND, "files": [], "rows": []}
    path = max(paths, key=lambda p: _filename_timestamp(p) or "")
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not set(BENCHMARK_RAW_COLUMNS).issubset(reader.fieldnames or ()):
                return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": []}
            raw_rows = list(reader)
    except (OSError, UnicodeError, csv.Error):
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": []}
    if not raw_rows:
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": []}
    rows = []
    for index, raw in enumerate(raw_rows, start=2):
        keyword = str(raw.get("词") or "").strip()
        record = {"所属产品编号": raw.get("所属产品编号") or raw.get("产品编号"), "对标ASIN": raw.get("对标ASIN") or raw.get("ASIN"), "Id": str(raw.get("Id") or "").strip() or None, "词": raw.get("词"), "中文": raw.get("中文"), "市场容量": raw.get("市场容量"), "Keyword": keyword, "KeywordCn": raw.get("中文"), "SearchVolume30": raw.get("市场容量"), "竞争产品数": raw.get("竞争产品数"), "供需比": raw.get("供需比"), "自然排名": raw.get("自然排名"), "source_file": str(path), "source_row": index, "source_type": "BENCHMARK_6_0_1_KEYWORD_OBSERVATION"}
        rows.append(record)
    if any(not row.get("Id") or not row.get("Keyword") for row in rows):
        return {"status": BENCHMARK_RAW_SCHEMA_INVALID, "files": [], "rows": []}
    stamp = _filename_timestamp(path)
    return {"status": "BENCHMARK_RAW_READY", "files": [str(path)], "rows": rows, "source_schema": list(BENCHMARK_RAW_COLUMNS), "run_timestamp": stamp, "input_resolution_method": "FILENAME_TIMESTAMP_MAX", "input_metadata": {}}


def build_dual_views_from_601_output(
    product_root: str | Path,
    *,
    product_code: str,
) -> dict[str, Any]:
    """Build the 6-0-2 input views from the latest 6-0-1 output only.

    The 6-0-1 CSV contains Benchmark × Keyword observations and source ``Id``.
    The AI blind view groups by Canonical Keyword once and aggregates rank
    evidence; final output later expands that judgment back to all observations.
    """
    resolved = resolve_latest_601_keyword_output(product_root, product_code=product_code)
    if resolved.get("status") != SIX_0_1_KEYWORD_OUTPUT_READY:
        return {
            "status": resolved.get("status") or SIX_0_1_KEYWORD_OUTPUT_NOT_FOUND,
            "source_file": resolved.get("file"),
            "source_schema": resolved.get("source_schema"),
            "source_row_count": 0,
            "manual_rows": [],
            "ai_blind_rows": [],
            "manual_status": "MANUAL_PRECISION_OUTPUT_REMOVED",
            "invalid_files": resolved.get("invalid_files") or [],
        }
    rows = list(resolved.get("rows") or [])
    blind_rows = build_keyword_judgment_units(rows)
    for row in blind_rows:
        row["Source"] = "SIX_0_1_KEYWORD_OUTPUT"
        row["ERP_ProId"] = None
        row["Current_ERP_ProId"] = None
    return {
        "status": "READY",
        "source_file": resolved.get("file"),
        "source_schema": resolved.get("source_schema"),
        "source_row_count": len(rows),
        "unique_keyword_count": len(blind_rows),
        "manual_rows": [],
        "ai_blind_rows": blind_rows,
        "manual_status": "MANUAL_PRECISION_OUTPUT_REMOVED",
        "invalid_files": resolved.get("invalid_files") or [],
    }


def benchmark_raw_csv_as_results(
    resolved: Mapping[str, Any],
    *,
    benchmark_erp_pro_ids: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    """Adapt resolved 6-0-1 rows to the internal Benchmark Evidence shape."""
    if resolved.get("status") != "BENCHMARK_RAW_READY":
        return []
    configured = [str(value).strip() for value in (benchmark_erp_pro_ids or ()) if str(value).strip()]
    rows_by_file: dict[str, list[Mapping[str, Any]]] = {}
    for row in resolved.get("rows") or ():
        rows_by_file.setdefault(str(row.get("source_file") or ""), []).append(row)
    files = list(resolved.get("files") or rows_by_file)
    results: list[dict[str, Any]] = []
    for index, path in enumerate(files):
        # Keep this legacy candidate adapter aligned with the all-observation
        # source by aggregating Reality Evidence per Canonical Keyword.
        pro_id = configured[index] if len(configured) == len(files) else DATA_NOT_AVAILABLE
        file_rows = rows_by_file.get(str(path), [])
        observations_by_keyword = _benchmark_observation_groups(file_rows)
        keyword_rows = []
        for source_index, unit in enumerate(build_keyword_judgment_units(file_rows)):
            observations = observations_by_keyword[unit["Canonical_Keyword"]]
            first = observations[0]
            reality = unit["Benchmark_Reality_Evidence"]
            keyword_rows.append({
                "keyword": unit["Keyword"],
                "KeywordCn": unit["KeywordCn"],
                "keyword_entity_id": unit["Id"],
                "keyword_entity_id_status": "USER_CONFIRMED_STABLE_ACROSS_PROID",
                "record_id": None,
                "record_id_status": ERP_KEYWORD_RECORD_ID_UNCONFIRMED,
                "source_file": str(path),
                "source_row": first.get("source_row", source_index + 2),
                "source_type": "BENCHMARK_6_0_1_ALL_OBSERVATIONS",
                "Benchmark_Observation_Count": reality["Benchmark_Observation_Count"],
                "Benchmark_Coverage_Count": reality["Benchmark_Coverage_Count"],
                "Benchmark_Organic_Rank_Count": reality["Organic_Rank_Count"],
                "Best_Benchmark_Organic_Rank": reality["Best_Benchmark_Organic_Rank"],
                "Median_Benchmark_Organic_Rank": reality["Median_Benchmark_Organic_Rank"],
                "field_semantics": first.get("field_semantics") or {},
                "raw_fields": {
                    "Keyword": unit["Keyword"],
                    "KeywordCn": unit["KeywordCn"],
                    "KwId": unit["Id"],
                    "SearchVolume30": first.get("市场容量"),
                    "AsinQuantity": first.get("竞争产品数"),
                },
            })
        results.append({
            "status": "BENCHMARK_EVIDENCE_READY",
            "erp_pro_id": pro_id,
            "source_type": "BENCHMARK_6_0_1_ALL_OBSERVATIONS",
            "source_file": str(path),
            "benchmark_count": resolved.get("benchmark_count"),
            "benchmark_codes": resolved.get("benchmark_codes") or [],
            "benchmark_erp_pro_ids": resolved.get("benchmark_erp_pro_ids") or [],
            "rows": keyword_rows,
        })
    return results


def _join_key(item: Mapping[str, Any]) -> tuple[str, str, str]:
    """Use the contractual Product_Code + ERP_ProId + Keyword join key."""
    return (
        str(item.get("Product_Code") or item.get("product_code") or "").strip(),
        str(item.get("ERP_ProId") or item.get("erp_pro_id") or "").strip(),
        str(item.get("Keyword") or item.get("keyword") or "").strip().lower(),
    )


def build_manual_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    product_code: str,
    erp_pro_id: Any,
) -> list[dict[str, Any]]:
    """Build the ERP/manual path using only the complete Tags label.

    IsExact is intentionally ignored.  Empty Keyword rows are excluded and
    source values are retained rather than rewritten.
    """
    output: list[dict[str, Any]] = []
    for row in rows:
        raw = _raw(row)
        row_pro_id = raw.get("ProId") or row.get("erp_pro_id")
        if row_pro_id is not None and str(row_pro_id) != str(erp_pro_id):
            continue
        keyword = _keyword(row)
        if not keyword or PRECISION_TAG not in str(raw.get("Tags") or ""):
            continue
        item = _identity(row, product_code)
        item["ERP_ProId"] = erp_pro_id
        item.update(_documented_quality(row))
        item.update({
            "Source": "ERP_MANUAL_TAG",
            "Manual_Is_Precision": "TRUE",
            "Manual_Precision_Label": "PRECISION",
            "Manual_Reason": f"Tags contains {PRECISION_TAG}",
            "record_id": row.get("record_id"),
            "record_id_status": row.get("record_id_status", ERP_KEYWORD_RECORD_ID_UNCONFIRMED),
        })
        output.append(item)
    return output


def build_ai_blind_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    product_code: str,
    erp_pro_id: Any,
) -> list[dict[str, Any]]:
    """Prepare all valid keywords for independent AI classification.

    The returned view contains no Tags, IsExact, or raw_fields.  This makes the
    human label unavailable to the model while retaining documented quality
    evidence and product scope.
    """
    output: list[dict[str, Any]] = []
    for row in rows:
        raw = _raw(row)
        row_pro_id = raw.get("ProId") or row.get("erp_pro_id")
        if row_pro_id is not None and str(row_pro_id) != str(erp_pro_id):
            continue
        keyword = _keyword(row)
        if not keyword:
            continue
        item = _identity(row, product_code)
        entity_id = row.get("keyword_entity_id")
        if entity_id not in (None, ""):
            # Preserve the user-confirmed keyword entity key so one decision
            # can be joined back to the unique 6-0-1 pool row. This is not a
            # writable PickPwK record id.
            item["Id"] = str(entity_id).strip()
            item["keyword_entity_id"] = str(entity_id).strip()
            item["keyword_entity_id_status"] = row.get("keyword_entity_id_status")
            item["Benchmark_Reality_Evidence"] = {
                "对标覆盖数": row.get("对标覆盖数", DATA_NOT_AVAILABLE),
                "最佳自然排名": row.get("最佳自然排名", DATA_NOT_AVAILABLE),
                "自然排名中位数": row.get("自然排名中位数", DATA_NOT_AVAILABLE),
            }
        item["ERP_ProId"] = erp_pro_id
        item["AI_Evidence"] = _documented_quality(row)
        item["record_id_status"] = row.get("record_id_status", ERP_KEYWORD_RECORD_ID_UNCONFIRMED)
        item["record_id"] = row.get("record_id")
        item["Source"] = "ERP_AI_BLIND_INPUT"
        output.append(item)
    return output


def choose_keyword_source_mode(
    own_rows: Iterable[Mapping[str, Any]],
    benchmark_results: Iterable[Mapping[str, Any]],
    *,
    own_keywords_sufficient: bool | None = None,
    own_intent_coverage_sufficient: bool | None = None,
) -> str:
    """Choose the candidate-pool mode without a fixed row-count threshold.

    Coverage sufficiency is a runtime evidence judgment.  ``None`` is kept
    conservative and does not silently activate Benchmark expansion when an
    own pool exists; explicit ``False`` activates the documented fallback.
    """
    own_count = sum(1 for row in own_rows if _normalized_keyword(_keyword(row)))
    benchmark_count = sum(
        1 for result in benchmark_results for row in (result.get("rows") or ())
        if _normalized_keyword(row.get("keyword") or _raw(row).get("Keyword"))
    )
    if own_count == 0:
        return BENCHMARK_FALLBACK if benchmark_count else OWN_ONLY
    if own_keywords_sufficient is False or own_intent_coverage_sufficient is False:
        return OWN_PLUS_BENCHMARK if benchmark_count else OWN_ONLY
    return OWN_ONLY


def build_keyword_candidate_pool(
    own_rows: Iterable[Mapping[str, Any]],
    benchmark_results: Iterable[Mapping[str, Any]] | None = None,
    *,
    product_code: str,
    erp_pro_id: Any,
    benchmark_erp_pro_ids: Iterable[Any] | None = None,
    benchmark_raw_input: Mapping[str, Any] | None = None,
    own_keywords_sufficient: bool | None = None,
    own_intent_coverage_sufficient: bool | None = None,
) -> dict[str, Any]:
    """Build a deduplicated, AI-safe candidate pool for the current product.

    New runs should pass ``benchmark_raw_input`` from
    :func:`resolve_benchmark_raw_csvs`; ``benchmark_results`` remains an
    internal adapter shape for compatibility and must not be populated by a
    second Benchmark PickPwKView query.
    Benchmark rows are candidates only. Their Tags/IsExact/raw fields are
    never used as classification labels. A documented stable Record ID from
    either the current product or an explicitly bound Benchmark is retained
    for downstream ERP synchronization; the record's source ProId remains
    separate from Current_ERP_ProId.
    """
    own = list(own_rows)
    if benchmark_raw_input is not None:
        if benchmark_raw_input.get("status") != "BENCHMARK_RAW_READY":
            return {
                "mode": None,
                "status": benchmark_raw_input.get("status") or BENCHMARK_RAW_NOT_FOUND,
                "candidates": [],
                "unresolved_candidates": [],
                "identity_conflicts": [],
                "benchmark_evidence": {},
                "own_candidate_keywords": len({
                    _normalized_keyword(_keyword(row)) for row in own if _normalized_keyword(_keyword(row))
                }),
                "benchmark_candidate_keywords": 0,
                "deduplicated_candidate_keywords": 0,
                "candidate_record_count": 0,
            }
        benchmarks = benchmark_raw_csv_as_results(
            benchmark_raw_input,
            benchmark_erp_pro_ids=benchmark_erp_pro_ids,
        )
    else:
        benchmarks = list(benchmark_results or ())
    configured = [str(value).strip() for value in (benchmark_erp_pro_ids or ()) if str(value).strip()]
    mode = choose_keyword_source_mode(
        own, benchmarks,
        own_keywords_sufficient=own_keywords_sufficient,
        own_intent_coverage_sufficient=own_intent_coverage_sufficient,
    )
    evidence = build_benchmark_evidence(benchmarks, benchmark_erp_pro_ids=configured)
    own_by_key: dict[str, list[Mapping[str, Any]]] = {}
    for row in own:
        key = _normalized_keyword(_keyword(row))
        if key:
            own_by_key.setdefault(key, []).append(row)
    benchmark_by_key: dict[str, list[Mapping[str, Any]]] = {}
    for result in benchmarks:
        result_pro_id = str(result.get("erp_pro_id") or "").strip()
        is_all_observation_asset = result.get("source_type") == "BENCHMARK_6_0_1_ALL_OBSERVATIONS"
        if configured and result_pro_id not in configured and not is_all_observation_asset:
            continue
        for row in result.get("rows") or ():
            keyword = str(row.get("keyword") or _raw(row).get("Keyword") or "").strip()
            key = _normalized_keyword(keyword)
            if key:
                benchmark_by_key.setdefault(key, []).append(row)
    keys = set(own_by_key)
    if mode != OWN_ONLY:
        keys.update(benchmark_by_key)
    candidates: list[dict[str, Any]] = []
    unresolved_candidates: list[dict[str, Any]] = []
    identity_by_id: dict[str, str] = {}
    identity_by_entity_id: dict[str, str] = {}
    identity_conflicts: set[str] = set()
    seen_records: set[tuple[str, str]] = set()

    def append_candidate(item: dict[str, Any], *, source_pro_id: Any, key: str) -> None:
        entity_id = item.get("keyword_entity_id")
        if item.get("keyword_entity_id_status") == "USER_CONFIRMED_STABLE_ACROSS_PROID" and entity_id not in (None, ""):
            normalized_entity_id = str(entity_id).strip()
            previous_key = identity_by_entity_id.get(normalized_entity_id)
            if previous_key is not None and previous_key != key:
                identity_conflicts.add(f"KWID:{normalized_entity_id}")
                return
            identity_by_entity_id[normalized_entity_id] = key
            record_key = (f"KWID:{normalized_entity_id}", key)
            if record_key not in seen_records:
                seen_records.add(record_key)
                # Classification uses the stable keyword entity, but keeps
                # PickPwK row identity unavailable for the restricted writer.
                item["record_id"] = None
                item["record_id_status"] = ERP_KEYWORD_RECORD_ID_UNCONFIRMED
                candidates.append(item)
            return
        record_id = item.get("record_id")
        status = str(item.get("record_id_status") or ERP_KEYWORD_RECORD_ID_UNCONFIRMED)
        if status == "DOCUMENTED_STABLE" and record_id not in (None, ""):
            record_key = (str(record_id).strip(), key)
            if record_key in seen_records:
                return
            seen_records.add(record_key)
            normalized_id = str(record_id).strip()
            previous_key = identity_by_id.get(normalized_id)
            if previous_key is not None and previous_key != key:
                identity_conflicts.add(normalized_id)
            identity_by_id[normalized_id] = key
        else:
            # Unresolved source records remain auditable but are never eligible
            # for a normal six-column output or downstream write-back.
            unresolved_key = (str(source_pro_id or "").strip(), key, "UNRESOLVED")
            if unresolved_key in seen_records:
                return
            seen_records.add(unresolved_key)
            item["record_id"] = None
            item["record_id_status"] = ERP_KEYWORD_RECORD_ID_UNCONFIRMED
            unresolved_candidates.append(item)
            return
        candidates.append(item)

    for key in sorted(keys):
        own_matches = own_by_key.get(key, [])
        if own_matches:
            for row in own_matches:
                item = _identity(row, product_code)
                item["ERP_ProId"] = erp_pro_id
                item["Current_ERP_ProId"] = erp_pro_id
                item["AI_Evidence"] = _documented_quality(row)
                item["record_id"] = row.get("record_id")
                item["record_id_status"] = row.get("record_id_status", ERP_KEYWORD_RECORD_ID_UNCONFIRMED)
                item["Source"] = "OWN_ERP" if key not in benchmark_by_key else "OWN_PLUS_BENCHMARK"
                append_candidate(item, source_pro_id=erp_pro_id, key=key)
        if mode != OWN_ONLY and key in benchmark_by_key:
            for result in benchmarks:
                result_pro_id = str(result.get("erp_pro_id") or "").strip()
                is_all_observation_asset = result.get("source_type") == "BENCHMARK_6_0_1_ALL_OBSERVATIONS"
                if configured and result_pro_id not in configured and not is_all_observation_asset:
                    continue
                for row in result.get("rows") or ():
                    keyword = str(row.get("keyword") or _raw(row).get("Keyword") or "").strip()
                    if _normalized_keyword(keyword) != key:
                        continue
                    raw = _raw(row)
                    item = {
                        "Product_Code": product_code,
                        "ERP_ProId": result_pro_id or row.get("erp_pro_id"),
                        "Current_ERP_ProId": erp_pro_id,
                        "Keyword": keyword,
                        "KeywordCn": raw.get("KeywordCn") or row.get("KeywordCn"),
                        "keyword_entity_id": row.get("keyword_entity_id"),
                        "keyword_entity_id_status": row.get("keyword_entity_id_status"),
                        "AI_Evidence": evidence.get(key, {}),
                        "record_id": row.get("record_id"),
                        "record_id_status": row.get("record_id_status", ERP_KEYWORD_RECORD_ID_UNCONFIRMED),
                        "record_id_source": row.get("record_id_source"),
                        "source_file": row.get("source_file") or result.get("source_file"),
                        "source_row": row.get("source_row"),
                        "Source": "BENCHMARK_ERP_CANDIDATE",
                    }
                    append_candidate(item, source_pro_id=result_pro_id, key=key)
    if identity_conflicts:
        candidates = [
            item for item in candidates
            if str(item.get("record_id") or "").strip() not in identity_conflicts
        ]
    return {
        "mode": mode,
        "status": ("READY" if candidates else KEYWORD_SOURCE_DATA_INSUFFICIENT),
        "candidates": candidates,
        "unresolved_candidates": unresolved_candidates,
        "identity_conflicts": sorted(identity_conflicts),
        "benchmark_evidence": evidence,
        "own_candidate_keywords": len(own_by_key),
        "benchmark_candidate_keywords": len(benchmark_by_key),
        "deduplicated_candidate_keywords": len(keys),
        "candidate_record_count": len(candidates),
    }


def keyword_source_summary(
    pool: Mapping[str, Any],
    ai_rows: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a compact runtime summary without changing the six-column CSV."""
    precision = sum(1 for row in (ai_rows or ()) if str(row.get("AI_Classification") or "").upper() == "PRECISION")
    return {
        "Keyword Source Mode": pool.get("mode", OWN_ONLY),
        "Keyword Source Status": pool.get("status", KEYWORD_SOURCE_DATA_INSUFFICIENT),
        "Own Candidate Keywords": pool.get("own_candidate_keywords", 0),
        "Benchmark Candidate Keywords": pool.get("benchmark_candidate_keywords", 0),
        "Deduplicated Candidate Keywords": pool.get("deduplicated_candidate_keywords", 0),
        "AI Precision Keywords": precision,
        "Benchmark Precision Candidates Without ERP Record ID": sum(
            1 for row in (ai_rows or ())
            if str(row.get("AI_Classification") or "").upper() == "PRECISION"
            and str(row.get("Source") or "").startswith("BENCHMARK")
            and row.get("record_id_status") == ERP_KEYWORD_RECORD_ID_UNCONFIRMED
        ),
    }


def _normalized_keyword(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _benchmark_observation_groups(rows):
    groups = {}
    for row in rows:
        key = _normalized_keyword(row.get("词", row.get("Keyword")))
        if not key: raise ValueError("601_INVALID_KEYWORD")
        groups.setdefault(key, []).append(row)
    return groups


def _rank_summary(rows):
    ranks = [value for value in (_number_or_none(row.get("自然排名")) for row in rows) if value is not None]
    return len(ranks), min(ranks) if ranks else DATA_NOT_AVAILABLE, median(ranks) if ranks else DATA_NOT_AVAILABLE


def build_keyword_judgment_units(observation_rows):
    units = []
    for canonical, observations in _benchmark_observation_groups(observation_rows).items():
        rank_count, best, middle = _rank_summary(observations)
        benchmarks = {(str(row.get("所属产品编号") or "").strip(), str(row.get("对标ASIN") or "").strip()) for row in observations}
        first = observations[0]
        judgment_item_id = "J-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        units.append({"JudgmentItemId": judgment_item_id, "Id": _full_id(first), "Keyword": str(_full_source_value(first, "词", "Keyword")).strip(),
            "KeywordCn": _full_source_value(first, "中文", "KeywordCn"), "Canonical_Keyword": canonical,
            "Benchmark_Reality_Evidence": {"Benchmark_Observation_Count": len(observations), "Benchmark_Coverage_Count": len(benchmarks),
                "Best_Benchmark_Organic_Rank": best, "Median_Benchmark_Organic_Rank": middle, "Organic_Rank_Count": rank_count}})
    return units


def build_deduplicated_high_precision_rows(rows, *, precision_levels: Iterable[Any] | None = None):
    selected_levels = _selected_precision_levels(precision_levels)
    output = []
    for _canonical, observations in _benchmark_observation_groups(rows).items():
        levels = {str(row.get("精准度") or "").strip() for row in observations}
        reasons = {str(row.get("精准原因") or "").strip() for row in observations}
        if not levels or not levels.issubset(selected_levels) or len(levels) != 1 or len(reasons) != 1: raise ValueError("KEYWORD_JUDGMENT_INCONSISTENT")
        facts = {}
        for field in ("市场容量", "竞争产品数", "供需比"):
            values = {str(row.get(field)).strip().replace(",", "") for row in observations if row.get(field) not in (None, "")}
            if len(values) > 1: raise ValueError("UNIQUE_KEYWORD_MARKET_FACT_INCONSISTENT")
            facts[field] = next((row.get(field) for row in observations if row.get(field) not in (None, "")), observations[0].get(field))
        _, best, middle = _rank_summary(observations)
        benchmarks = {(str(row.get("所属产品编号") or "").strip(), str(row.get("对标ASIN") or "").strip()) for row in observations}
        first = observations[0]
        output.append({"Id": str(first.get("Id") or "").strip(), "词": first.get("词"), "中文": first.get("中文"),
            "市场容量": facts["市场容量"], "竞争产品数": facts["竞争产品数"], "供需比": facts["供需比"],
            "对标覆盖数": len(benchmarks), "最佳自然排名": best, "自然排名中位数": middle,
            "精准度": next(iter(levels)), "精准原因": next(iter(reasons))})
    return _stable_full_sort(output)


def build_deduplicated_benchmark_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate B at Benchmark + Canonical Keyword grain, preserving ownership."""
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        code = str(row.get("所属产品编号") or "").strip()
        keyword = _normalized_keyword(row.get("词"))
        key = (code, keyword)
        if not code or not keyword or key in seen:
            continue
        seen.add(key)
        output.append(dict(row))
    return output


def _documented_natural_rank(row: Mapping[str, Any]) -> float | None:
    """Use a rank only when the maintained schema confirms organic semantics."""
    raw = _raw(row)
    semantics = _semantics(row)
    for field in ("RankOra", "abarank", "RankAdv", "RankRec"):
        definition = semantics.get(field)
        meaning = str(definition.get("meaning") or "") if isinstance(definition, Mapping) else ""
        if not isinstance(definition, Mapping) or definition.get("status") != "DOCUMENTED" or "自然" not in meaning:
            continue
        try:
            value = float(raw.get(field))
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def build_benchmark_evidence(
    benchmark_results: Iterable[Mapping[str, Any]],
    *,
    benchmark_erp_pro_ids: Iterable[Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Aggregate benchmark keyword/organic evidence without creating labels.

    Benchmark rows remain separate from the current-product rows. Rank values
    are used only when PickPwKView schema semantics explicitly document an
    organic-rank field; otherwise the evidence is marked unavailable.
    """
    configured = [str(value).strip() for value in (benchmark_erp_pro_ids or ()) if str(value).strip()]
    per_keyword: dict[str, dict[str, Any]] = {}
    for result in benchmark_results:
        pro_id = str(result.get("erp_pro_id") or "").strip()
        is_all_observation_asset = result.get("source_type") == "BENCHMARK_6_0_1_ALL_OBSERVATIONS"
        if configured and pro_id not in configured and not is_all_observation_asset:
            continue
        for row in result.get("rows") or ():
            keyword = str(row.get("keyword") or _raw(row).get("Keyword") or "").strip()
            key = _normalized_keyword(keyword)
            if not key:
                continue
            if is_all_observation_asset:
                coverage = _number_or_none(row.get("Benchmark_Coverage_Count"))
                rank_count = _number_or_none(row.get("Benchmark_Organic_Rank_Count"))
                best = _number_or_none(row.get("Best_Benchmark_Organic_Rank"))
                rank_median = _number_or_none(row.get("Median_Benchmark_Organic_Rank"))
                configured_count = _number_or_none(result.get("benchmark_count"))
                pro_ids = list(result.get("benchmark_erp_pro_ids") or ())
                per_keyword[key] = {
                    "preaggregated": True,
                    "Benchmark_ERP_ProIds": ",".join(pro_ids) if pro_ids else DATA_NOT_AVAILABLE,
                    "Benchmark_Count": coverage if coverage is not None else DATA_NOT_AVAILABLE,
                    "Benchmark_Keyword_Coverage": round(coverage / configured_count, 4) if coverage is not None and configured_count else DATA_NOT_AVAILABLE,
                    "Benchmark_Organic_Rank_Count": rank_count if rank_count is not None else 0,
                    "Benchmark_Organic_Evidence": "AVAILABLE" if best is not None else BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE,
                    "Best_Benchmark_Organic_Rank": best if best is not None else DATA_NOT_AVAILABLE,
                    "Median_Benchmark_Organic_Rank": rank_median if rank_median is not None else DATA_NOT_AVAILABLE,
                    "Evidence_Summary": json.dumps({
                        "benchmark_codes": list(result.get("benchmark_codes") or ()),
                        "benchmark_erp_pro_ids": pro_ids,
                        "organic_rank_observation_count": coverage,
                        "best_organic_rank": best,
                        "median_organic_rank": rank_median,
                        "rank_semantics": "AGGREGATED_DOCUMENTED_RANKORA",
                    }, ensure_ascii=False, sort_keys=True, default=str),
                }
                per_keyword[key]["Benchmark_Evidence_Summary"] = per_keyword[key]["Evidence_Summary"]
                continue
            bucket = per_keyword.setdefault(key, {"pro_ids": set(), "ranks": []})
            if pro_id:
                bucket["pro_ids"].add(pro_id)
            rank = _documented_natural_rank(row)
            if rank is not None:
                bucket["ranks"].append(rank)
    output: dict[str, dict[str, Any]] = {}
    for keyword, bucket in per_keyword.items():
        if bucket.get("preaggregated"):
            output[keyword] = {key: value for key, value in bucket.items() if key != "preaggregated"}
            continue
        pro_ids = sorted(bucket["pro_ids"])
        ranks = sorted(bucket["ranks"])
        rank_available = bool(ranks)
        output[keyword] = {
            "Benchmark_ERP_ProIds": ",".join(pro_ids) if pro_ids else DATA_NOT_AVAILABLE,
            "Benchmark_Count": len(pro_ids),
            "Benchmark_Keyword_Coverage": round(len(pro_ids) / len(configured), 4) if configured else DATA_NOT_AVAILABLE,
            "Benchmark_Organic_Rank_Count": len(ranks),
            "Benchmark_Organic_Evidence": "AVAILABLE" if rank_available else BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE,
            "Best_Benchmark_Organic_Rank": min(ranks) if ranks else DATA_NOT_AVAILABLE,
            "Median_Benchmark_Organic_Rank": median(ranks) if ranks else DATA_NOT_AVAILABLE,
            "Evidence_Summary": json.dumps({
                "benchmark_erp_pro_ids": pro_ids,
                "organic_rank_values": ranks if ranks else DATA_NOT_AVAILABLE,
                "rank_semantics": "DOCUMENTED_ORGANIC_RANK" if rank_available else BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE,
            }, ensure_ascii=False, sort_keys=True, default=str),
        }
        output[keyword]["Benchmark_Evidence_Summary"] = output[keyword]["Evidence_Summary"]
    return output


def _number_or_none(value: Any) -> float | None:
    if value in (None, "", DATA_NOT_AVAILABLE):
        return None
    try:
        parsed = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def build_ai_classified_rows(
    blind_rows: Iterable[Mapping[str, Any]],
    decisions: Mapping[str, Mapping[str, Any]],
    *,
    product_code: str,
    erp_pro_id: Any,
    benchmark_evidence: Mapping[str, Mapping[str, Any]] | None = None,
    benchmark_status: str = BENCHMARK_ERP_PROID_NOT_AVAILABLE,
    source_rows: Iterable[Mapping[str, Any]] | None = None,
    product_context: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Project blind model decisions into the complete AI asset table.

    Tags and the historical manual label are joined only after the blind
    decision is made.  Every valid keyword is retained so REVIEW_REQUIRED is
    auditable instead of silently disappearing.
    """
    source_by_keyword: dict[str, list[Mapping[str, Any]]] = {}
    for row in (source_rows or ()):
        key = _normalized_keyword(_keyword(row))
        if key:
            source_by_keyword.setdefault(key, []).append(row)
    context = dict(product_context or {})
    purchase_driver = build_product_purchase_driver(context)
    decisions_by_normalized_keyword = {
        _normalized_keyword(key): value for key, value in decisions.items()
    }
    fallback_benchmark_status = (
        BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE
        if benchmark_status == "BENCHMARK_EVIDENCE_READY"
        else benchmark_status
    )
    amazon_fields = (
        "Impressions", "Clicks", "CTR", "Spend", "CPC", "Orders", "Sales",
        "CVR", "CPA", "ACoS", "Organic_Rank", "Organic_Rank_Trend",
        "Provider", "Source_Grain", "Metric_Semantics", "Attribution_Semantics",
        "Data_Through", "Freshness",
    )
    output: list[dict[str, Any]] = []
    for blind in blind_rows:
        keyword = str(blind.get("Keyword") or "")
        decision = (
            decisions.get(keyword)
            or decisions.get(keyword.lower())
            or decisions_by_normalized_keyword.get(_normalized_keyword(keyword))
            or {}
        )
        # Semantic guardrail: structured Search_Intent is preferred, but the
        # current Keyword is always checked when the model omits that object.
        # It never promotes a keyword or uses performance metrics as a label.
        semantic_intent = decision.get("Keyword_Search_Intent")
        if not isinstance(semantic_intent, Mapping) and isinstance(decision.get("Search_Intent"), Mapping):
            semantic_intent = decision.get("Search_Intent")
        if not isinstance(semantic_intent, Mapping):
            semantic_intent = {"Core_Intent": keyword}
        benchmark = (benchmark_evidence or {}).get(_normalized_keyword(keyword))
        semantic_guard = evaluate_product_search_intent_fit(
            context, semantic_intent, keyword=keyword, supporting_evidence=benchmark,
            purchase_driver=purchase_driver,
        )
        classification = str(decision.get("AI_Classification") or "").strip().upper()
        if classification not in LEGACY_AI_CLASSIFICATIONS:
            legacy = decision.get("AI_Is_Precision")
            classification = "PRECISION" if legacy is True else "NOT_PRECISION" if legacy is False else "REVIEW_REQUIRED"
        if classification == "PRECISION" and semantic_guard and semantic_guard["AI_Classification"] in {"NOT_PRECISION", "REVIEW_REQUIRED"}:
            classification = semantic_guard["AI_Classification"]
        decision_reason = str(decision.get("AI_Reason") or "").strip()
        if classification == "PRECISION" and decision_reason == _GENERIC_PRECISION_REASON:
            classification = "REVIEW_REQUIRED"
            semantic_guard = {
                "AI_Classification": "REVIEW_REQUIRED",
                "AI_Reason": "精准理由未针对当前关键词提供可核验的具体意图和产品事实",
            }
        current_erp_evidence = blind.get("AI_Evidence")
        if isinstance(current_erp_evidence, Mapping) and current_erp_evidence:
            current_erp_evidence_value = json.dumps(current_erp_evidence, ensure_ascii=False, sort_keys=True, default=str)
        else:
            current_erp_evidence_value = DATA_NOT_AVAILABLE
        benchmark_values = dict(benchmark or {})
        if not benchmark_values:
            benchmark_values = {
                "Benchmark_ERP_ProIds": DATA_NOT_AVAILABLE,
                "Benchmark_Count": DATA_NOT_AVAILABLE,
                "Benchmark_Keyword_Coverage": DATA_NOT_AVAILABLE,
                "Benchmark_Organic_Rank_Count": DATA_NOT_AVAILABLE,
                "Benchmark_Organic_Evidence": fallback_benchmark_status or DATA_NOT_AVAILABLE,
                "Best_Benchmark_Organic_Rank": DATA_NOT_AVAILABLE,
                "Median_Benchmark_Organic_Rank": DATA_NOT_AVAILABLE,
                "Benchmark_Evidence_Summary": fallback_benchmark_status or DATA_NOT_AVAILABLE,
                "Evidence_Summary": fallback_benchmark_status or DATA_NOT_AVAILABLE,
            }
        source_matches = source_by_keyword.get(_normalized_keyword(keyword), [])
        source_row = source_matches[0] if source_matches else None
        record_id_status = str(blind.get("record_id_status") or ERP_KEYWORD_RECORD_ID_UNCONFIRMED)
        source_raw = _raw(source_row) if source_row else {}
        if not source_row or "Tags" not in source_raw:
            # 6-0-1 output intentionally contains no ERP Tags; a missing
            # manual label is unknown, never an inferred NOT_PRECISION value.
            manual_label = DATA_NOT_AVAILABLE
        else:
            manual_label = "PRECISION" if PRECISION_TAG in str(source_raw.get("Tags") or "") else "NOT_PRECISION"
        comparison = "REVIEW_REQUIRED" if classification == "REVIEW_REQUIRED" else (
            "BOTH_PRECISION" if classification == "PRECISION" and manual_label == "PRECISION" else
            "AI_ONLY" if classification == "PRECISION" else
            "MANUAL_ONLY" if manual_label == "PRECISION" else "BOTH_NOT_PRECISION"
        )
        # Precision Brain's final reason is the user-facing explanation for
        # adaptive driver decisions (especially Gift Mission matches). Keep
        # the formal CSV columns unchanged while exposing that reason on the
        # internal classified row.
        guard_reason = str((semantic_guard or {}).get("FinalPrecisionReason") or "").strip()
        if classification != "PRECISION" and semantic_guard:
            ai_reason = str((semantic_guard or {}).get("AI_Reason") or guard_reason or decision.get("AI_Reason") or "[AI未提供分类理由]").strip()
        else:
            ai_reason = guard_reason or str(decision.get("AI_Reason") or "[AI未提供分类理由]").strip()
        item = {
            "Product_Code": product_code,
            "ERP_ProId": blind.get("ERP_ProId") or erp_pro_id,
            "Current_ERP_ProId": erp_pro_id,
            "Marketplace": context.get("Marketplace", DATA_NOT_AVAILABLE),
            "ASIN": context.get("ASIN", DATA_NOT_AVAILABLE),
            "Keyword": keyword,
            "KeywordCn": blind.get("KeywordCn"),
            "AI_Classification": classification,
            "AI_Is_Precision": True if classification == "PRECISION" else False if classification == "NOT_PRECISION" else None,
            "AI_Confidence": str(decision.get("AI_Confidence", "LOW")).upper() if str(decision.get("AI_Confidence", "LOW")).upper() in AI_CONFIDENCE_VALUES else "LOW",
            "AI_Reason": ai_reason,
            "精准度": semantic_guard.get("FinalPrecision", _classification_level(classification)) if semantic_guard else _classification_level(classification),
            "精准原因": guard_reason or ai_reason,
            "AI_Precision_Score": DATA_NOT_AVAILABLE,
            "AI_Precision_Level": _precision_level(decision.get("精准度", decision.get("AI_Precision_Level", decision.get("Precision_Level")))),
            "Search_Intent": decision.get("Search_Intent", ""),
            "Product_Intent_Fit": decision.get("Product_Intent_Fit", DATA_NOT_AVAILABLE),
            "Matched_Product_Attributes": decision.get("Matched_Product_Attributes", DATA_NOT_AVAILABLE),
            "Conflicting_Product_Attributes": decision.get("Conflicting_Product_Attributes", DATA_NOT_AVAILABLE),
            "Manual_Precision_Label": manual_label,
            "Comparison_Status": comparison,
            "Current_Product_ERP_Evidence": current_erp_evidence_value,
            "Source": blind.get("Source") or "ERP_AI_CLASSIFIED",
            "Tags": source_raw.get("Tags", DATA_NOT_AVAILABLE),
            "RecordDate": source_raw.get("RecordDate", DATA_NOT_AVAILABLE),
            "UpdateTime": source_raw.get("UpdateTime", DATA_NOT_AVAILABLE),
            "record_id": blind.get("record_id"),
            "record_id_status": record_id_status,
        }
        item.update({
            "PrimaryPurchaseDriver": semantic_guard.get("PrimaryPurchaseDriver", purchase_driver.get("PrimaryPurchaseDriver", DATA_NOT_AVAILABLE)),
            "SecondaryPurchaseDrivers": semantic_guard.get("SecondaryPurchaseDrivers", purchase_driver.get("SecondaryPurchaseDrivers", [])),
            "PurchaseDriverReason": semantic_guard.get("PurchaseDriverReason", purchase_driver.get("PurchaseDriverReason", DATA_NOT_AVAILABLE)),
            "GiftIntentPresent": semantic_guard.get("GiftIntentPresent", DATA_NOT_AVAILABLE),
            "GiftMissionFit": semantic_guard.get("GiftMissionFit", DATA_NOT_AVAILABLE),
            "PurchaseMissionFit": semantic_guard.get("PurchaseMissionFit", semantic_guard.get("GiftMissionFit", DATA_NOT_AVAILABLE)),
            "RecipientFit": semantic_guard.get("RecipientFit", DATA_NOT_AVAILABLE),
            "RelationshipFit": semantic_guard.get("RelationshipFit", DATA_NOT_AVAILABLE),
            "OccasionFit": semantic_guard.get("OccasionFit", DATA_NOT_AVAILABLE),
            "EmotionalMessageFit": semantic_guard.get("EmotionalMessageFit", DATA_NOT_AVAILABLE),
            "PhysicalProductConvergence": semantic_guard.get("PhysicalProductConvergence", DATA_NOT_AVAILABLE),
            "PurchaseMissionConvergence": semantic_guard.get("PurchaseMissionConvergence", DATA_NOT_AVAILABLE),
            "CompatibilityConvergence": semantic_guard.get("CompatibilityConvergence", DATA_NOT_AVAILABLE),
            "InitialPrecision": semantic_guard.get("InitialPrecision", DATA_NOT_AVAILABLE),
            "DecisionChallenge": semantic_guard.get("DecisionChallenge", DATA_NOT_AVAILABLE),
            "ChallengeResult": semantic_guard.get("ChallengeResult", DATA_NOT_AVAILABLE),
            "FinalPrecisionReason": semantic_guard.get("FinalPrecisionReason", DATA_NOT_AVAILABLE),
        })
        for key in ("Product_Semantic_Profile",) + SEMANTIC_PROFILE_FIELDS:
            item[key] = decision.get(key, context.get(key, DATA_NOT_AVAILABLE))
        for field in amazon_fields:
            item[field] = decision.get(field, (decision.get("Amazon_Evidence") or {}).get(field, DATA_NOT_AVAILABLE))
        item.update(benchmark_values)
        evidence = blind.get("AI_Evidence")
        if isinstance(evidence, Mapping):
            item.update(evidence)
        # Preserve only documented source values; unknown semantics remain absent.
        if source_row:
            item.update(_documented_quality(source_row))
        output.append(item)
    return output


def build_dual_views(
    fetch_all_rows: Callable[[], Iterable[Mapping[str, Any]]],
    *,
    product_code: str,
    erp_pro_id: Any,
) -> dict[str, Any]:
    """Create both views from already supplied rows (legacy compatibility).

    This helper does not perform a query itself.  Normal 6-0-2 runs must use
    :func:`build_dual_views_from_601_output`; callers should not inject ERP
    rows into the runtime path.
    """
    rows = list(fetch_all_rows())
    return {
        "source_row_count": len(rows),
        "manual_rows": [],
        "ai_blind_rows": build_ai_blind_rows(rows, product_code=product_code, erp_pro_id=erp_pro_id),
        "manual_status": "MANUAL_PRECISION_OUTPUT_REMOVED",
    }


def compare_precision_sets(
    manual_rows: Iterable[Mapping[str, Any]],
    ai_rows: Iterable[Mapping[str, Any]],
    all_keywords: Iterable[Mapping[str, Any] | str] | None = None,
) -> dict[tuple[str, str, str], str]:
    """Return comparison state without creating a third CSV.

    ``all_keywords`` is the complete valid-Keyword universe from the single
    ERP query.  Supplying it preserves ``NEITHER`` rows; omitting it keeps the
    helper convenient for comparing only the two positive CSVs.
    """
    manual = {_join_key(item) for item in manual_rows if _join_key(item)[2]}
    ai = {
        _join_key(item) for item in ai_rows
        if _join_key(item)[2] and (
            str(item.get("AI_Classification") or "").upper() == "PRECISION"
            or item.get("AI_Is_Precision") is True
        )
    }
    universe: set[tuple[str, str, str]] = set()
    for term in all_keywords or ():
        key = _join_key(term) if isinstance(term, Mapping) else ("", "", str(term or "").strip().lower())
        if key[2]:
            universe.add(key)
    terms = sorted(manual | ai | universe)
    return {
        term: "BOTH_PRECISION" if term in manual and term in ai else
        "MANUAL_ONLY" if term in manual else
        "AI_ONLY" if term in ai else "NEITHER"
        for term in terms
    }


def output_paths(
    product_root: str | Path,
    product_code: str,
    run_context=None,
    *,
    benchmark_product_codes: Iterable[str] = (),
    output_directory: str | Path | None = None,
) -> dict[str, Any]:
    context = run_context or new_602_run_context(product_root, product_code)
    report_root = resolve_skill_report_dir(product_root, Path(__file__).resolve().parents[1])
    directory = Path(output_directory) if output_directory is not None else governance_paths(report_root)["data"]
    stamp = context.run_timestamp
    if not re.fullmatch(r"\d{8}_\d{6}", stamp):
        raise ValueError("RUN_TIMESTAMP must match YYYYMMDD_HHMMSS")
    def path(label: str) -> Path:
        return directory / f"6-0-2_{label}_{stamp}.csv"
    codes = list(dict.fromkeys(str(code).strip() for code in benchmark_product_codes))
    if any(not code or re.search(r'[<>:"/\\|?*]', code) or code.endswith((".", " ")) for code in codes):
        raise ValueError("INVALID_BENCHMARK_PRODUCT_CODE_FILENAME")
    return {
        "ai": path("精准判断所有词表"),
        # B: configuration-filtered Benchmark observations.
        "high_precision": path("筛选后的对标精准词"),
        # C: Benchmark-preserving deduplication.
        "deduplicated_benchmark": path("去重_筛选后的对标精准词"),
        # D: Benchmark-removed canonical keyword asset for 603.
        "deduplicated": path("去对标去重_筛选后的精准词"),
        # E: one configuration-filtered asset per Benchmark.
        "benchmarks": {code: path(f"{code}_筛选后的精准词") for code in codes},
    }


def new_602_run_context(product_root: str | Path, product_code: str, *, now: datetime | None = None):
    instant = (now or datetime.now().astimezone()).astimezone()
    root = Path(product_root) / "06_SKILL分析报告" / OUTPUT_DIR
    while (root / f"{RUN_MANIFEST_PREFIX}{instant.strftime('%Y%m%d_%H%M%S')}.json").exists():
        instant += timedelta(seconds=1)
    return new_run_context("6-0-2", SIX_0_2_SKILL_ID, product_code, now=instant)


def _columns(rows: list[Mapping[str, Any]], required: tuple[str, ...]) -> list[str]:
    columns = list(dict.fromkeys(required))
    for row in rows:
        for key in row:
            if key not in columns and key not in AI_EXCLUDED_FIELDS:
                columns.append(key)
    return columns


def write_csv(path: str | Path, rows: Iterable[Mapping[str, Any]], *, columns: Iterable[str]) -> Path:
    """Write an auditable UTF-8-with-BOM CSV suitable for Windows Excel."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    values = list(rows)
    fieldnames = list(columns)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        if values:
            writer.writerows({key: row.get(key) for key in fieldnames} for row in values)
        # Empty final assets intentionally contain header only; no synthetic
        # status row is allowed in the six-column contract.
        return target


def _score(value: Any) -> Any:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return DATA_NOT_AVAILABLE
    if not 0 <= number <= 100:
        return DATA_NOT_AVAILABLE
    return int(number) if number.is_integer() else round(number, 2)


def _precision_level(value: Any) -> str:
    """Accept only the four direct AI precision levels for CSV output."""
    text = str(value or "").strip()
    text = PRECISION_LABEL_ALIASES.get(text, text)
    return text if text in PRECISION_LEVELS else PRECISION_LEVEL_NOT_AVAILABLE


def _precision_filter_config_path(product_root: str | Path) -> Path | None:
    """Find the shared precision-filter config above a product project."""
    product_path = Path(product_root).resolve()
    for ancestor in (product_path, *product_path.parents):
        config_dir = ancestor / PRECISION_FILTER_CONFIG_RELATIVE.parent
        candidate = ancestor / PRECISION_FILTER_CONFIG_RELATIVE
        if candidate.is_file():
            return candidate
        if config_dir.is_dir():
            raise FileNotFoundError(
                f"PRECISION_FILTER_CONFIG_NOT_FOUND: {PRECISION_FILTER_CONFIG_RELATIVE}"
            )
    return None


def read_precision_filter_config(product_root: str | Path, *, require: bool = False) -> dict[str, Any]:
    """Read the shared selected-precision levels and normalize business aliases.

    The maintained file is intentionally a small text configuration rather
    than a code constant.  ``已精准`` is the documented business wording for
    the existing AI output level ``精准`` and is normalized only at this
    boundary.  Missing or malformed configuration fails closed.
    """
    path = _precision_filter_config_path(product_root)
    if path is None:
        if require:
            raise ValueError("PRECISION_LIBRARY_CONFIG_NOT_FOUND")
        # Compatibility mode is retained for low-level isolated fixtures;
        # real runners call with require=True and never use a default.
        return {
            "path": "",
            "raw_levels": sorted(DEFAULT_FILTERED_PRECISION_LEVELS),
            "levels": sorted(DEFAULT_FILTERED_PRECISION_LEVELS),
            "sha256": "",
            "size_bytes": 0,
            "modified_at_ns": 0,
        }
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"PRECISION_FILTER_CONFIG_READ_FAILED: {path}") from exc
    known = tuple(sorted((*PRECISION_LEVELS, *PRECISION_LABEL_ALIASES), key=len, reverse=True))
    labels: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "//", "<!--")):
            continue
        if line in known:
            labels.append(line)
            continue
        # Allow a maintained key/value line while avoiding the word
        # “精准” in the prose heading itself being interpreted as a value.
        if re.search(r"(?:筛选精准等级|精准级别|筛选等级|精准词库)\s*[：:=]", line):
            value = re.split(r"[：:=]", line, maxsplit=1)[1]
            parts = [part for part in re.split(r"[,，、/|;；\s]+", value.strip()) if part]
            if any(part not in known for part in parts):
                raise ValueError("CONFIG_PRECISION_LEVEL_INVALID")
            labels.extend(parts)
    if not labels:
        raise ValueError("PRECISION_LIBRARY_CONFIG_EMPTY")
    normalized: list[str] = []
    for label in labels:
        canonical = PRECISION_LABEL_ALIASES.get(label, label)
        if canonical not in PRECISION_LEVELS:
            raise ValueError("CONFIG_PRECISION_LEVEL_INVALID")
        if canonical not in normalized:
            normalized.append(canonical)
    if not normalized:
        raise ValueError("PRECISION_LIBRARY_CONFIG_EMPTY")
    stat = path.stat()
    return {
        "path": str(path),
        "raw_levels": labels,
        "levels": normalized,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "size_bytes": stat.st_size,
        "modified_at_ns": stat.st_mtime_ns,
    }


def build_product_purchase_driver(source: Mapping[str, Any] | None) -> dict[str, Any]:
    """Resolve one product-level purchase driver for the current run.

    An explicitly supplied driver is authoritative.  Otherwise this uses only
    confirmed profile fields and returns ``DATA_NOT_AVAILABLE`` when the
    product ground truth is insufficient; it never reads a keyword to invent
    a product driver.
    """
    profile = source if isinstance(source, Mapping) else {}
    explicit = str(profile.get("PrimaryPurchaseDriver") or "").strip().upper()
    if explicit in PURCHASE_DRIVERS:
        secondary = profile.get("SecondaryPurchaseDrivers") or []
        if isinstance(secondary, str):
            secondary = [secondary]
        secondary = [str(item).strip().upper() for item in secondary if str(item).strip().upper() in PURCHASE_DRIVERS and str(item).strip().upper() != explicit]
        return {
            "PrimaryPurchaseDriver": explicit,
            "SecondaryPurchaseDrivers": secondary,
            "PurchaseDriverReason": str(profile.get("PurchaseDriverReason") or "由产品 Ground Truth 明确指定").strip(),
            "Source": "EXPLICIT_PRODUCT_GROUND_TRUTH",
        }
    values = {field: " ".join(_semantic_values(profile.get(field))).lower() for field in (
        "Core_Product_Type", "Core_Functions", "Core_Use_Cases", "Compatibility",
        "Recipient", "Relationship_Intent", "Purchase_Occasions", "Core_Attributes",
    )}
    gift_signal = bool(values["Recipient"] or values["Relationship_Intent"]) and bool(
        values["Purchase_Occasions"] or any(token in values["Core_Product_Type"] for token in ("gift", "keepsake", "figurine", "memorial"))
    )
    compatibility_signal = bool(values["Compatibility"] or any(token in values["Core_Use_Cases"] for token in ("compatible", "fit", "model", "interface", "installation")))
    functional_signal = bool(values["Core_Functions"] or values["Core_Use_Cases"])
    aesthetic_signal = bool(any(token in values["Core_Product_Type"] or token in values["Core_Attributes"] for token in ("decor", "ornament", "style", "theme", "display", "visual")))
    occasion_signal = bool(values["Purchase_Occasions"])
    signals = []
    if compatibility_signal: signals.append("COMPATIBILITY")
    if gift_signal: signals.append("GIFT_EMOTIONAL")
    if aesthetic_signal: signals.append("AESTHETIC_DECOR")
    if functional_signal: signals.append("FUNCTIONAL")
    if occasion_signal: signals.append("OCCASION")
    if not signals:
        return {"PrimaryPurchaseDriver": DATA_NOT_AVAILABLE, "SecondaryPurchaseDrivers": [],
                "PurchaseDriverReason": "产品 Ground Truth 未提供足够购买驱动证据", "Source": "INSUFFICIENT_PRODUCT_GROUND_TRUTH"}
    priority = ("COMPATIBILITY", "GIFT_EMOTIONAL", "AESTHETIC_DECOR", "FUNCTIONAL", "OCCASION")
    primary = next(item for item in priority if item in signals)
    secondary = [item for item in signals if item != primary]
    return {
        "PrimaryPurchaseDriver": primary,
        "SecondaryPurchaseDrivers": secondary,
        "PurchaseDriverReason": "；".join(f"{item} 由已确认产品字段支持" for item in signals),
        "Source": "DERIVED_CONFIRMED_PRODUCT_GROUND_TRUTH",
    }


def _selected_precision_levels(precision_levels: Iterable[Any] | None) -> frozenset[str]:
    """Normalize an explicit runtime selection or use compatibility defaults."""
    if precision_levels is None:
        return FILTERED_PRECISION_LEVELS
    normalized = frozenset(
        PRECISION_LABEL_ALIASES.get(str(level or "").strip(), str(level or "").strip())
        for level in precision_levels
        if str(level or "").strip()
    )
    if not normalized or not normalized.issubset(set(PRECISION_LEVELS)):
        raise ValueError("PRECISION_FILTER_LEVELS_INVALID")
    return normalized


def _effective_precision_levels(product_root: str | Path, precision_levels: Iterable[Any] | None) -> Iterable[Any]:
    """Resolve writer selection from shared config unless explicitly supplied."""
    if precision_levels is not None:
        return precision_levels
    # Formal run_current_602 resolves the configuration strictly before
    # reaching this helper.  Keep low-level fixture writers usable without a
    # shared root while preserving the strict real-run gate.
    return read_precision_filter_config(product_root, require=False)["levels"]


def _classification_level(classification: Any, *, manual_label: Any = None) -> str:
    """Conservative compatibility fallback without numeric score conversion."""
    explicit = _precision_level(manual_label)
    if explicit != PRECISION_LEVEL_NOT_AVAILABLE:
        return explicit
    state = str(classification or "").strip().upper()
    return PRECISION_LEVEL_NOT_AVAILABLE


def _search_volume(value: Any) -> Any:
    """Return the documented SearchVolume30 value or an explicit missing marker."""
    if value in (None, "", DATA_NOT_AVAILABLE):
        return DATA_NOT_AVAILABLE
    try:
        text = str(value).strip().replace(",", "")
        number = float(text)
    except (TypeError, ValueError):
        return DATA_NOT_AVAILABLE
    if not math.isfinite(number) or number < 0:
        return DATA_NOT_AVAILABLE
    if isinstance(value, str):
        return value.strip()
    return int(number) if number.is_integer() else number


def _sort_by_search_volume(rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Sort valid SearchVolume30 descending, stably placing unavailable values last."""
    values = list(rows)

    def key(row: Mapping[str, Any]) -> tuple[int, float]:
        volume = _search_volume(row.get("SearchVolume30", row.get("搜索量")))
        if volume == DATA_NOT_AVAILABLE:
            return (1, 0.0)
        return (0, -float(volume))

    return sorted(values, key=key)


def _final_row(row: Mapping[str, Any], *, reason_key: str, score_key: str,
               translations: Mapping[str, str] | None = None) -> dict[str, Any]:
    keyword = str(row.get("Keyword") or row.get("keyword") or "").strip()
    cn = str(row.get("KeywordCn") or "").strip()
    if not cn and translations:
        cn = str(translations.get(keyword) or translations.get(keyword.lower()) or "").strip()
    search_volume = _search_volume(row.get("SearchVolume30"))
    level = _precision_level(row.get("精准度") or row.get("AI_Precision_Level") or row.get("Precision_Level"))
    if level == PRECISION_LEVEL_NOT_AVAILABLE:
        level = _classification_level(row.get("AI_Classification"), manual_label=row.get("Manual_Precision_Label"))
    return {
        "自动编号": _record_id(row),
        "关键词": keyword,
        "搜索量": search_volume,
        "中文名称": cn or DATA_NOT_AVAILABLE,
        "精准理由": str(row.get(reason_key) or "[未提供精准理由]").strip(),
        "精准度": level,
    }


def _unique_real_record_rows(rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Keep one output row per real ERP Record ID and block ID conflicts."""
    selected: list[Mapping[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    keyword_by_id: dict[str, str] = {}
    conflicts: set[str] = set()
    for row in rows:
        record_id = _record_id(row)
        if not record_id.isdigit():
            continue
        keyword = _normalized_keyword(row.get("Keyword") or row.get("keyword"))
        if not keyword:
            continue
        pair = (record_id, keyword)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        previous = keyword_by_id.get(record_id)
        if previous is not None and previous != keyword:
            conflicts.add(record_id)
        keyword_by_id[record_id] = keyword
        selected.append(row)
    return [row for row in selected if _record_id(row) not in conflicts]


def _conflicting_real_record_ids(rows: Iterable[Mapping[str, Any]]) -> set[str]:
    """Find IDs mapped to more than one normalized Keyword in all AI states."""
    keywords_by_id: dict[str, str] = {}
    conflicts: set[str] = set()
    for row in rows:
        record_id = _record_id(row)
        if not record_id.isdigit():
            continue
        keyword = _normalized_keyword(row.get("Keyword") or row.get("keyword"))
        if not keyword:
            continue
        previous = keywords_by_id.get(record_id)
        if previous is not None and previous != keyword:
            conflicts.add(record_id)
        keywords_by_id[record_id] = keyword
    return conflicts


def build_final_ai_rows(ai_rows: Iterable[Mapping[str, Any]], *,
                        translations: Mapping[str, str] | None = None) -> list[dict[str, Any]]:
    """Keep only AI PRECISION decisions and project to the six-column asset."""
    output = []
    all_rows = list(ai_rows)
    identity_conflicts = _conflicting_real_record_ids(all_rows)
    precision_rows = []
    for row in all_rows:
        state = str(row.get("AI_Classification") or "").strip().upper()
        legacy_precision = row.get("AI_Is_Precision") is True
        if state != "PRECISION" and not (not state and legacy_precision):
            continue
        if _record_id(row) in identity_conflicts:
            continue
        precision_rows.append(row)
    for row in _unique_real_record_rows(precision_rows):
        output.append(_final_row(row, reason_key="AI_Reason", score_key="AI_Precision_Score", translations=translations))
    return _sort_by_search_volume(output)


def build_final_manual_rows(manual_rows: Iterable[Mapping[str, Any]], *,
                            ai_rows: Iterable[Mapping[str, Any]] | None = None,
                            translations: Mapping[str, str] | None = None) -> list[dict[str, Any]]:
    """Project ERP-tagged rows to the same six-column final contract."""
    score_by_keyword = {
        _normalized_keyword(row.get("Keyword")): row.get("AI_Precision_Score")
        for row in (ai_rows or ())
        if str(row.get("AI_Classification") or "").upper() == "PRECISION"
    }
    output = []
    for row in _unique_real_record_rows(manual_rows):
        projected = _final_row(row, reason_key="Manual_Reason", score_key="AI_Precision_Score", translations=translations)
        if projected["精准度"] == PRECISION_LEVEL_NOT_AVAILABLE:
            projected["精准度"] = "精准"
        output.append(projected)
    return _sort_by_search_volume(output)


def build_high_precision_rows(rows: Iterable[Mapping[str, Any]], *, precision_levels: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    """Keep rows whose level is in the configured B/C/D/E selection."""
    selected_levels = _selected_precision_levels(precision_levels)
    selected = [dict(row) for row in rows if _precision_level(row.get("精准度")) in selected_levels]
    return _stable_full_sort(selected)


def write_high_precision_csv(product_root: str | Path, product_code: str, rows: Iterable[Mapping[str, Any]], *, precision_levels: Iterable[Any] | None = None) -> Path:
    context = new_run_context("6-0-2", SIX_0_2_SKILL_ID, product_code)
    paths = output_paths(product_root, product_code, context)
    selected = build_high_precision_rows(rows, precision_levels=_effective_precision_levels(product_root, precision_levels))
    path = paths["high_precision"]
    assert_new_outputs([path])
    write_csv(path, selected, columns=FULL_FINAL_COLUMNS)
    return path


def write_dual_csvs(product_root: str | Path, product_code: str, manual_rows: list[Mapping[str, Any]], ai_rows: list[Mapping[str, Any]], *, precision_levels: Iterable[Any] | None = None) -> dict[str, Path]:
    """Compatibility writer that emits the two AI assets and never a manual CSV.

    ``manual_rows`` is accepted for callers that still pass the historical
    argument, but it is intentionally ignored and no manual output is written.
    Canonical callers should use :func:`write_full_ai_csv`.
    """
    del manual_rows
    context = new_run_context("6-0-2", SIX_0_2_SKILL_ID, product_code)
    paths = output_paths(product_root, product_code, context)
    values = list(ai_rows)
    canonical = bool(values) and set(FULL_FINAL_COLUMNS).issubset(values[0])
    if canonical:
        full_rows = values
    else:
        full_rows = [
            {"Id": _record_id(row), "词": row.get("Keyword") or row.get("关键词"),
             "中文": row.get("KeywordCn") or row.get("中文名称") or DATA_NOT_AVAILABLE,
             "市场容量": row.get("SearchVolume30") or row.get("搜索量") or DATA_NOT_AVAILABLE,
             "竞争产品数": row.get("竞争产品数"),
             "供需比": row.get("供需比"),
             "自然排名": row.get("RankOra") or row.get("自然排名") or DATA_NOT_AVAILABLE,
             "精准度": _precision_level(row.get("精准度")) if _precision_level(row.get("精准度")) != PRECISION_LEVEL_NOT_AVAILABLE else _classification_level(row.get("AI_Classification")),
             "精准原因": row.get("AI_Reason") or row.get("精准理由") or "[未提供精准理由]"}
            for row in values
        ]
    _write_ai_asset_pair(full_rows, paths, context, precision_levels=_effective_precision_levels(product_root, precision_levels))
    return paths

# --- Canonical 6-0-2 full-coverage judgment API (current runtime) ---
# Legacy dual-track helpers above remain import-compatible for older reports.

def read_current_product_text_evidence(product_root: str | Path) -> dict[str, Any]:
    """Read the complete current-product text evidence file.

    This is deliberately a direct file read.  It does not inspect online
    reports, infer product facts from keywords, or fall back to another
    Product Root file.
    """
    root = Path(product_root)
    path = root / CURRENT_PRODUCT_TEXT_RELATIVE
    base = {
        "product_root": str(root),
        "text_path": str(path),
        "source_paths": [str(path)],
        "sources": [],
        "statuses": [],
        "product_text": "",
        "fully_read": False,
    }
    if not path.is_file():
        base["status"] = CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND
        base["statuses"] = [CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND]
        return base
    try:
        text = path.read_text(encoding="utf-8")
        stat = path.stat()
    except (OSError, UnicodeError):
        base["status"] = CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED
        base["statuses"] = [CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED]
        return base
    if not text.strip():
        base["status"] = CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY
        base["statuses"] = [CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY]
        return base
    base.update({
        "status": CURRENT_PRODUCT_TEXT_EVIDENCE_READY,
        "product_text": text,
        "fully_read": True,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "content_size_bytes": len(text.encode("utf-8")),
        "modified_at_ns": stat.st_mtime_ns,
        "sources": [{"path": str(path), "kind": "CURRENT_PRODUCT_TEXT_EVIDENCE", "content": text}],
    })
    return base

def _full_source_value(row: Mapping[str, Any], *keys: str) -> Any:
    raw=_raw(row)
    for key in keys:
        value=row.get(key,raw.get(key))
        if value not in (None,""): return value
    return ""

def _specific_reason(reason: Any) -> str:
    text=str(reason or "").strip()
    generic={"","[\u672a\u63d0\u4f9b\u7cbe\u51c6\u7406\u7531]",_GENERIC_PRECISION_REASON,"fit","reason","evidence"}
    if text in generic or len(text)<8: raise ValueError("AI_PRECISION_REASON_REQUIRED")
    return text

def _full_id(row: Mapping[str, Any]) -> str:
    text=str(_full_source_value(row,"Id","record_id","\u81ea\u52a8\u7f16\u53f7")).strip()
    if not text or text.startswith("["): raise ValueError(ERP_KEYWORD_RECORD_ID_UNCONFIRMED)
    return text

def _full_judgment_row(source: Mapping[str, Any], decision: Mapping[str, Any]) -> dict[str, Any]:
    keyword = str(_full_source_value(source, "\u8bcd", "Keyword", "\u5173\u952e\u8bcd")).strip()
    if not keyword:
        raise ValueError("601_INVALID_KEYWORD")
    level = _precision_level(decision.get("精准度", decision.get("AI_Precision_Level", decision.get("Precision_Level"))))
    if level == PRECISION_LEVEL_NOT_AVAILABLE:
        raise ValueError("AI_PRECISION_LEVEL_REQUIRED")
    reason = _specific_reason(decision.get("\u7cbe\u51c6\u539f\u56e0", decision.get("AI_Reason", decision.get("Precision_Reason"))))
    # This legacy projection accepts a keyword-level row. The current formal
    # run projects all 6-0-1 observations through _observation_judgment_row.
    return {
        "Id": _full_id(source),
        "\u8bcd": keyword,
        "\u4e2d\u6587": _full_source_value(source, "\u4e2d\u6587", "KeywordCn", "\u4e2d\u6587\u540d\u79f0") or DATA_NOT_AVAILABLE,
        "\u5e02\u573a\u5bb9\u91cf": _source_passthrough_value(source, "\u5e02\u573a\u5bb9\u91cf", "SearchVolume30"),
        "\u7ade\u4e89\u4ea7\u54c1\u6570": _source_passthrough_value(source, "\u7ade\u4e89\u4ea7\u54c1\u6570", "AsinQuantity"),
        "\u4f9b\u9700\u6bd4": _source_passthrough_value(source, "\u4f9b\u9700\u6bd4", "SupplyDemandRatio"),
        "\u5bf9\u6807\u8986\u76d6\u6570": _source_passthrough_value(source, "\u5bf9\u6807\u8986\u76d6\u6570"),
        "\u6700\u4f73\u81ea\u7136\u6392\u540d": _source_passthrough_value(source, "\u6700\u4f73\u81ea\u7136\u6392\u540d"),
        "\u81ea\u7136\u6392\u540d\u4e2d\u4f4d\u6570": _source_passthrough_value(source, "\u81ea\u7136\u6392\u540d\u4e2d\u4f4d\u6570"),
        "\u7cbe\u51c6\u5ea6": level,
        "\u7cbe\u51c6\u539f\u56e0": reason,
    }

def _source_passthrough_value(row: Mapping[str, Any], *keys: str) -> Any:
    raw = _raw(row)
    for key in keys:
        if key in row:
            return row[key]
        if key in raw:
            return raw[key]
    return None

def _stable_full_sort(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    values=[dict(x) for x in rows]
    def key(row):
        volume=_search_volume(row.get("\u5e02\u573a\u5bb9\u91cf")); return (1,0.0) if volume==DATA_NOT_AVAILABLE else (0,-float(volume))
    return sorted(values,key=key)

def coverage_check(input_rows: Iterable[Mapping[str, Any]], output_rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    source_ids=[str(_full_id(x)) for x in input_rows]; output_ids=[str(x.get("Id") or "").strip() for x in output_rows]
    def counts(ids):
        out={}
        for value in ids: out[value]=out.get(value,0)+1
        return out
    src,out=counts(source_ids),counts(output_ids)
    missing=sorted(k for k,v in src.items() if out.get(k,0)<v); extra=sorted(k for k,v in out.items() if src.get(k,0)<v)
    return {"input_record_count":len(source_ids),"output_record_count":len(output_ids),"missing_record_ids":missing,"extra_record_ids":extra,"status":"PASS" if len(source_ids)==len(output_ids) and not missing and not extra else "FAIL"}

def _passthrough_values_by_id(rows: Iterable[Mapping[str, Any]], field: str) -> dict[str, Counter]:
    values: dict[str, Counter] = {}
    for row in rows:
        record_id = str(row.get("Id") or row.get("record_id") or row.get("自动编号") or "[MISSING_ID]").strip()
        value = row.get(field)
        # CSV represents SQL NULL as an empty cell; treat those two in-memory
        # forms as equivalent, while preserving every nonempty source value.
        normalized = None if value in (None, "") else str(value)
        values.setdefault(record_id, Counter())[normalized] += 1
    return values

def _observation_key(row):
    return (str(row.get("所属产品编号") or "").strip(), str(row.get("对标ASIN") or "").strip(), str(row.get("Id") or "").strip(), _normalized_keyword(row.get("词")))


def _observation_data_integrity_check(input_rows, output_a_rows, output_b_rows, output_c_rows, output_d_rows=None, *, output_e_rows=None, precision_levels: Iterable[Any] | None = None):
    source, output_a, output_b, output_c = map(list, (input_rows, output_a_rows, output_b_rows, output_c_rows))
    errors = []
    source_keys, output_keys = Counter(_observation_key(row) for row in source), Counter(_observation_key(row) for row in output_a)
    if source_keys != output_keys: errors.append(FILE_A_RECORD_COVERAGE_MISMATCH)
    original = {_observation_key(row): row for row in source}; projected = {_observation_key(row): row for row in output_a}
    for key in original.keys() & projected.keys():
        if any(str(original[key].get(field) or "") != str(projected[key].get(field) or "") for field in OBSERVATION_FINAL_COLUMNS[:-2]):
            errors.append(MULTI_BENCHMARK_PASSTHROUGH_MISMATCH); break
    judgment = {}
    for row in output_a:
        key = _normalized_keyword(row.get("词")); value = (str(row.get("精准度") or "").strip(), str(row.get("精准原因") or "").strip())
        if key in judgment and judgment[key] != value: errors.append("KEYWORD_JUDGMENT_INCONSISTENT"); break
        judgment[key] = value
    expected_b = build_high_precision_rows(output_a, precision_levels=precision_levels)
    if expected_b != output_b: errors.append("HIGH_PRECISION_FILTER_MISMATCH")
    try: expected_c = build_deduplicated_high_precision_rows(expected_b, precision_levels=precision_levels)
    except ValueError as exc: expected_c = []; errors.append(str(exc))
    expected_c_benchmark = build_deduplicated_benchmark_rows(expected_b)
    c_is_benchmark = bool(output_c) and "所属产品编号" in output_c[0]
    actual_benchmark = output_c if c_is_benchmark else []
    actual_unique = output_d_rows if c_is_benchmark and output_d_rows is not None else (output_c if not c_is_benchmark else [])
    c_keys = [(str(row.get("所属产品编号") or "").strip(), _normalized_keyword(row.get("词"))) for row in actual_benchmark]
    if len(c_keys) != len(set(c_keys)): errors.append("DUPLICATE_BENCHMARK_KEYWORD_IN_C")
    stringify_obs = lambda rows: [{column: "" if row.get(column) is None else str(row.get(column)) for column in OBSERVATION_FINAL_COLUMNS} for row in rows]
    c_pass = stringify_obs(expected_c_benchmark) == stringify_obs(actual_benchmark) if c_is_benchmark else True
    if not c_pass: errors.append("BENCHMARK_DEDUPLICATION_FAILED")
    stringify = lambda rows: [{column: "" if row.get(column) is None else str(row.get(column)) for column in DEDUPLICATED_FINAL_COLUMNS} for row in rows]
    d_pass = stringify(expected_c) == stringify(actual_unique)
    if not d_pass: errors.append("DEDUPLICATION_FAILED")
    d_results = {}
    if output_e_rows is not None:
        expected_codes = set(output_e_rows)
        source_codes = {str(row.get("所属产品编号") or "").strip() for row in output_a}
        if not source_codes.issubset(expected_codes):
            errors.append("BENCHMARK_FILE_COUNT_MISMATCH")
        total_d = 0
        for code, actual in output_e_rows.items():
            actual = list(actual)
            expected = [row for row in expected_b if str(row.get("所属产品编号") or "").strip() == code]
            actual_keys = [_normalized_keyword(row.get("词")) for row in actual]
            valid = (actual == expected
                     and all(str(row.get("所属产品编号") or "").strip() == code for row in actual)
                     and len(actual_keys) == len(set(actual_keys)))
            if not valid:
                errors.append("BENCHMARK_FILTER_DERIVATION_MISMATCH")
            total_d += len(actual)
            d_results[code] = {"expected_filtered_observation_count": len(expected),
                               "output_observation_count": len(actual), "coverage": "PASS" if valid else "FAIL"}
        expected_d_count = len(expected_b)
        if total_d != expected_d_count:
            errors.append("BENCHMARK_FILTER_COVERAGE_MISMATCH")
    return {"status": "PASS" if not errors else "FAIL", "error_codes": list(dict.fromkeys(errors)),
        "file_a": {"input_observation_count": len(source), "output_observation_count": len(output_a), "coverage": "PASS" if source_keys == output_keys else "FAIL"},
        "file_b": {"expected_high_precision_observation_count": len(expected_b), "output_observation_count": len(output_b), "coverage": "PASS" if expected_b == output_b else "FAIL"},
        "file_c": {"expected_unique_benchmark_keyword_count": len(expected_c_benchmark), "output_unique_benchmark_keyword_count": len(actual_benchmark), "deduplication": "PASS" if c_pass else "FAIL"},
        "file_d": {"expected_unique_keyword_count": len(expected_c), "output_unique_keyword_count": len(actual_unique), "deduplication": "PASS" if d_pass else "FAIL"},
        "file_e": d_results, "benchmark_output_observation_count": sum(item["output_observation_count"] for item in d_results.values())}


def data_integrity_check(input_rows, output_a_rows, output_b_rows, output_c_rows=None, *, precision_levels: Iterable[Any] | None = None):
    source, output_a, output_b = list(input_rows), list(output_a_rows), list(output_b_rows)
    if source and all("所属产品编号" in row and "对标ASIN" in row for row in source):
        return _observation_data_integrity_check(source, output_a, output_b, list(output_c_rows or []), precision_levels=precision_levels)
    expected_b = build_high_precision_rows(output_a, precision_levels=precision_levels); coverage_a = coverage_check(source, output_a); coverage_b = coverage_check(expected_b, output_b); errors = []
    if coverage_a["status"] != "PASS": errors.append(FILE_A_RECORD_COVERAGE_MISMATCH)
    if coverage_b["status"] != "PASS": errors.append(FILE_B_RECORD_COVERAGE_MISMATCH)
    for field, code in (("竞争产品数", COMPETING_PRODUCTS_PASSTHROUGH_MISMATCH), ("供需比", SUPPLY_DEMAND_RATIO_PASSTHROUGH_MISMATCH)):
        if _passthrough_values_by_id(source, field) != _passthrough_values_by_id(output_a, field) or _passthrough_values_by_id(expected_b, field) != _passthrough_values_by_id(output_b, field): errors.append(code)
    for field in ("词", "中文", "市场容量", "对标覆盖数", "最佳自然排名", "自然排名中位数"):
        if _passthrough_values_by_id(source, field) != _passthrough_values_by_id(output_a, field) or _passthrough_values_by_id(expected_b, field) != _passthrough_values_by_id(output_b, field): errors.append(MULTI_BENCHMARK_PASSTHROUGH_MISMATCH); break
    return {"status": "PASS" if not errors else "FAIL", "error_codes": errors,
        "file_a": {"input_count": coverage_a["input_record_count"], "output_count": coverage_a["output_record_count"], "coverage": coverage_a["status"]},
        "file_b": {"expected_high_precision_count": len(expected_b), "output_count": len(output_b), "coverage": coverage_b["status"]}}


def _read_formal_csv(path: str | Path, expected_columns: Iterable[str] = FULL_FINAL_COLUMNS) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(expected_columns):
            raise ValueError(OUTPUT_SCHEMA_MISMATCH)
        return list(reader)

def validate_written_outputs(input_rows, paths, *, precision_levels: Iterable[Any] | None = None):
    try:
        output_a = _read_formal_csv(paths["ai"], OBSERVATION_FINAL_COLUMNS)
        output_b = _read_formal_csv(paths["high_precision"], OBSERVATION_FINAL_COLUMNS)
        output_c = _read_formal_csv(paths["deduplicated_benchmark"], OBSERVATION_FINAL_COLUMNS)
        output_d = _read_formal_csv(paths["deduplicated"], DEDUPLICATED_FINAL_COLUMNS)
        output_e = {code: _read_formal_csv(path, OBSERVATION_FINAL_COLUMNS)
                    for code, path in paths.get("benchmarks", {}).items()}
    except ValueError as exc:
        return {"status": "FAIL", "error_codes": [str(exc) or OUTPUT_SCHEMA_MISMATCH], "file_a": {}, "file_b": {}, "file_c": {}}
    except (OSError, UnicodeError, csv.Error):
        return {"status": "FAIL", "error_codes": [OUTPUT_READBACK_FAILED], "file_a": {}, "file_b": {}, "file_c": {}}
    return _observation_data_integrity_check(input_rows, output_a, output_b, output_c, output_d, output_e_rows=output_e, precision_levels=precision_levels)


def _decision_index(decisions):
    if isinstance(decisions, Mapping): return {str(k).strip(): v for k,v in decisions.items() if isinstance(v, Mapping)}
    indexed = {}
    for item in decisions:
        if isinstance(item, Mapping):
            for field in ("Canonical_Keyword", "Id", "record_id", "词", "Keyword"):
                key = str(item.get(field) or "").strip()
                if key: indexed.setdefault(key, item)
    return indexed


def _decision_signature(decision):
    level = _precision_level(decision.get("FinalPrecision", decision.get("精准度", decision.get("AI_Precision_Level", decision.get("Precision_Level")))))
    reason = str(decision.get("FinalPrecisionReason", decision.get("精准原因", decision.get("AI_Reason", decision.get("Precision_Reason")))) or "").strip()
    status = str(decision.get("JudgmentStatus") or "SUCCESS").strip().upper()
    if status not in JUDGMENT_STATUSES:
        raise ValueError("JUDGMENT_STATUS_INVALID")
    if level == PRECISION_LEVEL_NOT_AVAILABLE:
        if status in {"REVIEW_REQUIRED", "FAILED"}:
            return "", reason or "结构化AI判断失败，必须人工复核；未生成精准度"
        raise ValueError("AI_PRECISION_LEVEL_REQUIRED")
    return level, reason


def _observation_judgment_row(source, decision):
    level, reason = _decision_signature(decision)
    return {"所属产品编号": source.get("所属产品编号"), "对标ASIN": source.get("对标ASIN"), "Id": _full_id(source),
        "词": _full_source_value(source, "词", "Keyword"), "中文": _full_source_value(source, "中文", "KeywordCn"),
        "市场容量": _source_passthrough_value(source, "市场容量", "SearchVolume30"),
        "竞争产品数": _source_passthrough_value(source, "竞争产品数", "AsinQuantity"),
        "供需比": _source_passthrough_value(source, "供需比", "SupplyDemandRatio"),
        "自然排名": _source_passthrough_value(source, "自然排名", "RankOra"), "精准度": level, "精准原因": _specific_reason(reason)}


def _benchmark_identity_map(metadata: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    codes = metadata.get("Benchmark_Codes")
    asins = metadata.get("Benchmark_ASINs") or metadata.get("BenchmarkASINs")
    product_codes = metadata.get("BenchmarkProductCodes") or {}
    if not isinstance(codes, list) or not isinstance(asins, list) or len(codes) != len(asins) or not codes:
        raise ValueError("BENCHMARK_IDENTITY_MISSING")
    if not isinstance(product_codes, Mapping):
        raise ValueError("BENCHMARK_PRODUCT_CODE_MISSING")
    identities: dict[str, dict[str, str]] = {}
    seen_benchmark_codes: set[str] = set()
    for benchmark_code, asin in zip(codes, asins):
        benchmark_code, asin = str(benchmark_code or "").strip(), str(asin or "").strip()
        product_id = str(product_codes.get(asin) or "").strip()
        if not benchmark_code or not asin or not product_id:
            raise ValueError("BENCHMARK_IDENTITY_MISSING")
        if product_id in identities or benchmark_code in seen_benchmark_codes:
            raise ValueError("BENCHMARK_IDENTITY_DUPLICATE")
        if re.search(r'[<>:"/\\|?*]', product_id) or product_id.endswith((".", " ")):
            raise ValueError("INVALID_BENCHMARK_PRODUCT_CODE_FILENAME")
        identities[product_id] = {"对标编码": benchmark_code, "对标ASIN": asin}
        seen_benchmark_codes.add(benchmark_code)
    if metadata.get("Benchmark_Count") not in (None, len(identities)):
        raise ValueError("BENCHMARK_IDENTITY_COUNT_MISMATCH")
    return identities


def _validate_benchmark_observation_uniqueness(observation_rows) -> None:
    seen: set[tuple[str, str]] = set()
    for row in observation_rows:
        code = str(row.get("所属产品编号") or "").strip()
        canonical = _normalized_keyword(row.get("词"))
        if not code or not canonical:
            raise ValueError("BENCHMARK_IDENTITY_OR_KEYWORD_MISSING")
        key = (code, canonical)
        if key in seen:
            raise ValueError("DUPLICATE_KEYWORD_WITHIN_BENCHMARK")
        seen.add(key)


def _precision_brain_record(
    keyword: str, decision: Mapping[str, Any], driver: Mapping[str, Any], benchmark_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project internal Precision Brain evidence without changing CSV columns."""
    level, reason = _decision_signature(decision)
    fields = {field: decision.get(field, DATA_NOT_AVAILABLE) for field in (
        "SearcherPrimaryIntent", "ShoppingIntentStrength", "IntentConvergence",
        "ExpectedProductType", "ExpectedCoreFunction", "ExpectedRecipient",
        "ExpectedOccasion", "ExpectedInstallationMethod", "ExpectedCriticalAttributes",
        "HardConflictType", "InitialPrecision", "BenchmarkRealityAssessment",
        "ChallengeResult", "DecisionChallenge", "FinalPrecision", "FinalPrecisionReason",
        "JudgmentStatus", "ChallengeReasonSummary",
    )}
    fields.update({
        "PrimaryPurchaseDriver": driver.get("PrimaryPurchaseDriver", DATA_NOT_AVAILABLE),
        "SecondaryPurchaseDrivers": driver.get("SecondaryPurchaseDrivers", []),
        "PurchaseDriverReason": driver.get("PurchaseDriverReason", DATA_NOT_AVAILABLE),
        **{field: decision.get(field, DATA_NOT_AVAILABLE) for field in PURCHASE_DRIVER_EVIDENCE_FIELDS + CONVERGENCE_FIELDS},
        "精准度": level,
        "FinalPrecision": decision.get("FinalPrecision", level),
        "精准原因": reason,
        "Benchmark_Reality_Evidence": dict(benchmark_evidence or {}),
    })
    return fields


def finalize_observation_judgments(observation_rows, decisions, *, evidence_context=None):
    source = list(observation_rows); groups = _benchmark_observation_groups(source); index = _decision_index(decisions); chosen = {}; units = build_keyword_judgment_units(source)
    first_decision = next((item for item in index.values() if isinstance(item, Mapping)), {})
    profile_source = (evidence_context or {}).get("product_profile") if isinstance(evidence_context, Mapping) else None
    if not profile_source and isinstance(first_decision, Mapping):
        profile_source = first_decision.get("product_profile") or first_decision.get("Current_Product_Profile") or first_decision
    purchase_driver = build_product_purchase_driver(profile_source)
    for canonical, rows in groups.items():
        first = rows[0]; keyword = str(_full_source_value(first, "词", "Keyword")).strip(); ids = list(dict.fromkeys(_full_id(row) for row in rows))
        candidates = [index[key] for key in (canonical, keyword, keyword.lower(), *ids) if key in index]
        if not candidates: raise ValueError(f"AI_DECISION_MISSING:{ids[0]}")
        if len({_decision_signature(item) for item in candidates}) != 1: raise ValueError("KEYWORD_JUDGMENT_INCONSISTENT")
        chosen[canonical] = candidates[0]
    output = [_observation_judgment_row(row, chosen[_normalized_keyword(row.get("词", row.get("Keyword")))]) for row in source]
    output = _stable_full_sort(output); high = build_high_precision_rows(output); unique = build_deduplicated_high_precision_rows(high)
    coverage = coverage_check(source, output)
    if coverage["status"] != "PASS": raise ValueError("INPUT_OUTPUT_COVERAGE_FAILED:" + json.dumps(coverage, ensure_ascii=False))
    trace = [{"Canonical_Keyword": key, "词": str(rows[0].get("词") or ""),
        **_precision_brain_record(str(rows[0].get("词") or ""), chosen[key], purchase_driver, units[i]["Benchmark_Reality_Evidence"])}
        for i,(key,rows) in enumerate(groups.items())]
    return {"rows": output, "high_precision_rows": high, "deduplicated_rows": unique, "keyword_units": units,
        "coverage": coverage, "trace": trace, "precision_brain_records": trace,
        "purchase_driver": purchase_driver, "evidence_context": dict(evidence_context or {})}


def finalize_ai_judgments(source_rows: Iterable[Mapping[str, Any]], decisions: Mapping[Any, Mapping[str, Any]] | Iterable[Mapping[str, Any]], *, evidence_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Require one final four-level AI decision and specific reason per 6-0-1 row."""
    source=list(source_rows)
    if not source: return {"rows":[],"coverage":coverage_check([],[]),"evidence_context":dict(evidence_context or {})}
    if all("所属产品编号" in row and "对标ASIN" in row for row in source): return finalize_observation_judgments(source, decisions, evidence_context=evidence_context)
    if isinstance(decisions,Mapping): decision_map={str(k).strip():v for k,v in decisions.items()}
    else:
        decision_map={}
        for item in decisions:
            if isinstance(item,Mapping):
                key=str(item.get("Id") or item.get("record_id") or item.get("\u8bcd") or item.get("Keyword") or "").strip()
                if key: decision_map[key]=item
    first_decision = next((item for item in decision_map.values() if isinstance(item, Mapping)), {})
    profile_source = (evidence_context or {}).get("product_profile") if isinstance(evidence_context, Mapping) else None
    if not profile_source and isinstance(first_decision, Mapping):
        profile_source = first_decision.get("product_profile") or first_decision.get("Current_Product_Profile") or first_decision
    purchase_driver = build_product_purchase_driver(profile_source)
    projected=[]; trace=[]
    for row in source:
        rid=_full_id(row); keyword=str(_full_source_value(row,"\u8bcd","Keyword","\u5173\u952e\u8bcd")).strip(); decision=decision_map.get(rid)
        if decision is None: decision=decision_map.get(keyword) or decision_map.get(keyword.lower())
        if not isinstance(decision,Mapping): raise ValueError(f"AI_DECISION_MISSING:{rid}")
        final=_full_judgment_row(row,decision); projected.append(final)
        trace.append({"Id":rid,"\u8bcd":keyword,"Search_Intent":decision.get("Search_Intent",DATA_NOT_AVAILABLE),"Product_Intent_Fit":decision.get("Product_Intent_Fit",DATA_NOT_AVAILABLE),"Hard_Conflict":decision.get("Hard_Conflict",DATA_NOT_AVAILABLE),"\u7cbe\u51c6\u5ea6":final["\u7cbe\u51c6\u5ea6"],"\u7cbe\u51c6\u539f\u56e0":final["\u7cbe\u51c6\u539f\u56e0"],"Evidence_Sources":(evidence_context or {}).get("source_paths",[]), **_precision_brain_record(keyword, decision, purchase_driver)})
    ordered=_stable_full_sort(projected); coverage=coverage_check(source,ordered)
    if coverage["status"]!="PASS": raise ValueError("INPUT_OUTPUT_COVERAGE_FAILED:"+json.dumps(coverage,ensure_ascii=False))
    return {"rows":ordered,"coverage":coverage,"trace":trace,"precision_brain_records":trace,"purchase_driver":purchase_driver,"evidence_context":dict(evidence_context or {})}

def _write_ai_asset_pair(rows, paths, context, *, lineage=None, write_metadata=True, create_folder=True, precision_levels: Iterable[Any] | None = None):
    # 602 package metadata lives in the shared Run Manifest, never in per-CSV sidecars.
    values = list(rows)
    if values and not all("所属产品编号" in row and "对标ASIN" in row for row in values):
        values = [{"所属产品编号":"", "对标ASIN":"", "Id":row.get("Id"), "词":row.get("词",row.get("Keyword","")),
            "中文":row.get("中文",row.get("KeywordCn","")), "市场容量":row.get("市场容量",row.get("SearchVolume30")),
            "竞争产品数":row.get("竞争产品数"), "供需比":row.get("供需比"), "自然排名":row.get("自然排名",row.get("最佳自然排名","")),
            "精准度":row.get("精准度"), "精准原因":row.get("精准原因")} for row in values]
    selected = build_high_precision_rows(values, precision_levels=precision_levels)
    benchmark_unique = build_deduplicated_benchmark_rows(selected)
    unique = build_deduplicated_high_precision_rows(selected, precision_levels=precision_levels); folder = paths["ai"].parent
    benchmark_rows = {
        code: [row for row in selected if str(row.get("所属产品编号") or "").strip() == code]
        for code in paths.get("benchmarks", {})
    }
    if create_folder: folder.mkdir(parents=True, exist_ok=True)
    keys=("ai","high_precision","deduplicated_benchmark","deduplicated"); staged={key:Path(str(paths[key])+".tmp") for key in keys}
    staged_benchmarks = {code: Path(str(path) + ".tmp") for code, path in paths.get("benchmarks", {}).items()}
    output_paths_all = [*(paths[key] for key in keys), *paths.get("benchmarks", {}).values()]
    assert_new_outputs([*output_paths_all, *staged.values(), *staged_benchmarks.values()])
    write_csv(staged["ai"], values, columns=OBSERVATION_FINAL_COLUMNS)
    write_csv(staged["high_precision"], selected, columns=OBSERVATION_FINAL_COLUMNS)
    write_csv(staged["deduplicated_benchmark"], benchmark_unique, columns=OBSERVATION_FINAL_COLUMNS)
    write_csv(staged["deduplicated"], unique, columns=DEDUPLICATED_FINAL_COLUMNS)
    for code, temporary in staged_benchmarks.items():
        write_csv(temporary, benchmark_rows[code], columns=OBSERVATION_FINAL_COLUMNS)
    for key in keys: os.replace(staged[key], paths[key])
    for code, temporary in staged_benchmarks.items(): os.replace(temporary, paths["benchmarks"][code])
    return dict(paths)


def write_full_ai_csv(
    product_root: str | Path,
    product_code: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    run_context=None,
    write_metadata: bool = True,
    precision_levels: Iterable[Any] | None = None,
) -> Path:
    values = list(rows)
    context = run_context or new_602_run_context(product_root, product_code)
    benchmark_codes = sorted({str(row.get("所属产品编号") or "").strip() for row in values if str(row.get("所属产品编号") or "").strip()})
    report_root = resolve_skill_report_dir(product_root, Path(__file__).resolve().parents[1])
    build_folder = governance_paths(report_root)["staging"] / f"{context.run_timestamp}_build"
    build_folder.mkdir(parents=True, exist_ok=False)
    paths = output_paths(product_root, product_code, context, benchmark_product_codes=benchmark_codes,
                         output_directory=build_folder)
    effective_levels = _effective_precision_levels(product_root, precision_levels)
    config_info = read_precision_filter_config(product_root, require=False)
    _write_ai_asset_pair(values, paths, context, write_metadata=write_metadata,
                         precision_levels=effective_levels)
    all_output_paths = [paths["ai"], paths["high_precision"], paths["deduplicated_benchmark"], paths["deduplicated"], *paths.get("benchmarks", {}).values()]
    high_rows = [row for row in values if str(row.get("精准度") or "").strip() in effective_levels]
    unique_rows = {str(row.get("词") or "").strip().casefold() for row in high_rows}
    benchmark_identities = {}
    for code in benchmark_codes:
        row = next((item for item in values if str(item.get("所属产品编号") or "").strip() == code), {})
        benchmark_identities[code] = {"对标编码": code, "对标ASIN": str(row.get("对标ASIN") or "DATA_NOT_AVAILABLE")}
    manifest_path = build_folder / f"{RUN_MANIFEST_PREFIX}{context.run_timestamp}.json"
    manifest = {
        "SkillId": SIX_0_2_SKILL_ID, "Current Product": product_code,
        "RUN_ID": context.run_id, "RUN_TIMESTAMP": context.run_timestamp,
        "GeneratedAt": context.generated_at, "Input Source": "CALLER_SUPPLIED_ROWS",
        "Input Skill": "CALLER_SUPPLIED", "Input Run ID": context.run_id,
        "Input RUN_TIMESTAMP": context.run_timestamp, "Input Folder": str(build_folder),
        "Input File": "CALLER_SUPPLIED_ROWS", "Product Text Input": "DATA_NOT_AVAILABLE",
        "Input Record Count": len(values),
        "Input Unique Keyword Count": len({str(row.get("词") or "").strip().casefold() for row in values}),
        "Output Folder": str(build_folder), "Output Files": [path.name for path in all_output_paths],
        "Precision Filter Levels": sorted(effective_levels),
        "Precision Library Configuration": {
            "Path": str(config_info.get("path") or ""),
            "SelectedPrecisionLevelsRaw": config_info.get("raw_levels", []),
            "SelectedPrecisionLevelsNormalized": list(effective_levels),
        },
        "Benchmark Count": len(benchmark_codes),
        "Expected Benchmark Count": len(benchmark_codes), "Benchmark Product Codes": benchmark_codes,
        "Benchmark Identities": benchmark_identities,
        "Expected Benchmark Files": [path.name for path in paths.get("benchmarks", {}).values()],
        "GeneratedBenchmarkFiles": [path.name for path in paths.get("benchmarks", {}).values()],
        "Record Counts": {"Input Observation Count": len(values), "Input Unique Keyword Count": len({str(row.get("词") or "").strip().casefold() for row in values}),
                          "AI Record Count": len(values), "Filtered Benchmark Observation Count": len(high_rows),
                          "Unique Selected Precision Keyword Count": len(unique_rows)},
        "Output Record Counts": {"AI Precision Observation Count": len(values),
                                 "Filtered Benchmark Observation Count": sum(1 for row in values if str(row.get("精准度") or "").strip() in effective_levels),
                                 "Unique Selected Precision Keyword Count": len({str(row.get("词") or "").strip().casefold() for row in values if str(row.get("精准度") or "").strip() in effective_levels})},
        "Run Status": "VALID",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    published = publish_latest_valid_batch(
        report_root, context.run_timestamp,
        all_output_paths, manifest_files=[manifest_path],
        registry_payload={"Skill_ID": SIX_0_2_SKILL_ID, "Product_Code": product_code,
                          "RUN_ID": context.run_id, "RUN_TIMESTAMP": context.run_timestamp,
                          "Report_Identities": ["AI_PRECISION_OBSERVATIONS", "FILTERED_BENCHMARK_PRECISION_KEYWORDS", "DEDUPLICATED_FILTERED_BENCHMARK_KEYWORDS", "UNIQUE_SELECTED_PRECISION_KEYWORDS"] + [f"BENCHMARK_SELECTED_PRECISION_{code}" for code in benchmark_codes],
                          "Files": [path.name for path in all_output_paths]},
        move_sources=True,
    )
    manifest_target = Path(published["manifest_files"][0])
    published_manifest = json.loads(manifest_target.read_text(encoding="utf-8-sig"))
    published_manifest["Output Folder"] = str(Path(published["data_dir"]))
    manifest_target.write_text(json.dumps(published_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(build_folder, ignore_errors=True)
    return Path(published["data_dir"]) / paths["ai"].name


def _write_run_manifest(run_folder: Path, manifest: Mapping[str, Any]) -> Path:
    stamp = str(manifest.get("RUN_TIMESTAMP") or "").strip()
    if not re.fullmatch(r"\d{8}_\d{6}", stamp):
        raise ValueError("RUN_TIMESTAMP must match YYYYMMDD_HHMMSS")
    target = run_folder / f"{RUN_MANIFEST_PREFIX}{stamp}.json"
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target


def prepare_602(product_root: str | Path, product_code: str) -> dict[str, Any]:
    """PREPARE: collect and validate facts without making semantic judgments.

    The returned package is the handoff to the currently running Agent.  It
    deliberately contains no InitialPrecision, FinalPrecision, ProductMissionFit
    or HardConflict conclusion.
    """
    root = Path(product_root)
    evidence = read_current_product_text_evidence(root)
    if evidence.get("status") != CURRENT_PRODUCT_TEXT_EVIDENCE_READY:
        raise FileNotFoundError(str(evidence.get("status") or CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED))
    resolved = resolve_latest_601_keyword_output(root, product_code=product_code)
    if resolved.get("status") != SIX_0_1_KEYWORD_OUTPUT_READY:
        raise FileNotFoundError(str(resolved.get("status") or SIX_0_1_KEYWORD_OUTPUT_NOT_FOUND))
    input_rows = list(resolved.get("rows") or [])
    metadata = resolved.get("input_metadata") or {}
    try:
        identities = _benchmark_identity_map(metadata)
    except ValueError:
        identities = {}
        for row in input_rows:
            code = str(row.get("所属产品编号") or "").strip()
            asin = str(row.get("对标ASIN") or "").strip()
            if code and asin:
                if code in identities and identities[code].get("对标ASIN") != asin:
                    raise ValueError("BENCHMARK_IDENTITY_DUPLICATE")
                identities[code] = {"对标编码": code, "对标ASIN": asin}
        if not identities:
            raise ValueError("BENCHMARK_IDENTITY_MISSING")
    _validate_benchmark_observation_uniqueness(input_rows)
    if not {str(row.get("所属产品编号") or "").strip() for row in input_rows}.issubset(identities):
        raise ValueError("BENCHMARK_IDENTITY_MISSING")
    units = build_keyword_judgment_units(input_rows)
    profile_chars = max(1, len(str(evidence.get("product_text") or "")))
    average_keyword_chars = (sum(len(str(item.get("词") or "")) for item in units) / len(units)) if units else 0
    p95_keyword_chars = sorted((len(str(item.get("词") or "")) for item in units))[max(0, int(len(units) * 0.95) - 1)] if units else 0
    suggested_batch_size = max(1, min(32, 32000 // max(800, profile_chars + int(average_keyword_chars * 20) + int(p95_keyword_chars * 10))))
    return {
        "product_root": str(root),
        "product_code": product_code,
        "product_evidence": evidence,
        "input_rows": input_rows,
        "input_metadata": metadata,
        "resolved_601": resolved,
        "benchmark_identities": identities,
        "keyword_units": units,
        "product_evidence_package": {"text_path": evidence.get("text_path"), "content_sha256": evidence.get("content_sha256"), "product_text": evidence.get("product_text")},
        "adaptive_batch_plan": {"suggested_batch_size": suggested_batch_size, "keyword_count": len(units), "average_keyword_chars": average_keyword_chars, "p95_keyword_chars": p95_keyword_chars, "product_profile_chars": profile_chars},
    }


def _v4_judgment_records(judgments: Mapping[Any, Mapping[str, Any]] | Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize the one-shot Agent response without judging or remapping semantics."""
    if isinstance(judgments, Mapping):
        values = []
        for key, value in judgments.items():
            if not isinstance(value, Mapping):
                raise ValueError("AI_PRECISION_JUDGMENT_SCHEMA_INVALID")
            item = dict(value)
            item.setdefault("JudgmentItemId", str(key).strip())
            values.append(item)
        return values
    values = list(judgments or [])
    if not all(isinstance(item, Mapping) for item in values):
        raise ValueError("AI_PRECISION_JUDGMENT_SCHEMA_INVALID")
    return [dict(item) for item in values]


def audit_legacy_checkpoint(path: str | Path, *, prepared: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Audit a V3 checkpoint; never silently mix it into a V4 run."""
    target = Path(path)
    if not target.is_file():
        return {"status": "NOT_FOUND", "path": str(target)}
    try:
        payload = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"status": "LEGACY_CHECKPOINT_INCOMPATIBLE", "reason": "SCHEMA_INVALID", "path": str(target)}
    if not isinstance(payload, Mapping):
        return {"status": "LEGACY_CHECKPOINT_INCOMPATIBLE", "reason": "SCHEMA_INVALID", "path": str(target)}
    records = payload.get("records") or {}
    required = {"schema", "ProductProfileId", "BrainVersion", "TotalUniqueKeywordCount", "records"}
    compatible = payload.get("schema") == V4_CHECKPOINT_SCHEMA and required.issubset(payload)
    if prepared is not None and payload.get("TotalUniqueKeywordCount") != len(prepared.get("keyword_units") or []):
        compatible = False
    return {"status": "COMPATIBLE" if compatible else "LEGACY_CHECKPOINT_INCOMPATIBLE",
            "path": str(target), "schema": payload.get("schema"),
            "record_count": len(records), "total_unique": payload.get("TotalUniqueKeywordCount"),
            "brain_version": payload.get("BrainVersion"), "product_profile_id": payload.get("ProductProfileId")}


def run_602(
    product_root: str | Path,
    product_code: str,
    *,
    ai_judge: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """V4's single complete business entry: PREPARE → AI → APPLY → PUBLISH.

    ``ai_judge`` is an internal current-Agent handoff.  It must return one
    validated Product Profile and one structured judgment for every unique
    ``JudgmentItemId``.  No local rule or partial queue is accepted here.
    """
    if ai_judge is None:
        raise RuntimeError(AI_PRECISION_JUDGMENT_UNAVAILABLE)
    prepared = prepare_602(product_root, product_code)
    handoff = ai_judge({**prepared, "ExecutionMode": "V4_COMPLETE_602_TASK",
                        "JudgmentContract": "ONE_JUDGMENT_PER_UNIQUE_KEYWORD"})
    if not isinstance(handoff, Mapping):
        raise ValueError("AI_PRECISION_JUDGMENT_SCHEMA_INVALID")
    raw_profile = handoff.get("product_profile") or handoff.get("ProductProfile")
    if not isinstance(raw_profile, Mapping):
        raise ValueError("AI_PRECISION_JUDGMENT_SCHEMA_INVALID")
    profile = validate_product_profile(raw_profile)
    raw_judgments = handoff.get("judgments")
    if raw_judgments is None:
        raw_judgments = handoff.get("structured_judgments")
    records = _v4_judgment_records(raw_judgments)
    expected_ids = [str(item["JudgmentItemId"]) for item in prepared["keyword_units"]]
    validated = validate_structured_judgments(records, expected_ids, phase="A")
    allowed_reality = {"SUPPORTS", "WEAKLY_SUPPORTS", "NEUTRAL", "CONTRADICTS", "INSUFFICIENT"}
    if any(str(item.get("BenchmarkRealityAssessment") or "").strip().upper() not in allowed_reality for item in validated.values()):
        raise ValueError("AI_PRECISION_JUDGMENT_SCHEMA_INVALID")
    # Phase-B evidence and challenge fields are validated as part of the same
    # typed record; the semantic FinalPrecision remains the Agent's decision.
    canonical_by_id = {str(item["JudgmentItemId"]): str(item["Canonical_Keyword"]) for item in prepared["keyword_units"]}
    decisions = {canonical_by_id[item_id]: judgment for item_id, judgment in validated.items()}
    prepared["product_profile"] = profile
    prepared["_v4_execution"] = True
    result = run_current_602(product_root, product_code, prepared=prepared, agent_judgments=decisions)
    result.update({"execution_mode": "V4_COMPLETE_602_TASK",
                   "ai_judgment_count": len(validated),
                   "pending_judgment_count": 0,
                   "v4_contract": "PREPARE→AI JUDGE ALL UNIQUE→APPLY→PUBLISH"})
    return result


def apply_602_judgments(
    prepared: Mapping[str, Any],
    structured_judgments: Mapping[Any, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """APPLY handoff contract for Agent-produced structured judgments.

    This function validates and projects Agent output only; it never changes a
    FinalPrecision value and never performs semantic judgment itself.
    """
    rows = list(prepared.get("input_rows") or [])
    result = finalize_observation_judgments(rows, structured_judgments, evidence_context={
        "product_profile": prepared.get("product_profile"),
        "product_text": (prepared.get("product_evidence") or {}).get("product_text"),
    })
    levels = frozenset(read_precision_filter_config(prepared["product_root"], require=True)["levels"])
    result["high_precision_rows"] = build_high_precision_rows(result["rows"], precision_levels=levels)
    result["deduplicated_benchmark_rows"] = build_deduplicated_benchmark_rows(result["high_precision_rows"])
    result["deduplicated_rows"] = build_deduplicated_high_precision_rows(result["high_precision_rows"], precision_levels=levels)
    return result


def run_current_602_agent(
    product_root: str | Path,
    product_code: str,
    *,
    agent_judge: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    agent_batch_judge: Callable[[Mapping[str, Any], list[Mapping[str, Any]], str], Iterable[Mapping[str, Any]]] | None = None,
    checkpoint: str | Path | None = None,
) -> dict[str, Any]:
    """Deprecated V3 compatibility entry; use :func:`run_602` for production.

    The callback represents the Codex/Agent performing Product Profile,
    Phase-A, Phase-B and Challenge. It is intentionally not an HTTP/provider
    client and is not a user-supplied precision decision shortcut.
    """
    if agent_judge is None:
        raise RuntimeError(AGENT_JUDGMENT_UNAVAILABLE)
    prepared = prepare_602(product_root, product_code)

    # A complete production task may provide a profile callback plus a
    # per-batch Agent callback.  Keep the whole drain inside this function so
    # callers do not have to expose GET/SAVE/RESUME as user interactions.
    if agent_batch_judge is not None:
        profile_result = agent_judge({**prepared, "ExecutionPhase": "PRODUCT_PROFILE"})
        if not isinstance(profile_result, Mapping):
            raise ValueError("AGENT_JUDGMENT_SCHEMA_INVALID")
        profile = validate_product_profile(profile_result.get("product_profile") or profile_result.get("ProductProfile") or {})
        return run_current_602_production(
            product_root,
            product_code,
            product_profile=profile,
            agent_batch_judge=agent_batch_judge,
            checkpoint=checkpoint,
        )

    return run_602(product_root, product_code, ai_judge=agent_judge)


def production_checkpoint_path(product_root: str | Path, product_code: str) -> Path:
    """Return the resumable cache for expensive Agent judgments."""
    report_root = resolve_skill_report_dir(Path(product_root), Path(__file__).resolve().parents[1])
    target = report_root / "_system" / "checkpoints" / f"6-0-2_{product_code}_production_judgments.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


BATCH_SIZE_CONFIG_PATH = Path("E:/") / "\u3010\u6240\u6709\u4ea7\u54c1\u76ee\u5f55\u4e13\u7528\u3011" / "01_\u516c\u5171\u8d44\u6599" / "03_\u7cfb\u7edf\u914d\u7f6e" / "602_AI\u6279\u6b21\u5927\u5c0f.txt"


def read_602_batch_size(path: str | Path = BATCH_SIZE_CONFIG_PATH) -> dict[str, Any]:
    """Read the operator throughput setting without making it a business rule."""
    target = Path(path)
    if not target.is_file():
        return {"RequestedBatchSize": None,
                "ConfigStatus": "602_BATCH_SIZE_CONFIG_MISSING",
                "ConfigPath": str(target)}
    try:
        raw = target.read_text(encoding="utf-8-sig").strip()
        value = int(raw)
    except (OSError, UnicodeError, ValueError):
        return {"RequestedBatchSize": None,
                "ConfigStatus": "602_BATCH_SIZE_CONFIG_INVALID",
                "ConfigPath": str(target)}
    if value <= 0:
        return {"RequestedBatchSize": None,
                "ConfigStatus": "602_BATCH_SIZE_CONFIG_INVALID",
                "ConfigPath": str(target)}
    return {"RequestedBatchSize": value, "ConfigStatus": "OK", "ConfigPath": str(target)}


def load_production_checkpoint(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.is_file():
        return {"schema": PRODUCTION_CHECKPOINT_SCHEMA, "records": {}}
    try:
        payload = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("PRODUCTION_CHECKPOINT_INVALID") from exc
    if not isinstance(payload, Mapping) or payload.get("schema") != PRODUCTION_CHECKPOINT_SCHEMA or not isinstance(payload.get("records"), Mapping):
        raise ValueError("PRODUCTION_CHECKPOINT_INVALID")
    return dict(payload)


def save_production_checkpoint(path: str | Path, payload: Mapping[str, Any]) -> Path:
    """Atomically persist completed Agent results for resume."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target


def _production_batch_call(agent_batch_judge, profile, batch, phase):
    response = agent_batch_judge(profile, batch, phase)
    if isinstance(response, Mapping):
        response = response.get("judgments") or response.get("records") or []
    return list(response or [])


def run_current_602_production(
    product_root: str | Path,
    product_code: str,
    *,
    product_profile: Mapping[str, Any],
    agent_batch_judge: Callable[[Mapping[str, Any], list[Mapping[str, Any]], str], Iterable[Mapping[str, Any]]],
    initial_judgments: Mapping[str, Mapping[str, Any]] | None = None,
    calibration_sizes: Iterable[int] = DEFAULT_SAFE_BATCH_PROBES,
    checkpoint: str | Path | None = None,
    resume: bool = True,
) -> dict[str, Any]:
    """Compatibility/test runner; normal production orchestration belongs to the current Agent.

    The Agent owns the COMPLETE_602_TASK loop. This helper keeps deterministic
    calibration/checkpoint behavior for tests and injected adapters only.
    """
    prepared = prepare_602(product_root, product_code)
    profile = validate_product_profile(product_profile)
    units = list(prepared["keyword_units"])
    path = Path(checkpoint) if checkpoint else production_checkpoint_path(product_root, product_code)
    state = load_production_checkpoint(path) if resume else {"schema": PRODUCTION_CHECKPOINT_SCHEMA, "records": {}}
    records = dict(state.get("records") or {})
    for item_id, judgment in (initial_judgments or {}).items():
        records[str(item_id)] = {**dict(judgment), "JudgmentItemId": str(item_id), "Status": str(judgment.get("JudgmentStatus") or "SUCCESS")}
    state.update({"schema": PRODUCTION_CHECKPOINT_SCHEMA, "Product_Code": product_code,
                  "ProductProfileId": profile.get("ProductProfileId", DATA_NOT_AVAILABLE),
                  "BrainVersion": "CURRENT_FROZEN_BRAIN", "records": records})
    save_production_checkpoint(path, state)
    pending = [u for u in units if str(u["JudgmentItemId"]) not in records or records[str(u["JudgmentItemId"])].get("Status") in {"PENDING_JUDGMENT", "RUNNING", "FAILED"}]
    calibration, selected_batch = [], None
    sample_source = pending[:]
    for candidate in calibration_sizes:
        candidate = int(candidate)
        if candidate <= 0 or not sample_source:
            continue
        sample = sample_source[:candidate]; ids = [str(u["JudgmentItemId"]) for u in sample]
        try:
            validate_structured_judgments(_production_batch_call(agent_batch_judge, profile, sample, "A"), ids, phase="A")
            validate_structured_judgments(_production_batch_call(agent_batch_judge, profile, sample, "B"), ids, phase="B")
            calibration.append({"batch_size": candidate, "status": "PASS"}); selected_batch = candidate
        except Exception as exc:
            calibration.append({"batch_size": candidate, "status": "FAIL", "error": str(exc)})
    if selected_batch is None:
        return {"status": "FAILED", "reason": "AGENT_BATCH_CALIBRATION_FAILED", "checkpoint": str(path), "calibration": calibration, "pending_count": len(pending)}
    state["AdaptiveSafeBatchSize"] = selected_batch
    state["Calibration"] = calibration
    save_production_checkpoint(path, state)
    production_batches = 0; retries = 0; index = 0
    while index < len(pending):
        batch = pending[index:index + selected_batch]; ids = [str(u["JudgmentItemId"]) for u in batch]
        try:
            phase_a = validate_structured_judgments(_production_batch_call(agent_batch_judge, profile, batch, "A"), ids, phase="A")
            phase_b = validate_structured_judgments(_production_batch_call(agent_batch_judge, profile, batch, "B"), ids, phase="B")
            for item_id in ids:
                item = dict(phase_a[item_id]); item["BenchmarkRealityAssessment"] = phase_b[item_id]["BenchmarkRealityAssessment"]
                records[item_id] = {**item, "Status": item.get("JudgmentStatus", "SUCCESS"), "CompletedAt": datetime.now().isoformat(timespec="seconds")}
            production_batches += 1; index += len(batch); state["records"] = records; save_production_checkpoint(path, state)
        except Exception:
            if len(batch) > 1:
                retries += 1; selected_batch = max(1, selected_batch // 2); continue
            item_id = ids[0]
            records[item_id] = {"JudgmentItemId": item_id, "FinalPrecision": DATA_NOT_AVAILABLE, "FinalPrecisionReason": "Agent执行失败且Retry后仍失败，需人工复核。", "JudgmentStatus": "FAILED", "Status": "FAILED"}
            index += 1; state["records"] = records; save_production_checkpoint(path, state)
    unresolved = [u for u in units if str(u["JudgmentItemId"]) not in records or records[str(u["JudgmentItemId"])].get("Status") in {"PENDING_JUDGMENT", "RUNNING"}]
    failed = [r for r in records.values() if r.get("Status") == "FAILED"]
    if unresolved or failed:
        return {"status": "PENDING" if unresolved else "FAILED", "checkpoint": str(path), "calibration": calibration, "production_batch_size": selected_batch, "production_batches": production_batches, "retry_count": retries, "pending_count": len(unresolved), "failed_count": len(failed)}
    judgments = {item_id: {k: v for k, v in record.items() if k not in {"Status", "CompletedAt"}} for item_id, record in records.items()}
    result = run_current_602(product_root, product_code, prepared=prepared, agent_judgments=judgments)
    result.update({"production_checkpoint": str(path), "calibration": calibration, "production_batch_size": selected_batch, "production_batches": production_batches, "retry_count": retries})
    return result


def get_602_production_status(product_root: str | Path, product_code: str, *, checkpoint: str | Path | None = None) -> dict[str, Any]:
    """Deterministically report queue state; never performs an AI judgment."""
    path = Path(checkpoint) if checkpoint else production_checkpoint_path(product_root, product_code)
    state = load_production_checkpoint(path)
    records = list((state.get("records") or {}).values())
    counts = Counter(str(item.get("Status") or item.get("JudgmentStatus") or "PENDING_JUDGMENT") for item in records)
    total = int(state.get("TotalUniqueKeywordCount") or len(records))
    pending = max(0, total - sum(counts.values()) + counts.get("PENDING_JUDGMENT", 0))
    return {"ProductProfileId": state.get("ProductProfileId", DATA_NOT_AVAILABLE), "BrainVersion": state.get("BrainVersion", "CURRENT_FROZEN_BRAIN"),
            "TotalUnique": total, "SuccessCount": counts.get("SUCCESS", 0), "PendingCount": pending,
            "PendingJudgmentCount": pending,
            "ReviewRequiredCount": counts.get("REVIEW_REQUIRED", 0), "FailedCount": counts.get("FAILED", 0),
            "CheckpointPath": str(path), "CurrentBatchSize": state.get("CurrentBatchSize", DATA_NOT_AVAILABLE),
            "PublishStatus": state.get("PublishStatus", "NOT_PUBLISHED"), "Calibration": state.get("Calibration", []),
            "NextAvailable": pending > 0}


def get_next_602_batch(product_root: str | Path, product_code: str, *, batch_size: int | None = None, checkpoint: str | Path | None = None) -> dict[str, Any]:
    """Return the next pending Agent task; Python does not judge it."""
    prepared = prepare_602(product_root, product_code)
    path = Path(checkpoint) if checkpoint else production_checkpoint_path(product_root, product_code)
    state = load_production_checkpoint(path)
    records = state.get("records") or {}
    pending = [item for item in prepared["keyword_units"] if str(item["JudgmentItemId"]) not in records or records[str(item["JudgmentItemId"])].get("Status") == "PENDING_JUDGMENT"]
    # CurrentBatchSize is a last-run observation, not a permanent limit.  A
    # stale small value in an interrupted checkpoint must not pin every later
    # pull to that size; prefer the current run's adaptive plan unless an
    # explicitly calibrated AdaptiveSafeBatchSize is present.
    configured = read_602_batch_size()
    if configured["ConfigStatus"] != "OK":
        raise ValueError(configured["ConfigStatus"])
    explicit_safe_size = state.get("AdaptiveSafeBatchSize")
    if explicit_safe_size:
        adaptive_size = explicit_safe_size
    else:
        # A prepared plan may be conservative when the stored product profile
        # is unavailable.  Preserve the last successful observed size in that
        # case, while still allowing the current plan to grow the queue.
        suggested_size = prepared.get("adaptive_batch_plan", {}).get("suggested_batch_size") or 0
        observed_size = state.get("CurrentBatchSize") or 0
        adaptive_size = int(configured["RequestedBatchSize"])
    requested_size = int(configured["RequestedBatchSize"])
    size = min(max(1, requested_size), len(pending)) if pending else 0
    selected = pending[:size]
    profile = state.get("ProductProfile") or prepared.get("product_profile") or {}
    return {"status": "PENDING" if selected else "EMPTY", "BatchId": f"602-{product_code}-{len(records)+1:04d}",
            "ProductCode": product_code, "ProductProfileId": state.get("ProductProfileId", DATA_NOT_AVAILABLE),
            "BrainVersion": state.get("BrainVersion", "CURRENT_FROZEN_BRAIN"),
            "ConfiguredBatchSize": int(configured["RequestedBatchSize"]),
            "ActualBatchSize": size, "PendingBefore": len(pending),
            "ProcessedCount": 0, "PendingAfter": len(pending), "BatchSize": size,
            "ProductProfile": profile, "items": selected, "checkpoint": str(path)}


def save_602_batch_judgments(product_root: str | Path, product_code: str, batch: Mapping[str, Any], judgments: Iterable[Mapping[str, Any]], *, checkpoint: str | Path | None = None) -> dict[str, Any]:
    """Validate and persist one Agent-produced batch without changing labels."""
    path = Path(checkpoint or batch.get("checkpoint") or production_checkpoint_path(product_root, product_code))
    state = load_production_checkpoint(path); records = dict(state.get("records") or {})
    items = list(batch.get("items") or []); ids = [str(item.get("JudgmentItemId")) for item in items]
    incoming = validate_structured_judgments(judgments, ids)
    expected_profile = str(state.get("ProductProfileId") or batch.get("ProductProfileId") or DATA_NOT_AVAILABLE)
    expected_brain = str(state.get("BrainVersion") or batch.get("BrainVersion") or "CURRENT_FROZEN_BRAIN")
    for item_id, judgment in incoming.items():
        profile_id = str(judgment.get("ProductProfileId") or expected_profile)
        brain_version = str(judgment.get("BrainVersion") or expected_brain)
        if profile_id != expected_profile or brain_version != expected_brain:
            raise ValueError("AGENT_JUDGMENT_CONTEXT_MISMATCH")
        records[item_id] = {**dict(judgment), "JudgmentItemId": item_id, "Status": judgment.get("JudgmentStatus", "SUCCESS"),
                            "ProductProfileId": profile_id, "BrainVersion": brain_version, "BatchId": batch.get("BatchId"),
                            "CompletedAt": datetime.now().isoformat(timespec="seconds")}
    state["records"] = records; state["CurrentBatchSize"] = len(items); state["LastBatchId"] = batch.get("BatchId")
    save_production_checkpoint(path, state)
    result = get_602_production_status(product_root, product_code, checkpoint=path)
    result.update({"ConfiguredBatchSize": batch.get("ConfiguredBatchSize"),
                   "ActualBatchSize": len(items), "PendingBefore": len(items),
                   "ProcessedCount": len(incoming),
                   "PendingAfter": result.get("PendingCount")})
    return result


def finalize_602(product_root: str | Path, product_code: str, *, checkpoint: str | Path | None = None) -> dict[str, Any]:
    """Finalize only after the pull queue has no pending items."""
    status = get_602_production_status(product_root, product_code, checkpoint=checkpoint)
    if status["PendingCount"] != 0:
        return {"status": "PENDING", **status}
    if status["FailedCount"]:
        return {"status": "FAILED", **status}
    state = load_production_checkpoint(status["CheckpointPath"])
    judgments = {item_id: {k: v for k, v in record.items() if k not in {"Status", "CompletedAt", "BatchId", "ProductProfileId", "BrainVersion"}}
                 for item_id, record in (state.get("records") or {}).items()}
    prepared = prepare_602(product_root, product_code)
    result = run_current_602(product_root, product_code, prepared=prepared, agent_judgments=judgments)
    state["PublishStatus"] = "PUBLISHED"; save_production_checkpoint(status["CheckpointPath"], state)
    result["production_checkpoint"] = status["CheckpointPath"]
    return result


def codex_cli_schema_path() -> Path:
    return SCRIPT_DIR / "codex_cli_production_schema.json"


def _cli_batch_payload(prepared: Mapping[str, Any], state: Mapping[str, Any], batch: Mapping[str, Any]) -> dict[str, Any]:
    """Build a compact, auditable prompt payload; no hidden chain-of-thought requested."""
    evidence = prepared.get("product_evidence") or {}
    items = []
    for item in batch.get("items") or []:
        items.append({
            "JudgmentItemId": item.get("JudgmentItemId"),
            "Keyword": item.get("Keyword") or item.get("词"),
            "KeywordCn": item.get("KeywordCn") or item.get("中文"),
            "BenchmarkRealityEvidence": item.get("Benchmark_Reality_Evidence") or {},
        })
    return {
        "Task": "6-0-2 Precision Judgment batch",
        "BatchId": batch.get("BatchId"),
        "ProductProfileId": state.get("ProductProfileId") or DATA_NOT_AVAILABLE,
        "BrainVersion": state.get("BrainVersion") or "CURRENT_FROZEN_BRAIN",
        "SEMANTIC_EVIDENCE": {
            "CurrentProductText": evidence.get("product_text") or "",
            "Rule": "First reconstruct Searcher Purchase Mission and Product-Intent Fit. Distinguish CORE FIT from CAN SERVE. Check every Hard Modifier and Decision Challenge."
        },
        "SECOND_STAGE_BENCHMARK_REALITY": {
            "Rule": "Use rank only as supporting reality evidence. Rank must never directly set FinalPrecision or override a hard conflict."
        },
        "PrecisionLevels": list(PRECISION_LEVELS),
        "JudgmentStatuses": sorted(JUDGMENT_STATUSES),
        "OutputRule": "Return only concise auditable ShortReason and the required JSON fields; do not output hidden chain-of-thought.",
        "Judgments": items,
    }


def _normalize_cli_judgments(response: Mapping[str, Any], batch: Mapping[str, Any], state: Mapping[str, Any]) -> list[dict[str, Any]]:
    expected = {str(item.get("JudgmentItemId")) for item in batch.get("items") or []}
    if str(response.get("BatchId") or "") != str(batch.get("BatchId") or ""):
        raise ValueError("CODEX_CLI_BATCH_ID_MISMATCH")
    if str(response.get("ProductProfileId") or "") != str(state.get("ProductProfileId") or DATA_NOT_AVAILABLE):
        raise ValueError("AGENT_JUDGMENT_CONTEXT_MISMATCH")
    if str(response.get("BrainVersion") or "") != str(state.get("BrainVersion") or "CURRENT_FROZEN_BRAIN"):
        raise ValueError("AGENT_JUDGMENT_CONTEXT_MISMATCH")
    raw = response.get("Judgments")
    if not isinstance(raw, list):
        raise ValueError("CODEX_CLI_RESULT_SCHEMA_INVALID")
    output = []
    seen = set()
    for value in raw:
        if not isinstance(value, Mapping):
            raise ValueError("CODEX_CLI_RESULT_SCHEMA_INVALID")
        item = dict(value)
        item_id = str(item.get("JudgmentItemId") or "").strip()
        if item_id not in expected or item_id in seen:
            raise ValueError("STRUCTURED_JUDGMENT_ID_INVALID")
        seen.add(item_id)
        item["FinalPrecisionReason"] = item.get("ShortReason") or item.get("FinalPrecisionReason") or ""
        status = str(item.get("JudgmentStatus") or "").strip().upper()
        if status in {"REVIEW_REQUIRED", "FAILED"}:
            item["FinalPrecision"] = DATA_NOT_AVAILABLE
        item["ProductProfileId"] = state.get("ProductProfileId")
        item["BrainVersion"] = state.get("BrainVersion")
        item["JudgmentStatus"] = status
        output.append(item)
    if seen != expected:
        raise ValueError("STRUCTURED_JUDGMENT_COVERAGE_FAILED")
    validate_structured_judgments(output, expected, phase="A")
    allowed_reality = {"SUPPORTS", "WEAKLY_SUPPORTS", "NEUTRAL", "CONTRADICTS", "INSUFFICIENT"}
    if any(str(item.get("BenchmarkRealityAssessment") or "").upper() not in allowed_reality for item in output):
        raise ValueError("CODEX_CLI_RESULT_SCHEMA_INVALID")
    return output


def _append_codex_cli_log(report_root: Path, payload: Mapping[str, Any]) -> None:
    log_dir = governance_paths(report_root)["logs"]
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "6-0-2_codex_cli_runtime.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False) + "\n")


def run_codex_cli_production(
    product_root: str | Path,
    product_code: str,
    *,
    checkpoint: str | Path | None = None,
    timeout: float = 900.0,
    initial_batch_size: int | None = None,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Production Worker: Python pending loop → Codex CLI → checkpoint → next."""
    prepared = prepare_602(product_root, product_code)
    path = Path(checkpoint) if checkpoint else production_checkpoint_path(product_root, product_code)
    state = load_production_checkpoint(path)
    units = list(prepared.get("keyword_units") or [])
    total = len(units)
    if int(state.get("TotalUniqueKeywordCount") or total) != total:
        raise ValueError("CHECKPOINT_TOTAL_UNIQUE_MISMATCH")
    state.update({"schema": state.get("schema") or PRODUCTION_CHECKPOINT_SCHEMA,
                  "Product_Code": product_code, "TotalUniqueKeywordCount": total,
                  "BrainVersion": state.get("BrainVersion") or "CURRENT_FROZEN_BRAIN",
                  "ProductProfileId": state.get("ProductProfileId") or prepared.get("product_evidence_package", {}).get("content_sha256", DATA_NOT_AVAILABLE)})
    save_production_checkpoint(path, state)
    report_root = resolve_skill_report_dir(Path(product_root), Path(__file__).resolve().parents[1])
    cli_info = {"ExecutionRuntime": "CODEX_CLI", "CodexCliVersion": codex_version(),
                "AuthMode": codex_login_status(), "Checkpoint": str(path)}
    safe_size = int(initial_batch_size or state.get("AdaptiveSafeBatchSize") or state.get("CurrentBatchSize") or 16)
    safe_size = max(1, safe_size)
    retries_total = 0
    batches = 0
    while True:
        status = get_602_production_status(product_root, product_code, checkpoint=path)
        if status["PendingCount"] == 0:
            break
        batch = get_next_602_batch(product_root, product_code, batch_size=min(safe_size, status["PendingCount"]), checkpoint=path)
        if not batch.get("items"):
            raise RuntimeError("PENDING_QUEUE_STALLED")
        attempt = 0
        while True:
            started = datetime.now()
            try:
                payload = _cli_batch_payload(prepared, state, batch)
                response = run_codex_cli_judge(payload, schema_path=codex_cli_schema_path(), timeout=timeout, cwd=product_root)
                judgments = _normalize_cli_judgments(response, batch, state)
                saved = save_602_batch_judgments(product_root, product_code, batch, judgments, checkpoint=path)
                batches += 1
                state = load_production_checkpoint(path)
                safe_size = min(max(1, safe_size * 2), 512)
                state["CurrentBatchSize"] = len(batch["items"])
                state["AdaptiveSafeBatchSize"] = safe_size
                save_production_checkpoint(path, state)
                _append_codex_cli_log(report_root, {"BatchId": batch.get("BatchId"), "ItemCount": len(judgments),
                    "ExitCode": 0, "DurationSeconds": (datetime.now() - started).total_seconds(), "RetryCount": attempt,
                    "ValidationStatus": "PASS", "CheckpointSuccess": True, "ExecutionRuntime": "CODEX_CLI"})
                break
            except CodexCliError as exc:
                _append_codex_cli_log(report_root, {"BatchId": batch.get("BatchId"),
                    "ItemCount": len(batch.get("items") or []), "ExitCode": None,
                    "RetryCount": attempt, "ValidationStatus": "ERROR",
                    "ErrorCode": exc.code, "Error": str(exc)[-1200:],
                    "ExecutionRuntime": "CODEX_CLI"})
                if exc.code == "CODEX_CLI_AUTH_REQUIRED":
                    raise
                attempt += 1; retries_total += 1
                if attempt > max_retries and len(batch.get("items") or []) <= 1:
                    # Infrastructure failure is never an item-level business FAILED.
                    # Leave the item PENDING so the Agent Pull path can resume it.
                    raise RuntimeError(f"CODEX_CLI_RUNTIME_RETRY_EXHAUSTED: {exc}") from exc
                if attempt > max_retries:
                    safe_size = max(1, len(batch["items"]) // 2)
                    batch = get_next_602_batch(product_root, product_code, batch_size=safe_size, checkpoint=path)
                    attempt = 0
            except (ValueError, KeyError) as exc:
                attempt += 1; retries_total += 1
                if attempt > max_retries:
                    if len(batch["items"]) == 1:
                        raise RuntimeError(f"CODEX_CLI_VALIDATION_RETRY_EXHAUSTED: {exc}") from exc
                    safe_size = max(1, len(batch["items"]) // 2)
                    batch = get_next_602_batch(product_root, product_code, batch_size=safe_size, checkpoint=path)
                    attempt = 0
        # A successful batch returns to the Pending loop. Infrastructure or
        # validation exhaustion raises without mutating the batch to FAILED.
    final = finalize_602(product_root, product_code, checkpoint=path)
    final.update({"execution_runtime": "CODEX_CLI", "codex_cli": cli_info,
                  "production_batches": batches, "retry_count": retries_total,
                  "checkpoint": str(path)})
    return final


def run_current_602(
    product_root: str | Path,
    product_code: str,
    decisions: Mapping[Any, Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    *,
    precision_brain_client: Callable[[str], Iterable[Mapping[str, Any]]] | None = None,
    batch_size: int | None = None,
    prepared: Mapping[str, Any] | None = None,
    agent_judgments: Mapping[Any, Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Apply a prepared Agent handoff or run the internal compatibility adapter.

    Normal Skill execution uses ``run_current_602_agent``. The public
    ``decisions`` shortcut is rejected; only structured Agent judgments or
    the legacy test adapter may reach the deterministic APPLY path.
    """
    if decisions is not None:
        raise ValueError(EXTERNAL_DECISIONS_NOT_ALLOWED)
    precision_config = read_precision_filter_config(product_root, require=True)
    precision_levels = frozenset(precision_config["levels"])
    prepared = dict(prepared or prepare_602(product_root, product_code))
    evidence = prepared["product_evidence"]
    resolved = prepared["resolved_601"]
    input_rows = list(prepared["input_rows"])
    input_metadata = prepared.get("input_metadata") or {}
    benchmark_identities = dict(prepared["benchmark_identities"])
    brain_result = None
    if agent_judgments is not None:
        decisions = agent_judgments
        brain_result = {"decisions": decisions, "keyword_units": prepared["keyword_units"],
                        "product_profile": prepared.get("product_profile"),
                        "ExecutionMode": "V4_COMPLETE_602_TASK" if prepared.get("_v4_execution") else "EXTERNAL_AGENT",
                        "AgentProductProfileJudgmentCount": 1,
                        "AgentPhaseAJudgmentBatchCount": 0,
                        "AgentPhaseBJudgmentBatchCount": 0,
                        "AgentChallengeCount": 0,
                        "LocalValidatorInvocationCount": 0,
                        "ExternalModelCallCount": 0}
    elif precision_brain_client is None:
        raise RuntimeError(AGENT_JUDGMENT_UNAVAILABLE)
    if decisions is None:
        brain_result = run_precision_brain(
            input_rows, evidence, client=precision_brain_client, batch_size=batch_size,
        )
        decisions = brain_result["decisions"]
    if agent_judgments is not None:
        result = apply_602_judgments({**prepared, "product_profile": (brain_result or {}).get("product_profile")}, decisions)
    else:
        result = finalize_observation_judgments(input_rows, decisions, evidence_context={
            **evidence,
            "product_profile": (brain_result or {}).get("product_profile"),
        })
    if brain_result:
        result["precision_brain_run"] = brain_result
    # The AI judgment remains unchanged; only B/C/D/E projection follows the
    # shared configuration selected for this run.
    result["high_precision_rows"] = build_high_precision_rows(result["rows"], precision_levels=precision_levels)
    result["deduplicated_benchmark_rows"] = build_deduplicated_benchmark_rows(result["high_precision_rows"])
    result["deduplicated_rows"] = build_deduplicated_high_precision_rows(
        result["high_precision_rows"], precision_levels=precision_levels
    )
    context = new_602_run_context(product_root, product_code)
    benchmark_product_codes = list(benchmark_identities)
    report_root = resolve_skill_report_dir(product_root, Path(__file__).resolve().parents[1])
    build_folder = governance_paths(report_root)["staging"] / f"{context.run_timestamp}_build"
    build_folder.mkdir(parents=True, exist_ok=False)
    paths = output_paths(product_root, product_code, context, benchmark_product_codes=benchmark_product_codes,
                         output_directory=build_folder)
    all_output_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated_benchmark", "deduplicated")] + list(paths["benchmarks"].values())
    manifest_path = build_folder / f"{RUN_MANIFEST_PREFIX}{context.run_timestamp}.json"
    run_folder = paths["ai"].parent
    run_folder.mkdir(parents=True, exist_ok=True)
    high_rows = result["high_precision_rows"]
    benchmark_filtered_rows = high_rows
    unique_rows = result["deduplicated_rows"]
    per_benchmark_input_counts = {
        code: sum(str(row.get("所属产品编号") or "").strip() == code for row in input_rows)
        for code in benchmark_product_codes
    }
    per_benchmark_high_precision_counts = {
        code: sum(str(row.get("所属产品编号") or "").strip() == code for row in benchmark_filtered_rows)
        for code in benchmark_product_codes
    }
    input_folder = Path(str(resolved.get("file") or "")).parent
    counts = {
        "Input Record Count": len(input_rows),
        "Input Observation Count": len(input_rows),
        "Input Unique Keyword Count": len(result["keyword_units"]),
        "AI Record Count": len(result["rows"]),
        "High Precision Record Count": len(high_rows),
        "Unique High Precision Keyword Count": len(unique_rows),
        "Filtered Precision Record Count": len(high_rows),
        "Unique Filtered Precision Keyword Count": len(unique_rows),
        "Benchmark Count": len(benchmark_product_codes),
        "Benchmark File Count": len(benchmark_product_codes),
        "Benchmark Filtered Observation Count": len(benchmark_filtered_rows),
    }
    all_output_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated_benchmark", "deduplicated")] + list(paths["benchmarks"].values())
    manifest: dict[str, Any] = {
        "SkillId": SIX_0_2_SKILL_ID,
        "Current Product": product_code,
        "RUN_ID": context.run_id,
        "RUN_TIMESTAMP": context.run_timestamp,
        "GeneratedAt": context.generated_at,
        "Input Source": "601 data/ exact Report Identity / BENCHMARK_KEYWORD_ALL_OBSERVATIONS",
        "Input Skill": SIX_0_1_SKILL_ID,
        "Input Report Identity": SIX_0_1_REPORT_IDENTITY,
        "Input Report Name": "所有对标自然排名关键词",
        "Input Run ID": resolved.get("run_id"),
        "Input RUN_TIMESTAMP": resolved.get("run_timestamp"),
        "Input Folder": str(input_folder),
        "Input File": str(resolved.get("file") or ""),
        "Input Resolution Method": resolved.get("input_resolution_method"),
        "Input Record Count": len(input_rows),
        "Input Observation Count": len(input_rows),
        "Input Unique Keyword Count": len(result["keyword_units"]),
        "Product Text Input": str(evidence.get("text_path") or ""),
        "Product Text Input Version": {
            "SHA256": evidence.get("content_sha256"),
            "Size Bytes": evidence.get("content_size_bytes"),
            "Modified At NS": evidence.get("modified_at_ns"),
        },
        "Precision Filter Configuration": {
            "Path": precision_config["path"],
            "Raw Levels": precision_config["raw_levels"],
            "Normalized Levels": precision_config["levels"],
            "SHA256": precision_config["sha256"],
            "Size Bytes": precision_config["size_bytes"],
            "Modified At NS": precision_config["modified_at_ns"],
        },
        "Precision Library Configuration": {
            "Path": precision_config["path"],
            "SelectedPrecisionLevelsRaw": precision_config["raw_levels"],
            "SelectedPrecisionLevelsNormalized": precision_config["levels"],
        },
        "Precision Brain": {
            "Product Purchase Driver": result.get("purchase_driver", {}),
            "Structured Product Profile": result.get("product_profile", {}),
            "ExecutionMode": (result.get("precision_brain_run") or {}).get("ExecutionMode", DATA_NOT_AVAILABLE),
            "LocalBrainFallback": (result.get("precision_brain_run") or {}).get("LocalBrainFallback", DATA_NOT_AVAILABLE),
            "Record Count": len(result.get("precision_brain_records") or result.get("trace") or []),
            "AI Call Count": (result.get("precision_brain_run") or {}).get("ai_call_count", DATA_NOT_AVAILABLE),
            "ExternalModelCallCount": (result.get("precision_brain_run") or {}).get("ExternalModelCallCount", DATA_NOT_AVAILABLE),
            "ProductProfileModelCallCount": (result.get("precision_brain_run") or {}).get("ProductProfileModelCallCount", DATA_NOT_AVAILABLE),
            "PrecisionModelCallCount": (result.get("precision_brain_run") or {}).get("PrecisionModelCallCount", DATA_NOT_AVAILABLE),
            "LocalValidatorInvocationCount": (result.get("precision_brain_run") or {}).get("LocalValidatorInvocationCount", DATA_NOT_AVAILABLE),
            "SuccessfulUniqueJudgmentCount": (result.get("precision_brain_run") or {}).get("SuccessfulUniqueJudgmentCount", DATA_NOT_AVAILABLE),
            "ReviewRequiredCount": (result.get("precision_brain_run") or {}).get("ReviewRequiredCount", DATA_NOT_AVAILABLE),
            "FailedJudgmentCount": (result.get("precision_brain_run") or {}).get("FailedJudgmentCount", DATA_NOT_AVAILABLE),
            "RetryCount": (result.get("precision_brain_run") or {}).get("RetryCount", DATA_NOT_AVAILABLE),
            "Judgment Engine": "PrecisionJudgmentEngine",
            "Unique Judgment Count": len(result.get("keyword_units") or []),
            "Internal Fields": sorted({
                key for record in (result.get("precision_brain_records") or result.get("trace") or [])
                for key in record
            }),
            "Formal CSV Schema Changed": False,
        },
        "Output Folder": str(run_folder),
        "Precision Filter Levels": precision_config["levels"],
        "Output Files": [path.name for path in all_output_paths],
        "Benchmark Count": len(benchmark_product_codes),
        "Expected Benchmark Count": len(benchmark_product_codes),
        "Benchmark Product Codes": benchmark_product_codes,
        "Benchmark Identities": benchmark_identities,
        "PerBenchmarkInputObservationCount": per_benchmark_input_counts,
        "PerBenchmarkHighPrecisionRecordCount": per_benchmark_high_precision_counts,
        "Expected Benchmark Files": [path.name for path in paths["benchmarks"].values()],
        "GeneratedBenchmarkFiles": [],
        "Record Counts": counts,
        "Output Record Counts": {"AI Precision Observation Count": len(result["rows"]),
                                 "Filtered Benchmark Observation Count": len(high_rows),
                                 "Benchmark Deduplicated Observation Count": len(result["deduplicated_benchmark_rows"]),
                                 "Unique Selected Precision Keyword Count": len(unique_rows)},
        "Run Status": "RUNNING",
    }
    _write_run_manifest(run_folder, manifest)
    try:
        _write_ai_asset_pair(result["rows"], paths, context, write_metadata=False, create_folder=False, precision_levels=precision_levels)
        integrity = validate_written_outputs(input_rows, paths, precision_levels=precision_levels)
        if integrity["status"] != "PASS":
            manifest["Run Status"] = "FAILED"
            manifest["Failure"] = {"status": "DATA_INTEGRITY_FAILED", "errors": integrity.get("error_codes", [])}
            _write_run_manifest(run_folder, manifest)
            result.update({"status": "DATA_INTEGRITY_FAILED", "run_id": context.run_id,
                           "run_timestamp": context.run_timestamp, "data_integrity": integrity,
                           "run_folder": str(run_folder)})
            return result
        manifest["GeneratedBenchmarkFiles"] = [path.name for path in paths["benchmarks"].values()]
        manifest["Record Counts"]["Benchmark High Precision Observation Count"] = integrity["benchmark_output_observation_count"]
        manifest["Validation"] = integrity
        manifest["Run Status"] = "VALID"
        _write_run_manifest(run_folder, manifest)
        # A failed/incomplete package remains isolated in staging and cannot
        # replace the previous LATEST VALID data batch.
    except Exception as exc:
        manifest["Run Status"] = "FAILED"
        manifest["Failure"] = {"status": type(exc).__name__, "message": str(exc)}
        _write_run_manifest(run_folder, manifest)
        raise
    published = publish_latest_valid_batch(
        report_root,
        context.run_timestamp,
        all_output_paths,
        manifest_files=[manifest_path],
        registry_payload={
            "Skill_ID": SIX_0_2_SKILL_ID,
            "Product_Code": product_code,
            "RUN_ID": context.run_id,
            "RUN_TIMESTAMP": context.run_timestamp,
            "Report_Identities": ["AI_PRECISION_OBSERVATIONS", "FILTERED_BENCHMARK_PRECISION_KEYWORDS", "DEDUPLICATED_FILTERED_BENCHMARK_KEYWORDS", "UNIQUE_SELECTED_PRECISION_KEYWORDS"] + [f"BENCHMARK_SELECTED_PRECISION_{code}" for code in benchmark_product_codes],
            "Files": [path.name for path in all_output_paths],
        },
        move_sources=True,
    )
    shutil.rmtree(run_folder, ignore_errors=True)
    manifest_target = Path(report_root) / "_system" / "manifests" / manifest_path.name
    try:
        published_manifest = json.loads(manifest_target.read_text(encoding="utf-8-sig"))
        published_manifest["Output Folder"] = str(Path(published["data_dir"]))
        published_manifest["Output Files"] = [path.name for path in all_output_paths]
        manifest_target.write_text(json.dumps(published_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("RUN_MANIFEST_PUBLISH_UPDATE_FAILED")
    result.update({
        "status": "FULL_SUCCESS", "run_id": context.run_id, "run_timestamp": context.run_timestamp,
        "generated_at": context.generated_at, "data_integrity": integrity,
        "precision_filter_config": precision_config,
        "input_file": resolved.get("file"), "input_run_id": resolved.get("run_id"),
        "input_run_timestamp": resolved.get("run_timestamp"), "input_record_count": len(input_rows),
        "input_unique_keyword_count": len(result["keyword_units"]), "output_record_count": len(result["rows"]),
        "output_file": str(Path(published["data_dir"]) / paths["ai"].name),
        "high_precision_output_file": str(Path(published["data_dir"]) / paths["high_precision"].name),
        "deduplicated_benchmark_output_file": str(Path(published["data_dir"]) / paths["deduplicated_benchmark"].name),
        "deduplicated_output_file": str(Path(published["data_dir"]) / paths["deduplicated"].name),
        "run_folder": str(Path(published["data_dir"])),
        "benchmark_output_files": {code: str(Path(published["data_dir"]) / path.name) for code, path in paths["benchmarks"].items()},
        "run_manifest": str(Path(report_root) / "_system" / "manifests" / manifest_path.name), "product_text_source": evidence.get("text_path"),
    })
    return result




