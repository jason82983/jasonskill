#!/usr/bin/env python3
import argparse,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
CST=timezone(timedelta(hours=8))
def now(): return datetime.now(CST).isoformat(timespec="seconds")
def load(p,default): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
def save(p,d): d["updated_at"]=now(); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def next_id(items,prefix,y):
 nums=[]
 for x in items:
  try: nums.append(int(str(x.get("candidate_id" if prefix=="CAN" else "decision_id","")).split("-")[-1]))
  except: pass
 return f"{prefix}-{y}-{max(nums or [0])+1:04d}"
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("action",choices=["init","add","answer","checkpoint","list","candidate","candidate-list","candidate-status"]); ap.add_argument("--question"); ap.add_argument("--product-code",default=""); ap.add_argument("--priority",default="P1"); ap.add_argument("--recommendation",default=""); ap.add_argument("--decision-id"); ap.add_argument("--answer"); ap.add_argument("--comment",default=""); ap.add_argument("--brief-path"); ap.add_argument("--statement"); ap.add_argument("--status",default="WATCHING"); ap.add_argument("--candidate-id"); a=ap.parse_args(); root=Path(a.root); rp=root/"decision_register.json"; cp=root/"checkpoint.json"; ip=root/"decision_inbox.json"; d=load(rp,{"schema_version":"0-5-v1","decision_register":[]}); inbox=load(ip,{"schema_version":"0-5-inbox-v1","candidates":[]})
 if a.action=="init": save(rp,d); save(ip,inbox); cp.parent.mkdir(parents=True,exist_ok=True); cp.write_text(json.dumps({"last_successful_brief_at":None,"last_successful_brief_path":None},ensure_ascii=False,indent=2)+"\n",encoding="utf-8") if not cp.exists() else None
 elif a.action in ("add","answer","checkpoint","list"):
  if a.action=="add":
   if not a.question: ap.error("--question required")
   x={"decision_id":next_id(d.get("decision_register",[]),"DEC",datetime.now(CST).year),"created_at":now(),"product_code":a.product_code,"project":"","question":a.question,"priority":a.priority,"options":{"A":"","B":"","C":"","D":"其他/自定义"},"ai_recommendation":a.recommendation,"boss_answer":None,"boss_comment":None,"answered_at":None,"decision_status":"WAITING_DECISION","deadline":"[无硬性截止日期]","affected_skills":[],"execution_owner":"","follow_up_date":None,"result":None,"reopened_reason":None,"evidence":[],"material_new_evidence":False}; d.setdefault("decision_register",[]).append(x); save(rp,d); print(x["decision_id"])
  elif a.action=="answer":
   for x in d.get("decision_register",[]):
    if x.get("decision_id")==a.decision_id: x.update(boss_answer=a.answer,boss_comment=a.comment,answered_at=now(),decision_status="ANSWERED"); break
   else: ap.error("decision id not found")
   save(rp,d)
  elif a.action=="checkpoint":
   if not a.brief_path: ap.error("--brief-path required")
   cp.parent.mkdir(parents=True,exist_ok=True); cp.write_text(json.dumps({"last_successful_brief_at":now(),"last_successful_brief_path":a.brief_path},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  else: print(json.dumps(d.get("decision_register",[]),ensure_ascii=False,indent=2))
 elif a.action=="candidate":
  if not a.statement: ap.error("--statement required")
  x={"candidate_id":next_id(inbox.get("candidates",[]),"CAN",datetime.now(CST).year),"created_at":now(),"source_type":"USER_CONVERSATION","source_context":"","original_user_statement":a.statement,"ai_interpretation":"[AI推测的决策候选] 待周报复查","potential_decision_topic":"","decision_level":"PROJECT","related_product_codes":[a.product_code] if a.product_code else [],"related_projects":[],"related_skills":[],"why_it_may_matter":"","current_evidence":[],"missing_evidence":[],"suggested_review_time":"","status":a.status,"merged_into":None,"policy_candidate":False}; inbox.setdefault("candidates",[]).append(x); save(ip,inbox); print(x["candidate_id"])
 elif a.action=="candidate-status":
  for x in inbox.get("candidates",[]):
   if x.get("candidate_id")==a.candidate_id: x["status"]=a.status; save(ip,inbox); return
  ap.error("candidate id not found")
 else: print(json.dumps(inbox.get("candidates",[]),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
