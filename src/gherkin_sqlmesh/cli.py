"""CLI for gherkin-sqlmesh: compile Gherkin feature files to SQLMesh tests and audits."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click
import yaml

from gherkin_sqlmesh import audit_emitter, classifier, parser, test_emitter
from gherkin_sqlmesh.classifier import ClassificationError, UnknownStepError


def _audit_name_from_sql(sql: str) -> str:
    """Extract audit name from first line: AUDIT (name <name>);"""
    first_line = sql.splitlines()[0]
    m = re.search(r"AUDIT\s*\(name\s+(\S+)\)", first_line)
    if m:
        return m.group(1)
    raise ValueError(f"Could not extract audit name from: {first_line!r}")


def _compile_feature(feature_path: Path, out_tests: Path, out_audits: Path) -> bool:
    """Compile a single feature file. Returns True on success, False on error."""
    try:
        feature = parser.parse(feature_path)
    except Exception as exc:
        click.echo(f"ERROR: {feature_path}: {exc}")
        return False

    success = True
    for scenario in feature.scenarios:
        try:
            kind = classifier.classify(scenario)
        except (UnknownStepError, ClassificationError) as exc:
            click.echo(f"ERROR: {feature_path}: {exc}")
            success = False
            continue

        if kind == "test":
            result = test_emitter.emit(scenario)
            for test_name, test_data in result.items():
                out_tests.mkdir(parents=True, exist_ok=True)
                out_file = out_tests / f"{test_name}.yaml"
                out_file.write_text(yaml.dump({test_name: test_data}, sort_keys=False))
        else:
            audits = audit_emitter.emit(scenario)
            for audit_sql in audits:
                audit_name = _audit_name_from_sql(audit_sql)
                out_audits.mkdir(parents=True, exist_ok=True)
                out_file = out_audits / f"{audit_name}.sql"
                out_file.write_text(audit_sql)

    return success


@click.group()
def main() -> None:
    """gherkin-sqlmesh: compile Gherkin feature files to SQLMesh tests and audits."""


@main.command()
@click.argument("features_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--out-tests",
    required=True,
    type=click.Path(path_type=Path),
    help="Directory for test YAML files",
)
@click.option(
    "--out-audits",
    required=True,
    type=click.Path(path_type=Path),
    help="Directory for audit SQL files",
)
@click.option(
    "--dialect", default="duckdb", show_default=True, help="SQL dialect for audit generation"
)
def compile(features_path: Path, out_tests: Path, out_audits: Path, dialect: str) -> None:
    """Compile .feature file(s) to SQLMesh tests and audits."""
    if features_path.is_dir():
        feature_files = list(features_path.rglob("*.feature"))
    else:
        feature_files = [features_path]

    all_ok = True
    for feature_file in feature_files:
        ok = _compile_feature(feature_file, out_tests, out_audits)
        if not ok:
            all_ok = False

    if not all_ok:
        sys.exit(1)
