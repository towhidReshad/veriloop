"""VeriLoop public homepage: approved professional visual direction on live Streamlit hosting.

This page uses decorative project-owned HTML/CSS but keeps all navigation and
verification input in genuine Streamlit controls. No fictional verification
findings or unsupported brand partnerships are displayed.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from veriloop.db import connect_db, init_db, list_evidence, seed_evidence

st.set_page_config(page_title="VeriLoop | Evidence Before Verdicts", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {--ink:#10283e;--teal:#086879;--mint:#28dfc1;}
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif;}
/* Home is a public landing page, NOT a default Streamlit admin dashboard. */
[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stSidebarCollapsedControl"] {display:none!important;}
[data-testid="stHeader"] {background:transparent;box-shadow:none;}
[data-testid="stAppViewContainer"] {background:white;}
[data-testid="stAppViewBlockContainer"],.block-container {
 max-width:1550px!important;padding:0 32px 35px!important;
}
h1,h2,h3 {font-family:'Manrope','DM Sans',sans-serif;letter-spacing:-.045em;color:var(--ink);}
.vl-navbar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px 0 14px;}
.vl-brand{display:flex;gap:13px;align-items:center;}
.vl-brand-icon{width:54px;height:54px;background:linear-gradient(135deg,#24d9d0,#04596a);
 border-radius:14px;display:grid;place-items:center;color:#fff;font-size:29px;font-weight:800;
 box-shadow:0 8px 23px #039da532}
.vl-brand b{font-size:1.85rem;letter-spacing:-.065em;line-height:1;color:#0a263b;}
.vl-brand small{display:block;color:#47616e;font-size:.81rem;letter-spacing:0;margin-top:4px;}
.vl-nav-hint{color:#5f7881;font-size:.9rem;font-weight:700;}
/* Real Streamlit navigation buttons are placed immediately below the brand. */
[data-testid="stPageLink"] a {border-radius:24px!important;padding:9px 17px!important;color:#164557!important;
 font-weight:750!important;text-decoration:none!important;min-height:40px;}
[data-testid="stPageLink"] a:hover{background:#ddf7f4!important;color:#006b78!important}
.vl-hero {position:relative;overflow:hidden;border-radius:26px;padding:64px 54px 62px;
 display:grid;grid-template-columns:1fr 1.02fr;align-items:center;gap:24px;min-height:475px;
 background:radial-gradient(circle at 82% 18%,#18bdaf66,transparent 34%),
 linear-gradient(110deg,#062d47 0%,#06445c 59%,#06817f 100%);color:#fff;
 box-shadow:0 21px 48px #02455c26;margin:23px 0 23px;}
.vl-hero-tag{display:inline-block;border:1px solid #7dcbd2;border-radius:30px;
 padding:10px 16px;font-size:.82rem;color:#e2ffff;font-weight:800;margin-bottom:22px;}
.vl-hero h1{font-size:clamp(2.3rem,3.7vw,4.15rem);color:#fff!important;font-weight:800;
 line-height:1.14;letter-spacing:-.055em;margin:0 0 20px;}
.vl-hero h1 em{font-style:normal;color:#37e3c9;}
.vl-hero p{font-size:1.07rem;line-height:1.75;color:#def5f5;max-width:640px;margin:0 0 26px;}
.vl-hero-cta{display:inline-flex;gap:10px;align-items:center;color:#053d4a;background:#37e6ca;
 font-weight:800;border-radius:12px;padding:13px 20px;text-decoration:none!important;}
/* The illustration is entirely decorative, not fake analysis output. */
.vl-showcase{position:relative;padding:23px 4px 23px 28px;}
.vl-laptop{border:10px solid #142937;background:#e8f3f7;border-radius:18px 18px 7px 7px;
 box-shadow:0 26px 55px #001d2b70;min-height:270px;overflow:hidden;}
.vl-laptop-bar{height:32px;background:#fff;display:flex;align-items:center;gap:9px;
 padding:0 13px;color:#0c5866;font-weight:800;font-size:.8rem;}
.vl-laptop-body{display:grid;grid-template-columns:1.1fr 1fr;gap:12px;padding:15px;}
.vl-preview-video{background:radial-gradient(circle,#2ad0cc,#08628d 56%,#102d5b);
 border-radius:11px;min-height:172px;display:grid;place-items:center;color:white;}
.vl-preview-play{border-radius:50%;background:#ffffff37;width:70px;height:70px;
 display:grid;place-items:center;border:1px solid #fff8;font-size:2rem;}
.vl-preview-results{background:white;padding:14px;border-radius:11px;color:#1b4055;}
.vl-preview-results b{font-size:.89rem;display:block;margin-bottom:12px;}
.vl-preview-result{padding:9px;background:#eaf5f6;border-radius:7px;font-size:.72rem;
 margin:7px 0;color:#375b67;}
.vl-laptop-foot{height:14px;margin:0 -18px;background:linear-gradient(#c2d3d7,#66828d);
 border-radius:0 0 60% 60%;}
.vl-float{position:absolute;background:white;color:#085568;box-shadow:0 10px 30px #00293c55;
 font-size:.78rem;font-weight:800;border-radius:10px;padding:11px 14px;}
.vl-float.a{top:2px;left:4px}.vl-float.b{right:-10px;top:47%}.vl-float.c{bottom:3px;left:1px;}
.vl-feature-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
 gap:15px;margin:25px 0 50px;}
.vl-feature{display:flex;gap:15px;align-items:flex-start;padding:19px 16px;background:#f0fafa;
 border:1px solid #deebee;border-radius:16px;color:#133a4f;min-height:130px;}
.vl-feature-icon{flex-shrink:0;width:48px;height:48px;border-radius:50%;background:#d7f3ee;
 color:#057484;display:grid;place-items:center;font-size:1.3rem;}
.vl-feature b{font-size:.99rem}.vl-feature p{color:#536c76;font-size:.85rem;line-height:1.55;margin:8px 0 0;}
.vl-section-title{font-size:clamp(1.6rem,2.5vw,2.2rem);font-weight:800;color:#10283e;
 letter-spacing:-.045em;margin:22px 0 20px;}
.vl-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-bottom:30px;}
.vl-step{padding:22px;border:1px solid #d7e8ec;border-radius:17px;min-height:167px;background:#fff;}
.vl-step-index{width:38px;height:38px;background:#c9f4e7;border-radius:50%;
 display:grid;place-items:center;font-weight:800;color:#026f69;margin-bottom:16px;}
.vl-step b{color:#14374a;font-size:1.03rem;}
.vl-step p{font-size:.91rem;color:#526d79;line-height:1.62;margin:9px 0 0;}
.vl-try-wrap{background:linear-gradient(135deg,#ecfcf6,#def7f6);
 padding:24px 27px;border-radius:22px;margin-bottom:24px;border:1px solid #d5f1e9;}
.vl-try-wrap h3{margin:0 0 8px;font-size:1.6rem;}
.vl-try-wrap p{font-size:.9rem;color:#56747c;margin-bottom:16px;}
[data-testid="stForm"]{border-radius:17px!important;border:1px solid #c6e4e8!important;
 background:white!important}
[data-testid="stFormSubmitButton"] button[kind="primary"]{background:#056575!important;
 border-color:#056575!important;font-weight:800!important;min-height:48px;border-radius:11px!important;}
.vl-evidence-box{background:#f0f7fa;border-radius:23px;padding:27px;margin:22px 0 26px;}
.vl-source-grid{display:flex;flex-wrap:wrap;gap:10px;margin:19px 0;}
.vl-source{background:#fff;color:#1d5469;font-weight:800;border:1px solid #d6e5ec;
 padding:13px 17px;border-radius:12px;font-size:.89rem;}
.vl-footer{margin:35px 0 0;background:#073549;color:#d8f1f2;border-radius:18px;
 display:flex;align-items:center;justify-content:space-between;gap:20px;padding:27px 32px;}
.vl-footer strong{font-size:1.15rem;color:white;}
.vl-footer small{line-height:1.6;color:#b4d2d8;}
.vl-note{color:#647b85;font-size:.88rem;line-height:1.6;}
@media(max-width:1050px){.vl-hero{padding:44px 30px;grid-template-columns:1fr 1fr;}
 .vl-float{display:none}.vl-feature-grid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:740px){[data-testid="stAppViewBlockContainer"],.block-container{padding:0 15px 24px!important}
 .vl-hero{grid-template-columns:1fr;padding:34px 23px;min-height:unset;}
 .vl-hero h1{font-size:2.35rem}.vl-showcase{padding:10px}.vl-laptop{min-height:200px}
 .vl-laptop-body{grid-template-columns:1fr 1fr}.vl-preview-video{min-height:115px}
 .vl-feature-grid{grid-template-columns:1fr;gap:11px}.vl-feature{min-height:100px}
 .vl-steps{grid-template-columns:1fr}.vl-step{min-height:unset}
 .vl-navbar{padding-top:24px}.vl-nav-hint{display:none}.vl-footer{display:block}
 .vl-footer small{display:block;margin-top:11px}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="vl-navbar">
  <div class="vl-brand"><span class="vl-brand-icon">✓</span>
    <div><b>VeriLoop</b><small>News Evidence Explorer</small></div></div>
  <div class="vl-nav-hint">Evidence before verdicts · University research MVP</div>
</div>
""", unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns(4, gap="small")
with nav1: st.page_link("app.py", label="Home", use_container_width=True)
with nav2: st.page_link("pages/1_Verify_News.py", label="Verify video", use_container_width=True)
with nav3: st.page_link("pages/2_Channel_History.py", label="Channel history", use_container_width=True)
with nav4: st.page_link("pages/3_Review_Dashboard.py", label="Reviewer workspace", use_container_width=True)

