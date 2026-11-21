"""Conservative, auditable English metadata claim candidates (F-03/F-05).

This is NOT transcript analysis or a truth classifier. Abstain when a metadata
sentence is a headline label, question, advertisement or lacks a proposition.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re
import unicodedata

MAX_CLAIMS = 5
MAX_DESCRIPTION_CHARS = 7000
MAX_SEGMENTS = 48
_VERBS = re.compile(
    r"\b(?:is|are|was|were|has|have|had|will|can|cannot|did|does|do|"
    r"occur(?:s|red)?|cross(?:ed|es)?|move(?:s|d)?|mov(?:es|ed|ing)|"
    r"pass(?:es|ed)?|caus(?:e|es|ed)?|claim(?:s|ed|ing)?|flew|struck|strike(?:s)?|"
    r"predict(?:s|ed)?|show(?:s|ed|ing)?|report(?:s|ed)?|fell|"
    r"fall(?:s|ing)?|found|confirm(?:ed|s)?|alter(?:ed|s)?|"
    r"chang(?:es|ed)?|record(?:ed|s)?|reveal(?:ed|s)?|"
    r"increas(?:es|ed|ing)|decreas(?:es|ed|ing)|set|succeed(?:s|ed)?|"
    r"crash(?:ed|es)?|travel(?:s|ed|ing)?|block(?:s|ed|ing)?|"
    r"misidentif(?:ies|ied)|identif(?:ies|ied)|kill(?:s|ed)?|"
    r"spread(?:s)?|transmit(?:s|ted)?|lead(?:s)?|make(?:s)?|made)\b",
    re.IGNORECASE,
)
_IGNORE = re.compile(
    r"^(?:claims? (?:by|about|on|from)\b|watch|subscribe|follow|like\b|share\b|click|comment|join|"
    r"learn more|visit|read more|download|music\s*:|director\s*:|"
    r"writer\s*:|cast\s*:|stars\s*:|source\s*:|credits?\s*:|"
    r"https?://|www\.|#|(?:🎬|🎵|📺))",
    re.IGNORECASE,
)
_PROMO = re.compile(r"\b(?:full movie|official trailer|hindi dubbed|subscribe|giveaway|lyrical video)\b", re.IGNORECASE)
# Exclude audience-engagement imperatives even when prefixed by broadcast context.
# A request to viewers is not an event-level factual assertion.
_CALL_TO_ACTION = re.compile(
    r"\b(?:send|submit|post|share|leave)\s+(?:(?:us|your)\s+)?(?:your\s+)?(?:questions|comments|feedback)\b"
    r"|\b(?:let us know|ask us your questions)\b",
    re.IGNORECASE,
)
_DEBUNK = re.compile(r"\b(?:fact[\s-]?check(?:ing)?|debunk(?:ed|ing)?|hoax|false claim|misleading claim|myth busted|disproven|not true)\b", re.IGNORECASE)
_QUOTE = re.compile(r"\b(?:allegedly|according to|claims? that|reportedly|alleges? that|a video claims|quoted as|someone says)\b", re.IGNORECASE)
_SENTENCES = re.compile(r"(?:\r?\n)+|(?<=[.!?])\s+(?=[A-Z0-9\"“(])")
_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_WORD = re.compile(r"[A-Za-z]+")
_WATCH_AS = re.compile(r"^(?:watch live with us|watch|join us to watch) as (.+)$", re.IGNORECASE)
# A question is not a factual assertion even when a YouTube title adds a show name
# after its question mark (e.g., "What do experts think? - BBC World Service").
_LEADING_QUESTION = re.compile(
    r"^(?:what|which|who|whom|whose|where|when|why|how|is|are|was|were|do|does|did|can|could|should|would|will|has|have|had)\b[^?]{0,220}\?",
    re.IGNORECASE,
)
_NON_LATIN = re.compile(r"[\u0600-\u06ff\u0900-\u0dff\u1100-\u11ff\u3000-\u9fff\uac00-\ud7af]")


@dataclass(frozen=True)
class CandidateClaim:
    text: str
    source_field: str  # title or description
    stance: str  # ASSERTS, DEBUNKS, QUOTES, UNCLEAR
    stance_note: str


def infer_stance(sentence: str, *, title: str = "") -> tuple[str, str]:
    """Local cue-only label. Never infer that the video actually endorses a claim."""
    sample = (title + " " + sentence).strip()
    if _DEBUNK.search(sample):
        return "DEBUNKS", "Fact-check/debunk cue detected in metadata; not proof of video narration."
    if _QUOTE.search(sentence) or sentence.lstrip().startswith(('"', '“', '‘')):
        return "QUOTES", "Quotation/attribution cue in metadata; no uploader endorsement assumed."
    if "?" in sentence:
        return "UNCLEAR", "Question is not treated as an asserted factual proposition."
    return "ASSERTS", "Declarative metadata sentence; uploader's actual video stance is unverified."


def _clean(text: str) -> str:
    return " ".join(unescape(unicodedata.normalize("NFKC", text or "")).split())


def _plausible(sentence: str) -> bool:
    if not sentence or len(sentence) > 350 or len(sentence) < 12:
        return False
    if _NON_LATIN.search(sentence):
        # Transparent English-only pilot: avoid converting non-English content
        # into an invented English claim.
        return False
    if _IGNORE.search(sentence) or _PROMO.search(sentence) or _CALL_TO_ACTION.search(sentence):
        return False
    # Commentary about feelings, interest or generic opportunities alone does
    # not establish a specific verifiable event.
    if re.search(r"\b(?:interesting to learn about|opportunities for human society are enormous)\b", sentence, re.I):
        return False
    if sentence.rstrip().endswith("?") or _LEADING_QUESTION.search(sentence):
        return False
    stripped = _URL.sub("", sentence).strip()
    if len(_WORD.findall(stripped)) < 3 or not _VERBS.search(stripped):
        return False
    if re.fullmatch(r"[\W\d_]+", stripped):
        return False
    return True


def extract_claims(title: str, description: str, *, max_claims: int = MAX_CLAIMS) -> list[CandidateClaim]:
    """Return at most 5 tentative metadata sentences in deterministic order.

    Heuristics select declarative English statements; no statement is invented
    or 'verified'. A no-claim result is supported and must not be called false.
    """
    if not 0 < max_claims <= MAX_CLAIMS:
        raise ValueError("max_claims must be between 1 and 5")
    raw_title = _clean(title)
    raw_description = (description or "")[:MAX_DESCRIPTION_CHARS]
    parts = [(raw_title, "title")]
    parts.extend((s, "description") for s in _SENTENCES.split(raw_description)[:MAX_SEGMENTS])
    seen: set[str] = set()
    result: list[CandidateClaim] = []
    for text, source_field in parts:
        sentence = _clean(text)
        # Keep an exact substring of a live-event introduction instead of
        # discarding a factual clause just because it begins "Watch ... as".
        watch_intro = _WATCH_AS.match(sentence)
        if watch_intro:
            sentence = watch_intro.group(1)
        if not _plausible(sentence):
            continue
        key = re.sub(r"[^a-z0-9]", "", sentence.lower())
        if key in seen:
            continue
        seen.add(key)
        stance, note = infer_stance(sentence, title=raw_title)
        result.append(CandidateClaim(sentence, source_field, stance, note))
        if len(result) == max_claims:
            break
    return result
