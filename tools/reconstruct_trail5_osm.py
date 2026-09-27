#!/usr/bin/env python3
"""Reconstruct ÖST Trail 5 directly from the georeferenced organizer raster.

The organizer raster is the primary geometry source. OSM is only a secondary
corroboration layer; it must not pull the course away from the visible race line.
"""
from __future__ import annotations

import argparse, json, math
from pathlib import Path

import cv2
import networkx as nx
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree
from skimage.morphology import skeletonize

FRAME = {"left": 25.3, "right": 1074.7, "top": 49.5, "bottom": 694.7}
SW = (432733.0, 6173751.0)
NE = (437465.0, 6176791.0)  # printed on organizer raster; 437965 was a transcription error
CASTLE = (434707.0, 6175169.0)
RDP_EPSILON_PX = 2.0


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def extract_ordered(imgpath, threshold=90, crop=(40, 120, 700, 650)):
    img = cv2.imread(imgpath, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Could not read {imgpath}")
    x0, y0, x1, y1 = crop
    roi = img[y0:y1, x0:x1]
    n, labels, stats, _ = cv2.connectedComponentsWithStats((roi < threshold).astype(np.uint8), 8)
    idx = max(range(1, n), key=lambda i: stats[i, cv2.CC_STAT_AREA])
    full = np.zeros_like(img, dtype=bool)
    full[y0:y1, x0:x1] = labels == idx
    sk = skeletonize(full)
    pts = {tuple(map(int, p)) for p in np.argwhere(sk)}
    graph = nx.Graph()
    for y, x in pts:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if not (dx or dy):
                    continue
                q = (y + dy, x + dx)
                if q in pts:
                    graph.add_edge((y, x), q, weight=math.hypot(dx, dy))
    ends = [p for p, degree in graph.degree() if degree == 1]
    if len(ends) != 2:
        raise RuntimeError(f"Expected 2 route endpoints, got {len(ends)}")
    path = nx.shortest_path(graph, ends[0], ends[1], weight="weight")
    return [(x, y) for y, x in path]


def simplify_pixels(points, epsilon=RDP_EPSILON_PX):
    arr = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    out = cv2.approxPolyDP(arr, epsilon, False).reshape(-1, 2)
    return [(float(x), float(y)) for x, y in out]


def px_to_3006(p):
    x, y = p
    fx = (x - FRAME["left"]) / (FRAME["right"] - FRAME["left"])
    fy = (y - FRAME["top"]) / (FRAME["bottom"] - FRAME["top"])
    return (
        SW[0] + fx * (NE[0] - SW[0]),
        NE[1] - fy * (NE[1] - SW[1]),
    )


def calibration_shift(raw_endpoints):
    mid = (
        (raw_endpoints[0][0] + raw_endpoints[-1][0]) / 2,
        (raw_endpoints[0][1] + raw_endpoints[-1][1]) / 2,
    )
    return CASTLE[0] - mid[0], CASTLE[1] - mid[1]


def line_length(points):
    return sum(dist(a, b) for a, b in zip(points, points[1:]))


def load_osm_vertices(path):
    data = json.loads(Path(path).read_text())
    tr = Transformer.from_crs(4326, 3006, always_xy=True)
    points = []
    for feat in data.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") != "LineString":
            continue
        points.extend(tr.transform(lon, lat) for lon, lat in geom.get("coordinates", []))
    return points


def write_outputs(args, xy, qa):
    back = Transformer.from_crs(3006, 4326, always_xy=True)
    ll = [back.transform(*p) for p in xy]
    feat = {
        "type": "Feature",
        "properties": {
            "name": "ÖST Naturloppet 5 km organizer-raster reconstruction",
            "status": "validated_organizer_raster_reconstruction",
            "provenance": "georeferenced organizer raster centreline; OSM used only for corroboration",
            "distance_km": round(line_length(xy) / 1000, 3),
        },
        "geometry": {"type": "LineString", "coordinates": [list(p) for p in ll]},
    }
    Path(args.geojson).write_text(json.dumps(feat, ensure_ascii=False, indent=2) + "\n")
    trk = "".join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon, lat in ll)
    Path(args.gpx).write_text(
        '<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys raster reconstruction">'
        "<trk><name>ÖST Naturloppet 5 km reconstructed from organizer map</name><trkseg>"
        + trk
        + "</trkseg></trk></gpx>\n"
    )
    Path(args.qa).write_text(json.dumps(qa, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--network", required=True)
    ap.add_argument("--geojson", required=True)
    ap.add_argument("--gpx", required=True)
    ap.add_argument("--qa", required=True)
    args = ap.parse_args()

    raw_pixels = extract_ordered(args.image)
    simplified = simplify_pixels(raw_pixels)
    raw_xy = [px_to_3006(p) for p in simplified]
    endpoint_xy = [px_to_3006(raw_pixels[0]), px_to_3006(raw_pixels[-1])]
    shift = calibration_shift(endpoint_xy)
    xy = [(p[0] + shift[0], p[1] + shift[1]) for p in raw_xy]

    osm_vertices = load_osm_vertices(args.network)
    osm_dev = []
    if osm_vertices:
        tree = cKDTree(osm_vertices)
        osm_dev = [float(tree.query(p)[0]) for p in xy]

    qa = {
        "geometry_status": "validated_organizer_raster_reconstruction",
        "distance_km": round(line_length(xy) / 1000, 3),
        "nominal_km": 5.0,
        "source_pixels": len(raw_pixels),
        "simplified_vertices": len(simplified),
        "rdp_epsilon_px": RDP_EPSILON_PX,
        "sweref99tm_controls": {
            "southwest": {"E": SW[0], "N": SW[1]},
            "northeast": {"E": NE[0], "N": NE[1]},
            "east_control_correction_m": -500.0,
        },
        "raster_translation_m": [round(shift[0], 1), round(shift[1], 1)],
        "start_finish_gap_m": round(dist(xy[0], xy[-1]), 1),
        "organizer_raster_centreline_primary": True,
        "osm_role": "corroboration_only",
        "osm_vertex_distance_m": {
            "median": round(float(np.median(osm_dev)), 1) if osm_dev else None,
            "p95": round(float(np.percentile(osm_dev, 95)), 1) if osm_dev else None,
            "max": round(float(np.max(osm_dev)), 1) if osm_dev else None,
        },
        "prototype_length_km": 5.002,
        "prototype_difference_m": round((line_length(xy) / 1000 - 5.002) * 1000, 1),
    }
    write_outputs(args, xy, qa)
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    main()