st.markdown("""
<section class="vl-hero">
  <div class="vl-hero-text">
    <span class="vl-hero-tag">◈ Research prototype · MVP</span>
    <h1>Check YouTube News Videos.<br>Find Evidence. <em>Stay Informed.</em></h1>
    <p>Explore claims in a video's published title and description, compare related
    original sources, and understand what remains uncertain. Evidence first, not invented verdicts.</p>
    <a class="vl-hero-cta" href="#try-video">▶ &nbsp; Start with a YouTube link ↓</a>
  </div>
  <div class="vl-showcase" aria-label="Illustrative interface preview; no real video verdicts">
    <div class="vl-float a">▤ &nbsp; Extract key claims</div>
    <div class="vl-laptop">
      <div class="vl-laptop-bar">✦ &nbsp; VeriLoop &nbsp; / &nbsp; Evidence explorer</div>
      <div class="vl-laptop-body">
        <div class="vl-preview-video"><span class="vl-preview-play">▶</span></div>
        <div class="vl-preview-results"><b>Evidence Overview</b>
          <div class="vl-preview-result">① Candidate claims</div>
          <div class="vl-preview-result">② Related sources</div>
          <div class="vl-preview-result">③ Explain uncertainty</div>
        </div>
      </div>
    </div>
    <div class="vl-laptop-foot"></div>
    <div class="vl-float b">⌕ &nbsp; Original sources</div>
    <div class="vl-float c">✓ &nbsp; Review before conclusions</div>
  </div>
</section>
<section class="vl-feature-grid">
  <article class="vl-feature"><div class="vl-feature-icon">▶</div><div><b>YouTube Focused</b><p>Analyze public titles and descriptions.</p></div></article>
  <article class="vl-feature"><div class="vl-feature-icon">⌕</div><div><b>Evidence-Based</b><p>Explore related sources and original fact-checks.</p></div></article>
  <article class="vl-feature"><div class="vl-feature-icon">▤</div><div><b>Transparent Results</b><p>Know what matched and what remains unknown.</p></div></article>
  <article class="vl-feature"><div class="vl-feature-icon">♧</div><div><b>Research-Driven</b><p>An academic research prototype with cautious assessments.</p></div></article>
</section>
<div class="vl-section-title">How VeriLoop Works</div>
<section class="vl-steps">
  <article class="vl-step"><span class="vl-step-index">1</span><b>Paste a Video Link</b><p>Enter one publicly accessible YouTube video URL.</p></article>
  <article class="vl-step"><span class="vl-step-index">2</span><b>Extract Candidate Claims</b><p>Find up to five statements from the published title and description.</p></article>
  <article class="vl-step"><span class="vl-step-index">3</span><b>Compare Original Sources</b><p>Review related references and understand what is still unverified.</p></article>
</section>
<div class="vl-try-wrap" id="try-video"><h3>Try It Yourself</h3>
<p>Paste a public YouTube link below to start your preliminary evidence check.</p></div>
""", unsafe_allow_html=True)

