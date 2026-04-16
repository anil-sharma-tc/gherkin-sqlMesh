Feature: Payment model integrity
  The stg_payments model converts raw payment amounts from cents to dollars
  and guarantees key columns are never null.

  Scenario: Amount converts from cents to dollars
    Given seed_raw_payments contains:
      | id | order_id | payment_method | amount |
      | 1  | 10       | coupon         | 1800   |
      | 2  | 11       | credit_card    | 2600   |
    When stg_payments model runs
    Then output should contain:
      | payment_id | amount |
      | 1          | 18.0   |
      | 2          | 26.0   |

  Scenario: Payment IDs are never null
    Given stg_payments is materialized
    Then column "payment_id" should not be null

  Scenario: Payment IDs are unique
    Given stg_payments is materialized
    Then column "payment_id" should be unique

  Scenario: Payment methods are from an allowed set
    Given stg_payments is materialized
    Then column "payment_method" should only contain values "coupon", "credit_card", "bank_transfer"
