from __future__ import annotations

import csv
import html
import io
import re
import shutil
import statistics
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence


DEFAULT_PRODUCTS_ROOT = Path(r"E:\【所有产品目录专用】")
PRODUCT_AREAS = ("03_已上架产品", "02_新品待开发", "00_OtherSPro")
REPORT_DIR_NAME = "6-0-2_AI精准关键词识别"
SOURCE_601_DIR = "6-0-1_对标自然排名关键词提取"
SOURCE_601_IDENTITY = "6-0-1_05_所有对标自然排名关键词"
UNIQUE_REPORT_IDENTITY = "去对标去重_筛选后的精准词"
UNIQUE_REPORT_KEY = "UNIQUE_SELECTED_PRECISION_KEYWORDS"
BENCHMARK_REPORT_KEY = "BENCHMARK_SELECTED_PRECISION_KEYWORDS"
PRECISION_LEVELS = ("高度精准", "精准", "弱精准", "不精准")
JUDGMENT_FIELDS = (
    "KeywordId", "CanonicalKeyword", "SearcherPurchaseMission", "MissionFit", "HardConflict",
    "InitialPrecision", "BenchmarkReality", "DecisionChallenge",
    "FinalPrecision", "ShortReason",
)
OBSERVATION_COLUMNS = (
    "所属产品编号", "对标ASIN", "Id", "词", "中文", "市场容量",
    "竞争产品数", "供需比", "自然排名", "精准度", "精准原因",
)
UNIQUE_COLUMNS = (
    "Id", "词", "中文", "市场容量", "竞争产品数", "供需比",
    "对标覆盖数", "最佳自然排名", "自然排名中位数", "精准度", "精准原因",
)
REQUIRED_601_COLUMNS = {"Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "自然排名"}
TIMESTAMP_RE = re.compile(r"(?P<ts>\d{8}_\d{6})")
SEQUENCE_RE = re.compile(r"^6-0-2_(?P<seq>\d{3})_")


class PrecisionContractError(ValueError):
    pass


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        return fields, [dict(row) for row in reader]


def _write_csv(path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def locate_product_root(product_code: str, products_root: Path = DEFAULT_PRODUCTS_ROOT) -> Path:
    code = product_code.strip()
    if not code:
        raise PrecisionContractError("PRODUCT_CODE_EMPTY")
    pattern = re.compile(rf"^{re.escape(code)}(?:$|[\s_-])", re.IGNORECASE)
    matches: list[Path] = []
    for area in PRODUCT_AREAS:
        area_path = Path(products_root) / area
        if area_path.is_dir():
            matches.extend(path for path in area_path.iterdir() if path.is_dir() and pattern.match(path.name))
    if not matches:
        raise PrecisionContractError(f"PRODUCT_ROOT_NOT_FOUND: {code}")
    if len(matches) != 1:
        raise PrecisionContractError(f"PRODUCT_ROOT_AMBIGUOUS: {code}: {matches}")
    return matches[0]


def _validate_601_schema(path: Path) -> None:
    fields, rows = _read_csv(path)
    missing = REQUIRED_601_COLUMNS.difference(fields)
    if missing:
        raise PrecisionContractError(f"601_INPUT_SCHEMA_INVALID: missing={sorted(missing)}")
    if not ({"所属产品编号", "产品编号", "对标编号"} & set(fields)):
        raise PrecisionContractError("601_INPUT_SCHEMA_INVALID: benchmark code missing")
    if not ({"对标ASIN", "ASIN"} & set(fields)):
        raise PrecisionContractError("601_INPUT_SCHEMA_INVALID: benchmark ASIN missing")
    if not rows:
        raise PrecisionContractError("601_INPUT_EMPTY")


def resolve_latest_601(product_root: Path) -> Path:
    base = Path(product_root) / "06_SKILL分析报告" / SOURCE_601_DIR
    candidates: list[tuple[str, Path]] = []
    exact = re.compile(rf"^{re.escape(SOURCE_601_IDENTITY)}_(\d{{8}}_\d{{6}})\.csv$")
    for folder in (base, base / "data", base / "历史数据"):
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            match = exact.match(path.name)
            if path.is_file() and match:
                candidates.append((match.group(1), path))
    if not candidates:
        raise PrecisionContractError("601_INPUT_NOT_FOUND")
    path = max(candidates, key=lambda item: (item[0], item[1].name))[1]
    _validate_601_schema(path)
    return path


def locate_inputs(product_code: str, products_root: Path = DEFAULT_PRODUCTS_ROOT) -> dict[str, Path]:
    root = locate_product_root(product_code, products_root)
    product_text = root / "05_分析源数据" / "01_产品数据" / "本产品" / "产品识别 - 文本文案.txt"
    selection = Path(products_root) / "01_公共资料" / "03_系统配置" / "生成精准词库的要求.txt"
    if not product_text.is_file():
        raise PrecisionContractError("CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND")
    if not selection.is_file():
        raise PrecisionContractError("PRECISION_SELECTION_CONFIG_NOT_FOUND")
    return {
        "product_root": root,
        "product_text": product_text,
        "input_601": resolve_latest_601(root),
        "selection_config": selection,
        "batch_config": Path(products_root) / "01_公共资料" / "03_系统配置" / "602_AI批次大小.txt",
        "report_dir": root / "06_SKILL分析报告" / REPORT_DIR_NAME,
    }


def load_product_text(path: Path) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8-sig").strip()
    except OSError as exc:
        raise PrecisionContractError(f"CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED: {exc}") from exc
    if not text:
        raise PrecisionContractError("CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY")
    return text


def load_601(path: Path) -> list[dict[str, str]]:
    _validate_601_schema(Path(path))
    _, rows = _read_csv(Path(path))
    normalized: list[dict[str, str]] = []
    for index, row in enumerate(rows, 1):
        benchmark_code = next((row.get(key, "").strip() for key in ("所属产品编号", "产品编号", "对标编号") if row.get(key, "").strip()), "")
        asin = next((row.get(key, "").strip() for key in ("对标ASIN", "ASIN") if row.get(key, "").strip()), "")
        keyword = row.get("词", "").strip()
        if not benchmark_code or not asin or not keyword or not row.get("Id", "").strip():
            raise PrecisionContractError(f"601_INPUT_ROW_INVALID: row={index}")
        normalized.append({
            "所属产品编号": benchmark_code,
            "对标ASIN": asin,
            "Id": row["Id"].strip(),
            "词": keyword,
            "中文": row.get("中文", "").strip(),
            "市场容量": row.get("市场容量", "").strip(),
            "竞争产品数": row.get("竞争产品数", "").strip(),
            "供需比": row.get("供需比", "").strip(),
            "自然排名": row.get("自然排名", "").strip(),
        })
    return normalized


def canonicalize_keyword(keyword: str) -> str:
    value = unicodedata.normalize("NFKC", keyword).casefold()
    return re.sub(r"\s+", " ", value).strip()


def _rank_number(value: object) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def prepare_unique_keyword_evidence(observations: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    groups: dict[str, list[Mapping[str, str]]] = {}
    for row in observations:
        canonical = canonicalize_keyword(row["词"])
        if not canonical:
            raise PrecisionContractError("CANONICAL_KEYWORD_EMPTY")
        keyword_id = str(row["Id"])
        groups.setdefault(keyword_id, []).append(row)
    result: list[dict[str, object]] = []
    fact_fields = ("Id", "市场容量", "竞争产品数", "供需比")
    for keyword_id, rows in groups.items():
        canonical_values = {canonicalize_keyword(row["词"]) for row in rows}
        if len(canonical_values) != 1:
            raise PrecisionContractError(f"KEYWORD_ID_TEXT_CONFLICT: {keyword_id}")
        canonical = next(iter(canonical_values))
        for field in fact_fields:
            values = {row.get(field, "") for row in rows}
            if len(values) != 1:
                raise PrecisionContractError(f"KEYWORD_MARKET_FACT_CONFLICT: {canonical}: {field}")
        ranks = [rank for rank in (_rank_number(row.get("自然排名")) for row in rows) if rank is not None]
        result.append({
            "CanonicalKeyword": canonical,
            "Id": keyword_id,
            "Keyword": rows[0]["词"],
            "KeywordCn": next((row.get("中文", "") for row in rows if row.get("中文", "")), "DATA_NOT_AVAILABLE"),
            "MarketCapacity": rows[0].get("市场容量", ""),
            "CompetingProducts": rows[0].get("竞争产品数", ""),
            "SupplyDemandRatio": rows[0].get("供需比", ""),
            "BenchmarkCoverageCount": len({row["所属产品编号"] for row in rows}),
            "BestOrganicRank": min(ranks) if ranks else "DATA_NOT_AVAILABLE",
            "MedianOrganicRank": statistics.median(ranks) if ranks else "DATA_NOT_AVAILABLE",
            "BenchmarkObservations": [dict(row) for row in rows],
        })
    return result


def read_preferred_batch_size(path: Path) -> int:
    if not Path(path).is_file():
        raise PrecisionContractError("602_BATCH_SIZE_CONFIG_MISSING")
    raw = Path(path).read_text(encoding="utf-8-sig").strip()
    if not re.fullmatch(r"[1-9]\d*", raw):
        raise PrecisionContractError("602_BATCH_SIZE_CONFIG_INVALID")
    return int(raw)


def read_precision_selection_config(path: Path) -> tuple[str, ...]:
    if not Path(path).is_file():
        raise PrecisionContractError("PRECISION_SELECTION_CONFIG_NOT_FOUND")
    aliases = {"已精准": "精准"}
    selected: list[str] = []
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        value = aliases.get(raw.strip(), raw.strip())
        if value in PRECISION_LEVELS and value not in selected:
            selected.append(value)
    if not selected:
        raise PrecisionContractError("PRECISION_SELECTION_CONFIG_INVALID")
    return tuple(selected)


def validate_ai_judgments(unique_rows: Sequence[Mapping[str, object]], judgments: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    expected = {str(row["Id"]) for row in unique_rows}
    validated: dict[str, dict[str, object]] = {}
    for index, judgment in enumerate(judgments, 1):
        missing = [field for field in JUDGMENT_FIELDS if field not in judgment]
        if missing:
            raise PrecisionContractError(f"AI_JUDGMENT_SCHEMA_INVALID: row={index}: missing={missing}")
        keyword_id = str(judgment["KeywordId"]).strip()
        canonical = canonicalize_keyword(str(judgment["CanonicalKeyword"]))
        if keyword_id in validated:
            raise PrecisionContractError(f"AI_JUDGMENT_DUPLICATE: {keyword_id}")
        if judgment["FinalPrecision"] not in PRECISION_LEVELS or judgment["InitialPrecision"] not in PRECISION_LEVELS:
            raise PrecisionContractError(f"AI_JUDGMENT_LEVEL_INVALID: {canonical}")
        if not str(judgment["ShortReason"]).strip():
            raise PrecisionContractError(f"AI_JUDGMENT_REASON_EMPTY: {canonical}")
        validated[keyword_id] = dict(judgment, KeywordId=keyword_id, CanonicalKeyword=canonical)
    missing = expected.difference(validated)
    extra = set(validated).difference(expected)
    if missing or extra:
        raise PrecisionContractError(f"AI_JUDGMENT_COVERAGE_MISMATCH: missing={len(missing)} extra={len(extra)}")
    return validated


def build_all_observation_output(observations: Sequence[Mapping[str, str]], judgments: Mapping[str, Mapping[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in observations:
        judgment = judgments[str(source["Id"])]
        rows.append(dict(source, 精准度=judgment["FinalPrecision"], 精准原因=judgment["ShortReason"]))
    return rows


def build_dedup_selected_output(unique_rows: Sequence[Mapping[str, object]], judgments: Mapping[str, Mapping[str, object]], selected_levels: Iterable[str]) -> list[dict[str, object]]:
    selected = set(selected_levels)
    rows: list[dict[str, object]] = []
    for source in unique_rows:
        judgment = judgments[str(source["Id"])]
        if judgment["FinalPrecision"] not in selected:
            continue
        rows.append({
            "Id": source["Id"], "词": source["Keyword"], "中文": source["KeywordCn"],
            "市场容量": source["MarketCapacity"], "竞争产品数": source["CompetingProducts"],
            "供需比": source["SupplyDemandRatio"], "对标覆盖数": source["BenchmarkCoverageCount"],
            "最佳自然排名": source["BestOrganicRank"], "自然排名中位数": source["MedianOrganicRank"],
            "精准度": judgment["FinalPrecision"], "精准原因": judgment["ShortReason"],
        })
    return rows


def build_benchmark_selected_outputs(all_rows: Sequence[Mapping[str, object]], selected_levels: Iterable[str]) -> dict[str, list[dict[str, object]]]:
    selected = set(selected_levels)
    grouped: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    for row in all_rows:
        code = str(row["所属产品编号"])
        grouped[code]
        if row["精准度"] not in selected:
            continue
        canonical = canonicalize_keyword(str(row["词"]))
        current = grouped[code].get(canonical)
        if current is None:
            grouped[code][canonical] = dict(row)
        else:
            old_rank, new_rank = _rank_number(current.get("自然排名")), _rank_number(row.get("自然排名"))
            if new_rank is not None and (old_rank is None or new_rank < old_rank):
                grouped[code][canonical] = dict(row)
    return {code: list(rows.values()) for code, rows in sorted(grouped.items())}


def allocate_run_sequence(report_dir: Path) -> int:
    maximum = 0
    for folder in (Path(report_dir), Path(report_dir) / "历史数据", Path(report_dir) / "历史html"):
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            match = SEQUENCE_RE.match(path.name)
            if path.is_file() and match:
                maximum = max(maximum, int(match.group("seq")))
    return maximum + 1


def archive_previous_run(report_dir: Path) -> list[Path]:
    root = Path(report_dir)
    archived: list[Path] = []
    for path in list(root.iterdir()) if root.is_dir() else []:
        if not path.is_file() or not SEQUENCE_RE.match(path.name):
            continue
        target_dir = root / ("历史html" if path.suffix.lower() == ".html" else "历史数据")
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / path.name
        if target.exists():
            raise PrecisionContractError(f"HISTORY_ARCHIVE_COLLISION: {target}")
        shutil.move(str(path), str(target))
        archived.append(target)
    return archived


def _render_html(product_code: str, input_601: Path, observations: Sequence[Mapping[str, object]], unique_rows: Sequence[Mapping[str, object]], all_rows: Sequence[Mapping[str, object]], selected_rows: Sequence[Mapping[str, object]], benchmark_rows: Mapping[str, Sequence[Mapping[str, object]]], selected_levels: Sequence[str], sequence: int, timestamp: str) -> str:
    counts = Counter(str(row["精准度"]) for row in all_rows)
    unique_counts = Counter(str(row["FinalPrecision"]) for row in unique_rows)
    samples_high = [row for row in selected_rows if row["精准度"] == "高度精准"][:12]
    samples_no = [row for row in all_rows if row["精准度"] == "不精准"][:12]
    def cards(items: Iterable[tuple[str, object]]) -> str:
        return "".join(f'<div class="card"><b>{html.escape(str(k))}</b><span>{html.escape(str(v))}</span></div>' for k, v in items)
    def table(rows: Sequence[Mapping[str, object]]) -> str:
        return "<table><thead><tr><th>词</th><th>中文</th><th>精准度</th><th>原因</th></tr></thead><tbody>" + "".join(
            f"<tr><td>{html.escape(str(r.get('词','')))}</td><td>{html.escape(str(r.get('中文','')))}</td><td>{html.escape(str(r.get('精准度','')))}</td><td>{html.escape(str(r.get('精准原因','')))}</td></tr>" for r in rows
        ) + "</tbody></table>"
    summary = [
        ("Current Product", product_code), ("Run Sequence", f"{sequence:03d}"),
        ("601输入", input_601.name), ("Benchmark数量", len(benchmark_rows)),
        ("Observation数量", len(observations)), ("Unique Keyword数量", len(unique_rows)),
        ("词库选择等级", " / ".join(selected_levels)), ("统一精准词数量", len(selected_rows)),
    ]
    distributions = [(level, unique_counts.get(level, 0)) for level in PRECISION_LEVELS]
    benchmark_summary = "".join(f"<tr><td>{html.escape(code)}</td><td>{len(rows)}</td></tr>" for code, rows in benchmark_rows.items())
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>6-0-2 AI精准关键词识别</title><style>
body{{font-family:Segoe UI,'Microsoft YaHei',sans-serif;margin:0;background:#f4f7fb;color:#182230}}main{{max-width:1440px;margin:auto;padding:28px}}h1{{margin:0 0 8px}}.meta{{color:#667085}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}.card{{background:#fff;border:1px solid #e4e7ec;border-radius:12px;padding:15px;display:flex;flex-direction:column;gap:8px}}.card span{{font-size:20px;font-weight:700}}section{{background:#fff;border:1px solid #e4e7ec;border-radius:14px;padding:20px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #eaecf0;text-align:left;vertical-align:top}}@media print{{body{{background:#fff}}section,.card{{break-inside:avoid}}}}
</style></head><body><main><h1>6-0-2｜AI精准关键词识别</h1><div class="meta">Generated {timestamp} · Organic Rank is Benchmark Reality Evidence, not Current Product rank.</div><div class="grid">{cards(summary)}</div><section><h2>四级精准度分布（Unique Keyword）</h2><div class="grid">{cards(distributions)}</div></section><section><h2>各Benchmark筛选词数量</h2><table><thead><tr><th>所属产品编号</th><th>词数</th></tr></thead><tbody>{benchmark_summary}</tbody></table></section><section><h2>代表性精准词</h2>{table(samples_high)}</section><section><h2>代表性不精准词</h2>{table(samples_no)}</section><section><h2>边界</h2><p>AI按购买任务判断精准度；搜索量与Benchmark自然排名不决定精准等级。报告不代表Current Product自然排名，也不执行ERP或广告写入。</p></section></main></body></html>"""


def validate_outputs(paths: Sequence[Path], expected_sequence: int, expected_timestamp: str, observation_count: int, selected_unique_count: int) -> None:
    prefix = f"6-0-2_{expected_sequence:03d}_"
    for path in paths:
        if not path.is_file() or not path.name.startswith(prefix) or expected_timestamp not in path.name:
            raise PrecisionContractError(f"OUTPUT_LINEAGE_INVALID: {path}")
    all_path = next(path for path in paths if "精准判断所有词表" in path.name)
    unique_path = next(path for path in paths if UNIQUE_REPORT_IDENTITY in path.name)
    _, all_rows = _read_csv(all_path)
    _, unique_rows = _read_csv(unique_path)
    if len(all_rows) != observation_count:
        raise PrecisionContractError("OUTPUT_OBSERVATION_COUNT_MISMATCH")
    if len(unique_rows) != selected_unique_count:
        raise PrecisionContractError("OUTPUT_UNIQUE_COUNT_MISMATCH")
    canonicals = [canonicalize_keyword(row["词"]) for row in unique_rows]
    if len(canonicals) != len(set(canonicals)):
        raise PrecisionContractError("OUTPUT_UNIQUE_DUPLICATE")


def publish_complete_run(product_code: str, product_root: Path, input_601: Path, observations: Sequence[Mapping[str, str]], unique_rows: Sequence[Mapping[str, object]], judgments: Sequence[Mapping[str, object]], selection_config: Path, now: datetime | None = None) -> dict[str, object]:
    validated = validate_ai_judgments(unique_rows, judgments)
    selected_levels = read_precision_selection_config(selection_config)
    all_rows = build_all_observation_output(observations, validated)
    selected_rows = build_dedup_selected_output(unique_rows, validated, selected_levels)
    benchmark_rows = build_benchmark_selected_outputs(all_rows, selected_levels)
    expected_benchmarks = {str(row["所属产品编号"]) for row in observations}
    if set(benchmark_rows) != expected_benchmarks:
        raise PrecisionContractError("BENCHMARK_OUTPUT_COVERAGE_MISMATCH")
    report_dir = Path(product_root) / "06_SKILL分析报告" / REPORT_DIR_NAME
    report_dir.mkdir(parents=True, exist_ok=True)
    sequence = allocate_run_sequence(report_dir)
    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    seq = f"{sequence:03d}"
    names = {
        "all": f"6-0-2_{seq}_精准判断所有词表_{timestamp}.csv",
        "unique": f"6-0-2_{seq}_{UNIQUE_REPORT_IDENTITY}_{timestamp}.csv",
        "html": f"6-0-2_{seq}_AI精准关键词识别_{timestamp}.html",
    }
    for code in benchmark_rows:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", code):
            raise PrecisionContractError(f"BENCHMARK_CODE_UNSAFE: {code}")
    output_paths: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="602_publish_") as tmp_name:
        tmp = Path(tmp_name)
        _write_csv(tmp / names["all"], OBSERVATION_COLUMNS, all_rows)
        _write_csv(tmp / names["unique"], UNIQUE_COLUMNS, selected_rows)
        for code, rows in benchmark_rows.items():
            _write_csv(tmp / f"6-0-2_{seq}_{code}_筛选后的精准词_{timestamp}.csv", OBSERVATION_COLUMNS, rows)
        html_text = _render_html(product_code, Path(input_601), observations, [dict(row, FinalPrecision=validated[str(row["Id"])]["FinalPrecision"]) for row in unique_rows], all_rows, selected_rows, benchmark_rows, selected_levels, sequence, timestamp)
        (tmp / names["html"]).write_text(html_text, encoding="utf-8")
        temp_paths = list(tmp.iterdir())
        validate_outputs(temp_paths, sequence, timestamp, len(observations), len(selected_rows))
        archive_previous_run(report_dir)
        for source in temp_paths:
            target = report_dir / source.name
            shutil.move(str(source), str(target))
            output_paths.append(target)
    validate_outputs(output_paths, sequence, timestamp, len(observations), len(selected_rows))
    return {
        "Status": "COMPLETE", "RunSequence": seq, "Timestamp": timestamp,
        "ObservationCount": len(observations), "UniqueKeywordCount": len(unique_rows),
        "SelectedUniqueCount": len(selected_rows), "BenchmarkCount": len(benchmark_rows),
        "SelectedLevels": selected_levels, "OutputPaths": output_paths,
        "603ReportIdentity": UNIQUE_REPORT_KEY,
        "606ReportIdentity": BENCHMARK_REPORT_KEY,
    }
