#!/usr/bin/env python3
"""Year-specific controls for the 2018 ÖST Verkeån Trail 21km+ candidate.

Trace 7897 has dateCompet=2016, so its public geometry may not be assigned to
2018 merely from its filename/metadata. This script decodes the public map
geometry transiently and tests independent 2018 race-day landmarks and official
race metrics. Full coordinate arrays are never persisted.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from analyze_tracedetrail_public_geometry import (
    fetch, datatrace_object, top_properties, decode_geometry, cumulative,
    nearest_route_point,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/trail22-2018-triangulation.json"
OUT_MD=ROOT/"reports/trail22-2018-triangulation.md"
TRACE_ID=7897

# Public landmark coordinates. These are only point controls, not route geometry.
LANDMARKS=[
    {
      "key":"vantalangan",
      "name":"Vantalängan",
      "lat":55.72328,
      "lon":14.05955,
      "source":"https://mapcarta.com/N7125225402",
      "independent_2018_evidence":"Forsbackarunner race report places the steep climb immediately after Vantalängan at about km 14; current organizer material places the Vantalängan aid station at 13 km."
    },
    {
      "key":"hallamolla",
      "name":"Hallamölla",
      "lat":55.70819,
      "lon":14.01780,
      "source":"project independent control; see research/hallamolla-independent-controls-2026-09-26.md",
      "independent_2018_evidence":"The documented Verkeån race corridor passes Hallamölla before and after the Vantalängan section."
    },
]

def main():
    html, final=fetch(TRACE_ID)
    props=top_properties(datatrace_object(html))
    raw,pts=decode_geometry(props["geometry"])
    cum=cumulative(pts)
    total=cum[-1]/1000
    source_dp_values=[p.get("dp") for p in raw if isinstance(p,dict) and isinstance(p.get("dp"),(int,float))]
    source_dn_values=[p.get("dn") for p in raw if isinstance(p,dict) and isinstance(p.get("dn"),(int,float))]
    source_dp=source_dp_values[-1] if source_dp_values else None
    source_dn=source_dn_values[-1] if source_dn_values else None

    landmarks=[]
    for lm in LANDMARKS:
        sep,along=nearest_route_point(lm["lat"],lm["lon"],pts,cum)
        landmarks.append({
            **lm,
            "projected_distance_km":round(along/1000,3),
            "off_route_m":round(sep,1),
            "remaining_km":round(total-along/1000,3),
        })

    v=next(x for x in landmarks if x["key"]=="vantalangan")
    # Conservative gate: candidate must actually run at Vantalängan and reach it
    # in the independently documented race-day distance window.
    vantalangan_consistent=(v["off_route_m"] <= 150 and 12.0 <= v["projected_distance_km"] <= 14.2)

    # Official ITRA/UTMB 2018 race record: 21.7 km / 490 m+.
    metric_consistent=(
        abs(total-21.7) <= 0.35
        and (source_dp is None or abs(float(source_dp)-490) <= 40)
    )

    payload={
      "schema_version":1,
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "candidate":{
        "trace_id":TRACE_ID,
        "source_url":final,
        "source_date_compet":props.get("dateCompet"),
        "source_reported_distance_km":props.get("distance"),
        "derived_path_distance_km":round(total,3),
        "source_dp_last":source_dp,
        "source_dn_last":source_dn,
      },
      "independent_2018_controls":{
        "official_race_date":"2018-04-14",
        "official_distance_km":21.7,
        "official_ascent_m":490,
        "official_2016_ascent_m":290,
        "elevation_discrimination_note":"Trace 7897 exposes about 482 m D+, which is inconsistent with the official 2016 race's 290 m but closely matches the 2017-2018 490 m and 2019 480 m event records.",
        "race_day_watch_distance_km":22.03,
        "race_day_watch_source":"https://www.jogg.se/Traning/Pass.aspx?id=15416220",
        "race_day_narrative_source":"https://forsbacka10487151.wordpress.com/2018/04/15/ett-perfekt-osterlen-spring-trail/",
        "narrative":"First kilometres were easier; Vantalängan was followed by a steep climb around km 14; finish reported as roughly 22 km.",
      },
      "landmarks":landmarks,
      "tests":{
        "vantalangan_consistent":vantalangan_consistent,
        "official_metrics_consistent":metric_consistent,
      },
      "interpretation":(
        "triangulated_2018_reference_supported"
        if vantalangan_consistent and metric_consistent
        else "candidate_not_sufficiently_supported"
      ),
      "provenance_warning":"Trace dateCompet remains 2016. Passing these controls supports use as a triangulated 2018 reference geometry; it does not turn the Trace metadata into a direct 2018 source or grant redistribution rights.",
      "coordinate_storage_policy":"Trace coordinate series decoded transiently only; no coordinate array persisted."
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    lines=[
      "# Trail 21/22 — 2018 triangulation",
      "",
      f"- Trace candidate: {TRACE_ID}; Trace dateCompet: **{props.get('dateCompet')}**.",
      f"- Transient geometry length: **{total:.3f} km**; public Trace D+/D- endpoint: **{source_dp}/{source_dn} m**.",
      "- Independent 2018 event record: **21.7 km / 490 m+**.",
      "- Jörgen Forsbacka race-day watch: **22.03 km**; his race report places the steep climb after Vantalängan around km 14.",
      "",
      "## Landmark projection",
      "",
      "| Landmark | candidate km | remaining km | off route |",
      "|---|---:|---:|---:|",
    ]
    for lm in landmarks:
        lines.append(f"| {lm['name']} | {lm['projected_distance_km']:.3f} | {lm['remaining_km']:.3f} | {lm['off_route_m']:.1f} m |")
    lines += [
      "",
      f"Vantalängan consistency gate: **{'PASS' if vantalangan_consistent else 'FAIL'}**.",
      f"Official metric consistency gate: **{'PASS' if metric_consistent else 'FAIL'}**.",
      "",
      "## Interpretation",
      "",
      payload["interpretation"],
      "",
      "The full Trace coordinate array is not stored. A passing result supports a provenance-labelled triangulated 2018 reference assignment, not a claim that Trace's stale 2016 date field is correct for 2018 and not a right to redistribute its coordinates.",
    ]
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
