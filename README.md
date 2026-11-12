# Coverage

How much of NEAR's token issuance does fee burn pay back, and how far is break-even?

Coverage answers that from NEAR mainnet block headers alone. It needs no API key, no cloud account
and no dependencies beyond Python 3.9+. The thesis, the evidence against it and the result that
would change our mind are in [THESIS.md](THESIS.md).

## Reproduce (offline, about 1 second)

```
python3 run.py
```

Expected last line:

```
RESULT sha256=__RESULT_HASH__
```

The command reads `data/epochs.csv` and `data/price.csv`, asserts the supply identity below,
writes `out/results.json`, `out/predictions.json` and `dist/index.html`, and prints the headline
numbers. Open `dist/index.html` in a browser for the dashboard.

## Check the cache against the chain (network, no keys, under a minute)

```
python3 verify.py 3 12345
```

Replace `12345` with any integer you choose. The script refetches 3 randomly chosen epochs from
NEAR mainnet and requires every field to equal the cached row. Expected last line:

```
VERIFY seed=12345 PASS (3/3 epochs match the chain)
```

## Score the frozen predictions (network, no keys)

```
python3 fetch.py --epochs 45
python3 run.py
```

`fetch.py` adds only epochs newer than the cache. `run.py` then prints a line such as:

```
LEDGER 12/30 epochs resolved, 10 in interval, loss {...} -> PENDING
```

The verdict is `PENDING` until 30 epochs have closed, then `PASS` or `FALSIFIED`. The
`RESULT sha256` does not change, because the analysis is frozen at the height recorded in
`predictions.json`.

## Self-test

```
python3 test_run.py
```

Expected output: `SELFTEST PASS`.

## Rebuild the cache from the chain (slow)

```
rm data/epochs.csv
python3 fetch.py --epochs __EPOCHS__
```

This takes about 3 hours because the free endpoints rate-limit. It produces the same file.

## What is measured

Every NEAR block header carries `total_supply`. Within an epoch it falls by exactly the fees
burnt in that block; at the first block of an epoch it also rises by the newly minted reward.
So for each epoch:

| Quantity | Definition | Exact? |
|---|---|---|
| mint | `supply(first block) - supply(last block of previous epoch) + burnt(first block)` | yes, integer yoctoNEAR |
| burn | `burnt(first block) + supply(first block) - supply(last block)` | yes, integer yoctoNEAR |
| coverage | `burn / mint` | yes |
| utilization | `gas_used / gas_limit` over 3 seeded random blocks per epoch | sampled |
| ceiling | `coverage / utilization`: coverage if every block were full at today's effective gas price | sampled |
| multiple | `mint / burn`: how many times current burn offsets issuance | yes |

`burnt(block)` is the sum of `balance_burnt` over the chunks included at that height.
`run.py` asserts, across the whole cache, that

```
supply(last epoch end) - supply(first epoch start) == sum(mint - burn)
```

to the yoctoNEAR. If one cached number were wrong the command would fail.

## Data sources

| Data | Source | Key |
|---|---|---|
| Block headers by height or hash | `https://archival-rpc.mainnet.fastnear.com` (`block` RPC) | none |
| Block headers by height | `https://mainnet.neardata.xyz/v0/block/{height}/headers` | none |
| Daily NEAR price, 365 days | `https://api.coingecko.com/api/v3/coins/near/market_chart` | none |

The two header sources return identical fields and `fetch.py` alternates between them. Price is
the only off-chain input. It is used only by the rival forecasting model, never by the headline
numbers.

## Forecasts and the outside judge

`run.py` forecasts burn per epoch 30 epochs ahead with three models and scores them walk-forward
on history with pinball loss at the 10%, 50% and 90% quantiles:

| Model | Uses |
|---|---|
| `persistence` | mean of the last 30 epochs |
| `usage` | level of the last 30 epochs plus a time-of-week profile; no price |
| `price` | regression of burn on NEAR price only |

`predictions.json` holds the forecasts for the 30 epochs after the cache ends. Its sha256 was
published before those epochs existed (see [THESIS.md](THESIS.md) for where). `run.py` refuses to
score unless `predictions.json` is byte-for-byte what the code derives from the frozen data, so
neither the numbers nor the method can be changed after the fact.

Pre-registered rule, checked by `run.py` once 30 epochs have closed:

- `usage` has lower pinball loss than `price`, and
- between 20 and 28 of the 30 outcomes fall inside the `usage` 80% interval.

Both hold: `PASS`. Either fails: `FALSIFIED`, printed by the command and shown on the dashboard.

## Files

| File | Role |
|---|---|
| `fetch.py` | chain to `data/epochs.csv`; resumable; network |
| `run.py` | cache to results, predictions, ledger and dashboard; offline, deterministic |
| `dashboard.py` | renders `dist/index.html`; no external assets |
| `verify.py` | spot-checks cached epochs against the chain |
| `test_run.py` | self-test of the scoring maths |
| `data/epochs.csv` | one row per epoch, integers only |
| `data/price.csv` | daily NEAR price in USD |
| `predictions.json` | the frozen forecasts |
| `.github/workflows/pages.yml` | rebuilds the hosted dashboard every 6 hours without touching `main` |

## Limits

- Utilization and ceiling come from 3 blocks per epoch, so they are only meaningful as 100-epoch
  rolling figures (300 blocks). Mint, burn, coverage and multiple are exact.
- The ceiling assumes today's effective gas price. The protocol can raise the price under
  congestion; that is not modelled.
- The free endpoints allow short bursts and then block for minutes. Everything except
  `fetch.py` and `verify.py` works offline.
- Floats in `out/results.json` are rounded to 6 significant figures so the hash does not depend
  on the platform's maths library.

## Licence

MIT. See [LICENSE](LICENSE).
