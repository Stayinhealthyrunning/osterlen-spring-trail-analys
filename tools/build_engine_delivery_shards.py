#!/usr/bin/env python3
"""Build browser-delivery shards from the canonical ÖST Engine 1.0 payload.

The full Engine payload remains the canonical integration/debug artifact. Browser
delivery is intentionally smaller: one bootstrap file plus one selected-race
bundle at a time. Route/elevation assets remain separate.
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
BUDGET=ROOT/"config/frontend-performance-budget.json"


def dump_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode("utf-8")


def gzip_size(raw: bytes) -> int:
    return len(gzip.compress(raw,compresslevel=9,mtime=0))


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path,obj):
    raw=dump_bytes(obj)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    return {
        "path":str(path),
        "raw_bytes":len(raw),
        "gzip_bytes":gzip_size(raw),
        "sha256":sha256(raw),
    }


def build_full_payload():
    with tempfile.TemporaryDirectory(prefix="ost-delivery-") as td:
        p=Path(td)/"engine.json"
        run=subprocess.run(
            [sys.executable,str(EXPORTER),"--output",str(p)],
            cwd=ROOT,text=True,capture_output=True
        )
        if run.returncode:
            raise SystemExit(run.stderr or run.stdout)
        raw=p.read_bytes()
    return json.loads(raw),sha256(raw)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="out/engine-data")
    ap.add_argument("--report",default=None,help="Optional JSON report path.")
    args=ap.parse_args()

    out=Path(args.output_dir)
    if not out.is_absolute():
        out=ROOT/out
    out.mkdir(parents=True,exist_ok=True)

    budget=json.loads(BUDGET.read_text(encoding="utf-8"))
    data_budget=budget["data_delivery"]
    payload,payload_sha=build_full_payload()

    splits_by=defaultdict(list)
    for row in payload.get("splits",[]):
        splits_by[row["race_key"]].append(row)
    teams_by=defaultdict(list)
    for row in payload.get("teams",[]):
        teams_by[row["race_key"]].append(row)
    members_by=defaultdict(list)
    for row in payload.get("team_members",[]):
        members_by[row["race_key"]].append(row)

    bootstrap={
        "schema_version":1,
        "engine_contract":payload["engine_contract"],
        "payload_sha256":payload_sha,
        "event":payload["event"],
        "race_catalog":payload["race_catalog"],
        "courses":payload["courses"],
        "sources":payload.get("sources",{}),
    }
    bootstrap_info=write_json(out/"bootstrap.json",bootstrap)

    races={}
    total_records=total_splits=total_teams=total_members=0
    for race_key,race in sorted(payload["races"].items()):
        records=race.get("records",[])
        race_meta={k:v for k,v in race.items() if k!="records"}
        bundle={
            "schema_version":1,
            "engine_contract":payload["engine_contract"],
            "payload_sha256":payload_sha,
            "race_key":race_key,
            "race":race_meta,
            "records":records,
            "checkpoints":payload.get("checkpoints",{}).get(race_key,[]),
            "splits":splits_by.get(race_key,[]),
            "teams":teams_by.get(race_key,[]),
            "team_members":members_by.get(race_key,[]),
        }
        info=write_json(out/"races"/f"{race_key}.json",bundle)
        info["records"]=len(records)
        info["splits"]=len(bundle["splits"])
        info["teams"]=len(bundle["teams"])
        info["team_members"]=len(bundle["team_members"])
        races[race_key]=info
        total_records+=info["records"]
        total_splits+=info["splits"]
        total_teams+=info["teams"]
        total_members+=info["team_members"]

    manifest={
        "schema_version":1,
        "engine_contract":payload["engine_contract"],
        "payload_sha256":payload_sha,
        "architecture":"bootstrap_plus_per_race_bundle",
        "bootstrap":{
            "path":"bootstrap.json",
            "raw_bytes":bootstrap_info["raw_bytes"],
            "gzip_bytes":bootstrap_info["gzip_bytes"],
            "sha256":bootstrap_info["sha256"],
        },
        "races":{
            key:{**info,"path":f"races/{key}.json"}
            for key,info in races.items()
        },
        "totals":{
            "race_instances":len(races),
            "records":total_records,
            "splits":total_splits,
            "teams":total_teams,
            "team_members":total_members,
        },
        "route_assets":"separate_lazy_loaded_course_version_bundle",
        "elevation_assets":"separate_lazy_loaded_course_version_bundle_or_route_companion",
    }
    manifest_info=write_json(out/"manifest.json",manifest)

    # Contract/accounting checks.
    assert len(races)==34
    assert total_records==9871
    assert total_splits==6123
    assert total_teams==300
    assert total_members==599
    assert "records" not in bootstrap
    assert not (out/"engine.json").exists()

    failures=[]
    if bootstrap_info["gzip_bytes"]>data_budget["bootstrap_gzip_max_bytes"]:
        failures.append(
            f"bootstrap gzip {bootstrap_info['gzip_bytes']} > {data_budget['bootstrap_gzip_max_bytes']}"
        )
    max_raw=max(x["raw_bytes"] for x in races.values())
    max_gz=max(x["gzip_bytes"] for x in races.values())
    if max_raw>data_budget["selected_race_raw_max_bytes"]:
        failures.append(
            f"selected race raw {max_raw} > {data_budget['selected_race_raw_max_bytes']}"
        )
    if max_gz>data_budget["selected_race_gzip_max_bytes"]:
        failures.append(
            f"selected race gzip {max_gz} > {data_budget['selected_race_gzip_max_bytes']}"
        )
    if bootstrap_info["gzip_bytes"]+max_gz>data_budget["bootstrap_plus_selected_race_gzip_max_bytes"]:
        failures.append("bootstrap + selected-race gzip hard budget exceeded")

    report={
        "schema_version":1,
        "payload_sha256":payload_sha,
        "output_dir":str(out.relative_to(ROOT) if out.is_relative_to(ROOT) else out),
        "bootstrap":bootstrap_info,
        "manifest":manifest_info,
        "race_count":len(races),
        "max_selected_race_raw_bytes":max_raw,
        "max_selected_race_gzip_bytes":max_gz,
        "bootstrap_plus_max_selected_race_gzip_bytes":bootstrap_info["gzip_bytes"]+max_gz,
        "totals":manifest["totals"],
        "budget_source":"config/frontend-performance-budget.json",
        "budget_failures":failures,
    }

    if args.report:
        rp=Path(args.report)
        if not rp.is_absolute():
            rp=ROOT/rp
        rp.parent.mkdir(parents=True,exist_ok=True)
        rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    print(json.dumps(report,ensure_ascii=False,indent=2))
    if failures:
        raise SystemExit(1)


if __name__=="__main__":
    main()
