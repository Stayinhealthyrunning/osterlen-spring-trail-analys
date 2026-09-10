#!/usr/bin/env python3
"""Fetch route-only GPX files from Trace de Trail's normal public download control.

The public trace page exposes a GPX button. Its client code submits a POST to
`download/getFile/<platform>` with `format=gpx`, `trace=1`, and optional feature
flags. This tool intentionally requests the route only (`pi=0`) and does not
attempt to access subscriber-only POI/export features or bypass access controls.

Every stored file is validated as GPX and accompanied by provenance metadata.
"""
from __future__ import annotations

from pathlib import Path
from http.cookiejar import CookieJar
import argparse, hashlib, json, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / 'data/source/tracedetrail/tracks.json'
UA = 'Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'
BASE = 'https://tracedetrail.fr/'


def opener():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def get(op, url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,*/*;q=0.8'})
    with op.open(req, timeout=45) as r:
        return r.read(), r.geturl(), dict(r.headers.items())


def platform_candidates(page_text: str):
    found = []
    patterns = [
        r'\bplatform\s*[:=]\s*["\']([A-Za-z0-9_-]+)["\']',
        r'\bcartoPlatform\s*[:=]\s*["\']([A-Za-z0-9_-]+)["\']',
        r'["\']platform["\']\s*:\s*["\']([A-Za-z0-9_-]+)["\']',
    ]
    for pat in patterns:
        for value in re.findall(pat, page_text, re.I):
            if value not in found:
                found.append(value)
    for value in ('fr', 'en', 'web', 'trace'):
        if value not in found:
            found.append(value)
    return found


def valid_gpx(raw: bytes):
    head = raw[:5000].lower()
    if b'<gpx' not in head:
        return False, None
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return False, None
    if root.tag.split('}')[-1].lower() != 'gpx':
        return False, None
    counts = {'trkpt': 0, 'rtept': 0, 'wpt': 0, 'ele': 0}
    for el in root.iter():
        name = el.tag.split('}')[-1]
        if name in counts:
            counts[name] += 1
    return (counts['trkpt'] + counts['rtept'] > 1), counts


def preview(raw: bytes):
    return ' '.join(raw[:500].decode('utf-8','replace').split())[:350]


def post_download(op, platform: str, trace_id: int):
    endpoint = urllib.parse.urljoin(BASE, f'download/getFile/{platform}')
    fields = {
        'traceID': str(trace_id),
        'format': 'gpx',
        'trace': '1',
        'pi': '0',
        'waytypes': '0',
        'devneg': '0',
        'devpos': '0',
        'distance': '0',
        'dir': '0',
        'download': '1',
    }
    body = urllib.parse.urlencode(fields).encode('ascii')
    req = urllib.request.Request(endpoint, data=body, headers={
        'User-Agent': UA,
        'Accept': 'application/gpx+xml,application/xml,text/xml,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f'https://tracedetrail.fr/fr/trace/{trace_id}',
        'Origin': 'https://tracedetrail.fr',
        'X-Requested-With': 'XMLHttpRequest',
    })
    with op.open(req, timeout=60) as r:
        return r.read(12_000_000), r.geturl(), dict(r.headers.items()), endpoint


def fetch_one(item, output_dir: Path):
    tid = int(item['trace_id'])
    op = opener()
    page_url = f'https://tracedetrail.fr/fr/trace/{tid}'
    page_raw, page_final, _ = get(op, page_url)
    page = page_raw.decode('utf-8', 'replace')
    candidates=platform_candidates(page)
    attempts = []
    for platform in candidates:
        try:
            raw, final, headers, endpoint = post_download(op, platform, tid)
            ok, counts = valid_gpx(raw)
            attempts.append({
                'platform': platform,
                'endpoint': endpoint,
                'http_final_url': final,
                'bytes': len(raw),
                'content_type': headers.get('Content-Type'),
                'content_disposition': headers.get('Content-Disposition'),
                'valid_gpx': ok,
                'response_preview': None if ok else preview(raw),
            })
            if not ok:
                continue
            filename = f"{item['family']}-{item['year']}-trace-{tid}.gpx"
            path = output_dir / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            return {
                'family': item['family'], 'year': item['year'], 'trace_id': tid,
                'source_page': page_final, 'download_endpoint': endpoint,
                'platform_candidates': candidates,
                'platform': platform, 'file': str(path.relative_to(ROOT)),
                'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'point_counts': counts, 'attempts': attempts,
            }
        except Exception as exc:
            attempts.append({'platform': platform, 'error': f'{type(exc).__name__}: {exc}'})
    return {
        'family': item['family'], 'year': item['year'], 'trace_id': tid,
        'source_page': page_final, 'platform_candidates':candidates,
        'error': 'No candidate public download POST returned a valid GPX',
        'attempts': attempts,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--trace-id', type=int)
    ap.add_argument('--output-dir', default='data/source/tracedetrail/gpx')
    ap.add_argument('--manifest', default='data/source/tracedetrail/gpx-download-manifest.json')
    args = ap.parse_args()
    catalog = json.loads(TRACKS.read_text(encoding='utf-8'))['tracks']
    if args.trace_id:
        selected = [x for x in catalog if int(x['trace_id']) == args.trace_id]
        if not selected:
            raise SystemExit(f'Trace {args.trace_id} not present in tracks.json')
    elif args.all:
        selected = catalog
    else:
        raise SystemExit('Use --all or --trace-id N')

    outdir = ROOT / args.output_dir
    results = []
    for i, item in enumerate(selected, 1):
        print(f"[{i}/{len(selected)}] {item['family']} {item['year']} trace {item['trace_id']}", flush=True)
        result = fetch_one(item, outdir)
        results.append(result)
        if result.get('error'):
            print('  ERROR:', result['error'])
            print('  platform candidates:', result.get('platform_candidates'))
            for a in result.get('attempts', []): print('   ', a)
        else:
            print(f"  OK: {result['file']} {result['bytes']} bytes {result['point_counts']}")
        time.sleep(0.15)

    payload = {
        'schema_version': 2,
        'method': 'Normal public Trace de Trail route-only GPX download control; pi=0; no subscriber-only feature requested.',
        'results': results,
    }
    manifest = ROOT / args.manifest
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    errors = sum(1 for x in results if x.get('error'))
    print(f'Completed: {len(results)-errors}/{len(results)} valid GPX downloads; errors={errors}')
    raise SystemExit(1 if errors else 0)

if __name__ == '__main__':
    main()
