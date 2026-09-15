"""6-2 ERP exact-keyword and precise-broad-seed contract tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "erp_precision_keyword_analysis", ROOT / "scripts" / "erp_precision_keyword_analysis.py"
)
analysis = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(analysis)


def _defs():
    return {"Keyword": {"status": "DOCUMENTED"}, "Tags": {"status": "DOCUMENTED"}}


def test_tags_complete_precision_label_selects_and_keeps_duplicates():
    rows = [
        {"keyword": "Sister Gift", "raw_fields": {"Keyword": "Sister Gift", "Tags": "|1精准|"}},
        {"keyword": "sister gift", "raw_fields": {"Keyword": "sister gift", "Tags": "|2主|1精准|"}},
        {"keyword": "sister gifts", "raw_fields": {"Keyword": "sister gifts", "Tags": "|2主|"}},
    ]
    result = analysis.select_precision_keywords(rows, _defs())
    assert result["status"] == "READY"
    assert len(result["rows"]) == 2
    assert list(result["keywords"]) == ["sister gift"]
    assert analysis.select_precision_keywords(rows, {"Keyword": {"status": "DOCUMENTED"}})["status"] == analysis.SEMANTICS_UNCERTAIN


def test_isexact_is_ignored_and_tags_controls_precision():
    rows = [
        {"keyword": "tagged only", "raw_fields": {"Keyword": "tagged only", "IsExact": 0, "Tags": "|1精准|"}},
        {"keyword": "isexact only", "raw_fields": {"Keyword": "isexact only", "IsExact": 1, "Tags": "|2主|"}},
        {"keyword": "null isexact tagged", "raw_fields": {"Keyword": "null isexact tagged", "IsExact": None, "Tags": "|1精准|"}},
    ]
    result = analysis.select_precision_keywords(rows, _defs())
    assert set(result["keywords"]) == {"tagged only", "null isexact tagged"}


def test_precision_tag_requires_complete_label():
    rows = [
        {"keyword": "partial one", "raw_fields": {"Keyword": "partial one", "Tags": "精准"}},
        {"keyword": "partial two", "raw_fields": {"Keyword": "partial two", "Tags": "|11精准|"}},
        {"keyword": "digit only", "raw_fields": {"Keyword": "digit only", "Tags": "|1|"}},
    ]
    result = analysis.select_precision_keywords(rows, _defs())
    assert result["status"] == analysis.NO_PRECISION
    assert result["rows"] == []


def test_empty_keyword_is_not_generated():
    rows = [{"keyword": "", "raw_fields": {"Keyword": "", "Tags": "|1精准|"}}]
    result = analysis.select_precision_keywords(rows, _defs())
    assert result["status"] == analysis.NO_PRECISION


def test_precise_broad_seeds_are_short_but_review_gated():
    result = analysis.build_precise_broad_seeds([
        "sister gifts ideas", "sister gifts for birthday", "sister gifts for women"
    ])
    assert result["status"] == "READY"
    assert result["candidates"]
    assert all(len(item["seed"].split()) >= 2 for item in result["candidates"])
    assert all(item["status"] == "REVIEW_REQUIRED" for item in result["candidates"])


def test_no_exact_keywords_do_not_create_broad_candidates():
    result = analysis.build_precise_broad_seeds([])
    assert result["status"] == analysis.NO_PRECISION
    assert result["candidates"] == []


def test_broad_seed_filter_rejects_incomplete_fragments_and_limits_cluster_output():
    result = analysis.build_precise_broad_seeds([
        "sister gifts ideas", "sister gifts for birthday", "sister gifts for women",
        "sister gifts for graduation", "sister gifts for christmas",
    ])
    seeds = [item["seed"] for item in result["candidates"]]
    assert "gifts for" not in seeds
    assert "sister gifts for" not in seeds
    assert len(seeds) <= 3
