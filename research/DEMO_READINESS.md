# VeriLoop professor demonstration readiness checklist

**Status:** Prepared procedure; no invented approvals, observational claims, or API-positive responses.

## Site and repository

- Public hosted app: https://veriloop-research.streamlit.app
- Code: https://github.com/towhidReshad/veriloop
- Branch: `main`; check GitHub Actions before demonstrating
- App Settings → Secrets: `YOUTUBE_API_KEY`; optionally `FACTCHECK_API_KEY`
- Owner-only `REVIEWER_PASSWORD` is required for the reviewer and private backup pages; never show it on screen or commit it

## Real A/B/C demonstrations (do not substitute claims)

**A — Misleading context candidate:** `https://www.youtube.com/watch?v=GEG-K7TbKt0`; factual article: https://factcheck.afp.com/doc.afp.com.34TR7Q3 . The video/API accessibility and exact-context claim approval are NOT confirmed. If unavailable, explain the documented AFP candidate as an **offline source example**, not as a live app verdict. Do not label the original authentic India footage misleading.

**B — Supported eclipse event:** `https://www.youtube.com/watch?v=2MJY_ptQW1o`; source: https://science.nasa.gov/eclipses/future-eclipses/eclipse-2024/ . Owner previously demonstrated live NASA metadata. Link a specific title/description claim to the NASA source, distinguish tentative retrieval from human-approved finding.

**C — Unresolved UAP example:** `https://www.youtube.com/watch?v=TQcqOW39ksk`; source: https://science.nasa.gov/uap/ . Live availability unconfirmed; no assertion about extraterrestrial origin is warranted. An item without an extractable factual statement must show **no claim** or **insufficient evidence**, not invent a false claim.

## Human review and correction path

1. Any public user enters one accessible YouTube video URL and immediately gets a **preliminary** report (no automatic accusation).
2. Public user requests review for a specific candidate claim.
3. Reviewer signs in privately, compares claim stance/date/location, and records an evidence-linked human decision. Do not approve solely by TF-IDF/topic overlap.
4. The exact unchanged video/metadata/claim may later display a **previously reviewed** historical finding. Otherwise keep the new case tentative.
5. To create a correction, use a human-approved claim, save a draft, submit it, and have a **different identified editor** separately approve its content. Only then is manual Markdown export possible.
6. Download a private encrypted `.vlbackup` from the reviewer page; save the file and passphrase separately. Restore accepts **only an empty user-data database**. No automatic archive or external publishing.

## Evidence/research integrity

- Verification reference library: 13 curated source records; it is NOT the pilot observation sample.
- `research/news_dataset.csv` currently has **0** observation rows. Research dashboard should show no fabricated statistics.
- Google Fact Check Tools can return unrelated/no results even for supported public videos. This feature is optional and **no verified positive external API retrieval has yet been reported**.
- Thumbnail and metadata are display/retrieval inputs; the application does not check video audio or arbitrary frames.
- No generalized channel trust score, universal truth detector, fake participant responses, or guaranteed 100% accuracy.

## Demonstration acceptance record (fill with actual observations)

| Test | Real result | Evidence captured |
|---|---|---|
| Public app opens with no paid domain | Not yet checked in this session | — |
| A misleading-context candidate accurately scoped | Pending original-video access and independent review | — |
| B NASA metadata and supporting reference | Previously owner-demonstrated, reviewed verdict pending | — |
| C unknown claim handled responsibly | Pending | — |
| Request -> human decision -> reviewed history | Pending hosted end-to-end check | — |
| Separate editor approves Markdown export | Pending hosted end-to-end check | — |
| Encrypted backup downloaded, restored into empty instance | Pending hosted end-to-end check | — |
| Zero-data observational dashboard honest | Automated tests only; hosted check pending | — |

No new human-review approval, publication, or field-research result is implied by this checklist.


## Offline-only preparation (not in the public app)

The A/B/C source-linked references in this document and `data/demo_cases.json` are **offline preparation**, not a Streamlit professor-demo page, cached metadata or a reviewed video verdict. Use the actual public Verify News form for live behavior. The participant protocol and literature planning matrix remain academic documentation outside the software UI.

**Public UI correction (2026-11-21):** The professor guide is **not a public Streamlit page** anymore. Use this documentation or `data/demo_cases.json` outside the software. The separately runnable research dashboard lives at `research/research_dashboard_app.py` and must not be linked from the general-user app. The live Verify News page remains the only way to show real submitted-video metadata results.


