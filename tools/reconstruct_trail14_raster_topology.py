#!/usr/bin/env python3
import argparse, heapq, json, math
from pathlib import Path
import networkx as nx
import numpy as np
from pyproj import Transformer

CASTLE=(13.96063,55.71787)
HALL=(14.01780,55.70819)
OBS_REMAIN=4500.0

def D(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def L(p): return sum(D(a,b) for a,b in zip(p,p[1:]))
def segdist(p,a,b):
    vx,vy=b[0]-a[0],b[1]-a[1]; c=vx*vx+vy*vy
    if not c:return D(p,a)
    t=max(0,min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vy)/c))
    return D(p,(a[0]+t*vx,a[1]+t*vy))

def main():
    ap=argparse.ArgumentParser()
    for x in ('skeleton','registration','geojson','gpx','qa'): ap.add_argument('--'+x,required=True)
    a=ap.parse_args(); s=json.loads(Path(a.skeleton).read_text()); r=json.loads(Path(a.registration).read_text())
    H=np.array(r['trail14_to_trail5_homography'],float)
    tr=Transformer.from_crs(4326,3006,always_xy=True); back=Transformer.from_crs(3006,4326,always_xy=True)
    castle=tr.transform(*CASTLE); hall=tr.transform(*HALL)
    def xy(p):
        q=H@np.array([p[0],p[1],1.]); px,py=q[0]/q[2],q[1]/q[2]
        return (432733+(px-25.3)/(1074.7-25.3)*5232-198.3,6176791-(py-49.5)/(694.7-49.5)*3040+111.9)
    pts=[tuple(map(int,p)) for p in s['skeleton_pixels_xy']]; idx={p:i for i,p in enumerate(pts)}; X=[xy(p) for p in pts]
    G=nx.Graph(); G.add_nodes_from(range(len(pts)))
    for i,(x,y) in enumerate(pts):
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if not(dx or dy):continue
                j=idx.get((x+dx,y+dy))
                if j is not None and j>i:G.add_edge(i,j,w=D(X[i],X[j]))
    cycpx=[tuple(map(float,p)) for p in s['cycles'][0]['vertices_xy']]
    oncyc=set()
    for i,p in enumerate(pts):
        if min(segdist(p,u,v) for u,v in zip(cycpx,cycpx[1:]+cycpx[:1]))<1.1:oncyc.add(i)
    eps=[]
    for p in s['skeleton']['endpoints_xy']:
        i=idx.get(tuple(p))
        if i is not None:eps.append(i)
    eps=sorted(eps,key=lambda i:D(X[i],castle))[:2]
    def tail(st):
        d={st:0.}; prev={}; q=[(0.,st)]
        while q:
            du,u=heapq.heappop(q)
            if du!=d.get(u):continue
            if u in oncyc:
                p=[u]
                while p[-1]!=st:p.append(prev[p[-1]])
                return list(reversed(p)),u
            for v,e in G[u].items():
                nd=du+e['w']
                if nd<d.get(v,1e99):d[v]=nd;prev[v]=u;heapq.heappush(q,(nd,v))
        raise RuntimeError('no cycle')
    tails=[tail(i) for i in eps]; T=[[X[i] for i in p] for p,_ in tails]; entry=X[tails[0][1]]
    C=[xy(p) for p in cycpx]; ci=min(range(len(C)),key=lambda i:D(C[i],entry)); rot=C[ci:]+C[:ci]+[C[ci]]
    cycles=[('forward',rot),('reverse',[rot[0]]+list(reversed(rot[1:-1]))+[rot[0]])]
    variants=[]
    for si in (0,1):
        for name,c in cycles:
            route=T[si]+c[1:]+list(reversed(T[1-si]))[1:]
            hi=min(range(len(route)),key=lambda i:D(route[i],hall)); total=L(route); at=L(route[:hi+1]); rem=total-at
            variants.append((abs(rem-OBS_REMAIN),si,name,route,total,at,rem,D(route[hi],hall)))
    best=min(variants,key=lambda z:z[0]); _,si,name,route,total,at,rem,hallgap=best
    ll=[back.transform(*p) for p in route]
    feat={'type':'Feature','properties':{'name':'ÖST Trail 13/14 km organizer-raster topology','status':'georeferenced_organizer_raster_reference','distance_km':round(total/1000,3),'provenance':'organizer raster + participant Hallamölla direction control','not_an_organizer_gpx':True},'geometry':{'type':'LineString','coordinates':[list(p) for p in ll]}}
    Path(a.geojson).parent.mkdir(parents=True,exist_ok=True); Path(a.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+'\n')
    t=''.join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon,lat in ll); Path(a.gpx).write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys"><trk><name>ÖST Trail 13/14 raster topology</name><trkseg>'+t+'</trkseg></trk></gpx>\n')
    qa={'schema_version':2,'status':'georeferenced_organizer_raster_reference','distance_km':round(total/1000,3),'participant_2023_reference_km':13.67,'hallamolla_at_km':round(at/1000,3),'hallamolla_remaining_km':round(rem/1000,3),'participant_hallamolla_remaining_km':4.5,'hallamolla_control_m':round(hallgap,1),'start_finish_gap_m':round(D(route[0],route[-1]),1),'selected_start_tail':si,'selected_cycle_direction':name,'tail_lengths_km':[round(L(x)/1000,3) for x in T],'cycle_length_km':round(L(rot)/1000,3),'map_registration_median_px':r['reprojection_px']['median'],'map_registration_p95_px':r['reprojection_px']['p95'],'variants':[{'start_tail':v[1],'direction':v[2],'distance_km':round(v[4]/1000,3),'hall_remaining_km':round(v[6]/1000,3),'hall_control_m':round(v[7],1)} for v in variants]}
    qa['topology_qa_pass']=abs(qa['hallamolla_remaining_km']-4.5)<=0.15 and qa['hallamolla_control_m']<=150 and 12<=qa['distance_km']<=14.8
    Path(a.qa).write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(qa,indent=2,ensure_ascii=False))
    if not qa['topology_qa_pass']:raise SystemExit(2)
if __name__=='__main__':main()
