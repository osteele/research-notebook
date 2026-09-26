#!/usr/bin/env python3
"""Check the published notebook schema copy against the skill authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (
    ROOT
    / "skills"
    / "research-lab-notebook"
    / "references"
    / "notebook-schema.json"
)
SITE_SCHEMA = Path("src/data/research-lab-notebook-schema.json")
SITE_PAGES = (
    Path("src/pages/reference/index.astro"),
    Path("src/pages/reference/experiments/index.astro"),
    Path("src/pages/reference/plans/index.astro"),
    Path("src/pages/reference/spend/index.astro"),
    Path("src/pages/reference/review-ledger/index.astro"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, help="Root of the Research Notebook site repository")
    args = parser.parse_args()

    site_schema_path = args.site.resolve() / SITE_SCHEMA
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    published = json.loads(site_schema_path.read_text(encoding="utf-8"))
    if source != published:
        print(f"ERROR: {site_schema_path} differs from {SOURCE}")
        return 1

    rendered = ""
    for relative in SITE_PAGES:
        page = args.site.resolve() / relative
        if not page.is_file():
            print(f"ERROR: {page} is missing")
            return 1
        text = page.read_text(encoding="utf-8")
        if "import notebookSchema" not in text:
            print(f"ERROR: {page} does not import the schema")
            return 1
        rendered += text
    expected_fragments = (
        "notebookSchema.required_files",
        "notebookSchema.experiment_statuses",
        "notebookSchema.experiment_status_aliases",
        "notebookSchema.experiment_id.examples",
        "notebookSchema.experiment.estimand.registration_values",
        "notebookSchema.plan.required_frontmatter",
        "notebookSchema.plan.status_directories",
        "notebookSchema.plan.status_aliases",
        "notebookSchema.plan.completion_report.recognized_headings",
        "notebookSchema.plan.confirmation_reserve.required_markers",
        "notebookSchema.claim.columns",
        "notebookSchema.claim.roles",
        "notebookSchema.human_review.checkpoints",
        "notebookSchema.ledger.required_fields",
        "notebookSchema.spend.ledger_columns",
        "notebookSchema.spend.open_outcomes",
        "notebookSchema.spend.terminal_outcomes",
        "notebookSchema.review_ledger.register_columns",
        "notebookSchema.review_ledger.relations",
    )
    missing = [fragment for fragment in expected_fragments if fragment not in rendered]
    if missing:
        print(f"ERROR: the notebook pages do not render: {', '.join(missing)}")
        return 1
    print("Published notebook contract matches the skill schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
