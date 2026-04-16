"""Classify Gherkin scenarios as unit tests or audits."""

from __future__ import annotations

from typing import Literal

from gherkin_sqlmesh.parser import Scenario


class ClassificationError(Exception):
    """Raised when a scenario mixes unit-test and audit steps."""


class UnknownStepError(Exception):
    """Raised when a scenario contains a step not in the known vocabulary."""


_AUDIT_THEN_PREFIXES = (
    'column "',
    "row count should",
)


def _is_audit_then(step_text: str) -> bool:
    return any(step_text.startswith(prefix) for prefix in _AUDIT_THEN_PREFIXES)


def classify(scenario: Scenario) -> Literal["test", "audit"]:
    """Return 'test' or 'audit' for the given scenario."""
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
