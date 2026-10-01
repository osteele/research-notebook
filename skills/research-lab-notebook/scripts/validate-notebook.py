#!/usr/bin/env python3
"""Validate the portable structural invariants of a research notebook."""

from __future__ import annotations

import argparse
import datetime
import json
import re
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "references" / "notebook-schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
REQUIRED_FILES = tuple(SCHEMA["required_files"])
STATUSES = set(SCHEMA["experiment_statuses"])
STATUS_ALIASES = dict(SCHEMA["experiment_status_aliases"])
REJECTED_STATUSES = dict(SCHEMA["rejected_experiment_statuses"])
FINDING_STATUSES = set(SCHEMA["finding_statuses"])
LEDGER_FIELDS = set(SCHEMA["ledger"]["required_fields"])
ANNEX_SUFFIX = SCHEMA["experiment"]["annex_suffix"]
INFORMED_BY_SECTION = SCHEMA["experiment"]["informed_by_section"]
DECISIONS_SECTION = SCHEMA["decisions"]["section"]
DECISION_DATE_RE = re.compile(SCHEMA["decisions"]["entry_date_pattern"])
ESTIMAND_HEADING_RE = re.compile(SCHEMA["experiment"]["estimand"]["heading_pattern"])
ESTIMAND_REGISTRATION_RE = re.compile(
    r"^\*\*" + re.escape(SCHEMA["experiment"]["estimand"]["registration_field"]) + r"\*\*:\s*([A-Za-z][\w-]*)"
)
REGISTRATION_VALUES = set(SCHEMA["experiment"]["estimand"]["registration_values"])
CLAIM_ESTIMAND_RE = re.compile(SCHEMA["claim"]["estimand_reference_pattern"])
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
QUESTION_ID_RE = re.compile(r"^RQ[-A-Z0-9]*\d[A-Z0-9]*$", re.IGNORECASE)
STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*([a-z-]+)", re.MULTILINE)
DATE_RE = re.compile(r"^\*\*Date\*\*:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)
HEADING_ID_RE = re.compile(r"^#\s+([A-Z][A-Z0-9]*-[A-Z0-9]+[a-z]?)\s*:", re.MULTILINE)
FILE_ID_RE = re.compile(r"^([A-Z][A-Z0-9]*-[A-Z0-9]+[a-z]?)(?:-|\.md$)")
EXPERIMENT_ID_RE = re.compile(SCHEMA["experiment_id"]["pattern"])
FINDING_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
PLAN_FILE_RE = FINDING_FILE_RE
BACKEND_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXPERIMENT_REF_RE = re.compile(r"\b[A-Z][A-Z0-9]*-[A-Z0-9]+[a-z]?\b")
CLAIM_ID_RE = re.compile(r"^C\d+$", re.IGNORECASE)
CLAIM_EXPERIMENT_PATH_RE = re.compile(
    r"(?i)(?:(?:lab-notebook/)?experiments/)[A-Za-z0-9_./-]+\.md"
)
CLAIM_FINDING_PATH_RE = re.compile(
    r"(?i)(?:(?:lab-notebook/)?findings/)[A-Za-z0-9_./-]+\.md"
)
CLAIM_PAPER_PATH_RE = re.compile(
    r"(?i)(?:(?:lab-notebook/)?papers/)[A-Za-z0-9_./-]+\.(?:md|typ|tex)"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")

SPEND_DIR = Path(SCHEMA["spend"]["directory"])
SPEND_AUTHORITY_FILE = SCHEMA["spend"]["authority_file"]
SPEND_AUTHORITY_SCHEMA = SCHEMA["spend"]["authority_schema"]
SPEND_AUTHORITY_FIELDS = tuple(SCHEMA["spend"]["authority_required_fields"])
SPEND_LEDGER_FILE = SCHEMA["spend"]["ledger_file"]
SPEND_LEDGER_COLUMNS = SCHEMA["spend"]["ledger_columns"]
SPEND_OPEN_OUTCOMES = set(SCHEMA["spend"]["open_outcomes"])
SPEND_TERMINAL_OUTCOMES = set(SCHEMA["spend"]["terminal_outcomes"])
SPEND_PROVISIONAL_SUFFIX = SCHEMA["spend"]["provisional_suffix"]
SPEND_NO_PLAN = SCHEMA["spend"]["no_plan"]
SPEND_ROW_ID_RE = re.compile(r"^S\d+$")
SPEND_AMOUNT_RE = re.compile(r"^\d+(?:\.\d+)?$")
MONEY_RE = re.compile(SCHEMA["experiment"]["money_pattern"])
MATH_SPAN_RE = re.compile(SCHEMA["experiment"]["math_span_pattern"])
USD_MARKER_KINDS = tuple(SCHEMA["experiment"]["usd_marker"]["kinds"])
USD_MARKER_OPEN_RE = re.compile(SCHEMA["experiment"]["usd_marker"]["open_pattern"])
USD_MARKER_CLOSE_RE = re.compile(SCHEMA["experiment"]["usd_marker"]["close_pattern"])
USD_MARKER_PREFIX_RE = re.compile(SCHEMA["experiment"]["usd_marker"]["prefix_pattern"])
REVIEW_LEDGER_FILE = SCHEMA["review_ledger"]["file"]
REVIEW_REGISTER_HEADING = SCHEMA["review_ledger"]["register_heading"]
REVIEW_REGISTER_COLUMNS = SCHEMA["review_ledger"]["register_columns"]
REVIEW_FINDINGS_HEADING = SCHEMA["review_ledger"]["findings_heading"]
REVIEW_FINDING_COLUMNS = SCHEMA["review_ledger"]["finding_columns"]
REVIEW_RELATIONS = set(SCHEMA["review_ledger"]["relations"])
REVIEW_REGISTER_ID_RE = re.compile(r"^R\d+$")
REVIEW_SUMMARY_ROW_RE = re.compile(r"^R\d+\s*[—–-]\s*R\d+$")


@dataclass(frozen=True)
class Issue:
    level: str
    path: Path
    message: str

    def render(self, root: Path) -> str:
        try:
            display = self.path.relative_to(root)
        except ValueError:
            display = self.path
        return f"{self.level}: {display}: {self.message}"

    def as_dict(self, root: Path) -> dict[str, str]:
        try:
            display = self.path.relative_to(root).as_posix()
        except ValueError:
            display = str(self.path)
        return {"level": self.level.lower(), "path": display, "message": self.message}


def notebook_path(candidate: Path) -> Path:
    nested = candidate / "lab-notebook"
    return nested if nested.is_dir() else candidate


def read_text(path: Path, issues: list[Issue]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues.append(Issue("ERROR", path, "file is not valid UTF-8"))
    except OSError as error:
        issues.append(Issue("ERROR", path, f"could not read file: {error}"))
    return None


def heading_pattern(heading: str) -> str:
    """Escape a heading for matching; "preregistered" also matches the hyphenated spelling."""
    return re.sub(r"(?i)(pre)(registered)", r"\1-?\2", re.escape(heading))


def has_heading(text: str, heading: str, ignore_case: bool = False) -> bool:
    flags = re.MULTILINE | (re.IGNORECASE if ignore_case else 0)
    return re.search(rf"^#+\s+{heading_pattern(heading)}\s*$", text, flags) is not None


def section_body(text: str, heading: str) -> str | None:
    """Return the text under a heading, up to the next heading of equal or higher level."""
    match = re.search(rf"^(#+)\s+{heading_pattern(heading)}\s*$", text, re.MULTILINE)
    if match is None:
        return None
    level = len(match.group(1))
    rest = text[match.end():]
    end = re.search(rf"^#{{1,{level}}}\s+", rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


def estimand_registrations(text: str) -> dict[str, str]:
    """Map each declared estimand ID to its registration value ("" when absent)."""
    declared: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        heading = ESTIMAND_HEADING_RE.match(line)
        if heading:
            current = heading.group(0).split()[-1].upper()
            declared.setdefault(current, "")
            continue
        if line.startswith("#"):
            current = None
            continue
        if current is not None and not declared[current]:
            registration = ESTIMAND_REGISTRATION_RE.match(line)
            if registration:
                declared[current] = registration.group(1).lower()
    return declared


def notebook_markdown_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*.md")
        if not any(part.startswith(".") for part in path.relative_to(root).parts)
    ]


def wikilink_resolves(root: Path, target: str) -> bool:
    stem = target.strip()
    if QUESTION_ID_RE.fullmatch(stem):
        return True
    return any(path.stem == stem for path in notebook_markdown_files(root))


def validate_section_links(
    root: Path, path: Path, text: str, heading: str, issues: list[Issue]
) -> None:
    body = section_body(text, heading)
    if body is None:
        return
    for target in WIKILINK_RE.findall(body):
        if not wikilink_resolves(root, target):
            issues.append(
                Issue("ERROR", path, f"{heading} link [[{target}]] does not resolve to a notebook file")
            )
    for reference in MARKDOWN_LINK_RE.findall(body):
        if reference.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = plan_link_path(root, path, reference)
        if target.suffix.lower() == ".md" and not target.is_file():
            issues.append(Issue("ERROR", path, f"{heading} link {reference} does not resolve"))


def validate_decisions(root: Path, path: Path, text: str, issues: list[Issue]) -> None:
    """A `## Decisions` log: dated entries, newest last, links that resolve."""
    body = section_body(text, DECISIONS_SECTION)
    if body is None:
        return
    validate_section_links(root, path, text, DECISIONS_SECTION, issues)
    previous: str | None = None
    for line in body.splitlines():
        if not line.startswith("- "):
            continue
        match = DECISION_DATE_RE.match(line)
        if match is None:
            issues.append(
                Issue("WARNING", path, f"{DECISIONS_SECTION} entry lacks a leading **YYYY-MM-DD** date")
            )
            continue
        when = match.group(1)
        if previous is not None and when < previous:
            issues.append(
                Issue(
                    "WARNING",
                    path,
                    f"{DECISIONS_SECTION} entries run newest last; {when} follows {previous}",
                )
            )
        previous = when


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip("'\"")
    return values


def valid_date(value: str) -> bool:
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def valid_timestamp(value: str) -> bool:
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def ledger_filename(job_id: str) -> str:
    encoded = urllib.parse.quote(job_id, safe="-_")
    if encoded in {".", ".."}:
        encoded = encoded.replace(".", "%2E")
    return f"{encoded}.json"


def validate_index_membership(
    index_path: Path,
    records: list[tuple[Path, tuple[str, ...]]],
    issues: list[Issue],
) -> None:
    text = read_text(index_path, issues)
    if text is None:
        return
    for path, identifiers in records:
        if not any(identifier in text for identifier in identifiers):
            issues.append(Issue("ERROR", path, f"not listed in {index_path.name}"))


def validate_experiments(root: Path, issues: list[Issue]) -> None:
    experiment_dir = root / "experiments"
    seen: dict[str, Path] = {}
    records: list[tuple[Path, tuple[str, ...]]] = []
    for path in sorted(experiment_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        if path.name.endswith(ANNEX_SUFFIX):
            annex_match = FILE_ID_RE.match(path.name)
            if not annex_match or experiment_record(root, annex_match.group(1)) is None:
                issues.append(
                    Issue("ERROR", path, "annex filename must start with the ID of an existing experiment")
                )
            continue
        text = read_text(path, issues)
        if text is None:
            continue

        file_match = FILE_ID_RE.match(path.name)
        heading_match = HEADING_ID_RE.search(text)
        experiment_id = heading_match.group(1) if heading_match else None
        if not file_match:
            issues.append(Issue("ERROR", path, "filename does not start with an experiment ID"))
        if experiment_id is None:
            issues.append(Issue("ERROR", path, "first heading lacks an experiment ID"))
        elif file_match and experiment_id != file_match.group(1):
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"heading ID {experiment_id} does not match filename ID {file_match.group(1)}",
                )
            )

        if experiment_id:
            previous = seen.get(experiment_id)
            if previous:
                issues.append(
                    Issue("ERROR", path, f"duplicate experiment ID also used by {previous.name}")
                )
            else:
                seen[experiment_id] = path
            records.append((path, (experiment_id, path.name, path.stem)))

        status_match = STATUS_RE.search(text)
        if not status_match:
            issues.append(Issue("ERROR", path, "missing **Status** field"))
            continue
        status = status_match.group(1)
        if status in STATUS_ALIASES:
            canonical = STATUS_ALIASES[status]
            issues.append(
                Issue("WARNING", path, f"legacy status spelling {status!r}; write {canonical!r}")
            )
            status = canonical
        elif status in REJECTED_STATUSES:
            issues.append(
                Issue("ERROR", path, f"status {status!r} is not accepted: {REJECTED_STATUSES[status]}")
            )
            continue
        elif status not in STATUSES:
            issues.append(Issue("ERROR", path, f"unknown experiment status {status!r}"))

        for estimand_id, value in estimand_registrations(text).items():
            if not value:
                issues.append(
                    Issue("ERROR", path, f"estimand {estimand_id} has no **Registration**: line")
                )
            elif value not in REGISTRATION_VALUES:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"estimand {estimand_id} registration {value!r} is not one of "
                        f"{', '.join(sorted(REGISTRATION_VALUES))}",
                    )
                )
        validate_section_links(root, path, text, INFORMED_BY_SECTION, issues)
        validate_decisions(root, path, text, issues)

        designed = {"planned", "queued", "running", "in-progress", "pilot-complete", "blocked", "completed"}
        if status in designed:
            for heading in (
                "Hypothesis",
                "Method",
                "Preregistered predictions (a priori)",
                "Decision rule (a priori)",
            ):
                if not has_heading(text, heading):
                    issues.append(Issue("ERROR", path, f"missing ## {heading} section"))
        if status in {"queued", "running", "pilot-complete", "completed"}:
            if not has_heading(text, "Runs"):
                issues.append(Issue("ERROR", path, "missing ## Runs section"))
        if status == "completed":
            for heading in (
                "Results",
                "Outcomes against preregistered predictions",
                "Conclusion",
                "Artifacts",
            ):
                if not has_heading(text, heading):
                    issues.append(
                        Issue("ERROR", path, f"completed experiment lacks ## {heading}")
                    )
        if status == "proposed":
            for heading in ("Hypothesis", "Method"):
                if not has_heading(text, heading):
                    issues.append(Issue("WARNING", path, f"proposed experiment lacks ## {heading}"))
        if status == "abandoned" and not has_heading(text, "Conclusion"):
            issues.append(Issue("WARNING", path, "abandoned experiment lacks ## Conclusion"))

    validate_index_membership(experiment_dir / "README.md", records, issues)


