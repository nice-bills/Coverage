# Thesis: NEAR's token flow moved to the application layer. At today's flows, break-even is 8.5x away, not 109x

Every figure in this file is printed by `python3 run.py` (no keys, no network) and stored in
`out/results.json`. Figures are for the last 100 epochs, 29 days, ending 2026-11-12 at
height 224221936, unless a different period is stated.

## Claim

NEAR mints about 2.5% of its supply a year to validators. The usual question is how much of that
the gas-fee burn gives back. The answer from the chain is 0.92%, which puts break-even
109 times away.

That measures one layer. Since 23 February 2026 the NEAR Intents contract has been sending NEAR
to `buybacks.multisignature.near`, the wallet NEAR names for buybacks funded by Intents fee
revenue.

| Flow | NEAR a day | Share of mint |
|---|---|---|
| Minted to validators (exact) | 89,744 | 100% |
| Burnt in gas fees (exact) | 826 | 0.92% |
| Gained by the buyback account (exact balance change) | 9,749 | 10.9% |
| **Payback: burn plus buyback gain** | | **11.8%** |

The thesis has three parts:

1. Burn plus buybacks equal 11.8% of issuance, not 0.92%. If issuance and these
   flows stayed as they are, break-even would be 8.5x away, not 109x. "Payback" is our name for that ratio; buybacks are held,
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

**The inflows come from the NEAR Intents contract.** Of the 2983 transfers into the
buyback account since height 201009796, 2966 were sent by `intents.near`,
carrying 73.9% of the NEAR (`data/inflows.csv`, from the NearBlocks indexer, with
transaction hashes). Earlier transfers are not covered by this check.

**Captured revenue follows volume.** Across 37 complete weeks since buybacks began, weekly
captured revenue and weekly NEAR Intents volume have a correlation of 0.90 (DefiLlama). NEAR
keeps a median 2.6 basis points of volume, in a range of 1.1 to 6.1. So the
volume lever in the table below is measured, not assumed, though the take rate is not stable.

**A separate pipeline gives the same total.** DefiLlama computes NEAR's captured Intents revenue
from Dune tables across three revenue wallets. Converted at each day's price it is
13,589 NEAR a day over the same days. Balance changes of those three wallets, read
with 12 RPC calls, give 13,772 NEAR a day. The thesis uses only the buyback wallet,
9,749 NEAR a day, which is the lower figure.

**Realized inflation matches stated policy.** Measured mint annualizes to 2.47% of supply
over the whole cache; the protocol config has `max_inflation_rate` at 1/40
(`data/protocol.json`). If the buyback NEAR were burnt rather than held, net inflation would be
2.20%; as it is held, supply still grows at the gross rate.

**The capture lever is large.** Gross NEAR Intents fees run at $191,119 a day (DefiLlama).
The buyback account receives about 22% of that. If all of it arrived, at today's
volume, payback would be 49%.

**Burn has headroom on paper.** Sampled blocks are 0.78% full. Scaling today's burn to full
blocks at today's effective gas price gives 118% of issuance (90% bootstrap range
102% to 135%). This is an extrapolation from 300 sampled blocks, not a capacity
guarantee.

**Price does not explain burn.** In a walk-forward backtest of burn per epoch
(510 forecasts), a model that adds NEAR's price to the recent level scores
0.0938 pinball loss against 0.0865 for the recent level alone. A model that adds
a time-of-week profile scores 0.0785. Neither addition is a clear improvement, so at this
horizon burn behaves like a noisy level, not like a function of the token price.

## Evidence against

**Buybacks are not burns.** The NEAR sits in a multisig account. Supply does not fall, and the
key holders can spend or sell it. The balance has already fallen once: by 10,283 NEAR, net
of inflows, in 1 of the 662 epochs with buyback data. If outflows become
regular, the flow does not mean what this thesis takes it to mean.

**Payback has been falling.** The first 100-epoch window with buyback data (ending
2026-03-15) shows 2.5%; the peak is 16.5% (2026-09-19); the
latest is 11.8%. The history is too short to fit a trend.

