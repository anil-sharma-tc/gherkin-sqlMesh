Feature: Join orders with customers

  Scenario: Orders are enriched with customer names
    Given seed_raw_orders contains:
      | id | customer_id | amount |
      | 1  | 100         | 50     |
      | 2  | 101         | 75     |
    And seed_raw_customers contains:
      | id  | name  |
      | 100 | Alice |
      | 101 | Bob   |
    When stg_orders model runs
    Then output should contain:
      | order_id | customer_name | amount |
      | 1        | Alice         | 50     |
      | 2        | Bob           | 75     |