def validate_findings(root: Path, issues: list[Issue]) -> None:
    finding_dir = root / "findings"
    records: list[tuple[Path, tuple[str, ...]]] = []
    for path in sorted(finding_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = read_text(path, issues)
        if text is None:
            continue
        file_match = FINDING_FILE_RE.fullmatch(path.name)
        if not file_match:
            issues.append(
                Issue("ERROR", path, "filename must be YYYY-MM-DD-lowercase-topic.md")
            )
        date_match = DATE_RE.search(text)
        if not date_match:
            issues.append(Issue("ERROR", path, "missing **Date** field"))
        else:
            date = date_match.group(1)
            if not valid_date(date):
                issues.append(Issue("ERROR", path, f"invalid date {date!r}"))
            if file_match and date != file_match.group(1):
                issues.append(Issue("ERROR", path, "Date field does not match filename"))
        status_match = STATUS_RE.search(text)
        if not status_match:
            issues.append(Issue("ERROR", path, "missing **Status** field"))
        elif status_match.group(1) not in FINDING_STATUSES:
            issues.append(
                Issue("ERROR", path, f"unknown finding status {status_match.group(1)!r}")
            )
        references = set(EXPERIMENT_REF_RE.findall(text))
        if len(references) < 2:
            issues.append(
                Issue("ERROR", path, "finding must link at least two experiments")
            )
        for heading in (
            "Claim",
            "Evidence",
            "Synthesis",
            "Scope and threats to validity",
            "Consequences",
            "Sources",
        ):
            if not has_heading(text, heading):
                issues.append(Issue("ERROR", path, f"missing ## {heading} section"))
        records.append((path, (path.name, path.stem)))
    validate_index_membership(finding_dir / "README.md", records, issues)


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def evidence_path(root: Path, reference: str) -> Path:
    relative = Path(reference)
    if relative.parts and relative.parts[0] == "lab-notebook":
        relative = Path(*relative.parts[1:])
    return root / relative


def experiment_record(root: Path, experiment_id: str) -> Path | None:
    normalized = experiment_id.casefold()
    for path in sorted((root / "experiments").glob("*.md")):
        if path.name.endswith(ANNEX_SUFFIX):
            continue
        stem = path.stem.casefold()
        if stem == normalized:
            return path
        if stem.startswith(normalized):
            suffix = stem[len(normalized):]
            if suffix and not suffix[0].isalnum():
                return path
    return None


def experiment_exists(root: Path, experiment_id: str) -> bool:
    return experiment_record(root, experiment_id) is not None


def validate_claim_estimands(
    root: Path, path: Path, line_number: int, evidence: str, issues: list[Issue]
) -> None:
    for experiment_id, estimand_id in CLAIM_ESTIMAND_RE.findall(evidence):
        reference = f"{experiment_id}:{estimand_id}"
        record = experiment_record(root, experiment_id)
        declared = estimand_registrations(record.read_text(encoding="utf-8")) if record else {}
        value = declared.get(estimand_id.upper())
        if value is None:
            declared_ids = ", ".join(sorted(declared)) or "none"
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"line {line_number}: {reference} does not resolve; {experiment_id} declares {declared_ids}",
                )
            )
        elif value == "found":
            issues.append(
                Issue(
                    "WARNING",
                    path,
                    f"line {line_number}: {reference} is a found estimand, so this claim is a found result; "
                    "confirmatory use needs a fresh registered run",
                )
            )
        elif value == "gate":
            issues.append(
                Issue(
                    "WARNING",
                    path,
                    f"line {line_number}: {reference} is a gate on another estimand, not a result to cite",
                )
            )


