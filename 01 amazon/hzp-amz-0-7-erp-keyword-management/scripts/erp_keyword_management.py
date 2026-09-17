"""Safe, provider-agnostic PickKw KeywordCn management kernel for 0-7.

No database connection or credentials are embedded here. A real provider must
implement the small interface and explicitly opt in before writes.
"""
from __future__ import annotations
import csv, html, json, re, sys
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Any

SKILLS_ROOT = Path(__file__).resolve().parents[2]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))
from scripts.hzp_amz_report_contract import governance_paths, publish_latest_valid_batch, publish_latest_html

STATUSES = {
    "UPDATED_VERIFIED", "SKIP_ALREADY_TRANSLATED", "SKIP_CONCURRENTLY_FILLED",
    "SOURCE_KEYWORD_EMPTY", "SOURCE_KEYWORD_CHANGED",
    "TRANSLATION_VALIDATION_FAILED", "ERP_WRITE_FAILED",
    "READBACK_MISMATCH", "WRITE_BLOCKED", "DRY_RUN_PROPOSED",
}
ID_FIELD = "Id"
FIELDS = ["Id","Keyword","OriginalKeywordCn","ProposedKeywordCn",
          "FinalKeywordCn","Action","ResultStatus","FailureReason"]

def choose_page_size(estimated_rows: int | None = None) -> int:
    if estimated_rows is None:
        return 500
    if estimated_rows <= 1000:
        return max(100, estimated_rows or 100)
    if estimated_rows <= 10000:
        return 500
    if estimated_rows <= 100000:
        return 1000
    return 2000

def canonical_keyword(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())

def is_missing_cn(value: Any) -> bool:
    return value is None or not str(value).strip()

def validate_translation(keyword: str, proposed: Any, max_length: int = 255) -> tuple[bool, str]:
    text = str(proposed or "").strip()
    if not text:
        return False, "TRANSLATION_EMPTY"
    if len(text) > max_length:
        return False, "TRANSLATION_TOO_LONG"
    if "\n" in text or "\r" in text:
        return False, "TRANSLATION_MULTILINE"
    if re.search(r"[{}<>\[\]]", text):
        return False, "TRANSLATION_FORMAT_FRAGMENT"
    if re.match(r"(?i)^(translation|译文|中文)\s*[:：]", text):
        return False, "TRANSLATION_EXPLANATION"
    if re.match(r"^\s*(\d+[.)、]|[-*])\s+", text):
        return False, "TRANSLATION_LIST_ITEM"
    if canonical_keyword(keyword) == canonical_keyword(text):
        return False, "TRANSLATION_COPIES_SOURCE"
    return True, ""

@dataclass
class ResultRow:
    Id: str
    Keyword: str
    OriginalKeywordCn: str
    ProposedKeywordCn: str
    FinalKeywordCn: str
    Action: str
    ResultStatus: str
    FailureReason: str

class PickKwProvider:
    """Adapter contract. Implement with the repository's approved ERP client."""

    writer_verified = False

    def scan_missing(self, page_size: int = 100) -> Iterable[Mapping[str, Any]]:
        raise NotImplementedError

    def read(self, record_id: str) -> Mapping[str, Any]:
        raise NotImplementedError

    def compare_and_apply(self, record_id: str, expected_keyword: str,
                          expected_cn_missing: bool, proposed_cn: str) -> str:
        raise NotImplementedError

    def readback(self, record_id: str) -> Mapping[str, Any]:
        raise NotImplementedError

class MockPickKwProvider(PickKwProvider):
    """Keyset-paginated test provider; update payload is KeywordCn only."""

    writer_verified = True
    def __init__(self, records: Iterable[Mapping[str, Any]], page_size: int = 2):
        self.records = {str(r["Id"]): dict(r) for r in records}
        self.page_size = page_size
        self.updated_fields: list[set[str]] = []
        self.concurrent_fill: dict[str, str] = {}
        self.change_keyword: dict[str, str] = {}
        self.read_count = 0

    def scan_missing(self, page_size: int = 100):
        ids = sorted(self.records, key=lambda x: (str(x)))
        for i in range(0, len(ids), self.page_size or page_size):
            for rid in ids[i:i + (self.page_size or page_size)]:
                row = self.records[rid]
                # Candidate pages may include already translated rows so the
                # run can audit and count the non-overwrite decision.
                yield dict(row)

    def read(self, record_id):
        self.read_count += 1
        row = dict(self.records[str(record_id)])
        if str(record_id) in self.concurrent_fill:
            row["KeywordCn"] = self.concurrent_fill.pop(str(record_id))
        if str(record_id) in self.change_keyword:
            row["Keyword"] = self.change_keyword.pop(str(record_id))
        self.records[str(record_id)] = dict(row)
        return row

    def compare_and_apply(self, record_id, expected_keyword, expected_cn_missing, proposed_cn):
        row = self.records[str(record_id)]
        if row.get("Keyword") != expected_keyword:
            return "SOURCE_KEYWORD_CHANGED"
        if not is_missing_cn(row.get("KeywordCn")):
            return "SKIP_CONCURRENTLY_FILLED"
        self.updated_fields.append({"KeywordCn"})
        row["KeywordCn"] = proposed_cn
        return "APPLIED"

    def readback(self, record_id):
        return dict(self.records[str(record_id)])

