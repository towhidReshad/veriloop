"""Research-only F-11 dashboard. Run manually, never exposed by public app."""
from pathlib import Path
import pandas as pd
import streamlit as st
from veriloop.analytics import load_sample, summarize_sample
from veriloop.db import ROOT

st.set_page_config(page_title="Research pilot | VeriLoop", page_icon="📊")
st.title("Research pilot · observed sample")
st.caption(
    "Observed records only. This is not a worldwide misinformation rate, "
    "platform-wide accuracy estimate, or verified long-term trend."
)
sample_path = ROOT / "research" / "news_dataset.csv"
try:
    observations = load_sample(sample_path)
    stats = summarize_sample(observations)
except (OSError, ValueError) as exc:
    st.error(f"Observational sample unavailable or invalid: {exc}")
    st.stop()

a, b, c = st.columns(3)
a.metric("Documented observations", stats["sample_size"])
b.metric("Resolved annotations", stats["resolved_count"])
c.metric("Unresolved / unannotated", stats["unresolved_count"])

if not observations:
    st.info(
        "The separate observational research dataset currently has 0 records. "
        "VeriLoop will not invent participants, countries, labels or statistics. "
        "Add real, documented and properly annotated sample records before reporting pilot findings."
    )
else:
    st.subheader("Observed counts by reviewed claim verdict")
    st.dataframe(pd.DataFrame(sorted(stats["verdicts"].items()),
                             columns=["Reviewed verdict", "Observed count"]),
                 hide_index=True, use_container_width=True)
    for title, key, category in [
        ("Observed events", "events", "Event ID"),
        ("Observed presentation categories", "categories", "Category"),
        ("Source countries (only if documented)", "countries", "Source country"),
        ("Observed publication dates", "publication_dates", "Publication date"),
    ]:
        st.subheader(title)
        st.dataframe(pd.DataFrame(sorted(stats[key].items()),
                                 columns=[category, "Observed count"]),
                     hide_index=True, use_container_width=True)
    st.caption(
        "A resolved-only fraction must use a disclosed resolved denominator; "
        "sample selection biases and unresolved records limit interpretation."
    )

st.divider()
st.subheader("Pilot methodology & limitations")
st.write(
    "Verification references (13 curated source records) are NOT observational "
    "news-sample rows. The sample has a separate defined inclusion rule and "
    "annotation guide. Event, publication date, source-country and reviewer "
    "fields require evidence rather than inference. Where no data exists, "
    "the correct scientific output is no observed result."
)
st.caption("See research/annotation_guide.md and PROJECT_SOURCE_OF_TRUTH.md for data definitions.")
