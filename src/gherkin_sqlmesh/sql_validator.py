"""Validate and transpile SQL portions of audit SQL strings."""

from __future__ import annotations

import sqlglot


def validate_audit_sql(sql: str, dialect: str = "duckdb") -> None:
    """Validate the SELECT portion of an audit SQL string."""
    lines = sql.strip().splitlines()
    select_sql = "\n".join(line for line in lines if not line.strip().startswith("AUDIT ("))
    sqlglot.parse_one(select_sql, dialect=dialect)


def transpile_audit_sql(sql: str, from_dialect: str, to_dialect: str) -> str:
    """Transpile the SELECT portion of an audit SQL string to a target dialect.

    The AUDIT header line is preserved unchanged; only the SELECT part is transpiled.
    """
    lines = sql.strip().splitlines()
    header_lines = [line for line in lines if line.strip().startswith("AUDIT (")]
    select_lines = [line for line in lines if not line.strip().startswith("AUDIT (")]
    select_sql = "\n".join(select_lines)
    transpiled_select = sqlglot.transpile(select_sql, read=from_dialect, write=to_dialect)[0]
    header = "\n".join(header_lines)
    return f"{header}\n{transpiled_select}"
