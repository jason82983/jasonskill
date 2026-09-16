"""Calculate Benchmark Organic Search Occupancy over the 6-0-3 Intent Tree."""
from __future__ import annotations

import argparse
import csv
import html
import importlib.util
import json
import re
import statistics
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.stage6_artifact_contract import (  # noqa: E402
    assert_new_outputs, make_artifact_metadata, metadata_sidecar_path,
    new_run_context, resolve_latest_valid_bundle,
    timestamped_output_path, write_metadata_sidecar,
)
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_batch,
)

SKILL_ID = "hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis"
OUTPUT_DIR = "6-0-6_对标意图市场占领分析"
INPUT_DIR_603 = "6-0-3_精准泛词提取"
BENCHMARK_HIGH_PRECISION_COLUMNS = ("所属产品编号", "对标ASIN", "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名", "精准度", "精准原因")
DETAIL_COLUMNS = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标编码", "对标ASIN", "自然排名")
SUMMARY_COLUMNS = ("精准泛词", "中文", "层级", "父精准泛词", "直接搜索量", "汇总搜索量", "平均竞品数", "意图机会比", "直接对应词数")
MAPPING_COLUMNS = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数", "精准泛词", "精准泛词中文")
OCCUPANCY_COLUMNS = ("对标编码", "对标ASIN", "精准泛词", "中文", "层级", "父精准泛词", "汇总搜索量", "有效排名词数", "Top10关键词数", "Top20关键词数", "Top50关键词数", "Top100关键词数", "平均自然排名", "加权自然排名", "Top10占领搜索量", "Top10搜索量覆盖率", "Top20占领搜索量", "Top20搜索量覆盖率", "Top50占领搜索量", "Top50搜索量覆盖率", "Top100占领搜索量", "Top100搜索量覆盖率", "占领等级", "占领判断原因")
CONSENSUS_COLUMNS = ("精准泛词", "中文", "层级", "父精准泛词", "汇总搜索量", "对标总数", "有效覆盖对标数", "核心占领对标数", "强占领对标数", "核心/强占领对标数", "最佳对标编码", "最佳对标ASIN", "最佳Top20搜索量覆盖率", "Top20覆盖率中位数", "Top50覆盖率中位数", "多对标共识等级", "共识判断原因")
OCCUPANCY_LEVELS = {"核心占领", "强占领", "中度占领", "弱占领"}
CONSENSUS_LEVELS = {"高共识", "中共识", "低共识", "单点验证"}
TOPS = (10, 20, 50, 100)


