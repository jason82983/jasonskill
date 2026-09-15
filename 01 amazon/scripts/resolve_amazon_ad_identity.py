"""Read-only Amazon advertising identity resolver.

Rows are supplied by callers from the company mapping workbook and read-only
Provider responses. This module never edits source files or calls a remote API.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split()).casefold()


def _first(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


REQUIRED_IDENTITY_SHEETS = {
    "产品店铺映射": ("Product_Code", "Product_NewCode", "Product_Name", "广告组合", "SellerSpace_Store", "Marketplace", "ASIN", "SKU", "Status"),
    "填写说明": (),
    "产品对应变体": ("Product_Code", "Var_Code", "Var_Name"),
    "店铺产品代码前缀": ("SellerSpace_Store", "Product_Code_Prefix"),
}


def validate_identity_workbook_schema(sheet_headers: Mapping[str, Iterable[str]]) -> dict[str, Any]:
    """Check required sheets/columns without changing the workbook."""
    missing_sheets = [name for name in REQUIRED_IDENTITY_SHEETS if name not in sheet_headers]
    missing_fields: dict[str, list[str]] = {}
    for name, fields in REQUIRED_IDENTITY_SHEETS.items():
        actual = set(sheet_headers.get(name, ()))
        missing = [field for field in fields if field not in actual]
        if missing:
            missing_fields[name] = missing
    valid = not missing_sheets and not missing_fields
    return {"valid": valid, "missing_sheets": missing_sheets, "missing_fields": missing_fields, "status": "WORKBOOK_SCHEMA_OK" if valid else "AMAZON_IDENTITY_MAPPING_INCOMPLETE"}


def stable_sku_list(values: Iterable[Any] | None) -> list[str]:
    """Return deterministic, de-duplicated SKU values without choosing a primary SKU."""
    if isinstance(values, (str, bytes)):
        values = [values]
    cleaned = {str(value).strip() for value in (values or ()) if value not in (None, "") and str(value).strip()}
    return sorted(cleaned, key=lambda value: (value.casefold(), value))


def serialize_skus(values: Iterable[Any] | None) -> str:
    """Serialize SKU arrays for CSV/log fields using stable pipe-separated values."""
    return "|".join(stable_sku_list(values))


def _variant_records(formal_code: str, variant_rows: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str], str]:
    rows = [r for r in variant_rows if _norm(_first(r, "Product_Code", "Product Code")) == _norm(formal_code)]
    by_code: dict[str, dict[str, Any]] = {}
    conflicts: list[str] = []
    for row in rows:
        code = _first(row, "Var_Code", "Var Code", "variantCode")
        if not code:
            conflicts.append("variant row missing Var_Code")
            continue
        key = _norm(code)
        asin = _first(row, "Child_ASIN", "Child ASIN", "child_asin", "ASIN")
        sku = _first(row, "Child_SKU", "Child SKU", "child_sku", "SKU")
        if key not in by_code:
            by_code[key] = {"var_code": str(code), "var_names": set(), "asins": {}, "missing_asin": False, "missing_sku": False}
        group = by_code[key]
        name = _first(row, "Var_Name", "Var Name", "variantName")
        if name not in (None, ""):
            group["var_names"].add(str(name))
        asin_key = _norm(asin)
        if not asin_key:
            group["missing_asin"] = True
        if sku in (None, "") or not str(sku).strip():
            group["missing_sku"] = True
        group["asins"].setdefault(asin_key, {"child_asin": asin, "skus": set()})
        if sku not in (None, ""):
            group["asins"][asin_key]["skus"].add(str(sku).strip())

    records: list[dict[str, Any]] = []
    for key, group in by_code.items():
        asin_groups = [item for asin_key, item in group["asins"].items() if asin_key]
        if len(asin_groups) > 1:
            conflicts.append(f"Var_Code {group['var_code']} maps to multiple ASINs")
            continue
        if not asin_groups:
            asin_groups = [group["asins"].get("", {"child_asin": None, "skus": set()})]
        asin_group = asin_groups[0]
        skus = stable_sku_list(asin_group["skus"])
        var_names = sorted(group["var_names"], key=lambda value: (value.casefold(), value))
        record = {
            "var_code": group["var_code"],
            "var_name": var_names[0] if var_names else None,
            "child_asin": asin_group["child_asin"],
            "mapped_skus": skus,
            "sku_count": len(skus),
            # Legacy alias retained for callers that only display one field. It is
            # never used as the identity or as a default execution selection.
            "sku": skus[0] if len(skus) == 1 else None,
            "primary_advertised_sku": None,
            "identity_status": "MULTI_SKU_SAME_ASIN" if len(skus) > 1 else "SINGLE_SKU_ASIN",
            "mapping_incomplete": bool(group["missing_asin"] or group["missing_sku"]),
        }
        records.append(record)
    records.sort(key=lambda item: (_norm(item["var_code"]), _norm(item.get("child_asin"))))
    if conflicts and any("multiple ASINs" in conflict for conflict in conflicts):
        status = "VARIANT_ASIN_MAPPING_CONFLICT"
    elif conflicts:
        status = "VAR_CODE_NOT_UNIQUE"
    elif not records:
        status = "VARIANT_MAPPING_MISSING"
    elif any(not item["child_asin"] or not item["mapped_skus"] or item.get("mapping_incomplete") for item in records):
        status = "VARIANT_ASIN_SKU_UNMAPPED"
    else:
        status = "VARIANT_MAPPING_VERIFIED"
    return records, conflicts, status


def select_primary_advertised_sku(eligible_skus: Iterable[Any] | None, *, required: bool = False, preferred: Any = None) -> str | None:
    """Select a SKU only when an execution API truly requires one.

    A preferred, validated SKU or a sole eligible SKU may be selected; multiple
    eligible SKUs never fall back to Excel row order.
    """
    eligible = stable_sku_list(eligible_skus)
    if not required:
        return None
    if preferred in eligible:
        return str(preferred)
    return eligible[0] if len(eligible) == 1 else None


def decide_advertised_skus(mapped_skus: Iterable[Any] | None, eligible_skus: Iterable[Any] | None, *, asin_deduped: bool = False) -> dict[str, Any]:
    """Apply read-only eligibility results without forcing every mapped SKU into Ads."""
    mapped = stable_sku_list(mapped_skus)
    mapped_set = set(mapped)
    eligible = [sku for sku in stable_sku_list(eligible_skus) if sku in mapped_set]
    if not eligible:
        return {
            "action": "ADVERTISED_PRODUCT_NOT_ELIGIBLE",
            "status": "ADVERTISED_PRODUCT_NOT_ELIGIBLE",
            "mapped_skus": mapped,
            "eligible_skus": [],
            "advertised_skus": [],
            "sku_count": len(mapped),
            "primary_advertised_sku": None,
        }
    action = "ADD_ONCE" if asin_deduped else ("ADD_BOTH" if len(eligible) == len(mapped) and len(eligible) > 1 else "ADD_ELIGIBLE_SKU_ONLY")
    status = "SKU_ELIGIBILITY_VERIFIED" if len(eligible) == len(mapped) else "SKU_ELIGIBILITY_PARTIAL"
    return {
        "action": action,
        "status": status,
        "mapped_skus": mapped,
        "eligible_skus": eligible,
        "advertised_skus": eligible,
        "sku_count": len(mapped),
        "primary_advertised_sku": select_primary_advertised_sku(eligible, required=len(eligible) == 1),
    }


def aggregate_metric_to_asin(rows: Iterable[Mapping[str, Any]], metric: str, *, source_grain: str, already_asin_aggregate: bool = False, sku_key: str = "sku") -> dict[str, Any]:
    """Aggregate only when the source grain makes de-duplication semantics explicit."""
    items = list(rows)
    if already_asin_aggregate or _norm(source_grain) == "asin":
        if len(items) != 1:
            return {"value": None, "status": "ASIN_AGGREGATION_UNCERTAIN", "method": "UNCERTAIN", "source_grain": "ASIN", "deduplication_check": "UNCERTAIN"}
        return {"value": items[0].get(metric), "status": "DIRECT_ASIN", "method": "DIRECT_ASIN", "source_grain": "ASIN", "deduplication_check": "NOT_REQUIRED"}
    if _norm(source_grain) != "sku":
        return {"value": None, "status": "ASIN_AGGREGATION_UNCERTAIN", "method": "UNCERTAIN", "source_grain": source_grain, "deduplication_check": "UNCERTAIN"}
    sku_values = [str(item.get(sku_key) or "").strip() for item in items]
    if not items or any(not sku for sku in sku_values) or len(set(sku_values)) != len(sku_values):
        return {"value": None, "status": "ASIN_AGGREGATION_UNCERTAIN", "method": "UNCERTAIN", "source_grain": "SKU", "deduplication_check": "UNCERTAIN"}
    try:
        value = sum(float(item.get(metric) or 0) for item in items)
    except (TypeError, ValueError):
        return {"value": None, "status": "ASIN_AGGREGATION_UNCERTAIN", "method": "UNCERTAIN", "source_grain": "SKU", "deduplication_check": "UNCERTAIN"}
    return {"value": value, "status": "SUM_DISTINCT_SKU", "method": "SUM_DISTINCT_SKU", "source_grain": "SKU", "deduplication_check": "PASS"}


def summarize_inventory_by_asin(rows: Iterable[Mapping[str, Any]], *, quantity_field: str = "available", source_grain: str = "SKU", already_asin_aggregate: bool = False, sku_key: str = "sku") -> dict[str, Any]:
    """Return an ASIN summary plus SKU breakdown while preserving SKU exceptions."""
    items = list(rows)
    breakdown = [{"sku": item.get(sku_key), "available": item.get(quantity_field)} for item in items]
    aggregate = aggregate_metric_to_asin(items, quantity_field, source_grain=source_grain, already_asin_aggregate=already_asin_aggregate, sku_key=sku_key)
    return {
        "asin_total": aggregate["value"],
        "status": aggregate["status"],
        "method": aggregate["method"],
        "source_grain": aggregate.get("source_grain", source_grain),
        "deduplication_check": aggregate.get("deduplication_check", "UNCERTAIN"),
        "sku_breakdown": breakdown,
    }


def resolve_advertising_identity(
    product_code: str,
    mapping_rows: Iterable[Mapping[str, Any]],
    portfolio_rows: Iterable[Mapping[str, Any]] | None = None,
    *,
    prefix_rows: Iterable[Mapping[str, Any]] | None = None,
    variant_rows: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve a formal Product_Code or Product_NewCode with read-only rows."""
    requested = _norm(product_code)
    rows = [r for r in mapping_rows if requested in {
        _norm(_first(r, "Product_Code", "Product Code")),
        _norm(_first(r, "Product_NewCode", "Product NewCode")),
    }]
    active = [r for r in rows if _norm(_first(r, "Status")).upper() == "ACTIVE"]
    result: dict[str, Any] = {
        "product_code": product_code,
        "formal_product_code": None,
        "product_new_code": None,
        "conflicts": [],
        "identity_status": "IDENTITY_INCOMPLETE",
        "mcp_validation_status": "NOT_RUN",
        "parent_asin": None,
        "child_asin": None,
        "advertised_asin": None,
        "mapped_skus": [],
        "advertised_skus": [],
        "primary_advertised_sku": None,
        "sku_count": 0,
        "variants": [],
        "variant_status": "VARIANT_NOT_PROVIDED",
        "prefix_status": "PREFIX_NOT_PROVIDED",
    }
    if not active:
        result.update(mapping_status="MAPPING_MISSING", portfolio_status="MAPPING_PORTFOLIO_MISSING", identity_status="IDENTITY_MISSING")
        return result
    formal_codes = {_norm(_first(r, "Product_Code", "Product Code")) for r in active if _first(r, "Product_Code", "Product Code")}
    if len(active) != 1 or len(formal_codes) > 1:
        result.update(mapping_status="MAPPING_MULTIPLE_ACTIVE", portfolio_status="MAPPING_PORTFOLIO_MISSING", identity_status="IDENTITY_CONFLICT")
        result["conflicts"].append("multiple ACTIVE identity mapping rows")
        return result
    row = active[0]
    formal = _first(row, "Product_Code", "Product Code")
    new_code = _first(row, "Product_NewCode", "Product NewCode")
    portfolio_name = _first(row, "Portfolio_Name", "Portfolio Name", "广告组合")
    result.update(
        product_code=formal or product_code,
        formal_product_code=formal,
        product_new_code=new_code,
        product_name=_first(row, "Product_Name", "Product Name"),
        seller_space_store=_first(row, "SellerSpace_Store", "SellerSpace Store"),
        marketplace=_first(row, "Marketplace"),
        own_asin=_first(row, "ASIN", "Own ASIN"),
        sku=_first(row, "SKU"),
        portfolio_name=portfolio_name,
        mapping_status="MAPPING_UNIQUE_ACTIVE" if formal else "FORMAL_PRODUCT_CODE_MISSING",
    )
    if not formal:
        result["identity_status"] = "IDENTITY_CONFLICT"
        result["conflicts"].append("formal Product_Code is missing")
    if prefix_rows is not None:
        prefixes = [p for p in prefix_rows if _norm(_first(p, "SellerSpace_Store", "SellerSpace Store", "store")) == _norm(result.get("seller_space_store"))]
        if not prefixes:
            result["prefix_status"] = "PREFIX_MAPPING_MISSING"
        else:
            expected_values = {_norm(_first(p, "Product_Code_Prefix", "Product Code Prefix", "prefix")) for p in prefixes}
            expected = _first(prefixes[0], "Product_Code_Prefix", "Product Code Prefix", "prefix")
            result.update(product_code_prefix=expected, expected_product_code_prefix=expected)
            if len(expected_values) > 1:
                result["prefix_status"] = "PREFIX_CONFLICT"
                result["conflicts"].append("store maps to multiple Product_Code_Prefix values")
            elif not formal:
                result["prefix_status"] = "FORMAL_PRODUCT_CODE_MISSING"
            elif expected and _norm(formal).startswith(_norm(expected)):
                result["prefix_status"] = "PREFIX_PASS"
            else:
                result["prefix_status"] = "PREFIX_CONFLICT"
                result["conflicts"].append("Product_Code does not match store prefix")
    if variant_rows is not None and formal:
        variants, variant_conflicts, variant_status = _variant_records(str(formal), variant_rows)
        result.update(variants=variants, variant_status=variant_status)
        result["conflicts"].extend(variant_conflicts)
        mapped = []
        for variant in variants:
            mapped.extend(variant.get("mapped_skus", []))
        result["mapped_skus"] = stable_sku_list(mapped)
        result["sku_count"] = len(result["mapped_skus"])
    if result.get("own_asin"):
        result["advertised_asin"] = result["own_asin"]
    if not result.get("mapped_skus") and result.get("sku"):
        result["mapped_skus"] = stable_sku_list([result["sku"]])
        result["sku_count"] = len(result["mapped_skus"])
    if not portfolio_name:
        result["portfolio_status"] = "MAPPING_PORTFOLIO_MISSING"
    elif portfolio_rows is None:
        result["portfolio_status"] = "MCP_PORTFOLIO_PENDING"
    else:
        candidates = []
        for p in portfolio_rows:
            name = _first(p, "portfolioName", "portfolio_name", "Portfolio Name", "name", "名称")
            store = _first(p, "sellerSpaceStore", "store", "SellerSpace_Store", "SellerSpace Store")
            market = _first(p, "marketplace", "Marketplace")
            if _norm(name) == _norm(portfolio_name) and (not store or _norm(store) == _norm(result.get("seller_space_store"))) and (not market or _norm(market) == _norm(result.get("marketplace"))):
                candidates.append(p)
        if len(candidates) == 1:
            pid = _first(candidates[0], "portfolioId", "portfolio_id", "Portfolio ID", "id")
            result["portfolio_status"] = "PORTFOLIO_VERIFIED" if pid not in (None, "") else "PORTFOLIO_ID_UNRESOLVED"
            if pid not in (None, ""):
                result["portfolio_id"] = str(pid)
        elif len(candidates) > 1:
            result["portfolio_status"] = "PORTFOLIO_NAME_AMBIGUOUS"
            result["conflicts"].append("portfolio name matched multiple IDs")
        else:
            result["portfolio_status"] = "PORTFOLIO_SCOPE_CONFLICT"
    if result["conflicts"]:
        result["identity_status"] = "IDENTITY_CONFLICT"
    elif formal and result.get("seller_space_store") and result.get("marketplace") and result.get("own_asin") and (result.get("mapped_skus") or result.get("sku")) and result.get("portfolio_status") == "PORTFOLIO_VERIFIED":
        result["identity_status"] = "ADVERTISING_IDENTITY_VERIFIED"
    return result


