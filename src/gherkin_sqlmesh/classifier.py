"""Classify Gherkin scenarios as unit tests or audits."""

from __future__ import annotations

from typing import Literal

from gherkin_sqlmesh.parser import Scenario


class ClassificationError(Exception):
    """Raised when a scenario mixes unit-test and audit steps."""


class UnknownStepError(Exception):
    """Raised when a scenario contains a step not in the known vocabulary."""


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

    if has_when_model_runs and has_given_contains:
        return "test"

    return "audit"
