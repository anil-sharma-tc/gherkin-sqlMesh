# Execution Plan

This document lays out the work in stages. Each stage is small, testable, and produces a commit. Follow them in order. Do NOT skip ahead — later stages depend on the assumptions verified in earlier ones.

**Every task is phrased as "write a failing test that..." because TDD.** The implementation falls out naturally once the test exists.

---

## Stage 0 — Environment Bootstrap

**Goal:** Confirm the dev environment works before writing any code.

- [ ] `python -m venv .venv && source .venv/bin/activate`
- [ ] `pip install -e ".[dev]"`
- [ ] `pytest` — should collect 0 tests and exit 5 (no tests yet). This is expected.
- [ ] `ruff check src tests` — should pass on empty code.
- [ ] Commit: `chore: bootstrap environment`

---

## Stage 1 — Gherkin Parsing

**Goal:** Load a `.feature` file into a structured AST we control.

### 1.1 RED — Write a failing test
Create `tests/test_parser.py`. Write ONE test: `test_parse_empty_feature_returns_feature_with_no_scenarios`. It should call `gherkin_sqlmesh.parser.parse(path)` on a fixture file containing only `Feature: Empty`, and assert the returned object has `.name == "Empty"` and `.scenarios == []`.

Create the fixture: `tests/fixtures/features/empty.feature`.

Run pytest. Confirm it fails with an import error.

### 1.2 GREEN — Minimal implementation
Create `src/gherkin_sqlmesh/parser.py` with:
- A `Feature` dataclass (`name: str`, `scenarios: list[Scenario]`)
- A `Scenario` dataclass (stub for now: `name: str`, `steps: list`)
- A `parse(path: Path) -> Feature` function that uses `gherkin.parser.Parser` from `gherkin-official` and maps its output to your dataclasses.

Run pytest. Confirm GREEN. Commit.

### 1.3 RED+GREEN — One scenario, no steps
Add test: `test_parse_feature_with_one_empty_scenario`. Fixture has one scenario with no steps. Expect `len(feature.scenarios) == 1` and `feature.scenarios[0].name == "..."`.

Implement minimum to pass. Commit.

### 1.4 RED+GREEN — Steps with keywords
Add test: `test_parse_scenario_with_given_when_then_steps`. Build out `Step` dataclass (`keyword: Literal["given"|"when"|"then"|"and"|"but"]`, `text: str`, `data_table: list[list[str]] | None`).

Implement. Commit.

### 1.5 RED+GREEN — Data tables
Add test: `test_parse_step_with_data_table`. Fixture has `Given foo contains:` followed by a Gherkin table with a header row and two data rows. Assert `step.data_table` is a list of lists with the raw cell values.

Implement. Commit.

**Done when:** You can parse all the example `.feature` files in the README into your AST without losing information.

---

## Stage 2 — Scenario Classifier

**Goal:** Decide whether a scenario compiles to a test (YAML) or an audit (SQL).

### 2.1 RED+GREEN — Audit-only scenario
Test: `test_classify_scenario_with_only_column_assertion_is_audit`. Scenario has `Given X is materialized` and `Then column "y" should not be null`. Expect `classify(scenario) == "audit"`.

Create `src/gherkin_sqlmesh/classifier.py` with `classify(scenario) -> Literal["test", "audit"]`.

### 2.2 RED+GREEN — Unit test scenario
Test: `test_classify_scenario_with_input_fixture_and_when_step_is_test`. Scenario with `Given X contains: <table>`, `When Y model runs`, `Then output should contain: <table>`. Expect `"test"`.

### 2.3 RED+GREEN — Mixed scenario raises
Test: `test_classify_mixed_scenario_raises_clear_error`. Scenario with both input fixtures AND column assertions. Expect a `ClassificationError` with a message telling the user to split the scenario.

### 2.4 RED+GREEN — Unknown steps raise
Test: `test_classify_unknown_step_raises`. Scenario contains `Given the moon is full`. Expect `UnknownStepError` with the offending step text.

**Done when:** Every scenario in your fixture library classifies correctly, and bad scenarios raise clear errors.

---

## Stage 3 — Test Emitter (YAML output)

**Goal:** Convert a "test"-classified scenario into SQLMesh test YAML.

### 3.1 RED+GREEN — Minimal test YAML shape
Test: `test_emit_yaml_for_simple_test_scenario`. Given a parsed scenario, emit a dict matching SQLMesh's test format. Compare to a golden fixture in `tests/fixtures/expected/stg_payments_test.yaml`.

Create `src/gherkin_sqlmesh/test_emitter.py` with `emit(scenario) -> dict`.

### 3.2 RED+GREEN — Data table → row dicts
Test: `test_data_table_converts_to_list_of_row_dicts`. First row is headers, remaining rows become dicts keyed by headers. Strings that look like numbers get coerced (`"1800"` → `1800`, `"18.0"` → `18.0`).

