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
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterable, Mapping
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.stage6_artifact_contract import (  # noqa: E402
    assert_new_outputs,
    make_artifact_metadata,
    new_run_context,
    resolve_latest_valid_report,
    timestamped_output_path,
    validate_601_run_package,
    write_metadata_sidecar,
)
from scripts.hzp_amz_report_contract import (  # noqa: E402
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
AI_CLASSIFICATIONS = {"PRECISION", "NOT_PRECISION", "REVIEW_REQUIRED"}
PRECISION_LEVELS = ("高度精准", "精准", "弱精准", "不精准")
PRECISION_LEVEL_NOT_AVAILABLE = "PRECISION_LEVEL_NOT_AVAILABLE"
DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"
BENCHMARK_ERP_PROID_NOT_AVAILABLE = "BENCHMARK_ERP_PROID_NOT_AVAILABLE"
BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE = "BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE"
OWN_ONLY = "OWN_ONLY"
OWN_PLUS_BENCHMARK = "OWN_PLUS_BENCHMARK"
BENCHMARK_FALLBACK = "BENCHMARK_FALLBACK"
KEYWORD_SOURCE_DATA_INSUFFICIENT = "CURRENT_KEYWORDS_UNAVAILABLE_NO_BENCHMARK"
BENCHMARK_RAW_OUTPUT_DIR = "6-0-1_\u5bf9\u6807\u81ea\u7136\u6392\u540d\u5173\u952e\u8bcd\u63d0\u53d6"
BENCHMARK_RAW_FILENAME_RE = re.compile(r"^6-0-1_所有对标自然排名关键词_\d{8}_\d{6}\.csv$", re.I)
BENCHMARK_RAW_COLUMNS = ("Id", "\u8bcd", "\u4e2d\u6587", "\u5e02\u573a\u5bb9\u91cf", "\u7ade\u4e89\u4ea7\u54c1\u6570", "\u4f9b\u9700\u6bd4", "\u5bf9\u6807\u7f16\u53f7", "对标ASIN", "自然排名", "ASIN", "产品编号")
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
RUN_MANIFEST_NAME = "run_manifest.json"
RUN_MANIFEST_PREFIX = "6-0-2_RunPackage_"
OUTPUT_A_IDENTITY = "AI_PRECISION_KEYWORD_OBSERVATIONS"
OUTPUT_B_IDENTITY = "HIGH_PRECISION_KEYWORD_OBSERVATIONS"
OUTPUT_C_IDENTITY = "去对标去重 高度精准词"
OUTPUT_C_KEY = "UNIQUE_HIGH_PRECISION_KEYWORDS"
OUTPUT_D_IDENTITY = "BENCHMARK_HIGH_PRECISION_KEYWORDS"

SEMANTIC_PROFILE_FIELDS = (
    "Core_Product_Type", "Target_Customer", "Recipient", "Core_Functions",
    "Core_Use_Cases", "Purchase_Occasions", "Relationship_Intent",
    "Core_Attributes", "Important_Differentiators", "Compatibility",
    "Compatible_Search_Intents", "Incompatible_Search_Intents",
    "Excluded_Product_Types", "Hard_Intent_Conflicts",
)
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


def evaluate_product_search_intent_fit(
    product_profile: Mapping[str, Any] | None,
    keyword_intent: Mapping[str, Any] | None,
    *,
    keyword: str | None = None,
    supporting_evidence: Mapping[str, Any] | None = None,
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
    if mode in {"GIFT_LED", "RELATIONSHIP_ONLY"} and relationship_fit:
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


def resolve_benchmark_raw_csvs(product_root: str | Path, product_code: str | None = None) -> dict[str, Any]:
    """Resolve all observations from the latest valid 6-0-1 batch by RUN_TIMESTAMP."""
    source_skill_dir = REPO_ROOT / SIX_0_1_SKILL_ID
    directory = resolve_skill_report_dir(product_root, source_skill_dir)
    if not directory.is_dir():
        return {"status": BENCHMARK_RAW_NOT_FOUND, "files": [], "rows": [], "invalid_files": []}
    candidates = sorted(path for path in directory.glob("*.csv") if path.is_file() and BENCHMARK_RAW_FILENAME_RE.match(path.name))
    if not candidates:
        return {"status": BENCHMARK_RAW_NOT_FOUND, "files": [], "rows": [], "invalid_files": []}
    def coverage_validator(_path, file_rows, metadata):
        package_error = validate_601_run_package(_path, metadata)
        if package_error:
            return package_error
        if file_rows is None:
            return "CSV_READ_FAILED"
        if not metadata or metadata.get("Keyword_Entity_ID_Field") != "KwId":
            return "KEYWORD_ENTITY_ID_METADATA_UNCONFIRMED"
        observation_keys = [(str(row.get("所属产品编号") or row.get("产品编号") or "").strip(), str(row.get("对标ASIN") or row.get("ASIN") or "").strip(), str(row.get("Id") or "").strip(), _normalized_keyword(row.get("词"))) for row in file_rows]
        if any(not product_id or not asin or not keyword_id or not keyword for product_id, asin, keyword_id, keyword in observation_keys): return "OBSERVATION_IDENTITY_OR_KEYWORD_MISSING"
        if len(observation_keys) != len(set(observation_keys)): return "DUPLICATE_BENCHMARK_KEYWORD_OBSERVATION"
        if metadata and metadata.get("Record_Count") not in (None, len(file_rows)):
            return "RECORD_COUNT_MISMATCH"
        return None

    candidates.sort(
        key=lambda path: re.search(r"_(\d{8}_\d{6})\.csv$", path.name, re.I).group(1),
        reverse=True,
    )
    inspected_invalid: list[dict[str, Any]] = []
    selected: dict[str, Any] = {}
    for candidate in candidates:
        candidate_result = resolve_latest_valid_report(
            product_root,
            SIX_0_1_SKILL_ID,
            SIX_0_1_REPORT_IDENTITY,
            [candidate],
            product_code=product_code or _product_code_from_root(product_root),
            required_schema=BENCHMARK_RAW_COLUMNS,
            validator=coverage_validator,
        )
        if candidate_result.get("status") == "LATEST_VALID_REPORT_RESOLVED":
            selected = candidate_result
            selected["skipped_candidates"] = inspected_invalid
            if inspected_invalid:
                selected["input_resolution_method"] = "LATEST_INVALID_FALLBACK_USED"
            break
        inspected_invalid.extend(candidate_result.get("skipped_candidates") or [])
    if not selected:
        selected = {
            "status": "NO_VALID_UPSTREAM_REPORT",
            "skipped_candidates": inspected_invalid,
        }
    invalid_files = [
        {"path": item["path"], "status": item.get("reason") or BENCHMARK_RAW_SCHEMA_INVALID}
        for item in selected.get("skipped_candidates", []) if not item.get("valid")
    ]
    if selected.get("status") != "LATEST_VALID_REPORT_RESOLVED":
        reason = {item.get("status") for item in invalid_files}
        status = BENCHMARK_RAW_SCHEMA_INVALID if "SCHEMA_MISMATCH" in reason else selected.get("status")
        return {"status": status, "files": [], "rows": [], "invalid_files": invalid_files, "resolution": selected}
    path = Path(selected["file"])
    file_rows = selected.get("rows") or []
    rows: list[dict[str, Any]] = []
    for source_index, raw in enumerate(file_rows):
        rows.append({"所属产品编号": raw.get("所属产品编号", raw.get("产品编号")), "对标ASIN": raw.get("对标ASIN", raw.get("ASIN")),
            "Id": str(raw.get("Id") or "").strip() or None, "词": raw.get("词"), "中文": raw.get("中文"),
            "市场容量": raw.get("市场容量"), "Keyword": str(raw.get("词") or "").strip(),
            "KeywordCn": raw.get("中文"), "SearchVolume30": raw.get("市场容量"),
            "竞争产品数": raw.get("竞争产品数"), "供需比": raw.get("供需比"), "自然排名": raw.get("自然排名"),
            "keyword_entity_id": str(raw.get("Id") or "").strip() or None,
            "keyword_entity_id_status": "USER_CONFIRMED_STABLE_ACROSS_PROID", "record_id": None,
            "record_id_status": ERP_KEYWORD_RECORD_ID_UNCONFIRMED,
            "field_semantics": {"SearchVolume30": {"status": "DOCUMENTED", "meaning": "30天搜索量"},
                "竞争产品数": {"status": "DOCUMENTED", "meaning": "PickPwKView.AsinQuantity；仅透传，不参与精准判断"},
                "供需比": {"status": "DERIVED_SOURCE_VALUE", "meaning": "6-0-1计算值；仅透传，不参与精准判断"},
                "自然排名": {"status": "DOCUMENTED", "meaning": "该Benchmark Observation自然排名；仅作Reality Evidence"}},
            "source_file": str(path), "source_row": source_index + 2, "source_type": "BENCHMARK_6_0_1_KEYWORD_OBSERVATION"})
    return {
        "status": "BENCHMARK_RAW_READY",
        "files": [str(path)],
        "rows": rows,
        "invalid_files": invalid_files,
        "source_schema": list(BENCHMARK_RAW_COLUMNS),
        "benchmark_count": (selected.get("metadata") or {}).get("Benchmark_Count"),
        "benchmark_codes": (selected.get("metadata") or {}).get("Benchmark_Codes", []),
        "benchmark_erp_pro_ids": (selected.get("metadata") or {}).get("Benchmark_ERP_ProIds", []),
        "resolution": selected,
    }


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
    resolution = resolved.get("resolution") or {}
    return {
        "status": SIX_0_1_KEYWORD_OUTPUT_READY,
        "file": str(latest),
        "rows": rows,
        "invalid_files": list(resolved.get("invalid_files") or []),
        "source_schema": list(BENCHMARK_RAW_COLUMNS),
        "run_id": resolution.get("run_id"),
        "run_timestamp": resolution.get("run_timestamp"),
        "generated_at": resolution.get("generated_at"),
        "input_resolution_method": resolution.get("input_resolution_method"),
        "input_metadata": resolution.get("metadata") or {},
    }


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
        units.append({"Id": _full_id(first), "Keyword": str(_full_source_value(first, "词", "Keyword")).strip(),
            "KeywordCn": _full_source_value(first, "中文", "KeywordCn"), "Canonical_Keyword": canonical,
            "Benchmark_Reality_Evidence": {"Benchmark_Observation_Count": len(observations), "Benchmark_Coverage_Count": len(benchmarks),
                "Best_Benchmark_Organic_Rank": best, "Median_Benchmark_Organic_Rank": middle, "Organic_Rank_Count": rank_count}})
    return units


def build_deduplicated_high_precision_rows(rows):
    output = []
    for _canonical, observations in _benchmark_observation_groups(rows).items():
        levels = {str(row.get("精准度") or "").strip() for row in observations}
        reasons = {str(row.get("精准原因") or "").strip() for row in observations}
        if levels != {"高度精准"} or len(reasons) != 1: raise ValueError("KEYWORD_JUDGMENT_INCONSISTENT")
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
            "精准度": "高度精准", "精准原因": next(iter(reasons))})
    return _stable_full_sort(output)


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
            context, semantic_intent, keyword=keyword, supporting_evidence=benchmark
        )
        classification = str(decision.get("AI_Classification") or "").strip().upper()
        if classification not in AI_CLASSIFICATIONS:
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
            "AI_Reason": str((semantic_guard or {}).get("AI_Reason") if classification != "PRECISION" and semantic_guard else decision.get("AI_Reason") or "[AI未提供分类理由]").strip(),
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
) -> dict[str, Any]:
    context = run_context or new_602_run_context(product_root, product_code)
    directory = resolve_skill_report_dir(product_root, Path(__file__).resolve().parents[1])
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
        "high_precision": path("高度精准词表"),
        "deduplicated": path("去对标去重 高度精准词"),
        "benchmarks": {code: path(f"{code}_高度精准词") for code in codes},
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
    return text if text in PRECISION_LEVELS else PRECISION_LEVEL_NOT_AVAILABLE


