# CLAUDE.md — Instructions for Claude Code

You are working on **gherkin-sqlmesh**, a compiler that transforms Gherkin `.feature` files into native SQLMesh test YAML and audit SQL files.

## 🚨 TDD IS MANDATORY — NO EXCEPTIONS

Every piece of functionality MUST follow Red-Green-Refactor. This is non-negotiable.

### The Rules

1. **RED** — Write a failing test first. Do NOT write implementation code.
2. **Run the test** — Confirm it fails for the expected reason. If it passes or errors for the wrong reason, fix the test first.
3. **GREEN** — Write the MINIMUM code needed to pass the test. No extras. No "while I'm here" additions.
4. **Run the full test suite** — Confirm all tests pass.
5. **REFACTOR** — Clean up if needed. Tests must still pass after refactoring.
6. **Commit** — One red-green-refactor cycle = one commit.

### What This Means in Practice

- ❌ **Never write a function before its test exists.**
- ❌ **Never write more than one failing test at a time** (outside of committing the RED phase).
- ❌ **Never add "obvious" helper functions without a test that forces them into existence.**
- ✅ **If you feel the urge to write implementation first, STOP.** Write the test.
- ✅ **If a test feels trivial, still write it.** Trivial tests catch real bugs during refactors.

### The PostToolUse hook enforces this

After every file edit, pytest runs automatically. If you see failing tests you didn't expect, do NOT "fix" them by changing the tests — understand why they fail.

## Project Overview

**Input:** Gherkin `.feature` files using a specific Given/When/Then vocabulary for SQL.
**Output:** SQLMesh-native `tests/*.yaml` (unit tests) and `audits/*.sql` (data quality assertions).

**No Python runtime bridge.** The compiler runs once; SQLMesh runs the tests natively.

## Stack

- **Python 3.11+**
- **pytest** — test framework
- **gherkin-official** — Gherkin parser (don't write one from scratch)
- **sqlglot** — SQL parsing, validation, and dialect-aware generation
- **PyYAML** — YAML generation for SQLMesh test files
- **click** — CLI framework
- **ruff** — linting + formatting

## Architecture

```
┌─────────────────┐
│  .feature file  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  gherkin.parser         │  ← gherkin-official library
│  → AST                  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  step_classifier        │  ← Is this scenario a unit test or an audit?
│  → "test" | "audit"     │
└────────┬────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌─────────┐
│ test_  │ │ audit_  │
│ emitter│ │ emitter │
└───┬────┘ └────┬────┘
    │           │
    ▼           ▼
┌────────────────────────┐
│  sqlglot validation    │  ← Make sure generated SQL parses
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  File writers          │
│  → tests/*.yaml        │
│  → audits/*.sql        │
└────────────────────────┘
```

## Step Vocabulary (v1 scope)

### Unit-test-style steps (emit YAML test files)

- `Given <table> contains: <data_table>` → input fixture
- `When <model> model runs` → model under test
- `Then output should contain: <data_table>` → expected partial output
- `Then output should equal: <data_table>` → expected full output (not partial)

### Audit-style steps (emit SQL audit files)

- `Given <model> is materialized` → context only (no-op in audit)
- `Then column "<col>" should not be null`
- `Then column "<col>" should be unique`
- `Then column "<col>" should only contain values <list>`
- `Then row count should be greater than <n>`
- `Then row count should equal <n>`

Scenarios containing `When ... runs` compile to **tests**.
Scenarios with only `Given <model> is materialized` + `Then ...` compile to **audits**.

## Classification Rule (important)

A scenario is a **unit test** if it contains:
- A `When <model> model runs` step, AND
- At least one `Given <table> contains:` step with a data table

Otherwise it is an **audit**.

Mixed scenarios (input fixtures AND column assertions) should raise a clear compiler error telling the user to split them.

## Testing Strategy

Tests live in `tests/`. Organized by module:

- `tests/test_parser.py` — parsing `.feature` files into AST
- `tests/test_classifier.py` — scenario → "test" vs "audit" decision
- `tests/test_test_emitter.py` — AST → SQLMesh test YAML
- `tests/test_audit_emitter.py` — AST → audit SQL
- `tests/test_sql_validation.py` — sqlglot parses all generated SQL
- `tests/test_cli.py` — end-to-end CLI behavior
- `tests/fixtures/features/*.feature` — input fixtures
- `tests/fixtures/expected/*.yaml` / `*.sql` — golden output fixtures

**Golden-file testing:** For the emitters, prefer comparing against fixture files in `tests/fixtures/expected/`. Easier to review in diffs.

## Commit Discipline

- One commit per red-green-refactor cycle.
- Commit messages: `red: <what fails>`, `green: <what passes>`, `refactor: <what changed>`.
- Squash before merging to main if desired, but keep the discipline visible during development.

## What NOT to Do

- ❌ Don't add features not yet in the step vocabulary above. If a scenario uses an unknown step, the compiler should emit a clear error.
- ❌ Don't try to run SQLMesh from Python at compile time. The compiler's output is static files; SQLMesh runs them later.
- ❌ Don't add dependencies without a test that needs them.
- ❌ Don't write "future-proofing" code. YAGNI applies hard here.

## Reference Docs

- SQLMesh tests: https://sqlmesh.readthedocs.io/en/stable/concepts/tests/
- SQLMesh audits: https://sqlmesh.readthedocs.io/en/latest/concepts/audits/
- Gherkin reference: https://cucumber.io/docs/gherkin/reference/
- SQLGlot: https://sqlglot.com/