def _s(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _d(value: Any, code: str = "MISSING_MARKET_CAPACITY") -> Decimal:
    raw = _s(value).replace(",", "")
    if raw in {"", "NULL", "None", "DATA_NOT_AVAILABLE"}:
        raise ValueError(code)
    try:
        result = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(code) from exc
    if not result.is_finite():
        raise ValueError(code)
    return result


def _fmt(value: Decimal | None, places: int = 4) -> str:
    if value is None:
        return "DATA_NOT_AVAILABLE"
    q = Decimal(1).scaleb(-places)
    return str(value.quantize(q, rounding=ROUND_HALF_UP))


def _schema_validator(schema: tuple[str, ...]):
    def validate(_path, rows, metadata):
        if rows is None:
            return "CSV_READ_FAILED"
        if list(rows[0].keys()) != list(schema) if rows else False:
            return "SCHEMA_MISMATCH"
        if metadata and metadata.get("Schema") not in (None, list(schema)):
            return "METADATA_SCHEMA_MISMATCH"
        return None
    return validate


def input_candidates(product_root: str | Path, product_code: str) -> dict[str, list[Path]]:
    root = Path(product_root).resolve()
    dir603 = root / "06_SKILL分析报告" / INPUT_DIR_603
    patterns = {
        "summary": re.compile(r"^6-0-3_精准泛词汇总_\d{8}_\d{6}\.csv$"),
        "mapping": re.compile(r"^6-0-3_词对应的精准泛词_\d{8}_\d{6}\.csv$"),
    }
    return {
        "summary": [p for p in dir603.glob("*.csv") if patterns["summary"].fullmatch(p.name)] if dir603.is_dir() else [],
        "mapping": [p for p in dir603.glob("*.csv") if patterns["mapping"].fullmatch(p.name)] if dir603.is_dir() else [],
    }


def _resolve_602_package(root: Path, product_code: str) -> dict[str, Any]:
    skills_root = Path(__file__).resolve().parents[2]
    resolver_path = skills_root / "hzp-amz-6-0-3-precision-broad-extraction" / "scripts" / "broad_seed_cluster.py"
    if not resolver_path.is_file():
        raise FileNotFoundError("606_602_PACKAGE_RESOLVER_UNAVAILABLE")
    spec = importlib.util.spec_from_file_location("stage6_603_602_package_resolver", resolver_path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError("606_602_PACKAGE_RESOLVER_UNAVAILABLE")
    resolver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(resolver)
    package = resolver.resolve_latest_valid_602_run_package(root, product_code)
    if package.get("status") != "LATEST_VALID_602_RUN_PACKAGE_READY":
        raise ValueError("606_602_RUN_PACKAGE_NOT_FOUND")
    return package


def resolve_inputs(product_root: str | Path, product_code: str) -> dict[str, Any]:
    root = Path(product_root).resolve()
    candidates = input_candidates(root, product_code)
    if any(not candidates[key] for key in candidates):
        raise FileNotFoundError("606_INPUT_NOT_FOUND")
    benchmark = _resolve_602_package(root, product_code)
    bundle = resolve_latest_valid_bundle(
        root, "hzp-amz-6-0-3-precision-broad-extraction",
        {"summary": candidates["summary"], "mapping": candidates["mapping"]},
        product_code=product_code,
        report_identities={"summary": "PRECISION_BROAD_SUMMARY", "mapping": "PRECISION_BROAD_MAPPING"},
        required_schemas={"summary": SUMMARY_COLUMNS, "mapping": MAPPING_COLUMNS},
        validators={"summary": _schema_validator(SUMMARY_COLUMNS), "mapping": _schema_validator(MAPPING_COLUMNS)},
    )
    if bundle.get("status") != "LATEST_VALID_RUN_BUNDLE_RESOLVED":
        skipped = bundle.get("skipped_candidates") or {}
        inspected = [item for values in skipped.values() for item in values]
        if any(item.get("reason") in {"SCHEMA_MISMATCH", "METADATA_SCHEMA_MISMATCH"} for item in inspected):
            raise ValueError("606_INPUT_SCHEMA_INVALID")
        raise ValueError("606_INPUT_RUN_MISMATCH")
    if not bundle.get("run_id") or not bundle.get("run_timestamp"):
        raise ValueError("606_INPUT_RUN_MISMATCH")
    summary = bundle["assets"]["summary"]
    mapping = bundle["assets"]["mapping"]
    for asset in (summary, mapping):
        asset["run_id"] = bundle.get("run_id")
        asset["run_timestamp"] = bundle.get("run_timestamp")
        asset["input_resolution_method"] = bundle.get("input_resolution_method")
    manifest = benchmark.get("manifest") or {}
    identities_by_product_id = manifest.get("Benchmark Identities") or {}
    if (manifest.get("Current Product") != product_code
            or not isinstance(identities_by_product_id, dict)
            or len(identities_by_product_id) != manifest.get("Benchmark Count")):
        raise ValueError("BENCHMARK_IDENTITY_MISSING")
    benchmark_identities: dict[str, str] = {}
    product_id_by_code: dict[str, str] = {}
    for product_id, identity in identities_by_product_id.items():
        code, asin = _s(identity.get("对标编码")), _s(identity.get("对标ASIN"))
        if not code or not asin or code in benchmark_identities:
            raise ValueError("BENCHMARK_IDENTITY_MISSING")
        benchmark_identities[code] = asin
        product_id_by_code[code] = _s(product_id)
    detail_rows: list[dict[str, str]] = []
    benchmark_files = benchmark.get("files", {}).get("benchmarks") or {}
    if set(benchmark_files) != set(product_id_by_code.values()):
        raise ValueError("606_602_BENCHMARK_FILE_COUNT_MISMATCH")
    for code, product_id in product_id_by_code.items():
        path = Path(benchmark_files[product_id])
        rows = _read_asset_csv(path)
        headers, benchmark_rows = rows
        if headers != list(BENCHMARK_HIGH_PRECISION_COLUMNS):
            raise ValueError("606_INPUT_SCHEMA_INVALID")
        seen: set[str] = set()
        for row in benchmark_rows:
            canonical = " ".join(_s(row.get("词")).casefold().split())
            if (_s(row.get("所属产品编号")) != product_id or _s(row.get("对标ASIN")) != benchmark_identities[code]
                    or _s(row.get("精准度")) != "高度精准" or not canonical or canonical in seen):
                raise ValueError("606_602_BENCHMARK_ASSET_INVALID")
            seen.add(canonical)
            detail_rows.append({
                "Id": row.get("Id", ""), "词": row.get("词", ""), "中文": row.get("中文", ""),
                "市场容量": row.get("市场容量", ""), "竞争产品数": row.get("竞争产品数", ""),
                "供需比": row.get("供需比", ""), "对标编码": code,
                "对标ASIN": row.get("对标ASIN", ""), "自然排名": row.get("自然排名", ""),
            })
    detail = {"file": ";".join(benchmark_files.values()), "files": benchmark_files,
              "metadata": {"Skill_ID": "hzp-amz-6-0-2-ai-precision-keyword-identification",
                           "Report_Identity": "BENCHMARK_HIGH_PRECISION_KEYWORDS"},
              "run_id": benchmark.get("run_id"),
              "run_timestamp": benchmark.get("run_timestamp"),
              "input_resolution_method": "LATEST_VALID_602_3_PLUS_N_RUN_PACKAGE"}
    summary_rows, mapping_rows = summary.get("rows") or [], mapping.get("rows") or []
    if not summary_rows or not mapping_rows:
        raise ValueError("606_INPUT_EMPTY")
    return {"detail": detail, "benchmark": benchmark, "summary": summary, "mapping": mapping,
            "detail_rows": detail_rows, "summary_rows": summary_rows, "mapping_rows": mapping_rows,
            "benchmark_identities": benchmark_identities,
            "product_code": product_code, "product_root": str(root)}


def _rank(value: Any) -> tuple[Decimal | None, str | None]:
    raw = _s(value)
    if raw.upper() in {"", "NULL", "NONE", "DATA_NOT_AVAILABLE", "N/A"}:
        return None, "MISSING_ORGANIC_RANK"
    try:
        rank = Decimal(raw.replace(",", ""))
    except InvalidOperation:
        return None, "INVALID_ORGANIC_RANK"
    if not rank.is_finite() or rank <= 0:
        return None, "INVALID_ORGANIC_RANK"
    return rank, None


def _facts(row: Mapping[str, Any]) -> tuple[str, str, Decimal, Decimal | None, Decimal | None]:
    capacity = _d(row.get("市场容量"))
    competitor_raw = _s(row.get("竞争产品数"))
    competitor = None if competitor_raw.upper() in {"", "NULL", "DATA_NOT_AVAILABLE"} else _d(competitor_raw, "KEYWORD_MARKET_FACT_CONFLICT")
    ratio_raw = _s(row.get("供需比"))
    ratio = None if ratio_raw.upper() in {"", "NULL", "DATA_NOT_AVAILABLE"} else _d(ratio_raw, "KEYWORD_MARKET_FACT_CONFLICT")
    return _s(row.get("词")), _s(row.get("中文")), capacity, competitor, ratio


def _build_subtrees(summary_rows: list[dict[str, str]]) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, str]]]:
    by_name = {_s(row.get("精准泛词")): row for row in summary_rows}
    if "" in by_name or len(by_name) != len(summary_rows):
        raise ValueError("INVALID_INTENT_TREE")
    children: dict[str, list[str]] = defaultdict(list)
    for name, row in by_name.items():
        parent = _s(row.get("父精准泛词"))
        if parent:
            if parent not in by_name or parent == name:
                raise ValueError("INVALID_INTENT_TREE")
            children[parent].append(name)
    subtrees: dict[str, list[dict[str, str]]] = {}
    for name in by_name:
        seen: set[str] = set()
        stack = [name]
        while stack:
            current = stack.pop()
            if current in seen:
                raise ValueError("INVALID_INTENT_TREE")
            seen.add(current)
            stack.extend(children[current])
        subtrees[name] = [by_name[item] for item in sorted(seen)]
    return subtrees, by_name


