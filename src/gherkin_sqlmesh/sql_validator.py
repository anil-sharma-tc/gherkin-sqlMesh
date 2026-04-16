"""Validate and transpile SQL portions of audit SQL strings."""

from __future__ import annotations

import sqlglot


def validate_audit_sql(sql: str, dialect: str = "duckdb") -> None:
    """Validate the SELECT portion of an audit SQL string."""
    lines = sql.strip().splitlines()
    select_sql = "\n".join(l for l in lines if not l.strip().startswith("AUDIT ("))
    sqlglot.parse_one(select_sql, dialect=dialect)
