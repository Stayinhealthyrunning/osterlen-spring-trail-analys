#!/usr/bin/env python3
from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'reports/sportstiming-structure.json'
OUT=ROOT/'data/source/sportstiming/class-catalog.json'

def family(label):
    s=' '.join(label.lower().split())
    if 'duo' in s or 'relay' in s: return 'duo60'
    if 'ultra' in s or re.search(r'\b60\s*k(?:m)?\b',s): return 'ultra60'
    if re.search(r'\b(?:21|22)\s*k(?:m)?\b',s): return 'trail22'
    if re.search(r'\b(?:13|14)\s*k(?:m)?\b',s): return 'trail14'
    if re.search(r'\b5\s*k(?:m)?\b',s): return 'trail5'
    return None

def nominal(label):
    fam=family(label)
    return {'ultra60':60,'duo60':60,'trail22':22,'trail14':14,'trail5':5}.get(fam)

def historical_nominal(label):
    s=' '.join(label.lower().split())
    for value in (60,22,21,14,13,5):
        if re.search(rf'\b{value}\s*k(?:m)?\b',s): return value
    if 'duo' in s: return 60
    return None

def main():
    data=json.loads(SRC.read_text(encoding='utf-8'))
    editions=[]
    unknown=[]
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
            fam=family(label)
            item={'sportstiming_distance_id':str(o.get('value')) if o.get('value') is not None else None,
                  'source_label':label,'race_family':fam,'canonical_nominal_km':nominal(label),
                  'historical_nominal_km':historical_nominal(label)}
            classes.append(item)
            if not fam: unknown.append({'year':row['year'],**item})
        editions.append({'year':row['year'],'event_id':row['event_id'],'classes':classes})
    payload={'schema_version':2,'generated_from':'reports/sportstiming-structure.json','editions':editions,'unmapped_classes':unknown}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if unknown:
        raise SystemExit('Unmapped Sportstiming classes: '+json.dumps(unknown,ensure_ascii=False))

if __name__=='__main__': main()