def derive_consensus_from_occupancy(occupancy: list[dict[str, Any]],
                                   intent_rows: Mapping[str, dict[str, str]],
                                   benchmarks: list[str]) -> list[dict[str, Any]]:
    """Rebuild all numeric Consensus fields solely from OUTPUT A-shaped rows."""
    by_intent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in occupancy:
        by_intent[row["精准泛词"]].append(row)
    rebuilt: list[dict[str, Any]] = []
    for intent, source in intent_rows.items():
        rows = by_intent[intent]
        covered = [row for row in rows if row["_valid_count"] > 0]
        ranked = sorted(rows, key=lambda row: (
            -Decimal(row["Top20搜索量覆盖率"] if row["Top20搜索量覆盖率"] != "DATA_NOT_AVAILABLE" else "-1"),
            -Decimal(row["Top10搜索量覆盖率"] if row["Top10搜索量覆盖率"] != "DATA_NOT_AVAILABLE" else "-1"),
            Decimal(row["加权自然排名"]) if row["加权自然排名"] != "DATA_NOT_AVAILABLE" else Decimal("Infinity"),
            row["对标编码"],
        ))
        best = ranked[0] if covered else None
        rates20 = [Decimal(row["Top20搜索量覆盖率"]) for row in rows if row["Top20搜索量覆盖率"] != "DATA_NOT_AVAILABLE"]
        rates50 = [Decimal(row["Top50搜索量覆盖率"]) for row in rows if row["Top50搜索量覆盖率"] != "DATA_NOT_AVAILABLE"]
        rebuilt.append({
            "精准泛词": intent,
            "对标总数": len(benchmarks),
            "有效覆盖对标数": len(covered),
            "核心占领对标数": sum(row["占领等级"] == "核心占领" for row in rows),
            "强占领对标数": sum(row["占领等级"] == "强占领" for row in rows),
            "核心/强占领对标数": sum(row["占领等级"] in {"核心占领", "强占领"} for row in rows),
            "最佳对标编码": best["对标编码"] if best else "DATA_NOT_AVAILABLE",
            "最佳对标ASIN": best["对标ASIN"] if best else "DATA_NOT_AVAILABLE",
            "最佳Top20搜索量覆盖率": best["Top20搜索量覆盖率"] if best else "DATA_NOT_AVAILABLE",
            "Top20覆盖率中位数": _fmt(Decimal(str(statistics.median(rates20))) if rates20 else None),
            "Top50覆盖率中位数": _fmt(Decimal(str(statistics.median(rates50))) if rates50 else None),
        })
    return rebuilt


