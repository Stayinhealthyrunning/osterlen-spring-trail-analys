#!/usr/bin/env python3
"""Create a local Trail 21/22 reference route from the organizer-hosted 2019 PDF.

The PDF's visible magenta course line is the geometry source. Public Trace de
Trail 69864 geometry is decoded only transiently to register the PDF map and
preserve traversal order; the Trace coordinate array is never persisted.
"""
from __future__ import annotations

import argparse, json, math
from pathlib import Path

import cv2
import fitz
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree

from analyze_tracedetrail_public_geometry import (
    fetch, datatrace_object, top_properties, decode_geometry, hav,
)

R=6378137.0
ORIGIN=20037508.342789244

def wgs_to_merc(lat,lon):
    x=lon*ORIGIN/180.0
    y=math.log(math.tan((90+lat)*math.pi/360.0))/(math.pi/180.0)
    y=y*ORIGIN/180.0
    return x,y

def merc_to_wgs(x,y):
    lon=x/ORIGIN*180.0
    lat=y/ORIGIN*180.0
    lat=180/math.pi*(2*math.atan(math.exp(lat*math.pi/180.0))-math.pi/2)
    return lat,lon

def render_pdf(path, scale=2.0):
    doc=fitz.open(path)
    page=doc[0]
    pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
    arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
    return arr

def red_route_pixels(rgb):
    h,w=rgb.shape[:2]
    y0,y1=int(h*0.075),int(h*0.725)
    x0,x1=int(w*0.015),int(w*0.985)
    crop=rgb[y0:y1,x0:x1]
    r=crop[:,:,0].astype(np.int16); g=crop[:,:,1].astype(np.int16); b=crop[:,:,2].astype(np.int16)
    mask=((r>145)&(r-g>55)&(r-b>25)&(g<150)).astype(np.uint8)
    # Preserve the thin route while removing isolated text/logo noise.
    n,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
    comps=[]
    for i in range(1,n):
        area=int(stats[i,cv2.CC_STAT_AREA])
        if area>=25:
            comps.append((area,i))
    # Route can be split by anti-aliasing/markers, so retain all substantial
    # magenta components in the map crop rather than one global component.
    keep=np.zeros_like(mask)
    for area,i in comps:
        if area>=25:
            keep[labels==i]=1
    ys,xs=np.nonzero(keep)
    if len(xs)<1000:
        raise RuntimeError(f"Too few route-colour pixels extracted: {len(xs)}")
    return np.column_stack([xs+x0,ys+y0]).astype(float), keep, (x0,y0,x1,y1)

def decode_trace(trace_id):
    html,_=fetch(trace_id)
    props=top_properties(datatrace_object(html))
    _,pts=decode_geometry(props["geometry"])
    return props,pts