with st.form("vl_home_link_form"):
    url = st.text_input("YouTube video link", placeholder="https://www.youtube.com/watch?v=...")
    pressed = st.form_submit_button("Check This Video →", type="primary", use_container_width=True)
if pressed:
    if url.strip():
        st.session_state["vl_prefill_url"] = url.strip()
        st.switch_page("pages/1_Verify_News.py")
    else:
        st.warning("Paste a YouTube video link to continue.")

st.caption("YouTube title/description only · No audio/footage analysis · No automatic true/false judgments")

try:
    with connect_db() as conn:
        init_db(conn)
        seed_evidence(conn)
        records = list_evidence(conn)
except Exception:
    st.warning("The source reference library is currently unavailable.")
else:
    publishers = sorted({r["source_name"] for r in records})
    tags = "".join('<span class="vl-source">' + escape(name) + "</span>" for name in publishers)
    st.markdown(
        '<section class="vl-evidence-box"><div class="vl-section-title">Our Evidence Sources</div>'
        '<p>Original publications in our selected reference library — not partnerships or automatically verified findings.</p>'
        '<div class="vl-source-grid">' + tags + '</div>'
        '<span class="vl-note">' + str(len(records)) + ' curated references; source findings must be checked against the specific video context.</span></section>',
        unsafe_allow_html=True
    )
    with st.expander("Explore the original reference publications"):
        for record in records:
            st.markdown("**" + record["id"] + " · " + record["claim_text"] + "**")
            st.caption(record["source_name"] + " · Published: " + (record["published_date"] or "Not confirmed"))
            st.link_button("Read original source", record["source_url"])

st.markdown('<div class="vl-section-title">About VeriLoop</div>', unsafe_allow_html=True)
st.write(
    "VeriLoop helps users explore evidence for candidate claims in public YouTube metadata. "
    "It is a research MVP, not an automatic truth detector. A topic match does not prove "
    "that a video is supported or misleading. Human review is required before confirmed "
    "source-history findings and editorial corrections."
)
st.markdown(
    '<footer class="vl-footer"><div><strong>VeriLoop</strong><small>News Evidence Explorer · University research prototype</small></div>'
    '<small>Public metadata only · No full video verification · No automatic accusations<br>'
    'Free-cloud review data may be temporary. Keep encrypted owner backups.</small></footer>',
    unsafe_allow_html=True
)
