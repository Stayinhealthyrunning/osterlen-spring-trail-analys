#!/usr/bin/env python3
"""Final source-side prebuild audit before ÖST Engine 1.0 integration.

This is intentionally offline. It validates that the frozen curated result layer,
later course-version decisions, readiness flags and Engine 1.0 export agree with
one another. It does not acquire or mutate source data.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COURSES=ROOT/"config/course-versions.json"
READINESS=ROOT/"reports/engine-readiness.json"
FOUNDATION=ROOT/"config/foundation-state.json"
TRAIL14_PROV=ROOT/"routes/ost/trail14-current-reference/provenance.json"
TRAIL14_SUPERSEDED_PROV=ROOT/"routes/ost/trail14-current-reference/superseded-raster-provenance.json"
EXPORTER=ROOT/"tools/export_engine_v1.py"

ENGINE_REQUIRED_TOP={"event","race_catalog","courses","races","checkpoints","splits"}
ENGINE_EVENT_REQUIRED={"event_key","name","product_title","storage_namespace"}
ENGINE_RACE_REQUIRED={"race_key","race_family","year","data_status","participant","competition","capabilities"}
CAPABILITY_KEYS={
    "finish_statistics","runner_profile","sex_filter","age_analysis","club_analysis",
    "class_analysis","segment_analysis","replay","head_to_head","person_history",
    "course_history","goal_pace","team_members"
}
LOCAL_ASSET_STATUSES={"archived_organizer_gpx","derived_reconstructed_reference","derived_public_trace_geometry","derived_provisional_reference"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors):
    if errors:
        print("Prebuild audit FAILED:")
        for e in errors:
            print("  -",e)
        return 1
    print("Prebuild audit OK")
    return 0


def main():
    errors=[]
    courses=load(COURSES)
    readiness=load(READINESS)
    foundation=load(FOUNDATION)
    trail14_prov=load(TRAIL14_PROV)
    trail14_superseded_prov=load(TRAIL14_SUPERSEDED_PROV)

    versions={v["course_version_id"]:v for v in courses["versions"]}
    assignments={}
    for a in courses["assignments"]:
        key=(int(a["year"]),a["family"])
        if key in assignments:
            errors.append(f"duplicate course assignment {key}")
        assignments[key]=a
        vid=a.get("course_version_id")
        if vid is not None and vid not in versions:
            errors.append(f"{key}: unknown course version {vid}")
        if a.get("route_asset_available"):
            if not vid:
                errors.append(f"{key}: local route asset declared without course version")
                continue
            v=versions[vid]
            status=v.get("route_asset_status")
            if status not in LOCAL_ASSET_STATUSES:
                errors.append(f"{key}: route asset declared but status is {status}")
            p=v.get("primary_source_path")
            if not p or not (ROOT/p).exists():
                errors.append(f"{key}: declared route asset is missing: {p}")
            if status in {"derived_public_trace_geometry","derived_provisional_reference"} and not v.get("route_provenance_label"):
                errors.append(f"{key}: derived route asset lacks explicit provenance label")

    ready_by_key={r["race_key"]:r for r in readiness["races"]}
    if len(ready_by_key)!=34:
        errors.append(f"readiness must contain 34 held race instances, got {len(ready_by_key)}")
    if readiness["totals"].get("races_with_course_version")!=21:
        errors.append("readiness course-version total must be 21 after 2026 short-course overlay")

    for r in readiness["races"]:
        assignment=assignments.get((int(r["year"]),r["race_family"]))
        if assignment is None:
            continue
        if r.get("course_version")!=assignment.get("course_version_id"):
            errors.append(f"{r['race_key']}: readiness course version disagrees with config assignment")
        if bool(r.get("route_asset_available"))!=bool(assignment.get("route_asset_available")):
            errors.append(f"{r['race_key']}: readiness route-asset flag disagrees with config assignment")

    # Explicit policy checks for the current short-course references.
    t14=versions["trail14-current-reference"]
    if t14.get("status")!="provisional_hallamolla_splice_reference":
        errors.append("Trail 13/14 current reference is not marked provisional Hallamölla splice")
    if abs(float(t14.get("derived_path_distance_km",0))-13.472)>0.001:
        errors.append("Trail 13/14 working reference distance is not 13.472 km")
    if t14.get("route_asset_status")!="derived_provisional_reference":
        errors.append("Trail 13/14 materialized working reference lost derived_provisional_reference status")
    t14_path=t14.get("primary_source_path")
    if not t14_path or not (ROOT/t14_path).exists():
        errors.append("Trail 13/14 materialized provisional route is missing")
    if t14.get("route_provenance_label")!="Rekonstruerad bana · provisorisk":
        errors.append("Trail 13/14 materialized route lacks the required provisional publication label")
    for stale in (
        ROOT/"routes/ost/trail14-current-reference/route.geojson",
        ROOT/"routes/ost/trail14-current-reference/candidate-frontier.json",
    ):
        if stale.exists():
            errors.append(f"superseded Trail 13/14 artifact must stay removed: {stale.relative_to(ROOT)}")
    recipe=t14.get("reference_recipe",{})
    if recipe.get("base_course_version")!="trail22-2022-2024":
        errors.append("Trail 13/14 recipe base course must be trail22-2022-2024")
    if abs(float(recipe.get("removed_loop_km",0))-8.269)>0.001:
        errors.append("Trail 13/14 recipe removed-loop distance changed unexpectedly")
    if float(recipe.get("splice_point_separation_m",999))>=1.0:
        errors.append("Trail 13/14 Hallamölla splice points are no longer practically coincident")

    if trail14_prov.get("geometry_status")!="provisional_hallamolla_splice_reference":
        errors.append("active Trail 13/14 provenance is not the provisional Hallamölla splice")
    if trail14_prov.get("not_an_organizer_gpx") is not True:
        errors.append("active Trail 13/14 provenance must state that it is not organizer GPX")
    if trail14_prov.get("publication_label")!="Rekonstruerad bana · provisorisk":
        errors.append("active Trail 13/14 provenance lost its provisional publication label")
    if abs(float(trail14_prov.get("distance_km",0))-13.472)>0.001:
        errors.append("active Trail 13/14 provenance distance is not 13.472 km")
    if trail14_prov.get("base_course_version")!="trail22-2022-2024":
        errors.append("active Trail 13/14 provenance has the wrong base course")
    if trail14_prov.get("source_year_matches_manifest") is not True:
        errors.append("active Trail 13/14 base Trace source year is not verified")

    if trail14_superseded_prov.get("geometry_status")!="superseded_raster_candidate":
        errors.append("old 14.249 km raster candidate must remain explicitly superseded in its audit sidecar")
    if trail14_superseded_prov.get("publishable_as_reconstructed_reference") is not False:
        errors.append("old Trail 13/14 raster candidate must remain non-publishable")

    t5=versions["trail5-current-reference"]
    if t5.get("route_asset_status")!="derived_reconstructed_reference":
        errors.append("Trail 5 current reference lost reconstructed-route status")
    if not t5.get("primary_source_path") or not (ROOT/t5["primary_source_path"]).exists():
        errors.append("Trail 5 local reconstructed route asset is missing")

    # Foundation snapshot should agree with machine-readable readiness.
    if foundation.get("engine_readiness",{}).get("races_with_course_version")!=readiness["totals"].get("races_with_course_version"):
        errors.append("foundation-state course-version readiness count is stale")
    if foundation.get("engine_readiness",{}).get("races_with_replay_and_map_data")!=readiness["totals"].get("races_with_replay_ready_data"):
        errors.append("foundation-state replay readiness count is stale")

    # Build the actual Engine 1.0 payload and validate the frozen contract surface.
    with tempfile.TemporaryDirectory(prefix="ost-prebuild-") as td:
        out=Path(td)/"engine.json"
        run=subprocess.run(
            [sys.executable,str(EXPORTER),"--output",str(out)],
            cwd=ROOT,text=True,capture_output=True
        )
        if run.returncode:
            errors.append("Engine 1.0 export failed: "+(run.stderr or run.stdout).strip())
            return fail(errors)
        payload=load(out)

    missing=ENGINE_REQUIRED_TOP-set(payload)
    if missing:
        errors.append(f"Engine payload missing top-level keys: {sorted(missing)}")
    if ENGINE_EVENT_REQUIRED-set(payload["event"]):
        errors.append("Engine event object misses frozen contract fields")
    if len(payload["races"])!=34:
        errors.append("Engine payload race count is not 34")

    for rk,race in payload["races"].items():
        miss=ENGINE_RACE_REQUIRED-set(race)
        if miss:
            errors.append(f"{rk}: missing race fields {sorted(miss)}")
        if "entity" not in race.get("participant",{}):
            errors.append(f"{rk}: participant entity missing")
        comp=race.get("competition",{})
        if not {"format","team_structure"}<=set(comp):
            errors.append(f"{rk}: competition semantics incomplete")
        if not CAPABILITY_KEYS<=set(race.get("capabilities",{})):
            errors.append(f"{rk}: capability object incomplete")
        if race["capabilities"].get("replay"):
            cv=race.get("course_version")
            if not cv or not payload["courses"].get(cv,{}).get("assets",{}).get("route_source"):
                errors.append(f"{rk}: replay enabled without a local route source")

    # High-value acceptance cases.
    if payload["races"]["ost-2018-trail22"].get("course_version") is not None:
        errors.append("2018 Trail 21/22 must remain explicitly unassigned")
    trail14=payload["races"]["ost-2026-trail14"]
    if trail14.get("course_version")!="trail14-current-reference":
        errors.append("2026 Trail 13/14 working course version missing from engine export")
    if trail14["capabilities"]["segment_analysis"] or trail14["capabilities"]["replay"]:
        errors.append("2026 Trail 13/14 must remain finish-only/no replay")
    t14assets=payload["courses"]["trail14-current-reference"]["assets"]
    if not t14assets.get("route_source"):
        errors.append("Trail 13/14 materialized provisional route is missing from engine export")
    if t14assets.get("official_gpx") is not False or t14assets.get("route_asset_status")!="derived_provisional_reference":
        errors.append("Trail 13/14 engine provenance is not explicitly provisional/derived")
    old_ultra=payload["races"]["ost-2018-ultra60"]
    if not payload["courses"][old_ultra["course_version"]]["assets"].get("route_source") or old_ultra["capabilities"]["replay"]:
        errors.append("2018 Ultra must expose its verified map route while keeping replay disabled")
    modern_2022=payload["races"]["ost-2022-ultra60"]
    if not modern_2022["capabilities"]["replay"]:
        errors.append("2022 Ultra should have replay after verified Bengtemölla route anchoring")
    trail22_2026=payload["races"]["ost-2026-trail22"]
    if not payload["courses"][trail22_2026["course_version"]]["assets"].get("route_source") or trail22_2026["capabilities"]["replay"]:
        errors.append("2026 Trail 21/22 must expose its route map without synthetic replay")
    trail5=payload["races"]["ost-2026-trail5"]
    if trail5.get("course_version")!="trail5-current-reference":
        errors.append("2026 Trail 5 working course version missing from engine export")
    t5assets=payload["courses"]["trail5-current-reference"]["assets"]
    if not t5assets.get("route_source") or t5assets.get("official_gpx") is not False:
        errors.append("Trail 5 reconstructed route provenance is not explicit in engine export")
    if trail5["capabilities"]["replay"]:
        errors.append("Trail 5 replay must remain disabled without observed intermediate splits")

    return fail(errors)


if __name__=="__main__":
    raise SystemExit(main())
