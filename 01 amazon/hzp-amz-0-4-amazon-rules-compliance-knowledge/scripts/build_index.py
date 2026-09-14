from __future__ import annotations
import argparse, html, json, re
from pathlib import Path
CATEGORIES=["01_Amazon平台规则","02_Listing与页面","03_FBA物流与包装","04_产品合规与认证","05_类目准入与限制","06_广告规则","07_账户与店铺","08_官方帮助与操作","09_出口税务与跨境","10_其他"]
def meta(text,name):
    m=re.search(r'<meta\s+name=["\']'+re.escape(name)+r'["\']\s+content=["\']([^"\']*)',text,re.I)
    return m.group(1).strip() if m else ""
def load(path,root):
    if path.suffix.lower()==".json":
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: return None
    if path.suffix.lower()!=".html" or path.name.lower()=="index.html": return None
    text=path.read_text(encoding="utf-8",errors="replace"); kid=meta(text,"knowledge-id")
    if not kid: return None
    return {"knowledge_id":kid,"title":meta(text,"knowledge-title") or path.stem,"marketplace":meta(text,"marketplace") or "US","category":meta(text,"category") or path.parent.name,"status":meta(text,"status") or "[待确认]","change_risk":meta(text,"change-risk") or "MEDIUM","last_verified_at":meta(text,"last-verified-at") or "","version":meta(text,"version") or "","report_path":path.relative_to(root).as_posix()}
def build(root):
    entries=[]
    for p in root.rglob("*"):
        if p.is_file() and p.name.lower()!="index.html":
            e=load(p,root)
            if e and e.get("report_path"): entries.append(e)
    entries.sort(key=lambda e:(e.get("category",""),e.get("title",""),e.get("version","")))
    rows=[]
    for e in entries:
        rows.append('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><a href="{}">打开报告</a></td></tr>'.format(*(html.escape(str(e.get(k,"")),quote=True) for k in ["title","marketplace","category","status","last_verified_at","change_risk","report_path"])))
    body="".join(rows) or '<tr><td colspan="7" class="empty">暂无已登记专项知识</td></tr>'
    out='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HZP Amazon 日常知识中心</title><style>body{font:14px/1.6 Segoe UI,"Microsoft YaHei",sans-serif;background:#f5f7fa;color:#172033;margin:0}main{max-width:1200px;margin:auto;padding:28px}header,.card{background:#fff;border:1px solid #e4eaf1;border-radius:14px;padding:22px;box-shadow:0 4px 14px #233b5b0d}h1{margin:0;color:#176b87}table{width:100%;border-collapse:collapse;margin-top:16px}th,td{padding:9px;border-bottom:1px solid #e4eaf1;text-align:left;vertical-align:top}th{background:#f0f4f7}.empty{color:#66758a;text-align:center}</style></head><body><main><header><h1>HZP Amazon 日常知识中心</h1><p>公共规则、合规与官方知识；0-4知识报告不进入产品正式报告索引。</p></header><section class="card"><table><thead><tr><th>知识主题</th><th>Marketplace</th><th>知识分类</th><th>知识状态</th><th>最后核验</th><th>Change Risk</th><th>操作</th></tr></thead><tbody>''' + body + '''</tbody></table></section></main></body></html>'''
    (root/"index.html").write_text(out,encoding="utf-8"); return len(entries)
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--knowledge-root",required=True); a=ap.parse_args(); root=Path(a.knowledge_root).resolve(); root.mkdir(parents=True,exist_ok=True)
    for c in CATEGORIES: (root/c).mkdir(exist_ok=True)
    print(f"indexed={build(root)} path={root/'index.html'}")
