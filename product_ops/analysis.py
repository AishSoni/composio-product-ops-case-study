"""Deterministic aggregation of the validated research dataset."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


def _sorted_counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build transparent counts and actionable queues without model inference."""
    auth_methods = [method for record in records for method in record.get("auth_methods", [])]
    access_statuses = [record.get("access", {}).get("status", "unclear") for record in records]
    verdicts = [record.get("buildability", {}).get("verdict", "unclear") for record in records]
    mcp_statuses = [record.get("api", {}).get("mcp", "unclear") for record in records]
    categories = [record.get("category", "Uncategorized") for record in records]

    easy_wins = sorted(
        [
            record
            for record in records
            if record.get("buildability", {}).get("verdict") == "buildable_today"
            and record.get("access", {}).get("status") in {"free_self_serve", "trial_self_serve"}
            and record.get("confidence") in {"high", "medium"}
        ],
        key=lambda record: record["id"],
    )
    outreach_queue = sorted(
        [
            record
            for record in records
            if record.get("access", {}).get("status") in {"admin_approval", "partner_or_sales_gated"}
            or record.get("buildability", {}).get("verdict") in {"partial", "blocked"}
        ],
        key=lambda record: record["id"],
    )

    category_breakdown: dict[str, dict[str, Any]] = {}
    for category in sorted(set(categories)):
        rows = [record for record in records if record.get("category") == category]
        category_breakdown[category] = {
            "apps": len(rows),
            "free_or_trial_self_serve": sum(
                record.get("access", {}).get("status") in {"free_self_serve", "trial_self_serve"}
                for record in rows
            ),
            "gated_or_approval": sum(
                record.get("access", {}).get("status") in {"admin_approval", "partner_or_sales_gated"}
                for record in rows
            ),
            "buildable_today": sum(
                record.get("buildability", {}).get("verdict") == "buildable_today" for record in rows
            ),
        }

    return {
        "total_apps": len(records),
        "auth_counts": _sorted_counts(auth_methods),
        "access_counts": _sorted_counts(access_statuses),
        "buildability_counts": _sorted_counts(verdicts),
        "mcp_counts": _sorted_counts(mcp_statuses),
        "category_counts": _sorted_counts(categories),
        "category_breakdown": category_breakdown,
        "easy_wins": easy_wins,
        "outreach_queue": outreach_queue,
    }
