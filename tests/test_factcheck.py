"""Live Fact Check Tools fallback: responses are leads, never video verdicts."""
from types import SimpleNamespace

import pytest

from veriloop.factcheck import LiveLookup, lookup_factchecks, run_live_fallback


class FakeResponse:
    def __init__(self, payload=None, status=200):
        self.payload = payload
        self.status_code = status

    def json(self):
        return self.payload


def hit(text="Vaccines cause autism.", link="https://www.who.int/article"):
    return {
        "text": text,
        "claimReview": [{
            "publisher": {"name": "WHO"},
            "url": link,
            "reviewDate": "2025-12-11T00:00:00Z",
            "textualRating": "False",
        }],
    }


def get_api(response):
    def get(url, **kwargs):
        assert url == "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        assert kwargs["params"]["key"] == "PRIVATE-KEY"
        assert kwargs["timeout"] <= 8
        assert kwargs["allow_redirects"] is False
        return response
    return get


def test_source_link_found_without_video_verdict():
    result = lookup_factchecks(
        "Vaccines cause autism.", "PRIVATE-KEY",
        http_get=get_api(FakeResponse({"claims": [hit()]})),
    )
    assert result.status == "FOUND"
    assert len(result.articles) == 1
    assert result.articles[0].publisher_rating == "False"
    assert result.articles[0].context_status == "UNCONFIRMED"


def test_absent_key_is_unavailable_not_false():
    assert lookup_factchecks("Vaccines cause autism.", None).status == "UNAVAILABLE"


def test_empty_results_are_not_an_accusation():
    assert lookup_factchecks(
        "Vaccines cause autism.", "PRIVATE-KEY",
        http_get=get_api(FakeResponse({"claims": []})),
    ).status == "NO_RESULTS"


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500])
def test_http_errors_never_expose_api_key(status):
    result = lookup_factchecks(
        "Vaccines cause autism.", "PRIVATE-KEY",
        http_get=get_api(FakeResponse(status=status)),
    )
    assert result.status == "ERROR"
    assert "PRIVATE-KEY" not in result.note


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "http://www.who.int/fact",
    "https://localhost/path", "https://user:pw@example.com/page",
])
def test_unsafe_urls_not_rendered(url):
    result = lookup_factchecks(
        "Vaccines cause autism.", "PRIVATE-KEY",
        http_get=get_api(FakeResponse({"claims": [hit(link=url)]})),
    )
    assert result.status == "NO_RESULTS"


def test_explicit_event_year_conflict_excludes_match():
    result = lookup_factchecks(
        "A total solar eclipse crossed Mexico in 2026.", "PRIVATE-KEY",
        http_get=get_api(FakeResponse({
            "claims": [hit("A total solar eclipse crossed Mexico in 2024.")]
        })),
    )
    assert result.status == "NO_RESULTS"


def test_local_match_skips_external_lookup():
    cases = [
        SimpleNamespace(matches=[1], candidate=SimpleNamespace(text="Existing local match")),
        SimpleNamespace(matches=[], candidate=SimpleNamespace(text="Vaccines cause autism.")),
    ]
    queries = []

    def lookup(query, key):
        queries.append(query)
        return LiveLookup("NO_RESULTS")

    outcomes = run_live_fallback(cases, "PRIVATE-KEY", lookup=lookup)
    assert list(outcomes) == [1]
    assert queries == ["Vaccines cause autism."]


def test_no_configured_key_does_not_call_provider():
    case = [SimpleNamespace(matches=[], candidate=SimpleNamespace(text="Vaccines cause autism."))]

    def unexpected(*args):
        raise AssertionError("Missing API key must not make a request")

    assert run_live_fallback(case, None, lookup=unexpected)[0].status == "UNAVAILABLE"


def test_per_video_budget_is_capped_at_five():
    cases = [
        SimpleNamespace(matches=[], candidate=SimpleNamespace(
            text=f"Vaccines cause autism and event number {i}."
        )) for i in range(9)
    ]
    calls = []

    def lookup(query, key):
        calls.append(query)
        return LiveLookup("NO_RESULTS")

    outcomes = run_live_fallback(cases, "PRIVATE-KEY", lookup=lookup)
    assert len(calls) == 5
    assert len(outcomes) == 9
    assert outcomes[8].status == "UNAVAILABLE"


def test_invalid_api_payload_is_a_technical_error():
    result = lookup_factchecks(
        "Vaccines cause autism.", "PRIVATE-KEY",
        http_get=get_api(FakeResponse([1])),
    )
    assert result.status == "ERROR"
