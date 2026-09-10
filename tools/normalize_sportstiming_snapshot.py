#!/usr/bin/env python3
"""Normalize a structured Sportstiming source snapshot into analysis-ready records.

The normalizer is deliberately conservative. Unknown or absent source fields remain
null. It never synthesizes checkpoint passages or finish status.
"""
from __future__ import annotations
from pathlib import Path
import argparse, json, re, unicodedata

ROOT=Path(__file__).resolve().parents[1]

def txt(cell): return (cell or {}).get('text','').strip()
def rows(table): return [[txt(c) for c in row] for row in table.get('rows',[])]

def parse_seconds(value):
    if not value:return None
    m=re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d{2})',value.strip())
    if not m:return None
    h=int(m.group(1) or 0);mi=int(m.group(2));s=int(m.group(3));return h*3600+mi*60+s

def parse_distance(value):
    if not value:return None
    m=re.search(r'(\d+(?:[.,]\d+)?)\s*km',value,re.I)
    return float(m.group(1).replace(',','.')) if m else None

def parse_rank(value):
    if not value:return (None,None)
    m=re.search(r'(\d+)\s+av\s+(\d+)',value,re.I)
    return (int(m.group(1)),int(m.group(2))) if m else (None,None)

def parse_split_ranks(value):
    nums=[int(x) for x in re.findall(r'\d+',value or '')]
    return {'overall':nums[0] if len(nums)>0 else None,'gender':nums[1] if len(nums)>1 else None,'class':nums[2] if len(nums)>2 else None}

def slug(value):
    s=unicodedata.normalize('NFKD',value or '').encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')

def pair_maps(tables):
    out=[]
    for t in tables:
        pairs={}
        for r in rows(t):
            if len(r)>=2 and r[0]:pairs[r[0]]=r[1]
        if pairs:out.append((t,pairs))
    return out

def identity_values(tables):
    candidates=[]
    for t in tables:
        rr=rows(t)
        vals=[]
        for r in rr:
            if len(r)>=2 and not r[0] and r[1]:vals.append(r[1])
        if len(vals)>=2:candidates.append(vals)
    return max(candidates,key=len) if candidates else []

def normalize_result(source,record):
    tables=record.get('tables',[]);pairs=pair_maps(tables)
    flat={}
    for _,m in pairs:flat.update(m)
    ids=identity_values(tables)
    gender=None;age=None;age_category=None;country=None;name=None;club=None
    gender_re=re.compile(r'^(Man|Kvinna|Male|Female),\s*(\d+)\s*år',re.I)
    agecat_re=re.compile(r'^\d{1,2}-\d{1,2}\s+(?:män|kvinnor)',re.I)
    for v in ids:
        gm=gender_re.search(v)
        if gm:gender='M' if gm.group(1).lower() in ('man','male') else 'F';age=int(gm.group(2));continue
        if agecat_re.search(v):age_category=v.split(' Åldersgrupp',1)[0].strip();continue
        if v in ('Sverige','Sweden','Danmark','Denmark','Norge','Norway','Finland','Tyskland','Germany','Frankrike','France','Storbritannien','United Kingdom'):country=v;continue
        if name is None:name=v
        elif club is None:club=v
    overall_place,overall_count=parse_rank(flat.get('Total'))
    gender_label='Män' if gender=='M' else 'Kvinnor' if gender=='F' else None
    gender_place,gender_count=parse_rank(flat.get(gender_label)) if gender_label else (None,None)
    class_place,class_count=parse_rank(flat.get(age_category)) if age_category else (None,None)
    splits=[]
    for t in tables:
        if 'splits-table' not in (t.get('class') or ''):continue
        for r in rows(t):
            if len(r)<8:continue
            label=r[0].strip()
            if not label or label in ('Distans','Totalt') or label.startswith('Mellantid'):continue
            # Current Sportstiming layout: checkpoint, segment distance, participant, segment time,
            # rank triplet, pace, elapsed time, rank triplet, clock time.
            segment_time=r[3] if len(r)>3 else None
            split_rank=parse_split_ranks(r[4] if len(r)>4 else '')
            pace=r[5] if len(r)>5 else None
            elapsed=r[6] if len(r)>6 else None
            cumulative_rank=parse_split_ranks(r[7] if len(r)>7 else '')
            clock=r[8] if len(r)>8 else None
            splits.append({
                'checkpoint_source_label':label,
                'checkpoint_key':slug(label),
                'reported_checkpoint_distance_km':parse_distance(label),
                'segment_distance_km':parse_distance(r[1] if len(r)>1 else None),
                'segment_seconds':parse_seconds(segment_time),
                'segment_place_overall':split_rank['overall'],
                'segment_place_gender':split_rank['gender'],
                'segment_place_class':split_rank['class'],
                'segment_pace_source':pace or None,
                'elapsed_seconds':parse_seconds(elapsed),
                'place_overall':cumulative_rank['overall'],
                'place_gender':cumulative_rank['gender'],
                'place_class':cumulative_rank['class'],
                'clock_time':clock or None,
                'raw_cells':r
            })
    finish_seconds=parse_seconds(flat.get('Nettotid'))
    # A positive published net time is treated as finished; otherwise leave status UNKNOWN until explicit status evidence is parsed.
    status='FINISHED' if finish_seconds and finish_seconds>0 else 'UNKNOWN'
    return {
        'result_uid':f"st:{source['event_id']}:{record['sportstiming_result_id']}",
        'sportstiming_result_id':record['sportstiming_result_id'],
        'year':source['year'],'race_family':source['race_family'],'source_class':flat.get('Klass') or source.get('source_label'),
        'name':name,'club':club,'country':country,'gender':gender,'age':age,'age_category':age_category,
        'status':status,'distance_km':parse_distance(flat.get('Distans')),
        'finish_seconds':finish_seconds,'gross_seconds':parse_seconds(flat.get('Bruttotid')),
        'start_clock':flat.get('Starttidspunkt'),'finish_clock':flat.get('Sluttidspunkt'),'date_source':flat.get('Datum'),
        'overall_place':overall_place,'overall_count':overall_count,'gender_place':gender_place,'gender_count':gender_count,
        'class_place':class_place,'class_count':class_count,'speed_source':flat.get('Hastighet'),'pace_source':flat.get('Tempo'),
        'splits':splits,'source_url':record.get('source_url'),'source_sha256':record.get('source_sha256'),
        'raw_tables':record.get('tables',[])
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--output');args=ap.parse_args()
    src=json.loads((ROOT/args.input).read_text(encoding='utf-8'))
    normalized=[];errors=[]
    for r in src.get('results',[]):
        if r.get('error'):errors.append(r);continue
        try:normalized.append(normalize_result(src,r))
        except Exception as exc:errors.append({'sportstiming_result_id':r.get('sportstiming_result_id'),'error':repr(exc)})
    payload={'schema_version':1,'source_snapshot':args.input,'year':src['year'],'race_family':src['race_family'],
             'event_id':src['event_id'],'records':normalized,'source_errors':errors}
    out=ROOT/(args.output or f"data/normalized/samples/{src['year']}-{src['race_family']}.json")
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Normalized {len(normalized)} records; source errors={len(errors)}; output={out.relative_to(ROOT)}')
if __name__=='__main__':main()
