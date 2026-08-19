"""Schema-level guardrails that prevent unsupported research claims from rendering."""

from __future__ import annotations

from product_ops.validation import validate_records


def _record() -> dict:
    return {
        "id": 1,
        "name": "Example CRM",
        "category": "CRM and Sales",
        "hint": "example.com",
        "one_line": "A test CRM.",
        "auth_methods": ["OAuth2"],
        "access": {"status": "free_self_serve", "note": "Free developer account."},
        "api": {
            "documented": True,
            "protocols": ["REST"],
            "breadth": "broad",
            "mcp": "official",
            "note": "Official MCP server exists.",
        },
        "buildability": {"verdict": "buildable_today", "blocker": None},
        "evidence": {
            "auth_url": "https://docs.example.com/auth",
            "access_url": "https://example.com/pricing",
            "api_url": "https://docs.example.com/api",
            "mcp_url": "https://docs.example.com/mcp",
        },
        "confidence": "high",
        "research_notes": "All fields were sourced from official pages.",
    }


def test_validation_accepts_an_evidence_complete_buildable_record() -> None:
    assert validate_records([_record()]) == []


def test_validation_blocks_unsupported_claims_before_they_reach_the_case_study() -> None:
    record = _record()
    record["id"] = 2
    record["evidence"]["auth_url"] = ""
    record["api"]["mcp"] = "official"
    record["evidence"]["mcp_url"] = None
    record["buildability"] = {"verdict": "partial", "blocker": None}

    issues = validate_records([record])

    assert {issue["field"] for issue in issues} == {
        "evidence.auth_url",
        "evidence.mcp_url",
        "buildability.blocker",
    }
