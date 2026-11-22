"""F-09: User-facing repeat review request status reflects the database.

A repeated request is idempotent but must not be misrepresented as pending
when a human has already approved, rejected or requested more evidence.
"""
from types import SimpleNamespace

import pytest

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import (
    ReviewPolicyError, decide_review, get_review_request_status, request_review,
)


@pytest.fixture
def conn(tmp_path):
    with connect_db(tmp_path/"request_status.db") as db:
        init_db(db)
        seed_evidence(db)
        yield db


def sample():
    video = SimpleNamespace(
        video_id="2MJY_ptQW1o", channel_id="UC1234567890",
        channel_name="NASA", title="NASA eclipse",
        description="The eclipse crossed Mexico on April 8, 2024.",
        published_at="2024-04-08T20:20:27Z", thumbnail_url=None,
    )
    claim = SimpleNamespace(
        text="A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
        source_field="description", stance="ASSERTS",
    )
    assessment = SimpleNamespace(
        candidate=claim, preliminary_state="POSSIBLE_EVIDENCE_MATCH",
        explanation="A potential source match only.",
        matches=[SimpleNamespace(
            evidence_id="EV-002", similarity=0.8, context_status="ALIGNED"
        )],
    )
    return video, assessment


@pytest.mark.parametrize("status", ["APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"])
def test_repeated_review_preserves_actual_status(conn, status):
    video, assessment = sample()
    rid, created = request_review(conn, video, assessment)
    assert created and get_review_request_status(conn, rid) == "PENDING"

    if status == "APPROVED":
        decide_review(
            conn, rid, status, reviewer_id="FixtureReviewer",
            note="Fixture reviewer independently checked exact event, date, context, and source.",
            verdict="SUPPORTED", evidence_id="EV-002", confirmed_context=True,
        )
    else:
        decide_review(
            conn, rid, status, reviewer_id="FixtureReviewer",
            note="Fixture reviewer requires a further source/context check.",
        )
    assert request_review(conn, video, assessment) == (rid, False)
    assert get_review_request_status(conn, rid) == status
    assert conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 1


def test_unknown_review_id_not_reported_as_pending(conn):
    with pytest.raises(ReviewPolicyError, match="no longer available"):
        get_review_request_status(conn, 9999)


def test_public_confirmation_uses_stored_status():
    from pathlib import Path
    page = (Path(__file__).resolve().parents[1] /
            "pages" / "1_Verify_News.py").read_text(encoding="utf-8")
    assert "stored_status = get_review_request_status(conn, request_id)" in page
    assert "f\\"· {stored_status}. \\"" in page
    assert "already exists'} · PENDING" not in page
