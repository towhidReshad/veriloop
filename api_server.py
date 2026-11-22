"""Public read-only VeriLoop API for the separate React website.

Does not authorize editorial decisions or expose API credentials. Reviews and
correction exports remain in the existing restricted Streamlit workspace.
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import asdict
from threading import Lock
from time import monotonic

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from veriloop.config import get_factcheck_api_key, get_youtube_api_key
from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.factcheck import run_live_fallback
from veriloop.matching import assess_metadata
from veriloop.youtube import (
    InvalidYouTubeURL, MissingAPIKey, VideoUnavailableError, YouTubeAPIError,
    extract_video_id, fetch_video_metadata,
)

app = FastAPI(title="VeriLoop Public API", version="1.0")
origins = [s.strip() for s in os.getenv(
    "VERILOOP_FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if s.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)

# Small in-process limiter for the public MVP. Production multi-worker deployments
# require a shared rate limiter at the proxy or edge.
_hits: dict[str, list[float]] = {}
_lock = Lock()


class VerificationInput(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


def _rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = monotonic()
    with _lock:
        if len(_hits) > 2000:
            _hits.clear()
        recent = [t for t in _hits.get(ip, []) if now - t < 60]
        if len(recent) >= 12:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again shortly.")
        recent.append(now)
        _hits[ip] = recent


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "veriloop-public-api"}


@app.get("/api/sources")
def sources():
    try:
        with connect_db() as conn:
            init_db(conn)
            seed_evidence(conn)
            rows = list_evidence(conn)
        return {
            "count": len(rows),
            "publishers": sorted({str(row["source_name"]) for row in rows}),
            "note": "External references are not endorsements or judgments about any submitted video.",
        }
    except Exception:
        raise HTTPException(status_code=503, detail="Reference library is temporarily unavailable.")


@app.post("/api/verify")
def verify(body: VerificationInput, request: Request):
    _rate_limit(request)
    try:
        # Validate the URL before any outgoing request or database action.
        extract_video_id(body.url)
        video = fetch_video_metadata(body.url, get_youtube_api_key())
    except InvalidYouTubeURL as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MissingAPIKey:
        raise HTTPException(status_code=503, detail="YouTube lookup is not configured on the server.")
    except VideoUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except YouTubeAPIError:
        raise HTTPException(status_code=502, detail="YouTube metadata lookup failed. Please retry later.")

    try:
        with connect_db() as conn:
            init_db(conn)
            seed_evidence(conn)
            references = [dict(row) for row in list_evidence(conn)]
        assessments = assess_metadata(video.title, video.description, references)
        live = run_live_fallback(assessments, get_factcheck_api_key())
    except Exception:
        raise HTTPException(status_code=503, detail="Evidence service is temporarily unavailable.")

    claims = []
    for i, item in enumerate(assessments):
        online = live.get(i)
        articles = [asdict(a) for a in online.articles] if online else []
        matches = [asdict(m) for m in item.matches]
        claims.append({
            "id": i + 1,
            "text": item.candidate.text,
            "source_field": item.candidate.source_field,
            "stance_cue": item.candidate.stance,
            "preliminary_state": item.preliminary_state,
            "explanation": item.explanation,
            "references": matches,
            "factchecks": articles,
            "online_status": online.status if online else "SKIPPED_LOCAL_CONTEXT",
            "online_note": online.note if online else "A local reference had overlapping context cues.",
            "has_related_sources": bool(matches or articles),
            "verdict": "NOT_DETERMINED",
        })

    return {
        "video": asdict(video),
        "summary": {
            "statements": len(claims),
            "with_related_sources": sum(c["has_related_sources"] for c in claims),
            "without_related_sources": sum(not c["has_related_sources"] for c in claims),
            "overall_verdict": "NOT_DETERMINED",
        },
        "claims": claims,
        "limits": [
            "Only public YouTube title and description were checked, not audio or video frames.",
            "Text similarity and external ratings do not establish a verdict about this upload.",
            "Review decisions and corrections require the restricted human-review workspace.",
        ],
    }

# Optional single-origin release: after `cd web && npm run build`, the Python
# server can serve the generated React site and /api endpoints on one domain.
DIST = Path(__file__).resolve().parent / "web" / "dist"
if DIST.is_dir() and (DIST / "index.html").is_file():
    assets = DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="web-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def react_spa(full_path: str):
        requested = (DIST / full_path).resolve()
        if requested.is_file() and requested.is_relative_to(DIST.resolve()):
            return FileResponse(requested)
        return FileResponse(DIST / "index.html")
