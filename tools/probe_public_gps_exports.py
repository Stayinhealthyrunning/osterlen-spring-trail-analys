#!/usr/bin/env python3
import json, pathlib, urllib.request, urllib.error
OUT=pathlib.Path("data/source/gpx/public-probes"); OUT.mkdir(parents=True,exist_ok=True)
REP=pathlib.Path("research/public-gps-probe"); REP.mkdir(parents=True,exist_ok=True)
targets=[
 ("topogps-hallamolla-43794","https://api.topo-gps.com/route/fetch?format=gpx&id=43794","gpx"),
 ("strava-christian-ost60-2023","https://www.strava.com/activities/8895037345/export_gpx","gpx"),
 ("strava-christian-ost60-2023-tcx","https://www.strava.com/activities/8895037345/export_tcx","tcx"),
 ("wikiloc-alunbruket-hallamolla-104740116","https://www.wikiloc.com/wikiloc/download.do?event=file&id=104740116","gpx"),
 ("wikiloc-christinehof-1767530","https://www.wikiloc.com/wikiloc/download.do?event=file&id=1767530","gpx"),
 ("wikiloc-hallamollaleden-52431996","https://www.wikiloc.com/wikiloc/download.do?event=file&id=52431996","gpx"),
]
rows=[]
for name,url,ext in targets:
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 route-research/1.0"})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:
   data=r.read(); final=r.geturl(); ct=r.headers.get("Content-Type","")
   is_gps=(b"<gpx" in data[:5000].lower() or b"<trainingcenterdatabase" in data[:5000].lower())
   row={"name":name,"requested_url":url,"status":r.status,"final_url":final,"content_type":ct,"bytes":len(data),"gps_xml":is_gps}
   if is_gps:
    (OUT/f"{name}.{ext}").write_bytes(data)
   else:
    (REP/f"{name}.response-head.txt").write_bytes(data[:12000])
   rows.append(row)
 except urllib.error.HTTPError as e:
  body=e.read(12000)
  rows.append({"name":name,"requested_url":url,"status":e.code,"final_url":e.geturl(),"content_type":e.headers.get("Content-Type",""),"bytes":len(body),"gps_xml":False,"error":"HTTPError"})
  (REP/f"{name}.response-head.txt").write_bytes(body)
 except Exception as e:
  rows.append({"name":name,"requested_url":url,"error":type(e).__name__+": "+str(e)})
(REP/"probe-results.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(rows,indent=2,ensure_ascii=False))
