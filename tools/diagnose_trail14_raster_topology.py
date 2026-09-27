#!/usr/bin/env python3
import json, math, sys
from pathlib import Path
import cv2, numpy as np, networkx as nx
from skimage.morphology import skeletonize

img=cv2.imread(sys.argv[1],0)
mask=(img<90).astype(np.uint8)
n,lab,stats,_=cv2.connectedComponentsWithStats(mask,8)
cands=[i for i in range(1,n) if stats[i,0]<950 and 150<stats[i,1]<580]
best=max(cands,key=lambda i:stats[i,4])
route=(lab==best)
sk=skeletonize(route)
ys,xs=np.where(sk)
S={(int(x),int(y)) for x,y in zip(xs,ys)}
G=nx.Graph()
for x,y in S:
    for dx,dy,w in ((1,0,1),(0,1,1),(1,1,2**.5),(1,-1,2**.5)):
        q=(x+dx,y+dy)
        if q in S:G.add_edge((x,y),q,weight=w)
# Prune short spurs caused by arrows/text attached to the thick course line.
for _ in range(30):
    ends=[v for v in G if G.degree(v)==1]
    changed=False
    for e in ends:
        path=[e]; cur=e; prev=None; L=0
        while G.degree(cur)<=2:
            nxt=[z for z in G.neighbors(cur) if z!=prev]
            if not nxt: break
            z=nxt[0]; L+=G[cur][z]['weight']; path.append(z); prev,cur=cur,z
            if G.degree(cur)!=2: break
        if L<35:
            G.remove_nodes_from(path[:-1]); changed=True
    if not changed: break
cycles=nx.cycle_basis(G)
cycles=sorted(cycles,key=len,reverse=True)
out={
 "component_bbox_px":[int(stats[best,0]),int(stats[best,1]),int(stats[best,2]),int(stats[best,3])],
 "component_area_px":int(stats[best,4]),
 "skeleton_nodes":G.number_of_nodes(),
 "skeleton_edges":G.number_of_edges(),
 "endpoints":sum(G.degree(v)==1 for v in G),
 "junctions":sum(G.degree(v)>2 for v in G),
 "cycle_count":len(cycles),
 "largest_cycles_nodes":[len(c) for c in cycles[:20]]
}
Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
