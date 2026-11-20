"""Research fixture integrity only; these tests do NOT verify YouTube availability or claims."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from veriloop.youtube import extract_video_id

CASES = json.loads((Path(__file__).resolve().parents[1] / "data" / "demo_cases.json").read_text())


def test_three_distinct_real_candidate_link_shapes():
    candidates = CASES["cases"]
    assert {c["case_id"] for c in candidates} == {"A", "B", "C"}
    assert len({c["youtube_id"] for c in candidates}) == 3
    for c in candidates:
        assert extract_video_id(c["youtube_url"]) == c["youtube_id"]
        assert urlsplit(c["source_record_url"]).scheme == "https"


def test_no_candidate_is_mislabeled_as_a_human_review():
    for c in CASES["cases"]:
        assert c["has_veriloop_approved_review"] is False
        assert c["editorial_validation"] == "UNREVIEWED_RESEARCH_CANDIDATE"
        assert c["live_youtube_api_status"] == "UNTESTED_KEY_MISSING"
        assert c["demo_acceptance_status"].startswith("PENDING_")


def test_abc_scenarios_have_expected_prepared_annotations():
    by_id = {c["case_id"]: c for c in CASES["cases"]}
    assert by_id["A"]["verdict_candidate_for_manual_review"] == "MISLEADING_CONTEXT"
    assert by_id["B"]["verdict_candidate_for_manual_review"] == "SUPPORTED"
    assert by_id["C"]["verdict_candidate_for_manual_review"] == "INSUFFICIENT_EVIDENCE"


def test_no_correction_or_channel_score_is_preloaded():
    assert all("correction_approval" not in c and "channel_trust_score" not in c for c in CASES["cases"])
