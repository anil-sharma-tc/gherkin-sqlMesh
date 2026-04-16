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
    return "audit"
