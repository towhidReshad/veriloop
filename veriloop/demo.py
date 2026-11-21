"""F-12: prepared source-linked professor cases, never fabricated live assessments.

All examples are research *candidates*. Case labels do not imply that
VeriLoop retrieved metadata, reviewed a claim, or made a video verdict.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlsplit

from .youtube import extract_video_id

DEFAULT_CASES = Path(__file__).resolve().parents[1] / "data" / "demo_cases.json"
EXPECTED = {"A", "B", "C"}
SCENARIOS = {
    "A": "MISLEADING_CONTEXT",
    "B": "SUPPORTED",
    "C": "INSUFFICIENT_EVIDENCE",
}

class DemoCaseError(ValueError):
    pass

def _https(url: str) -> bool:
    if not isinstance(url, str):
        return False
    p = urlsplit(url)
    return p.scheme == "https" and bool(p.hostname) and p.username is None and p.password is None

def load_demo_cases(path: str | Path = DEFAULT_CASES) -> list[dict]:
    """Validate public case provenance and explicit non-approval boundaries."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("collection") != "prepared_demo_candidates_only_not_population_sample":
        raise DemoCaseError("This file must contain prepared research cases, not a sample")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != 3:
        raise DemoCaseError("The professor demo requires exactly three case candidates")
    if {c.get("case_id") for c in cases if isinstance(c, dict)} != EXPECTED:
        raise DemoCaseError("Cases A, B and C must each appear once")
    if len({c.get("youtube_id") for c in cases}) != 3:
        raise DemoCaseError("Cases must refer to distinct YouTube IDs")
    for case in cases:
        ident = case["case_id"]
        try:
            video_id = extract_video_id(case["youtube_url"])
        except Exception as exc:
            raise DemoCaseError(f"Invalid YouTube link in case {ident}") from exc
        if video_id != case["youtube_id"] or case.get("scenario") != SCENARIOS[ident]:
            raise DemoCaseError(f"Scenario/video mismatch in case {ident}")
        for field in ("source_record_url",):
            if not _https(case.get(field)):
                raise DemoCaseError(f"Case {ident} requires a traceable HTTPS source")
        if case.get("has_veriloop_approved_review") is not False:
            raise DemoCaseError("Prepared cases must never imply a human-approved review")
        if case.get("editorial_validation") != "UNREVIEWED_RESEARCH_CANDIDATE":
            raise DemoCaseError("Prepared cases must be explicitly unreviewed")
        if not case.get("demo_acceptance_status", "").startswith("PENDING_"):
            raise DemoCaseError("Do not silently declare professor acceptance")
    return sorted(cases, key=lambda c: c["case_id"])

def public_summary(case: dict) -> dict[str, str]:
    """Only display attributes that are supported by the curated source record."""
    return {
        "case_id": case["case_id"],
        "scenario": case["scenario"],
        "youtube_url": case["youtube_url"],
        "source_record_url": case["source_record_url"],
        "target_claim_summary": case["target_claim_summary"],
        "evidence_summary": case["evidence_summary"],
        "live_status": case["live_youtube_api_status"],
        "acceptance": case["demo_acceptance_status"],
        "disclaimer": (
            "Prepared research candidate only. Not a live YouTube API response, "
            "not a VeriLoop claim verdict, and not an approved human review."
        ),
    }
