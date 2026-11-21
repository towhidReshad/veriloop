"""Verify a candidate can reach external published-review results with a mocked provider.

This does not constitute a live Google API response or a truth judgment.
"""
from veriloop.matching import assess_metadata
from veriloop.factcheck import lookup_factchecks, run_live_fallback


class ExampleGoogleResponse:
    status_code = 200
    def json(self):
        return {
            "claims": [{
                "text": "The 2024 solar eclipse crossed Mexico on April 8, 2024.",
                "claimReview": [{
                    "publisher": {"name": "Example Fact Check Organization"},
                    "url": "https://example.org/solar-eclipse-factcheck",
                    "reviewDate": "2024-04-09T00:00:00Z",
                    "textualRating": "Supported",
                    "title": "Example review of the eclipse",
                }],
            }]
        }


def test_pipeline_from_unseen_title_to_linked_publisher_response():
    # Empty local library makes this an otherwise-unseen evidence scenario.
    analyses = assess_metadata(
        "The 2024 solar eclipse crossed Mexico on April 8, 2024.",
        "The eclipse was observed by many people.",
        [],
    )
    assert analyses and not analyses[0].matches
    requests = []
    def fake_get(endpoint, **kwargs):
        requests.append((endpoint, kwargs["params"]["query"]))
        return ExampleGoogleResponse()
    def adapter(claim_text, api_key):
        return lookup_factchecks(claim_text, api_key, http_get=fake_get)

    outcome = run_live_fallback(analyses, "TEST-ONLY-API-KEY", lookup=adapter)
    first = outcome[0]
    assert first.status == "FOUND"
    assert len(first.articles) == 1
    match = first.articles[0]
    assert match.article_url == "https://example.org/solar-eclipse-factcheck"
    assert match.publisher == "Example Fact Check Organization"
    assert match.publisher_rating == "Supported"
    assert match.review_date == "2024-04-09T00:00:00Z"
    assert match.context_status in ("ALIGNED", "UNCONFIRMED")
    assert requests and "2024 solar eclipse" in requests[0][1]
    # Publisher's rating remains publisher metadata, not a VeriLoop video verdict.
    assert all(a.preliminary_state == "INSUFFICIENT_EVIDENCE" for a in analyses)


def test_external_no_results_does_not_invent_a_reference():
    analyses = assess_metadata(
        "Vaccines cause autism.", "", [],
    )
    class EmptyGoogle:
        status_code = 200
        def json(self):
            return {"claims": []}
    outcome = run_live_fallback(
        analyses, "TEST-ONLY-API-KEY",
        lookup=lambda claim, key: lookup_factchecks(claim, key, http_get=lambda *a, **k: EmptyGoogle()),
    )
    assert outcome[0].status == "NO_RESULTS"
    assert outcome[0].articles == ()
