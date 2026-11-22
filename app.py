"""VeriLoop public landing page — research MVP, with a direct video-check entry point."""
from __future__ import annotations

from html import escape
import streamlit as st

from veriloop.db import connect_db, init_db, list_evidence, seed_evidence
from veriloop.ui import apply_theme

st.set_page_config(page_title="VeriLoop | Evidence before verdicts", page_icon="🔎", layout="wide")
apply_theme()

st.markdown(
    """
    <style>
    .vl-home-hero {
      background: radial-gradient(circle at 90% 20%,rgba(25,235,209,.20),transparent 40%),
      linear-gradient(112deg,#072b43 0%,#05495b 55%,#087b80 100%);
      color:white; border-radius:24px; padding:52px 50px 45px; margin:8px 0 24px;
      box-shadow:0 18px 42px rgba(3,51,67,.16);
    }
    .vl-home-hero h1 {font-size:clamp(2.05rem,4vw,3.3rem);color:#fff!important;
      line-height:1.15;margin:12px 0 15px;letter-spacing:-.045em;max-width:800px;}
    .vl-home-hero h1 em {color:#3be5ce;font-style:normal;}
    .vl-home-hero p {color:#e4f9f8;line-height:1.7;font-size:1.08rem;max-width:720px;}
    .vl-home-pill {display:inline-block;border:1px solid rgba(255,255,255,.6);
      border-radius:50px;padding:7px 14px;color:#e5ffff;font-size:.81rem;font-weight:750;}
    .vl-home-features {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:20px 0 36px;}
    .vl-home-feature {background:#f0fafb;border:1px solid #d4e7e9;border-radius:17px;
      padding:21px 18px;min-height:150px;color:#123248;}
    .vl-home-feature strong {display:block;margin:8px 0 5px;font-size:1rem;}
    .vl-home-feature span {font-size:.9rem;line-height:1.5;color:#45616c;}
    .vl-home-icon {font-size:1.5rem;color:#047f85;}
    .vl-home-heading {font-size:1.75rem;font-weight:790;letter-spacing:-.035em;margin:10px 0 18px;}
    .vl-home-steps {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;margin:0 0 20px;}
    .vl-home-step {border:1px solid #d4e5e8;border-radius:16px;padding:23px 21px;background:#fff;min-height:174px;}
    .vl-home-step b {display:block;color:#043e53;font-size:1.03rem;margin:14px 0 7px;}
    .vl-home-step p {font-size:.91rem;color:#48626c;line-height:1.6;margin:0;}
    .vl-home-number {display:inline-flex;background:#d4f7ee;border-radius:50%;
      width:38px;height:38px;justify-content:center;align-items:center;
      font-weight:800;color:#086c69;}
    .vl-home-sources {background:#edf5f9;border-radius:20px;padding:25px 28px;margin-top:20px;}
    .vl-home-source-tiles {display:flex;flex-wrap:wrap;gap:9px;margin:13px 0;}
    .vl-home-source {background:white;border:1px solid #d6e4eb;border-radius:11px;
      padding:11px 15px;font-weight:700;color:#143e52;font-size:.93rem;}
    .vl-home-foot {border-top:1px solid #d7e6ea;padding-top:20px;margin-top:35px;
      color:#617780;font-size:.88rem;line-height:1.7;}
    @media(max-width:840px) {
      .vl-home-features {grid-template-columns:repeat(2,minmax(0,1fr));}
      .vl-home-hero {padding:34px 25px;}
      .vl-home-steps {grid-template-columns:1fr;}
    }
    @media(max-width:480px) {.vl-home-features{grid-template-columns:1fr;}}
    </style>
    """,
    unsafe_allow_html=True,
)

nav_left, nav_a, nav_b, nav_c = st.columns([3.4, 1, 1.2, 1.1])
with nav_left:
    st.markdown("### 🛡️ VeriLoop")
    st.caption("News Evidence Explorer")
with nav_a:
    st.page_link("app.py", label="Home", use_container_width=True)
with nav_b:
    st.page_link("pages/1_Verify_News.py", label="Verify Video", use_container_width=True)
with nav_c:
    st.page_link("pages/2_Channel_History.py", label="History", use_container_width=True)