class TranslationCache:
    def __init__(self, translator: Callable[[str], str]):
        self.translator = translator
        self.values: dict[str, str] = {}
        self.calls = 0

    def translate(self, keyword: str) -> str:
        key = canonical_keyword(keyword)
        if key not in self.values:
            self.calls += 1
            self.values[key] = self.translator(keyword)
        return self.values[key]

def process(provider: PickKwProvider, translator: Callable[[str], str],
            dry_run: bool = True, max_length: int = 255,
            run_id: str | None = None, scope: Mapping[str, Any] | None = None,
            estimated_rows: int | None = None) -> dict[str, Any]:
    if not scope:
        raise ValueError("UPDATE_SCOPE_REQUIRED")
    try:
        limit = int(scope.get("Limit", 0))
    except (TypeError, ValueError):
        limit = 0
    if limit <= 0:
        raise ValueError("UPDATE_LIMIT_REQUIRED")
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cache = TranslationCache(translator)
    rows: list[ResultRow] = []
    eligible = 0
    page_size = choose_page_size(estimated_rows)
    for src in provider.scan_missing(page_size=page_size):
        rid = str(src.get(ID_FIELD, ""))
        keyword = str(src.get("Keyword") or "")
        original_cn = "" if src.get("KeywordCn") is None else str(src.get("KeywordCn"))
        if not is_missing_cn(src.get("KeywordCn")):
            rows.append(ResultRow(rid, keyword, original_cn, "", original_cn,
                                  "NONE", "SKIP_ALREADY_TRANSLATED", "KeywordCn已有内容"))
            continue
        if not keyword.strip():
            rows.append(ResultRow(rid, keyword, original_cn, "", original_cn,
                                  "NONE", "SOURCE_KEYWORD_EMPTY", "Keyword为空"))
            continue
        eligible += 1
        proposed = cache.translate(keyword)
        ok, reason = validate_translation(keyword, proposed, max_length)
        if not ok:
            rows.append(ResultRow(rid, keyword, original_cn, str(proposed or ""),
                                  original_cn, "NONE", "TRANSLATION_VALIDATION_FAILED", reason))
            if eligible >= limit:
                break
            continue
        if not dry_run and not provider.writer_verified:
            rows.append(ResultRow(rid, keyword, original_cn, proposed, original_cn,
                                  "NONE", "WRITE_BLOCKED", "PickKw.KeywordCn Writer未验证"))
            if eligible >= limit:
                break
            continue
        if dry_run:
            rows.append(ResultRow(rid, keyword, original_cn, proposed, original_cn,
                                  "PROPOSE", "DRY_RUN_PROPOSED", ""))
            if eligible >= limit:
                break
            continue
        live = provider.read(rid)
        if live.get("Keyword") != keyword:
            rows.append(ResultRow(rid, keyword, original_cn, proposed, str(live.get("KeywordCn") or ""),
                                  "NONE", "SOURCE_KEYWORD_CHANGED", "Keyword在写入前变化"))
            if eligible >= limit:
                break
            continue
        if not is_missing_cn(live.get("KeywordCn")):
            rows.append(ResultRow(rid, keyword, original_cn, proposed, str(live.get("KeywordCn")),
                                  "NONE", "SKIP_CONCURRENTLY_FILLED", "KeywordCn已被填充"))
            if eligible >= limit:
                break
            continue
        result = provider.compare_and_apply(rid, keyword, True, proposed)
        if result != "APPLIED":
            rows.append(ResultRow(rid, keyword, original_cn, proposed, str(live.get("KeywordCn") or ""),
                                  "NONE", result if result in STATUSES else "ERP_WRITE_FAILED", result))
            if eligible >= limit:
                break
            continue
        final = provider.readback(rid)
        final_cn = str(final.get("KeywordCn") or "")
        status = "UPDATED_VERIFIED" if final_cn == proposed else "READBACK_MISMATCH"
        rows.append(ResultRow(rid, keyword, original_cn, proposed, final_cn,
                              "UPDATE" if status == "UPDATED_VERIFIED" else "NONE", status,
                              "" if status == "UPDATED_VERIFIED" else "读回值不一致"))
        if eligible >= limit:
            break
    stats = Counter(r.ResultStatus for r in rows)
    stats.update({"scanned": len(rows), "translation_requests": cache.calls,
                  "translation_cache_hits": max(0, sum(1 for r in rows if r.ProposedKeywordCn) - cache.calls)})
    if not dry_run and not provider.writer_verified:
        stats["write_blocked"] = sum(1 for r in rows if r.ResultStatus == "WRITE_BLOCKED")
    return {"RunId": run_id, "Rows": rows, "Stats": dict(stats), "DryRun": dry_run,
            "Scope": {**dict(scope), "DataSource": "PickKw", "Limit": limit},
            "PageSize": page_size}