def calculate(detail_rows: list[dict[str, str]], summary_rows: list[dict[str, str]],
              mapping_rows: list[dict[str, str]], decisions: Mapping[str, Any] | None = None,
              benchmark_identities: Mapping[str, str] | None = None) -> dict[str, Any]:
    if not summary_rows or not mapping_rows:
        raise ValueError("606_INPUT_EMPTY")
    subtree_rows, intent_rows = _build_subtrees(summary_rows)
    keyword_by_id: dict[str, dict[str, str]] = {}
    primary_by_intent: dict[str, set[str]] = defaultdict(set)
    for row in mapping_rows:
        kid, intent = _s(row.get("Id")), _s(row.get("精准泛词"))
        if not kid:
            raise ValueError("BENCHMARK_OBSERVATION_JOIN_FAILED")
        if kid in keyword_by_id:
            raise ValueError("BENCHMARK_OBSERVATION_JOIN_FAILED")
        if intent not in intent_rows:
            raise ValueError("INTENT_MAPPING_MISSING")
        keyword_by_id[kid] = row
        primary_by_intent[intent].add(kid)

    market_facts: dict[str, tuple[Any, ...]] = {}
    observations: dict[tuple[str, str], dict[str, Any]] = {}
    benchmark_asins: dict[str, str] = {_s(code): _s(asin) for code, asin in (benchmark_identities or {}).items()}
    rank_audit: list[dict[str, str]] = []
    observed_ids: set[str] = set()
    for row in detail_rows:
        kid, code, asin = _s(row.get("Id")), _s(row.get("对标编码")), _s(row.get("对标ASIN"))
        if not kid or not code or not asin:
            raise ValueError("BENCHMARK_IDENTITY_MISSING")
        if code in benchmark_asins and benchmark_asins[code] != asin:
            raise ValueError("BENCHMARK_IDENTITY_MISSING")
        benchmark_asins[code] = asin
        key = (kid, code)
        if key in observations:
            raise ValueError("DUPLICATE_BENCHMARK_OBSERVATION")
        if kid not in keyword_by_id:
            continue
        facts = _facts(row)
        if kid in market_facts and market_facts[kid] != facts:
            raise ValueError("BENCHMARK_OBSERVATION_JOIN_FAILED")
        market_facts[kid] = facts
        rank, issue = _rank(row.get("自然排名"))
        observations[key] = {"rank": rank, "row": row}
        if issue:
            rank_audit.append({"Id": kid, "词": _s(row.get("词")), "对标编码": code,
                               "对标ASIN": asin, "自然排名": _s(row.get("自然排名")), "状态": issue})
        if kid in keyword_by_id:
            observed_ids.add(kid)
    if not benchmark_asins:
        raise ValueError("BENCHMARK_IDENTITY_MISSING")
    missing_ids = sorted(set(keyword_by_id) - set(market_facts))
    if missing_ids:
        raise ValueError("BENCHMARK_OBSERVATION_JOIN_FAILED")
    if set(keyword_by_id) - observed_ids:
        raise ValueError("BENCHMARK_OBSERVATION_JOIN_FAILED")
    no_observation_audit = [
        {"Id": kid, "词": _s(keyword_by_id[kid].get("词")), "精准泛词": _s(keyword_by_id[kid].get("精准泛词")),
         "对标编码": code, "对标ASIN": benchmark_asins[code], "状态": "NO_602_HIGH_PRECISION_OBSERVATION"}
        for kid in keyword_by_id for code in benchmark_asins if (kid, code) not in observations
    ]

    for kid, mapped in keyword_by_id.items():
        canonical = market_facts[kid]
        if _facts(mapped) != canonical:
            raise ValueError("BENCHMARK_OBSERVATION_JOIN_FAILED")
    for intent, ids in primary_by_intent.items():
        try:
            direct_from_rows = sum((market_facts[kid][2] for kid in ids), Decimal(0))
            direct_reported = _d(intent_rows[intent].get("直接搜索量"))
            subtree_ids = {kid for child in subtree_rows[intent] for kid in primary_by_intent.get(_s(child.get("精准泛词")), set())}
            subtree_from_rows = sum((market_facts[kid][2] for kid in subtree_ids), Decimal(0))
            subtree_reported = _d(intent_rows[intent].get("汇总搜索量"))
        except ValueError:
            raise
        if direct_from_rows != direct_reported or subtree_from_rows != subtree_reported:
            raise ValueError("INTENT_VOLUME_MISMATCH")
    # An intent with no direct records is legitimate if it has descendants; validate it too.
    for intent, row in intent_rows.items():
        direct_ids = primary_by_intent.get(intent, set())
        direct_actual = sum((market_facts[kid][2] for kid in direct_ids), Decimal(0))
        if direct_actual != _d(row.get("直接搜索量")):
            raise ValueError("INTENT_VOLUME_MISMATCH")
        ids = {kid for child in subtree_rows[intent] for kid in primary_by_intent.get(_s(child.get("精准泛词")), set())}
        if sum((market_facts[kid][2] for kid in ids), Decimal(0)) != _d(row.get("汇总搜索量")):
            raise ValueError("INTENT_VOLUME_MISMATCH")

    if decisions is not None and not isinstance(decisions, Mapping):
        raise ValueError("DECISION_COVERAGE_MISMATCH")
    occ_decision_rows = (decisions or {}).get("occupancy_decisions", [])
    consensus_decision_rows = (decisions or {}).get("consensus_decisions", [])
    if not isinstance(occ_decision_rows, list) or not isinstance(consensus_decision_rows, list):
        raise ValueError("DECISION_COVERAGE_MISMATCH")
    occ_keys = [(_s(x.get("对标编码")), _s(x.get("精准泛词"))) for x in occ_decision_rows]
    consensus_keys = [_s(x.get("精准泛词")) for x in consensus_decision_rows]
    if len(occ_keys) != len(set(occ_keys)) or len(consensus_keys) != len(set(consensus_keys)):
        raise ValueError("DECISION_COVERAGE_MISMATCH")
    occ_decisions = dict(zip(occ_keys, occ_decision_rows))
    consensus_decisions = dict(zip(consensus_keys, consensus_decision_rows))
    benchmarks = sorted(benchmark_asins)
    if decisions is not None:
        wanted_occ = {(code, intent) for code in benchmarks for intent in intent_rows}
        wanted_consensus = set(intent_rows) if len(benchmarks) > 1 else set()
        if (set(occ_decisions) != wanted_occ
                or (len(benchmarks) > 1 and set(consensus_decisions) != wanted_consensus)
                or (len(benchmarks) == 1 and consensus_decisions)):
            raise ValueError("DECISION_COVERAGE_MISMATCH")

    occupancy: list[dict[str, Any]] = []
    for intent, ir in intent_rows.items():
        sub_ids = {kid for child in subtree_rows[intent] for kid in primary_by_intent.get(_s(child.get("精准泛词")), set())}
        denominator = _d(ir.get("汇总搜索量"))
        for code in benchmarks:
            ranks: dict[str, Decimal] = {}
            for kid in sub_ids:
                obs = observations.get((kid, code))
                if obs and obs["rank"] is not None:
                    ranks[kid] = obs["rank"]
            volumes: dict[int, Decimal] = {}
            counts: dict[int, int] = {}
            for top in TOPS:
                selected = [kid for kid, rank in ranks.items() if rank <= top]
                volumes[top] = sum((market_facts[kid][2] for kid in selected), Decimal(0))
                counts[top] = len(selected)
            if any(volumes[a] > volumes[b] for a, b in zip(TOPS, TOPS[1:])) or any(counts[a] > counts[b] for a, b in zip(TOPS, TOPS[1:])):
                raise ValueError("OCCUPANCY_MONOTONICITY_FAILED")
            if any(volume > denominator for volume in volumes.values()):
                raise ValueError("OCCUPANCY_MONOTONICITY_FAILED")
            rates = {top: (volumes[top] / denominator if denominator > 0 else None) for top in TOPS}
            if any(rates[a] is not None and rates[b] is not None and rates[a] > rates[b] for a, b in zip(TOPS, TOPS[1:])):
                raise ValueError("OCCUPANCY_MONOTONICITY_FAILED")
            avg = sum(ranks.values(), Decimal(0)) / len(ranks) if ranks else None
            weight = sum((ranks[kid] * market_facts[kid][2] for kid in ranks), Decimal(0))
            weight_den = sum((market_facts[kid][2] for kid in ranks), Decimal(0))
            weighted = weight / weight_den if ranks and weight_den > 0 else None
            decision = occ_decisions.get((code, intent), {})
            level = _s(decision.get("占领等级"))
            reason = _s(decision.get("占领判断原因"))
            if decisions is not None and (level not in OCCUPANCY_LEVELS or not reason):
                raise ValueError("DECISION_COVERAGE_MISMATCH")
            occupancy.append({
                "对标编码": code, "对标ASIN": benchmark_asins[code], "精准泛词": intent,
                "中文": _s(ir.get("中文")), "层级": _s(ir.get("层级")), "父精准泛词": _s(ir.get("父精准泛词")),
                "汇总搜索量": _fmt(denominator, 0), "有效排名词数": len(ranks),
                "Top10关键词数": counts[10], "Top20关键词数": counts[20], "Top50关键词数": counts[50], "Top100关键词数": counts[100],
                "平均自然排名": _fmt(avg), "加权自然排名": _fmt(weighted),
                "Top10占领搜索量": _fmt(volumes[10], 0), "Top10搜索量覆盖率": _fmt(rates[10]),
                "Top20占领搜索量": _fmt(volumes[20], 0), "Top20搜索量覆盖率": _fmt(rates[20]),
                "Top50占领搜索量": _fmt(volumes[50], 0), "Top50搜索量覆盖率": _fmt(rates[50]),
                "Top100占领搜索量": _fmt(volumes[100], 0), "Top100搜索量覆盖率": _fmt(rates[100]),
                "占领等级": level, "占领判断原因": reason,
                "_valid_count": len(ranks), "_weighted": weighted, "_rates": rates,
            })

    consensus: list[dict[str, Any]] = []
    by_intent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in occupancy:
        by_intent[row["精准泛词"]].append(row)
    for intent, ir in intent_rows.items():
        rows = by_intent[intent]
        covered = [r for r in rows if r["_valid_count"] > 0]
        core = sum(r["占领等级"] == "核心占领" for r in rows)
        strong = sum(r["占领等级"] == "强占领" for r in rows)
        ranked = sorted(rows, key=lambda r: (
            -Decimal(r["Top20搜索量覆盖率"] if r["Top20搜索量覆盖率"] != "DATA_NOT_AVAILABLE" else "-1"),
            -Decimal(r["Top10搜索量覆盖率"] if r["Top10搜索量覆盖率"] != "DATA_NOT_AVAILABLE" else "-1"),
            Decimal(r["加权自然排名"]) if r["加权自然排名"] != "DATA_NOT_AVAILABLE" else Decimal("Infinity"),
            r["对标编码"],
        ))
        best = ranked[0] if covered else None
        top20 = [Decimal(r["Top20搜索量覆盖率"]) for r in rows if r["Top20搜索量覆盖率"] != "DATA_NOT_AVAILABLE"]
        top50 = [Decimal(r["Top50搜索量覆盖率"]) for r in rows if r["Top50搜索量覆盖率"] != "DATA_NOT_AVAILABLE"]
        decision = consensus_decisions.get(intent, {})
        if len(benchmarks) == 1:
            consensus_level, consensus_reason = "单对标模式", "单对标模式：只有一个 Benchmark，不能宣称多对标共识。"
        else:
            consensus_level = _s(decision.get("多对标共识等级"))
            consensus_reason = _s(decision.get("共识判断原因"))
            if decisions is not None and (consensus_level not in CONSENSUS_LEVELS or not consensus_reason):
                raise ValueError("DECISION_COVERAGE_MISMATCH")
        consensus.append({
            "精准泛词": intent, "中文": _s(ir.get("中文")), "层级": _s(ir.get("层级")), "父精准泛词": _s(ir.get("父精准泛词")),
            "汇总搜索量": _fmt(_d(ir.get("汇总搜索量")), 0), "对标总数": len(benchmarks),
            "有效覆盖对标数": len(covered), "核心占领对标数": core, "强占领对标数": strong,
            "核心/强占领对标数": core + strong, "最佳对标编码": best["对标编码"] if best else "DATA_NOT_AVAILABLE",
            "最佳对标ASIN": best["对标ASIN"] if best else "DATA_NOT_AVAILABLE",
            "最佳Top20搜索量覆盖率": best["Top20搜索量覆盖率"] if best else "DATA_NOT_AVAILABLE",
            "Top20覆盖率中位数": _fmt(Decimal(str(statistics.median(top20))) if top20 else None),
            "Top50覆盖率中位数": _fmt(Decimal(str(statistics.median(top50))) if top50 else None),
            "多对标共识等级": consensus_level, "共识判断原因": consensus_reason,
        })
    computed_consensus = derive_consensus_from_occupancy(occupancy, intent_rows, benchmarks)
    if len(computed_consensus) != len(consensus):
        raise ValueError("CONSENSUS_SOURCE_MISMATCH")
    for expected, actual in zip(computed_consensus, consensus):
        tie_fields = CONSENSUS_COLUMNS[10:13]
        if any(expected[field] != actual[field] for field in tie_fields):
            raise ValueError("BEST_BENCHMARK_TIEBREAK_MISMATCH")
        check_fields = (*CONSENSUS_COLUMNS[5:10], *CONSENSUS_COLUMNS[13:15])
        if any(expected[field] != actual[field] for field in check_fields):
            raise ValueError("CONSENSUS_SOURCE_MISMATCH")
            if expected[field] != actual[field]:
                raise ValueError("CONSENSUS_SOURCE_MISMATCH")
    return {"occupancy": occupancy, "consensus": consensus, "benchmarks": benchmarks,
            "benchmark_asins": benchmark_asins, "rank_audit": rank_audit,
            "no_observation_audit": no_observation_audit,
            "keyword_by_id": keyword_by_id, "observations": observations,
            "summary_rows": summary_rows, "subtree_rows": subtree_rows, "intent_rows": intent_rows,
            "input_keyword_count": len(keyword_by_id), "ranked_observation_count": sum(r["_valid_count"] for r in occupancy)}


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_asset_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or ()), list(reader)


