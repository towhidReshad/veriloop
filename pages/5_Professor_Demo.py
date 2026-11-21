"""Source-grounded demonstration materials, not a cached imitation of live analysis."""
import streamlit as st

from veriloop.demo import DemoCaseError, load_demo_cases, public_summary
from veriloop.ui import apply_theme

st.set_page_config(page_title="Professor demo guide | VeriLoop", page_icon="🎓", layout="centered")
apply_theme()
st.title("Professor demo · prepared research examples")
st.caption(
    "Source-linked examples and honest availability status, not automatically "
    "verified videos. Run the public verifier separately for real live results."
)
st.warning(
    "This page is NOT the video verification engine. The case labels describe what "
    "the original research sources address; VeriLoop has NOT automatically issued "
    "a verdict on these videos, and no human approval is preloaded."
)
try:
    cases = [public_summary(c) for c in load_demo_cases()]
except (OSError, ValueError, DemoCaseError) as exc:
    st.error("Prepared demonstration references are unavailable or invalid.")
    st.stop()

descriptions = {
    "A": ("Misleading-context example", "A historical video was reportedly relabeled as a different event. Compare the repost with the AFP investigation; never condemn the original footage."),
    "B": ("Documented supported event", "NASA describes the 2024 eclipse path. A source about the eclipse does not certify everything said in its broadcast."),
    "C": ("Evidence is unresolved", "NASA's UAP reference explains why insufficient observation data limits conclusions. Do not invent an extraterrestrial-origin claim."),
}
for item in cases:
    code = item["case_id"]
    heading, explanation = descriptions[code]
    with st.container(border=True):
        st.subheader(f"Case {code} · {heading}")
        st.write(explanation)
        st.write("**Research claim/topic:**", item["target_claim_summary"])
        st.write("**What the documented source addresses:**", item["evidence_summary"])
        st.link_button("Open the source publication", item["source_record_url"])
        st.link_button("Try this public YouTube link in a new tab", item["youtube_url"])
        st.caption("YouTube availability record: " + item["live_status"])
        st.caption("Demo acceptance status: " + item["acceptance"])
        st.info(item["disclaimer"])

st.divider()
st.markdown("### Live verification and limitations")
st.page_link("pages/1_Verify_News.py", label="🔎 Open the real YouTube verification form")
st.write(
    "Use the actual live verifier for metadata, claim candidates and tentative related "
    "sources. If the original YouTube item is private, removed or unavailable, this "
    "guide remains a source-linked research explanation, not a simulated API success."
)
st.write(
    "Case A and C have not been demonstrated with live YouTube API metadata in the "
    "recorded project history. Case B was previously owner-demonstrated. "
    "A reviewer must independently confirm claim stance/event/date/location "
    "before approving any reviewed claim or correction."
)
st.caption(
    "Three prepared cases are not an observational sample, a user study or "
    "evidence of the product's accuracy. No automatic true/false video labels."
)
