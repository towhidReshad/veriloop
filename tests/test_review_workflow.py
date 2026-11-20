"""Day 4 review invariants: request, approval, revision, evidence-only history."""
import json
from types import SimpleNamespace
import sqlite3
import pytest

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import ReviewPolicyError, request_review, decide_review, list_review_queue, linked_evidence
from veriloop.source_history import get_reviewed_history

@pytest.fixture
def conn(tmp_path):
    with connect_db(tmp_path / "review.db") as db:
        init_db(db)
        seed_evidence(db)
        yield db

def video():
    return SimpleNamespace(video_id="2MJY_ptQW1o", channel_id="UC1234567890",
        channel_name="NASA", title="NASA eclipse", thumbnail_url=None,
        published_at="2024-04-08T20:20:27Z", description="The eclipse crossed North America.")

def candidate(stance="ASSERTS", matched=True, context="ALIGNED"):
    m=SimpleNamespace(evidence_id="EV-002", similarity=0.8, context_status=context)
    return SimpleNamespace(
        candidate=SimpleNamespace(text="A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
                                   source_field="description", stance=stance),
        preliminary_state="POSSIBLE_EVIDENCE_MATCH" if matched else "INSUFFICIENT_EVIDENCE",
        explanation="Preliminary candidate, not final.", matches=(m,) if matched else ())

def approve(conn, rid):
    decide_review(conn,rid,"APPROVED",reviewer_id="HumanReviewer1",
        note="Exact asserted claim, event date, location and NASA evidence checked independently.",
        verdict="SUPPORTED",evidence_id="EV-002",confirmed_context=True)

def test_new_request_is_pending(conn):
    rid,created=request_review(conn,video(),candidate())
    assert created is True
    assert rid > 0
    assert list_review_queue(conn)[0]["review_status"]=="PENDING"
    assert get_reviewed_history(conn,"UC1234567890")["approved_count"] == 0

def test_idempotent_request(conn):
    rid,_=request_review(conn,video(),candidate())
    assert request_review(conn,video(),candidate())==(rid,False)

@pytest.mark.parametrize("stance", ["DEBUNKS","QUOTES","UNCLEAR"])
def test_nonasserted_claim_never_approved(conn,stance):
    rid,_=request_review(conn,video(),candidate(stance=stance))
    with pytest.raises(ReviewPolicyError):
        approve(conn,rid)
    assert get_reviewed_history(conn,"UC1234567890")["approved_count"]==0

@pytest.mark.parametrize("change", [
    dict(confirmed_context=False),dict(evidence_id=None),
    dict(evidence_id="EV-001"),dict(verdict="fake"),
    dict(note="too short"),
])
def test_approval_requires_provenance_and_human_note(conn,change):
    rid,_=request_review(conn,video(),candidate())
    fields=dict(reviewer_id="ActualReviewer", note="Independently compared exact asserted context, event and date.",
                verdict="SUPPORTED", evidence_id="EV-002", confirmed_context=True)
    fields.update(change)
    with pytest.raises(ReviewPolicyError):
        decide_review(conn,rid,"APPROVED",**fields)
    assert get_reviewed_history(conn,"UC1234567890")["approved_count"]==0

def test_approval_visible_only_after_explicit_reviewer_action(conn):
    rid,_=request_review(conn,video(),candidate())
    assert get_reviewed_history(conn,"UC1234567890")["review_requests"]==1
    approve(conn,rid)
    h=get_reviewed_history(conn,"UC1234567890")
    assert h["approved_count"]==1
    assert h["records"][0]["source_url"]=="https://science.nasa.gov/eclipses/future-eclipses/eclipse-2024/"
    assert h["records"][0]["video_published_at"]=="2024-04-08T20:20:27Z"

def test_revised_approval_drops_out_of_history_and_audit_retained(conn):
    rid,_=request_review(conn,video(),candidate())
    approve(conn,rid)
    decide_review(conn,rid,"NEEDS_MORE_EVIDENCE",reviewer_id="Reviewer2",
                  note="Further checks found unresolved event context.")
    assert get_reviewed_history(conn,"UC1234567890")["approved_count"]==0
    row=conn.execute("SELECT reviewed_verdict,reviewer_note FROM reviews WHERE id=?",(rid,)).fetchone()
    assert row["reviewed_verdict"] is None
    assert json.loads(row["reviewer_note"])["history"][0]["status"]=="APPROVED"

def test_unconfirmed_evidence_cannot_approve(conn):
    rid,_=request_review(conn,video(),candidate(context="UNCONFIRMED"))
    with pytest.raises(ReviewPolicyError):
        approve(conn,rid)

def test_no_match_not_falsely_approved(conn):
    rid,_=request_review(conn,video(),candidate(matched=False))
    with pytest.raises(ReviewPolicyError):
        approve(conn,rid)

def test_approved_history_empty_for_other_channel(conn):
    rid,_=request_review(conn,video(),candidate())
    approve(conn,rid)
    assert get_reviewed_history(conn,"UC87654321")["records"]==[]

def test_rejected_decision_not_public(conn):
    rid,_=request_review(conn,video(),candidate())
    decide_review(conn,rid,"REJECTED",reviewer_id="ActualReviewer",note="Insufficient provenance to support approval.")
    assert get_reviewed_history(conn,"UC1234567890")["approved_count"]==0

def test_foreign_key_cannot_link_fake_evidence(conn):
    rid,_=request_review(conn,video(),candidate())
    claim_id=list_review_queue(conn)[0]["claim_id"]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("""INSERT INTO claim_matches
            (claim_id,evidence_id,similarity_score,context_status,created_at)
            VALUES (?,?,?,?,?)""",(claim_id,"EV-999",0.8,"ALIGNED","2026-11-21T00:00:00+00:00"))
