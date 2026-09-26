#!/usr/bin/env python3
"""Validate minimum provenance fields before reconstructed route export."""
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED_ROUTE = {"race_id", "course_version_id", "status", "segments"}
REQUIRED_SEGMENT = {"segment_id", "provenance", "evidence_ids", "decision_reason"}

def validate(doc: dict) -> list[str]:
    errors = []
    for key in sorted(REQUIRED_ROUTE - set(doc)):
        errors.append(f"missing route field: {key}")
    for i, segment in enumerate(doc.get("segments", [])):
        for key in sorted(REQUIRED_SEGMENT - set(segment)):
            errors.append(f"segment {i}: missing {key}")
        if segment.get("provenance") == "unresolved_gap" and segment.get("geometry") is not None:
            errors.append(f"segment {i}: unresolved_gap must not masquerade as resolved geometry")
        if segment.get("status") == "canonical" and not segment.get("evidence_ids"):
            errors.append(f"segment {i}: canonical segment lacks evidence")
    if doc.get("status") == "organizer_gpx" and doc.get("reconstructed", False):
        errors.append("reconstructed route cannot be labelled organizer_gpx")
    return errors

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("route_json",type=Path)
    args=ap.parse_args()
    doc=json.loads(args.route_json.read_text(encoding="utf-8"))
    errors=validate(doc)
    print(json.dumps({"valid":not errors,"errors":errors},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=="__main__":
    raise SystemExit(main())
