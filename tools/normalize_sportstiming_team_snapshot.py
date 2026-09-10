#!/usr/bin/env python3
"""Normalize Sportstiming relay/team snapshots conservatively.

Final team result fields come primarily from the public result-list row, whose
column layout is stable across the inspected ÖST Duo editions. The complete team
detail tables remain embedded in `raw_record` so member/leg parsing can be refined
later without another network fetch.
"""
from __future__ import annotations
from pathlib import Path
import argparse, json, re

ROOT=Path(__file__).resolve().parents[1]

def parse_seconds(value):
    if not value:return None
    value=value.strip()
    m=re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d{2})',value)
    if not m:return None
    return int(m.group(1) or 0)*3600+int(m.group(2))*60+int(m.group(3))

def cell_texts(record):
    return [(c.get('text') or '').strip() for c in record.get('list_row',[])]

def parse_place(value):
    m=re.search(r'\d+',value or '')
    return int(m.group()) if m else None

def normalize(src,record):
    cells=cell_texts(record)
    # Inspected ÖST Duo list layout: place, bib, net, gross, team, category/class.
    # Preserve null rather than guessing when a future layout differs.
    place=parse_place(cells[0]) if len(cells)>0 else None
    bib=cells[1] or None if len(cells)>1 else None
    net=cells[2] or None if len(cells)>2 else None
    gross=cells[3] or None if len(cells)>3 else None
    team_name=cells[4] or None if len(cells)>4 else None
    class_name=cells[5] or src.get('source_label') if len(cells)>5 else src.get('source_label')
    finish_seconds=parse_seconds(net) or parse_seconds(gross)
    return {
        'result_uid':f"st:{src['event_id']}:team:{record['sportstiming_result_id']}",
        'sportstiming_result_id':record['sportstiming_result_id'],
        'entity_type':'team',
        'year':src['year'],
        'race_family':src['race_family'],
        'source_class':class_name,
        'name':team_name,
        'bib':bib,
        'status':'FINISHED' if finish_seconds else 'UNKNOWN',
        'finish_seconds':finish_seconds,
        'gross_seconds':parse_seconds(gross),
        'net_seconds':parse_seconds(net),
        'overall_place':place,
        'splits':[],
        'derived_checkpoint_metrics':[],
        'source_url':record.get('source_url'),
        'source_sha256':record.get('source_sha256'),
        'list_headers':record.get('list_headers',[]),
        'list_row':record.get('list_row',[]),
        'raw_record':record
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--output');args=ap.parse_args()
    src=json.loads((ROOT/args.input).read_text(encoding='utf-8'))
    records=[];errors=[]
    for r in src.get('results',[]):
        if r.get('error'): errors.append(r); continue
        try: records.append(normalize(src,r))
        except Exception as exc: errors.append({'sportstiming_result_id':r.get('sportstiming_result_id'),'error':repr(exc)})
    payload={'schema_version':1,'source_snapshot':args.input,'year':src['year'],'race_family':src['race_family'],'event_id':src['event_id'],
             'entity_type':'team','records':records,'source_errors':errors,
             'normalization_note':'Team final-result fields are normalized from public list rows; full detail tables remain in raw_record for future leg/member parsing.'}
    out=ROOT/(args.output or f"data/normalized/samples/{src['year']}-{src['race_family']}.json")
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Normalized {len(records)} team records; source errors={len(errors)}; output={out.relative_to(ROOT)}')
    raise SystemExit(1 if errors else 0)
if __name__=='__main__':main()
