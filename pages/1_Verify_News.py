"""A simple public interface over VeriLoop's cautious evidence-retrieval engine."""
from __future__ import annotations

import streamlit as st

from veriloop.config import get_youtube_api_key, get_factcheck_api_key
from veriloop.factcheck import run_live_fallback, focused_search_query
from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.matching import assess_metadata
from veriloop.presentation import friendly_explanation, friendly_status, summarize, has_conflicting_wording
from veriloop.review import ReviewPolicyError, request_review, find_reviewed_exact_context, get_review_request_status
from veriloop.ui import apply_theme, hero
from veriloop.youtube import (
    InvalidYouTubeURL, MissingAPIKey, VideoUnavailableError, YouTubeAPIError,
    fetch_video_metadata,
)

st.set_page_config(page_title="Check a video | VeriLoop", page_icon="🔎", layout="centered")
apply_theme()
hero(
    "VeriLoop · News evidence explorer",
    "Understand the claim. Explore the evidence.",
    "Paste a public YouTube news link. We will look for factual statements in its published "
    "title and description and show any related sources we can find.",
)

with st.form("metadata_lookup"):
    url = st.text_input(
        "YouTube video link", placeholder="https://www.youtube.com/watch?v=...",
        help="Supports YouTube watch, Shorts, live, youtu.be and embed links for publicly accessible videos. We do not inspect narration, frames or audio.",
    )
    submitted = st.form_submit_button("Find related evidence", type="primary", use_container_width=True)
st.caption("No account required for a preliminary check · Results are not automatic true/false verdicts")

if submitted:
    st.session_state.pop("vl_current_result", None)
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

