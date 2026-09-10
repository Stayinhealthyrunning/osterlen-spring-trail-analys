#!/usr/bin/env python3
"""Analyze Duo member tables in the frozen Sportstiming archive.

The report is aggregate-only: no runner or team names are emitted. The purpose is
to validate whether Sportstiming's per-member rows can safely be interpreted as
relay leg 1/2 rows by comparing their times/clocks with team net time and the
Bengtemölla/final timing observations.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import gzip, json, re, shutil, sqlite3, tempfile

ROOT=Path(__file__).resolve().parents[1]
GZ=ROOT/'data/archive/ost-results-2018-2026.sqlite.gz'
OUT=ROOT/'reports/duo-member-evidence.json'
OUTMD=ROOT/'reports/duo-member-evidence.md'
MEMBER_LINK_RE=re.compile(r'/event/\d+/app/results/(\d+)$')

def sec(v):
 if not v:return None
 m=re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d{2})',v.strip())
 if not m:return None
 return int(m.group(1) or 0)*3600+int(m.group(2))*60+int(m.group(3))

def clock_sec(v):
 if not v:return None
 m=re.fullmatch(r'(\d{1,2}):(\d{2}):(\d{2})',v.strip())
 if not m:return None
 return int(m.group(1))*3600+int(m.group(2))*60+int(m.group(3))

def delta_clock(a,b):
 """Smallest absolute same/next-day delta in seconds."""
 if a is None or b is None:return None
 ds=[abs(a-b),abs((a+86400)-b),abs(a-(b+86400))]
 return min(ds)

def text(c):return (c.get('text') or '').strip()

def member_rows(raw):
 out=[]
 for t in raw.get('tables',[]):
  header=None; idx={}
  for row in t.get('rows',[]):
   if row and all((c.get('tag') or '').lower()=='th' for c in row):
    header=[text(c) for c in row];idx={h:i for i,h in enumerate(header) if h};continue
   if not header or 'Startnummer' not in idx or 'Namn' not in idx:continue
   vals=[text(c) for c in row]
   ni=idx['Namn']; bi=idx['Startnummer']
   name=vals[ni] if ni<len(vals) else ''
   bib=vals[bi] if bi<len(vals) else ''
   if not name:continue
   links=row[ni].get('links',[]) if ni<len(row) else []
   linked_id=None
   for h in links:
    m=MEMBER_LINK_RE.search(h)
    if m:linked_id=m.group(1);break
   out.append({
    'bib':bib or None,'name':name,'source_member_result_id':linked_id,
    'time_seconds':sec(vals[idx['Tid']]) if 'Tid' in idx and idx['Tid']<len(vals) else None,
    'finish_clock':vals[idx['Sluttidspunkt']] if 'Sluttidspunkt' in idx and idx['Sluttidspunkt']<len(vals) else None,
    'speed_source':vals[idx['Hastighet']] if 'Hastighet' in idx and idx['Hastighet']<len(vals) else None,
   })
 return out

def pair_map(raw):
 d={}
 for t in raw.get('tables',[]):
  for row in t.get('rows',[]):
   vals=[text(c) for c in row]
   if len(vals)>=2 and vals[0]:d[vals[0]]=vals[1]
 return d

def team_split_clocks(raw):
 out={}
 for t in raw.get('tables',[]):
  if 'splits-table' not in (t.get('class') or ''):continue
  for row in t.get('rows',[]):
   vals=[text(c) for c in row]
   if len(vals)<9:continue
   label=vals[0]
   if not label or label in ('Distans','Totalt') or label.startswith('Mellantid'):continue
   out[label]=vals[8] or None
 return out

def main():
 with tempfile.TemporaryDirectory(prefix='ost-duo-') as td:
  db=Path(td)/'a.sqlite'
  with gzip.open(GZ,'rb') as f,db.open('wb') as o:shutil.copyfileobj(f,o)
  con=sqlite3.connect(db);con.row_factory=sqlite3.Row
  byyear=defaultdict(Counter);examples=[]
  for r in con.execute("SELECT year,finish_seconds,normalized_json FROM results WHERE race_family='duo60' ORDER BY year,result_uid"):
   year=str(r['year']);obj=json.loads(r['normalized_json']);raw=obj.get('raw_record',{});members=member_rows(raw);pairs=pair_map(raw);splitclocks=team_split_clocks(raw)
   c=byyear[year];c['teams']+=1;c[f'member_count_{len(members)}']+=1
   if len(members)==2:c['two_members']+=1
   if any(m.get('source_member_result_id') for m in members):c['teams_with_linked_member']+=1
   if len(members)==2 and all(m.get('time_seconds') is not None for m in members):
    c['two_members_with_both_times']+=1
    team_time=r['finish_seconds']
    if team_time is not None:
     diff=abs(sum(m['time_seconds'] for m in members)-team_time)
     if diff<=2:c['member_time_sum_matches_team_le_2s']+=1
     if diff<=10:c['member_time_sum_matches_team_le_10s']+=1
     c['member_time_sum_comparable']+=1
   if len(members)==2:
    c1=clock_sec(members[0].get('finish_clock'));c2=clock_sec(members[1].get('finish_clock'))
    if c1 is not None and c2 is not None:
     c['two_members_with_both_clocks']+=1
     forward=(c2-c1)%86400
     if 0<forward<12*3600:c['member_clocks_in_source_order']+=1
    team_finish=clock_sec(pairs.get('Sluttidspunkt'))
    if c2 is not None and team_finish is not None:
     c['second_clock_vs_team_finish_comparable']+=1
     if delta_clock(c2,team_finish)<=2:c['second_clock_matches_team_finish_le_2s']+=1
    # Same-year exchange label used by Sportstiming.
    labels=['Bengtemölla km 32','Bengtemölla','34 km']
    exch=next((clock_sec(splitclocks.get(x)) for x in labels if splitclocks.get(x)),None)
    if c1 is not None and exch is not None:
     c['first_clock_vs_exchange_comparable']+=1
     if delta_clock(c1,exch)<=2:c['first_clock_matches_exchange_le_2s']+=1
  con.close()

 report={'schema_version':1,'years':{y:dict(c) for y,c in sorted(byyear.items())}}
 totals=Counter()
 for c in byyear.values():totals.update(c)
 report['totals']=dict(totals)
 comparable=totals['member_time_sum_comparable'];exchange=totals['first_clock_vs_exchange_comparable'];finish=totals['second_clock_vs_team_finish_comparable'];ordered=totals['two_members_with_both_clocks']
 report['evidence_rates']={
  'two_member_coverage_pct':round(100*totals['two_members']/totals['teams'],2) if totals['teams'] else None,
  'member_time_sum_matches_team_le_2s_pct':round(100*totals['member_time_sum_matches_team_le_2s']/comparable,2) if comparable else None,
  'first_member_clock_matches_exchange_le_2s_pct':round(100*totals['first_clock_matches_exchange_le_2s']/exchange,2) if exchange else None,
  'second_member_clock_matches_team_finish_le_2s_pct':round(100*totals['second_clock_matches_team_finish_le_2s']/finish,2) if finish else None,
  'member_clocks_in_source_order_pct':round(100*totals['member_clocks_in_source_order']/ordered,2) if ordered else None,
 }
 rates=report['evidence_rates']
 report['interpretation']={
  'member_rows_verified_as_public_team_member_rows': totals['two_members']>0,
  'leg_order_can_be_assigned_when_two_rows_present': bool(ordered and rates['member_clocks_in_source_order_pct'] is not None and rates['member_clocks_in_source_order_pct']>=99 and exchange and rates['first_member_clock_matches_exchange_le_2s_pct'] is not None and rates['first_member_clock_matches_exchange_le_2s_pct']>=95),
  'rule':'Only assign leg_no from row order if aggregate timing evidence validates row 1 as exchange and row 2 as final finisher. Otherwise retain source sequence without inventing a leg number.'
 }
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# Duo – evidens för lagmedlemmar och etappordning','', '| År | Lag | 2 medlemsrader | Båda tider | Summa=lagtid ±2s | Rad1=växling ±2s | Rad2=mål ±2s |','|---:|---:|---:|---:|---:|---:|---:|']
 for y,c in sorted(byyear.items()):lines.append(f"| {y} | {c['teams']} | {c['two_members']} | {c['two_members_with_both_times']} | {c['member_time_sum_matches_team_le_2s']} | {c['first_clock_matches_exchange_le_2s']} | {c['second_clock_matches_team_finish_le_2s']} |")
 lines += ['','## Totala träffgrader','']+[f'- **{k}:** {v}' for k,v in rates.items()]
 lines += ['','## Regel','',report['interpretation']['rule'],'']
 OUTMD.write_text('\n'.join(lines),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
