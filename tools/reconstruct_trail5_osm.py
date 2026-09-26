#!/usr/bin/env python3
import argparse,json,math,heapq
from pathlib import Path
import cv2,numpy as np,networkx as nx
from skimage.morphology import skeletonize
from scipy.spatial import cKDTree
from pyproj import Transformer

def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def extract_ordered(imgpath,thr=90,crop=(40,120,700,650)):
 im=cv2.imread(imgpath,0); x0,y0,x1,y1=crop; roi=im[y0:y1,x0:x1]
 n,lab,stats,_=cv2.connectedComponentsWithStats((roi<thr).astype(np.uint8),8); idx=max(range(1,n),key=lambda i:stats[i,cv2.CC_STAT_AREA])
 full=np.zeros_like(im,dtype=bool); full[y0:y1,x0:x1]=lab==idx; sk=skeletonize(full)
 pts={tuple(map(int,p)) for p in np.argwhere(sk)}; g=nx.Graph()
 for y,x in pts:
  for dy in (-1,0,1):
   for dx in (-1,0,1):
    if not(dx or dy):continue
    q=(y+dy,x+dx)
    if q in pts:g.add_edge((y,x),q,weight=math.hypot(dx,dy))
 ends=[p for p,d in g.degree() if d==1]
 if len(ends)!=2: raise RuntimeError(f"Expected 2 endpoints, got {len(ends)}")
 p=nx.shortest_path(g,ends[0],ends[1],weight="weight")
 return [(x,y) for y,x in p]

def px_to_3006(p):
 # native 1100x777 raster frame scaled from validated prototype frame
 left,right,top,bottom=25.3,1074.7,49.5,694.7
 sw=(432733.0,6173751.0); ne=(437965.0,6176791.0)
 x,y=p; fx=(x-left)/(right-left); fy=(y-top)/(bottom-top)
 return (sw[0]+fx*(ne[0]-sw[0]), ne[1]-fy*(ne[1]-sw[1]))

def sample(line,step=25):
 out=[line[0]]; acc=0
 for a,b in zip(line,line[1:]):
  L=dist(a,b); acc+=L
  if dist(out[-1],b)>=step:out.append(b)
 if dist(out[-1],line[-1])>1:out.append(line[-1])
 return out

def build_osm(path,trace):
 d=json.loads(Path(path).read_text()); tr=Transformer.from_crs(4326,3006,always_xy=True)
 G=nx.Graph(); ttree=cKDTree(trace)
 for f in d["features"]:
  c=f["geometry"]["coordinates"]; pr=f.get("properties",{})
  xy=[tr.transform(lon,lat) for lon,lat in c]
  for a,b in zip(xy,xy[1:]):
   L=dist(a,b)
   if L==0:continue
   mid=((a[0]+b[0])/2,(a[1]+b[1])/2); dev=float(ttree.query(mid)[0])
   # raster fit dominates, but length still prevents wild detours
   cost=L*(1+(min(dev,120)/28)**2)
   G.add_edge(a,b,weight=cost,length=L,way=pr.get("osm_way_id"),highway=pr.get("highway"))
 return G

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--image");ap.add_argument("--network");ap.add_argument("--geojson");ap.add_argument("--gpx");ap.add_argument("--qa");a=ap.parse_args()
 pix=extract_ordered(a.image); trace=[px_to_3006(p) for p in pix]
 # Registration: translate the validated raster frame so the midpoint of its start/finish gap equals the independent Christinehof control.
 castle=(434707.0,6175169.0); gapmid=((trace[0][0]+trace[-1][0])/2,(trace[0][1]+trace[-1][1])/2); shift=(castle[0]-gapmid[0],castle[1]-gapmid[1]); trace=[(p[0]+shift[0],p[1]+shift[1]) for p in trace]; trace_s=sample(trace,250)
 G=build_osm(a.network,trace); nodes=list(G.nodes); tree=cKDTree(nodes)
 anchors=[]; anchor_dev=[]
 for p in trace_s:
  dd,ii=tree.query(p); n=nodes[int(ii)]
  if dd<=90 and (not anchors or n!=anchors[-1]): anchors.append(n);anchor_dev.append(float(dd))
 route=[]
 usedways=[]; hws=[]
 used_edges=set()
 for s,t in zip(anchors,anchors[1:]):
  def dyn(u,v,d):
   return d["weight"]*(80 if frozenset((u,v)) in used_edges else 1)
  try:path=nx.shortest_path(G,s,t,weight=dyn)
  except nx.NetworkXNoPath:continue
  plen=sum(G[u][v]["length"] for u,v in zip(path,path[1:]))
  direct=dist(s,t)
  if plen > max(550,direct*4.0): continue
  for u,v in zip(path,path[1:]): used_edges.add(frozenset((u,v)))
  if route and path[0]==route[-1]:path=path[1:]
  route.extend(path)
 # close tiny organizer start/finish gap through graph
 if route:
  try:
   close=nx.shortest_path(G,route[-1],route[0],weight="weight")
   close_len=sum(G[u][v]["length"] for u,v in zip(close,close[1:]))
   if close_len<350: route.extend(close[1:])
  except nx.NetworkXNoPath:pass
 for u,v in zip(route,route[1:]):
  e=G[u][v];usedways.append(e.get("way"));hws.append(e.get("highway"))
 length=sum(G[u][v]["length"] for u,v in zip(route,route[1:]))
 rtree=cKDTree(trace); dev=np.array([rtree.query(p)[0] for p in route]) if route else np.array([])
 back=Transformer.from_crs(3006,4326,always_xy=True); ll=[back.transform(*p) for p in route]
 feat={"type":"Feature","properties":{"name":"ÖST Naturloppet 5 km reconstructed","status":"validated_reconstruction_candidate","provenance":"organizer raster snapped to OpenStreetMap","distance_km":round(length/1000,3),"osm_way_ids":list(dict.fromkeys(x for x in usedways if x))},"geometry":{"type":"LineString","coordinates":[list(p) for p in ll]}}
 Path(a.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+"\n")
 pts="".join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon,lat in ll)
 Path(a.gpx).write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys route reconstruction"><trk><name>ÖST Naturloppet 5 km reconstructed</name><trkseg>'+pts+'</trkseg></trk></gpx>\n')
 qa={"distance_km":round(length/1000,3),"nominal_km":5.0,"route_points":len(route),"anchors":len(anchors),"raster_translation_m":[round(shift[0],1),round(shift[1],1)],"max_anchor_to_osm_m":round(max(anchor_dev),1),"median_route_to_raster_m":round(float(np.median(dev)),1),"p95_route_to_raster_m":round(float(np.percentile(dev,95)),1),"start_finish_gap_m":round(dist(route[0],route[-1]),1),"osm_way_count":len(set(x for x in usedways if x)),"highway_types":sorted(set(x for x in hws if x))}
 Path(a.qa).write_text(json.dumps(qa,indent=2)+"\n");print(json.dumps(qa,indent=2))
if __name__=="__main__":main()
