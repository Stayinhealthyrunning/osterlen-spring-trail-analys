#!/usr/bin/env python3
"""Validate the measured ÖST browser-delivery data budgets."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUDGET=ROOT/"config/performance-budget.json"
EXPORTER=ROOT/"tools/export_engine_delivery.py"


def main():
    budget=json.loads(BUDGET.read_text(encoding="utf-8"))
    b=budget["data_budgets"]
    errors=[]

    with tempfile.TemporaryDirectory(prefix="ost-performance-budget-") as td:
        out=Path(td)/"delivery"
        run=subprocess.run(
            [sys.executable,str(EXPORTER),"--output-dir",str(out)],
            cwd=ROOT,text=True,capture_output=True
        )
        if run.returncode:
            raise SystemExit(run.stderr or run.stdout)
        manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))

    bootstrap=manifest["bootstrap"]
    largest=manifest["largest_race_bundle"]
    combined=manifest["bootstrap_plus_largest_gzip_bytes"]
    full=manifest["source_payload"]

    checks=[
        ("bootstrap raw",bootstrap["raw_bytes"],b["bootstrap_max_raw_bytes"]),
        ("bootstrap gzip",bootstrap["gzip_bytes"],b["bootstrap_max_gzip_bytes"]),
        ("largest selected race raw",largest["raw_bytes"],b["selected_race_max_raw_bytes"]),
        ("largest selected race gzip",largest["gzip_bytes"],b["selected_race_max_gzip_bytes"]),
        ("bootstrap + largest selected race gzip",combined,b["bootstrap_plus_selected_race_max_gzip_bytes"]),
        ("full Engine payload gzip sanity",full["gzip_bytes"],b["full_engine_payload_sanity_max_gzip_bytes"]),
    ]
    for name,value,limit in checks:
        if value>limit:
            errors.append(f"{name}: {value:,} > budget {limit:,}")

    if manifest["counts"]!={"race_instances":34,"records":9871,"splits":6123,"teams":300,"team_members":599}:
        errors.append(f"delivery counts drifted: {manifest['counts']}")

    if errors:
        print("Performance budget FAILED")
        for e in errors:
            print(" -",e)
        return 1

    print("Performance budget OK")
    print(json.dumps({
        "bootstrap_gzip_bytes":bootstrap["gzip_bytes"],
        "largest_race_key":largest["race_key"],
        "largest_race_gzip_bytes":largest["gzip_bytes"],
        "bootstrap_plus_largest_gzip_bytes":combined,
        "full_engine_payload_gzip_bytes":full["gzip_bytes"],
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
