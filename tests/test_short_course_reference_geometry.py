#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

class ShortCourseReferenceGeometry(unittest.TestCase):
    def test_trail14_reference_is_raster_derived_and_qa_passed(self):
        qa=load("routes/ost/trail14-current-reference/qa.json")
        geo=load("routes/ost/trail14-current-reference/route.geojson")
        prov=load("routes/ost/trail14-current-reference/provenance.json")
        self.assertTrue(qa["topology_qa_pass"])
        self.assertEqual(qa["status"],"georeferenced_organizer_raster_reference")
        self.assertAlmostEqual(qa["distance_km"],14.249,places=3)
        self.assertLessEqual(abs(qa["hallamolla_remaining_km"]-qa["participant_hallamolla_remaining_km"]),0.15)
        self.assertLessEqual(qa["hallamolla_control_m"],150)
        self.assertEqual(geo["properties"]["status"],"georeferenced_organizer_raster_reference")
        self.assertTrue(geo["properties"]["not_an_organizer_gpx"])
        self.assertEqual(prov["geometry_status"],"validated_raster_reference")
        self.assertTrue(prov["publishable_as_reconstructed_reference"])
        self.assertTrue(prov["not_an_organizer_gpx"])

    def test_trail5_reference_has_independent_raster_crosscheck(self):
        qa=load("routes/ost/trail5-current-reference/qa.json")
        prov=load("routes/ost/trail5-current-reference/provenance.json")
        direct=qa["organizer_raster_skeleton_measurement"]
        self.assertEqual(qa["qa_status"],"validated_reconstruction")
        self.assertTrue(qa["publishable_as_reconstructed_reference"])
        self.assertEqual(direct["point_count"],971)
        self.assertLessEqual(abs(direct["distance_km"]-qa["distance_km"]),0.10)
        self.assertEqual(prov["geometry_status"],"validated_reconstruction")
        self.assertTrue(prov["not_an_organizer_gpx"])

    def test_2026_course_versions_point_to_reference_assets(self):
        versions=load("config/course-versions.json")
        by_id={v["course_version_id"]:v for v in versions["versions"]}
        assigns={(a["year"],a["family"]):a for a in versions["assignments"]}
        for family,vid in (("trail14","trail14-current-reference"),("trail5","trail5-current-reference")):
            self.assertIn(vid,by_id)
            self.assertEqual(assigns[(2026,family)]["course_version_id"],vid)
            self.assertTrue(assigns[(2026,family)]["route_asset_available"])
            self.assertTrue((ROOT/by_id[vid]["primary_source_path"]).exists())

if __name__=="__main__":
    unittest.main()
