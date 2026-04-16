from pathlib import Path

from gherkin_sqlmesh.parser import parse

FIXTURES = Path(__file__).parent / "fixtures" / "features"


def test_parse_empty_feature_returns_feature_with_no_scenarios():
    feature = parse(FIXTURES / "empty.feature")
    assert feature.name == "Empty"
    assert feature.scenarios == []


def test_parse_feature_with_one_empty_scenario():
    feature = parse(FIXTURES / "one_empty_scenario.feature")
    assert len(feature.scenarios) == 1
    assert feature.scenarios[0].name == "Does nothing"


def test_parse_scenario_with_given_when_then_steps():
    feature = parse(FIXTURES / "simple_steps.feature")
    scenario = feature.scenarios[0]
    assert len(scenario.steps) == 3
    assert scenario.steps[0].keyword == "given"
    assert scenario.steps[0].text == "some table contains data"
    assert scenario.steps[1].keyword == "when"
    assert scenario.steps[2].keyword == "then"


def test_parse_step_with_data_table():
    feature = parse(FIXTURES / "data_table.feature")
    step = feature.scenarios[0].steps[0]
    assert step.data_table is not None
    assert step.data_table[0] == ["id", "amount"]
    assert step.data_table[1] == ["1", "1800"]
    assert step.data_table[2] == ["2", "900"]
