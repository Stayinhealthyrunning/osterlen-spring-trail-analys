#!/usr/bin/env python3
"""Profile unresolved status and Duo detail semantics from the frozen archive.

Outputs aggregate/schema information only. No participant or team names are written.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import gzip, json, re, shutil, sqlite3, tempfile

ROOT=Path(__file__).resolve().parents[1]
GZ=ROOT/'data/archive/ost-results-2018-2026.sqlite.gz'
OUT=ROOT/'reports/archive-semantics-profile.json'
OUTMD=ROOT/'reports/archive-semantics-profile.md'
STATUS_PATTERNS={
 'DNF':[r'\butgått\b',r'\bdnf\b',r'\bbrutit\b',r'\bbröt\b',r'\bretired\b',r'\bdid not finish\b'],
 'DNS':[r'\bdns\b',r'\bej start\w*\b',r'\bdid not start\b'],
 'DSQ':[r'\bdsq\b',r'\bdq\b',r'\bdiskval\w*\b',r'\bdisqual\w*\b'],
}
STATUS_RE={k:[re.compile(x,re.I) for x in v] for k,v in STATUS_PATTERNS.items()}
SAFE_LABEL_RE=re.compile(r'^(status|resultat?|tid|time|distans|distance|klass|class|placering|rank|sträcka|etapp|leg|löpare|deltagare|medlem|member|växling|bengtemölla|starttidspunkt|sluttidspunkt|nettotid|bruttotid|mellantid\s*\d*)$',re.I)
MEMBER_LINK_RE=re.compile(r'/event/\d+/app/results/(\d+)$')

def text_rows(t):
 return [[(c.get('text') or '').strip() for c in row] for row in t.get('rows',[])]

def statuses(obj):
 text='\n'.join(c for t in obj.get('raw_tables',[]) for row in text_rows(t) for c in row)
 found=[]
 for status,patterns in STATUS_RE.items():
  if any(p.search(text) for p in patterns): found.append(status)
 return found

def safe_cell(text, has_member_link=False):
 text=(text or '').strip()
 if has_member_link:
  return '<LINKED_TEXT>'
 if not text:
  return '<EMPTY>'
 if SAFE_LABEL_RE.fullmatch(text):
  return text
 if re.fullmatch(r'\d+(?:[.,]\d+)?',text):
  return '<NUMBER>'
 if re.fullmatch(r'\d{1,2}:\d{2}(?::\d{2})?',text):
  return '<TIME>'
 if re.fullmatch(r'\d+(?:[.,]\d+)?\s*km',text,re.I):
  return '<DISTANCE>'
 return '<TEXT>'

def main():
 with tempfile.TemporaryDirectory(prefix='ost-sem-') as td:
  db=Path(td)/'a.sqlite'
  with gzip.open(GZ,'rb') as f, db.open('wb') as o: shutil.copyfileobj(f,o)
  con=sqlite3.connect(db); con.row_factory=sqlite3.Row
  unknown=defaultdict(Counter); unknown_features=defaultdict(Counter)
  for r in con.execute("SELECT year,race_family,entity_type,normalized_json FROM results WHERE status='UNKNOWN'"):
   obj=json.loads(r['normalized_json']); key=f"{r['year']}:{r['race_family']}:{r['entity_type']}"
   sts=statuses(obj)
   unknown[key]['total']+=1
   if sts:
    for s in sts: unknown[key][s]+=1
   else: unknown[key]['no_explicit_status_word']+=1
   if obj.get('splits'): unknown_features[key]['has_splits']+=1
   if obj.get('start_clock'): unknown_features[key]['has_start_clock']+=1
   if obj.get('overall_place') is not None: unknown_features[key]['has_overall_place']+=1

  relay_tables=Counter(); relay_row_shapes=Counter(); relay_safe_labels=Counter(); relay_links=Counter()
  relay_years=defaultdict(Counter); member_link_counts=defaultdict(Counter); linked_row_contexts=Counter()
  for r in con.execute("SELECT year,normalized_json FROM results WHERE race_family='duo60'"):
   obj=json.loads(r['normalized_json']); raw=obj.get('raw_record',{}); year=str(r['year'])
   relay_years[year]['teams']+=1
   team_member_links=0
   for t in raw.get('tables',[]):
    relay_tables[(t.get('class') or '',t.get('id') or '')]+=1
    header=None
    for row in t.get('rows',[]):
     if row and all((c.get('tag') or '').lower()=='th' for c in row):
      header=tuple(safe_cell(c.get('text')) for c in row)
     texts=[(c.get('text') or '').strip() for c in row]
     shape=tuple(('EMPTY' if not x else ('TIME' if re.fullmatch(r'\d{1,2}:\d{2}(?::\d{2})?',x) else 'TEXT')) for x in texts)
     relay_row_shapes[(len(texts),shape)]+=1
     if texts and SAFE_LABEL_RE.fullmatch(texts[0]): relay_safe_labels[texts[0]]+=1
     member_positions=[]
     for idx,c in enumerate(row):
      has_member=False
      for href in c.get('links',[]):
       h=re.sub(r'\d+','{id}',href); relay_links[h]+=1
       if MEMBER_LINK_RE.search(href):
        has_member=True; team_member_links+=1; member_positions.append(idx)
      if has_member:
       pass
     if member_positions:
      masked=tuple(safe_cell(c.get('text'), any(MEMBER_LINK_RE.search(h) for h in c.get('links',[]))) for c in row)
      linked_row_contexts[(header or (),tuple(member_positions),masked)]+=1
   member_link_counts[year][team_member_links]+=1
  con.close()
 report={
  'schema_version':2,
  'unknown_status':{k:dict(v) for k,v in sorted(unknown.items())},
  'unknown_features':{k:dict(v) for k,v in sorted(unknown_features.items())},
  'relay':{
   'by_year':{k:dict(v) for k,v in sorted(relay_years.items())},
   'member_links_per_team_by_year':{y:{str(k):v for k,v in sorted(c.items())} for y,c in sorted(member_link_counts.items())},
   'table_signatures':[{'class':k[0],'id':k[1],'count':v} for k,v in relay_tables.most_common()],
   'safe_first_cell_labels':dict(relay_safe_labels.most_common()),
   'link_patterns':dict(relay_links.most_common()),
   'linked_row_contexts':[{'header':list(k[0]),'member_link_columns':list(k[1]),'row':list(k[2]),'count':v} for k,v in linked_row_contexts.most_common(30)],
   'row_shapes':[{'columns':k[0],'shape':list(k[1]),'count':v} for k,v in relay_row_shapes.most_common(30)],
  }
 }
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# Semantikprofil för fryst resultatarkiv','', '## Olösta statusar','', '| Grupp | Totalt | DNF-ord | DNS-ord | DSQ-ord | Utan explicit statusord | Har splits |','|---|---:|---:|---:|---:|---:|---:|']
 for k,v in sorted(unknown.items()):
  f=unknown_features[k]; lines.append(f"| {k} | {v['total']} | {v['DNF']} | {v['DNS']} | {v['DSQ']} | {v['no_explicit_status_word']} | {f['has_splits']} |")
 lines += ['','## Duo – medlemslänkar per team och år','', '| År | Antal medlemslänkar i teamdetaljen → antal team |','|---:|---|']
 for y,c in sorted(member_link_counts.items()):
  desc=', '.join(f'{k}→{v}' for k,v in sorted(c.items()))
  lines.append(f'| {y} | {desc} |')
 lines += ['','## Duo – säkra etiketter i detaljtabeller','']
 for k,v in relay_safe_labels.most_common(): lines.append(f'- `{k}`: {v}')
 lines += ['','## Duo – länkmönster i detaljtabeller','']
 for k,v in relay_links.most_common(): lines.append(f'- `{k}`: {v}')
 lines += ['','## Duo – anonymiserade rader med medlemslänk','']
 for (hdr,pos,row),v in linked_row_contexts.most_common(20):
  lines.append(f'- header={list(hdr)}; linkkolumn={list(pos)}; rad={list(row)}; n={v}')
 OUTMD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
