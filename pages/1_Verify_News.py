"""VeriLoop Day 3: public YouTube metadata + cautious local evidence retrieval.

A source match is *never* a verified video verdict, channel accusation,
or substitute for approval. Transcript/audio/frame analysis is out of scope.
"""
from __future__ import annotations

import streamlit as st

from veriloop.config import get_youtube_api_key
from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.matching import assess_metadata
from veriloop.youtube import (
    InvalidYouTubeURL,
    MissingAPIKey,
    VideoUnavailableError,
    YouTubeAPIError,
    fetch_video_metadata,
)

st.set_page_config(page_title="Verify News | VeriLoop", page_icon="🔎")
st.title("Verify a YouTube news video")
st.caption("Day 3 pilot · metadata-based claim candidates and local evidence retrieval · no final verdict")

with st.form("metadata_lookup"):
    url = st.text_input("Public YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")
    submitted = st.form_submit_button("Fetch metadata & find related evidence")

if submitted:
    try:
        video = fetch_video_metadata(url, get_youtube_api_key())
    except InvalidYouTubeURL as exc:
        st.error(f"Invalid video URL: {exc}")
    except MissingAPIKey:
        st.warning("YouTube API key is not configured in Streamlit Cloud Secrets.")
    except VideoUnavailableError as exc:
        st.warning(str(exc))
    except YouTubeAPIError as exc:
        st.error(f"Technical retrieval error: {exc}")
    else:
        st.success("Official video metadata retrieved from YouTube Data API v3.")
        st.subheader(video.title or "(No title provided)")
        if video.thumbnail_url:
            st.image(video.thumbnail_url, caption="YouTube thumbnail (display only; not verified)")
        st.write("**Video ID:**", video.video_id)
        st.write("**Channel name:**", video.channel_name or "Unavailable")
        st.write("**Channel ID:**", video.channel_id or "Unavailable")
        st.write("**Published:**", video.published_at or "Unavailable")
        st.write("**Official watch URL:**", video.watch_url)
        with st.expander("Video description (as published)"):
            st.text(video.description or "(Description unavailable)")

        st.divider()
        st.subheader("Candidate factual claims & related sources")
        st.caption(
            "Only available English title/description text is analyzed (up to 5 candidate statements). "
            "The video itself, its audio, and thumbnails are not checked. "
            "An external reference's classification is NOT a verdict about this video."
        )
        try:
            with connect_db() as conn:
                init_db(conn)
                seed_evidence(conn)
                references = [dict(row) for row in list_evidence(conn)]
            analyses = assess_metadata(video.title, video.description, references)
        except Exception:
            # Operational failure is distinct from insufficient evidence.
            st.error("Technical retrieval error: the local evidence engine could not run. No assessment was made.")
        else:
            if not analyses:
                st.info(
                    "No clear declarative factual claim was identified from the available "
                    "English metadata. This does NOT prove the video is accurate or "
                    "claim-free: its narration and footage have not been examined."
                )
            for index, result in enumerate(analyses, 1):
                st.markdown(f"#### Candidate {index}")
                st.write(result.candidate.text)
                st.write("Metadata field:", result.candidate.source_field)
                st.write("Tentative stance:", result.candidate.stance)
                st.caption(result.candidate.stance_note)
                st.write("**Preliminary state:**", result.preliminary_state)
                st.info(result.explanation)
                for match in result.matches:
                    st.write(f"**Reference {match.evidence_id}:** {match.reference_claim}")
                    st.write("Source:", match.source_name)
                    st.link_button("Read original evidence", match.source_url)
                    st.caption("Source publication date: " + (match.published_date or "not confirmed"))
                    st.caption("Context check: " + match.context_status + " — " + match.context_note)
                    st.caption(
                        f"Text retrieval similarity: {match.similarity:.2f} "
                        "(relevance ranking only; NOT truth probability)."
                    )
                    st.caption(
                        "External source class for its OWN reference claim: "
                        + match.external_reference_classification
                        + ". No VeriLoop human review of this video."
                    )
                st.divider()
            st.warning(
                "No submitted video has been declared true, false or misleading. "
                "A text match alone cannot establish an event's identity or the uploader's stance. "
                "Insufficient local evidence does not mean a claim is false."
            )

st.caption(
    "Policy: these are provisional retrieval findings, not approved corrections "
    "or source-history records. Human review is optional and not yet implemented."
)
