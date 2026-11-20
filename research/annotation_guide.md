# VeriLoop pilot annotation guide (initial, Day 2)

Authority: PROJECT_SOURCE_OF_TRUTH.md Sections 3, 4.5, 10. This is a research procedure, not a competing scope document.

## Two independent collections

- **A. Verification library** (data/seed_evidence.json): purposively chosen source-backed claims for local retrieval tests. No platform prevalence can be inferred from these records. An external publisher's determination is not a VeriLoop human review.
- **B. Observational news sample** (research/news_dataset.csv): target 20–30 public YouTube news items if feasible. Record inclusion criteria, collection window, event matching, original content, outlet country where supported, claim context, reviewer notes and uncertainty. **No items have yet been collected in this file.**

## Collection B procedure

1. Choose a defined event and collection date window; log why a video is eligible. Select different outlet presentations of the *same independently verified event* where feasible. Keep duplicates/reposts traceable rather than assuming unique claims.
2. Record YouTube URL and ID, channel ID, title, description, publication and collection timestamps; record original screenshot/thumbnail references only where permissible.
3. Keep distinct (a) **outlet/source country** with supporting source, (b) **event country/location**, and (c) any **participant/viewer country**. Do not infer outlet country from language.
4. Record factual claim as stated, whether **ASSERTS / DEBUNKS / QUOTES / UNCLEAR**, and original event/date/place context. Headlines may be sensational and accurate.
5. Label *neutral*, *sensational-but-accurate*, *contradicted*, *misleading context*, *misleading omission* (only when demonstrated), or *insufficient evidence*. Attach relevant **exact source URL, evidence scope, and date**.
6. Request a second independent annotator when feasible; log disagreements and adjudication. An automated similarity score is never a misinformation probability.
7. Keep unresolved items visible. Report sample selection, denominators, date range and limits; never claim global or representative misinformation rates. Run any human-facing pilot only with required consent/approval.

All factual findings are provisional until research annotations and required human review have been completed. No fake participants or studies are entered.
