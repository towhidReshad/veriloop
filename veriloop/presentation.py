"""Safe, plain-language presentation of VeriLoop preliminary retrieval results.

This module only changes copy and counts; it never decides whether a claim,
video, or channel is true or false.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ResultSummary:
    candidates: int
    related: int
    unmatched: int


def summarize(assessments: Sequence) -> ResultSummary:
    """Count claim-level retrieval outcomes without inventing a truth score."""
    related = sum(1 for item in assessments if item.preliminary_state == "POSSIBLE_EVIDENCE_MATCH")
    return ResultSummary(
        candidates=len(assessments),
        related=related,
        unmatched=sum(1 for item in assessments if item.preliminary_state == "INSUFFICIENT_EVIDENCE"),
    )


def has_conflicting_wording(assessment) -> bool:
    """Surface differences in negation even when references share keywords."""
    from .matching import has_polarity_conflict

    return any(
        has_polarity_conflict(assessment.candidate.text, match.reference_claim)
        for match in getattr(assessment, "matches", ())
        if isinstance(getattr(match, "reference_claim", None), str)
    )


def friendly_status(state: str) -> str:
    return {
        "POSSIBLE_EVIDENCE_MATCH": "Related sources found",
        "PREVIOUSLY_REVIEWED_CONTEXT_MATCH": "Previously reviewed context found",
        "INSUFFICIENT_EVIDENCE": "Not enough matching evidence",
        "ERROR_RETRIEVING_DATA": "Couldn't complete the check",
    }.get(state, "Further review needed")


def friendly_explanation(assessment) -> str:
    """Interpret *retrieval*, never change the actual engine state."""
    state = assessment.preliminary_state
    stance = assessment.candidate.stance
    if state == "POSSIBLE_EVIDENCE_MATCH":
        if has_conflicting_wording(assessment):
            return (
                "A stored source discusses the same topic, but negation differs "
                "between the reference claim and the video statement. This is "
                "not supporting evidence or a verdict; examine what the "
                "publisher actually concluded."
            )
        if stance in ("DEBUNKS", "QUOTES", "UNCLEAR"):
            return (
                "Published sources discuss a similar claim, but this video may "
                "be quoting or challenging it. We cannot infer what the uploader believes."
            )
        return (
            "We found published material about a similar claim. The exact wording, "
            "event and video context still need checking before any conclusion."
        )
    if state == "PREVIOUSLY_REVIEWED_CONTEXT_MATCH":
        return (
            "An earlier reviewed context may be relevant. Check the original "
            "review and its event details; this is not a new verdict about the video."
        )
    if state == "INSUFFICIENT_EVIDENCE":
        return (
            "Our small reference library has no sufficiently related source for "
            "this statement. This does not mean it is false."
        )
    return "The evidence check could not finish. No factual assessment was made."
