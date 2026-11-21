"""A simple public interface over VeriLoop's cautious evidence-retrieval engine."""
from __future__ import annotations

import streamlit as st

from veriloop.config import get_youtube_api_key, get_factcheck_api_key
from veriloop.factcheck import run_live_fallback
from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.matching import assess_metadata
from veriloop.presentation import friendly_explanation, friendly_status, summarize
from veriloop.review import ReviewPolicyError, request_review
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
        help="Use a public YouTube video. We do not inspect its narration, frames or audio.",
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
        except Exception:
            st.error("We got the video details, but the evidence service is temporarily unavailable. No assessment was made.")
        else:
            with st.spinner("Looking for related published fact-checks..."):
                online = run_live_fallback(analyses, get_factcheck_api_key())
            st.session_state["vl_current_result"] = (video, analyses, online)

result = st.session_state.get("vl_current_result")
if result:
    video, analyses = result[:2]
    online = result[2] if len(result) > 2 else {}
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
    live_found = sum(1 for x in online.values() if x.status == "FOUND")
    fully_unmatched = sum(1 for i, a in enumerate(analyses)
                          if not a.matches and online.get(i) and online[i].status == "NO_RESULTS")
    a, b, c = st.columns(3)
    a.metric("Statements found", summary.candidates)
    b.metric("Related references", summary.related + live_found)
    c.metric("No close match", fully_unmatched)
    st.info(
        "We compare statements with 13 curated references and, where no local match exists, "
        "search Google's indexed fact-check publications. Counts mean **related sources**, "
        "not true/false findings or accuracy scores."
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
            if live and live.status == "FOUND":
                st.markdown("**Related published fact-checks found**")
                st.write(
                    "No matching record was found in our local library, but Google's Fact Check "
                    "index returned potentially related articles. Check the exact statement, "
                    "date and context; we have **not** verified this video."
                )
            elif live and live.status in ("ERROR", "UNAVAILABLE"):
                st.markdown("**Evidence check incomplete**")
                st.write("Local reference matching was inconclusive and the live lookup could not finish.")
            else:
                st.markdown(f"**{friendly_status(assessment.preliminary_state)}**")
                st.write(friendly_explanation(assessment))
            if assessment.matches:
                st.caption("RELATED PUBLISHED SOURCES · NOT A VERIFIED CLAIM VERDICT")
                for match in assessment.matches:
                    st.write("**" + match.source_name + "**")
                    st.write(match.reference_claim)
                    st.link_button("Read the original source", match.source_url)
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
                    st.caption("Text relevance and limited event checks only; publisher's rating is not a verdict about this video.")
            elif live and live.status == "NO_RESULTS":
                st.caption("Live search checked Google's fact-check index; no sufficiently related article was identified. This does **not** establish the claim is false.")
            elif live and live.status in ("ERROR", "UNAVAILABLE"):
                st.warning(live.note)

            with st.expander("Research details · how this result was found"):
                st.write("**Preliminary state:**", assessment.preliminary_state)
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
                except ReviewPolicyError as exc:
                    st.warning(f"Couldn't create this request: {exc}")
                except Exception:
                    st.error("Technical issue: your review request was not saved.")
                else:
                    st.success(
                        f"Review request #{request_id} {'submitted' if new else 'already exists'} · PENDING. "
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
