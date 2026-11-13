-- intents_share: how much of NEAR's daily contract activity goes to intents.near.
--
-- Table   bigquery-public-data.crypto_near_mainnet_us.receipt_actions (partitioned on block_date)
--         One row per action inside an action receipt. index_in_action_receipt = 0 marks the first
--         action of each receipt, so counting those rows counts receipts without reading the long
--         receipt_id strings.
-- Columns read: block_date, index_in_action_receipt, action_kind, receipt_receiver_account_id.
-- Window  2026-02-13 to 2026-11-12, filtered on block_date so only these 273 days are read.
-- Cost    about 50 bytes a row. At 20 to 40 million actions a day, roughly 270 to 550 GB: the
--         largest of the four. The console shows the exact figure before you run it. The free
--         sandbox allows 1 TB a month; to halve the cost, run it twice with half the window each
--         and concatenate the two CSVs.
-- Run     BigQuery console (sandbox: free, no card): paste, Run, then
--         "Save results" -> "CSV (local file)", saved as data/bq/intents_share.csv
--     or  mkdir -p data/bq && bq query --use_legacy_sql=false --format=csv --max_rows=1000 \
--           < queries/intents_share.sql > data/bq/intents_share.csv
-- Output  block_date, receipts, intents_receipts, function_calls, intents_function_calls,
--         intents_receipt_share (one row per day).
-- Check   action_kind values follow the NEAR indexer enum ('FUNCTION_CALL', 'TRANSFER', ...). If
--         function_calls comes back 0, run SELECT DISTINCT action_kind for one day and adjust.
SELECT
  block_date,
  COUNTIF(index_in_action_receipt = 0) AS receipts,
  COUNTIF(index_in_action_receipt = 0 AND receipt_receiver_account_id = 'intents.near') AS intents_receipts,
  COUNTIF(action_kind = 'FUNCTION_CALL') AS function_calls,
  COUNTIF(action_kind = 'FUNCTION_CALL' AND receipt_receiver_account_id = 'intents.near') AS intents_function_calls,
  SAFE_DIVIDE(
    COUNTIF(index_in_action_receipt = 0 AND receipt_receiver_account_id = 'intents.near'),
    COUNTIF(index_in_action_receipt = 0)) AS intents_receipt_share
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN DATE '2026-02-13' AND DATE '2026-11-12'
GROUP BY block_date
ORDER BY block_date
