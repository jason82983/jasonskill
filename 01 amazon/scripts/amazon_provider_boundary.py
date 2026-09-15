"""Small provider boundary for HZP Amazon canonical business semantics.

This module is deliberately pure and read-only.  Provider adapters map their
raw response keys to the canonical fields consumed by Skills; no MCP/API
client, provider schema, or network operation belongs here.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from typing import Any, Iterable, Mapping

from resolve_amazon_ad_identity import stable_sku_list


SUPPORTED = "SUPPORTED"
NOT_SUPPORTED = "NOT_SUPPORTED"
SEMANTICS_UNCERTAIN = "SEMANTICS_UNCERTAIN"
CAPABILITY_NOT_AVAILABLE = "CAPABILITY_NOT_AVAILABLE"
SAFE_WRITE_CAPABILITY_NOT_AVAILABLE = "SAFE_WRITE_CAPABILITY_NOT_AVAILABLE"

_CAPABILITY_VALUES = {SUPPORTED, NOT_SUPPORTED, SEMANTICS_UNCERTAIN}


def normalize_capabilities(raw: Mapping[str, Any] | None, requested: Iterable[str] | None = None) -> dict[str, str]:
    """Normalize adapter capability discovery without guessing missing values."""
    source = raw or {}
    names = list(requested or source.keys())
    result: dict[str, str] = {}
    for name in names:
        value = source.get(name)
        if isinstance(value, Mapping):
            value = value.get("status") or value.get("state")
        normalized = str(value or "").strip().upper()
        result[name] = normalized if normalized in _CAPABILITY_VALUES else CAPABILITY_NOT_AVAILABLE
    return result


def canonicalize_identity(raw: Mapping[str, Any], *, field_map: Mapping[str, str] | None = None, provider: str | None = None) -> dict[str, Any]:
    """Map provider response keys to HZP identity fields.

    ``field_map`` is supplied by the provider adapter, keeping provider-specific
    names outside core Skill logic.  Missing fields remain explicit ``None``.
    """
    mapping = field_map or {}
    def value(canonical: str, *fallbacks: str) -> Any:
        key = mapping.get(canonical)
        if key and key in raw:
            return raw[key]
        for key in fallbacks:
            if key in raw:
                return raw[key]
        return None

    def sku_values(item: Any) -> list[str]:
        if isinstance(item, str):
            text = item.strip()
            if text.startswith("["):
                try:
                    item = json.loads(text)
                except json.JSONDecodeError:
                    pass
            elif "|" in text:
                item = text.split("|")
        return stable_sku_list(item)

    mapped = sku_values(value("mapped_skus", "mapped_skus", "Mapped_SKUs"))
    advertised = sku_values(value("advertised_skus", "advertised_skus", "Advertised_SKUs"))
    return {
        "provider": provider,
        "product_code": value("product_code", "product_code", "Product_Code"),
        "var_code": value("var_code", "var_code", "Var_Code"),
        "var_name": value("var_name", "var_name", "Var_Name"),
        "own_asin": value("own_asin", "own_asin", "Own_ASIN", "Own ASIN"),
        "parent_asin": value("parent_asin", "parent_asin", "Parent_ASIN", "Parent ASIN"),
        "child_asin": value("child_asin", "child_asin", "Child_ASIN", "Child ASIN"),
        "advertised_asin": value("advertised_asin", "advertised_asin", "Advertised_ASIN", "asin", "ASIN"),
        "mapped_skus": mapped,
        "advertised_skus": advertised,
        "primary_advertised_sku": value("primary_advertised_sku", "primary_advertised_sku", "Primary_Advertised_SKU"),
        "sku_count": len(mapped),
        "identity_status": value("identity_status", "identity_status", "Identity_Status"),
        "identity_conflicts": value("identity_conflicts", "identity_conflicts", "Identity_Conflicts") or [],
        "store": value("store", "store", "Store"),
        "marketplace": value("marketplace", "marketplace", "Marketplace"),
        "portfolio_name": value("portfolio_name", "portfolio_name", "Portfolio_Name", "Portfolio Name"),
        "portfolio_id": value("portfolio_id", "portfolio_id", "Portfolio_ID", "Portfolio ID"),
    }


@dataclass(frozen=True)
class CanonicalMetric:
    value: Any
    metric: str
    provider: str | None
    source_grain: str | None
    metric_semantics: str | None
    attribution_semantics: str | None
    data_through: str | None
    freshness: str | None
    aggregation_method: str | None
    deduplication_status: str | None


def canonicalize_metric(raw: Mapping[str, Any], *, field_map: Mapping[str, str] | None = None, provider: str | None = None, metric: str = "", semantics: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize a metric while retaining provenance and attribution semantics."""
    mapping = field_map or {}
    meta = semantics or {}
    raw_metric_key = mapping.get("value") or metric or "value"
    item = CanonicalMetric(
        value=raw.get(raw_metric_key),
        metric=metric,
        provider=provider,
        source_grain=meta.get("source_grain") or raw.get(mapping.get("source_grain", "source_grain")),
        metric_semantics=meta.get("metric_semantics") or raw.get(mapping.get("metric_semantics", "metric_semantics")),
        attribution_semantics=meta.get("attribution_semantics") or raw.get(mapping.get("attribution_semantics", "attribution_semantics")),
        data_through=meta.get("data_through") or raw.get(mapping.get("data_through", "data_through")),
        freshness=meta.get("freshness") or raw.get(mapping.get("freshness", "freshness")),
        aggregation_method=meta.get("aggregation_method") or raw.get(mapping.get("aggregation_method", "aggregation_method")),
        deduplication_status=meta.get("deduplication_status") or raw.get(mapping.get("deduplication_status", "deduplication_status")),
    )
    return asdict(item)


def validate_safe_write_capabilities(capabilities: Mapping[str, str] | None) -> dict[str, Any]:
    """Require the full Decision→Prepare→Diff→Apply→Read-back chain."""
    normalized = normalize_capabilities(capabilities, ("prepare_change_plan", "exact_diff", "apply_change_plan", "read_back"))
    missing = [name for name, status in normalized.items() if status != SUPPORTED]
    return {
        "allowed": not missing,
        "status": "SAFE_WRITE_CAPABILITY_VERIFIED" if not missing else SAFE_WRITE_CAPABILITY_NOT_AVAILABLE,
        "capabilities": normalized,
        "missing_or_uncertain": missing,
    }
