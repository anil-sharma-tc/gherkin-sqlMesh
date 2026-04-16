# gherkin-sqlmesh

A compiler that transforms Gherkin feature files into native SQLMesh tests and audits.

## Why

SQLMesh already has two excellent testing layers:
- **Tests** — fixture-based unit tests (YAML, input → expected output)
- **Audits** — SQL assertions that run after every model execution

This project adds a human-readable Gherkin authoring layer on top. You write `.feature` files; the compiler emits native SQLMesh YAML and SQL. No Python runtime bridge, no custom test runner — SQLMesh runs everything natively.

```
.feature → [gherkin-sqlmesh compile] → tests/*.yaml + audits/*.sql → sqlmesh test / sqlmesh audit
```

## Quickstart

```bash
pip install -e .
gherkin-sqlmesh compile features/ --out-tests sqlmesh_project/tests --out-audits sqlmesh_project/audits
cd sqlmesh_project
sqlmesh test
sqlmesh audit
```

## Example

**Input** (`features/payments.feature`):
```gherkin
Feature: Payment model integrity

  Scenario: Amount converts from cents to dollars
    Given seed_raw_payments contains:
      | id | order_id | amount |
      | 1  | 10       | 1800   |
    When stg_payments model runs
    Then output should contain:
      | payment_id | amount |
      | 1          | 18.0   |

  Scenario: Payment IDs are never null
    Given stg_payments is materialized
    Then column "payment_id" should not be null
```

**Output 1** (`tests/test_stg_payments.yaml`):
```yaml
test_stg_payments_amount_converts_from_cents_to_dollars:
  model: stg_payments
  inputs:
    seed_raw_payments:
      - id: 1
        order_id: 10
        amount: 1800
  outputs:
    partial: true
    query:
      - payment_id: 1
        amount: 18.0
```

**Output 2** (`audits/stg_payments_payment_id_not_null.sql`):
```sql
AUDIT (name assert_stg_payments_payment_id_not_null);
SELECT * FROM @this_model WHERE payment_id IS NULL;
```

## Development

This project is built strictly with TDD. See `CLAUDE.md` for the Red-Green-Refactor rules every contributor (human or AI) must follow.
