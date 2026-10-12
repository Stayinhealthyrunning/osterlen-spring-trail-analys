#!/usr/bin/env python3
"""Fail publication when records with proven age <18 still expose identity."""
import json
import sys
from pathlib import Path
from minor_suppression import confirmed_minor

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/"docs/data"
count=0
races=list((root/"races").glob("*.json"))
if not races: raise SystemExit("No race data to audit")
for path in races:
    doc=json.loads(path.read_text(encoding="utf-8"))
    for row in doc["race"]["records"]:
        if confirmed_minor(row):
            raise SystemExit(f"Unprotected under-18 record: {path.name}")
        if row.get("name")=="Anonym löpare":
            raise SystemExit(f"Pseudonymous individual row remains: {path.name}")
print(json.dumps({"files":len(races),"masked_identity_rows":count,"status":"PASS"}))
