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
    import shutil
    from pathlib import Path
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
    key = list(content.keys())[0]
    assert key.startswith("test_stg_payments")
    assert content[key]["model"] == "stg_payments"


def test_cli_recursively_compiles_feature_directory(tmp_path):
    runner = CliRunner()
    features = tmp_path / "features"
    features.mkdir()
    out_tests = tmp_path / "tests"
    out_audits = tmp_path / "audits"

    import shutil
    from pathlib import Path
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
