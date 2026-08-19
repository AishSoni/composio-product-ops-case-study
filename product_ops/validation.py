"""Evidence and schema guardrails for researched application records."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


ACCESS_STATUSES = {
    "free_self_serve",
    "trial_self_serve",
    "paid_self_serve",
    "admin_approval",
    "partner_or_sales_gated",
    "unclear",
}
BREADTHS = {"narrow", "moderate", "broad", "unclear"}
MCP_STATUSES = {"official", "community", "none_found", "unclear"}
VERDICTS = {"buildable_today", "partial", "blocked", "unclear"}
CONFIDENCES = {"high", "medium", "low"}
AUTH_METHODS = {"OAuth2", "API key", "Basic", "token", "other"}


def _is_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _issue(record: dict[str, Any], field: str, message: str) -> dict[str, Any]:
    return {"id": record.get("id"), "field": field, "message": message}


def validate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return deterministic issues; never repair or infer missing research facts."""
    issues: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, int):
            issues.append(_issue(record, "id", "must be an integer"))
        elif record_id in seen_ids:
            issues.append(_issue(record, "id", "must be unique"))
        else:
            seen_ids.add(record_id)

        for field in ("name", "category", "one_line", "research_notes"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                issues.append(_issue(record, field, "must be a non-empty string"))

        methods = record.get("auth_methods")
        if not isinstance(methods, list) or not methods or any(method not in AUTH_METHODS for method in methods):
            issues.append(_issue(record, "auth_methods", f"must be a non-empty subset of {sorted(AUTH_METHODS)}"))

        access = record.get("access")
        if not isinstance(access, dict) or access.get("status") not in ACCESS_STATUSES:
            issues.append(_issue(record, "access.status", "must use a supported access status"))
        if not isinstance(access, dict) or not isinstance(access.get("note"), str) or not access["note"].strip():
            issues.append(_issue(record, "access.note", "must be a non-empty evidence note"))

        api = record.get("api")
        if not isinstance(api, dict) or not isinstance(api.get("documented"), bool):
            issues.append(_issue(record, "api.documented", "must be boolean"))
        if not isinstance(api, dict) or api.get("breadth") not in BREADTHS:
            issues.append(_issue(record, "api.breadth", "must use a supported breadth"))
        if not isinstance(api, dict) or api.get("mcp") not in MCP_STATUSES:
            issues.append(_issue(record, "api.mcp", "must use a supported MCP status"))
        if not isinstance(api, dict) or not isinstance(api.get("protocols"), list):
            issues.append(_issue(record, "api.protocols", "must be a list"))
        if not isinstance(api, dict) or not isinstance(api.get("note"), str) or not api["note"].strip():
            issues.append(_issue(record, "api.note", "must be a non-empty evidence note"))

        buildability = record.get("buildability")
        verdict = buildability.get("verdict") if isinstance(buildability, dict) else None
        blocker = buildability.get("blocker") if isinstance(buildability, dict) else None
        if verdict not in VERDICTS:
            issues.append(_issue(record, "buildability.verdict", "must use a supported verdict"))
        if verdict != "buildable_today" and (not isinstance(blocker, str) or not blocker.strip()):
            issues.append(_issue(record, "buildability.blocker", "is required unless verdict is buildable_today"))
        if verdict == "buildable_today" and blocker not in {None, ""}:
            issues.append(_issue(record, "buildability.blocker", "must be null for buildable_today"))

        evidence = record.get("evidence")
        for field in ("auth_url", "access_url", "api_url"):
            if not isinstance(evidence, dict) or not _is_url(evidence.get(field)):
                issues.append(_issue(record, f"evidence.{field}", "must be an absolute http(s) URL"))
        if isinstance(api, dict) and api.get("mcp") in {"official", "community"}:
            if not isinstance(evidence, dict) or not _is_url(evidence.get("mcp_url")):
                issues.append(_issue(record, "evidence.mcp_url", "is required when an MCP is claimed"))

        if record.get("confidence") not in CONFIDENCES:
            issues.append(_issue(record, "confidence", "must use a supported confidence level"))

    return issues
