#!/usr/bin/env python3
"""Measure the full Trail 5 organizer-raster skeleton in SWEREF 99 TM.

This is a geometry cross-check of the archived organizer raster. It does not
create an organizer GPX and does not use nominal race distance as a target.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

FRAME={"left":25.3,"right":1074.7,"top":49.5,"bottom":694.8}
SW={"E":432733.0,"N":6173751.0}
NE={"E":437965.0,"N":6176791.0}

def xy(p):
    px,py=p
    return (
        SW["E"]+(px-FRAME["left"])/(FRAME["right"]-FRAME["left"])*(NE["E"]-SW["E"]),
        NE["N"]-(py-FRAME["top"])/(FRAME["bottom"]-FRAME["top"])*(NE["N"]-SW["N"]),
    )

def dist(a,b):
    return math.hypot(a[0]-b[0],a[1]-b[1])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("skeleton")
    args=ap.parse_args()
    doc=json.loads(Path(args.skeleton).read_text(encoding="utf-8"))
    pts=[tuple(map(int,p)) for p in doc["skeleton_pixels_xy"]]
    ids={p:i for i,p in enumerate(pts)}
    adj=[[] for _ in pts]
    for i,(x,y) in enumerate(pts):
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if not (dx or dy):
                    continue
                j=ids.get((x+dx,y+dy))
                if j is not None:
                    adj[i].append(j)
    endpoints=[i for i,a in enumerate(adj) if len(a)==1]
    if len(endpoints)!=2:
        raise SystemExit(f"expected 2 endpoints, got {len(endpoints)}")
    order=[endpoints[0]]
    prev=-1
    cur=endpoints[0]
    while cur!=endpoints[1]:
        nxt=next((j for j in adj[cur] if j!=prev),None)
        if nxt is None:
            raise SystemExit("skeleton is not a single connected line")
        order.append(nxt)
        prev,cur=cur,nxt
        if len(order)>len(pts)+1:
            raise SystemExit("unexpected cycle in Trail 5 skeleton")
    if len(order)!=len(pts):
        raise SystemExit(f"ordered {len(order)} of {len(pts)} skeleton points")
    coords=[xy(pts[i]) for i in order]
    length=sum(dist(a,b) for a,b in zip(coords,coords[1:]))
    out={
        "status":"organizer_raster_skeleton_measurement",
        "point_count":len(coords),
        "distance_km":round(length/1000,3),
        "start_finish_gap_m":round(dist(coords[0],coords[-1]),1),
        "source":"reports/trail5-route-skeleton.json",
        "provenance":"derived_from_georeferenced_organizer_raster",
        "not_an_organizer_gpx":True,
    }
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
