"""Run category-scoped, evidence-first OpenCode research workers reproducibly."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from product_ops.opencode_runner import parse_events_to_file


def build_research_prompt(records: list[dict[str, Any]]) -> str:
    """Create a strict, category-scoped contract for one OpenCode research worker."""
    if not records:
        raise ValueError("At least one seed record is required")
    categories = {record["category"] for record in records}
    if len(categories) != 1:
        raise ValueError("A worker must research exactly one category")

    app_lines = "\n".join(f"- {record['id']} {record['name']} ({record['hint']})" for record in records)
    category = next(iter(categories))
    return f'''Act as an evidence-first product-ops research worker. Research ONLY these {len(records)} apps in {category}:
{app_lines}

Use primary vendor documentation or official vendor pages for every factual claim. Do not modify files. Return ONLY a JSON array in the final response (no Markdown), exactly in the supplied ID order. Each object must follow this schema:
{{
  "id": int,
  "name": str,
  "category": "{category}",
  "one_line": str,
  "auth_methods": ["OAuth2" | "API key" | "Basic" | "token" | "other"],
  "access": {{"status": "free_self_serve" | "trial_self_serve" | "paid_self_serve" | "admin_approval" | "partner_or_sales_gated" | "unclear", "note": str}},
  "api": {{"documented": bool, "protocols": [str], "breadth": "narrow" | "moderate" | "broad" | "unclear", "mcp": "official" | "community" | "none_found" | "unclear", "note": str}},
              "buildability": {{"verdict": "buildable_today" | "partial" | "blocked" | "unclear", "blocker": str | null}},
              "evidence": {{"auth_url": str, "access_url": str, "api_url": str, "mcp_url": str | null}},
              "confidence": "high" | "medium" | "low",
              "research_notes": str
  }}

  Evidence rules: auth_url, access_url, and api_url must be actual checked http(s) URLs; if you claim an official or community MCP, mcp_url MUST be a real GitHub repo or vendor page URL (not null). Never claim an absence as proven—use unclear and lower confidence if first-party evidence is unavailable. Do not invent facts.'''


def run_worker(
    records: list[dict[str, Any]],
    *,
    events_path: Path,
    output_path: Path,
    workdir: Path,
    opencode_binary: str = "opencode",
) -> list[dict[str, Any]]:
    """Run OpenCode, retain its full event evidence, then normalize its final answer."""
    prompt = build_research_prompt(records)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("w", encoding="utf-8", newline="") as event_stream:
        result = subprocess.run(
            [
                opencode_binary,
                "run",
                "--format",
                "json",
                "--title",
                f"{records[0]['category']} research first pass",
                prompt,
            ],
            cwd=workdir,
            text=True,
            stdout=event_stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(f"OpenCode worker failed with exit code {result.returncode}; see {events_path}")
    return parse_events_to_file(events_path, output_path, [record["id"] for record in records])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, required=True, help="Seed JSON generated from assignment.md")
    parser.add_argument("--category", required=True, help="Exact category name to research")
    parser.add_argument("--events", type=Path, required=True, help="Path to retain raw OpenCode JSONL")
    parser.add_argument("--output", type=Path, required=True, help="Normalized category records JSON")
    parser.add_argument("--opencode", default="opencode", help="OpenCode binary path")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without calling OpenCode")
    args = parser.parse_args()

    seeds = json.loads(args.seed.read_text(encoding="utf-8"))
    records = [record for record in seeds if record["category"] == args.category]
    if not records:
        raise ValueError(f"No seed records matched category {args.category!r}")
    if args.dry_run:
        print(build_research_prompt(records))
        return

    normalized = run_worker(
        records,
        events_path=args.events,
        output_path=args.output,
        workdir=Path.cwd(),
        opencode_binary=args.opencode,
    )
    print(f"Researched {len(normalized)} apps; saved raw events to {args.events} and records to {args.output}")


if __name__ == "__main__":
    main()
