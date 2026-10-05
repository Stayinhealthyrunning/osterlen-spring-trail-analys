#!/usr/bin/env python3
"""Sanitize public ÖST SQLite archives according to the suppression registry.

This keeps race observations and aggregate/statistical usefulness, while masking
direct identity fields in the public GitHub archives. It deliberately does not
claim irreversible anonymisation of exact race performances.
"""
from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from privacy import load_rules, is_suppressed_name, record_is_suppressed

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "config" / "privacy-suppressions.json"
DEFAULT_ARCHIVES = (
    ROOT / "data" / "archive" / "ost-results-2018-2026.sqlite.gz",
    ROOT / "data" / "derived" / "ost-analysis-2018-2026.sqlite.gz",
)
FULL_KEYS = {
    "name", "name_as_published", "canonical_name", "member_name_as_published",
    "runner_name_as_published", "published_name", "navnformatert", "namn",
}
FIRST_KEYS = {"first_name", "firstname", "fornavn", "förnamn"}
LAST_KEYS = {"last_name", "surname", "etternavn", "efternamn"}
DIRECT_KEYS = {
    "bib", "startnummer", "startnr", "club", "klubb", "klubbnavn",
    "listed_contact_name", "source_member_result_id", "public_contestant_uid",
    "source_url",
}
JSON_NAME_MARKERS = ("json", "snapshot", "payload", "raw", "source")


def _key(value: Any) -> str:
    return str(value or "").strip().casefold().replace(" ", "_")


def sanitize_tree(value: Any, rules: dict[str, Any]) -> tuple[Any, int]:
    changes = 0
    if isinstance(value, list):
        out = []
        for item in value:
            clean, count = sanitize_tree(item, rules)
            out.append(clean); changes += count
        return out, changes
    if not isinstance(value, dict):
        if isinstance(value, str) and is_suppressed_name(value, rules):
            return rules["display_name"], 1
        return value, 0

    out = {}
    for key, item in value.items():
        clean, count = sanitize_tree(item, rules)
        out[key] = clean; changes += count

    normalized = {_key(k): k for k in out}
    candidates = []
    for nk, original in normalized.items():
        if nk in FULL_KEYS and out.get(original) not in (None, ""):
            candidates.append(str(out[original]))
    first_values = [out[normalized[k]] for k in FIRST_KEYS if k in normalized and out.get(normalized[k]) not in (None, "")]
    last_values = [out[normalized[k]] for k in LAST_KEYS if k in normalized and out.get(normalized[k]) not in (None, "")]
    for first in first_values:
        for last in last_values:
            candidates.extend((f"{first} {last}", f"{last} {first}"))

    if any(is_suppressed_name(candidate, rules) for candidate in candidates):
        for nk, original in normalized.items():
            if nk in FULL_KEYS:
                out[original] = rules["display_name"]; changes += 1
            elif nk in FIRST_KEYS or nk in LAST_KEYS or nk in DIRECT_KEYS:
                if out.get(original) not in (None, ""):
                    changes += 1
                out[original] = None
    return out, changes


def _table_names(con: sqlite3.Connection) -> list[str]:
    return [row[0] for row in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]


def _columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in con.execute(f'PRAGMA table_info("{table}")')]


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sanitize_database(db: Path, rules: dict[str, Any]) -> dict[str, int]:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    counts = {"matched_rows": 0, "identity_fields": 0, "json_values": 0}
    display = rules["display_name"]
    try:
        for table in _table_names(con):
            columns = _columns(con, table)
            if not columns:
                continue
            rows = list(con.execute(f'SELECT rowid AS __rowid__, * FROM {_quote(table)}'))
            for row in rows:
                record = dict(row)
                top_match = record_is_suppressed(record, rules)
                updates: dict[str, Any] = {}
                if top_match:
                    counts["matched_rows"] += 1
                    for col in columns:
                        nk = _key(col)
                        if nk in FULL_KEYS:
                            updates[col] = display
                        elif nk in FIRST_KEYS or nk in LAST_KEYS or nk in DIRECT_KEYS:
                            updates[col] = None
                    counts["identity_fields"] += len(updates)

                for col in columns:
                    raw = row[col]
                    if not isinstance(raw, str) or not raw:
                        continue
                    nk = _key(col)
                    if not any(marker in nk for marker in JSON_NAME_MARKERS):
                        continue
                    stripped = raw.lstrip()
                    if not stripped.startswith(("{", "[")):
                        continue
                    try:
                        parsed = json.loads(raw)
                    except (ValueError, TypeError):
                        continue
                    clean, changed = sanitize_tree(parsed, rules)
                    if changed:
                        updates[col] = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
                        counts["json_values"] += changed

                if updates:
                    set_sql = ", ".join(f"{_quote(k)}=?" for k in updates)
                    con.execute(
                        f'UPDATE {_quote(table)} SET {set_sql} WHERE rowid=?',
                        [*updates.values(), row["__rowid__"]],
                    )
        con.commit()
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"{db}: integrity_check={integrity}")
    finally:
        con.close()
    return counts


def sanitize_archive(path: Path, rules: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)), "status": "missing"}
    with tempfile.TemporaryDirectory(prefix="ost-privacy-") as td:
        db = Path(td) / "archive.sqlite"
        with gzip.open(path, "rb") as src, db.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        before = db.stat().st_size
        counts = sanitize_database(db, rules)
        temp_gz = Path(td) / "archive.sqlite.gz"
        with db.open("rb") as src, temp_gz.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as dst:
                shutil.copyfileobj(src, dst)
        shutil.copy2(temp_gz, path)
        return {
            "path": str(path.relative_to(ROOT)),
            "status": "sanitized",
            "sqlite_bytes": before,
            **counts,
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archives", nargs="*", type=Path)
    ap.add_argument("--report", default=str(ROOT / "reports" / "privacy-suppression-audit.json"))
    args = ap.parse_args()
    rules = load_rules(RULES)
    archives = [p if p.is_absolute() else ROOT / p for p in (args.archives or DEFAULT_ARCHIVES)]
    report = {
        "schema_version": 1,
        "display_name": rules["display_name"],
        "suppression_rule_count": len(rules["_fingerprints"]),
        "archives": [sanitize_archive(path, rules) for path in archives],
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
