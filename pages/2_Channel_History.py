"""Public channel *reviewed-claims-only* history, no universal trust score."""
import streamlit as st

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.source_history import get_reviewed_history

st.set_page_config(page_title="Channel History | VeriLoop", page_icon="📚")
st.title("Channel reviewed-claim history")
st.caption("Only approved, evidence-linked human decisions appear here. No channel credibility percentage.")
with st.form("channel_history_query"):
    channel_id = st.text_input("Exact YouTube channel ID", placeholder="UC...")
    show = st.form_submit_button("Show approved claim history")

if show:
    try:
        with connect_db() as conn:
            init_db(conn)
            seed_evidence(conn)
            history = get_reviewed_history(conn, channel_id.strip())
    except ValueError as exc:
        st.warning(str(exc))
    except Exception:
        st.error("Technical database error. No channel assessment was produced.")
    else:
        if not history["channel_name"]:
            st.info("No submitted records for that exact channel ID in this local pilot database.")
        else:
            st.subheader(history["channel_name"])
            st.write("**Approved, evidence-linked claim records:**", history["approved_count"])
            st.caption(f"Total review requests currently recorded for this channel: {history['review_requests']} (including pending/rejected). Counts are not prevalence or an accuracy score.")
            if not history["records"]:
                st.info("No human-approved claims are available here. This does not indicate the channel is reliable or unreliable.")
            for item in history["records"]:
                st.markdown("---")
                st.write("**Specific reviewed claim:**", item["claim_text"])
                st.write("**Reviewer-approved finding:**", item["reviewed_verdict"])
                st.caption("Reviewed at: " + item["reviewed_at"])
                st.caption("Video published: " + (item["video_published_at"] or "not available"))
                st.write("Video:", item["video_title"])
                st.link_button("View original video", f"https://www.youtube.com/watch?v={item['youtube_id']}")
                st.write("Linked evidence:", item["reference_claim"])
                st.write("Source:", item["source_name"])
                st.link_button("Read original evidence", item["source_url"])
                st.caption("Source published: " + (item["source_published_date"] or "not confirmed"))

st.warning("A channel may have other videos or claims that have not been reviewed. This is NOT a channel-wide verdict.")
st.caption("Free Streamlit Community Cloud can reset SQLite data when the app restarts. Research decisions require independent durable backups before real use.")
