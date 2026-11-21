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


## Day 3 post-deployment quality update

Owner's live NASA test confirmed related EV-002/EV-004 references and explicit insufficient-evidence cases. The test also exposed a false positive: a request to viewers to send questions was labeled a factual claim. The conservative extractor now excludes audience calls-to-action, with dedicated regression tests. This narrows one known error but does not establish general precision, video stance, or truth verdict. 60 offline tests were rerun in this patch session (Day 2 suite plus 6 new regressions); the broader Day 3 suite had passed 88 tests before this patch, not yet rerun here.


## Day 4 — optional human review and approved-only history

Verify News now offers **Request human review** for each candidate (pending state, not an accusation). A separate **Channel History** page lists only explicit human-approved, linked, context-aligned claim decisions and the source URL, timestamp and denominator of current review requests; no channel-wide trust/misinformation percentage is shown. A password-gated **Review Dashboard** lets a genuine reviewer mark a request APPROVED, REJECTED or NEEDS_MORE_EVIDENCE, with a mandatory rationale; approval requires an ASSERTS stance, selected directly linked ALIGNED evidence, and explicit context confirmation. An approved decision can later be revised, removing it from public history.

**Security/setup:** Add `REVIEWER_PASSWORD = "YOUR_STRONG_RANDOM_16_PLUS_CHARACTER_SECRET"` in Streamlit Community Cloud **App Settings → Secrets**, alongside the existing `YOUTUBE_API_KEY`. Never commit either value; do not share the secret in screenshots. If unset, reviewer dashboard remains locked. This is a simple research pilot password gate, not production-grade accounts/authentication.

**Persistence warning:** Free cloud SQLite storage is **ephemeral**. Review requests, human decisions and their audit trail may disappear when Streamlit restarts. Do **not** collect sensitive participant information or treat the demo as durable public corrections. A durable approval archive and separate correction/export approval are still pending P0 work. Only real human reviews may populate channel history; 13 seeded reference records do not qualify. 69 selected offline tests passed in Day 4 development; hosted testing remains pending.


## Public-first UI refinement (2026-11-21)

The existing verification backend is unchanged. The homepage now provides a **one-link starting point** and a three-step explanation. Verify News shows the video summary, a count of detected **candidate statements** and how many have tentative reference matches, and clear per-statement source links. Unmatched statements are explicitly **not** labeled false. `Research details` expanders retain exact preliminary states, metadata stance, context matching and TF-IDF similarity **as a retrieval metric, not a probability or truth score**. Optional human-review requests and approved-only Channel History remain intact. The reviewer dashboard's restricted security workflow is not changed.

66 selected offline tests passed after this presentation update (Day 1/2 + presentation invariants). Python compile checks passed. Hosted UI must still be checked manually. These counts are not a claim of full end-to-end validity or misinformation-detection accuracy.


## Optional live fact-check fallback (2026-11-21)

To improve coverage for **previously unseen public YouTube news URLs**, VeriLoop now checks its existing 13 curated reference records first, then searches **Google Fact Check Tools API `claims:search`** when a metadata claim has no sufficiently similar local match. It uses only available English YouTube **title and description** (not video/audio or a transcript). It checks a maximum of five claims per video, returns published fact-check article links, publisher name and review date when available, and labels the source as **live fact-check search**. It does **not** run general web search or guarantee every video or claim has a match.

Configuration: add `FACTCHECK_API_KEY = "YOUR_PRIVATE_RESTRICTED_KEY"` under Streamlit Community Cloud App Settings → Secrets, keeping existing YouTube and reviewer secrets unchanged. The Fact Check Tools API must be enabled for the same Google Cloud project; restrict the key to that API. Never paste secrets into chat, source code or GitHub. If unconfigured, quota-limited or unavailable, the existing local result is preserved and the UI shows an explanatory status, never a fabricated source or verdict. Up to five lookups per submitted video may consume Google API quota; inspect current quota and billing in your own Google Cloud Console.

**Important:** Fact-check search results are publisher-authored references. An article's original rating is visible only as research detail and must not be presented as VeriLoop's finding about a submitted video, uploader, or channel. Live matches are **not added automatically** to the human-approved SQLite evidence/review history and cannot be automatically approved. Same-event identity, stance, event date and context must still be independently checked. Live result relevance is text matching, **not** a probability of truth. Google’s indexed fact-check publications are not the whole internet.

