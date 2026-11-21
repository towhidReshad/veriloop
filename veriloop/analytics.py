"""F-11 pilot sample summaries; never infer population misinformation rates."""
from __future__ import annotations
import csv
from collections import Counter
from pathlib import Path

EXPECTED = (
    "item_id", "youtube_url", "youtube_id", "channel_id", "published_at",
    "collected_at", "headline_or_title", "description", "thumbnail_url",
    "language", "source_country_if_supported", "event_id", "event_date",
    "event_location", "claim_text", "presentation_label", "claim_verdict",
    "evidence_url", "annotation_notes", "reviewer_identifier", "annotation_date"
)
RESOLVED = frozenset({"SUPPORTED", "CONTRADICTED", "MISLEADING_CONTEXT"})

def load_sample(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or any(k not in reader.fieldnames for k in EXPECTED):
            raise ValueError("Observational sample CSV is missing required columns")
        records = list(reader)
    keys: set[str] = set()
    for record in records:
        ident = record["item_id"].strip()
        if not ident or ident in keys:
            raise ValueError("Observation has a missing or duplicate item_id")
        keys.add(ident)
    return records

def summarize_sample(records: list[dict[str, str]]) -> dict:
    verdicts = Counter((r["claim_verdict"].strip().upper() or "UNRESOLVED") for r in records)
    resolved_count = sum(v for k, v in verdicts.items() if k in RESOLVED)
    unresolved_count = len(records) - resolved_count
    events = Counter((r["event_id"].strip() or "Undocumented") for r in records)
    categories = Counter((r["presentation_label"].strip() or "Unannotated") for r in records)
    countries = Counter((r["source_country_if_supported"].strip() or "Not documented") for r in records)
    dates = Counter((r["published_at"][:10] or "Unknown") for r in records)
    return {
        "sample_size": len(records), "resolved_count": resolved_count,
        "unresolved_count": unresolved_count,
        "verdicts": dict(verdicts), "events": dict(events),
        "categories": dict(categories), "countries": dict(countries),
        "publication_dates": dict(dates),
    }
