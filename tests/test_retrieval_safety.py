"""Regression tests for conservative metadata matching and unseen-video handling.

All API responses are mocked: these cases do NOT claim live key/network validation.
"""
from types import SimpleNamespace

import pytest

from veriloop.claims import extract_claims
from veriloop.matching import compare_context, retrieve_matches
from veriloop.factcheck import LiveLookup, lookup_factchecks, run_live_fallback


@pytest.mark.parametrize("a,b", [
    ("The eclipse crossed Mexico on April 8, 2024.",
     "The eclipse crossed Mexico on April 9, 2024."),
    ("The eclipse crossed Mexico on 2024-04-08.",
     "The eclipse crossed Mexico on 2024-04-09."),
    ("The eclipse crossed Mexico on 8 April 2024.",
     "The eclipse crossed Mexico on April 9, 2024."),
])
def test_different_calendar_days_never_align(a, b):
    assert compare_context(a, b)[0] == "INCOMPATIBLE"


def test_same_event_date_in_multiple_formats_can_overlap():
    state, note = compare_context(
        "The eclipse crossed Mexico on April 8, 2024.",
        "The eclipse crossed Mexico on 2024-04-08.",
    )
    assert state == "ALIGNED"
    assert "Full event date" in note


def test_same_large_region_different_country_is_unconfirmed():
    status, note = compare_context(
        "The video shows an incident in Canada in 2024.",
        "The video shows an incident in Mexico in 2024.",
    )
    assert status == "UNCONFIRMED"
    assert "places differ" in note


def test_multiple_calendar_dates_abstain():
    status, _ = compare_context(
        "The event was reported April 8, 2024 and revisited April 9, 2024.",
        "The event was reported April 8, 2024.",
    )
    assert status == "UNCONFIRMED"


def test_nasa_and_mislabeled_year_safeguards():
    from veriloop.db import load_evidence
    from veriloop.claims import CandidateClaim
    refs = load_evidence()
    c = CandidateClaim(
        "A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024.",
        "description", "ASSERTS", "unverified",
    )
    assert retrieve_matches(c, refs)[0].evidence_id == "EV-002"
    wrong = CandidateClaim(c.text.replace("2024", "2026"), "description", "ASSERTS", "unverified")
    assert "EV-002" not in [m.evidence_id for m in retrieve_matches(wrong, refs)]


def test_quoted_metadata_is_not_auto_endorsed():
    found = extract_claims(
        "Health discussion", '"Vaccines do not cause autism," said the presenter.'
    )
    assert found
    assert found[0].stance == "QUOTES"


def test_generic_opinion_and_promotion_are_not_claims():
    assert extract_claims("", "There are risks, but the opportunities for human society are enormous.") == []
    assert extract_claims("", "Even if you don't believe one, it can still be interesting to learn about.") == []


def test_uncertain_local_reference_still_allows_live_fallback():
    local = SimpleNamespace(
        candidate=SimpleNamespace(text="A claim about Mexico in 2024."),
        matches=[SimpleNamespace(reference_claim="A claim about Canada in 2024.", context_status="UNCONFIRMED")],
    )
    calls = []
    def lookup(query, key):
        calls.append(query)
        return LiveLookup("NO_RESULTS")
    result = run_live_fallback([local], "PRIVATE-KEY", lookup=lookup)
    assert calls == ["A claim about Mexico in 2024."]
    assert result[0].status == "NO_RESULTS"


def test_precisely_aligned_local_reference_skips_api():
    local = SimpleNamespace(
        candidate=SimpleNamespace(text="The solar eclipse crossed Mexico in 2024."),
        matches=[SimpleNamespace(reference_claim="The solar eclipse crossed Mexico in 2024.", context_status="ALIGNED")],
    )
    def no_call(*_args):
        raise AssertionError("Should not use live API when local aligned lead exists")
    assert run_live_fallback([local], "PRIVATE-KEY", lookup=no_call) == {}


def test_mock_google_fact_check_positive_result_preserves_publisher_provenance():
    class Response:
        status_code = 200
        def json(self):
            return {"claims": [{
                "text": "Childhood vaccines cause autism.",
                "claimReview": [{
                    "publisher": {"name": "Publisher Example"},
                    "url": "https://example.org/fact-check",
                    "reviewDate": "2025-11-19T00:00:00Z",
                    "textualRating": "False",
                }],
            }]}
    def get(_endpoint, **kwargs):
        assert kwargs["params"]["key"] == "PRIVATE-KEY"
        return Response()
    result = lookup_factchecks(
        "Childhood vaccines cause autism.", "PRIVATE-KEY", http_get=get
    )
    assert result.status == "FOUND"
    assert result.articles[0].publisher == "Publisher Example"
    assert result.articles[0].publisher_rating == "False"
    assert result.articles[0].article_url == "https://example.org/fact-check"
    assert result.articles[0].context_status == "UNCONFIRMED"
