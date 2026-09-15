"""Dual-track ERP precision-keyword views for Stage 6-0-1.

The module is deliberately provider-agnostic: the caller supplies the complete
PickPwKView result once.  It creates a manual/ERP-tagged view and an AI-blind
view without querying SQL twice or leaking Tags/IsExact into AI classification.
It never writes ERP or Amazon data.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterable, Mapping

PRECISION_TAG = "|1精准|"
MANUAL_FILENAME = "6-0-1_{product_code}_手动分类精准词.csv"
AI_FILENAME = "6-0-1_{product_code}_AI精准词.csv"
OUTPUT_DIR = "6-0-1_精准关键词识别"
FINAL_COLUMNS = ("自动编号", "关键词", "搜索量", "中文名称", "精准理由", "精准度")
ERP_KEYWORD_RECORD_ID_UNCONFIRMED = "[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]"
ERP_KEYWORD_RECORD_ID_AMBIGUOUS = "[ERP_KEYWORD_RECORD_ID_AMBIGUOUS]"
ERP_KEYWORD_RECORD_IDENTITY_CONFLICT = "[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]"

QUALITY_FIELDS = (
    "KeywordCn", "IsMain", "IsLongTail", "IsGoodCvt", "IsSold",
    "SearchVolume30", "SearchVolumeDaily", "SearchGrowthRate30", "IQScore",
    "SearchSoldSum", "SearchCvtRate", "SearchHitSum", "SearchHitRate",
    "abarank", "UpdateTime", "RecordDate",
)
AI_EXCLUDED_FIELDS = {"IsExact", "raw_fields"}
AI_CONFIDENCE_VALUES = {"HIGH", "MEDIUM", "LOW"}
AI_CLASSIFICATIONS = {"PRECISION", "NOT_PRECISION", "REVIEW_REQUIRED"}
DATA_NOT_AVAILABLE = "DATA_NOT_AVAILABLE"
BENCHMARK_ERP_PROID_NOT_AVAILABLE = "BENCHMARK_ERP_PROID_NOT_AVAILABLE"
BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE = "BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE"
OWN_ONLY = "OWN_ONLY"
OWN_PLUS_BENCHMARK = "OWN_PLUS_BENCHMARK"
BENCHMARK_FALLBACK = "BENCHMARK_FALLBACK"
KEYWORD_SOURCE_DATA_INSUFFICIENT = "CURRENT_KEYWORDS_UNAVAILABLE_NO_BENCHMARK"

SEMANTIC_PROFILE_FIELDS = (
    "Core_Product_Type", "Target_Customer", "Recipient", "Core_Functions",
    "Core_Use_Cases", "Purchase_Occasions", "Relationship_Intent",
    "Core_Attributes", "Important_Differentiators", "Compatibility",
    "Compatible_Search_Intents", "Incompatible_Search_Intents",
    "Excluded_Product_Types", "Hard_Intent_Conflicts",
)
_GENERIC_PRODUCT_TYPES = {"gift", "gifts", "product", "products", "item", "items"}

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
    profile_relationship = profile.get("Relationship_Intent") or profile.get("Recipient")
    if relationship not in (None, "", DATA_NOT_AVAILABLE) and profile_relationship not in (None, "", DATA_NOT_AVAILABLE):
        if not _semantic_overlap(relationship, profile_relationship):
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


def evaluate_product_search_intent_fit(
    product_profile: Mapping[str, Any] | None,
    keyword_intent: Mapping[str, Any] | None,
    *,
    supporting_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply semantic guardrails to an AI's holistic Product–Search Intent judgment.

    Hard conflicts explicitly confirmed by the product profile veto Precision.
    An explicit requirement whose product support is unknown yields
    ``REVIEW_REQUIRED``.  Volume, advertising metrics, rank, orders, and
    Benchmark labels are retained only as supporting evidence and cannot alter
    the semantic classification.
    """
    profile = build_product_semantic_profile(product_profile)
    intent = keyword_intent if isinstance(keyword_intent, Mapping) else {}
    conflict = _hard_conflict(profile, intent)
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
    compatible = profile.get("Compatible_Search_Intents")
    intent_core = intent.get("Core_Intent")
    matched = _semantic_overlap(intent_core, compatible)
    # When the caller has supplied a complete core intent, an unrelated
    # recipient/function overlap must not promote the keyword.  Dimension-only
    # matching is reserved for intents whose core expression is absent.
    if not matched and not intent_core:
        for field in ("Recipient", "Relationship", "Core_Functions", "Use_Cases", "Purchase_Occasions"):
            if _semantic_overlap(intent.get(field), profile.get(field)):
                matched = True
                break
    if matched:
        return {
            "AI_Classification": "PRECISION",
            "AI_Is_Precision": True,
            "AI_Confidence": "HIGH",
            "AI_Reason": "核心搜索意图与产品语义画像在购买对象/场景/功能上直接匹配",
            "Product_Intent_Fit": "DIRECT_SEMANTIC_FIT",
            "Matched_Product_Attributes": "Product–Search Intent Fit",
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
        return ("manual", "ai")
    if normalized in {"手动分类精准词", "manual"}:
        return ("manual",)
    if normalized in {"自动分类精准词", "AI精准词", "ai", "auto"}:
        return ("ai",)
    raise ValueError(f"unsupported 6-0-1 precision path: {mode}")


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
            values[field] = raw.get(field)
    return values


def _identity(row: Mapping[str, Any], product_code: str | None = None) -> dict[str, Any]:
    raw = _raw(row)
    return {
        "Product_Code": product_code or row.get("product_code"),
        "ERP_ProId": row.get("erp_pro_id") or raw.get("ProId"),
        "Keyword": _keyword(row),
        "KeywordCn": raw.get("KeywordCn"),
    }


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
    benchmark_results: Iterable[Mapping[str, Any]],
    *,
    product_code: str,
    erp_pro_id: Any,
    benchmark_erp_pro_ids: Iterable[Any] | None = None,
    own_keywords_sufficient: bool | None = None,
    own_intent_coverage_sufficient: bool | None = None,
) -> dict[str, Any]:
    """Build a deduplicated, AI-safe candidate pool for the current product.

    Benchmark rows are candidates only. Their Tags/IsExact/raw fields are
    never used as classification labels. A documented stable Record ID from
    either the current product or an explicitly bound Benchmark is retained
    for downstream ERP synchronization; the record's source ProId remains
    separate from Current_ERP_ProId.
    """
    own = list(own_rows)
    benchmarks = list(benchmark_results)
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
        if configured and result_pro_id not in configured:
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
    identity_conflicts: set[str] = set()
    seen_records: set[tuple[str, str]] = set()

    def append_candidate(item: dict[str, Any], *, source_pro_id: Any, key: str) -> None:
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
                if configured and result_pro_id not in configured:
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
                        "AI_Evidence": evidence.get(key, {}),
                        "record_id": row.get("record_id"),
                        "record_id_status": row.get("record_id_status", ERP_KEYWORD_RECORD_ID_UNCONFIRMED),
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
        if configured and pro_id not in configured:
            continue
        for row in result.get("rows") or ():
            keyword = str(row.get("keyword") or _raw(row).get("Keyword") or "").strip()
            key = _normalized_keyword(keyword)
            if not key:
                continue
            bucket = per_keyword.setdefault(key, {"pro_ids": set(), "ranks": []})
            if pro_id:
                bucket["pro_ids"].add(pro_id)
            rank = _documented_natural_rank(row)
            if rank is not None:
                bucket["ranks"].append(rank)
    output: dict[str, dict[str, Any]] = {}
    for keyword, bucket in per_keyword.items():
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
        # Optional semantic guardrail: callers may provide a structured
        # Search_Intent.  It only vetoes a claimed Precision when the verified
        # product profile proves a hard conflict or leaves a required property
        # unknown; it never promotes a keyword or uses performance metrics as a
        # semantic label.
        semantic_intent = decision.get("Keyword_Search_Intent")
        if not isinstance(semantic_intent, Mapping) and isinstance(decision.get("Search_Intent"), Mapping):
            semantic_intent = decision.get("Search_Intent")
        semantic_guard = evaluate_product_search_intent_fit(context, semantic_intent) if isinstance(semantic_intent, Mapping) else None
        classification = str(decision.get("AI_Classification") or "").strip().upper()
        if classification not in AI_CLASSIFICATIONS:
            legacy = decision.get("AI_Is_Precision")
            classification = "PRECISION" if legacy is True else "NOT_PRECISION" if legacy is False else "REVIEW_REQUIRED"
        if classification == "PRECISION" and semantic_guard and semantic_guard["AI_Classification"] in {"NOT_PRECISION", "REVIEW_REQUIRED"}:
            classification = semantic_guard["AI_Classification"]
        benchmark = (benchmark_evidence or {}).get(_normalized_keyword(keyword))
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
        manual_label = "PRECISION" if PRECISION_TAG in str(source_raw.get("Tags") or "") else "NOT_PRECISION" if source_row else DATA_NOT_AVAILABLE
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
            "AI_Precision_Score": _score(decision.get("AI_Precision_Score", decision.get("Precision_Score"))),
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
    """Fetch the complete ProId result exactly once and create both views."""
    rows = list(fetch_all_rows())
    return {
        "source_row_count": len(rows),
        "manual_rows": build_manual_rows(rows, product_code=product_code, erp_pro_id=erp_pro_id),
        "ai_blind_rows": build_ai_blind_rows(rows, product_code=product_code, erp_pro_id=erp_pro_id),
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


def output_paths(product_root: str | Path, product_code: str) -> dict[str, Path]:
    directory = Path(product_root) / "06_SKILL分析报告" / OUTPUT_DIR
    return {
        "manual": directory / MANUAL_FILENAME.format(product_code=product_code),
        "ai": directory / AI_FILENAME.format(product_code=product_code),
    }


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


def _final_row(row: Mapping[str, Any], *, reason_key: str, score_key: str,
               translations: Mapping[str, str] | None = None) -> dict[str, Any]:
    keyword = str(row.get("Keyword") or row.get("keyword") or "").strip()
    cn = str(row.get("KeywordCn") or "").strip()
    if not cn and translations:
        cn = str(translations.get(keyword) or translations.get(keyword.lower()) or "").strip()
    search_volume = row.get("SearchVolume30")
    if search_volume in (None, ""):
        search_volume = DATA_NOT_AVAILABLE
    return {
        "自动编号": _record_id(row),
        "关键词": keyword,
        "搜索量": search_volume,
        "中文名称": cn or DATA_NOT_AVAILABLE,
        "精准理由": str(row.get(reason_key) or "[未提供精准理由]").strip(),
        "精准度": _score(row.get(score_key)),
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
    return output


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
        if projected["精准度"] == DATA_NOT_AVAILABLE:
            projected["精准度"] = _score(score_by_keyword.get(_normalized_keyword(row.get("Keyword"))))
        output.append(projected)
    return output


def write_dual_csvs(product_root: str | Path, product_code: str, manual_rows: list[Mapping[str, Any]], ai_rows: list[Mapping[str, Any]]) -> dict[str, Path]:
    paths = output_paths(product_root, product_code)
    manual_final = build_final_manual_rows(manual_rows, ai_rows=ai_rows)
    ai_final = build_final_ai_rows(ai_rows)
    write_csv(paths["manual"], manual_final, columns=FINAL_COLUMNS)
    write_csv(paths["ai"], ai_final, columns=FINAL_COLUMNS)
    return paths