def validate_claims(root: Path, issues: list[Issue]) -> None:
    path = root / "CLAIMS.md"
    if not path.is_file():
        return
    text = read_text(path, issues)
    if text is None:
        return
    lines = text.splitlines()
    expected_columns = SCHEMA["claim"]["columns"]
    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.lstrip().startswith("|") and table_cells(line) == expected_columns
        ),
        None,
    )
    if header_index is None:
        issues.append(
            Issue("ERROR", path, f"claim table must use columns: {' | '.join(expected_columns)}")
        )
        return
    seen: set[str] = set()
    for line_number, line in enumerate(lines[header_index + 2 :], start=header_index + 3):
        if not line.lstrip().startswith("|"):
            break
        cells = table_cells(line)
        if len(cells) != len(expected_columns):
            issues.append(Issue("ERROR", path, f"line {line_number}: claim row has {len(cells)} columns"))
            continue
        claim_id, role, claim, status, evidence, paper = cells
        if not CLAIM_ID_RE.fullmatch(claim_id):
            issues.append(Issue("ERROR", path, f"line {line_number}: invalid claim ID {claim_id!r}"))
        normalized_id = claim_id.casefold()
        if normalized_id in seen:
            issues.append(Issue("ERROR", path, f"line {line_number}: duplicate claim ID {claim_id}"))
        seen.add(normalized_id)
        if role not in SCHEMA["claim"]["roles"]:
            issues.append(Issue("ERROR", path, f"line {line_number}: invalid claim role {role!r}"))
        if not claim:
            issues.append(Issue("ERROR", path, f"line {line_number}: claim text is empty"))
        if status in SCHEMA["claim"]["status_aliases"]:
            canonical = SCHEMA["claim"]["status_aliases"][status]
            issues.append(
                Issue("WARNING", path, f"line {line_number}: legacy claim status spelling {status!r}; write {canonical!r}")
            )
        elif status not in SCHEMA["claim"]["statuses"]:
            issues.append(Issue("ERROR", path, f"line {line_number}: invalid claim status {status!r}"))
        if not paper:
            issues.append(Issue("ERROR", path, f"line {line_number}: paper key is empty"))
        if not evidence:
            issues.append(Issue("ERROR", path, f"line {line_number}: evidence is empty"))
            continue

        experiment_paths = CLAIM_EXPERIMENT_PATH_RE.findall(evidence)
        evidence_without_paths = CLAIM_EXPERIMENT_PATH_RE.sub(" ", evidence)
        finding_paths = CLAIM_FINDING_PATH_RE.findall(evidence_without_paths)
        evidence_without_paths = CLAIM_FINDING_PATH_RE.sub(" ", evidence_without_paths)
        experiment_ids = sorted(set(EXPERIMENT_REF_RE.findall(evidence_without_paths)))
        resolved_experiment = False
        for reference in experiment_paths:
            target = evidence_path(root, reference)
            if target.is_file():
                resolved_experiment = True
            else:
                issues.append(Issue("ERROR", path, f"line {line_number}: missing experiment path {reference}"))
        for experiment_id in experiment_ids:
            if experiment_exists(root, experiment_id):
                resolved_experiment = True
            else:
                issues.append(Issue("ERROR", path, f"line {line_number}: no record for {experiment_id}"))
        for reference in finding_paths:
            if not evidence_path(root, reference).is_file():
                issues.append(Issue("ERROR", path, f"line {line_number}: missing finding path {reference}"))
        if CLAIM_PAPER_PATH_RE.search(evidence):
            issues.append(Issue("ERROR", path, f"line {line_number}: papers cannot be evidence sources"))
        validate_claim_estimands(root, path, line_number, evidence, issues)
        if not resolved_experiment:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"line {line_number}: evidence must cite at least one experiment record; findings cannot replace it",
                )
            )


