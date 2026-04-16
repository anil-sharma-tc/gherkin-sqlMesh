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


def test_emit_accepted_values_audit():
    scenario = Scenario(
        name="Status values are valid",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text='column "status" should only contain values "pending", "shipped", "delivered"'),
        ],
    )
    results = emit(scenario)
    assert len(results) == 1
    sql = results[0]
    assert "assert_stg_payments_status_accepted_values" in sql
    assert "NOT IN" in sql.upper()
    assert "'pending'" in sql
    assert "'shipped'" in sql
    assert "'delivered'" in sql
    sqlglot.parse_one(sql, dialect="duckdb")


def test_emit_row_count_greater_than_audit():
    scenario = Scenario(
        name="Has enough rows",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text="row count should be greater than 0"),
        ],
    )
    results = emit(scenario)
    sql = results[0]
    assert "assert_stg_payments_row_count_gt_0" in sql
    assert "COUNT(*)" in sql.upper()
    sqlglot.parse_one(sql, dialect="duckdb")

def test_emit_row_count_equal_audit():
    scenario = Scenario(
        name="Exactly ten rows",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text="row count should equal 10"),
        ],
    )
    results = emit(scenario)
    sql = results[0]
    assert "assert_stg_payments_row_count_eq_10" in sql
    assert "COUNT(*)" in sql.upper()
    sqlglot.parse_one(sql, dialect="duckdb")


def test_scenario_with_multiple_assertions_emits_multiple_audits():
    scenario = Scenario(
        name="Multiple checks",
        steps=[
            Step(keyword="given", text="stg_payments is materialized"),
            Step(keyword="then", text='column "payment_id" should not be null'),
            Step(keyword="then", text='column "payment_id" should be unique'),
        ],
    )
    results = emit(scenario)
    assert len(results) == 2
    assert any("not_null" in r for r in results)
    assert any("unique" in r for r in results)
