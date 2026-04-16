"""Emit SQLMesh audit SQL files from Gherkin audit scenarios."""

from __future__ import annotations

import re

import sqlglot

from gherkin_sqlmesh.parser import Scenario


def _get_model_name(scenario: Scenario) -> str:
    """Extract model name from the 'Given <model> is materialized' step."""
    for step in scenario.steps:
        if step.keyword == "given" and step.text.endswith(" is materialized"):
            return step.text[: -len(" is materialized")]
    raise ValueError(f"No 'Given <model> is materialized' step found in scenario '{scenario.name}'")


def _validate_sql(sql: str) -> None:
    """Validate audit SQL is parseable by sqlglot (uses @this_model which sqlglot treats as a variable)."""
    sqlglot.parse_one(sql, dialect="duckdb")


def _emit_not_null(model: str, col: str) -> str:
    audit_name = f"assert_{model}_{col}_not_null"
    sql = f"-- {audit_name}\nSELECT * FROM @this_model WHERE {col} IS NULL;"
    _validate_sql(sql)
    return sql


def emit(scenario: Scenario) -> list[str]:
    """Emit a list of SQL audit strings (one per Then assertion) for the scenario."""
    model = _get_model_name(scenario)
    results = []

    for step in scenario.steps:
        if step.keyword != "then":
            continue

        text = step.text

        # column "<col>" should not be null
        m = re.match(r'^column "(.+)" should not be null$', text)
        if m:
            col = m.group(1)
            results.append(_emit_not_null(model, col))
            continue

    return results
