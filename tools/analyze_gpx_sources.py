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

def resample_by_step(points, step_m=50.0):
    coords=[(p[0],p[1]) for p in points]
    cum=[0.0]
    for i in range(1,len(coords)): cum.append(cum[-1]+haversine(coords[i-1],coords[i]))
    total=cum[-1]
    targets=[]
    x=0.0
    while x<total:
        targets.append(x); x+=step_m
    if not targets or targets[-1] != total: targets.append(total)
    out=[]; j=1
    for t in targets:
        while j<len(cum)-1 and cum[j]<t: j+=1
        a=max(0,j-1); b=j
        span=cum[b]-cum[a]
        q=0 if span<=0 else (t-cum[a])/span
        out.append((t,coords[a][0]+(coords[b][0]-coords[a][0])*q,coords[a][1]+(coords[b][1]-coords[a][1])*q))
    return out

def local_xy(samples, lat0):
    c=math.cos(math.radians(lat0))
    return [(d, math.radians(lon)*EARTH_M*c, math.radians(lat)*EARTH_M) for d,lat,lon in samples]

def nearest_distances(a_samples,b_samples):
    lat0=sum([x[1] for x in a_samples]+[x[1] for x in b_samples])/(len(a_samples)+len(b_samples))
    ax=local_xy(a_samples,lat0); bx=local_xy(b_samples,lat0)
    out=[]
    for d,x,y in ax:
        best=min((x-x2)**2+(y-y2)**2 for _,x2,y2 in bx)
        out.append((d,math.sqrt(best)))
    return out

def pct(values, q):
    if not values: return None
    vals=sorted(values); idx=min(len(vals)-1,max(0,int(round((len(vals)-1)*q))))
    return vals[idx]

def divergence_intervals(nearest, threshold_m=100.0, min_length_m=300.0):
    intervals=[]; start=None; last=None; vals=[]
    for d,sep in nearest:
        if sep>threshold_m:
            if start is None: start=d; vals=[]
            last=d; vals.append(sep)
        elif start is not None:
            if last-start>=min_length_m:
                intervals.append({'start_km':round(start/1000,2),'end_km':round(last/1000,2),'length_km':round((last-start)/1000,2),'median_separation_m':round(pct(vals,.5),1),'max_separation_m':round(max(vals),1)})
            start=last=None; vals=[]
    if start is not None and last is not None and last-start>=min_length_m:
        intervals.append({'start_km':round(start/1000,2),'end_km':round(last/1000,2),'length_km':round((last-start)/1000,2),'median_separation_m':round(pct(vals,.5),1),'max_separation_m':round(max(vals),1)})
    return intervals

def corridor_stats(a_near,b_near):
    a=[x[1] for x in a_near]; b=[x[1] for x in b_near]
    thresholds=(25,50,100,250)
    shared={}
    for t in thresholds:
        fa=sum(v<=t for v in a)/len(a); fb=sum(v<=t for v in b)/len(b)
        shared[str(t)]={'a_fraction':round(fa,4),'b_fraction':round(fb,4),'symmetric_min_fraction':round(min(fa,fb),4),'symmetric_mean_fraction':round((fa+fb)/2,4)}
    return {
      'nearest_separation_a_to_b_m':{'median':round(pct(a,.5),2),'p95':round(pct(a,.95),2),'max':round(max(a),2)},
      'nearest_separation_b_to_a_m':{'median':round(pct(b,.5),2),'p95':round(pct(b,.95),2),'max':round(max(b),2)},
      'shared_corridor_fraction_by_threshold_m':shared,
    }

def classify(stats,distance_diff_km,start_sep,finish_sep):
    s50=stats['shared_corridor_fraction_by_threshold_m']['50']['symmetric_min_fraction']
    s100=stats['shared_corridor_fraction_by_threshold_m']['100']['symmetric_min_fraction']
    if s50>=.98 and abs(distance_diff_km)<=.5 and start_sep<=100 and finish_sep<=100:
        return 'same_course_geometry_strong'
    if s100>=.95:
        return 'largely_same_corridor_with_changes'
    if s100>=.70:
        return 'substantial_shared_corridor_but_material_changes'
    return 'materially_different_geometry'

def compare(a,b):
    # 50 m route samples make the comparison insensitive to source point density.
    ra=resample_by_step(a['points'],50.0); rb=resample_by_step(b['points'],50.0)
    ab=nearest_distances(ra,rb); ba=nearest_distances(rb,ra)
    stats=corridor_stats(ab,ba)
    start_sep=haversine(a['start'],b['start']); finish_sep=haversine(a['finish'],b['finish'])
    dd=b['distance_km']-a['distance_km']
    return {
      "start_separation_m":start_sep,"finish_separation_m":finish_sep,
      "distance_difference_km":dd,
      **stats,
      "a_divergence_intervals_over_100m":divergence_intervals(ab,100,300),
      "b_divergence_intervals_over_100m":divergence_intervals(ba,100,300),
      "geometry_classification":classify(stats,dd,start_sep,finish_sep),
      "method_note":"Each route is resampled every 50 m. Shared-corridor fractions use nearest sampled route distance in both directions; they are robust diagnostics, not a legal/official statement of course identity."
    }

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
                def rounded(v): return round(v,2) if isinstance(v,float) else v
                comparisons.append({"a":keys[i],"b":keys[j],**{k:rounded(v) for k,v in c.items()}})
    payload={
      "method":"Haversine track length from source GPX. Route equivalence diagnostics use 50 m resampling and symmetric nearest-route corridor coverage. Raw elevation differences are unsmoothed and are not authoritative D+.",
      "files":records,"same_family_comparisons":comparisons
    }
    REPORT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# GPX source analysis','',payload['method'],'','## Files','', '| File | Points | Calculated km | Raw D+ | Raw D- |','|---|---:|---:|---:|---:|']
    for r in records: lines.append(f"| `{r['path']}` | {r['point_count']} | {r['distance_km']:.3f} | {r['raw_ascent_m'] if r['raw_ascent_m'] is not None else '–'} | {r['raw_descent_m'] if r['raw_descent_m'] is not None else '–'} |")
    lines += ['','## Same-family geometry diagnostics','']
    for c in comparisons:
        shared=c['shared_corridor_fraction_by_threshold_m']
        lines += [
          f"### `{c['a']}` vs `{c['b']}`",'',
          f"- Geometry classification: **{c['geometry_classification']}**",
          f"- Distance difference: {c['distance_difference_km']:+.2f} km",
          f"- Start separation: {c['start_separation_m']:.0f} m; finish separation: {c['finish_separation_m']:.0f} m",
          f"- Shared corridor within 50 m (symmetric minimum): {100*shared['50']['symmetric_min_fraction']:.1f}%",
          f"- Shared corridor within 100 m (symmetric minimum): {100*shared['100']['symmetric_min_fraction']:.1f}%",
          f"- A→B nearest distance median/p95: {c['nearest_separation_a_to_b_m']['median']:.0f}/{c['nearest_separation_a_to_b_m']['p95']:.0f} m",
          f"- B→A nearest distance median/p95: {c['nearest_separation_b_to_a_m']['median']:.0f}/{c['nearest_separation_b_to_a_m']['p95']:.0f} m",
          '', 'Divergence intervals over 100 m are recorded in the JSON report for course-change localization.',''
        ]
    REPORT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