def plan_paths(root: Path) -> list[Path]:
    plan_dir = root / "plans"
    if not plan_dir.is_dir():
        return []
    return [
        path
        for path in sorted(plan_dir.rglob("*.md"))
        if path.name != "README.md" and not path.is_relative_to(root / SPEND_DIR)
    ]


def plan_link_path(root: Path, source: Path, reference: str) -> Path:
    clean = reference.split("#", 1)[0]
    if clean.startswith("lab-notebook/"):
        return root / clean.removeprefix("lab-notebook/")
    if clean.startswith(("plans/", "experiments/", "findings/")):
        return root / clean
    return source.parent / clean


def validate_plan_links(root: Path, path: Path, text: str, issues: list[Issue]) -> None:
    for reference in MARKDOWN_LINK_RE.findall(text):
        if reference.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = plan_link_path(root, path, reference)
        if target.suffix.lower() == ".md" and not target.is_file():
            issues.append(Issue("ERROR", path, f"broken plan link {reference}"))


def validate_plans(root: Path, issues: list[Issue]) -> None:
    plan_dir = root / "plans"
    if not plan_dir.is_dir():
        return
    plan_schema = SCHEMA["plan"]
    seen_stems: dict[str, Path] = {}
    for path in plan_paths(root):
        relative = path.relative_to(plan_dir)
        previous = seen_stems.get(path.stem)
        if previous is not None:
            issues.append(
                Issue("ERROR", path, f"duplicate plan basename also used by {previous.as_posix()}")
            )
        seen_stems[path.stem] = relative
        text = read_text(path, issues)
        if text is None:
            continue
        file_match = PLAN_FILE_RE.fullmatch(path.name)
        if not file_match:
            issues.append(
                Issue("ERROR", path, "filename must be YYYY-MM-DD-lowercase-topic.md")
            )
        metadata = frontmatter(text)
        if not metadata:
            issues.append(Issue("ERROR", path, "missing YAML frontmatter"))
            continue
        missing = [
            key for key in plan_schema["required_frontmatter"] if key not in metadata
        ]
        if missing:
            issues.append(
                Issue("ERROR", path, f"missing frontmatter: {', '.join(missing)}")
            )
        status = metadata.get("status", "")
        written_status = status
        if status in plan_schema["status_aliases"]:
            status = plan_schema["status_aliases"][status]
            issues.append(
                Issue("WARNING", path, f"legacy plan status spelling {written_status!r}; write {status!r}")
            )
        elif status not in plan_schema["statuses"]:
            issues.append(Issue("ERROR", path, f"unknown plan status {status!r}"))
        expected_dir = plan_schema["status_directories"].get(status)
        actual_dir = "." if relative.parent == Path(".") else relative.parts[0]
        accepted_dirs = {expected_dir, written_status if expected_dir not in (None, ".") else expected_dir}
        if expected_dir is not None and actual_dir not in accepted_dirs:
            issues.append(
                Issue("ERROR", path, f"status {status!r} belongs in {expected_dir}/")
            )
        for field in ("created", "updated"):
            value = metadata.get(field)
            if value is not None and not valid_date(value):
                issues.append(Issue("ERROR", path, f"{field} must be YYYY-MM-DD"))
        validate_decisions(root, path, text, issues)
        created = metadata.get("created", "")
        updated = metadata.get("updated", "")
        if file_match and valid_date(created) and created != file_match.group(1):
            issues.append(Issue("ERROR", path, "created date does not match filename"))
        if valid_date(created) and valid_date(updated) and updated < created:
            issues.append(Issue("ERROR", path, "updated date precedes created date"))
        if not metadata.get("summary", "").strip():
            issues.append(Issue("ERROR", path, "summary must be non-empty"))
        next_action = metadata.get("next_action", "").strip()
        if status in plan_schema["terminal_statuses"]:
            if next_action.lower() not in {"", "none", "null", "~"}:
                issues.append(
                    Issue("ERROR", path, "terminal plan next_action must be empty or none")
                )
            for heading in plan_schema["terminal_sections"].get(status, []):
                if not has_heading(text, heading):
                    issues.append(
                        Issue("ERROR", path, f"terminal plan lacks ## {heading}")
                    )
            report = plan_schema["completion_report"]
            if status == "completed" and not any(
                has_heading(text, heading, ignore_case=True)
                for heading in report["recognized_headings"]
            ):
                issues.append(
                    Issue("ERROR", path, f"completed plan lacks ## {report['heading']}")
                )
        elif not next_action:
            issues.append(Issue("ERROR", path, "nonterminal plan needs next_action"))
        reserve = plan_schema["confirmation_reserve"]
        reserve_body = section_body(text, reserve["heading"])
        if reserve_body is not None:
            for marker in reserve["required_markers"]:
                if f"**{marker}:**" not in reserve_body and f"**{marker}**:" not in reserve_body:
                    issues.append(
                        Issue("ERROR", path, f"{reserve['heading']} section lacks **{marker}:**")
                    )
        for field in plan_schema["required_frontmatter_by_status"].get(status, []):
            if not metadata.get(field, "").strip():
                issues.append(Issue("ERROR", path, f"{status} plan requires {field}"))
        alternatives = plan_schema["one_of_frontmatter_by_status"].get(status, [])
        if alternatives and not any(metadata.get(field, "").strip() for field in alternatives):
            issues.append(
                Issue("ERROR", path, f"{status} plan requires one of: {', '.join(alternatives)}")
            )
        if status in {"active", "blocked", "gated"} and not metadata.get("current_phase", "").strip():
            issues.append(Issue("WARNING", path, f"{status} plan has no current_phase"))
        for heading in plan_schema["required_sections"]:
            if not has_heading(text, heading):
                issues.append(Issue("ERROR", path, f"missing ## {heading} section"))
        validate_plan_links(root, path, text, issues)


