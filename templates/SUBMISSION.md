# Submission kit

Everything needed to submit. Numbers below are filled from `out/results.json`.

## Description (paste into the form, under 2,000 characters)

Coverage: what offsets NEAR's issuance, measured from the chain with no keys.

NEAR mints about 2.5% of supply a year. Counting only the gas-fee burn, under 1% of that comes back, so break-even looks __BURN_MULT__x away. Since April 2026 the NEAR Intents contract has been sending NEAR to buybacks.multisignature.near. Counting burn plus that buyback flow, __PAYBACK__ of issuance is offset and break-even is __MULT__x away.

Since 27 October more Intents swaps settle privately (found by another entry, Tideline), so public swap data misses their fees. The buyback account is a mainnet balance and still does: __PS_BUY__ NEAR a day since, against __PB_BUY__ before.

What makes it checkable:
- One command, `python3 run.py`: no keys, no network, no dependencies. It prints a hash that must match the README.
- `python3 verify.py 3 <your seed>` refetches random epochs from mainnet and requires an exact match with the cache.
- `python3 test_run.py`: the command refuses a cache with one yoctoNEAR changed, and edited predictions.
- Audit: all __W_RECEIPTS__ receipts of the buyback account reconcile with chain balances to the yoctoNEAR in __W_EXACT__ of __W_BUSY__ transfer-only epochs. intents.near sent __W_TOP1_SHARE__ of the NEAR; __W_PAID_SHARE__ has left; __C_CONF__ of __C_KEYS__ keys can move it.
- BigQuery SQL in queries/, results committed: the chain got quieter; intents.near's receipts grew 2.8x.
- Verdict: not yet a supply story. The bet is governance: fee capture and HSP-029.
- The bear case has equal weight in THESIS.md: buybacks are held, not burnt; payback has fallen from __PAY_PEAK__ to __PAYBACK__; Intents volume is flat year on year; one app supplies over 90% of the flow.

The outside judge is the chain. Forecast rounds in predictions/ commit to ranges for payback, burn and buyback gain after a fixed height, each timestamped in Bitcoin with OpenTimestamps. They close during judging: `python3 fetch.py --epochs 45 && python3 run.py` prints PASS or FALSIFIED per round, and refuses any round it cannot re-derive exactly. An hourly job scores them as they close.

## X post (attach the video; fits 280 characters)

Built at NEAR HACKATHON: NEAR's burn covers __BURN_COV__ of issuance. With Intents buybacks: __PAYBACK__. Break-even is __MULT__x away, not __BURN_MULT__x.

Swaps went private; the buyback balance still shows revenue.

No keys: python3 run.py

@NEARProtocol #NEARHackathon
https://github.com/nice-bills/Coverage

(Reply to it with: the dashboard https://nice-bills.github.io/Coverage/ ; "Forecasts frozen and
Bitcoin-timestamped on 12 Nov; mainnet scores them during judging"; and "The three rounds close
14 to 18 Nov; the live scoreboard is on the dashboard".)

## Demo video (72 seconds)

Rendered from code, every frame from real screens and real numbers: `film/` (brief, shot list,
composition, renderer, score). Rebuild with `cd film && python3 build.py && node render.js video 30 && python3 sound.py`,
then mux (see `film/voiceover.md`). It works on mute; the optional voiceover script is in `film/voiceover.md`.

| Time | Beat | On screen |
|---|---|---|
| 0:00 | Hook | Fee-burn dashboards say NEAR burns back __BURN_COV__ |
| 0:05 | Problem | Right number, wrong layer: the minted bar with a sliver of burn |
| 0:10 | Reveal | Intents buybacks grow the bar to __PAYBACK__; break-even __MULT__x, not __BURN_MULT__x |
| 0:18 | Product | The live dashboard |
| 0:24 | Proof | `python3 run.py`, the hash matches the README |
| 0:32 | Proof | Every epoch since February, from block headers |
| 0:39 | Proof | BigQuery: the chain got quieter, Intents grew |
| 0:46 | Future | Break-even turns on two votes: fee capture and HSP-029 |
| 0:53 | Live | Forecasts frozen in Bitcoin, inside their ranges so far, closing 14 to 18 Nov |
| 1:01 | Verdict | Not yet a supply story. The bet is governance. |
| 1:07 | Close | URL and `python3 run.py` |

## Checklist

Already done: the repo is public, GitHub Pages serves the dashboard, and the scheduled `pages`
workflow fetches new epochs, scores the frozen rounds, upgrades their Bitcoin timestamps and
commits every hour during judging (freezing new rounds is paused until 25 Nov). The first round
closes about 14 November 07:00 UTC and is scored within the hour.

Left before Saturday 14 November, 23:59 UTC:

- [ ] Record the video and post on X with the text above.
- [ ] Submit: repo URL, X post URL, description, NEAR mainnet payout account.
- [ ] Leave the repo public and Pages enabled until at least 25 November 2026.
