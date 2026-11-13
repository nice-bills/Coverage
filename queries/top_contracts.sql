-- top_contracts: the 25 contracts receiving the most function calls, in the first and the last
-- 30 days of the window, so a change in rank (intents.near's in particular) is visible.
--
-- Table   bigquery-public-data.crypto_near_mainnet_us.receipt_actions (partitioned on block_date)
-- Columns read: block_date, action_kind, receipt_receiver_account_id.
-- Window  two 30-day slices of 2026-02-13 to 2026-11-12: 2026-02-13 to 2026-03-14 and
--         2026-10-14 to 2026-11-12. The WHERE clause on block_date reads only those 60 days.
-- Cost    about 45 bytes a row: at 20 to 40 million actions a day, roughly 55 to 110 GB.
--         The console shows the exact figure before you run it. Free sandbox: 1 TB a month.
-- Run     BigQuery console (sandbox: free, no card): paste, Run, then
--         "Save results" -> "CSV (local file)", saved as data/bq/top_contracts.csv
--     or  mkdir -p data/bq && bq query --use_legacy_sql=false --format=csv --max_rows=1000 \
--           < queries/top_contracts.sql > data/bq/top_contracts.csv
-- Output  period ('first_30d' or 'last_30d'), rank, contract, function_calls, share; up to 26 rows
--         a period (the top 25, plus intents.near if it ranks lower)
--         (share = the contract's function calls / all function calls in that period).
WITH calls AS (
  SELECT
    IF(block_date <= DATE '2026-03-14', 'first_30d', 'last_30d') AS period,
    receipt_receiver_account_id AS contract
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
  WHERE (block_date BETWEEN DATE '2026-02-13' AND DATE '2026-03-14'
         OR block_date BETWEEN DATE '2026-10-14' AND DATE '2026-11-12')
    AND action_kind = 'FUNCTION_CALL'
),
per_contract AS (
  SELECT period, contract, COUNT(*) AS function_calls
  FROM calls
  GROUP BY period, contract
),
ranked AS (
  SELECT
    period,
    ROW_NUMBER() OVER (PARTITION BY period ORDER BY function_calls DESC, contract) AS rank,
    contract,
    function_calls,
    function_calls / SUM(function_calls) OVER (PARTITION BY period) AS share
  FROM per_contract
)
SELECT period, rank, contract, function_calls, share
FROM ranked
WHERE rank <= 25 OR contract = 'intents.near'  -- intents.near is kept even outside the top 25
ORDER BY period, rank
