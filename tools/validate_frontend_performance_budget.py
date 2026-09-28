#!/usr/bin/env python3
"""Validate the measured ÖST browser-delivery performance budget."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUDGET=ROOT/"config/frontend-performance-budget.json"
EXPORTER=ROOT/"tools/build_frontend.py"


def main():
    budget=json.loads(BUDGET.read_text(encoding="utf-8"))
    limits=budget["data_delivery"]
    errors=[]

    with tempfile.TemporaryDirectory(prefix="ost-web-budget-") as td:
        run=subprocess.run(
            [sys.executable,str(EXPORTER),"--output-dir",td],
            cwd=ROOT,text=True,capture_output=True
        )
        if run.returncode:
            raise SystemExit(run.stderr or run.stdout)
        summary=json.loads(run.stdout)
        manifest=json.loads((Path(td)/"manifest.json").read_text(encoding="utf-8"))

        expected={"race_instances":34,"records":9871,"splits":6123,"teams":300,"team_members":599}
        if manifest.get("totals")!=expected:
            errors.append(f"delivery accounting changed: {manifest.get('totals')} != {expected}")

        bootstrap=manifest["bootstrap"]
        races=list(manifest["races"].values())
        largest_gz=max(r["gzip_bytes"] for r in races)
        largest_raw=max(r["raw_bytes"] for r in races)
        combined=bootstrap["gzip_bytes"]+largest_gz

        if bootstrap["gzip_bytes"]>limits["bootstrap_gzip_max_bytes"]:
            errors.append(f"bootstrap gzip {bootstrap['gzip_bytes']} > {limits['bootstrap_gzip_max_bytes']}")
        if largest_gz>limits["selected_race_gzip_max_bytes"]:
            errors.append(f"largest race gzip {largest_gz} > {limits['selected_race_gzip_max_bytes']}")
        if largest_raw>limits["selected_race_raw_max_bytes"]:
            errors.append(f"largest race raw {largest_raw} > {limits['selected_race_raw_max_bytes']}")
        if combined>limits["bootstrap_plus_selected_race_gzip_max_bytes"]:
            errors.append(f"bootstrap + largest race gzip {combined} > {limits['bootstrap_plus_selected_race_gzip_max_bytes']}")
        if summary["full_engine_gzip_bytes"]>limits["full_engine_gzip_regression_max_bytes"]:
            errors.append(f"full Engine gzip {summary['full_engine_gzip_bytes']} > {limits['full_engine_gzip_regression_max_bytes']}")

        payload_sha=manifest.get("payload_sha256")
        if not payload_sha:
            errors.append("payload SHA-256 missing from web manifest")
        for race_key,race in manifest["races"].items():
            doc=json.loads((Path(td)/race["path"]).read_text(encoding="utf-8"))
            if doc.get("payload_sha256")!=payload_sha:
                errors.append(f"{race_key}: payload identity mismatch")
            if doc.get("race_key")!=race_key:
                errors.append(f"{race_key}: race_key mismatch")

    from frontend_asset_budget import measure, violations
    assets=measure()
    errors.extend(violations(assets,combined))

    if errors:
        print("Frontend data performance budget FAILED")
        for e in errors: print(" -",e)
        return 1

    print(json.dumps({
        "status":"ok",
        "payload_sha256":payload_sha,
        "totals":expected,
        "full_engine_gzip_bytes":summary["full_engine_gzip_bytes"],
        "bootstrap_gzip_bytes":bootstrap["gzip_bytes"],
        "largest_selected_race_gzip_bytes":largest_gz,
        "largest_selected_race_raw_bytes":largest_raw,
        "bootstrap_plus_largest_gzip_bytes":combined,
        "budget":limits,
        "frontend_assets":assets,
    },ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
