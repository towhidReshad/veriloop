"""A simple public interface over VeriLoop's cautious evidence-retrieval engine."""
from __future__ import annotations

import streamlit as st

from veriloop.config import get_youtube_api_key, get_factcheck_api_key
from veriloop.factcheck import run_live_fallback, focused_search_query
from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.matching import assess_metadata
from veriloop.presentation import friendly_explanation, friendly_status, summarize, has_conflicting_wording
from veriloop.review import ReviewPolicyError, request_review, find_reviewed_exact_context, get_review_request_status
from veriloop.ui import apply_theme, site_navigation, page_intro
from veriloop.youtube import (
    InvalidYouTubeURL, MissingAPIKey, VideoUnavailableError, YouTubeAPIError,
    fetch_video_metadata,
)

st.set_page_config(page_title="Check a video | VeriLoop", page_icon="🔎", layout="wide", initial_sidebar_state="collapsed")
# Invalidate earlier session results when retrieval logic changes; otherwise
# Streamlit can keep showing a previous 0-match analysis after redeployment.
MATCH_ENGINE_VERSION = "2026-11-26-overlapping-anchor-v3"
if st.session_state.get("vl_result_engine_version") != MATCH_ENGINE_VERSION:
    st.session_state.pop("vl_current_result", None)
    st.session_state.pop("vl_selected_claim", None)
    st.session_state["vl_result_engine_version"] = MATCH_ENGINE_VERSION
apply_theme()
site_navigation()
page_intro(
    "VeriLoop · News evidence explorer",
    "Check a YouTube video. See what we found.",
    "Paste a public YouTube news link. We look for candidate factual statements "
    "in the published title and description, then show related original sources "
    "and explain what remains unverified.",
)

with st.form("metadata_lookup"):
    url = st.text_input(
        "YouTube video link", placeholder="https://www.youtube.com/watch?v=...",
        value=st.session_state.pop("vl_prefill_url", ""),
        help="Supports YouTube watch, Shorts, live, youtu.be and embed links for publicly accessible videos. We do not inspect narration, frames or audio.",
    )
    submitted = st.form_submit_button("Check this video", type="primary", use_container_width=True)
st.caption("No account required for a preliminary check · Results are not automatic true/false verdicts · Evidence matcher v3")

if submitted:
    st.session_state.pop("vl_current_result", None)
    st.session_state.pop("vl_selected_claim", None)
    try:
        video = fetch_video_metadata(url, get_youtube_api_key())
    except InvalidYouTubeURL as exc:
        st.error(f"That doesn't look like a valid YouTube video link. {exc}")
    except MissingAPIKey:
        st.warning("The site's YouTube connection is not configured. Please contact the project owner.")
    except VideoUnavailableError as exc:
        st.warning(f"This public video could not be retrieved. {exc}")
    except YouTubeAPIError as exc:
        st.error(f"We couldn't retrieve video details because of a technical issue: {exc}")
    else:
        try:
            with connect_db() as conn:
                init_db(conn)
                seed_evidence(conn)
                references = [dict(row) for row in list_evidence(conn)]
            analyses = assess_metadata(video.title, video.description, references)
            with connect_db() as conn:
                init_db(conn)
                reviewed = {
                    i: result
                    for i, assessment in enumerate(analyses)
                    if (result := find_reviewed_exact_context(conn, video, assessment)) is not None
                }
        except Exception:
            st.error("We got the video details, but the evidence service is temporarily unavailable. No assessment was made.")
        else:
            with st.spinner("Looking for related published fact-checks..."):
                online = run_live_fallback(analyses, get_factcheck_api_key())
            st.session_state["vl_current_result"] = (video, analyses, online, reviewed)
            st.session_state["vl_result_engine_version"] = MATCH_ENGINE_VERSION

