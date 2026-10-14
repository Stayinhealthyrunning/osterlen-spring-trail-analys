#!/usr/bin/env python3
"""Restore verified ÖST SQLite sources from an authenticated private checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATIONS = {
    "source-archive/ost-results-2018-2026.sqlite.gz":
        ROOT / "data/archive/ost-results-2018-2026.sqlite.gz",
    "source-archive/ost-analysis-2018-2026.sqlite.gz":
        ROOT / "data/derived/ost-analysis-2018-2026.sqlite.gz",
}


def digest(path: Path) -> tuple[int, str]:
    checksum = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size += len(chunk)
            checksum.update(chunk)
    return size, checksum.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", required=True, type=Path)
    args = parser.parse_args()
    project = args.private_root.resolve() / "ost"
    manifest_path = project / "SOURCE_MANIFEST.json"
    if not manifest_path.is_file():
        raise SystemExit("Private ÖST source manifest is unavailable")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != 2:
        raise SystemExit("Private ÖST source manifest is invalid")

    restored = 0
    for entry in files:
        relative = entry.get("path")
        target = DESTINATIONS.get(relative)
        if target is None:
            raise SystemExit("Private manifest contains an unapproved ÖST path")
        source = project / relative
        if not source.is_file() or digest(source) != (entry["bytes"], entry["sha256"]):
            raise SystemExit("A private ÖST source failed integrity verification")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if digest(target) != (entry["bytes"], entry["sha256"]):
            raise SystemExit("A restored ÖST source failed verification")
        restored += 1
    print(f"Private ÖST sources restored and verified: {restored}")


if __name__ == "__main__":
    main()
