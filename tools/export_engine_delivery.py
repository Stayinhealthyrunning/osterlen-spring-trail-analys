#!/usr/bin/env python3
"""Export a sharded static delivery package from the canonical ÖST Engine 1.0 payload.

The canonical semantic payload remains tools/export_engine_v1.py. This tool only
changes delivery shape for the browser: small bootstrap metadata plus one file per
race edition. Route/elevation assets stay outside this package and are lazy-loaded
separately by course_version.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTER=ROOT/"tools/export_engine_v1.py"


def compact_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode("utf-8")


def stats(raw):
    gz=gzip.compress(raw,compresslevel=9,mtime=0)
    return {
        "raw_bytes":len(raw),
        "gzip_bytes":len(gz),
        "sha256":hashlib.sha256(raw).hexdigest(),
    }


def write_json(path,obj):
    raw=compact_bytes(obj)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    return stats(raw)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    outdir=Path(args.output_dir)
    if not outdir.is_absolute():
        outdir=ROOT/outdir

    with tempfile.TemporaryDirectory(prefix="ost-engine-delivery-") as td:
        full=Path(td)/"engine.json"
        run=subprocess.run(
            [sys.executable,str(EXPORTER),"--output",str(full)],
            cwd=ROOT,text=True,capture_output=True
        )
        if run.returncode:
            raise SystemExit(run.stderr or run.stdout)
        full_raw=full.read_bytes()
        payload=json.loads(full_raw)

    splits_by_race=defaultdict(list)
    for row in payload.get("splits",[]):
        splits_by_race[row["race_key"]].append(row)

    teams_by_race=defaultdict(list)
    for row in payload.get("teams",[]):
        teams_by_race[row["race_key"]].append(row)

    members_by_race=defaultdict(list)
    for row in payload.get("team_members",[]):
        members_by_race[row["race_key"]].append(row)

    race_summaries={}
    for race_key,race in payload["races"].items():
        records=race.get("records",[])
        status_counts={}
        for rec in records:
            status=rec.get("status") or "UNKNOWN"
            status_counts[status]=status_counts.get(status,0)+1
        race_summaries[race_key]={
            "records":len(records),
            "splits":len(splits_by_race.get(race_key,[])),
            "teams":len(teams_by_race.get(race_key,[])),
            "team_members":len(members_by_race.get(race_key,[])),
            "status_counts":status_counts,
        }

    index={
        "schema_version":1,
        "delivery_model":"bootstrap_plus_selected_race_shards",
        "engine_contract":payload.get("engine_contract"),
        "event":payload["event"],
        "race_catalog":payload["race_catalog"],
        "race_summaries":race_summaries,
        "courses":payload["courses"],
        "sources":payload.get("sources",{}),
        "race_bundle_pattern":"races/{race_key}.json",
        "route_bundle_policy":"lazy_by_course_version",
    }
    index_stats=write_json(outdir/"index.json",index)

    manifest={
        "schema_version":1,
        "engine_contract":payload.get("engine_contract"),
        "source_payload":stats(full_raw),
        "bootstrap":{"path":"index.json",**index_stats},
        "races":{},
        "counts":{
            "race_instances":len(payload["races"]),
            "records":0,
            "splits":0,
            "teams":0,
            "team_members":0,
        },
    }

    for race_key,race in sorted(payload["races"].items()):
        records=race.get("records",[])
        race_meta={k:v for k,v in race.items() if k!="records"}
        bundle={
            "schema_version":1,
            "race":race_meta,
            "records":records,
            "checkpoints":payload.get("checkpoints",{}).get(race_key,[]),
            "splits":splits_by_race.get(race_key,[]),
            "teams":teams_by_race.get(race_key,[]),
            "team_members":members_by_race.get(race_key,[]),
        }
        rel=Path("races")/f"{race_key}.json"
        st=write_json(outdir/rel,bundle)
        manifest["races"][race_key]={
            "path":str(rel).replace("\\","/"),
            **st,
            "records":len(bundle["records"]),
            "splits":len(bundle["splits"]),
            "teams":len(bundle["teams"]),
            "team_members":len(bundle["team_members"]),
        }
        manifest["counts"]["records"]+=len(bundle["records"])
        manifest["counts"]["splits"]+=len(bundle["splits"])
        manifest["counts"]["teams"]+=len(bundle["teams"])
        manifest["counts"]["team_members"]+=len(bundle["team_members"])

    assert manifest["counts"]=={
        "race_instances":34,
        "records":9871,
        "splits":6123,
        "teams":300,
        "team_members":599,
    },manifest["counts"]

    largest=max(manifest["races"].items(),key=lambda kv:kv[1]["gzip_bytes"])
    manifest["largest_race_bundle"]={"race_key":largest[0],**largest[1]}
    manifest["bootstrap_plus_largest_gzip_bytes"]=index_stats["gzip_bytes"]+largest[1]["gzip_bytes"]
    write_json(outdir/"manifest.json",manifest)

    print(json.dumps({
        "output_dir":str(outdir),
        "bootstrap_raw_bytes":index_stats["raw_bytes"],
        "bootstrap_gzip_bytes":index_stats["gzip_bytes"],
        "largest_race_key":largest[0],
        "largest_race_raw_bytes":largest[1]["raw_bytes"],
        "largest_race_gzip_bytes":largest[1]["gzip_bytes"],
        "bootstrap_plus_largest_gzip_bytes":manifest["bootstrap_plus_largest_gzip_bytes"],
    },indent=2))


if __name__=="__main__":
    main()