def _classification_level(classification: Any, *, manual_label: Any = None) -> str:
    """Conservative compatibility fallback without numeric score conversion."""
    explicit = _precision_level(manual_label)
    if explicit != PRECISION_LEVEL_NOT_AVAILABLE:
        return explicit
    state = str(classification or "").strip().upper()
    return {"PRECISION": "精准", "NOT_PRECISION": "不精准", "REVIEW_REQUIRED": "弱精准"}.get(state, "弱精准")


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


def build_high_precision_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Keep only rows directly adjudicated as 高度精准 for the 6-0-3 shortcut asset."""
    selected = [dict(row) for row in rows if str(row.get("精准度") or "").strip() == "高度精准"]
    return _stable_full_sort(selected)


def write_high_precision_csv(product_root: str | Path, product_code: str, rows: Iterable[Mapping[str, Any]]) -> Path:
    context = new_run_context("6-0-2", SIX_0_2_SKILL_ID, product_code)
    paths = output_paths(product_root, product_code, context)
    selected = build_high_precision_rows(rows)
    path = paths["high_precision"]
    assert_new_outputs([path, str(path) + ".meta.json"])
    write_csv(path, selected, columns=FULL_FINAL_COLUMNS)
    metadata = make_artifact_metadata(
        context, "HIGH_PRECISION_KEYWORDS", run_status="FULL_SUCCESS",
        schema=FULL_FINAL_COLUMNS, record_count=len(selected),
        inputs=[{
            "Input_Skill": "CALLER_PROVIDED_DATA",
            "Input_Report_Identity": "IN_MEMORY_PRECISION_DECISIONS",
            "Input_File_Name": None,
            "Input_Run_Timestamp": None,
            "Input_Generated_At": None,
            "Input_Record_Count": len(selected),
            "Input_Resolution_Method": "CALLER_PROVIDED_IN_MEMORY",
        }],
        output_assets=[str(path)],
    )
    write_metadata_sidecar(path, metadata)
    return path


def write_dual_csvs(product_root: str | Path, product_code: str, manual_rows: list[Mapping[str, Any]], ai_rows: list[Mapping[str, Any]]) -> dict[str, Path]:
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
    _write_ai_asset_pair(full_rows, paths, context)
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


def _observation_data_integrity_check(input_rows, output_a_rows, output_b_rows, output_c_rows, output_d_rows=None):
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
    expected_b = build_high_precision_rows(output_a)
    if expected_b != output_b: errors.append("HIGH_PRECISION_FILTER_MISMATCH")
    try: expected_c = build_deduplicated_high_precision_rows(expected_b)
    except ValueError as exc: expected_c = []; errors.append(str(exc))
    c_keys = [_normalized_keyword(row.get("词")) for row in output_c]
    if len(c_keys) != len(set(c_keys)): errors.append("DUPLICATE_KEYWORD_IN_DEDUP_OUTPUT")
    if any("所属产品编号" in row for row in output_c): errors.append("PRODUCT_CODE_COLUMN_FOUND_IN_DEDUP_OUTPUT")
    stringify = lambda rows: [{column: "" if row.get(column) is None else str(row.get(column)) for column in DEDUPLICATED_FINAL_COLUMNS} for row in rows]
    c_pass = stringify(expected_c) == stringify(output_c)
    if not c_pass: errors.append("DEDUPLICATION_FAILED")
    d_results = {}
    if output_d_rows is not None:
        expected_codes = set(output_d_rows)
        source_codes = {str(row.get("所属产品编号") or "").strip() for row in output_a}
        if not source_codes.issubset(expected_codes):
            errors.append("BENCHMARK_FILE_COUNT_MISMATCH")
        total_d = 0
        for code, actual in output_d_rows.items():
            actual = list(actual)
            expected = [row for row in expected_b if str(row.get("所属产品编号") or "").strip() == code]
            actual_keys = [_normalized_keyword(row.get("词")) for row in actual]
            valid = (actual == expected
                     and all(str(row.get("所属产品编号") or "").strip() == code for row in actual)
                     and len(actual_keys) == len(set(actual_keys)))
            if not valid:
                errors.append("BENCHMARK_HIGH_PRECISION_DERIVATION_MISMATCH")
            total_d += len(actual)
            d_results[code] = {"expected_high_precision_observation_count": len(expected),
                               "output_observation_count": len(actual), "coverage": "PASS" if valid else "FAIL"}
        if total_d != len(expected_b):
            errors.append("BENCHMARK_HIGH_PRECISION_COVERAGE_MISMATCH")
    return {"status": "PASS" if not errors else "FAIL", "error_codes": list(dict.fromkeys(errors)),
        "file_a": {"input_observation_count": len(source), "output_observation_count": len(output_a), "coverage": "PASS" if source_keys == output_keys else "FAIL"},
        "file_b": {"expected_high_precision_observation_count": len(expected_b), "output_observation_count": len(output_b), "coverage": "PASS" if expected_b == output_b else "FAIL"},
        "file_c": {"expected_unique_keyword_count": len(expected_c), "output_unique_keyword_count": len(output_c), "deduplication": "PASS" if c_pass else "FAIL"},
        "file_d": d_results, "benchmark_output_observation_count": sum(item["output_observation_count"] for item in d_results.values())}


def data_integrity_check(input_rows, output_a_rows, output_b_rows, output_c_rows=None):
    source, output_a, output_b = list(input_rows), list(output_a_rows), list(output_b_rows)
    if source and all("所属产品编号" in row and "对标ASIN" in row for row in source):
        return _observation_data_integrity_check(source, output_a, output_b, list(output_c_rows or []))
    expected_b = build_high_precision_rows(output_a); coverage_a = coverage_check(source, output_a); coverage_b = coverage_check(expected_b, output_b); errors = []
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

def validate_written_outputs(input_rows, paths):
    try:
        output_a = _read_formal_csv(paths["ai"], OBSERVATION_FINAL_COLUMNS)
        output_b = _read_formal_csv(paths["high_precision"], OBSERVATION_FINAL_COLUMNS)
        output_c = _read_formal_csv(paths["deduplicated"], DEDUPLICATED_FINAL_COLUMNS)
        output_d = {code: _read_formal_csv(path, OBSERVATION_FINAL_COLUMNS)
                    for code, path in paths.get("benchmarks", {}).items()}
    except ValueError as exc:
        return {"status": "FAIL", "error_codes": [str(exc) or OUTPUT_SCHEMA_MISMATCH], "file_a": {}, "file_b": {}, "file_c": {}}
    except (OSError, UnicodeError, csv.Error):
        return {"status": "FAIL", "error_codes": [OUTPUT_READBACK_FAILED], "file_a": {}, "file_b": {}, "file_c": {}}
    return _observation_data_integrity_check(input_rows, output_a, output_b, output_c, output_d if "benchmarks" in paths else None)


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
    return (_precision_level(decision.get("精准度", decision.get("AI_Precision_Level", decision.get("Precision_Level")))),
            str(decision.get("精准原因", decision.get("AI_Reason", decision.get("Precision_Reason"))) or "").strip())


def _observation_judgment_row(source, decision):
    level, reason = _decision_signature(decision)
    if level == PRECISION_LEVEL_NOT_AVAILABLE: raise ValueError("AI_PRECISION_LEVEL_REQUIRED")
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


def finalize_observation_judgments(observation_rows, decisions, *, evidence_context=None):
    source = list(observation_rows); groups = _benchmark_observation_groups(source); index = _decision_index(decisions); chosen = {}; units = build_keyword_judgment_units(source)
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
    trace = [{"Canonical_Keyword": key, "词": str(rows[0].get("词") or ""), "精准度": _decision_signature(chosen[key])[0],
        "精准原因": _decision_signature(chosen[key])[1], "Benchmark_Reality_Evidence": units[i]["Benchmark_Reality_Evidence"]}
        for i,(key,rows) in enumerate(groups.items())]
    return {"rows": output, "high_precision_rows": high, "deduplicated_rows": unique, "keyword_units": units,
        "coverage": coverage, "trace": trace, "evidence_context": dict(evidence_context or {})}


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
    projected=[]; trace=[]
    for row in source:
        rid=_full_id(row); keyword=str(_full_source_value(row,"\u8bcd","Keyword","\u5173\u952e\u8bcd")).strip(); decision=decision_map.get(rid)
        if decision is None: decision=decision_map.get(keyword) or decision_map.get(keyword.lower())
        if not isinstance(decision,Mapping): raise ValueError(f"AI_DECISION_MISSING:{rid}")
        final=_full_judgment_row(row,decision); projected.append(final)
        trace.append({"Id":rid,"\u8bcd":keyword,"Search_Intent":decision.get("Search_Intent",DATA_NOT_AVAILABLE),"Product_Intent_Fit":decision.get("Product_Intent_Fit",DATA_NOT_AVAILABLE),"Hard_Conflict":decision.get("Hard_Conflict",DATA_NOT_AVAILABLE),"\u7cbe\u51c6\u5ea6":final["\u7cbe\u51c6\u5ea6"],"\u7cbe\u51c6\u539f\u56e0":final["\u7cbe\u51c6\u539f\u56e0"],"Evidence_Sources":(evidence_context or {}).get("source_paths",[])})
    ordered=_stable_full_sort(projected); coverage=coverage_check(source,ordered)
    if coverage["status"]!="PASS": raise ValueError("INPUT_OUTPUT_COVERAGE_FAILED:"+json.dumps(coverage,ensure_ascii=False))
    return {"rows":ordered,"coverage":coverage,"trace":trace,"evidence_context":dict(evidence_context or {})}

def _write_ai_asset_pair(rows, paths, context, *, lineage=None, write_metadata=True, create_folder=True):
    values = list(rows)
    if values and not all("所属产品编号" in row and "对标ASIN" in row for row in values):
        values = [{"所属产品编号":"", "对标ASIN":"", "Id":row.get("Id"), "词":row.get("词",row.get("Keyword","")),
            "中文":row.get("中文",row.get("KeywordCn","")), "市场容量":row.get("市场容量",row.get("SearchVolume30")),
            "竞争产品数":row.get("竞争产品数"), "供需比":row.get("供需比"), "自然排名":row.get("自然排名",row.get("最佳自然排名","")),
            "精准度":row.get("精准度"), "精准原因":row.get("精准原因")} for row in values]
    high = build_high_precision_rows(values); unique = build_deduplicated_high_precision_rows(high); folder = paths["ai"].parent
    benchmark_rows = {
        code: [row for row in high if str(row.get("所属产品编号") or "").strip() == code]
        for code in paths.get("benchmarks", {})
    }
    if create_folder: folder.mkdir(parents=True, exist_ok=True)
    keys=("ai","high_precision","deduplicated"); staged={key:Path(str(paths[key])+".tmp") for key in keys}
    staged_benchmarks = {code: Path(str(path) + ".tmp") for code, path in paths.get("benchmarks", {}).items()}
    output_paths_all = [*(paths[key] for key in keys), *paths.get("benchmarks", {}).values()]
    sidecars = [str(path) + ".meta.json" for path in output_paths_all]
    assert_new_outputs([*output_paths_all, *sidecars, *staged.values(), *staged_benchmarks.values()])
    write_csv(staged["ai"], values, columns=OBSERVATION_FINAL_COLUMNS)
    write_csv(staged["high_precision"], high, columns=OBSERVATION_FINAL_COLUMNS)
    write_csv(staged["deduplicated"], unique, columns=DEDUPLICATED_FINAL_COLUMNS)
    for code, temporary in staged_benchmarks.items():
        write_csv(temporary, benchmark_rows[code], columns=OBSERVATION_FINAL_COLUMNS)
    for key in keys: os.replace(staged[key], paths[key])
    for code, temporary in staged_benchmarks.items(): os.replace(temporary, paths["benchmarks"][code])
    if write_metadata:
        inputs=list(lineage or [{"Input_Skill":"CALLER_PROVIDED_DATA","Input_Report_Identity":"IN_MEMORY_PRECISION_DECISIONS","Input_File_Name":None,"Input_Run_Timestamp":None,"Input_Generated_At":None,"Input_Record_Count":len(values),"Input_Resolution_Method":"CALLER_PROVIDED_IN_MEMORY"}])
        definitions={"ai":(OUTPUT_A_IDENTITY,values,OBSERVATION_FINAL_COLUMNS),"high_precision":(OUTPUT_B_IDENTITY,high,OBSERVATION_FINAL_COLUMNS),"deduplicated":(OUTPUT_C_IDENTITY,unique,DEDUPLICATED_FINAL_COLUMNS)}
        assets=[str(path) for path in output_paths_all]
        for key,(identity,output_rows,schema) in definitions.items():
            extra = {"Report_Key": OUTPUT_C_KEY} if key == "deduplicated" else None
            write_metadata_sidecar(paths[key],make_artifact_metadata(context,identity,run_status="FULL_SUCCESS",schema=schema,record_count=len(output_rows),inputs=inputs,output_assets=assets,extra=extra))
        for code, benchmark_path in paths.get("benchmarks", {}).items():
            write_metadata_sidecar(benchmark_path, make_artifact_metadata(
                context, OUTPUT_D_IDENTITY, run_status="FULL_SUCCESS", schema=OBSERVATION_FINAL_COLUMNS,
                record_count=len(benchmark_rows[code]), inputs=inputs, output_assets=assets,
                extra={"Benchmark_Product_Code": code, "Report_Key": f"BENCHMARK_HIGH_PRECISION_KEYWORDS:{code}"},
            ))
    return dict(paths)


def write_full_ai_csv(
    product_root: str | Path,
    product_code: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    run_context=None,
    write_metadata: bool = True,
) -> Path:
    values = list(rows)
    context = run_context or new_602_run_context(product_root, product_code)
    benchmark_codes = sorted({str(row.get("所属产品编号") or "").strip() for row in values if str(row.get("所属产品编号") or "").strip()})
    paths = output_paths(product_root, product_code, context, benchmark_product_codes=benchmark_codes)
    _write_ai_asset_pair(values, paths, context, write_metadata=write_metadata)
    return paths["ai"]


def _write_run_manifest(run_folder: Path, manifest: Mapping[str, Any]) -> Path:
    stamp = str(manifest.get("RUN_TIMESTAMP") or "").strip()
    if not re.fullmatch(r"\d{8}_\d{6}", stamp):
        raise ValueError("RUN_TIMESTAMP must match YYYYMMDD_HHMMSS")
    target = run_folder / f"{RUN_MANIFEST_PREFIX}{stamp}.json"
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target


def _write_602_output_metadata(paths: Mapping[str, Path], context: Any, lineage: list[Mapping[str, Any]], rows_by_key: Mapping[str, list[Mapping[str, Any]]]) -> None:
    definitions = {
        "ai": (OUTPUT_A_IDENTITY, OBSERVATION_FINAL_COLUMNS),
        "high_precision": (OUTPUT_B_IDENTITY, OBSERVATION_FINAL_COLUMNS),
        "deduplicated": (OUTPUT_C_IDENTITY, DEDUPLICATED_FINAL_COLUMNS),
    }
    assets = [str(paths[key]) for key in definitions] + [str(path) for path in paths.get("benchmarks", {}).values()]
    input_method = next(
        (str(item.get("Input_Resolution_Method")) for item in lineage
         if item.get("Input_Skill") == SIX_0_1_SKILL_ID and item.get("Input_Resolution_Method")),
        "LATEST_VALID_601_RUN_PACKAGE",
    )
    for key, (identity, schema) in definitions.items():
        extra = {"Input_Resolution_Method": input_method}
        if key == "deduplicated":
            extra["Report_Key"] = OUTPUT_C_KEY
        metadata = make_artifact_metadata(
            context, identity, run_status="FULL_SUCCESS", schema=schema,
            record_count=len(rows_by_key[key]), inputs=lineage, output_assets=assets,
            extra=extra,
        )
        write_metadata_sidecar(paths[key], metadata)
    for code, path in paths.get("benchmarks", {}).items():
        rows = rows_by_key["benchmarks"][code]
        metadata = make_artifact_metadata(
            context, OUTPUT_D_IDENTITY, run_status="FULL_SUCCESS", schema=OBSERVATION_FINAL_COLUMNS,
            record_count=len(rows), inputs=lineage, output_assets=assets,
            extra={"Input_Resolution_Method": input_method, "Benchmark_Product_Code": code,
                   "Report_Key": f"BENCHMARK_HIGH_PRECISION_KEYWORDS:{code}"},
        )
        write_metadata_sidecar(path, metadata)


def run_current_602(product_root: str | Path, product_code: str, decisions: Mapping[Any, Mapping[str, Any]] | Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Read current product text and 6-0-1 Observations; create one valid 3+N CSV package."""
    evidence = read_current_product_text_evidence(product_root)
    if evidence.get("status") != CURRENT_PRODUCT_TEXT_EVIDENCE_READY:
        raise FileNotFoundError(str(evidence.get("status") or CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED))
    resolved = resolve_latest_601_keyword_output(product_root, product_code=product_code)
    if resolved.get("status") != SIX_0_1_KEYWORD_OUTPUT_READY:
        raise FileNotFoundError(str(resolved.get("status") or SIX_0_1_KEYWORD_OUTPUT_NOT_FOUND))
    input_rows = list(resolved.get("rows") or [])
    input_metadata = resolved.get("input_metadata") or {}
    benchmark_identities = _benchmark_identity_map(input_metadata)
    _validate_benchmark_observation_uniqueness(input_rows)
    input_product_codes = {str(row.get("所属产品编号") or "").strip() for row in input_rows}
    if not input_product_codes.issubset(benchmark_identities):
        raise ValueError("BENCHMARK_IDENTITY_MISSING")
    result = finalize_observation_judgments(input_rows, decisions, evidence_context=evidence)
    context = new_602_run_context(product_root, product_code)
    benchmark_product_codes = list(benchmark_identities)
    paths = output_paths(product_root, product_code, context, benchmark_product_codes=benchmark_product_codes)
    all_output_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated")] + list(paths["benchmarks"].values())
    manifest_path = paths["ai"].parent / f"{RUN_MANIFEST_PREFIX}{context.run_timestamp}.json"
    report_error = validate_hzp_amz_report_batch(
        [*all_output_paths, manifest_path], product_root, Path(__file__).resolve().parents[1], timestamp=context.run_timestamp,
    )
    if report_error:
        raise ValueError(report_error)
    run_folder = paths["ai"].parent
    run_folder.mkdir(parents=True, exist_ok=True)
    high_rows = result["high_precision_rows"]
    unique_rows = result["deduplicated_rows"]
    per_benchmark_input_counts = {
        code: sum(str(row.get("所属产品编号") or "").strip() == code for row in input_rows)
        for code in benchmark_product_codes
    }
    per_benchmark_high_precision_counts = {
        code: sum(str(row.get("所属产品编号") or "").strip() == code for row in high_rows)
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
        "Benchmark Count": len(benchmark_product_codes),
        "Benchmark File Count": len(benchmark_product_codes),
        "Benchmark High Precision Observation Count": len(high_rows),
    }
    all_output_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated")] + list(paths["benchmarks"].values())
    manifest: dict[str, Any] = {
        "SkillId": SIX_0_2_SKILL_ID,
        "Current Product": product_code,
        "RUN_ID": context.run_id,
        "RUN_TIMESTAMP": context.run_timestamp,
        "GeneratedAt": context.generated_at,
        "Input Source": "601 LATEST VALID RUN PACKAGE / BENCHMARK_KEYWORD_ALL_OBSERVATIONS",
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
        "Output Folder": str(run_folder),
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
                                 "High Precision Observation Count": len(high_rows),
                                 "Unique High Precision Keyword Count": len(unique_rows)},
        "Run Status": "RUNNING",
    }
    _write_run_manifest(run_folder, manifest)
    try:
        _write_ai_asset_pair(result["rows"], paths, context, write_metadata=False, create_folder=False)
        integrity = validate_written_outputs(input_rows, paths)
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
        lineage = [
            {"Input_Skill": "CURRENT_PRODUCT_TEXT_EVIDENCE", "Input_Report_Identity": "CURRENT_PRODUCT_TEXT_EVIDENCE",
             "Input_File_Name": str(evidence.get("text_path") or ""), "Input_Run_Timestamp": None,
             "Input_File_SHA256": evidence.get("content_sha256"),
             "Input_File_Size_Bytes": evidence.get("content_size_bytes"),
             "Input_File_Modified_At_NS": evidence.get("modified_at_ns"),
             "Input_Generated_At": None, "Input_Record_Count": 1,
             "Input_Resolution_Method": "CURRENT_PRODUCT_ROOT_FIXED_INPUT"},
            {"Input_Skill": SIX_0_1_SKILL_ID, "Input_Report_Identity": SIX_0_1_REPORT_IDENTITY,
             "Input_Report_Name": "所有对标自然排名关键词",
             "Input_File_Name": str(resolved.get("file") or ""), "Input_Run_ID": resolved.get("run_id"),
             "Input_Run_Timestamp": resolved.get("run_timestamp"), "Input_Folder": str(input_folder),
             "Input_Generated_At": resolved.get("generated_at"), "Input_Record_Count": len(input_rows),
             "Input_Unique_Keyword_Count": len(result["keyword_units"]),
             "Input_Resolution_Method": resolved.get("input_resolution_method") or "LATEST_VALID_601_RUN_PACKAGE"},
        ]
        rows_by_key = {"ai": result["rows"], "high_precision": high_rows, "deduplicated": unique_rows,
                       "benchmarks": {code: [row for row in high_rows if str(row.get("所属产品编号") or "").strip() == code]
                                      for code in benchmark_product_codes}}
        _write_602_output_metadata(paths, context, lineage, rows_by_key)
        manifest["Validation"] = integrity
        manifest["Run Status"] = "VALID"
        _write_run_manifest(run_folder, manifest)
    except Exception as exc:
        manifest["Run Status"] = "FAILED"
        manifest["Failure"] = {"status": type(exc).__name__, "message": str(exc)}
        _write_run_manifest(run_folder, manifest)
        raise
    result.update({
        "status": "FULL_SUCCESS", "run_id": context.run_id, "run_timestamp": context.run_timestamp,
        "generated_at": context.generated_at, "data_integrity": integrity,
        "input_file": resolved.get("file"), "input_run_id": resolved.get("run_id"),
        "input_run_timestamp": resolved.get("run_timestamp"), "input_record_count": len(input_rows),
        "input_unique_keyword_count": len(result["keyword_units"]), "output_record_count": len(result["rows"]),
        "output_file": str(paths["ai"]), "high_precision_output_file": str(paths["high_precision"]),
        "deduplicated_output_file": str(paths["deduplicated"]), "run_folder": str(run_folder),
        "benchmark_output_files": {code: str(path) for code, path in paths["benchmarks"].items()},
        "run_manifest": str(run_folder / f"{RUN_MANIFEST_PREFIX}{context.run_timestamp}.json"), "product_text_source": evidence.get("text_path"),
    })
    return result
