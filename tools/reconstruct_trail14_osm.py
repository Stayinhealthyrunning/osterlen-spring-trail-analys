#!/usr/bin/env python3
import argparse,json,math
from pathlib import Path
import cv2,numpy as np,networkx as nx
from scipy.spatial import cKDTree
from pyproj import Transformer

def D(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])

def component(imgpath):
 im=cv2.imread(imgpath,0); mask=(im<90).astype(np.uint8)
 n,lab,stats,_=cv2.connectedComponentsWithStats(mask,8)
 best=max((i for i in range(1,n) if stats[i,0]<950 and 150<stats[i,1]<580),key=lambda i:stats[i,4])
 ys,xs=np.where(lab==best); return np.column_stack([xs,ys]).astype(float)

def main():
 ap=argparse.ArgumentParser()
 for x in ("image","network","registration","relations","trail5","geojson","gpx","qa"): ap.add_argument("--"+x,required=True)
 a=ap.parse_args()
 pix=component(a.image); reg=json.loads(Path(a.registration).read_text()); H=np.array(reg["trail14_to_trail5_homography"])
 q=np.c_[pix,np.ones(len(pix))]@H.T; p5=q[:,:2]/q[:,2,None]
 left,right,top,bottom=25.3,1074.7,49.5,694.7; sw=(432733.,6173751.); ne=(437965.,6176791.)
 xy=np.column_stack([sw[0]+(p5[:,0]-left)/(right-left)*(ne[0]-sw[0])-198.3,
                     ne[1]-(p5[:,1]-top)/(bottom-top)*(ne[1]-sw[1])+111.9])
 cloud=cKDTree(xy[::3])
 tr=Transformer.from_crs(4326,3006,always_xy=True); back=Transformer.from_crs(3006,4326,always_xy=True)
 rels=json.loads(Path(a.relations).read_text()); skane=set(); backset=set()
 for r in rels:
  name=(r.get("tags",{}).get("name") or "").lower()
  target=skane if ("skåneleden" in name or "skaneleden" in name) else backset if "backaleden" in name else None
  if target is not None: target.update(m["ref"] for m in r.get("members",[]) if m.get("type")=="way")
 net=json.loads(Path(a.network).read_text()); G=nx.Graph()
 for f in net["features"]:
  pr=f.get("properties",{}); wid=pr.get("osm_way_id"); pts=[tr.transform(*z) for z in f["geometry"]["coordinates"]]
  for u,v in zip(pts,pts[1:]):
   L=D(u,v)
   if not L: continue
   samples=[(u[0]+(v[0]-u[0])*t,u[1]+(v[1]-u[1])*t) for t in (0.0,0.25,0.5,0.75,1.0)]
   sdev=[float(cloud.query(p)[0]) for p in samples]
   dev=float(np.percentile(sdev,80))
   fit=L*(1+(min(dev,300)/32)**2)
   # Organizer raster remains primary; named hiking relations are independent
   # corridor evidence. They can improve a close candidate but never override
   # a gross raster disagreement.
   relation_factor=0.72 if wid in skane else 0.82 if wid in backset else 1.0
   if dev>180: relation_factor=max(relation_factor,1.35)
   G.add_edge(u,v,length=L,weight=fit*relation_factor,dev=dev,way=wid,highway=pr.get("highway"),skane=wid in skane,back=wid in backset)
 nodes=list(G.nodes); nt=cKDTree(nodes); castle=(434707.,6175169.); hall=tr.transform(14.01780,55.70819)
 s=nodes[int(nt.query(castle)[1])]; h=nodes[int(nt.query(hall)[1])]
 # Alunbruket is a mandatory named corridor in both organizer evidence and
 # Hallamöllaleden. Use the OSM/local-map vicinity as a topology gate rather
 # than permitting arbitrary Christinehof-Hallamölla shortcuts.
 alun=tr.transform(14.0032,55.7049)
 an=nodes[int(nt.query(alun)[1])]
 # Current organizer evidence constrains the eastern loop to Skåneleden
 # outbound and Backaleden return, through Alunbruket and Hallamölla.
 def ep(P): return [(u,v,G[u][v]) for u,v in zip(P,P[1:])]
 def st(P):
  ee=ep(P); return {"length":sum(e["length"] for _,_,e in ee),"cost":sum(e["weight"] for _,_,e in ee),
   "skane":sum(e["length"] for _,_,e in ee if e["skane"]),"back":sum(e["length"] for _,_,e in ee if e["back"]),
   "devs":[e["dev"] for _,_,e in ee]}
 def candidates(u,v,mode,k):
  def w(a,b,e):
   base=e["weight"]
   if mode=="skane": return base*(0.18 if e["skane"] else 1.8 if e["back"] else 1.0)
   if mode=="back": return base*(0.18 if e["back"] else 1.8 if e["skane"] else 1.0)
   return base
  out=[]
  for P in nx.shortest_simple_paths(G,u,v,weight=w):
   z=st(P); unsupported=sum(e["length"] for _,_,e in ep(P) if e["dev"]>180 and not(e["skane"] or e["back"]))
   if unsupported<=250: out.append((P,z))
   if len(out)>=k: break
  return out
 approaches=candidates(s,an,"neutral",20); skpaths=candidates(an,h,"skane",60)
 backpaths=candidates(h,an,"back",60); returns=candidates(an,s,"neutral",20)
 pareto=[]; best=None
 for A,sa in approaches[:8]:
  for B,sb in skpaths[:25]:
   for C,sc in backpaths[:25]:
    for D,sd in returns[:8]:
     east_route=A+B[1:]+C[1:]+D[1:]; east=sa["length"]+sb["length"]+sc["length"]+sd["length"]
     if not 7000<=east<=10000 or sb["skane"]<1000 or sc["back"]<1000: continue
     edges=[frozenset((u,v)) for u,v in zip(east_route,east_route[1:])]
     overlap=sum(G[tuple(e)[0]][tuple(e)[1]]["length"] for e in set(edges) if edges.count(e)>1)
     devs=sa["devs"]+sb["devs"]+sc["devs"]+sd["devs"]; p95=float(np.percentile(devs,95))
     score=sa["cost"]+sb["cost"]+sc["cost"]+sd["cost"]+overlap*250+p95*200
     row={"east_km":round(east/1000,3),"overlap_m":round(overlap,1),"skane_out_m":round(sb["skane"],1),
      "back_return_m":round(sc["back"],1),"p95_raster_m":round(p95,1),"score":round(score,1)}
     pareto.append(row)
     if best is None or score<best[0]: best=(score,east_route,overlap,east,row)
 if best is None:
  Path(a.qa).with_name("candidate-frontier.json").write_text(json.dumps(sorted(pareto,key=lambda x:x["score"])[:1000],indent=2)+"\n")
  raise RuntimeError("No Skaneleden-out/Backaleden-return candidate satisfies topology gates")
 _,east_route,overlap,east_total,bestrow=best
 # Western loop comes from the independently QA-passed Trail5 reconstruction; final serialized calibration run.
 t5=json.loads(Path(a.trail5).read_text()); t5ll=t5["geometry"]["coordinates"]; t5xy=[tr.transform(*p) for p in t5ll]
 if D(t5xy[-1],s)>D(t5xy[0],s): t5xy=list(reversed(t5xy))
 join=D(t5xy[-1],s); route=t5xy + east_route[1:]
 t5m=float(t5["properties"]["distance_km"])*1000; total=t5m+east_total
 ways=list(t5.get("properties",{}).get("osm_way_ids",[])); devs=[]; hws=[]
 for u,v in zip(east_route,east_route[1:]):
  e=G[u][v]; ways.append(e["way"]);devs.append(e["dev"]);hws.append(e["highway"])
 ll=[back.transform(*p) for p in route]
 props={"name":"ÖST Trail 13/14 km reconstructed","status":"validated_reconstruction_candidate","provenance":"organizer raster + QA-passed western Trail5 + OSM","distance_km":round(total/1000,3),"osm_way_ids":list(dict.fromkeys(x for x in ways if x))}
 feat={"type":"Feature","properties":props,"geometry":{"type":"LineString","coordinates":[list(x) for x in ll]}}
 Path(a.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+"\n")
 pts="".join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon,lat in ll)
 Path(a.gpx).write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys route reconstruction"><trk><name>ÖST Trail 13/14 km reconstructed</name><trkseg>'+pts+'</trkseg></trk></gpx>\n')
 qa={"distance_km":round(total/1000,3),"participant_2023_reference_km":13.67,"western_trail5_km":round(t5m/1000,3),"eastern_loop_km":round(east_total/1000,3),"route_points":len(route),"candidate_paths_considered":len(first),"shared_out_return_m":round(overlap,1),"median_edge_to_raster_m":round(float(np.median(devs)),1),"p95_edge_to_raster_m":round(float(np.percentile(devs,95)),1),"start_finish_gap_m":round(D(route[0],route[-1]),1),"western_eastern_join_m":round(join,1),"hallamolla_control_m":round(min(D(p,hall) for p in east_route),1),"skane_out_m":bestrow["skane_out_m"],"back_return_m":bestrow["back_return_m"],"osm_way_count":len(set(x for x in ways if x)),"highway_types":sorted(set(x for x in hws if x)),"far_raster_way_ids":list(dict.fromkeys(w for w,d in zip(ways[-len(devs):],devs) if w and d>150)),"max_edge_to_raster_m":round(float(np.max(devs)),1),"map_registration_median_px":reg["reprojection_px"]["median"],"map_registration_p95_px":reg["reprojection_px"]["p95"]}
 qa["candidate_pair_count"]=len(pareto)
 Path(a.qa).write_text(json.dumps(qa,indent=2)+"\n")
 frontier=sorted(pareto,key=lambda x:x["score"])[:500]
 Path(a.qa).with_name("candidate-frontier.json").write_text(json.dumps(frontier,indent=2)+"\n")
 print(json.dumps(qa,indent=2))
if __name__=="__main__":
 main()
