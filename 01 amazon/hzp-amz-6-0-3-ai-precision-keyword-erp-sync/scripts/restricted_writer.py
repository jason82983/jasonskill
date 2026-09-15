"""Fail-closed, business-action-only PickPwK writer for Stage 6-0-3.

This module is never invoked against production during skill development.  It
accepts no SQL text; SQL statements are fixed to the validated JSON target.
"""
from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

CONFIG_PATH = Path(r"E:\【所有产品目录专用】\00_公共资料\03_系统配置\erp-pickpwk-write-access.json")
INPUT_DIR = "6-0-1_精准关键词识别"
INPUT_NAME = "6-0-1_{product_code}_AI精准词.csv"
LOG_DIR = Path("06_SKILL分析报告") / "6-0-3_AI精准词同步ERP" / "执行日志"
FINAL_COLUMNS = ("自动编号", "关键词", "搜索量", "中文名称", "精准理由", "精准度")
PRECISION_TAG = "|1精准|"

WRITE_BLOCKED = "WRITE_BLOCKED"
SUCCESS = "SUCCESS"
NO_CHANGE = "NO_CHANGE"
SKIPPED = "SKIPPED"
FAILED = "FAILED"
ERR_CAPABILITY = "[ERP_PICKPWK_WRITE_CAPABILITY_NOT_AVAILABLE]"
ERR_ID_NOT_FOUND = "[ERP_PICKPWK_ID_NOT_FOUND]"
ERR_ID_NOT_UNIQUE = "[ERP_PICKPWK_ID_NOT_UNIQUE]"
ERR_IDENTITY = "[ERP_KEYWORD_IDENTITY_MISMATCH]"
ERR_CSV_CONFLICT = "[CSV_RECORD_IDENTITY_CONFLICT]"
ERR_RECORD_IDENTITY_CONFLICT = "[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]"
ERR_READBACK = "[ERP_PRECISION_TAG_READBACK_FAILED]"


