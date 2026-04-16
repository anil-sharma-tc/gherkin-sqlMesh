import sqlglot
from gherkin_sqlmesh.parser import Scenario, Step
from gherkin_sqlmesh.audit_emitter import emit


def test_emit_not_null_audit():
    scenario = Scenario(
        name="Payment IDs are never null",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text='column "payment_id" should not be null'),
        ],
    )
    results = emit(scenario)
    assert len(results) == 1
    sql = results[0]
    assert "assert_stg_payments_payment_id_not_null" in sql
    assert "payment_id IS NULL" in sql
    # Validate SQL is parseable
    sqlglot.parse_one(sql, dialect="duckdb")


def test_emit_unique_audit():
    scenario = Scenario(
        name="Payment IDs are unique",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text='column "payment_id" should be unique'),
        ],
    )
    results = emit(scenario)
    assert len(results) == 1
    sql = results[0]
    assert "assert_stg_payments_payment_id_unique" in sql
    assert "GROUP BY" in sql.upper()
    assert "HAVING" in sql.upper()
    sqlglot.parse_one(sql, dialect="duckdb")
