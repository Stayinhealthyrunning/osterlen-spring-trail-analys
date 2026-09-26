#!/usr/bin/env python3
"""Extract path/road candidate geometry from a small OpenStreetMap XML export.

This helper is intentionally route-neutral: it does not decide which OSM ways
belong to Österlen Spring Trail. It preserves source way IDs and tags so a later
raster-to-network snap can remain auditable.

Example:
    python tools/extract_osm_path_network.py christinehof.osm christinehof-paths.geojson
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_HIGHWAYS = {
    "path",
    "footway",
    "track",
    "steps",
    "pedestrian",
    "service",
    "unclassified",
    "tertiary",
    "secondary",
    "residential",
    "living_street",
    "cycleway",
    "bridleway",
    "road",
}


def parse_osm(path: Path, accepted: set[str]) -> dict:
    nodes: dict[str, tuple[float, float]] = {}
    selected_ways: list[dict] = []

    for _event, elem in ET.iterparse(path, events=("end",)):
        if elem.tag == "node":
            node_id = elem.attrib.get("id")
            if node_id and "lat" in elem.attrib and "lon" in elem.attrib:
                nodes[node_id] = (float(elem.attrib["lon"]), float(elem.attrib["lat"]))
            elem.clear()
            continue

        if elem.tag != "way":
            continue

        tags = {
            child.attrib["k"]: child.attrib["v"]
            for child in elem.findall("tag")
            if "k" in child.attrib and "v" in child.attrib
        }
        highway = tags.get("highway")
        if highway in accepted:
            selected_ways.append(
                {
                    "id": elem.attrib.get("id"),
                    "refs": [
                        child.attrib["ref"]
                        for child in elem.findall("nd")
                        if "ref" in child.attrib
                    ],
                    "tags": tags,
                }
            )
        elem.clear()

    features = []
    skipped_missing_nodes = 0
    for way in selected_ways:
        coordinates = []
        for ref in way["refs"]:
            point = nodes.get(ref)
            if point is None:
                coordinates = []
                skipped_missing_nodes += 1
                break
            coordinates.append(point)
        if len(coordinates) < 2:
            continue

        way_id = way["id"]
        if way_id and way_id.lstrip("-").isdigit():
            way_id = int(way_id)

        features.append(
            {
                "type": "Feature",
                "properties": {"osm_way_id": way_id, **way["tags"]},
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "metadata": {
            "source_format": "OpenStreetMap XML",
            "selection": "way with highway tag in accepted_highways",
            "accepted_highways": sorted(accepted),
            "node_count": len(nodes),
            "selected_way_count": len(selected_ways),
            "feature_count": len(features),
            "skipped_missing_nodes": skipped_missing_nodes,
        },
        "features": features,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_osm", type=Path)
    parser.add_argument("output_geojson", type=Path)
    parser.add_argument(
        "--highway",
        action="append",
        dest="highways",
        help="Accepted OSM highway value; repeat to override defaults.",
    )
    args = parser.parse_args()

    accepted = set(args.highways) if args.highways else set(DEFAULT_HIGHWAYS)
    result = parse_osm(args.input_osm, accepted)
    args.output_geojson.parent.mkdir(parents=True, exist_ok=True)
    args.output_geojson.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {result['metadata']['feature_count']} ways "
        f"({result['metadata']['node_count']} nodes read) "
        f"to {args.output_geojson}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