class WriteBlocked(RuntimeError):
    pass


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def load_config(path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    try:
        config = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WriteBlocked(ERR_CAPABILITY) from exc
    target = config.get("target") or {}
    credentials = config.get("credentials") or {}
    allowed = config.get("allowed_update_columns") or []
    if config.get("enabled") is not True or config.get("capability_id") != "erp_pickpwk_precision_tag_writer":
        raise WriteBlocked(ERR_CAPABILITY)
    if (target.get("table_schema"), target.get("table_name"), target.get("primary_key"), target.get("tags_column")) != ("dbo", "PickPwK", "Id", "Tags"):
        raise WriteBlocked(ERR_CAPABILITY)
    source = config.get("source_identity") or {}
    if (source.get("source_view"), source.get("source_record_id_field"), source.get("target_record_id_field")) != ("PickPwKView", "Id", "Id"):
        raise WriteBlocked(ERR_CAPABILITY)
    if allowed != ["Tags"] or config.get("precision_tag") != PRECISION_TAG:
        raise WriteBlocked(ERR_CAPABILITY)
    required_policy = (config.get("write_policy") or {})
    if (required_policy.get("mode") != "add_only" or required_policy.get("require_preflight") is not True
            or required_policy.get("require_transaction") is not True
            or required_policy.get("require_read_back") is not True):
        raise WriteBlocked(ERR_CAPABILITY)
    for key in ("server_env", "database_env", "username_env", "password_env"):
        if not str(credentials.get(key) or "").strip():
            raise WriteBlocked(ERR_CAPABILITY)
    return config


def resolve_credentials(config: Mapping[str, Any]) -> dict[str, str]:
    refs = config["credentials"]
    values: dict[str, str] = {}
    for key in ("server_env", "database_env", "username_env", "password_env"):
        env_name = str(refs[key])
        value = os.environ.get(env_name)
        if not value:
            raise WriteBlocked(ERR_CAPABILITY)
        values[key[:-4] if key.endswith("_env") else key] = value
    return values


def input_path(product_root: str | Path, product_code: str) -> Path:
    return Path(product_root) / "06_SKILL分析报告" / INPUT_DIR / INPUT_NAME.format(product_code=product_code)


def read_input(path: str | Path) -> list[dict[str, str]]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError("[6-0-1_AI_PRECISION_KEYWORD_INPUT_MISSING]")
    with target.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FINAL_COLUMNS:
            raise ValueError("[6-0-1_AI_PRECISION_KEYWORD_INPUT_INVALID]")
        return list(reader)


def validate_csv_rows(rows: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Deduplicate IDs and classify CSV-level conflicts before any DB call."""
    by_id: dict[str, dict[str, Any]] = {}
    stats = {"TOTAL": 0, "INVALID_ROW": 0, "CSV_RECORD_IDENTITY_CONFLICT": 0, "ERP_KEYWORD_RECORD_IDENTITY_CONFLICT": 0}
    conflict_ids: set[str] = set()
    for raw in rows:
        stats["TOTAL"] += 1
        record_id = str(raw.get("自动编号") or "").strip()
        keyword = str(raw.get("关键词") or "").strip()
        if not record_id or not re.fullmatch(r"[0-9]+", record_id) or not keyword:
            stats["INVALID_ROW"] += 1
            continue
        current = by_id.get(record_id)
        item = {"record_id": record_id, "keyword": keyword, "source": dict(raw)}
        if current is None:
            by_id[record_id] = item
        elif _norm(current["keyword"]) != _norm(keyword):
            current["status"] = ERR_RECORD_IDENTITY_CONFLICT
            conflict_ids.add(record_id)
            stats["CSV_RECORD_IDENTITY_CONFLICT"] += 1
            stats["ERP_KEYWORD_RECORD_IDENTITY_CONFLICT"] += 1
        # Same ID + same Keyword is intentionally processed once.
    return [item for record_id, item in by_id.items() if record_id not in conflict_ids], stats


def append_precision_tag(tags: Any, token: str = PRECISION_TAG) -> str:
    value = "" if tags is None else str(tags)
    if token.strip("|") in _tag_tokens(value):
        return value
    if not value:
        return token
    if value.endswith("|"):
        return value + token.lstrip("|")
    return value + token


def _tag_tokens(tags: Any) -> set[str]:
    return {part for part in str(tags or "").split("|") if part}


def _tag_count(tags: Any, token: str = PRECISION_TAG) -> int:
    return str(tags or "").split("|").count(token.strip("|"))


def preflight_rows(rows: Iterable[Mapping[str, Any]], records: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    by_id: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        by_id.setdefault(str(record.get("Id") or ""), []).append(record)
    prepared: list[dict[str, Any]] = []
    stats = {"TOTAL": 0, "READY_TO_ADD": 0, "ALREADY_PRECISION": 0, "ID_NOT_FOUND": 0, "ID_NOT_UNIQUE": 0, "IDENTITY_MISMATCH": 0, "INVALID_ROW": 0, "WRITE_CAPABILITY_ERROR": 0}
    for row in rows:
        stats["TOTAL"] += 1
        record_id = str(row.get("record_id") or "")
        if row.get("status") in {ERR_CSV_CONFLICT, ERR_RECORD_IDENTITY_CONFLICT}:
            stats["IDENTITY_MISMATCH"] += 1
            continue
        matches = by_id.get(record_id, [])
        if not matches:
            stats["ID_NOT_FOUND"] += 1
            continue
        if len(matches) != 1:
            stats["ID_NOT_UNIQUE"] += 1
            continue
        record = matches[0]
        if _norm(record.get("Keyword")) != _norm(row.get("keyword")):
            stats["IDENTITY_MISMATCH"] += 1
            continue
        before = record.get("Tags")
        if _tag_count(before) > 0:
            stats["ALREADY_PRECISION"] += 1
            status = NO_CHANGE
        else:
            stats["READY_TO_ADD"] += 1
            status = "READY_TO_ADD"
        prepared.append({"record_id": record_id, "keyword": row["keyword"], "record": dict(record), "before_tags": before, "status": status})
    return prepared, stats


def _fixed_select(config: Mapping[str, Any]) -> str:
    target = config["target"]
    return f"SELECT [{target['primary_key']}],[Keyword],[{target['tags_column']}] FROM [{target['table_schema']}].[{target['table_name']}] WHERE [{target['primary_key']}] = ?"


def _fixed_update(config: Mapping[str, Any]) -> str:
    target = config["target"]
    schema, table, key, tags = (target["table_schema"], target["table_name"], target["primary_key"], target["tags_column"])
    return f"UPDATE [{schema}].[{table}] SET [{tags}] = ? WHERE [{key}] = ? AND (([{tags}] = ?) OR ([{tags}] IS NULL AND ? IS NULL))"


class RestrictedWriter:
    def __init__(self, config: Mapping[str, Any], connection: Any):
        self.config = config
        self.connection = connection

    def select_record(self, record_id: str) -> list[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(_fixed_select(self.config), record_id)
        rows = [dict(zip(("Id", "Keyword", "Tags"), values)) for values in cursor.fetchall()]
        cursor.close()
        return rows

    # Public provider actions are intentionally narrow.  These aliases keep
    # the business contract readable without exposing a generic SQL method.
    def get_record(self, record_id: str) -> list[dict[str, Any]]:
        return self.select_record(record_id)

    def update_tags_only(self, record_id: str, before_tags: Any, after_tags: str) -> int:
        cursor = self.connection.cursor()
        cursor.execute(_fixed_update(self.config), after_tags, record_id, before_tags, before_tags)
        count = int(getattr(cursor, "rowcount", 0))
        cursor.close()
        return count

    def verify_record(self, record_id: str, expected_keyword: str, before_tags: Any) -> tuple[bool, dict[str, Any] | None]:
        rows = self.select_record(record_id)
        if len(rows) != 1:
            return False, None
        row = rows[0]
        old_tokens = _tag_tokens(before_tags)
        new_tokens = _tag_tokens(row.get("Tags"))
        ok = (_norm(row.get("Keyword")) == _norm(expected_keyword) and _tag_count(row.get("Tags")) == 1 and old_tokens.issubset(new_tokens))
        return ok, row

    def sync_record(self, record_id: str, expected_keyword: str) -> dict[str, Any]:
        """Perform one guarded ADD ONLY operation using the fixed contract.

        The caller supplies no SQL and no tag value.  The latest row is read
        immediately before the conditional update; rollback is attempted on
        every failed verification.  A provider can expose commit/rollback or
        autocommit in the usual DB-API form, but these are not required for
        read-only preflight tests.
        """
        result: dict[str, Any] = {"record_id": str(record_id), "keyword": expected_keyword, "action": "ADD_PRECISION_TAG"}
        try:
            if hasattr(self.connection, "autocommit"):
                self.connection.autocommit = False
            latest = self.select_record(str(record_id))
            if len(latest) == 0:
                result.update(result=FAILED, error_code=ERR_ID_NOT_FOUND)
                return result
            if len(latest) != 1:
                result.update(result=FAILED, error_code=ERR_ID_NOT_UNIQUE)
                return result
            row = latest[0]
            if _norm(row.get("Keyword")) != _norm(expected_keyword):
                result.update(result=FAILED, error_code=ERR_IDENTITY)
                return result
            before = row.get("Tags")
            if _tag_count(before) > 0:
                result.update(result=NO_CHANGE, before_tags=before, after_tags=before)
                return result
            after = append_precision_tag(before)
            # Conditional update prevents overwriting a tag added after the
            # read.  A rowcount other than one is a concurrency failure.
            if self.update_tags_only(str(record_id), before, after) != 1:
                if hasattr(self.connection, "rollback"):
                    self.connection.rollback()
                result.update(result=FAILED, error_code="[ERP_PICKPWK_CONCURRENT_CHANGE]")
                return result
            verified, verified_row = self.verify_record(str(record_id), expected_keyword, before)
            if not verified:
                if hasattr(self.connection, "rollback"):
                    self.connection.rollback()
                result.update(result=FAILED, error_code=ERR_READBACK)
                return result
            if hasattr(self.connection, "commit"):
                self.connection.commit()
            # Verify once after commit as well; this is intentionally a
            # second read and never trusts the pre-commit snapshot.
            verified_after, _ = self.verify_record(str(record_id), expected_keyword, before)
            if not verified_after:
                result.update(result=FAILED, error_code=ERR_READBACK)
                return result
            result.update(result=SUCCESS, before_tags=before, after_tags=(verified_row or {}).get("Tags"))
            return result
        except Exception:
            if hasattr(self.connection, "rollback"):
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            result.update(result=FAILED, error_code=ERR_CAPABILITY)
            return result

    def add_precision_tag(self, record_id: str, expected_keyword: str) -> dict[str, Any]:
        return self.sync_record(record_id, expected_keyword)


def log_result(product_root: str | Path, product_code: str, run_id: str, results: Iterable[Mapping[str, Any]]) -> Path:
    target_dir = Path(product_root) / LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{run_id}.md"
    lines = [f"# 6-0-3 AI精准词同步ERP｜{product_code}", "", f"Run_ID：{run_id}", f"Timestamp：{datetime.now(timezone.utc).replace(microsecond=0).isoformat()}", ""]
    for result in results:
        lines.extend([f"- Record ID：{result.get('record_id')}", f"- Keyword：{result.get('keyword')}", f"- Action：{result.get('action')}", f"- Result：{result.get('result')}", f"- Error Code：{result.get('error_code') or ''}", ""])
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
