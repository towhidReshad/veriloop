"""Private backups: confidentiality, restore, tampering and overwrite safeguards."""
from types import SimpleNamespace

import pytest

from veriloop.archive import ArchiveError, create_encrypted_backup, restore_encrypted_backup
from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import request_review, decide_review

PASS = "An independently stored test-only passphrase"

def connect(path):
    db = connect_db(path)
    init_db(db)
    seed_evidence(db)
    return db

def add_review(conn):
    v = SimpleNamespace(
        video_id="2MJY_ptQW1o", channel_id="UC1234567890", channel_name="NASA",
        title="NASA eclipse", description="Total solar eclipse",
        thumbnail_url=None, published_at="2024-04-08T20:20:27Z",
    )
    c = SimpleNamespace(
        text="A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
        source_field="description", stance="ASSERTS",
    )
    match = SimpleNamespace(evidence_id="EV-002", similarity=0.8, context_status="ALIGNED")
    a = SimpleNamespace(candidate=c, matches=(match,),
        preliminary_state="POSSIBLE_EVIDENCE_MATCH", explanation="Tentative.")
    rid, _ = request_review(conn, v, a)
    decide_review(conn, rid, "APPROVED", reviewer_id="ResearchReviewer",
        note="Independently confirmed the exact claim, source, event, location and date.",
        verdict="SUPPORTED", evidence_id="EV-002", confirmed_context=True)

def test_encrypted_roundtrip_preserves_review(tmp_path):
    with connect(tmp_path/"original.db") as original:
        add_review(original)
        encrypted = create_encrypted_backup(original, PASS)
        assert b"NASA eclipse" not in encrypted
        assert b"ResearchReviewer" not in encrypted
    with connect(tmp_path/"restored.db") as restored:
        restore_encrypted_backup(restored, encrypted, PASS)
        assert restored.execute("SELECT review_status FROM reviews").fetchone()[0] == "APPROVED"
        assert restored.execute("PRAGMA foreign_key_check").fetchone() is None

def test_wrong_passphrase_or_modified_file_is_rejected(tmp_path):
    with connect(tmp_path/"a.db") as original:
        encrypted = create_encrypted_backup(original, PASS)
    with connect(tmp_path/"b.db") as restored:
        with pytest.raises(ArchiveError, match="Wrong passphrase"):
            restore_encrypted_backup(restored, encrypted, "An incorrect archive passphrase")
        modified = encrypted[:-1] + bytes([encrypted[-1] ^ 1])
        with pytest.raises(ArchiveError, match="tampered"):
            restore_encrypted_backup(restored, modified, PASS)

def test_restore_cannot_overwrite_user_records(tmp_path):
    with connect(tmp_path/"a.db") as original:
        add_review(original)
        encrypted = create_encrypted_backup(original, PASS)
    with connect(tmp_path/"b.db") as restored:
        add_review(restored)
        with pytest.raises(ArchiveError, match="Existing user data"):
            restore_encrypted_backup(restored, encrypted, PASS)
        assert restored.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 1

def test_invalid_archive_and_short_passphrase_rejected(tmp_path):
    with connect(tmp_path/"a.db") as original:
        with pytest.raises(ArchiveError):
            create_encrypted_backup(original, "short")
        with pytest.raises(ArchiveError):
            restore_encrypted_backup(original, b"not a real backup", PASS)

def test_empty_backup_roundtrip(tmp_path):
    with connect(tmp_path/"a.db") as original:
        encrypted=create_encrypted_backup(original,PASS)
    with connect(tmp_path/"b.db") as restored:
        restore_encrypted_backup(restored,encrypted,PASS)
        assert restored.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 13
