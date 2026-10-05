#!/usr/bin/env python3
"""Fail if a blocked identity is still present in distributed ÖST JSON."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
from privacy import load_rules, name_fingerprint, normalize_name

ROOT=Path(__file__).resolve().parents[1]
RULES=ROOT/"config"/"privacy-suppressions.json"

def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values(): yield from strings(child)
    elif isinstance(value, list):
        for child in value: yield from strings(child)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=str(ROOT/"docs"/"data"));args=ap.parse_args()
    base=Path(args.root);rules=load_rules(RULES);blocked=rules["_fingerprints"];display=normalize_name(rules["display_name"])
    files=list(base.rglob("*.json")) if base.exists() else []
    anonymous=0
    for path in files:
        doc=json.loads(path.read_text(encoding="utf-8"))
        for text in strings(doc):
            norm=normalize_name(text)
            if norm and norm!=display and name_fingerprint(norm) in blocked:
                raise SystemExit(f"Blocked identity fingerprint remains in {path}")
        for item in walk(doc):
            if normalize_name(item.get("name") or item.get("name_as_published"))==display:
                anonymous+=1
                if item.get("bib") not in (None,"") or item.get("club") not in (None,""):
                    raise SystemExit(f"Direct identifier remains on anonymous record in {path}")
    if not files:
        raise SystemExit(f"No JSON files found under {base}")
    print(json.dumps({"files":len(files),"anonymous_records":anonymous,"status":"PASS"}))

if __name__=="__main__":
    main()
