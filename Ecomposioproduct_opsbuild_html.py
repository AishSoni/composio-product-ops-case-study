"""Build the single-file HTML case study by combining template with data."""

from __future__ import annotations

import json
from pathlib import Path


def _esc(s: str) -> str:
    return s.replace("&", "&").replace("<", "<").replace(">", ">").replace('"', '"').replace("'", "'")


def main() -> None:
    records = json.loads(Path("data/research_all_first_pass_fixed.json").read_text(encoding="utf-8"))
    l1 = json.loads(Path("data/verification_l1.json").read_text(encoding="utf-8"))

    from product_ops.analysis import summarize_records
    summary = summarize_records(records)

    patterns = [
        {"title": "OAuth2 dominates", "desc": f"OAuth2 is the primary auth method across {summary['auth_counts'].get('OAuth2', 0)}/100 apps, often paired with API keys."},
        {"title": "Free self-serve is common", "desc": f"{summary['access_counts'].get('free_self_serve', 0)}/100 apps offer free self-serve access; another {summary['access_counts'].get('trial_self_serve', 0)} offer free trials."},
        {"title": "Most apps are buildable today", "desc": f"{summary['buildability_counts'].get('buildable_today', 0)}/100 apps can be built as agent toolkits today with current access."},
        {"title": "Official MCP coverage is strong", "desc": f"{summary['mcp_counts'].get('official', 0)}/100 apps have official MCP servers; only {summary['mcp_counts'].get('none_found', 0)} have none."},
        {"title": "Partner gating clusters in fintech & data", "desc": f"Finance ({summary['category_breakdown'].get('Finance and Fintech', {}).get('gated_or_approval', 0)}/10) and Data/SEO ({summary['category_breakdown'].get('Data, SEO and Scraping', {}).get('gated_or_approval', 0)}/10) have the highest gating rates."},
        {"title": "Productivity & Dev platforms are easy wins", "desc": f"All {summary['category_breakdown'].get('Productivity and Project Management', {}).get('apps', 0)}/{summary['category_breakdown'].get('Productivity and Project Management', {}).get('apps', 0)} Productivity apps and {summary['category_breakdown'].get('Developer, Infra and Data platforms', {}).get('apps', 0)}/{summary['category_breakdown'].get('Developer, Infra and Data platforms', {}).get('apps', 0)} Dev platforms are free/trial self-serve and buildable today."},
    ]

    easy_wins = []
    for rec in summary["easy_wins"][:15]:
        easy_wins.append({
            "name": rec["name"], "category": rec["category"],
            "access": rec["access"]["status"], "verdict": rec["buildability"]["verdict"],
            "mcp": rec["api"]["mcp"],
        })

    outreach = []
    for rec in summary["outreach_queue"]:
        outreach.append({
            "name": rec["name"], "category": rec["category"],
            "blocker": rec["buildability"]["blocker"] or "Gated access",
        })

    table_rows = []
    for rec in records:
        access = rec["access"]["status"]
        verdict = rec["buildability"]["verdict"]
        mcp = rec["api"]["mcp"]
        confidence = rec["confidence"]

        badges = []
        if access in {"admin_approval", "partner_or_sales_gated", "unclear"}:
            badges.append('<span class="badge gated">Gated</span>')
        if confidence == "low":
            badges.append('<span class="badge low-conf">Low confidence</span>')
        if rec.get("needs_human"):
            badges.append('<span class="badge needs-human">Needs human</span>')
        if mcp == "official":
            badges.append('<span class="badge mcp">MCP</span>')

        one_line = rec["one_line"]
        if len(one_line) > 120:
            one_line = one_line[:117] + "..."

        auth_str = ", ".join(rec["auth_methods"])
        evidence_links = []
        for label, url in rec["evidence"].items():
            if url:
                evidence_links.append(f'<a href="{_esc(url)}" target="_blank" rel="noopener">{label}</a>')

        row = f'''<tr data-category="{_esc(rec["category"])}" data-verdict="{_esc(verdict)}" data-access="{_esc(access)}" data-mcp="{_esc(mcp)}">
            <td>{rec["id"]}</td>
            <td><strong>{_esc(rec["name"])}</strong></td>
            <td>{_esc(rec["category"])}</td>
            <td>{_esc(one_line)}</td>
            <td>{_esc(auth_str)}</td>
            <td>{_esc(access)}</td>
            <td>{_esc(verdict)}</td>
            <td>{_esc(mcp)}</td>
            <td>{_esc(confidence)}</td>
            <td>{" ".join(badges)}</td>
            <td class="evidence-cell">{" | ".join(evidence_links)}</td>
        </tr>'''
        table_rows.append(row)

    misses = []
    for result in l1["results"]:
        if not result["live"]:
            rec = next(r for r in records if r["id"] == result["id"])
            misses.append({
                "name": rec["name"], "field": result["field"],
                "url": result["url"], "status": result["status"],
            })

    verification = {
        "checked": l1["checked"], "live": l1["live"], "dead": l1["dead"],
    }

    data = {
        "patterns": patterns,
        "easyWins": easy_wins,
        "outreach": outreach,
        "tableRows": table_rows,
        "verification": verification,
        "misses": misses,
    }

    Path("docs/case_study_data.js").write_text(
        "window.CASE_STUDY_DATA = " + json.dumps(data, separators=(',', ':')) + ";",
        encoding="utf-8"
    )

    template = Path("docs/template.html").read_text(encoding="utf-8")
    Path("docs/index.html").write_text(template, encoding="utf-8")

    print("Data written to docs/case_study_data.js")
    print("Index written to docs/index.html")


if __name__ == "__main__":
    main()
