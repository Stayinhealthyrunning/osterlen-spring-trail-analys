#!/usr/bin/env python3
"""Build factual source-coverage reports by year and race family.

The report deliberately distinguishes observed source capabilities from inferred
analysis capabilities. It never treats one sampled result as proof that every
participant has complete splits.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT=Path(__file__).resolve().parents[1]
COURSE=json.loads((ROOT/'config/course-source-manifest.json').read_text(encoding='utf-8'))
EVENTS=json.loads((ROOT/'data/source/sportstiming/events.json').read_text(encoding='utf-8'))
YEARS_CFG=json.loads((ROOT/'config/years.json').read_text(encoding='utf-8'))
FAMILY_CFG=json.loads((ROOT/'config/race-families.json').read_text(encoding='utf-8'))
CLASS_CATALOG_PATH=ROOT/'data/source/sportstiming/class-catalog.json'
SPLIT_INVENTORY_PATH=ROOT/'data/source/sportstiming/split-inventory.json'
TRACKING_INVENTORY_PATH=ROOT/'data/source/sportstiming/points-tracking-inventory.json'
CLASS_CATALOG=json.loads(CLASS_CATALOG_PATH.read_text(encoding='utf-8')) if CLASS_CATALOG_PATH.exists() else {'editions':[]}
SPLITS=json.loads(SPLIT_INVENTORY_PATH.read_text(encoding='utf-8')) if SPLIT_INVENTORY_PATH.exists() else {'inventory':[]}
TRACKING=json.loads(TRACKING_INVENTORY_PATH.read_text(encoding='utf-8')) if TRACKING_INVENTORY_PATH.exists() else {'editions':[]}
OUT_JSON=ROOT/'reports/source-coverage.json'
OUT_MD=ROOT/'reports/source-coverage.md'

def applies(value,year):
    return value==year or (isinstance(value,list) and year in value)

def has_actual_path(src):
    target=src.get('target_path')
    return bool(target and (ROOT/target).exists())

def class_index():
    out={}
    for ed in CLASS_CATALOG.get('editions',[]):
        year=int(ed['year'])
        for c in ed.get('classes',[]):
            out[(year,c.get('race_family'))]=c
    return out

def split_index():
    return {(int(x['year']),x.get('race_family')):x for x in SPLITS.get('inventory',[])}

def tracking_index():
    out={}
    for ed in TRACKING.get('editions',[]):
        year=int(ed['year'])
        tr=next((v for v in ed.get('views',[]) if v.get('kind')=='tracking'),None)
        if not tr: continue
        values=[]
        for select in tr.get('selects',[]):
            for opt in select.get('options',[]):
                if opt.get('value'): values.append(str(opt['value']))
        out[year]={
          'view_http_status':tr.get('http_status'),
          'view_available':tr.get('http_status')==200,
          'distance_ids':sorted(set(values)),
          'html_bytes':tr.get('html_bytes',0),
          'error':tr.get('error'),
        }
    return out

def main():
    event_by_year={int(e['year']):e for e in EVENTS.get('events',[])}
    classes=class_index(); splits=split_index(); tracking=tracking_index()
    rows=[]
    for ycfg in YEARS_CFG:
        year=int(ycfg['year'])
        if ycfg.get('status')!='held':
            continue
        expected=set(ycfg.get('race_families',[]))
        for family in FAMILY_CFG.keys():
            exists=family in expected
            if not exists: continue
            route_family='ultra60' if FAMILY_CFG.get(family,{}).get('route_family_ref')=='ultra60' else family
            sources=[s for s in COURSE.get('sources',[]) if s.get('family')==route_family and applies(s.get('year'),year)]
            actual=[s for s in sources if has_actual_path(s) and str(s.get('target_path','')).lower().endswith('.gpx')]
            trace=[s for s in sources if s.get('trace_id')]
            maps=[s for s in sources if has_actual_path(s) and str(s.get('target_path','')).lower().endswith('.pdf')]
            cls=classes.get((year,family))
            sp=splits.get((year,family))
            tr=tracking.get(year,{})
            distance_id=str(cls.get('sportstiming_distance_id')) if cls and cls.get('sportstiming_distance_id') is not None else None
            sample_result=sp.get('sample_result_id') if sp else None
            if sp is None:
                split_status='not_inventoried'
                split_labels=[]
            elif sp.get('has_split_table'):
                split_labels=[r.get('label') for r in sp.get('rows',[]) if r.get('label') and r.get('label')!='Totalt']
                split_status='split_table_observed'
            else:
                split_labels=[]
                split_status='no_split_table_in_sample'
            result_detail_status=(
              'participant_detail_observed' if sample_result else
              'team_or_relay_adapter_needed' if family=='duo60' else
              'not_observed'
            )
            row={
              'year':year,'family':family,'route_family':route_family,
              'official_result_event': bool(event_by_year.get(year)),
              'sportstiming_event_id':event_by_year.get(year,{}).get('event_id'),
              'sportstiming_class_observed':bool(cls),
              'sportstiming_distance_id':distance_id,
              'sportstiming_source_label':cls.get('source_label') if cls else None,
              'result_detail_status':result_detail_status,
              'sample_result_id':sample_result,
              'timing_split_status':split_status,
              'observed_split_labels':split_labels,
              'observed_split_count':len(split_labels),
              'tracking_view_available':bool(tr.get('view_available')),
              'tracking_distance_match':bool(distance_id and distance_id in tr.get('distance_ids',[])),
              'route_reference_count':len(trace),
              'trace_ids':sorted({s['trace_id'] for s in trace}),
              'actual_gpx_count':len(actual),
              'actual_gpx_paths':[s['target_path'] for s in actual],
              'actual_map_count':len(maps),
              'map_paths':[s['target_path'] for s in maps],
              'route_geometry_status':(
                'via_same_year_ultra60' if family=='duo60' and actual else
                'ultra_reference_only' if family=='duo60' and trace else
                'archived' if actual else
                'reference_only' if trace else
                'missing'
              ),
            }
            rows.append(row)
    report={
      'generated_at':datetime.now(timezone.utc).isoformat(),
      'method_notes':[
        'Sportstiming class presence comes from the discovered class catalog.',
        'Split-table status comes from one sampled result per class and is evidence of schema, not proof of complete split coverage for every runner.',
        'Duo result-detail handling remains a separate relay/team adapter concern.',
        'Route geometry status reflects locally archived validated GPX bytes; Trace de Trail references alone remain reference_only.'
      ],
      'rows':rows
    }
    OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Source coverage','',
           'Observed source coverage used to decide what the future analysis UI may safely enable. A sampled split table proves the schema exists, not that every runner has every split.','',
           '| Year | Family | Result class | Detail | Splits | Split labels | Tracking | Route geometry | GPX | Trace ref |',
           '|---:|---|:---:|---|---|---|:---:|---|---:|---:|']
    for r in rows:
        labels=', '.join(r['observed_split_labels']) if r['observed_split_labels'] else '—'
        lines.append(
          f"| {r['year']} | `{r['family']}` | {'✓' if r['sportstiming_class_observed'] else '—'} | "
          f"{r['result_detail_status']} | {r['timing_split_status']} | {labels} | "
          f"{'✓' if r['tracking_distance_match'] else ('view' if r['tracking_view_available'] else '—')} | "
          f"{r['route_geometry_status']} | {r['actual_gpx_count']} | {r['route_reference_count']} |"
        )
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for r in rows:
        print(r['year'],r['family'],r['timing_split_status'],r['route_geometry_status'])

if __name__=='__main__': main()
