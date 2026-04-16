"""Classify Gherkin scenarios as unit tests or audits."""

from __future__ import annotations

import re
from typing import Literal

from gherkin_sqlmesh.parser import Scenario, Step


class ClassificationError(Exception):
    """Raised when a scenario mixes unit-test and audit steps."""


class UnknownStepError(Exception):
    """Raised when a scenario contains a step not in the known vocabulary."""


_AUDIT_THEN_PREFIXES = (
    'column "',
    "row count should",
)

# Known step patterns by keyword (normalized to given/when/then)
_KNOWN_GIVEN_PATTERNS = [
    re.compile(r".+ contains:$"),        # <table> contains:
    re.compile(r".+ is materialized$"),  # <model> is materialized
]

_KNOWN_WHEN_PATTERNS = [
    re.compile(r".+ model runs$"),  # <model> model runs
]

_KNOWN_THEN_PATTERNS = [
    re.compile(r"output should contain:$"),             # output should contain:
    re.compile(r"output should equal:$"),               # output should equal:
    re.compile(r'column ".+" should not be null$'),     # column "x" should not be null
    re.compile(r'column ".+" should be unique$'),       # column "x" should be unique
    re.compile(r'column ".+" should only contain values .+$'),  # column "x" should only contain values ...
    re.compile(r"row count should be greater than \d+$"),       # row count should be greater than n
    re.compile(r"row count should equal \d+$"),                 # row count should equal n
]


def _normalize_keyword(step: Step) -> str:
    """Return the effective keyword for a step (and/but inherit from context)."""
    # For now we just use the step keyword directly; and/but are handled by context
    return step.keyword


def _is_known_step(step: Step) -> bool:
    """Return True if the step matches a known vocabulary pattern."""
    kw = step.keyword
    text = step.text

    if kw in ("given", "and", "but"):
        return any(p.match(text) for p in _KNOWN_GIVEN_PATTERNS)
    if kw == "when":
        return any(p.match(text) for p in _KNOWN_WHEN_PATTERNS)
    if kw == "then":
        return any(p.match(text) for p in _KNOWN_THEN_PATTERNS)
    return False


def _is_audit_then(step_text: str) -> bool:
    return any(step_text.startswith(prefix) for prefix in _AUDIT_THEN_PREFIXES)


def classify(scenario: Scenario) -> Literal["test", "audit"]:
    """Return 'test' or 'audit' for the given scenario."""
    # Check for unknown steps first
    for step in scenario.steps:
        if not _is_known_step(step):
            raise UnknownStepError(step.text)

    has_when_model_runs = any(
        step.keyword == "when" and step.text.endswith("model runs")
        for step in scenario.steps
    )
    has_given_contains = any(
        step.keyword == "given" and step.text.endswith("contains:") and step.data_table is not None
        for step in scenario.steps
    )
    has_audit_then = any(
        step.keyword == "then" and _is_audit_then(step.text)
        for step in scenario.steps
    )

    if has_given_contains and has_audit_then:
        raise ClassificationError(
            f"Scenario '{scenario.name}' mixes unit-test input fixtures with audit "
            "assertions. Please split it into separate scenarios."
        )

    if has_when_model_runs and has_given_contains:
        return "test"

    return "audit"