def format_campaign_name(product_code: str, ad_type: str, role: str, target_match: str, sequence: int | str, var_code: str | None = None) -> str:
    """Shared naming contract, with optional variant segment."""
    prefix = f"{product_code}.{var_code}." if var_code else f"{product_code}."
    seq = f"{int(sequence):02d}" if str(sequence).isdigit() else str(sequence)
    return f"{prefix}{ad_type}-{role}-{target_match}-{seq}"


def format_ad_group_name(product_code: str, role: str, sequence: int | str = 1, var_code: str | None = None, group: str | None = None) -> str:
    """Stable Ad Group name; it does not repeat AdType or Match in Campaign."""
    seq = f"{int(sequence):02d}" if str(sequence).isdigit() else str(sequence)
    prefix = f"{product_code}.{var_code}." if var_code else f"{product_code}."
    suffix = group or role
    return f"{prefix}{suffix}-{seq}" if not group else f"{prefix}{suffix}"


def next_campaign_sequence(existing_names: Iterable[str], product_code: str, ad_type: str, role: str, target_match: str, var_code: str | None = None) -> dict[str, Any]:
    """Return an approval-time collision check; existing objects are never renamed."""
    existing = set(existing_names)
    seq = 1
    while format_campaign_name(product_code, ad_type, role, target_match, seq, var_code) in existing:
        seq += 1
    name = format_campaign_name(product_code, ad_type, role, target_match, seq, var_code)
    return {"name": name, "sequence": f"{seq:02d}", "collision": seq > 1, "reason": "Existing sequence detected" if seq > 1 else "No collision"}


