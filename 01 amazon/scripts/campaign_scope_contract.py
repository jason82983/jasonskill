"""Runtime CampaignTag scope helpers for Stage 6 advertising operations."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping


class CampaignScopeError(ValueError):
    """Stable runtime scope errors."""


_TOKEN = re.compile(r"^[A-Za-z0-9]+$")


def build_campaign_scope(product_code: str, campaign_tag: str) -> dict[str, str]:
    product = str(product_code or "").strip()
    tag = str(campaign_tag or "").strip()
    if not tag:
        raise CampaignScopeError("CAMPAIGN_TAG_MISSING")
    if not _TOKEN.fullmatch(tag):
        raise CampaignScopeError("CAMPAIGN_TAG_INVALID")
    if not _TOKEN.fullmatch(product):
        raise CampaignScopeError("CAMPAIGN_PREFIX_INVALID")
    return {"ProductCode": product, "CampaignTag": tag, "CampaignPrefix": f"{product}.{tag}."}


def load_product_campaign_scope(product_root: str | Path) -> dict[str, str]:
    """Read the authoritative ProductCode/Tag/Prefix block from 01_产品档案.md."""
    path = Path(product_root) / "01_产品档案.md"
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        raise CampaignScopeError("CAMPAIGN_SCOPE_NOT_CONFIGURED") from None
    values: dict[str, str] = {}
    for key in ("ProductCode", "CampaignTag", "CampaignPrefix"):
        match = re.search(rf"(?mi)^\s*{re.escape(key)}\s*=\s*([^\r\n#]+?)\s*$", text)
        if match:
            values[key] = match.group(1).strip()
    if set(values) != {"ProductCode", "CampaignTag", "CampaignPrefix"}:
        raise CampaignScopeError("CAMPAIGN_SCOPE_NOT_CONFIGURED")
    scope = build_campaign_scope(values["ProductCode"], values["CampaignTag"])
    if values["CampaignPrefix"] != scope["CampaignPrefix"]:
        raise CampaignScopeError("CAMPAIGN_PREFIX_INVALID")
    return scope


def scope_matches_metadata(metadata: Mapping[str, Any], scope: Mapping[str, str]) -> bool:
    return all(metadata.get(field) == scope[field] for field in ("ProductCode", "CampaignTag", "CampaignPrefix"))


def campaign_is_in_scope(name: Any, prefix: str) -> bool:
    if not prefix or not prefix.endswith("."):
        raise CampaignScopeError("CAMPAIGN_PREFIX_INVALID")
    return isinstance(name, str) and name.startswith(prefix)


def select_campaigns(campaigns: Iterable[Mapping[str, Any]], scope: Mapping[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [dict(row) for row in campaigns]
    matched = [row for row in rows if campaign_is_in_scope(row.get("CampaignName") or row.get("name"), scope["CampaignPrefix"])]
    ids = sorted({str(row.get("CampaignId") or row.get("amazon_id") or "").strip() for row in matched} - {""})
    return matched, {
        **dict(scope),
        "AccountCampaignCount": len(rows),
        "PrefixMatchedCampaignCount": len(ids),
        "ExcludedCampaignCount": len(rows) - len(matched),
        "MatchedCampaignIds": ids,
    }


def require_same_scope(metadata: Mapping[str, Any], scope: Mapping[str, str]) -> None:
    if not scope_matches_metadata(metadata, scope):
        raise CampaignScopeError("RUNTIME_SCOPE_MISMATCH")
