# VeriLoop: Evidence-Linked YouTube Metadata Verification — Technical Pilot Report

**Document status:** Technical feasibility report based on implemented code and automated tests. It is **not** a completed human-participant experiment or a measured misinformation-prevalence study. Updated 2026-11-22.

## Abstract

VeriLoop is a zero-budget prototype designed to assist ordinary users in examining factual claims found in public YouTube video titles and descriptions. It uses the official YouTube Data API v3 for metadata, extracts at most five candidate statements from bounded English metadata, retrieves related records from a small curated SQLite evidence library using TF-IDF, and optionally queries Google's indexed published fact-checks. It distinguishes preliminary retrieval from human-approved, claim-specific findings, and offers optional review and independently approved correction export. The pilot does not analyze audiovisual content, measure the probability of misinformation, or assign generalized channel credibility scores. The implementation has passed 272 automated regression cases on the relevant release commit (GitHub Actions run 45011309492); the public hosting probe returned HTTP 303 and **did not confirm live application availability**. No observational news-item sample or consented participant experiment has been completed, so this report makes no empirical claims about prevalence, user trust, intervention effectiveness or country-level effects.

## 1. Problem and objective

A compelling thumbnail, title or description may be accurate, incomplete or misleading because of context. Similarity to an external fact-check does not prove that a video endorsed the fact-check's target assertion: the video may quote or debunk it. VeriLoop therefore targets a narrower and auditable problem than automatic fake-news detection: help a user find traceable related sources, expose uncertainty, and optionally escalate a specific claim to human review.

The **software question** is whether these cautious workflows can be implemented and tested in a free YouTube-metadata-first prototype. The separate **research question**, which remains untested here, is whether evidence-linked presentations influence actual users' claim judgments or simulated sharing intentions across different presentations of a documented event.

## 2. Implemented system

The frontend is Streamlit, with Python modules separating URL parsing, metadata collection, claim extraction, TF-IDF matching, limited context safeguards, optional Google Fact Check Tools queries, reviewer workflows, and export controls. SQLite stores eight canonical logical tables for channels, videos, claims, curated evidence, matches, preliminary assessments, reviews and corrections.

The public interface accepts supported YouTube video URL formats and requests official metadata. Candidate claims are extracted from title/description; up to five are ranked by topic relevance and checkable details. Their tentative stance is distinguished as ASSERTS, DEBUNKS, QUOTES or UNCLEAR when metadata permits. The local 13-record library is a purposively selected **reference corpus**, not a measured representative sample. Search similarities are used for retrieval, not calibrated truth percentages.

Preliminary user feedback distinguishes a previously reviewed exact-context match, a possible related evidence match, insufficient evidence and data retrieval errors. Optional external results remain third-party publisher claims, **not** automatically verified results about the submitted video. The public reviewed channel history displays only claims with explicit approval, linked evidence and validated audit provenance; it is neither a comprehensive history nor a channel trust score.

A user can request human review of a selected metadata claim. Approval requires a named reviewer, rationale, confirmed context and supporting source. Correction drafts require separate editorial approval before a manual Markdown export. The reviewer workspace has a password gate for this research pilot. Owner-initiated AES-GCM encrypted snapshots allow manually archived recovery to an empty-user-data instance; ephemeral Streamlit Cloud SQLite is **not durable storage** and this is not automatic backup or production identity management.

## 3. Method and validation

The engineering evaluation uses deterministic offline unit and Streamlit script-interaction tests for URL validation, metadata/API error handling, stance and negation safeguards, retrieval provenance, review-state transitions, approved-only history, correction/editor separation, audit rejection, encrypted archive round trips and authenticated reviewer session handling. Test videos, reviewers and approvals are fixtures rather than documented real-world decisions.

On commit `4a3dcb0`, GitHub Actions run **45011309492** passed **272/272** Python tests and `compileall`. A separate public deployment health request using the GitHub Actions runner got **HTTP 303**, classified `NOT_CONFIRMED`. A successful code test, or even a healthy server endpoint, would not by itself constitute a hosted end-to-end user acceptance test. A subsequent documentation-only commit is not represented as a new functional validation.

The case references in `data/demo_cases.json` cover a misleading-context investigation candidate, NASA's 2024 eclipse, and unresolved UAP evidence. They are **prepared research candidates**, not 3 new human-approved video verdicts or a validation sample. Prior owner-supplied screenshots demonstrate some real metadata retrieval, but this report does not infer arbitrary-video success or a live positive Google fact-check result.

## 4. Research materials and missing observations

The separate `research/news_dataset.csv` contains **zero observation rows**. The proposed collection size of 20–30 items, annotation rubric and event-matching procedures are protocols, not achieved recruitment or collection. `research/USER_PILOT_PROTOCOL.md` proposes conditions, consent and a questionnaire but no participant has been recorded and no ethics approval is assumed.

Five starting academic references are listed in `research/literature_matrix.csv`, including misinformation diffusion, crowdsourced source judgments, accuracy nudges, correction presentation and cognitive mechanisms. Bibliographic metadata has been checked; study-specific findings and relevance should be verified in full text before making literature claims. The literature matrix is not a completed systematic review.

Consequently, **no** experimental effect size, confidence interval, participant trust change, cross-country effect, intervention superiority, recall/precision on a held-out dataset or representative misinformation proportion can be reported. Treat these as research goals for a future properly approved study.

## 5. Limitations and threats to validity

The analysis does not inspect narration, transcript, original footage, audiovisual manipulation or frames. The metadata can omit the central claim, contain quotations, be updated later or lack English factual text. Keyword/context heuristics cannot establish semantic entailment; unrelated references may rank as similar. Google Fact Check Tools indexes third-party fact-check publications rather than the open web and may return no relevant result. The 13 references were curated for demonstrative coverage, creating selection and example-overlap risks. Code-level regressions cannot validate measured real-world accuracy or credibility impact.

The reviewer gate uses a shared pilot password and free cloud SQLite is ephemeral. An encrypted file only protects a snapshot that the owner actually downloads and retains with a separate passphrase. Reviewer decisions should not be presented as durable or independently endorsed without a genuine hosted acceptance check. Public video metadata availability and third-party link access may change.

## 6. Conclusion

VeriLoop provides a code-verified technical prototype for evidence-linked, uncertainty-aware **claim-level** YouTube metadata exploration and controlled human-review/correction workflows. The correct deliverable classification today is **functional MVP code and technical feasibility evaluation**, with deployment and research collection limitations explicitly declared—not a completed causal user study or fully validated automated fact-checker. Further acceptance requires checking a real hosted submission/reviewer/correction/archive sequence and, separately, carrying out ethically permitted, documented data collection.

## References and reproducibility

The canonical feature contract and decisions are in `PROJECT_SOURCE_OF_TRUTH.md`; implementation and commands are in `README.md`. The cited pilot bibliography with URLs/DOIs is in `research/literature_matrix.csv`. Annotation rules, separate observation schema, prepared cases and conditional participant study protocol are in `research/annotation_guide.md`, `research/news_dataset.csv`, `data/demo_cases.json`, and `research/USER_PILOT_PROTOCOL.md`. Verification evidence: https://github.com/towhidReshad/veriloop/actions/runs/45011309492 .
