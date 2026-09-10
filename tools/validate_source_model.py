#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
errors=[];warnings=[]

def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))

def error(msg):errors.append(msg)
def warn(msg):warnings.append(msg)

event=load('config/event.json')
years=load('config/years.json')
families=load('config/race-families.json')
events=load('data/source/sportstiming/events.json')
cat_path=ROOT/'data/source/sportstiming/class-catalog.json'
cat=load('data/source/sportstiming/class-catalog.json') if cat_path.exists() else None

held=[y['year'] for y in years if y['status']=='held']
cancelled=[y['year'] for y in years if y['status']=='cancelled']
if held!=event['held_years']:error(f"Held years mismatch: {held} vs {event['held_years']}")
if cancelled!=event['cancelled_years']:error(f"Cancelled years mismatch: {cancelled} vs {event['cancelled_years']}")
source_years=[x['year'] for x in events['events']]
if source_years!=held:error(f"Sportstiming event years mismatch: {source_years} vs {held}")
known=set(event['race_families'])
for y in years:
    extra=set(y.get('race_families',[]))-known
    if extra:error(f"Unknown race families in {y['year']}: {sorted(extra)}")
for fam,obj in families.items():
    if fam not in known:error(f"Race family config not declared by event: {fam}")
    if fam=='duo60' and obj.get('route_family_ref')!='ultra60':error('Duo route must reference ultra60')
if cat:
    if cat.get('unmapped_classes'):error(f"Unmapped Sportstiming classes: {cat['unmapped_classes']}")
    edition_by_year={x['year']:x for x in cat['editions']}
    for year in held:
        if year not in edition_by_year:error(f'Missing class catalog year {year}')
        else:
            present={x['race_family'] for x in edition_by_year[year]['classes'] if x.get('race_family')}
            expected=set(next(y['race_families'] for y in years if y['year']==year))
            if present!=expected:error(f'Race family mismatch {year}: catalog={sorted(present)} expected={sorted(expected)}')
else:warn('class-catalog.json has not yet been generated')

for p in ROOT.glob('data/source/gpx/**/*.gpx'):
    try:
        r=ET.parse(p).getroot()
        if r.tag.rsplit('}',1)[-1].lower()!='gpx':error(f'Not GPX root: {p.relative_to(ROOT)}')
        pts=[e for e in r.iter() if e.tag.rsplit('}',1)[-1].lower() in {'trkpt','rtept'}]
        if len(pts)<2:error(f'GPX has too few points: {p.relative_to(ROOT)}')
    except Exception as exc:error(f'Invalid GPX {p.relative_to(ROOT)}: {exc}')

# Course versions intentionally unresolved at this phase.
for fam,obj in families.items():
    if obj.get('course_version_policy') not in (None,'unassigned_until_geometry_comparison'):
        warn(f'{fam} has non-default course version policy: {obj.get("course_version_policy")}')

print(f'ÖST source model validation: {len(errors)} error(s), {len(warnings)} warning(s)')
for x in warnings:print('WARN:',x)
for x in errors:print('ERROR:',x)
raise SystemExit(1 if errors else 0)
