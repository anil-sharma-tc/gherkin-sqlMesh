from gherkin_sqlmesh.parser import Scenario, Step
from gherkin_sqlmesh.classifier import classify, ClassificationError, UnknownStepError


def test_classify_scenario_with_only_column_assertion_is_audit():
    scenario = Scenario(
        name="Payment IDs are never null",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text='column "payment_id" should not be null'),
        ],
    )
    assert classify(scenario) == "audit"


def test_classify_scenario_with_input_fixture_and_when_step_is_test():
    scenario = Scenario(
        name="Amount converts from cents to dollars",
        steps=[
            Step(keyword="given", text="seed_raw_payments contains:", data_table=[["id","amount"],["1","1800"]]),
            Step(keyword="when", text="stg_payments model runs"),
            Step(keyword="then", text="output should contain:", data_table=[["payment_id","amount"],["1","18.0"]]),
        ],
    )
    assert classify(scenario) == "test"


def test_classify_mixed_scenario_raises_clear_error():
    scenario = Scenario(
        name="Mixed bad scenario",
        steps=[
            Step(keyword="given", text="seed_payments contains:", data_table=[["id"],["1"]]),
            Step(keyword="when", text="stg_payments model runs"),
            Step(keyword="then", text='column "id" should not be null'),
        ],
    )
    import pytest as pt
    with pt.raises(ClassificationError) as exc_info:
        classify(scenario)
    assert "split" in str(exc_info.value).lower()


def test_classify_unknown_step_raises():
    scenario = Scenario(
        name="Weird scenario",
        steps=[
            Step(keyword="given", text="the moon is full"),
        ],
    )
    import pytest as pt
    with pt.raises(UnknownStepError) as exc_info:
        classify(scenario)
    assert "the moon is full" in str(exc_info.value)
