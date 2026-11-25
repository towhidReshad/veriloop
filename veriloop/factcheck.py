"""Optional Google Fact Check Tools claims:search fallback for public metadata.

Never use external publisher ratings as VeriLoop verdicts, approved reviews,
or channel-history accusations. Never log or display API keys or raw API errors.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlsplit
import re

import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .matching import compare_context, has_polarity_conflict

API_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
MAX_SEARCHES_PER_VIDEO = 5
MAX_RESULTS_PER_SEARCH = 5
MIN_RELEVANCE = 0.18  # text retrieval heuristic, not a probability

# Public claim-search queries work better when narration about the claim is
# removed. Never drop the factual proposition, explicit negation, year or place.
_ATTRIBUTION_PREFIX = re.compile(
    r"^(?:(?:according to|as reported by)\s+[^,]{3,55},\s*|"
    r"(?:scientific evidence suggests|research suggests|studies show|"
    r"experts say|researchers say|the video claims|the narrator says)\s+that\s+)",
    re.IGNORECASE,
)
_META_PREFIX = re.compile(
    r"^(?:in this video|in this report|in today's episode|the report says)\s*,?\s*",
    re.IGNORECASE,
)


def focused_search_query(claim_text: str) -> str:
    """Produce a conservative searchable proposition from an original claim.

    Preserve critical factual modifiers and polarity. The comparison stage
    *always* receives the original user-video metadata statement.
    """
    original = " ".join(claim_text.split()) if isinstance(claim_text, str) else ""
    result = original
    for _ in range(2):
        before = result
        result = _META_PREFIX.sub("", result)
        result = _ATTRIBUTION_PREFIX.sub("", result)
        if result == before:
            break
    result = result.strip(" \t.,:;")
    if len(result) < 12 or len(result.split()) < 3:
        result = original
    return result[:220]


# Search index wording is often much shorter than a video's complete
# declarative sentence. These are retrieval-only stopwords; the full
# unmodified candidate is still used for contextual verification.
_INDEX_STOPWORDS = frozenset("""
a an the and or but with without in on at of to from for by as this that
these those it its their there here has have had is are was were be been being
will would can could may might did does do no not never
after before when where why how what which who whose into during while
about says said say saying report reports reported video footage clip
shows showing watch live official english news france channel episode
cause causes caused
weren\x27t wasnt weren isn\x27t aren\x27t didn\x27t doesn\x27t
""".split())
_INDEX_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*|\\d{4}")


def index_search_query(claim_text: str) -> str:
    """Concise, auditable discovery query. Never used as a claim verdict.

    Strip broadcaster/title trailers and generic prose, preserving topical
    words in original order. Omitting negation is permitted for broad source
    *retrieval*, never when assessing original claim polarity or stance.
    """
    source = focused_search_query(claim_text).replace("’", "'")
    source = re.split(r"\\s*(?:[|•])\\s*", source, maxsplit=1)[0]
    tokens = [
        word for word in _INDEX_WORD.findall(source)
        if word.casefold().strip("'") not in _INDEX_STOPWORDS
        and len(word) > 2
    ]
    if len(tokens) < 3:
        return source[:150]
    return " ".join(tokens[:9])[:150]



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
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return False
    host = parts.hostname.rstrip(".").lower()
    if host in {"localhost"} or host.endswith((".localhost", ".local")) or "." not in host:
        return False
    try:
        address = ipaddress.ip_address(host)
        return address.is_global
    except ValueError:
        return True


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
    query = index_search_query(claim_text)
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
        return LiveLookup("NO_RESULTS", note="API returned no usable indexed fact-check articles with an original HTTPS link.")
    scores = _relevance_scores(claim_text, [e["checked"] for e in entries])
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
    return LiveLookup("NO_RESULTS", note=(
        f"API returned {len(entries)} linked article candidate(s), but none passed "
        "minimum textual relevance and basic date/location context checks."
    ))


def run_live_fallback(assessments: list, api_key: str | None, *, lookup=lookup_factchecks) -> dict[int, LiveLookup]:
    """Try all unmatched claim candidates; at most five calls in three workers."""
    outcomes: dict[int, LiveLookup] = {}
    pending: list[tuple[int, str]] = []
    for index, assessment in enumerate(assessments):
        # A same-topic local reference with opposite negation is NOT enough
        # to suppress live search. Treat it as a topical lead, not proof.
        # If every local match is context-uncertain, or wording conflicts,
        # still look for outside fact-checks. A shared topic is not a verified event.
        if assessment.matches and any(
            getattr(match, "context_status", "ALIGNED") == "ALIGNED"
            and not (
                isinstance(getattr(match, "reference_claim", None), str)
                and has_polarity_conflict(assessment.candidate.text, match.reference_claim)
            )
            for match in assessment.matches
        ):
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
