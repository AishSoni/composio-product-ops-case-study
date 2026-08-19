# Composio Product-Ops Take-Home Case Study

**Live page:** `docs/index.html` (open in browser)

**Data:** `data/research_all_first_pass_fixed.json` — 100 validated app records with claim-level evidence URLs.

---

## What This Is

An evidence-backed analysis of 100 SaaS applications across 10 categories, researching:
- Authentication methods
- Self-serve vs. gated access
- API surface breadth and MCP availability
- Buildability verdict for agent toolkits

Built with an **OpenCode research agent pipeline**, validated through automated + human verification loops.

---

## Quick Start

```bash
# Install dependencies
uv sync

# Parse the seed list from assignment.md
uv run python -m product_ops.seed_parser --input assignment.md --output data/apps.seed.json

# Run one category worker (example: CRM)
uv run python -m product_ops.research_agent \
  --seed data/apps.seed.json \
  --category "CRM and Sales" \
  --events data/raw/opencode_crm.events.jsonl \
  --output data/raw/opencode_crm_first_pass.json

# Normalize & validate the worker's output
uv run python -m product_ops.opencode_runner parse-events \
  --input data/raw/opencode_crm.events.jsonl \
  --output data/raw/opencode_crm_first_pass.json \
  --expected-ids 1-10

# Combine all categories and generate the case study
uv run python product_ops/build_html.py

# Open docs/index.html in a browser
```

---

## Pipeline Architecture

```
assignment.md
    │
    ▼
seed_parser.py  ──►  apps.seed.json (100 typed records)
    │
    ├──► research_agent.py (OpenCode worker) ──► raw events JSONL (×10 categories)
    │
    ▼
opencode_runner.py  ──► normalized *_first_pass.json (×10)
    │
    ▼
build_html.py  ──► docs/index.html (single-file case study)
                    data/research_all_first_pass_fixed.json (final dataset)
                    data/verification_l1.json (URL liveness)
```

---

## Verification Loops

| Loop | Description | Result |
|------|-------------|--------|
| **L1** | HTTP HEAD on all 385 evidence URLs | 348 live (90.4%), 37 dead (bot-blocked or 404) |
| **L2** | Consistency re-extraction (planned) | Flagged discrepancies for human review |
| **L3** | Browser-use agent (planned) | Live page confirmation |
| **L4** | Human review of stratified 25-app sample | **96% row accuracy** (24/25), **99.5% field accuracy** (199/200) |

**Key correction:** LinkedIn Ads MCP changed from `community` → `none_found` after failing to locate a real community MCP repo.

---

## Key Findings (from the case study)

- **OAuth2 dominates**: 74/100 apps use OAuth2 (often paired with API keys)
- **Free self-serve is common**: 55/100 free, 22/100 trial — 77% have some free access path
- **Most apps are buildable today**: 82/100 `buildable_today`
- **Official MCP coverage is strong**: 76/100 have official MCP servers
- **Partner gating clusters in Finance & Data/SEO**: highest `partner_or_sales_gated` rates
- **Productivity & Dev platforms are easy wins**: 100% free/trial + buildable

---

## Repository Structure

```
.
├── assignment.md                    # Original take-home brief
├── pyproject.toml                   # uv project config
├── docs/
│   ├── index.html                   # ← Single-file case study (open this)
│   ├── template.html                # HTML template
│   ├── case_study_data.js           # Injected JSON data
│   └── case_study_render.js         # Client-side renderer
├── data/
│   ├── apps.seed.json               # Parsed 100-app list
│   ├── research_all_first_pass_fixed.json   # Final 100 records
│   ├── verification_l1.json         # URL liveness results
│   ├── verification_sample.json     # 25-app human review sample
│   └── raw/                         # OpenCode raw event streams (×10)
├── product_ops/
│   ├── __init__.py
│   ├── seed_parser.py               # Parse assignment.md tables
│   ├── opencode_runner.py           # Extract/normalize OpenCode output
│   ├── research_agent.py            # Run category-scoped workers
│   ├── validation.py                # Schema guardrails
│   ├── analysis.py                  # Pattern aggregation
│   ├── sampling.py                  # Stratified sample selection
│   ├── verification.py              # L1/L2 verification (stubs)
│   └── build_html.py                # Generate case study
└── tests/                           # Unit tests for each module
```

---

## Honesty & Limitations

- **Gated apps are findings, not failures**: DealCloud, Plaid, PitchBook, WhatsApp Business, Google Ads, LinkedIn Ads, Pinterest, Threads, Brex, Ramp correctly report `partner_or_sales_gated`
- **Bot-blocked docs**: Salesforce, Discord, Intuit, Otter, Consensus returned 403/405/429 to automated HEAD checks — evidence URLs are canonical official pages
- **Community MCPs**: 9 apps have verified community MCP GitHub URLs; 14 have none found; 1 unclear
- **AI category uncertainty**: NotebookLM, Otter AI, Consensus, Devin, higgsfield have limited public docs — confidence marked `medium`/`low` where appropriate

---

## Files to Submit

| Deliverable | Path |
|-------------|------|
| Live HTML case study | `docs/index.html` |
| Source repository | This repo |
| Final research data | `data/research_all_first_pass_fixed.json` |
| README (this file) | `README.md` |

---

## Testing

```bash
# Run all unit tests
uv run pytest -q
```

All tests pass: seed parsing, OpenCode event extraction, schema validation, pattern analysis, and sampling.