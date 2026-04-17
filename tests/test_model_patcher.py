from gherkin_sqlmesh.model_patcher import patch_model_sql


def test_injects_audits_into_model_without_audits():
    model_sql = "MODEL (\n  name stg_orders,\n  kind FULL\n);\nSELECT id FROM tbl"
    result = patch_model_sql(model_sql, ["assert_order_id_not_null"])
    assert "audits (" in result
    assert "assert_order_id_not_null" in result


def test_handles_multiple_audit_names():
    model_sql = "MODEL (\n  name stg_orders,\n  kind FULL\n);\nSELECT 1"
    result = patch_model_sql(model_sql, ["audit_a", "audit_b", "audit_c"])
    assert "audit_a" in result
    assert "audit_b" in result
    assert "audit_c" in result


def test_replaces_existing_audits():
    model_sql = "MODEL (\n  name stg_orders,\n  audits (old_audit)\n);\nSELECT id FROM tbl"
    result = patch_model_sql(model_sql, ["new_audit_a", "new_audit_b"])
    assert "new_audit_a" in result
    assert "new_audit_b" in result
    assert "old_audit" not in result


def test_patched_sql_preserves_select_logic():
    model_sql = "MODEL (\n  name stg_orders,\n  kind FULL\n);\nSELECT id AS order_id FROM src"
    result = patch_model_sql(model_sql, ["assert_not_null"])
    assert "SELECT id AS order_id FROM src" in result


def test_patched_sql_is_valid_model_block():
    model_sql = "MODEL (\n  name stg_orders,\n  kind FULL\n);\nSELECT 1"
    result = patch_model_sql(model_sql, ["assert_a", "assert_b"])
    # MODEL block must still close with );
    assert ");" in result
    # audits must be inside MODEL block, before );
    model_end = result.index(");")
    audits_pos = result.index("audits (")
    assert audits_pos < model_end
