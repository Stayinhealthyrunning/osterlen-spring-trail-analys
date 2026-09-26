#!/usr/bin/env python3
import json, math, sys
from pathlib import Path

def hav(a,b):
    R=6371000.0
    p1,p2=map(math.radians,(a[1],b[1])); dp=math.radians(b[1]-a[1]); dl=math.radians(b[0]-a[0])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))

def main():
    p=Path(sys.argv[1]); d=json.loads(p.read_text())
    feats=d.get("features",[])
    ways=[]; total=0
    types={}
    for f in feats:
        g=f.get("geometry") or {}
        if g.get("type")!="LineString": continue
        c=g["coordinates"]; L=sum(hav(a,b) for a,b in zip(c,c[1:]))
        pr=f.get("properties") or {}
        hw=pr.get("highway","unknown"); types[hw]=types.get(hw,0)+1
        ways.append({"osm_way_id":pr.get("osm_way_id") or pr.get("id"),"highway":hw,"name":pr.get("name"),"length_m":round(L,1),"points":len(c)})
        total+=L
    out={"feature_count":len(feats),"line_count":len(ways),"network_length_km":round(total/1000,3),"highway_counts":types,
         "named_ways":[w for w in ways if w["name"]]}
    Path(sys.argv[2]).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:out[k] for k in ("feature_count","line_count","network_length_km","highway_counts")},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
