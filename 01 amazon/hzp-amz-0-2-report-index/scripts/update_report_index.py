"""Rebuild a portable Product Root report index without touching reports."""

from __future__ import annotations

import argparse
import html
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


SKILL_LABELS = {
    "2-1": "2-1｜产品分析",
    "2-2": "2-2｜细分市场分析",
}


def read_first_field(path: Path, labels: tuple[str, ...]) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="gb18030", errors="replace")
    for line in text.splitlines():
        for label in labels:
            match = re.match(rf"\s*{re.escape(label)}\s*[:：]\s*(.+?)\s*$", line)
            if match:
                return match.group(1).strip()
    return ""


def product_identity(product_root: Path) -> tuple[str, str]:
    archive = product_root / "01_产品档案.md"
    product_code = read_first_field(archive, ("产品编号", "Product Code"))
    product_name = read_first_field(archive, ("产品名称", "Product Name"))
    product_code = product_code or read_first_field(product_root / "PRODUCT.md", ("Current Product Code", "Product Code"))
    product_name = product_name or read_first_field(product_root / "PRODUCT.md", ("Product Name", "产品名称"))
    return product_code or "当前产品", product_name or ""


def parse_report(path: Path, report_root: Path) -> dict | None:
    if path.name.lower() == "index.html":
        return None
    if any(
        token in {"test", "temp", "demo", "debug"}
        for part in path.relative_to(report_root).parts[:-1]
        for token in [part.casefold()]
    ) or any(
        token in path.stem.casefold()
        for token in ("test", "temp", "demo", "debug")
    ):
        return None
    stem = path.stem
    match = re.match(r"^(?P<skill>\d+-\d+)[-_](?P<product>[^_]+)(?:_(?P<title>.+))?$", stem)
    parent_match = re.match(r"^(?P<skill>\d+-\d+)(?:[_-].*)?$", path.parent.name)
    if not match and not parent_match:
        return None

    skill = match.group("skill") if match else parent_match.group("skill")
    product = match.group("product") if match else ""
    title = (match.group("title") or "") if match else ""
    version_match = re.search(r"_V(?P<version>\d+)(?:_|$)", stem, re.IGNORECASE)
    timestamp_match = re.search(r"_(?P<date>\d{8})_(?P<time>\d{6})(?:$|_)", stem)
    version = int(version_match.group("version")) if version_match else None
    timestamp = None
    if timestamp_match:
        try:
            timestamp = datetime.strptime(
                timestamp_match.group("date") + timestamp_match.group("time"), "%Y%m%d%H%M%S"
            )
        except ValueError:
            timestamp = None
    if title:
        title = re.sub(r"_V\d+(?:_\d{8}_\d{6})?$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"_\d{8}(?:_\d{6})?$", "", title)
    file_time = datetime.fromtimestamp(path.stat().st_mtime)
    relative = Path(path).relative_to(report_root).as_posix()
    return {
        "skill": skill,
        "product": product,
        "title": title,
        "version": version,
        "timestamp": timestamp,
        "file_time": file_time,
        "path": relative,
        "filename": path.name,
        "legacy": version is None or timestamp is None,
    }


def sort_reports(reports: list[dict]) -> list[dict]:
    return sorted(
        reports,
        key=lambda item: (
            item["version"] is not None,
            item["version"] if item["version"] is not None else -1,
            item["timestamp"] or item["file_time"],
        ),
        reverse=True,
    )


def display_time(item: dict) -> str:
    value = item["timestamp"] or item["file_time"]
    return value.strftime("%Y-%m-%d %H:%M:%S")


def build_html(product_code: str, product_name: str, reports: list[dict], generated_at: datetime) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in reports:
        grouped[item["skill"]].append(item)
    ordered_groups = sorted(grouped.items(), key=lambda pair: tuple(int(part) for part in pair[0].split("-")))
    cards: list[str] = []
    for skill, group in ordered_groups:
        group = sort_reports(group)
        label = SKILL_LABELS.get(skill, f"{skill}｜{group[0]['title'] or '分析报告'}")
        latest = group[0]
        latest_link = "./" + latest["path"]
        rows: list[str] = []
        for index, item in enumerate(group):
            version = f"V{item['version']}" if item["version"] is not None else "历史报告"
            legacy = " <span class=\"legacy\">历史报告</span>" if item["legacy"] else ""
            newest = " <span class=\"latest\">最新</span>" if index == 0 else ""
            rows.append(
                "<tr>"
                f"<td>{html.escape(version)}{newest}{legacy}</td>"
                f"<td>{html.escape(display_time(item))}</td>"
                f"<td class=\"filename\">{html.escape(item['filename'])}</td>"
                f"<td><a href=\"./{html.escape(item['path'])}\">打开报告</a></td>"
                "</tr>"
            )
        cards.append(
            "<section class=\"skill-group\">"
            f"<div class=\"group-head\"><h2>{html.escape(label)}</h2>"
            f"<a class=\"latest-link\" href=\"{html.escape(latest_link)}\">打开最新报告</a></div>"
            "<table><thead><tr><th>版本</th><th>生成时间</th><th>报告文件名</th><th>操作</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></section>"
        )
    latest_time = max((item["timestamp"] or item["file_time"] for item in reports), default=generated_at)
    skill_count = len(grouped)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(product_code)}｜分析报告中心</title>