Regression: **17/17 offline mocked API/fallback tests passed** (missing key, authorization/quota errors, unsafe URLs, incompatible years, local-first behavior, 5-query cap). A real hosted API request has **not yet been verified**.


## Unseen-video no-match regression (2026-11-21)

Owner screenshot confirms an unseen BBC World Service interview fetched successfully, but neither the 13 curated references nor Google's indexed fact-check search returned related records for the metadata statements. This is a valid uncertainty outcome, not rejection of the link or a verdict about the video. Fixed a false-positive question title carrying a programme suffix after `?`, and clarified the all-no-match status in the general-user UI. Regression tests were added; the updated hosted UI still requires verification. Google's claim-review index is not an internet-wide evidence crawler, and dialogue/interviews may contain opinions rather than independently checkable propositions.


## WHO reference and negation safeguards (2026-11-21)

Owner supplied a live Seeker video screenshot with two WHO-topic local matches. EV-010 stores the **checked reference proposition** `Childhood vaccines cause autism.` and the **WHO reference classification** `CONTRADICTED`; this does not mean that the video's opposite wording has been contradicted. The UI now shows the reference's own classification alongside its checked proposition, and explicitly flags a simple negation mismatch as a **related topic, not confirmed support**. When such a mismatch exists the optional external fact-check search also runs instead of treating the local topic match as a sufficient comparison. This is a conservative lexical warning, not reliable semantic entailment or a verified verdict. Human review remains necessary.

Targeted regression tests added for vaccine/autism wording, no automatic verdict, and external-search fall-through. New hosted UI not yet confirmed and full project test suite not rerun as part of this patch.


## Conservative evidence improvements (2026-11-21)

Metadata candidate matching now checks **explicit full calendar dates** (in month-first, day-first and ISO formats), not only four-digit years. Contradicting dates are not matched; vague broad-region overlap with differing explicit countries remains `UNCONFIRMED`. Quoted statements are marked as tentative quotations, and a small set of generic discussion/opinion phrases is filtered before retrieval. The existing TF-IDF baseline remains unchanged and does **not** establish semantic equivalence or truth.

If local reference wording conflicts or event/context is still unconfirmed, the optional Fact Check Tools lookup can still run within the existing five-query-per-video budget. A mixed local/live display names sources separately, avoids falsely saying no local reference exists, and counts unique **statements with sources**, not truth verdicts. A mocked provider-positive regression case checks original article URL/publisher/rating provenance but does not establish a real, indexed positive API response. New source-level tests and a GitHub Actions `compileall` + `pytest` workflow were added; check the actual CI run before claiming the full suite passes.

**Still required for final frozen MVP:** F-07 reviewed exact-context reuse, F-10 correction draft plus independent export approval, F-11 measured pilot dashboard, full A/B/C professor test evidence and durable reviewed-record storage. These are not marked completed by this patch.


### Automated full-suite verification

GitHub Actions [run 44899946003](https://github.com/towhidReshad/veriloop/actions/runs/44899946003) completed successfully on Python 3.11: **165/165 pytest passed** plus `compileall`. An earlier run surfaced four old presentation test-fixture crashes because test objects had no `matches` field; the helper now handles missing optional matches safely. A successful mocked API test is not a confirmed real Fact Check Tools result. The free-hosted new UI still requires direct validation.


## Title-aware claim selection (2026-11-21)

Instead of stopping at the first five eligible metadata sentences, VeriLoop now examines up to 48 bounded title/description segments, selects checkable English statements, and ranks those statements by overlap with informative **video-title topic words** and a limited set of explicit factual details. It keeps a deterministic five-statement cap and preserves exact original wording. The relevance ranking is **not** a truth probability, semantic-entailment model, or an endorsement of the video's claims. This improves coverage of important claims buried later in long descriptions but cannot guarantee the five most fact-checkable claims.

New regression coverage includes a mocked Google Fact Check Tools **positive** claims:search response containing original publisher URL, date and rating; the app's local preliminary status remains unapproved. A mock is not a real authenticated API call. Actual positive retrieval from Google's current index and Google API quota remain to be verified in the hosted app. GitHub Actions CI status must be checked after deployment.
