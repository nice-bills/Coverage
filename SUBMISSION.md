# Submission kit

Everything needed to submit. Numbers below are filled from `out/results.json`.

## Description (paste into the form, under 2,000 characters)

Coverage: what offsets NEAR's issuance, measured from the chain with no keys.

NEAR mints about 2.5% of supply a year. Counting only the gas-fee burn, under 1% of that comes back, so break-even looks 108x away. Since April 2026 the NEAR Intents contract has been sending NEAR to buybacks.multisignature.near. Counting burn plus that buyback flow, 12.0% of issuance is offset and break-even is 8.4x away.

Since 27 October a growing share of Intents swaps settles privately (found by another entry, Tideline), so public swap data no longer shows their fees. The buyback account is a mainnet balance and still does: 10,452 NEAR a day since, against 9,298 before.

What makes it checkable:
- One command, `python3 run.py`: no keys, no network, no dependencies. It prints a result hash that must equal the one in the README.
- `python3 verify.py 3 <your seed>` refetches random epochs from mainnet and requires an exact match with the cache.
- `python3 test_run.py` shows the command refuses a cache with one yoctoNEAR changed and refuses edited predictions.
- Audit: all 3,374 receipts of the buyback account reconcile with chain balances to the yoctoNEAR in 658 of 658 transfer-only epochs. intents.near sent 77.2% of the NEAR; 0.53% has left; 2 of 4 keys can move it.
- The bear case has equal weight in THESIS.md: buybacks are held, not burnt; payback has fallen from 16.5% to 12.0%; Intents volume is flat year on year; one app supplies over 90% of the flow.

The outside judge is the chain. Short forecast rounds in predictions/ commit to intervals for payback, burn and buyback gain over the epochs after a fixed height, each timestamped in Bitcoin with OpenTimestamps. They close before and during judging: `python3 fetch.py --epochs 45 && python3 run.py` prints PASS or FALSIFIED per round. The command refuses any round it cannot re-derive exactly, so outcomes cannot be edited. A scheduled job freezes and commits a new round about daily.

## X post (attach the video; fits 280 characters)

Built at NEAR HACKATHON: NEAR's burn covers 0.92% of issuance. With Intents buybacks: 12.0%. Break-even is 8.4x away, not 108x.

Swaps went private; the buyback balance still shows revenue.

No keys: python3 run.py

@NEARProtocol #NEARHackathon
https://github.com/nice-bills/Coverage

(Reply to it with: the dashboard https://nice-bills.github.io/Coverage/ ; "Forecasts frozen and
Bitcoin-timestamped on 12 Nov; mainnet scores them during judging"; and the round hashes from
the README.)

## 60-second video

| Time | Screen | Say |
|---|---|---|
| 0:00 | Dashboard headline | "Every NEAR dashboard says the token burns back under one percent of what it mints. That number is right, and it measures the wrong layer." |
| 0:08 | Terminal: `git clone`, `python3 run.py` | "One command. No keys, no network. It rebuilds every number and prints a hash." |
| 0:18 | Terminal last line next to README hash | "The hash matches the README. Change one yoctoNEAR in the cache and the command refuses to run." |
| 0:25 | Terminal: `python3 verify.py 3 2026` | "Pick any seed. It pulls random epochs from mainnet and they must match the cache exactly." |
| 0:30 | Dashboard: click "Check a random epoch" | "The page does the same check in your browser: block headers and the buyback balance from mainnet; mint, burn and buyback gain equal to the yoctoNEAR." |
| 0:38 | Dashboard epoch tape and the chain-versus-indexer table | "Counting the NEAR Intents buyback flow, 12.0% of issuance is offset and break-even is 8.4 times away. A separate pipeline at DefiLlama gives nearly the same total." |
| 0:45 | Lever calculator: drag capture share, then volume | "Two of the three levers are governance decisions." |
| 0:52 | Ledger table and THESIS.md 'Evidence against' | "The bear case is in the repo: buybacks are held, not burnt, and payback has been falling. The forecasts are frozen, and mainnet scores them during judging. If we are wrong, the page says FALSIFIED." |

## Checklist

Already done: the repo is public, GitHub Pages serves the dashboard, and the scheduled `pages`
workflow fetches new epochs, scores the frozen rounds, upgrades their Bitcoin timestamps, freezes a
new round about daily and commits every 6 hours. The first round closes about 14 November
07:00 UTC and is scored by the next run after that.

Left before Saturday 14 November, 23:59 UTC:

- [ ] Record the video and post on X with the text above.
- [ ] Submit: repo URL, X post URL, description, NEAR mainnet payout account.
- [ ] Leave the repo public and Pages enabled until at least 25 November 2026.
