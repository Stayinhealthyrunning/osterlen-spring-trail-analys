#!/usr/bin/env python3
import json, math, argparse
from pathlib import Path
import cv2, numpy as np
from pyproj import Transformer

def hav(a,b):
    R=6371000.; p1,p2=map(math.radians,(a[1],b[1])); dp=math.radians(b[1]-a[1]); dl=math.radians(b[0]-a[0])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))

def component_pixels(image, threshold, seed_bbox):
    img=cv2.imread(image,cv2.IMREAD_GRAYSCALE)
    mask=(img<threshold).astype(np.uint8)
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask,8)
    sx,sy,sw,sh=seed_bbox
    best=None
    for i in range(1,n):
        x,y,w,h,area=map(int,stats[i])
        overlap=max(0,min(x+w,sx+sw)-max(x,sx))*max(0,min(y+h,sy+sh)-max(y,sy))
        if overlap and (best is None or overlap>best[0]): best=(overlap,i)
    if not best: raise SystemExit("route component not found")
    ys,xs=np.where(lab==best[1])
    return list(zip(xs.tolist(),ys.tolist()))

def pix_to_lonlat(x,y,frame,sw,ne,tr):
    fx=(x-frame["left"])/(frame["right"]-frame["left"])
    fy=(y-frame["top"])/(frame["bottom"]-frame["top"])
    E=sw[0]+fx*(ne[0]-sw[0]); N=ne[1]-fy*(ne[1]-sw[1])
    lon,lat=tr.transform(E,N); return lon,lat

def local_xy(lon,lat,lat0):
    return lon*111320*math.cos(math.radians(lat0)),lat*110540

def segdist(p,a,b):
    vx,vy=b[0]-a[0],b[1]-a[1]; wx,wy=p[0]-a[0],p[1]-a[1]
    q=(wx*vx+wy*vy)/(vx*vx+vy*vy) if vx or vy else 0; q=max(0,min(1,q))
    return math.hypot(p[0]-(a[0]+q*vx),p[1]-(a[1]+q*vy))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--image",required=True); ap.add_argument("--network",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    # Native 1100x777 organizer image; frame scaled from the quantitatively validated prototype.
    frame={"left":25.3,"right":1074.7,"top":49.5,"bottom":694.8}
    sw=(432733.,6173751.); ne=(437965.,6176791.)
    tr=Transformer.from_crs(3006,4326,always_xy=True)
    pix=component_pixels(a.image,110,(246,257,269,294))
    # Thin the source cloud spatially by taking every fourth pixel; distance is to cloud, not inferred route order.
    ll=[pix_to_lonlat(x,y,frame,sw,ne,tr) for x,y in pix[::4]]
    lat0=sum(p[1] for p in ll)/len(ll); cloud=[local_xy(*p,lat0) for p in ll]
    net=json.loads(Path(a.network).read_text())
    ranked=[]
    for f in net["features"]:
        if (f.get("geometry") or {}).get("type")!="LineString": continue
        c=f["geometry"]["coordinates"]; xy=[local_xy(*p,lat0) for p in c]
        samples=[]
        for A,B in zip(xy,xy[1:]):
            L=math.hypot(B[0]-A[0],B[1]-A[1]); n=max(1,int(L/20))
            samples += [(A[0]+(B[0]-A[0])*i/n,A[1]+(B[1]-A[1])*i/n) for i in range(n+1)]
        ds=[min(math.hypot(s[0]-q[0],s[1]-q[1]) for q in cloud) for s in samples]
        pr=f.get("properties") or {}
        length=sum(hav(x,y) for x,y in zip(c,c[1:]))
        ranked.append({"osm_way_id":pr.get("osm_way_id") or pr.get("id"),"highway":pr.get("highway"),"name":pr.get("name"),
          "length_m":round(length,1),"median_raster_distance_m":round(float(np.median(ds)),1),"p95_raster_distance_m":round(float(np.percentile(ds,95)),1),
          "coordinates":c})
    ranked.sort(key=lambda z:(z["median_raster_distance_m"],z["p95_raster_distance_m"]))
    out={"method":"OSM way proximity to georeferenced organizer raster dark-route component","route_component_pixels":len(pix),
         "map_frame_px":frame,"sweref_controls":{"sw":sw,"ne":ne},"top_ways":ranked[:80]}
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps([{k:x[k] for k in ("osm_way_id","highway","name","length_m","median_raster_distance_m","p95_raster_distance_m")} for x in ranked[:25]],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
