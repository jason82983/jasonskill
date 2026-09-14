#!/usr/bin/env python3
from pathlib import Path
from html import escape
import argparse,json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args()
    root=Path(a.root); root.mkdir(parents=True,exist_ok=True)
    rp=root/'decision_register.json'
    ip=root/'decision_inbox.json'
    data=json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else {'decision_register':[]}
    items=data.get('decision_register',[])
    inbox=json.loads(ip.read_text(encoding='utf-8')) if ip.exists() else {'candidates':[]}
    candidates=inbox.get('candidates',[])
    statuses=['WAITING_DECISION','ANSWERED','IN_EXECUTION','RESOLVED','REOPENED']
    stats={s:sum(1 for x in items if x.get('decision_status')==s) for s in statuses}
    weekly_dir=root/'weekly'
    files=sorted(weekly_dir.glob('Weekly_Decision_Brief_*.html')) if weekly_dir.exists() else []
    if files:
        rows=''.join('<tr><td>'+escape(f.name)+'</td><td><a href="./weekly/'+escape(f.name)+'">打开周报</a></td></tr>' for f in reversed(files))
    else:
        rows='<tr><td colspan="2">暂无周报</td></tr>'
    cards=''.join('<div class="card"><b>'+escape(label)+'</b><strong>'+str(value)+'</strong></div>' for label,value in [('待决策',stats['WAITING_DECISION']),('已回答',stats['ANSWERED']),('执行中',stats['IN_EXECUTION']),('已解决',stats['RESOLVED']),('重新打开',stats['REOPENED']),('观察中候选',sum(1 for x in candidates if x.get('status')=='WATCHING'))])
    doc='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HZP Amazon 决策中心</title><style>body{font:14px/1.6 Arial,"Microsoft YaHei";background:#f5f7fb;color:#172235;margin:0}main{max-width:980px;margin:30px auto;padding:0 18px}header,.panel{background:#fff;border:1px solid #dfe7f0;border-radius:14px;padding:22px;box-shadow:0 8px 24px #17223510}header{background:linear-gradient(135deg,#402080,#7c3aed);color:white}h1{margin:0 0 4px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:16px 0}.card{background:#fff;border:1px solid #dfe7f0;border-radius:10px;padding:12px}.card b,.card strong{display:block}.card b{color:#64748b;font-size:12px}.card strong{font-size:24px;color:#402080}table{width:100%;border-collapse:collapse}th,td{padding:9px;border-bottom:1px solid #e5eaf0;text-align:left}th{background:#f0ebfb}a{color:#5b21b6}</style></head><body><main><header><h1>HZP Amazon 决策中心</h1><div>0-5｜上级决策与经营问询</div></header><div class="cards">'''+cards+'''</div><section class="panel"><h2>周报</h2><table><tr><th>文件</th><th>操作</th></tr>'''+rows+'''</table></section></main></body></html>'''
    (root/'index.html').write_text(doc,encoding='utf-8')

if __name__=='__main__': main()
