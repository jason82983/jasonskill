import csv
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from erp_keyword_management import MockPickKwProvider, process, validate_translation, write_csv, FIELDS, choose_page_size

def tr(s):
    return {"sister gift": "姐妹礼物", "wallet chain": "钱包链"}.get(s.lower(), "中文词")

def test_dry_run_and_existing_preserved():
    p = MockPickKwProvider([
        {"Id": "2", "Keyword": "sister gift", "KeywordCn": None},
        {"Id": "1", "Keyword": "wallet chain", "KeywordCn": "钱包链"},
    ])
    out = process(p, tr, dry_run=True, scope={"Limit": 1, "Filter": "KeywordCn IS NULL"})
    assert [r.ResultStatus for r in out["Rows"]] == ["SKIP_ALREADY_TRANSLATED", "DRY_RUN_PROPOSED"]

def test_empty_source_and_validation():
    p = MockPickKwProvider([{"Id": "1", "Keyword": " ", "KeywordCn": None}])
    calls = []
    out = process(p, lambda x: calls.append(x) or "中文", dry_run=True, scope={"Limit": 1})
    assert out["Rows"][0].ResultStatus == "SOURCE_KEYWORD_EMPTY"
    assert calls == []
    assert validate_translation("abc", "", 10)[0] is False
    assert validate_translation("abc", "Translation: 中文")[0] is False

def test_cache_and_update_only_keyword_cn():
    p = MockPickKwProvider([
        {"Id": "1", "Keyword": "wallet chain", "KeywordCn": None},
        {"Id": "2", "Keyword": "WALLET   CHAIN", "KeywordCn": ""},
    ])
    out = process(p, tr, dry_run=False, scope={"Limit": 2, "Batch": "1"})
    assert all(r.ResultStatus == "UPDATED_VERIFIED" for r in out["Rows"])
    assert p.updated_fields == [{"KeywordCn"}, {"KeywordCn"}]
    assert out["Stats"]["translation_requests"] == 1

def test_concurrency_and_source_change():
    p = MockPickKwProvider([
        {"Id": "1", "Keyword": "sister gift", "KeywordCn": None},
        {"Id": "2", "Keyword": "wallet chain", "KeywordCn": None},
    ])
    p.concurrent_fill["1"] = "姐妹礼物"
    p.change_keyword["2"] = "changed"
    out = process(p, tr, dry_run=False, scope={"Limit": 2})
    assert {r.ResultStatus for r in out["Rows"]} == {"SKIP_CONCURRENTLY_FILLED", "SOURCE_KEYWORD_CHANGED"}

def test_csv_bom_and_fields(tmp_path):
    p = MockPickKwProvider([{"Id": "1", "Keyword": "wallet chain", "KeywordCn": None}])
    out = process(p, tr, dry_run=True, scope={"Limit": 1})
    path = tmp_path / "x.csv"; write_csv(path, out["Rows"])
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    with path.open(encoding="utf-8-sig", newline="") as f:
        assert next(csv.reader(f)) == FIELDS

def test_unverified_writer_is_blocked():
    class ReadOnly(MockPickKwProvider):
        writer_verified = False
    p = ReadOnly([{"Id": "1", "Keyword": "wallet chain", "KeywordCn": None}])
    out = process(p, tr, dry_run=False, scope={"Limit": 1})
    assert out["Rows"][0].ResultStatus == "WRITE_BLOCKED"
    assert p.updated_fields == []

def test_scope_required_and_adaptive_page_size():
    p = MockPickKwProvider([{"Id": "1", "Keyword": "wallet chain", "KeywordCn": None}])
    try:
        process(p, tr, dry_run=True)
        assert False, "scope should be mandatory"
    except ValueError as exc:
        assert str(exc) == "UPDATE_SCOPE_REQUIRED"
    out = process(p, tr, dry_run=True, scope={"Limit": 1}, estimated_rows=200000)
    assert out["PageSize"] == 2000

def test_limit_is_number_of_missing_nonempty_keywords():
    p = MockPickKwProvider([
        {"Id": "1", "Keyword": "wallet chain", "KeywordCn": None},
        {"Id": "2", "Keyword": "sister gift", "KeywordCn": None},
        {"Id": "3", "Keyword": "already", "KeywordCn": "已有"},
    ])
    out = process(p, tr, dry_run=True, scope={"Limit": 1})
    assert [r.ResultStatus for r in out["Rows"]].count("DRY_RUN_PROPOSED") == 1
