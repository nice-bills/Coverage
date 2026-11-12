# Thesis: NEAR's payback moved to the application layer, and break-even is single-digit multiples away

## Claim

NEAR mints about 2.5% of its supply a year to validators. The usual question is how much of that
the protocol's gas-fee burn gives back, and the usual answer is "under 1%", which puts break-even
about __BURN_MULT__ times away.

That answer measures the wrong layer. Since 23 February 2026, fee revenue from NEAR Intents has
been used to buy NEAR, and the NEAR accumulates in `buybacks.multisignature.near`. Measured on
chain over the last 100 epochs (about 28 days, ending __LAST__):

| Flow | NEAR a day | Share of mint |
|---|---|---|
| Minted to validators (exact) | __MINT__ | 100% |
| Burnt in gas fees (exact) | __BURN__ | __BURN_COV__ |
| Added to the buyback account (exact balance change) | __BUY__ | __BUY_COV__ |
| **Payback: burn plus buybacks** | | **__PAYBACK__** |

So the thesis is:

1. NEAR already pays back __PAYBACK__ of its issuance, not __BURN_COV__. Break-even is
   __MULT__x away, not __BURN_MULT__x.
2. More than nine-tenths of that payback comes from application revenue, not from gas. The
   token's cash flow is tied to NEAR Intents fees, not to block space.
3. The remaining gap can close through levers NEAR controls, without waiting for the market:
   the share of Intents fees it captures, and the issuance rate.

All three figures in the table come from `python3 run.py`, which needs no keys and no network.

## Evidence for

**The flows are exact and reconcile.** Mint and burn are read from `total_supply` in block
headers. `run.py` asserts that the change in supply over the whole cache equals the sum of mint
minus burn, to the yoctoNEAR, across __EPOCHS__ epochs. The buyback figure is the change in an
account balance between two block heights.

**An independent pipeline agrees.** DefiLlama computes captured NEAR Intents revenue from Dune
tables. Over the same days it reports __LLAMA_BUY__ a day. Our 12 RPC calls against all three
revenue wallets give __ALL_USD__ a day. The buyback wallet alone, which is the figure the thesis
uses, is __BUY_USD__ a day, so the headline is the conservative one.

**The indexer's burn figure is stale, in NEAR's favour.** DefiLlama's NEAR adapter states that
70% of each gas fee is burnt. The live protocol config has `burnt_gas_reward` at 0 (the developer
rebate was removed), and the chain shows __BURN_USD__ a day burnt against DefiLlama's
__LLAMA_BURN__. A model built on that indexer understates burn.

**Realized inflation matches the stated policy.** Measured mint annualizes to __INFL__ of
supply against a configured maximum of 1/40. Net of payback it is __NET_INFL__.

**The capture lever is large.** Gross NEAR Intents fees run at __FEES_USD__ a day (DefiLlama).
If all of it were captured at today's volume, payback would be __LEVER__. Capturing fees is a
governance decision, already taken once.

**Burn has headroom inside existing capacity.** Blocks are __UTIL__ full. At today's effective
gas price, full blocks would burn __CEIL__ of issuance (90% range __CEIL_LO__ to __CEIL_HI__).
Burn alone can reach break-even without new shards, though it is far from doing so.

**Burn follows the clock, not the price.** Burn per epoch has a stable time-of-week profile.
The backtest table in the dashboard compares a model that uses only that profile with a model
that uses only NEAR's price. __BACKTEST_SENTENCE__

## Evidence against

**Buybacks are not burns.** The NEAR sits in a multisig account. Supply does not fall, and the
holders of the keys can spend or sell it. Payback here is a flow that offsets issuance, not
destroyed tokens. If the account's balance starts falling, this thesis is wrong about what the
flow means.

**NEAR Intents is not growing.** Over the year to __LAST__, daily Intents volume is
__VOL_RATIO__x what it was, gross Intents fees are __FEE_RATIO__x and NEAR gas fees in USD are
__GAS_RATIO__x (first 30 days against last 30 days, DefiLlama). Payback rose because capture
was switched on, not because the business grew. At today's capture share, break-even needs
__MULT__x the volume, and volume has not moved.

**The payback is concentrated.** One application supplies over 90% of it. One counterparty
change, exploit or fee cut at NEAR Intents removes most of the thesis.

**Burn is under 1% and has been falling in USD.** Measured from the chain, gas burn covers
__BURN_COV__ of issuance. On its own it is __BURN_MULT__x from break-even.

**The window is short.** Buybacks began on 2026-02-23, so there are under nine months of
history, and one transfer of __LUMP__ NEAR on 2026-09-09 had to be excluded as a treasury
movement. The exclusion rule is mechanical and backward-looking, but it is still a rule we
chose.

**Buyback amounts depend on the NEAR price.** Revenue is earned in dollars and converted to
NEAR. A higher NEAR price buys fewer NEAR for the same revenue, so payback in NEAR terms falls
as price rises. Break-even is harder to reach exactly when the token is doing well.

**Sampling.** Utilization and the ceiling use 3 blocks per epoch. They are reported only as
100-epoch aggregates with a bootstrap range.

## What would change our mind

Checked automatically by `python3 run.py` against epochs that closed after the predictions were
frozen:

1. **Burn is explained by price after all.** The price-only model beats the price-free model
   over the next 30 epochs, or the price-free model's 80% interval contains fewer than 20 or
   more than 28 of the 30 outcomes. The command prints `FALSIFIED`.
2. **Buybacks stop or reverse.** The buyback account's gain over the next 30 epochs falls
   outside the committed interval. The command prints `MISS`.

Checked by rerunning `fetch.py` and `run.py` later:

3. The buyback account balance falls between two epoch ends (NEAR is being spent, not held).
4. Payback over any 100-epoch window drops below half of today's figure.
5. Gross Intents fees fall while capture share is unchanged, so payback falls with them.

## Pre-registration

`predictions.json` contains 30 epochs of burn forecasts from three models and the buyback
interval. It was generated by `run.py` from data ending at height __LAST_HEIGHT__.

```
sha256(predictions.json) = __PRED_HASH__
```

This hash is published in the repository's commit history, in the demo post and in the
submission description, each timestamped by a party we do not control, before the epochs it
predicts had closed. `run.py` will not score unless `predictions.json` is exactly what the code
derives from the frozen data, so the method is frozen with the numbers.

## How to read the multiple

`multiple = mint / (burn + buyback)`. It is the factor by which today's fee flows must grow, at
constant issuance, for the flows to equal issuance. It is not a price target and says nothing
about valuation. It moves when any of these move:

| Lever | Who controls it | Effect on the multiple |
|---|---|---|
| NEAR Intents volume | the market | inversely proportional |
| Share of Intents fees captured | NEAR governance | inversely proportional |
| Gas use and gas price | users and protocol | small today: burn is under a tenth of payback |
| Issuance rate | NEAR governance | proportional: halving issuance halves it |
| NEAR price | the market | higher price means fewer NEAR bought per dollar |

## Sources

- NEAR mainnet via `archival-rpc.mainnet.fastnear.com` and `mainnet.neardata.xyz` (no key).
- `buybacks.multisignature.near`, `fefundsadmin.sputnik-dao.near` and
  `1csfundsadmin.sputnik-dao.near` are the revenue wallets listed on revenue.near.org and in
  DefiLlama's `fees/near-intents` adapter, which also gives the 2026-02-23 buyback start.
- DefiLlama `api.llama.fi/summary/...` and CoinGecko (no key) for USD context only.
