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


## Day 3 — metadata claim candidates and preliminary evidence retrieval

The Verify News page now runs local deterministic candidate extraction on the video's title and first 7,000 characters of English description (up to five tentative sentences). It retrieves related claims from the existing 13-reference SQLite seed using TF-IDF with 1–2 gram vocabulary, and lists original evidence links, publication dates, textual similarity *for retrieval only*, and explicit context uncertainty. A heuristic context check can rule out clearly conflicting event years or regions; debunking and quoting cues do not imply endorsement. No exact event identity, fact-check verdict, reviewer approval or channel accusation is derived from similarity.

Expected local acceptance: NASA eclipse video 2MJY_ptQW1o -> candidate claim from the published description and possible NASA EV-002 evidence match; entertainment/video labels -> no factual claim; unrelated claim -> INSUFFICIENT_EVIDENCE; misleading-context or debunking descriptions -> tentative reference matching only, never automatic misinformation verdict. No unsupported 85% misleading percentages are emitted.

Run `python -m pytest -q`. At Day 3 implementation the suite passed 88/88 offline tests (Python environment with scikit-learn installed); the live hosted deployment must be checked separately. The app still needs a private YOUTUBE_API_KEY configured in Streamlit Cloud Secrets. Streamlit Community Cloud restarts may recreate the seeded evidence database. No pilot participant responses have been collected.

Day 4+ frozen requirements—including approved-context reuse, reviewed channel history, optional human review, corrections with separate publishing approval and analytics—are **not yet implemented**.
