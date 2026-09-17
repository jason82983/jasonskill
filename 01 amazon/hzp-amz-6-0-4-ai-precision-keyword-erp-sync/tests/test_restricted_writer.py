from __future__ import annotations

import csv
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("restricted_writer", ROOT / "scripts" / "restricted_writer.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def config(enabled=True):
    return {
        "capability_id": "erp_pickpwk_precision_tag_writer", "enabled": enabled,
        "credentials": {"server_env": "S", "database_env": "D", "username_env": "U", "password_env": "P"},
        "target": {"table_schema": "dbo", "table_name": "PickPwK", "primary_key": "Id", "tags_column": "Tags"},
        "source_identity": {"source_view": "PickPwKView", "source_record_id_field": "Id", "target_record_id_field": "Id"},
        "allowed_update_columns": ["Tags"], "precision_tag": "|1精准|",
        "write_policy": {"mode": "add_only", "require_preflight": True, "require_transaction": True, "require_read_back": True},
    }


def test_config_and_disabled_guard(tmp_path):
    path = tmp_path / "writer.json"
    path.write_text(json.dumps(config()), encoding="utf-8")
    assert module.load_config(path)["target"]["primary_key"] == "Id"
    path.write_text(json.dumps(config(False)), encoding="utf-8")
    try:
        module.load_config(path)
    except module.WriteBlocked as exc:
        assert str(exc) == module.ERR_CAPABILITY
    else:
        raise AssertionError("disabled writer must block")


def test_config_requires_tags_only_transaction_and_readback(tmp_path):
    path = tmp_path / "writer.json"
    invalid = config()
    invalid["allowed_update_columns"] = ["Tags", "Keyword"]
    path.write_text(json.dumps(invalid), encoding="utf-8")
    try:
        module.load_config(path)
    except module.WriteBlocked:
        pass
    else:
        raise AssertionError("non-Tags update must block")
    invalid = config()
    invalid["write_policy"]["require_transaction"] = False
    path.write_text(json.dumps(invalid), encoding="utf-8")
    try:
        module.load_config(path)
    except module.WriteBlocked:
        pass
    else:
        raise AssertionError("transaction requirement must block")


def test_missing_config_and_missing_writer_credential_fail_closed(tmp_path):
    try:
        module.load_config(tmp_path / "does-not-exist.json")
    except module.WriteBlocked as exc:
        assert str(exc) == module.ERR_CAPABILITY
    else:
        raise AssertionError("missing JSON must block")
    saved = {name: os.environ.pop(name, None) for name in ("S", "D", "U", "P")}
    try:
        try:
            module.resolve_credentials(config())
        except module.WriteBlocked as exc:
            assert str(exc) == module.ERR_CAPABILITY
        else:
            raise AssertionError("missing writer credential must block")
    finally:
        for name, value in saved.items():
            if value is not None:
                os.environ[name] = value


def test_csv_requires_six_columns_and_deduplicates_ids(tmp_path):
    path = tmp_path / "6-0-2_B2_AI精准词.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=module.FINAL_COLUMNS)
        writer.writeheader()
        writer.writerow({"自动编号": "1", "关键词": "sister gifts", "搜索量": "1", "中文名称": "", "精准理由": "", "精准度": "90"})
        writer.writerow({"自动编号": "1", "关键词": "sister gifts", "搜索量": "1", "中文名称": "", "精准理由": "", "精准度": "90"})
        writer.writerow({"自动编号": "1", "关键词": "different", "搜索量": "1", "中文名称": "", "精准理由": "", "精准度": "90"})
    rows = module.read_input(path)
    unique, stats = module.validate_csv_rows(rows)
    assert len(unique) == 0
    assert stats["CSV_RECORD_IDENTITY_CONFLICT"] == 1
    assert stats["ERP_KEYWORD_RECORD_IDENTITY_CONFLICT"] == 1


def test_tag_append_is_add_only_and_idempotent():
    assert module.append_precision_tag(None) == "|1精准|"
    assert module.append_precision_tag("") == "|1精准|"
    assert module.append_precision_tag("|新品|礼品|") == "|新品|礼品|1精准|"
    assert module.append_precision_tag("|新品|1精准|") == "|新品|1精准|"
    assert module.append_precision_tag("|精准提示|") == "|精准提示|1精准|"
    assert module.append_precision_tag("prefix|1精准|suffix") == "prefix|1精准|suffix"


def test_preflight_statuses_and_identity_checks():
    rows = [{"record_id": "1", "keyword": "sister gifts"}, {"record_id": "2", "keyword": "missing"}, {"record_id": "3", "keyword": "wrong"}]
    records = [{"Id": 1, "Keyword": "sister gifts", "Tags": "|gift|"}, {"Id": 3, "Keyword": "other", "Tags": ""}]
    prepared, stats = module.preflight_rows(rows, records)
    assert prepared[0]["status"] == "READY_TO_ADD"
    assert stats["ID_NOT_FOUND"] == 1
    assert stats["IDENTITY_MISMATCH"] == 1


def test_log_contains_no_secret(tmp_path):
    path = module.log_result(tmp_path, "B2", "run-1", [{"record_id": "1", "keyword": "sister gifts", "action": "ADD_PRECISION_TAG", "result": "SUCCESS"}])
    text = path.read_text(encoding="utf-8")
    assert "run-1" in text and "sister gifts" in text
    assert "password" not in text.lower() and "connection string" not in text.lower()


class _FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []
        self.rowcount = 0

    def execute(self, sql, *params):
        self.connection.sql.append(sql)
        if sql.startswith("SELECT"):
            record_id = str(params[0])
            self.rows = [
                (row["Id"], row["Keyword"], row.get("Tags"))
                for row in self.connection.records
                if str(row["Id"]) == record_id
            ]
        elif sql.startswith("UPDATE"):
            after, record_id, before, before_null = params
            self.rowcount = 0
            for row in self.connection.records:
                if str(row["Id"]) == str(record_id) and row.get("Tags") == before == before_null:
                    row["Tags"] = after
                    self.rowcount += 1
        else:
            raise AssertionError("arbitrary SQL must not be accepted")

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class _FakeConnection:
    def __init__(self, records):
        self.records = records
        self.sql = []
        self.commits = 0
        self.rollbacks = 0
        self.autocommit = True

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_sync_record_transaction_readback_and_add_only():
    connection = _FakeConnection([{"Id": 10, "Keyword": "sister gifts", "Tags": "|gift|"}])
    writer = module.RestrictedWriter(config(), connection)
    result = writer.sync_record("10", "sister gifts")
    assert result["result"] == module.SUCCESS
    assert connection.records[0]["Tags"] == "|gift|1精准|"
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert all(sql.startswith(("SELECT", "UPDATE")) for sql in connection.sql)


def test_sync_record_is_idempotent_for_existing_tag():
    connection = _FakeConnection([{"Id": 11, "Keyword": "sister gifts", "Tags": "|gift|1精准|"}])
    result = module.RestrictedWriter(config(), connection).sync_record("11", "sister gifts")
    assert result["result"] == module.NO_CHANGE
    assert connection.commits == 0


def test_benchmark_record_id_is_allowed_without_product_ownership_check():
    connection = _FakeConnection([{"Id": 201, "Keyword": "benchmark term", "Tags": "", "ProId": 99999}])
    result = module.RestrictedWriter(config(), connection).sync_record("201", "benchmark term")
    assert result["result"] == module.SUCCESS
    assert connection.records[0]["Tags"] == "|1精准|"


def test_sync_record_blocks_missing_and_identity_mismatch():
    connection = _FakeConnection([{"Id": 12, "Keyword": "other", "Tags": None}])
    writer = module.RestrictedWriter(config(), connection)
    assert writer.sync_record("404", "sister gifts")["error_code"] == module.ERR_ID_NOT_FOUND
    assert writer.sync_record("12", "sister gifts")["error_code"] == module.ERR_IDENTITY


def test_csv_invalid_id_is_rejected_without_database_identity_guessing():
    rows, stats = module.validate_csv_rows([{"自动编号": "row-1", "关键词": "sister gifts"}, {"自动编号": "", "关键词": ""}])
    assert rows == []
    assert stats["INVALID_ROW"] == 2


def test_preflight_rejects_duplicate_database_id():
    rows = [{"record_id": "13", "keyword": "sister gifts"}]
    records = [{"Id": 13, "Keyword": "sister gifts", "Tags": ""}, {"Id": 13, "Keyword": "sister gifts", "Tags": ""}]
    _, stats = module.preflight_rows(rows, records)
    assert stats["ID_NOT_UNIQUE"] == 1


def test_preflight_is_read_only_and_preserves_all_existing_tags():
    rows = [{"record_id": "14", "keyword": "sister gifts"}]
    records = [{"Id": 14, "Keyword": "sister gifts", "Tags": "|gift|seasonal|"}]
    snapshot = dict(records[0])
    prepared, stats = module.preflight_rows(rows, records)
    assert stats["READY_TO_ADD"] == 1
    assert prepared[0]["before_tags"] == "|gift|seasonal|"
    assert records[0] == snapshot


def test_sync_record_blocks_concurrent_tag_change_without_overwrite():
    connection = _FakeConnection([{"Id": 15, "Keyword": "sister gifts", "Tags": "|gift|"}])
    original_update = _FakeCursor.execute

    def changed_before_update(self, sql, *params):
        if sql.startswith("UPDATE"):
            self.connection.records[0]["Tags"] = "|gift|manual|"
        return original_update(self, sql, *params)

    _FakeCursor.execute = changed_before_update
    try:
        result = module.RestrictedWriter(config(), connection).sync_record("15", "sister gifts")
    finally:
        _FakeCursor.execute = original_update
    assert result["result"] == module.FAILED
    assert result["error_code"] == "[ERP_PICKPWK_CONCURRENT_CHANGE]"
    assert connection.records[0]["Tags"] == "|gift|manual|"


def test_sync_record_readback_failure_is_not_success():
    class ReadbackFailureWriter(module.RestrictedWriter):
        def verify_record(self, record_id, expected_keyword, before_tags):
            return False, None

    connection = _FakeConnection([{"Id": 16, "Keyword": "sister gifts", "Tags": "|gift|"}])
    result = ReadbackFailureWriter(config(), connection).sync_record("16", "sister gifts")
    assert result["result"] == module.FAILED
    assert result["error_code"] == module.ERR_READBACK
    assert connection.rollbacks == 1


def test_fixed_update_cannot_touch_non_tags_columns_and_preflight_precedes_update():
    sql = module._fixed_update(config())
    assert "SET [Tags]" in sql
    assert "Keyword" not in sql and "ProId" not in sql and "IsExact" not in sql
    connection = _FakeConnection([{"Id": 17, "Keyword": "sister gifts", "Tags": "|gift|"}])
    result = module.RestrictedWriter(config(), connection).sync_record("17", "sister gifts")
    assert result["result"] == module.SUCCESS
    assert connection.sql[0].startswith("SELECT")
    assert connection.sql[1].startswith("UPDATE")
    assert connection.sql[2].startswith("SELECT")


def test_public_contract_keeps_6_0_2_out_and_isexact_untouched():
    script = (ROOT / "scripts" / "restricted_writer.py").read_text(encoding="utf-8")
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "6-0-3" not in script
    assert "execute_sql" not in script
    assert "arbitrary_query" not in script
    assert "IsExact" not in script
    assert "6-0-3" in skill and "精准泛词" in skill


if __name__ == "__main__":
    test_tag_append_is_add_only_and_idempotent()
    test_preflight_statuses_and_identity_checks()
    print("6-0-4 restricted writer tests: PASS")
