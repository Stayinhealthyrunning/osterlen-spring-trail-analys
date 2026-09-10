#!/usr/bin/env python3
"""Join curated ÖST race facts with observed source/capability metadata.

`config/race-catalog.json` remains the curated source catalog. This builder never rewrites
it; instead it creates a derived handoff catalog that can be consumed by the future generic
analysis engine once the Gotaleden refactor is ready.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=json.loads((ROOT/'config/race-catalog.json').read_text(encoding='utf-8'))
CLASSES=json.loads((ROOT/'data/source/sportstiming/class-catalog.json').read_text(encoding='utf-8'))
VERSIONS=json.loads((ROOT/'config/course-versions.json').read_text(encoding='utf-8'))
COVERAGE_PATH=ROOT/'reports/source-coverage.json'
CAPS_PATH=ROOT/'data/derived/analysis-capabilities.json'
GEOM_PATH=ROOT/'reports/tracedetrail-public-geometry-analysis.json'
COVERAGE=json.loads(COVERAGE_PATH.read_text(encoding='utf-8')) if COVERAGE_PATH.exists() else {'rows':[]}
CAPS=json.loads(CAPS_PATH.read_text(encoding='utf-8')) if CAPS_PATH.exists() else {'rows':[]}
GEOM=json.loads(GEOM_PATH.read_text(encoding='utf-8')) if GEOM_PATH.exists() else {'routes':[]}
OUT=ROOT/'data/derived/race-catalog-enriched.json'
OUT_MD=ROOT/'reports/race-catalog-enriched.md'


def class_index():
    out={}
    for ed in CLASSES.get('editions',[]):
        for c in ed.get('classes',[]): out[(int(ed['year']),c.get('race_family'))]=c
    return out


def assignment_index():
    return {(int(a['year']),a['family']):a for a in VERSIONS.get('assignments',[])}


def row_index(payload):
    return {(int(r['year']),r['family']):r for r in payload.get('rows',[])}


def geom_index():
    return {(int(r['year']),r['family']):r for r in GEOM.get('routes',[])}


def main():
    ci=class_index(); vi=assignment_index(); cov=row_index(COVERAGE); cap=row_index(CAPS); gi=geom_index()
    rows=[]
    for source in BASE.get('races',[]):
        r=dict(source); key=(int(r['year']),r['race_family'])
        cls=ci.get(key); assn=vi.get(key); coverage=cov.get(key); capability=cap.get(key); geometry=gi.get((int(r['year']),r.get('route_family_ref') or r['race_family']))
        r['source_catalog_course_version']=r.pop('course_version',None)
        r['course_version']=assn.get('course_version_id') if assn else None
        r['course_version_assignment_status']=assn.get('status') if assn else 'not_assigned'
        r['sportstiming_distance_id']=cls.get('sportstiming_distance_id') if cls else None
        r['sportstiming_source_label']=cls.get('source_label') if cls else None
        r['timing_split_status']=coverage.get('timing_split_status') if coverage else r.get('timing_split_status','unknown')
        r['observed_split_labels']=coverage.get('observed_split_labels',[]) if coverage else []
        r['result_detail_status']=coverage.get('result_detail_status') if coverage else None
        r['route_geometry_status']=coverage.get('route_geometry_status') if coverage else None
        r['tracking_distance_match']=coverage.get('tracking_distance_match') if coverage else None
        if geometry:
            r['trace_geometry_evidence']={
              'trace_id':geometry.get('trace_id'),
              'source_date_compet':geometry.get('source_date_compet'),
              'manifest_year_match':geometry.get('source_year_matches_manifest'),
              'public_geometry_sha256':geometry.get('geometry_sha256'),
              'derived_path_distance_km':geometry.get('path_distance_km'),
              'landmarks':geometry.get('landmarks',[]),
            }
        r['analysis_capabilities']=capability.get('features',{}) if capability else {}
        rows.append(r)
    payload={
      'schema_version':1,
      'generated_at':datetime.now(timezone.utc).isoformat(),
      'source_catalog':'config/race-catalog.json',
      'derived_from':[
        'data/source/sportstiming/class-catalog.json','config/course-versions.json',
        'reports/source-coverage.json','data/derived/analysis-capabilities.json',
        'reports/tracedetrail-public-geometry-analysis.json (when available)'
      ],
      'rules':[
        'The curated source catalog is never modified by this builder.',
        'Observed Sportstiming and route capability fields override stale placeholder status only in this derived output.',
        'course_version comes only from config/course-versions.json assignments.',
        'Feature readiness is source-driven and does not imply that the production UI/import has already been implemented.'
      ],
      'races':rows
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Enriched race catalog','',
           'Derived handoff view. `config/race-catalog.json` remains the curated source of race facts.','',
           '| År | Familj | Sportstiming round | splits | course version | route geometry | resultat |',
           '|---:|---|---:|---|---|---|---|']
    for r in rows:
        result='detail' if r.get('result_detail_status')=='participant_detail_observed' else ('relay-adapter' if r.get('result_detail_status')=='team_or_relay_adapter_needed' else 'class')
        lines.append(f"| {r['year']} | `{r['race_family']}` | {r.get('sportstiming_distance_id') or '—'} | {r.get('timing_split_status') or '—'} | `{r.get('course_version') or '—'}` | {r.get('route_geometry_status') or '—'} | {result} |")
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Built enriched catalog for {len(rows)} races')

if __name__=='__main__': main()