def first_heading(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def render_plan_index(root: Path) -> str:
    plan_dir = root / "plans"
    groups: dict[str, list[tuple[Path, str, dict[str, str]]]] = {
        status: [] for status in SCHEMA["plan"]["statuses"]
    }
    for path in plan_paths(root):
        text = path.read_text(encoding="utf-8")
        metadata = frontmatter(text)
        status = metadata.get("status", "")
        if status in groups:
            groups[status].append(
                (path.relative_to(plan_dir), first_heading(text, path.stem), metadata)
            )
    lines = [
        "# Plans",
        "",
        "Generated from plan frontmatter. Active plans live at the top level; other",
        "statuses live in matching subdirectories.",
        "",
    ]
    for status in SCHEMA["plan"]["statuses"]:
        records = groups[status]
        if not records:
            continue
        lines.extend((f"## {status.title()}", ""))
        for relative, title, metadata in sorted(records, key=lambda item: item[0].as_posix()):
            lines.append(f"- [{title}]({relative.as_posix()}): {metadata.get('summary', '').strip()}")
            next_action = metadata.get("next_action", "").strip()
            if next_action.lower() not in {"", "none", "null", "~"}:
                lines.append(f"  Next: {next_action}")
            for field, label in (
                ("gate", "Gate"),
                ("revisit_when", "Revisit"),
                ("promote_when", "Promote"),
                ("superseded_by", "Superseded by"),
                ("abandoned_because", "Abandoned because"),
            ):
                value = metadata.get(field, "").strip()
                if value:
                    lines.append(f"  {label}: {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def experiment_record_paths(root: Path) -> list[Path]:
    experiment_dir = root / "experiments"
    if not experiment_dir.is_dir():
        return []
    return [
        path
        for path in sorted(experiment_dir.glob("*.md"))
        if path.name != "README.md" and not path.name.endswith(ANNEX_SUFFIX)
    ]


def table_header(lines: list[str], columns: list[str]) -> int | None:
    return next(
        (
            index
            for index, line in enumerate(lines)
            if line.lstrip().startswith("|") and table_cells(line) == columns
        ),
        None,
    )


def validate_spend_authority(
    path: Path,
    authority: object,
    known_plans: set[str],
    issues: list[Issue],
) -> None:
    if not isinstance(authority, dict):
        issues.append(Issue("ERROR", path, "authority must be a JSON object"))
        return
    if authority.get("schema") != SPEND_AUTHORITY_SCHEMA:
        issues.append(Issue("ERROR", path, f"schema must be {SPEND_AUTHORITY_SCHEMA!r}"))
    plans = authority.get("plans")
    if not isinstance(plans, dict):
        issues.append(Issue("ERROR", path, "plans must be an object"))
        return
    for stem, entry in plans.items():
        if stem not in known_plans:
            issues.append(Issue("ERROR", path, f"plans entry {stem!r} names no plan"))
        if not isinstance(entry, dict):
            issues.append(Issue("ERROR", path, f"plans entry {stem!r} must be an object"))
            continue
        missing = [field for field in SPEND_AUTHORITY_FIELDS if field not in entry]
        if missing:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"plans entry {stem!r} is missing fields: {', '.join(missing)}",
                )
            )
        ceiling = entry.get("shared_ceiling_usd")
        if isinstance(ceiling, bool) or not isinstance(ceiling, (int, float)) or ceiling <= 0:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"plans entry {stem!r} shared_ceiling_usd must be a positive number",
                )
            )


