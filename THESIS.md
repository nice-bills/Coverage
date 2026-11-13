# Thesis: NEAR's token flow moved to the application layer. At today's flows, break-even is 8.4x away, not 108x

Every figure in this file is printed by `python3 run.py` (no keys, no network) and stored in
`out/results.json`. Figures are for the last 100 epochs, 29 days, ending 2026-11-12 at
height 224265136, unless a different period is stated.

Terms used below: an *epoch* is NEAR's accounting period, about 12 hours (43,200 blocks); a
*yoctoNEAR* is 10^-24 NEAR, the chain's smallest unit; *payback* is burn plus buyback inflow
divided by new issuance; *break-even* is how many times flows must grow to equal issuance.

## Claim

NEAR mints about 2.5% of its supply a year to validators (the current maximum; HSP-029, voted
through on 2026-11-02, would lower it to 1.6% over 24 months). The usual question is how much of that
the gas-fee burn gives back. The answer from the chain is 0.92%, which puts break-even
108 times away.

That measures one layer. NEAR Intents began capturing fees on 23 February 2026. The wallet NEAR
names for buybacks funded by that revenue, `buybacks.multisignature.near`, was created on
2026-03-18, and the Intents contract has sent NEAR to it since 2026-04-23 (both dates from the
account's receipts, `data/wallet_history.csv`).

| Flow | NEAR a day | Share of mint |
|---|---|---|
| Minted to validators (exact) | 89,783 | 100% |
| Burnt in gas fees (exact) | 829 | 0.92% |
| Gained by the buyback account (exact balance change) | 9,922 | 11.1% |
| **Payback: burn plus buyback gain** | | **12.0%** |

The thesis has three parts:

1. Burn plus buybacks equal 12.0% of issuance, not 0.92%. If issuance and these
   flows stayed as they are, break-even would be 8.4x away, not 108x. "Payback" is our name for that ratio. It compares flows; it is not a change in supply, and
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

**The inflows come from the NEAR Intents contract.** Of the 2996 transfers into the
buyback account since height 201009796, 2979 were sent by `intents.near`,
carrying 74.0% of the NEAR (`data/inflows.csv`, from the NearBlocks indexer, with
transaction hashes). Earlier transfers are not covered by this check; the audit below, over
every receipt since the account opened, gives a share for the whole history.

**Captured revenue follows volume.** Across 37 complete weeks since buybacks began, weekly
captured revenue and weekly NEAR Intents volume have a correlation of 0.90 (DefiLlama). NEAR
keeps a median 2.6 basis points of volume, in a range of 1.1 to 6.1. So the
volume lever in the table below rests on an observed relationship, not an assumption. It is
37 weekly points: a description of this period, not proof that the relationship is stable
or causal, and the take rate is not stable.

**A separate pipeline gives the same total.** DefiLlama computes NEAR's captured Intents revenue
from Dune tables across three revenue wallets. Converted at each day's price it is
13,589 NEAR a day over the same days. Balance changes of those three wallets, read
with 12 RPC calls, give 13,984 NEAR a day. The thesis uses only the buyback wallet,
9,922 NEAR a day, which is the lower figure.

**Other teams' published figures agree once the wallet scope is matched.** Several entries in
this hackathon measured the same flow independently. As published in their READMEs, read
2026-11-13 (typed in from those pages, not computed here):

| Source | Their figure | Scope | Ours on the same scope |
|---|---|---|---|
| [NEAR Books](https://github.com/IhorMuliar/nearbooks) | revenue covers about 17% of new supply; 69.0% of DefiLlama's "buyback" revenue reached the buyback wallet; a 505,085.6 NEAR gap in published buyback totals, which they trace to an internal transfer | three revenue wallets | 16.5%; 73%; 505,041 NEAR excluded as a transfer |
| [NEAR Agent Census](https://github.com/daodudestiny56-netizen/near-thesis-) | Intents revenue covers 15.1% of issuance; burn 0.58% | DefiLlama revenue, sampled burn, 2026-06 to 2026-11 | 16.5%; 0.92% (exact, last 29 days) |
| [near-thesis](https://github.com/soldanoandrea/near-thesis) | 7.2x to offset issuance | all captured revenue | 6.1x |

The headline here is lower (12.0%, 8.4x) because it counts only the wallet NEAR names
for buybacks and reads it as a balance change. Counting all three revenue wallets gives
16.5% and 6.1x. The periods differ, so agreement is approximate; the point is that
separate code on separate data sources lands in the same range.

**The flow did not fall when swaps went private.** Another entry
([Tideline](https://github.com/ervhint/tideline-thesis)) reports that since 2026-10-27 a growing
share of Intents swaps settles on a private chain, and that fees on those swaps cannot be seen
in public data. We take the date from them. Confidential Intents itself launched in February
2026; 27 October is when Tideline sees its share grow, not a launch date. The buyback account does not depend on seeing
swaps: it is a balance on NEAR mainnet.

| Period | Buyback gain, NEAR a day | Payback | Epochs with an inflow |
|---|---|---|---|
| 30 days before 2026-10-27 | 9,298 | 11.7% | 101 of 101 |
| 17 days since | 10,452 | 12.5% | 58 of 58 |

We also checked the shift itself from raw mainnet blocks. `fetch.py private` draws seeded
random blocks from each period and counts the event logs emitted by `intents.near`, and how
many name the Confidential Intents treasury account, whose id we take from Tideline's
published data (`data/published/confidential.json` in their repo). Our counts are in
`data/private_sample.csv`.

| Period | Blocks sampled | `intents.near` event logs | Share naming the treasury | 90% interval |
|---|---|---|---|---|
| 30 days before 2026-10-27 | 250 | 438 | 13% | 8% to 18% |
| Since, to height 224265136 | 250 | 631 | 43% | 36% to 49% |

The share rose, and the two intervals do not overlap, so the shift is visible in mainnet logs alone. The treasury account already appears in the logs before 2026-10-27, so that date
marks a step up, not a start. The interval resamples whole blocks, because events in one block
are not independent. This counts events, not dollars.

So the one public measure of Intents revenue that still works shows it arriving at least as
fast as before. In dollars it is lower, because the NEAR price fell over the same weeks. The
forecast rounds below were frozen on 2026-11-12, after the change, so they test whether the
flow persists under private settlement.

**Realized inflation matches stated policy.** Measured mint annualizes to 2.47% of supply
over the whole cache; the protocol config has `max_inflation_rate` at 1/40
(`data/protocol.json`). If the buyback NEAR were burnt rather than held, net inflation would be
2.20%; as it is held, supply still grows at the gross rate.

**The capture lever is large.** Gross NEAR Intents fees run at $191,119 a day (DefiLlama).
The buyback account receives about 23% of that. If all of it arrived, at today's
volume, payback would be 49%.

**Burn has headroom on paper (extrapolated, not observed).** Sampled blocks are 0.78% full. Scaling today's burn to full
blocks at today's effective gas price gives 119% of issuance (90% bootstrap range
104% to 137%). This is an extrapolation from 300 sampled blocks, not a capacity
guarantee.

**Price does not explain burn.** In a walk-forward backtest of burn per epoch
(510 forecasts, up to 30 epochs ahead), the recent level alone scores 0.0865
pinball loss. Adding NEAR's price to it scores 0.0938 (9% worse); adding a
time-of-week profile scores 0.0785 (9% better). Lower is better. Burn follows
the calendar of use more than it follows the token price. The bands these models produce are
too narrow: they held about two-thirds of outcomes against a nominal 80%.

## Evidence against

**Buybacks are not burns.** The NEAR sits in a multisig account. Supply does not fall, and the
key holders can spend or sell it. The balance has already fallen once: by 10,283 NEAR, net
of inflows, in 1 of the 663 epochs with buyback data. If outflows become
regular, the flow does not mean what this thesis takes it to mean.

**We audited the account the way a short seller would.** Four questions, all answered from
committed data (`python3 fetch.py history` and `python3 fetch.py multisig` rebuild it).

*Does the balance add up?* `data/wallet_history.csv` lists all 3,374 receipts to or
from the account with exact amounts, from the FastNear index. `data/buybacks.csv` has the
balance at each epoch end, read from the chain. In all 658 epochs where the account only
received or sent transfers, the receipts sum to the balance change to the yoctoNEAR. The
5 epochs with multisig calls differ by 0.34 NEAR in total, which is gas and its refunds.
`test_run.py` fails if any epoch is unexplained.

*Who pays in?* 13 senders, counting the protocol's own gas refunds, sent 2,274,740 NEAR. `intents.near` sent 77.2% of
it in 3,327 transfers. `1csfundsadmin.sputnik-dao.near` sent 22.4% in 3 transfers
(510,068 NEAR, which includes the one transfer the headline excludes). Everyone else
sent 0.39%. So the flow has two sources, and one of them is a DAO treasury that paid
in a lump. The headline counts only the steady source plus small transfers.

*Has it sold?* 12,025 NEAR has left, 0.53% of what came in.

| Recipient | Transfers | NEAR | Epoch ending |
|---|---|---|---|
| `508aa18569e5a59d63b0f4c445e02e7b5fc53b86337328e756b32745ebac50e7` | 1 | 12,000 | 2026-07-10 |
| `nf-payments.near` | 2 | 25 | 2026-03-20 |

The 12,000 NEAR went to an implicit account that forwarded it to `bridge-mng.near` 14 blocks
later (heights 206365726 and 206365740, visible in any explorer). We did not trace it past that
account, so we cannot say whether it was sold. Nothing was burnt.

*Who can move it?* At height 224265136 the account has 0 full-access keys and
4 function-call keys, and its contract needs 2 confirmations per request
(`data/multisig.json`). It has made 4 requests in its life and 0 are pending. One
of them replaced the contract code on 2026-05-27 (now `2v9kZJHN4sogHuKtKHaqYAqQBazkqH2cjY1rrjQYvNQa`). The chain does not say who
holds the keys. Any two of them can move the whole balance, so "held" is a policy, not a
guarantee.

**Most gross fees never reach the account.** NEAR Intents charges a protocol fee of 0.0001% and
a distribution fee set by each partner, shared between NEAR and the partner
([fees](https://docs.near-intents.org/resources/fees),
[tokenomics post](https://www.near.org/blog/evolving-near-tokenomics)). We measure what
arrives, not the split, which is not published per swap.

**Payback has been falling.** The first 100-epoch window with buyback data (ending
2026-03-15) shows 2.5%; the peak is 16.5% (2026-09-19); the
latest is 12.0%. The history is too short to fit a trend.

**NEAR Intents is not growing.** Comparing the first and last 30 days of the year to 2026-11-12
(DefiLlama): daily Intents volume is 1.02x, gross Intents fees 0.75x, and
NEAR gas fees in USD 0.62x. Within the year volume fell to a weekly low of
$51M a day and has recovered to $130M, so the year-on-year figure hides a round trip,
not steady growth. The buyback flow exists because capture was switched on in February 2026. At today's capture share, break-even needs
8.4x the volume.

**The payback is concentrated.** One application supplies over 90% of it. A fee cut, exploit
or loss of flow at NEAR Intents removes most of the thesis.

**Burn alone is far from break-even.** 0.92% of issuance, 108x away.

**The headline does not depend on the exclusion, and its sampling range is wide.** The
excluded transfer and the one outflow both lie outside the last 100 epochs (0 and
0 epochs in the window), so no threshold changes the 12.0% figure. Resampling
the window's epochs gives a 90% range of 10.7% to 13.5%: a few large buyback epochs
carry much of the flow.

**The history is short and needed one exclusion.** Fee capture began on 2026-02-23; the first NEAR from `intents.near` reached the buyback account on 2026-04-23. One gain of
505,041 NEAR was excluded by a mechanical rule (more than 20 times the median of the previous
100 epochs). The chain shows what it was: across that epoch, heights 214890733 to 214933933,
the other two revenue wallets fell by 501,917 NEAR (`data/wallets.csv`). That is revenue
captured earlier moving between wallets. The rule removes the whole gain, slightly more than
the matched outflow, which lowers payback. The transfer itself is inferred from balances; the
sender check above does not reach back that far.

**Buyback size depends on the NEAR price.** Fee revenue is earned mostly in dollar terms and
arrives as NEAR, so the same revenue is fewer NEAR at a higher price. This is arithmetic, not
something the repo tests.

**Public volume and fee series may now undercount.** If Tideline's finding is right, the
DefiLlama volume, fee and take-rate figures used here for context understate activity from
2026-10-27. The correlation and the capture share are computed on those series.

**Third-party inputs.** Attribution of inflows uses NearBlocks, and the USD context uses
DefiLlama and CoinGecko. None of these feed mint, burn, the buyback gain or payback. DefiLlama's
NEAR page states that 70% of gas fees are burnt; the live protocol config has
`burnt_gas_reward` at 0. Over the same days DefiLlama reports 978 NEAR a day in
gas fees and 684 burnt, against 829 measured from the chain. We report the
difference and do not explain it.

**Sampling.** Utilization and the ceiling use 3 blocks per epoch and are reported only as
100-epoch aggregates.

## Pre-registered rounds and what would change our mind

Each file in `predictions/` is a round: a forecast frozen at one block height about the epochs
after it. `run.py freeze` writes a round from the newest cached epoch and never overwrites one.
Rounds are short on purpose: they close before and during judging, and `python3 fetch.py
--epochs 45 && python3 run.py` scores whatever has closed.

| Round | Epochs | Expected to close (UTC) | Payback | NEAR burnt | Buyback gain, NEAR | Payback interval held in the past | sha256 |
|---|---|---|---|---|---|---|---|
| `round-224265136-h05.json` | 5 | about 2026-11-14 07:00 | 6.9% to 27.2% | 1,193 to 1,880 | 7,318 to 35,576 | 134 of 168 | `e4cf5acdca0e2f74153a91c93febba9a185b9c7b0e1c2a0edc97df11db7530ba` |
| `round-224265136-h10.json` | 10 | about 2026-11-15 19:00 | 6.3% to 30.8% | 2,174 to 3,554 | 14,073 to 86,748 | 71 of 83 | `2c738b805dd13904d226f2511ebb437fb7780f908a96e79c6a3f2cedab39321f` |
| `round-224265136-h20.json` | 20 | about 2026-11-18 17:00 | 6.9% to 26.8% | 2,820 to 6,524 | 34,148 to 133,348 | 35 of 40 | `926ba45df2401210a5d871b512caddbd92f41fca761cbcebf02d53814c9bddf5` |

Each round commits to three intervals for its window: payback, total NEAR burnt and total NEAR
gained by the buyback account. An interval is the last same-length window's value scaled by how
much consecutive windows have differed historically. "Held in the past" is how often that
procedure, run at earlier dates on data available then, contained the outcome
(`claims_backtest` in `out/results.json`).

- If payback over a round's window falls outside its interval, `run.py` prints `FALSIFIED` for
  that round. The band is the 5% to 95% range of past window-to-window changes. It has held
  less often than 90% of the time (see the table), so an occasional miss is expected even when
  the model is right; we accept that.
- The other two claims are reported as `HIT` or `MISS`. The burn interval has held less often
  than the payback band, so a burn miss is weaker evidence than a payback miss.
- The payback interval is wide because consecutive windows differ a lot. What it rules out is
  the burn-only picture: its lower bound is several times 0.92%. A result near the
  bounds is weak support, not confirmation.
- Each round also carries per-epoch burn forecasts from three models, scored as epochs close.

Timestamps we do not control: every round file has an OpenTimestamps proof next to it
(`predictions/*.ots`), which anchors its sha256 in the Bitcoin blockchain. Check one with
`ots verify predictions/<file>.ots` (opentimestamps-client). The hashes are also fixed by the
commits that add the files and quoted in the demo post and the submission. `run.py` refuses a
round that is not exactly what the code derives from the data up to that round's height, so
the method is frozen with the numbers.

Beyond the rounds, rerunning `fetch.py` and `run.py` would change our mind if:

- the buyback account balance keeps falling. It has fallen in 1 of 663 epochs so far
  (10,283 NEAR in total), so a single further outflow would not, but a run of them would;
- payback over a 100-epoch window drops below half of 12.0%;
- transfers into the buyback account stop coming from `intents.near`.

## What this implies for the long term

The investment question is whether the flows that offset issuance can grow about 8.4x. The
evidence supports a conditional answer, not a forecast:

| Growth in burn plus buybacks | Years to break-even, issuance at 2.5% | Years, issuance ramping to 1.6% (HSP-029) |
|---|---|---|
| 10% a year | 22.3 | 17.7 |
| 25% a year | 9.6 | 7.6 |
| 50% a year | 5.2 | 4.2 |
| 100% a year | 3.1 | 2.5 |

| Path to break-even | What it requires |
|---|---|
| Growth alone, issuance unchanged | burn plus buybacks growing 103% a year for 3 years, 53% for 5, or 24% for 10 |
| Capture all gross Intents fees, at today's volume | payback of 49%; the rest must come from growth or lower issuance |
| Lower issuance to 1.6% a year (HSP-029) | the multiple falls to 5.3x at today's flows |

HSP-029 is the issuance lever being pulled now. It lowers maximum issuance from 2.5% to 1.6% a
year over 24 months. NEAR's House of Stake passed it on 2026-11-02. As of 2026-11-13 it still needs the
Security Council veto window (closing about 2026-11-16) to pass and validators to adopt it
(https://gov.near.org/t/hsp-029-establish-a-24-month-issuance-ramp-to-a-1-6-target-rate-of-near-token-emissions/42644).
This repo does not model the ramp; the row above only rescales today's multiple.

For: the flow exists, is measurable on chain, has moved with a product's volume over 37 weeks (correlation
0.90), and two of the three levers are governance decisions. Against: the product's volume
is flat year on year, the flow is under nine months old and has fallen from its peak, and the
NEAR is held, not destroyed. On this evidence NEAR is closer to offsetting its issuance than
fee-burn analysis shows, and still far from doing so. A long-term case needs either sustained
volume growth of the size in the table or a governance decision on capture or issuance. The
rounds above check only that the flow persists, which is necessary for that case and
not sufficient.

## How to read the multiple

`multiple = mint / (burn + buyback gain)`: the factor by which today's flows must grow, at
constant issuance, to equal issuance. It is not a price target and says nothing about valuation.

| Lever | Who controls it | Effect on the multiple |
|---|---|---|
| NEAR Intents volume | the market | inversely proportional |
| Share of Intents fees reaching the buyback account | NEAR governance | inversely proportional |
| Gas use and gas price | users and protocol | small today: burn is under a tenth of payback |
| Issuance rate | NEAR governance | proportional: 2.5% to 1.6% takes it from 8.4x to 5.3x |
| NEAR price | the market | higher price means fewer NEAR per dollar of revenue |

## Sources

- NEAR mainnet: `https://archival-rpc.mainnet.fastnear.com` and `https://mainnet.neardata.xyz` (no key).
- Revenue wallets and the buyback start date: https://revenue.near.org and
  https://github.com/DefiLlama/dimension-adapters/blob/master/fees/near-intents/index.ts
- DefiLlama's burn assumption for NEAR: the `methodology` field of
  `https://api.llama.fi/summary/fees/near?dataType=dailyRevenue`.
- Protocol parameters: `EXPERIMENTAL_protocol_config` on the RPC, cached in `data/protocol.json`.
- Inflow attribution: `https://api.nearblocks.io/v1/account/buybacks.multisignature.near/receipts`.
- USD context: DefiLlama `https://api.llama.fi/summary/fees/near-intents` and `https://api.llama.fi/summary/dexs/near-intents` (the URLs are listed in `fetch.py`), and CoinGecko.
