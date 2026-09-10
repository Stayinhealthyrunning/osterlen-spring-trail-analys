#!/usr/bin/env python3
"""Discover historical organizer-hosted GPX/PDF assets via Internet Archive CDX.

The script stores only archive metadata/URLs. It does not automatically redistribute
archived file bodies. This gives us a reproducible lead list for missing historical routes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import json, urllib.request, urllib.error

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/wayback-organizer-assets.json'
BASE='https://web.archive.org/cdx/search/cdx'
PATTERNS=[
    'www.osterlentrail.se/uploads/4/1/8/7/41870619/*.gpx',
    'osterlentrail.se/uploads/4/1/8/7/41870619/*.gpx',
    'www.osterlentrail.se/uploads/4/1/8/7/41870619/*.pdf',
    'osterlentrail.se/uploads/4/1/8/7/41870619/*.pdf',
]

def query(pattern):
    params={
      'url':pattern,'output':'json','fl':'timestamp,original,mimetype,statuscode,digest,length',
      'filter':'statuscode:200','collapse':'digest','from':'2017','to':'2026','limit':'5000'
    }
    req=urllib.request.Request(BASE+'?'+urlencode(params),headers={'User-Agent':'OST-analysis-research/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            payload=json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'pattern':pattern,'error':f'{type(e).__name__}: {e}','captures':[]}
    if not payload: return {'pattern':pattern,'captures':[]}
    header=payload[0]; rows=[dict(zip(header,row)) for row in payload[1:]]
    for row in rows:
        row['archive_url']=f"https://web.archive.org/web/{row['timestamp']}id_/{row['original']}"
    return {'pattern':pattern,'captures':rows}

def main():
    queries=[query(p) for p in PATTERNS]
    unique={}
    for q in queries:
        for r in q.get('captures',[]):
            key=(r.get('original'),r.get('digest'))
            old=unique.get(key)
            if old is None or r.get('timestamp','')>old.get('timestamp',''):
                unique[key]=r
    rows=sorted(unique.values(),key=lambda x:(x.get('original',''),x.get('timestamp','')))
    report={
      'generated_at':datetime.now(timezone.utc).isoformat(),
      'scope':'historical organizer-hosted GPX/PDF discovery; metadata only',
      'queries':queries,
      'unique_assets':rows,
      'gpx_assets':[r for r in rows if '.gpx' in r.get('original','').lower()],
      'pdf_assets':[r for r in rows if '.pdf' in r.get('original','').lower()],
      'policy':'Archive captures are leads. Validate provenance/content before adding any historical body to the repository.'
    }
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"unique={len(rows)} gpx={len(report['gpx_assets'])} pdf={len(report['pdf_assets'])}")
    for r in report['gpx_assets']:
        print(r.get('timestamp'),r.get('original'))

if __name__=='__main__': main()
