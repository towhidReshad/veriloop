"""F-08: public channel history refuses malformed human-review audit provenance.

These fixtures are synthetic and never represent real human endorsements.
"""
import json
from types import SimpleNamespace

import pytest

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import decide_review, request_review
from veriloop.source_history import get_reviewed_history

CHANNEL = "UC1234567890"


@pytest.fixture
def approved(tmp_path):
    with connect_db(tmp_path/"history.db") as conn:
        init_db(conn)
        seed_evidence(conn)
        video=SimpleNamespace(
            video_id="2MJY_ptQW1o", channel_id=CHANNEL, channel_name="NASA",
            title="NASA eclipse", description="Eclipse across North America",
            thumbnail_url=None, published_at="2024-04-08T20:20:27Z",
        )
        candidate=SimpleNamespace(
            text="A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
            source_field="description", stance="ASSERTS",
        )
        assessment=SimpleNamespace(
            candidate=candidate,
            preliminary_state="POSSIBLE_EVIDENCE_MATCH",
            explanation="Preliminary only, not a verdict.",
            matches=(SimpleNamespace(
                evidence_id="EV-002", similarity=0.8, context_status="ALIGNED"
            ),),
        )
        review_id, _ = request_review(conn, video, assessment)
        decide_review(conn, review_id, "APPROVED",
                      reviewer_id="TestReviewer",
                      note="Fixture source, event, country and exact claim were checked independently.",
                      verdict="SUPPORTED", evidence_id="EV-002",
                      confirmed_context=True)
        yield conn, review_id


def test_valid_approved_review_remains_visible(approved):
    conn, rid=approved
    result=get_reviewed_history(conn, CHANNEL)
    assert result["approved_count"]==1
    assert result["records"][0]["review_id"]==rid
    assert "reviewer_note" not in result["records"][0]


@pytest.mark.parametrize("field,value", [
    ("reviewer_id", ""),
    ("reviewer_id", None),
    ("rationale", "short"),
    ("timestamp", "2000-01-01T00:00:00Z"),
    ("evidence_id", "EV-001"),
    ("confirmed_context", False),
    ("status", "PENDING"),
    ("verdict", "CONTRADICTED"),
])
def test_tampered_audit_must_not_surface_as_public_claim(approved,field,value):
    conn, rid=approved
    row=conn.execute("SELECT reviewer_note FROM reviews WHERE id=?", (rid,)).fetchone()
    audit=json.loads(row["reviewer_note"])
    audit[field]=value
    conn.execute(
        "UPDATE reviews SET reviewer_note=? WHERE id=?",
        (json.dumps(audit),rid)
    )
    result=get_reviewed_history(conn,CHANNEL)
    assert result["review_requests"]==1
    assert result["approved_count"]==0
    assert result["records"]==[]


def test_unsafe_linked_reference_excluded_from_public_history(approved):
    conn,_=approved
    conn.execute("UPDATE evidence SET source_url='http://untrusted.invalid' WHERE id='EV-002'")
    assert get_reviewed_history(conn,CHANNEL)["records"]==[]
