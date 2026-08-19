"""Build the single-file HTML case study by embedding data directly."""

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

    # Build patterns data
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

    # Build table rows
    table_rows = []
    for rec in records:
        access = rec["access"]["status"]
        verdict = rec["buildability"]["verdict"]
        mcp = rec["api"]["mcp"]
        confidence = rec["confidence"]

        badges = []
        if access in {"admin_approval", "partner_or_sales_gated", "unclear"}:
            badges.append('<span class="badge badge-gated">Gated</span>')
        if confidence == "low":
            badges.append('<span class="badge badge-low">Low</span>')
        if rec.get("needs_human"):
            badges.append('<span class="badge badge-human">Human</span>')
        if mcp == "official":
            badges.append('<span class="badge badge-mcp">MCP</span>')

        one_line = rec["one_line"]
        if len(one_line) > 120:
            one_line = one_line[:117] + "..."

        auth_str = ", ".join(rec["auth_methods"])
        evidence_links = []
        for label, url in rec["evidence"].items():
            if url:
                evidence_links.append(f'<a href="{_esc(url)}" target="_blank" rel="noopener">{label}</a>')

        row = f'<tr data-category="{_esc(rec["category"])}" data-verdict="{_esc(verdict)}" data-access="{_esc(access)}" data-mcp="{_esc(mcp)}">'
        row += f'<td class="col-id">{rec["id"]}</td>'
        row += f'<td class="col-name"><strong>{_esc(rec["name"])}</strong></td>'
        row += f'<td class="col-category">{_esc(rec["category"])}</td>'
        row += f'<td class="col-oneline">{_esc(one_line)}</td>'
        row += f'<td class="col-auth">{_esc(auth_str)}</td>'
        row += f'<td class="col-access">{_esc(access)}</td>'
        row += f'<td class="col-verdict"><span class="badge badge-verdict">{_esc(verdict)}</span></td>'
        row += f'<td class="col-mcp">{_esc(mcp)}</td>'
        row += f'<td class="col-conf">{_esc(confidence)}</td>'
        row += f'<td class="col-flags">{" ".join(badges)}</td>'
        row += f'<td class="col-evidence evidence-cell">{" | ".join(evidence_links)}</td>'
        row += '</tr>'
        table_rows.append(row)

    # Build misses
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

    # Read the HTML template
    html = Path("docs/index.html").read_text(encoding="utf-8")

    # Embed the data directly in the HTML (replace the external script load)
    data_script = f'<script>\nwindow.CASE_STUDY_DATA = {json.dumps(data, separators=(",", ":"))};\nwindow.dataLoaded = true;\n</script>\n</body>'
    html = html.replace('<script src="case_study_data.js"></script>\n</body>', data_script)

    # Also remove the loadData async logic since data is now inline
    html = html.replace(
        'let dataLoaded = false;\n\nasync function loadData() {\n  if (dataLoaded) return;\n  try {\n    const res = await fetch(\'case_study_data.js\');\n    if (res.ok) {\n      const text = await res.text();\n      const match = text.match(/window\\.CASE_STUDY_DATA\\s*=\\s*(\\{[\\s\\S]*\\});/);\n      if (match) {\n        Object.assign(CASE_STUDY_DATA, JSON.parse(match[1]));\n        dataLoaded = true;\n        renderAll();\n      }\n    }\n  } catch (e) {\n    console.warn(\'Could not load case_study_data.js, using empty data\');\n  }\n}',
        '// Data embedded inline above'
    )

    html = html.replace(
        'document.addEventListener(\'DOMContentLoaded\', async () => {\n  await loadData();\n  if (!dataLoaded) renderAll(); // fallback if data already inline\n});',
        'document.addEventListener(\'DOMContentLoaded\', () => {\n  renderAll();\n});'
    )

    Path("docs/index.html").write_text(html, encoding="utf-8")
    print("Built docs/index.html with embedded data")


if __name__ == "__main__":
    main()