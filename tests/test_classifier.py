from gherkin_sqlmesh.parser import Scenario, Step
from gherkin_sqlmesh.classifier import classify


def test_classify_scenario_with_only_column_assertion_is_audit():
    scenario = Scenario(
        name="Payment IDs are never null",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text='column "payment_id" should not be null'),
        ],
    )
    assert classify(scenario) == "audit"
