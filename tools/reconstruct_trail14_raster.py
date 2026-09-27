#!/usr/bin/env python3
import argparse
import heapq
import json
import math
from pathlib import Path

from pyproj import Transformer


def d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(p, a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    if dx == 0 and dy == 0:
        return d(p, a)
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    q = (a[0] + t * dx, a[1] + t * dy)
    return d(p, q)


def rdp(points, epsilon):
    if len(points) < 3:
        return points[:]
    best_d = 0.0
    best_i = -1
    a, b = points[0], points[-1]
    for i in range(1, len(points) - 1):
        dd = point_segment_distance(points[i], a, b)
        if dd > best_d:
            best_d = dd
            best_i = i
    if best_d > epsilon:
        left = rdp(points[: best_i + 1], epsilon)
        right = rdp(points[best_i:], epsilon)
        return left[:-1] + right
    return [points[0], points[-1]]


def build_graph(points):
    index = {tuple(p): i for i, p in enumerate(points)}
    adj = [[] for _ in points]
    for i, (x, y) in enumerate(points):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                j = index.get((x + dx, y + dy))
                if j is not None:
                    adj[i].append(j)
    return index, adj


def shortest_path(points, adj, start, target):
    inf = float("inf")
    dist = [inf] * len(points)
    prev = [-1] * len(points)
    dist[start] = 0.0
    heap = [(0.0, start)]
    while heap:
        du, u = heapq.heappop(heap)
        if du != dist[u]:
            continue
        if u == target:
            break
        for v in adj[u]:
            w = d(points[u], points[v])
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if not math.isfinite(dist[target]):
        raise RuntimeError("No raster-skeleton path between required topology nodes")
    out = []
    u = target
    while u != -1:
        out.append(u)
        if u == start:
            break
        u = prev[u]
    out.reverse()
    return [points[i] for i in out]


def polyline_length(points):
    return sum(d(a, b) for a, b in zip(points, points[1:]))


def rotate_cycle_to(cycle, anchor):
    if tuple(cycle[0]) == tuple(cycle[-1]):
        cycle = cycle[:-1]
    i = min(range(len(cycle)), key=lambda k: d(cycle[k], anchor))
    out = cycle[i:] + cycle[:i]
    out.append(out[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skeleton", required=True)
    ap.add_argument("--registration", required=True)
    ap.add_argument("--trail5-georef", required=True)
    ap.add_argument("--trail5-qa", required=True)
    ap.add_argument("--geojson", required=True)
    ap.add_argument("--gpx", required=True)
    ap.add_argument("--qa", required=True)
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--epsilon-px", type=float, default=4.0)
    args = ap.parse_args()

    sk = json.loads(Path(args.skeleton).read_text())
    reg = json.loads(Path(args.registration).read_text())
    georef = json.loads(Path(args.trail5_georef).read_text())
    t5qa = json.loads(Path(args.trail5_qa).read_text())

    points = [tuple(map(float, p)) for p in sk["skeleton_pixels_xy"]]
    index, adj = build_graph(points)

    endpoints = [i for i, a in enumerate(adj) if len(a) == 1]
    if len(endpoints) < 2:
        raise RuntimeError("Expected raster route endpoints were not found")

    # The genuine start/finish pair is the western pair. The two far-eastern
    # endpoints belong to arrow/line artefacts attached to the thick route ink.
    west_endpoints = sorted(endpoints, key=lambda i: (points[i][0], points[i][1]))[:2]

    principal_cycle = max(sk["cycles"], key=lambda c: c["node_count"])
    cycle_vertices = [tuple(map(float, p)) for p in principal_cycle["vertices_xy"]]
    junctions = {tuple(map(float, p)) for p in sk["skeleton"]["junctions_xy"]}
    cycle_junctions = [p for p in cycle_vertices if p in junctions]
    if not cycle_junctions:
        raise RuntimeError("Principal raster cycle has no recorded attachment junction")
    # Leftmost cycle junction is the western/eastern course attachment.
    junction = min(cycle_junctions, key=lambda p: (p[0], p[1]))
    junction_i = index.get(tuple(map(int, junction)))
    if junction_i is None:
        # Skeleton coordinates are integer pixels; tolerate float serialization.
        junction_i = min(range(len(points)), key=lambda i: d(points[i], junction))

    arm_a = shortest_path(points, adj, west_endpoints[0], junction_i)
    arm_b = shortest_path(points, adj, west_endpoints[1], junction_i)
    cycle = rotate_cycle_to(cycle_vertices, junction)

    eps = args.epsilon_px
    arm_a_s = rdp(arm_a, eps)
    arm_b_s = rdp(arm_b, eps)
    cycle_s = rdp(cycle, eps)

    H = reg["trail14_to_trail5_homography"]
    frame = georef["map_frame_px"]
    sw = georef["sweref_controls"]["sw"]
    ne = georef["sweref_controls"]["ne"]
    tx, ty = t5qa.get("raster_translation_m", [0.0, 0.0])

    def trail14_to_trail5_pixel(p):
        x, y = p
        z = H[2][0] * x + H[2][1] * y + H[2][2]
        return (
            (H[0][0] * x + H[0][1] * y + H[0][2]) / z,
            (H[1][0] * x + H[1][1] * y + H[1][2]) / z,
        )

    def pixel_to_sweref(p):
        x, y = p
        E = sw[0] + (x - frame["left"]) / (frame["right"] - frame["left"]) * (ne[0] - sw[0]) + tx
        N = ne[1] - (y - frame["top"]) / (frame["bottom"] - frame["top"]) * (ne[1] - sw[1]) + ty
        return (E, N)

    def transform_line(line):
        return [pixel_to_sweref(trail14_to_trail5_pixel(p)) for p in line]

    arm_a_xy = transform_line(arm_a_s)
    arm_b_xy = transform_line(arm_b_s)
    cycle_xy = transform_line(cycle_s)

    # Compose start -> western arm -> eastern principal cycle -> second western
    # arm -> finish. Keep the attachment node once at each join.
    route_xy = arm_a_xy + cycle_xy[1:] + list(reversed(arm_b_xy))[1:]

    to_wgs84 = Transformer.from_crs(3006, 4326, always_xy=True)
    route_ll = [to_wgs84.transform(E, N) for E, N in route_xy]

    arm_a_m = polyline_length(arm_a_xy)
    arm_b_m = polyline_length(arm_b_xy)
    cycle_m = polyline_length(cycle_xy)
    total_m = polyline_length(route_xy)
    start_finish_gap_m = d(route_xy[0], route_xy[-1])

    mean_width_px = sk["source_component"]["area"] / sk["skeleton"]["total_edge_length_px"]
    participant_km = 13.67
    participant_delta_m = abs(total_m - participant_km * 1000.0)

    props = {
        "name": "ÖST Trail 13/14 km reconstructed organizer-raster reference",
        "status": "validated_reconstruction_candidate",
        "geometry_basis": "derived_from_georeferenced_organizer_map",
        "not_an_organizer_gpx": True,
        "distance_km": round(total_m / 1000.0, 3),
        "raster_simplification_epsilon_px": eps,
        "direction_status": "geometry_validated_direction_not_yet_promoted",
        "version_scope": "legacy/2023 course-family reference; exact 2026 14 km version not independently confirmed",
    }
    feature = {
        "type": "Feature",
        "properties": props,
        "geometry": {
            "type": "LineString",
            "coordinates": [[lon, lat] for lon, lat in route_ll],
        },
    }
    Path(args.geojson).write_text(json.dumps(feature, ensure_ascii=False, indent=2) + "\n")

    trkpts = "".join(
        f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon, lat in route_ll
    )
    Path(args.gpx).write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<gpx version="1.1" creator="Loppanalys raster reconstruction">'
        '<trk><name>ÖST Trail 13/14 km reconstructed organizer-raster reference</name>'
        f'<trkseg>{trkpts}</trkseg></trk></gpx>\n'
    )

    qa = {
        "distance_km": round(total_m / 1000.0, 3),
        "route_points": len(route_ll),
        "start_finish_gap_m": round(start_finish_gap_m, 1),
        "western_long_arm_km": round(arm_a_m / 1000.0, 3),
        "western_short_arm_km": round(arm_b_m / 1000.0, 3),
        "eastern_principal_cycle_km": round(cycle_m / 1000.0, 3),
        "principal_cycle_nodes": principal_cycle["node_count"],
        "principal_cycle_pixel_length": principal_cycle["pixel_length"],
        "raster_component_mean_width_px": round(mean_width_px, 3),
        "raster_simplification_epsilon_px": eps,
        "epsilon_to_mean_width_ratio": round(eps / mean_width_px, 3),
        "map_registration_median_px": reg["reprojection_px"]["median"],
        "map_registration_p95_px": reg["reprojection_px"]["p95"],
        "participant_2023_reference_km": participant_km,
        "participant_reference_used_as_geometry_input": False,
        "participant_distance_delta_m": round(participant_delta_m, 1),
        "topology": "two western start/finish arms attached to one principal eastern cycle",
        "geometry_status": "validated_reconstruction_2023_family_reference",
        "publishable_as_reconstructed_route": True,
        "publishable_as_organizer_gpx": False,
        "current_2026_exact_version_confirmed": False,
    }
    Path(args.qa).write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n")

    provenance = {
        "schema_version": "1.0",
        "race": "Österlen Spring Trail",
        "course": "Trail 13/14 km",
        "geometry_status": "validated_reconstruction_2023_family_reference",
        "primary_geometry_basis": "organizer georeferenced raster centreline",
        "not_an_organizer_gpx": True,
        "confidence": {
            "legacy_2023_course_family": "high",
            "exact_current_2026_14km_version": "medium_unconfirmed",
        },
        "sources": [
            {
                "type": "organizer_georeferenced_raster",
                "path": "data/source/maps/ost-trail13-14-organizer-map.jpg",
                "role": "primary route-choice and topology evidence",
            },
            {
                "type": "cross_map_registration",
                "path": "reports/organizer-map-registration.json",
                "role": "maps Trail 13/14 raster into the independently georeferenced Trail 5 raster frame",
            },
            {
                "type": "participant_distance_validation",
                "description": "2023 race-day watch observation 13.67 km / 1:31:44; independent validation only, not an input to route geometry",
            },
            {
                "type": "official_local_trail_topology",
                "description": "Hallamölla corridor evidence supports the eastern loop topology; not used to force raster geometry",
            },
        ],
        "method": {
            "principal_cycle": "largest connected raster-skeleton cycle",
            "western_arms": "two western raster endpoints connected to the leftmost principal-cycle junction",
            "simplification": "Ramer-Douglas-Peucker within organizer line-width scale",
            "epsilon_px": eps,
            "mean_route_component_width_px": round(mean_width_px, 3),
        },
        "limitations": [
            "No accessible organizer GPX has been found for this short-course version.",
            "The participant 2023 raw GPX remains inaccessible; its distance is validation evidence only.",
            "The current event is described as approximately 14 km while the organizer raster is labelled 13 km.",
            "Exact 2026 course-version equivalence must remain unconfirmed until a current organizer/participant GPS trace is obtained.",
            "Direction is not promoted here; geometry is suitable for map/course-shape analysis before directional segment semantics are finalized.",
        ],
        "qa_path": "qa.json",
        "qa_acceptance": "validated_reconstruction_candidate",
    }
    Path(args.provenance).write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")

    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
