"""Public metadata verification with nonblocking, optional human-review requests."""
from __future__ import annotations

import streamlit as st

from veriloop.config import get_youtube_api_key
from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.matching import assess_metadata
from veriloop.review import ReviewPolicyError, request_review
from veriloop.youtube import (
    InvalidYouTubeURL, MissingAPIKey, VideoUnavailableError, YouTubeAPIError,
    fetch_video_metadata,
)

st.set_page_config(page_title="Verify News | VeriLoop", page_icon="🔎")
st.title("Verify a YouTube news video")
st.caption("Preliminary metadata claims and related sources · optional review · no final automatic verdict")

with st.form("metadata_lookup"):
    url = st.text_input("Public YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")
    submitted = st.form_submit_button("Fetch metadata & find related evidence")

if submitted:
    st.session_state.pop("vl_current_result", None)
    try:
        video = fetch_video_metadata(url, get_youtube_api_key())
    except InvalidYouTubeURL as exc:
        st.error(f"Invalid video URL: {exc}")
    except MissingAPIKey:
        st.warning("YouTube API key is not configured in private Streamlit Cloud Secrets.")
    except VideoUnavailableError as exc:
        st.warning(str(exc))
    except YouTubeAPIError as exc:
        st.error(f"Technical retrieval error: {exc}")
    else:
        try:
            with connect_db() as conn:
                init_db(conn)
                seed_evidence(conn)
                references = [dict(row) for row in list_evidence(conn)]
            analyses = assess_metadata(video.title, video.description, references)
        except Exception:
            st.error("Evidence engine unavailable: metadata was fetched but no claim assessment was made.")
        else:
            st.session_state["vl_current_result"] = (video, analyses)

result = st.session_state.get("vl_current_result")
if result:
    video, analyses = result
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
        "Only available English title/description is analyzed (up to five candidate statements). "
        "Audio, video and thumbnails are not fact-checked. A reference classification "
        "is not a verdict about this submitted video."
    )
    if not analyses:
        st.info(
            "No clear declarative factual claim was identified from available English metadata. "
            "This does NOT prove the video is accurate or claim-free."
        )
    for index, assessment in enumerate(analyses, 1):
        st.markdown(f"#### Candidate {index}")
        st.write(assessment.candidate.text)
        st.write("Metadata field:", assessment.candidate.source_field)
        st.write("Tentative stance:", assessment.candidate.stance)
        st.caption(assessment.candidate.stance_note)
        st.write("**Preliminary state:**", assessment.preliminary_state)
        st.info(assessment.explanation)
        for match in assessment.matches:
            st.write(f"**Reference {match.evidence_id}:** {match.reference_claim}")
            st.write("Source:", match.source_name)
            st.link_button("Read original evidence", match.source_url)
            st.caption("Source publication date: " + (match.published_date or "not confirmed"))
            st.caption("Context check: " + match.context_status + " — " + match.context_note)
            st.caption(
                f"Text retrieval similarity: {match.similarity:.2f} (relevance ranking ONLY; NOT truth probability)."
            )
            st.caption(
                "External source class for its own reference claim: "
                + match.external_reference_classification
                + ". No automated approval is issued for this video."
            )
        st.caption("If needed, request independent human review of this specific candidate claim. No review is automatic.")
        if st.button("Request human review", key=f"review_{video.video_id}_{index}"):
            try:
                with connect_db() as conn:
                    init_db(conn)
                    seed_evidence(conn)
                    request_id, new = request_review(conn, video, assessment)
            except ReviewPolicyError as exc:
                st.warning(f"Could not create request: {exc}")
            except Exception:
                st.error("Technical database error; review request was not recorded.")
            else:
                st.success(
                    f"Review request #{request_id} {'created' if new else 'already exists'} — PENDING. "
                    "The immediate preliminary report remains unchanged. "
                    "Free cloud storage may reset, so this is not durable archival storage."
                )
        st.divider()
    st.warning(
        "No whole video or channel has been declared true, false or misleading. "
        "A text match cannot prove video stance or identity. Missing local evidence does NOT mean false."
    )

st.caption(
    "This automated report is a preliminary assessment of available evidence, "
    "not a final determination. You can request further review. "
    "Human review does not guarantee perfect accuracy."
)
