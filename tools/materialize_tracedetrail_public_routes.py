#!/usr/bin/env python3
"""Materialize ÖST route references from Trace de Trail public map geometry.

The public route page exposes dataTrace.geometry so browsers can draw the map.
This does not call or bypass the login-protected GPX export. Materialized files
are derived route references with explicit provenance, never organizer GPX.

Trail22 trace 7897 is deliberately excluded: its Trace date is 2016, not 2018.
Trail14 2026 is the documented provisional Hallamölla splice of Trail22 2022.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,xml.etree.ElementTree as ET
from analyze_tracedetrail_public_geometry import geometry_record,waypoint_index,hav

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/course-versions.json").read_text(encoding="utf-8"))
VERSIONS={x["course_version_id"]:x for x in CFG["versions"]}
OUT=ROOT/"routes"/"ost"; NS="http://www.topografix.com/GPX/1/1"
ROUTES=[
 ("ultra60-2018","ultra60",2018,43970,[]),
 ("ultra60-2019","ultra60",2019,69381,[]),
 ("ultra60-2022-2023","ultra60",2022,172147,[(2023,203147)]),
 ("trail22-2019","trail22",2019,69864,[]),
 ("trail22-2022-2024","trail22",2022,165617,[(2023,203146),(2024,237224)]),
 ("trail22-2025-2026","trail22",2026,322314,[(2025,280053)]),
]

def cumulative(pts):
    out=[0.0]
    for a,b in zip(pts,pts[1:]):
        out.append(out[-1]+hav((a["lat"],a["lon"]),(b["lat"],b["lon"])))
    return out

def point_hash(pts):
    s=";".join(f'{p["lat"]:.7f},{p["lon"]:.7f},{p.get("y")}' for p in pts)
    return hashlib.sha256(s.encode()).hexdigest()

def gpx(name,url,pts,desc):
    ET.register_namespace("",NS)
    root=ET.Element(f"{{{NS}}}gpx",{"version":"1.1","creator":"ÖST Analys derived route materializer"})
    meta=ET.SubElement(root,f"{{{NS}}}metadata")
    ET.SubElement(meta,f"{{{NS}}}name").text=name
    ET.SubElement(meta,f"{{{NS}}}desc").text=desc
    link=ET.SubElement(meta,f"{{{NS}}}link",{"href":url})
    ET.SubElement(link,f"{{{NS}}}text").text="Trace de Trail public map page"
    seg=ET.SubElement(ET.SubElement(root,f"{{{NS}}}trk"),f"{{{NS}}}trkseg")
    for p in pts:
        n=ET.SubElement(seg,f"{{{NS}}}trkpt",{"lat":f'{p["lat"]:.7f}',"lon":f'{p["lon"]:.7f}'})
        if isinstance(p.get("y"),(int,float)) and math.isfinite(float(p["y"])):
            ET.SubElement(n,f"{{{NS}}}ele").text=f'{float(p["y"]):.1f}'
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def write_route(version,source,pts,label,status,extra=None):
    d=OUT/version; d.mkdir(parents=True,exist_ok=True)
    desc="Derived from dataTrace.geometry embedded in the public Trace de Trail map; not an organizer-direct or authenticated-export GPX."
    (d/"route.gpx").write_bytes(gpx(version,source["source_url"],pts,desc))
    dist=cumulative(pts)[-1]/1000
    prov={
      "schema_version":1,"course_version":version,"materialized_at":datetime.now(timezone.utc).isoformat(),
      "geometry_status":status,"not_an_organizer_gpx":True,"not_a_trace_gpx_export":True,
      "source_page":source["source_url"],"trace_id":source["trace_id"],
      "source_date_compet":source["source_date_compet"],"source_year_matches_manifest":source["source_year_matches_manifest"],
      "public_geometry_sha256":source["geometry_sha256"],"materialized_point_sha256":point_hash(pts),
      "point_count":len(pts),"distance_km":round(dist,3),
      "method":"WGS84 points decoded from publicly embedded dataTrace.geometry; no login-protected endpoint used.",
      "publication_label":label,
      "limitations":["Derived local representation of public map geometry, not organizer-direct GPX bytes.",
                     "Course identity is gated by source-date/hash evidence in config/course-versions.json."]
    }
    if extra: prov.update(extra)
    (d/"provenance.json").write_text(json.dumps(prov,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return prov

def verified(version,family,year,trace,peers,wp):
    src=geometry_record({"family":family,"year":year,"trace_id":trace},wp)
    if not src["source_year_matches_manifest"]: raise RuntimeError(f"source year mismatch {trace}")
    expected=VERSIONS[version].get("derived_path_distance_km")
    if expected is not None and abs(float(expected)-float(src["path_distance_km"]))>.08:
        raise RuntimeError(f"distance mismatch {version}: {src['path_distance_km']} vs {expected}")
    for py,pt in peers:
        peer=geometry_record({"family":family,"year":py,"trace_id":pt},wp)
        if peer["geometry_sha256"]!=src["geometry_sha256"]:
            raise RuntimeError(f"exact peer mismatch {trace}/{pt}")
    return src

def trail14_splice(base):
    pts=base["points"]; c=cumulative(pts); total=c[-1]; found=[]
    for i,p in enumerate(pts):
        if not 8200<=c[i]<=9150: continue
        for j in range(i+1,len(pts)):
            rem=total-c[j]; loop=c[j]-c[i]
            if not 4300<=rem<=5250 or not 7800<=loop<=8750: continue
            sep=hav((p["lat"],p["lon"]),(pts[j]["lat"],pts[j]["lon"]))
            if sep<=15:
                score=abs(c[i]-8687)+abs(rem-4784)+10*sep
                found.append((score,i,j,sep,loop,rem))
    if not found: raise RuntimeError("Hallamölla splice not found")
    _,i,j,sep,loop,rem=min(found); out=pts[:i+1]+pts[j:]; dist=cumulative(out)[-1]/1000
    if not 13.35<=dist<=13.60: raise RuntimeError(f"bad Trail14 distance {dist:.3f}")
    return out,{"base_course_version":"trail22-2022-2024","base_trace_id":base["trace_id"],
      "recipe":"remove eastern loop between two nearly coincident Hallamölla passages",
      "splice":{"first_passage_km":round(c[i]/1000,3),"second_passage_km":round(c[j]/1000,3),
                "removed_loop_km":round(loop/1000,3),"splice_separation_m":round(sep,2),
                "remaining_km":round(rem/1000,3),"materialized_distance_km":round(dist,3)},
      "limitations":["Provisional reconstructed working reference; not organizer or participant GPX.",
                     "Supported by organizer raster topology and the verified 2023 participant Hallamölla/distance evidence."]}

def main():
    wp=waypoint_index(); report=[]; srcs={}
    for version,family,year,trace,peers in ROUTES:
        src=verified(version,family,year,trace,peers,wp); srcs[version]=src
        p=write_route(version,src,src["points"],"Publik banreferens · Trace de Trail",
                      "derived_from_public_trace_map_geometry",{"corroborating_exact_trace_ids":[x[1] for x in peers]})
        report.append({k:p[k] for k in ("course_version","trace_id","distance_km","point_count","publication_label")})
        print(version,p["distance_km"],"km")
    pts,extra=trail14_splice(srcs["trail22-2022-2024"])
    p=write_route("trail14-current-reference",srcs["trail22-2022-2024"],pts,
                  "Rekonstruerad bana · provisorisk","provisional_hallamolla_splice_reference",extra)
    report.append({k:p[k] for k in ("course_version","trace_id","distance_km","point_count","publication_label")})
    (ROOT/"reports"/"materialized-public-route-assets.json").write_text(json.dumps({
      "schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),
      "policy":"Derived route references from publicly embedded map geometry; login-protected GPX export is not used.",
      "routes":report,
      "excluded":[
        {"family":"trail22","year":2018,"trace_id":7897,"reason":"Trace dateCompet is 2016; provenance mismatch."},
        {"family":"trail14","years":"2018-2025","reason":"No verified year-specific geometry."},
        {"family":"trail5","years":"2018-2025","reason":"No verified year-specific geometry."}
      ]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("materialized",len(report),"routes")

if __name__=="__main__": main()
