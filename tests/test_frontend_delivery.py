import gzip,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from frontend_asset_budget import measure,violations
class FrontendDeliveryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory()
  cls.out=Path(cls.tmp.name)
  run=subprocess.run([sys.executable,str(ROOT/"tools/build_frontend.py"),"--output-dir",str(cls.out)],capture_output=True,text=True)
  if run.returncode:raise AssertionError(run.stderr)
  cls.boot=json.loads((cls.out/"bootstrap.json").read_text(encoding="utf-8"))
  cls.manifest=json.loads((cls.out/"manifest.json").read_text(encoding="utf-8"))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_every_browser_document_has_same_generation(self):
  for p in self.out.rglob("*.json"):
   self.assertEqual(json.loads(p.read_text(encoding="utf-8")).get("payload_sha256"),self.boot["payload_sha256"],p)
 def test_routes_only_explicit_local_entitlements(self):
  self.assertEqual(set(self.manifest["routes"]),{"ultra60-2024","ultra60-2025-2026","trail5-current-reference"})
  for key,meta in self.manifest["routes"].items():
   route=json.loads((self.out/meta["path"]).read_text(encoding="utf-8"))
   self.assertEqual(route["course_version"],key)
   self.assertEqual(hashlib.sha256((ROOT/route["source"]).read_bytes()).hexdigest(),route["source_sha256"])
   self.assertGreater(route["full_distance_km"],0)
   self.assertTrue(all(a[3]<=b[3] for a,b in zip(route["points"],route["points"][1:])))
 def test_missing_gpx_elevation_remains_missing(self):
  route=json.loads((self.out/"courses/ultra60-2024/route.json").read_text(encoding="utf-8"))
  self.assertTrue(any(p[2] is None for p in route["points"]))
  self.assertTrue(any(p[1] is None for p in route["elevation"]))
  self.assertTrue(any(p[1] is not None for p in route["elevation"]))
 def test_budget_and_failure_path(self):
  report=measure();data=self.manifest["bootstrap"]["gzip_bytes"]+max(x["gzip_bytes"] for x in self.manifest["races"].values())
  self.assertEqual(violations(report,data),[])
  report["javascript"]["gzip_bytes"]=10**7
  self.assertTrue(violations(report,data))
 def test_source_archives_unchanged(self):
  expected=json.loads((ROOT/"config/frontend-source-lock.json").read_text(encoding="utf-8"))
  for rel,digest in expected.items():self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),digest)
if __name__=="__main__":unittest.main()