### 3.3 RED+GREEN — Partial output flag
Test: `test_then_output_should_contain_sets_partial_true`. Test: `test_then_output_should_equal_omits_partial_flag`.

### 3.4 RED+GREEN — Multiple input tables
Test: `test_emit_handles_multiple_given_input_tables`.

### 3.5 RED+GREEN — Test name derived from scenario
Test: `test_test_name_is_sanitized_scenario_name`. "Amount converts from cents to dollars" → `test_stg_payments_amount_converts_from_cents_to_dollars`.

**Done when:** All example scenarios produce SQLMesh-compatible YAML that `sqlmesh test` would accept (validate later in Stage 5).

---

## Stage 4 — Audit Emitter (SQL output)

**Goal:** Convert an "audit"-classified scenario into an audit `.sql` file.

### 4.1 RED+GREEN — Not-null audit
Test: `test_emit_not_null_audit`. Scenario with `Then column "payment_id" should not be null` produces:
```sql
AUDIT (name assert_stg_payments_payment_id_not_null);
SELECT * FROM @this_model WHERE payment_id IS NULL;
```
Use sqlglot to **parse** the generated SQL to confirm it's valid syntax.

### 4.2 RED+GREEN — Uniqueness audit
Test: `test_emit_unique_audit`. Generates a `GROUP BY col HAVING COUNT(*) > 1` query.

### 4.3 RED+GREEN — Value-set audit
Test: `test_emit_accepted_values_audit`. `Then column "status" should only contain values "pending", "shipped", "delivered"` → `WHERE status NOT IN (...)`.

### 4.4 RED+GREEN — Row count audits
Tests for `row count should equal N` and `row count should be greater than N`.

### 4.5 RED+GREEN — Multiple Then steps in one scenario = multiple audits
Test: `test_scenario_with_multiple_assertions_emits_multiple_audit_files`.

**Done when:** Every audit-class scenario produces valid, sqlglot-parseable SQL that follows SQLMesh's audit file convention.

---

## Stage 5 — SQL Dialect Validation

**Goal:** Ensure generated SQL is parseable in the target dialect.

### 5.1 RED+GREEN — Default dialect is duckdb
Test: `test_audit_sql_parses_in_duckdb`. Run all generated audit SQL through `sqlglot.parse_one(sql, dialect="duckdb")`.

### 5.2 RED+GREEN — Configurable dialect
Test: `test_audit_sql_transpiles_to_snowflake`. Same audit, emitted for Snowflake dialect.

Add a `dialect` parameter to the emitter. Use sqlglot's transpile for dialect-specific output where syntax differs.

---

## Stage 6 — CLI

**Goal:** `gherkin-sqlmesh compile <features_dir>` produces output files on disk.

### 6.1 RED+GREEN — Single-file compile
Test: `test_cli_compiles_single_feature_to_output_dirs`. Use `click.testing.CliRunner`. Point at a single feature file and a temp output dir. Assert files exist with expected content.

### 6.2 RED+GREEN — Directory of features
Test: `test_cli_recursively_compiles_feature_directory`.

### 6.3 RED+GREEN — Clear error on unknown step
Test: `test_cli_exits_nonzero_on_unknown_step_with_clear_message`. The CLI should print the file, line, and offending step text.

### 6.4 RED+GREEN — `--dialect` flag
Test: `test_cli_respects_dialect_flag`.

---

## Stage 7 — End-to-End Smoke Test

**Goal:** Prove the whole thing works against a real SQLMesh project.

### 7.1 Create `examples/sushi-demo/`
- Copy the SQLMesh `sushi` example project.
- Replace its handwritten tests/audits with Gherkin features.
- Write a script `examples/sushi-demo/run.sh` that:
  1. Runs `gherkin-sqlmesh compile features/`
  2. Runs `sqlmesh test`
  3. Runs `sqlmesh audit`

### 7.2 Add a CI test
Test: `test_sushi_example_compiles_and_sqlmesh_accepts_output`. Marks as `@pytest.mark.integration` so it's opt-in.

---

## Stage 8 — Polish

- [ ] Error message quality review — every compiler error should include file, line, and a suggestion.
- [ ] README examples for every supported step.
- [ ] `docs/step-vocabulary.md` — exhaustive reference.
- [ ] `CHANGELOG.md`.
- [ ] GitHub Actions workflow: `pytest`, `ruff check`, `mypy`.

---

## Milestones

| Milestone | Stages | Target sessions |
|---|---|---|
| M1: Parser works | 1 | 1 session |
| M2: Classifier + emitters work | 2, 3, 4 | 2–3 sessions |
| M3: CLI usable end-to-end | 5, 6 | 1–2 sessions |
| M4: Real SQLMesh integration proven | 7 | 1 session |
| M5: Ship | 8 | 1 session |

Total: **~1 week of focused Claude Code sessions**.
