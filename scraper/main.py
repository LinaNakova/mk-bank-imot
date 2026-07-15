"""Run all bank adapters, merge with existing data, write site/data/listings.json.

Every adapter is isolated: a failure in one bank never stops the others, and each
bank contributes at least a link so nothing silently disappears.

Usage:  python -m scraper.main
"""
import os
import sys
import time
import json
import traceback

from . import common as c
from .banks import ADAPTERS
from .merge import merge

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "..", "site", "data", "listings.json")


def run():
    s = c.session()
    all_listings = []
    report = []

    for mod in ADAPTERS:
        name = getattr(mod, "NAME", mod.__name__)
        t0 = time.time()
        try:
            items = mod.scrape(s) or []
            all_listings.extend(items)
            report.append((name, len(items), round(time.time() - t0, 1), ""))
        except Exception as e:  # never let one bank break the run
            traceback.print_exc()
            report.append((name, 0, round(time.time() - t0, 1), f"ERROR: {e}"))

    data = merge([x for x in all_listings if not c.is_noise(x["title"])], DATA_PATH)

    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # summary
    print("\n" + "=" * 56)
    print(f"{'BANK':<16}{'ITEMS':>7}{'SECS':>7}   NOTE")
    print("-" * 56)
    for name, n, secs, note in report:
        print(f"{name:<16}{n:>7}{secs:>7}   {note}")
    print("-" * 56)
    print(f"TOTAL listings: {data['count']}   NEW this week: {data['new_count']}")
    print(f"Written to: {os.path.relpath(DATA_PATH)}")
    print("=" * 56)

    # non-zero exit only if literally nothing came back
    return 0 if data["count"] else 1


if __name__ == "__main__":
    sys.exit(run())
