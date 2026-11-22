"""Public approved-only history, explained in ordinary language."""
import streamlit as st

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.source_history import get_reviewed_history
from veriloop.ui import apply_theme, site_navigation, page_intro

st.set_page_config(page_title="Reviewed claim history | VeriLoop", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")
apply_theme()
site_navigation()
page_intro(
    "VeriLoop · Reviewed evidence",
    "Reviewed claim history",
    "Explore only claim-specific evidence decisions approved by a human reviewer. "
    "An empty history is not a rating or judgment of any channel.",
)

stored = st.session_state.get("vl_current_result")
known_channel = stored[0].channel_id if stored else ""
with st.form("channel_history_query"):
    channel_id = st.text_input(
        "YouTube channel ID", value=known_channel or "", placeholder="UC...",
        help="If you already checked a video, its channel ID may be filled in automatically.",
    )
    show = st.form_submit_button("View reviewed claims", type="primary")

if show:
    try:
        with connect_db() as conn:
            init_db(conn)
            seed_evidence(conn)
            history = get_reviewed_history(conn, channel_id.strip())
    except ValueError as exc:
        st.warning(str(exc))
    except Exception:
        st.error("We couldn't load the review history. This is a technical error, not a channel verdict.")
    else:
        if not history["channel_name"]:
            st.info("No review requests for this channel were found in our current pilot database. This does not tell us whether the channel is reliable.")
        else:
            st.subheader(history["channel_name"])
            st.metric("Approved claim reviews", history["approved_count"])
            st.caption(
                f"{history['review_requests']} total requests stored for this channel, including pending or rejected ones. "
                "This is not a credibility score or a count of all channel uploads."
            )
            if not history["records"]:
                st.info("No human-approved claim findings are available yet. We don't label this channel true or false.")
            for item in history["records"]:
                with st.container(border=True):
                    st.write("**Claim reviewed:**", item["claim_text"])
                    st.write("**Human-reviewed claim outcome:**", item["reviewed_verdict"])
                    st.caption("Reviewed on: " + item["reviewed_at"])
                    st.write("Original video:", item["video_title"])
                    st.link_button("Open YouTube video", f"https://www.youtube.com/watch?v={item['youtube_id']}")
                    st.write("**Published reference:**", item["reference_claim"])
                    st.write("Source:", item["source_name"])
                    st.link_button("Read source", item["source_url"])
                    with st.expander("Technical provenance and dates"):
                        st.write("Evidence ID:", item["evidence_id"])
                        st.write("Video published:", item["video_published_at"] or "Not available")
                        st.write("Source published:", item["source_published_date"] or "Not confirmed")

st.warning(
    "History covers only the small number of explicitly reviewed claims stored in this pilot. "
    "It is **not** a verdict on the channel or its other videos."
)
st.caption("Free cloud SQLite storage can reset when the app restarts; permanent research decisions require an independent archive.")
