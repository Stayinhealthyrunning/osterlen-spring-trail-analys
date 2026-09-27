#!/usr/bin/env python3
"""Extract organizer route strokes as skeleton graphs and report candidate cycles.

This is deliberately format-agnostic: it works in image space first. Georeferencing
and OSM snapping consume the persisted skeleton/cycle output in later steps.
"""
import argparse, json, math
from pathlib import Path
import cv2
import numpy as np
import networkx as nx
from skimage.morphology import skeletonize

NEIGH=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def pixlen(a,b):
    return math.sqrt(2.0) if a[0]!=b[0] and a[1]!=b[1] else 1.0

def largest_component(mask):
    n,lab,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    if n<=1: raise RuntimeError("No dark component")
    idx=max(range(1,n),key=lambda i:int(stats[i,cv2.CC_STAT_AREA]))
    return lab==idx, {
      "area":int(stats[idx,cv2.CC_STAT_AREA]),
      "bbox":[int(stats[idx,cv2.CC_STAT_LEFT]),int(stats[idx,cv2.CC_STAT_TOP]),
              int(stats[idx,cv2.CC_STAT_WIDTH]),int(stats[idx,cv2.CC_STAT_HEIGHT])]
    }

def graph_from_skeleton(skel):
    pts=np.argwhere(skel)
    s={tuple(map(int,p)) for p in pts}
    g=nx.Graph()
    for y,x in s: g.add_node((y,x))
    for y,x in s:
        for dy,dx in NEIGH:
            q=(y+dy,x+dx)
            if q in s and (y,x)<q:
                g.add_edge((y,x),q,weight=pixlen((y,x),q))
    return g

def path_length(g,nodes,closed=False):
    if len(nodes)<2:return 0.0
    total=sum(g[a][b]["weight"] for a,b in zip(nodes,nodes[1:]) if g.has_edge(a,b))
    if closed and g.has_edge(nodes[-1],nodes[0]): total+=g[nodes[-1]][nodes[0]]["weight"]
    return total

def simplify_cycle(cycle, epsilon=1.5):
    pts=np.array([[x,y] for y,x in cycle],dtype=np.float32).reshape((-1,1,2))
    simp=cv2.approxPolyDP(pts,epsilon,True).reshape((-1,2))
    return [[float(x),float(y)] for x,y in simp]

def extract(image, threshold, crop):
    img=cv2.imread(str(image),cv2.IMREAD_GRAYSCALE)
    h,w=img.shape
    x0,y0,x1,y1=crop or (0,0,w,h)
    roi=img[y0:y1,x0:x1]
    comp,st=largest_component(roi<threshold)
    full=np.zeros((h,w),dtype=bool); full[y0:y1,x0:x1]=comp
    sk=skeletonize(full)
    g=graph_from_skeleton(sk)
    comps=sorted(nx.connected_components(g),key=len,reverse=True)
    if not comps: raise RuntimeError("Empty skeleton")
    g=g.subgraph(comps[0]).copy()
    degrees=dict(g.degree())
    endpoints=[n for n,d in degrees.items() if d==1]
    junctions=[n for n,d in degrees.items() if d>=3]
    cycles=nx.cycle_basis(g)
    cyc=[]
    for c in cycles:
        cyc.append({
          "node_count":len(c),
          "pixel_length":path_length(g,c,True),
          "vertices_xy":simplify_cycle(c,1.2)
        })
    cyc.sort(key=lambda z:z["pixel_length"],reverse=True)
    skeleton_xy=[[int(x),int(y)] for y,x in sorted(g.nodes())]
    return {
      "image":str(image),"size_px":[w,h],"threshold":threshold,
      "crop_xyxy":[x0,y0,x1,y1],
      "source_component":{"area":st["area"],"bbox_local":st["bbox"]},
      "skeleton":{"node_count":g.number_of_nodes(),"edge_count":g.number_of_edges(),
                  "total_edge_length_px":sum(d["weight"] for _,_,d in g.edges(data=True)),
                  "endpoints_xy":[[x,y] for y,x in endpoints],
                  "junctions_xy":[[x,y] for y,x in junctions],
                  "endpoint_count":len(endpoints),"junction_count":len(junctions)},
      "cycle_count":len(cyc),"cycles":cyc[:25],
      "skeleton_pixels_xy":skeleton_xy
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--image",required=True)
    ap.add_argument("--threshold",type=int,default=90)
    ap.add_argument("--crop",nargs=4,type=int,metavar=("X0","Y0","X1","Y1"))
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    out=extract(Path(a.image),a.threshold,tuple(a.crop) if a.crop else None)
    Path(a.output).write_text(json.dumps(out,indent=2)+"\n")
    slim={k:v for k,v in out.items() if k!="skeleton_pixels_xy"}
    slim["cycles"]=[{k:v for k,v in c.items() if k!="vertices_xy"} for c in out["cycles"]]
    print(json.dumps(slim,indent=2))
if __name__=="__main__": main()
