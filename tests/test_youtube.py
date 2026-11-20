"""Deterministic Day 1 YouTube URL/API tests; no external internet required."""
import pytest
import requests

from veriloop.youtube import (
    InvalidYouTubeURL,
    MissingAPIKey,
    VideoUnavailableError,
    YouTubeAPIError,
    extract_video_id,
    fetch_video_metadata,
)

ID = "2MJY_ptQW1o"


@pytest.mark.parametrize("url", [
    f"https://www.youtube.com/watch?v={ID}",
    f"http://youtube.com/watch?v={ID}&t=10",
    f"https://m.youtube.com/watch?v={ID}",
    f"https://youtube.com/shorts/{ID}",
    f"https://www.youtube.com/shorts/{ID}?feature=share",
    f"https://youtu.be/{ID}?si=abc123",
    f"youtu.be/{ID}",
    f"www.youtube.com/watch?v={ID}",
])
def test_supported_urls(url):
    assert extract_video_id(url) == ID


@pytest.mark.parametrize("url", [
    "", "hi", "https://example.com/watch?v=2MJY_ptQW1o",
    "https://youtube.com.evil.example/watch?v=2MJY_ptQW1o",
    "https://www.youtube.com/watch?v=12345",
    "https://www.youtube.com/watch?v=2MJY_ptQW1o&v=AbCdeFGhI1_",
    "https://www.youtube.com/watch?v=2MJY_ptQW1oextra",
    "https://youtu.be/2MJY_ptQW1o/extra",
    "https://youtube.com/shorts/2MJY_ptQW1o/other",
    "https://youtube.com/@someone",
    "javascript:alert(1)",
    "ftp://youtube.com/watch?v=2MJY_ptQW1o",
    "https://user:pass@youtube.com/watch?v=2MJY_ptQW1o",
    "https://youtube.com:8080/watch?v=2MJY_ptQW1o",
])
def test_reject_unsupported_urls(url):
    with pytest.raises(InvalidYouTubeURL):
        extract_video_id(url)


class FakeResponse:
    def __init__(self, payload=None, status=200):
        self.payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"HTTP {self.status_code}")
            err.response = self
            raise err

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append((url, params, timeout))
        if self.error:
            raise self.error
        return self.response


def response_for(video_id=ID):
    return {"items": [{"id": video_id, "snippet": {
        "title": "NASA total solar eclipse", "description": "Official webcast",
        "channelId": "UC_a", "channelTitle": "NASA",
        "publishedAt": "2024-04-08T00:00:00Z",
        "thumbnails": {"high": {"url": "https://i.ytimg.com/vi/example/hqdefault.jpg"}},
    }}]}


def test_fetch_metadata_and_request_contract():
    s = FakeSession(FakeResponse(response_for()))
    video = fetch_video_metadata(f"https://youtu.be/{ID}", "test-key", session=s)
    assert video.video_id == ID
    assert video.title == "NASA total solar eclipse"
    assert video.description == "Official webcast"
    assert video.channel_name == "NASA"
    assert video.published_at == "2024-04-08T00:00:00Z"
    assert video.thumbnail_url.startswith("https://")
    url, params, timeout = s.calls[0]
    assert url == "https://www.googleapis.com/youtube/v3/videos"
    assert params == {"part": "snippet", "id": ID, "key": "test-key"}
    assert timeout == 10.0


def test_missing_api_key_no_request():
    s = FakeSession(FakeResponse(response_for()))
    with pytest.raises(MissingAPIKey, match="YOUTUBE_API_KEY"):
        fetch_video_metadata(ID, "", session=s)
    assert not s.calls


def test_unavailable_video_no_fabrication():
    with pytest.raises(VideoUnavailableError):
        fetch_video_metadata(ID, "key", session=FakeSession(FakeResponse({"items": []})))


def test_api_403_is_technical_not_truth_verdict():
    with pytest.raises(YouTubeAPIError, match="HTTP 403"):
        fetch_video_metadata(ID, "key", session=FakeSession(FakeResponse({"error": {}}, 403)))


def test_api_timeout_caught():
    with pytest.raises(YouTubeAPIError, match="timed out"):
        fetch_video_metadata(ID, "key", session=FakeSession(error=requests.Timeout("timeout")))


def test_api_connection_failure_caught_without_secret():
    with pytest.raises(YouTubeAPIError, match="Unable to contact") as exc:
        fetch_video_metadata(ID, "sensitive-key", session=FakeSession(error=requests.ConnectionError("sensitive-key")))
    assert "sensitive-key" not in str(exc.value)


@pytest.mark.parametrize("bad", [None, {}, {"items": {}}, {"items": [{"id": ID}]}, {"items": [{"id": "notrequested", "snippet": {}}]}])
def test_invalid_response_structure_is_error(bad):
    with pytest.raises(YouTubeAPIError):
        fetch_video_metadata(ID, "key", session=FakeSession(FakeResponse(bad)))


def test_missing_optional_metadata_is_handled():
    video = fetch_video_metadata(ID, "key", session=FakeSession(FakeResponse({"items": [{"id": ID, "snippet": {}}]})))
    assert video.title == ""
    assert video.thumbnail_url is None
    assert video.published_at is None
