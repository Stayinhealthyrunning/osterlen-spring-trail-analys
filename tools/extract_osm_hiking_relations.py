#!/usr/bin/env python3
import xml.etree.ElementTree as ET,json,sys
root=ET.parse(sys.argv[1]).getroot()
out=[]
for r in root.findall("relation"):
 tags={t.attrib["k"]:t.attrib["v"] for t in r.findall("tag")}
 if tags.get("route") in ("hiking","foot") or any(x in (tags.get("name","").lower()) for x in ("hallam","fiskab","skåne","skane")):
  out.append({"id":int(r.attrib["id"]),"tags":tags,"members":[{"type":m.attrib["type"],"ref":int(m.attrib["ref"]),"role":m.attrib.get("role","")} for m in r.findall("member")]})
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False,indent=2)
print(json.dumps([{"id":x["id"],"name":x["tags"].get("name"),"route":x["tags"].get("route"),"members":len(x["members"])} for x in out],ensure_ascii=False,indent=2))
