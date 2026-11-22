"""Credential-free, bounded public health probe. Not end-to-end app acceptance."""
from __future__ import annotations
import os
from urllib.parse import urlsplit
import requests

DEFAULT_URL = "https://veriloop-research.streamlit.app"
TIMEOUT_SECONDS = 15

def probe_deployment(url: str = DEFAULT_URL, *, get=requests.get) -> tuple[str, str]:
    """Check a pinned Streamlit health URL; do not infer app functionality."""
    p = urlsplit(url.rstrip("/"))
    if (p.scheme != "https" or p.hostname != "veriloop-research.streamlit.app"
            or p.username or p.password or p.port not in (None, 443) or p.path or p.query or p.fragment):
        return "INVALID_TARGET", "Only the exact public VeriLoop HTTPS host is permitted."
    try:
        response = get(
            DEFAULT_URL + "/_stcore/health", timeout=TIMEOUT_SECONDS,
            allow_redirects=False,
            headers={"User-Agent": "VeriLoop-public-health-probe/1.0"},
        )
    except requests.RequestException as exc:
        return "UNREACHABLE", "Public health request failed: " + type(exc).__name__
    if response.status_code == 200 and response.text.strip().lower() == "ok":
        return "HEALTHY_ENDPOINT", "Streamlit public health endpoint returned HTTP 200 and ok; app features were not exercised."
    return ("NOT_CONFIRMED", "Health returned HTTP " + str(response.status_code)
            + " or no expected ok signal; instance may be asleep, starting or unavailable.")

def main() -> int:
    status, message = probe_deployment()
    print("VeriLoop public health: " + status + "\n" + message, flush=True)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fp:
            fp.write("### Public deployment health (informational)\n\n")
            fp.write("**" + status + "** — " + message + "\n\n")
            fp.write("No YouTube analysis, live fact-check, reviewer approval or recovery was tested.\n")
    # Free host availability and network are external to local regression.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
