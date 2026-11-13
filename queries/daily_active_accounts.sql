-- daily_active_accounts: accounts that signed at least one transaction, per UTC day.
--
-- Table   bigquery-public-data.crypto_near_mainnet_us.transactions (partitioned on block_date)
-- Columns read: block_date (DATE), signer_account_id (STRING). Nothing else is scanned.
-- Window  2026-02-13 to 2026-11-12, the same days as the repo's chain window; the WHERE clause
--         on block_date prunes partitions, so only these 273 days are read.
-- Cost    BigQuery bills the bytes of the columns read. Measured on 2026-11-13 (dry run): 9.6 GB.
--         The console shows the exact figure ("This query will process ...") before you run it.
--         All four queries together scanned 122 GB; the free sandbox allows 1 TB a month.
-- Run     BigQuery console (sandbox: free, no card): paste, Run, then
--         "Save results" -> "CSV (local file)", saved as data/bq/daily_active_accounts.csv
--     or  mkdir -p data/bq && bq query --use_legacy_sql=false --format=csv --max_rows=1000 \
--           < queries/daily_active_accounts.sql > data/bq/daily_active_accounts.csv
-- Output  block_date, active_accounts (one row per day). Read by bq.py; nothing else edits it.
-- Schema  column names from the dataset's published schema; if the console reports an unknown
--         column, check the table's Schema tab (signer_account_id is the transaction signer).
SELECT
  block_date,
  COUNT(DISTINCT signer_account_id) AS active_accounts
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN DATE '2026-02-13' AND DATE '2026-11-12'
GROUP BY block_date
ORDER BY block_date
