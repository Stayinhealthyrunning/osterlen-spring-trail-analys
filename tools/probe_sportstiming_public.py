#!/usr/bin/env python3
"""Conservatively probe Sportstiming's public surface without bypassing access controls.

The goal is endpoint discovery and reproducibility, not bulk extraction. The probe:
- uses ordinary unauthenticated HTTPS GET requests;
- never attempts CAPTCHA/challenge bypass;
- records only response metadata and structural JSON summaries;
- does not persist participant-level response bodies.

A historical public GitHub note mentions `sportstiming.dk/api/v1.1`; this script
checks a small candidate set around that namespace plus the ordinary public event
URLs for one known ÖST event.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "sportstiming-public-probe.json"
EVENT_ID = 16880
BASES = ["https://www.sportstiming.dk", "https://www.sportstiming.se"]

PATHS = [
    "/",
    "/robots.txt",
    f"/event/{EVENT_ID}",
    f"/event/{EVENT_ID}/results",
    "/api/v1.1",
    "/api/v1.1/",
    f"/api/v1.1/event/{EVENT_ID}",
    f"/api/v1.1/events/{EVENT_ID}",
    f"/api/v1.1/event/{EVENT_ID}/races",
    f"/api/v1.1/events/{EVENT_ID}/races",
    f"/api/v1.1/results?event={EVENT_ID}",
    f"/api/v1.1/results?eventid={EVENT_ID}",
    f"/api/v1.1/participants?event={EVENT_ID}",
    f"/api/v1.1/participants?eventid={EVENT_ID}",
]

HEADERS = {
    "User-Agent": "OST-analysis-research/1.0 (+https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)",
    "Accept": "application/json,text/html,text/plain;q=0.9,*/*;q=0.5",
}


def structural_summary(body: bytes, content_type: str) -> dict:
    text = body.decode("utf-8", errors="replace")
    lower = text.lower()
    summary: dict = {
        "bytes": len(body),
        "human_verification_marker": any(
            marker in lower
            for marker in ["verify you're human", "confirm you're human", "javascript is required"]
        ),
    }
    if "json" in content_type.lower() or text.lstrip().startswith(("{", "[")):
        try:
            obj = json.loads(text)
            summary["json_type"] = type(obj).__name__
            if isinstance(obj, dict):
                summary["json_keys"] = sorted(str(k) for k in obj.keys())[:100]
            elif isinstance(obj, list):
                summary["json_length"] = len(obj)
                if obj and isinstance(obj[0], dict):
                    summary["first_item_keys"] = sorted(str(k) for k in obj[0].keys())[:100]
            return summary
        except Exception as exc:
            summary["json_parse_error"] = type(exc).__name__
    if "html" in content_type.lower() or "<html" in lower:
        scripts = sorted(set(re.findall(r'<script[^>]+src=["\']([^"\']+)', text, flags=re.I)))
        links = sorted(set(re.findall(r'<link[^>]+href=["\']([^"\']+)', text, flags=re.I)))
        summary["script_src"] = scripts[:50]
        summary["link_href"] = links[:50]
        title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
        if title_match:
            summary["title"] = re.sub(r"\s+", " ", title_match.group(1)).strip()[:200]
    return summary


def probe(url: str) -> dict:
    request = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(2_000_000)
            ctype = response.headers.get("Content-Type", "")
            return {
                "url": url,
                "status": response.status,
                "content_type": ctype,
                "final_url": response.geturl(),
                "headers": {
                    k: response.headers.get(k)
                    for k in ["Server", "Content-Length", "Location", "Cache-Control", "Allow"]
                    if response.headers.get(k) is not None
                },
                "summary": structural_summary(body, ctype),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read(2_000_000)
        ctype = exc.headers.get("Content-Type", "") if exc.headers else ""
        return {
            "url": url,
            "status": exc.code,
            "content_type": ctype,
            "final_url": getattr(exc, "url", url),
            "headers": {
                k: exc.headers.get(k)
                for k in ["Server", "Content-Length", "Location", "Cache-Control", "Allow"]
                if exc.headers and exc.headers.get(k) is not None
            },
            "summary": structural_summary(body, ctype),
        }
    except Exception as exc:
        return {"url": url, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    results = []
    for base in BASES:
        for path in PATHS:
            results.append(probe(urljoin(base, path)))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "unauthenticated_public_surface_only",
        "event_id": EVENT_ID,
        "policy": "No challenge/CAPTCHA bypass; no participant-level body persistence.",
        "hint_source": "https://github.com/kasperlaessoe/Lynx2TCP/blob/86aaba8bdf5169516596c4f686cf4b97f003fd37/Notes.Md",
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(results)} probes")
    for item in results:
        print(item.get("status", "ERR"), item["url"], item.get("summary", {}).get("json_keys", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
