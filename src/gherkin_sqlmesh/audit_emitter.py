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


def _emit_unique(model: str, col: str) -> str:
    audit_name = f"assert_{model}_{col}_unique"
    sql = f"-- {audit_name}\nSELECT {col}, COUNT(*) FROM @this_model GROUP BY {col} HAVING COUNT(*) > 1;"
    _validate_sql(sql)
    return sql


def _emit_accepted_values(model: str, col: str, values: list[str]) -> str:
    audit_name = f"assert_{model}_{col}_accepted_values"
    quoted_values = ", ".join(f"'{v}'" for v in values)
    sql = f"-- {audit_name}\nSELECT * FROM @this_model WHERE {col} NOT IN ({quoted_values});"
    _validate_sql(sql)
    return sql


def _emit_row_count_gt(model: str, n: int) -> str:
    audit_name = f"assert_{model}_row_count_gt_{n}"
    sql = f"-- {audit_name}\nSELECT * FROM (SELECT COUNT(*) AS cnt FROM @this_model) WHERE cnt <= {n};"
    _validate_sql(sql)
    return sql


def _emit_row_count_eq(model: str, n: int) -> str:
    audit_name = f"assert_{model}_row_count_eq_{n}"
    sql = f"-- {audit_name}\nSELECT * FROM (SELECT COUNT(*) AS cnt FROM @this_model) WHERE cnt != {n};"
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

        # column "<col>" should be unique
        m = re.match(r'^column "(.+)" should be unique$', text)
        if m:
            col = m.group(1)
            results.append(_emit_unique(model, col))
            continue

        # column "<col>" should only contain values "v1", "v2", ...
        m = re.match(r'^column "(.+)" should only contain values (.+)$', text)
        if m:
            col = m.group(1)
            raw_values = m.group(2)
            values = re.findall(r'"([^"]+)"', raw_values)
            results.append(_emit_accepted_values(model, col, values))
            continue

        # row count should be greater than <n>
        m = re.match(r"^row count should be greater than (\d+)$", text)
        if m:
            n = int(m.group(1))
            results.append(_emit_row_count_gt(model, n))
            continue

        # row count should equal <n>
        m = re.match(r"^row count should equal (\d+)$", text)
        if m:
            n = int(m.group(1))
            results.append(_emit_row_count_eq(model, n))
            continue

    return results
