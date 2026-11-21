"""Local, non-committed environment configuration."""
from __future__ import annotations

import os
from dotenv import load_dotenv


def get_youtube_api_key() -> str | None:
    load_dotenv()
    return os.environ.get("YOUTUBE_API_KEY") or None

def get_factcheck_api_key() -> str | None:
    """Use private environment/Streamlit Secrets; never commit credentials."""
    load_dotenv()
    value = os.environ.get("FACTCHECK_API_KEY")
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get("FACTCHECK_API_KEY") or None
    except Exception:
        return None
