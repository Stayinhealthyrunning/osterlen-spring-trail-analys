#!/usr/bin/env python3
"""Build an engine-ready curated ÖST database from the immutable frozen archive.

No network access is used. The frozen Sportstiming archive remains the source of
truth. This derived database:
- upgrades UNKNOWN to DNF/DNS/DSQ only from explicit frozen source evidence,
- recovers published bibs from list rows when available,
- carries individual Ultra splits,
- parses Duo team split tables from the frozen team details,
- preserves Duo member rows with source sequence but does not invent leg numbers,
- adds year-specific checkpoint semantics and Bengtemölla service-window candidates,
- provides race/participant/team tables and audit-friendly provenance.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse, gzip, hashlib, json, re, shutil, sqlite3, tempfile

ROOT=Path(__file__).resolve().parents[1]
FROZEN_GZ=ROOT/'data/archive/ost-results-2018-2026.sqlite.gz'
FROZEN_SUMMARY=ROOT/'reports/result-archive-summary.json'
RACE_CATALOG=ROOT/'config/race-catalog.json'
COURSE_VERSIONS=ROOT/'config/course-versions.json'
CHECKPOINT_CONFIG=ROOT/'config/checkpoint-normalization.json'
DUO_EVIDENCE=ROOT/'reports/duo-member-evidence.json'
OUT_GZ=ROOT/'data/derived/ost-analysis-2018-2026.sqlite.gz'
OUT_JSON=ROOT/'reports/curated-analysis-db-summary.json'
OUT_MD=ROOT/'reports/curated-analysis-db-summary.md'

STATUS_PATTERNS={
 'DNF':[r'\butgått\b',r'\bdnf\b',r'\bbrutit\b',r'\bbröt\b',r'\bretired\b',r'\bdid not finish\b'],
 'DNS':[r'\bdns\b',r'\bej start(?:at)?\b',r'\binte start(?:at)?\b',r'\bdid not start\b',r'\bno start\b'],
 'DSQ':[r'\bdsq\b',r'\bdq\b',r'\bdiskval\w*\b',r'\bdisqual\w*\b'],
}
STATUS_RE={k:[re.compile(p,re.I) for p in ps] for k,ps in STATUS_PATTERNS.items()}
MEMBER_LINK_RE=re.compile(r'/event/\d+/app/results/(\d+)$')


def sha256_file(path:Path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def parse_seconds(v):
 if not v:return None
 m=re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d{2})',str(v).strip())
 if not m:return None
 return int(m.group(1) or 0)*3600+int(m.group(2))*60+int(m.group(3))

def parse_distance(v):
 if not v:return None
 m=re.search(r'(\d+(?:[.,]\d+)?)\s*km',str(v),re.I)
 return float(m.group(1).replace(',','.')) if m else None

def parse_ranks(v):
 nums=[int(x) for x in re.findall(r'\d+',v or '')]
 return (nums+[None,None,None])[:3]

def slug(v):
 import unicodedata
 s=unicodedata.normalize('NFKD',v or '').encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]+','-',s).strip('-')

def collect_text(obj):
 vals=[]
 if isinstance(obj,dict):
  for v in obj.values():vals.extend(collect_text(v))
 elif isinstance(obj,list):
  for v in obj:vals.extend(collect_text(v))
 elif isinstance(obj,str):vals.append(obj)
 return vals

def explicit_status(*objects):
 text='\n'.join(x for obj in objects for x in collect_text(obj))
 found=[]
 for status,patterns in STATUS_RE.items():
  if any(p.search(text) for p in patterns):found.append(status)
 return found[0] if len(found)==1 else None

def list_value(rec,label):
 headers=rec.get('list_headers') or []; row=rec.get('list_row') or []
 norm=lambda s:re.sub(r'\s+',' ',str(s or '').strip()).lower()
 wanted=norm(label)
 for i,h in enumerate(headers):
  if norm(h)==wanted and i<len(row):return (row[i].get('text') or '').strip() or None
 return None

def text(c):return (c.get('text') or '').strip()

def pair_map(tables):
 out={}
 for t in tables:
  for row in t.get('rows',[]):
   vals=[text(c) for c in row]
   if len(vals)>=2 and vals[0]:out[vals[0]]=vals[1]
 return out

def checkpoint_index():
 cfg=json.loads(CHECKPOINT_CONFIG.read_text(encoding='utf-8'));idx={}
 for m in cfg.get('mappings',[]):
  for y in m.get('years',[]):
   for label in m.get('source_labels',[]):idx[(int(y),label)]={k:v for k,v in m.items() if k not in ('years','source_labels')}
 return cfg,idx

def checkpoint_semantics(year,label,idx):
 m=idx.get((int(year),label))
 if not m:return {'semantic_key':None,'landmark_key':None,'role':'unmapped_source_checkpoint','analysis_primary':None,'mapping_confidence':None}
 sem=m.get('semantic_key')
 return {'semantic_key':sem,'landmark_key':m.get('canonical_landmark_key') or (sem if sem not in (None,'finish') else None),'role':m.get('role'),'analysis_primary':m.get('analysis_primary'),'mapping_confidence':m.get('confidence')}

def parse_team_splits(year,raw,idx):
 out=[]
 for t in raw.get('tables',[]):
  if 'splits-table' not in (t.get('class') or ''):continue
  for row in t.get('rows',[]):
   vals=[text(c) for c in row]
   if len(vals)<8:continue
   label=vals[0]
   if not label or label in ('Distans','Totalt') or label.startswith('Mellantid'):continue
   sem=checkpoint_semantics(year,label,idx); seg_rank=parse_ranks(vals[4] if len(vals)>4 else ''); cum_rank=parse_ranks(vals[7] if len(vals)>7 else '')
   elapsed=parse_seconds(vals[6] if len(vals)>6 else None)
   # Preserve published rows even when elapsed is absent; analysis layers may filter them.
   out.append({'source_label':label,'checkpoint_key':slug(label),**sem,'reported_distance_km':parse_distance(label),'segment_distance_km':parse_distance(vals[1] if len(vals)>1 else None),
               'segment_seconds':parse_seconds(vals[3] if len(vals)>3 else None),'segment_place_overall':seg_rank[0],'segment_place_gender':seg_rank[1],'segment_place_class':seg_rank[2],
               'segment_pace_source':vals[5] if len(vals)>5 and vals[5] else None,'elapsed_seconds':elapsed,'place_overall':cum_rank[0],'place_gender':cum_rank[1],'place_class':cum_rank[2],
               'clock_time':vals[8] if len(vals)>8 and vals[8] else None,'raw_cells':vals})
 return out

def parse_team_members(raw):
 out=[]
 for t in raw.get('tables',[]):
  header=None;idx={}
  for row in t.get('rows',[]):
   if row and all((c.get('tag') or '').lower()=='th' for c in row):
    header=[text(c) for c in row];idx={h:i for i,h in enumerate(header) if h};continue
   if not header or 'Startnummer' not in idx or 'Namn' not in idx:continue
   vals=[text(c) for c in row];ni=idx['Namn'];bi=idx['Startnummer']
   if ni>=len(vals) or not vals[ni]:continue
   ext=None
   for href in row[ni].get('links',[]):
    m=MEMBER_LINK_RE.search(href)
    if m:ext=m.group(1);break
   out.append({'name':vals[ni],'bib':vals[bi] if bi<len(vals) and vals[bi] else None,'source_member_result_id':ext,
               'member_time_seconds':parse_seconds(vals[idx['Tid']]) if 'Tid' in idx and idx['Tid']<len(vals) else None,
               'finish_clock':vals[idx['Sluttidspunkt']] if 'Sluttidspunkt' in idx and idx['Sluttidspunkt']<len(vals) and vals[idx['Sluttidspunkt']] else None,
               'speed_source':vals[idx['Hastighet']] if 'Hastighet' in idx and idx['Hastighet']<len(vals) and vals[idx['Hastighet']] else None})
 return out

def create_schema(con):
 con.executescript('''
 PRAGMA foreign_keys=ON;
 CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
 CREATE TABLE races(
   race_key TEXT PRIMARY KEY,event_key TEXT NOT NULL,year INTEGER NOT NULL,race_family TEXT NOT NULL,race_type TEXT NOT NULL,
   event_id INTEGER,source_race_name TEXT,race_date TEXT,scheduled_start_local TEXT,nominal_distance_km REAL,
   canonical_family_distance_km REAL,course_version TEXT,route_family_ref TEXT,route_asset_available INTEGER,source_json TEXT NOT NULL,
   UNIQUE(year,race_family)
 );
 CREATE TABLE participants(
   participant_uid TEXT PRIMARY KEY,race_key TEXT NOT NULL REFERENCES races(race_key),source_result_id TEXT NOT NULL,bib TEXT,name TEXT NOT NULL,
   sex TEXT,age INTEGER,birth_year INTEGER,age_category TEXT,club TEXT,country TEXT,
   identity_scope TEXT NOT NULL DEFAULT 'race_result',identity_status TEXT NOT NULL DEFAULT 'source_local',
   UNIQUE(race_key,source_result_id)
 );
 CREATE TABLE relay_teams(
   team_uid TEXT PRIMARY KEY,race_key TEXT NOT NULL REFERENCES races(race_key),source_result_id TEXT NOT NULL,bib TEXT,team_name TEXT NOT NULL,class_name TEXT,
   UNIQUE(race_key,source_result_id)
 );
 CREATE TABLE results(
   result_uid TEXT PRIMARY KEY,race_key TEXT NOT NULL REFERENCES races(race_key),year INTEGER NOT NULL,race_family TEXT NOT NULL,
   source_result_id TEXT NOT NULL,entity_type TEXT NOT NULL,participant_uid TEXT REFERENCES participants(participant_uid),team_uid TEXT REFERENCES relay_teams(team_uid),
   bib TEXT,name_as_published TEXT NOT NULL,sex TEXT,age INTEGER,age_category TEXT,club TEXT,country TEXT,source_class TEXT,
   status TEXT NOT NULL,status_source TEXT NOT NULL,status_evidence TEXT,finish_seconds REAL,gross_seconds REAL,net_seconds REAL,
   overall_place INTEGER,gender_place INTEGER,class_place INTEGER,start_clock TEXT,finish_clock TEXT,date_source TEXT,pace_source TEXT,speed_source TEXT,
   source_url TEXT,source_sha256 TEXT,source_normalized_json TEXT NOT NULL,
   UNIQUE(race_key,source_result_id)
 );
 CREATE TABLE splits(
   result_uid TEXT NOT NULL REFERENCES results(result_uid) ON DELETE CASCADE,sequence_no INTEGER NOT NULL,source_kind TEXT NOT NULL,
   checkpoint_source_label TEXT,checkpoint_key TEXT,checkpoint_semantic_key TEXT,canonical_landmark_key TEXT,checkpoint_role TEXT,
   analysis_primary INTEGER,mapping_confidence TEXT,reported_checkpoint_distance_km REAL,segment_distance_km REAL,segment_seconds REAL,
   segment_place_overall INTEGER,segment_place_gender INTEGER,segment_place_class INTEGER,segment_pace_source TEXT,
   elapsed_seconds REAL,place_overall INTEGER,place_gender INTEGER,place_class INTEGER,clock_time TEXT,raw_json TEXT NOT NULL,
   PRIMARY KEY(result_uid,sequence_no)
 );
 CREATE TABLE derived_metrics(
   result_uid TEXT NOT NULL REFERENCES results(result_uid) ON DELETE CASCADE,metric_key TEXT NOT NULL,seconds REAL,
   interpretation TEXT,classification TEXT,raw_json TEXT NOT NULL,PRIMARY KEY(result_uid,metric_key)
 );
 CREATE TABLE relay_members(
   member_uid TEXT PRIMARY KEY,team_uid TEXT NOT NULL REFERENCES relay_teams(team_uid) ON DELETE CASCADE,source_sequence INTEGER NOT NULL,
   source_member_result_id TEXT,bib TEXT,name_as_published TEXT NOT NULL,member_time_seconds REAL,finish_clock TEXT,speed_source TEXT,
   leg_no INTEGER,assignment_status TEXT NOT NULL,source_json TEXT NOT NULL,UNIQUE(team_uid,source_sequence)
 );
 CREATE INDEX idx_results_race_status ON results(race_key,status);
 CREATE INDEX idx_results_family_year ON results(race_family,year);
 CREATE INDEX idx_results_finish ON results(race_key,finish_seconds);
 CREATE INDEX idx_participants_name ON participants(name);
 CREATE INDEX idx_splits_semantic ON splits(checkpoint_semantic_key);
 CREATE INDEX idx_splits_result ON splits(result_uid);
 CREATE VIEW v_race_status_counts AS SELECT race_key,status,COUNT(*) AS n FROM results GROUP BY race_key,status;
 CREATE VIEW v_split_coverage AS SELECT r.race_key,s.checkpoint_semantic_key,s.checkpoint_source_label,COUNT(*) AS passages FROM splits s JOIN results r USING(result_uid) GROUP BY r.race_key,s.checkpoint_semantic_key,s.checkpoint_source_label;
 ''')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT_GZ.relative_to(ROOT)));args=ap.parse_args()
 frozen_summary=json.loads(FROZEN_SUMMARY.read_text(encoding='utf-8'))
 races_cfg=json.loads(RACE_CATALOG.read_text(encoding='utf-8'))['races'];course_cfg=json.loads(COURSE_VERSIONS.read_text(encoding='utf-8'))
 cp_cfg,cp_idx=checkpoint_index()
 assignment={(int(x['year']),x['family']):x for x in course_cfg.get('assignments',[])}
 duo_evidence=json.loads(DUO_EVIDENCE.read_text(encoding='utf-8')) if DUO_EVIDENCE.exists() else {}
 allow_leg_assignment=bool(duo_evidence.get('interpretation',{}).get('leg_order_can_be_assigned_when_two_rows_present',False))
 outgz=ROOT/args.output;outgz.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='ost-curated-') as td:
  td=Path(td);srcdb=td/'source.sqlite';dstdb=td/'curated.sqlite'
  with gzip.open(FROZEN_GZ,'rb') as f,srcdb.open('wb') as o:shutil.copyfileobj(f,o)
  src=sqlite3.connect(srcdb);src.row_factory=sqlite3.Row
  dst=sqlite3.connect(dstdb);create_schema(dst)
  created=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
  meta={'schema_version':'1','event_key':'osterlen-spring-trail','created_at_utc':created,'source_archive_path':str(FROZEN_GZ.relative_to(ROOT)),
        'source_archive_gzip_sha256':sha256_file(FROZEN_GZ),'source_archive_database_sha256':frozen_summary['database_sha256'],
        'status_policy':'FINISHED retained; UNKNOWN promoted only from exactly one explicit DNF/DNS/DSQ source status; otherwise UNKNOWN.',
        'relay_member_policy':'Preserve published member rows and source_sequence. leg_no remains NULL unless aggregate evidence validates ordering.',
        'duo_leg_order_validated':json.dumps(allow_leg_assignment).lower()}
  dst.executemany('INSERT INTO meta VALUES(?,?)',meta.items())
  race_lookup={}
  for r in races_cfg:
   y=int(r['year']);fam=r['race_family'];a=assignment.get((y,fam),{});cv=a.get('course_version_id') or r.get('course_version')
   route_available=a.get('route_asset_available')
   dst.execute('INSERT INTO races VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
    r['race_key'],r.get('event_key','osterlen-spring-trail'),y,fam,r['race_type'],r.get('sportstiming_event_id'),r.get('source_race_name'),r.get('race_date'),r.get('scheduled_start_local'),
    r.get('nominal_distance_km'),r.get('canonical_family_distance_km'),cv,r.get('route_family_ref'),None if route_available is None else int(bool(route_available)),json.dumps(r,ensure_ascii=False,separators=(',',':'))))
   race_lookup[(y,fam)]=r['race_key']

  # Lookup list-row source records from embedded immutable snapshots.
  source_records={}
  for imp in src.execute('SELECT year,race_family,snapshot_json FROM imports'):
   snap=json.loads(imp['snapshot_json'])
   for rec in snap.get('results',[]):source_records[(int(imp['year']),imp['race_family'],str(rec.get('sportstiming_result_id') or ''))]=rec

  status_counts=Counter();status_promotions=Counter();individual_split_count=0;duo_split_count=0;member_count=0;service_metrics=0
  for rr in src.execute('SELECT * FROM results ORDER BY year,race_family,result_uid'):
   y=int(rr['year']);fam=rr['race_family'];race_key=race_lookup[(y,fam)];rid=str(rr['source_result_id']);norm=json.loads(rr['normalized_json']);srec=source_records.get((y,fam,rid),{})
   bib=rr['bib'] or list_value(srec,'Startnummer') or list_value(srec,'Startnr') or list_value(srec,'Startnr.') or list_value(srec,'Startnummer.')
   category=list_value(srec,'Kategori')
   sex=rr['gender'];age_category=rr['age_category']
   if rr['entity_type']=='athlete' and category:
    cm=re.fullmatch(r'([FM])(\d{1,2}-\d{1,2})',category)
    if cm:
     if not sex:sex=cm.group(1)
     if not age_category:age_category=category
   club=rr['club'] or list_value(srec,'Klubb/Firma/Sponsor')
   country=rr['country'] or list_value(srec,'Land')
   status=rr['status'];status_source='frozen_normalized';status_evidence=None
   if status=='UNKNOWN':
    source_detail=norm.get('raw_tables',norm.get('raw_record',{}).get('tables',[]));explicit=explicit_status(source_detail,srec.get('list_row',[]))
    if explicit:
     status=explicit;status_source='explicit_frozen_source_text';status_evidence='Explicit canonical status keyword found in frozen detail/list source surfaces.';status_promotions[explicit]+=1
   status_counts[status]+=1
   uid=rr['result_uid'];entity=rr['entity_type'];participant_uid=None;team_uid=None
   if entity=='athlete':
    participant_uid='p:'+uid
    dst.execute('INSERT INTO participants VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(participant_uid,race_key,rid,bib,rr['name'],sex,rr['age'],None,age_category,club,country,'race_result','source_local'))
   else:
    team_uid='team:'+uid
    dst.execute('INSERT INTO relay_teams VALUES(?,?,?,?,?,?)',(team_uid,race_key,rid,bib,rr['name'],category or rr['source_class']))
   dst.execute('''INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
    uid,race_key,y,fam,rid,entity,participant_uid,team_uid,bib,rr['name'],sex,rr['age'],age_category,club,country,category or rr['source_class'],status,status_source,status_evidence,
    rr['finish_seconds'],rr['gross_seconds'],rr['net_seconds'],rr['overall_place'],rr['gender_place'],rr['class_place'],rr['start_clock'],rr['finish_clock'],rr['date_source'],rr['pace_source'],rr['speed_source'],rr['source_url'],rr['source_sha256'],rr['normalized_json']))

   splits=[]
   if fam=='duo60':
    raw=norm.get('raw_record',{});splits=parse_team_splits(y,raw,cp_idx)
    members=parse_team_members(raw)
    for seq,m in enumerate(members,1):
     leg_no=seq if allow_leg_assignment and len(members)==2 else None
     assign='validated_leg_order' if leg_no else 'source_sequence_only'
     muid=f'{team_uid}:member:{seq}'
     dst.execute('INSERT INTO relay_members VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(muid,team_uid,seq,m.get('source_member_result_id'),m.get('bib'),m['name'],m.get('member_time_seconds'),m.get('finish_clock'),m.get('speed_source'),leg_no,assign,json.dumps(m,ensure_ascii=False,separators=(',',':'))))
     member_count+=1
    duo_split_count+=len(splits)
   else:
    for s in src.execute('SELECT * FROM splits WHERE result_uid=? ORDER BY sequence_no',(uid,)):
     splits.append({'source_label':s['checkpoint_source_label'],'checkpoint_key':s['checkpoint_key'],'semantic_key':s['checkpoint_semantic_key'],'landmark_key':s['canonical_landmark_key'],'role':s['checkpoint_role'],
                    'analysis_primary':s['analysis_primary'],'mapping_confidence':None,'reported_distance_km':s['reported_checkpoint_distance_km'],'segment_distance_km':s['segment_distance_km'],'segment_seconds':s['segment_seconds'],
                    'segment_place_overall':s['segment_place_overall'],'segment_place_gender':s['segment_place_gender'],'segment_place_class':s['segment_place_class'],'segment_pace_source':s['segment_pace_source'],
                    'elapsed_seconds':s['elapsed_seconds'],'place_overall':s['place_overall'],'place_gender':s['place_gender'],'place_class':s['place_class'],'clock_time':s['clock_time'],'raw_json':s['raw_json']})
    individual_split_count+=len(splits)
   for seq,s in enumerate(splits,1):
    dst.execute('INSERT INTO splits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
     uid,seq,'duo_raw_team_detail' if fam=='duo60' else 'frozen_individual_normalized',s.get('source_label'),s.get('checkpoint_key'),s.get('semantic_key'),s.get('landmark_key'),s.get('role'),
     s.get('analysis_primary'),s.get('mapping_confidence'),s.get('reported_distance_km'),s.get('segment_distance_km'),s.get('segment_seconds'),s.get('segment_place_overall'),s.get('segment_place_gender'),s.get('segment_place_class'),s.get('segment_pace_source'),
     s.get('elapsed_seconds'),s.get('place_overall'),s.get('place_gender'),s.get('place_class'),s.get('clock_time'),s.get('raw_json') or json.dumps(s,ensure_ascii=False,separators=(',',':'))))
   # Existing frozen individual derived metrics.
   for m in src.execute('SELECT * FROM derived_metrics WHERE result_uid=?',(uid,)):
    dst.execute('INSERT OR REPLACE INTO derived_metrics VALUES(?,?,?,?,?,?)',(uid,m['metric_key'],m['seconds'],m['interpretation'],m['classification'],m['raw_json']));service_metrics+=1
   # Duo service-window candidate from actual team split observations.
   if fam=='duo60' and y in (2022,2023):
    bysem={s.get('semantic_key'):s for s in splits if s.get('semantic_key')}
    a=bysem.get('bengtemolla_approach');b=bysem.get('bengtemolla')
    if a and b and a.get('elapsed_seconds') is not None and b.get('elapsed_seconds') is not None and b['elapsed_seconds']>=a['elapsed_seconds']:
     val=b['elapsed_seconds']-a['elapsed_seconds'];raw={'from':'bengtemolla_approach','to':'bengtemolla','seconds':val}
     dst.execute('INSERT OR REPLACE INTO derived_metrics VALUES(?,?,?,?,?,?)',(uid,'bengtemolla_service_window_seconds',val,'Elapsed time between the 32 km observation and named Bengtemölla; operational phase remains unverified.','between_timing_observations_not_pure_dwell',json.dumps(raw,separators=(',',':'))));service_metrics+=1

  dst.commit()
  integrity=dst.execute('PRAGMA integrity_check').fetchone()[0]
  totals={
   'races':dst.execute('SELECT COUNT(*) FROM races').fetchone()[0],
   'results':dst.execute('SELECT COUNT(*) FROM results').fetchone()[0],
   'participants':dst.execute('SELECT COUNT(*) FROM participants').fetchone()[0],
   'relay_teams':dst.execute('SELECT COUNT(*) FROM relay_teams').fetchone()[0],
   'relay_members':dst.execute('SELECT COUNT(*) FROM relay_members').fetchone()[0],
   'splits':dst.execute('SELECT COUNT(*) FROM splits').fetchone()[0],
   'derived_metrics':dst.execute('SELECT COUNT(*) FROM derived_metrics').fetchone()[0],
  }
  checks={
   'integrity':integrity,
   'result_count_matches_frozen':totals['results']==frozen_summary['total_results'],
   'race_count_expected_34':totals['races']==34,
   'orphan_results':dst.execute('SELECT COUNT(*) FROM results r LEFT JOIN races q ON q.race_key=r.race_key WHERE q.race_key IS NULL').fetchone()[0],
   'orphan_splits':dst.execute('SELECT COUNT(*) FROM splits s LEFT JOIN results r ON r.result_uid=s.result_uid WHERE r.result_uid IS NULL').fetchone()[0],
   'finished_without_time':dst.execute("SELECT COUNT(*) FROM results WHERE status='FINISHED' AND (finish_seconds IS NULL OR finish_seconds<=0)").fetchone()[0],
   'dnf_with_positive_finish_time':dst.execute("SELECT COUNT(*) FROM results WHERE status='DNF' AND finish_seconds IS NOT NULL AND finish_seconds>0").fetchone()[0],
   'split_chronology_errors':dst.execute('''SELECT COUNT(*) FROM splits a JOIN splits b ON a.result_uid=b.result_uid AND b.sequence_no=a.sequence_no+1 WHERE a.elapsed_seconds IS NOT NULL AND b.elapsed_seconds IS NOT NULL AND b.elapsed_seconds<a.elapsed_seconds''').fetchone()[0],
   'duo_members_with_assigned_leg':dst.execute('SELECT COUNT(*) FROM relay_members WHERE leg_no IS NOT NULL').fetchone()[0],
  }
  dst.execute('VACUUM');dst.close();src.close()
  hard_ok=integrity=='ok' and checks['result_count_matches_frozen'] and checks['race_count_expected_34'] and checks['orphan_results']==0 and checks['orphan_splits']==0 and checks['finished_without_time']==0 and checks['split_chronology_errors']==0
  if not hard_ok:raise SystemExit(f'Curated database checks failed: {checks}')
  with dstdb.open('rb') as inf,outgz.open('wb') as outf:
   with gzip.GzipFile(filename='',mode='wb',fileobj=outf,compresslevel=9,mtime=0) as z:shutil.copyfileobj(inf,z)
  db_sha=sha256_file(dstdb);gz_sha=sha256_file(outgz);db_bytes=dstdb.stat().st_size

 summary={'schema_version':1,'generated_at':created,'source_frozen_archive':str(FROZEN_GZ.relative_to(ROOT)),'source_frozen_archive_sha256':sha256_file(FROZEN_GZ),
          'curated_archive':str(outgz.relative_to(ROOT)),'curated_database_sha256':db_sha,'curated_archive_sha256':gz_sha,'database_bytes':db_bytes,'compressed_bytes':outgz.stat().st_size,
          'totals':totals,'status_counts':dict(status_counts),'status_promotions_from_explicit_source':dict(status_promotions),'individual_splits_carried':individual_split_count,'duo_splits_parsed':duo_split_count,
          'relay_member_rows':member_count,'duo_leg_numbers_assigned':checks['duo_members_with_assigned_leg'],'checks':checks,
          'policies':{'source_archive_immutable':True,'remaining_unknown_not_inferred':True,'duo_member_source_sequence_preserved':True,'duo_leg_number_requires_validated_evidence':True}}
 OUT_JSON.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 lines=['# Kuraterad ÖST-analysdatabas','',f"Skapad: {created}",'',f"- Resultat: **{totals['results']:,}**",f"- Deltagarposter: **{totals['participants']:,}**",f"- Duo-lag: **{totals['relay_teams']:,}**",f"- Publicerade Duo-medlemsrader: **{totals['relay_members']:,}**",f"- Mellantider totalt: **{totals['splits']:,}**",f"- varav Duo-splits parserade från fryst teamdata: **{duo_split_count:,}**",f"- Härledda checkpointmått: **{totals['derived_metrics']:,}**",'', '## Status','']
 for k,v in sorted(status_counts.items()):lines.append(f'- **{k}:** {v:,}')
 lines += ['',f"Explicit källstatus uppgraderade {sum(status_promotions.values()):,} tidigare UNKNOWN-poster: "+', '.join(f'{k}={v}' for k,v in sorted(status_promotions.items()))+'.',
           '', '## Duo','',f"- Medlemsrader med tilldelat `leg_no`: **{checks['duo_members_with_assigned_leg']}**.",'- Medlemsradernas källordning bevaras även när etappnummer inte kan bevisas.','', '## Validering','']
 for k,v in checks.items():lines.append(f'- `{k}`: **{v}**')
 OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
