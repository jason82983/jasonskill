"""Pure desired-vs-actual planning and guarded execution for 6-1.

Provider I/O is injected by the caller.  Tests use a fake provider; this module
never connects to Amazon or SellerSpace itself.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.resolve_amazon_ad_identity import (  # noqa: E402
    format_ad_group_name,
    format_campaign_name,
    parse_campaign_name,
)
from scripts.campaign_scope_contract import build_campaign_scope, campaign_is_in_scope, load_product_campaign_scope


ENTITY_ORDER = {"campaign": 0, "ad_group": 1, "advertised_product": 2, "target": 3}
UPDATE_FIELDS = {
    "campaign": {"name", "daily_budget", "placement", "bidding_strategy", "status"},
    "ad_group": {"name", "default_bid", "status"},
    "advertised_product": {"status"},
    "target": {"bid", "status"},
}
IDENTITY_FIELDS = {
    "logical_id", "amazon_id", "entity_type", "product_code", "var_code",
    "intent_code", "battle_unit_id", "parent_logical_id", "ad_type",
    "control_mode",
    "campaign_tag", "campaign_prefix",
    "technical_role", "target_type", "match_type", "value", "advertised_asin",
    "own_asin", "sku", "advertised_sku", "advertised_skus", "store",
    "marketplace", "portfolio_name", "portfolio_id",
}
AUDIT_FIELDS = {"605_run_id", "logical_group", "sequence", "approved_battle_unit_ids"}
CREATE_ONLY_FIELDS = {"advertised_product": {"name"}}


class Provider(Protocol):
    def query_actual(self) -> list[dict[str, Any]]: ...
    def prepare(self, changes: list[dict[str, Any]], idempotency_key: str) -> Mapping[str, Any]: ...
    def apply(self, plan_id: str, idempotency_key: str) -> Mapping[str, Any]: ...
    def read_back(self, logical_ids: list[str]) -> list[dict[str, Any]]: ...


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_id(entity_type: str, *parts: Any) -> str:
    """Readable, deterministic logical identity; excludes mutable settings."""
    if entity_type not in ENTITY_ORDER or not parts or any(part in (None, "") for part in parts):
        raise ValueError("LOGICAL_IDENTITY_INCOMPLETE")
    return f"{entity_type}:" + "|".join(str(part).strip() for part in parts)


def translate_role(task: str, method: str) -> tuple[str, str, str]:
    """Translate an already-approved 605 task/method; never chooses strategy."""
    method = str(method or "").strip().upper()
    task = str(task or "").strip()
    tools = {
        "EXACT": "EXA", "PHRASE": "PHR", "BROAD": "BRO", "AUTO": "AUT",
        "ASIN": "ASI", "PT": "PT", "PRODUCT": "PT", "PRODUCT_TARGET": "PT",
        "CATEGORY": "CAT",
    }
    if method not in tools:
        raise ValueError("ROLE_TRANSLATION_AMBIGUOUS")
    if method == "ASIN":
        role = "COM"
    elif method in {"PT", "PRODUCT", "PRODUCT_TARGET"}:
        role = "DIS"
    elif method == "CATEGORY":
        role = "CAT"
    else:
        role = {"首攻": "COR", "核心": "COR", "扩展": "EXP", "探索": "DIS"}.get(task)
    if not role:
        raise ValueError("ROLE_TRANSLATION_AMBIGUOUS")
    return role, tools[method], "SP"


def campaign_logical_id(product_code: str, variant_code: str, intent_codes: Iterable[str], ad_type: str, role: str, target_match: str, logical_group: str = "DEFAULT", control_mode: str | None = None, campaign_tag: str | None = None) -> str:
    codes = sorted({str(code).strip() for code in intent_codes if str(code).strip()})
    if control_mode == "独立" and not codes:
        raise ValueError("INTENT_CODE_REQUIRED_FOR_INDEPENDENT_CAMPAIGN")
    if control_mode == "共享":
        codes = []
    elif control_mode == "不投":
        raise ValueError("NO_INVESTMENT_HAS_NO_CAMPAIGN")
    elif control_mode not in (None, "独立"):
        raise ValueError("INVALID_CONTROL_MODE")
    intent_key = "+".join(codes) if codes else "NO_INTENT"
    # Multiple Intent Codes are allowed only when the approved architecture
    # deliberately shares one physical Campaign; that set remains stable.
    parts = (product_code, *([campaign_tag] if campaign_tag else []), variant_code or "NO_VARIANT", intent_key, ad_type, role, target_match, logical_group)
    return stable_id("campaign", *parts, *([control_mode] if control_mode else []))


def ad_group_logical_id(campaign_id: str, logical_group: str) -> str:
    return stable_id("ad_group", campaign_id, logical_group)


def target_logical_id(battle_unit_id: str, campaign_id: str | None = None) -> str:
    """Bind a target to its physical control boundary so migrations are additive."""
    return stable_id("target", battle_unit_id, campaign_id) if campaign_id else stable_id("target", battle_unit_id)


def execution_id(product_code: str, run_id: str, desired: Iterable[Mapping[str, Any]]) -> str:
    """Stable for the same approved 605 run and desired state; no wall-clock input."""
    digest = sha256(_canonical(sorted((dict(row) for row in desired), key=lambda row: row["logical_id"])).encode("utf-8")).hexdigest()[:16]
    return f"6-1:{product_code}:{run_id}:{digest}"


def resolve_mode(actual_entities: Iterable[Mapping[str, Any]]) -> str:
    """Choose BUILD only when no live advertising entities exist."""
    return "RECONCILE" if any(True for _ in actual_entities) else "BUILD"


def validate_desired_state(entities: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(entity) for entity in entities]
    seen: set[str] = set()
    for row in rows:
        entity_type = row.get("entity_type")
        logical_id = row.get("logical_id")
        if entity_type not in ENTITY_ORDER or not logical_id or logical_id in seen:
            raise ValueError("DESIRED_STATE_INVALID")
        if not row.get("approved", False):
            raise ValueError("INVALID_APPROVAL_STATE")
        seen.add(str(logical_id))
        if entity_type in {"ad_group", "advertised_product", "target"} and not row.get("parent_logical_id"):
            raise ValueError("DESIRED_STATE_INVALID")
        required_by_type = {
            "campaign": ("name", "daily_budget", "placement", "bidding_strategy", "status"),
            "ad_group": ("name", "default_bid", "status"),
            "advertised_product": ("name", "advertised_asin", "sku", "status"),
            "target": ("value", "target_type", "bid", "status"),
        }
        required = required_by_type[entity_type]
        if any(row.get(field) in (None, "") for field in required):
            raise ValueError("DESIRED_STATE_INVALID")
        mutable = set(row) - IDENTITY_FIELDS - AUDIT_FIELDS - {"approved"}
        if mutable - UPDATE_FIELDS[entity_type] - CREATE_ONLY_FIELDS.get(entity_type, set()):
            # Reject unknown knobs instead of treating them as silently writable.
            raise ValueError("DESIRED_STATE_FIELD_NOT_ALLOWED")
    by_id = {str(row["logical_id"]): row for row in rows}
    for row in rows:
        parent_id = row.get("parent_logical_id")
        if parent_id:
            parent = by_id.get(str(parent_id))
            if parent is None:
                raise ValueError("DESIRED_STATE_INVALID")
            expected_type = "campaign" if row["entity_type"] == "ad_group" else "ad_group"
            if parent["entity_type"] != expected_type:
                raise ValueError("DESIRED_STATE_INVALID")
    return sorted(rows, key=lambda row: (ENTITY_ORDER[row["entity_type"]], row["logical_id"]))


def build_diff(desired_entities: Iterable[Mapping[str, Any]], actual_entities: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    desired = validate_desired_state(desired_entities)
    actual_rows = [dict(row) for row in actual_entities]
    actual_by_id: dict[str, dict[str, Any]] = {}
    for row in actual_rows:
        logical_id = row.get("logical_id")
        if not logical_id or not row.get("amazon_id"):
            raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        if logical_id in actual_by_id:
            raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        actual_by_id[str(logical_id)] = row

    desired_by_id = {str(row["logical_id"]): row for row in desired}
    actions: list[dict[str, Any]] = []
    for row in desired:
        key = str(row["logical_id"])
        current = actual_by_id.get(key)
        if current is None:
            actions.append({"entity_type": row["entity_type"], "logical_id": key, "action": "CREATE", "before": None, "desired": row})
            continue
        if current.get("entity_type") != row["entity_type"]:
            raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        if row["entity_type"] != "campaign" and current.get("parent_logical_id") != row.get("parent_logical_id"):
            raise ValueError("ADGROUP_IDENTITY_CONFLICT" if row["entity_type"] == "ad_group" else "TARGET_IDENTITY_CONFLICT")
        immutable_fields = (IDENTITY_FIELDS - {"logical_id", "amazon_id", "entity_type", "parent_logical_id"}) & set(row)
        if row["entity_type"] == "advertised_product" and "name" in row:
            immutable_fields.add("name")
        if any(current.get(field) != row.get(field) for field in immutable_fields if field in current):
            code = "CAMPAIGN_IDENTITY_CONFLICT" if row["entity_type"] == "campaign" else "TARGET_IDENTITY_CONFLICT"
            raise ValueError(code)
        changed = {
            field: {"before": current.get(field), "desired": row.get(field)}
            for field in UPDATE_FIELDS[row["entity_type"]]
            if field in row and current.get(field) != row.get(field)
        }
        if changed:
            actions.append({"entity_type": row["entity_type"], "logical_id": key, "amazon_id": current["amazon_id"], "action": "UPDATE", "before": changed, "desired": row})
        else:
            actions.append({"entity_type": row["entity_type"], "logical_id": key, "amazon_id": current["amazon_id"], "action": "NO_CHANGE", "before": None, "desired": row})
    desired_targets_by_battle = {
        str(row.get("battle_unit_id")): row for row in desired
        if row["entity_type"] == "target" and row.get("battle_unit_id")
    }
    for key, current in actual_by_id.items():
        if key not in desired_by_id:
            moved = (current.get("entity_type") == "target"
                     and str(current.get("battle_unit_id", "")) in desired_targets_by_battle)
            action = "MIGRATION_CANDIDATE" if moved else "PAUSE_CANDIDATE"
            actions.append({"entity_type": current["entity_type"], "logical_id": key,
                            "amazon_id": current["amazon_id"], "action": action,
                            "before": current,
                            "desired": desired_targets_by_battle.get(str(current.get("battle_unit_id"))) if moved else None})
    return sorted(actions, key=lambda item: (ENTITY_ORDER[item["entity_type"]], item["logical_id"], item["action"]))


def exact_change_digest(changes: Iterable[Mapping[str, Any]]) -> str:
    return sha256(_canonical(list(changes)).encode("utf-8")).hexdigest()


def execute_approved_diff(actions: Iterable[Mapping[str, Any]], provider: Provider, *, approved: bool, idempotency_key: str) -> dict[str, Any]:
    """Execute only exact approved CREATE/UPDATE actions; never executes pause candidates."""
    rows = [dict(action) for action in actions]
    changes = [row for row in rows if row["action"] in {"CREATE", "UPDATE"}]
    if not approved:
        return {"status": "EXECUTION_NOT_READY", "executed": 0, "read_back": []}
    if not changes:
        return {"status": "NO_CHANGE", "executed": 0, "read_back": []}
    try:
        preview = dict(provider.prepare(changes, idempotency_key))
    except Exception as exc:
        return {"status": "EXECUTION_NOT_READY", "executed": 0, "error": str(exc)}
    if preview.get("status") not in {"PREPARED", "SUCCESS"} or preview.get("change_digest") != exact_change_digest(changes):
        return {"status": "TECHNICAL_EXECUTION_CONFLICT", "executed": 0, "plan_id": preview.get("plan_id")}
    plan_id = preview.get("plan_id")
    if not plan_id:
        return {"status": "CREATE_FAILED", "executed": 0}
    try:
        applied = dict(provider.apply(str(plan_id), idempotency_key))
    except Exception as exc:
        failure = "UPDATE_FAILED" if all(row["action"] == "UPDATE" for row in changes) else "CREATE_FAILED"
        return {"status": failure, "executed": 0, "plan_id": plan_id, "error": str(exc)}
    if applied.get("status") not in {"APPLIED", "SUCCESS"}:
        failure = "UPDATE_FAILED" if all(row["action"] == "UPDATE" for row in changes) else "CREATE_FAILED"
        return {"status": failure, "executed": 0, "plan_id": plan_id}
    ids = [str(row["logical_id"]) for row in changes]
    try:
        observed = provider.read_back(ids)
    except Exception as exc:
        return {"status": "READBACK_FAILED", "executed": len(changes), "plan_id": plan_id, "error": str(exc), "read_back": []}
    by_id = {str(row.get("logical_id")): row for row in observed}
    failures = []
    for action in changes:
        logical_id = str(action["logical_id"])
        result = by_id.get(logical_id)
        desired = action["desired"]
        if (not result or not result.get("amazon_id")
                or (action["entity_type"] != "campaign" and result.get("parent_logical_id") != desired.get("parent_logical_id"))
                or any(result.get(field) != desired.get(field)
                       for field in IDENTITY_FIELDS
                       if field in desired and field not in {"logical_id", "amazon_id", "entity_type", "parent_logical_id"})
                or (action["entity_type"] == "advertised_product" and result.get("name") != desired.get("name"))
                or any(result.get(field) != desired.get(field) for field in UPDATE_FIELDS[action["entity_type"]] if field in desired)):
            failures.append(logical_id)
    if failures:
        return {"status": "READBACK_FAILED", "executed": len(changes), "plan_id": plan_id, "failed_logical_ids": failures, "read_back": observed}
    return {"status": "FULL_SUCCESS", "executed": len(changes), "plan_id": plan_id, "read_back": observed}


def _number(value: Any, *, positive: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError("EXECUTION_NOT_READY") from None
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError("EXECUTION_NOT_READY")
    return result


def _target_value(row: Mapping[str, Any], method: str, settings: Mapping[str, Any]) -> tuple[str, str]:
    if method in {"EXACT", "PHRASE", "BROAD"}:
        value = str(row.get("词", "")).strip()
        if value:
            return "KEYWORD", value
    keys = ("Target Value", "目标值", "Target ASIN", "目标ASIN", "Category Target", "类目目标")
    value = next((str(row.get(key, "")).strip() for key in keys if str(row.get(key, "")).strip()), "")
    # A target added by 605 must be represented by an approved plan fact.
    # Execution parameters may not introduce a new ASIN/category/keyword.
    if not value:
        raise ValueError("TECHNICAL_EXECUTION_CONFLICT")
    return {"AUTO": "AUTO", "ASIN": "ASIN", "PT": "PRODUCT", "PRODUCT": "PRODUCT",
            "PRODUCT_TARGET": "PRODUCT", "CATEGORY": "CATEGORY"}[method], value


def _identity_for_desired(identity: Mapping[str, Any]) -> dict[str, Any]:
    if identity.get("identity_status") != "ADVERTISING_IDENTITY_VERIFIED":
        raise ValueError("TECHNICAL_EXECUTION_CONFLICT")
    product = str(identity.get("product_code", "")).strip()
    variant = str(identity.get("var_code", "")).strip()
    own_asin = str(identity.get("own_asin", "")).strip()
    asin = str(identity.get("advertised_asin") or identity.get("child_asin") or own_asin).strip()
    skus = identity.get("advertised_skus") or ([identity.get("sku")] if identity.get("sku") else [])
    skus = sorted({str(item).strip() for item in skus if str(item).strip()})
    benchmarks = {str(item).strip() for item in identity.get("benchmark_asins", []) if str(item).strip()}
    allowed_asins = {item for item in (own_asin, str(identity.get("child_asin", "")).strip(),
                                         *[str(x).strip() for x in identity.get("own_asins", [])]) if item}
    if (not product or not variant or not asin or not skus or not identity.get("store")
            or not identity.get("marketplace") or asin in benchmarks
            or (allowed_asins and asin not in allowed_asins)):
        raise ValueError("TECHNICAL_EXECUTION_CONFLICT")
    return {"product_code": product, "var_code": variant, "own_asin": own_asin or asin,
            "advertised_asin": asin, "advertised_skus": skus,
            "store": identity.get("store"), "marketplace": identity.get("marketplace"),
            "portfolio_name": identity.get("portfolio_name"), "portfolio_id": identity.get("portfolio_id")}


def build_desired_state_from_605(
    plan_bundle: Mapping[str, Any],
    identity: Mapping[str, Any],
    execution_parameters: Mapping[str, Mapping[str, Any]],
    *,
    product_code: str,
    campaign_tag: str,
    product_root: str | Path | None = None,
    actual_entities: Iterable[Mapping[str, Any]] = (),
    sequence_registry: Mapping[str, str | int] | None = None,
    allowed_phases: Iterable[str] = ("PHASE_1",),
    supported_ad_types: Iterable[str] = ("SP",),
) -> dict[str, Any]:
    """Translate one resolved 605 bundle into a complete, deterministic Desired State.

    All financial/execution parameters are supplied by the caller from approved
    limits and current evidence. This pure helper never chooses strategy or does I/O.
    """
    if (plan_bundle.get("status") != "LATEST_VALID_RUN_BUNDLE_RESOLVED"
            or not plan_bundle.get("run_id")):
        raise ValueError("61_INPUT_RUN_MISMATCH")
    try:
        assets = plan_bundle["assets"]
        intent_rows = assets["intent"]["rows"]
        keyword_rows = assets["keyword"]["rows"]
        battle_rows = assets["battle"]["rows"]
    except (KeyError, TypeError):
        raise ValueError("61_INPUT_SCHEMA_INVALID") from None
    # A/C/B are validated as one same-run bundle before translation.
    if not intent_rows or not keyword_rows or not battle_rows:
        raise ValueError("61_INPUT_SCHEMA_INVALID")
    allowed = set(allowed_phases)
    eligible = [row for row in battle_rows
                if row.get("确认状态") == "APPROVED"
                and row.get("计划阶段") in allowed
                and row.get("控制方式") != "不投"]
    if not eligible:
        raise ValueError("NO_APPROVED_BATTLE_PLAN")
    resolved_identity = _identity_for_desired(identity)
    if resolved_identity["product_code"] != str(product_code).strip():
        raise ValueError("TECHNICAL_EXECUTION_CONFLICT")
    ad_types = {str(item).upper() for item in supported_ad_types}
    scope = build_campaign_scope(product_code, campaign_tag)
    if product_root is not None:
        configured = load_product_campaign_scope(product_root)
        if configured != scope:
            raise ValueError("RUNTIME_SCOPE_MISMATCH")
        scope = configured
    actual = [dict(row) for row in actual_entities]
    actual = [row for row in actual if row.get("entity_type") != "campaign" or campaign_is_in_scope(row.get("name") or row.get("CampaignName"), scope["CampaignPrefix"])]
    actual_campaigns = {str(row.get("logical_id")): row for row in actual
                        if row.get("entity_type") == "campaign" and row.get("logical_id")}
    sequences = {str(key): str(value).zfill(2) for key, value in (sequence_registry or {}).items()}

    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in eligible:
        battle_id = str(row.get("作战单元ID", "")).strip()
        control = str(row.get("控制方式", "")).strip()
        intent_code = str(row.get("意图代码", "")).strip()
        phase = str(row.get("计划阶段", "")).strip()
        if not battle_id:
            raise ValueError("BATTLE_UNIT_ID_MISSING")
        if control not in {"独立", "共享"}:
            if control == "不投":
                continue
            raise ValueError("CONTROL_MODE_MISSING")
        if control == "独立" and not intent_code:
            raise ValueError("INTENT_CODE_MISSING")
        task = str(row.get("作战任务", "")).strip()
        method = str(row.get("投放方式", "")).strip().upper()
        role, tool, ad_type = translate_role(task, method)
        if ad_type not in ad_types:
            raise ValueError("TECHNICAL_EXECUTION_CONFLICT")
        settings = dict(execution_parameters.get(battle_id, {}))
        if not settings:
            raise ValueError("EXECUTION_NOT_READY")
        target_type, value = _target_value(row, method, settings)
        logical_group = str(settings.get("logical_group", "DEFAULT")).strip() or "DEFAULT"
        boundary = intent_code if control == "独立" else "NO_INTENT"
        grouping = (control, resolved_identity["product_code"], resolved_identity["var_code"],
                    ad_type, boundary, role, tool, phase, logical_group)
        record = groups.setdefault(grouping, {"row": row, "settings": settings, "targets": []})
        signature_fields = ("daily_budget", "placement", "bidding_strategy", "campaign_status",
                            "ad_group_default_bid", "ad_group_status", "portfolio_id", "portfolio_name")
        if any(_canonical(record["settings"].get(field)) != _canonical(settings.get(field))
               for field in signature_fields):
            raise ValueError("SHARED_GROUP_INCOMPATIBLE" if control == "共享" else "TECHNICAL_EXECUTION_CONFLICT")
        bid = _number(settings.get("target_bid"), positive=True)
        status = str(settings.get("target_status", "")).strip()
        if not status:
            raise ValueError("EXECUTION_NOT_READY")
        record["targets"].append({"row": row, "settings": settings, "battle_unit_id": battle_id,
                                  "intent_code": intent_code, "target_type": target_type,
                                  "match_type": tool if tool in {"EXA", "PHR", "BRO"} else tool,
                                  "value": value, "bid": bid, "status": status})

    if not groups:
        raise ValueError("NO_APPROVED_BATTLE_PLAN")
    desired: list[dict[str, Any]] = []
    campaign_candidates: list[dict[str, Any]] = []
    for grouping, data in groups.items():
        control, product, variant, ad_type, boundary, role, tool, phase, logical_group = grouping
        row, settings = data["row"], data["settings"]
        intent_code = str(row.get("意图代码", "")).strip() if control == "独立" else ""
        logical_id = campaign_logical_id(product, variant, [intent_code] if intent_code else [],
                                         ad_type, role, tool, f"{phase}:{logical_group}", control, scope["CampaignTag"])
        campaign_candidates.append({"grouping": grouping, "data": data, "logical_id": logical_id,
                                     "intent_code": intent_code, "role": role, "tool": tool,
                                     "ad_type": ad_type, "phase": phase, "control": control})

    # Append-only sequence registry; existing Logical IDs keep their persisted/live sequence.
    used_by_base: dict[str, set[int]] = {}
    for row in actual:
        if row.get("entity_type") != "campaign":
            continue
        live_name = str(row.get("name", ""))
        if not campaign_is_in_scope(live_name, scope["CampaignPrefix"]):
            continue
        parsed = parse_campaign_name(live_name)
        if parsed.get("status") == "CURRENT_STANDARD" and str(parsed.get("sequence", "")).isdigit():
            # The legacy parser calls segment 2 `var_code`; in the current
            # Campaign Scope contract it is an opaque CampaignTag instead.
            campaign_tag = live_name.split(".", 2)[1]
            base = (parsed.get("product_code"), campaign_tag, parsed.get("ad_type"),
                    parsed.get("role"), parsed.get("target_match"), parsed.get("intent_code"))
            used_by_base.setdefault(_canonical(base), set()).add(int(parsed["sequence"]))
    for candidate in sorted(campaign_candidates, key=lambda item: item["logical_id"]):
        logical_id = candidate["logical_id"]
        data = candidate["data"]
        live = actual_campaigns.get(logical_id)
        parsed_live = parse_campaign_name(str(live.get("name", ""))) if live else {}
        if live:
            if not campaign_is_in_scope(live.get("name"), scope["CampaignPrefix"]):
                raise ValueError("OUTSIDE_CAMPAIGN_SCOPE")
            seq = str(sequences.get(logical_id) or parsed_live.get("sequence") or "01").zfill(2)
            sequences[logical_id] = seq
            # Retain the live name, including a legacy form; no implicit rename.
            campaign_name = str(live.get("name", "")).strip()
            if not campaign_name:
                raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        else:
            seq = sequences.get(logical_id)
            if not seq:
                candidate_row = _format_scoped_name(resolved_identity["product_code"], scope["CampaignTag"], candidate, 1)
                parsed = parse_campaign_name(candidate_row)
                base = (parsed.get("product_code"), scope["CampaignTag"], parsed.get("ad_type"),
                        parsed.get("role"), parsed.get("target_match"), parsed.get("intent_code"))
                used = used_by_base.setdefault(_canonical(base), set())
                next_seq = 1
                while next_seq in used:
                    next_seq += 1
                seq = f"{next_seq:02d}"
                used.add(next_seq)
                sequences[logical_id] = seq
            campaign_name = _format_scoped_name(resolved_identity["product_code"], scope["CampaignTag"], candidate, seq)
        if not campaign_is_in_scope(campaign_name, scope["CampaignPrefix"]):
            raise ValueError("OUTSIDE_CAMPAIGN_SCOPE")
        candidate.update(sequence=seq, campaign_name=campaign_name)

    names: dict[str, str] = {}
    for candidate in campaign_candidates:
        prior = names.setdefault(candidate["campaign_name"], candidate["logical_id"])
        if prior != candidate["logical_id"]:
            raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        data, grouping = candidate["data"], candidate["grouping"]
        control, product, variant, ad_type, boundary, role, tool, phase, logical_group = grouping
        row, settings = data["row"], data["settings"]
        campaign = {
            "entity_type": "campaign", "logical_id": candidate["logical_id"],
            "product_code": product, "var_code": variant, "ad_type": ad_type,
            "control_mode": control, "intent_code": candidate["intent_code"] or None,
            "technical_role": role, "target_type": tool, "logical_group": logical_group,
            "605_run_id": str(plan_bundle["run_id"]), "name": candidate["campaign_name"],
            "daily_budget": _number(settings.get("daily_budget"), positive=True),
            "placement": settings.get("placement"),
            "bidding_strategy": settings.get("bidding_strategy"),
            "status": settings.get("campaign_status"), "approved": True,
            "own_asin": resolved_identity["own_asin"], "advertised_asin": resolved_identity["advertised_asin"],
            "advertised_skus": resolved_identity["advertised_skus"], "store": resolved_identity["store"],
            "marketplace": resolved_identity["marketplace"], "portfolio_name": settings.get("portfolio_name"),
            "portfolio_id": settings.get("portfolio_id"),
        }
        campaign.update({"campaign_tag": scope["CampaignTag"], "campaign_prefix": scope["CampaignPrefix"]})
        if not isinstance(campaign["placement"], Mapping) or not campaign["bidding_strategy"] or not campaign["status"]:
            raise ValueError("EXECUTION_NOT_READY")
        desired.append(campaign)
        group_id = ad_group_logical_id(candidate["logical_id"], f"{tool}:{phase}:{logical_group}")
        group_name = format_ad_group_name(product, role, 1, variant, group=f"{role}-{tool}-{phase}")
        adgroup = {"entity_type": "ad_group", "logical_id": group_id,
                   "parent_logical_id": candidate["logical_id"], "product_code": product,
                   "var_code": variant, "ad_type": ad_type, "control_mode": control,
                   "technical_role": role, "target_type": tool, "name": group_name,
                   "default_bid": _number(settings.get("ad_group_default_bid"), positive=True),
                   "status": settings.get("ad_group_status"), "approved": True}
        if not adgroup["status"]:
            raise ValueError("EXECUTION_NOT_READY")
        desired.append(adgroup)
        for sku in resolved_identity["advertised_skus"]:
            product_id = stable_id("advertised_product", group_id, resolved_identity["advertised_asin"], sku)
            desired.append({"entity_type": "advertised_product", "logical_id": product_id,
                            "parent_logical_id": group_id, "product_code": product, "var_code": variant,
                            "own_asin": resolved_identity["own_asin"],
                            "advertised_asin": resolved_identity["advertised_asin"], "sku": sku,
                            "name": sku, "status": settings.get("product_status", "ENABLED"), "approved": True})
        for target in data["targets"]:
            # Non-keyword targets must be explicitly present in approved 605 data;
            # the current 605 contract does not infer them from benchmark ASINs.
            target_id = target_logical_id(target["battle_unit_id"], candidate["logical_id"])
            desired.append({"entity_type": "target", "logical_id": target_id,
                            "parent_logical_id": group_id, "product_code": product, "var_code": variant,
                            "ad_type": ad_type, "control_mode": control,
                            "intent_code": target["intent_code"] or None,
                            "battle_unit_id": target["battle_unit_id"],
                            "target_type": target["target_type"], "match_type": target["match_type"],
                            "value": target["value"], "bid": target["bid"],
                            "status": target["status"], "approved": True})
    normalized = validate_desired_state(desired)
    return {"status": "DESIRED_STATE_READY", "product_code": resolved_identity["product_code"],
            "var_code": resolved_identity["var_code"], "own_asin": resolved_identity["own_asin"],
            "ProductCode": scope["ProductCode"], "CampaignTag": scope["CampaignTag"], "CampaignPrefix": scope["CampaignPrefix"],
            "605_run_id": str(plan_bundle["run_id"]),
            "approved_battle_unit_ids": sorted({str(row.get("作战单元ID")) for row in eligible}),
            "sequence_registry": sequences, "entities": normalized}


def _format_scoped_name(product_code: str, campaign_tag: str, candidate: Mapping[str, Any], sequence: int | str) -> str:
    """Campaign second segment is an opaque runtime tag; real Variant remains identity metadata."""
    from scripts.campaign_scope_contract import build_campaign_scope
    scope = build_campaign_scope(product_code, campaign_tag)
    intent = f"-{candidate['intent_code']}" if candidate.get("intent_code") else ""
    return f"{scope['CampaignPrefix']}{candidate['ad_type']}-{candidate['role']}-{candidate['tool']}{intent}-{int(sequence):02d}"


def load_campaign_sequence_registry(path: str | Path) -> dict[str, str]:
    """Read append-only sequence reservations; missing file means no reservations."""
    source = Path(path)
    if not source.exists():
        return {}
    registry: dict[str, str] = {}
    try:
        with source.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("event") != "CAMPAIGN_SEQUENCE_RESERVED":
                    continue
                logical_id, sequence = str(row.get("logical_id", "")), str(row.get("sequence", ""))
                if not logical_id or not sequence.isdigit():
                    raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
                sequence = sequence.zfill(2)
                if logical_id in registry and registry[logical_id] != sequence:
                    raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
                registry[logical_id] = sequence
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("CAMPAIGN_IDENTITY_CONFLICT") from None
    return registry


def execution_manifest_path(product_root: str | Path) -> Path:
    return (Path(product_root) / "06_SKILL分析报告" / "广告表现汇报优化日志"
            / "6-1_广告实体身份清单.jsonl")


def resolve_actual_logical_identities(
    actual_entities: Iterable[Mapping[str, Any]], manifest_path: str | Path,
) -> list[dict[str, Any]]:
    """Attach persisted Logical IDs to live provider IDs; names never act as keys."""
    source = Path(manifest_path)
    manifest: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        if source.exists():
            with source.open("r", encoding="utf-8-sig") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if event.get("event") != "ENTITY_IDENTITY_VERIFIED":
                        continue
                    key = (str(event.get("entity_type", "")), str(event.get("amazon_id", "")))
                    if not all(key) or not event.get("logical_id"):
                        raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
                    if key in manifest and manifest[key].get("logical_id") != event.get("logical_id"):
                        raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
                    manifest[key] = event
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("CAMPAIGN_IDENTITY_CONFLICT") from None
    by_amazon_id = {amazon_id: event for (_, amazon_id), event in manifest.items()}
    resolved = []
    for item in actual_entities:
        row = dict(item)
        kind, amazon_id = str(row.get("entity_type", "")), str(row.get("amazon_id", ""))
        event = manifest.get((kind, amazon_id))
        if not event:
            raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        if row.get("logical_id") and row["logical_id"] != event["logical_id"]:
            raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        row["logical_id"] = event["logical_id"]
        if event.get("parent_logical_id"):
            row["parent_logical_id"] = event["parent_logical_id"]
        elif row.get("parent_amazon_id"):
            parent = by_amazon_id.get(str(row["parent_amazon_id"]))
            if not parent:
                raise ValueError("ADGROUP_IDENTITY_CONFLICT" if kind == "ad_group" else "TARGET_IDENTITY_CONFLICT")
            row["parent_logical_id"] = parent["logical_id"]
        resolved.append(row)
    return resolved


def append_verified_entities(
    manifest_path: str | Path,
    entities: Iterable[Mapping[str, Any]],
    *,
    run_id: str,
    generated_at: str,
) -> None:
    """Append verified Amazon-ID links after successful read-back."""
    rows = [dict(item) for item in entities]
    if not run_id or not generated_at or any(not item.get("logical_id") or not item.get("amazon_id")
                                              for item in rows):
        raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            event = {"event": "ENTITY_IDENTITY_VERIFIED", "entity_type": row.get("entity_type"),
                     "logical_id": row["logical_id"], "amazon_id": row["amazon_id"],
                     "parent_logical_id": row.get("parent_logical_id"),
                     "parent_amazon_id": row.get("parent_amazon_id"),
                     "name": row.get("name"), "battle_unit_id": row.get("battle_unit_id"),
                     "intent_code": row.get("intent_code"), "control_mode": row.get("control_mode"),
                     "product_code": row.get("product_code"), "var_code": row.get("var_code"),
                     "campaign_tag": row.get("campaign_tag"), "campaign_prefix": row.get("campaign_prefix"),
                     "ad_type": row.get("ad_type"), "technical_role": row.get("technical_role"),
                     "target_type": row.get("target_type"), "target_value": row.get("target_value", row.get("value")),
                     "match_type": row.get("match_type"), "run_id": run_id, "generated_at": generated_at}
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def reserve_campaign_sequences(path: str | Path, desired_state: Mapping[str, Any]) -> dict[str, str]:
    """Persist new logical sequence reservations before any provider write."""
    destination = Path(path)
    registry = load_campaign_sequence_registry(destination)
    proposed = dict(desired_state.get("sequence_registry") or {})
    missing = []
    for logical_id, sequence in proposed.items():
        sequence = str(sequence).zfill(2)
        if logical_id in registry and registry[logical_id] != sequence:
            raise ValueError("CAMPAIGN_IDENTITY_CONFLICT")
        if logical_id not in registry:
            missing.append((str(logical_id), sequence))
    if missing:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8", newline="\n") as handle:
            for logical_id, sequence in sorted(missing):
                handle.write(json.dumps({"event": "CAMPAIGN_SEQUENCE_RESERVED",
                                         "logical_id": logical_id, "sequence": sequence},
                                        ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
    return {**registry, **dict(missing)}


def reconcile_live_state(
    desired_entities: Iterable[Mapping[str, Any]],
    provider: Provider,
    *,
    approved: bool,
    idempotency_key: str,
) -> dict[str, Any]:
    """Query live state, compute the diff, execute exact approval, and expose recovery diff."""
    try:
        actual = provider.query_actual()
    except Exception as exc:
        return {"status": "ACTUAL_STATE_QUERY_FAILED", "error": str(exc), "actions": []}
    try:
        desired = validate_desired_state(desired_entities)
        actions = build_diff(desired, actual)
    except ValueError as exc:
        return {"status": str(exc), "execution_mode": resolve_mode(actual), "actions": []}
    mode = resolve_mode(actual)
    result = execute_approved_diff(actions, provider, approved=approved,
                                   idempotency_key=idempotency_key)
    output = {**result, "execution_mode": mode, "actions": actions}
    if result.get("status") in {"CREATE_FAILED", "UPDATE_FAILED", "READBACK_FAILED"}:
        # Never replay after an uncertain or partial result. Re-query and return
        # only the remaining diff for explicit recovery review.
        try:
            current = provider.query_actual()
            output["recovery_diff"] = build_diff(desired, current)
        except Exception as exc:
            output["recovery_status"] = "ACTUAL_STATE_QUERY_FAILED"
            output["recovery_error"] = str(exc)
    return output
