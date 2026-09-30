import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class EngineV1ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="ost-engine-v1-test-")
        cls.out=Path(cls.tmp.name)/"engine.json"
        run=subprocess.run([sys.executable,str(ROOT/"tools/export_engine_v1.py"),"--output",str(cls.out)],cwd=ROOT,text=True,capture_output=True)
        if run.returncode:
            raise AssertionError(run.stderr or run.stdout)
        cls.summary=json.loads(run.stdout.strip())
        cls.data=json.loads(cls.out.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_totals_and_contract(self):
        self.assertEqual(self.summary["engine_contract"],"loppanalys-engine-1.0")
        self.assertEqual(self.summary["races"],34)
        self.assertEqual(self.summary["results"],9871)
        self.assertEqual(self.summary["teams"],300)
        self.assertEqual(self.summary["team_members"],599)
        self.assertEqual(self.summary["replay_ready"],10)

    def test_sparse_finish_only_race_stays_sparse(self):
        race=self.data["races"]["ost-2026-trail22"]
        self.assertFalse(race["capabilities"]["segment_analysis"])
        self.assertFalse(race["capabilities"]["replay"])
        self.assertFalse(race["capabilities"]["head_to_head"])
        self.assertEqual({x["key"] for x in self.data["checkpoints"][race["race_key"]]},{"start","finish"})

    def test_historical_ultra_can_have_map_route_without_replay(self):
        race=self.data["races"]["ost-2018-ultra60"]
        self.assertTrue(race["capabilities"]["segment_analysis"])
        self.assertTrue(race["capabilities"]["head_to_head"])
        self.assertFalse(race["capabilities"]["replay"])
        assets=self.data["courses"][race["course_version"]]["assets"]
        self.assertEqual(assets["route_asset_status"],"derived_public_trace_geometry")
        self.assertTrue(assets["route_source"])
        self.assertFalse(assets["official_gpx"])

    def test_local_route_unlocks_replay_only_where_readiness_allows(self):
        race=self.data["races"]["ost-2025-ultra60"]
        self.assertTrue(race["capabilities"]["segment_analysis"])
        self.assertTrue(race["capabilities"]["replay"])
        self.assertTrue(self.data["courses"][race["course_version"]]["assets"]["route_source"])

    def test_duo_is_team_without_invented_leg_assignment(self):
        race=self.data["races"]["ost-2025-duo60"]
        self.assertEqual(race["participant"]["entity"],"team")
        self.assertEqual(race["competition"]["format"],"duo")
        self.assertEqual(race["competition"]["team_structure"],{"kind":"sequential","leg_count":2,"member_assignment":"unknown"})
        members=[x for x in self.data["team_members"] if x["race_key"]==race["race_key"]]
        self.assertTrue(members)
        self.assertTrue(all(x["leg_no"] is None for x in members))

    def test_demographic_capabilities_follow_observed_coverage(self):
        old=self.data["races"]["ost-2018-ultra60"]
        modern=self.data["races"]["ost-2025-ultra60"]
        self.assertFalse(old["capabilities"]["sex_filter"])
        self.assertFalse(old["capabilities"]["age_analysis"])
        self.assertTrue(modern["capabilities"]["sex_filter"])
        self.assertTrue(modern["capabilities"]["age_analysis"])


    def test_short_course_assignments_overlay_curated_db(self):
        trail14=self.data["races"]["ost-2026-trail14"]
        trail5=self.data["races"]["ost-2026-trail5"]
        self.assertEqual(trail14["course_version"],"trail14-current-reference")
        self.assertEqual(trail5["course_version"],"trail5-current-reference")
        self.assertFalse(trail14["capabilities"]["segment_analysis"])
        self.assertFalse(trail14["capabilities"]["replay"])
        self.assertFalse(trail5["capabilities"]["segment_analysis"])
        self.assertFalse(trail5["capabilities"]["replay"])

    def test_reconstructed_trail5_asset_is_exposed_with_provenance(self):
        course=self.data["courses"]["trail5-current-reference"]
        self.assertEqual(course["assets"]["route_asset_status"],"derived_reconstructed_reference")
        self.assertFalse(course["assets"]["official_gpx"])
        self.assertTrue(course["assets"]["route_source"])
        trail14=self.data["courses"]["trail14-current-reference"]["assets"]
        self.assertEqual(trail14["route_asset_status"],"derived_provisional_reference")
        self.assertFalse(trail14["official_gpx"])
        self.assertTrue(trail14["route_source"])

    def test_all_exported_results_and_splits_are_internally_consistent(self):
        valid_status={"FINISHED","DNF","DNS","DSQ","UNKNOWN"}
        results_by_race={}
        for race_key,race in self.data["races"].items():
            records=race["records"]
            ids=[str(record["source_result_id"]) for record in records]
            self.assertEqual(len(ids),len(set(ids)),f"{race_key}: duplicate source_result_id")
            results_by_race[race_key]={str(record["source_result_id"]):record for record in records}
            for record in records:
                self.assertIn(record["status"],valid_status)
                if record["status"]=="FINISHED":
                    self.assertIsNotNone(record["finish_seconds"],f"{race_key}: FINISHED without time")
                    self.assertGreater(record["finish_seconds"],0)
                if record["finish_seconds"] is not None:
                    self.assertGreater(record["finish_seconds"],0)
                self.assertIn(record["sex"],(None,"F","M"))
                if record["age"] is not None:
                    self.assertGreater(record["age"],0)
                    self.assertLess(record["age"],100)
                for field in ("overall_place","class_place","gender_place"):
                    if record[field] is not None:
                        self.assertGreater(record[field],0)

        checkpoint_keys={key:{cp["key"] for cp in value} for key,value in self.data["checkpoints"].items()}
        for split in self.data["splits"]:
            race_key=split["race_key"]
            result=results_by_race[race_key].get(str(split["source_result_id"]))
            self.assertIsNotNone(result,f"{race_key}: orphan split {split['source_result_id']}")
            self.assertIn(split["checkpoint"],checkpoint_keys[race_key])
            self.assertGreater(split["elapsed_seconds"],0)
            if result["status"]=="FINISHED" and result["finish_seconds"] is not None:
                self.assertLessEqual(split["elapsed_seconds"],result["finish_seconds"])

        teams={(team["race_key"],str(team["source_result_id"])) for team in self.data["teams"]}
        for member in self.data["team_members"]:
            self.assertIn((member["race_key"],str(member["team_source_result_id"])),teams)
            self.assertIsNone(member["leg_no"])

    def test_historical_checkpoint_order_follows_semantic_policy(self):
        expected=["start","stenshuvud","bengtemolla","vantalangan","finish"]
        for key in ("ost-2019-ultra60","ost-2019-duo60"):
            self.assertEqual([x["key"] for x in self.data["checkpoints"][key]],expected)

    def test_observed_splits_are_chronological_in_exported_checkpoint_order(self):
        for race_key,checkpoints in self.data["checkpoints"].items():
            rank={cp["key"]:i for i,cp in enumerate(checkpoints)}
            by_result={}
            for split in self.data["splits"]:
                if split["race_key"]!=race_key or split["checkpoint"] not in rank:
                    continue
                by_result.setdefault(str(split["source_result_id"]),[]).append(split)
            for source_result_id,splits in by_result.items():
                ordered=sorted(splits,key=lambda s:rank[s["checkpoint"]])
                times=[s["elapsed_seconds"] for s in ordered]
                self.assertEqual(times,sorted(times),f"{race_key} {source_result_id} has non-chronological semantic checkpoints")

    def test_person_history_remains_disabled_without_linkage_layer(self):
        self.assertTrue(all(not race["capabilities"]["person_history"] for race in self.data["races"].values()))


if __name__=="__main__":
    unittest.main()
