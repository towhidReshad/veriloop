"""F-10: reviewed correction drafting, separate editorial approval, Markdown export.

A source match or a third-party rating is NEVER an approved VeriLoop review.
No public posting, webhook or third-party publishing action is implemented.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone

class CorrectionPolicyError(ValueError):
    pass

_ALLOWED = {"DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED", "EXPORTED"}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _text(text: str, name: str, maximum: int = 5000) -> str:
    if not isinstance(text, str) or not text.strip() or len(text) > maximum:
        raise CorrectionPolicyError(f"{name} must be 1–{maximum} characters")
    return text.strip()

def _review(conn: sqlite3.Connection, review_id: int) -> dict:
    row = conn.execute("""SELECT r.id AS review_id, r.review_status,
        r.reviewed_verdict, r.reviewed_at, r.reviewer_note,
        c.claim_text, c.stance, v.youtube_id, v.title,
        e.id AS evidence_id, e.source_name, e.source_url,
        e.claim_text AS source_claim
        FROM reviews r JOIN claims c ON c.id=r.claim_id
        JOIN videos v ON v.id=c.video_id
        JOIN claim_matches m ON m.claim_id=c.id
        JOIN evidence e ON e.id=m.evidence_id
        WHERE r.id=? AND r.review_status='APPROVED' AND c.stance='ASSERTS'
          AND m.context_status='ALIGNED' AND e.source_url LIKE 'https://%'
        ORDER BY m.similarity_score DESC""", (review_id,)).fetchall()
    for r in row:
        try:
            audit = json.loads(r["reviewer_note"])
        except (TypeError, ValueError):
            continue
        if (isinstance(audit, dict)
            and audit.get("status") == "APPROVED"
            and audit.get("confirmed_context") is True
            and audit.get("verdict") == r["reviewed_verdict"]
            and audit.get("evidence_id") == r["evidence_id"]
            and audit.get("timestamp") == r["reviewed_at"]
            and isinstance(audit.get("reviewer_id"), str)
            and audit["reviewer_id"].strip()):
            return dict(r)
    raise CorrectionPolicyError("Correction requires an active, audited, evidence-linked human-approved claim")

def default_draft(conn: sqlite3.Connection, review_id: int) -> str:
    r = _review(conn, review_id)
    return (
        f"## Correction draft — review #{review_id}\n\n"
        f"**Video:** {r['title']} (YouTube ID: {r['youtube_id']})\n\n"
        f"**Exact reviewed claim:** {r['claim_text']}\n\n"
        f"**Human-reviewed claim-level finding:** {r['reviewed_verdict']}\n\n"
        f"**Original source:** {r['source_name']} — {r['source_url']}\n\n"
        f"**Reference claim examined by source:** {r['source_claim']}\n\n"
        "Editorial explanation (revise before approval):\n\n"
        "This finding applies only to the exact reviewed claim and event context. "
        "It is not a verdict about the whole video or its channel.\n"
    )

def list_corrections(conn: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in conn.execute("""SELECT x.id, x.review_id,
        x.approval_status, x.approved_at, x.export_path, x.drafted_by,
        x.editorial_reviewer, x.editorial_note, x.last_updated_at,
        r.review_status, c.claim_text
        FROM corrections x JOIN reviews r ON r.id=x.review_id
        JOIN claims c ON c.id=r.claim_id ORDER BY x.id DESC""")]

def create_or_edit_draft(conn: sqlite3.Connection, review_id: int,
                         draft_text: str, *, editor_id: str) -> int:
    _review(conn, review_id)
    draft = _text(draft_text, "draft_text")
    editor = _text(editor_id, "editor_id", 80)
    now = _now()
    with conn:
        existing = conn.execute(
            "SELECT id,approval_status FROM corrections WHERE review_id=? ORDER BY id DESC LIMIT 1",
            (review_id,),
        ).fetchone()
        if existing:
            if existing["approval_status"] != "DRAFT":
                raise CorrectionPolicyError("Submitted/approved corrections are immutable; start a new reviewed workflow")
            conn.execute("""UPDATE corrections SET draft_text=?,drafted_by=?,
                last_updated_at=? WHERE id=?""", (draft, editor, now, existing["id"]))
            return int(existing["id"])
        return int(conn.execute("""INSERT INTO corrections
            (review_id,draft_text,approval_status,drafted_by,last_updated_at)
            VALUES (?,?,'DRAFT',?,?)""", (review_id, draft, editor, now)).lastrowid)

def _correction(conn: sqlite3.Connection, correction_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM corrections WHERE id=?", (correction_id,)).fetchone()
    if row is None:
        raise CorrectionPolicyError("Correction draft not found")
    _review(conn, row["review_id"])  # revoked reviews cannot be approved/exported
    return row

def submit_for_approval(conn: sqlite3.Connection, correction_id: int) -> None:
    r = _correction(conn, correction_id)
    if r["approval_status"] != "DRAFT":
        raise CorrectionPolicyError("Only editable drafts can be submitted")
    with conn:
        conn.execute("""UPDATE corrections SET approval_status='PENDING_APPROVAL',
            last_updated_at=? WHERE id=?""", (_now(), correction_id))

def editorial_decision(conn: sqlite3.Connection, correction_id: int, *,
                       approve: bool, editor_id: str, rationale: str) -> None:
    r = _correction(conn, correction_id)
    if r["approval_status"] != "PENDING_APPROVAL":
        raise CorrectionPolicyError("Separate editorial approval requires a submitted draft")
    editor = _text(editor_id, "editor_id", 80)
    if not r["drafted_by"] or editor.casefold() == r["drafted_by"].casefold():
        raise CorrectionPolicyError(
            "Editorial approval requires an independently identified editor distinct from the drafter"
        )
    note = _text(rationale, "editorial_rationale", 1000)
    if len(note) < 25:
        raise CorrectionPolicyError("Editorial decision needs at least 25 characters of rationale")
    status = "APPROVED" if approve else "REJECTED"
    now = _now()
    with conn:
        conn.execute("""UPDATE corrections SET approval_status=?,
            approved_at=?, editorial_reviewer=?, editorial_note=?,
            last_updated_at=? WHERE id=?""",
            (status, now if approve else None, editor, note, now, correction_id))

def markdown_export(conn: sqlite3.Connection, correction_id: int) -> tuple[str,str]:
    r = _correction(conn, correction_id)
    if r["approval_status"] not in ("APPROVED", "EXPORTED"):
        raise CorrectionPolicyError("Only separately approved corrections may be downloaded")
    filename = f"veriloop-correction-{correction_id}.md"
    return filename, (r["draft_text"] +
        f"\n\n---\nCorrection ID: {correction_id} · Review ID: {r['review_id']}"
        f"\nEditorial approval recorded: {r['approved_at']}\n"
        "Manually exported file; not posted to any platform.\n")

def record_export(conn: sqlite3.Connection, correction_id: int) -> None:
    filename, _ = markdown_export(conn, correction_id)
    with conn:
        conn.execute("""UPDATE corrections SET approval_status='EXPORTED',
            export_path=?, last_updated_at=? WHERE id=?""",
            (filename, _now(), correction_id))
