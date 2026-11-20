"""VeriLoop local Streamlit app entry point."""
import streamlit as st

st.set_page_config(page_title="VeriLoop", page_icon="🔎", layout="centered")
st.title("VeriLoop")
st.caption("Evidence-linked news verification · YouTube metadata pilot")
st.write("Open **Verify News** from the sidebar to inspect a public video's metadata.")
st.info(
    "Day 1 implementation only retrieves official video metadata. "
    "It does not yet extract claims, search evidence, or issue truth verdicts."
)
st.warning(
    "No automated result should be interpreted as a final determination. "
    "Human review and evidence matching are planned later in the frozen MVP scope."
)
