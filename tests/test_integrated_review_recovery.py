"""Full, offline F-07/F-09/F-10 continuity across a private encrypted restore.

This uses fixture decisions; it DOES NOT assert a real human-approved verdict
or hosted Streamlit reviewer identity was tested.
"""
from types import SimpleNamespace

import pytest

from veriloop.archive import ArchiveError, create_encrypted_backup, restore_encrypted_backup
from veriloop.corrections import (
    CorrectionPolicyError, create_or_edit_draft, default_draft,
    editorial_decision, list_corrections, markdown_export,
    record_export, submit_for_approval,
)
from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import (
    decide_review, find_reviewed_exact_context,
    list_review_queue, request_review,
)

PASSPHRASE = "This is a private test-only archive passphrase"

def _db(path):
    conn = connect_db(path)
    init_db(conn)
    seed_evidence(conn)
    return conn

def _case():
    video = SimpleNamespace(
        video_id="2MJY_ptQW1o", channel_id="UC1234567890",
        channel_name="NASA", title="NASA eclipse",
        description="A total solar eclipse crossed North America on April 8, 2024.",
        thumbnail_url=None, published_at="2024-04-08T20:20:27Z",
    )
    candidate = SimpleNamespace(
        text="A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
        source_field="description", stance="ASSERTS",
    )
    match = SimpleNamespace(
        evidence_id="EV-002", context_status="ALIGNED", similarity=0.82,
    )
    assessment = SimpleNamespace(
        candidate=candidate, matches=(match,),
        preliminary_state="POSSIBLE_EVIDENCE_MATCH",
        explanation="Preliminary source retrieval, not a verdict.",
    )
    return video, assessment

def test_full_review_to_correction_to_archive_restore(tmp_path):
    video, assessment = _case()
    with _db(tmp_path / "first.db") as db:
        rid, created = request_review(db, video, assessment)
        assert created and list_review_queue(db)[0]["review_status"] == "PENDING"
        assert find_reviewed_exact_context(db, video, assessment) is None

        with pytest.raises(CorrectionPolicyError):
            default_draft(db, rid)

        decide_review(
            db, rid, "APPROVED", reviewer_id="FixtureReviewer",
            note="Fixture reviewer explicitly checked the original source, claim, event and location.",
            verdict="SUPPORTED", evidence_id="EV-002", confirmed_context=True,
        )
        reviewed = find_reviewed_exact_context(db, video, assessment)
        assert reviewed and reviewed["review_id"] == rid
        assert reviewed["reviewed_verdict"] == "SUPPORTED"

        cid = create_or_edit_draft(
            db, rid, default_draft(db, rid), editor_id="DraftEditor",
        )
        with pytest.raises(CorrectionPolicyError):
            markdown_export(db, cid)
        submit_for_approval(db, cid)
        with pytest.raises(CorrectionPolicyError):
            markdown_export(db, cid)
        with pytest.raises(CorrectionPolicyError):
            editorial_decision(
                db, cid, approve=True, editor_id="DraftEditor",
                rationale="Fixture self-approval must be forbidden even with written reasoning.",
            )
        editorial_decision(
            db, cid, approve=True, editor_id="IndependentEditor",
            rationale="Fixture editor independently checks source and correction wording.",
        )
        name, contents = markdown_export(db, cid)
        assert name.endswith(".md") and "Editorial approval recorded" in contents
        record_export(db, cid)
        assert list_corrections(db)[0]["approval_status"] == "EXPORTED"
        encrypted = create_encrypted_backup(db, PASSPHRASE)
        assert b"FixtureReviewer" not in encrypted
        assert b"DraftEditor" not in encrypted

    with _db(tmp_path / "empty_second.db") as db:
        restore_encrypted_backup(db, encrypted, PASSPHRASE)
        assert find_reviewed_exact_context(db, video, assessment)["review_id"] == rid
        assert list_corrections(db)[0]["approval_status"] == "EXPORTED"
        assert markdown_export(db, cid)[1] == contents
        assert db.execute("PRAGMA foreign_key_check").fetchone() is None

        with pytest.raises(ArchiveError, match="Existing user data"):
            restore_encrypted_backup(db, encrypted, PASSPHRASE)

        # Revoking an old approval blocks both exact-context reuse and export.
        decide_review(
            db, rid, "NEEDS_MORE_EVIDENCE",
            reviewer_id="FixtureReviewer",
            note="A newly discovered event-context issue requires further investigation.",
        )
        assert find_reviewed_exact_context(db, video, assessment) is None
        with pytest.raises(CorrectionPolicyError):
            markdown_export(db, cid)


def test_review_logout_clears_prepared_archive_in_public_page_code():
    from pathlib import Path
    page = (
        Path(__file__).resolve().parents[1]
        / "pages" / "3_Review_Dashboard.py"
    ).read_text(encoding="utf-8")
    assert 'st.session_state.pop("vl_encrypted_archive", None)' in page
    assert 'if st.button("Lock workspace"' in page
