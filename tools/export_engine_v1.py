#!/usr/bin/env python3
"""Export the curated ÖST archive to the frozen Loppanalys Engine 1.0 contract.

Offline only. No source acquisition occurs here. The curated SQLite database and
its readiness report are the input truth; missing evidence remains missing.
"""
from __future__ import annotations
import argparse, gzip, json, sqlite3, tempfile
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB_GZ=ROOT/"data/derived/ost-analysis-2018-2026.sqlite.gz"
READINESS=ROOT/"reports/engine-readiness.json"
COURSES=ROOT/"config/course-versions.json"
ADAPTER=ROOT/"config/engine-adapter.json"

def load_json(path): return json.loads(path.read_text(encoding="utf-8"))

def competition(race_type, family):
    if family=="duo60":
        return {"participant":{"entity":"team"},"competition":{"format":"duo","team_structure":{"kind":"sequential","leg_count":2,"member_assignment":"unknown"}}}
    return {"participant":{"entity":"person"},"competition":{"format":"individual","team_structure":{"kind":"none","member_assignment":"unknown"}}}

def capabilities(ready):
    f=ready["features"]; cov=ready["field_counts"]
    split=bool(f["split_analysis"])
    return {
        "finish_statistics":bool(f["finish_statistics"]),
        "runner_profile":bool(f["runner_or_team_profile"]),
        "sex_filter":cov["gender"]>0,
        "age_analysis":cov["age_exact"]>0 or cov["age_category"]>0,
        "club_analysis":cov["club"]>0,
        "class_analysis":cov["source_class"]>0,
        "segment_analysis":split,
        "replay":bool(f["runner_replay"]),
        "head_to_head":split,
        "person_history":False,
        "course_history":bool(f["course_version_records"]),
        "goal_pace":ready["race_type"]=="individual" and bool(f["finish_statistics"]),
        "team_members":bool(f["relay_member_display"]),
    }

def record(row):
    return {
        "source_result_id":row["source_result_id"],"bib":row["bib"],"entity_type":row["entity_type"],
        "name":row["name_as_published"],"sex":row["sex"],"age":row["age"],"age_category":row["age_category"],
        "club":row["club"],"country":row["country"],"class_name":row["source_class"],"status":row["status"],
        "finish_seconds":row["finish_seconds"],"overall_place":row["overall_place"],"gender_place":row["gender_place"],
        "class_place":row["class_place"],"person_key":None,"identity_status":"source_local","identity_scope":"race_result"
    }

