# Coverage

How much of NEAR's token issuance is offset by protocol flows, and how far is break-even?

Coverage measures three flows on NEAR mainnet: NEAR minted to validators, NEAR burnt in gas fees,
and NEAR gained by `buybacks.multisignature.near`, the account that receives NEAR from the NEAR
Intents contract. Mint and burn come from block headers. It needs no API key, no cloud account
and no dependencies beyond Python 3.9+.

Result for the 100 epochs ending __LAST__: burn plus buybacks equal __PAYBACK__ of issuance
(burn alone: __BURN_COV__). The thesis, the evidence against it and what would change our mind
are in [THESIS.md](THESIS.md).

## Reproduce (offline, under 2 seconds)

```
python3 run.py
```

Expected last line:

```
RESULT sha256=__RESULT_HASH__
```

The command reads the files in `data/`, checks that the cached epochs chain together, writes
`out/results.json`, `out/predictions.json` and `dist/index.html`, and prints every headline
number. Open `dist/index.html` in a browser for the dashboard. The three output files are also
committed, so they can be read without running anything.

Because `predictions.json` is committed, the command also prints `LEDGER` lines: the frozen
forecasts scored against any cached epochs newer than height __LAST_HEIGHT__.

## Self-test (offline, about 2 seconds)

```
python3 test_run.py
```

Expected output: `SELFTEST PASS`. It tests the scoring maths, then runs `run.py` on a copy of
the repo and confirms that (a) the result hash is unchanged once predictions are frozen, (b) an
edited `predictions.json` is refused, and (c) one yoctoNEAR added to one cached row is refused.

## Check the cache against the chain (network, no keys, about a minute)

```
python3 verify.py 3 12345
```

Replace `12345` with any integer you choose. For 3 randomly chosen epochs the script refetches
the epoch from NEAR mainnet and requires every cached field, and the buyback balance at the
epoch's last block, to match. It also checks on two random blocks per epoch that
`total_supply` fell by exactly the fees burnt in that block. Expected last line:

```
VERIFY seed=12345 PASS (3/3 epochs match the chain)
```

[VERIFY.txt](VERIFY.txt) is the recorded output of one run. The free endpoints rate-limit, so a
run can pause for a minute or two; it retries on its own.

## Score the frozen predictions (network, no keys)

```
python3 fetch.py --epochs 45
python3 run.py
```

`fetch.py` adds only epochs and balances newer than the cache. `run.py` then prints lines such as:

```
LEDGER 12/30 epochs resolved, 10 in interval, loss {...} -> PENDING
LEDGER claim payback: 0.08 to 0.19, actual None -> PENDING
```

The verdict is `PENDING` until 30 epochs have closed, then `PASS` or `FALSIFIED`. The
`RESULT sha256` does not change when newer epochs are added, because the analysis is frozen at
the height recorded in `predictions.json`; newer epochs are used only for scoring.

## Rebuild the cache from the chain (slow)

```
python3 fetch.py --epochs __EPOCHS__
python3 fetch.py wallets 214890733 214933933
python3 fetch.py inflows
python3 fetch.py protocol
python3 fetch.py offchain
```

`fetch.py` skips whatever is already cached, so to rebuild from nothing move `data/` aside
first (`git checkout data/` restores it). A full rebuild takes several hours because the free
endpoints allow short bursts and then block for minutes. A rebuild run later also picks up
newer epochs; `run.py` uses those only for scoring. `inflows` and `offchain` read third-party
indexers and return newer rows on a later day.

## What is measured

Every NEAR block header carries `total_supply`. Within an epoch it falls by exactly the fees
burnt in that block; at the first block of an epoch it also rises by the newly minted reward.

| Quantity | Definition | Exact? |
|---|---|---|
| mint | `supply(first block) - supply(last block of previous epoch) + burnt(first block)` | yes, integer yoctoNEAR |
| burn | `burnt(first block) + supply(first block) - supply(last block)` | yes, integer yoctoNEAR |
| buyback gain | change in the NEAR balance of `buybacks.multisignature.near` between epoch ends | yes, as a balance change |
| payback | `(burn + buyback gain) / mint` | yes |
| multiple | `mint / (burn + buyback gain)`: growth in those flows that equals issuance | yes |
| utilization | `gas_used / gas_limit` over 3 seeded random blocks per epoch | sampled |
| ceiling | `burn / mint / utilization`: burn coverage scaled to full blocks at today's effective gas price | sampled, extrapolated |

