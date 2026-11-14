# Submission kit

Everything needed to submit. Numbers below are filled from `out/results.json`.

## Description (paste into the form, under 2,000 characters)

Coverage: what offsets NEAR's issuance, measured from the chain with no keys.

NEAR mints about 2.5% of supply a year. Counting only the gas-fee burn, under 1% of that comes back, so break-even looks 108x away. Since April 2026 the NEAR Intents contract has been sending NEAR to buybacks.multisignature.near. Counting burn plus that buyback flow, 12.0% of issuance is offset and break-even is 8.4x away.

Since 27 October more Intents swaps settle privately (found by another entry, Tideline), so public swap data misses their fees. The buyback account is a mainnet balance and still does: 10,452 NEAR a day since, against 9,298 before.

What makes it checkable:
- `python3 run.py`: no keys, no network, no dependencies. It prints a hash that must match the README.
- `python3 verify.py 3 <your seed>` refetches random epochs from mainnet; they must match the cache exactly.
- `python3 test_run.py`: the command refuses a cache with one yoctoNEAR changed, and edited predictions.
- Audit: all 3,374 receipts of the buyback account match chain balances to the yoctoNEAR in 658 of 658 transfer-only epochs. intents.near sent 77.2% of the NEAR; 0.53% has left; 2 of 4 keys can move it.
- BigQuery SQL in queries/, results committed: the chain got quieter; intents.near's receipts grew 2.8x.
- Verdict: not yet a supply story. The bet is governance: fee capture, HSP-029.
- The bear case has equal weight in THESIS.md: buybacks are held, not burnt; payback has fallen from 16.5% to 12.0%; Intents volume is flat year on year; one app supplies over 90% of the flow.

The outside judge is the chain. Forecast rounds in predictions/ commit to ranges for payback, burn and buyback gain after a fixed height, each timestamped in Bitcoin with OpenTimestamps. They close 14 to 18 Nov, through judging: `python3 fetch.py --epochs 45 && python3 run.py` prints PASS or FALSIFIED per round, and refuses any round it cannot re-derive exactly. A scheduled job scores each as it closes.

## X post (attach the video or screenshots; fits 280 characters)

Built at NEAR HACKATHON: NEAR's burn covers 0.92% of issuance. With Intents buybacks: 12.0%. Break-even is 8.4x away, not 108x.

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
| 0:00 | Hook | Fee-burn dashboards say NEAR burns back 0.92% |
| 0:05 | Problem | Right number, wrong layer: the minted bar with a sliver of burn |
| 0:10 | Reveal | Intents buybacks grow the bar to 12.0%; break-even 8.4x, not 108x |
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
commits every hour during judging (freezing new rounds is paused until 25 Nov). Each round
is scored within the hour of closing; its status is in the README's round table.

Left before Saturday 14 November, 23:59 UTC (judging is 16 to 18 November; results by 18 November, 23:59 UTC):

- [x] Posted on X with the video, as a 7-post thread (film/thread.md): https://x.com/willIsbillls/status/2121603731192160642
- [ ] Submit: repo URL, X post URL (above), description, NEAR mainnet payout account.
- [ ] Leave the repo public and Pages enabled until at least 25 November 2026.
