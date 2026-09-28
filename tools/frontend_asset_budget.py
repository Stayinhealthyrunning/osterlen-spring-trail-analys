"""Measure actual frontend source artifacts. All first-party JS is conservatively charged initially."""
import gzip,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sizes(paths):
 raw=[p.read_bytes() for p in paths]
 return {"raw_bytes":sum(map(len,raw)),"gzip_bytes":sum(len(gzip.compress(b,compresslevel=9,mtime=0)) for b in raw)}
def measure(root=ROOT):
 docs=root/"docs";limits=json.loads((root/"config/frontend-performance-budget.json").read_text(encoding="utf-8"))["frontend_runtime_provisional"]
 report={"html":sizes([docs/"index.html"]),"css":sizes(list((docs/"assets").glob("*.css"))),"javascript":sizes(list((docs/"assets").glob("*.js"))),"lazy_vendor":sizes(list((docs/"vendor").rglob("*.js"))+list((docs/"vendor").rglob("*.css")))}
 report["limits"]=limits
 return report
def violations(report,critical_data_bytes):
 limits=report["limits"]; errors=[]
 for key,limit in (("html","initial_html_gzip_max_bytes"),("css","initial_css_gzip_max_bytes"),("javascript","initial_javascript_gzip_max_bytes")):
  if report[key]["gzip_bytes"]>limits[limit]:errors.append(key+" exceeds "+limit)
 critical=sum(report[k]["gzip_bytes"] for k in ("html","css","javascript"))+critical_data_bytes
 report["critical_initial_transfer_gzip_bytes"]=critical
 if critical>limits["critical_initial_transfer_gzip_max_bytes"]:errors.append("critical initial transfer exceeds budget")
 return errors