result = st.session_state.get("vl_current_result")
if result:
    video, analyses = result[:2]
    online = result[2] if len(result) > 2 else {}
    reviewed = result[3] if len(result) > 3 else {}

    st.markdown("### Video being checked")
    with st.container(border=True):
        image_col, description_col = st.columns([1.05, 1.45], gap="large")
        with image_col:
            if video.thumbnail_url:
                st.image(video.thumbnail_url, use_container_width=True)
            else:
                st.caption("Video thumbnail unavailable")
        with description_col:
            st.markdown("#### " + (video.title or "Untitled video"))
            st.caption("Channel: " + (video.channel_name or "Not available"))
            st.caption("Published: " + (video.published_at or "Date unavailable"))
            st.link_button("Open original video ↗", video.watch_url)
        with st.expander("Original YouTube title, description and IDs"):
            st.write("Video ID:", video.video_id)
            st.write("Channel ID:", video.channel_id or "Unknown")
            st.text_area(
                "Original description (scroll to read)",
                value=video.description or "No description provided",
                height=190,
                disabled=True,
                key=f"vl_video_description_{video.video_id}",
            )
            st.caption("These are YouTube metadata, not verified video/audio or imagery.")

    sources_count = sum(
        bool(a.matches or (online.get(i) and online[i].status == "FOUND"))
        for i, a in enumerate(analyses)
    )
    st.markdown("### Result at a glance")
    with st.container(border=True):
        one, two, three = st.columns(3, gap="medium")
        one.metric("Statements found", len(analyses))
        two.metric("With related sources", sources_count)
        three.metric("Without a match", len(analyses) - sources_count)
        st.info(
            "**Overall assessment: Not determined yet.** A source match does not "
            "prove a claim true or false. We haven't verified the full video, "
            "its spoken narration or footage."
        )
        if not sources_count and analyses:
            st.caption(
                "Why no matching sources? The current local library has only 13 "
                "curated references; Google's published fact-check index is searched "
                "where available. Neither covers every topic or video. "
                "No match means unknown, not false."
            )
        if any(check.status in ("ERROR", "UNAVAILABLE") for check in online.values()):
            st.caption("Some online searches were unavailable. See individual claim details.")

    with st.expander("How is evidence matched?"):
        st.write(
            "VeriLoop extracts up to five possible statements from this video's "
            "published English title and description. It first searches 13 "
            "curated external references using text similarity, then searches "
            "Google's index of published fact-checks when configured and needed."
        )
        st.write(
            "References are leads to investigate, not final verdicts. "
            "Text similarity does not measure truth. A human must check "
            "the exact assertion, uploader stance, event, location and date "
            "before approving a conclusion."
        )

    st.markdown("### Claim-by-claim results")
    st.caption("Select a statement on the left to see its sources and explanation on the right.")
    if analyses:
        if (
            "vl_selected_claim" not in st.session_state
            or not isinstance(st.session_state["vl_selected_claim"], int)
            or st.session_state["vl_selected_claim"] >= len(analyses)
        ):
            st.session_state["vl_selected_claim"] = 0

        list_col, details_col = st.columns([1, 1.15], gap="large")
        with list_col:
            for i, assessment in enumerate(analyses):
                prior = reviewed.get(i)
                live = online.get(i)
                found = bool(assessment.matches or (live and live.status == "FOUND"))
                status = (
                    "Human-reviewed"
                    if prior
                    else "Related sources found" if found
                    else "Not enough evidence"
                )
                icon = "✓" if prior else "◉" if found else "?"
                selected = i == st.session_state["vl_selected_claim"]
                label = f"{'▸ ' if selected else ''}{i + 1}. {assessment.candidate.text}"
                if st.button(
                    label,
                    key=f"vl_claim_select_{video.video_id}_{i}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                ):
                    st.session_state["vl_selected_claim"] = i
                    st.rerun()
                st.caption(f"{icon} {status}")
        with details_col:
            i = st.session_state["vl_selected_claim"]
            assessment = analyses[i]
            live = online.get(i)
            prior = reviewed.get(i)
            with st.container(border=True):
                st.caption(f"CLAIM {i + 1} OF {len(analyses)} · PUBLISHED {assessment.candidate.source_field.upper()}")
                st.markdown("#### " + assessment.candidate.text)
                if prior:
                    st.success("**Previously human-reviewed finding** for this exact video and unchanged metadata.")
                    st.write("**Reviewed conclusion:**", prior["reviewed_verdict"])
                    st.caption("Reviewed on " + prior["reviewed_at"] + " · Evidence record " + prior["evidence_id"])
                    st.link_button("Read reviewed evidence ↗", prior["source_url"])
                elif assessment.matches or (live and live.status == "FOUND"):
                    st.info("**Possible related evidence.** This does not yet confirm support, contradiction or misleading context for this video.")
                else:
                    st.warning("**Not enough evidence to decide.** We found no sufficiently close reference for this statement.")
                st.markdown("**Why this result?**")
                st.write(
                    "An exact-context human decision is available above."
                    if prior
                    else friendly_explanation(assessment)
                )
                if has_conflicting_wording(assessment):
                    st.warning("A related source uses different negation or wording. It may be discussing the opposite claim.")
                if assessment.matches:
                    st.markdown("**Original references from the curated library**")
                    for match in assessment.matches:
                        with st.container(border=True):
                            st.markdown("**" + match.source_name + "**")
                            st.write("**Claim checked by this source:**", match.reference_claim)
                            st.write("**Source's classification of its own claim:**", match.external_reference_classification.replace("_", " ").title())
                            st.caption("Context: " + match.context_status.replace("_", " ").title() + ". " + match.context_note)
                            st.caption("Source publication date: " + (match.published_date or "Not confirmed"))
                            st.link_button("Read original source ↗", match.source_url)
                else:
                    st.caption("Curated library: no matching reference. This does not establish that the claim is false.")
                if live and live.status == "FOUND":
                    st.markdown("**Related published fact-checks (Google index)**")
                    for check in live.articles:
                        with st.container(border=True):
                            st.markdown("**" + check.publisher + "**")
                            st.write("**Claim checked:**", check.checked_claim)
                            st.write("**Publisher's own rating:**", check.publisher_rating or "Not supplied")
                            st.caption("Context: " + check.context_status.replace("_", " ").title())
                            st.caption("Reviewed: " + (check.review_date or "Date not supplied"))
                            st.link_button("Read published fact-check ↗", check.article_url)
                    st.caption("These are external articles about similar claims, not VeriLoop verdicts on this video.")
                elif live and live.status == "NO_RESULTS":
                    st.caption("Google's published fact-check index was checked, but no sufficiently relevant article was found.")
                elif live and live.status in ("ERROR", "UNAVAILABLE"):
                    st.caption("Online fact-check search unavailable: " + live.note)

                with st.expander("Technical details for researchers"):
                    st.write("Preliminary state:", assessment.preliminary_state)
                    st.write("Metadata stance cue:", assessment.candidate.stance)
                    st.caption(assessment.candidate.stance_note)
                    for match in assessment.matches:
                        st.write("Reference:", match.evidence_id, "· Context:", match.context_status)
                        st.write("TF-IDF text similarity (not truth probability):", f"{match.similarity:.2f}")
                    if live:
                        st.write("Fact-check lookup status:", live.status)
                        st.write("Search query:", focused_search_query(assessment.candidate.text))
                        for check in live.articles:
                            st.write("Indexed-source relevance (not truth probability):", f"{check.relevance:.2f}")
                if st.button("Request human review", key=f"review_{video.video_id}_{i}"):
                    try:
                        with connect_db() as conn:
                            init_db(conn)
                            seed_evidence(conn)
                            request_id, new = request_review(conn, video, assessment)
                            stored_status = get_review_request_status(conn, request_id)
                    except ReviewPolicyError as exc:
                        st.warning(f"Couldn't create this request: {exc}")
                    except Exception:
                        st.error("Technical issue: your review request was not saved.")
                    else:
                        st.success(
                            f"Review request #{request_id} {'submitted' if new else 'already exists'} "
                            f"· {stored_status}. This is a review status, not a verdict."
                        )
    else:
        st.caption("No checkable statements were extracted from this metadata.")

    st.markdown("### Notes and limitations")
    st.caption(
        "Research MVP · English YouTube title and description only · No speech, "
        "full video or image verification · No universal channel score · "
        "Unreviewed evidence matches are never automatic misinformation verdicts."
    )
