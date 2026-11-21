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


**Verified CI result:** [GitHub Actions run 44900704832](https://github.com/towhidReshad/veriloop/actions/runs/44900704832) passed Python `compileall` and **173/173 pytest cases** on commit `61814ca`. Hosted interface and real positive Google API results have not been verified by that test run.


## Frozen F-07: exact-context reviewed reuse (2026-11-21)

The public Verify News page can now display a **previously human-reviewed claim-level finding** only for the **same YouTube video ID, same channel ID, identical title/description/publication timestamp, exact extracted claim text and source field, unchanged ASSERTS stance**, AND an approved review with valid audit provenance and a linked `ALIGNED` source. The original local match remains tentative; the previous review is clearly labeled as a *historical human decision*, never a new automatic decision or a verdict about the whole video. Changing metadata, video, claim wording, stance or the review to a nonapproved status suppresses reuse. This conservatively implements the safe subset of F-07, **not cross-video semantic reuse**. Review data in free Streamlit Cloud SQLite is ephemeral.

No real reviewer approval or hosted exact-context reuse has yet been demonstrated. New automated tests and GitHub Actions must pass before claiming the code verified.


**Automated verification:** [GitHub Actions run 44901360529](https://github.com/towhidReshad/veriloop/actions/runs/44901360529) passed Python syntax checks and **187/187 pytest tests** on commit `a9a1a92`. This verifies the strict F-07 reuse rules at code level; a real hosted approved-review demonstration has not yet occurred.


## F-10 Corrections and F-11 research counts (2026-11-21)

Corrections are no longer just a SQLite placeholder. An audited, linked human-approved exact claim can produce an editable draft in the restricted Review Dashboard. Draft submission, **separate editorial approve/reject action**, and Markdown download are distinct stages. Export requires current approved review plus editorial approval; no social-media posting is performed. Free cloud SQLite is ephemeral; do not use it to permanently archive public accusations. New columns use an additive eight-table database migration.

The Research Dashboard shows counts from the separately annotated `research/news_dataset.csv`. At present that CSV has **zero** observation rows. It displays honest zero counts rather than made-up study outcomes or prevalence. The technical report draft explicitly states pilot study limitations.

Code added and regression tests written; full CI and hosted verification are pending.


**First combined CI:** [197/197 tests passed](https://github.com/towhidReshad/veriloop/actions/runs/44901926635); an additional independent-drafter/editor check awaits the final CI run. Separate editor identifiers are not strong production authentication, so public publication remains disabled.


**Consolidated F-10/F-11 verification:** GitHub Actions [run 44902043884](https://github.com/towhidReshad/veriloop/actions/runs/44902043884) passed 198/198 tests and compileall. Final UI compatibility patch is included in the next commit and must pass CI separately. Hosted usage and manual reviewer decisions have not been verified by these tests.


## Manual encrypted owner backups (2026-11-21)

The **restricted Review Dashboard** includes an encrypted `.vlbackup` download and a recovery form. You must first configure `REVIEWER_PASSWORD` privately in Streamlit Cloud Secrets; this is the existing reviewer-only pilot gate. Enter a **different 16+ character archive passphrase**; the research SQLite database is snapshotted and encrypted using AES-256-GCM, salt and password-derived key before download. Keep the downloaded file **off GitHub and outside the public app**, and keep the archive passphrase somewhere safe and separate. Neither the password nor the original unencrypted database is uploaded to GitHub by this feature.

For recovery, upload your own original `.vlbackup` to the reviewer page and provide its archive passphrase. Restore is **refused if any user-generated channel, video, claim, match, assessment, review or correction already exists**, preventing silent overwrite. The encrypted archive is limited to the project's small (8 MB) pilot database. A wrong password, modified ciphertext, incompatible schema, broken SQLite integrity or foreign keys causes rejection. This is **manual recovery only**, not automatic backups or fully durable cloud storage. A lost backup or passphrase cannot be recovered by the app. Only trusted owner archives should be restored; this is not a secure multi-user import service.

The regression workflow now uses Node24-compatible `actions/checkout@v6` and `actions/setup-python@v6`. Confirm the actual GitHub Actions run before claiming no warning.


**Verified workflow:** GitHub Actions [run 44903799198](https://github.com/towhidReshad/veriloop/actions/runs/44903799198) passed Python 3.11 `compileall` and **204/204 tests** on commit `6f513ee`. The Node24-compatible checkout/setup-python actions completed successfully, with no Node.js 20 deprecation warning in this run's logs. This is code-level verification: the hosted private backup/restore and real reviewer editorial workflow still need integrated human acceptance.


## F-12 Professor demo guide and conditional research protocol (2026-11-21)

The homepage links **Professor demo · documented case guide** (`pages/5_Professor_Demo.py`). It displays exactly three source-linked cases from `data/demo_cases.json` and transparently states where actual YouTube video availability or independent claim review is **not** demonstrated. It is **not** a simulated metadata endpoint, a cached app verdict, or a prepared human-approved accusation. Use the real Verify News form for live results; if a video is inaccessible, the source guide stays clearly labeled as a research example.

A study questionnaire and conditional consent/analysis protocol are in `research/USER_PILOT_PROTOCOL.md`, with a five-paper planning matrix in `research/LITERATURE_GAP_MATRIX.md`. No institutional approval, survey participants, experimental effects, country comparisons, or population prevalence are assumed. Verify literature claims in full text before submission. The observational sample remains empty.


**CI verification:** [GitHub Actions run 44904417714](https://github.com/towhidReshad/veriloop/actions/runs/44904417714) passed **208/208 pytest tests** plus Python compileall on commit `c127f97`. This validates prepared-case safety and code, not live A/C metadata availability or any human research finding.


## Public software vs academic deliverables (2026-11-21 correction)

The public Streamlit app is a **general-user product**. It must not expose professor-demo guides, participant-study documentation, an academic literature matrix, or an observational-sample dashboard in its automatically discovered navigation. The previously added public `pages/5_Professor_Demo.py` has been deleted; its valid A/B/C case source files remain for **offline academic preparation**. The F-11 descriptive dashboard has been moved out of the public `pages/` directory to `research/research_dashboard_app.py`. Researchers can run it **separately**, e.g. `streamlit run research/research_dashboard_app.py` from a local project checkout, without integrating it into the publicly deployed app. Do not deploy or expose this research dashboard publicly. All original documentation stays in `research/` and `PROJECT_SOURCE_OF_TRUTH.md`; its existence in a public GitHub repository does not make it an in-app feature.


## F-01 URL compatibility maintenance (2026-11-21)

Public Verify News accepts validated YouTube watch (`youtube.com/watch?v=`), Shorts (`/shorts/ID`), live (`/live/ID`), embed (`/embed/ID` and `youtube-nocookie.com/embed/ID`), legacy `/v/ID`, `music.youtube.com/watch?v=`, and short `youtu.be/ID` links. All extract an exact 11-character video identifier and use the **same official YouTube Data API**. Allowing a URL structure does not guarantee a video is public, contains factual claims, or has matching published fact-checks. Arbitrary hosts, channel/playlist pages, nested paths, and malformed IDs are rejected.


**URL compatibility verification:** [GitHub Actions run 44907528142](https://github.com/towhidReshad/veriloop/actions/runs/44907528142) passed Python compileall and **222/222 tests**. Valid URL parsing does not imply live public-video availability or fact-check coverage.


## Optional live fact-check search wording refinement (2026-11-21)

The existing one-query-per-claim Google Fact Check Tools lookup now trims a **small, documented list of report-introduction phrases** such as “Scientific evidence suggests that” before searching for the claim. It preserves negation, the claim's underlying factual proposition, date and location. The submitted video statement remains unchanged for the subsequent source relevance and context checks. A query refinement can improve retrieval opportunities but cannot make Google's index internet-wide or guarantee a matching article. Each eligible claim still uses at most one provider query; the five-query-per-video cap stays intact. Unsafe private/local IP fact-check article URLs are now excluded. The public report's optional source-search details show the actual wording used. Automated tests cover these safety constraints; GitHub CI needs to confirm final status.


**Verified CI:** [GitHub Actions run 44911474128](https://github.com/towhidReshad/veriloop/actions/runs/44911474128) passed **236/236 tests** and Python syntax checks on commit `7afa6f4`. This does not prove a positive response from the owner's live Google API key.


## Integrated review → correction → private recovery regression (2026-11-21)

A new deterministic end-to-end test covers review request, explicit human-approval **fixture**, previously-reviewed exact-context reuse, correction drafting, separate editor identity and approval, Markdown export, encrypted backup, restore into empty SQLite, no-overwrite protection, and revocation invalidating previously approved results. This is an automated pilot workflow test, **not a claim that a real reviewer performed these steps on Streamlit Cloud**. On reviewer logout the prepared encrypted archive and typed archive passwords are cleared from Streamlit session memory; downloaded files remain the owner's responsibility. Full GitHub CI verification is required.


**Verified integrated CI (2026-11-21):** [GitHub Actions run 44912850764](https://github.com/towhidReshad/veriloop/actions/runs/44912850764) passed Python compileall and **238/238 tests**. It confirms the entire simulated review/correction/export/encrypted-backup/restore/revocation pipeline with explicitly labeled fixture decisions; it does **not** establish that a real reviewer performed a hosted approval or that permanent storage now exists.


## F-07/F-09: Changed-video metadata review safety (2026-11-21)

Review requests are now scoped to the **original retrieved video metadata** (title, description and published timestamp) as well as exact claim text, stance and metadata field. Re-submitting an identical source context stays idempotent. If the publisher has changed the metadata for a video that already has a stored review request, the pilot refuses to silently reuse that old review. The eight-table frozen schema keeps one video record per YouTube ID, so a separate reviewed snapshot after publisher edits would require explicit versioned schema design; the current pilot transparently refuses the changed-context review rather than passing the original review off as new. Reviewed findings remain subject to the existing exact-context lookup and approval restrictions. Automated tests cover changed contexts; CI results must be checked separately.


**F-07/F-09 verification:** [GitHub Actions run 44914590673](https://github.com/towhidReshad/veriloop/actions/runs/44914590673) completed successfully with **244/244 tests** and Python compileall. Hosted live metadata-change acceptance remains unverified.


## Streamlit UI acceptance suite (2026-11-22)

`tests/test_streamlit_ui_acceptance.py` now drives real Streamlit script widgets using `streamlit.testing.v1.AppTest`. Its six offline checks cover: homepage product-only navigation, invalid URL failure message, mocked successful video metadata/preliminary evidence, reviewer page locked without an owner secret, rejected wrong reviewer password, and authorized access to an empty queue with **test-only credentials**. No credentials are saved in source or real external APIs called. The initial suite found test-code assertion mistakes; corrections and an additional positive-login test led to [GitHub Actions run 44918254742](https://github.com/towhidReshad/veriloop/actions/runs/44918254742) passing **250/250 tests**, plus `compileall` (commit `a4a517e`). This is **not a real cloud-browser end-to-end test** and does not prove permanent cloud review persistence or live publisher API results.
