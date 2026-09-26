#!/usr/bin/env python3
import argparse,json,math
from pathlib import Path
import cv2,numpy as np,networkx as nx
from scipy.spatial import cKDTree
from pyproj import Transformer

def D(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def component(imgpath):
 im=cv2.imread(imgpath,0); mask=(im<90).astype(np.uint8); n,lab,stats,_=cv2.connectedComponentsWithStats(mask,8)
 # organizer route is the dominant 13/14 km component in this bounding region
 best=max((i for i in range(1,n) if stats[i,0]<950 and stats[i,1]>150 and stats[i,1]<580),key=lambda i:stats[i,4])
 ys,xs=np.where(lab==best); return np.column_stack([xs,ys]).astype(float)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--image");ap.add_argument("--network");ap.add_argument("--registration");ap.add_argument("--relations");ap.add_argument("--trail5");ap.add_argument("--geojson");ap.add_argument("--gpx");ap.add_argument("--qa");a=ap.parse_args()
 pix=component(a.image)
 reg=json.loads(Path(a.registration).read_text()); H=np.array(reg["trail14_to_trail5_homography"])
 q=np.c_[pix,np.ones(len(pix))]@H.T; p5=q[:,:2]/q[:,2,None]
 # validated Trail5 pixel frame -> EPSG:3006, then Christinehof translation control
 left,right,top,bottom=25.3,1074.7,49.5,694.7; sw=(432733.,6173751.); ne=(437965.,6176791.)
 xy=np.column_stack([sw[0]+(p5[:,0]-left)/(right-left)*(ne[0]-sw[0])-198.3, ne[1]-(p5[:,1]-top)/(bottom-top)*(ne[1]-sw[1])+111.9])
 cloud=cKDTree(xy[::3])
 tr=Transformer.from_crs(4326,3006,always_xy=True); back=Transformer.from_crs(3006,4326,always_xy=True)
 rels=json.loads(Path(a.relations).read_text())
 skane=set(); backset=set()
 for r in rels:
  name=(r.get("tags",{}).get("name") or "").lower()
  target=None
  if "skåneleden" in name or "skaneleden" in name: target=skane
  if "backaleden" in name: target=backset
  if target is not None:
   target.update(m["ref"] for m in r.get("members",[]) if m.get("type")=="way")
 net=json.loads(Path(a.network).read_text()); G=nx.Graph()
 for f in net["features"]:
  pr=f.get("properties",{}); c=f["geometry"]["coordinates"]; pts=[tr.transform(*z) for z in c]
  for u,v in zip(pts,pts[1:]):
   L=D(u,v)
   if not L:continue
   mid=((u[0]+v[0])/2,(u[1]+v[1])/2); dev=float(cloud.query(mid)[0])
   # strongly prefer the organizer stroke; cap so disconnected-looking raster noise does not dominate
   w=L*(1+(min(dev,150)/35)**2)
   wid=pr.get("osm_way_id")
   G.add_edge(u,v,weight=w,length=L,dev=dev,way=wid,highway=pr.get("highway"),skane=wid in skane,back=wid in backset)
 nodes=list(G.nodes); nt=cKDTree(nodes)
 castle=(434707.,6175169.); hall=tr.transform(14.01780,55.70819)
 s=nodes[int(nt.query(castle)[1])]; h=nodes[int(nt.query(hall)[1])]
 # Candidate search: generate plausible outbound paths; for each, force the return search away from its used edges.
 first=[]
 for path in nx.shortest_simple_paths(G,s,h,weight="weight"):
  L=sum(G[u][v]["length"] for u,v in zip(path,path[1:])); cost=sum(G[u][v]["weight"] for u,v in zip(path,path[1:]))
  if 3500<=L<=8500:
   edges={frozenset((u,v)) for u,v in zip(path,path[1:])}; first.append((path,L,cost,edges))
  if len(first)>=35:break
 best=None
 for A in first:
  def return_weight(u,v,d):
   return d["weight"]*(60 if frozenset((u,v)) in A[3] else 1)
  try: bp=nx.shortest_path(G,s,h,weight=return_weight)
  except nx.NetworkXNoPath: continue
  BL=sum(G[u][v]["length"] for u,v in zip(bp,bp[1:])); BC=sum(G[u][v]["weight"] for u,v in zip(bp,bp[1:]))
  Bedges={frozenset((u,v)) for u,v in zip(bp,bp[1:])}
  overlap=sum(G[tuple(e)[0]][tuple(e)[1]]["length"] for e in A[3]&Bedges)
  total=A[1]+BL
  score=A[2]+BC+overlap*100+abs(total-13670)*1.5
  B=(bp,BL,BC,Bedges)
  if best is None or score<best[0]:best=(score,A,B,overlap,total)
 if best is None: raise RuntimeError(f"No two-corridor loop candidate; outbound count {len(first)}")
 _,A,B,overlap,total=best
 paths=first
 route=A[0]+list(reversed(B[0]))[1:]
 ways=list(t5.get("properties",{}).get("osm_way_ids",[]));devs=[];hws=[]
 for u,v in zip(east_route,east_route[1:]):
  e=G[u][v];ways.append(e["way"]);devs.append(e["dev"]);hws.append(e["highway"])
 ll=[back.transform(*p) for p in route]
 props={"name":"ÖST Trail 13/14 km reconstructed","status":"validated_reconstruction_candidate","provenance":"organizer raster cross-registered to Trail5 and snapped to OpenStreetMap","distance_km":round(total/1000,3),"osm_way_ids":list(dict.fromkeys(x for x in ways if x))}
 feat={"type":"Feature","properties":props,"geometry":{"type":"LineString","coordinates":[list(x) for x in ll]}}
 Path(a.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+"\n")
 pts="".join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon,lat in ll);Path(a.gpx).write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys route reconstruction"><trk><name>ÖST Trail 13/14 km reconstructed</name><trkseg>'+pts+'</trkseg></trk></gpx>\n')
 qa={"distance_km":round(total/1000,3),"participant_2023_reference_km":13.67,"eastern_loop_km":round(east_total/1000,3),"route_points":len(route),"candidate_paths_considered":len(first),"shared_out_return_m":round(overlap,1),"median_edge_to_raster_m":round(float(np.median(devs)),1),"p95_edge_to_raster_m":round(float(np.percentile(devs,95)),1),"start_finish_gap_m":round(D(route[0],route[-1]),1),"hallamolla_control_m":round(D(A[0][-1],hall),1),"osm_way_count":len(set(x for x in ways if x)),"highway_types":sorted(set(x for x in hws if x)),"map_registration_median_px":reg["reprojection_px"]["median"],"map_registration_p95_px":reg["reprojection_px"]["p95"]}
 Path(a.qa).write_text(json.dumps(qa,indent=2)+"\n");print(json.dumps(qa,indent=2))