## Owner-observed successful live matching — 2026-11-26 (evidence screenshots)

Two genuine, distinct retrieval paths were demonstrated in the deployed Streamlit app:

| Path | Exact YouTube URL | Extracted statements | Statements with related sources | Provenance displayed | Classification boundary |
|---|---|---:|---:|---|---|
| Curated local evidence | https://www.youtube.com/watch?v=GEG-K7TbKt0 | 1 | 1 | Local EV-001, AFP Fact Check, source URL | Source labeled MISLEADING_CONTEXT; VeriLoop returned unconfirmed related evidence, not an approved video verdict |
| Google Fact Check API | https://www.youtube.com/watch?v=anHwQIaZlZ0 | 4 | 1 | Four linked Google-indexed reviews: Fact Crescendo (1), AFP Fact Check (2), AAP (1) | External article ratings shown separately; claim context UNCONFIRMED; overall video assessment NOT DETERMINED |
| No-match behavior, same Dubai video | same as above | 3 of 4 | 0 for those three | Explicit insufficient-evidence descriptions | No false/unverified accusations |

**Evidence type:** Owner-supplied live browser screenshots, not an independent benchmark or editorial approval. Google API returned actual articles after v5 topical reranking; this establishes a successful positive API retrieval in the observed session, but does not independently verify all four fact-check articles' full texts, general accuracy, geographic reliability, or claimed video stance. Do not replace these results with illustrative statistics.

**Release policy:** Both local and live-index retrieval have been demonstrated. Freeze retrieval functionality except a reproducible critical defect. Professor demonstration order: local Karachi → Google API Dubai → three Dubai unmatched claims. No new research sample/participants are implied. Source links should be opened live only when needed.


## Owner-observed additional six-video browser checks — 2026-11-26

The following were supplied as **screenshots of deployed VeriLoop results**. The numbers below are extracted from screenshots, not independent replication or quality/accuracy measurements. A source match is a retrieval lead and **not** a video truth verdict.

| YouTube video | ID | Candidate statements | Statements with related sources | Without match | Observed origin or notable limitation |
|---|---|---:|---:|---:|---|
| Pope Francis puffer jacket (Inside Edition) | `BCjhg994fIU` | 5 | 2 | 3 | Google-indexed reviews: Lead Stories, Snopes, Full Fact visible for selected claim; actual article counts are different from matched-claim count |
| Dubai cloud seeding (Sky News) | `KdcVDdCR0Q0` | 5 | 0 | 5 | Google API NO_RESULTS for selected claim; no usable linked article returned, despite related France24 case succeeding |
| Buzz Aldrin moon landing video | `0tEgfxmVGUc` | 5 | 0 | 5 | Google API NO_RESULTS for selected claim; no usable linked article shown |
| NASA UAP Independent Study | `TQcqOW39ksk` | 5 | 1 | 4 | Local NASA UAP reference matched **title**, but title is a topic label rather than a clear factual assertion; candidate extraction warrants review |
| UNDRR earthquake prediction | `KRI1JKIQ4RQ` | 2 | 0 | 2 | Potential retrieval false-negative: USGS curated EV-005 discusses inability to predict exact date/location/magnitude; inspected claim concerns exact date only. Human context check needed; no forced match |
| 2024 eclipse (Space Affairs replay) | `vcdDOE7Gwrg` | 5 | 3 | 2 | Curated NASA EV-002 shown for selected claim; uploader is **Space Affairs**, not NASA, despite NASA material in title/image |

**Observed caution:** Screenshots suggest claim extraction sometimes treats a topical heading/title as a claim (NASA UAP title), and an unrelated social/media description item may be selected as a candidate (Sky News and Buzz Aldrin description lists). These are quality limitations, not fabricated results. Overall assessment remained NOT DETERMINED in all six screenshots.

**Demonstration shortlist:** 
- Local positive: Karachi Mayor -> AFP EV-001 (previously demonstrated); eclipse replay -> NASA evidence.
- Google index positive: France 24 Dubai -> 4 indexed articles (previously demonstrated); Pope puffer jacket -> 2 matched claims with linked publisher articles.
- No match: Sky News Dubai (0/5); Buzz Aldrin clip (0/5); UNDRR earthquake (0/2, note missed local reference).
- UAP: contextual uncertainty example, not a claim about extraterrestrial origin.

**Freeze status:** Treat these as observed test cases. Do not use the matched numbers as precision/recall. Do not mark unreviewed YouTube uploads as true or misleading.
