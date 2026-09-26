import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RouteElevationEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace = json.loads((ROOT / "reports" / "tracedetrail-public-geometry-analysis.json").read_text(encoding="utf-8"))
        cls.evidence = json.loads((ROOT / "reports" / "route-elevation-evidence.json").read_text(encoding="utf-8"))

    def test_all_trace_routes_are_represented(self):
        source = {(r["family"], r["year"], int(r["trace_id"])): r for r in self.trace["routes"]}
        derived = {(r["family"], r["year"], int(r["trace_id"])): r for r in self.evidence["trace_routes"]}
        self.assertEqual(set(source), set(derived))

    def test_trace_elevation_summaries_match_source_report(self):
        source = {(r["family"], r["year"], int(r["trace_id"])): r for r in self.trace["routes"]}
        for r in self.evidence["trace_routes"]:
            s = source[(r["family"], r["year"], int(r["trace_id"]))]
            self.assertEqual(r["profile_sample_count"], s.get("source_x_count"))
            self.assertEqual(r["profile_elevation_min_m"], s.get("source_y_min"))
            self.assertEqual(r["profile_elevation_max_m"], s.get("source_y_max"))
            self.assertEqual(r["trace_cumulative_ascent_m"], s.get("source_dp_last"))
            self.assertEqual(r["trace_cumulative_descent_m"], s.get("source_dn_last"))

    def test_no_coordinates_are_persisted_in_elevation_evidence(self):
        text = json.dumps(self.evidence)
        self.assertNotIn('"lat"', text)
        self.assertNotIn('"lon"', text)

    def test_2024_missing_gpx_elevation_has_trace_fallback_evidence(self):
        route = next(r for r in self.evidence["trace_routes"] if r["family"] == "ultra60" and r["year"] == 2024)
        gpx = next(r for r in self.evidence["local_organizer_gpx"] if "2024-organizer.gpx" in r["path"])
        self.assertEqual(gpx["raw_ascent_m"], 0)
        self.assertEqual(route["trace_cumulative_ascent_m"], 693)
        self.assertEqual(route["trace_cumulative_descent_m"], 578)


if __name__ == "__main__":
    unittest.main()
