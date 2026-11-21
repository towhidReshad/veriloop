"""Optional Google Fact Check Tools claims:search fallback for public metadata.

Never use external publisher ratings as VeriLoop verdicts, approved reviews,
or channel-history accusations. Never log or display API keys or raw API errors.
"""
from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlsplit
import re

import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .matching import compare_context

API_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
MAX_SEARCHES_PER_VIDEO = 5
MAX_RESULTS_PER_SEARCH = 5
MIN_RELEVANCE = 0.18  # text retrieval heuristic, not a probability


@dataclass(frozen=True)
class PublishedFactCheck:
    checked_claim: str
    publisher: str
    article_url: str
    article_title: str
    review_date: str | None
    publisher_rating: str | None
    relevance: float
    context_status: str
    context_note: str


@dataclass(frozen=True)
class LiveLookup:
    status: str  # FOUND | NO_RESULTS | UNAVAILABLE | ERROR
    articles: tuple[PublishedFactCheck, ...] = ()
    note: str = ""


def _safe_article_url(url: object) -> bool:
    if not isinstance(url, str) or len(url) > 1800:
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    return (parts.scheme == "https" and bool(parts.hostname)
            and "." in parts.hostname and not parts.username and not parts.password
            and parts.hostname not in ("localhost", "127.0.0.1")
            and not parts.hostname.endswith(".local"))


def _clean_text(value: object, max_length: int = 300) -> str:
    return " ".join(value.split())[:max_length] if isinstance(value, str) else ""


def _relevance_scores(candidate: str, texts: list[str]) -> list[float]:
    if not texts:
        return []
    try:
        vectors = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True).fit_transform([candidate, *texts])
        return [float(x) for x in cosine_similarity(vectors[:1], vectors[1:]).ravel()]
    except ValueError:
        return [0.0] * len(texts)


def lookup_factchecks(claim_text: str, api_key: str | None, *, http_get=None) -> LiveLookup:
    """One bounded request for one claim. Never send full videos or secrets to UI.

    A returned publisher rating is *about the publisher's checked claim*,
    not a judgment about the linked YouTube upload.
    """
    if not isinstance(api_key, str) or not api_key.strip():
        return LiveLookup("UNAVAILABLE", note="The optional live fact-check service is not configured.")
    query = _clean_text(claim_text, 220)
    if len(query) < 12:
        return LiveLookup("NO_RESULTS", note="Not enough claim text for live fact-check search.")
    getter = http_get or requests.get
    try:
        response = getter(
            API_ENDPOINT,
            params={"query": query, "languageCode": "en", "pageSize": MAX_RESULTS_PER_SEARCH, "key": api_key},
            timeout=7,
            allow_redirects=False,
        )
        if response.status_code != 200:
            # Never log response body or URL; those may contain the API key.
            return LiveLookup("ERROR", note=(
                "Live fact-check lookup reached its quota or authorization limit."
                if response.status_code in (401, 403, 429)
                else "Live fact-check service returned an error."
            ))
        payload = response.json()
    except (requests.RequestException, ValueError, TypeError):
        return LiveLookup("ERROR", note="Live fact-check service could not be reached or read.")
    if not isinstance(payload, dict) or not isinstance(payload.get("claims", []), list):
        return LiveLookup("ERROR", note="Live fact-check service returned invalid data.")

    entries: list[dict] = []
    for claim in payload.get("claims", [])[:MAX_RESULTS_PER_SEARCH]:
        if not isinstance(claim, dict):
            continue
        checked = _clean_text(claim.get("text"), 700)
        if not checked:
            continue
        reviews = claim.get("claimReview", [])
        if not isinstance(reviews, list):
            continue
        for review in reviews[:3]:
            if not isinstance(review, dict) or not _safe_article_url(review.get("url")):
                continue
            publisher = review.get("publisher")
            pub_name = _clean_text(publisher.get("name"), 120) if isinstance(publisher, dict) else ""
            entries.append({
                "checked": checked,
                "publisher": pub_name or "Fact-check publisher (name unavailable)",
                "url": review["url"],
                "title": _clean_text(review.get("title"), 200),
                "date": _clean_text(review.get("reviewDate"), 40) or None,
                "rating": _clean_text(review.get("textualRating"), 100) or None,
            })
    if not entries:
        return LiveLookup("NO_RESULTS", note="No indexed, source-linked fact-check articles were returned.")
    scores = _relevance_scores(query, [e["checked"] for e in entries])
    found: list[PublishedFactCheck] = []
    seen: set[tuple[str, str]] = set()
    for ix in sorted(range(len(entries)), key=lambda i: -scores[i]):
        entry = entries[ix]
        if scores[ix] < MIN_RELEVANCE:
            continue
        context, note = compare_context(claim_text, entry["checked"])
        if context == "INCOMPATIBLE":
            continue
        identity = (entry["checked"].casefold(), entry["url"])
        if identity in seen:
            continue
        seen.add(identity)
        found.append(PublishedFactCheck(
            checked_claim=entry["checked"], publisher=entry["publisher"],
            article_url=entry["url"], article_title=entry["title"],
            review_date=entry["date"], publisher_rating=entry["rating"],
            relevance=scores[ix], context_status=context, context_note=note,
        ))
        if len(found) >= MAX_RESULTS_PER_SEARCH:
            break
    if found:
        return LiveLookup("FOUND", tuple(found),
                          "Potentially related published fact-checks; not a verdict about this video.")
    return LiveLookup("NO_RESULTS", note="No sufficiently related indexed fact-checks with compatible basic context were found.")


def run_live_fallback(assessments: list, api_key: str | None, *, lookup=lookup_factchecks) -> dict[int, LiveLookup]:
    """Try all unmatched claim candidates; at most five calls in three workers."""
    outcomes: dict[int, LiveLookup] = {}
    pending: list[tuple[int, str]] = []
    for index, assessment in enumerate(assessments):
        if assessment.matches:
            continue
        if not api_key:
            outcomes[index] = LiveLookup("UNAVAILABLE", note="Live fact-check API key is not configured.")
        elif len(pending) >= MAX_SEARCHES_PER_VIDEO:
            outcomes[index] = LiveLookup("UNAVAILABLE", note="Live search limit reached for this video.")
        else:
            pending.append((index, assessment.candidate.text))
    if pending:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(lookup, query, api_key): index for index, query in pending}
            for future in as_completed(futures):
                try:
                    outcomes[futures[future]] = future.result()
                except Exception:
                    # Suppress sensitive errors and keep other claims unaffected.
                    outcomes[futures[future]] = LiveLookup("ERROR", note="Live search was interrupted. No assessment was made.")
    return outcomes
