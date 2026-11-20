"""Read-only F-08: only explicitly approved claim-level reviews with evidence.

Never expose pending, rejected, or raw reference records as channel accusations.
"""
from __future__ import annotations

import json
import re
import sqlite3


def get_reviewed_history(conn: sqlite3.Connection, youtube_channel_id: str) -> dict:
    if not isinstance(youtube_channel_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{4,100}", youtube_channel_id):
        raise ValueError("Enter an exact YouTube channel ID")
    channel = conn.execute("SELECT id,name FROM channels WHERE youtube_channel_id=?", (youtube_channel_id,)).fetchone()
    if not channel:
        return {"channel_name": None, "approved_count": 0, "review_requests": 0, "records": []}
    count = conn.execute("""SELECT COUNT(*) FROM reviews r
                            JOIN claims c ON c.id=r.claim_id
                            JOIN videos v ON v.id=c.video_id
                            WHERE v.channel_id=?""", (channel[0],)).fetchone()[0]
    rows = conn.execute("""SELECT r.id AS review_id, r.reviewed_verdict, r.reviewed_at,
                       r.reviewer_note, c.id AS claim_id, c.claim_text, c.stance,
                       v.youtube_id, v.title, v.published_at, e.id AS evidence_id,
                       e.source_url,e.source_name,e.published_date,e.claim_text AS reference_claim,
                       m.context_status
                       FROM reviews r JOIN claims c ON c.id=r.claim_id
                       JOIN videos v ON v.id=c.video_id
                       JOIN claim_matches m ON m.claim_id=c.id
                       JOIN evidence e ON e.id=m.evidence_id
                       WHERE v.channel_id=? AND r.review_status='APPROVED'
                         AND r.reviewed_verdict IS NOT NULL AND r.reviewed_at IS NOT NULL
                         AND c.stance='ASSERTS' AND m.context_status='ALIGNED'
                       ORDER BY r.reviewed_at DESC, r.id DESC""", (channel[0],)).fetchall()
    result, seen = [], set()
    for r in rows:
        if r[0] in seen:
            continue
        try:
            data = json.loads(r[3])
        except (TypeError, ValueError):
            continue
        if (not isinstance(data, dict) or data.get('status') != 'APPROVED'
            or data.get('verdict') != r[1] or data.get('evidence_id') != r[10]
            or data.get('confirmed_context') is not True):
            continue
        seen.add(r[0])
        result.append({
            "review_id": r[0], "reviewed_verdict": r[1], "reviewed_at": r[2],
            "claim_text": r[5], "youtube_id": r[7], "video_title": r[8],
            "video_published_at": r[9],
            "evidence_id": r[10], "source_url": r[11], "source_name": r[12],
            "source_published_date": r[13], "reference_claim": r[14],
        })
    return {"channel_name": channel[1], "approved_count": len(result),
            "review_requests": count, "records": result}
