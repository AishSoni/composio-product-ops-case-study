"""Parse the fixed application list from the supplied assignment markdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CATEGORY_RE = re.compile(r"^###\s+\d+\.\s+(.+?)\s*$")
ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")


def parse_assignment(markdown: str) -> list[dict[str, Any]]:
    """Extract app ID, name, category, and supplied hint from assignment tables."""
    category: str | None = None
    records: list[dict[str, Any]] = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        category_match = CATEGORY_RE.match(line)
        if category_match:
            category = category_match.group(1)
            continue

        row_match = ROW_RE.match(line)
        if not row_match or category is None:
            continue

        app_id = int(row_match.group(1))
        records.append(
            {
                "id": app_id,
                "name": row_match.group(2).strip(),
                "category": category,
                "hint": row_match.group(3).strip(),
            }
        )

    expected_ids = list(range(1, 101))
    actual_ids = [record["id"] for record in records]
    if actual_ids != expected_ids:
        raise ValueError(
            f"Expected the 100 fixed app IDs 1–100; extracted {len(records)} records: {actual_ids!r}"
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Assignment markdown path")
    parser.add_argument("--output", type=Path, required=True, help="Seed JSON output path")
    args = parser.parse_args()

    records = parse_assignment(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} seed records to {args.output}")


if __name__ == "__main__":
    main()