def checkpoint_catalog(con,race):
    key=race["race_key"]; nominal=race["nominal_distance_km"]
    rows=con.execute("""SELECT checkpoint_semantic_key,checkpoint_key,checkpoint_source_label,
        MIN(sequence_no) sequence_no,MAX(COALESCE(analysis_primary,0)) analysis_primary,
        MAX(reported_checkpoint_distance_km) distance_km,COUNT(CASE WHEN elapsed_seconds IS NOT NULL THEN 1 END) observed
        FROM splits s JOIN results r USING(result_uid) WHERE r.race_key=?
        GROUP BY checkpoint_semantic_key,checkpoint_key,checkpoint_source_label ORDER BY MIN(sequence_no)""",(key,)).fetchall()
    out=[{"key":"start","name":"Start","semantic_key":"start","sequence_no":0,"race_distance_km":0.0,"route_distance_km":0.0,"analysis_boundary":True,"replay_anchor":True,"source_label":None}]
    seen={"start"}
    seq=1
    for row in rows:
        sem=row["checkpoint_semantic_key"] or row["checkpoint_key"]
        if not sem or sem=="finish" or sem in seen: continue
        seen.add(sem)
        out.append({"key":sem,"name":row["checkpoint_source_label"] or sem,"semantic_key":row["checkpoint_semantic_key"],
                    "source_label":row["checkpoint_source_label"],"sequence_no":seq,
                    "race_distance_km":row["distance_km"],"route_distance_km":None,
                    "analysis_boundary":bool(row["analysis_primary"]),"replay_anchor":bool(row["observed"])})
        seq+=1
    out.append({"key":"finish","name":"Mål","semantic_key":"finish","sequence_no":seq,"race_distance_km":nominal,
                "route_distance_km":None,"analysis_boundary":True,"replay_anchor":True,"source_label":None})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",help="Optional JSON output path. If omitted, validate/build in memory only.")
    args=ap.parse_args()
    adapter=load_json(ADAPTER)
    if adapter["target"]["engine_contract"]!="loppanalys-engine-1.0":
        raise SystemExit("engine adapter does not target Engine 1.0")
    readiness=load_json(READINESS); ready={x["race_key"]:x for x in readiness["races"]}
    course_cfg=load_json(COURSES); versions={x["course_version_id"]:x for x in course_cfg["versions"]}\n    assignments={(int(x["year"]),x["family"]):x for x in course_cfg.get("assignments",[])}
    with tempfile.TemporaryDirectory(prefix="ost-engine-v1-") as td:
        db=Path(td)/"ost.sqlite"
        with gzip.open(DB_GZ,"rb") as src,db.open("wb") as dst:
            while chunk:=src.read(1024*1024): dst.write(chunk)
        con=sqlite3.connect(db);con.row_factory=sqlite3.Row
        payload={
          "engine_contract":"loppanalys-engine-1.0",
          "event":{"event_key":"osterlen-spring-trail","name":"Österlen Spring Trail","product_title":"ÖST Analys","storage_namespace":"ost"},
          "race_catalog":{},"courses":{},"races":{},"checkpoints":{},"splits":[],"teams":[],"team_members":[],
          "sources":{"curated_database":str(DB_GZ.relative_to(ROOT)),"readiness":str(READINESS.relative_to(ROOT))}
        }
        for cv,v in versions.items():
            assets={}
            if v.get("primary_source_path") and v.get("route_asset_status")=="archived_organizer_gpx":
                assets["route_source"]=v["primary_source_path"]
            payload["courses"][cv]={"course_version":cv,"route_family":v["route_family"],"whole_course_comparison_group":v.get("whole_course_comparison_group"),
                "geometry_evidence":{"status":v["status"],"geometry_hash_prefix":v.get("geometry_hash_prefix"),"derived_path_distance_km":v.get("derived_path_distance_km")},
                "assets":assets}
        race_rows=con.execute("SELECT * FROM races ORDER BY year,race_family").fetchall()
        for rr in race_rows:
            r=dict(rr);rk=r["race_key"];rd=ready[rk];sem=competition(r["race_type"],r["race_family"]);caps=capabilities(rd)\n            assignment=assignments.get((int(r["year"]),r["race_family"]),{})\n            course_version=assignment.get("course_version_id") if assignment else r["course_version"]
            records=[record(x) for x in con.execute("SELECT * FROM results WHERE race_key=? ORDER BY COALESCE(overall_place,999999),name_as_published",(rk,))]
            item={"race_key":rk,"event_key":r["event_key"],"race_family":r["race_family"],"year":r["year"],"race_date":r["race_date"],
                  "course_version":course_version,"data_status":"available","section":r["source_race_name"] or r["race_family"],
                  "nominal_distance_km":r["nominal_distance_km"],**sem,"capabilities":caps,"records":records}
            payload["races"][rk]=item
            payload["race_catalog"][rk]={k:item[k] for k in ("race_key","event_key","race_family","year","race_date","course_version","data_status","section","nominal_distance_km","participant","competition","capabilities")}
            payload["checkpoints"][rk]=checkpoint_catalog(con,r)
        for s in con.execute("""SELECT r.race_key,r.source_result_id,r.bib,s.* FROM splits s JOIN results r USING(result_uid)
                              WHERE s.elapsed_seconds IS NOT NULL ORDER BY r.race_key,r.result_uid,s.sequence_no"""):
            payload["splits"].append({"race_key":s["race_key"],"source_result_id":s["source_result_id"],"bib":s["bib"],
                "checkpoint":s["checkpoint_semantic_key"] or s["checkpoint_key"],"source_point_name":s["checkpoint_source_label"],
                "elapsed_seconds":s["elapsed_seconds"],"place_overall":s["place_overall"],"place_class":s["place_class"],"place_gender":s["place_gender"]})
        for t in con.execute("SELECT * FROM relay_teams ORDER BY race_key,team_uid"):
            members=[dict(x) for x in con.execute("SELECT source_sequence,source_member_result_id,bib,name_as_published,member_time_seconds,finish_clock,speed_source,leg_no,assignment_status FROM relay_members WHERE team_uid=? ORDER BY source_sequence",(t["team_uid"],))]
            payload["teams"].append({"race_key":t["race_key"],"source_result_id":t["source_result_id"],"bib":t["bib"],"team_name":t["team_name"],"class_name":t["class_name"]})
            for m in members: payload["team_members"].append({"race_key":t["race_key"],"team_source_result_id":t["source_result_id"],**m})
        con.close()
    # Contract-level invariants.
    assert len(payload["races"])==34
    assert sum(len(r["records"]) for r in payload["races"].values())==9871
    assert len(payload["splits"])<=6123 and len(payload["splits"])>0
    for race in payload["races"].values():
        if race["capabilities"]["replay"]:
            assert race["course_version"] and payload["courses"][race["course_version"]]["assets"].get("route_source")
            assert race["capabilities"]["segment_analysis"]
        if race["participant"]["entity"]=="team":
            assert race["competition"]["team_structure"]["member_assignment"]=="unknown"
        if not race["capabilities"]["segment_analysis"]:
            assert not race["capabilities"]["replay"]
    if args.output:
        out=ROOT/args.output;out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(json.dumps({"engine_contract":payload["engine_contract"],"races":len(payload["races"]),"results":sum(len(r["records"]) for r in payload["races"].values()),"splits":len(payload["splits"]),"teams":len(payload["teams"]),"team_members":len(payload["team_members"]),"replay_ready":sum(1 for r in payload["races"].values() if r["capabilities"]["replay"])},ensure_ascii=False))

if __name__=="__main__": main()
