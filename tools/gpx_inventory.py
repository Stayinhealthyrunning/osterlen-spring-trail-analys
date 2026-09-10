#!/usr/bin/env python3
"""Validate every archived GPX and report reproducible geometric metadata."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GPX_ROOT = ROOT / "data/source/gpx"
OUT_JSON = ROOT / "reports/gpx-inventory.json"
OUT_MD = ROOT / "reports/gpx-inventory.md"
R = 6371008.8

def hav(a,b):
    lat1,lon1=map(math.radians,a); lat2,lon2=map(math.radians,b)
    dlat=lat2-lat1; dlon=lon2-lon1
    h=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))

def parse(path):
    raw=path.read_bytes(); root=ET.fromstring(raw)
    pts=[]
    for el in root.iter():
        if el.tag.rsplit('}',1)[-1].lower() not in {'trkpt','rtept'}: continue
        lat=float(el.attrib['lat']); lon=float(el.attrib['lon']); ele=None
        for c in el:
            if c.tag.rsplit('}',1)[-1].lower()=='ele':
                try: ele=float(c.text)
                except Exception: pass
                break
        pts.append((lat,lon,ele))
    if len(pts)<2: raise ValueError('fewer than two route points')
    distances=[0.0]
    for a,b in zip(pts,pts[1:]): distances.append(distances[-1]+hav(a[:2],b[:2]))
    elev=[p[2] for p in pts if p[2] is not None]
    raw_up=raw_down=0.0
    for a,b in zip(pts,pts[1:]):
        if a[2] is None or b[2] is None: continue
        d=b[2]-a[2]
        if d>0: raw_up+=d
        elif d<0: raw_down-=d
    return {
        'path':str(path.relative_to(ROOT)).replace('\\','/'),
        'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
        'points':len(pts),'computed_distance_km':round(distances[-1]/1000,4),
        'start':{'lat':pts[0][0],'lon':pts[0][1]},
        'finish':{'lat':pts[-1][0],'lon':pts[-1][1]},
        'elevation_points':len(elev),
        'raw_gpx_ascent_m':round(raw_up,1) if elev else None,
        'raw_gpx_descent_m':round(raw_down,1) if elev else None,
        'elevation_warning':'Raw GPX ascent/descent is diagnostic only; not harmonized elevation for public cross-year comparison.' if elev else None,
    }

def main():
    rows=[]; errors=[]
    for p in sorted(GPX_ROOT.rglob('*.gpx')):
        try: rows.append(parse(p))
        except Exception as e: errors.append({'path':str(p.relative_to(ROOT)),'error':f'{type(e).__name__}: {e}'})
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'gpx_count':len(rows),'error_count':len(errors),'files':rows,'errors':errors}
    OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# GPX inventory','',f'Validated GPX files: **{len(rows)}**. Errors: **{len(errors)}**.','',
           '| File | Points | Computed km | Elevation pts | SHA-256 |','|---|---:|---:|---:|---|']
    for r in rows:
        lines.append(f"| `{r['path']}` | {r['points']} | {r['computed_distance_km']:.4f} | {r['elevation_points']} | `{r['sha256'][:16]}…` |")
    if errors:
        lines += ['','## Errors','']+[f"- `{e['path']}`: {e['error']}" for e in errors]
    lines += ['','Raw GPX elevation sums are diagnostic only. Cross-year elevation comparisons require one harmonized elevation method.','']
    OUT_MD.write_text('\n'.join(lines),encoding='utf-8')
    print(f'GPX={len(rows)} errors={len(errors)}')
    if errors: raise SystemExit(1)

if __name__=='__main__': main()
