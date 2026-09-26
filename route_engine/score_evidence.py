#!/usr/bin/env python3
"""Score curated evidence for reconstructed race-route segments."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

WEIGHTS = {
    "organizer_gpx": 1.00,
    "organizer_vector_route": 0.98,
    "participant_gps_consensus": 0.95,
    "participant_gps_single": 0.82,
    "organizer_georeferenced_raster": 0.78,
    "official_local_trail": 0.66,
    "open_map_snapped": 0.62,
    "heatmap_corroborated": 0.46,
    "text_constraint": 0.38,
    "satellite_corroborated": 0.32,
    "manual_hypothesis": 0.12,
    "unresolved_gap": 0.0,
}

def level(score: float) -> str:
    if score >= 0.90:
        return "canonical"
    if score >= 0.75:
        return "high"
    if score >= 0.50:
        return "medium"
    return "low"

def score_segment(segment: dict) -> dict:
    groups = {}
    for ev in segment.get("evidence", []):
        group = ev.get("independence_group") or ev.get("source_id")
        weight = float(ev.get("weight", WEIGHTS.get(ev.get("provenance"), 0.0)))
        weight = min(1.0, max(0.0, weight))
        groups[group] = max(groups.get(group, 0.0), weight)

    miss = 1.0
    for weight in groups.values():
        miss *= 1.0 - weight
    score = 1.0 - miss if groups else 0.0

    for penalty in segment.get("penalties", {}).values():
        penalty = min(1.0, max(0.0, float(penalty)))
        score *= 1.0 - penalty

    score = round(min(1.0, max(0.0, score)), 4)
    result = dict(segment)
    result["confidence_score"] = score
    result["confidence"] = level(score)
    return result

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_json", type=Path)
    ap.add_argument("output_json", type=Path)
    args = ap.parse_args()

    doc = json.loads(args.input_json.read_text(encoding="utf-8"))
    doc["segments"] = [score_segment(s) for s in doc.get("segments", [])]
    scores = [s["confidence_score"] for s in doc["segments"]]
    doc["route_confidence_floor"] = min(scores) if scores else 0.0
    doc["route_confidence_mean"] = round(sum(scores) / len(scores), 4) if scores else 0.0
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
