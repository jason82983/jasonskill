"""Read-only ERP keyword adapter for Stage 6.

The adapter is deliberately small and provider-boundary only.  It resolves the
current ERP product number and explicitly labelled benchmark ERP numbers from
``01_产品档案.md``, reads the field-definition document, and queries
``Amazon.dbo.PickPwKView`` with parameterized ``ProId`` values.
Business metrics whose semantics are not documented are returned as raw fields
and marked ``SEMANTICS_UNCERTAIN``; they are never silently mapped to Amazon
orders, clicks, sales, ranking, or conversion metrics.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping


PROVIDER = "ERP_SQL_SERVER"
SOURCE_VIEW = "PickPwKView"
PRECISION_TAG = "|1精准|"
MISSING_PROID = "ERP_PROID_MISSING"
CONFLICT_PROID = "ERP_PROID_CONFLICT"
PROVIDER_UNAVAILABLE = "ERP_KEYWORD_PROVIDER_UNAVAILABLE"
DATA_NOT_FOUND = "ERP_KEYWORD_DATA_NOT_FOUND"
DATA_READY = "ERP_KEYWORD_DATA_READY"
BENCHMARK_PROID_NOT_AVAILABLE = "BENCHMARK_ERP_PROID_NOT_AVAILABLE"
KEYWORD_RECORD_ID_UNCONFIRMED = "[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]"

DEFAULT_CONFIG_NAME = "sql-server-erp-connection.json"
DEFAULT_MAPPING_NAME = "erp-amazon-data-mapping.json"
DEFAULT_SCHEMA_NAME = "erp-amazon-pickpwkview-schema.md"

# Keep the query explicit so a view change is visible in review.  The adapter
# does not interpret these fields unless the field-definition document does.
QUERY_COLUMNS = (
    "Id", "KwId", "ProId", "RankOra", "IsRelate", "RankAdv", "RankRec",
    "IsMain", "IsExact", "IsLongTail", "IsGoodCvt", "UpdateTime",
    "Keyword", "KeywordCn", "SearchVolume30", "SearchVolumeDaily",
    "SearchGrowthRate30", "PriceSuggest", "PriceLow", "PriceHigh",
    "AsinQuantity", "AsinQuantityAdv", "Cpr8", "CprDaily",
    "TitleIncludeKwProSum", "IsTj", "IsAdv", "IsOra", "IQScore",
    "IsSold", "R3HitPercentage", "R3SoldPercentage", "RecordDate",
    "SearchSoldSum", "SearchCvtRate", "SearchHitSum", "SearchHitRate",
    "abarank", "IsOut", "Tags", "AdvSoldSum", "AdvSoldSum30",
    "AdvSoldStatDate", "HitTimes30", "ShowTimes30", "HitRate30",
    "CvRate30", "AmzSiteNo",
)

# These are the only structural meanings explicitly called out in the current
# 03_系统配置 schema document.  All other columns remain uncertain.
DOCUMENTED_FIELDS = {
    "ProId": "产品关联键（原文档定义）",
    "Keyword": "关键词原文（原文档定义）",
    "KeywordCn": "关键词中文（原文档定义）",
    # IsExact is retained as a raw documented field, but is explicitly not
    # used for ERP precision-keyword classification.
    "IsExact": "暂不用；不得作为精准关键词判定（原文档定义）",
    "IsMain": "是否主关键词标记（原文档定义）",
    "IsLongTail": "是否长尾关键词标记（原文档定义）",
    "IsGoodCvt": "是否高转化标记（原文档定义）",
    "IsSold": "是否产生销售标记（原文档定义）",
    "SearchVolume30": "30天搜索量字段（原文档定义）",
    "AsinQuantity": "竞争产品数（阶段 6-0-1 正式映射；PickPwKView 原字段）",
    "SearchVolumeDaily": "日搜索量字段（原文档定义）",
    "SearchGrowthRate30": "30天搜索增长率（原文档定义）",
    "IQScore": "关键词IQ评分（原文档定义）",
    "SearchSoldSum": "搜索相关销售汇总（原文档定义）",
    "SearchCvtRate": "搜索转化率（原文档定义）",
    "SearchHitSum": "搜索命中/点击汇总（原文档定义）",
    "SearchHitRate": "搜索命中/点击率（原文档定义）",
    "UpdateTime": "记录更新时间（原文档定义）",
    "RecordDate": "数据记录日期（原文档定义）",
    "Tags": "业务标签；完整标签 |1精准| 表示 ERP 精准词（原文档定义）",
}

_PROID_PATTERNS = (
    re.compile(r"^\s*(?:[-*]\s*)?(ERP编号|ERP\s*产品编号|ERP_ProId|ERP\s+ProId|ERP产品编号)\s*[:：]\s*(\S+)\s*$", re.I),
)
_BENCHMARK_PROID_LINE = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<label>[^:：]*(?:对标|benchmark)[^:：]*(?:ERP|erp)[^:：]*(?:编号|id|proid))\s*[:：]\s*(?P<value>.+?)\s*$",
    re.I,
)


class ERPKeywordProviderUnavailable(RuntimeError):
    """Raised when the configured read-only provider cannot be opened."""


def read_erp_pro_id(product_archive: str | Path) -> dict[str, Any]:
    """Resolve the ERP product number without substituting Product_Code."""
    path = Path(product_archive)
    text = path.read_text(encoding="utf-8-sig")
    values: list[tuple[str, str]] = []
    for line in text.splitlines():
        for pattern in _PROID_PATTERNS:
            match = pattern.match(line)
            if match:
                values.append((match.group(1), match.group(2).strip()))
                break
    distinct = {value for _, value in values}
    if not values:
        return {"status": MISSING_PROID, "erp_pro_id": None, "field_name": None, "conflicts": []}
    if len(distinct) > 1:
        return {
            "status": CONFLICT_PROID,
            "erp_pro_id": None,
            "field_name": values[0][0],
            "conflicts": [value for _, value in values],
        }
    return {"status": "ERP_PROID_RESOLVED", "erp_pro_id": values[0][1], "field_name": values[0][0], "conflicts": []}


def read_benchmark_erp_pro_ids(product_archive: str | Path) -> dict[str, Any]:
    """Read only explicitly labelled benchmark ERP IDs from the product archive.

    The archive field label is evidence: no ID is inferred from ASIN, product
    name, role text, or the current product's ERP ID. Multiple IDs may be
    separated by commas/semicolons.
    """
    path = Path(product_archive)
    text = path.read_text(encoding="utf-8-sig")
    ids: list[str] = []
    field_names: list[str] = []
    for line in text.splitlines():
        match = _BENCHMARK_PROID_LINE.match(line)
        if not match:
            continue
        field_names.append(match.group("label").strip())
        for value in re.split(r"[,，;；]", match.group("value")):
            token = value.strip().strip("`[]()")
            if token and re.fullmatch(r"[A-Za-z0-9_-]+", token):
                ids.append(token)
    unique_ids = list(dict.fromkeys(ids))
    if not unique_ids:
        return {
            "status": BENCHMARK_PROID_NOT_AVAILABLE,
            "benchmark_erp_pro_ids": [],
            "field_names": field_names,
        }
    return {
        "status": "BENCHMARK_ERP_PROID_RESOLVED",
        "benchmark_erp_pro_ids": unique_ids,
        "field_names": field_names,
    }


def load_field_definitions(config_dir: str | Path) -> dict[str, Any]:
    """Read the maintained schema document; do not infer meanings from names."""
    path = Path(config_dir) / DEFAULT_SCHEMA_NAME
    text = path.read_text(encoding="utf-8-sig")
    fields: dict[str, dict[str, str]] = {}
    for column in QUERY_COLUMNS:
        if column in DOCUMENTED_FIELDS and re.search(rf"`{re.escape(column)}`", text):
            fields[column] = {"status": "DOCUMENTED", "meaning": DOCUMENTED_FIELDS[column]}
        else:
            # A missing or undocumented column is intentionally explicit: raw
            # values may be retained, but they cannot enter a business metric.
            fields[column] = {"status": "SEMANTICS_UNCERTAIN", "meaning": None}
    return {"source": str(path), "fields": fields}


def _resolve_password(config: Mapping[str, Any]) -> str | None:
    """Resolve a secret from an existing secret manager or environment only."""
    ref = str(config.get("passwordRef") or "").strip()
    if not ref:
        return None
    value = os.environ.get(ref)
    if value:
        return value
    # Optional keyring support keeps the adapter independent of a credential
    # implementation while allowing an existing OS keyring to be reused.
    try:
        import keyring  # type: ignore
        value = keyring.get_password(ref, str(config.get("username") or ""))
        return value or None
    except Exception:
        return None


def _connection_string(config: Mapping[str, Any], password: str) -> str:
    server = str(config.get("server") or "").strip()
    port = config.get("port")
    if port and "," not in server:
        server = f"{server},{port}"
    encrypt = "yes" if config.get("encrypt", True) else "no"
    trust = "yes" if config.get("trustServerCertificate", False) else "no"
    driver = str(config.get("driver") or "ODBC Driver 18 for SQL Server")
    return ";".join((
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={config.get('database')}",
        f"UID={config.get('username')}",
        f"PWD={password}",
        f"Encrypt={encrypt}",
        f"TrustServerCertificate={trust}",
        "ApplicationIntent=ReadOnly",
    ))


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ERPKeywordAdapter:
    """Minimal read-only adapter shared by Stage 6 skills."""

    def __init__(
        self,
        config_dir: str | Path,
        *,
        connector: Callable[[Mapping[str, Any], str], Any] | None = None,
        password_resolver: Callable[[Mapping[str, Any]], str | None] | None = None,
        clock: Callable[[], str] = _now_iso,
    ) -> None:
        self.config_dir = Path(config_dir)
        self.connector = connector
        self.password_resolver = password_resolver or _resolve_password
        self.clock = clock

    def _load_config(self) -> tuple[dict[str, Any], dict[str, Any]]:
        connection_path = self.config_dir / DEFAULT_CONFIG_NAME
        mapping_path = self.config_dir / DEFAULT_MAPPING_NAME
        connection = json.loads(connection_path.read_text(encoding="utf-8-sig"))
        mapping = json.loads(mapping_path.read_text(encoding="utf-8-sig"))
        product_keywords = mapping.get("mappings", {}).get("productKeywords", {})
        if product_keywords.get("objectName") != SOURCE_VIEW or product_keywords.get("productCodeField") != "ProId":
            raise ERPKeywordProviderUnavailable("ERP mapping does not define PickPwKView.ProId")
        return connection, mapping

    def _connect(self, config: Mapping[str, Any], password: str) -> Any:
        if self.connector is not None:
            return self.connector(config, password)
        try:
            import pyodbc  # type: ignore
        except Exception as exc:
            raise ERPKeywordProviderUnavailable("pyodbc is unavailable") from exc
        if config.get("readOnly") is not True:
            raise ERPKeywordProviderUnavailable("ERP connection is not marked readOnly")
        return pyodbc.connect(_connection_string(config, password), timeout=int(config.get("connectTimeoutMs", 30000)) // 1000)

    @staticmethod
    def _query(*, precision_only: bool = False) -> str:
        columns = ", ".join(f"[{column}]" for column in QUERY_COLUMNS)
        predicate = "WHERE [ProId] = ?"
        if precision_only:
            predicate += " AND CHARINDEX(?, COALESCE([Tags], '')) > 0"
        return f"SELECT {columns} FROM [Amazon].[dbo].[{SOURCE_VIEW}] {predicate}"

    def fetch(
        self,
        product_archive: str | Path,
        *,
        product_code: str | None = None,
        precision_only: bool = False,
        pro_id_override: Any | None = None,
        evidence_role: str = "CURRENT_PRODUCT",
    ) -> dict[str, Any]:
        identity = (
            {"status": "ERP_PROID_RESOLVED", "erp_pro_id": str(pro_id_override), "field_name": "explicit_pro_id", "conflicts": []}
            if pro_id_override is not None and str(pro_id_override).strip()
            else read_erp_pro_id(product_archive)
        )
        field_defs = load_field_definitions(self.config_dir)
        base = {
            "provider": PROVIDER,
            "source_view": SOURCE_VIEW,
            "product_code": product_code,
            "field_definition_source": field_defs["source"],
            "erp_pro_id": identity.get("erp_pro_id"),
            "erp_pro_id_field": identity.get("field_name"),
            "retrieved_at": self.clock(),
            "rows": [],
            "field_definitions": field_defs["fields"],
            "metric_semantics": "仅使用配置文档明确字段；其余字段 SEMANTICS_UNCERTAIN",
            "source_grain": "PickPwKView row（视图行，未聚合）",
            "data_through": None,
            "freshness": "由 UpdateTime/RecordDate 的文档语义与实际值共同判断；未推断",
            "aggregation_method": "NONE",
            "evidence_role": evidence_role,
            # PickPwKView.Id remains a view-row identity whose mapping to a
            # writable PickPwK.Id is separately governed by the restricted
            # writer capability. The user confirmed KwId is stable/unique for
            # a keyword across ProIds, so expose it as entity identity only.
            "record_id_field": None,
            "record_id_status": KEYWORD_RECORD_ID_UNCONFIRMED,
            "keyword_entity_id_field": "KwId",
            "keyword_entity_id_status": "USER_CONFIRMED_STABLE_ACROSS_PROID",
        }
        if identity["status"] in {MISSING_PROID, CONFLICT_PROID}:
            base.update(status=identity["status"], conflicts=identity.get("conflicts", []))
            return base
        try:
            config, _mapping = self._load_config()
            password = self.password_resolver(config)
            if not password:
                raise ERPKeywordProviderUnavailable("passwordRef could not be resolved")
            connection = self._connect(config, password)
            cursor = connection.cursor()
            params: tuple[Any, ...] = (identity["erp_pro_id"],)
            if precision_only:
                params += (PRECISION_TAG,)
            cursor.execute(self._query(precision_only=precision_only), *params)
            description = [str(item[0]) for item in (cursor.description or ())]
            rows = []
            for values in cursor.fetchall():
                raw = dict(zip(description, values))
                # Keep the product boundary defensive even if a view or test
                # connector returns a row outside the parameterized scope.
                if str(raw.get("ProId")) != str(identity["erp_pro_id"]):
                    continue
                rows.append({
                    "product_code": product_code,
                    "keyword": raw.get("Keyword"),
                    "keyword_cn": raw.get("KeywordCn"),
                    "erp_pro_id": identity["erp_pro_id"],
                    "raw_fields": raw,
                    "keyword_entity_id": raw.get("KwId"),
                    "keyword_entity_id_status": "USER_CONFIRMED_STABLE_ACROSS_PROID",
                    "field_semantics": field_defs["fields"],
                    "record_id": None,
                    "record_id_status": KEYWORD_RECORD_ID_UNCONFIRMED,
                    "provenance": {
                        "Provider": PROVIDER,
                        "Source_View": SOURCE_VIEW,
                        "ERP_ProId": identity["erp_pro_id"],
                        "Field_Definition_Source": field_defs["source"],
                        "Retrieved_At": base["retrieved_at"],
                        "Source_Grain": "PickPwKView row（视图行，未聚合）",
                        "Metric_Semantics": base["metric_semantics"],
                        "Data_Through": None,
                        "Freshness": base["freshness"],
                        "Aggregation_Method": "NONE",
                        "Evidence_Role": evidence_role,
                    },
                })
            try:
                cursor.close()
            finally:
                connection.close()
            base.update(status=DATA_READY if rows else DATA_NOT_FOUND, rows=rows, conflicts=[])
            return base
        except ERPKeywordProviderUnavailable as exc:
            base.update(status=PROVIDER_UNAVAILABLE, conflicts=[str(exc)])
            return base
        except Exception as exc:
            base.update(status=PROVIDER_UNAVAILABLE, conflicts=[type(exc).__name__])
            return base


def fetch_current_product_keyword_evidence(product_archive: str | Path, config_dir: str | Path, **kwargs: Any) -> dict[str, Any]:
    """Convenience entry point used by Stage 6 without exposing SQL details."""
    return ERPKeywordAdapter(config_dir, **kwargs).fetch(product_archive)


def fetch_benchmark_keyword_evidence(
    product_archive: str | Path,
    config_dir: str | Path,
    *,
    product_code: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Fetch explicitly configured benchmark ProId rows as separate evidence.

    Each benchmark is queried with its own parameterized ``ProId``. Results
    never replace the current-product result and retain ``evidence_role`` so
    callers cannot mistake benchmark keywords for current-product keywords.
    """
    identity = read_benchmark_erp_pro_ids(product_archive)
    if identity["status"] == BENCHMARK_PROID_NOT_AVAILABLE:
        return {
            "status": BENCHMARK_PROID_NOT_AVAILABLE,
            "benchmark_erp_pro_ids": [],
            "results": [],
            "field_names": identity.get("field_names", []),
        }
    adapter = ERPKeywordAdapter(config_dir, **kwargs)
    results = [
        adapter.fetch(
            product_archive,
            product_code=product_code,
            pro_id_override=pro_id,
            evidence_role="BENCHMARK",
        )
        for pro_id in identity["benchmark_erp_pro_ids"]
    ]
    return {
        "status": "BENCHMARK_EVIDENCE_READY" if results else BENCHMARK_PROID_NOT_AVAILABLE,
        "benchmark_erp_pro_ids": identity["benchmark_erp_pro_ids"],
        "results": results,
        "field_names": identity.get("field_names", []),
    }
