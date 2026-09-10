#!/usr/bin/env python3
"""Fetch organizer-hosted source assets declared in project manifests.

Only downloads sources hosted on www.osterlentrail.se and explicitly marked
as organizer_direct_download. Third-party Trace de Trail GPX is intentionally
not downloaded by this tool.
"""

from __future__ import annotations
from pathlib import Path
import hashlib
import json
import os
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COURSE_MANIFEST = ROOT / "config" / "course-source-manifest.json"
MAP_MANIFEST = ROOT / "data" / "source" / "maps" / "manifest.json"
ALLOWED_HOST = "www.osterlentrail.se"

def iter_sources():
    course = json.loads(COURSE_MANIFEST.read_text(encoding="utf-8"))
    maps = json.loads(MAP_MANIFEST.read_text(encoding="utf-8"))
    for source in course["sources"] + maps["sources"]:
        if source.get("redistribution") == "organizer_direct_download" or source.get("source_type") == "organizer_pdf":
            if source.get("target_path"):
                yield source

def validate_gpx(data: bytes):
    root = ET.fromstring(data)
    local = root.tag.rsplit("}", 1)[-1].lower()
    if local != "gpx":
        raise ValueError(f"Expected GPX root element, got {root.tag!r}")
    points = [el for el in root.iter() if el.tag.rsplit("}", 1)[-1].lower() in {"trkpt", "rtept"}]
    if not points:
        raise ValueError("GPX contains no track/route points")

def validate_pdf(data: bytes):
    if not data.startswith(b"%PDF"):
        raise ValueError("Downloaded file is not a PDF")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def download(source):
    url = source["url"]
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname != ALLOWED_HOST:
        raise ValueError(f"Blocked non-organizer host: {parsed.hostname}")
    req = urllib.request.Request(url, headers={"User-Agent": "OST-analysis-source-archiver/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        data = response.read()
    target = ROOT / source["target_path"]
    suffix = target.suffix.lower()
    if suffix == ".gpx":
        validate_gpx(data)
    elif suffix == ".pdf":
        validate_pdf(data)
    else:
        raise ValueError(f"Unsupported target suffix: {suffix}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, target)
    digest = sha256(data)
    target.with_suffix(target.suffix + ".sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    return target, len(data), digest

def main():
    failures = 0
    for source in iter_sources():
        try:
            target, size, digest = download(source)
            print(f"OK  {target.relative_to(ROOT)}  {size} bytes  sha256={digest}")
        except Exception as exc:
            failures += 1
            print(f"ERR {source.get('url')}: {exc}", file=sys.stderr)
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
