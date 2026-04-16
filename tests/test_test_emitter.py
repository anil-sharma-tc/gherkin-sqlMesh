from pathlib import Path
import yaml
from gherkin_sqlmesh.parser import Scenario, Step
from gherkin_sqlmesh.test_emitter import emit, rows_to_dicts

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
