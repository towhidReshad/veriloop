"""SQLite schema, curated evidence validation, and data access for VeriLoop.

Day 2: an external publisher's reference verdict is NOT a VeriLoop human review.
Every seeded evidence.reviewed_by stays NULL, and no review is auto-approved.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "veriloop.db"
DEFAULT_SEED_PATH = ROOT / "data" / "seed_evidence.json"
REFERENCE_VERDICTS = frozenset(
    {"SUPPORTED", "CONTRADICTED", "MISLEADING_CONTEXT", "INSUFFICIENT_EVIDENCE"}
)
SEED_FIELDS = frozenset(
    {"id", "claim_text", "reference_verdict", "source_name", "source_url", "published_date", "reviewed_by", "notes"}
)

# The eight tables and their relationships follow Section 9 of PROJECT_SOURCE_OF_TRUTH.md.
# Claim verdict, review workflow status, and correction approval remain separate fields.
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    youtube_channel_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY,
    youtube_id TEXT NOT NULL UNIQUE,
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    thumbnail_url TEXT,
    published_at TEXT,
    fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id),
    claim_text TEXT NOT NULL,
    claim_context TEXT,
    stance TEXT NOT NULL DEFAULT 'UNCLEAR' CHECK (stance IN ('ASSERTS', 'DEBUNKS', 'QUOTES', 'UNCLEAR')),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    claim_text TEXT NOT NULL,
    reference_verdict TEXT NOT NULL CHECK (
      reference_verdict IN ('SUPPORTED', 'CONTRADICTED', 'MISLEADING_CONTEXT', 'INSUFFICIENT_EVIDENCE')
    ),
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    published_date TEXT,
    reviewed_by TEXT,
    notes TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claim_matches (
    id INTEGER PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    evidence_id TEXT NOT NULL REFERENCES evidence(id),
    similarity_score REAL NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 1),
    context_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (claim_id, evidence_id)
);
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    preliminary_state TEXT NOT NULL CHECK (
      preliminary_state IN ('PREVIOUSLY_REVIEWED_CONTEXT_MATCH', 'POSSIBLE_EVIDENCE_MATCH',
                            'INSUFFICIENT_EVIDENCE', 'ERROR_RETRIEVING_DATA')
    ),
    explanation TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    assessment_id INTEGER REFERENCES assessments(id),
    review_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
      review_status IN ('PENDING', 'APPROVED', 'REJECTED', 'NEEDS_MORE_EVIDENCE')
    ),
    reviewed_verdict TEXT CHECK (
      reviewed_verdict IN ('SUPPORTED', 'CONTRADICTED', 'MISLEADING_CONTEXT', 'INSUFFICIENT_EVIDENCE')
    ),
    reviewer_note TEXT,
    reviewed_at TEXT,
    CHECK (review_status <> 'APPROVED' OR (reviewed_verdict IS NOT NULL AND reviewed_at IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY,
    review_id INTEGER NOT NULL REFERENCES reviews(id),
    draft_text TEXT NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'DRAFT' CHECK (
      approval_status IN ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'EXPORTED')
    ),
    approved_at TEXT,
    export_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_claims_video_id ON claims(video_id);
CREATE INDEX IF NOT EXISTS idx_claim_matches_claim_id ON claim_matches(claim_id);
CREATE INDEX IF NOT EXISTS idx_reviews_claim_id_status ON reviews(claim_id, review_status);
"""


class InvalidEvidenceRecord(ValueError):
    """A seed entry has missing/invalid provenance or a forbidden value."""


def connect_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with FK enforcement; never connect on module import."""
    path = Path(db_path or os.getenv("VERILOOP_DB_PATH") or DEFAULT_DB_PATH)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    """Create the 8 canonical logical tables; safe to call repeatedly."""
    connection.executescript(SCHEMA_SQL)

    # Additive migration only: preserve the frozen eight-table logical model.
    # Existing free-cloud databases lack the new editorial audit columns.
    extras = {
        "drafted_by": "TEXT",
        "editorial_reviewer": "TEXT",
        "editorial_note": "TEXT",
        "last_updated_at": "TEXT",
    }
    existing = {row["name"] for row in connection.execute("PRAGMA table_info(corrections)")}
    for column, sql_type in extras.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE corrections ADD COLUMN {column} {sql_type}")


def validate_evidence_record(record: object) -> dict:
    if not isinstance(record, dict) or set(record) != SEED_FIELDS:
        raise InvalidEvidenceRecord("Evidence entry must contain exactly the canonical seed fields")
    for field in ("id", "claim_text", "reference_verdict", "source_name", "source_url", "notes"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise InvalidEvidenceRecord(f"Missing/empty field: {field}")
    if not re.fullmatch(r"EV-\d{3}", record["id"]):
        raise InvalidEvidenceRecord("Evidence ID must use EV-001 format")
    if record["reference_verdict"] not in REFERENCE_VERDICTS:
        raise InvalidEvidenceRecord("Unexpected reference verdict")
    parsed = urlsplit(record["source_url"])
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise InvalidEvidenceRecord("Evidence source must be an absolute HTTPS URL")
    if record["published_date"] is not None:
        if not isinstance(record["published_date"], str):
            raise InvalidEvidenceRecord("Published date must be ISO yyyy-mm-dd or null")
        try:
            parsed_date = date.fromisoformat(record["published_date"])
        except ValueError as e:
            raise InvalidEvidenceRecord("Invalid published_date") from e
        if parsed_date.isoformat() != record["published_date"]:
            raise InvalidEvidenceRecord("Non-canonical published_date")
    if record["reviewed_by"] is not None:
        raise InvalidEvidenceRecord("Seed records cannot claim a VeriLoop human review")
    return record


def load_evidence(seed_path: str | Path = DEFAULT_SEED_PATH) -> list[dict]:
    """Read a provenance-labeled snapshot. Never fetch evidence from the network."""
    data = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("collection") != "verification_library" or not isinstance(data.get("records"), list):
        raise InvalidEvidenceRecord("Expected verification_library records")
    records = [validate_evidence_record(item) for item in data["records"]]
    ids = [item["id"] for item in records]
    if len(ids) != len(set(ids)):
        raise InvalidEvidenceRecord("Duplicate evidence IDs")
    return records


def seed_evidence(connection: sqlite3.Connection, seed_path: str | Path = DEFAULT_SEED_PATH) -> int:
    """Insert missing records only, never silently overwrite an existing review/source.

    Returns how many NEW records were inserted; running again should return zero.
    """
    records = load_evidence(seed_path)
    with connection:
        before = connection.total_changes
        for r in records:
            connection.execute(
                """INSERT INTO evidence
                 (id, claim_text, reference_verdict, source_name, source_url,
                  published_date, reviewed_by, notes)
                 VALUES (:id, :claim_text, :reference_verdict, :source_name, :source_url,
                         :published_date, :reviewed_by, :notes)
                 ON CONFLICT(id) DO NOTHING""",
                r,
            )
        return connection.total_changes - before


def list_evidence(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Read-only display of the curated reference library (not a verdict for a video)."""
    return connection.execute(
        """SELECT id, claim_text, reference_verdict, source_name,
                  source_url, published_date, reviewed_by, notes
           FROM evidence ORDER BY id"""
    ).fetchall()
