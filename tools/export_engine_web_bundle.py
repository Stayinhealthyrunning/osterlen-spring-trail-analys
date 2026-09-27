#!/usr/bin/env python3
"""Build the browser-oriented ÖST Engine 1.0 data bundle.

The canonical Engine payload remains the integration/debug artifact. Browser
delivery is a tiny bootstrap plus one complete selected-race file. Route and
elevation assets remain separate and lazy-loaded.
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
ENGINE_EXPORTER=ROOT/"tools/export_engine_v1.py"


def compact_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode("utf-8")


def gzip_size(raw):
    return len(gzip.compress(raw,compresslevel=9,mtime=0))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path,obj):
    raw=compact_bytes(obj)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    return {"raw_bytes":len(raw),"gzip_bytes":gzip_size(raw),"sha256":sha256(raw)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    outdir=Path(args.output_dir)
    if not outdir.is_absolute():
        outdir=ROOT/outdir

    with tempfile.TemporaryDirectory(prefix="ost-engine-web-") as td:
        canonical=Path(td)/"engine.json"
        run=subprocess.run(
            [sys.executable,str(ENGINE_EXPORTER),"--output",str(canonical)],
            cwd=ROOT,text=True,capture_output=True
        )
        if run.returncode:
            raise SystemExit(run.stderr or run.stdout)
        canonical_raw=canonical.read_bytes()
        payload=json.loads(canonical_raw)

    payload_sha=sha256(canonical_raw)
    full_meta={"raw_bytes":len(canonical_raw),"gzip_bytes":gzip_size(canonical_raw),"sha256":payload_sha}

    splits=defaultdict(list)
    for x in payload.get("splits",[]): splits[x["race_key"]].append(x)
    teams=defaultdict(list)
    for x in payload.get("teams",[]): teams[x["race_key"]].append(x)
    members=defaultdict(list)
    for x in payload.get("team_members",[]): members[x["race_key"]].append(x)

    bootstrap={
        "schema_version":1,
        "engine_contract":payload["engine_contract"],
        "payload_sha256":payload_sha,
        "event":payload["event"],
        "race_catalog":payload["race_catalog"],
        "courses":payload["courses"],
        "sources":payload.get("sources",{}),
    }
    bootstrap_meta=dump(outdir/"bootstrap.json",bootstrap)

    race_entries={}
    total_records=total_splits=total_teams=total_members=0
    for race_key,race in sorted(payload["races"].items()):
        doc={
            "schema_version":1,
            "engine_contract":payload["engine_contract"],
            "payload_sha256":payload_sha,
            "race_key":race_key,
            "race":race,
            "checkpoints":payload.get("checkpoints",{}).get(race_key,[]),
            "splits":splits.get(race_key,[]),
            "teams":teams.get(race_key,[]),
            "team_members":members.get(race_key,[]),
        }
        meta=dump(outdir/"races"/f"{race_key}.json",doc)
        entry={
            **meta,
            "path":f"races/{race_key}.json",
            "year":race["year"],
            "race_family":race["race_family"],
            "records":len(race.get("records",[])),
            "splits":len(doc["splits"]),
            "teams":len(doc["teams"]),
            "team_members":len(doc["team_members"]),
        }
        race_entries[race_key]=entry
        total_records+=entry["records"]; total_splits+=entry["splits"]
        total_teams+=entry["teams"]; total_members+=entry["team_members"]

    totals={
        "race_instances":len(race_entries),
        "records":total_records,
        "splits":total_splits,
        "teams":total_teams,
        "team_members":total_members,
    }
    assert totals=={"race_instances":34,"records":9871,"splits":6123,"teams":300,"team_members":599},totals

    manifest={
        "schema_version":1,
        "engine_contract":payload["engine_contract"],
        "payload_sha256":payload_sha,
        "delivery_model":"bootstrap_plus_per_race_bundle",
        "canonical_engine":full_meta,
        "bootstrap":{**bootstrap_meta,"path":"bootstrap.json"},
        "races":race_entries,
        "totals":totals,
        "route_assets":"separate_lazy_load_by_course_version",
        "elevation_assets":"separate_lazy_load_by_course_version",
        "replay_assets":"load_only_for_replay_capable_selected_race",
    }
    manifest_meta=dump(outdir/"manifest.json",manifest)

    print(json.dumps({
        "output_dir":str(outdir),
        "payload_sha256":payload_sha,
        "races":len(race_entries),
        "totals":totals,
        "full_engine_raw_bytes":full_meta["raw_bytes"],
        "full_engine_gzip_bytes":full_meta["gzip_bytes"],
        "bootstrap_gzip_bytes":bootstrap_meta["gzip_bytes"],
        "largest_race_gzip_bytes":max(v["gzip_bytes"] for v in race_entries.values()),
        "largest_race_raw_bytes":max(v["raw_bytes"] for v in race_entries.values()),
        "bootstrap_plus_largest_race_gzip_bytes":bootstrap_meta["gzip_bytes"]+max(v["gzip_bytes"] for v in race_entries.values()),
        "manifest_raw_bytes":manifest_meta["raw_bytes"],
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
