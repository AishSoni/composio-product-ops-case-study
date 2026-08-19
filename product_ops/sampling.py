"""Stratified sampling for human verification."""

from __future__ import annotations

import json
import random
from pathlib import Path
from product_ops.analysis import summarize_records


def select_stratified_sample(records: list[dict[str, Any]], sample_size: int = 25) -> list[int]:
    """Select a stratified sample biased toward tricky categories."""
    # Categories ranked by difficulty (fintech, AI, data-heavy = harder)
    priority_categories = [
        "Finance and Fintech",
        "AI, Research and Media-native",
        "Data, SEO and Scraping",
        "Marketing, Ads, Email and Social",
        "Ecommerce",
        "Developer, Infra and Data platforms",
        "Support and Helpdesk",
        "Communications and Messaging",
        "CRM and Sales",
        "Productivity and Project Management",
    ]

    # Group by category
    by_category: dict[str, list[int]] = {}
    for rec in records:
        cat = rec["category"]
        by_category.setdefault(cat, []).append(rec["id"])

    # Allocate samples proportionally but with extra weight to priority categories
    sample_ids = []
    remaining = sample_size

    for cat in priority_categories:
        if cat not in by_category or remaining <= 0:
            continue
        # More samples from priority categories
        weight = 2 if cat in priority_categories[:4] else 1
        n = min(len(by_category[cat]), max(1, remaining * weight // 10))
        if n > len(by_category[cat]):
            n = len(by_category[cat])
        if n > remaining:
            n = remaining
        selected = random.sample(by_category[cat], n)
        sample_ids.extend(selected)
        remaining -= n

    # Fill remaining from any category
    all_remaining = [r["id"] for r in records if r["id"] not in sample_ids]
    if remaining > 0 and all_remaining:
        sample_ids.extend(random.sample(all_remaining, min(remaining, len(all_remaining))))

    return sorted(sample_ids)


def main() -> None:
    records = json.loads(Path("data/research_all_first_pass_fixed.json").read_text(encoding="utf-8"))
    random.seed(42)  # Reproducible
    sample_ids = select_stratified_sample(records, 25)

    print(f"Sample size: {len(sample_ids)}")
    print(f"Sample IDs: {sample_ids}")

    # Save sample for human review
    sample_records = [r for r in records if r["id"] in sample_ids]
    Path("data/verification_sample.json").write_text(
        json.dumps(sample_records, indent=2) + "\n", encoding="utf-8"
    )

    # Also save first-pass frozen snapshot for comparison
    first_pass = json.loads(Path("data/research_all_first_pass.json").read_text(encoding="utf-8"))
    first_pass_sample = [r for r in first_pass if r["id"] in sample_ids]
    Path("data/verification_first_pass_sample.json").write_text(
        json.dumps(first_pass_sample, indent=2) + "\n", encoding="utf-8"
    )

    print("Saved verification_sample.json and verification_first_pass_sample.json")


if __name__ == "__main__":
    main()