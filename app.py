"""VeriLoop Streamlit homepage; read-only Day 2 reference library preview."""
import streamlit as st

from veriloop.db import connect_db, init_db, list_evidence, seed_evidence

st.set_page_config(page_title="VeriLoop", page_icon="🔎", layout="centered")
st.title("VeriLoop")
st.caption("Evidence-linked news verification · YouTube metadata pilot")
st.write("Open **Verify News** from the sidebar to inspect a public video's metadata.")
st.info(
    "Official YouTube metadata retrieval is available. The Day 2 curated evidence "
    "library is prepared, but claim extraction, matching and preliminary verdicts "
    "are not implemented yet."
)

st.subheader("Curated reference evidence · Day 2")
try:
    # Streamlit Community Cloud disk is ephemeral. Re-seed missing public
    # references from checked-in JSON. Never seed private reviews/accusations.
    with connect_db() as connection:
        init_db(connection)
        seed_evidence(connection)
        rows = list_evidence(connection)
except (OSError, ValueError, RuntimeError) as exc:
    st.warning(f"Evidence database unavailable: {exc}")
except Exception:
    # A DB failure is an operational error, not insufficient truth evidence.
    st.error("Evidence database could not be opened. Check app logs.")
else:
    st.write(f"**{len(rows)} curated source-backed references loaded.**")
    st.caption(
        "These are external-source claim references only—not verified findings "
        "about submitted videos, not VeriLoop reviewer approvals, and not an "
        "observational prevalence sample."
    )
    with st.expander("Browse evidence sources (not matched to your video)"):
        for record in rows:
            st.markdown(f"**{record['id']} · {record['claim_text']}**")
            st.write("External reference classification:", record['reference_verdict'])
            st.write("Source:", record['source_name'])
            st.link_button("Open original source", record['source_url'])
            st.caption("Published: " + (record['published_date'] or "not confirmed") + " · VeriLoop human review: none")
            st.caption(record['notes'])
            st.divider()
st.warning(
    "No automated result should be interpreted as a final determination. "
    "An evidence match alone cannot prove a video asserts a claim."
)
st.caption(
    "On free Streamlit Cloud, SQLite files may be reset on app restart. "
    "This read-only research library is reconstructed from versioned seed JSON; "
    "no persistent reviewer decisions are promised."
)
