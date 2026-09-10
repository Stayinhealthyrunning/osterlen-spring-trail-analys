#!/usr/bin/env python3
"""Build source-coverage reports by year and race family."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT=Path(__file__).resolve().parents[1]
COURSE=json.loads((ROOT/'config/course-source-manifest.json').read_text(encoding='utf-8'))
EVENTS=json.loads((ROOT/'data/source/sportstiming/events.json').read_text(encoding='utf-8'))
YEARS=[2018,2019,2022,2023,2024,2025,2026]
FAMILIES=['ultra60','duo60','trail22','trail14','trail5']
OUT_JSON=ROOT/'reports/source-coverage.json'
OUT_MD=ROOT/'reports/source-coverage.md'

def applies(value,year):
    return value==year or (isinstance(value,list) and year in value)

def has_actual_path(src):
    target=src.get('target_path')
    return bool(target and (ROOT/target).exists())

def main():
    event_by_year={int(e['year']):e for e in EVENTS['events']}
    rows=[]
    for year in YEARS:
        for family in FAMILIES:
            exists=not (family=='duo60' and year==2018)
            sources=[s for s in COURSE['sources'] if s.get('family')==('ultra60' if family=='duo60' else family) and applies(s.get('year'),year)] if exists else []
            actual=[s for s in sources if has_actual_path(s) and str(s.get('target_path','')).lower().endswith('.gpx')]
            trace=[s for s in sources if s.get('trace_id')]
            maps=[s for s in sources if has_actual_path(s) and str(s.get('target_path','')).lower().endswith('.pdf')]
            row={
              'year':year,'family':family,'race_expected':exists,
              'official_result_event': bool(event_by_year.get(year)) if exists else False,
              'sportstiming_event_id':event_by_year.get(year,{}).get('event_id') if exists else None,
              'route_reference_count':len(trace),
              'trace_ids':sorted({s['trace_id'] for s in trace}),
              'actual_gpx_count':len(actual),
              'actual_gpx_paths':[s['target_path'] for s in actual],
              'actual_map_count':len(maps),
              'map_paths':[s['target_path'] for s in maps],
              'route_geometry_status':(
                'via_same_year_ultra60' if family=='duo60' and exists else
                'archived' if actual else
                'reference_only' if trace else
                'missing'
              ) if exists else 'not_applicable',
              'timing_split_status':'unknown' if exists else 'not_applicable',
            }
            rows.append(row)
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'rows':rows}
    OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Source coverage','',
           'Coverage before result/split import. `reference_only` means a historical route reference exists but no validated GPX bytes are archived locally.','',
           '| Year | Family | Result event | Route geometry | Actual GPX | Trace ref | Map | Timing splits |',
           '|---:|---|:---:|---|---:|---:|---:|---|']
    for r in rows:
        if not r['race_expected']:
            continue
        lines.append(f"| {r['year']} | `{r['family']}` | {'✓' if r['official_result_event'] else '—'} | {r['route_geometry_status']} | {r['actual_gpx_count']} | {r['route_reference_count']} | {r['actual_map_count']} | {r['timing_split_status']} |")
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for r in rows:
        if r['race_expected']:
            print(r['year'],r['family'],r['route_geometry_status'],r['actual_gpx_count'],r['route_reference_count'])

if __name__=='__main__': main()
