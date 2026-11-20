# VeriLoop — Day 2 evidence library build

A **YouTube metadata + curated evidence library** research pilot. The authoritative frozen feature contract and latest verified status are in PROJECT_SOURCE_OF_TRUTH.md.

## Free online demo (Streamlit Community Cloud)

Existing application: https://veriloop-research.streamlit.app (GitHub: towhidReshad/veriloop, branch main). Updates to the main branch normally trigger a redeployment. A domain, paid hosting, and local server are unnecessary. Set YOUTUBE_API_KEY only in the app's **private Streamlit Secrets**, never in GitHub.

The **Verify News** page retrieves public YouTube video metadata via the official YouTube Data API v3. The homepage also offers a read-only view of **13 curated external-source references** with original links and dates. **These are not matched to a submitted video, not human-approved VeriLoop findings, and not an observational research sample.** Claim extraction, stance/context validation, TF-IDF retrieval and guarded preliminary reports remain to be implemented.

**Streamlit Community Cloud SQLite storage is ephemeral.** The app reconstructs the public curated library from versioned data/seed_evidence.json. Do not rely on this deployment for durable reviewer, correction or participant data.

## Offline build / tests

Requires Python 3.11+; from repository root:

    python -m pip install -r requirements.txt
    python scripts/seed_db.py
    python scripts/seed_db.py
    python -m pytest -q

The seed is idempotent: the second run inserts zero new references. Optionally run Streamlit locally with: streamlit run app.py. Local hosting is *not* required for the university demonstration.

The seed script and homepage require no YouTube API credentials; the live metadata page needs the restricted YouTube key stored securely. Google Fact Check Tools API lookup is optional and not part of this Day 2 build.

## Research and review boundaries

- data/seed_evidence.json is the **verification library**, not the 20–30-item observational sample. The latter is separately defined in research/news_dataset.csv and currently contains **zero** observations.
- External reference classifications are not verified decisions about submitted videos. All evidence.reviewed_by fields are NULL; zero reviews, assessments, claim matches, corrections or channel accusations are preloaded.
- Source URLs and available publication dates are preserved; unknown source publication dates remain null. Event dates are not substituted for publication dates.
- No channel credibility percentage, truth probability, automatic correction publishing or arbitrary video/audio verification is implemented.
