"""Tests for the reproducible OpenCode research-worker prompt contract."""

from __future__ import annotations

from product_ops.research_agent import build_research_prompt


def test_worker_prompt_is_category_scoped_and_demands_claim_level_evidence() -> None:
    prompt = build_research_prompt(
        [
            {"id": 1, "name": "Salesforce", "category": "CRM and Sales", "hint": "salesforce.com"},
            {"id": 2, "name": "HubSpot", "category": "CRM and Sales", "hint": "hubspot.com"},
        ]
    )

    assert "ONLY these 2 apps" in prompt
    assert "1 Salesforce (salesforce.com)" in prompt
    assert "2 HubSpot (hubspot.com)" in prompt
    assert '"auth_url"' in prompt
    assert '"mcp_url"' in prompt
    assert "Do not invent facts" in prompt
    assert "primary vendor documentation" in prompt
