#!/usr/bin/env python3
"""Compare archived GPX geometries without assuming marketed distance equals course identity.

Routes are resampled at fixed distance intervals and compared symmetrically by nearest
geographic distance. This report is diagnostic input for later explicit course-version
assignment; it never assigns versions automatically.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, statistics
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
GPX_ROOT=ROOT/'data/source/gpx'
OUT_JSON=ROOT/'reports/gpx-comparison.json'
OUT_MD=ROOT/'reports/gpx-comparison.md'
R=6371008.8
STEP_M=100.0

def hav(a,b):
    lat1,lon1=map(math.radians,a); lat2,lon2=map(math.radians,b)
    dlat=lat2-lat1; dlon=lon2-lon1
    h=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))

def parse(path):
    root=ET.parse(path).getroot(); pts=[]
    for el in root.iter():
        if el.tag.rsplit('}',1)[-1].lower() in {'trkpt','rtept'}:
            pts.append((float(el.attrib['lat']),float(el.attrib['lon'])))
    if len(pts)<2: raise ValueError(f'{path}: fewer than 2 points')
    cumulative=[0.0]
    for a,b in zip(pts,pts[1:]): cumulative.append(cumulative[-1]+hav(a,b))
    return pts,cumulative

def interpolate(a,b,t): return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)

def resample(pts,cum,step=STEP_M):
    total=cum[-1]; targets=[]; x=0.0
    while x<total: targets.append(x); x+=step
    if not targets or targets[-1] != total: targets.append(total)
    out=[]; j=1
    for target in targets:
        while j<len(cum)-1 and cum[j]<target: j+=1
        a_i=max(0,j-1); b_i=min(j,len(pts)-1); span=cum[b_i]-cum[a_i]
        t=(target-cum[a_i])/span if span>0 else 0
        out.append(interpolate(pts[a_i],pts[b_i],max(0,min(1,t))))
    return out,total

def nearest_distances(a,b):
    return [min(hav(p,q) for q in b) for p in a]

def percentile(vals,q):
    if not vals: return None
    s=sorted(vals); pos=(len(s)-1)*q; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return s[lo]
    return s[lo]+(s[hi]-s[lo])*(pos-lo)

def route_fingerprint(samples):
    # Direction-sensitive, 100 m-resampled, coordinates rounded to ~1 m.
    text='\n'.join(f'{lat:.5f},{lon:.5f}' for lat,lon in samples)
    return hashlib.sha256(text.encode()).hexdigest()

def comparison(path_a,path_b):
    pa,ca=parse(path_a); pb,cb=parse(path_b)
    sa,ta=resample(pa,ca); sb,tb=resample(pb,cb)
    ab=nearest_distances(sa,sb); ba=nearest_distances(sb,sa); sym=ab+ba
    within={str(m):round(sum(d<=m for d in sym)/len(sym),4) for m in (10,25,50,100,250)}
    length_delta=abs(ta-tb)
    return {
      'a':str(path_a.relative_to(ROOT)).replace('\\','/'),
      'b':str(path_b.relative_to(ROOT)).replace('\\','/'),
      'resample_step_m':STEP_M,
      'length_a_km':round(ta/1000,4),'length_b_km':round(tb/1000,4),
      'absolute_length_delta_km':round(length_delta/1000,4),
      'start_separation_m':round(hav(sa[0],sb[0]),1),
      'finish_separation_m':round(hav(sa[-1],sb[-1]),1),
      'symmetric_nearest_distance_m':{
        'median':round(statistics.median(sym),1),'p95':round(percentile(sym,.95),1),'max':round(max(sym),1)
      },
      'fraction_within_m':within,
      'fingerprint_a':route_fingerprint(sa),'fingerprint_b':route_fingerprint(sb),
      'identical_fingerprint':route_fingerprint(sa)==route_fingerprint(sb),
      'interpretation_hint':(
        'very_high_overlap' if within['50']>=.98 else
        'high_overlap' if within['50']>=.95 else
        'substantial_overlap' if within['100']>=.90 else
        'materially_different_geometry'
      ),
      'warning':'Nearest-distance overlap is diagnostic. Course versions must still be explicitly reviewed/assigned.'
    }

def family_from_path(p):
    try: return p.relative_to(GPX_ROOT).parts[0]
    except Exception: return None

def main():
    files=sorted(GPX_ROOT.rglob('*.gpx'))
    pairs=[]
    for i,a in enumerate(files):
        for b in files[i+1:]:
            if family_from_path(a)==family_from_path(b):
                pairs.append(comparison(a,b))
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'method':{'resample_step_m':STEP_M,'comparison':'symmetric nearest-route-point distance'},'comparisons':pairs}
    OUT_JSON.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# GPX geometry comparisons','',
           'Diagnostic comparison of archived routes. This report does **not** automatically assign course versions.','',
           '| A | B | km A | km B | Δ km | ≤50 m | ≤100 m | median m | p95 m | hint |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for c in pairs:
        n=c['symmetric_nearest_distance_m']; w=c['fraction_within_m']
        lines.append(f"| `{c['a']}` | `{c['b']}` | {c['length_a_km']:.2f} | {c['length_b_km']:.2f} | {c['absolute_length_delta_km']:.2f} | {w['50']:.1%} | {w['100']:.1%} | {n['median']:.1f} | {n['p95']:.1f} | {c['interpretation_hint']} |")
    if not pairs: lines.append('| _No comparable same-family GPX pairs yet_ | | | | | | | | | |')
    lines += ['','Course identity must be reviewed with route context, direction, start/finish, known race-day changes and source provenance.','']
    OUT_MD.write_text('\n'.join(lines),encoding='utf-8')
    print(f'Compared {len(pairs)} same-family GPX pairs')

if __name__=='__main__': main()
