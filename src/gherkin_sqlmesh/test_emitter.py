"""Emit SQLMesh test YAML dicts from Gherkin Scenario objects."""

from __future__ import annotations

import re

from gherkin_sqlmesh.parser import Scenario


def rows_to_dicts(table: list[list[str]]) -> list[dict]:
    """Convert a data table (first row = headers) to a list of row dicts with type coercion."""
    headers = table[0]
    result = []
    for row in table[1:]:
        d = {}
        for key, val in zip(headers, row, strict=True):
            d[key] = _coerce(val)
        result.append(d)
    return result


def _coerce(value: str) -> int | float | str:
    """Try to coerce a string to int, then float, else keep as str."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def make_test_name(model: str, scenario_name: str) -> str:
    """Build the SQLMesh test key: test_<model>_<sanitized_scenario_name>."""
    sanitized = scenario_name.lower()
    sanitized = sanitized.replace(" ", "_")
    sanitized = re.sub(r"[^a-z0-9_]", "", sanitized)
    return f"test_{model}_{sanitized}"


def emit(scenario: Scenario) -> dict:
    """Emit a SQLMesh test YAML dict for the given scenario."""
    model = None
    inputs = {}
    output_rows = None
    partial = None

    for step in scenario.steps:
        kw = step.keyword
        text = step.text

        if kw in ("given", "and", "but") and text.endswith("contains:") and step.data_table:
            table_name = text[: -len(" contains:")].strip()
            inputs[table_name] = rows_to_dicts(step.data_table)

        elif kw == "when" and text.endswith("model runs"):
            model = text[: -len(" model runs")].strip()

        elif kw == "then" and text == "output should contain:" and step.data_table:
            output_rows = rows_to_dicts(step.data_table)
            partial = True

        elif kw == "then" and text == "output should equal:" and step.data_table:
            output_rows = rows_to_dicts(step.data_table)
            partial = False

    test_name = make_test_name(model, scenario.name)

    outputs: dict = {}
    if partial:
        outputs["partial"] = True
    outputs["query"] = output_rows

    return {
        test_name: {
            "model": model,
            "inputs": inputs,
            "outputs": outputs,
        }
    }
