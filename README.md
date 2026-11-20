# VeriLoop (Day 1 working slice)

A **YouTube metadata-only** implementation within the frozen seven-day VeriLoop pilot. Its scope and live status are governed solely by `PROJECT_SOURCE_OF_TRUTH.md`. This build has **no fact-check verdict or evidence matching**.

## Local setup

Requires Python 3.11+ and a YouTube Data API v3 key. A key is not bundled. No paid AI service or hosting is required.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env  # On Windows, copy the file manually
# Set YOUTUBE_API_KEY in .env (never commit it).
streamlit run app.py
```

Open the **Verify News** sidebar page, paste a public YouTube watch, Shorts, mobile watch or youtu.be URL, and request metadata. Missing key, invalid URL, removed/private video and HTTP failures produce explicit messages rather than invented results. YouTube API access may require project/API enablement and appropriate quota.

## Tests (offline)

```bash
python -m pytest -q
```

Tests use a fake session; they **do not prove live YouTube API access**. Day 1 live acceptance still requires a valid `YOUTUBE_API_KEY`, network, and a publicly available real video URL. Progress is documented in Section 15 of the source of truth.

## Ethics and interpretation

Thumbnails are displayed but not forensically analyzed. No unsupported channel accusation, similarity-as-probability, or automatic correction publishing is implemented.
