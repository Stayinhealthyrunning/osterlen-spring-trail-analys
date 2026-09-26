#!/usr/bin/env python3
"""Rank pre-generated race-route candidates against normalized constraints.

The matcher is source-neutral. Upstream adapters may derive candidates from
OSM, another vector network, or manually curated alternatives.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT_WEIGHTS = {
    "raster_fit": 0.30,
    "control_fit": 0.22,
    "distance_fit": 0.14,
    "gps_fit": 0.18,
    "terrain_fit": 0.08,
    "topology_fit": 0.05,
    "year_fit": 0.03,
}

def rank(candidate: dict, weights: dict[str, float]) -> dict:
    checks = candidate.get("checks", {})
    total_weight = 0.0
    total = 0.0
    missing = []
    for name, weight in weights.items():
        value = checks.get(name)
        if value is None:
            missing.append(name)
            continue
        value = min(1.0, max(0.0, float(value)))
        total += value * weight
        total_weight += weight
    score = total / total_weight if total_weight else 0.0

    # Hard contradictions should not be washed out by several good soft checks.
    contradictions = candidate.get("hard_contradictions", [])
    eligible = not contradictions
    if contradictions:
        score *= 0.25

    out = dict(candidate)
    out["candidate_score"] = round(score, 4)
    out["eligible"] = eligible
    out["missing_checks"] = missing
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_json", type=Path)
    ap.add_argument("output_json", type=Path)
    args = ap.parse_args()

    doc = json.loads(args.input_json.read_text(encoding="utf-8"))
    weights = dict(DEFAULT_WEIGHTS)
    weights.update(doc.get("weights", {}))
    candidates = [rank(c, weights) for c in doc.get("candidates", [])]
    candidates.sort(key=lambda c: (c["eligible"], c["candidate_score"]), reverse=True)
    doc["weights_used"] = weights
    doc["candidates"] = candidates
    doc["best_candidate_id"] = next((c.get("candidate_id") for c in candidates if c["eligible"]), None)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
