#!/usr/bin/env python3
"""Convert persisted organizer-raster pixel vertices to SWEREF99TM/WGS84-like intermediate GeoJSON.

The affine transform is exact with respect to supplied raster frame/control values.
WGS84 conversion is intentionally left to a CRS-capable downstream step; this tool
never invents coordinates when pyproj is unavailable.
"""
import argparse, json, math
from pathlib import Path

def affine(px, py, frame, sw, ne):
    fx=(px-frame["left"])/(frame["right"]-frame["left"])
    fy=(py-frame["top"])/(frame["bottom"]-frame["top"])
    e=sw["E"]+fx*(ne["E"]-sw["E"])
    n=ne["N"]-fy*(ne["N"]-sw["N"])
    return [e,n]

def length(coords):
    return sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(coords,coords[1:]))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("trace_json")
    p.add_argument("output_geojson")
    a=p.parse_args()
    src=json.loads(Path(a.trace_json).read_text())
    coords=[affine(x,y,src["map_frame_px"],src["sweref99tm_control"]["southwest"],src["sweref99tm_control"]["northeast"]) for x,y in src["pixel_vertices"]]
    out={"type":"Feature","properties":{
        "crs":"EPSG:3006",
        "provenance":"derived_from_georeferenced_organizer_map",
        "source_image":src["source_image"],
        "vertex_count":len(coords),
        "planar_length_km":round(length(coords)/1000,6)
    },"geometry":{"type":"LineString","coordinates":coords}}
    Path(a.output_geojson).write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out["properties"],indent=2))

if __name__=="__main__": main()
