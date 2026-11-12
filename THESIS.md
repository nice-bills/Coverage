# Thesis: NEAR's token flow moved to the application layer, and break-even is single-digit multiples away

Every figure in this file is printed by `python3 run.py` (no keys, no network) and stored in
`out/results.json`. Figures are for the last 100 epochs, about 28 days, ending __LAST__ at
height __LAST_HEIGHT__, unless a different period is stated.

## Claim

NEAR mints about 2.5% of its supply a year to validators. The usual question is how much of that
the gas-fee burn gives back. The answer from the chain is __BURN_COV__, which puts break-even
__BURN_MULT__ times away.

That measures one layer. Since 23 February 2026 the NEAR Intents contract has been sending NEAR
to `buybacks.multisignature.near`, the wallet NEAR names for buybacks funded by Intents fee
revenue.

| Flow | NEAR a day | Share of mint |
|---|---|---|
| Minted to validators (exact) | __MINT__ | 100% |
| Burnt in gas fees (exact) | __BURN__ | __BURN_COV__ |
| Gained by the buyback account (exact balance change) | __BUY__ | __BUY_COV__ |
| **Payback: burn plus buyback gain** | | **__PAYBACK__** |

The thesis has three parts:

1. Burn plus buybacks equal __PAYBACK__ of issuance, not __BURN_COV__. Break-even is
   __MULT__x away, not __BURN_MULT__x. "Payback" is our name for that ratio; buybacks are held,
   not destroyed (see Evidence against).
2. More than nine-tenths of the payback comes from application revenue, not gas. The token's
   flow is tied to NEAR Intents fees, not to block space.
3. The gap can narrow through levers NEAR governance controls: the share of Intents fees that
   reaches the buyback account, and the issuance rate.

## Evidence for

**Mint and burn are read from the chain, and anyone can recheck them.** Both come from
`total_supply` in block headers. `python3 verify.py 3 <seed>` refetches random epochs from
mainnet, requires every cached field to match, and checks on random blocks that supply fell by
exactly the fees burnt in that block. `VERIFY.txt` records one such run. `run.py` also refuses a
cache whose epochs do not chain together in height and supply; that check catches gaps and
edits, but it is the chain comparison, not the internal check, that establishes correctness.

**The inflows come from the NEAR Intents contract.** Of the last __INFLOW_N__ transfers into the
buyback account, __INFLOW_INTENTS__ were sent by `intents.near`, carrying __INFLOW_SHARE__ of
the NEAR (`data/inflows.csv`, from the NearBlocks indexer, with transaction hashes).

**A separate pipeline gives the same total.** DefiLlama computes NEAR's captured Intents revenue
from Dune tables across three revenue wallets. Converted at each day's price it is
__LLAMA_BUY_NEAR__ NEAR a day over the same days. Balance changes of those three wallets, read
with 12 RPC calls, give __ALL_NEAR__ NEAR a day. The thesis uses only the buyback wallet,
__BUY__ NEAR a day, which is the lower figure.

**Realized inflation matches stated policy.** Measured mint annualizes to __INFL__ of supply
over the whole cache; the protocol config has `max_inflation_rate` at 1/40
(`data/protocol.json`). Net of payback it is __NET_INFL__.

**The capture lever is large.** Gross NEAR Intents fees run at __FEES_USD__ a day (DefiLlama).
The buyback account receives about __CAPTURE__ of that. If all of it arrived, at today's
volume, payback would be __LEVER__.

**Burn has headroom on paper.** Sampled blocks are __UTIL__ full. Scaling today's burn to full
blocks at today's effective gas price gives __CEIL__ of issuance (90% bootstrap range
__CEIL_LO__ to __CEIL_HI__). This is an extrapolation from 300 sampled blocks, not a capacity
guarantee.

**Price does not explain burn.** In a walk-forward backtest of burn per epoch
(__BT_N__ forecasts), a model that adds NEAR's price to the recent level scores
__BT_PRICE__ pinball loss against __BT_PERSIST__ for the recent level alone. A model that adds
a time-of-week profile scores __BT_CLOCK__. Neither addition is a clear improvement, so at this
horizon burn behaves like a noisy level, not like a function of the token price.

## Evidence against

**Buybacks are not burns.** The NEAR sits in a multisig account. Supply does not fall, and the
key holders can spend or sell it. If the balance starts falling, the flow does not mean what
this thesis takes it to mean.

**Payback has been falling.** The first 100-epoch window with buyback data (ending
__PAY_FIRST_DATE__) shows __PAY_FIRST__; the peak is __PAY_PEAK__ (__PAY_PEAK_DATE__); the
latest is __PAYBACK__. The history is too short to fit a trend.

