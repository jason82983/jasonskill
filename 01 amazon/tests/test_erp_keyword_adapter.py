"""ERP Keyword Adapter tests; no SQL Server, network, or write operations."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("erp_keyword_adapter", ROOT / "scripts" / "erp_keyword_adapter.py")
adapter = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(adapter)


def test_product_archive_uses_explicit_erp_field_and_rejects_missing_or_conflict(tmp_path):
    archive = tmp_path / "01_产品档案.md"
    archive.write_text("产品编号：B2\nERP编号：49727\n", encoding="utf-8")
    result = adapter.read_erp_pro_id(archive)
    assert result["status"] == "ERP_PROID_RESOLVED"
    assert result["field_name"] == "ERP编号"
    assert result["erp_pro_id"] == "49727"

    missing = tmp_path / "missing.md"
    missing.write_text("产品编号：A6\n", encoding="utf-8")
    assert adapter.read_erp_pro_id(missing)["status"] == adapter.MISSING_PROID

    conflict = tmp_path / "conflict.md"
    conflict.write_text("ERP编号：1\nERP编号：2\n", encoding="utf-8")
    assert adapter.read_erp_pro_id(conflict)["status"] == adapter.CONFLICT_PROID


def test_benchmark_erp_ids_require_explicit_archive_field(tmp_path):
    archive = tmp_path / "01_产品档案.md"
    archive.write_text("产品编号：B2\nERP编号：49727\n对标ERP产品编号：49726, 49725\n", encoding="utf-8")
    result = adapter.read_benchmark_erp_pro_ids(archive)
    assert result["status"] == "BENCHMARK_ERP_PROID_RESOLVED"
    assert result["benchmark_erp_pro_ids"] == ["49726", "49725"]

    missing = tmp_path / "missing-benchmark.md"
    missing.write_text("产品编号：B2\nERP编号：49727\nASIN：B0CR17M53J\n", encoding="utf-8")
    assert adapter.read_benchmark_erp_pro_ids(missing)["status"] == adapter.BENCHMARK_PROID_NOT_AVAILABLE


def test_query_is_parameterized_and_rows_keep_raw_fields(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / adapter.DEFAULT_CONFIG_NAME).write_text(json.dumps({
        "server": "placeholder", "port": 1433, "database": "Amazon",
        "username": "readonly", "passwordRef": "ERP_TEST_PASSWORD",
        "encrypt": True, "trustServerCertificate": False, "readOnly": True,
        "schema": "dbo",
    }), encoding="utf-8")
    (config_dir / adapter.DEFAULT_MAPPING_NAME).write_text(json.dumps({
        "mappings": {"productKeywords": {"objectName": "PickPwKView", "productCodeField": "ProId"}}
    }), encoding="utf-8")
    (config_dir / adapter.DEFAULT_SCHEMA_NAME).write_text(
        "`ProId` `Keyword` `KeywordCn` `IsExact` `Tags` `SearchVolume30` `UpdateTime` `RecordDate`\n", encoding="utf-8"
    )
    archive = tmp_path / "01_产品档案.md"
    archive.write_text("产品编号：B2\nERP编号：49727\n", encoding="utf-8")

    class Cursor:
        description = [("ProId",), ("Keyword",), ("SearchVolume30",)]
        def __init__(self):
            self.sql = None
            self.params = None
        def execute(self, sql, *params):
            self.sql, self.params = sql, params
        def fetchall(self):
            return [(49727, "sister gifts", 1234)]
        def close(self):
            pass

    class Connection:
        def __init__(self):
            self.cursor_obj = Cursor()
        def cursor(self):
            return self.cursor_obj
        def close(self):
            pass

    connection = Connection()
    seen = {}
    def connector(config, password):
        seen["password"] = password
        return connection

    result = adapter.ERPKeywordAdapter(
        config_dir,
        connector=connector,
        password_resolver=lambda _config: "secret-only-in-memory",
        clock=lambda: "2026-09-15T00:00:00+00:00",
    ).fetch(archive)
    assert result["status"] == adapter.DATA_READY
    assert connection.cursor_obj.params == ("49727",)
    assert "?" in connection.cursor_obj.sql and "49727" not in connection.cursor_obj.sql
    assert result["rows"][0]["keyword"] == "sister gifts"
    assert result["rows"][0]["raw_fields"]["SearchVolume30"] == 1234
    assert result["rows"][0]["field_semantics"]["SearchVolume30"]["status"] == "DOCUMENTED"
    assert result["rows"][0]["field_semantics"]["IsExact"]["status"] == "DOCUMENTED"
    assert result["rows"][0]["field_semantics"]["Tags"]["status"] == "DOCUMENTED"
    assert result["record_id_field"] is None
    assert result["record_id_status"] == adapter.KEYWORD_RECORD_ID_UNCONFIRMED
    assert result["rows"][0]["record_id"] is None
    assert result["rows"][0]["record_id_status"] == adapter.KEYWORD_RECORD_ID_UNCONFIRMED
    assert "secret-only-in-memory" not in repr(result)


def test_provider_unavailable_is_explicit_and_does_not_guess_product_code(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / adapter.DEFAULT_CONFIG_NAME).write_text(json.dumps({
        "passwordRef": "MISSING_SECRET", "username": "readonly"
    }), encoding="utf-8")
    (config_dir / adapter.DEFAULT_MAPPING_NAME).write_text(json.dumps({
        "mappings": {"productKeywords": {"objectName": "PickPwKView", "productCodeField": "ProId"}}
    }), encoding="utf-8")
    (config_dir / adapter.DEFAULT_SCHEMA_NAME).write_text("`ProId` `Keyword`", encoding="utf-8")
    archive = tmp_path / "01_产品档案.md"
    archive.write_text("产品编号：B2\n", encoding="utf-8")
    result = adapter.ERPKeywordAdapter(config_dir, password_resolver=lambda _config: None).fetch(archive)
    assert result["status"] == adapter.MISSING_PROID
    assert result["erp_pro_id"] is None


def test_precision_query_uses_proid_and_complete_tag_parameters(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / adapter.DEFAULT_CONFIG_NAME).write_text(
        json.dumps({"passwordRef": "ERP_TEST_PASSWORD", "username": "readonly", "readOnly": True}),
        encoding="utf-8",
    )
    (config_dir / adapter.DEFAULT_MAPPING_NAME).write_text(
        json.dumps({"mappings": {"productKeywords": {"objectName": "PickPwKView", "productCodeField": "ProId"}}}),
        encoding="utf-8",
    )
    (config_dir / adapter.DEFAULT_SCHEMA_NAME).write_text("`ProId` `Keyword` `Tags`\n", encoding="utf-8")
    archive = tmp_path / "01_产品档案.md"
    archive.write_text("产品编号：B2\nERP编号：49727\n", encoding="utf-8")

    class Cursor:
        description = [("ProId",), ("Keyword",), ("Tags",)]
        def __init__(self):
            self.sql = None
            self.params = None
        def execute(self, sql, *params):
            self.sql, self.params = sql, params
        def fetchall(self):
            return [(49727, "sister gift", "|1精准|"), (99999, "sister gift", "|1精准|")]
        def close(self):
            pass

    class Connection:
        def __init__(self):
            self.cursor_obj = Cursor()
        def cursor(self):
            return self.cursor_obj
        def close(self):
            pass

    connection = Connection()
    result = adapter.ERPKeywordAdapter(
        config_dir,
        connector=lambda _config, _password: connection,
        password_resolver=lambda _config: "memory-only",
    ).fetch(archive, product_code="B2", precision_only=True)
    assert result["status"] == adapter.DATA_READY
    assert connection.cursor_obj.params == ("49727", adapter.PRECISION_TAG)
    assert "CHARINDEX(?," in connection.cursor_obj.sql
    assert "|1精准|" not in connection.cursor_obj.sql
    assert len(result["rows"]) == 1
    assert result["rows"][0]["erp_pro_id"] == "49727"


def test_benchmark_fetch_queries_each_explicit_proid_separately(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / adapter.DEFAULT_CONFIG_NAME).write_text(
        json.dumps({"passwordRef": "ERP_TEST_PASSWORD", "username": "readonly", "readOnly": True}),
        encoding="utf-8",
    )
    (config_dir / adapter.DEFAULT_MAPPING_NAME).write_text(
        json.dumps({"mappings": {"productKeywords": {"objectName": "PickPwKView", "productCodeField": "ProId"}}}),
        encoding="utf-8",
    )
    (config_dir / adapter.DEFAULT_SCHEMA_NAME).write_text("`ProId` `Keyword` `Tags`\n", encoding="utf-8")
    archive = tmp_path / "01_产品档案.md"
    archive.write_text("产品编号：B2\nERP编号：49727\n对标ERP产品编号：49726,49725\n", encoding="utf-8")

    calls = []

    class Cursor:
        description = [("ProId",), ("Keyword",), ("Tags",)]
        def execute(self, sql, *params):
            calls.append((sql, params))
        def fetchall(self):
            pro_id = calls[-1][1][0]
            return [(int(pro_id), "sister gift", "|1精准|")]
        def close(self):
            pass

    class Connection:
        def cursor(self):
            return Cursor()
        def close(self):
            pass

    result = adapter.fetch_benchmark_keyword_evidence(
        archive,
        config_dir,
        product_code="B2",
        connector=lambda _config, _password: Connection(),
        password_resolver=lambda _config: "memory-only",
    )
    assert result["status"] == "BENCHMARK_EVIDENCE_READY"
    assert result["benchmark_erp_pro_ids"] == ["49726", "49725"]
    assert [call[1] for call in calls] == [("49726",), ("49725",)]
    assert all("49727" not in call[0] for call in calls)
