"""Extract compact precision broad seeds from the 6-0-1 AI precision CSV."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

MISSING_INPUT = "6-0-1_AI_PRECISION_KEYWORD_INPUT_MISSING"
OUTPUT_DIR = "6-0-2_精准泛词提取"
AI_NAME = "6-0-1_{product_code}_AI精准词.csv"
BROAD_NAME = "6-0-2_{product_code}_精准泛词.csv"
BROAD_COLUMNS = ("词", "中文", "同意思词的合并总量")
STOP_WORDS = {"a", "an", "and", "for", "from", "in", "of", "on", "the", "to", "with"}
OPTIONAL_MODIFIERS = {"best", "better", "buy", "cute", "great", "idea", "ideas", "unique", "perfect", "present", "presents"}
SCENARIO_ANCHORS = {"birthday", "christmas", "graduation", "mother", "mothers", "wedding", "anniversary", "retirement", "thanksgiving", "valentine", "valentines"}
DUPLICATE_KEYWORD_VOLUME_CONFLICT = "[DUPLICATE_KEYWORD_VOLUME_CONFLICT]"


def input_paths(product_root: str | Path, product_code: str) -> dict[str, Path]:
    directory = Path(product_root) / "06_SKILL分析报告" / "6-0-1_精准关键词识别"
    return {"ai": directory / AI_NAME.format(product_code=product_code)}


def output_paths(product_root: str | Path, product_code: str) -> dict[str, Path]:
    directory = Path(product_root) / "06_SKILL分析报告" / OUTPUT_DIR
    return {"broad": directory / BROAD_NAME.format(product_code=product_code)}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_6_0_1_inputs(product_root: str | Path, product_code: str) -> list[dict[str, str]]:
    path = input_paths(product_root, product_code)["ai"]
    if not path.exists():
        raise FileNotFoundError(f"{MISSING_INPUT}: {path}")
    rows = read_csv(path)
    required = {"自动编号", "关键词", "搜索量", "中文名称", "精准理由", "精准度"}
    if rows and not required.issubset(rows[0]):
        raise ValueError(f"{MISSING_INPUT}: invalid 6-0-1 six-column contract")
    return rows


def _tokens(keyword: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:['-][a-z0-9]+)?", keyword.lower())


def _intent_tokens(keyword: str) -> frozenset[str]:
    tokens = set(_tokens(keyword)) - STOP_WORDS
    return frozenset(tokens - OPTIONAL_MODIFIERS)


def _group_key(keyword: str) -> tuple[frozenset[str], frozenset[str]]:
    intent = _intent_tokens(keyword)
    return intent & SCENARIO_ANCHORS, intent - SCENARIO_ANCHORS


def _volume(value: Any) -> float | None:
    if value in (None, "", "NULL", "DATA_NOT_AVAILABLE"):
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _format_volume(value: float | None) -> Any:
    if value in {DUPLICATE_KEYWORD_VOLUME_CONFLICT}:
        return DUPLICATE_KEYWORD_VOLUME_CONFLICT
    if value is None:
        return "DATA_NOT_AVAILABLE"
    return int(value) if value.is_integer() else round(value, 2)


def _dedupe_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        keyword = str(row.get("关键词") or "").strip()
        key = " ".join(_tokens(keyword))
        if not key:
            continue
        volume = _volume(row.get("搜索量"))
        current = unique.get(key)
        if current is None:
            unique[key] = {"keyword": keyword, "cn": str(row.get("中文名称") or "").strip(), "volume": volume, "volume_conflict": False}
        elif current["volume"] is None and volume is not None:
            current["volume"] = volume
        elif current["volume"] is not None and volume is not None and current["volume"] != volume:
            current["volume_conflict"] = True
        # Same-keyword duplicate IDs are one semantic keyword. Conflicting
        # volumes are retained as an explicit conflict and never summed.
    return list(unique.values())


def extract_broad_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique = _dedupe_rows(rows)
    groups: dict[tuple[frozenset[str], frozenset[str]], list[dict[str, Any]]] = {}
    for row in unique:
        groups.setdefault(_group_key(row["keyword"]), []).append(row)
    output: list[dict[str, Any]] = []
    for members in groups.values():
        representative = sorted(members, key=lambda item: (len(_tokens(item["keyword"])), item["keyword"].lower()))[0]
        if len(_tokens(representative["keyword"])) < 2:
            continue
        known = [item["volume"] for item in members if item["volume"] is not None]
        has_volume_conflict = any(item.get("volume_conflict") for item in members)
        total = DUPLICATE_KEYWORD_VOLUME_CONFLICT if has_volume_conflict else (sum(known) if known else None)
        chinese = representative["cn"] or next((item["cn"] for item in members if item["cn"]), "DATA_NOT_AVAILABLE")
        output.append({"词": representative["keyword"], "中文": chinese, "同意思词的合并总量": _format_volume(total)})
    return sorted(output, key=lambda row: (row["同意思词的合并总量"] in {"DATA_NOT_AVAILABLE", DUPLICATE_KEYWORD_VOLUME_CONFLICT}, -(float(row["同意思词的合并总量"]) if row["同意思词的合并总量"] not in {"DATA_NOT_AVAILABLE", DUPLICATE_KEYWORD_VOLUME_CONFLICT} else 0), row["词"]))


def write_csv(path: str | Path, rows: Iterable[Mapping[str, Any]], columns: Iterable[str] = BROAD_COLUMNS) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return target


def run(product_root: str | Path, product_code: str) -> Path:
    return write_csv(output_paths(product_root, product_code)["broad"], extract_broad_rows(load_6_0_1_inputs(product_root, product_code)))
