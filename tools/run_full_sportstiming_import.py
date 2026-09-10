#!/usr/bin/env python3
"""Fetch every in-scope ÖST result class and freeze it into one SQLite archive."""
from __future__ import annotations
from pathlib import Path
import argparse, json, shutil, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data/source/sportstiming/class-catalog.json'

def run(cmd,retries=2):
    for attempt in range(1,retries+1):
        print('+',' '.join(str(x) for x in cmd),flush=True)
        p=subprocess.run(cmd,cwd=ROOT)
        if p.returncode==0:return
        if attempt<retries:
            print(f'Command failed (attempt {attempt}/{retries}); retrying in 3s',flush=True);time.sleep(3)
    raise SystemExit(p.returncode)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=6);ap.add_argument('--keep-work',action='store_true');args=ap.parse_args()
    work=ROOT/'data/work';snap=work/'snapshots';norm=work/'normalized'
    if work.exists() and not args.keep_work: shutil.rmtree(work)
    snap.mkdir(parents=True,exist_ok=True);norm.mkdir(parents=True,exist_ok=True)
    cat=json.loads(CAT.read_text(encoding='utf-8'))
    jobs=[]
    for ed in cat['editions']:
        for c in ed['classes']:
            jobs.append((int(ed['year']),c['race_family']))
    print(f'Importing {len(jobs)} year/family result sets',flush=True)
    py=sys.executable
    for n,(year,family) in enumerate(jobs,1):
        print(f'\n[{n}/{len(jobs)}] {year} {family}',flush=True)
        sp=f'data/work/snapshots/{year}-{family}.json';np=f'data/work/normalized/{year}-{family}.json'
        run([py,'tools/fetch_sportstiming_snapshot.py','--year',str(year),'--family',family,'--workers',str(args.workers),'--output',sp],retries=2)
        normalizer='tools/normalize_sportstiming_team_snapshot.py' if family=='duo60' else 'tools/normalize_sportstiming_snapshot.py'
        run([py,normalizer,sp,'--output',np],retries=1)
        time.sleep(0.25)
    run([py,'tools/build_frozen_results_db.py','--snapshots-dir','data/work/snapshots','--normalized-dir','data/work/normalized','--output','data/archive/ost-results-2018-2026.sqlite'],retries=1)
    print('\nFull frozen result archive built successfully.',flush=True)

if __name__=='__main__':main()
