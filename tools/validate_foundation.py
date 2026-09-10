#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_JSON = [
    "config/event.json",
    "config/race-families.json",
    "config/race-editions.json",
    "config/race-catalog.json",
    "config/course-versions.json",
    "config/checkpoint-normalization.json",
    "config/analysis-data-contract.json",
    "config/analysis-feature-policy.json",
    "config/engine-adapter.json",
    "data/source/sportstiming/events.json",
    "data/source/sportstiming/class-catalog.json",
    "data/source/sportstiming/split-inventory.json",
    "data/source/sportstiming/points-tracking-inventory.json",
]

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "PREP_STATUS.md",
    "PREP_MANIFEST.json",
    "research/gotaleden-engine-handoff.md",
    "research/current-data-coverage.md",
    "reports/source-coverage.md",
    "reports/tracedetrail-public-geometry-analysis.md",
]


def load_json(rel: str) -> Any:
    path = ROOT / rel
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_FILES + REQUIRED_JSON:
        if not (ROOT / rel).exists():
            errors.append(f"Missing required file: {rel}")

    payloads: dict[str, Any] = {}
    for rel in REQUIRED_JSON:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            payloads[rel] = load_json(rel)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Invalid JSON in {rel}: {exc}")

    if errors:
        return finish(errors, warnings)

    event = payloads["config/event.json"]
    families = payloads["config/race-families.json"]
    editions = payloads["config/race-editions.json"]
    sport_events = payloads["data/source/sportstiming/events.json"]
    course_versions = payloads["config/course-versions.json"]
    split_inventory = payloads["data/source/sportstiming/split-inventory.json"]

    held = {int(v) for v in event.get("held_years", [])}
    cancelled = {int(v) for v in event.get("cancelled_years", [])}
    event_families = set(event.get("race_families", []))

    if held & cancelled:
        errors.append(f"Years cannot be both held and cancelled: {sorted(held & cancelled)}")
    if event_families != set(families):
        errors.append("config/event.json race_families differs from config/race-families.json keys")

    for family, meta in families.items():
        years = {int(v) for v in meta.get("years", [])}
        if not years <= held:
            errors.append(f"{family}: family years outside held_years: {sorted(years - held)}")
        first = meta.get("first_year_in_scope")
        if years and first is not None and int(first) != min(years):
            errors.append(f"{family}: first_year_in_scope does not equal first listed year")

    edition_by_year = {int(row["year"]): row for row in editions.get("editions", [])}
    expected_edition_years = held | cancelled
    if set(edition_by_year) != expected_edition_years:
        errors.append(
            "race-editions year set differs from event held+cancelled years: "
            f"expected {sorted(expected_edition_years)}, got {sorted(edition_by_year)}"
        )

    sport_event_by_year = {int(row["year"]): row for row in sport_events.get("events", [])}
    if set(sport_event_by_year) != held:
        errors.append("Sportstiming event inventory must contain exactly the held analysis years")

    for year in sorted(held):
        edition = edition_by_year.get(year, {})
        source = sport_event_by_year.get(year, {})
        if edition.get("status") == "cancelled":
            errors.append(f"{year}: held year marked cancelled in race-editions")
        if edition.get("sportstiming_event_id") != source.get("event_id"):
            errors.append(f"{year}: Sportstiming event ID mismatch between race-editions and events.json")
        expected = {name for name, meta in families.items() if year in {int(v) for v in meta.get("years", [])}}
        actual = set((edition.get("races") or {}).keys())
        if expected != actual:
            errors.append(f"{year}: race families mismatch. expected {sorted(expected)}, got {sorted(actual)}")

    for year in sorted(cancelled):
        edition = edition_by_year.get(year, {})
        if edition.get("status") != "cancelled":
            errors.append(f"{year}: cancelled year must have status=cancelled")
        if edition.get("races"):
            errors.append(f"{year}: cancelled year must not contain race rows")

    versions = {row["course_version_id"]: row for row in course_versions.get("versions", [])}
    assignments = course_versions.get("assignments", [])
    assignment_key: dict[tuple[int, str], dict[str, Any]] = {}
    for row in assignments:
        key = (int(row["year"]), row["family"])
        if key in assignment_key:
            errors.append(f"Duplicate course assignment: {key}")
        assignment_key[key] = row
        version = row.get("course_version_id")
        if version and version not in versions:
            errors.append(f"{key}: unknown course_version_id {version}")

    for year in sorted(held):
        if (year, "ultra60") not in assignment_key:
            errors.append(f"{year}: missing Ultra 60 course assignment")
        if (year, "trail22") not in assignment_key:
            errors.append(f"{year}: missing Trail 21/22 course assignment or explicit pending row")

    for year in sorted(families["duo60"]["years"]):
        duo = assignment_key.get((year, "duo60"))
        ultra = assignment_key.get((year, "ultra60"))
        if not duo or not ultra:
            errors.append(f"{year}: Duo/Ultra course assignment pair missing")
        elif duo.get("course_version_id") != ultra.get("course_version_id"):
            errors.append(f"{year}: Duo must inherit the same course_version_id as Ultra 60")

    for version_id, version in versions.items():
        if version.get("route_asset_status") == "archived_organizer_gpx":
            source_path = version.get("primary_source_path")
            if not source_path:
                errors.append(f"{version_id}: archived organizer GPX lacks primary_source_path")
            elif not (ROOT / source_path).exists():
                errors.append(f"{version_id}: referenced organizer GPX missing: {source_path}")

    split_rows = split_inventory.get("inventory", [])
    split_keys = {(int(row["year"]), row["race_family"]) for row in split_rows}
    for year in sorted(held):
        for family, meta in families.items():
            if year in {int(v) for v in meta.get("years", [])} and (year, family) not in split_keys:
                errors.append(f"{year} {family}: missing Sportstiming split-schema inventory row")

    for year in sorted(held):
        row = next((r for r in split_rows if int(r["year"]) == year and r["race_family"] == "ultra60"), None)
        if row and not row.get("has_split_table"):
            warnings.append(f"{year} ultra60: split table not observed in current sample")

    unresolved = course_versions.get("unresolved", [])
    if not unresolved:
        warnings.append("course-versions.json has no unresolved list; verify that this is intentional")

    return finish(errors, warnings)


def finish(errors: list[str], warnings: list[str]) -> int:
    if warnings:
        print("Foundation warnings:")
        for item in warnings:
            print(f"  - {item}")
    if errors:
        print("Foundation validation FAILED:")
        for item in errors:
            print(f"  - {item}")
        return 1
    print("Foundation validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
