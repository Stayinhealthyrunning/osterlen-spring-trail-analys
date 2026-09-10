#!/usr/bin/env python3
"""Build the frozen multi-year ÖST result archive from fetched Sportstiming snapshots.

Each family/year source snapshot is embedded verbatim as JSON in SQLite, while
normalized result/split tables make later analysis-engine integration cheap.
The database is gzip-compressed for repository storage and audited by summaries.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import argparse, gzip, hashlib, json, shutil, sqlite3

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data/source/sportstiming/class-catalog.json'

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def expected_classes():
    cat=json.loads(CAT.read_text(encoding='utf-8')); out=[]
    for ed in cat['editions']:
        for c in ed['classes']:
            out.append((int(ed['year']),c['race_family'],int(ed['event_id']),str(c['sportstiming_distance_id']),c.get('source_label')))
    return out

def schema(con):
    con.executescript('''
    PRAGMA foreign_keys=ON;
    CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE imports(
      year INTEGER NOT NULL,race_family TEXT NOT NULL,event_id INTEGER NOT NULL,distance_id TEXT NOT NULL,
      entity_type TEXT NOT NULL,source_label TEXT,discovered_count INTEGER NOT NULL,normalized_count INTEGER NOT NULL,
      source_errors INTEGER NOT NULL,snapshot_sha256 TEXT NOT NULL,snapshot_json TEXT NOT NULL,
      PRIMARY KEY(year,race_family)
    );
    CREATE TABLE results(
      result_uid TEXT PRIMARY KEY,year INTEGER NOT NULL,race_family TEXT NOT NULL,event_id INTEGER NOT NULL,distance_id TEXT NOT NULL,
      source_result_id TEXT NOT NULL,entity_type TEXT NOT NULL,name TEXT,bib TEXT,club TEXT,country TEXT,gender TEXT,age INTEGER,
      age_category TEXT,source_class TEXT,status TEXT,distance_km REAL,finish_seconds REAL,gross_seconds REAL,net_seconds REAL,
      overall_place INTEGER,overall_count INTEGER,gender_place INTEGER,gender_count INTEGER,class_place INTEGER,class_count INTEGER,
      start_clock TEXT,finish_clock TEXT,date_source TEXT,speed_source TEXT,pace_source TEXT,source_url TEXT,source_sha256 TEXT,
      normalized_json TEXT NOT NULL,UNIQUE(event_id,entity_type,source_result_id)
    );
    CREATE TABLE splits(
      result_uid TEXT NOT NULL REFERENCES results(result_uid) ON DELETE CASCADE,sequence_no INTEGER NOT NULL,
      checkpoint_source_label TEXT,checkpoint_key TEXT,checkpoint_semantic_key TEXT,canonical_landmark_key TEXT,checkpoint_role TEXT,
      analysis_primary INTEGER,reported_checkpoint_distance_km REAL,segment_distance_km REAL,segment_seconds REAL,
      segment_place_overall INTEGER,segment_place_gender INTEGER,segment_place_class INTEGER,segment_pace_source TEXT,
      elapsed_seconds REAL,place_overall INTEGER,place_gender INTEGER,place_class INTEGER,clock_time TEXT,raw_json TEXT NOT NULL,
      PRIMARY KEY(result_uid,sequence_no)
    );
    CREATE TABLE derived_metrics(
      result_uid TEXT NOT NULL REFERENCES results(result_uid) ON DELETE CASCADE,metric_key TEXT NOT NULL,seconds REAL,
      from_checkpoint_semantic_key TEXT,to_checkpoint_semantic_key TEXT,interpretation TEXT,classification TEXT,raw_json TEXT NOT NULL,
      PRIMARY KEY(result_uid,metric_key)
    );
    CREATE TABLE source_errors(
      year INTEGER NOT NULL,race_family TEXT NOT NULL,source_result_id TEXT,error TEXT NOT NULL,raw_json TEXT NOT NULL
    );
    CREATE INDEX idx_results_year_family ON results(year,race_family);
    CREATE INDEX idx_results_finish ON results(year,race_family,finish_seconds);
    CREATE INDEX idx_results_name ON results(name);
    CREATE INDEX idx_splits_semantic ON splits(checkpoint_semantic_key);
    ''')

def as_int_bool(v):
    if v is None:return None
    return 1 if bool(v) else 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--snapshots-dir',default='data/work/snapshots');ap.add_argument('--normalized-dir',default='data/work/normalized')
    ap.add_argument('--output',default='data/archive/ost-results-2018-2026.sqlite');args=ap.parse_args()
    snapshots=ROOT/args.snapshots_dir; normalized=ROOT/args.normalized_dir; out=ROOT/args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists(): out.unlink()
    con=sqlite3.connect(out); schema(con)
    now=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    con.executemany('INSERT INTO meta(key,value) VALUES(?,?)',[
      ('archive_schema_version','1'),('event_key','osterlen-spring-trail'),('provider','Sportstiming'),
      ('analysis_scope','2018,2019,2022,2023,2024,2025,2026'),('created_at_utc',now),
      ('provenance','Public Sportstiming /app result views fetched by repository tools; source snapshots embedded verbatim.')])
    coverage=[]; total_errors=0
    for year,family,event_id,distance_id,label in expected_classes():
        sp=snapshots/f'{year}-{family}.json'; np=normalized/f'{year}-{family}.json'
        if not sp.exists() or not np.exists(): raise SystemExit(f'Missing import material: {sp.relative_to(ROOT)} or {np.relative_to(ROOT)}')
        raw=sp.read_bytes(); src=json.loads(raw); norm=json.loads(np.read_text(encoding='utf-8'))
        errs=norm.get('source_errors',[]); total_errors+=len(errs)
        con.execute('INSERT INTO imports VALUES(?,?,?,?,?,?,?,?,?,?,?)',(
          year,family,event_id,distance_id,src.get('entity_type','athlete'),label,int(src.get('discovered_result_ids',0)),len(norm.get('records',[])),len(errs),sha256_bytes(raw),raw.decode('utf-8')))
        for e in errs:
            con.execute('INSERT INTO source_errors VALUES(?,?,?,?,?)',(year,family,str(e.get('sportstiming_result_id') or ''),str(e.get('error') or 'unknown'),json.dumps(e,ensure_ascii=False)))
        for r in norm.get('records',[]):
            uid=r['result_uid']; entity=r.get('entity_type') or ('team' if family=='duo60' else 'athlete')
            vals=(uid,year,family,event_id,distance_id,str(r.get('sportstiming_result_id') or ''),entity,r.get('name'),r.get('bib'),r.get('club'),r.get('country'),r.get('gender'),r.get('age'),
              r.get('age_category'),r.get('source_class'),r.get('status'),r.get('distance_km'),r.get('finish_seconds'),r.get('gross_seconds'),r.get('net_seconds') if r.get('net_seconds') is not None else r.get('finish_seconds'),
              r.get('overall_place'),r.get('overall_count'),r.get('gender_place'),r.get('gender_count'),r.get('class_place'),r.get('class_count'),
              r.get('start_clock'),r.get('finish_clock'),r.get('date_source'),r.get('speed_source'),r.get('pace_source'),r.get('source_url'),r.get('source_sha256'),json.dumps(r,ensure_ascii=False,separators=(',',':')))
            con.execute('INSERT INTO results VALUES('+','.join('?' for _ in vals)+')',vals)
            for i,s in enumerate(r.get('splits',[]),1):
                vals=(uid,i,s.get('checkpoint_source_label'),s.get('checkpoint_key'),s.get('checkpoint_semantic_key'),s.get('canonical_landmark_key'),s.get('checkpoint_role'),as_int_bool(s.get('analysis_primary')),
                  s.get('reported_checkpoint_distance_km'),s.get('segment_distance_km'),s.get('segment_seconds'),s.get('segment_place_overall'),s.get('segment_place_gender'),s.get('segment_place_class'),s.get('segment_pace_source'),
                  s.get('elapsed_seconds'),s.get('place_overall'),s.get('place_gender'),s.get('place_class'),s.get('clock_time'),json.dumps(s,ensure_ascii=False,separators=(',',':')))
                con.execute('INSERT INTO splits VALUES('+','.join('?' for _ in vals)+')',vals)
            for m in r.get('derived_checkpoint_metrics',[]):
                if not m.get('metric_key'): continue
                con.execute('INSERT OR REPLACE INTO derived_metrics VALUES(?,?,?,?,?,?,?,?)',(
                  uid,m.get('metric_key'),m.get('seconds'),m.get('from_checkpoint_semantic_key'),m.get('to_checkpoint_semantic_key'),m.get('interpretation'),m.get('classification'),json.dumps(m,ensure_ascii=False,separators=(',',':'))))
        coverage.append({'year':year,'race_family':family,'event_id':event_id,'distance_id':distance_id,'entity_type':src.get('entity_type','athlete'),
                         'discovered':int(src.get('discovered_result_ids',0)),'normalized':len(norm.get('records',[])),'errors':len(errs)})
    con.commit()
    integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
    total_results=con.execute('SELECT COUNT(*) FROM results').fetchone()[0]
    total_splits=con.execute('SELECT COUNT(*) FROM splits').fetchone()[0]
    unknown_status=con.execute("SELECT COUNT(*) FROM results WHERE status='UNKNOWN'").fetchone()[0]
    con.execute('VACUUM'); con.close()
    if integrity!='ok': raise SystemExit(f'SQLite integrity_check failed: {integrity}')
    if total_errors: raise SystemExit(f'Archive contains {total_errors} source errors; refusing to freeze incomplete database')
    bad=[x for x in coverage if x['discovered']<=0 or x['normalized']!=x['discovered']]
    if bad: raise SystemExit(f'Incomplete class coverage: {bad}')

    gz=out.with_suffix(out.suffix+'.gz')
    with out.open('rb') as srcf, gz.open('wb') as rawgz:
        with gzip.GzipFile(filename='',mode='wb',fileobj=rawgz,compresslevel=9,mtime=0) as z: shutil.copyfileobj(srcf,z)
    summary={'schema_version':1,'generated_at':now,'database_path':str(out.relative_to(ROOT)),'compressed_path':str(gz.relative_to(ROOT)),
             'database_bytes':out.stat().st_size,'compressed_bytes':gz.stat().st_size,'database_sha256':sha256_file(out),'compressed_sha256':sha256_file(gz),
             'integrity_check':integrity,'expected_family_year_imports':len(coverage),'total_results':total_results,'total_splits':total_splits,
             'unknown_status_records':unknown_status,'source_errors':total_errors,'coverage':coverage}
    repj=ROOT/'reports/result-archive-summary.json'; repm=ROOT/'reports/result-archive-summary.md'
    repj.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Fryst ÖST-resultatarkiv','',f"Skapad: {now}",'',f"- Resultat: **{total_results:,}**",f"- Mellantider: **{total_splits:,}**",f"- Importerade år/distans-kombinationer: **{len(coverage)}**",f"- Källfel: **{total_errors}**",f"- UNKNOWN-status: **{unknown_status}**",f"- SQLite integrity_check: **{integrity}**",f"- Komprimerad SHA-256: `{summary['compressed_sha256']}`",'', '| År | Familj | Typ | Hittade | Normaliserade | Fel |','|---:|---|---|---:|---:|---:|']
    for x in coverage: lines.append(f"| {x['year']} | {x['race_family']} | {x['entity_type']} | {x['discovered']} | {x['normalized']} | {x['errors']} |")
    repm.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('total_results','total_splits','source_errors','integrity_check','compressed_bytes')},indent=2))

if __name__=='__main__':main()
