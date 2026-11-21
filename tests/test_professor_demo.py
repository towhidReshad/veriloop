"""F-12 source-linked professor cases without fabricated API or human verdicts."""
import copy
import json

import pytest

from veriloop.demo import DemoCaseError, load_demo_cases, public_summary

def test_three_curated_demonstrations_are_not_approved_reviews():
    cases = load_demo_cases()
    assert [c["case_id"] for c in cases] == ["A", "B", "C"]
    for case in cases:
        info = public_summary(case)
        assert "Not a live YouTube API response" in info["disclaimer"]
        assert info["acceptance"].startswith("PENDING_")
        assert info["source_record_url"].startswith("https://")
        assert "video_publication_date" not in info

def test_case_a_factual_source_is_not_confused_with_video_verdict():
    cases = load_demo_cases()
    a = public_summary(cases[0])
    assert a["scenario"] == "MISLEADING_CONTEXT"
    assert "review" in a["disclaimer"].lower()

def test_demo_case_file_cannot_preload_human_approval(tmp_path):
    cases = load_demo_cases()
    altered = copy.deepcopy(cases)
    altered[0]["has_veriloop_approved_review"] = True
    data = {"collection": "prepared_demo_candidates_only_not_population_sample", "cases": altered}
    path = tmp_path / "unsafe.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(DemoCaseError, match="approved"):
        load_demo_cases(path)

def test_demo_case_invalid_provenance_or_fake_accepted_status_rejected(tmp_path):
    cases = load_demo_cases()
    cases[2]["source_record_url"] = "http://insecure.invalid/review"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"collection": "prepared_demo_candidates_only_not_population_sample",
                                "cases": cases}), encoding="utf-8")
    with pytest.raises(DemoCaseError, match="HTTPS"):
        load_demo_cases(path)
    cases[2]["source_record_url"] = "https://science.nasa.gov/uap/"
    cases[2]["demo_acceptance_status"] = "LIVE_APPROVED"
    path.write_text(json.dumps({"collection": "prepared_demo_candidates_only_not_population_sample",
                                "cases": cases}), encoding="utf-8")
    with pytest.raises(DemoCaseError, match="acceptance"):
        load_demo_cases(path)
