#!/usr/bin/env python3
import argparse,heapq,json,math
from pathlib import Path
from statistics import median
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

HALL=(14.01780,55.70819)
def D(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def plen(P):return sum(D(a,b) for a,b in zip(P,P[1:]))
def pdist(p,a,b):
    x,y=b[0]-a[0],b[1]-a[1]; c=x*x+y*y
    if not c:return D(p,a)
    t=max(0,min(1,((p[0]-a[0])*x+(p[1]-a[1])*y)/c));return D(p,(a[0]+t*x,a[1]+t*y))
def line_dist(p,P):return min(pdist(p,a,b) for a,b in zip(P,P[1:])) if len(P)>1 else D(p,P[0])
def pct(a,p):
    a=sorted(a);return a[min(len(a)-1,int((len(a)-1)*p))] if a else None
def resample(P,step=40.):
    out=[P[0]]; target=step; cum=0.
    for a,b in zip(P,P[1:]):
        l=D(a,b)
        if not l:continue
        while cum+l>=target:
            t=(target-cum)/l;out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])));target+=step
        cum+=l
    if D(out[-1],P[-1])>1:out.append(P[-1])
    return out

def graph(net,tr):
    ll=[];xy=[];ids={};adj=[]
    def nid(lon,lat):
        k=(round(float(lon),7),round(float(lat),7))
        if k not in ids:ids[k]=len(ll);ll.append((float(lon),float(lat)));xy.append(tr.transform(float(lon),float(lat)));adj.append([])
        return ids[k]
    for f in net['features']:
        pr=f.get('properties',{}); c=f['geometry']['coordinates']
        for a,b in zip(c,c[1:]):
            u,v=nid(*a),nid(*b);l=D(xy[u],xy[v])
            if l:
                e=(l,pr.get('osm_way_id'),pr.get('highway'));adj[u].append((v,*e));adj[v].append((u,*e))
    return ll,xy,adj,cKDTree(np.asarray(xy,float))

def candidates(tree,p,k=6,maxd=190.):
    d,i=tree.query(np.asarray(p),k=min(k,tree.n));d=np.atleast_1d(d);i=np.atleast_1d(i)
    z=[(int(n),float(x)) for x,n in zip(d,i) if x<=maxd]
    return z or [(int(i[0]),float(d[0]))]

def dij(adj,xy,src,targets,P,want_prev=False):
    targets=set(targets);found={};q=[(0.,src)];cost={src:0.};phys={src:0.};prev={};cache={}
    while q and len(found)<len(targets):
        du,u=heapq.heappop(q)
        if du!=cost.get(u):continue
        if u in targets and u not in found:found[u]=(du,phys[u])
        for v,l,way,hw in adj[u]:
            ek=(min(u,v),max(u,v))
            if ek not in cache:
                m=((xy[u][0]+xy[v][0])/2,(xy[u][1]+xy[v][1])/2);cache[ek]=line_dist(m,P)
            dv=min(cache[ek],220.); nd=du+l*(1+(dv/42.)**2)
            if nd<cost.get(v,1e100):cost[v]=nd;phys[v]=phys[u]+l;prev[v]=u;heapq.heappush(q,(nd,v))
    return found,prev

def path(prev,s,t):
    if s==t:return[s]
    if t not in prev:return None
    p=[t]
    while p[-1]!=s:p.append(prev[p[-1]])
    return list(reversed(p))

