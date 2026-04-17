Feature: Orders model integrity
  The stg_orders model derives order status from raw order data
  and ensures key columns meet data quality standards.

  Scenario: Order status is derived correctly
    Given seed_raw_orders contains:
      | id | customer_id | status    |
      | 1  | 42          | placed    |
      | 2  | 43          | shipped   |
      | 3  | 44          | completed |
    When stg_orders model runs
    Then output should contain:
      | order_id | customer_id | status    |
      | 1        | 42          | placed    |
      | 2        | 43          | shipped   |
      | 3        | 44          | completed |

  Scenario: Order IDs are never null
    Given stg_orders is materialized
    Then column "order_id" should not be null

  Scenario: Order IDs are unique
    Given stg_orders is materialized
    Then column "order_id" should be unique

  Scenario: Order status is from an allowed set
    Given stg_orders is materialized
    Then column "status" should only contain values "placed", "shipped", "completed", "return_pending", "returned"

  Scenario: There is at least one order
    Given stg_orders is materialized
    Then row count should be greater than 0
