#!/usr/bin/env python3
"""Resolve only well-separated route alternatives; preserve the rest."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def resolve(record: dict, margin: float) -> dict:
    alternatives = [a for a in record.get("alternatives", []) if not a.get("contradictions")]
    alternatives.sort(key=lambda a: float(a.get("candidate_score", 0.0)), reverse=True)
    out = dict(record)
    if not alternatives:
        out["resolution_status"] = "unresolved"
        out["selected_alternative_id"] = None
        return out
    if len(alternatives) == 1:
        out["resolution_status"] = "resolved"
        out["selected_alternative_id"] = alternatives[0].get("alternative_id")
        return out
    gap = float(alternatives[0].get("candidate_score", 0.0)) - float(alternatives[1].get("candidate_score", 0.0))
    out["score_margin"] = round(gap, 4)
    if gap >= margin:
        out["resolution_status"] = "resolved"
        out["selected_alternative_id"] = alternatives[0].get("alternative_id")
    else:
        out["resolution_status"] = "preferred_but_unresolved"
        out["selected_alternative_id"] = None
        out["preferred_alternative_id"] = alternatives[0].get("alternative_id")
    return out

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("input_json",type=Path)
    ap.add_argument("output_json",type=Path)
    ap.add_argument("--margin",type=float,default=0.15)
    args=ap.parse_args()
    doc=json.loads(args.input_json.read_text(encoding="utf-8"))
    doc["ambiguities"]=[resolve(x,args.margin) for x in doc.get("ambiguities",[])]
    args.output_json.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
