#!/usr/bin/env python3
"""Dependency-free regression tests for the generic route engine."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

score=load("score_evidence")
rank=load("rank_candidates")
resolve=load("resolve_ambiguities")

def test_independence_group_not_double_counted():
    s=score.score_segment({"evidence":[
        {"source_id":"copy-a","independence_group":"organizer","provenance":"organizer_georeferenced_raster"},
        {"source_id":"copy-b","independence_group":"organizer","provenance":"organizer_georeferenced_raster"}
    ]})
    assert s["confidence_score"] == 0.78

def test_independent_sources_combine():
    s=score.score_segment({"evidence":[
        {"source_id":"raster","independence_group":"organizer","provenance":"organizer_georeferenced_raster"},
        {"source_id":"gps","independence_group":"participant-1","provenance":"participant_gps_single"}
    ]})
    assert s["confidence_score"] > 0.9

def test_hard_contradiction_disqualifies():
    c=rank.rank({"checks":{"distance_fit":1,"raster_fit":1},"hard_contradictions":["misses mandatory control"]},rank.DEFAULT_WEIGHTS)
    assert c["eligible"] is False

def test_close_alternatives_remain_unresolved():
    r=resolve.resolve({"alternatives":[
        {"alternative_id":"a","candidate_score":0.80,"contradictions":[]},
        {"alternative_id":"b","candidate_score":0.72,"contradictions":[]}
    ]},0.15)
    assert r["resolution_status"] == "preferred_but_unresolved"
    assert r["selected_alternative_id"] is None

def test_clear_alternative_resolves():
    r=resolve.resolve({"alternatives":[
        {"alternative_id":"a","candidate_score":0.90,"contradictions":[]},
        {"alternative_id":"b","candidate_score":0.60,"contradictions":[]}
    ]},0.15)
    assert r["resolution_status"] == "resolved"
    assert r["selected_alternative_id"] == "a"

class RouteEngineRegression(unittest.TestCase):
    def test_independence_group(self): test_independence_group_not_double_counted()
    def test_independent_sources(self): test_independent_sources_combine()
    def test_hard_contradiction(self): test_hard_contradiction_disqualifies()
    def test_close_alternatives(self): test_close_alternatives_remain_unresolved()
    def test_clear_alternative(self): test_clear_alternative_resolves()

if __name__=="__main__":
    unittest.main()
