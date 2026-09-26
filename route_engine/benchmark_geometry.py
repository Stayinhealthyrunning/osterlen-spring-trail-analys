#!/usr/bin/env python3
"""Compare two GeoJSON LineStrings using dependency-free sampled geodesic metrics."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

R=6371000.0
def hav(a,b):
    lon1,lat1=map(math.radians,a); lon2,lat2=map(math.radians,b)
    h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 2*R*math.asin(math.sqrt(h))

def line(doc):
    if doc.get("type")=="Feature": return doc["geometry"]["coordinates"]
    if doc.get("type")=="LineString": return doc["coordinates"]
    if doc.get("type")=="FeatureCollection":
        for f in doc.get("features",[]):
            if f.get("geometry",{}).get("type")=="LineString": return f["geometry"]["coordinates"]
    raise ValueError("No LineString found")

def length(c): return sum(hav(a,b) for a,b in zip(c,c[1:]))

def resample(c,step=10.0):
    out=[c[0]]
    for a,b in zip(c,c[1:]):
        d=hav(a,b); n=max(1,math.ceil(d/step))
        for i in range(1,n+1):
            t=i/n; out.append([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t])
    return out

def nearest(samples,target):
    # Target is also densely resampled; sufficient for benchmark calibration.
    return [min(hav(p,q) for q in target) for p in samples]

def pct(values,p):
    if not values:return 0.0
    v=sorted(values); idx=min(len(v)-1,max(0,math.ceil(p*len(v))-1)); return v[idx]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("reconstruction",type=Path); ap.add_argument("truth",type=Path)
    ap.add_argument("--sample-m",type=float,default=10.0)
    args=ap.parse_args()
    a=line(json.loads(args.reconstruction.read_text())); b=line(json.loads(args.truth.read_text()))
    ar=resample(a,args.sample_m); br=resample(b,args.sample_m)
    d=nearest(ar,br)+nearest(br,ar)
    la,lb=length(a),length(b)
    result={
      "reconstruction_km":round(la/1000,3),"truth_km":round(lb/1000,3),
      "length_error_pct":round(100*(la-lb)/lb,2) if lb else None,
      "symmetric_median_m":round(pct(d,.5),1),"symmetric_p95_m":round(pct(d,.95),1),
      "within_10m_pct":round(100*sum(x<=10 for x in d)/len(d),1),
      "within_25m_pct":round(100*sum(x<=25 for x in d)/len(d),1),
      "within_50m_pct":round(100*sum(x<=50 for x in d)/len(d),1),
      "sample_spacing_m":args.sample_m
    }
    print(json.dumps(result,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
