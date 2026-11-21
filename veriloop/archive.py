"""Private encrypted backup/restore for ephemeral Streamlit SQLite research data.

A download is not automatically persisted. The owner must keep the encrypted
file and passphrase offline. Restores refuse to overwrite current user records.
No public storage, remote sync, or production-grade accounts are provided.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .db import init_db, seed_evidence

MAGIC = b"VLARCH1"
AAD = b"VeriLoop private database backup / v1"
ITERATIONS = 390_000
MAX_SQLITE_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_BYTES = MAX_SQLITE_BYTES + 256
USER_TABLES = ("channels", "videos", "claims", "claim_matches",
               "assessments", "reviews", "corrections")
SCHEMA = {
    "channels": {"id", "youtube_channel_id", "name", "created_at"},
    "videos": {"id", "youtube_id", "channel_id", "title", "description", "published_at", "fetched_at"},
    "claims": {"id", "video_id", "claim_text", "claim_context", "stance", "created_at"},
    "evidence": {"id", "claim_text", "reference_verdict", "source_name", "source_url", "published_date", "reviewed_by", "notes"},
    "claim_matches": {"id", "claim_id", "evidence_id", "similarity_score", "context_status", "created_at"},
    "assessments": {"id", "claim_id", "preliminary_state", "explanation", "created_at"},
    "reviews": {"id", "claim_id", "assessment_id", "review_status", "reviewed_verdict", "reviewer_note", "reviewed_at"},
    "corrections": {"id", "review_id", "draft_text", "approval_status", "approved_at", "export_path"},
}

class ArchiveError(ValueError):
    """Private backup cannot be safely created or restored."""

def _derive_key(passphrase: str, salt: bytes) -> bytes:
    if not isinstance(passphrase, str) or not 16 <= len(passphrase) <= 256:
        raise ArchiveError("Use an independent private passphrase of 16–256 characters")
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, ITERATIONS, dklen=32)

def _check_sqlite(conn: sqlite3.Connection) -> None:
    try:
        objects = conn.execute(
            "SELECT name,type FROM sqlite_master WHERE type IN ('table','view','trigger')"
        ).fetchall()
        if {row[0] for row in objects} != set(SCHEMA) or any(row[1] != "table" for row in objects):
            raise ArchiveError("The backup does not contain the eight canonical tables")
        for table, required in SCHEMA.items():
            cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if not required <= cols:
                raise ArchiveError(f"Backup is missing required {table} fields")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ArchiveError("Backup SQLite integrity check failed")
        if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ArchiveError("Backup contains broken foreign keys")
        valid_review = {"PENDING", "APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"}
        valid_correction = {"DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED", "EXPORTED"}
        statuses = {r[0] for r in conn.execute("SELECT DISTINCT review_status FROM reviews")}
        editorial = {r[0] for r in conn.execute("SELECT DISTINCT approval_status FROM corrections")}
        if not statuses <= valid_review or not editorial <= valid_correction:
            raise ArchiveError("Backup has an unrecognized decision status")
    except sqlite3.DatabaseError as exc:
        raise ArchiveError("Backup database validation failed") from exc

def create_encrypted_backup(conn: sqlite3.Connection, passphrase: str) -> bytes:
    """Encrypt a consistent SQLite snapshot, including any WAL transactions."""
    salt, nonce = os.urandom(16), os.urandom(12)
    key = _derive_key(passphrase, salt)
    with tempfile.TemporaryDirectory(prefix="vl_private_backup_") as folder:
        path = Path(folder) / "archive.db"
        try:
            conn.commit()
            with sqlite3.connect(path) as destination:
                conn.backup(destination)
            if path.stat().st_size > MAX_SQLITE_BYTES:
                raise ArchiveError("Backup exceeds the 8 MB pilot archive limit")
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as check:
                check.execute("PRAGMA foreign_keys=ON")
                _check_sqlite(check)
            payload = path.read_bytes()
        except sqlite3.DatabaseError as exc:
            raise ArchiveError("Unable to make a verified backup") from exc
    return MAGIC + salt + nonce + AESGCM(key).encrypt(nonce, payload, AAD)

def _decrypt(archive: bytes, passphrase: str) -> bytes:
    if (not isinstance(archive, bytes) or not archive.startswith(MAGIC)
            or not len(MAGIC) + 44 <= len(archive) <= MAX_ARCHIVE_BYTES):
        raise ArchiveError("Unsupported encrypted backup file")
    offset = len(MAGIC)
    salt = archive[offset:offset+16]
    nonce = archive[offset+16:offset+28]
    try:
        result = AESGCM(_derive_key(passphrase, salt)).decrypt(nonce, archive[offset+28:], AAD)
    except InvalidTag as exc:
        raise ArchiveError("Wrong passphrase or tampered backup file") from exc
    if len(result) > MAX_SQLITE_BYTES or not result.startswith(b"SQLite format 3\x00"):
        raise ArchiveError("Decrypted content is not a valid-size SQLite snapshot")
    return result

def restore_encrypted_backup(conn: sqlite3.Connection, archive: bytes, passphrase: str) -> None:
    """Restore only into a database with NO user-created records.

    Existing seeded evidence rows are not treated as user submissions.
    Backups are intentionally not imported into arbitrary active databases.
    """
    try:
        if any(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
               for table in USER_TABLES):
            raise ArchiveError("Existing user data detected; restore refuses to overwrite it")
        conn.commit()
    except sqlite3.DatabaseError as exc:
        raise ArchiveError("The destination database cannot be safely checked") from exc

    plaintext = _decrypt(archive, passphrase)
    with tempfile.TemporaryDirectory(prefix="vl_private_restore_") as folder:
        path = Path(folder) / "restored.db"
        path.write_bytes(plaintext)
        try:
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as source:
                source.execute("PRAGMA foreign_keys=ON")
                source.execute("PRAGMA trusted_schema=OFF")
                _check_sqlite(source)
                source.backup(conn)
            init_db(conn)
            seed_evidence(conn)
            conn.commit()
            _check_sqlite(conn)
        except sqlite3.DatabaseError as exc:
            raise ArchiveError("SQLite restore failed; recovery was not confirmed") from exc