def validate_spend_ledger(
    path: Path,
    lines: list[str],
    known_plans: set[str],
    issues: list[Issue],
) -> None:
    header_index = table_header(lines, SPEND_LEDGER_COLUMNS)
    if header_index is None:
        issues.append(
            Issue(
                "ERROR",
                path,
                f"spend ledger table must use columns: {' | '.join(SPEND_LEDGER_COLUMNS)}",
            )
        )
        return
    seen_ids: set[str] = set()
    for line_number, line in enumerate(lines[header_index + 2 :], start=header_index + 3):
        if not line.lstrip().startswith("|"):
            continue
        cells = table_cells(line)
        if len(cells) != len(SPEND_LEDGER_COLUMNS):
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"line {line_number}: spend ledger row has {len(cells)} cells "
                    f"(expected {len(SPEND_LEDGER_COLUMNS)})",
                )
            )
            continue
        row_id, _, plan, _, _, _, _, committed, actual, outcome = cells
        if not SPEND_ROW_ID_RE.fullmatch(row_id):
            issues.append(
                Issue("ERROR", path, f"line {line_number}: invalid spend ledger row ID {row_id!r}")
            )
        elif row_id in seen_ids:
            issues.append(
                Issue("ERROR", path, f"line {line_number}: duplicate spend ledger row ID {row_id}")
            )
        seen_ids.add(row_id)
        if plan != SPEND_NO_PLAN and plan not in known_plans:
            issues.append(Issue("ERROR", path, f"line {line_number}: unknown spend plan {plan!r}"))
        if outcome.endswith(SPEND_PROVISIONAL_SUFFIX):
            base = outcome.removesuffix(SPEND_PROVISIONAL_SUFFIX)
            outcome_known = base in SPEND_TERMINAL_OUTCOMES
        else:
            outcome_known = outcome in SPEND_OPEN_OUTCOMES or outcome in SPEND_TERMINAL_OUTCOMES
        if not outcome_known:
            issues.append(
                Issue("ERROR", path, f"line {line_number}: invalid spend outcome {outcome!r}")
            )
        for label, amount in (("Committed USD", committed), ("Actual USD", actual)):
            if amount != SPEND_NO_PLAN and not SPEND_AMOUNT_RE.fullmatch(amount):
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"line {line_number}: invalid {label} amount {amount!r}",
                    )
                )


def validate_spend(root: Path, issues: list[Issue]) -> None:
    spend_dir = root / SPEND_DIR
    if not spend_dir.is_dir():
        return
    known_plans = {path.stem for path in plan_paths(root)}

    authority_path = spend_dir / SPEND_AUTHORITY_FILE
    if not authority_path.is_file():
        issues.append(Issue("ERROR", authority_path, f"missing {SPEND_AUTHORITY_FILE}"))
    else:
        text = read_text(authority_path, issues)
        if text is not None:
            try:
                authority = json.loads(text)
            except json.JSONDecodeError as error:
                issues.append(Issue("ERROR", authority_path, f"invalid JSON: {error.msg}"))
            else:
                validate_spend_authority(authority_path, authority, known_plans, issues)

    ledger_path = spend_dir / SPEND_LEDGER_FILE
    if not ledger_path.is_file():
        issues.append(Issue("ERROR", ledger_path, f"missing {SPEND_LEDGER_FILE}"))
        return
    text = read_text(ledger_path, issues)
    if text is not None:
        validate_spend_ledger(ledger_path, text.splitlines(), known_plans, issues)


def validate_money_in_records(root: Path, issues: list[Issue]) -> None:
    """Report currency in experiment records outside `usd:` markers.

    A marker wraps lines whose dollars are data: `measured` for a simulator's
    objective, `parameter` for an external market input whose source it names.
    It scopes lines rather than files, so a simulator table cannot license a
    rental-cost line beside it. Each record's marked line count is reported as a
    NOTE so growth in exemptions stays visible.
    """
    for path in experiment_record_paths(root):
        text = read_text(path, issues)
        if text is None:
            continue
        open_at: int | None = None
        open_kind = ""
        marked: dict[str, int] = {}
        for line_number, line in enumerate(text.splitlines(), start=1):
            closer = USD_MARKER_CLOSE_RE.search(line)
            opener = USD_MARKER_OPEN_RE.search(line)
            if closer:
                if open_at is None:
                    issues.append(Issue("ERROR", path, f"line {line_number}: `<!-- /usd -->` closes no open usd marker"))
                open_at = None
                continue
            if opener:
                kind, reason = opener.group("kind"), opener.group("reason")
                if open_at is not None:
                    issues.append(Issue("ERROR", path, f"line {line_number}: usd marker opened while the one at line {open_at} is still open"))
                if kind not in USD_MARKER_KINDS:
                    issues.append(Issue("ERROR", path, f"line {line_number}: usd marker label {kind!r} is not one of {', '.join(USD_MARKER_KINDS)}"))
                if not reason:
                    issues.append(Issue("ERROR", path, f"line {line_number}: usd marker needs a reason naming its source or the model it feeds"))
                open_at, open_kind = line_number, kind
                continue
            if USD_MARKER_PREFIX_RE.search(line):
                issues.append(Issue("ERROR", path, f"line {line_number}: malformed usd marker; use `<!-- usd: measured|parameter — reason -->`"))
                continue
            if open_at is not None:
                marked[open_kind] = marked.get(open_kind, 0) + 1
                continue
            without_math = MATH_SPAN_RE.sub(" ", line)
            match = MONEY_RE.search(without_math)
            if match:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"line {line_number}: currency amount {match.group(0)!r} in a record; "
                        "records carry units and job ids, money lives in plans/spend/",
                    )
                )
        if open_at is not None:
            issues.append(Issue("ERROR", path, f"line {open_at}: usd marker is never closed with `<!-- /usd -->`"))
        if marked:
            detail = ", ".join(f"{kind} {count}" for kind, count in sorted(marked.items()))
            issues.append(Issue("NOTE", path, f"{sum(marked.values())} lines inside usd markers ({detail})"))


