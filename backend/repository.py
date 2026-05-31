"""Inventory data-access layer (the "repository" seam).

Phase 1: reads the static demo dataset from ``data/carData.json``.
Phase 3: this becomes a Supabase Postgres query — callers in ``main.py`` stay
the same, only this module changes.
"""

import json
import os

DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "carData.json")
)


def get_listings():
    """Return the list of vehicle listings, or ``[]`` if unavailable."""
    if not os.path.exists(DATA_PATH):
        print(f"[repository] carData.json not found at {DATA_PATH}", flush=True)
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("listings", [])
    except Exception as exc:  # noqa: BLE001 — best-effort load
        print(f"[repository] failed to load listings: {exc}", flush=True)
        return []
