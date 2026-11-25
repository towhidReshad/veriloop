"""F-04/F-05: local TF-IDF evidence retrieval and conservative context guards.

Similarity is only retrieval relevance, NEVER a misinformation probability.
Reference verdicts describe source claims, not verdicts about a submitted video.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Mapping, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .claims import CandidateClaim, extract_claims

MIN_SIMILARITY = 0.18  # candidate retrieval heuristic, not empirically calibrated
CHAR_FALLBACK_SIMILARITY = 0.22  # spelling fallback; never truth confidence
_SHARED_ANCHOR = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_NEGATION = re.compile(r"\b(?:not|no|never|cannot|false|fake|misleading|isn't|aren't|doesn't|didn't)\b", re.IGNORECASE)
_REGION_TERMS = {
    "karachi": "pakistan", "gujjar nala": "pakistan", "pakistan": "pakistan",
    "panaji": "india", "goa": "india", "india": "india",
    "mexico": "north_america", "united states": "north_america",
    "canada": "north_america", "north america": "north_america",
    "japan": "japan", "tohoku": "japan", "honshu": "japan",
}


@dataclass(frozen=True)
class EvidenceMatch:
    evidence_id: str
    reference_claim: str
    source_name: str
    source_url: str
    published_date: str | None
    external_reference_classification: str
    similarity: float
    context_status: str  # ALIGNED, UNCONFIRMED
    context_note: str


@dataclass(frozen=True)
class ClaimAssessment:
    candidate: CandidateClaim
    preliminary_state: str  # POSSIBLE_EVIDENCE_MATCH / INSUFFICIENT_EVIDENCE
    matches: tuple[EvidenceMatch, ...]
    explanation: str



_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
           "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
_MONTH_NAME = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_MONTH_FIRST = re.compile(rf"\b({_MONTH_NAME})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*((?:19|20)\d{{2}})\b", re.I)
_DAY_FIRST = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_NAME})\.?\s*,?\s*((?:19|20)\d{{2}})\b", re.I)
_ISO_DATE = re.compile(r"\b((?:19|20)\d{2})-(\d{1,2})-(\d{1,2})\b")

def _event_dates(text: str) -> set[date]:
    """Read explicit full dates in claim text, never source publication dates."""
    found: set[date] = set()
    for month, day, year in _MONTH_FIRST.findall(text):
        try:
            found.add(date(int(year), _MONTHS[month[:3].lower()], int(day)))
        except ValueError:
            continue
    for day, month, year in _DAY_FIRST.findall(text):
        try:
            found.add(date(int(year), _MONTHS[month[:3].lower()], int(day)))
        except ValueError:
            continue
    for year, month, day in _ISO_DATE.findall(text):
        try:
            found.add(date(int(year), int(month), int(day)))
        except ValueError:
            continue
    return found


def _explicit_places(text: str) -> set[str]:
    lower = text.lower()
    return {name for name in _REGION_TERMS if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", lower)}


def _place_groups(text: str) -> set[str]:
    lowered = text.lower()
    found: set[str] = set()
    for name, region in _REGION_TERMS.items():
        if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", lowered):
            found.add(region)
    return found


def has_polarity_conflict(candidate: str, reference: str) -> bool:
    """Conservative lexical cue: one sentence negates a claim, the other does not.

    This is an ambiguity warning, not a full natural-language contradiction test.
    """
    return bool(_NEGATION.search(candidate)) != bool(_NEGATION.search(reference))


def compare_context(candidate: str, reference: str) -> tuple[str, str]:
    """Exclude only explicit conflicting years/regions; otherwise abstain.

    'ALIGNED' just means shared context cues, not confirmed same event.
    The reference text itself, not its publication date, is compared.
    """
    a_year, b_year = set(_YEAR.findall(candidate)), set(_YEAR.findall(reference))
    if len(a_year) > 1 or len(b_year) > 1:
        return "UNCONFIRMED", "Multiple year cues appear; exact event-year context needs manual checking."
    if len(a_year) == 1 and len(b_year) == 1 and a_year.isdisjoint(b_year):
        return "INCOMPATIBLE", f"Different stated event years ({', '.join(sorted(a_year))} vs {', '.join(sorted(b_year))})."
    a_dates, b_dates = _event_dates(candidate), _event_dates(reference)
    if len(a_dates) > 1 or len(b_dates) > 1:
        return "UNCONFIRMED", "Multiple event dates appear; a reviewer must identify the actual event."
    if a_dates and b_dates and a_dates.isdisjoint(b_dates):
        return "INCOMPATIBLE", "Different explicit event dates; no automatic match is assumed."
    a_region, b_region = _place_groups(candidate), _place_groups(reference)
    if len(a_region) > 1 or len(b_region) > 1:
        return "UNCONFIRMED", "Multiple locations/regions appear; event context needs manual checking."
    if len(a_region) == 1 and len(b_region) == 1 and a_region.isdisjoint(b_region):
        return "INCOMPATIBLE", "Different explicit event locations/regions; no match is assumed."
    notes: list[str] = []
    if a_dates and b_dates and a_dates.intersection(b_dates):
        notes.append("Full event date overlaps")
    a_places, b_places = _explicit_places(candidate), _explicit_places(reference)
    if a_places and b_places and a_places.isdisjoint(b_places) and a_region and b_region:
        return "UNCONFIRMED", "Broad region overlaps, but specific places differ; independent context review required."
    if a_year and b_year and a_year.intersection(b_year):
        notes.append("Year cue overlaps")
    if a_region and b_region and a_region.intersection(b_region):
        notes.append("Geographic cue overlaps")
    if has_polarity_conflict(candidate, reference):
        return "UNCONFIRMED", "Different negation/polarity wording; never transfer external reference verdict automatically."
    if notes:
        return "ALIGNED", "; ".join(notes) + ". Exact event/stance still requires review."
    return "UNCONFIRMED", "Event, date, and location are not established as identical by the available metadata."


def _shared_named_anchor(candidate: str, reference: str) -> bool:
    """Only fuzzy-match references with the same distinctive two-word name."""
    a = {m.group().casefold() for m in _SHARED_ANCHOR.finditer(candidate)}
    b = {m.group().casefold() for m in _SHARED_ANCHOR.finditer(reference)}
    return bool(a & b)


def retrieve_matches(
    candidate: CandidateClaim,
    evidence: Sequence[Mapping],
    *,
    top_k: int = 2,
    minimum_similarity: float = MIN_SIMILARITY,
) -> tuple[EvidenceMatch, ...]:
    """Retrieve ranked traceable references, excluding clear date/place conflicts."""
    if top_k <= 0 or not (0 <= minimum_similarity <= 1):
        raise ValueError("Invalid evidence retrieval options")
    if not evidence:
        return ()
    refs = [dict(e) for e in evidence if dict(e).get("claim_text") and dict(e).get("source_url")]
    if not refs:
        return ()
    corpus = [candidate.text] + [str(e["claim_text"]) for e in refs]
    model = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        vectors = model.fit_transform(corpus)
    except ValueError:
        return ()
    scores = cosine_similarity(vectors[0:1], vectors[1:]).ravel()
    # Character n-grams help recover changed spellings and reworded claims.
    # Fallback also requires a shared specific named anchor, never mere topic.
    try:
        fuzzy_vectors = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True
        ).fit_transform(corpus)
        fuzzy_scores = cosine_similarity(fuzzy_vectors[0:1], fuzzy_vectors[1:]).ravel()
    except ValueError:
        fuzzy_scores = [0.0] * len(refs)
    ranking = []
    for ix, record in enumerate(refs):
        word_score = float(scores[ix])
        fuzzy_score = float(fuzzy_scores[ix])
        fallback = (
            minimum_similarity <= MIN_SIMILARITY
            and fuzzy_score >= CHAR_FALLBACK_SIMILARITY
            and _shared_named_anchor(candidate.text, str(record["claim_text"]))
        )
        if word_score >= minimum_similarity or fallback:
            ranking.append((ix, max(word_score, fuzzy_score) if fallback else word_score))
    ranking.sort(key=lambda item: (-item[1], str(refs[item[0]]["id"])))
    matches: list[EvidenceMatch] = []
    for ix, score in ranking:
        record = refs[ix]
        status, note = compare_context(candidate.text, str(record["claim_text"]))
        if status == "INCOMPATIBLE":
            continue
        # Fuzzy-only similarity is a possible lead, NOT validated same-event
        # context, even when broad geographic cues overlap.
        if float(scores[ix]) < minimum_similarity:
            status = "UNCONFIRMED"
            note = "Named-entity spelling/wording lead only; verify exact event and video stance independently. " + note
        matches.append(EvidenceMatch(
            evidence_id=str(record["id"]),
            reference_claim=str(record["claim_text"]),
            source_name=str(record["source_name"]),
            source_url=str(record["source_url"]),
            published_date=record["published_date"],
            external_reference_classification=str(record["reference_verdict"]),
            similarity=score,
            context_status=status,
            context_note=note,
        ))
        if len(matches) == top_k:
            break
    return tuple(matches)


def assess_metadata(title: str, description: str, evidence: Sequence[Mapping]) -> list[ClaimAssessment]:
    """Day 3 preliminary relevance only: never approve a review or video verdict."""
    results: list[ClaimAssessment] = []
    for claim in extract_claims(title, description):
        matches = retrieve_matches(claim, evidence)
        if matches:
            state = "POSSIBLE_EVIDENCE_MATCH"
            if claim.stance in ("DEBUNKS", "QUOTES", "UNCLEAR"):
                explanation = (
                    "Related external sources found, but uploader stance is not an endorsement. "
                    "No misleading label or final verdict can be transferred to the video."
                )
            else:
                explanation = (
                    "Tentative local text match only; compare the exact assertion, dates, "
                    "location and video stance before drawing conclusions."
                )
        else:
            state = "INSUFFICIENT_EVIDENCE"
            explanation = (
                "No sufficiently related, context-compatible local reference found. "
                "This does not mean the claim is false."
            )
        results.append(ClaimAssessment(claim, state, matches, explanation))
    return results
