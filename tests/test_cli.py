import shutil
from pathlib import Path

import yaml
from click.testing import CliRunner

from gherkin_sqlmesh.cli import main


def test_cli_compiles_single_feature_to_output_dirs(tmp_path):
    runner = CliRunner()
    features = tmp_path / "features"
    features.mkdir()
    out_tests = tmp_path / "tests"
    out_audits = tmp_path / "audits"

    # Copy fixture feature file
    shutil.copy(
        Path(__file__).parent / "fixtures" / "features" / "payments.feature",
        features / "payments.feature",
    )

    result = runner.invoke(main, [
        "compile",
        str(features / "payments.feature"),
        "--out-tests", str(out_tests),
        "--out-audits", str(out_audits),
    ])
    assert result.exit_code == 0, result.output
    # Test YAML was written
    yaml_files = list(out_tests.glob("*.yaml"))
    assert len(yaml_files) == 1
    content = yaml.safe_load(yaml_files[0].read_text())
    key = next(iter(content.keys()))
    assert key.startswith("test_stg_payments")
    assert content[key]["model"] == "stg_payments"


def test_cli_recursively_compiles_feature_directory(tmp_path):
    runner = CliRunner()
    features = tmp_path / "features"
    features.mkdir()
    out_tests = tmp_path / "tests"
    out_audits = tmp_path / "audits"

    fixture_dir = Path(__file__).parent / "fixtures" / "features"
    shutil.copy(fixture_dir / "payments.feature", features / "payments.feature")

    result = runner.invoke(main, [
        "compile",
        str(features),
        "--out-tests", str(out_tests),
        "--out-audits", str(out_audits),
    ])
    assert result.exit_code == 0, result.output
    yaml_files = list(out_tests.glob("*.yaml"))
    assert len(yaml_files) >= 1


def test_cli_exits_nonzero_on_unknown_step_with_clear_message(tmp_path):
    runner = CliRunner()
    bad_feature = Path(__file__).parent / "fixtures" / "features" / "bad_steps.feature"
    result = runner.invoke(main, [
        "compile",
        str(bad_feature),
        "--out-tests", str(tmp_path / "tests"),
        "--out-audits", str(tmp_path / "audits"),
    ])
    assert result.exit_code != 0
    assert "the moon is full" in result.output


def test_cli_patches_model_file_with_audit_names(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    model_file = models_dir / "stg_orders.sql"
    model_file.write_text("MODEL (\n  name stg_orders,\n  kind FULL\n);\nSELECT id AS order_id FROM src\n")

    feature_file = tmp_path / "orders.feature"
    feature_file.write_text(
        "Feature: Orders\n\n"
        "  Scenario: Order IDs are never null\n"
        "    Given stg_orders is materialized\n"
        '    Then column "order_id" should not be null\n\n'
        "  Scenario: Order IDs are unique\n"
        "    Given stg_orders is materialized\n"
        '    Then column "order_id" should be unique\n'
    )

    runner = CliRunner()
    result = runner.invoke(main, [
        "compile", str(feature_file),
        "--out-tests", str(tmp_path / "tests"),
        "--out-audits", str(tmp_path / "audits"),
        "--models-dir", str(models_dir),
    ])
    assert result.exit_code == 0, result.output

    patched = model_file.read_text()
    assert "audits (" in patched
    assert "assert_stg_orders_order_id_not_null" in patched
    assert "assert_stg_orders_order_id_unique" in patched
    # SELECT logic must be preserved
    assert "SELECT id AS order_id FROM src" in patched


def test_cli_creates_model_stub_when_model_file_missing(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    feature_file = tmp_path / "orders.feature"
    feature_file.write_text(
        "Feature: Orders\n\n"
        "  Scenario: Order IDs are never null\n"
        "    Given stg_orders is materialized\n"
        '    Then column "order_id" should not be null\n'
    )

    runner = CliRunner()
    result = runner.invoke(main, [
        "compile", str(feature_file),
        "--out-tests", str(tmp_path / "tests"),
        "--out-audits", str(tmp_path / "audits"),
        "--models-dir", str(models_dir),
    ])
    assert result.exit_code == 0, result.output

    stub = (models_dir / "stg_orders.sql").read_text()
    assert "MODEL (" in stub
    assert "name stg_orders" in stub
    assert "audits (" in stub
    assert "assert_stg_orders_order_id_not_null" in stub


def test_cli_respects_dialect_flag(tmp_path):
    runner = CliRunner()
    features = tmp_path / "features"
    features.mkdir()
    out_tests = tmp_path / "tests"
    out_audits = tmp_path / "audits"

    # Write an audit-only feature
    feature_content = """Feature: Audit only

  Scenario: Payment IDs are never null
    Given stg_payments is materialized
    Then column "payment_id" should not be null
"""
    (features / "audit.feature").write_text(feature_content)

    result = runner.invoke(main, [
        "compile",
        str(features),
        "--out-tests", str(out_tests),
        "--out-audits", str(out_audits),
        "--dialect", "snowflake",
    ])
    assert result.exit_code == 0, result.output
    sql_files = list(out_audits.glob("*.sql"))
    assert len(sql_files) == 1