result = st.session_state.get("vl_current_result")
if result:
    video, analyses = result[:2]
    online = result[2] if len(result) > 2 else {}
    reviewed = result[3] if len(result) > 3 else {}
    st.markdown('''<div class="vl-section-label">01 / Video overview</div>''', unsafe_allow_html=True)
    with st.container(border=True):
        left, right = st.columns([1, 1.2], gap="medium")
        with left:
            if video.thumbnail_url:
                st.image(video.thumbnail_url, use_container_width=True)
            else:
                st.caption("No thumbnail is available")
        with right:
            st.markdown("**Video submitted**")
            st.write(video.title or "(No title provided)")
            st.caption("Channel: " + (video.channel_name or "Not available"))
            st.caption("Published: " + (video.published_at or "Not available"))
            st.link_button("Open original YouTube video", video.watch_url)
        with st.expander("View original metadata"):
            st.write("**Video ID:**", video.video_id)
            st.write("**Channel ID:**", video.channel_id or "Not available")
            st.write("**Video description:**")
            st.text(video.description or "(No description provided)")
            st.caption("Title, description and thumbnail are supplied by YouTube; they have not been independently verified.")

    st.markdown('''<div class="vl-section-label">02 / Preliminary findings</div>''', unsafe_allow_html=True)
    summary = summarize(analyses)
    statements_with_sources = sum(
        1 for i, item in enumerate(analyses)
        if item.matches or (online.get(i) and online[i].status == "FOUND")
    )
    without_sources = summary.candidates - statements_with_sources
    a, b, c = st.columns(3)
    a.metric("Statements examined", summary.candidates)
    b.metric("With related sources", statements_with_sources)
    c.metric("Without source match", without_sources)
    st.info(
        "VeriLoop checks up to five metadata statements chosen for topic relevance "
        "to this video's title and checkable details, not their likelihood of being true. "
        "It searches a small curated reference library first, then Google's index "
        "of published fact-checks when local context is uncertain or unmatched. "
        "These counts measure **retrieval coverage only**, not accuracy or video truth."
    )
    if summary.candidates and without_sources == summary.candidates:
        st.info(
            "**Your video was processed successfully.** No sufficiently related published "
            "fact-check was identified for these candidate statements. Discussions, "
            "interviews and emerging topics may have no indexed fact-check articles. "
            "This is **not** a failed video lookup and **not** evidence that the statements are false."
        )
    if any(x.status in ("ERROR", "UNAVAILABLE") for x in online.values()):
        st.warning("Some live fact-check searches could not run. Those statements remain unresolved; this is not evidence that they are false.")
    if not analyses:
        st.warning(
            "We couldn't identify a clear factual statement in the available English title or description. "
            "That doesn't mean the video is accurate or claim-free: its audio and footage have not been checked."
        )

    for index, assessment in enumerate(analyses, 1):
        with st.container(border=True):
            st.caption(f"STATEMENT {index:02d} · From the published {assessment.candidate.source_field}")
            st.write(assessment.candidate.text)
            live = online.get(index - 1)
            previous_review = reviewed.get(index - 1)
            if previous_review:
                st.success(
                    "**Previously reviewed exact context** — This specific claim was "
                    "approved by a human reviewer for the same video and unchanged "
                    "published metadata. This is a historical claim-level finding, "
                    "not a fresh assessment or a verdict about the entire video."
                )
                st.write("**Previously reviewed claim verdict:**", previous_review["reviewed_verdict"])
                st.caption(
                    "Reviewed: " + previous_review["reviewed_at"]
                    + " · Review #" + str(previous_review["review_id"])
                    + " · Evidence: " + previous_review["evidence_id"]
                )
                st.link_button(
                    "See the original evidence for this reviewed finding",
                    previous_review["source_url"],
                )
                st.caption(
                    "This historical finding is only reused for identical claim text, "
                    "stance, video identity and metadata. Changes require a new review."
                )
            polarity_conflict = has_conflicting_wording(assessment)
            if polarity_conflict:
                st.warning(
                    "**Related topic — different wording or negation.** "
                    "The reference is about a similar topic, but it does not necessarily "
                    "make the same assertion as this video. Check what the publisher concluded."
                )
            if live and live.status == "FOUND":
                st.markdown("**Related published fact-checks found**")
                st.write(
                    "Google's Fact Check index returned potentially related articles, "
                    "in addition to any local topic references shown below. Check the exact statement, "
                    "date and context; we have **not** verified this video."
                )
            elif live and live.status in ("ERROR", "UNAVAILABLE"):
                st.markdown("**Evidence search partly unavailable**")
                st.write(
                    "A live lookup could not finish. Any local reference listed below "
                    "is only a topical retrieval lead, not a validated verdict."
                )
            else:
                st.markdown(
                    "**Related topic, not confirmed support**"
                    if polarity_conflict
                    else f"**{friendly_status(assessment.preliminary_state)}**"
                )
                st.write(friendly_explanation(assessment))
            if assessment.matches:
                st.caption("TOPICALLY RELATED REFERENCE · NOT A VERIFIED CLAIM VERDICT")
                for match in assessment.matches:
                    st.write("**" + match.source_name + "**")
                    st.write("**Reference claim being checked:**", match.reference_claim)
                    st.write(
                        "**The source classifies that reference claim as:**",
                        match.external_reference_classification,
                    )
                    st.caption(
                        "CONTRADICTED means the source rejects its *reference claim*, "
                        "not that this video was found false."
                        if match.external_reference_classification == "CONTRADICTED"
                        else "This classification belongs to the original source's reference claim, not the video."
                    )
                    st.link_button("Read original publication and its conclusion", match.source_url)
                    st.caption("Source published: " + (match.published_date or "Date not confirmed"))
            else:
                st.caption("No closely related record was found in the current curated library.")

            if live and live.status == "FOUND":
                st.caption("LIVE FACT-CHECK SEARCH · GOOGLE'S INDEX OF PUBLISHED FACT-CHECKS")
                for check in live.articles:
                    st.write("**" + check.publisher + "**")
                    st.write("Claim examined by publisher:", check.checked_claim)
                    if check.article_title:
                        st.caption(check.article_title)
                    st.link_button("Read published fact-check", check.article_url)
                    st.caption("Fact-check reviewed: " + (check.review_date or "Date not supplied"))
                    st.caption(
                        "This is an indexed **third-party fact-check** of a published claim. "
                        "It may be about a different context or a quoted claim; its rating "
                        "is **not** VeriLoop's verdict about the submitted video."
                    )
            elif live and live.status == "NO_RESULTS":
                st.caption("Live search checked Google's fact-check index; no sufficiently related article was identified. This does **not** establish the claim is false.")
            elif live and live.status in ("ERROR", "UNAVAILABLE"):
                st.warning(live.note)

            with st.expander("Research details · how this result was found"):
                st.write(
                    "**Displayed claim-level state:**",
                    "PREVIOUSLY_REVIEWED_CONTEXT_MATCH" if previous_review
                    else assessment.preliminary_state,
                )
                st.caption(
                    "The original local evidence assessment remains preliminary. "
                    "A separate historical human decision is shown only when exact "
                    "video and metadata context is unchanged."
                )
                st.write("**Tentative metadata stance:**", assessment.candidate.stance)
                st.caption(assessment.candidate.stance_note)
                st.caption(assessment.explanation)
                for match in assessment.matches:
                    st.write("**Reference ID:**", match.evidence_id)
                    st.write("**Context comparison:**", match.context_status)
                    st.caption(match.context_note)
                    st.write("**TF-IDF similarity (retrieval only):**", f"{match.similarity:.2f}")
                    st.write("**External source's classification of its own claim:**", match.external_reference_classification)
                    st.caption("Similarity is not a probability of misinformation. Source verdicts are not transferred to this video.")
                if live:
                    st.write("**Live fact-check lookup status:**", live.status)
                    st.write("**Search wording sent to fact-check index:**", focused_search_query(assessment.candidate.text))
                    st.caption("The original statement remains unchanged for source context comparison.")
                    for check in live.articles:
                        st.write("**Publisher and its original rating:**", check.publisher, "·", check.publisher_rating or "Not supplied")
                        st.write("**Text retrieval relevance (not truth probability):**", f"{check.relevance:.2f}")
                        st.write("**Limited context status:**", check.context_status)
                        st.caption(check.context_note)
                        st.caption("These live publications are NOT inserted into the approved evidence/reviewer database.")
            st.caption("Want an independent check of this exact statement?")
            if st.button("Request human review", key=f"review_{video.video_id}_{index}"):
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
                        f"· {stored_status}. "
                        "This is the current request workflow status, not a new claim verdict. "
                        "Your preliminary results are unchanged. "
                        "Free cloud storage can reset, so this is not permanent archival storage."
                    )

    st.markdown('''<div class="vl-section-label">03 / What this means</div>''', unsafe_allow_html=True)
    st.warning(
        "VeriLoop has **not** judged this whole video or its channel true, false or misleading. "
        "A related source may concern a quote, a correction or a different event. "
        "A claim-level conclusion requires context checks and human review."
    )

st.markdown(
    '''<p class="vl-footer">Research pilot · English title/description only · No video/audio verification · No channel trust scores · No automatic accusations. Human review is optional and does not guarantee perfect accuracy.</p>''',
    unsafe_allow_html=True,
)
