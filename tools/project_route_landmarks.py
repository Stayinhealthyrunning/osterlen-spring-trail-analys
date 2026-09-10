#!/usr/bin/env python3
"""Project public route landmarks onto archived GPX geometry.

This creates a reusable bridge between named course landmarks (Trace de Trail POIs)
and distance along the locally archived route. It is intentionally geometric: source
names and source coordinates are preserved, while the projected course distance is a
derived value with an explicit off-route residual.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json, math, re, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'config/course-source-manifest.json').read_text(encoding='utf-8'))
WAYPOINTS=json.loads((ROOT/'data/source/tracedetrail/waypoints.json').read_text(encoding='utf-8'))
OUT=ROOT/'data/derived/route-landmark-projections.json'
OUT_MD=ROOT/'reports/route-landmark-projections.md'
R=6371008.8


def hav(a,b):
    lat1,lon1=map(math.radians,a); lat2,lon2=map(math.radians,b)
    dlat=lat2-lat1; dlon=lon2-lon1
    h=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))


def parse_gpx(path):
    root=ET.parse(path).getroot(); pts=[]
    for el in root.iter():
        if el.tag.rsplit('}',1)[-1].lower() in {'trkpt','rtept'}:
            pts.append((float(el.attrib['lat']),float(el.attrib['lon'])))
    if len(pts)<2: raise ValueError(f'{path}: too few route points')
    cum=[0.0]
    for a,b in zip(pts,pts[1:]): cum.append(cum[-1]+hav(a,b))
    return pts,cum


def project_point(point,pts,cum):
    lat0=math.radians(point[0]); c=math.cos(lat0)
    def xy(p): return (math.radians(p[1]-point[1])*R*c, math.radians(p[0]-point[0])*R)
    best=None
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        ax,ay=xy(a); bx,by=xy(b)
        vx,vy=bx-ax,by-ay
        denom=vx*vx+vy*vy
        t=0.0 if denom<=0 else max(0.0,min(1.0,-(ax*vx+ay*vy)/denom))
        x=ax+t*vx; y=ay+t*vy; d=math.hypot(x,y)
        if best is None or d<best[0]:
            seg_len=cum[i+1]-cum[i]
            best=(d,cum[i]+t*seg_len,i,t)
    return {'off_route_m':best[0],'distance_m':best[1],'segment_index':best[2],'segment_fraction':best[3]}


def semantic_key(title,types):
    s=(title or '').lower()
    if 'bengtem' in s: return 'bengtemolla'
    if 'vantal' in s: return 'vantalangan'
    if 'stenshuvud' in s: return 'stenshuvud'
    if re.search(r'\bstart\b|\bdepart\b',s) or any(str(t).lower()=='depart' for t in types or []): return 'start'
    if re.search(r'finish|mål|malgang|arriv',s) or any('arriv' in str(t).lower() for t in types or []): return 'finish'
    return None


def applies(value,year):
    return value==year or (isinstance(value,list) and year in value)


def waypoint_index():
    return {int(r['trace_id']):r for r in WAYPOINTS.get('routes',[])}


def main():
    wpidx=waypoint_index(); rows=[]; errors=[]
    local_sources=[s for s in MANIFEST.get('sources',[]) if s.get('target_path') and str(s['target_path']).lower().endswith('.gpx') and (ROOT/s['target_path']).exists()]
    for src in local_sources:
        years=src['year'] if isinstance(src.get('year'),list) else [src.get('year')]
        family=src.get('family'); path=ROOT/src['target_path']
        try: pts,cum=parse_gpx(path)
        except Exception as exc:
            errors.append({'path':src['target_path'],'error':f'{type(exc).__name__}: {exc}'}); continue
        for year in years:
            refs=[x for x in MANIFEST.get('sources',[]) if x.get('family')==family and applies(x.get('year'),year) and x.get('trace_id')]
            for ref in refs:
                route=wpidx.get(int(ref['trace_id']))
                if not route: continue
                for wp in route.get('waypoints',[]):
                    if wp.get('lat') is None or wp.get('lon') is None: continue
                    p=project_point((float(wp['lat']),float(wp['lon'])),pts,cum)
                    key=semantic_key(wp.get('title'),wp.get('types'))
                    rows.append({
                      'year':int(year),'family':family,'gpx_path':src['target_path'],
                      'trace_id':int(ref['trace_id']),'source_pi_id':wp.get('source_pi_id'),
                      'title':wp.get('title'),'types':wp.get('types',[]),'semantic_key':key,
                      'source_coord':[float(wp['lat']),float(wp['lon'])],
                      'projected_distance_km':round(p['distance_m']/1000,3),
                      'off_route_m':round(p['off_route_m'],1),
                      'projection_quality':('excellent' if p['off_route_m']<=25 else 'good' if p['off_route_m']<=75 else 'review' if p['off_route_m']<=200 else 'poor'),
                    })
    payload={
      'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),
      'method':'Nearest point on archived GPX polyline using local equirectangular segment projection; distance measured cumulatively along source GPX.',
      'warning':'Projected distance is derived geometry. Preserve the source waypoint identity/coordinate and inspect large off-route residuals before use.',
      'rows':rows,'errors':errors
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    lines=['# Route landmark projections','',payload['method'],'',
           '| År | Bana | Landmark | Källa | km på GPX | Avstånd från GPX | kvalitet |',
           '|---:|---|---|---:|---:|---:|---|']
    interesting=[r for r in rows if r.get('semantic_key') or any(str(t).lower() in {'ravitoc','ravitaillement','basevie','bh'} for t in r.get('types',[]))]
    for r in interesting:
        label=r.get('semantic_key') or r.get('title') or r.get('source_pi_id')
        lines.append(f"| {r['year']} | `{r['family']}` | {label} | {r['trace_id']} | {r['projected_distance_km']:.3f} | {r['off_route_m']:.1f} m | {r['projection_quality']} |")
    if not interesting: lines.append('| — | — | — | — | — | — | — |')
    lines += ['','Alla POI-projektioner, även de som inte visas i tabellen, finns i JSON-filen.','']
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Projected {len(rows)} route waypoints; errors={len(errors)}')

if __name__=='__main__': main()