`burnt(block)` is the sum of `balance_burnt` over the chunks included at that height.

A buyback gain larger than 20 times the median of the previous 100 epochs is treated as a
transfer of revenue captured earlier. It is excluded from every figure and reported as
`lump_transfers`. The rule only looks backwards. One epoch qualifies; `data/wallets.csv` shows
the other revenue wallets falling by nearly the same amount across it.

What the internal check does and does not prove: `run.py` requires each epoch to begin at the
height and supply where the previous one ended, and each row's `mint - burn` to equal its
supply change. That catches gaps, reordering and single edited values. It cannot catch a row
that is wrong in a self-consistent way; `verify.py` compares rows with the chain for that.

## Data

| File | Content | Source | Key |
|---|---|---|---|
| `data/epochs.csv` | one row per epoch: heights, timestamps, supply, mint, burn, gas sample | `block` on `archival-rpc.mainnet.fastnear.com`; `/v0/block/{h}/headers` on `mainnet.neardata.xyz` | none |
| `data/buybacks.csv` | buyback account balance at each epoch end | `query view_account` on the same RPC | none |
| `data/wallets.csv` | NEAR and wNEAR in all three revenue wallets at selected heights | `view_account`, `ft_balance_of` on `wrap.near` | none |
| `data/protocol.json` | protocol parameters cited in the thesis | `EXPERIMENTAL_protocol_config` | none |
| `data/inflows.csv` | recent transfers into the buyback account, with sender and transaction hash | NearBlocks API (third party) | none |
| `data/llama.csv` | daily USD: NEAR fees, NEAR Intents volume, fees, captured revenue | DefiLlama API (third party) | none |
| `data/price.csv` | daily NEAR price in USD | CoinGecko API (third party) | none |

The two header sources return identical fields and `fetch.py` alternates between them. The
third-party files never feed mint, burn, buyback gain, payback or the multiple. They are used
for sender attribution, a cross-check table, the price-based forecasting model and USD context.

## Forecasts and the outside judge

`predictions.json` commits to three claims about the 30 epochs after height __LAST_HEIGHT__:
payback (90% interval), total NEAR burnt (90%) and total NEAR gained by the buyback account
(90%). Each interval is the last 30-epoch value scaled by how much consecutive 30-epoch windows
have differed historically. `out/results.json` records, under `claims_backtest`, how often the
same procedure held when run at earlier dates.

Rule, checked by `run.py` once 30 epochs have closed:

- payback inside its interval: `PASS`; outside: `FALSIFIED`;
- the other two claims: `HIT` or `MISS`.

`predictions.json` also holds per-epoch burn forecasts from three models (`persistence`, `clock`,
`price`), scored with pinball loss as epochs close. The same three are compared on history in
the dashboard.

Its sha256 is `__PRED_HASH__`, published before the epochs it predicts had closed (see
[THESIS.md](THESIS.md)). `run.py` refuses to score unless the file is byte-for-byte what the
code derives from the frozen data, so the method is frozen with the numbers.

## Files

| File | Role |
|---|---|
| `fetch.py` | chain and indexers to `data/`; resumable; needs network |
| `run.py` | `data/` to results, predictions, ledger and dashboard; offline, deterministic |
| `dashboard.py` | renders `dist/index.html`; no external assets |
| `verify.py` | spot-checks cached epochs against the chain |
| `test_run.py` | self-test and tamper checks |
| `predictions.json` | the frozen forecasts |
| `VERIFY.txt` | recorded output of one `verify.py` run |
| `THESIS.md` | claim, evidence for and against, what would change our mind |
| `.github/workflows/pages.yml` | rebuilds the hosted dashboard every 6 hours without changing `main` |

## Limits

- Buybacks are held by a multisig account, not burnt. They do not reduce supply and could be
  spent. Payback counts them as a flow that offsets issuance.
- The buyback figure covers one of three revenue wallets. The all-wallet figure is in the
  cross-check table.
- A balance change is exact, but that the NEAR was bought with fee revenue rests on NEAR's own
  description of the wallet and on the sender being `intents.near`.
- Utilization and the ceiling come from 3 blocks per epoch and are only meaningful as 100-epoch
  figures. The ceiling assumes today's effective gas price and is not a capacity guarantee.
- Floats in `out/results.json` are rounded to 6 significant figures so the hash does not depend
  on the platform's maths library.

## Licence

MIT. See [LICENSE](LICENSE).
