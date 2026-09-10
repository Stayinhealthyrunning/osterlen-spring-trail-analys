#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json, math, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GPX_ROOT = ROOT / "data" / "source" / "gpx"
REPORT_JSON = ROOT / "reports" / "gpx-source-analysis.json"
REPORT_MD = ROOT / "reports" / "gpx-source-analysis.md"

EARTH_M = 6371008.8

def haversine(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2-lat1, lon2-lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * EARTH_M * math.asin(min(1, math.sqrt(h)))

def parse_gpx(path):
    root = ET.parse(path).getroot()
    pts=[]
    for e in root.iter():
        if e.tag.rsplit('}',1)[-1] in {'trkpt','rtept'}:
            lat=float(e.attrib['lat']); lon=float(e.attrib['lon'])
            ele=None
            for child in e:
                if child.tag.rsplit('}',1)[-1]=='ele':
                    try: ele=float(child.text)
                    except Exception: pass
                    break
            pts.append((lat,lon,ele))
    if len(pts)<2: raise ValueError(f"Too few points in {path}")
    dist=sum(haversine((pts[i-1][0],pts[i-1][1]),(pts[i][0],pts[i][1])) for i in range(1,len(pts)))
    gain=loss=0.0
    elev=[p[2] for p in pts if p[2] is not None]
    if len(elev)==len(pts):
        for i in range(1,len(pts)):
            d=pts[i][2]-pts[i-1][2]
            if d>0: gain+=d
            elif d<0: loss-=d
    return {"points":pts,"distance_km":dist/1000,"raw_ascent_m":gain if elev else None,"raw_descent_m":loss if elev else None,
            "start":[pts[0][0],pts[0][1]],"finish":[pts[-1][0],pts[-1][1]],"min_ele_m":min(elev) if elev else None,"max_ele_m":max(elev) if elev else None}

def resample(points, n=600):
    coords=[(p[0],p[1]) for p in points]
    cum=[0.0]
    for i in range(1,len(coords)): cum.append(cum[-1]+haversine(coords[i-1],coords[i]))
    total=cum[-1]
    out=[]; j=1
    for k in range(n+1):
        t=total*k/n
        while j<len(cum)-1 and cum[j]<t: j+=1
        a=max(0,j-1); b=j
        span=cum[b]-cum[a]
        q=0 if span<=0 else (t-cum[a])/span
        out.append((coords[a][0]+(coords[b][0]-coords[a][0])*q, coords[a][1]+(coords[b][1]-coords[a][1])*q))
    return out

def compare(a,b):
    ra,rb=resample(a['points']),resample(b['points'])
    sep=[haversine(x,y) for x,y in zip(ra,rb)]
    return {"start_separation_m":haversine(a['start'],b['start']),"finish_separation_m":haversine(a['finish'],b['finish']),
            "mean_progress_separation_m":sum(sep)/len(sep),"median_progress_separation_m":sorted(sep)[len(sep)//2],
            "p95_progress_separation_m":sorted(sep)[int(.95*(len(sep)-1))],"max_progress_separation_m":max(sep),
            "distance_difference_km":b['distance_km']-a['distance_km'],
            "warning":"Progress-aligned separation is diagnostic only; it is not a final shared-corridor percentage."}

def main():
    files=sorted(GPX_ROOT.rglob('*.gpx'))
    records=[]; parsed={}
    for p in files:
        info=parse_gpx(p); parsed[str(p.relative_to(ROOT))]=info
        records.append({"path":str(p.relative_to(ROOT)),"point_count":len(info['points']),"distance_km":round(info['distance_km'],3),
                        "raw_ascent_m":round(info['raw_ascent_m'],1) if info['raw_ascent_m'] is not None else None,
                        "raw_descent_m":round(info['raw_descent_m'],1) if info['raw_descent_m'] is not None else None,
                        "start":info['start'],"finish":info['finish'],"min_ele_m":info['min_ele_m'],"max_ele_m":info['max_ele_m']})
    comparisons=[]
    keys=list(parsed)
    for i in range(len(keys)):
        for j in range(i+1,len(keys)):
            if Path(keys[i]).parent==Path(keys[j]).parent:
                c=compare(parsed[keys[i]],parsed[keys[j]])
                comparisons.append({"a":keys[i],"b":keys[j],**{k:(round(v,2) if isinstance(v,float) else v) for k,v in c.items()}})
    payload={"method":"Haversine track length from source GPX; raw elevation differences are unsmoothed and are not authoritative D+.","files":records,"same_family_comparisons":comparisons}
    REPORT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# GPX source analysis','',payload['method'],'','## Files','', '| File | Points | Calculated km | Raw D+ | Raw D- |','|---|---:|---:|---:|---:|']
    for r in records: lines.append(f"| `{r['path']}` | {r['point_count']} | {r['distance_km']:.3f} | {r['raw_ascent_m'] or '–'} | {r['raw_descent_m'] or '–'} |")
    lines += ['','## Same-family diagnostics','']
    for c in comparisons:
        lines += [f"### `{c['a']}` vs `{c['b']}`",'',f"- Distance difference: {c['distance_difference_km']:+.2f} km",f"- Start separation: {c['start_separation_m']:.0f} m",f"- Finish separation: {c['finish_separation_m']:.0f} m",f"- Median progress-aligned separation: {c['median_progress_separation_m']:.0f} m",f"- 95th percentile separation: {c['p95_progress_separation_m']:.0f} m",f"- Maximum separation: {c['max_progress_separation_m']:.0f} m",'', '> This is a diagnostic, not yet a course-version decision.','']
    REPORT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
