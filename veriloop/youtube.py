"""Official YouTube metadata retrieval (VeriLoop F-01/F-02, Day 1).

No transcript/audio/thumbnail analysis and no misinformation verdict is implied.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import parse_qs, urlsplit

import requests


_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_WATCH_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
_SHORT_HOSTS = {"youtu.be", "www.youtu.be"}
_YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeError(Exception):
    """Base class for controlled errors surfaced to the Streamlit user."""


class InvalidYouTubeURL(YouTubeError):
    """URL is not a supported public YouTube video link."""


class MissingAPIKey(YouTubeError):
    """Live YouTube lookup requires a configured API key."""


class VideoUnavailableError(YouTubeError):
    """YouTube did not return publicly accessible metadata for the video."""


class YouTubeAPIError(YouTubeError):
    """Request, quota, authentication or response format error."""


@dataclass(frozen=True)
class VideoMetadata:
    video_id: str
    title: str
    description: str
    thumbnail_url: str | None
    channel_id: str | None
    channel_name: str | None
    published_at: str | None
    watch_url: str


def extract_video_id(url: str) -> str:
    """Parse supported watch, mobile, Shorts and youtu.be URLs safely.

    A video ID is a platform identifier, not proof that a video exists or is public.
    """
    if not isinstance(url, str) or not url.strip():
        raise InvalidYouTubeURL("Enter a YouTube video URL.")
    value = url.strip()
    if not re.match(r"^https?://", value, flags=re.IGNORECASE):
        # Support typical scheme-less pasted URLs, not arbitrary unsupported schemes.
        if value.startswith("//") or "://" in value:
            raise InvalidYouTubeURL("Use a standard YouTube http(s) URL.")
        value = f"https://{value}"

    try:
        parts = urlsplit(value)
        hostname = (parts.hostname or "").lower()
        if (
            parts.scheme.lower() not in {"http", "https"}
            or parts.username is not None
            or parts.password is not None
            or parts.port is not None
        ):
            raise InvalidYouTubeURL("Invalid YouTube URL format.")
    except ValueError as exc:
        raise InvalidYouTubeURL("Invalid YouTube URL format.") from exc

    path = parts.path.strip("/")
    if hostname in _WATCH_HOSTS and path == "watch":
        videos = parse_qs(parts.query, keep_blank_values=True).get("v", [])
        if len(videos) != 1:
            raise InvalidYouTubeURL("A YouTube watch link must contain one video ID.")
        video_id = videos[0]
    elif hostname in _WATCH_HOSTS and path.startswith("shorts/"):
        sections = path.split("/")
        if len(sections) != 2:
            raise InvalidYouTubeURL("Invalid YouTube Shorts path.")
        video_id = sections[1]
    elif hostname in _SHORT_HOSTS and path:
        sections = path.split("/")
        if len(sections) != 1:
            raise InvalidYouTubeURL("Invalid youtu.be link.")
        video_id = sections[0]
    else:
        raise InvalidYouTubeURL(
            "Use a youtube.com/watch, youtube.com/shorts, or youtu.be video link."
        )

    if not _VIDEO_ID.fullmatch(video_id):
        raise InvalidYouTubeURL("YouTube video ID must have 11 valid characters.")
    return video_id


def _thumbnail(snippet: dict[str, Any]) -> str | None:
    thumbs = snippet.get("thumbnails") or {}
    if not isinstance(thumbs, dict):
        return None
    for quality in ("maxres", "standard", "high", "medium", "default"):
        item = thumbs.get(quality)
        if isinstance(item, dict):
            url = item.get("url")
            if isinstance(url, str) and url.startswith("https://"):
                return url
    return None


def fetch_video_metadata(
    url_or_id: str,
    api_key: str | None,
    *,
    session: requests.Session | None = None,
    timeout: float = 10.0,
) -> VideoMetadata:
    """Fetch the real snippet from YouTube Data API v3 (videos.list).

    The injectable session permits offline, mocked tests. This function never
    invents metadata or falls back silently to an unrelated/cached video.
    """
    video_id = (
        url_or_id
        if isinstance(url_or_id, str) and _VIDEO_ID.fullmatch(url_or_id)
        else extract_video_id(url_or_id)
    )
    if not api_key or not api_key.strip():
        raise MissingAPIKey(
            "YOUTUBE_API_KEY is not configured. Add your key to a local .env file "
            "to enable live YouTube metadata lookup."
        )
    client = session if session is not None else requests.Session()
    try:
        response = client.get(
            _YOUTUBE_API_URL,
            params={"part": "snippet", "id": video_id, "key": api_key.strip()},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as exc:
        raise YouTubeAPIError("YouTube request timed out. Retry later.") from exc
    except requests.RequestException as exc:
        # Do not leak response URLs: an API key may be in the query string.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        msg = (
            "YouTube rejected the metadata request (HTTP "
            f"{status}). Check API-key access, quota, and video availability."
            if status is not None
            else "Unable to contact the YouTube API. Check network connectivity."
        )
        raise YouTubeAPIError(msg) from exc
    except ValueError as exc:
        raise YouTubeAPIError("YouTube returned an invalid JSON response.") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise YouTubeAPIError("YouTube returned an unexpected response structure.")
    items = payload["items"]
    if not items:
        raise VideoUnavailableError(
            "No accessible video metadata was returned. The video may be "
            "private, removed, unavailable or have an invalid ID."
        )
    item = next((it for it in items if isinstance(it, dict) and it.get("id") == video_id), None)
    if not item or not isinstance(item.get("snippet"), dict):
        raise YouTubeAPIError("The response did not contain the requested video's snippet.")
    snippet = item["snippet"]
    return VideoMetadata(
        video_id=video_id,
        title=str(snippet.get("title") or ""),
        description=str(snippet.get("description") or ""),
        thumbnail_url=_thumbnail(snippet),
        channel_id=snippet.get("channelId") or None,
        channel_name=snippet.get("channelTitle") or None,
        published_at=snippet.get("publishedAt") or None,
        watch_url=f"https://www.youtube.com/watch?v={video_id}",
    )
