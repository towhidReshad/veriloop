"""Day 1 public YouTube metadata verification entry point."""
from __future__ import annotations

import streamlit as st

from veriloop.config import get_youtube_api_key
from veriloop.youtube import (
    InvalidYouTubeURL,
    MissingAPIKey,
    VideoUnavailableError,
    YouTubeAPIError,
    fetch_video_metadata,
)

st.set_page_config(page_title="Verify News | VeriLoop", page_icon="🔎")
st.title("Verify a YouTube news video")
st.caption("Day 1: official YouTube metadata only · no factual verdict")

with st.form("metadata_lookup"):
    url = st.text_input("Public YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")
    submitted = st.form_submit_button("Fetch public metadata")

if submitted:
    try:
        video = fetch_video_metadata(url, get_youtube_api_key())
    except InvalidYouTubeURL as exc:
        st.error(f"Invalid video URL: {exc}")
    except MissingAPIKey as exc:
        st.warning(str(exc))
    except VideoUnavailableError as exc:
        st.warning(str(exc))
    except YouTubeAPIError as exc:
        st.error(f"Technical retrieval error: {exc}")
    else:
        st.success("Metadata retrieved directly from YouTube Data API v3.")
        st.subheader(video.title or "(No title provided)")
        if video.thumbnail_url:
            st.image(video.thumbnail_url, caption="YouTube thumbnail (display only; not verified)")
        st.markdown(f"**Video ID:** `{video.video_id}`")
        st.markdown(f"**Channel name:** {video.channel_name or 'Unavailable'}")
        st.markdown(f"**Channel ID:** `{video.channel_id or 'Unavailable'}`")
        st.markdown(f"**Published:** {video.published_at or 'Unavailable'}")
        st.markdown(f"**Official watch URL:** {video.watch_url}")
        st.markdown("**Video description**")
        st.text(video.description or "(Description unavailable)")
        st.info(
            "No claim has been verified. Metadata is not evidence that a headline "
            "is true or false. Evidence matching and review are later P0 steps."
        )

st.caption(
    "Preliminary assessment policy: available evidence may be incomplete; "
    "human review will be optional and cannot guarantee perfect accuracy."
)
