"""Local, non-committed environment configuration."""
from __future__ import annotations

import os
from dotenv import load_dotenv


def get_youtube_api_key() -> str | None:
    load_dotenv()
    return os.environ.get("YOUTUBE_API_KEY") or None
