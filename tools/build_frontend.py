"""Offline deploy build: existing Engine web exporter plus derived presentation assets."""
from pathlib import Path
import argparse, hashlib, json, math, statistics, subprocess, sys
import xml.etree.ElementTree as ET
from export_engine_web_bundle import dump
ROOT=Path(__file__).resolve().parents[1]
def read(path): return json.loads(path.read_text(encoding="utf-8"))
def hav(a,b):
    p,q=math.radians(a[0]),math.radians(b[0])
    d=math.sin((q-p)/2)**2+math.cos(p)*math.cos(q)*math.sin(math.radians(b[1]-a[1])/2)**2
    return 6371.0088*2*math.asin(min(1,math.sqrt(d)))
def route_asset(path,version,sha,anchors):
    tree=ET.parse(path); pts=[]; distance=0
    for el in tree.iter():
        if el.tag.split("}")[-1] not in ("trkpt","rtept"): continue
        ele=next((x for x in el if x.tag.split("}")[-1]=="ele"),None)
        point=[float(el.attrib["lat"]),float(el.attrib["lon"]),float(ele.text) if ele is not None and ele.text else None]
        if pts: distance+=hav(pts[-1],point)
        pts.append([*point,round(distance,6)])
    assert len(pts)>2
    mapped={"start":0,"finish":distance}; evidence={}
    for key,anchor in anchors.items():
        near=min(pts,key=lambda p:hav(p,[anchor["lat"],anchor["lon"]]))
        offset=hav(near,[anchor["lat"],anchor["lon"]])*1000
        assert offset<=anchor["max_offset_m"],(version,key,offset)
        mapped[key]=near[3]; evidence[key]={**anchor,"offset_m":round(offset,1),"route_distance_km":near[3]}
    # Preserve partial/missing source elevation. Never replace absent points with zero.
    profile=[]
    for i,p in enumerate(pts):
        if profile and p[3]-profile[-1][0]<.05 and i<len(pts)-1: continue
        neighbours=[x[2] for x in pts[max(0,i-3):i+4] if x[2] is not None]
        profile.append([p[3],round(statistics.median(neighbours),1) if p[2] is not None else None])
    return {"payload_sha256":sha,"course_version":version,"points":pts,"full_distance_km":distance,
      "anchors":mapped,"anchor_evidence":evidence,"elevation":profile,
      "elevation_method":"GPX point elevation, median of up to 7 adjacent samples, retained at 50 m; descriptive, not authoritative D+",
      "source":str(path.relative_to(ROOT)),"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
def build(out):
    subprocess.run([sys.executable,str(ROOT/"tools/export_engine_web_bundle.py"),"--output-dir",str(out)],check=True)
    boot=read(out/"bootstrap.json"); manifest=read(out/"manifest.json"); sha=boot["payload_sha256"]
    presentation=read(ROOT/"config/frontend-presentation.json")
    boot["event"]["product_title"]="ÖST Splits"
    boot["presentation"]=presentation["families"]; boot["default_race"]=presentation["default_race"]
    boot["cancelled_years"]=read(ROOT/"config/event.json")["cancelled_years"]
    cfg={v["course_version_id"]:v for v in read(ROOT/"config/course-versions.json")["versions"]}
    manifest["routes"]={}
    for key,course in boot["courses"].items():
        course["description"]=cfg[key].get("notes")
        assets=course["assets"]
        if not assets.get("route_source"): continue
        route=route_asset(ROOT/assets["route_source"],key,sha,presentation["route_anchors"].get(key,{}))
        route["provenance_label"]="Arrangörs-GPX" if assets["official_gpx"] else "Rekonstruerad bana"
        rel=f"courses/{key}/route.json"
        manifest["routes"][key]={**dump(out/rel,route),"path":rel}
        assets["route"]=rel
    history=[]
    for key,meta in manifest["races"].items():
        doc=read(out/meta["path"]); race=doc["race"]; records=race["records"]
        finish=[r["finish_seconds"] for r in records if r["status"]=="FINISHED" and r["finish_seconds"] and r["finish_seconds"]>0]
        row={k:race[k] for k in ("race_key","race_family","year","course_version","capabilities")}
        row.update(records=len(records),finished=len(finish),dnf=sum(r["status"]=="DNF" for r in records),
           median=statistics.median(finish) if len(finish)>=5 else None,best=min(finish) if finish else None,
           sex_coverage=sum(r["sex"] is not None for r in records),women=sum(r["sex"]=="F" for r in records))
        history.append(row)
    manifest["history"]={**dump(out/"history.json",{"payload_sha256":sha,"editions":history}),"path":"history.json"}
    manifest["bootstrap"]={**dump(out/"bootstrap.json",boot),"path":"bootstrap.json"}
    dump(out/"manifest.json",manifest)
    return manifest
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--output-dir",default="docs/data");args=ap.parse_args()
    dest=Path(args.output_dir)
    build(dest if dest.is_absolute() else ROOT/dest)

