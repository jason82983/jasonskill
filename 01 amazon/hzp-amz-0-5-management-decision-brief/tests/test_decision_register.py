import json,subprocess,sys,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]; SCRIPT=BASE/"scripts/decision_register.py"
def run(*args): return subprocess.check_output([sys.executable,str(SCRIPT),*args],text=True)
def test_register_lifecycle():
 with tempfile.TemporaryDirectory() as t:
  root=Path(t); run("--root",str(root),"init"); did=run("--root",str(root),"add","--product-code","B2","--question","是否批准标准Launch？","--recommendation","B").strip(); assert did.startswith("DEC-"); run("--root",str(root),"answer","--decision-id",did,"--answer","B","--comment","按标准增长"); d=json.loads((root/"decision_register.json").read_text(encoding="utf-8")); assert d["decision_register"][0]["boss_answer"]=="B"; assert d["decision_register"][0]["decision_status"]=="ANSWERED"; run("--root",str(root),"checkpoint","--brief-path","weekly/Weekly_Decision_Brief_20260914.html"); cp=json.loads((root/"checkpoint.json").read_text(encoding="utf-8")); assert cp["last_successful_brief_path"].startswith("weekly/")
