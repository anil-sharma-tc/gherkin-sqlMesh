"""Patch SQLMesh MODEL SQL files to inject the audits(...) property."""

from __future__ import annotations

import re


def patch_model_sql(model_sql: str, audit_names: list[str]) -> str:
    """Add or replace the audits(...) property in a SQLMesh MODEL block."""
    audit_list = ",\n    ".join(audit_names)
    audits_clause = f"audits (\n    {audit_list}\n  )"

    if re.search(r"\baudits\s*\(", model_sql, re.IGNORECASE):
        return re.sub(
            r"\baudits\s*\([^)]*\)",
            audits_clause,
            model_sql,
            count=1,
            flags=re.IGNORECASE,
        )

    def _inject(m: re.Match) -> str:
        interior = m.group(2).rstrip().rstrip(",")
        return m.group(1) + interior + ",\n  " + audits_clause + "\n" + m.group(3)

    return re.sub(
        r"(MODEL\s*\()(.*?)(\);)",
        _inject,
        model_sql,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