if __name__=="__main__":
 main() # The organizer raster contains a western Christinehof loop plus the eastern
 # Hallamölla loop. Build the eastern loop independently, then prepend the
 # already QA-passed Trail5 reconstruction as the western geometry control.
 # Generate candidates by physical length, then score raster fit and overlap.
 first=[]
 for path in nx.shortest_simple_paths(G,s,h,weight="length"):
  L=sum(G[u][v]["length"] for u,v in zip(path,path[1:]))
  C=sum(G[u][v]["weight"] for u,v in zip(path,path[1:]))
  if 3000<=L<=5200:
   E={frozenset((u,v)) for u,v in zip(path,path[1:])}; first.append((path,L,C,E))
  if len(first)>=120: break
 best=None
 for i,A in enumerate(first):
  for B in first[i+1:]:
   overlap=sum(G[tuple(e)[0]][tuple(e)[1]]["length"] for e in A[3]&B[3])
   east=A[1]+B[1]
   if not 7000<=east<=9500: continue
   score=A[2]+B[2]+overlap*70+abs(east-8200)*1.5
   if best is None or score<best[0]: best=(score,A,B,overlap,east)
 if best is None: raise RuntimeError(f"No eastern Hallamolla loop candidate; path count {len(first)}")
 _,A,B,overlap,east_total=best
 east_route=A[0]+list(reversed(B[0]))[1:]
 t5=json.loads(Path(a.trail5).read_text())
 t5ll=t5["geometry"]["coordinates"]
 t5xy=[tr.transform(*p) for p in t5ll]
 # Orient western loop so it ends at the eastern-loop start.
 if D(t5xy[-1],s)>D(t5xy[0],s): t5xy=list(reversed(t5xy))
 route=t5xy + east_route[1:]
 total=sum(D(u,v) for u,v in zip(route,route[1:]))
 ways=[];devs=[];hws=[]
 for u,v in zip(route,route[1:]):
  e=G[u][v];ways.append(e["way"]);devs.append(e["dev"]);hws.append(e["highway"])
 ll=[back.transform(*p) for p in route]
 props={"name":"ÖST Trail 13/14 km reconstructed","status":"validated_reconstruction_candidate","provenance":"organizer raster cross-registered to Trail5 and snapped to OpenStreetMap","distance_km":round(total/1000,3),"osm_way_ids":list(dict.fromkeys(x for x in ways if x))}
 feat={"type":"Feature","properties":props,"geometry":{"type":"LineString","coordinates":[list(x) for x in ll]}}
 Path(a.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+"\n")
 pts="".join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon,lat in ll);Path(a.gpx).write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys route reconstruction"><trk><name>ÖST Trail 13/14 km reconstructed</name><trkseg>'+pts+'</trkseg></trk></gpx>\n')
 qa={"distance_km":round(total/1000,3),"participant_2023_reference_km":13.67,"route_points":len(route),"candidate_paths_considered":len(paths),"shared_out_return_m":round(overlap,1),"median_edge_to_raster_m":round(float(np.median(devs)),1),"p95_edge_to_raster_m":round(float(np.percentile(devs,95)),1),"start_finish_gap_m":round(D(route[0],route[-1]),1),"hallamolla_control_m":round(D(A[0][-1],hall),1),"osm_way_count":len(set(x for x in ways if x)),"highway_types":sorted(set(x for x in hws if x)),"map_registration_median_px":reg["reprojection_px"]["median"],"map_registration_p95_px":reg["reprojection_px"]["p95"]}
 Path(a.qa).write_text(json.dumps(qa,indent=2)+"\n");print(json.dumps(qa,indent=2))
if __name__=="__main__":
 main()
