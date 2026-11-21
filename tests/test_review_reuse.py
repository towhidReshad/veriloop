"""F-07: approved findings reused only on the exact, unchanged video context."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import (
    decide_review, find_reviewed_exact_context, request_review,
)


@pytest.fixture
def conn(tmp_path):
    with connect_db(tmp_path / "reused.db") as db:
        init_db(db)
        seed_evidence(db)
        yield db


def video(**updates):
    info = dict(
        video_id="2MJY_ptQW1o", channel_id="UC1234567890", channel_name="NASA",
        title="NASA eclipse",
        description="A total solar eclipse crossed Mexico on April 8, 2024.",
        thumbnail_url=None, published_at="2024-04-08T20:20:27Z",
    )
    info.update(updates)
    return SimpleNamespace(**info)


def assessment(*, stance="ASSERTS", field="description", text=None):
    claim = SimpleNamespace(
        text=text or "A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
        source_field=field, stance=stance,
    )
    match = SimpleNamespace(evidence_id="EV-002", context_status="ALIGNED", similarity=0.80)
    return SimpleNamespace(
        candidate=claim, preliminary_state="POSSIBLE_EVIDENCE_MATCH",
        matches=(match,), explanation="Preliminary retrieval only."
    )


def approve(conn, v=None, a=None):
    v = v or video()
    a = a or assessment()
    review_id, _ = request_review(conn, v, a)
    decide_review(
        conn, review_id, "APPROVED", reviewer_id="ResearchReviewer",
        note="Independently compared exact clip claim, date, country and linked NASA source.",
        verdict="SUPPORTED", evidence_id="EV-002", confirmed_context=True,
    )
    return review_id


def test_approved_same_video_verbatim_context_can_be_reused(conn):
    review_id = approve(conn)
    result = find_reviewed_exact_context(conn, video(), assessment())
    assert result is not None
    assert result["review_id"] == review_id
    assert result["reviewed_verdict"] == "SUPPORTED"
    assert result["evidence_id"] == "EV-002"
    assert result["source_url"].startswith("https://")
    assert result["reviewed_at"]
    assert "reviewer_note" not in result


@pytest.mark.parametrize("changes", [
    {"video_id": "2MJY_ptQW1x"},
    {"channel_id": "UC9999999999"},
    {"title": "Updated NASA eclipse title"},
    {"description": "Updated description after review."},
    {"published_at": "2024-04-09T20:20:27Z"},
])
def test_different_video_or_metadata_never_reuses(conn, changes):
    approve(conn)
    assert find_reviewed_exact_context(conn, video(**changes), assessment()) is None


@pytest.mark.parametrize("updates", [
    {"stance": "QUOTES"},
    {"stance": "DEBUNKS"},
    {"stance": "UNCLEAR"},
    {"field": "title"},
    {"text": "A different claim about an eclipse in 2024."},
])
def test_different_stance_field_or_claim_never_reuses(conn, updates):
    approve(conn)
    assert find_reviewed_exact_context(conn, video(), assessment(**updates)) is None


def test_pending_rejected_or_revised_findings_do_not_reuse(conn):
    v, a = video(), assessment()
    review_id, _ = request_review(conn, v, a)
    assert find_reviewed_exact_context(conn, v, a) is None
    decide_review(conn, review_id, "NEEDS_MORE_EVIDENCE",
                  reviewer_id="ResearchReviewer", note="More event-context evidence required.")
    assert find_reviewed_exact_context(conn, v, a) is None
    approve(conn, v, a)
    assert find_reviewed_exact_context(conn, v, a)
    decide_review(conn, review_id, "REJECTED",
                  reviewer_id="ResearchReviewer", note="New concerns about exact event source.")
    assert find_reviewed_exact_context(conn, v, a) is None


def test_corrupted_audit_invalidates_reuse(conn):
    rid = approve(conn)
    conn.execute("UPDATE reviews SET reviewer_note='{}' WHERE id=?", (rid,))
    assert find_reviewed_exact_context(conn, video(), assessment()) is None


def test_reuse_is_read_only(conn):
    approve(conn)
    n = conn.total_changes
    for _ in range(3):
        assert find_reviewed_exact_context(conn, video(), assessment())
    assert conn.total_changes == n
