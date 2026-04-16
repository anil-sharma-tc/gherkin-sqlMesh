from gherkin_sqlmesh.audit_emitter import emit
from gherkin_sqlmesh.parser import Scenario, Step
from gherkin_sqlmesh.sql_validator import transpile_audit_sql, validate_audit_sql


def _all_audit_scenarios():
    """Return a set of audit scenarios covering all assertion types."""
    return [
        Scenario("not null", [
            Step("given", "stg_payments is materialized"),
            Step("then", 'column "payment_id" should not be null'),
        ]),
        Scenario("unique", [
            Step("given", "stg_payments is materialized"),
            Step("then", 'column "payment_id" should be unique'),
        ]),
        Scenario("accepted values", [
            Step("given", "stg_payments is materialized"),
            Step("then", 'column "status" should only contain values "pending", "shipped"'),
        ]),
        Scenario("row count gt", [
            Step("given", "stg_payments is materialized"),
            Step("then", "row count should be greater than 0"),
        ]),
        Scenario("row count eq", [
            Step("given", "stg_payments is materialized"),
            Step("then", "row count should equal 10"),
        ]),
    ]


def test_all_audit_sql_parses_in_duckdb():
    for scenario in _all_audit_scenarios():
        for sql in emit(scenario):
            validate_audit_sql(sql, dialect="duckdb")  # must not raise


def test_audit_sql_transpiles_to_snowflake():
    scenario = Scenario("not null", [
        Step("given", "stg_payments is materialized"),
        Step("then", 'column "payment_id" should not be null'),
    ])
    for sql in emit(scenario):
        snowflake_sql = transpile_audit_sql(sql, from_dialect="duckdb", to_dialect="snowflake")
        # Result should still be valid SQL with the audit header preserved
        assert "AUDIT (name" in snowflake_sql
        assert "PAYMENT_ID IS NULL" in snowflake_sql.upper()
        validate_audit_sql(snowflake_sql, dialect="snowflake")
