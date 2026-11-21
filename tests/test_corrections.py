"""Frozen F-10 editorial separation, provenance and export safety."""
from types import SimpleNamespace
import pytest
from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import request_review, decide_review
from veriloop.corrections import (CorrectionPolicyError, default_draft,
    create_or_edit_draft, submit_for_approval, editorial_decision,
    markdown_export, record_export, list_corrections)

@pytest.fixture
def conn(tmp_path):
    with connect_db(tmp_path / "pilot.db") as db:
        init_db(db); seed_evidence(db); yield db

def setup_review(conn, approved=True):
    video=SimpleNamespace(video_id="2MJY_ptQW1o",channel_id="UC1234567890",
        channel_name="NASA", title="NASA Eclipse", description="Eclipse passed Mexico",
        thumbnail_url=None,published_at="2024-04-08T20:20:27Z")
    claim=SimpleNamespace(text="A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
                          source_field="description",stance="ASSERTS")
    match=SimpleNamespace(evidence_id="EV-002",similarity=0.8,context_status="ALIGNED")
    a=SimpleNamespace(candidate=claim,matches=(match,),preliminary_state="POSSIBLE_EVIDENCE_MATCH",explanation="Preliminary.")
    rid,_=request_review(conn,video,a)
    if approved:
        decide_review(conn,rid,"APPROVED",reviewer_id="IndependentResearcher",
            note="Independently checked the actual event, date, assertion, source and location.",
            verdict="SUPPORTED",evidence_id="EV-002",confirmed_context=True)
    return rid

def test_pending_review_cannot_create_correction(conn):
    rid=setup_review(conn,approved=False)
    with pytest.raises(CorrectionPolicyError): default_draft(conn,rid)
    with pytest.raises(CorrectionPolicyError): create_or_edit_draft(conn,rid,"draft",editor_id="EditorA")

def test_separate_approval_and_export(conn):
    rid=setup_review(conn)
    draft=default_draft(conn,rid)
    cid=create_or_edit_draft(conn,rid,draft,editor_id="EditorA")
    with pytest.raises(CorrectionPolicyError): markdown_export(conn,cid)
    submit_for_approval(conn,cid)
    with pytest.raises(CorrectionPolicyError): markdown_export(conn,cid)
    with pytest.raises(CorrectionPolicyError):
        editorial_decision(conn,cid,approve=True,editor_id="EditorB",rationale="short")
    editorial_decision(conn,cid,approve=True,editor_id="EditorB",
        rationale="Independently checked every sentence of the correction draft and sources.")
    filename,text=markdown_export(conn,cid)
    assert filename.endswith(".md") and "not posted" in text
    assert list_corrections(conn)[0]["approval_status"]=="APPROVED"
    record_export(conn,cid)
    assert list_corrections(conn)[0]["approval_status"]=="EXPORTED"
    assert markdown_export(conn,cid)[0]==filename

def test_rejected_correction_cannot_export(conn):
    rid=setup_review(conn)
    cid=create_or_edit_draft(conn,rid,"An editorial correction draft",editor_id="EditorA")
    submit_for_approval(conn,cid)
    editorial_decision(conn,cid,approve=False,editor_id="EditorB",
        rationale="Needs stronger source comparisons and more precise wording.")
    with pytest.raises(CorrectionPolicyError): markdown_export(conn,cid)

def test_revised_review_revokes_export_permission(conn):
    rid=setup_review(conn)
    cid=create_or_edit_draft(conn,rid,"Correction with sourced claim",editor_id="EditorA")
    submit_for_approval(conn,cid)
    editorial_decision(conn,cid,approve=True,editor_id="EditorB",
        rationale="Evidence and wording independently checked before manual export.")
    decide_review(conn,rid,"NEEDS_MORE_EVIDENCE",
        reviewer_id="ResearcherAgain",note="New doubts about exact event context.")
    with pytest.raises(CorrectionPolicyError): markdown_export(conn,cid)

def test_immutable_after_submitting_and_editable_before(conn):
    rid=setup_review(conn)
    cid=create_or_edit_draft(conn,rid,"Initial editorial draft",editor_id="EditorA")
    assert create_or_edit_draft(conn,rid,"Changed editorial draft",editor_id="EditorA")==cid
    submit_for_approval(conn,cid)
    with pytest.raises(CorrectionPolicyError):
        create_or_edit_draft(conn,rid,"Malicious rewrite",editor_id="EditorA")

def test_additive_schema_migration(conn):
    init_db(conn)
    assert {"drafted_by","editorial_reviewer","editorial_note","last_updated_at"} <= {
        x["name"] for x in conn.execute("PRAGMA table_info(corrections)")
    }


def test_editorial_approver_must_differ_from_draft_author(conn):
    rid=setup_review(conn)
    cid=create_or_edit_draft(conn,rid,"Verifiable draft",editor_id="EditorA")
    submit_for_approval(conn,cid)
    with pytest.raises(CorrectionPolicyError,match="distinct from the drafter"):
        editorial_decision(conn,cid,approve=True,editor_id="editora",
            rationale="I independently reviewed this claim and linked original evidence.")
    assert list_corrections(conn)[0]["approval_status"]=="PENDING_APPROVAL"
