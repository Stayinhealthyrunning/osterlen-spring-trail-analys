#!/usr/bin/env python3
from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'reports/sportstiming-structure.json'
OUT=ROOT/'data/source/sportstiming/class-catalog.json'

def family(label):
    s=label.lower()
    if 'duo' in s or 'relay' in s: return 'duo60'
    if 'ultra' in s or '60 k' in s or '60km' in s: return 'ultra60'
    if '21km' in s or '21 km' in s or '22 k' in s or '22km' in s: return 'trail22'
    if '13 km' in s or '14 km' in s: return 'trail14'
    if '5km' in s or '5 km' in s: return 'trail5'
    return None

def nominal(label):
    fam=family(label)
    return {'ultra60':60,'duo60':60,'trail22':22,'trail14':14,'trail5':5}.get(fam)

def main():
    data=json.loads(SRC.read_text(encoding='utf-8'))
    editions=[]
    for row in data['rows']:
        selects=row.get('selects') or []
        dist=None
        for s in selects:
            cls=(s.get('attrs') or {}).get('class','')
            if 'selectDistance' in cls:
                dist=s; break
        classes=[]
        for o in (dist or {}).get('options',[]):
            label=o.get('text') or ''
            classes.append({'sportstiming_distance_id':str(o.get('value')) if o.get('value') is not None else None,
                            'source_label':label,'race_family':family(label),'canonical_nominal_km':nominal(label)})
        editions.append({'year':row['year'],'event_id':row['event_id'],'classes':classes})
    OUT.write_text(json.dumps({'schema_version':1,'generated_from':'reports/sportstiming-structure.json','editions':editions},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
