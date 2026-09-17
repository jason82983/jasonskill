"""Static, same-run HTML rendering for the 6-1 decision package."""
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence


def _h(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _cell(value: Any) -> str:
    value = "" if value is None else str(value)
    return _h(value) if value else "—"


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]], empty: str = "No records in this run.") -> str:
    if not rows:
        return f'<p class="empty">{_h(empty)}</p>'
    head = "".join(f"<th>{_h(item)}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{_cell(value)}</td>" for value in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _campaign_groups(battle_rows: Sequence[Mapping[str, Any]], product_code: str, campaign_tag: str | None) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in battle_rows:
        grouped[str(row.get("作战单元ID") or "")].append(row)
    role_codes = {"首攻": "COR", "核心": "COR", "扩展": "EXP", "探索": "DIS", "暂缓": "DEF"}
    mode_codes = {"EXACT": "EXA", "PHRASE": "PHR", "BROAD": "BRO", "AUTO": "AUT", "ASIN": "ASI",
                  "PT": "PT", "PRODUCT": "PT", "PRODUCT_TARGET": "PT", "CATEGORY": "CAT"}
    campaigns: list[dict[str, Any]] = []
    for unit_id, rows in sorted(grouped.items()):
        first = rows[0]
        control = str(first.get("控制方式") or "")
        task = str(first.get("作战任务") or "")
        mode = str(first.get("投放方式") or "")
        role_code = role_codes.get(task, "COR")
        mode_code = mode_codes.get(mode, "EXA")
        intents = list(dict.fromkeys(str(row.get("精准泛词") or "") for row in rows))
        intent_codes = list(dict.fromkeys(str(row.get("意图代码") or "") for row in rows))
        if control == "独立":
            intent_part = intent_codes[0] if intent_codes else "{IntentCode}"
            if campaign_tag:
                name = f"{product_code}.{campaign_tag}.SP-{role_code}-{mode_code}-SBG-{intent_part}-01"
            else:
                name = f"{{ProductCode}}.{{CampaignTag}}.SP-{role_code}-{mode_code}-SBG-{intent_part}-01"
        else:
            if campaign_tag:
                name = f"{product_code}.{campaign_tag}.SP-{role_code}-{mode_code}-SBG-01"
            else:
                name = "{ProductCode}.{CampaignTag}.SP-COR-EXA-SBG-01" if role_code == "COR" and mode_code == "EXA" else f"{{ProductCode}}.{{CampaignTag}}.SP-{role_code}-{mode_code}-SBG-01"
        campaigns.append({
            "unit_id": unit_id,
            "control": control,
            "task": task,
            "mode": mode,
            "role_code": role_code,
            "intent": " / ".join(intents),
            "intent_code": " / ".join(intent_codes),
            "keyword_count": len(rows),
            "name": name,
        })
    return campaigns


def _run_table_rows(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> list[list[Any]]:
    return [[row.get(field, "") for field in fields] for row in rows]


def render_report_html(
    *,
    product_code: str,
    run_id: str,
    run_timestamp: str,
    input_run_id: str,
    input_timestamp: str,
    input_folder: str,
    input_files: Sequence[str],
    six_0_6_run_id: str | None,
    six_0_6_status: str,
    intent_rows: Sequence[Mapping[str, Any]],
    lifecycle_rows: Sequence[Mapping[str, Any]],
    battle_rows: Sequence[Mapping[str, Any]],
    campaign_tag: str | None = None,
) -> str:
    """Render a self-contained HTML snapshot strictly from same-run A/C/B/D rows."""
    phases = Counter(str(row.get("计划阶段") or "") for row in lifecycle_rows)
    launch_count = sum(str(row.get("新品期是否投放") or "") == "是" for row in lifecycle_rows)
    held_rows = [row for row in lifecycle_rows if str(row.get("新品期是否投放") or "") == "否"]
    first_attack = [row for row in intent_rows if row.get("作战任务") == "首攻"]
    core_expansion_hold = [row for row in intent_rows if row.get("作战任务") in {"核心", "扩展", "探索", "暂缓"}]
    child_rows = [row for row in intent_rows if str(row.get("父精准泛词") or "").strip()]
    expansion_rows = [[row.get("父精准泛词"), row.get("精准泛词"), row.get("作战任务"), row.get("控制方式"), row.get("决策原因")] for row in child_rows]
    lifecycle_counts = Counter(str(row.get("当前状态") or "") for row in lifecycle_rows)
    campaigns = _campaign_groups(battle_rows, product_code, campaign_tag)
    control_rows = []
    for control in ("独立", "共享", "不投"):
        matching = [row for row in intent_rows if row.get("控制方式") == control]
        control_rows.append([control, len(matching), "；".join(str(row.get("精准泛词") or "") for row in matching), "；".join(str(row.get("控制原因") or "") for row in matching)])
    battlefield = _run_table_rows(intent_rows, ["意图代码", "精准泛词", "中文", "层级", "父精准泛词", "直接搜索量", "汇总搜索量", "平均竞品数", "意图机会比", "直接对应词数", "作战任务", "作战优先级", "控制方式", "决策原因"])
    first_rows = [[row.get("精准泛词"), row.get("父精准泛词"), row.get("作战优先级"), row.get("作战方向"), row.get("决策原因"), row.get("控制方式"), row.get("控制原因")] for row in first_attack]
    core_rows = [[row.get("作战任务"), row.get("精准泛词"), row.get("父精准泛词"), row.get("作战优先级"), row.get("控制方式"), row.get("决策原因")] for row in core_expansion_hold]
    lifecycle_view = _run_table_rows(lifecycle_rows, ["Id", "词", "精准泛词", "意图代码", "作战任务", "控制方式", "当前状态", "新品期是否投放", "计划阶段", "计划投放方式", "启动条件", "暂不投放原因"])
    battle_view = _run_table_rows(battle_rows, ["作战单元ID", "精准泛词", "意图代码", "作战任务", "控制方式", "Id", "词", "市场容量", "计划阶段", "投放方式", "目标类型", "目标值", "作战目的"])
    held_view = _run_table_rows(held_rows, ["Id", "词", "精准泛词", "当前状态", "计划阶段", "启动条件", "暂不投放原因"])
    campaign_view = [[item["name"], item["control"], item["task"], item["mode"], item["intent"], item["intent_code"] if item["control"] == "独立" else "—", item["keyword_count"], item["unit_id"]] for item in campaigns]
    phase_rows = [[phase, count] for phase, count in sorted(phases.items())]
    state_rows = [[state, count] for state, count in sorted(lifecycle_counts.items())]
    summary_items = [
        ("Precise Intents", len(intent_rows)),
        ("Lifecycle Keywords", len(lifecycle_rows)),
        ("PHASE_1 execution", len(battle_rows)),
        ("Launch investment = yes", launch_count),
        ("Proposed Campaign groups", len(campaigns)),
    ]
    cards = "".join(f'<div class="metric"><strong>{count}</strong><span>{_h(label)}</span></div>' for label, count in summary_items)
    intent_rows_json = [dict(row) for row in intent_rows]
    lifecycle_rows_json = [dict(row) for row in lifecycle_rows]
    battle_rows_json = [dict(row) for row in battle_rows]
    embedded = json.dumps({"run_id": run_id, "run_timestamp": run_timestamp, "A": intent_rows_json, "C": lifecycle_rows_json, "B": battle_rows_json}, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    input_files_text = "、".join(input_files)
    input_file_list = ", ".join(_h(name) for name in input_files) or "Not recorded"
    latest_status = "LATEST VALID 606 evidence available" if six_0_6_status == "LATEST_VALID_606_RUN_PACKAGE_READY" else "606_EVIDENCE_NOT_AVAILABLE"
    nav = "".join(f'<a href="#{i}">{i}</a>' for i in range(1, 13))
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>新品广告作战规划｜{_h(product_code)}｜{_h(run_timestamp)}</title>
<style>
:root{{--ink:#172033;--muted:#65738a;--line:#dce3ec;--paper:#f4f7fb;--blue:#2859a5;--teal:#087e8b;--gold:#a66b09;--red:#a13c37}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.58 "Segoe UI","Microsoft YaHei",sans-serif}}header{{background:linear-gradient(120deg,#132d52,#246178);color:white;padding:34px max(22px,calc((100vw - 1320px)/2)) 30px}}h1{{margin:0 0 8px;font-size:30px}}header p{{margin:4px 0;color:#d5e3f1}}main{{max-width:1320px;margin:auto;padding:22px}}nav{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 20px}}nav a{{color:var(--blue);background:white;border:1px solid var(--line);padding:5px 9px;border-radius:7px;text-decoration:none;font-size:13px}}section{{background:white;border:1px solid var(--line);border-radius:12px;padding:22px;margin:16px 0;box-shadow:0 3px 14px #1f335010}}h2{{font-size:21px;margin:0 0 12px}}h3{{font-size:16px;margin:18px 0 7px}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin:16px 0}}.metric{{background:#f0f5fa;border-radius:9px;padding:13px 15px}}.metric strong{{display:block;color:var(--blue);font-size:24px}}.metric span{{color:var(--muted);font-size:13px}}.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:8px}}table{{border-collapse:collapse;width:100%;font-size:13px;min-width:750px}}th,td{{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;max-width:420px}}th{{background:#edf2f8;color:#30415d;position:sticky;top:0}}tr:last-child td{{border-bottom:0}}.empty,.muted{{color:var(--muted)}}.callout{{border-left:4px solid var(--teal);background:#edf8f8;padding:12px 15px;border-radius:5px;margin:12px 0}}.warning{{border-left-color:var(--gold);background:#fff8e9}}.risk{{border-left-color:var(--red);background:#fff1ef}}.meta{{font:13px/1.7 Consolas,monospace;color:#40516b;overflow-wrap:anywhere}}.pill{{display:inline-block;padding:2px 8px;border-radius:99px;background:#e7eef8;color:#284b7d;font-size:12px}}footer{{max-width:1320px;margin:auto;padding:4px 22px 30px;color:var(--muted);font-size:12px}}
@media(max-width:700px){{header{{padding:25px 18px}}main{{padding:12px}}section{{padding:15px}}h1{{font-size:24px}}}}
</style></head><body>
<header><h1>新品广告作战规划</h1><p>Product Code：{_h(product_code)}　｜　6-1 Run：{_h(run_id)}　｜　状态：PROPOSED</p><p>同一 Run Package 快照：{_h(run_timestamp)}</p></header>
<main><nav>{nav}</nav>
<section id="1"><h2>1. Executive Summary</h2><p>本报告把 6-0-3 的精准 Intent 与关键词资产整理为新品阶段的市场顺序、关键词生命周期和拟建控制架构。最终执行金额由 6-2 根据执行时证据确定。</p><div class="metrics">{cards}</div><p>首攻 Intent：{_h("、".join(str(row.get("精准泛词") or "") for row in first_attack) or "本次未指定")}</p><p class="meta">603 input: {_h(input_run_id)} / {_h(input_timestamp)}；606: {_h(latest_status)}</p></section>
<section id="2"><h2>2. Search Intent Battlefield</h2><p>每行指标直接继承同一 6-0-3 Summary。父子汇总搜索量有包含关系，不能跨层相加。</p>{_table(["Intent Code","精准泛词","中文","层级","父Intent","直接量","汇总量","平均竞品","机会比","直接词数","任务","优先级","控制","决策理由"], battlefield)}</section>
<section id="3"><h2>3. 为什么选择首攻</h2><p>首攻判断综合产品核心需求、父子意图关系、市场规模、竞争环境、具体突破词与 Benchmark Evidence；没有固定权重排序。</p>{_table(["首攻Intent","父Intent","优先级","作战方向","决策原因","控制方式","控制原因"], first_rows, "本次没有 Intent 被规划为首攻；请检查完整决策输入。")}</section>
<section id="4"><h2>4. 核心、扩展与暂缓市场</h2>{_table(["任务","Intent","父Intent","优先级","控制","决策原因"], core_rows)}</section>
<section id="5"><h2>5. Intent Expansion Path</h2><p>沿用 6-0-3 Parent/Child Tree。Child 首攻、Parent 核心时，先验证局部突破，再扩展到上层市场。</p>{_table(["父Intent","子Intent","当前任务","控制","决策原因"], expansion_rows)}</section>
<section id="6"><h2>6. Keyword Lifecycle</h2><p>覆盖 {len(lifecycle_rows)} 条 6-0-3 Keyword Mapping 记录；每个 source Id 只出现一次。</p><h3>生命周期状态</h3>{_table(["当前状态","关键词数"], state_rows)}<h3>计划阶段</h3>{_table(["计划阶段","关键词数"], phase_rows)}<h3>逐词规划</h3>{_table(["Id","词","精准泛词","Intent Code","作战任务","控制","当前状态","新品期投放","阶段","方式","启动条件","暂不投放原因"], lifecycle_view)}</section>
<section id="7"><h2>7. Campaign Control Design</h2><p>独立用于需要独立预算、竞价、广告位、流量隔离、绩效责任或增长节奏的 Intent。共享用于低成本验证与扩展，减少预算碎片化。Intent 不等于 Campaign。</p>{_table(["控制方式","Intent 数","Intent","控制原因"], control_rows)}<div class="callout warning">独立 Campaign 会增加独立预算单元，可能使新品预算过度分散。每个独立控制决定都应有明确的隔离价值。</div></section>
<section id="8"><h2>8. 当前 Keyword Battle Plan</h2><p>B 严格由 C 中 PHASE_1、投放为“是”、控制方式不是“不投”的记录派生，共 {len(battle_rows)} 条。</p>{_table(["作战单元ID","精准泛词","Intent Code","任务","控制","Id","词","市场容量","计划阶段","投放方式","目标类型","目标值","作战目的"], battle_view)}</section>
<section id="9"><h2>9. 暂不投放分析</h2><p>暂缓表示精准资产继续保留，但当前不进入广告。</p>{_table(["Id","词","精准泛词","当前状态","计划阶段","启动条件","暂不投放原因"], held_view)}</section>
<section id="10"><h2>10. 风险边界</h2><div class="callout risk"><ul><li>意图机会比是 6-0-3 内部信号，不是 Amazon 官方指标。</li><li>父子 Intent 的汇总搜索量重叠，不可跨层相加。</li><li>高度精准不等于新品期立即投放；仍需产品适配、阶段和经济边界判断。</li><li>Benchmark 自然排名不代表本品销量份额，也不能直接推算销量。</li><li>6-1必须输出广告创建参数；缺失值标记 DATA_NOT_AVAILABLE，6-2不得补猜。</li></ul></div></section>
<section id="11"><h2>11. 拟创建广告架构</h2><p>架构仅从本 Run 的 B 作战单元 ID 分组派生。兼容关键词按意图与控制方式聚合，不按关键词逐个建 Campaign。</p>{_table(["Campaign Naming Preview","控制","Role","方式","Intent","Intent Code","Keyword 数","作战单元 ID"], campaign_view, "PHASE_1 没有可执行关键词，因此不生成 Campaign 架构。")}</section>
<section id="12"><h2>12. 6-2 Handoff Summary</h2><div class="callout">6-2 应将本报告与同一 RUN_TIMESTAMP 的 A/B/C/D CSV 作为一个完整输入包，不能跨 Run 拼接。D 广告创建参数表是 Bid、Budget、Placement、策略、身份和状态的唯一来源；批准后6-2只做实时身份/能力/差异校验并执行，不再补算参数。</div><p class="meta">6-1 RUN_TIMESTAMP：{_h(run_timestamp)}<br>603 Report Root/Package：{_h(input_folder)}<br>603 Files：{input_file_list}<br>606 Run ID：{_h(six_0_6_run_id or "606_EVIDENCE_NOT_AVAILABLE")}<br>CampaignTag：{_h(campaign_tag or "未提供；命名使用 Placeholder")}</p></section>
<script type="application/json" id="run-data">{embedded}</script>
</main><footer>静态同 Run 快照；打开时不请求最新 CSV 或外部服务。Source file lineage: {_h(input_files_text)}</footer></body></html>'''


def read_embedded_snapshot(html_text: str) -> dict[str, Any]:
    """Read the explicit JSON snapshot used by package validation."""
    marker = '<script type="application/json" id="run-data">'
    start = html_text.find(marker)
    if start < 0:
        raise ValueError("HTML_SNAPSHOT_MISSING")
    start += len(marker)
    end = html_text.find("</script>", start)
    if end < 0:
        raise ValueError("HTML_SNAPSHOT_MALFORMED")
    try:
        data = json.loads(html_text[start:end])
    except json.JSONDecodeError as exc:
        raise ValueError("HTML_SNAPSHOT_MALFORMED") from exc
    if not isinstance(data, dict) or set(data) != {"run_id", "run_timestamp", "A", "C", "B"}:
        raise ValueError("HTML_SNAPSHOT_SCHEMA_INVALID")
    return data
