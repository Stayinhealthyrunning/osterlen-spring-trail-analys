#!/usr/bin/env python3
"""Derive analysis-feature readiness from observed source coverage.

This is a planning artifact for the future generic frontend. `source_ready` means the
required source evidence exists; it does not mean the final production dataset or UI
has already been built.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json

ROOT=Path(__file__).resolve().parents[1]
COVERAGE_PATH=ROOT/'reports/source-coverage.json'
POLICY_PATH=ROOT/'config/analysis-feature-policy.json'
VERSIONS_PATH=ROOT/'config/course-versions.json'
OUT=ROOT/'data/derived/analysis-capabilities.json'
OUT_MD=ROOT/'reports/analysis-capabilities.md'


def route_ready(row):
    return row.get('route_geometry_status') in {'archived','via_same_year_ultra60'}


def course_version_index():
    if not VERSIONS_PATH.exists(): return {}
    cfg=json.loads(VERSIONS_PATH.read_text(encoding='utf-8'))
    return {(int(a['year']),a['family']):a.get('course_version_id') for a in cfg.get('assignments',[])}


def feature_status(row,feature,version_id):
    has_class=bool(row.get('sportstiming_class_observed'))
    detail=row.get('result_detail_status')
    split=row.get('timing_split_status')=='split_table_observed'
    split_n=int(row.get('observed_split_count') or 0)
    geometry=route_ready(row)

    if feature in {'results_database','finish_statistics','cross_year_participation'}:
        return ('source_ready' if has_class else 'blocked_pending_source',
                'Sportstiming class discovered.' if has_class else 'No Sportstiming class observed.')
    if feature=='runner_profile':
        if detail=='participant_detail_observed': return 'source_ready','Participant detail page observed.'
        if detail=='team_or_relay_adapter_needed': return 'adapter_needed','Relay/team result format needs a dedicated adapter.'
        return 'blocked_pending_source','Participant/team detail page not observed.'
    if feature=='split_analysis':
        if split: return 'source_ready',f'{split_n} published split/checkpoint labels observed in sampled result.'
        return 'not_available_in_sample','No split table observed in the sampled result for this class.'
    if feature in {'runner_replay','map_duel','course_difficulty_vs_pacing'}:
        missing=[]
        if not split: missing.append('published splits')
        if split_n<2: missing.append('at least two observed checkpoints')
        if not geometry: missing.append('archived route geometry')
        if not missing: return 'source_ready','Published checkpoints and archived route geometry are both available.'
        return 'blocked_pending_source','Missing: '+', '.join(missing)+'.'
    if feature=='course_version_records':
        if not has_class: return 'blocked_pending_source','No Sportstiming class observed.'
        if not version_id: return 'blocked_pending_geometry','Course version is not yet assigned.'
        return 'source_ready',f'Assigned to verified course version {version_id}.'
    return 'unknown','No readiness rule implemented.'


def main():
    if not COVERAGE_PATH.exists():
        raise SystemExit('Run tools/source_coverage.py first')
    coverage=json.loads(COVERAGE_PATH.read_text(encoding='utf-8'))
    policy=json.loads(POLICY_PATH.read_text(encoding='utf-8'))
    versions=course_version_index()
    features=list(policy['features'])
    rows=[]
    for source_row in coverage.get('rows',[]):
        key=(int(source_row['year']),source_row['family'])
        version_id=versions.get(key)
        statuses={}
        for feature in features:
            status,reason=feature_status(source_row,feature,version_id)
            statuses[feature]={'status':status,'reason':reason}
        rows.append({
          'year':source_row['year'],'family':source_row['family'],
          'course_version_id':version_id,
          'features':statuses,
        })
    payload={
      'schema_version':1,
      'generated_at':datetime.now(timezone.utc).isoformat(),
      'meaning':{
        'source_ready':'Required source evidence exists; production import/UI may still be pending.',
        'adapter_needed':'Source exists but a format-specific adapter is still needed.',
        'blocked_pending_source':'Required source evidence is missing or not yet recovered.',
        'blocked_pending_geometry':'Results exist but route comparability/course-version assignment is unresolved.',
        'not_available_in_sample':'The sampled result did not expose the required source structure; do not fabricate it.'
      },
      'rows':rows
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    lines=['# Analysis capability matrix','',
           '`source_ready` betyder att källdata som krävs har observerats. Det betyder inte att slutlig import eller UI redan är färdig.','',
           '| År | Familj | Resultat | Profil | Splits | Replay | Kartduell | Bana+pacing | Banversionsrekord |',
           '|---:|---|---|---|---|---|---|---|---|']
    short={
      'source_ready':'✓ source-ready','adapter_needed':'adapter',
      'blocked_pending_source':'saknas','blocked_pending_geometry':'bana?',
      'not_available_in_sample':'ej observerat','unknown':'?'
    }
    for row in rows:
        f=row['features']
        vals=[
          short.get(f['results_database']['status'],f['results_database']['status']),
          short.get(f['runner_profile']['status'],f['runner_profile']['status']),
          short.get(f['split_analysis']['status'],f['split_analysis']['status']),
          short.get(f['runner_replay']['status'],f['runner_replay']['status']),
          short.get(f['map_duel']['status'],f['map_duel']['status']),
          short.get(f['course_difficulty_vs_pacing']['status'],f['course_difficulty_vs_pacing']['status']),
          short.get(f['course_version_records']['status'],f['course_version_records']['status']),
        ]
        lines.append(f"| {row['year']} | `{row['family']}` | "+' | '.join(vals)+' |')
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Built capabilities for {len(rows)} race-year combinations')

if __name__=='__main__': main()
