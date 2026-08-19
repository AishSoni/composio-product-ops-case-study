"""Tests for safely converting OpenCode's event stream into research records."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_opencode_event_parser_extracts_only_the_final_fenced_json_array(tmp_path: Path) -> None:
    events = tmp_path / "worker.events.jsonl"
    output = tmp_path / "records.json"
    first_event = {"type": "tool_use", "part": {"type": "tool", "tool": "websearch"}}
    final_records = [
        {
            "id": 1,
            "name": "Salesforce",
            "category": "CRM and Sales",
            "one_line": "CRM.",
            "auth_methods": ["OAuth2"],
            "access": {"status": "free_self_serve", "note": "Developer org."},
            "api": {
                "documented": True,
                "protocols": ["REST"],
                "breadth": "broad",
                "mcp": "official",
                "note": "Official MCP.",
            },
            "buildability": {"verdict": "buildable_today", "blocker": None},
            "evidence": {
                "auth_url": "https://developer.salesforce.com/auth",
                "access_url": "https://developer.salesforce.com/signup",
                "api_url": "https://developer.salesforce.com/api",
                "mcp_url": "https://github.com/salesforce/mcp",
            },
            "confidence": "high",
            "research_notes": "Checked official documentation.",
        }
    ]
    final_event = {
        "type": "text",
        "part": {
            "type": "text",
            "text": "Research complete.\n```json\n"
            + json.dumps(final_records)
            + "\n```",
        },
    }
    postscript_event = {
        "type": "text",
        "part": {
            "type": "text",
            "text": "The research JSON was delivered in the previous message.",
        },
    }
    events.write_text(
        "\n".join(json.dumps(event) for event in [first_event, final_event, postscript_event]) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "product_ops.opencode_runner",
            "parse-events",
            "--input",
            str(events),
            "--output",
            str(output),
            "--expected-ids",
            "1",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text(encoding="utf-8")) == final_records
