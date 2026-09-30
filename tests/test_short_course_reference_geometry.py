#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))

class ShortCourseReferenceGeometry(unittest.TestCase):
    def test_trail14_superseded_raster_candidate_is_retained_for_audit(self):
        qa=load("routes/ost/trail14-current-reference/superseded-raster-qa.json")
        prov=load("routes/ost/trail14-current-reference/superseded-raster-provenance.json")
        self.assertTrue(qa["topology_qa_pass"])
        self.assertAlmostEqual(qa["distance_km"],14.249,places=3)
        self.assertEqual(prov["geometry_status"],"superseded_raster_candidate")
        self.assertFalse(prov["publishable_as_reconstructed_reference"])
        self.assertEqual(prov["replacement_reference"]["status"],"provisional_hallamolla_splice_reference")
        self.assertAlmostEqual(prov["replacement_reference"]["derived_distance_km"],13.472,places=3)
        self.assertFalse((ROOT/"routes/ost/trail14-current-reference/route.geojson").exists())
        self.assertFalse((ROOT/"routes/ost/trail14-current-reference/candidate-frontier.json").exists())

    def test_trail14_active_reference_is_materialized_but_explicitly_provisional(self):
        versions=load("config/course-versions.json")
        by_id={v["course_version_id"]:v for v in versions["versions"]}
        assigns={(a["year"],a["family"]):a for a in versions["assignments"]}
        v=by_id["trail14-current-reference"]
        a=assigns[(2026,"trail14")]
        qa=load("routes/ost/trail14-current-reference/qa.json")
        prov=load("routes/ost/trail14-current-reference/provenance.json")

        self.assertEqual(v["status"],"provisional_hallamolla_splice_reference")
        self.assertAlmostEqual(v["derived_path_distance_km"],13.472,places=3)
        self.assertEqual(v["route_asset_status"],"derived_provisional_reference")
        self.assertEqual(v["route_provenance_label"],"Rekonstruerad bana · provisorisk")
        self.assertEqual(v["reference_recipe"]["base_course_version"],"trail22-2022-2024")
        self.assertAlmostEqual(v["reference_recipe"]["removed_loop_km"],8.269,places=3)
        self.assertLess(v["reference_recipe"]["splice_point_separation_m"],1.0)
        self.assertEqual(a["course_version_id"],"trail14-current-reference")
        self.assertTrue(a["route_asset_available"])
        self.assertTrue((ROOT/v["primary_source_path"]).exists())

        self.assertEqual(qa["status"],"provisional_hallamolla_splice_reference_materialized")
        self.assertAlmostEqual(qa["distance_km"],13.472,places=3)
        self.assertTrue(qa["qa"]["publishable_as_provisional_reconstruction"])
        self.assertFalse(qa["qa"]["publishable_as_authoritative_gpx"])

        self.assertEqual(prov["geometry_status"],"provisional_hallamolla_splice_reference")
        self.assertTrue(prov["not_an_organizer_gpx"])
        self.assertTrue(prov["not_a_trace_gpx_export"])
        self.assertEqual(prov["publication_label"],"Rekonstruerad bana · provisorisk")
        self.assertAlmostEqual(prov["distance_km"],13.472,places=3)
        self.assertEqual(prov["base_course_version"],"trail22-2022-2024")
        self.assertAlmostEqual(prov["splice"]["removed_loop_km"],8.269,places=3)
        self.assertLess(prov["splice"]["splice_separation_m"],1.0)

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

    def test_2026_trail5_assignment_has_local_reference_asset(self):
        versions=load("config/course-versions.json")
        by_id={v["course_version_id"]:v for v in versions["versions"]}
        assigns={(a["year"],a["family"]):a for a in versions["assignments"]}
        v=by_id["trail5-current-reference"]
        a=assigns[(2026,"trail5")]
        self.assertEqual(a["course_version_id"],"trail5-current-reference")
        self.assertTrue(a["route_asset_available"])
        self.assertTrue((ROOT/v["primary_source_path"]).exists())

if __name__=="__main__":
    unittest.main()
