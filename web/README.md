# VeriLoop — React website (approved public visual redesign)

This is a **real React + Vite frontend** backed by the project's existing Python verification modules through a read-only FastAPI service in `../api_server.py`. It is not a sample result page: submitted YouTube URLs use the actual configured API, evidence library, and optional Google fact-check index. The mock laptop on the public landing page is **decorative**, and does not display real verdicts.

## Local development — two terminals

Requirements: Python 3.11+, Node 20+.

Backend (repository root):

```bash
python -m pip install -r requirements-api.txt
# Set YOUTUBE_API_KEY in a private .env. FACTCHECK_API_KEY is optional.
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```bash
cd web
npm install
npm run dev
```

Open http://127.0.0.1:5173 . Vite proxies `/api` to the Python backend. The API key stays server-side, never in the React code.

## Single-server build / deployment

```bash
cd web && npm install && npm run build && cd ..
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

After the build, the same FastAPI application serves the React assets at `/` and its API at `/api/*`. Configure `YOUTUBE_API_KEY` privately on the server; configure `FACTCHECK_API_KEY` privately if live published fact-check search is desired. This is **not deployed automatically** to Streamlit Community Cloud. A separate Python/Node-capable hosting setup is needed. Streamlit's existing demo remains unchanged until explicit migration.

The `/api/verify` endpoint supports public **read-only verification**. The existing restricted Streamlit reviewer/correction workspace is still separate: this frontend links to it but does not bypass its password. No user verdicts or source approvals are hardcoded.

## Safety and scope

- YouTube public title and description only, not audio or full video.
- Up to five candidate claims, local curated references and optional published fact-check index.
- External source ratings stay attributed to their own checked claims; neither similarity nor a publisher rating is transferred automatically to the submitted upload.
- Overall video status remains **Not determined**, pending actual evidence and review.
- Public API uses a small in-process request cap; real public production should use an external rate limiter and TLS.
- Ephemeral SQLite is not durable approved-review storage.

## Verification status

The files have been committed to GitHub. Local `npm run build`, Python automated regression tests, real browser testing and external deployment have **not yet been confirmed** in this environment. Do not call this a live React release until those checks pass.