def main():
    ap=argparse.ArgumentParser()
    for x in ('guide','network','geojson','gpx','qa'):ap.add_argument('--'+x,required=True)
    a=ap.parse_args();guide=json.loads(Path(a.guide).read_text());net=json.loads(Path(a.network).read_text())
    tr=Transformer.from_crs(4326,3006,always_xy=True);back=Transformer.from_crs(3006,4326,always_xy=True)
    gl=[tr.transform(*p) for p in guide['geometry']['coordinates']]; fine=resample(gl,40.); step=6
    ai=list(range(0,len(fine),step))
    if ai[-1]!=len(fine)-1:ai.append(len(fine)-1)
    ll,xy,adj,tree=graph(net,tr); layers=[candidates(tree,fine[i]) for i in ai]
    dp={n:(3*d,None) for n,d in layers[0]}; backs=[]
    for z,(i0,i1) in enumerate(zip(ai,ai[1:])):
        P=fine[i0:i1+1]; rl=plen(P); nxt={n for n,_ in layers[z+1]}; snap=dict(layers[z+1]); ndp={};bk={}
        for src,(base,_) in dp.items():
            found,_=dij(adj,xy,src,nxt,P)
            for tgt,(wc,pl) in found.items():
                ratio=pl/max(1,rl); pen=2.2*abs(pl-rl)
                if ratio<.45:pen+=(.45-ratio)*rl*35
                if ratio>1.9:pen+=(ratio-1.9)*rl*35
                score=base+wc+pen+3*snap[tgt]
                if score<ndp.get(tgt,(1e100,None))[0]:ndp[tgt]=(score,src);bk[tgt]=src
        if not ndp:raise RuntimeError(f'no transition {z}')
        dp=ndp;backs.append(bk)
    end=min(dp,key=lambda n:dp[n][0]); chosen=[end]
    for z in range(len(backs)-1,-1,-1):chosen.append(backs[z][chosen[-1]])
    chosen.reverse();route=[]
    for z,(s0,t0) in enumerate(zip(chosen,chosen[1:])):
        P=fine[ai[z]:ai[z+1]+1];_,pr=dij(adj,xy,s0,{t0},P,True);p=path(pr,s0,t0)
        if route and route[-1]==p[0]:p=p[1:]
        route+=p
    R=[xy[i] for i in route];Rll=[ll[i] for i in route];total=plen(R); hall=tr.transform(*HALL);hi=min(range(len(R)),key=lambda i:D(R[i],hall));hat=plen(R[:hi+1]);dev=[];ways=[];hws=[];dup={}
    for u,v in zip(route,route[1:]):
        e=next(x for x in adj[u] if x[0]==v);m=((xy[u][0]+xy[v][0])/2,(xy[u][1]+xy[v][1])/2);dev.append(line_dist(m,gl));ways.append(e[2]);hws.append(e[3]);k=(min(u,v),max(u,v));dup[k]=dup.get(k,0)+1
    duplicate_m=sum(next(x[1] for x in adj[u] if x[0]==v)*(n-1) for (u,v),n in dup.items() if n>1)
    snaps=[D(fine[i],xy[n]) for i,n in zip(ai,chosen)]
    qa={'schema_version':1,'status':'candidate','distance_km':round(total/1000,3),'guide_distance_km':round(plen(gl)/1000,3),'hallamolla_at_km':round(hat/1000,3),'hallamolla_remaining_km':round((total-hat)/1000,3),'hallamolla_control_m':round(D(R[hi],hall),1),'start_finish_gap_m':round(D(R[0],R[-1]),1),'anchor_count':len(ai),'anchor_snap_median':round(median(snaps),1),'anchor_snap_p95':round(pct(snaps,.95),1),'edge_to_guide_median':round(median(dev),1),'edge_to_guide_p95':round(pct(dev,.95),1),'edge_to_guide_max':round(max(dev),1),'duplicate_edge_m':round(duplicate_m,1),'osm_way_count':len(set(w for w in ways if w)),'highway_types':sorted(set(h for h in hws if h))}
    qa['qa_pass']=12<=qa['distance_km']<=14.8 and qa['hallamolla_control_m']<=100 and 3.8<=qa['hallamolla_remaining_km']<=5.2 and qa['start_finish_gap_m']<=100 and qa['edge_to_guide_p95']<=150
    qa['status']='validated_reconstruction_candidate' if qa['qa_pass'] else 'blocked_by_qa'
    feat={'type':'Feature','properties':{'name':'ÖST Trail 13/14 km OSM map-match v2','status':qa['status'],'distance_km':qa['distance_km'],'provenance':'organizer raster topology map-matched to OSM','not_an_organizer_gpx':True},'geometry':{'type':'LineString','coordinates':[list(p) for p in Rll]}}
    Path(a.geojson).parent.mkdir(parents=True,exist_ok=True);Path(a.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+'\n');pts=''.join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon,lat in Rll);Path(a.gpx).write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys"><trk><name>ÖST Trail 13/14 OSM map match v2</name><trkseg>'+pts+'</trkseg></trk></gpx>\n');Path(a.qa).write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n');print(json.dumps(qa,indent=2,ensure_ascii=False))
    if not qa['qa_pass']:raise SystemExit(2)
if __name__=='__main__':main()
