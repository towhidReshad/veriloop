"""Shared lightweight Streamlit styling for the existing VeriLoop multipage UI."""
from __future__ import annotations

from html import escape
import streamlit as st


_STYLES = """
<style>
  .block-container {max-width: 1020px; padding-top: 1.8rem; padding-bottom: 4rem;}
  .vl-hero {
    background: linear-gradient(115deg, #102d3b 0%, #174a58 58%, #1b6b75 100%);
    border-radius: 22px; padding: 34px 36px; color: #ffffff;
    box-shadow: 0 14px 32px rgba(12, 43, 53, .15);
    margin: 8px 0 26px;
  }
  .vl-eyebrow {color: #a8e3d8; font-size: .78rem; font-weight: 750; letter-spacing: .13em;
               text-transform: uppercase; margin-bottom: 13px;}
  .vl-hero h1 {color: #ffffff !important; font-weight: 760; font-size: clamp(1.85rem, 3.5vw, 2.65rem);
               line-height: 1.14; letter-spacing: -.045em; margin: 0 0 14px;}
  .vl-hero p {color: #d5e7eb; font-size: 1.02rem; max-width: 680px; line-height: 1.65;
              margin: 0;}
  .vl-section-label {font-size: .79rem; font-weight: 760; text-transform: uppercase;
                     letter-spacing: .09em; color: #18867c; margin: 17px 0 10px;}
  .vl-step {border: 1px solid rgba(120, 147, 158, .3); border-radius: 17px;
            padding: 18px; min-height: 133px; margin-bottom: 8px;}
  .vl-step b {font-size: 1rem; display: block; margin-bottom: 7px;}
  .vl-step small {line-height: 1.5; opacity: .75;}
  .vl-number {color: #18867c; font-weight: 800; font-size: .9rem; margin-bottom: 12px;}
  .vl-footer {font-size: .85rem; line-height: 1.7; opacity: .7; margin-top: 24px;}
  div[data-testid="stForm"] {border-radius: 17px; border-color: rgba(120,147,158,.38);}
  div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 17px;}
  .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
     border-radius: 11px; background-color: #147b75; border-color: #147b75;
  }
  .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
     background-color: #0f6560; border-color: #0f6560;
  }
  /* Clearer public-facing evidence cards and responsive reading hierarchy */
  .block-container {max-width: 1080px;}
  [data-testid="stMetric"] {
    background: rgba(20, 123, 117, .055);
    border: 1px solid rgba(20, 123, 117, .15);
    border-radius: 15px;
    padding: 14px 17px;
    min-height: 115px;
  }
  [data-testid="stMetricLabel"] {font-size: .85rem; font-weight: 650;}
  [data-testid="stMetricValue"] {font-weight: 760; letter-spacing: -.04em;}
  [data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(94, 126, 136, .24);
    box-shadow: 0 4px 18px rgba(20, 48, 61, .035);
  }
  div[data-testid="stAlert"] {border-radius: 13px;}
  [data-testid="stExpander"] {border-radius: 12px; overflow: hidden;}
  [data-testid="stLinkButton"] a {border-radius: 10px;}
  .stMarkdown h3 {letter-spacing: -.025em; margin-top: .8rem;}
  .stMarkdown h4 {line-height: 1.35; font-size: 1.13rem;}
  /* Selected VeriLoop teal dashboard visual direction */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07374a 0%, #064b5d 60%, #086375 100%);
  }
  [data-testid="stSidebar"] * {color: #eefbfc;}
  [data-testid="stSidebar"] a:hover,
  [data-testid="stSidebar"] [aria-current="page"] {
    background: rgba(70, 205, 206, .23);
    border-radius: 10px;
  }
  .vl-hero {
    background: linear-gradient(110deg, #07384b, #095f71 68%, #168f9b);
    border-radius: 18px;
    padding: 30px 34px;
    margin-bottom: 20px;
  }
  [data-testid="stMetric"] {
    border: 1px solid #cde4ee;
    background: linear-gradient(145deg, #edf9fc 0%, #f7fbfe 100%);
    min-height: 102px;
  }
  div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #d6e4eb;
    box-shadow: 0 7px 24px rgba(8, 45, 69, .05);
  }
  .stButton > button:not([kind="primary"]) {
    text-align: left; justify-content: flex-start; white-space: pre-line;
    border-color: #d4e4ed; border-radius: 13px;
    min-height: 54px; font-weight: 550;
  }
  .stButton > button:not([kind="primary"]):hover {
    border-color: #23a9af; background: #f0fcfd;
  }
  .stButton > button[kind="primary"] {
    background: #086a78; border-color: #086a78;
    white-space: pre-line;
  }
  /* Wrap complete claim labels, including long words; avoid ellipsis and clipping. */
  .stButton > button,
  .stButton > button[kind="primary"] {
    height: auto; min-height: 54px; padding: 12px 15px;
  }
  .stButton > button p {
    white-space: normal !important;
    overflow-wrap: anywhere;
    word-break: break-word;
    text-overflow: clip;
    text-align: left;
    line-height: 1.45;
    margin: 0;
  }
  [data-testid="stTextArea"] textarea {
    overflow-wrap: anywhere;
    word-break: break-word;
    line-height: 1.6;
  }
  .stMarkdown p, .stCaption, [data-testid="stCaptionContainer"] {
    overflow-wrap: anywhere;
  }
  @media (max-width: 650px) {
    .block-container {padding-top: .75rem;}
    .vl-hero {padding: 24px 22px; border-radius: 17px;}
    .vl-step {min-height: 0;}
  }
</style>
"""


def apply_theme() -> None:
    """Inject only fixed project-owned CSS; never user or video-supplied HTML."""
    st.markdown(_STYLES, unsafe_allow_html=True)


def hero(eyebrow: str, headline: str, description: str) -> None:
    """Accessible styled section with escaped, plain-text fields."""
    st.markdown(
        '<section class="vl-hero">'
        f'<div class="vl-eyebrow">{escape(eyebrow)}</div>'
        f'<h1>{escape(headline)}</h1>'
        f'<p>{escape(description)}</p>'
        '</section>',
        unsafe_allow_html=True,
    )
