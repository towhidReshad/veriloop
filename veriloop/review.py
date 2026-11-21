"""Day 4 optional human-review requests and explicit, evidence-bound decisions.

No automatic approval is possible. This module is intentionally UI-independent:
reviewer access must be enforced by the Streamlit dashboard *before* calling
decide_review, which also requires an explicit reviewer identity and confirmation.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone

STATES = {"PENDING", "APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"}
VERDICTS = {"SUPPORTED", "CONTRADICTED", "MISLEADING_CONTEXT", "INSUFFICIENT_EVIDENCE"}
VID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class ReviewPolicyError(ValueError):
    """Review workflow rejected an unsafe or inconsistent transition."""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _checked_text(s, name: str, limit: int):
    if not isinstance(s, str) or not s.strip() or len(s) > limit:
        raise ReviewPolicyError(f"{name} must contain 1–{limit} characters")
    return s.strip()


def request_review(conn: sqlite3.Connection, video, assessment) -> tuple[int, bool]:
    """Save a *real retrieved video* and one exact metadata candidate on request.

    Never creates a review of evidence just because a TF-IDF match exists.
    Repeated submissions are idempotent (same YouTube video/claim/stance).
    Returns (review_id, newly_created).
    """
    if not VID.fullmatch(video.video_id):
        raise ReviewPolicyError("Invalid YouTube video ID")
    if not video.channel_id or not isinstance(video.channel_id, str) or len(video.channel_id) > 100:
        raise ReviewPolicyError("A YouTube channel ID is required for an auditable review")
    if assessment.candidate.stance not in {"ASSERTS", "DEBUNKS", "QUOTES", "UNCLEAR"}:
        raise ReviewPolicyError("Unsupported claim stance")
    claim_text = _checked_text(assessment.candidate.text, "claim_text", 350)
    if assessment.preliminary_state not in {"POSSIBLE_EVIDENCE_MATCH", "INSUFFICIENT_EVIDENCE"}:
        raise ReviewPolicyError("Only preliminary retrieval cases can be escalated")
    timestamp = _now()
    with conn:
        conn.execute("INSERT OR IGNORE INTO channels (youtube_channel_id,name,created_at) VALUES (?,?,?)",
                     (video.channel_id, (video.channel_name or "Unknown")[:200], timestamp))
        channel_id = conn.execute("SELECT id FROM channels WHERE youtube_channel_id=?", (video.channel_id,)).fetchone()[0]
        conn.execute("""INSERT OR IGNORE INTO videos
                    (youtube_id,channel_id,title,description,thumbnail_url,published_at,fetched_at)
                    VALUES (?,?,?,?,?,?,?)""", (video.video_id, channel_id, video.title[:500], video.description[:7000],
                    video.thumbnail_url, video.published_at, timestamp))
        vrow = conn.execute("""SELECT id,channel_id,title,description,published_at
                               FROM videos WHERE youtube_id=?""",
                            (video.video_id,)).fetchone()
        if vrow["channel_id"] != channel_id:
            raise ReviewPolicyError("Platform video/channel identifiers disagree")
        # Frozen F-07 provenance is tied to the video metadata at submission.
        # Never reuse a review after publisher edits title, description or
        # publish timestamp. The frozen single-row video schema cannot
        # represent multiple independent snapshots for the same YouTube ID.
        if (vrow["title"] != (video.title or "")[:500]
                or vrow["description"] != (video.description or "")[:7000]
                or vrow["published_at"] != video.published_at):
            raise ReviewPolicyError(
                "This video's published metadata has changed since an earlier review "
                "request. The old review remains tied to its original snapshot; "
                "a new context-specific review cannot be attached automatically."
            )
        existing = conn.execute("""SELECT r.id, c.claim_context
                                   FROM reviews r JOIN claims c ON c.id=r.claim_id
                                   WHERE c.video_id=? AND c.claim_text=? AND c.stance=?
                                   ORDER BY r.id DESC""",
                                (vrow["id"], claim_text, assessment.candidate.stance)).fetchall()
        for previous in existing:
            try:
                old_context = json.loads(previous["claim_context"])
            except (TypeError, ValueError):
                continue
            if (isinstance(old_context, dict)
                    and old_context.get("metadata_field") == assessment.candidate.source_field
                    and old_context.get("title") == (video.title or "")[:500]
                    and old_context.get("published_at") == video.published_at):
                return previous["id"], False
        context = json.dumps({"title": video.title[:500], "published_at": video.published_at,
                              "metadata_field": assessment.candidate.source_field}, ensure_ascii=False)
        claim_id = conn.execute("""INSERT INTO claims (video_id,claim_text,claim_context,stance,created_at)
                                  VALUES (?,?,?,?,?)""",
                                (vrow[0], claim_text, context, assessment.candidate.stance, timestamp)).lastrowid
        aid = conn.execute("""INSERT INTO assessments (claim_id,preliminary_state,explanation,created_at)
                              VALUES (?,?,?,?)""", (claim_id, assessment.preliminary_state,
                              assessment.explanation[:2000], timestamp)).lastrowid
        for match in assessment.matches:
            if match.context_status not in {"ALIGNED", "UNCONFIRMED"}:
                continue
            # Foreign key ensures source is in the versioned evidence library.
            conn.execute("""INSERT INTO claim_matches
                         (claim_id,evidence_id,similarity_score,context_status,created_at)
                         VALUES (?,?,?,?,?)""", (claim_id, match.evidence_id, float(match.similarity),
                         match.context_status, timestamp))
        rid = conn.execute("""INSERT INTO reviews (claim_id,assessment_id,review_status)
                              VALUES (?,?,'PENDING')""", (claim_id, aid)).lastrowid
        return rid, True


def list_review_queue(conn: sqlite3.Connection) -> list[dict]:
    """Sensitive queue; caller MUST first verify reviewer authentication."""
    return [dict(r) for r in conn.execute("""SELECT r.id AS review_id, r.review_status,
        r.reviewed_verdict, r.reviewer_note, r.reviewed_at, c.id AS claim_id,
        c.claim_text, c.stance, c.claim_context, v.youtube_id, v.title,
        v.published_at, ch.youtube_channel_id, ch.name AS channel_name
        FROM reviews r JOIN claims c ON r.claim_id=c.id
        JOIN videos v ON v.id=c.video_id JOIN channels ch ON ch.id=v.channel_id
        ORDER BY CASE WHEN r.review_status='PENDING' THEN 0 ELSE 1 END, r.id DESC""")]


def linked_evidence(conn: sqlite3.Connection, claim_id: int) -> list[dict]:
    return [dict(r) for r in conn.execute("""SELECT m.evidence_id, m.similarity_score,
        m.context_status, e.claim_text, e.reference_verdict, e.source_url,
        e.source_name, e.published_date
        FROM claim_matches m JOIN evidence e ON e.id=m.evidence_id
        WHERE m.claim_id=? ORDER BY m.similarity_score DESC, m.evidence_id""", (claim_id,))]


def decide_review(conn: sqlite3.Connection, review_id: int, status: str, *,
                  reviewer_id: str, note: str, verdict: str | None = None,
                  evidence_id: str | None = None, confirmed_context: bool = False) -> None:
    """Update one human decision with a serialized history of prior decisions.

    APPROVED requires exact-context, direct linked evidence, ASSERTS stance,
    an accountable reviewer and detailed note. No review is auto-approved.
    """
    if status not in STATES or status == "PENDING":
        raise ReviewPolicyError("Invalid completed review status")
    reviewer = _checked_text(reviewer_id, "reviewer_id", 80)
    explanation = _checked_text(note, "reviewer_note", 2000)
    with conn:
        r = conn.execute("""SELECT r.id,r.review_status,r.reviewed_verdict,r.reviewer_note,r.reviewed_at,
                                 c.id AS claim_id,c.stance
                          FROM reviews r JOIN claims c ON c.id=r.claim_id
                          WHERE r.id=?""", (review_id,)).fetchone()
        if not r:
            raise ReviewPolicyError("Review request not found")
        if status == "APPROVED":
            if r[6] != "ASSERTS":
                raise ReviewPolicyError("Only a directly asserted claim can receive an approved verdict")
            if verdict not in VERDICTS:
                raise ReviewPolicyError("Select a valid claim-level verdict")
            if not confirmed_context:
                raise ReviewPolicyError("Reviewer must confirm exact claim, date, event, location and stance")
            if len(explanation) < 25:
                raise ReviewPolicyError("Approval requires at least 25 characters of written rationale")
            match = conn.execute("""SELECT 1 FROM claim_matches m JOIN evidence e ON e.id=m.evidence_id
                                   WHERE m.claim_id=? AND m.evidence_id=? AND m.context_status='ALIGNED'
                                     AND e.source_url LIKE 'https://%'""", (r[5], evidence_id)).fetchone()
            if not match:
                raise ReviewPolicyError("Approval requires linked evidence with aligned context")
        elif verdict is not None or evidence_id is not None:
            raise ReviewPolicyError("Non-approved decisions must not supply a reviewed verdict/evidence")
        previous_history = []
        if r[3]:
            try:
                previous = json.loads(r[3])
                previous_history = previous.get("history", []) if isinstance(previous, dict) else []
                if isinstance(previous, dict):
                    previous_history.append({k: v for k, v in previous.items() if k != "history"})
            except (TypeError, ValueError):
                previous_history.append({"legacy_note": "Earlier human note retained in database"})
        reviewed_at = _now()
        audit = {"reviewer_id": reviewer, "rationale": explanation,
                 "evidence_id": evidence_id if status == "APPROVED" else None,
                 "confirmed_context": bool(confirmed_context) if status == "APPROVED" else False,
                 "verdict": verdict if status == "APPROVED" else None,
                 "status": status, "timestamp": reviewed_at, "history": previous_history}
        conn.execute("""UPDATE reviews SET review_status=?, reviewed_verdict=?, reviewer_note=?,
                       reviewed_at=? WHERE id=?""", (status, verdict if status == "APPROVED" else None,
                       json.dumps(audit, ensure_ascii=False), reviewed_at, review_id))


def find_reviewed_exact_context(conn: sqlite3.Connection, video, assessment) -> dict | None:
    """Read-only F-07 reuse for the SAME video, unchanged metadata and exact claim.

    Intentionally never transfer an approved finding to another video/channel,
    a changed description/title/date, or a quotation/debunk. This safe pilot
    subset is narrower than general cross-video semantic matching.
    """
    candidate = assessment.candidate
    if (getattr(candidate, "stance", None) != "ASSERTS"
            or getattr(candidate, "source_field", None) not in {"title", "description"}
            or not isinstance(getattr(candidate, "text", None), str)
            or not VID.fullmatch(getattr(video, "video_id", "") or "")):
        return None
    rows = conn.execute("""
        SELECT r.id AS review_id, r.review_status, r.reviewed_verdict,
               r.reviewed_at, r.reviewer_note, c.claim_text, c.claim_context,
               c.stance, v.title, v.description, v.published_at,
               ch.youtube_channel_id, e.id AS evidence_id, e.source_name,
               e.source_url, e.published_date, m.context_status
        FROM reviews r
        JOIN claims c ON c.id=r.claim_id
        JOIN videos v ON v.id=c.video_id
        JOIN channels ch ON ch.id=v.channel_id
        JOIN claim_matches m ON m.claim_id=c.id
        JOIN evidence e ON e.id=m.evidence_id
        WHERE v.youtube_id=? AND c.claim_text=? AND c.stance='ASSERTS'
          AND r.review_status='APPROVED' AND r.reviewed_verdict IS NOT NULL
          AND r.reviewed_at IS NOT NULL AND m.context_status='ALIGNED'
          AND e.source_url LIKE 'https://%'
        ORDER BY r.reviewed_at DESC, r.id DESC
    """, (video.video_id, candidate.text)).fetchall()
    for row in rows:
        if (row["title"] != (video.title or "")[:500]
                or row["description"] != (video.description or "")[:7000]
                or row["published_at"] != video.published_at
                or row["youtube_channel_id"] != video.channel_id
                or row["context_status"] != "ALIGNED"):
            continue
        try:
            context = json.loads(row["claim_context"])
            audit = json.loads(row["reviewer_note"])
        except (ValueError, TypeError):
            continue
        if (not isinstance(context, dict) or not isinstance(audit, dict)
                or context.get("title") != row["title"]
                or context.get("published_at") != video.published_at
                or context.get("metadata_field") != candidate.source_field
                or audit.get("status") != "APPROVED"
                or audit.get("verdict") != row["reviewed_verdict"]
                or audit.get("evidence_id") != row["evidence_id"]
                or audit.get("confirmed_context") is not True
                or audit.get("timestamp") != row["reviewed_at"]
                or not isinstance(audit.get("reviewer_id"), str)
                or not audit["reviewer_id"].strip()):
            continue
        # The result contains public source provenance but excludes private
        # reviewer notes, names, and authentication details.
        return {
            "review_id": row["review_id"],
            "reviewed_verdict": row["reviewed_verdict"],
            "reviewed_at": row["reviewed_at"],
            "evidence_id": row["evidence_id"],
            "source_name": row["source_name"],
            "source_url": row["source_url"],
            "source_published_date": row["published_date"],
            "scope": "same_video_unchanged_metadata_and_claim",
        }
    return None
