-- daily_transactions: signed transactions included on chain, per UTC day.
--
-- Table   bigquery-public-data.crypto_near_mainnet_us.transactions (partitioned on block_date)
-- Columns read: block_date (DATE) only, so this is the cheapest of the four queries.
-- Window  2026-02-13 to 2026-11-12, filtered on block_date so only these 273 days are read.
-- Cost    8 bytes a row: at 5 to 10 million transactions a day, roughly 10 to 20 GB.
--         The console shows the exact figure before you run it. Free sandbox: 1 TB a month.
-- Run     BigQuery console (sandbox: free, no card): paste, Run, then
--         "Save results" -> "CSV (local file)", saved as data/bq/daily_transactions.csv
--     or  mkdir -p data/bq && bq query --use_legacy_sql=false --format=csv --max_rows=1000 \
--           < queries/daily_transactions.sql > data/bq/daily_transactions.csv
-- Output  block_date, transactions (one row per day).
-- Note    counts every included transaction, successful or not (the status column is not read).
SELECT
  block_date,
  COUNT(*) AS transactions
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN DATE '2026-02-13' AND DATE '2026-11-12'
GROUP BY block_date
ORDER BY block_date
