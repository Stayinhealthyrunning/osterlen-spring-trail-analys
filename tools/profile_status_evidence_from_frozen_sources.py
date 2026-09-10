#!/usr/bin/env python3
"""Profile status evidence using every frozen Sportstiming source surface.

Unlike the first semantic audit, this reads both the normalized detail tables and
the original list rows embedded in imports.snapshot_json. It emits aggregate counts
only; no participant/team names are written.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import gzip, json, re, shutil, sqlite3, tempfile

ROOT=Path(__file__).resolve().parents[1]
GZ=ROOT/'data/archive/ost-results-2018-2026.sqlite.gz'
OUT=ROOT/'reports/status-evidence-profile.json'
OUTMD=ROOT/'reports/status-evidence-profile.md'
PATTERNS={
 'DNF':[r'\butgått\b',r'\bdnf\b',r'\bbrutit\b',r'\bbröt\b',r'\bretired\b',r'\bdid not finish\b'],
 'DNS':[r'\bdns\b',r'\bej start(?:at)?\b',r'\binte start(?:at)?\b',r'\bdid not start\b',r'\bno start\b'],
 'DSQ':[r'\bdsq\b',r'\bdq\b',r'\bdiskval\w*\b',r'\bdisqual\w*\b'],
}
RES={k:[re.compile(p,re.I) for p in ps] for k,ps in PATTERNS.items()}

def collect_text(obj):
 vals=[]
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k not in ('name','team_name','canonical_name'):
    vals.extend(collect_text(v))
 elif isinstance(obj,list):
  for v in obj:vals.extend(collect_text(v))
 elif isinstance(obj,str):vals.append(obj)
 return vals

def detect(texts):
 text='\n'.join(texts);found=[]
 for status,patterns in RES.items():
  if any(p.search(text) for p in patterns):found.append(status)
 return found

def main():
 with tempfile.TemporaryDirectory(prefix='ost-status-') as td:
  db=Path(td)/'a.sqlite'
  with gzip.open(GZ,'rb') as f,db.open('wb') as o:shutil.copyfileobj(f,o)
  con=sqlite3.connect(db);con.row_factory=sqlite3.Row
  source_records={}
  for imp in con.execute('SELECT year,race_family,snapshot_json FROM imports'):
   snap=json.loads(imp['snapshot_json'])
   for rec in snap.get('results',[]):
    rid=str(rec.get('sportstiming_result_id') or '')
    source_records[(int(imp['year']),imp['race_family'],rid)]=rec
  groups=defaultdict(Counter);surfaces=defaultdict(Counter);ambiguous=Counter()
  for r in con.execute("SELECT year,race_family,entity_type,source_result_id,status,normalized_json FROM results WHERE status='UNKNOWN'"):
   key=f"{r['year']}:{r['race_family']}:{r['entity_type']}";groups[key]['total']+=1
   norm=json.loads(r['normalized_json']);src=source_records.get((int(r['year']),r['race_family'],str(r['source_result_id'])),{})
   detail_text=collect_text(norm.get('raw_tables',norm.get('raw_record',{}).get('tables',[])))
   list_text=collect_text(src.get('list_row',[]))
   d=detect(detail_text);l=detect(list_text);all_status=sorted(set(d+l))
   if len(all_status)==1:groups[key][all_status[0]]+=1
   elif len(all_status)>1:
    groups[key]['conflicting_explicit_status']+=1;ambiguous['+'.join(all_status)]+=1
   else:groups[key]['no_explicit_status']+=1
   for s in d:surfaces[f'detail:{s}']+=1
   for s in l:surfaces[f'list:{s}']+=1
   if d and l and set(d)==set(l):surfaces['same_status_on_both_surfaces']+=1
  con.close()
 totals=Counter()
 for c in groups.values():totals.update(c)
 report={'schema_version':1,'groups':{k:dict(v) for k,v in sorted(groups.items())},'totals':dict(totals),'surface_evidence':dict(surfaces),'ambiguous_status_combinations':dict(ambiguous),
         'rule':'Promote UNKNOWN only when exactly one canonical status is explicitly evidenced across the frozen detail/list source surfaces; conflicting or absent evidence stays UNKNOWN.'}
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# Status-evidens från hela frysta Sportstiming-källan','', '| Grupp | UNKNOWN | DNF | DNS | DSQ | Utan explicit | Konflikt |','|---|---:|---:|---:|---:|---:|---:|']
 for k,c in sorted(groups.items()):lines.append(f"| {k} | {c['total']} | {c['DNF']} | {c['DNS']} | {c['DSQ']} | {c['no_explicit_status']} | {c['conflicting_explicit_status']} |")
 lines += ['','## Totalt','']+[f'- `{k}`: {v}' for k,v in totals.items()]+['','## Regel','',report['rule'],'']
 OUTMD.write_text('\n'.join(lines),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
