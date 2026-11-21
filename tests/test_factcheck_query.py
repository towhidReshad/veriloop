"""Focused live Fact Check queries retain original claim safety and provenance."""
from types import SimpleNamespace
import pytest
from veriloop.factcheck import focused_search_query, lookup_factchecks

@pytest.mark.parametrize(("input_claim", "expected"), [
    ("Scientific evidence suggests that vaccines do not cause autism.",
     "vaccines do not cause autism"),
    ("In this video, scientific evidence suggests that childhood vaccines do not cause autism.",
     "childhood vaccines do not cause autism"),
    ("According to the health ministry, the eclipse crossed Mexico on April 8, 2024.",
     "the eclipse crossed Mexico on April 8, 2024"),
    ("A total eclipse crossed Mexico on April 8, 2024.",
     "A total eclipse crossed Mexico on April 8, 2024"),
])
def test_query_focus_keeps_factual_modifiers(input_claim, expected):
    assert focused_search_query(input_claim) == expected


def test_short_focused_fragment_reverts_to_original():
    original = "Scientific evidence suggests that no."
    assert focused_search_query(original) == original


def test_search_uses_focused_query_but_compares_original():
    seen=[]
    class Response:
        status_code=200
        def json(self):
            return {"claims":[{
                "text":"Vaccines do not cause autism.",
                "claimReview":[{
                    "publisher":{"name":"Independent publisher"},
                    "url":"https://example.org/fact",
                    "reviewDate":"2025-01-01T00:00:00Z",
                    "textualRating":"True",
                }],
            }]}
    def fake_get(url, **kw):
        seen.append(kw["params"]["query"])
        return Response()
    result=lookup_factchecks(
        "Scientific evidence suggests that vaccines do not cause autism.",
        "TEST-KEY",http_get=fake_get)
    assert seen == ["vaccines do not cause autism"]
    assert result.status=="FOUND"
    assert result.articles[0].publisher_rating=="True"
    assert "verdict about this video" in result.note


@pytest.mark.parametrize("host",[
    "127.0.0.2","10.0.0.8","192.168.1.5","172.16.1.1",
    "localhost","test.local","169.254.1.1","::1",
])
def test_private_or_local_factcheck_article_urls_rejected(host):
    from veriloop.factcheck import _safe_article_url
    assert not _safe_article_url(f"https://{host}/example")
