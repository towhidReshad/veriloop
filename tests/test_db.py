"""Day 2 SQLite invariants; no live API or Streamlit runtime required."""
import json
import sqlite3
from copy import deepcopy

import pytest

from veriloop.db import (
    InvalidEvidenceRecord,
    connect_db,
    init_db,
    list_evidence,
    load_evidence,
    seed_evidence,
    validate_evidence_record,
)


@pytest.fixture
def database(tmp_path):
    with connect_db(tmp_path / "test.db") as conn:
        init_db(conn)
        yield conn


def test_schema_has_exact_eight_canonical_tables(database):
    tables = {r[0] for r in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"channels", "videos", "claims", "evidence", "claim_matches", "assessments", "reviews", "corrections"}
    assert database.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_real_curated_records_are_traceable_and_unreviewed(database):
    records = load_evidence()
    assert 12 <= len(records) <= 15
    assert len({r['source_url'] for r in records}) >= 12
    assert all(r['reviewed_by'] is None for r in records)
    assert seed_evidence(database) == len(records)
    rows = list_evidence(database)
    assert len(rows) == len(records)
    assert {r['id'] for r in rows} == {r['id'] for r in records}
    assert database.execute('SELECT COUNT(*) FROM reviews').fetchone()[0] == 0
    assert database.execute('SELECT COUNT(*) FROM corrections').fetchone()[0] == 0
    assert database.execute('SELECT COUNT(*) FROM claim_matches').fetchone()[0] == 0


def test_seed_idempotent_and_does_not_overwrite_existing_record(database):
    assert seed_evidence(database) == 13
    database.execute("UPDATE evidence SET notes='local audit note' WHERE id='EV-001'")
    assert seed_evidence(database) == 0
    assert database.execute("SELECT notes FROM evidence WHERE id='EV-001'").fetchone()[0] == 'local audit note'


@pytest.mark.parametrize('change', [
    {'source_url': 'not-a-url'},
    {'source_url': 'http://example.org/article'},
    {'source_url': 'https://evil.test@legit.test/path'},
    {'published_date': '2024-99-10'},
    {'published_date': '04/08/2024'},
    {'reviewed_by': 'invented reviewer'},
    {'reference_verdict': '100_PERCENT_FAKE'},
    {'claim_text': ''},
    {'id': '../secret'},
])
def test_seed_rejects_invalid_evidence(change):
    record = deepcopy(load_evidence()[0])
    record.update(change)
    with pytest.raises(InvalidEvidenceRecord):
        validate_evidence_record(record)


def test_duplicate_seed_ids_rejected_without_partial_writes(database, tmp_path):
    records = load_evidence()
    records[1]['id'] = records[0]['id']
    seed_path = tmp_path / 'bad.json'
    seed_path.write_text(json.dumps({'collection': 'verification_library', 'records': records}))
    with pytest.raises(InvalidEvidenceRecord, match='Duplicate'):
        seed_evidence(database, seed_path)
    assert database.execute('SELECT COUNT(*) FROM evidence').fetchone()[0] == 0


def test_research_records_are_not_video_claims_or_review_approvals(database):
    seed_evidence(database)
    for table in ('channels', 'videos', 'claims', 'assessments', 'reviews', 'corrections'):
        assert database.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0


def test_claim_and_assessment_state_are_separate_from_review_verdict(database):
    database.execute("INSERT INTO channels (youtube_channel_id,name,created_at) VALUES ('channel123','Example','2026-11-20T12:00:00+09:00')")
    database.execute("""INSERT INTO videos (youtube_id,channel_id,title,fetched_at)
                      VALUES ('2MJY_ptQW1o',1,'Eclipse','2026-11-20T12:00:00+09:00')""")
    database.execute("""INSERT INTO claims (video_id,claim_text,stance,created_at)
                      VALUES (1,'Claim sample','UNCLEAR','2026-11-20T12:00:00+09:00')""")
    database.execute("""INSERT INTO assessments (claim_id,preliminary_state,explanation,created_at)
                      VALUES (1,'INSUFFICIENT_EVIDENCE','No match','2026-11-20T12:00:00+09:00')""")
    database.execute("INSERT INTO reviews (claim_id,assessment_id,review_status) VALUES (1,1,'PENDING')")
    assert database.execute('SELECT reviewed_verdict FROM reviews').fetchone()[0] is None
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO reviews (claim_id,review_status) VALUES (1,'APPROVED')")
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO claims (video_id,claim_text,stance,created_at) VALUES (1,'Invalid','FAKE','2026-11-20T12:00:00+09:00')")
    database.execute("""INSERT INTO reviews (claim_id,review_status,reviewed_verdict,reviewed_at)
                      VALUES (1,'APPROVED','SUPPORTED','2026-11-20T13:00:00+09:00')""")
    database.execute("INSERT INTO corrections (review_id,draft_text,approval_status) VALUES (2,'Working draft','DRAFT')")
    assert database.execute('SELECT approval_status FROM corrections').fetchone()[0] == 'DRAFT'


def test_foreign_keys_enforced(database):
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("""INSERT INTO videos (youtube_id,channel_id,title,fetched_at)
                          VALUES ('fakevideo00',999,'Invalid','2026-11-20T12:00:00+09:00')""")
