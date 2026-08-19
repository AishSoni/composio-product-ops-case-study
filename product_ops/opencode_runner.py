"""OpenCode worker integration for the evidence-first research pipeline.

The runner deliberately preserves the raw event stream and only accepts the
worker's final JSON payload. Tool logs and intermediate thoughts are never
silently interpreted as research results.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FENCED_JSON_RE = re.compile(r"```json\s*(\[.*\])\s*```", re.IGNORECASE | re.DOTALL)


def extract_final_records(events_text: str) -> list[dict[str, Any]]:
    """Return the newest valid JSON-array payload from an OpenCode JSONL stream.

    OpenCode can emit a plain closing message after delivering its JSON answer,
    so "last text event" is not synonymous with "last research payload." We
    deliberately walk text events in reverse and accept only a valid array.
    """
    text_events: list[str] = []
    for line in events_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part")
        if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
            text_events.append(part["text"])

    if not text_events:
        raise ValueError("OpenCode event stream has no text events")

    for text in reversed(text_events):
        # First try fenced JSON blocks
        candidates = [match.group(1) for match in FENCED_JSON_RE.finditer(text)]
        # Also look for raw JSON arrays that start with record pattern
        if not candidates:
            # Find arrays that start with [{"id": - our known record structure
            for match in re.finditer(r'(\[\s*\{\s*"id"\s*:)', text):
                start = match.start()
                # Find the matching closing bracket by counting
                bracket_count = 0
                in_string = False
                escape = False
                for i, ch in enumerate(text[start:], start):
                    if escape:
                        escape = False
                        continue
                    if ch == '\\':
                        escape = True
                        continue
                    if ch == '"' and not escape:
                        in_string = not in_string
                        continue
                    if not in_string:
                        if ch == '[':
                            bracket_count += 1
                        elif ch == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                candidate = text[start:i+1]
                                candidates.append(candidate)
                                break
        # Also look for any raw arrays (as fallback, sorted by length descending)
        if not candidates:
            array_candidates: list[str] = []
            for match in re.finditer(r'(\[.*?\])', text, re.DOTALL):
                array_candidates.append(match.group(1))
            array_candidates.sort(key=len, reverse=True)
            candidates.extend(array_candidates)

        for candidate in reversed(candidates):
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
                return payload

    raise ValueError("No valid JSON array was found in OpenCode text events")


def parse_expected_ids(spec: str) -> list[int]:
    """Parse a compact ID list such as ``1-10,15,17-18``."""
    ids: list[int] = []
    for item in (piece.strip() for piece in spec.split(",")):
        if not item:
            continue
        if "-" in item:
            start_text, end_text = item.split("-", maxsplit=1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ValueError(f"Invalid descending range: {item}")
            ids.extend(range(start, end + 1))
        else:
            ids.append(int(item))
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Expected IDs must be non-empty and unique")
    return ids


def parse_events_to_file(input_path: Path, output_path: Path, expected_ids: list[int]) -> list[dict[str, Any]]:
    """Parse, validate deterministic ordering, and write one worker's raw results."""
    records = extract_final_records(input_path.read_text(encoding="utf-8", errors="replace"))
    received_ids = [record.get("id") for record in records]
    if received_ids != expected_ids:
        raise ValueError(f"Worker returned IDs {received_ids!r}; expected {expected_ids!r}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    parse_events = subparsers.add_parser("parse-events", help="Extract final records from OpenCode JSONL output")
    parse_events.add_argument("--input", type=Path, required=True)
    parse_events.add_argument("--output", type=Path, required=True)
    parse_events.add_argument("--expected-ids", required=True, help="For example: 1-10 or 1,2,3")
    args = parser.parse_args()

    if args.command == "parse-events":
        records = parse_events_to_file(args.input, args.output, parse_expected_ids(args.expected_ids))
        print(f"Wrote {len(records)} normalized OpenCode research records to {args.output}")


if __name__ == "__main__":
    main()