<style>
:root{{--bg:#f4f6f8;--panel:#fff;--ink:#1f2933;--muted:#667085;--line:#d9e0e7;--accent:#0f6b78;}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1280px;margin:0 auto;padding:42px 28px 64px}}.hero{{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:30px 34px;box-shadow:0 8px 24px rgba(31,41,51,.06)}}
.eyebrow{{color:var(--accent);font-weight:700;letter-spacing:.08em;font-size:12px}}h1{{margin:6px 0 18px;font-size:30px;letter-spacing:-.02em}}.identity{{color:var(--muted);font-size:15px}}
.stats{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:24px}}.stat{{border:1px solid var(--line);border-radius:12px;padding:15px 17px;background:#fbfcfd}}.stat b{{display:block;font-size:22px;color:var(--accent)}}.stat span{{color:var(--muted);font-size:12px}}
.skill-group{{margin-top:24px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:22px 24px;box-shadow:0 5px 18px rgba(31,41,51,.045)}}.group-head{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:12px}}h2{{margin:0;font-size:20px}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}.latest-link{{font-size:13px;font-weight:600}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:11px 10px;border-top:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:12px;color:var(--muted);font-weight:600;background:#fafbfc}}tbody tr:hover{{background:#f7fafb}}.filename{{word-break:break-word;color:#475467}}.latest,.legacy{{display:inline-block;margin-left:7px;padding:1px 6px;border-radius:999px;font-size:11px;font-weight:600}}.latest{{background:#e7f3f4;color:var(--accent)}}.legacy{{background:#f0f1f3;color:var(--muted)}}footer{{margin-top:26px;color:var(--muted);font-size:12px;text-align:center}}
@media(max-width:700px){{.wrap{{padding:24px 14px 40px}}.hero{{padding:24px 20px}}h1{{font-size:25px}}.stats{{grid-template-columns:1fr}}.skill-group{{padding:18px 14px;overflow-x:auto}}table{{min-width:680px}}.group-head{{align-items:flex-start;flex-direction:column}}}}
</style></head><body><main class="wrap"><header class="hero"><div class="eyebrow">HZP AMAZON · 分析报告中心</div>
<h1>{html.escape(product_code)}｜{html.escape(product_name or '当前产品')}</h1><div class="identity">当前产品所有正式 Skill 分析报告统一入口</div>
<div class="stats"><div class="stat"><b>{len(reports)}</b><span>正式报告总数</span></div><div class="stat"><b>{skill_count}</b><span>已有报告的 Skill 数</span></div><div class="stat"><b>{html.escape(latest_time.strftime('%Y-%m-%d'))}</b><span>最近报告日期</span></div><div class="stat"><b>{html.escape(generated_at.strftime('%Y-%m-%d %H:%M:%S'))}</b><span>索引更新时间</span></div></div></header>
{''.join(cards) or '<section class="skill-group"><p>当前尚未生成正式分析报告。</p></section>'}
<footer>索引文件：06_SKILL分析报告/index.html · 最近报告：{html.escape(latest_time.strftime('%Y-%m-%d %H:%M:%S'))}</footer></main></body></html>
"""


def rebuild(product_root: Path) -> Path:
    product_root = product_root.resolve()
    report_root = product_root / "06_SKILL分析报告"
    report_root.mkdir(parents=True, exist_ok=True)
    reports = [item for path in report_root.rglob("*.html") if (item := parse_report(path, report_root))]
    reports = sorted(reports, key=lambda item: item["path"])
    code, name = product_identity(product_root)
    output = report_root / "index.html"
    output.write_text(build_html(code, name, reports, datetime.now()), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild Product Root report index")
    parser.add_argument("--product-root", required=True, type=Path)
    args = parser.parse_args()
    print(rebuild(args.product_root))


if __name__ == "__main__":
    main()
