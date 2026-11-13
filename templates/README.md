# Coverage

How much of NEAR's token issuance is offset by protocol flows, and how far is break-even?

[![pages](https://github.com/nice-bills/Coverage/actions/workflows/pages.yml/badge.svg)](https://github.com/nice-bills/Coverage/actions/workflows/pages.yml)

Live dashboard, rebuilt from the chain every 6 hours: https://nice-bills.github.io/Coverage/

![The dashboard](docs/dashboard.jpg)

## Where each track requirement is met

Track: Investment Thesis ("a data-backed case for NEAR's long-term potential using onchain
analytics, dashboards and reproducible models").

| Requirement | Where | Honest note |
|---|---|---|
| Onchain analytics from public data | `fetch.py`: mint and burn from `total_supply` in block headers for every one of __EPOCHS__ epochs; buyback balance by `view_account` | Free keyless endpoints; a full rebuild takes hours because they rate-limit |
| An Intents data pull | `data/inflows.csv` (transfers into the buyback account, with senders) and `data/llama.csv` | Third-party (NearBlocks, DefiLlama). They never feed mint, burn, payback or the multiple |
| One command rebuilds every figure | `python3 run.py`, offline, under 2 seconds, prints a hash that must match this file | Rebuilds from the committed cache; `verify.py` compares the cache with mainnet |
| A dashboard: each chart, its method, one sentence | `dist/index.html`, live at the link above: every chart is titled with its finding and carries its source | One static file, no build step, no external assets |
| Reproducible models | Four, listed on the dashboard under Models with the `run.py` functions behind each | The burn forecasters' bands are too narrow (about two-thirds held against a nominal 80%); stated, not hidden |
| Claim, evidence for, evidence against, what would change our mind | [THESIS.md](THESIS.md), generated from the results | The case against has equal weight; the headline counts held buybacks, which are not burns |
| Evidence someone else can check | Result hash, tamper tests (`test_run.py`), seeded mainnet check (`verify.py`), forecast rounds timestamped in Bitcoin and scored by the chain | The rounds test that the flow persists over days. They do not test the multi-year case |

Coverage measures three flows on NEAR mainnet: NEAR minted to validators, NEAR burnt in gas fees,
and NEAR gained by `buybacks.multisignature.near`, the account that receives NEAR from the NEAR
Intents contract. Mint and burn come from block headers. It needs no API key, no cloud account
and no dependencies beyond Python 3.9+.

Since 2026-10-27 a growing share of Intents swaps settles privately (reported by another entry,
Tideline), which hides fees from public swap data. The buyback account is a mainnet balance and
still shows them: __PS_BUY__ NEAR a day since, against __PB_BUY__ in the 30 days before.

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
`out/results.json` and `dist/index.html`, and prints every headline number. Open
`dist/index.html` in a browser for the dashboard: the flows to scale, the onchain charts with
their sources, the four models, the forecast rounds and the commands on this page. Both output files are also committed, so they
can be read without running anything.

It also prints `LEDGER` lines: each frozen forecast round in `predictions/`, scored against the
cached epochs that closed after it.

## Self-test (offline, about 2 seconds)

```
python3 test_run.py
```

Expected output: `SELFTEST PASS`. It tests the scoring maths, then runs `run.py` on a copy of
the repo and confirms that (a) the result hash is unchanged once rounds are frozen, (b) a frozen
round cannot be rewritten, (c) an edited round is refused, and (d) one yoctoNEAR added to one
cached row is refused.

## Check that the prose matches the data (offline)

```
python3 docs.py --check
```

Expected output: `DOCS IN SYNC from result <first 12 characters of the hash above>`. This file,
`THESIS.md` and `SUBMISSION.md` are generated from `templates/` by `docs.py`; every measured
figure in them is filled in from `out/results.json`, so those figures cannot drift from the
data. Dates and governance facts (the buyback start date, HSP-029) are not computed here; each
is cited to its source in `THESIS.md` and is true as of 2026-11-12.

## Check the cache against the chain (network, no keys, about a minute)

```
python3 verify.py 3 12345
```

Replace `12345` with any integer you choose. For 3 randomly chosen epochs the script refetches
the epoch from NEAR mainnet and requires every cached field, and the buyback balance at the
epoch's last block, to match. It also checks on two random blocks per epoch that
`total_supply` fell by exactly the fees burnt in that block. Expected last line:

```
VERIFY seed=12345 PASS (3/3 epochs match the chain, 6 blocks checked against their parents)
```

[VERIFY.txt](VERIFY.txt) is the recorded output of one run. The free endpoints rate-limit, so a
run can pause for minutes; it waits and retries for as long as they do. Stop it with Ctrl-C at
any time.

## Score the frozen predictions (network, no keys)

```
python3 fetch.py --epochs 45
python3 run.py
```

`fetch.py` adds only epochs and balances newer than the cache. `run.py` then prints, per round
(illustrative; the committed cache was frozen at the rounds' height, so it prints `0/5`, `0/10`
and `0/20` until `fetch.py` adds the epochs that closed since):

```
LEDGER round-<height>-h10.json: 7/10 epochs closed -> PENDING
LEDGER   payback: <low> to <high>, actual None -> PENDING
```

A round is `PENDING` until all its epochs have closed, then `PASS` or `FALSIFIED`. The
`RESULT sha256` does not change when newer epochs are added, because the analysis stops at the
newest round's height; later epochs are used only for scoring.

## Rebuild the cache from the chain (slow)

```
python3 fetch.py --epochs __EPOCHS__
python3 fetch.py wallets 214890733 214933933
python3 fetch.py inflows
python3 fetch.py protocol
python3 fetch.py offchain
```

`fetch.py` skips whatever is already cached, so to rebuild from nothing move `data/` aside
first (`git checkout data/` restores it). `--epochs` counts back from the current chain tip, so
use a number at least as large as shown plus the epochs that have closed since; `run.py`
ignores epochs before or after the frozen range, so extra history does not change the result.
The third-party files (`inflows`, `offchain`) return newer rows on a later day and will change
the hash; keep the committed copies to reproduce it. A full rebuild takes several hours because the free
endpoints allow short bursts and then block for minutes. A rebuild run later also picks up
newer epochs; `run.py` uses those only for scoring.

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
| utilization | `gas_used / gas_limit` over 3 seeded random heights per epoch (a skipped height yields no block, so a few epochs have 2) | sampled |
| ceiling | `burn / mint / utilization`: burn coverage scaled to full blocks at today's effective gas price | sampled, extrapolated |

`burnt(block)` is the sum of `balance_burnt` over the chunks included at that height.

A buyback gain larger than 20 times the median of the previous 100 epochs is treated as a
transfer of revenue captured earlier. It is excluded from every figure and reported as
`lump_transfers`. The rule only looks backwards. The headline window contains
__LUMP_IN__ excluded epochs and __OUT_IN__ outflow epochs, so the headline payback does not
depend on the threshold. One epoch qualifies; `data/wallets.csv` shows
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

`data/sources.json` records, for every file in `data/`, when it was written, from which
URLs, and its sha256; `test_run.py` fails if a file does not match its recorded hash. The two header sources return identical fields and `fetch.py` alternates between them. The
third-party files never feed mint, burn, buyback gain, payback or the multiple. They are used
for sender attribution, a cross-check table, the price-based forecasting model and USD context.

## Forecasts and the outside judge

Each file in `predictions/` is a round, written by `python3 run.py freeze <epochs>` from the
newest cached epoch and never overwritten. A round commits to bands (the 5% to 95% range of past window-to-window changes) for payback, total
NEAR burnt and total NEAR gained by the buyback account over the next `<epochs>` epochs, plus
per-epoch burn forecasts from three models (`persistence`, `clock`, `price`).

__ROUNDS_TABLE__

Rule, checked by `run.py` once a round's epochs have closed:

- payback inside its interval: `PASS`; outside: `FALSIFIED`;
- the other two claims: `HIT` or `MISS`.

`out/results.json` records under `claims_backtest` how often the same procedure held at earlier
dates. Each round file has an OpenTimestamps proof beside it (`.ots`), anchoring its sha256 in
Bitcoin: `ots verify predictions/<file>.ots`. `run.py` refuses a round that is not exactly what
the code derives from the data up to that round's height.

## Files

| File | Role |
|---|---|
| `fetch.py` | chain and indexers to `data/`; resumable; needs network |
| `run.py` | `data/` to results, predictions, ledger and dashboard; offline, deterministic |
| `dashboard.py` | renders `dist/index.html`; no external assets |
| `verify.py` | spot-checks cached epochs against the chain |
| `docs.py`, `templates/` | generate this file, `THESIS.md` and `SUBMISSION.md` from the results |
| `test_run.py` | self-test and tamper checks |
| `predictions/` | the frozen forecast rounds and their OpenTimestamps proofs |
| `VERIFY.txt` | recorded output of one `verify.py` run |
| `THESIS.md` | claim, evidence for and against, what would change our mind |
| `.github/workflows/pages.yml` | rebuilds the hosted dashboard every 6 hours without changing `main` |

## Limits

- Buybacks are held by a multisig account, not burnt. They do not reduce supply and could be
  spent. Payback is a comparison of flows, not a change in supply: supply keeps growing at the
  gross issuance rate unless the held NEAR is burnt. "Break-even" here means the flows
  are equal, not that supply stops growing.
- The buyback figure covers one of three revenue wallets. The all-wallet figure is in the
  cross-check table.
- A balance change is exact, but that the NEAR was bought with fee revenue rests on NEAR's own
  description of the wallet and on the sender being `intents.near`.
- `data/wallets.csv` shows zero wNEAR for all three wallets at every height queried. That is
  what `ft_balance_of` on `wrap.near` returned; a failed call stops `fetch.py` and is never
  written as zero.
- The hosted dashboard refetches epochs and buyback balances every 6 hours. Its DefiLlama,
  price and sender sections stay at the committed snapshot.
- Utilization and the ceiling come from 3 blocks per epoch and are only meaningful as 100-epoch
  figures. The ceiling assumes today's effective gas price and is not a capacity guarantee.
- Floats in `out/results.json` are rounded to 6 significant figures so the hash does not depend
  on the platform's maths library.

## Licence

MIT. See [LICENSE](LICENSE).