def _table(headers: tuple[str, ...] | list[str], rows: list[list[Any]], empty: str = "暂无记录") -> str:
    def esc(value: Any) -> str:
        return html.escape(_s(value))
    def cell(header: Any, value: Any) -> str:
        raw = _s(value)
        if "率" in _s(header) and raw not in {"", "DATA_NOT_AVAILABLE"}:
            try:
                raw = f"{Decimal(raw) * 100:.2f}%"
            except InvalidOperation:
                pass
        return esc(raw)
    if not rows:
        return f'<p class="empty">{esc(empty)}</p>'
    return "<div class=\"table-wrap\"><table><thead><tr>" + "".join(f"<th>{esc(x)}</th>" for x in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{cell(headers[i], x)}</td>" for i, x in enumerate(row)) + "</tr>" for row in rows) + "</tbody></table></div>"


def render_html(product_code: str, result: Mapping[str, Any], inputs: Mapping[str, Any], *, run_id: str, generated_at: str) -> str:
    occ, con = result["occupancy"], result["consensus"]
    codes = result["benchmarks"]
    by_intent = {r["精准泛词"]: r for r in con}
    core = sum(r["占领等级"] == "核心占领" for r in occ)
    strong = sum(r["占领等级"] == "强占领" for r in occ)
    high = [r for r in con if r["多对标共识等级"] == "高共识"]
    single = [r for r in con if r["多对标共识等级"] in {"单点验证", "单对标模式"}]
    title = f"{product_code}｜对标意图市场占领分析"
    sections: list[str] = []
    def section(i: int, name: str, body: str) -> None:
        sections.append(f'<section id="m{i}"><h2>{i:02d}｜{html.escape(name)}</h2>{body}</section>')
    section(1, "Executive Summary", f'<div class="kpis"><div><b>{len(codes)}</b><span>Benchmark</span></div><div><b>{len(by_intent)}</b><span>Search Intent</span></div><div><b>{result["input_keyword_count"]}</b><span>Unique Keyword</span></div><div><b>{len(high)}</b><span>高共识市场</span></div><div><b>{len(single)}</b><span>单点/单对标市场</span></div><div><b>{core}/{strong}</b><span>核心/强占领判定行</span></div></div><p class="callout">本报告衡量 Organic Search Occupancy，不是 Sales Market Share；不推断销量、GMV、订单或点击份额。高共识不等于低竞争。</p><p>分析 ${html.escape(product_code)} 的 ${len(codes)} 个 Benchmark 在 ${len(by_intent)} 个 603 Search Intent 中的自然排名证据。所有数值由程序从 602 高度精准对标资产与 603 Intent Tree 计算；占领/共识等级与原因由 AI 定性判断。</p>')
    benchmark_rows = []
    for code in codes:
        own = [r for r in occ if r["对标编码"] == code]
        ranked = sorted(own, key=lambda r: (-Decimal(r["Top20搜索量覆盖率"] if r["Top20搜索量覆盖率"] != "DATA_NOT_AVAILABLE" else "-1"), r["精准泛词"]))
        leaders = "；".join(f'{r["精准泛词"]}（{r["占领等级"]}，Top20 {r["Top20搜索量覆盖率"]}）' for r in ranked[:3])
        benchmark_rows.append([code, result["benchmark_asins"][code], sum(r["占领等级"] == "核心占领" for r in own), sum(r["占领等级"] == "强占领" for r in own), leaders])
    section(2, "Benchmark Overview", _table(["对标编码", "对标ASIN", "核心占领Intent数", "强占领Intent数", "主要阵地（Top20覆盖率优先）"], benchmark_rows))
    matrix = []
    for intent, row in by_intent.items():
        per = {r["对标编码"]: r for r in occ if r["精准泛词"] == intent}
        matrix.append([intent, row["多对标共识等级"], *[f'{per[c]["占领等级"]} / {per[c]["Top20搜索量覆盖率"]} / {per[c]["Top50搜索量覆盖率"]}' for c in codes]])
    section(3, "Search Intent Occupancy Matrix", _table(["Intent", "共识", *codes], matrix))
    section(4, "各 Benchmark 核心阵地", _table(["对标编码", "Intent", "层级", "占领等级", "Top20覆盖", "加权自然排名", "原因"], [[r["对标编码"],r["精准泛词"],r["层级"],r["占领等级"],r["Top20搜索量覆盖率"],r["加权自然排名"],r["占领判断原因"]] for r in occ if r["占领等级"] in {"核心占领","强占领"}]))
    section(5, "多对标高共识市场", _table(["Intent", "层级", "有效覆盖对标数", "Best Benchmark", "Top20中位数", "Top50中位数", "共识原因"], [[r["精准泛词"],r["层级"],r["有效覆盖对标数"],r["最佳对标编码"],r["Top20覆盖率中位数"],r["Top50覆盖率中位数"],r["共识判断原因"]] for r in high]) + '<p class="note">高共识表示多个对标呈现相近的自然排名验证；竞争可能成熟甚至激烈，不表示市场容易进入。</p>')
    section(6, "单点验证市场", _table(["Intent", "最佳对标", "最佳Top20覆盖", "共识等级", "原因"], [[r["精准泛词"],r["最佳对标编码"],r["最佳Top20搜索量覆盖率"],r["多对标共识等级"],r["共识判断原因"]] for r in single]))
    section(7, "Parent / Child Occupancy", _table(["Benchmark", "Intent", "层级", "父Intent", "汇总搜索量", "Top20占领量", "Top20覆盖率", "等级"], [[r["对标编码"],r["精准泛词"],r["层级"],r["父精准泛词"],r["汇总搜索量"],r["Top20占领搜索量"],r["Top20搜索量覆盖率"],r["占领等级"]] for r in occ]))
    top_terms = []
    for kid, mapping in result["keyword_by_id"].items():
        for code in codes:
            obs = result["observations"].get((kid, code))
            if obs:
                rank = obs["rank"]
                band = ("Top10" if rank is not None and rank <= 10 else "Top20" if rank is not None and rank <= 20 else "Top50" if rank is not None and rank <= 50 else "Top100" if rank is not None and rank <= 100 else "Rank>100" if rank is not None else "\u6392\u540d\u7f3a\u5931/\u65e0\u6548")
                top_terms.append([kid, mapping["词"], mapping["精准泛词"], code, mapping["市场容量"], _s(rank), band])
    top_terms.sort(key=lambda x: (Decimal(x[4]), x[3], x[0]), reverse=True)
    section(8, "Top Search Demand Control", _table(["KwId", "关键词", "Intent", "Benchmark", "市场容量", "自然排名", "阈值"], top_terms[:100]))
    weak = [r for r in occ if r["占领等级"] == "弱占领"]
    section(9, "Weak / White Space Evidence", _table(["Benchmark", "Intent", "Top20覆盖", "Top50覆盖", "有效排名词", "限制性解释"], [[r["对标编码"],r["精准泛词"],r["Top20搜索量覆盖率"],r["Top50搜索量覆盖率"],r["有效排名词数"],"仅表示当前对标相对薄弱或验证不足；不是蓝海、低竞争或容易进入结论。"] for r in weak]))
    section(10, "给未来 6-0-5 的 Reality Evidence", _table(["Intent", "共识等级", "最佳Benchmark", "Top20覆盖中位数", "Top50覆盖中位数", "可用证据"], [[r["精准泛词"],r["多对标共识等级"],r["最佳对标编码"],r["Top20覆盖率中位数"],r["Top50覆盖率中位数"],"只提供对标自然搜索证据；6-0-5 独立决定首攻/核心/扩展/探索/暂缓。"] for r in con]))
    audit = [[x["Id"],x["词"],x["对标编码"],x["对标ASIN"],x["自然排名"],x["状态"]] for x in result["rank_audit"]]
    no_obs = [[x["Id"],x["词"],x["精准泛词"],x["对标编码"],x["对标ASIN"],x["状态"]] for x in result["no_observation_audit"]]
    benchmark_package = inputs.get("benchmark") or inputs.get("detail", {})
    benchmark_files = (benchmark_package.get("files", {}).get("benchmarks")
                       or inputs.get("detail", {}).get("files")
                       or {"detail": inputs.get("detail", {}).get("file", "detail.csv")})
    lineage = [["602对标高度精准词", Path(path).name, benchmark_package.get("run_id") or "DATA_NOT_AVAILABLE"]
               for path in benchmark_files.values()]
    lineage.extend([["603汇总", Path(inputs["summary"]["file"]).name, inputs["summary"].get("run_id")],
                    ["603映射", Path(inputs["mapping"]["file"]).name, inputs["mapping"].get("run_id")]])
    section(11, "数据质量、来源与边界", '<p>Organic Search Occupancy ≠ Sales Market Share。Rank NULL 不当作 999；缺失/非法排名仅记录审计，不进入均值或TopN。单个 Benchmark 未出现的观察记录单列为未观察，不推断其自然排名。父Intent含子级，父子可重叠，不能跨层相加；各Benchmark覆盖率不可相加。</p><h3>本次使用数据</h3>' + _table(["来源", "文件", "RUN_ID"], lineage) + '<h3>缺失/非法自然排名</h3>' + _table(["KwId","词","Benchmark","ASIN","原始排名","状态"], audit) + '<h3>未观察记录</h3>' + _table(["KwId","词","Primary Intent","Benchmark","ASIN","状态"], no_obs))
    css = "body{margin:0;background:#f3f5f8;color:#172438;font:14px/1.55 'Segoe UI',Arial,sans-serif}header,.wrap{max-width:1440px;margin:auto}header{padding:34px 24px 22px}.eyebrow{color:#54708f;letter-spacing:.12em;text-transform:uppercase;font-size:12px}h1{font-size:30px;margin:8px 0}main{max-width:1440px;margin:auto;padding:0 24px 42px}section{background:#fff;border:1px solid #e0e6ed;border-radius:12px;padding:20px;margin:14px 0;break-inside:avoid}h2{font-size:19px;margin:0 0 16px}h3{margin-top:22px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}.kpis div{background:#f5f8fb;padding:16px;border-radius:8px}.kpis b{display:block;font-size:25px}.kpis span,.note,.eyebrow{color:#60748a}.callout{border-left:4px solid #3874b8;background:#f2f7fd;padding:12px 16px}.table-wrap{overflow:auto;max-height:560px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;padding:9px;border-bottom:1px solid #e8edf2;vertical-align:top;min-width:82px}th{background:#eff4f8;position:sticky;top:0}td:nth-child(1){font-weight:600}.empty{color:#718096}@media(max-width:720px){header{padding:24px 14px}main{padding:0 12px 24px}section{padding:14px}h1{font-size:24px}}@media print{body{background:#fff}section{box-shadow:none;border-color:#bbb;page-break-inside:avoid}.table-wrap{max-height:none;overflow:visible}th{position:static}header,main{max-width:none;padding-left:0;padding-right:0}}"
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{css}</style></head><body><header><div class="eyebrow">Benchmark Intent Market Occupancy Analysis</div><h1>{html.escape(title)}</h1><div>Product Code: {html.escape(product_code)} ｜ RUN_ID: {html.escape(run_id)} ｜ Generated: {html.escape(generated_at)}</div></header><main>{"".join(sections)}</main></body></html>'


def build_outputs(product_root: str | Path, product_code: str, inputs: Mapping[str, Any], decisions: Mapping[str, Any]) -> dict[str, Path]:
    result = calculate(inputs["detail_rows"], inputs["summary_rows"], inputs["mapping_rows"], decisions,
                       inputs.get("benchmark_identities"))
    context = new_run_context("6-0-6", SKILL_ID, product_code)
    skill_dir = Path(__file__).resolve().parents[1]
    out_dir = resolve_skill_report_dir(product_root, skill_dir)
    definitions = {
        "occupancy": ("对标意图市场占领明细", "csv", OCCUPANCY_COLUMNS, "BENCHMARK_INTENT_OCCUPANCY_DETAIL"),
        "consensus": ("意图多对标占领共识", "csv", CONSENSUS_COLUMNS, "BENCHMARK_INTENT_OCCUPANCY_CONSENSUS"),
        "html": ("对标意图市场占领分析报告", "html", None, "BENCHMARK_INTENT_OCCUPANCY_REPORT"),
    }
    paths = {key: out_dir / build_report_filename(skill_dir, name, context.run_timestamp, ext)
             for key, (name, ext, _, _) in definitions.items()}
    report_error = validate_hzp_amz_report_batch(list(paths.values()), product_root, skill_dir,
                                                 timestamp=context.run_timestamp)
    if report_error:
        raise ValueError(report_error)
    sidecars = [metadata_sidecar_path(path) for path in paths.values()]
    assert_new_outputs([*paths.values(), *sidecars])
    status = "INCOMPLETE" if result["rank_audit"] else "FULL_SUCCESS"
    benchmark_package = inputs.get("benchmark") or inputs.get("detail", {})
    benchmark_manifest = benchmark_package.get("manifest") or {}
    benchmark_files = (benchmark_package.get("files", {}).get("benchmarks")
                       or inputs.get("detail", {}).get("files")
                       or {"detail": inputs.get("detail", {}).get("file", "detail.csv")})
    per_benchmark_counts = benchmark_manifest.get("PerBenchmarkHighPrecisionRecordCount") or {}
    lineage = [{"Input_Skill": "hzp-amz-6-0-2-ai-precision-keyword-identification",
                "Input_Report_Identity": "BENCHMARK_HIGH_PRECISION_KEYWORDS",
                "Input_File_Name": Path(path).name, "Input_Run_ID": benchmark_package.get("run_id"),
                "Input_Run_Timestamp": benchmark_package.get("run_timestamp"),
                "Input_Record_Count": per_benchmark_counts.get(product_id, 0),
                "Input_Benchmark_Product_Code": product_id,
                "Input_Benchmark_Code": (benchmark_manifest.get("Benchmark Identities", {}).get(product_id, {}).get("对标编码")),
                "Input_Benchmark_ASIN": (benchmark_manifest.get("Benchmark Identities", {}).get(product_id, {}).get("对标ASIN")),
                "Input_Resolution_Method": "LATEST_VALID_602_3_PLUS_N_RUN_PACKAGE"}
               for product_id, path in benchmark_files.items()]
    for key in ("summary", "mapping"):
        asset = inputs[key]
        meta = asset.get("metadata") or {}
        lineage.append({"Input_Skill": meta.get("Skill_ID"), "Input_Report_Identity": meta.get("Report_Identity"),
                        "Input_File_Name": Path(asset["file"]).name, "Input_Run_ID": asset.get("run_id"),
                        "Input_Run_Timestamp": asset.get("run_timestamp"), "Input_Record_Count": asset.get("record_count"),
                        "Input_Resolution_Method": asset.get("input_resolution_method") or "LATEST_VALID_BUNDLE"})
    metadata_extra = {"Benchmark_Count": len(result["benchmarks"]), "Benchmark_Codes": result["benchmarks"],
                      "Benchmark_ASINs": [result["benchmark_asins"][c] for c in result["benchmarks"]],
                      "Input_Keyword_Count": result["input_keyword_count"],
                      "Input_Intent_Count": len(result["intent_rows"]), "Rank_Audit_Count": len(result["rank_audit"]),
                      "602_Input_Run_ID": benchmark_package.get("run_id"),
                      "602_Input_RUN_TIMESTAMP": benchmark_package.get("run_timestamp"),
                      "602_Input_Files": [Path(path).name for path in benchmark_files.values()],
                      "Input_Resolution_Method": "LATEST_VALID_602_3_PLUS_N_AND_SAME_RUN_603_BUNDLE"}
    _write_csv(paths["occupancy"], result["occupancy"], OCCUPANCY_COLUMNS)
    _write_csv(paths["consensus"], result["consensus"], CONSENSUS_COLUMNS)
    a_schema, a_rows = _read_asset_csv(paths["occupancy"])
    b_schema, b_rows = _read_asset_csv(paths["consensus"])
    if a_schema != list(OCCUPANCY_COLUMNS) or b_schema != list(CONSENSUS_COLUMNS):
        raise ValueError("606_OUTPUT_SCHEMA_INVALID")
    if len(a_rows) != len(result["occupancy"]) or len(b_rows) != len(result["consensus"]):
        raise ValueError("606_OUTPUT_COVERAGE_MISMATCH")
    a_keys = [(row["对标编码"], row["精准泛词"]) for row in a_rows]
    if len(a_keys) != len(set(a_keys)):
        raise ValueError("606_OUTPUT_COVERAGE_MISMATCH")
    a_for_rebuild = [dict(row, _valid_count=int(row["有效排名词数"])) for row in a_rows]
    rebuilt = derive_consensus_from_occupancy(a_for_rebuild, result["intent_rows"], result["benchmarks"])
    expected_by_intent = {row["精准泛词"]: row for row in rebuilt}
    for actual in b_rows:
        expected = expected_by_intent.get(actual["精准泛词"])
        if expected is None:
            raise ValueError("CONSENSUS_SOURCE_MISMATCH")
        if any(expected[field] != actual[field] for field in CONSENSUS_COLUMNS[10:13]):
            raise ValueError("BEST_BENCHMARK_TIEBREAK_MISMATCH")
        if any(str(expected[field]) != actual[field] for field in (*CONSENSUS_COLUMNS[5:10], *CONSENSUS_COLUMNS[13:15])):
            raise ValueError("CONSENSUS_SOURCE_MISMATCH")
    if len(expected_by_intent) != len(b_rows):
        raise ValueError("CONSENSUS_SOURCE_MISMATCH")
    render_result = {**result, "occupancy": a_rows, "consensus": b_rows}
    content = render_html(product_code, render_result, inputs, run_id=context.run_id, generated_at=context.generated_at)
    with paths["html"].open("x", encoding="utf-8", newline="") as stream:
        stream.write(content)
    for key, (_, _, schema, identity) in definitions.items():
        rows = result[key] if key != "html" else None
        metadata = make_artifact_metadata(context, identity, run_status=status, schema=schema,
                                          record_count=len(rows) if rows is not None else None,
                                          inputs=lineage, output_assets=[str(p) for p in paths.values()],
                                          extra=metadata_extra)
        write_metadata_sidecar(paths[key], metadata)
    return paths


def inspect(product_root: str | Path, product_code: str) -> dict[str, Any]:
    inputs = resolve_inputs(product_root, product_code)
    preview = calculate(inputs["detail_rows"], inputs["summary_rows"], inputs["mapping_rows"],
                        benchmark_identities=inputs.get("benchmark_identities"))
    return {"status": "INPUTS_VALID", "product_code": product_code,
            "602_benchmark_high_precision": {"files": (inputs.get("benchmark") or inputs["detail"]).get("files", {}).get("benchmarks"),
                                              "run_id": (inputs.get("benchmark") or inputs["detail"]).get("run_id"),
                                              "run_timestamp": (inputs.get("benchmark") or inputs["detail"]).get("run_timestamp"),
                                              "count": len(inputs["detail_rows"])},
            "603_summary": {"file": inputs["summary"]["file"], "run_id": inputs["summary"].get("run_id"), "count": len(inputs["summary_rows"])},
            "603_mapping": {"file": inputs["mapping"]["file"], "run_id": inputs["mapping"].get("run_id"), "count": len(inputs["mapping_rows"])},
            "benchmark_codes": preview["benchmarks"], "benchmark_asins": preview["benchmark_asins"],
            "keyword_count": preview["input_keyword_count"], "intent_count": len(preview["intent_rows"]),
            "rank_audit_count": len(preview["rank_audit"]),
            "calculated_occupancy_evidence": [{k: v for k, v in row.items() if not k.startswith("_") and k not in {"占领等级", "占领判断原因"}} for row in preview["occupancy"]],
            "calculated_consensus_evidence": [{k: v for k, v in row.items() if k not in {"多对标共识等级", "共识判断原因"}} for row in preview["consensus"]],
            "required_decisions": {"occupancy": [{"对标编码": c, "精准泛词": i} for c in preview["benchmarks"] for i in preview["intent_rows"]],
                                   "consensus": [{"精准泛词": i} for i in preview["intent_rows"]]}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "build"):
        p = sub.add_parser(command)
        p.add_argument("--product-root", required=True)
        p.add_argument("--product-code", required=True)
        if command == "build":
            p.add_argument("--decisions", required=True)
    args = parser.parse_args(argv)
    try:
        inputs = resolve_inputs(args.product_root, args.product_code)
        if args.command == "inspect":
            print(json.dumps(inspect(args.product_root, args.product_code), ensure_ascii=False, indent=2))
        else:
            with Path(args.decisions).open("r", encoding="utf-8-sig") as stream:
                decisions = json.load(stream)
            result = calculate(inputs["detail_rows"], inputs["summary_rows"], inputs["mapping_rows"], decisions,
                               inputs.get("benchmark_identities"))
            paths = build_outputs(args.product_root, args.product_code, inputs, decisions)
            print(json.dumps({"status": "INCOMPLETE" if result["rank_audit"] else "FULL_SUCCESS",
                              "outputs": {key: str(path) for key, path in paths.items()}}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
