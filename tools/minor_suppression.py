#!/usr/bin/env python3
"""Race-result minors: cautious, auditable, pre-publication identity masking.

Only a credible numeric age <18 (or an explicit age band whose upper edge <18)
can trigger automatic masking. Other rows are not automatically classified.
This is pseudonymisation; source-identical results may remain linkable.
"""
from __future__ import annotations
import hashlib
import re

MASKED = "Anonym löpare"
DIRECT_IDENTITY_FIELDS = ("bib", "club", "country", "person_key",
                          "age", "age_category", "class_name", "class_place",
                          "identity_status", "identity_scope")

def confirmed_minor(row):
    age = row.get("age")
    if type(age) is int and 0 <= age < 18:
        return True
    if age is not None:
        return False
    for key in ("age_category", "class_name"):
        value = str(row.get(key) or "").strip()
        # Only an explicit, bounded age interval; e.g. 0-11, (F) 16-17, F0-11 or M16-17.
        match = re.fullmatch(r"(?:\([A-Za-z]\)\s*|[A-Za-z]\s*)?(\d{1,2})\s*[-–]\s*(\d{1,2})(?:\s+(?:män|kvinnor))?", value, re.I)
        if match and int(match.group(1)) <= int(match.group(2)) < 18:
            return True
    return False

def redact_race_bundle(race_key, race, splits, team_members):
    removed_ids = set()
    count = 0
    kept_records = []
    for row in race.get("records", []):
        if not confirmed_minor(row):
            kept_records.append(row)
            continue
        original_id = row.get("source_result_id")
        if original_id is not None:
            removed_ids.add(str(original_id))
        count += 1
    race["records"] = kept_records

    def references_removed(row):
        return any(
            str(row.get(key)) in removed_ids
            for key in ("source_result_id", "result_id", "member_result_id", "source_member_result_id")
            if row.get(key) is not None
        )

    def remove_refs(items, *, member_rows=False):
        kept = []
        for row in items:
            if not isinstance(row, dict):
                kept.append(row)
                continue
            if references_removed(row):
                continue
            kept.append(row)
        items[:] = kept

    remove_refs(splits)
    remove_refs(team_members, member_rows=True)
    return count
