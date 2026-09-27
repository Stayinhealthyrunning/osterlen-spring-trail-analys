#!/usr/bin/env python3
"""Build the browser-oriented ÖST Engine 1.0 data bundle.

The canonical Engine 1.0 export is preserved, but browser delivery is sharded
into a tiny bootstrap document plus one file per race edition. Route/elevation
assets remain outside this bundle and are loaded separately on demand.
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

def dump(path: Path, obj):
    raw=json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    return {
        "path":str(path),
        "raw_bytes":len(raw),
        "gzip_bytes":len(gzip.compress(raw,compresslevel=9,mtime=0)),
        "sha256":hashlib.sha256(raw).hexdigest(),
    }

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
        payload=json.loads(canonical.read_text(encoding="utf-8"))

    splits=defaultdict(list)
    for x in payload.get("splits",[]):
        splits[x["race_key"]].append(x)
    teams=defaultdict(list)
    for x in payload.get("teams",[]):
        teams[x["race_key"]].append(x)
    members=defaultdict(list)
    for x in payload.get("team_members",[]):
        members[x["race_key"]].append(x)

    bootstrap={
        "engine_contract":payload["engine_contract"],
        "event":payload["event"],
        "race_catalog":payload["race_catalog"],
        "courses":payload["courses"],
        "sources":payload.get("sources",{}),
    }
    bootstrap_meta=dump(outdir/"bootstrap.json",bootstrap)

    race_entries={}
    for race_key,race in sorted(payload["races"].items()):
        doc={
            "race":race,
            "checkpoints":payload.get("checkpoints",{}).get(race_key,[]),
            "splits":splits.get(race_key,[]),
            "teams":teams.get(race_key,[]),
            "team_members":members.get(race_key,[]),
        }
        meta=dump(outdir/"races"/f"{race_key}.json",doc)
        race_entries[race_key]={
            **meta,
            "year":race["year"],
            "race_family":race["race_family"],
            "records":len(race.get("records",[])),
            "splits":len(doc["splits"]),
            "teams":len(doc["teams"]),
            "team_members":len(doc["team_members"]),
        }

    manifest={
        "schema_version":1,
        "engine_contract":payload["engine_contract"],
        "delivery_model":"bootstrap_plus_per_race_bundle",
        "bootstrap":bootstrap_meta,
        "races":race_entries,
        "route_assets":"separate_lazy_load",
        "elevation_assets":"separate_lazy_load",
        "replay_assets":"separate_lazy_load",
    }
    dump(outdir/"manifest.json",manifest)

    print(json.dumps({
        "output_dir":str(outdir),
        "races":len(race_entries),
        "bootstrap_gzip_bytes":bootstrap_meta["gzip_bytes"],
        "largest_race_gzip_bytes":max(v["gzip_bytes"] for v in race_entries.values()),
        "largest_race_raw_bytes":max(v["raw_bytes"] for v in race_entries.values()),
    },indent=2))

if __name__=="__main__":
    main()