def fit_registration(merc, red):
    tree=cKDTree(red)
    xmin,ymin=np.percentile(red,[1],axis=0)[0]
    xmax,ymax=np.percentile(red,[99],axis=0)[0]
    mx=merc[:,0]; my=merc[:,1]
    sx=(xmax-xmin)/(np.percentile(mx,99)-np.percentile(mx,1))
    sy=(ymax-ymin)/(np.percentile(my,99)-np.percentile(my,1))
    tx=xmin-sx*np.percentile(mx,1)
    ty=ymax+sy*np.percentile(my,1)

    sample=merc[::max(1,len(merc)//1000)]
    def project(p,z):
        sx,sy,tx,ty=z
        return np.column_stack([sx*p[:,0]+tx, -sy*p[:,1]+ty])
    def objective(z):
        q=project(sample,z)
        d=tree.query(q,k=1)[0]
        d=np.minimum(d,50.0)
        return float(np.mean(d*d))
    z0=np.array([sx,sy,tx,ty],float)
    bounds=[(sx*.9,sx*1.1),(sy*.9,sy*1.1),(tx-150,tx+150),(ty-150,ty+150)]
    res=minimize(objective,z0,method="Nelder-Mead",options={"maxiter":2500,"xatol":1e-8,"fatol":1e-5})
    z=res.x
    # reject wild unconstrained excursions; fall back to bbox start if needed
    if not (bounds[0][0] <= z[0] <= bounds[0][1] and bounds[1][0] <= z[1] <= bounds[1][1] and bounds[2][0] <= z[2] <= bounds[2][1] and bounds[3][0] <= z[3] <= bounds[3][1]):
        z=z0
    q=project(merc,z)
    dd=tree.query(q,k=1)[0]
    return z,q,dd,tree

def snap_ordered(projected, tree, red, z):
    # Snap each ordered transient route sample to the visible organizer-PDF line.
    # Use every ~10th original point to avoid encoding raster aliasing.
    sx,sy,tx,ty=z
    out=[]
    for i,q in enumerate(projected):
        if i and i%8: continue
        d,idx=tree.query(q,k=1)
        px,py=red[idx]
        mx=(px-tx)/sx
        my=(ty-py)/sy
        lat,lon=merc_to_wgs(mx,my)
        if not out or hav(out[-1],(lat,lon))>2.0:
            out.append((lat,lon))
    # ensure closure from the organizer line near the finish
    if out and hav(out[0],out[-1])<100:
        out[-1]=out[0]
    return out

def length(points):
    return sum(hav(a,b) for a,b in zip(points,points[1:]))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pdf",required=True)
    ap.add_argument("--gpx",required=True)
    ap.add_argument("--geojson",required=True)
    ap.add_argument("--qa",required=True)
    args=ap.parse_args()

    rgb=render_pdf(args.pdf,2.0)
    red,_,crop=red_route_pixels(rgb)
    props,pts=decode_trace(69864)
    merc=np.asarray([wgs_to_merc(p["lat"],p["lon"]) for p in pts])
    z,projected,dd,tree=fit_registration(merc,red)
    snapped=snap_ordered(projected,tree,red,z)
    total=length(snapped)

    Path(args.gpx).parent.mkdir(parents=True,exist_ok=True)
    trk="".join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lat,lon in snapped)
    Path(args.gpx).write_text(
      '<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys organizer-map reconstruction">'
      '<trk><name>ÖST Verkeån Trail 21/22 organizer 2019 map reference</name><trkseg>'+trk+'</trkseg></trk></gpx>\n',
      encoding="utf-8"
    )
    coords=[[lon,lat] for lat,lon in snapped]
    feat={
      "type":"Feature",
      "properties":{
        "name":"ÖST Trail 21/22 organizer-map reference",
        "source_year":2019,
        "geometry_status":"validated_organizer_pdf_reference",
        "not_organizer_gpx":True,
        "distance_km":round(total/1000,3),
      },
      "geometry":{"type":"LineString","coordinates":coords}
    }
    Path(args.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    qa={
      "geometry_status":"validated_organizer_pdf_reference",
      "source_pdf":args.pdf,
      "organizer_pdf_label_km":21.8,
      "organizer_pdf_ascent_m":480,
      "organizer_pdf_descent_m":480,
      "distance_km":round(total/1000,3),
      "point_count":len(snapped),
      "trace_registration_role":"transient registration/order only; no Trace coordinate array persisted",
      "trace_registration_id":69864,
      "registration_pixel_distance":{
        "median":round(float(np.median(dd)),2),
        "p95":round(float(np.percentile(dd,95)),2),
        "max":round(float(np.max(dd)),2),
      },
      "render_size_px":[int(rgb.shape[1]),int(rgb.shape[0])],
      "map_crop_px":list(crop),
      "registration_parameters":{
        "mercator_x_scale":float(z[0]),"mercator_y_scale":float(z[1]),
        "x_translation":float(z[2]),"y_translation":float(z[3])
      },
      "source_policy":"Route positions are snapped to the organizer-hosted PDF's visible course line. Trace geometry is transient calibration evidence only."
    }
    Path(args.qa).write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(qa,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
