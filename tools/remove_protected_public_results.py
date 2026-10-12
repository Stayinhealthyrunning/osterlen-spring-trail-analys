#!/usr/bin/env python3
"""Remove protected people and their linked observations from ÖST browser data."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from privacy import DISPLAY_NAME, load_rules, normalize_name, record_is_suppressed

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/data"
RULES = ROOT / "config/privacy-suppressions.json"


def compact(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def write(path: Path, payload: object) -> dict[str, int | str]:
    raw = compact(payload)
    path.write_bytes(raw)
    return {
        "raw_bytes": len(raw),
        "gzip_bytes": len(gzip.compress(raw, compresslevel=9, mtime=0)),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> None:
    rules = load_rules(RULES, require_private=True)
    manifest_path = DATA / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    removed_total = 0
    removed_member_total = 0
    affected = 0
    totals = {"race_instances": 0, "records": 0, "splits": 0, "teams": 0, "team_members": 0}
    for path in sorted((DATA / "races").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        race_key = payload["race_key"]
        removed_refs = set()
        kept = []
        for row in payload["race"].get("records", []):
            blocked = normalize_name(row.get("name")) == normalize_name(DISPLAY_NAME)
            blocked = blocked or record_is_suppressed(row, rules, scope=race_key)
            if blocked:
                for key in ("source_result_id", "result_id", "bib"):
                    if row.get(key) not in (None, ""):
                        removed_refs.add(str(row[key]))
                removed_total += 1
            else:
                kept.append(row)
        payload["race"]["records"] = kept

        def linked(row: dict) -> bool:
            return any(
                str(row.get(key)) in removed_refs
                for key in ("source_result_id", "result_id", "member_result_id", "source_member_result_id")
                if row.get(key) not in (None, "")
            )

        payload["splits"] = [row for row in payload.get("splits", []) if not linked(row)]
        members = []
        for row in payload.get("team_members", []):
            name = row.get("name") or row.get("name_as_published") or row.get("member_name_as_published")
            blocked = normalize_name(name) == normalize_name(DISPLAY_NAME)
            blocked = blocked or linked(row) or record_is_suppressed(row, rules, scope=race_key)
            if blocked:
                removed_member_total += 1
            else:
                members.append(row)
        payload["team_members"] = members
        meta = write(path, payload)
        old_entry = manifest["races"][race_key]
        new_entry = {
            **old_entry,
            **meta,
            "records": len(payload["race"].get("records", [])),
            "splits": len(payload.get("splits", [])),
            "teams": len(payload.get("teams", [])),
            "team_members": len(payload.get("team_members", [])),
        }
        manifest["races"][race_key] = new_entry
        totals["race_instances"] += 1
        for key in ("records", "splits", "teams", "team_members"):
            totals[key] += new_entry[key]
        if new_entry["records"] != old_entry["records"] or new_entry["team_members"] != old_entry["team_members"]:
            affected += 1
    manifest["totals"] = totals
    write(manifest_path, manifest)
    print(json.dumps({
        "status": "PASS",
        "removed_results": removed_total,
        "removed_team_members": removed_member_total,
        "affected_races": affected,
    }))


if __name__ == "__main__":
    main()
