#!/usr/bin/env python3
"""Profile the real ÖST Engine 1.0 export and estimate frontend delivery shards."""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPORTER=ROOT/"tools/export_engine_v1.py"
OUT_JSON=ROOT/"reports/engine-payload-profile.json"
OUT_MD=ROOT/"reports/engine-payload-profile.md"

def encoded(obj):
    raw=json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    gz=gzip.compress(raw,compresslevel=9,mtime=0)
    return {"raw_bytes":len(raw),"gzip_bytes":len(gz),"gzip_ratio":round(len(gz)/len(raw),4) if raw else 0.0}

def human(n):
    units=["B","KiB","MiB","GiB"]
    x=float(n)
    for u in units:
        if x<1024 or u==units[-1]:
            return f"{x:.1f} {u}" if u!="B" else f"{int(x)} B"
        x/=1024

def main():
    with tempfile.TemporaryDirectory(prefix="ost-payload-profile-") as td:
        out=Path(td)/"ost-engine-v1.json"
        run=subprocess.run([sys.executable,str(EXPORTER),"--output",str(out)],cwd=ROOT,text=True,capture_output=True)
        if run.returncode:
            raise SystemExit(run.stderr or run.stdout)
        raw_bytes=out.read_bytes()
        payload=json.loads(raw_bytes)

    whole_raw=len(raw_bytes)
    whole_gz=len(gzip.compress(raw_bytes,compresslevel=9,mtime=0))
    top={key:encoded(value) for key,value in payload.items()}

    bootstrap={"engine_contract":payload.get("engine_contract"),"event":payload["event"],"race_catalog":payload["race_catalog"],"courses":payload["courses"],"sources":payload.get("sources",{})}
    bootstrap_size=encoded(bootstrap)

    splits_by_race=defaultdict(list)
    for row in payload.get("splits",[]):
        splits_by_race[row["race_key"]].append(row)
    teams_by_race=defaultdict(list)
    for row in payload.get("teams",[]):
        teams_by_race[row["race_key"]].append(row)
    members_by_race=defaultdict(list)
    for row in payload.get("team_members",[]):
        members_by_race[row["race_key"]].append(row)

    race_profiles=[]
    for race_key,race in sorted(payload["races"].items()):
        records=race.get("records",[])
        race_meta={k:v for k,v in race.items() if k!="records"}
        core={"race":race_meta,"records":records,"checkpoints":payload.get("checkpoints",{}).get(race_key,[])}
        split_part=splits_by_race.get(race_key,[])
        team_part={"teams":teams_by_race.get(race_key,[]),"team_members":members_by_race.get(race_key,[])}
        full_selected={**core,"splits":split_part,**team_part}
        race_profiles.append({
            "race_key":race_key,"year":race.get("year"),"race_family":race.get("race_family"),
            "records":len(records),"splits":len(split_part),"teams":len(team_part["teams"]),"team_members":len(team_part["team_members"]),
            "core":encoded(core),"splits_payload":encoded(split_part),"team_payload":encoded(team_part),"selected_race_total":encoded(full_selected)
        })

    largest_raw=sorted(race_profiles,key=lambda x:x["selected_race_total"]["raw_bytes"],reverse=True)[:10]
    largest_gzip=sorted(race_profiles,key=lambda x:x["selected_race_total"]["gzip_bytes"],reverse=True)[:10]

    family_summary={}
    for fam in sorted({r["race_family"] for r in race_profiles}):
        subset=[r for r in race_profiles if r["race_family"]==fam]
        family_summary[fam]={
            "race_instances":len(subset),"records":sum(r["records"] for r in subset),"splits":sum(r["splits"] for r in subset),
            "selected_race_raw_bytes_sum":sum(r["selected_race_total"]["raw_bytes"] for r in subset),
            "selected_race_gzip_bytes_sum":sum(r["selected_race_total"]["gzip_bytes"] for r in subset)
        }

    payload_hash=hashlib.sha256(raw_bytes).hexdigest()
    sorted_selected=sorted(r["selected_race_total"]["gzip_bytes"] for r in race_profiles)
    profile={
        "schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"engine_contract":payload.get("engine_contract"),
        "payload_sha256":payload_hash,
        "whole_payload":{"raw_bytes":whole_raw,"gzip_bytes":whole_gz,"gzip_ratio":round(whole_gz/whole_raw,4) if whole_raw else 0.0},
        "bootstrap_candidate":bootstrap_size,"top_level":top,
        "counts":{"races":len(payload.get("races",{})),"records":sum(len(r.get("records",[])) for r in payload.get("races",{}).values()),"splits":len(payload.get("splits",[])),"teams":len(payload.get("teams",[])),"team_members":len(payload.get("team_members",[])),"courses":len(payload.get("courses",{}))},
        "race_profiles":race_profiles,"largest_selected_races_raw":largest_raw,"largest_selected_races_gzip":largest_gzip,"family_summary":family_summary,
        "delivery_observations":{
            "single_payload_initial_load_gzip_bytes":whole_gz,
            "bootstrap_plus_largest_selected_race_gzip_bytes":bootstrap_size["gzip_bytes"]+max(sorted_selected),
            "bootstrap_plus_median_selected_race_gzip_bytes":bootstrap_size["gzip_bytes"]+sorted_selected[len(sorted_selected)//2],
            "route_and_elevation_assets_excluded_from_engine_payload":True
        }
    }
    OUT_JSON.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    lines=["# ÖST Engine 1.0 payload profile","",
        f"Generated from the real frozen/curated Engine 1.0 export. Payload SHA-256: {payload_hash}.","",
        "## Whole payload","",
        f"- Raw/minified JSON: **{human(whole_raw)}** ({whole_raw:,} bytes)",
        f"- gzip -9: **{human(whole_gz)}** ({whole_gz:,} bytes)",
        f"- gzip/raw ratio: **{profile['whole_payload']['gzip_ratio']:.3f}**","",
        "## Bootstrap candidate","",
        "Contains event, race catalog, course metadata and source/version metadata, but no result rows/splits.","",
        f"- Raw: **{human(bootstrap_size['raw_bytes'])}**",f"- gzip: **{human(bootstrap_size['gzip_bytes'])}**","",
        "## Top-level contribution","","| Section | Raw | gzip |","|---|---:|---:|"]
    for key,sz in sorted(top.items(),key=lambda kv:kv[1]["raw_bytes"],reverse=True):
        lines.append(f"| {key} | {human(sz['raw_bytes'])} | {human(sz['gzip_bytes'])} |")
    lines += ["","## Largest selected race bundles","",
        "A selected-race bundle is race metadata + all result records + checkpoints + real splits + team/member rows for one edition.","",
        "| Race | records | splits | raw | gzip |","|---|---:|---:|---:|---:|"]
    for r in largest_gzip:
        sz=r["selected_race_total"]
        lines.append(f"| {r['race_key']} | {r['records']} | {r['splits']} | {human(sz['raw_bytes'])} | {human(sz['gzip_bytes'])} |")
    obs=profile["delivery_observations"]
    lines += ["","## Delivery implication","",
        f"- Monolithic initial payload: **{human(obs['single_payload_initial_load_gzip_bytes'])} gzip** before route/elevation assets.",
        f"- Bootstrap + largest selected race: **{human(obs['bootstrap_plus_largest_selected_race_gzip_bytes'])} gzip**.",
        f"- Bootstrap + median selected race: **{human(obs['bootstrap_plus_median_selected_race_gzip_bytes'])} gzip**.",
        "- Route and elevation assets are separate and should remain lazy-loaded.","",
        "This report measures transport size only. Browser parse/render cost and map/replay memory must be measured once the frontend exists."]
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"whole_raw_bytes":whole_raw,"whole_gzip_bytes":whole_gz,"bootstrap_gzip_bytes":bootstrap_size["gzip_bytes"],"largest_selected_race_gzip_bytes":max(sorted_selected),"payload_sha256":payload_hash},indent=2))

if __name__=="__main__":
    main()