def validate_review_register(path: Path, body: str, issues: list[Issue]) -> None:
    lines = body.splitlines()
    header_index = table_header(lines, REVIEW_REGISTER_COLUMNS)
    if header_index is None:
        issues.append(
            Issue(
                "ERROR",
                path,
                f"review register table must use columns: {' | '.join(REVIEW_REGISTER_COLUMNS)}",
            )
        )
        return
    seen: set[str] = set()
    relation_index = REVIEW_REGISTER_COLUMNS.index("Relation")
    for line_number, line in enumerate(lines[header_index + 2 :], start=header_index + 3):
        if not line.lstrip().startswith("|"):
            break
        cells = table_cells(line)
        row_id = cells[0]
        if REVIEW_SUMMARY_ROW_RE.fullmatch(row_id):
            continue
        if not REVIEW_REGISTER_ID_RE.fullmatch(row_id):
            issues.append(
                Issue("ERROR", path, f"line {line_number}: invalid review register ID {row_id!r}")
            )
            continue
        if row_id in seen:
            issues.append(
                Issue("ERROR", path, f"line {line_number}: duplicate review register ID {row_id}")
            )
        seen.add(row_id)
        if len(cells) != len(REVIEW_REGISTER_COLUMNS):
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"line {line_number}: review register row has {len(cells)} cells "
                    f"(expected {len(REVIEW_REGISTER_COLUMNS)})",
                )
            )
            continue
        if cells[relation_index] not in REVIEW_RELATIONS:
            issues.append(
                Issue("ERROR", path, f"line {line_number}: invalid relation {cells[relation_index]!r}")
            )


def validate_review_ledger(root: Path, issues: list[Issue]) -> None:
    path = root / REVIEW_LEDGER_FILE
    if not path.is_file():
        return
    text = read_text(path, issues)
    if text is None:
        return

    register_body = section_body(text, REVIEW_REGISTER_HEADING)
    if register_body is None:
        issues.append(Issue("ERROR", path, f"missing ## {REVIEW_REGISTER_HEADING} section"))
    else:
        validate_review_register(path, register_body, issues)

    findings_body = section_body(text, REVIEW_FINDINGS_HEADING)
    if findings_body is None:
        return
    first_row = next((line for line in findings_body.splitlines() if line.lstrip().startswith("|")), None)
    if first_row is not None and table_cells(first_row) != REVIEW_FINDING_COLUMNS:
        issues.append(
            Issue(
                "ERROR",
                path,
                f"open findings table must use columns: {' | '.join(REVIEW_FINDING_COLUMNS)}",
            )
        )