st.markdown(
    """
    <section class="vl-home-hero">
      <span class="vl-home-pill">◈ Research prototype (MVP)</span>
      <h1>Check YouTube News Videos.<br>Find Evidence. <em>Stay Informed.</em></h1>
      <p>VeriLoop helps you explore factual statements from a video's published
      title and description, compare related original sources, and see what remains
      uncertain — without inventing a misleadingness score.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

start, learn = st.columns([1, 1.25], gap="medium")
with start:
    st.page_link("pages/1_Verify_News.py", label="▶  Verify a Video Now", use_container_width=True)
with learn:
    st.caption("No sign-up required · YouTube public metadata · Evidence first, verdicts only after review")

st.markdown(
    """
    <section class="vl-home-features">
      <article class="vl-home-feature"><div class="vl-home-icon">▶</div>
        <strong>YouTube Focused</strong><span>Check publicly accessible video title and description.</span></article>
      <article class="vl-home-feature"><div class="vl-home-icon">⌕</div>
        <strong>Evidence-Based</strong><span>Explore curated references and published fact-check links.</span></article>
      <article class="vl-home-feature"><div class="vl-home-icon">▤</div>
        <strong>Transparent Results</strong><span>See what was matched, what was not, and why.</span></article>
      <article class="vl-home-feature"><div class="vl-home-icon">♧</div>
        <strong>Research-Driven</strong><span>A carefully scoped university research prototype.</span></article>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="vl-home-heading">How VeriLoop Works</div>', unsafe_allow_html=True)
st.markdown(
    """
    <section class="vl-home-steps">
      <article class="vl-home-step"><span class="vl-home-number">1</span>
        <b>Paste a YouTube Link</b><p>Enter one public video URL. We retrieve its published metadata.</p></article>
      <article class="vl-home-step"><span class="vl-home-number">2</span>
        <b>Extract Possible Claims</b><p>We identify up to five candidate factual statements from the title and description.</p></article>
      <article class="vl-home-step"><span class="vl-home-number">3</span>
        <b>Explore Original Evidence</b><p>Inspect related sources and their context; unresolved claims remain unresolved.</p></article>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="vl-home-heading">Try It Yourself</div>', unsafe_allow_html=True)
with st.form("vl_home_link_form"):
    url = st.text_input("YouTube video link", placeholder="https://www.youtube.com/watch?v=...")
    pressed = st.form_submit_button("Check This Video →", type="primary", use_container_width=True)
if pressed:
    if url.strip():
        st.session_state["vl_prefill_url"] = url.strip()
        st.switch_page("pages/1_Verify_News.py")
    else:
        st.warning("Paste a public YouTube video link to continue.")
st.caption("The next page verifies the link and retrieves metadata. We do not analyze the full video, speech or audio.")

try:
    with connect_db() as conn:
        init_db(conn)
        seed_evidence(conn)
        records = list_evidence(conn)
except Exception:
    st.warning("The curated evidence source list is temporarily unavailable.")
else:
    names = sorted({record["source_name"] for record in records})
    st.markdown('<div class="vl-home-heading">Our Evidence Sources</div>', unsafe_allow_html=True)
    tiles = "".join(f'<span class="vl-home-source">{escape(name)}</span>' for name in names)
    st.markdown(
        '<section class="vl-home-sources">'
        '<strong>External publications in our small curated reference library</strong>'
        f'<div class="vl-home-source-tiles">{tiles}</div>'
        f'<small>{len(records)} reference records. Mentioning a source does not imply '
        'endorsement, a partnership, or a verified verdict about a submitted video.</small>'
        '</section>',
        unsafe_allow_html=True,
    )
    with st.expander("Browse original reference claims and publications"):
        for record in records:
            st.write("**" + record["id"] + " · " + record["claim_text"] + "**")
            st.caption(record["source_name"] + " · Published: " + (record["published_date"] or "Not confirmed"))
            st.link_button("Read original publication", record["source_url"])

st.markdown('<div class="vl-home-heading">About this research MVP</div>', unsafe_allow_html=True)
st.write(
    "VeriLoop is an evidence-exploration prototype, not an automatic truth detector. "
    "An apparent source match is not proof of support or contradiction. "
    "Claim-level decisions require careful event, date, location and uploader-stance checks. "
    "Human review is optional for visitors and necessary before approved source-history findings or corrections."
)
left, right = st.columns(2)
with left:
    st.page_link("pages/2_Channel_History.py", label="See reviewed channel history")
with right:
    st.page_link("pages/3_Review_Dashboard.py", label="Restricted reviewer workspace")

st.markdown(
    '<footer class="vl-home-foot">© VeriLoop · University research MVP · '
    'Published YouTube title and description only · No full video/audio verification · '
    'No automatic accusations or universal channel scores · '
    'Cloud research data may not persist after a restart.</footer>',
    unsafe_allow_html=True,
)
