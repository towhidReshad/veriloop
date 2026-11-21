# VeriLoop — conditional user research protocol (not yet conducted)

**Status:** Proposed study material only. No participants recruited, no data collected, no ethical/institutional clearance assumed. Follow the professor's and institution's approval process before recruiting anyone.

## Research purpose

Evaluate whether evidence-linked, claim-specific reports affect a participant's assessment of an online news item's **specific claim** compared with no assistance or a minimal fact-check label. The separate research question about variations in presentation (accurate, sensational-but-accurate, misleading) requires selected event-matched exemplars with independent evidence and permissions. The pilot cannot establish society-wide impact or globally representative accuracy.

## Eligibility and informed consent

Recruit only adults (18+) who can give informed consent and understand the materials in English. Do not recruit university students whose course grades depend on participation. Obtain institutional/ethics clearance where required before solicitation. Participation must be voluntary, with withdrawal permitted under the approved protocol. No passwords, personal contact details, precise location, or political affiliation should be collected.

### Suggested consent text (must be reviewed locally)

> You are invited to participate in a university pilot exploring how people evaluate selected publicly available news claims. You will view a small number of news examples and may be shown related source information. Participation is voluntary, you may skip questions, and you may stop at any point without penalty. Some examples contain disputed statements presented for research; they are not endorsed by the research team. We will collect your choices and optional written feedback without requesting your name or email. Data will be reported only in aggregate. Your institutionally approved information sheet will explain storage, deletion and research contacts. Do you consent to participate?

**Consent response:** Yes / No. If No, stop. Do not record an unconsented participant's responses.

## Study conditions, subject to approved design

- **Condition A, control:** news example, title and normal source information without VeriLoop.
- **Condition B, minimal label:** same example plus a short, properly sourced claim-level fact-check label (not a whole-channel score).
- **Condition C, evidence-linked:** same example plus original source citations, event/date/context caveats and uncertainty as VeriLoop displays.

Randomize condition order or assignment using a documented seed; do not always present one condition last. Match examples to the **same independently documented event** when comparing different headlines. Avoid presenting the same exact question three times to a respondent if it encourages memorization. Record which instrument version and randomization method were used.

## Proposed participant questions

After each item:

1. **Claim accuracy judgment:** “How accurate do you think the specific statement shown is?” (1 = Definitely inaccurate; 2 = Probably inaccurate; 3 = Unsure; 4 = Probably accurate; 5 = Definitely accurate).
2. **Confidence in judgment:** “How confident are you in your answer?” (1 = Not at all; 5 = Extremely).
3. **Simulated sharing intention:** “How likely would you be to share this item as news?” (1 = Very unlikely; 5 = Very likely). This is **intention**, not observed sharing behavior.
4. **Evidence understanding:** “Which piece of information most influenced your answer?” (short voluntary response).
5. **Uncertainty awareness:** “Does the available evidence support a definite conclusion about this *specific claim*?” (Yes / No / Unsure).

After the exercise:

6. “Was the difference between a topical reference and evidence for the exact claim clear?” (1 = Not at all; 5 = Very clear).
7. “Did the report overstate any certainty?” (Yes / No / Unsure; optional explanation).
8. “What, if anything, made the report hard to understand?” (optional free text).

## Recording template (do NOT upload raw participant responses to public GitHub)

Use anonymous random study IDs, not names. Columns: study_id, consent_recorded, assigned_condition, item_id, item_order, instrument_version, accuracy_1to5, confidence_1to5, sharing_intent_1to5, definite_conclusion, evidence_understanding_code, optional_feedback, collected_at_utc. Keep approved protocols and restricted participant files out of the public repository. Do not put real study responses into \`research/news_dataset.csv\`, which is a different *news-item observation* dataset.

## Analysis plan (only after real consented collection)

Report recruited/consented/completed counts, exclusions and missingness, item/condition-level descriptive summaries and sample sizes. If the design and sample allow, compare paired or randomized condition scores with confidence intervals and a predeclared analysis method. Do not conclude that VeriLoop improves user judgment without supporting observed data. Include negative and null outcomes and discuss selection, measurement, convenience sampling and item-order effects.

## No-approval contingency (legitimate seven-day deliverable)

If clearance or recruitment cannot be completed before the course deadline, submit this protocol and questionnaire **as planned, unconducted work**. Present only genuine software tests and case-source descriptions. State explicitly that no participant findings, causal effects, or empirical user trust changes were measured.

## Research-to-product separation

The 13 curated \`data/seed_evidence.json\` references are **verification reference records**, not 13 user participants or a news-item probability sample. The currently header-only \`research/news_dataset.csv\` contains zero sampled news observations. A/B/C demo cases are three curated examples, not a representative dataset.
