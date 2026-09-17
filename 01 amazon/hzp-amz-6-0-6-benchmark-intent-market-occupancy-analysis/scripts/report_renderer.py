"""Render a self-contained HTML snapshot from one 6-0-6 CSV pair."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any


def _e(value: Any) -> str:
    return html.escape(str(value if value not in (None, "") else "—"), quote=True)


def _n(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def read_embedded_snapshot(html_text: str) -> dict[str, Any]:
    match = re.search(
        r'<script type="application/json" id="same-run-csv-snapshot">(.*?)</script>',
        html_text, flags=re.DOTALL,
    )
    if not match:
        raise ValueError("HTML_DATA_RECONCILIATION_FAILED: embedded snapshot missing")
    try:
        result = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("HTML_DATA_RECONCILIATION_FAILED: embedded snapshot invalid") from exc
    if not isinstance(result, dict):
        raise ValueError("HTML_DATA_RECONCILIATION_FAILED: embedded snapshot is not an object")
    return result


def _table(headers: list[str], rows: list[list[Any]], *, empty: str = "没有符合条件的记录") -> str:
    if not rows:
        return f'<div class="empty">{_e(empty)}</div>'
    head = "".join(f"<th>{_e(value)}</th>" for value in headers)
    body = "".join("<tr>" + "".join(f"<td>{_e(value)}</td>" for value in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render_report(
    detail: list[dict[str, str]], consensus: list[dict[str, str]], output_path: Path,
    run_timestamp: str, lineage: dict[str, Any] | None = None,
) -> None:
    """Write the dashboard; all displayed business data comes from the two CSV readbacks."""
    lineage = lineage or {}
    benchmarks = sorted({row.get("对标编码", "") for row in detail if row.get("对标编码")})
    intents = sorted(consensus, key=lambda row: (-_n(row.get("汇总搜索量")), row.get("精准泛词", "")))
    high = [row for row in consensus if row.get("多对标共识等级") == "高共识"]
    single = [row for row in consensus if row.get("多对标共识等级") == "单点验证"]
    total_valid_observations = sum(int(row.get("有效排名词数") or 0) for row in detail)
    core_strong = sum(row.get("占领等级") in {"核心占领", "强占领"} for row in detail)

    benchmark_overview: list[list[Any]] = []
    for code in benchmarks:
        rows = [row for row in detail if row.get("对标编码") == code]
        core = sum(row.get("占领等级") == "核心占领" for row in rows)
        strong = sum(row.get("占领等级") == "强占领" for row in rows)
        focus = sorted(
            (row for row in rows if row.get("占领等级") in {"核心占领", "强占领"}),
            key=lambda row: (-_n(row.get("Top20搜索量覆盖率")), -_n(row.get("Top10搜索量覆盖率")), row.get("精准泛词", "")),
        )[:5]
        benchmark_overview.append([
            code, rows[0].get("对标ASIN", "") if rows else "", core, strong,
            "、".join(row.get("精准泛词", "") for row in focus) or "当前未见核心/强占领Intent",
        ])

    matrix_rows: list[list[Any]] = []
    for intent in intents:
        iname = intent.get("精准泛词", "")
        by_code = {row.get("对标编码"): row for row in detail if row.get("精准泛词") == iname}
        cells = []
        for code in benchmarks:
            row = by_code.get(code, {})
            cells.append(
                f"{row.get('占领等级', '—')}｜Top20 {row.get('Top20搜索量覆盖率', '—')}｜Top50 {row.get('Top50搜索量覆盖率', '—')}"
            )
        matrix_rows.append([iname, intent.get("汇总搜索量", ""), intent.get("多对标共识等级", ""), *cells])

    core_intent_rows = []
    for code in benchmarks:
        selected = [
            row for row in detail if row.get("对标编码") == code and row.get("占领等级") in {"核心占领", "强占领"}
        ]
        selected.sort(key=lambda row: (-_n(row.get("Top20搜索量覆盖率")), -_n(row.get("Top10搜索量覆盖率")), row.get("精准泛词", "")))
        for row in selected:
            core_intent_rows.append([
                code, row.get("精准泛词", ""), row.get("层级", ""), row.get("汇总搜索量", ""),
                row.get("占领等级", ""), row.get("Top10搜索量覆盖率", ""),
                row.get("Top20搜索量覆盖率", ""), row.get("Top50搜索量覆盖率", ""),
                row.get("加权自然排名", ""), row.get("占领判断原因", ""),
            ])

    consensus_rows = [
        [row.get("精准泛词", ""), row.get("汇总搜索量", ""), row.get("有效覆盖对标数", ""),
         row.get("核心/强占领对标数", ""), row.get("最佳对标编码", ""),
         row.get("最佳Top20搜索量覆盖率", ""), row.get("Top20覆盖率中位数", ""),
         row.get("Top50覆盖率中位数", ""), row.get("共识判断原因", "")]
        for row in sorted(high, key=lambda row: (-_n(row.get("汇总搜索量")), row.get("精准泛词", "")))
    ]
    single_rows = [
        [row.get("精准泛词", ""), row.get("汇总搜索量", ""), row.get("有效覆盖对标数", ""),
         row.get("核心/强占领对标数", ""), row.get("最佳对标编码", ""),
         row.get("最佳Top20搜索量覆盖率", ""), row.get("Top20覆盖率中位数", ""),
         row.get("共识判断原因", "")]
        for row in sorted(single, key=lambda row: (-_n(row.get("汇总搜索量")), row.get("精准泛词", "")))
    ]

    by_intent = {row.get("精准泛词"): row for row in consensus}
    hierarchy_rows: list[list[Any]] = []
    for summary in intents:
        parent = summary.get("父精准泛词", "")
        if not parent:
            continue
        parent_summary = by_intent.get(parent, {})
        child_rows = [row for row in detail if row.get("精准泛词") == summary.get("精准泛词")]
        parent_rows = [row for row in detail if row.get("精准泛词") == parent]
        child_code = {row.get("对标编码"): row for row in child_rows}
        parent_code = {row.get("对标编码"): row for row in parent_rows}
        for code in benchmarks:
            child = child_code.get(code, {})
            par = parent_code.get(code, {})
            hierarchy_rows.append([
                parent, summary.get("精准泛词", ""), code, parent_summary.get("汇总搜索量", ""),
                summary.get("汇总搜索量", ""), par.get("Top20搜索量覆盖率", ""),
                child.get("Top20搜索量覆盖率", ""), "父级包含该子树；父子数字不相加",
            ])

    demand_rows: list[list[Any]] = []
    for intent in intents[:12]:
        iname = intent.get("精准泛词", "")
        by_code = {row.get("对标编码"): row for row in detail if row.get("精准泛词") == iname}
        for code in benchmarks:
            row = by_code.get(code, {})
            demand_rows.append([
                intent.get("精准泛词", ""), intent.get("汇总搜索量", ""), code,
                row.get("Top10关键词数", ""), row.get("Top10占领搜索量", ""),
                row.get("Top10搜索量覆盖率", ""), row.get("Top20关键词数", ""),
                row.get("Top20占领搜索量", ""), row.get("Top20搜索量覆盖率", ""),
            ])

    weak_rows = []
    for summary in intents:
        if summary.get("多对标共识等级") not in {"低共识", "单点验证"} and int(summary.get("核心/强占领对标数") or 0) > 0:
            continue
        iname = summary.get("精准泛词", "")
        for row in detail:
            if row.get("精准泛词") == iname:
                weak_rows.append([
                    iname, summary.get("多对标共识等级", ""), row.get("对标编码", ""),
                    row.get("有效排名词数", ""), row.get("Top20搜索量覆盖率", ""),
                    row.get("Top50搜索量覆盖率", ""), row.get("占领等级", ""),
                    row.get("占领判断原因", ""),
                ])

    reality_rows = [
        [row.get("精准泛词", ""), row.get("多对标共识等级", ""), row.get("最佳对标编码", ""),
         row.get("最佳Top20搜索量覆盖率", ""), row.get("Top20覆盖率中位数", ""),
         row.get("Top50覆盖率中位数", "")]
        for row in sorted(consensus, key=lambda row: (-_n(row.get("汇总搜索量")), row.get("精准泛词", "")))
    ]
    data_snapshot = {
        "run_timestamp": run_timestamp,
        "detail_columns": list(detail[0].keys()) if detail else [],
        "consensus_columns": list(consensus[0].keys()) if consensus else [],
        "detail": detail,
        "consensus": consensus,
    }
    embedded_json = json.dumps(data_snapshot, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    keyword_scope = (
        f"{total_valid_observations:,} 个Benchmark×Intent有效排名观察（父Intent包含后代，存在有意重复）"
    )
    cards = [
        ("Benchmarks", len(benchmarks)), ("Search Intents", len(consensus)),
        ("High Consensus", len(high)), ("Single-point Validation", len(single)),
        ("Core / Strong cells", core_strong),
    ]
    cards_html = "".join(f'<div class="card"><div class="card-value">{_e(value)}</div><div class="card-label">{_e(label)}</div></div>' for label, value in cards)
    matrix_headers = ["精准泛词", "汇总搜索量", "共识等级", *benchmarks]
    sections = [
        ("1. Executive Summary", f'<div class="cards">{cards_html}</div><p>关键词范围：{_e(keyword_scope)}。指标来自同一Run的OUTPUT A/B回读。父子Intent使用各自Subtree口径，跨层不相加。</p>'),
        ("2. Benchmark Overview", _table(["对标编码", "对标ASIN", "核心占领Intent数", "强占领Intent数", "主要阵地"], benchmark_overview)),
        ("3. Search Intent Occupancy Matrix", _table(matrix_headers, matrix_rows)),
        ("4. Benchmark Core Intent Positions", _table(["对标编码", "精准泛词", "层级", "汇总搜索量", "等级", "Top10率", "Top20率", "Top50率", "加权排名", "判断原因"], core_intent_rows)),
        ("5. Multi-Benchmark High Consensus", _table(["精准泛词", "汇总搜索量", "有效覆盖对标数", "核心/强占领数", "最佳对标", "最佳Top20率", "Top20中位数", "Top50中位数", "共识原因"], consensus_rows, empty="当前没有被判为高共识的Intent。高共识表示多个相似Benchmark验证了需求，不代表竞争容易。")),
        ("6. Single-Point Validation", _table(["精准泛词", "汇总搜索量", "有效覆盖对标数", "核心/强占领数", "最佳对标", "最佳Top20率", "Top20中位数", "共识原因"], single_rows, empty="当前没有被判为单点验证的Intent。")),
        ("7. Parent / Child Occupancy", _table(["Parent Intent", "Child Intent", "对标编码", "Parent需求", "Child需求", "Parent Top20率", "Child Top20率", "口径"], hierarchy_rows, empty="603当前Intent Tree中没有Parent/Child关系。")),
        ("8. Top Search Demand Control", _table(["精准泛词", "Intent汇总搜索量", "对标编码", "Top10词数", "Top10占领量", "Top10覆盖率", "Top20词数", "Top20占领量", "Top20覆盖率"], demand_rows, empty="没有可显示的Intent数据。") + '<p class="note">本节按Intent汇总需求排序，展示各Benchmark对高需求Intent的Top10/Top20控制；固定OUTPUT A不含逐关键词字段，因此不列单个关键词名称。</p>'),
        ("9. Weak / White Space Evidence", _table(["精准泛词", "共识等级", "对标编码", "有效排名词数", "Top20率", "Top50率", "占领等级", "判断原因"], weak_rows, empty="当前没有达到低共识或单点验证筛选条件的Intent。") + '<p class="note">这里仅表示相对占领较弱或验证不足，不代表蓝海，也不证明进入容易。</p>'),
        ("10. Reality Evidence for 6-1", _table(["精准泛词", "共识等级", "最佳对标", "最佳Top20率", "Top20中位数", "Top50中位数"], reality_rows) + '<p class="note">供6-1作为现实证据参考；本报告不替6-1决定首攻、核心或扩展Intent。</p>'),
        ("11. Sources and Boundaries", '<p>自然排名来自602 LATEST VALID Batch中的各Benchmark高度精准D表；Intent Tree和汇总需求来自同一有效603 Run Package。自然搜索占领不等于销量、GMV、订单或点击份额。不同Benchmark覆盖率不得相加成组合市场份额。603意图汇总搜索量为覆盖率分母。HTML仅由本Run的OUTPUT A/B CSV回读生成，不查找最新文件，也不请求外部资源。</p>'),
    ]
    body = "".join(f'<section><h2>{_e(title)}</h2>{content}</section>' for title, content in sections)
    html_doc = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>6-0-6 对标意图市场占领分析 {run_timestamp}</title>
<style>
:root{{--ink:#172033;--muted:#627086;--line:#dce3ed;--paper:#f4f7fb;--blue:#1459a6;--teal:#0f766e;--gold:#a16207}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}}
header{{background:linear-gradient(120deg,#0b2545,#1459a6);color:white;padding:32px max(24px,calc((100vw - 1320px)/2))}}
header h1{{margin:0 0 8px;font-size:28px}}header p{{margin:0;color:#dbeafe}}main{{max-width:1320px;margin:22px auto;padding:0 18px}}
section{{background:white;border:1px solid var(--line);border-radius:12px;padding:22px;margin:16px 0;box-shadow:0 5px 16px #1720330a}}
h2{{margin:0 0 14px;font-size:20px;color:#12355b}}p{{margin:10px 0}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}}
.card{{border:1px solid var(--line);border-radius:10px;padding:14px;background:#f8fbff}}.card-value{{font-size:24px;font-weight:700;color:var(--blue)}}.card-label{{color:var(--muted);font-size:13px}}
.table-wrap{{overflow:auto;max-height:560px;border:1px solid var(--line);border-radius:8px}}table{{border-collapse:collapse;width:100%;min-width:760px;font-size:13px}}
th{{position:sticky;top:0;background:#eaf1f9;text-align:left;color:#193c63;z-index:1}}th,td{{padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}}
tbody tr:nth-child(even){{background:#fafcff}}.note{{color:var(--muted);font-size:13px}}.empty{{padding:14px;color:var(--muted);background:#f8fafc;border-radius:8px}}
footer{{text-align:center;color:var(--muted);padding:20px;font-size:12px}}@media(max-width:680px){{header h1{{font-size:22px}}section{{padding:15px}}}}
</style></head><body>
<header><h1>对标意图市场占领分析</h1><p>Benchmark Intent Market Occupancy Analysis｜Run {run_timestamp}</p></header>
<main>{body}</main><footer>6-0-6｜Organic Search Occupancy｜自然搜索占领深度与多对标共识｜不代表销量市场份额</footer>
<script type="application/json" id="same-run-csv-snapshot">{embedded_json}</script>
</body></html>"""
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(html_doc, encoding="utf-8")
    temporary.replace(output_path)
