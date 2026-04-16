from pathlib import Path
import yaml
from gherkin_sqlmesh.parser import Scenario, Step
from gherkin_sqlmesh.test_emitter import emit, make_test_name, rows_to_dicts

EXPECTED = Path(__file__).parent / "fixtures" / "expected"


def test_emit_yaml_for_simple_test_scenario():
    scenario = Scenario(
        name="Amount converts from cents to dollars",
        steps=[
            Step(keyword="given", text="seed_raw_payments contains:", data_table=[
                ["id", "order_id", "amount"],
                ["1", "10", "1800"],
            ]),
            Step(keyword="when", text="stg_payments model runs"),
            Step(keyword="then", text="output should contain:", data_table=[
                ["payment_id", "amount"],
                ["1", "18.0"],
            ]),
        ],
    )
    result = emit(scenario)
    expected = yaml.safe_load((EXPECTED / "test_stg_payments_amount_converts.yaml").read_text())
    assert result == expected


def test_data_table_converts_to_list_of_row_dicts():
    table = [["id", "amount", "label"], ["1", "18.0", "foo"]]
    result = rows_to_dicts(table)
    assert result == [{"id": 1, "amount": 18.0, "label": "foo"}]


def test_then_output_should_contain_sets_partial_true():
    scenario = Scenario(
        name="Partial check",
        steps=[
            Step(keyword="given", text="t contains:", data_table=[["a"],["1"]]),
            Step(keyword="when", text="m model runs"),
            Step(keyword="then", text="output should contain:", data_table=[["a"],["1"]]),
        ],
    )
    result = emit(scenario)
    test = list(result.values())[0]
    assert test["outputs"]["partial"] is True


def test_then_output_should_equal_omits_partial_flag():
    scenario = Scenario(
        name="Full check",
        steps=[
            Step(keyword="given", text="t contains:", data_table=[["a"],["1"]]),
            Step(keyword="when", text="m model runs"),
            Step(keyword="then", text="output should equal:", data_table=[["a"],["1"]]),
        ],
    )
    result = emit(scenario)
    test = list(result.values())[0]
    assert "partial" not in test["outputs"]


def test_emit_handles_multiple_given_input_tables():
    scenario = Scenario(
        name="Multi input",
        steps=[
            Step(keyword="given", text="table_a contains:", data_table=[["x"],["1"]]),
            Step(keyword="given", text="table_b contains:", data_table=[["y"],["2"]]),
            Step(keyword="when", text="my_model model runs"),
            Step(keyword="then", text="output should contain:", data_table=[["x"],["1"]]),
        ],
    )
    result = emit(scenario)
    test = list(result.values())[0]
    assert "table_a" in test["inputs"]
    assert "table_b" in test["inputs"]


def test_test_name_is_sanitized_scenario_name():
    name = make_test_name("stg_payments", "Amount converts from cents to dollars")
    assert name == "test_stg_payments_amount_converts_from_cents_to_dollars"