def validate_ledger(root: Path, issues: list[Issue]) -> None:
    ledger_root = root / "jobs" / "processed"
    if not ledger_root.exists():
        return
    seen: set[tuple[str, str]] = set()
    for path in sorted(ledger_root.rglob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            issues.append(Issue("ERROR", path, f"invalid JSON: {error.msg}"))
            continue
        except UnicodeDecodeError:
            issues.append(Issue("ERROR", path, "file is not valid UTF-8"))
            continue
        except OSError as error:
            issues.append(Issue("ERROR", path, f"could not read file: {error}"))
            continue
        if not isinstance(record, dict):
            issues.append(Issue("ERROR", path, "ledger record must be a JSON object"))
            continue
        missing = sorted(LEDGER_FIELDS - record.keys())
        if missing:
            issues.append(Issue("ERROR", path, f"missing fields: {', '.join(missing)}"))
            continue
        backend = record["backend"]
        job_id = record["job_id"]
        if not isinstance(backend, str) or not isinstance(job_id, str):
            issues.append(Issue("ERROR", path, "backend and job_id must be strings"))
            continue
        key = (backend, job_id)
        if key in seen:
            issues.append(Issue("ERROR", path, f"duplicate ledger key {backend}:{job_id}"))
        seen.add(key)
        if path.parent.name != backend:
            issues.append(Issue("ERROR", path, "backend field does not match parent directory"))
        if not BACKEND_RE.fullmatch(backend):
            issues.append(Issue("ERROR", path, f"invalid normalized backend {backend!r}"))
        if path.name != ledger_filename(job_id):
            issues.append(Issue("ERROR", path, "filename is not the encoded job_id"))
        if record["schema_version"] != SCHEMA["ledger"]["schema_version"]:
            issues.append(Issue("ERROR", path, "unsupported schema_version"))
        if record["terminal_status"] not in SCHEMA["ledger"]["terminal_statuses"]:
            issues.append(Issue("ERROR", path, "invalid terminal_status"))
        experiment_id = record["experiment_id"]
        if not isinstance(experiment_id, str) or not EXPERIMENT_ID_RE.fullmatch(experiment_id):
            issues.append(Issue("ERROR", path, "experiment_id must be a non-empty experiment ID"))
        processed_at = record["processed_at"]
        if not isinstance(processed_at, str) or not valid_timestamp(processed_at):
            issues.append(Issue("ERROR", path, "processed_at must be an ISO 8601 timestamp with timezone"))
        revision = record["notebook_revision"]
        if not isinstance(revision, str) or not revision.strip():
            issues.append(Issue("ERROR", path, "notebook_revision must be a non-empty string"))
        evidence = record["evidence"]
        if not isinstance(evidence, list) or not evidence:
            issues.append(Issue("ERROR", path, "evidence must be a non-empty list"))
            continue
        for item in evidence:
            if not isinstance(item, str):
                issues.append(Issue("ERROR", path, "evidence entries must be strings"))
                continue
            relative = Path(item)
            if relative.is_absolute() or ".." in relative.parts:
                issues.append(Issue("ERROR", path, f"evidence path must stay inside notebook: {item}"))
                continue
            evidence_path = (root / relative).resolve()
            if not evidence_path.is_relative_to(root):
                issues.append(Issue("ERROR", path, f"evidence path escapes notebook: {item}"))
            elif not evidence_path.is_file():
                issues.append(Issue("ERROR", path, f"evidence path does not exist: {item}"))


def validate(candidate: Path) -> tuple[Path, list[Issue]]:
    root = notebook_path(candidate.resolve())
    issues: list[Issue] = []
    if not root.is_dir():
        return root, [Issue("ERROR", root, "notebook directory does not exist")]
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            issues.append(Issue("ERROR", path, "required file is missing"))
    if (root / "experiments").is_dir():
        validate_experiments(root, issues)
    if (root / "findings").is_dir():
        validate_findings(root, issues)
    validate_claims(root, issues)
    validate_plans(root, issues)
    validate_spend(root, issues)
    validate_money_in_records(root, issues)
    validate_review_ledger(root, issues)
    validate_ledger(root, issues)
    return root, issues


def diagnostics_report(root: Path, issues: list[Issue], strict: bool) -> dict[str, object]:
    errors = sum(issue.level == "ERROR" for issue in issues)
    warnings = sum(issue.level == "WARNING" for issue in issues)
    return {
        "schema_version": 1,
        "notebook_schema_version": SCHEMA["schema_version"],
        "notebook": str(root),
        "valid": errors == 0 and (warnings == 0 or not strict),
        "strict": strict,
        "counts": {"errors": errors, "warnings": warnings},
        "issues": [issue.as_dict(root) for issue in issues],
    }


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="validate-notebook-") as temporary:
        root = Path(temporary) / "lab-notebook"
        for relative in REQUIRED_FILES:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Placeholder\n", encoding="utf-8")
        (root / "CLAIMS.md").write_text(
            "# Publication claims\n\n"
            "| ID | Role | Claim | Status | Evidence | Paper |\n"
            "|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
        experiment = root / "experiments" / "EXP-001-example.md"
        experiment.write_text(
            """# EXP-001: Example

**Status**: completed

## Hypothesis

Example.

## Method

Example.

## Preregistered predictions (a priori)

- **P1**: Example.

## Decision rule (a priori)

- **If P1 holds**: Continue.

## Runs

| Backend | Job ID |
|---|---|
| local | synthetic |

## Results

Example.

### Outcomes against preregistered predictions

| Prediction | Verdict |
|---|---|
| P1 | confirmed |

## Conclusion

Example.

## Artifacts

- `results/example.json`
""",
            encoding="utf-8",
        )
        (root / "experiments" / "README.md").write_text(
            "# Experiments\n\n- [[EXP-001-example]]\n", encoding="utf-8"
        )
        clean_experiment = experiment.read_text(encoding="utf-8")
        _, valid_issues = validate(root)
        if any(issue.level == "ERROR" for issue in valid_issues):
            for issue in valid_issues:
                print(issue.render(root))
            return 1
        experiment.write_text(
            experiment.read_text(encoding="utf-8").replace("completed", "finished"),
            encoding="utf-8",
        )
        _, invalid_issues = validate(root)
        if not any("unknown experiment status" in issue.message for issue in invalid_issues):
            print("ERROR: self-test did not detect an invalid status")
            return 1
        experiment.write_text(
            experiment.read_text(encoding="utf-8").replace("finished", "completed")
            + "\n## Estimands\n\n### E1 Example quantity\n\nNo registration line.\n",
            encoding="utf-8",
        )
        _, estimand_issues = validate(root)
        if not any("no **Registration**" in issue.message for issue in estimand_issues):
            print("ERROR: self-test did not detect an unregistered estimand")
            return 1
        experiment.write_text(clean_experiment, encoding="utf-8")

        spend_dir = root / "plans" / "spend"
        spend_dir.mkdir(parents=True)
        authority_path = spend_dir / "AUTHORITY.json"
        empty_authority = json.dumps({"schema": SPEND_AUTHORITY_SCHEMA, "plans": {}})
        authority_path.write_text(empty_authority, encoding="utf-8")
        ledger_header = "| " + " | ".join(SPEND_LEDGER_COLUMNS) + " |\n"
        ledger_separator = "|" + "---|" * len(SPEND_LEDGER_COLUMNS) + "\n"
        good_row = (
            "| S001 | 2026-09-10 | - | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00 | complete |\n"
        )
        ledger_path = spend_dir / "LEDGER.md"
        ledger_path.write_text(ledger_header + ledger_separator + good_row, encoding="utf-8")
        _, spend_issues = validate(root)
        if any(issue.level == "ERROR" for issue in spend_issues):
            for issue in spend_issues:
                print(issue.render(root))
            return 1

        short_row = "| S001 | 2026-09-10 | - | - | pilot-r1 | demo:JOB-1 | pilot | 3.00 | 2.00 |\n"
        ledger_path.write_text(ledger_header + ledger_separator + short_row, encoding="utf-8")
        _, row_issues = validate(root)
        if not any("spend ledger row has 9 cells" in issue.message for issue in row_issues):
            print("ERROR: self-test did not detect a short spend ledger row")
            return 1
        ledger_path.write_text(ledger_header + ledger_separator + good_row, encoding="utf-8")
        authority_path.write_text(
            json.dumps(
                {
                    "schema": SPEND_AUTHORITY_SCHEMA,
                    "plans": {
                        "2026-01-01-missing-plan": {
                            "shared_ceiling_usd": 5.0,
                            "authorized_by": "A. Researcher",
                            "recorded_utc": "2026-09-09T00:00:00+00:00",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        _, authority_issues = validate(root)
        if not any("names no plan" in issue.message for issue in authority_issues):
            print("ERROR: self-test did not detect an authority entry naming no plan")
            return 1
        authority_path.write_text(empty_authority, encoding="utf-8")

        experiment.write_text(
            clean_experiment.replace(
                "## Results\n\nExample.\n",
                "## Results\n\nExample. The attempt finished (exit 0, 3m42s, $0.03).\n",
            ),
            encoding="utf-8",
        )
        _, money_issues = validate(root)
        if not any("money lives in plans/spend/" in issue.message for issue in money_issues):
            print("ERROR: self-test did not detect currency in a record")
            return 1
    print("validate-notebook self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="project or notebook path")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Diagnostic output format",
    )
    parser.add_argument(
        "--write-plan-index",
        action="store_true",
        help="Regenerate plans/README.md from plan frontmatter before validation",
    )
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.path is None:
        parser.error("path is required unless --self-test is used")
    notebook = notebook_path(args.path.resolve())
    if args.write_plan_index:
        plan_dir = notebook / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "README.md").write_text(render_plan_index(notebook), encoding="utf-8")
    root, issues = validate(args.path)
    errors = sum(issue.level == "ERROR" for issue in issues)
    warnings = sum(issue.level == "WARNING" for issue in issues)
    if args.format == "json":
        print(json.dumps(diagnostics_report(root, issues, args.strict), indent=2))
        return 1 if errors or (args.strict and warnings) else 0
    for issue in issues:
        print(issue.render(root))
    if errors or (args.strict and warnings):
        print(f"{errors} error(s), {warnings} warning(s)")
        return 1
    print(f"Notebook structure valid ({warnings} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