_NAME_RE = re.compile(r"^(?P<product>[A-Za-z0-9]+)\.(?:(?P<variant>[A-Za-z0-9]+)\.)?(?P<ad_type>SP|SB|SD)-(?P<role>COR|EXP|DIS|COM|CAT|DEF)-(?P<target>EXA|PHR|BRO|AUT|ASI|CAT)(?:-(?P<placement>TOS|PPG))?-(?P<sequence>\d{2,})$")


def parse_campaign_name(name: str) -> dict[str, Any]:
    """Parse current stable names; non-matching names remain legacy hints."""
    match = _NAME_RE.match(str(name or "").strip())
    if not match:
        return {"name": name, "status": "LEGACY_UNKNOWN", "product_code": None, "var_code": None, "ad_type": None, "role": None, "target_match": None, "sequence": None}
    data = match.groupdict()
    return {"name": name, "status": "CURRENT_STANDARD", "product_code": data["product"], "var_code": data["variant"], "ad_type": data["ad_type"], "role": data["role"], "target_match": data["target"], "placement_experiment": data["placement"], "sequence": data["sequence"]}


def validate_campaign_name(name: str) -> dict[str, Any]:
    """Return parser status and machine-readable validation issues."""
    parsed = parse_campaign_name(name)
    if parsed["status"] == "CURRENT_STANDARD":
        return {"valid": True, "status": parsed["status"], "issues": [], "parsed": parsed}
    return {"valid": False, "status": parsed["status"], "issues": ["name does not match current Campaign schema"], "parsed": parsed}


