"""Regression: repeated review requests never reuse a changed video context."""
from types import SimpleNamespace

import pytest

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import ReviewPolicyError, request_review, decide_review, list_review_queue

def _video(**changes):
    fields = dict(
        video_id="2MJY_ptQW1o", channel_id="UC1234567890",
        channel_name="NASA", title="NASA eclipse broadcast",
        description="Official eclipse broadcast, with date and geographic details.",
        published_at="2024-04-08T20:20:27Z", thumbnail_url=None,
    )
    fields.update(changes)
    return SimpleNamespace(**fields)

def _assessment(field="description"):
    return SimpleNamespace(
        candidate=SimpleNamespace(
            text="A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
            source_field=field, stance="ASSERTS",
        ),
        preliminary_state="POSSIBLE_EVIDENCE_MATCH",
        explanation="Tentative source match.",
        matches=[SimpleNamespace(evidence_id="EV-002", similarity=0.8, context_status="ALIGNED")],
    )

@pytest.fixture
def conn(tmp_path):
    with connect_db(tmp_path/"review.db") as db:
        init_db(db)
        seed_evidence(db)
        yield db

@pytest.mark.parametrize("changed_field", [
    {"title": "NASA eclipse broadcast updated"},
    {"description": "The video description has been edited by its publisher."},
    {"published_at": "2024-04-09T20:20:27Z"},
])
def test_changed_video_metadata_does_not_reuse_prior_review(conn, changed_field):
    rid, _ = request_review(conn, _video(), _assessment())
    decide_review(conn, rid, "APPROVED",
                  reviewer_id="FixtureReviewer",
                  note="Fixture source and original exact event context checked independently.",
                  verdict="SUPPORTED", evidence_id="EV-002", confirmed_context=True)
    with pytest.raises(ReviewPolicyError, match="metadata has changed"):
        request_review(conn, _video(**changed_field), _assessment())
    queue = list_review_queue(conn)
    assert len(queue) == 1
    assert queue[0]["review_id"] == rid
    assert queue[0]["review_status"] == "APPROVED"
    assert conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 1

def test_identical_metadata_and_source_field_is_idempotent(conn):
    original, created = request_review(conn, _video(), _assessment())
    assert created
    assert request_review(conn, _video(), _assessment()) == (original, False)

def test_different_metadata_source_field_does_not_reuse_previous_claim(conn):
    first, _ = request_review(conn, _video(), _assessment(field="description"))
    second, created = request_review(conn, _video(), _assessment(field="title"))
    assert created and second != first
    assert len(list_review_queue(conn)) == 2

def test_changed_channel_identity_cannot_reuse(conn):
    request_review(conn, _video(), _assessment())
    with pytest.raises(ReviewPolicyError, match="identifiers disagree"):
        request_review(conn, _video(channel_id="UCINVALIDDIFFERENT"), _assessment())
    assert len(list_review_queue(conn)) == 1
