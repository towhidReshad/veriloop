# VeriLoop technical pilot report — draft

## Research status

The public Streamlit research demonstration retrieves official metadata for
supported public YouTube videos, produces tentative textual claim candidates,
searches an explicitly small curated evidence reference library and optionally
checks Google's indexed published fact-check articles. A source match does not
establish claim truth or video credibility.

## Observational pilot

The separate \`research/news_dataset.csv\` observational dataset currently has
zero observation rows. No representative prevalence estimate, hypothesis
test, treatment-effect result, user-survey outcome or country comparison has
been conducted. No participant observations have been invented.

## Method

Use the frozen inclusion and annotation criteria in
\`PROJECT_SOURCE_OF_TRUTH.md\`. Preserve item provenance, exact claim text,
date and event context. Store resolved and unresolved reviewer decisions
separately. Document that reference evidence is not an observational sample.

## Current limitations

YouTube title/description only; no claim that transcript/audio/frames have been
verified. Up to five relevance-ranked statements from bounded metadata may
miss important claims. Local TF-IDF similarity and lexically checked context
are not semantic entailment or probabilities of falsehood. Google Fact Check
Tools indexes third-party published reviews, not the entire internet.
A positive live response is still unverified. Free Streamlit Cloud SQLite is
not durable archival storage; approved corrections require independent
editorial approval and private manual archive. No automatic social posting.

## Required next evidence

Complete the documented observational sample if feasible; independently
annotate claims, note reviewer disagreements and unresolved status, and
report descriptive sample counts only. Conduct A/B/C professor demonstrations
using genuine sourced cases. Never manufacture research data to fill a chart.
