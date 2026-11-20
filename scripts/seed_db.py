"""Seed VeriLoop's curated, traceable evidence library: python scripts/seed_db.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from veriloop.db import DEFAULT_DB_PATH, connect_db, init_db, list_evidence, seed_evidence  # noqa: E402


def main() -> None:
    with connect_db() as conn:
        init_db(conn)
        inserted = seed_evidence(conn)
        count = len(list_evidence(conn))
    print(f"VeriLoop SQLite: {DEFAULT_DB_PATH}")
    print(f"Evidence records: {count} | Newly inserted: {inserted}")
    print("Reference records are not VeriLoop human-approved reviews.")


if __name__ == "__main__":
    main()