def classify_campaign_name(name: str, resolved_identity: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify a name without allowing it to become the identity source."""
    parsed = parse_campaign_name(name)
    if resolved_identity is None:
        return parsed
    product = _norm(resolved_identity.get("formal_product_code") or resolved_identity.get("product_code"))
    variant = _norm(resolved_identity.get("var_code"))
    if parsed["status"] == "CURRENT_STANDARD":
        if (product and _norm(parsed["product_code"]) != product) or (variant and parsed["var_code"] and _norm(parsed["var_code"]) != variant):
            parsed["status"] = "NAME_IDENTITY_CONFLICT"
    elif product or variant:
        parsed["status"] = "LEGACY_RECOGNIZABLE"
    return parsed


IDENTITY_DIFF_FIELDS = ("product_code", "product_new_code", "product_code_prefix", "seller_space_store", "marketplace", "portfolio_id", "portfolio_name", "var_code", "child_asin", "sku", "mapped_skus", "advertised_skus", "primary_advertised_sku", "campaign_name")


def diff_identity_fields(approved: Mapping[str, Any], prepared: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Compare material identity fields before a prepared change plan."""
    return {field: {"approved": approved.get(field), "prepared": prepared.get(field)} for field in IDENTITY_DIFF_FIELDS if approved.get(field) != prepared.get(field)}


def verify_advertised_product(approved: Mapping[str, Any], readback: Mapping[str, Any]) -> dict[str, Any]:
    """Read-back check for Own advertised Child ASIN/SKU and variant."""
    fields = ("product_code", "var_code", "child_asin", "sku", "mapped_skus", "advertised_skus", "primary_advertised_sku", "portfolio_id")
    mismatches = {}
    for field in fields:
        left, right = approved.get(field), readback.get(field)
        if field.endswith("skus") and left is not None and right is not None:
            if stable_sku_list(left) != stable_sku_list(right):
                mismatches[field] = (stable_sku_list(left), stable_sku_list(right))
        elif left != right:
            mismatches[field] = (left, right)
    return {"ok": not mismatches, "status": "READ_BACK_MATCH" if not mismatches else "ADVERTISED_PRODUCT_MISMATCH", "mismatches": mismatches}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit("Use the read-only resolver functions; no network calls are implemented.")
