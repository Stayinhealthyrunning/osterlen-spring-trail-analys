#!/usr/bin/env python3
"""Reconstruct the legacy ÖST Trail 13/14 route from its organizer raster.

This replaces the rejected "Trail 5 + eastern OSM loop" hypothesis. The
13-km organizer map contains its own western loop, a shared Christinehof-
Verkeån connector, and an eastern Hallamölla loop. The visible organizer
centreline is the primary source. OSM/official local trails are corroboration,
not geometry substitutes.
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
NE = (437465.0, 6176791.0)  # corrected from organizer Trail-5 raster label
TRAIL5_SHIFT = (9.3226605679, 111.9119652826)
HALLAMOLLA_WGS84 = (14.01780, 55.70819)
RDP_EPSILON_PX = 1.0


def d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def path_length(graph, path):
    return sum(graph[u][v]["weight"] for u, v in zip(path, path[1:]))


def extract_graph(imgpath, threshold=90, crop=(50, 150, 950, 580)):
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
        graph.add_node((y, x))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if not (dx or dy):
                    continue
                q = (y + dy, x + dx)
                if q in pts:
                    graph.add_edge((y, x), q, weight=math.hypot(dx, dy))
    return graph


def cycle_perimeter(graph, cycle):
    return sum(
        graph[cycle[i]][cycle[(i + 1) % len(cycle)]]["weight"]
        for i in range(len(cycle))
    )


def simplify_xy_pixels(points, epsilon=RDP_EPSILON_PX):
    arr = np.asarray([(p[1], p[0]) for p in points], dtype=np.float32).reshape(-1, 1, 2)
    out = cv2.approxPolyDP(arr, epsilon, False).reshape(-1, 2)
    return [(float(y), float(x)) for x, y in out]


def homography_pixel_to_3006(node, H):
    y, x = node
    vec = H @ np.array([x, y, 1.0])
    u, v = vec[0] / vec[2], vec[1] / vec[2]
    fx = (u - FRAME["left"]) / (FRAME["right"] - FRAME["left"])
    fy = (v - FRAME["top"]) / (FRAME["bottom"] - FRAME["top"])
    return (
        SW[0] + fx * (NE[0] - SW[0]) + TRAIL5_SHIFT[0],
        NE[1] - fy * (NE[1] - SW[1]) + TRAIL5_SHIFT[1],
    )


def cumulative_length_xy(points):
    out = [0.0]
    for a, b in zip(points, points[1:]):
        out.append(out[-1] + d(a, b))
    return out


def nearest_point_on_polyline(point, line):
    best = (float("inf"), 0.0)
    cumulative = 0.0
    for a, b in zip(line, line[1:]):
        vx, vy = b[0] - a[0], b[1] - a[1]
        den = vx * vx + vy * vy
        t = 0.0 if den <= 0 else max(
            0.0,
            min(1.0, ((point[0] - a[0]) * vx + (point[1] - a[1]) * vy) / den),
        )
        q = (a[0] + t * vx, a[1] + t * vy)
        sep = d(point, q)
        along = cumulative + t * d(a, b)
        if sep < best[0]:
            best = (sep, along)
        cumulative += d(a, b)
    return best


def load_osm_vertices(path):
    data = json.loads(Path(path).read_text())
    tr = Transformer.from_crs(4326, 3006, always_xy=True)
    points = []
    for feat in data.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") == "LineString":
            points.extend(tr.transform(lon, lat) for lon, lat in geom.get("coordinates", []))
    return points


def main():
    ap = argparse.ArgumentParser()
    for name in ("image", "network", "registration", "relations", "trail5", "geojson", "gpx", "qa"):
        ap.add_argument("--" + name, required=True)
    args = ap.parse_args()

    graph = extract_graph(args.image)
    endpoints = [node for node, degree in graph.degree() if degree == 1]
    if len(endpoints) < 4:
        raise RuntimeError(f"Expected organizer line plus arrow-spur endpoints; got {len(endpoints)}")
    west_endpoints = sorted(endpoints, key=lambda p: p[1])[:2]
    west_path = nx.shortest_path(graph, west_endpoints[0], west_endpoints[1], weight="weight")

    cycles = nx.cycle_basis(graph)
    if not cycles:
        raise RuntimeError("No organizer-raster loop found")
    east_cycle = max(cycles, key=lambda c: cycle_perimeter(graph, c))

    distances, paths = nx.multi_source_dijkstra(graph, west_path, weight="weight")
    east_join = min(east_cycle, key=lambda n: distances.get(n, float("inf")))
    connector = paths[east_join]
    west_join = connector[0]
    if west_join not in west_path:
        raise RuntimeError("Connector did not originate on western organizer path")

    j = west_path.index(west_join)
    left = west_path[: j + 1]
    right = west_path[j:]
    if path_length(graph, left) >= path_length(graph, right):
        western_before = left
        western_after = right
    else:
        western_before = list(reversed(right))
        western_after = list(reversed(left))

    # cycle_basis returns cyclic node order. Rotate it to the connector join.
    ci = east_cycle.index(east_join)
    fwd = east_cycle[ci:] + east_cycle[:ci] + [east_join]
    rev_base = list(reversed(east_cycle))
    ri = rev_base.index(east_join)
    rev = rev_base[ri:] + rev_base[:ri] + [east_join]

    reg = json.loads(Path(args.registration).read_text())
    H = np.asarray(reg["trail14_to_trail5_homography"], dtype=float)
    to_xy = lambda node: homography_pixel_to_3006(node, H)
    hall = Transformer.from_crs(4326, 3006, always_xy=True).transform(*HALLAMOLLA_WGS84)

    # Independent 2023 activity text says Hallamölla was reached with ~4.5 km
    # remaining. Choose route direction only; never fit geometry to that distance.
    def hall_stats(seq):
        line = [to_xy(p) for p in seq]
        sep, along = nearest_point_on_polyline(hall, line)
        return sep, along

    f_sep, f_along = hall_stats(fwd)
    r_sep, r_along = hall_stats(rev)
    cycle_route = fwd if f_along >= r_along else rev

    # Suppress one-pixel skeleton staircase noise while preserving the organizer
    # line topology. Simplify open pieces independently so repeated connector
    # geometry remains exactly repeated.
    western_before_s = simplify_xy_pixels(western_before)
    connector_s = simplify_xy_pixels(connector)

    cycle_xy_dense = [to_xy(p) for p in cycle_route]
    hall_index = min(range(len(cycle_route) - 1), key=lambda i: d(cycle_xy_dense[i], hall))
    arc1_s = simplify_xy_pixels(cycle_route[: hall_index + 1])
    arc2_s = simplify_xy_pixels(cycle_route[hall_index:])
    cycle_s = arc1_s + arc2_s[1:]
    western_after_s = simplify_xy_pixels(western_after)

    route_nodes = (
        western_before_s
        + connector_s[1:]
        + cycle_s[1:]
        + list(reversed(connector_s))[1:]
        + western_after_s[1:]
    )
    route_xy = [to_xy(p) for p in route_nodes]
    total_m = cumulative_length_xy(route_xy)[-1]
    hall_sep, hall_along = nearest_point_on_polyline(hall, route_xy)

    osm_vertices = load_osm_vertices(args.network)
    osm_dev = []
    if osm_vertices:
        tree = cKDTree(osm_vertices)
        osm_dev = [float(tree.query(p)[0]) for p in route_xy]

    back = Transformer.from_crs(3006, 4326, always_xy=True)
    route_ll = [back.transform(*p) for p in route_xy]
    properties = {
        "name": "ÖST Trail 13/14 km organizer-raster reconstruction",
        "status": "validated_organizer_raster_reconstruction",
        "provenance": "legacy organizer 13 km raster; corrected SWEREF calibration; OSM only corroborates",
        "distance_km": round(total_m / 1000, 3),
    }
    feat = {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "LineString", "coordinates": [list(p) for p in route_ll]},
    }
    Path(args.geojson).write_text(json.dumps(feat, ensure_ascii=False, indent=2) + "\n")
    trk = "".join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon, lat in route_ll)
    Path(args.gpx).write_text(
        '<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys raster reconstruction">'
        "<trk><name>ÖST Trail 13/14 km reconstructed from organizer map</name><trkseg>"
        + trk
        + "</trkseg></trk></gpx>\n"
    )

    connector_m = cumulative_length_xy([to_xy(p) for p in connector_s])[-1]
    west_before_m = cumulative_length_xy([to_xy(p) for p in western_before_s])[-1]
    west_after_m = cumulative_length_xy([to_xy(p) for p in western_after_s])[-1]
    east_cycle_m = cumulative_length_xy([to_xy(p) for p in cycle_s])[-1]

    qa = {
        "geometry_status": "validated_organizer_raster_reconstruction",
        "distance_km": round(total_m / 1000, 3),
        "organizer_map_label_km": 13.0,
        "current_marketing_distance_km": 14.0,
        "participant_2023_watch_km": 13.67,
        "participant_difference_m": round(total_m - 13670.0, 1),
        "source_pixels": graph.number_of_nodes(),
        "route_vertices": len(route_nodes),
        "rdp_epsilon_px": RDP_EPSILON_PX,
        "topology": {
            "western_before_km": round(west_before_m / 1000, 3),
            "shared_connector_one_way_km": round(connector_m / 1000, 3),
            "eastern_cycle_km": round(east_cycle_m / 1000, 3),
            "western_finish_km": round(west_after_m / 1000, 3),
            "connector_traversals": 2,
        },
        "sweref99tm_controls": {
            "southwest": {"E": SW[0], "N": SW[1]},
            "northeast": {"E": NE[0], "N": NE[1]},
            "east_control_correction_m": -500.0,
        },
        "map_registration_median_px": reg["reprojection_px"]["median"],
        "map_registration_p95_px": reg["reprojection_px"]["p95"],
        "trail5_calibration_translation_m": [round(TRAIL5_SHIFT[0], 1), round(TRAIL5_SHIFT[1], 1)],
        "start_finish_gap_m": round(d(route_xy[0], route_xy[-1]), 1),
        "hallamolla_control_m": round(hall_sep, 1),
        "hallamolla_route_km": round(hall_along / 1000, 3),
        "hallamolla_remaining_km": round((total_m - hall_along) / 1000, 3),
        "direction_evidence": "participant_2023_hallamolla_remaining_distance_plus_organizer_arrows",
        "organizer_raster_centreline_primary": True,
        "osm_role": "corroboration_only",
        "osm_vertex_distance_m": {
            "median": round(float(np.median(osm_dev)), 1) if osm_dev else None,
            "p95": round(float(np.percentile(osm_dev, 95)), 1) if osm_dev else None,
            "max": round(float(np.max(osm_dev)), 1) if osm_dev else None,
        },
        "legacy_map_assignment_warning": "Validated geometry for the organizer's legacy 13 km raster; not proof that every historical 13 km or current 14 km edition is identical.",
    }
    Path(args.qa).write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n")
    frontier = {
        "status": "superseded",
        "reason": "Trail 13/14 is reconstructed from its own organizer raster topology; it is not composed from the Trail 5 loop.",
        "corrected_east_control": 437465,
        "previous_east_control": 437965,
    }
    Path(args.qa).with_name("candidate-frontier.json").write_text(json.dumps(frontier, indent=2) + "\n")
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
