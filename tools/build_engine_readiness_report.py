#!/usr/bin/env python3
"""Build a per-race feature/readiness matrix from the curated ÖST archive.

This report is the bridge to the future generalized Gotaleden engine. Feature
availability is derived from actual stored results, splits, course versions and
local route assets. Field coverage distinguishes exact age from source-backed age
category so older editions are not overstated or understated.
"""
from __future__ import annotations
from pathlib import Path
import gzip, json, shutil, sqlite3, tempfile

ROOT=Path(__file__).resolve().parents[1]
GZ=ROOT/'data/derived/ost-analysis-2018-2026.sqlite.gz'
OUT=ROOT/'reports/engine-readiness.json'
OUTMD=ROOT/'reports/engine-readiness.md'


def pct(n,d):
 return round(100*n/d,1) if d else 0.0


def main():
 with tempfile.TemporaryDirectory(prefix='ost-ready-') as td:
  db=Path(td)/'a.sqlite'
  with gzip.open(GZ,'rb') as f,db.open('wb') as o:shutil.copyfileobj(f,o)
  con=sqlite3.connect(db);con.row_factory=sqlite3.Row
  rows=[]
  for race in con.execute('SELECT * FROM races ORDER BY year,race_family'):
   rk=race['race_key']
   q=lambda sql:con.execute(sql,(rk,)).fetchone()[0]
   results=q('SELECT COUNT(*) FROM results WHERE race_key=?')
   finished=q("SELECT COUNT(*) FROM results WHERE race_key=? AND status='FINISHED'")
   dnf=q("SELECT COUNT(*) FROM results WHERE race_key=? AND status='DNF'")
   unknown=q("SELECT COUNT(*) FROM results WHERE race_key=? AND status='UNKNOWN'")
   splits=q('SELECT COUNT(*) FROM splits s JOIN results r USING(result_uid) WHERE r.race_key=? AND s.elapsed_seconds IS NOT NULL')
   split_results=q('SELECT COUNT(DISTINCT s.result_uid) FROM splits s JOIN results r USING(result_uid) WHERE r.race_key=? AND s.elapsed_seconds IS NOT NULL')
   semantic_checkpoints=q("SELECT COUNT(DISTINCT s.checkpoint_semantic_key) FROM splits s JOIN results r USING(result_uid) WHERE r.race_key=? AND s.elapsed_seconds IS NOT NULL AND s.checkpoint_semantic_key IS NOT NULL")
   source_checkpoints=q('SELECT COUNT(DISTINCT s.checkpoint_source_label) FROM splits s JOIN results r USING(result_uid) WHERE r.race_key=? AND s.elapsed_seconds IS NOT NULL')
   bib_known=q("SELECT COUNT(*) FROM results WHERE race_key=? AND bib IS NOT NULL AND TRIM(bib)<>''")
   gender_known=q("SELECT COUNT(*) FROM results WHERE race_key=? AND sex IS NOT NULL AND TRIM(sex)<>''")
   age_known=q('SELECT COUNT(*) FROM results WHERE race_key=? AND age IS NOT NULL')
   agecat_known=q("SELECT COUNT(*) FROM results WHERE race_key=? AND age_category IS NOT NULL AND TRIM(age_category)<>''")
   club_known=q("SELECT COUNT(*) FROM results WHERE race_key=? AND club IS NOT NULL AND TRIM(club)<>''")
   country_known=q("SELECT COUNT(*) FROM results WHERE race_key=? AND country IS NOT NULL AND TRIM(country)<>''")
   class_known=q("SELECT COUNT(*) FROM results WHERE race_key=? AND source_class IS NOT NULL AND TRIM(source_class)<>''")
   relay_members=q('SELECT COUNT(*) FROM relay_members m JOIN relay_teams t ON t.team_uid=m.team_uid WHERE t.race_key=?') if race['race_type']=='relay' else 0
   local_route=bool(race['route_asset_available']);course=bool(race['course_version'])
   split_ready=splits>0 and split_results>0
   replay_ready=split_ready and local_route and semantic_checkpoints>=2
   rec={
    'race_key':rk,'year':race['year'],'race_family':race['race_family'],'race_type':race['race_type'],'course_version':race['course_version'],
    'route_asset_available':local_route,'results':results,'finished':finished,'dnf':dnf,'unknown':unknown,'split_passages':splits,'results_with_splits':split_results,
    'semantic_checkpoint_count':semantic_checkpoints,'source_checkpoint_count':source_checkpoints,'relay_member_rows':relay_members,
    'field_counts':{'bib':bib_known,'gender':gender_known,'age_exact':age_known,'age_category':agecat_known,'club':club_known,'country':country_known,'source_class':class_known},
    'field_coverage_pct':{
      'bib':pct(bib_known,results),'gender':pct(gender_known,results),'age_exact':pct(age_known,results),'age_category':pct(agecat_known,results),
      'club':pct(club_known,results),'country':pct(country_known,results),'source_class':pct(class_known,results),
    },
    'features':{
      'results_database':results>0,
      'finish_statistics':finished>0,
      'runner_or_team_profile':results>0,
      'split_analysis':split_ready,
      'runner_replay':replay_ready,
      'map_duel':replay_ready,
      'course_difficulty_vs_pacing':replay_ready,
      'course_version_records':course and finished>0,
      'cross_year_participation':results>0,
      'relay_member_display':race['race_type']=='relay' and relay_members>0,
      'relay_leg_assignment':False if race['race_type']=='relay' else None,
    }
   }
   rows.append(rec)
  con.close()
 summary={
  'schema_version':2,
  'source':'data/derived/ost-analysis-2018-2026.sqlite.gz',
  'rule':'Feature flags are derived from the curated archive. Route-dependent features require a local usable route asset; relay leg assignment remains disabled until leg ordering is source-verified. Exact age and age-category coverage are reported separately.',
  'races':rows,
  'totals':{
   'races':len(rows),'results':sum(r['results'] for r in rows),'split_passages':sum(r['split_passages'] for r in rows),
   'races_with_split_analysis':sum(r['features']['split_analysis'] for r in rows),
   'races_with_replay_ready_data':sum(r['features']['runner_replay'] for r in rows),
   'races_with_course_version':sum(r['course_version'] is not None for r in rows),
   'results_with_bib':sum(r['field_counts']['bib'] for r in rows),
   'results_with_gender':sum(r['field_counts']['gender'] for r in rows),
   'results_with_exact_age':sum(r['field_counts']['age_exact'] for r in rows),
   'results_with_age_category':sum(r['field_counts']['age_category'] for r in rows),
   'results_with_country':sum(r['field_counts']['country'] for r in rows),
  }
 }
 OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# ÖST – engine readiness','',summary['rule'],'', '| År | Familj | Resultat | DNF | ? | Splitpassager | Splitlöpare/lag | Bana | Lokal rutt | Splitanalys | Replay/kartduell |','|---:|---|---:|---:|---:|---:|---:|---|---|---|---|']
 for r in rows:
  lines.append(f"| {r['year']} | {r['race_family']} | {r['results']} | {r['dnf']} | {r['unknown']} | {r['split_passages']} | {r['results_with_splits']} | {r['course_version'] or '—'} | {'ja' if r['route_asset_available'] else 'nej'} | {'ja' if r['features']['split_analysis'] else 'nej'} | {'ja' if r['features']['runner_replay'] else 'nej'} |")
 lines += ['','## Fälttäckning','', '| År | Familj | Bib % | Kön % | Exakt ålder % | Åldersklass % | Klubb % | Land % | Duo-medlemsrader |','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
 for r in rows:
  c=r['field_coverage_pct'];lines.append(f"| {r['year']} | {r['race_family']} | {c['bib']:.1f} | {c['gender']:.1f} | {c['age_exact']:.1f} | {c['age_category']:.1f} | {c['club']:.1f} | {c['country']:.1f} | {r['relay_member_rows']} |")
 lines += ['','## Totalt','']+[f"- `{k}`: **{v:,}**" for k,v in summary['totals'].items()]
 OUTMD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps(summary['totals'],indent=2))

if __name__=='__main__':main()
