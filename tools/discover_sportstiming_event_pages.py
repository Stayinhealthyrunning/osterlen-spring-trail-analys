#!/usr/bin/env python3
"""Extract non-participant metadata and discover public links from ÖST Sportstiming event pages.

This is deliberately conservative: it reads ordinary public event/participant/result pages,
does not bypass challenge pages and stores no participant rows. The output is intended to
reveal event metadata, form/link patterns and candidate download/API routes that can later
be used by an official-data importer.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EVENTS_FILE = ROOT / "data/source/sportstiming/events.json"
OUT = ROOT / "reports/sportstiming-event-discovery.json"

UA = "OST-analysis-research/1.0 (+https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)"

KEYWORDS = (
    "api", "result", "participant", "download", "export", "startlist", "start-list",
    "race", "class", "tracking", "track", "replay", "split", "intermediate", "mellemtid",
    "ajax", "json", "csv", "xml"
)

class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.scripts = []
        self.forms = []
        self._form = None
        self.text_parts = []
        self.attrs = []
        self.title_parts = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        self.attrs.append({"tag": tag, **{k:v for k,v in d.items() if v and any(x in k.lower() for x in ("href","src","action","url","endpoint","download","event","race","class"))}})
        if tag == "a" and d.get("href"):
            self.links.append(d["href"])
        if tag == "script" and d.get("src"):
            self.scripts.append(d["src"])
        if tag == "form":
            self._form = {"action": d.get("action"), "method": (d.get("method") or "GET").upper()}
            self.forms.append(self._form)
        if tag == "title": self._in_title = True

    def handle_endtag(self, tag):
        if tag == "form": self._form = None
        if tag == "title": self._in_title = False

    def handle_data(self, data):
        t = re.sub(r"\s+", " ", data).strip()
        if t:
            self.text_parts.append(t)
            if self._in_title: self.title_parts.append(t)


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept":"text/html,application/json,text/plain;q=0.9,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(3_000_000)
            status = r.status
            final_url = r.geturl()
            content_type = r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        body = e.read(3_000_000)
        status = e.code
        final_url = getattr(e, "url", url)
        content_type = e.headers.get("Content-Type", "") if e.headers else ""
    except Exception as exc:
        return {"url":url,"error":f"{type(exc).__name__}: {exc}"}

    text = body.decode("utf-8", errors="replace")
    lower = text.lower()
    challenge = any(x in lower for x in ("verify you're human", "verify you&#39;re human", "challenges.cloudflare.com/turnstile"))
    result = {
        "url": url,
        "final_url": final_url,
        "status": status,
        "content_type": content_type,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "challenge": challenge,
    }
    if "html" not in content_type.lower() and "<html" not in lower:
        return result

    p = Collector(); p.feed(text)
    result["title"] = " ".join(p.title_parts)[:300]
    base = final_url
    links = sorted({urljoin(base, x) for x in p.links if x and not x.startswith(("javascript:","mailto:","tel:"))})
    result["event_links"] = [x for x in links if f"/event/" in x][:250]
    result["candidate_links"] = [x for x in links if any(k in x.lower() for k in KEYWORDS)][:250]
    result["scripts"] = sorted({urljoin(base, x) for x in p.scripts})[:100]
    result["forms"] = [
        {"action": urljoin(base, f["action"] or final_url), "method": f["method"]}
        for f in p.forms
    ][:100]

    # Store only short metadata snippets, never participant tables/rows.
    metadata_terms = ("österlen", "osterlen", "ultra", "fogarolli", "duo", "ekopark", "naturloppet", "60 km", "22 km", "21 km", "14 km", "13 km", "5 km", "startar kl", "april")
    snippets = []
    parts = p.text_parts
    for i, part in enumerate(parts):
        pl = part.lower()
        if any(term in pl for term in metadata_terms):
            context = " | ".join(parts[max(0,i-2):min(len(parts),i+3)])
            if len(context) <= 600 and context not in snippets:
                snippets.append(context)
        if len(snippets) >= 80: break
    result["metadata_snippets"] = snippets

    # Candidate literal routes embedded in inline HTML/JS; keep only endpoint-looking strings.
    literals = set(re.findall(r'["\']((?:https?://[^"\']+|/[^"\']{2,180}))["\']', text))
    result["candidate_literals"] = sorted(
        x for x in literals if any(k in x.lower() for k in KEYWORDS)
    )[:250]
    return result


def main():
    registry = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "Public metadata discovery only; no challenge bypass and no participant-row persistence.",
        "events": []
    }
    for event in registry["events"]:
        event_id = int(event["event_id"])
        parsed = urlparse(event["url"])
        base = f"{parsed.scheme}://{parsed.netloc}"
        pages = []
        for path in [
            f"/event/{event_id}",
            f"/event/{event_id}/participants",
            f"/event/{event_id}/results",
        ]:
            pages.append(fetch(base + path))
        output["events"].append({"year":event["year"],"event_id":event_id,"pages":pages})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    for e in output["events"]:
        print(e["year"], [(p.get("status"), p.get("challenge"), len(p.get("candidate_links",[]))) for p in e["pages"]])

if __name__ == "__main__":
    main()
