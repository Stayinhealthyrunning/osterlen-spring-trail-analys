import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class EngineDeliveryShardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="ost-delivery-test-")
        cls.out=Path(cls.tmp.name)/"engine-data"
        cls.report=Path(cls.tmp.name)/"report.json"
        run=subprocess.run([
            sys.executable,str(ROOT/"tools/build_engine_delivery_shards.py"),
            "--output-dir",str(cls.out),"--report",str(cls.report)
        ],cwd=ROOT,text=True,capture_output=True)
        if run.returncode:
            raise AssertionError(run.stderr or run.stdout)
        cls.summary=json.loads(cls.report.read_text(encoding="utf-8"))
        cls.bootstrap=json.loads((cls.out/"bootstrap.json").read_text(encoding="utf-8"))
        cls.manifest=json.loads((cls.out/"manifest.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_data_accounted_for(self):
        self.assertEqual(self.summary["race_count"],34)
        self.assertEqual(self.summary["totals"]["records"],9871)
        self.assertEqual(self.summary["totals"]["splits"],6123)
        self.assertEqual(self.summary["totals"]["teams"],300)
        self.assertEqual(self.summary["totals"]["team_members"],599)

    def test_bootstrap_contains_no_result_rows(self):
        self.assertNotIn("records",self.bootstrap)
        self.assertEqual(len(self.bootstrap["race_catalog"]),34)

    def test_exactly_one_shard_per_held_race(self):
        files=list((self.out/"races").glob("*.json"))
        self.assertEqual(len(files),34)
        self.assertEqual(set(self.manifest["races"]),{p.stem for p in files})

    def test_budget_is_green(self):
        self.assertEqual(self.summary["budget_failures"],[])
        budget=json.loads((ROOT/"config/frontend-performance-budget.json").read_text(encoding="utf-8"))
        b=budget["data_delivery"]
        self.assertLessEqual(self.summary["bootstrap"]["gzip_bytes"],b["bootstrap_gzip_max_bytes"])
        self.assertLessEqual(self.summary["max_selected_race_gzip_bytes"],b["selected_race_gzip_max_bytes"])

    def test_route_geometry_is_not_embedded_in_race_bundle(self):
        race=json.loads((self.out/"races"/"ost-2025-ultra60.json").read_text(encoding="utf-8"))
        self.assertNotIn("route",race)
        self.assertNotIn("elevation",race)
        self.assertTrue(race["race"]["capabilities"]["replay"])


if __name__=="__main__":
    unittest.main()
