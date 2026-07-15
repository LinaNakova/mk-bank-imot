"""Merge a fresh scrape with the previous data file.

- Keeps only currently-listed properties (removed ones drop off).
- Preserves first_seen from prior runs so we can flag what's genuinely new.
- Marks is_new = first seen within the last NEW_WINDOW_DAYS.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta

NEW_WINDOW_DAYS = 7


def _clean(v):
    if isinstance(v, str) and not v.strip():
        return None
    return v


def merge(fresh: list[dict], data_path: str) -> dict:
    today = date.today()
    today_s = today.isoformat()

    prev_first: dict[str, str] = {}
    if os.path.exists(data_path):
        try:
            with open(data_path, encoding="utf-8") as f:
                old = json.load(f)
            for it in old.get("listings", []):
                prev_first[it["id"]] = it.get("first_seen", today_s)
        except Exception:
            pass

    # de-dup fresh by id (adapters can occasionally emit the same ref twice)
    by_id: dict[str, dict] = {}
    for it in fresh:
        it = {k: _clean(v) for k, v in it.items()}
        by_id[it["id"]] = it

    listings = []
    for it in by_id.values():
        first = prev_first.get(it["id"], today_s)
        try:
            is_new = (today - date.fromisoformat(first)).days < NEW_WINDOW_DAYS
        except Exception:
            is_new = first == today_s
        it["first_seen"] = first
        it["last_seen"] = today_s
        it["is_new"] = is_new
        listings.append(it)

    # newest first, then by bank
    listings.sort(key=lambda x: (not x["is_new"], x["bank"], x["title"]))

    banks: dict[str, int] = {}
    for it in listings:
        banks[it["bank"]] = banks.get(it["bank"], 0) + 1

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "count": len(listings),
        "new_count": sum(1 for x in listings if x["is_new"]),
        "banks": banks,
        "listings": listings,
    }
