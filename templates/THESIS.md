# Thesis: NEAR's token flow moved to the application layer. At today's flows, break-even is __MULT__x away, not __BURN_MULT__x

Every figure in this file is printed by `python3 run.py` (no keys, no network) and stored in
`out/results.json`. Figures are for the last 100 epochs, __WINDOW_DAYS__ days, ending __LAST__ at
height __LAST_HEIGHT__, unless a different period is stated.

Terms used below: an *epoch* is NEAR's accounting period, about 12 hours (43,200 blocks); a
*yoctoNEAR* is 10^-24 NEAR, the chain's smallest unit; *payback* is burn plus buyback inflow
divided by new issuance; *break-even* is how many times flows must grow to equal issuance.

## Verdict for an investor

__VERDICT__

The rest of this file is the evidence for that stance, the case against it, and the rounds that
test it while judging runs.

## Claim

NEAR mints about 2.5% of its supply a year to validators (the current maximum; HSP-029, voted
through on 2026-11-02, would lower it to 1.6% over 24 months). The usual question is how much of that
the gas-fee burn gives back. The answer from the chain is __BURN_COV__, which puts break-even
__BURN_MULT__ times away.

That measures one layer. NEAR Intents began capturing fees on 23 February 2026. The wallet NEAR
names for buybacks funded by that revenue, `buybacks.multisignature.near`, was created on
2026-03-18, and the Intents contract has sent NEAR to it since 2026-04-23 (both dates from the
account's receipts, `data/wallet_history.csv`).

| Flow | NEAR a day | Share of mint |
|---|---|---|
| Minted to validators (exact) | __MINT__ | 100% |
| Burnt in gas fees (exact) | __BURN__ | __BURN_COV__ |
| Gained by the buyback account (exact balance change) | __BUY__ | __BUY_COV__ |
| **Payback: burn plus buyback gain** | | **__PAYBACK__** |

The thesis has three parts:

1. Burn plus buybacks equal __PAYBACK__ of issuance, not __BURN_COV__. If issuance and these
   flows stayed as they are, break-even would be __MULT__x away, not __BURN_MULT__x. "Payback" is our name for that ratio. It compares flows; it is not a change in supply, and
   "break-even" means the flows are equal. Buybacks are held,
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

**The inflows come from the NEAR Intents contract.** Of the __INFLOW_N__ transfers into the
buyback account since height __INFLOW_H__, __INFLOW_INTENTS__ were sent by `intents.near`,
carrying __INFLOW_SHARE__ of the NEAR (`data/inflows.csv`, from the NearBlocks indexer, with
transaction hashes). Earlier transfers are not covered by this check. Over every receipt since the account opened
(the audit below, from FastNear), `intents.near` sent __W_TOP1_SHARE__; the two figures cover
different periods and sources and are both reported.

**Captured revenue follows volume.** Across __WEEKS__ complete weeks since buybacks began, weekly
captured revenue and weekly NEAR Intents volume have a correlation of __CORR__ (DefiLlama). NEAR
keeps a median __BPS__ basis points of volume, in a range of __BPS_LO__ to __BPS_HI__. So the
volume lever in the table below rests on an observed relationship, not an assumption. It is
__WEEKS__ weekly points: a description of this period, not proof that the relationship is stable
or causal, and the take rate is not stable.

**A separate pipeline gives the same total.** DefiLlama computes NEAR's captured Intents revenue
from Dune tables across three revenue wallets. Converted at each day's price it is
__LLAMA_BUY_NEAR__ NEAR a day over the same days. Balance changes of those three wallets, read
with 12 RPC calls, give __ALL_NEAR__ NEAR a day. The thesis uses only the buyback wallet,
__BUY__ NEAR a day, which is the lower figure.

**Other teams' published figures agree once the wallet scope is matched.** Several entries in
this hackathon measured the same flow independently. As published in their READMEs, read
2026-11-14 (typed in from those pages, not computed here):

| Source | Their figure | Scope | Ours on the same scope |
|---|---|---|---|
| [NEAR Books](https://github.com/IhorMuliar/nearbooks) | revenue covers about 17% of new supply; 69.0% of DefiLlama's "buyback" revenue reached the buyback wallet; a 505,085.6 NEAR gap in published buyback totals, which they trace to an internal transfer of 510,068.0 NEAR, less outflows and fees, plus revenue received after the dashboard's cutoff | three revenue wallets | __ALL_PAY__; __BUY_SHARE__; __LUMP__ NEAR excluded as a transfer |
| [NEAR Agent Census](https://github.com/daodudestiny56-netizen/near-thesis-) | Intents revenue covers 15.1% of issuance; burn 0.58% | DefiLlama revenue, sampled burn, 2026-06 to 2026-11 | __ALL_PAY__; __BURN_COV__ (exact, last __WINDOW_DAYS__ days) |
| [near-thesis](https://github.com/soldanoandrea/near-thesis) | 7.2x to offset issuance | all captured revenue | __ALL_MULT__x |

The headline here is lower (__PAYBACK__, __MULT__x) because it counts only the wallet NEAR names
for buybacks and reads it as a balance change. Counting all three revenue wallets gives
__ALL_PAY__ and __ALL_MULT__x. The periods differ, so agreement is approximate; the point is that
separate code on separate data sources lands in the same range.

**The flow did not fall when swaps went private.** Another entry
([Tideline](https://github.com/ervhint/tideline-thesis)) reports that since 2026-10-27 a growing
share of Intents swaps settles on a private chain, and that fees on those swaps cannot be seen
in public data. We take the date from them. Confidential Intents itself launched in February
2026; 27 October is when Tideline sees its share grow, not a launch date. The buyback account does not depend on seeing
swaps: it is a balance on NEAR mainnet.

| Period | Buyback gain, NEAR a day | Payback | Epochs with an inflow |
|---|---|---|---|
| __PB_DAYS__ days before 2026-10-27 | __PB_BUY__ | __PB_PAY__ | __PB_IN__ of __PB_N__ |
| __PS_DAYS__ days since | __PS_BUY__ | __PS_PAY__ | __PS_IN__ of __PS_N__ |

We also checked the shift itself from raw mainnet blocks. `fetch.py private` draws seeded
random blocks from each period and counts the event logs emitted by `intents.near`, and how
many name the Confidential Intents treasury account, whose id we take from Tideline's
published data (`data/published/confidential.json` in their repo). Our counts are in
`data/private_sample.csv`.

| Period | Blocks sampled | `intents.near` event logs | Share naming the treasury | 90% interval |
|---|---|---|---|---|
| 30 days before 2026-10-27 | __LB_BLOCKS__ | __LB_EVENTS__ | __LB_SHARE__ | __LB_LO__ to __LB_HI__ |
| Since, to height __C_HEIGHT__ | __LS_BLOCKS__ | __LS_EVENTS__ | __LS_SHARE__ | __LS_LO__ to __LS_HI__ |

__L_VERDICT__ The treasury account already appears in the logs before 2026-10-27, so that date
marks a step up, not a start. The interval resamples whole blocks, because events in one block
are not independent. This counts events, not dollars.

So the one public measure of Intents revenue that still works shows it arriving at least as
fast as before. In dollars it is lower, because the NEAR price fell over the same weeks. The
forecast rounds below were frozen on 2026-11-12, after the change, so they test whether the
flow persists under private settlement.

**Realized inflation matches stated policy.** Measured mint annualizes to __INFL__ of supply
over the whole cache; the protocol config has `max_inflation_rate` at 1/40
(`data/protocol.json`). If the buyback NEAR were burnt rather than held, net inflation would be
__IF_BURNT__; as it is held, supply still grows at the gross rate.

**The capture lever is large.** Gross NEAR Intents fees run at __FEES_USD__ a day (DefiLlama).
The buyback account receives about __CAPTURE__ of that. If all of it arrived, at today's
volume, payback would be __LEVER__.

**Burn has headroom on paper (extrapolated, not observed).** Sampled blocks are __UTIL__ full. Scaling today's burn to full
blocks at today's effective gas price gives __CEIL__ of issuance (90% bootstrap range
__CEIL_LO__ to __CEIL_HI__). This is an extrapolation from 300 sampled blocks, not a capacity
guarantee.

**Price does not explain burn.** In a walk-forward backtest of burn per epoch
(__BT_N__ forecasts, up to 30 epochs ahead), the recent level alone scores __BT_PERSIST__
pinball loss. Adding NEAR's price to it scores __BT_PRICE__ (__BT_PRICE_SKILL__); adding a
time-of-week profile scores __BT_CLOCK__ (__BT_CLOCK_SKILL__). Lower is better. Burn follows
the calendar of use more than it follows the token price. The bands these models produce are
too narrow: they held about two-thirds of outcomes against a nominal 80%.

## Evidence against

**Buybacks are not burns.** The NEAR sits in a multisig account. Supply does not fall, and the
key holders can spend or sell it. The balance has already fallen once: by __OUT_NEAR__ NEAR, net
of inflows, in __OUT_N__ of the __BUY_EPOCHS__ epochs with buyback data. If outflows become
regular, the flow does not mean what this thesis takes it to mean.

**We audited the account the way a short seller would.** Four questions, all answered from
committed data (`python3 fetch.py history` and `python3 fetch.py multisig` rebuild it).

*Does the balance add up?* `data/wallet_history.csv` lists all __W_RECEIPTS__ receipts to or
from the account with exact amounts, from the FastNear index. `data/buybacks.csv` has the
balance at each epoch end, read from the chain. In all __W_BUSY__ epochs where the account only
received or sent transfers, the receipts sum to the balance change to the yoctoNEAR. The
__W_CALLS__ epochs with multisig calls differ by __W_RESID__ NEAR in total, which is gas and its refunds.
`test_run.py` fails if any epoch is unexplained.

*Who pays in?* __W_SENDERS__ senders, counting the protocol's own gas refunds, sent __W_IN__ NEAR. `__W_TOP1__` sent __W_TOP1_SHARE__ of
it in __W_TOP1_N__ transfers. `__W_TOP2__` sent __W_TOP2_SHARE__ in __W_TOP2_N__ transfers
(__W_TOP2_NEAR__ NEAR, which includes the one transfer the headline excludes). Everyone else
sent __W_OTHER_SHARE__. So the flow has two sources, and one of them is a DAO treasury that paid
in a lump. The headline counts only the steady source plus small transfers.

*Has it sold?* __W_PAID_NEAR__ NEAR has left, __W_PAID_SHARE__ of what came in.

__W_PAID_TABLE__

The 12,000 NEAR went to an implicit account that forwarded it to `bridge-mng.near` 14 blocks
later (heights 206365726 and 206365740, visible in any explorer). We did not trace it past that
account, so we cannot say whether it was sold. Nothing was burnt.

*Who can move it?* At height __C_HEIGHT__ the account has __C_FULL__ full-access keys and
__C_KEYS__ function-call keys, and its contract needs __C_CONF__ confirmations per request
(`data/multisig.json`). It has made __C_REQ__ requests in its life and __C_PEND__ are pending. One
of them replaced the contract code on 2026-05-27 (now `__C_CODE__`). The chain does not say who
holds the keys. Any two of them can move the whole balance, so "held" is a policy, not a
guarantee.

**Most gross fees never reach the account.** NEAR Intents charges a protocol fee of 0.0001% and
a distribution fee set by each partner, shared between NEAR and the partner
([fees](https://docs.near-intents.org/resources/fees),
[tokenomics post](https://www.near.org/blog/evolving-near-tokenomics)). We measure what
arrives, not the split, which is not published per swap.

**Payback has been falling.** The first 100-epoch window with buyback data (ending
__PAY_FIRST_DATE__) shows __PAY_FIRST__; the peak 100-epoch payback, buyback account only, is __PAY_PEAK__ (__PAY_PEAK_DATE__; close to, but not, the three-wallet figure above); the
latest is __PAYBACK__. The history is too short to fit a trend.

**NEAR Intents is not growing.** Comparing the first and last 30 days of the year to __LAST__
(DefiLlama): daily Intents volume is __VOL_RATIO__x, gross Intents fees __FEE_RATIO__x, and
NEAR gas fees in USD __GAS_RATIO__x. Within the year volume fell to a weekly low of
$__VOL_LOW__M a day and has recovered to $__VOL_NOW__M, so the year-on-year figure hides a round trip,
not steady growth. The buyback flow exists because capture was switched on in February 2026. At today's capture share, break-even needs
__MULT__x the volume.

**The payback is concentrated.** One application supplies over 90% of it. A fee cut, exploit
or loss of flow at NEAR Intents removes most of the thesis.

**Burn alone is far from break-even.** __BURN_COV__ of issuance, __BURN_MULT__x away.

**The headline does not depend on the exclusion, and its sampling range is wide.** The
excluded transfer and the one outflow both lie outside the last 100 epochs (__LUMP_IN__ and
__OUT_IN__ epochs in the window), so no threshold changes the __PAYBACK__ figure. Resampling
the window's epochs gives a 90% range of __PAY_LO__ to __PAY_HI__: a few large buyback epochs
carry much of the flow.

**The history is short and needed one exclusion.** Fee capture began on 2026-02-23; the first NEAR from `intents.near` reached the buyback account on 2026-04-23. One gain of
__LUMP__ NEAR was excluded by a mechanical rule (more than 20 times the median of the previous
100 epochs). The chain shows what it was: across that epoch, heights 214890733 to 214933933,
the other two revenue wallets fell by __LUMP_OUT__ NEAR (`data/wallets.csv`). That is revenue
captured earlier moving between wallets. The rule removes the whole gain, slightly more than
the matched outflow, which lowers payback. The transfer itself is inferred from balances; the
sender check above does not reach back that far.

**Buyback size depends on the NEAR price.** Fee revenue is earned mostly in dollar terms and
arrives as NEAR, so the same revenue is fewer NEAR at a higher price. This is arithmetic, not
something the repo tests.

**The chain got quieter.** Over the last 30 days against the first 30 of the window, BigQuery
shows daily active accounts and transactions both down by more than two thirds (see Network
activity below). A smaller network is a weaker base for any token. Most of the fall traces to one
application, KaiChing, which made most of the chain's function calls in February and has left
the top 25, while intents.near's own receipts grew. If activity outside Intents keeps shrinking,
the application-layer case narrows to a single product.

**Public volume and fee series may now undercount.** If Tideline's finding is right, the
DefiLlama volume, fee and take-rate figures used here for context understate activity from
2026-10-27. The correlation and the capture share are computed on those series.

**Third-party inputs.** Attribution of inflows uses NearBlocks, and the USD context uses
DefiLlama and CoinGecko. None of these feed mint, burn, the buyback gain or payback. DefiLlama's
NEAR page states that 70% of gas fees are burnt; the live protocol config has
`burnt_gas_reward` at 0. Over the same days DefiLlama reports __LLAMA_FEES_NEAR__ NEAR a day in
gas fees and __LLAMA_BURN_NEAR__ burnt, against __BURN__ measured from the chain. We report the
difference and do not explain it.

**Sampling.** Utilization and the ceiling use 3 blocks per epoch and are reported only as
100-epoch aggregates.

## Pre-registered rounds and what would change our mind

Each file in `predictions/` is a round: a forecast frozen at one block height about the epochs
after it. `run.py freeze` writes a round from the newest cached epoch and never overwrites one.
Rounds are short on purpose: they close before and during judging, and `python3 fetch.py
--epochs 45 && python3 run.py` scores whatever has closed.

__ROUNDS_TABLE__

Each round commits to three intervals for its window: payback, total NEAR burnt and total NEAR
gained by the buyback account. An interval is the last same-length window's value scaled by how
much consecutive windows have differed historically. "Held in the past" is how often that
procedure, run at earlier dates on data available then, contained the outcome
(`claims_backtest` in `out/results.json`).

- If payback over a round's window falls outside its interval, `run.py` prints `FALSIFIED` for
  that round. The band is the 5% to 95% range of past window-to-window changes. It has held
  less often than 90% of the time (see the table), so an occasional miss is expected even when
  the model is right; we accept that.
- The other two claims are reported as `HIT` or `MISS`. How often each interval has held is in
  the table; where an interval has held less often, a miss on it is weaker evidence.
- The payback interval is wide because consecutive windows differ a lot. What it rules out is
  the burn-only picture: its lower bound is several times __BURN_COV__. A result near the
  bounds is weak support, not confirmation.
- Each round also carries per-epoch burn forecasts from three models, scored as epochs close.

Timestamps we do not control: every round file has an OpenTimestamps proof next to it
(`predictions/*.ots`), which anchors its sha256 in the Bitcoin blockchain. Check one with
`ots verify predictions/<file>.ots` (opentimestamps-client). The hashes are also fixed by the
commits that add the files and quoted in the demo post and the submission. `run.py` refuses a
round that is not exactly what the code derives from the data up to that round's height, so
the method is frozen with the numbers.

Beyond the rounds, rerunning `fetch.py` and `run.py` would change our mind if:

- the buyback account balance keeps falling. It has fallen in __OUT_N__ of __BUY_EPOCHS__ epochs so far
  (__OUT_NEAR__ NEAR in total), so a single further outflow would not, but a run of them would;
- payback over a 100-epoch window drops below half of __PAYBACK__;
- transfers into the buyback account stop coming from `intents.near`.
- the year-long growth measures behind the scenarios move. The base case is their median
  (__SC_BASE_G__ a year, break-even in __SC_BASE_YEAR__): another year of falling Intents fees
  would make the bear case the base, and a year at the volume trend's pace (__SC_BULL_G__)
  would bring the base case within about five years. The path to break-even below is
  recomputed by every run.

## What this implies for the long term

The investment question is whether the flows that offset issuance can grow about __MULT__x. Our
stance is the verdict at the top of this file; the evidence behind it is conditional, not a
forecast:

__YEARS_TABLE__

| Path to break-even | What it requires |
|---|---|
| Growth alone, issuance unchanged | burn plus buybacks growing __G3__ a year for 3 years, __G5__ for 5, or __G10__ for 10 |
| Capture all gross Intents fees, at today's volume | payback of __LEVER__; the rest must come from growth or lower issuance |
| Lower issuance to 1.6% a year (HSP-029) | the multiple falls to __MULT_HSP__x at today's flows |

HSP-029 is the issuance lever being pulled now. It lowers maximum issuance from 2.5% to 1.6% a
year over 24 months. Its timeline
(https://gov.near.org/t/hsp-029-establish-a-24-month-issuance-ramp-to-a-1-6-target-rate-of-near-token-emissions/42644):

| Date | Step |
|---|---|
| 2026-10-07 | Proposal posted (author: Sal Ternullo, SVRN) |
| 2026-11-02 | House of Stake vote passes, 99.96% of voting power, 36 voters |
| 2026-11-16, 16:48 UTC | End of the Security Council veto window; with no veto it is ratified |
| about 2027-02-14 | Earliest start: a 90-day grace period follows ratification |
| after that | Validators adopt a nearcore release; the cut binds only then |

When this was last checked, on 2026-11-14, no veto and no nearcore release had been reported; the thread linked above carries any later news. The row above only
rescales today's multiple; the scenarios below start the ramp at its earliest date.

For: the flow exists, is measurable on chain, has moved with a product's volume over __WEEKS__ weeks (correlation
__CORR__), and two of the three levers are governance decisions. Against: the product's volume
is flat year on year, the flow is under nine months old and has fallen from its peak, and the
NEAR is held, not destroyed. On this evidence NEAR is closer to offsetting its issuance than
fee-burn analysis shows, and still far from doing so. A long-term case needs either sustained
volume growth of the size in the table or a governance decision on capture or issuance. The
rounds above check only that the flow persists, which is necessary for that case and
not sufficient.

## Path to break-even

Where does this go? Not a forecast: three growth rates taken from the data by a fixed rule, and
the year each one brings burn plus buybacks to 100% of issuance (`run.py: scenarios`,
`scenarios` in `out/results.json`).

The rule. The captured flow is about nine months old and was ramping up, so its own growth rate
is not used. What drives it is: buybacks are __BUY_COV__ of __PAYBACK__ payback and track NEAR
Intents volume week by week (correlation __CORR__). The data hold a full year of Intents volume
and gross fees, each measured two ways. Windows shorter than a year are left out because they
annualise one regime shift (weekly volume doubled in August 2026) into rates of several hundred
percent a year.

__SC_MEASURES__

Bear is the lowest of the four, base the median, bull the highest. Each path starts from today's
payback (__PAYBACK__) and holds the capture share and the NEAR price constant. Issuance is a rate on a
supply that keeps growing (buybacks are held, not burnt), so the NEAR minted each year grows too and
every path is measured against that rising mint. DefiLlama days whose Intents buybacks exceed their
gross fees are incomplete and left out. HSP-029 is
modelled as a linear ramp from 2.5% to 1.6% over 24 months, starting at its earliest possible
date, about 2027-02-14 (after the veto window and the 90-day grace period).

__SC_TABLE__

In plain words: if Intents fees keep shrinking as they did over the last year (__SC_BEAR_G__),
__SC_BEAR_SENT__. At the median year-long growth (__SC_BASE_G__) it comes in
__SC_BASE_YEAR__, or __SC_BASE_YEAR_HSP__ with HSP-029: decades, not years. At the year's best
trend, Intents volume's __SC_BULL_G__ a year, it comes in __SC_BULL_YEAR__, or __SC_BULL_YEAR_HSP__
with HSP-029; that rate is close to the __G5__ a year that five-year break-even needs.

Capture is the larger lever on the base case. At today's volume, by share of gross Intents fees
reaching the buyback account:

__SC_LEVERS__

Issuance: today's flow would equal issuance if issuance were __SC_BE_ISS__ a year. HSP-029's
1.6% takes the multiple from __MULT__x to __MULT_HSP__x; capture and growth have to close the rest.

## How to read the multiple

`multiple = mint / (burn + buyback gain)`: the factor by which today's flows must grow, at
constant issuance, to equal issuance. It is not a price target and says nothing about valuation.

| Lever | Who controls it | Effect on the multiple |
|---|---|---|
| NEAR Intents volume | the market | inversely proportional |
| Share of Intents fees reaching the buyback account | NEAR governance | inversely proportional |
| Gas use and gas price | users and protocol | small today: burn is under a tenth of payback |
| Issuance rate | NEAR governance | proportional: 2.5% to 1.6% takes it from __MULT__x to __MULT_HSP__x |
| NEAR price | the market | higher price means fewer NEAR per dollar of revenue |

## Network activity (BigQuery)

Does NEAR Intents grow as a share of the network's activity? Four queries against Google's
public NEAR dataset (`bigquery-public-data.crypto_near_mainnet_us`) measure it, each filtered on
`block_date` over 2026-02-13 to 2026-11-12:

__BQ_TABLE__

Status: __BQ_STATUS__.

Finding: __BQ_FINDING__

This is context, not evidence for the claim. Payback depends on the fees Intents sends to the
buyback account, not on how many receipts it handles, so these figures do not enter the
multiple or the result hash.

We do not pull from the Intents Explorer API. Its terms (1Click Swap API Terms of Use, section
4.1(e), https://partners.near-intents.org/legal/terms-of-service) forbid keeping its data beyond
24 hours, and a thesis that others must re-check cannot rest on data that has to be deleted.
DefiLlama's public NEAR Intents series stands in for it.

## Sources

- NEAR mainnet: `https://archival-rpc.mainnet.fastnear.com` and `https://mainnet.neardata.xyz` (no key).
- Revenue wallets and the buyback start date: https://revenue.near.org and
  https://github.com/DefiLlama/dimension-adapters/blob/master/fees/near-intents/index.ts
- DefiLlama's burn assumption for NEAR: the `methodology` field of
  `https://api.llama.fi/summary/fees/near?dataType=dailyRevenue`.
- Protocol parameters: `EXPERIMENTAL_protocol_config` on the RPC, cached in `data/protocol.json`.
- Inflow attribution: `https://api.nearblocks.io/v1/account/buybacks.multisignature.near/receipts`.
- USD context: DefiLlama `https://api.llama.fi/summary/fees/near-intents` and `https://api.llama.fi/summary/dexs/near-intents` (the URLs are listed in `fetch.py`), and CoinGecko.
