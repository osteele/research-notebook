from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = (
    ROOT
    / "skills"
    / "research-lab-notebook"
    / "scripts"
    / "validate-notebook.py"
)
SPEC = importlib.util.spec_from_file_location("validate_notebook", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


COMPLETED_EXPERIMENT = """# EXP-001: Synthetic check

**Status**: completed

## Hypothesis

The synthetic condition changes the primary metric.

## Method

Run two deterministic conditions.

## Preregistered predictions (a priori)

- **P1**: The metric increases.

## Decision rule (a priori)

- **If P1 holds**: Record the scoped result.

## Runs

| Backend | Job ID |
|---|---|
| local | job-1 |

## Results

The metric increased.

### Outcomes against preregistered predictions

| Prediction | Verdict |
|---|---|
| P1 | confirmed |

## Conclusion

The result supports the synthetic claim.

## Artifacts

- `results/metrics.json`
"""

FINDING = """# Finding: Synthetic result holds twice

**Date**: 2026-08-11
**Status**: supported
**Experiments**: [[EXP-001]], [[EXP-002]]

## Claim

The result holds in both synthetic experiments.

## Evidence

- [[EXP-001]] supports the claim.
- [[EXP-002]] supports the claim.

## Synthesis

The two conditions agree.

## Scope and threats to validity

This is synthetic evidence only.

## Consequences

Use the example to test validation.

## Sources

- `experiments/EXP-001-synthetic-check.md`
"""

PLAN = """---
status: active
summary: Decide whether the synthetic result survives a control
next_action: Run Phase 1
current_phase: Phase 1
created: 2026-08-11
updated: 2026-08-11
---

# Synthetic control campaign

## Objective

Decide whether the result survives a control.

## Existing evidence

- [[EXP-001]]

## Phases

### Phase 1

Run the bounded control.

## Risks and controls

Use synthetic data only.

## Terminal conditions

- Complete when the control is recorded.
"""


class NotebookFixture:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        for relative in validator.REQUIRED_FILES:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Index\n", encoding="utf-8")
        (root / "CLAIMS.md").write_text(
            "# Publication claims\n\n"
            "| ID | Role | Claim | Status | Evidence | Paper |\n"
            "|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )

    def add_experiment(self, name: str = "EXP-001-synthetic-check.md") -> pathlib.Path:
        path = self.root / "experiments" / name
        path.write_text(COMPLETED_EXPERIMENT, encoding="utf-8")
        (self.root / "experiments" / "README.md").write_text(
            f"# Experiments\n\n- [{path.stem}]({path.name})\n", encoding="utf-8"
        )
        return path

    def add_spend_dir(self) -> pathlib.Path:
        spend = self.root / "plans" / "spend"
        spend.mkdir(parents=True)
        return spend

    def write_spend_authority(self, plans: dict) -> None:
        (self.root / "plans" / "spend" / "AUTHORITY.json").write_text(
            json.dumps({"schema": validator.SPEND_AUTHORITY_SCHEMA, "plans": plans}),
            encoding="utf-8",
        )

    def write_spend_ledger(self, *rows: str) -> None:
        header = "| " + " | ".join(validator.SPEND_LEDGER_COLUMNS) + " |\n"
        separator = "|" + "---|" * len(validator.SPEND_LEDGER_COLUMNS) + "\n"
        (self.root / "plans" / "spend" / "LEDGER.md").write_text(
            header + separator + "".join(rows), encoding="utf-8"
        )


class NotebookValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name) / "lab-notebook"
        self.fixture = NotebookFixture(self.root)

    def messages(self) -> list[str]:
        return [issue.message for issue in validator.validate(self.root)[1]]

    def test_minimum_notebook_is_valid(self) -> None:
        self.assertEqual(self.messages(), [])

    def test_missing_claim_ledger_is_invalid(self) -> None:
        (self.root / "CLAIMS.md").unlink()
        _, issues = validator.validate(self.root)
        self.assertTrue(
            any(issue.level == "ERROR" and issue.path.name == "CLAIMS.md" for issue in issues)
        )

    def test_completed_experiment_requires_outcome_table(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT.replace(
                "### Outcomes against preregistered predictions",
                "### Prediction notes",
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any("Outcomes against" in message for message in self.messages())
        )

    def test_experiment_must_be_in_index(self) -> None:
        self.fixture.add_experiment()
        (self.root / "experiments" / "README.md").write_text(
            "# Experiments\n", encoding="utf-8"
        )
        self.assertIn("not listed in README.md", self.messages())

    def test_blocked_status_is_canonical(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT.replace("**Status**: completed", "**Status**: blocked"),
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_status_qualifier_in_parentheses_is_allowed(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT.replace(
                "**Status**: completed", "**Status**: completed (2026-08-11)"
            ),
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_legacy_status_spelling_warns(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT.replace("**Status**: completed", "**Status**: done"),
            encoding="utf-8",
        )
        root, issues = validator.validate(self.root)
        self.assertEqual(
            [(issue.level, issue.message) for issue in issues],
            [("WARNING", "legacy status spelling 'done'; write 'completed'")],
        )

    def test_closed_status_is_rejected(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT.replace("**Status**: completed", "**Status**: closed"),
            encoding="utf-8",
        )
        self.assertTrue(
            any("status 'closed' is not accepted" in message for message in self.messages())
        )

    def test_estimand_requires_recognized_registration(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT
            + "\n## Estimands\n\n### E1 Metric change\n\nProse only.\n\n### E2 Headroom\n\n**Registration**: planned\n",
            encoding="utf-8",
        )
        messages = self.messages()
        self.assertIn("estimand E1 has no **Registration**: line", messages)
        self.assertTrue(
            any("estimand E2 registration 'planned'" in message for message in messages)
        )

    def test_registered_estimands_are_valid(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT
            + "\n## Estimands\n\n### E1 Metric change\n\n**Registration**: registered\n\n### E2 Headroom\n\n**Registration**: gate\n",
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_informed_by_links_must_resolve(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT
            + "\n## Informed by\n\n- [[EXP-000-missing]]\n- [[RQ1]]\n- [[EXP-001-synthetic-check]]\n",
            encoding="utf-8",
        )
        self.assertEqual(
            self.messages(),
            ["Informed by link [[EXP-000-missing]] does not resolve to a notebook file"],
        )

    def test_decisions_entries_are_dated_ordered_and_linked(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT
            + "\n## Decisions\n\n"
            + "- **2026-09-02** — Rotated order rather than cyclic, after\n"
            + "  [[EXP-001-synthetic-check]] showed carryover. Source: review.\n"
            + "- **2026-09-01** — Comparator pinned rather than tuned.\n"
            + "- Undated choice of [[EXP-000-missing]].\n",
            encoding="utf-8",
        )
        self.assertEqual(
            sorted(self.messages()),
            sorted(
                [
                    "Decisions link [[EXP-000-missing]] does not resolve to a notebook file",
                    "Decisions entries run newest last; 2026-09-01 follows 2026-09-02",
                    "Decisions entry lacks a leading **YYYY-MM-DD** date",
                ]
            ),
        )

    def test_revision_letter_suffix_is_a_valid_id(self) -> None:
        experiment = self.fixture.add_experiment("EXP-001b-synthetic-check.md")
        experiment.write_text(
            COMPLETED_EXPERIMENT.replace("# EXP-001:", "# EXP-001b:"),
            encoding="utf-8",
        )
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | major | Synthetic result | supported | [[EXP-001b]] | synthetic-paper |
""",
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_hyphenated_preregistered_headings_are_accepted(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT.replace(
                "## Preregistered predictions (a priori)",
                "## Pre-registered predictions (a priori)",
            ).replace(
                "### Outcomes against preregistered predictions",
                "### Outcomes against pre-registered predictions",
            ),
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_annex_is_not_an_experiment(self) -> None:
        self.fixture.add_experiment()
        annex = self.root / "experiments" / "EXP-001-synthetic-check.annex.md"
        annex.write_text("# Residuals\n\n| row | value |\n|---|---|\n", encoding="utf-8")
        self.assertEqual(self.messages(), [])
        orphan = self.root / "experiments" / "EXP-009-orphan.annex.md"
        orphan.write_text("# Rows\n", encoding="utf-8")
        self.assertIn(
            "annex filename must start with the ID of an existing experiment",
            self.messages(),
        )

    def test_finding_contract_and_index(self) -> None:
        path = self.root / "findings" / "2026-08-11-synthetic-result.md"
        path.write_text(FINDING, encoding="utf-8")
        (self.root / "findings" / "README.md").write_text(
            f"# Findings\n\n- [{path.stem}]({path.name})\n", encoding="utf-8"
        )
        self.assertEqual(self.messages(), [])

    def test_finding_date_must_match_filename(self) -> None:
        path = self.root / "findings" / "2026-08-10-synthetic-result.md"
        path.write_text(FINDING, encoding="utf-8")
        (self.root / "findings" / "README.md").write_text(
            path.name, encoding="utf-8"
        )
        self.assertIn("Date field does not match filename", self.messages())

    def test_claim_requires_direct_experiment_evidence(self) -> None:
        self.fixture.add_experiment()
        finding = self.root / "findings" / "2026-08-11-synthetic-result.md"
        finding.write_text(FINDING, encoding="utf-8")
        (self.root / "findings" / "README.md").write_text(
            finding.name, encoding="utf-8"
        )
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | major | Synthetic result | supported | findings/2026-08-11-synthetic-result.md | synthetic-paper |
""",
            encoding="utf-8",
        )
        self.assertTrue(
            any("findings cannot replace it" in message for message in self.messages())
        )

    def test_claim_may_add_finding_context_to_experiment_evidence(self) -> None:
        self.fixture.add_experiment()
        finding = self.root / "findings" / "2026-08-11-synthetic-result.md"
        finding.write_text(FINDING, encoding="utf-8")
        (self.root / "findings" / "README.md").write_text(
            finding.name, encoding="utf-8"
        )
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | major | Synthetic result | supported | [[EXP-001]]; synthesis: findings/2026-08-11-synthetic-result.md | synthetic-paper |
""",
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_claim_accepts_project_specific_experiment_id(self) -> None:
        experiment = self.fixture.add_experiment("ACC-E1-synthetic-check.md")
        experiment.write_text(
            COMPLETED_EXPERIMENT.replace("# EXP-001:", "# ACC-E1:"),
            encoding="utf-8",
        )
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | major | Synthetic result | supported | [[ACC-E1]] | synthetic-paper |
""",
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_claim_estimand_reference_must_resolve(self) -> None:
        self.fixture.add_experiment()
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | major | Synthetic result | supported | EXP-001:E1 | synthetic-paper |
""",
            encoding="utf-8",
        )
        self.assertTrue(
            any("EXP-001:E1 does not resolve" in message for message in self.messages())
        )

    def test_claim_citing_found_estimand_warns(self) -> None:
        path = self.fixture.add_experiment()
        path.write_text(
            COMPLETED_EXPERIMENT
            + "\n## Estimands\n\n### E1 Metric change\n\n**Registration**: registered\n\n### E2 Side pattern\n\n**Registration**: found\n",
            encoding="utf-8",
        )
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | major | Synthetic result | supported | EXP-001:E1 | synthetic-paper |
| C2 | supporting | Side pattern | provisional | EXP-001:E2 | synthetic-paper |
""",
            encoding="utf-8",
        )
        root, issues = validator.validate(self.root)
        self.assertEqual([issue.level for issue in issues], ["WARNING"])
        self.assertIn("EXP-001:E2 is a found estimand", issues[0].message)

    def test_legacy_claim_status_spelling_warns(self) -> None:
        self.fixture.add_experiment()
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | major | Synthetic result | live | [[EXP-001]] | synthetic-paper |
""",
            encoding="utf-8",
        )
        root, issues = validator.validate(self.root)
        self.assertEqual(
            [(issue.level, issue.message) for issue in issues],
            [("WARNING", "line 5: legacy claim status spelling 'live'; write 'supported'")],
        )

    def test_claim_requires_valid_role_and_paper_key(self) -> None:
        self.fixture.add_experiment()
        (self.root / "CLAIMS.md").write_text(
            """# Claims

| ID | Role | Claim | Status | Evidence | Paper |
|---|---|---|---|---|---|
| C1 | headline | Synthetic result | supported | [[EXP-001]] | |
""",
            encoding="utf-8",
        )
        messages = self.messages()
        self.assertTrue(
            any("invalid claim role 'headline'" in message for message in messages)
        )
        self.assertTrue(any("paper key is empty" in message for message in messages))

    def test_ledger_record_validates_evidence_and_identity(self) -> None:
        experiment = self.fixture.add_experiment()
        ledger = self.root / "jobs" / "processed" / "slurm" / "job-1.json"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "backend": "slurm",
                    "job_id": "job-1",
                    "experiment_id": "EXP-001",
                    "terminal_status": "succeeded",
                    "processed_at": "2026-08-11T14:25:00Z",
                    "evidence": [str(experiment.relative_to(self.root))],
                    "notebook_revision": "abc123",
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_ledger_rejects_escaping_evidence(self) -> None:
        ledger = self.root / "jobs" / "processed" / "Slurm" / "wrong.json"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "backend": "Slurm",
                    "job_id": "../job",
                    "experiment_id": "",
                    "terminal_status": "done",
                    "processed_at": "2026-08-11",
                    "evidence": ["../outside.md"],
                    "notebook_revision": "",
                }
            ),
            encoding="utf-8",
        )
        messages = self.messages()
        self.assertIn("invalid normalized backend 'Slurm'", messages)
        self.assertIn("unsupported schema_version", messages)
        self.assertTrue(any("stay inside notebook" in message for message in messages))

    def test_active_plan_contract(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        (plans / "2026-08-11-synthetic-control.md").write_text(
            PLAN, encoding="utf-8"
        )
        self.assertEqual(self.messages(), [])

    def test_plan_decisions_are_validated(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        (plans / "2026-08-11-synthetic-control.md").write_text(
            PLAN + "\n## Decisions\n\n- Ran phase 2 before phase 1.\n", encoding="utf-8"
        )
        self.assertEqual(
            self.messages(), ["Decisions entry lacks a leading **YYYY-MM-DD** date"]
        )

    def test_plan_created_date_must_match_filename(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        (plans / "2026-08-10-synthetic-control.md").write_text(
            PLAN, encoding="utf-8"
        )
        self.assertIn("created date does not match filename", self.messages())

    def test_terminal_plan_requires_closure_and_no_next_action(self) -> None:
        plans = self.root / "plans" / "completed"
        plans.mkdir(parents=True)
        (plans / "2026-08-11-synthetic-control.md").write_text(
            PLAN.replace("status: active", "status: completed"),
            encoding="utf-8",
        )
        messages = self.messages()
        self.assertIn("terminal plan next_action must be empty or none", messages)
        self.assertIn("completed plan lacks ## Completion report", messages)
        self.assertIn("terminal plan lacks ## Evidence", messages)

    def test_abandoned_plan_requires_disposition(self) -> None:
        plans = self.root / "plans" / "abandoned"
        plans.mkdir(parents=True)
        abandoned = PLAN.replace("status: active", "status: abandoned").replace(
            "next_action: Run Phase 1", "next_action: none"
        ).replace("current_phase: Phase 1", "abandoned_because: The premise changed")
        (plans / "2026-08-11-synthetic-control.md").write_text(
            abandoned, encoding="utf-8"
        )
        messages = self.messages()
        self.assertIn("terminal plan lacks ## Disposition", messages)
        self.assertIn("terminal plan lacks ## Evidence", messages)
        self.assertNotIn("completed plan lacks ## Completion report", messages)

    def test_completed_plan_with_completion_report_is_valid(self) -> None:
        plans = self.root / "plans" / "completed"
        plans.mkdir(parents=True)
        terminal = PLAN.replace("status: active", "status: completed").replace(
            "next_action: Run Phase 1", "next_action: none"
        )
        terminal += "\n## Completion report\n\nThe control passed.\n\n## Evidence\n\n- [[EXP-001]]\n"
        (plans / "2026-08-11-synthetic-control.md").write_text(
            terminal, encoding="utf-8"
        )
        self.assertEqual(self.messages(), [])

    def test_completed_plan_accepts_recognized_outcome_heading(self) -> None:
        plans = self.root / "plans" / "completed"
        plans.mkdir(parents=True)
        terminal = PLAN.replace("status: active", "status: completed").replace(
            "next_action: Run Phase 1", "next_action: none"
        )
        terminal += "\n## Execution result\n\nThe control passed.\n\n## Evidence\n\n- [[EXP-001]]\n"
        (plans / "2026-08-11-synthetic-control.md").write_text(
            terminal, encoding="utf-8"
        )
        self.assertEqual(self.messages(), [])

    def test_confirmation_reserve_requires_both_markers(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        reserved = PLAN + "\n## Confirmation reserve\n\n**Held back:** seeds 7 and 11\n"
        (plans / "2026-08-11-synthetic-control.md").write_text(
            reserved, encoding="utf-8"
        )
        self.assertIn(
            "Confirmation reserve section lacks **Decision rule:**", self.messages()
        )
        (plans / "2026-08-11-synthetic-control.md").write_text(
            reserved + "\n**Decision rule:** accept if the reserve beats baseline by 2pp\n",
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])

    def test_plan_status_directory_and_gate_metadata(self) -> None:
        plans = self.root / "plans" / "gated"
        plans.mkdir(parents=True)
        gated = PLAN.replace("status: active", "status: gated").replace(
            "current_phase: Phase 1",
            "current_phase: Phase 1\ngate: Human review of pilot evidence\nrevisit_when: Reviewer approves Phase 2",
        )
        (plans / "2026-08-11-synthetic-control.md").write_text(
            gated, encoding="utf-8"
        )
        self.assertEqual(self.messages(), [])

        path = plans / "2026-08-11-synthetic-control.md"
        path.write_text(
            gated.replace("gate: Human review of pilot evidence\n", "").replace(
                "revisit_when: Reviewer approves Phase 2\n", ""
            ),
            encoding="utf-8",
        )
        messages = self.messages()
        self.assertIn("gated plan requires gate", messages)
        self.assertIn(
            "gated plan requires one of: revisit_when, promote_when", messages
        )

    def test_legacy_plan_status_spelling_warns_and_accepts_its_directory(self) -> None:
        plans = self.root / "plans" / "complete"
        plans.mkdir(parents=True)
        terminal = PLAN.replace("status: active", "status: complete").replace(
            "next_action: Run Phase 1", "next_action: none"
        )
        terminal += "\n## Outcome\n\nThe control passed.\n\n## Evidence\n\n- [[EXP-001]]\n"
        (plans / "2026-08-11-synthetic-control.md").write_text(terminal, encoding="utf-8")
        root, issues = validator.validate(self.root)
        self.assertEqual(
            [(issue.level, issue.message) for issue in issues],
            [("WARNING", "legacy plan status spelling 'complete'; write 'completed'")],
        )

    def test_plan_status_must_match_directory(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        (plans / "2026-08-11-synthetic-control.md").write_text(
            PLAN.replace("status: active", "status: draft"), encoding="utf-8"
        )
        self.assertIn("status 'draft' belongs in draft/", self.messages())

    def test_plan_link_must_resolve(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        linked = PLAN.replace(
            "- [[EXP-001]]", "- [missing experiment](experiments/EXP-999.md)"
        )
        (plans / "2026-08-11-synthetic-control.md").write_text(
            linked, encoding="utf-8"
        )
        self.assertIn(
            "broken plan link experiments/EXP-999.md", self.messages()
        )

    def test_json_diagnostics_are_stable(self) -> None:
        root, issues = validator.validate(self.root)
        report = validator.diagnostics_report(root, issues, strict=False)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(
            report["notebook_schema_version"], validator.SCHEMA["schema_version"]
        )
        self.assertTrue(report["valid"])
        self.assertEqual(report["counts"], {"errors": 0, "warnings": 0})

    def test_plan_index_is_deterministic(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        (plans / "2026-08-11-synthetic-control.md").write_text(
            PLAN, encoding="utf-8"
        )
        first = validator.render_plan_index(self.root)
        second = validator.render_plan_index(self.root)
        self.assertEqual(first, second)
        self.assertIn("## Active", first)
        self.assertIn("[Synthetic control campaign]", first)

    def test_spend_ledger_is_not_reported_as_a_plan(self) -> None:
        plans = self.root / "plans"
        (plans / "spend").mkdir(parents=True)
        (plans / "2026-08-11-synthetic-control.md").write_text(PLAN, encoding="utf-8")
        self.fixture.write_spend_authority(
            {
                "2026-08-11-synthetic-control": {
                    "shared_ceiling_usd": 21.0,
                    "authorized_by": "A. Researcher",
                    "recorded_utc": "2026-09-09T00:00:00+00:00",
                }
            }
        )
        self.fixture.write_spend_ledger(
            "| S001 | 2026-09-10 | 2026-08-11-synthetic-control | EXP-001 | pilot-r1"
            " | demo:JOB-1 | pilot | 3.00 | 2.00 | complete |\n"
        )
        self.assertEqual(self.messages(), [])

    def test_spend_authority_entry_for_status_subdirectory_plan_is_clean(self) -> None:
        plans = self.root / "plans" / "completed"
        plans.mkdir(parents=True)
        terminal = PLAN.replace("status: active", "status: completed").replace(
            "next_action: Run Phase 1", "next_action: none"
        )
        terminal += (
            "\n## Completion report\n\nThe control passed.\n\n## Evidence\n\n- [[EXP-001]]\n"
        )
        (plans / "2026-08-11-synthetic-control.md").write_text(terminal, encoding="utf-8")
        self.fixture.add_spend_dir()
        self.fixture.write_spend_authority(
            {
                "2026-08-11-synthetic-control": {
                    "shared_ceiling_usd": 8.0,
                    "authorized_by": "A. Researcher",
                    "recorded_utc": "2026-09-09T00:00:00+00:00",
                }
            }
        )
        self.fixture.write_spend_ledger(
            "| S001 | 2026-09-10 | 2026-08-11-synthetic-control | EXP-001 | pilot-r1"
            " | demo:JOB-1 | pilot | 3.00 | 2.00 | complete |\n"
        )
        self.assertEqual(self.messages(), [])

    def test_spend_authority_entry_must_name_a_plan(self) -> None:
        self.fixture.add_spend_dir()
        self.fixture.write_spend_authority(
            {
                "2026-01-01-vanished-plan": {
                    "shared_ceiling_usd": 5.0,
                    "authorized_by": "A. Researcher",
                    "recorded_utc": "2026-09-09T00:00:00+00:00",
                }
            }
        )
        self.fixture.write_spend_ledger(
            "| S001 | 2026-09-10 | - | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00 | complete |\n"
        )
        self.assertIn(
            "plans entry '2026-01-01-vanished-plan' names no plan", self.messages()
        )

    def test_spend_ceiling_must_be_positive(self) -> None:
        plans = self.root / "plans"
        plans.mkdir()
        (plans / "2026-08-11-synthetic-control.md").write_text(PLAN, encoding="utf-8")
        self.fixture.add_spend_dir()
        self.fixture.write_spend_ledger(
            "| S001 | 2026-09-10 | - | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00 | complete |\n"
        )
        for ceiling in (0, -5.0):
            with self.subTest(ceiling=ceiling):
                self.fixture.write_spend_authority(
                    {
                        "2026-08-11-synthetic-control": {
                            "shared_ceiling_usd": ceiling,
                            "authorized_by": "A. Researcher",
                            "recorded_utc": "2026-09-09T00:00:00+00:00",
                        }
                    }
                )
                self.assertIn(
                    "plans entry '2026-08-11-synthetic-control' shared_ceiling_usd"
                    " must be a positive number",
                    self.messages(),
                )

    def test_spend_ledger_row_contract(self) -> None:
        self.fixture.add_spend_dir()
        self.fixture.write_spend_authority({})
        good_row = (
            "| S001 | 2026-09-10 | - | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00"
            " | complete/provisional |\n"
        )
        self.fixture.write_spend_ledger(good_row)
        self.assertEqual(self.messages(), [])

        self.fixture.write_spend_ledger(
            "| S001 | 2026-09-10 | - | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00 |\n"
        )
        self.assertIn(
            "line 3: spend ledger row has 9 cells (expected 10)", self.messages()
        )

        self.fixture.write_spend_ledger(
            "| S001 | 2026-09-10 | - | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00 | paused |\n"
        )
        self.assertIn("line 3: invalid spend outcome 'paused'", self.messages())

        self.fixture.write_spend_ledger(
            "| S001 | 2026-09-10 | 2026-08-11-missing-plan | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00 | complete |\n"
        )
        self.assertIn(
            "line 3: unknown spend plan '2026-08-11-missing-plan'", self.messages()
        )

    def test_money_in_record_is_an_error(self) -> None:
        path = self.fixture.add_experiment()
        for snippet in (
            "done (exit 0, 3m42s, $0.03)",
            "at most $20",
            "`run_ceiling_usd`",
            "in USD",
        ):
            with self.subTest(snippet=snippet):
                path.write_text(
                    COMPLETED_EXPERIMENT.replace(
                        "The metric increased.",
                        f"The metric increased, {snippet}.",
                    ),
                    encoding="utf-8",
                )
                messages = self.messages()
                self.assertTrue(
                    any("money lives in plans/spend/" in message for message in messages),
                    messages,
                )

    def test_usd_markers_exempt_marked_lines_and_report_a_note(self) -> None:
        path = self.fixture.add_experiment()
        marked = (
            "The metric increased.\n\n"
            "<!-- usd: measured — simulator objective, total cost per job -->\n"
            "| policy | $/job |\n|---|---|\n| greedy | $1.20 |\n"
            "<!-- /usd -->\n\n"
            "<!-- usd: parameter — spot price feeding the cost model, provider list 2026-09 -->\n"
            "rate $2.21/hr\n"
            "<!-- /usd -->\n"
        )
        path.write_text(COMPLETED_EXPERIMENT.replace("The metric increased.", marked), encoding="utf-8")
        _, issues = validator.validate(self.root)
        self.assertEqual([issue.level for issue in issues], ["NOTE"])
        self.assertIn("lines inside usd markers (measured 3, parameter 1)", issues[0].message)
        path.write_text(
            COMPLETED_EXPERIMENT.replace("The metric increased.", marked + "\nThe rental cost $3.40.\n"),
            encoding="utf-8",
        )
        self.assertTrue(any("money lives in plans/spend/" in m for m in self.messages()))

    def test_usd_marker_defects_are_errors(self) -> None:
        path = self.fixture.add_experiment()
        for label, block in (
            ("unclosed", "<!-- usd: measured — x -->\n$1.00\n"),
            ("stray close", "<!-- /usd -->\n"),
            ("unknown label", "<!-- usd: guess — x -->\n$1\n<!-- /usd -->\n"),
            ("no reason", "<!-- usd: parameter -->\n$1\n<!-- /usd -->\n"),
            ("nested", "<!-- usd: measured — a -->\n<!-- usd: measured — b -->\n<!-- /usd -->\n"),
            ("malformed", "<!-- usd measured x -->\n"),
        ):
            with self.subTest(label=label):
                path.write_text(
                    COMPLETED_EXPERIMENT.replace("The metric increased.", "The metric increased.\n\n" + block),
                    encoding="utf-8",
                )
                _, issues = validator.validate(self.root)
                self.assertTrue(any(i.level == "ERROR" and "usd marker" in i.message for i in issues), [i.message for i in issues])

    def test_math_spans_and_units_in_records_are_clean(self) -> None:
        path = self.fixture.add_experiment()
        for snippet in (
            "$10^{-4}$",
            "$x_1$ and $y$",
            "$1 - 0.9^{12} \\approx 0.718$",
            "1,620 forward passes, 0.26 GPU-hours",
        ):
            with self.subTest(snippet=snippet):
                path.write_text(
                    COMPLETED_EXPERIMENT.replace(
                        "The metric increased.",
                        f"The metric changed by {snippet}.",
                    ),
                    encoding="utf-8",
                )
                self.assertEqual(self.messages(), [])

    def test_review_ledger_register_header_must_match_schema(self) -> None:
        (self.root / "REVIEW-LEDGER.md").write_text(
            "# Review ledger\n\n"
            "## Review register\n\n"
            "| ID | Date | Kind | Target | Reviewer | Findings |\n"
            "|---|---|---|---|---|---|\n"
            "| R001 | 2026-09-10 | review-script | scripts/exp.py @ 3f1c9a2e"
            " | fresh session | none |\n",
            encoding="utf-8",
        )
        self.assertIn(
            "review register table must use columns: ID | Date | Kind | Target"
            " | Reviewer | Relation | Findings",
            self.messages(),
        )

    def test_well_formed_review_ledger_is_valid(self) -> None:
        (self.root / "REVIEW-LEDGER.md").write_text(
            "# Review ledger\n\n"
            "## Review register\n\n"
            "| ID | Date | Kind | Target | Reviewer | Relation | Findings |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| R001 | 2026-09-10 | review-script"
            " | scripts/exp_002_comparison.py @ 3f1c9a2e | fresh session"
            " | same model, no shared context | F001, F002 |\n"
            "| R002 | 2026-09-11 | review-design | EXP-002 design | second provider"
            " | different model | none |\n"
            "| R040–R061 | 2026-09-20 | review-script | 22 script revisions"
            " | fresh sessions | various | 2 findings |\n"
            "\n"
            "## Open findings\n\n"
            "| ID | Fault | Caught by | Severity | Status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| F002 | Summary averages over all cells, including the excluded pilot cell"
            " | R001 | silent | repair landed; awaiting review |\n",
            encoding="utf-8",
        )
        self.assertEqual(self.messages(), [])


if __name__ == "__main__":
    unittest.main()
