"""VeriLoop welcoming homepage with research details kept accessible."""
import streamlit as st

from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.ui import apply_theme, hero

st.set_page_config(page_title="VeriLoop · Evidence before verdicts", page_icon="🔎", layout="centered")
apply_theme()
hero(
    "VeriLoop · Evidence before verdicts",
    "News moves fast. Evidence matters.",
    "Explore the published claims in a YouTube news video and see where related "
    "source material is available. Easy to use, transparent about uncertainty.",
)

st.markdown('''<div class="vl-section-label">Start here</div>''', unsafe_allow_html=True)
st.page_link("pages/1_Verify_News.py", label="🔎  Check a YouTube news video", use_container_width=True)
st.caption("One link to start · No user account needed for preliminary results")

cols = st.columns(3, gap="medium")
steps = [
    ("01", "Paste a video link", "Use a public YouTube URL. We read the title and description."),
    ("02", "Explore related sources", "See claim-specific evidence links without invented truth ratings."),
    ("03", "Ask for human review", "Optionally send one claim to a restricted reviewer."),
]
for col, (num, heading, description) in zip(cols, steps):
    with col:
        st.markdown(
            f'<div class="vl-step"><div class="vl-number">{num}</div>'
            f'<b>{heading}</b><small>{description}</small></div>',
            unsafe_allow_html=True,
        )

st.markdown('''<div class="vl-section-label">Explore evidence sources</div>''', unsafe_allow_html=True)
try:
    with connect_db() as conn:
        init_db(conn)
        seed_evidence(conn)
        rows = list_evidence(conn)
except Exception:
    st.error("The curated evidence library is unavailable right now. No assessment was made.")
else:
    st.write(f"**{len(rows)} curated reference records** in our small, traceable research library")
    st.caption(
        "These are external publications, not verified judgments about any submitted video. "
        "The collection is selected for demonstration and does not estimate misinformation prevalence."
    )
    with st.expander("Explore original reference publications"):
        for record in rows:
            st.write("**" + record["id"] + " · " + record["claim_text"] + "**")
            st.write("Source:", record["source_name"])
            st.link_button("Read original publication", record["source_url"])
            st.caption("Published: " + (record["published_date"] or "Date not confirmed"))
            st.caption("External classification: " + record["reference_verdict"])
            st.caption("Human review by VeriLoop: none")
            st.divider()

st.markdown('''<div class="vl-section-label">Explore more</div>''', unsafe_allow_html=True)
a, b = st.columns(2)
with a:
    st.page_link("pages/2_Channel_History.py", label="📚  Reviewed claim history")
with b:
    st.page_link("pages/3_Review_Dashboard.py", label="🔒  Reviewer workspace")
st.info(
    "**Important:** We find relevant material, not automatic true/false verdicts. "
    "A similarity score is not the probability that a claim is false."
)
st.markdown(
    '''<p class="vl-footer">VeriLoop is a university research prototype. Only YouTube's public metadata is checked; narration, video frames and audio are not verified. Human review and persistent research records are limited on free cloud hosting.</p>''',
    unsafe_allow_html=True,
)