def write_csv(path: str | Path, rows: Iterable[ResultRow]) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
        for row in rows: w.writerow(asdict(row))

def render_html(product_code: str, result: Mapping[str, Any]) -> str:
    counts = html.escape(json.dumps(result["Stats"], ensure_ascii=False))
    scope = html.escape(json.dumps(result["Scope"], ensure_ascii=False))
    trs = "".join("<tr>" + "".join(f"<td>{html.escape(str(getattr(r, k)))}</td>" for k in FIELDS) + "</tr>"
                  for r in result["Rows"])
    heads = "".join(f"<th>{html.escape(k)}</th>" for k in FIELDS)
    return f"<!doctype html><meta charset='utf-8'><title>0-7 ERP关键词管理</title><h1>0-7｜ERP关键词管理｜{html.escape(product_code)}</h1><p>Run ID: {html.escape(result['RunId'])}｜Dry Run: {result['DryRun']}｜Page Size: {result['PageSize']}</p><p>Scope: <code>{scope}</code></p><pre>{counts}</pre><table border='1'><thead><tr>{heads}</tr></thead><tbody>{trs}</tbody></table>"

def write_report(product_root: str | Path, product_code: str, result: Mapping[str, Any],
                 generated_at: datetime | None = None) -> dict[str, Path]:
    dt = generated_at or datetime.now()
    stamp = dt.strftime("%Y%m%d_%H%M%S"); human = dt.strftime("%Y-%m-%d_%H%M%S")
    base = (Path(product_root) / "01_公共资料" / "0-7_ERP关键词管理"
            if product_code == "ALL_PICKKW"
            else Path(product_root) / "06_SKILL分析报告" / "0-7_ERP关键词管理")
    dirs = governance_paths(base)
    build_dir = dirs["staging"] / f"{stamp}_build"
    build_dir.mkdir(parents=True, exist_ok=False)
    csv_path = build_dir / f"0-7_关键词翻译更新结果_{stamp}.csv"
    latest_path = build_dir / f"0-7_ERP关键词管理报告_最新_{human}.html"
    write_csv(csv_path, result["Rows"])
    content = render_html(product_code, result)
    latest_path.write_text(content, encoding="utf-8")
    manifest_path = build_dir / f"0-7_RunPackage_{stamp}.json"
    manifest_path.write_text(json.dumps(
        {"RunId": result["RunId"], "ProductCode": product_code, "GeneratedAt": dt.isoformat(),
         "DryRun": result["DryRun"], "Scope": result["Scope"],
         "PageSize": result["PageSize"], "Stats": result["Stats"], "RUN_TIMESTAMP": stamp,
         "Run_Status": "VALID", "Output_Assets": [csv_path.name, latest_path.name]}, ensure_ascii=False, indent=2), encoding="utf-8")
    published = publish_latest_valid_batch(
        base, stamp, [csv_path], manifest_files=[manifest_path],
        registry_payload={"Skill_ID": "hzp-amz-0-7-erp-keyword-management", "Product_Code": product_code,
                          "RUN_ID": result["RunId"], "RUN_TIMESTAMP": stamp, "Files": [csv_path.name]},
        move_sources=True,
    )
    publish_latest_html(latest_path, base)
    import shutil
    shutil.rmtree(build_dir, ignore_errors=True)
    return {"csv": Path(published["data_dir"]) / csv_path.name,
            "history_html": base / "历史HTML",
            "latest_html": base / latest_path.name}
