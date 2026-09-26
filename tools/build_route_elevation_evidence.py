#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "reports" / "tracedetrail-public-geometry-analysis.json"
MANIFEST = ROOT / "config" / "course-source-manifest.json"
GPX = ROOT / "reports" / "gpx-source-analysis.json"
OUT_JSON = ROOT / "reports" / "route-elevation-evidence.json"
OUT_MD = ROOT / "reports" / "route-elevation-evidence.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    trace = load(TRACE)
    manifest = load(MANIFEST)
    gpx = load(GPX)

    by_trace = {}
    for source in manifest.get("sources", []):
        tid = source.get("trace_id")
        if tid is not None:
            by_trace[int(tid)] = source

    rows = []
    for route in trace.get("routes", []):
        tid = int(route["trace_id"])
        source = by_trace.get(tid, {})
        asc = route.get("source_dp_last")
        desc = route.get("source_dn_last")
        reported_asc = source.get("reported_ascent_m")
        reported_desc = source.get("reported_descent_m")

        comparison = None
        if asc is not None and reported_asc is not None:
            comparison = {
                "ascent_delta_m": round(float(asc) - float(reported_asc), 1),
                "descent_delta_m": None if reported_desc is None or desc is None else round(float(desc) - float(reported_desc), 1),
            }

        rows.append({
            "family": route["family"],
            "year": route["year"],
            "trace_id": tid,
            "source_date_compet": route.get("source_date_compet"),
            "source_year_matches_manifest": route.get("source_year_matches_manifest"),
            "route_distance_km": route.get("path_distance_km"),
            "profile_distance_last_km": route.get("source_x_last"),
            "profile_sample_count": route.get("source_x_count"),
            "profile_elevation_min_m": route.get("source_y_min"),
            "profile_elevation_max_m": route.get("source_y_max"),
            "trace_cumulative_ascent_m": asc,
            "trace_cumulative_descent_m": desc,
            "manifest_reported_ascent_m": reported_asc,
            "manifest_reported_descent_m": reported_desc,
            "manifest_agreement": comparison,
            "usage": "source_specific_elevation_evidence_not_standardized_cross_year",
        })

    local_gpx = []
    for f in gpx.get("files", []):
        local_gpx.append({
            "path": f["path"],
            "distance_km": f.get("distance_km"),
            "raw_ascent_m": f.get("raw_ascent_m"),
            "raw_descent_m": f.get("raw_descent_m"),
            "min_ele_m": f.get("min_ele_m"),
            "max_ele_m": f.get("max_ele_m"),
            "usage": "raw_source_gpx_diagnostic_not_standardized_cross_year",
        })

    payload = {
        "schema_version": 1,
        "method_notes": [
            "Trace de Trail public dataTrace geometry includes route-distance/elevation fields and cumulative positive/negative elevation values. This report stores only factual elevation/distance summaries, not coordinate arrays.",
            "trace_cumulative_ascent_m/descent_m are source-specific values and must not be treated as a harmonized cross-year D+/D- metric.",
            "Local organizer GPX raw ascent/descent is retained separately because point density, elevation source and filtering differ from Trace de Trail and participant recordings.",
            "Cross-year elevation comparisons must use config/elevation-policy.json and one common DEM/filter method.",
        ],
        "trace_routes": sorted(rows, key=lambda r: (r["family"], r["year"])),
        "local_organizer_gpx": local_gpx,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Route elevation evidence",
        "",
        "Source-specific elevation evidence extracted from existing verified route sources. These values are **not** a harmonized cross-year D+ series.",
        "",
        "## Trace de Trail",
        "",
        "| Family | Year | km | profile pts | elev min–max | D+ | D- | provenance |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in payload["trace_routes"]:
        prov = "year-match" if r["source_year_matches_manifest"] else "date mismatch ⚠"
        lines.append(
            f"| `{r['family']}` | {r['year']} | {r['route_distance_km']:.3f} | "
            f"{r['profile_sample_count'] or 0} | {r['profile_elevation_min_m']}–{r['profile_elevation_max_m']} m | "
            f"{r['trace_cumulative_ascent_m'] if r['trace_cumulative_ascent_m'] is not None else '—'} | "
            f"{r['trace_cumulative_descent_m'] if r['trace_cumulative_descent_m'] is not None else '—'} | {prov} |"
        )

    lines += [
        "",
        "## Local organizer GPX",
        "",
        "| File | km | raw D+ | raw D- | elevation range |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in local_gpx:
        lines.append(
            f"| `{r['path']}` | {r['distance_km']:.3f} | {r['raw_ascent_m']} | {r['raw_descent_m']} | "
            f"{r['min_ele_m']}–{r['max_ele_m']} m |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- Trace values are valuable historical source evidence and can supply route-profile metadata where an organizer GPX lacks elevation.",
        "- The 2024 organizer GPX has incomplete elevation and a raw D+ of 0 in the current parser, while the matching Trace route exposes a complete profile summary and cumulative +693/-578 m.",
        "- The 2025/2026 organizer GPX raw +1058/-942 m differs materially from Trace (+680/-564 in 2025; +683/-567 in 2026), demonstrating method dependence rather than a trustworthy cross-source D+ identity.",
        "- Therefore the public product should keep source-specific values for transparency and use a separately standardized DEM-derived profile for cross-year comparisons.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