**NEAR Intents is not growing.** Comparing the first and last 30 days of the year to __LAST__
(DefiLlama): daily Intents volume is __VOL_RATIO__x, gross Intents fees __FEE_RATIO__x, and
NEAR gas fees in USD __GAS_RATIO__x. The buyback flow exists because capture was switched on
in February 2026, not because the business grew. At today's capture share, break-even needs
__MULT__x the volume.

**The payback is concentrated.** One application supplies over 90% of it. A fee cut, exploit
or loss of flow at NEAR Intents removes most of the thesis.

**Burn alone is far from break-even.** __BURN_COV__ of issuance, __BURN_MULT__x away.

**The history is short and needed one exclusion.** Buybacks began on 2026-02-23. One gain of
__LUMP__ NEAR was excluded by a mechanical rule (more than 20 times the median of the previous
100 epochs). The chain shows what it was: across that epoch, heights 214890733 to 214933933,
the other two revenue wallets fell by __LUMP_OUT__ NEAR (`data/wallets.csv`). That is revenue
captured earlier moving between wallets.

**Buyback size depends on the NEAR price.** Fee revenue is earned mostly in dollar terms and
arrives as NEAR, so the same revenue is fewer NEAR at a higher price. This is arithmetic, not
something the repo tests.

**Third-party inputs.** Attribution of inflows uses NearBlocks, and the USD context uses
DefiLlama and CoinGecko. None of these feed mint, burn, the buyback gain or payback. DefiLlama's
NEAR page states that 70% of gas fees are burnt; the live protocol config has
`burnt_gas_reward` at 0. Over the same days DefiLlama reports __LLAMA_FEES_NEAR__ NEAR a day in
gas fees and __LLAMA_BURN_NEAR__ burnt, against __BURN__ measured from the chain. We report the
difference and do not explain it.

**Sampling.** Utilization and the ceiling use 3 blocks per epoch and are reported only as
100-epoch aggregates.

## Pre-registered claims and what would change our mind

`predictions.json` was generated by `run.py` from data ending at height __LAST_HEIGHT__. It
commits to three claims about the 30 epochs after that height (about 9 days):

| Claim | Committed interval | Held in past windows |
|---|---|---|
| Payback over the 30 epochs (90% interval) | __C_PAY__ | __H_PAY__ |
| NEAR burnt over the 30 epochs (90% interval) | __C_BURN__ | __H_BURN__ |
| NEAR gained by the buyback account (90% interval) | __C_BUY__ | __H_BUY__ |

Each interval is the last 30-epoch value scaled by how much consecutive 30-epoch windows have
differed historically. "Held in past windows" is how often the same procedure, run at earlier
dates on data available then, contained the outcome.

- If payback over those 30 epochs falls outside its interval, `run.py` prints `FALSIFIED`. A
  90% interval fails about one time in ten even when the model is right; we accept that.
- The other two claims are reported as `HIT` or `MISS`.
- `predictions.json` also carries per-epoch burn forecasts from three models, scored as epochs
  close.

```
sha256(predictions.json) = __PRED_HASH__
```

The hash is in this repository's commit history, in the demo post and in the submission
description, each timestamped by a party we do not control. `run.py` will not score unless
`predictions.json` is byte-for-byte what the code derives from the frozen data.

Beyond the 30 epochs, rerunning `fetch.py` and `run.py` would change our mind if:

- the buyback account balance falls between two epoch ends;
- payback over a 100-epoch window drops below half of __PAYBACK__;
- transfers into the buyback account stop coming from `intents.near`.

## How to read the multiple

`multiple = mint / (burn + buyback gain)`: the factor by which today's flows must grow, at
constant issuance, to equal issuance. It is not a price target and says nothing about valuation.

| Lever | Who controls it | Effect on the multiple |
|---|---|---|
| NEAR Intents volume | the market | inversely proportional |
| Share of Intents fees reaching the buyback account | NEAR governance | inversely proportional |
| Gas use and gas price | users and protocol | small today: burn is under a tenth of payback |
| Issuance rate | NEAR governance | proportional: halving issuance halves it |
| NEAR price | the market | higher price means fewer NEAR per dollar of revenue |

## Sources

- NEAR mainnet: `https://archival-rpc.mainnet.fastnear.com` and `https://mainnet.neardata.xyz` (no key).
- Revenue wallets and the buyback start date: https://revenue.near.org and
  https://github.com/DefiLlama/dimension-adapters/blob/master/fees/near-intents/index.ts
- DefiLlama's burn assumption for NEAR: the `methodology` field of
  `https://api.llama.fi/summary/fees/near?dataType=dailyRevenue`.
- Protocol parameters: `EXPERIMENTAL_protocol_config` on the RPC, cached in `data/protocol.json`.
- Inflow attribution: `https://api.nearblocks.io/v1/account/buybacks.multisignature.near/receipts`.
- USD context: DefiLlama `https://api.llama.fi/summary/...` and CoinGecko.
