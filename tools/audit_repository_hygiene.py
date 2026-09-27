#!/usr/bin/env python3
"""Cheap repository-hygiene guard.

This is not a source-data validator. It prevents transient build/test junk and
obviously non-runtime raw database/source files from leaking into the tracked
working tree or future GitHub Pages surface.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

TRANSIENT_PREFIXES=(
    "out/","node_modules/","__pycache__/",".pytest_cache/",".ruff_cache/",
    ".mypy_cache/","dist/"
)
TRANSIENT_PARTS=("/__pycache__/","/.pytest_cache/","/.ruff_cache/","/.mypy_cache/")
FORBIDDEN_DOC_SUFFIXES=(".sqlite",".sqlite.gz",".db",".db.gz",".osm")
MAX_DOC_FILE_BYTES=8*1024*1024


def tracked_files():
    run=subprocess.run(
        ["git","ls-files","-z"],cwd=ROOT,check=True,capture_output=True
    )
    return [p.decode("utf-8") for p in run.stdout.split(b"\0") if p]


def main():
    errors=[]
    tracked=tracked_files()

    for rel in tracked:
        normalized=rel.replace("\\","/")
        if normalized.startswith(TRANSIENT_PREFIXES) or any(x in "/"+normalized for x in TRANSIENT_PARTS):
            errors.append(f"transient artifact is tracked: {rel}")
        if normalized.endswith((".pyc",".pyo")):
            errors.append(f"compiled Python artifact is tracked: {rel}")
        if normalized.startswith("docs/"):
            lower=normalized.lower()
            if lower.endswith(FORBIDDEN_DOC_SUFFIXES):
                errors.append(f"raw source/database file leaked into frontend surface: {rel}")
            p=ROOT/rel
            if p.exists() and p.stat().st_size>MAX_DOC_FILE_BYTES:
                errors.append(f"frontend file exceeds 8 MiB review threshold: {rel}")

    if errors:
        print("Repository hygiene FAILED")
        for e in errors:
            print(" -",e)
        return 1

    total=sum((ROOT/p).stat().st_size for p in tracked if (ROOT/p).is_file())
    docs=[p for p in tracked if p.startswith("docs/") and (ROOT/p).is_file()]
    docs_bytes=sum((ROOT/p).stat().st_size for p in docs)
    print(f"Repository hygiene OK: {len(tracked)} tracked files, {total:,} bytes; docs={len(docs)} files/{docs_bytes:,} bytes")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
