"""Public deployment probe must not fabricate successful app behavior."""
from types import SimpleNamespace
import requests
from scripts.smoke_deployment import probe_deployment

def response(status=200, body="ok"):
    return SimpleNamespace(status_code=status, text=body)

def test_only_explicit_health_ok_is_confirmed():
    state, msg = probe_deployment(get=lambda url, **kwargs: response())
    assert state == "HEALTHY_ENDPOINT"
    assert "app features were not exercised" in msg

def test_html_or_error_does_not_prove_health():
    for status, body in ((200, "<html>Waking</html>"), (302, "ok"),
                         (403, "ok"), (429, "ok"), (503, "ok")):
        assert probe_deployment(get=lambda url, **kwargs: response(status, body))[0] == "NOT_CONFIRMED"

def test_network_failure_is_reported_without_false_up_claim():
    def no_network(url, **kwargs):
        raise requests.ConnectionError("DNS failure")
    state, msg = probe_deployment(get=no_network)
    assert state == "UNREACHABLE"
    assert "ConnectionError" in msg

def test_must_not_allow_unsafe_hosts_or_paths():
    for url in ("http://veriloop-research.streamlit.app",
                "https://invalid.example",
                "https://user:pass@veriloop-research.streamlit.app",
                "https://veriloop-research.streamlit.app/admin"):
        assert probe_deployment(url, get=lambda *args, **kwargs: response())[0] == "INVALID_TARGET"

def test_requests_have_timeout_and_no_credentials():
    details={}
    def fake(url, **kwargs):
        details.update(kwargs)
        details["url"] = url
        return response()
    assert probe_deployment(get=fake)[0] == "HEALTHY_ENDPOINT"
    assert details["url"] == "https://veriloop-research.streamlit.app/_stcore/health"
    assert details["timeout"] == 15
    assert details["allow_redirects"] is False
    assert "Authorization" not in details["headers"]
