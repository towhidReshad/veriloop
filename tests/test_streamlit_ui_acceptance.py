"""Streamlit UI acceptance checks, isolated from live APIs and owner credentials.

AppTest exercises actual Streamlit page scripts and form/widget interactions.
Mocks provide a fixture video solely for reproducible UI behavior; these tests
do not claim the hosted app or live YouTube/Google APIs were exercised.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from veriloop.youtube import VideoMetadata

ROOT = Path(__file__).resolve().parents[1]


def _text(elements) -> str:
    """Aggregate displayed messages without depending on Streamlit internals."""
    return " ".join(str(item.value) for item in elements)


def _fixture_video() -> VideoMetadata:
    return VideoMetadata(
        video_id="2MJY_ptQW1o",
        title="NASA eclipse video",
        description=(
            "A total solar eclipse crossed Mexico, the United States "
            "and Canada on April 8, 2024."
        ),
        thumbnail_url=None,
        channel_id="UC1234567890",
        channel_name="NASA",
        published_at="2024-04-08T20:20:27Z",
        watch_url="https://www.youtube.com/watch?v=2MJY_ptQW1o",
    )


@pytest.fixture
def isolated_cloud(monkeypatch, tmp_path):
    """Never use the repository's actual on-disk user-review SQLite."""
    monkeypatch.setenv("VERILOOP_DB_PATH", str(tmp_path / "ui_acceptance.db"))
    monkeypatch.delenv("FACTCHECK_API_KEY", raising=False)
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("REVIEWER_PASSWORD", raising=False)


def test_homepage_renders_without_professor_or_research_navigation(isolated_cloud):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not at.exception
    assert "VeriLoop" in " ".join(x.value for x in at.title) or (
        "Paste a video link" in " ".join(x.value for x in at.markdown)
    )
    page_contents = " ".join(x.value for x in at.markdown)
    assert "Professor demo" not in page_contents
    assert "Research dashboard" not in page_contents


def test_invalid_public_video_input_renders_controlled_error(isolated_cloud):
    at = AppTest.from_file(
        str(ROOT / "pages" / "1_Verify_News.py"), default_timeout=20
    ).run()
    assert not at.exception
    at.text_input[0].set_value("https://example.org/not-youtube")
    at.button[0].click().run()
    assert not at.exception
    assert "valid YouTube video link" in _text(at.error)
    assert "reviewed claim verdict" not in " ".join(x.value for x in at.markdown).lower()


def test_mocked_video_shows_preliminary_results_without_verdict(isolated_cloud):
    with (
        patch("veriloop.config.get_youtube_api_key", return_value="TEST-KEY"),
        patch("veriloop.config.get_factcheck_api_key", return_value=None),
        patch("veriloop.youtube.fetch_video_metadata", return_value=_fixture_video()),
    ):
        at = AppTest.from_file(
            str(ROOT / "pages" / "1_Verify_News.py"), default_timeout=20
        ).run()
        at.text_input[0].set_value(
            "https://www.youtube.com/watch?v=2MJY_ptQW1o"
        )
        at.button[0].click().run()
    assert not at.exception
    displayed = " ".join(
        x.value for collection in (at.markdown, at.text, at.info, at.warning)
        for x in collection
        if isinstance(x.value, str)
    )
    assert "NASA eclipse video" in displayed
    assert "A total solar eclipse crossed" in displayed
    # The page must explicitly deny a whole-video verdict, even when
    # the offline fixture has a related local source.
    assert "whole video" in displayed
    assert "human review" in displayed


def test_reviewer_page_stays_locked_without_configured_password(isolated_cloud):
    at = AppTest.from_file(
        str(ROOT / "pages" / "3_Review_Dashboard.py"), default_timeout=20
    ).run()
    assert not at.exception
    assert "locked" in _text(at.warning).lower()
    assert not at.button
    assert not at.selectbox


def test_reviewer_login_wrong_password_cannot_open_workspace(
    isolated_cloud, monkeypatch
):
    monkeypatch.setenv("REVIEWER_PASSWORD", "Test-only reviewer passphrase 2026")
    at = AppTest.from_file(
        str(ROOT / "pages" / "3_Review_Dashboard.py"), default_timeout=20
    ).run()
    assert not at.exception
    assert at.text_input
    at.text_input[0].set_value("definitely-wrong")
    at.button[0].click().run()
    assert not at.exception
    assert "Incorrect reviewer password" in _text(at.error)
    assert not at.selectbox


def test_valid_reviewer_password_unlocks_empty_queue(isolated_cloud, monkeypatch):
    """Known test-only password exposes the restricted queue, no approvals made."""
    password = "Test-only reviewer passphrase 2026"
    monkeypatch.setenv("REVIEWER_PASSWORD", password)
    at = AppTest.from_file(
        str(ROOT / "pages" / "3_Review_Dashboard.py"), default_timeout=20
    ).run()
    assert not at.exception
    at.text_input[0].set_value(password)
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["vl_review_authenticated"] is True
    assert "No requests have been submitted yet" in _text(at.info)
    assert any(button.label == "Lock workspace" for button in at.button)
