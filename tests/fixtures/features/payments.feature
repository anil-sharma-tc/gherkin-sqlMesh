Feature: Payment model integrity

  Scenario: Amount converts from cents to dollars
    Given seed_raw_payments contains:
      | id | order_id | amount |
      | 1  | 10       | 1800   |
    When stg_payments model runs
    Then output should contain:
      | payment_id | amount |
      | 1          | 18.0   |
