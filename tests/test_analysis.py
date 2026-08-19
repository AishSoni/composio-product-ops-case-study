"""Tests for deterministic, explainable cross-app pattern analysis."""

from __future__ import annotations

from product_ops.analysis import summarize_records


def _record(
    app_id: int,
    *,
    auth: list[str],
    access: str,
    verdict: str,
    category: str = "CRM and Sales",
    mcp: str = "none_found",
    confidence: str = "high",
) -> dict:
    return {
        "id": app_id,
        "name": f"App {app_id}",
        "category": category,
        "auth_methods": auth,
        "access": {"status": access, "note": "Evidence note."},
        "api": {"documented": True, "protocols": ["REST"], "breadth": "broad", "mcp": mcp, "note": "Evidence note."},
        "buildability": {"verdict": verdict, "blocker": None if verdict == "buildable_today" else "Access gate."},
        "confidence": confidence,
    }


def test_summary_counts_multi_auth_and_prioritizes_evidence_backed_easy_wins() -> None:
    records = [
        _record(1, auth=["OAuth2"], access="free_self_serve", verdict="buildable_today", mcp="official"),
        _record(2, auth=["OAuth2", "API key"], access="trial_self_serve", verdict="buildable_today"),
        _record(3, auth=["API key"], access="partner_or_sales_gated", verdict="partial", category="Finance and Fintech"),
    ]

    summary = summarize_records(records)

    assert summary["total_apps"] == 3
    assert summary["auth_counts"] == {"API key": 2, "OAuth2": 2}
    assert summary["access_counts"] == {
        "free_self_serve": 1,
        "partner_or_sales_gated": 1,
        "trial_self_serve": 1,
    }
    assert summary["buildability_counts"] == {"buildable_today": 2, "partial": 1}
    assert summary["mcp_counts"] == {"none_found": 2, "official": 1}
    assert [app["id"] for app in summary["easy_wins"]] == [1, 2]
    assert [app["id"] for app in summary["outreach_queue"]] == [3]
