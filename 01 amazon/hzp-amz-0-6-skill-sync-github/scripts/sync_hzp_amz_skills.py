from pathlib import Path
import argparse, shutil, subprocess

def main():
    p=argparse.ArgumentParser(); p.add_argument('--source', default=r'C:\Users\qmhzp\.codex\skills'); p.add_argument('--repo', default=r'E:\codex\JasonSkill'); p.add_argument('--push', action='store_true', default=True); p.add_argument('--dry-run', action='store_true'); a=p.parse_args()
    src=Path(a.source); repo=Path(a.repo)/'01 amazon';
    skills=sorted(x for x in src.glob('hzp-amz-*') if x.is_dir())
    source_names={s.name for s in skills}
    for stale in sorted(x for x in repo.glob('hzp-amz-*') if x.is_dir() and x.name not in source_names):
        shutil.rmtree(stale)
        print(f'removed stale skill: {stale.name}')
    for s in skills:
        d=repo/s.name; d.mkdir(parents=True, exist_ok=True)
        shutil.copytree(s,d,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo'))
    subprocess.run(['git','status','--short'],cwd=a.repo,check=True)
    if a.push and not a.dry_run:
        subprocess.run(['git','add','-A','--','01 amazon'],cwd=a.repo,check=True)
        subprocess.run(['git','commit','-m','Sync HZP Amazon skills from .codex'],cwd=a.repo,check=False)
        subprocess.run(['git','push','origin','HEAD'],cwd=a.repo,check=True)
    print(f'synced {len(skills)} skills')
if __name__=='__main__': main()




