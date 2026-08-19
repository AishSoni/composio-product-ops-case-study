"""Verification loops for the research pipeline."""

from __future__ import annotations

import subprocess
from typing import Any


def l1_verify_urls(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Check HTTP liveness of all evidence URLs (HEAD requests)."""
    results = []
    checked = 0
    live = 0
    dead = 0
    errors = 0

    for record in records:
        evidence = record.get("evidence", {})
        for field in ("auth_url", "access_url", "api_url", "mcp_url"):
            url = evidence.get(field)
            if not url:
                continue
            checked += 1
            try:
                # Use curl for HEAD request
                result = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-I", "-L", "--max-time", "10", url],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                status = result.stdout.strip()
                if status.startswith("2") or status.startswith("3"):
                    live += 1
                    results.append({"id": record["id"], "field": field, "url": url, "status": status, "live": True})
                else:
                    dead += 1
                    results.append({"id": record["id"], "field": field, "url": url, "status": status, "live": False})
            except subprocess.TimeoutExpired:
                errors += 1
                results.append({"id": record["id"], "field": field, "url": url, "status": "timeout", "live": False})
            except Exception as e:
                errors += 1
                results.append({"id": record["id"], "field": field, "url": url, "status": f"error: {e}", "live": False})

    return {
        "checked": checked,
        "live": live,
        "dead": dead,
        "errors": errors,
        "results": results,
    }


def l2_consistency_check(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Placeholder for L2 consistency check - would re-extract with different prompt."""
    # This would require re-running extraction with different model/prompt
    # For now, return a stub
    return {
        "note": "L2 consistency check not yet implemented - would re-extract from cached HTML with different prompts/models",
        "flagged": [],
    }