**NEAR Intents is not growing.** Comparing the first and last 30 days of the year to 2026-11-12
(DefiLlama): daily Intents volume is 1.02x, gross Intents fees 0.75x, and
NEAR gas fees in USD 0.62x. Within the year volume fell to a weekly low of
$51M a day and has recovered to $130M, so the year-on-year figure hides a round trip,
not steady growth. The buyback flow exists because capture was switched on in February 2026. At today's capture share, break-even needs
8.5x the volume.

**The payback is concentrated.** One application supplies over 90% of it. A fee cut, exploit
or loss of flow at NEAR Intents removes most of the thesis.

**Burn alone is far from break-even.** 0.92% of issuance, 109x away.

**The history is short and needed one exclusion.** Buybacks began on 2026-02-23. One gain of
604,559 NEAR was excluded by a mechanical rule (more than 20 times the median of the previous
100 epochs). The chain shows what it was: across that epoch, heights 214890733 to 214933933,
the other two revenue wallets fell by 501,917 NEAR (`data/wallets.csv`). That is revenue
captured earlier moving between wallets. The rule removes the whole gain, slightly more than
the matched outflow, which lowers payback. The transfer itself is inferred from balances; the
sender check above does not reach back that far.

**Buyback size depends on the NEAR price.** Fee revenue is earned mostly in dollar terms and
arrives as NEAR, so the same revenue is fewer NEAR at a higher price. This is arithmetic, not
something the repo tests.

**Third-party inputs.** Attribution of inflows uses NearBlocks, and the USD context uses
DefiLlama and CoinGecko. None of these feed mint, burn, the buyback gain or payback. DefiLlama's
NEAR page states that 70% of gas fees are burnt; the live protocol config has
`burnt_gas_reward` at 0. Over the same days DefiLlama reports 978 NEAR a day in
gas fees and 684 burnt, against 826 measured from the chain. We report the
difference and do not explain it.

**Sampling.** Utilization and the ceiling use 3 blocks per epoch and are reported only as
100-epoch aggregates.

## Pre-registered rounds and what would change our mind

Each file in `predictions/` is a round: a forecast frozen at one block height about the epochs
after it. `run.py freeze` writes a round from the newest cached epoch and never overwrites one.
Rounds are short on purpose, so the chain has scored them by the time this is judged.

(no rounds frozen yet)

Each round commits to three intervals for its window: payback, total NEAR burnt and total NEAR
gained by the buyback account. An interval is the last same-length window's value scaled by how
much consecutive windows have differed historically. "Held in the past" is how often that
procedure, run at earlier dates on data available then, contained the outcome
(`claims_backtest` in `out/results.json`).

- If payback over a round's window falls outside its interval, `run.py` prints `FALSIFIED` for
  that round. A 90% interval misses about one time in ten even when the model is right; we
  accept that.
- The other two claims are reported as `HIT` or `MISS`. The burn interval has held less often
  than its nominal 90%, so a burn miss is weaker evidence than a payback miss.
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

- the buyback account balance keeps falling. It has fallen in 1 of 662 epochs so far
  (10,283 NEAR in total), so a single further outflow would not, but a run of them would;
- payback over a 100-epoch window drops below half of 11.8%;
- transfers into the buyback account stop coming from `intents.near`.

## What this implies for the long term

The investment question is whether the flows that offset issuance can grow about 8.5x. The
evidence supports a conditional answer, not a forecast:

| Path to break-even | What it requires |
|---|---|
| Growth alone, issuance unchanged | burn plus buybacks growing 104% a year for 3 years, 53% for 5, or 24% for 10 |
| Capture all gross Intents fees, at today's volume | payback of 49%; the rest must come from growth or lower issuance |
| Lower issuance to 1.6% a year (HSP-029) | the multiple falls to 5.4x at today's flows |

HSP-029 is the issuance lever being pulled now. It lowers maximum issuance from 2.5% to 1.6% a
year over 24 months. NEAR's House of Stake passed it on 2026-11-02; it still needs the Security
Council veto window to close and validators to adopt it
(https://gov.near.org/t/hsp-029-establish-a-24-month-issuance-ramp-to-a-1-6-target-rate-of-near-token-emissions/42644).
This repo does not model the ramp; the row above only rescales today's multiple.

For: the flow exists, is measurable on chain, scales with a product's volume (correlation
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
| Issuance rate | NEAR governance | proportional: 2.5% to 1.6% takes it from 8.5x to 5.4x |
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
