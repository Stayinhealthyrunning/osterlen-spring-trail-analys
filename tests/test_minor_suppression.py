"""Regression tests for youth-age evidence and public export referential safety."""
import unittest

from tools.minor_suppression import confirmed_minor, redact_race_bundle


class MinorSuppressionTests(unittest.TestCase):
    def test_historic_youth_age_band_spellings(self):
        for label in ("F0-11", "M12-13", "F14-15", "M16-17",
                      "(F) 16-17", "0-11", "16–17 kvinnor"):
            with self.subTest(label=label):
                self.assertTrue(confirmed_minor({"age": None, "age_category": label}))

    def test_no_age_inference_from_ambiguous_categories(self):
        for label in ("M18-19", "F20-24", "Naturloppet 5km+",
                      "Ekopark trail 13 km", "M17+", ""):
            with self.subTest(label=label):
                self.assertFalse(confirmed_minor({"age": None, "class_name": label}))
        self.assertTrue(confirmed_minor({"age": 17}))
        self.assertFalse(confirmed_minor({"age": 18}))
        self.assertFalse(confirmed_minor({"age": None}))

    def test_minor_result_and_linked_rows_are_removed(self):
        record = {
            "source_result_id": "source-123", "name": "Fiktiv Testperson",
            "bib": "201", "club": "Testklubb", "age": None,
            "class_name": "M16-17", "person_key": "person-123",
        }
        race = {"records": [record]}
        splits = [{"source_result_id": "source-123", "elapsed_seconds": 100}]
        members = [{"source_member_result_id": "source-123",
                    "bib": "201", "name_as_published": "Fiktiv Testperson"}]
        self.assertEqual(redact_race_bundle("synthetic", race, splits, members), 1)
        self.assertEqual(race["records"], [])
        self.assertEqual(splits, [])
        self.assertEqual(members, [])

    def test_adult_record_is_unchanged(self):
        adult = {"source_result_id": "adult-1", "age": 18,
                 "name": "Fiktiv Vuxen", "club": "Testklubb"}
        self.assertEqual(redact_race_bundle("synthetic", {"records": [adult]}, [], []), 0)
        self.assertEqual(adult["name"], "Fiktiv Vuxen")


if __name__ == "__main__":
    unittest.main()
