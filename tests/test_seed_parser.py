"""Regression tests for extracting the assignment's fixed research set."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "assignment.md"


def test_seed_parser_cli_extracts_the_complete_100_app_research_set(tmp_path: Path) -> None:
    """The runnable seed stage must faithfully preserve the supplied 100-app set."""
    output = tmp_path / "apps.seed.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "product_ops.seed_parser",
            "--input",
            str(ASSIGNMENT),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    records = json.loads(output.read_text(encoding="utf-8"))

    assert len(records) == 100
    assert [record["id"] for record in records] == list(range(1, 101))
    assert records[0] == {
        "id": 1,
        "name": "Salesforce",
        "category": "CRM and Sales",
        "hint": "salesforce.com",
    }
    assert records[-1] == {
        "id": 100,
        "name": "Grain",
        "category": "AI, Research and Media-native",
        "hint": "grain.com (meeting notes)",
    }
    assert {record["category"] for record in records} == {
        "CRM and Sales",
        "Support and Helpdesk",
        "Communications and Messaging",
        "Marketing, Ads, Email and Social",
        "Ecommerce",
        "Data, SEO and Scraping",
        "Developer, Infra and Data platforms",
        "Productivity and Project Management",
        "Finance and Fintech",
        "AI, Research and Media-native",
    }
    assert all(record["name"] and record["hint"] for record in records)
