# Submission kit

Everything needed to submit. Numbers below are filled from `out/results.json`.

## Description (paste into the form, under 2,000 characters)

Coverage: what NEAR pays back, measured from the chain with no keys.

NEAR mints about 2.5% of supply a year. Fee-burn dashboards say under 1% of that comes back, so break-even looks __BURN_MULT__x away. That measures the wrong layer. Since February 2026, NEAR Intents fee revenue buys NEAR into buybacks.multisignature.near. Counting burn plus buybacks, NEAR pays back __PAYBACK__ of issuance and break-even is __MULT__x away.

What makes it checkable:
- One command, `python3 run.py`: no keys, no network, no dependencies. It prints a result hash that must equal the one in the README.
- Mint and burn are read from block-header total_supply and reconcile to the yoctoNEAR across __EPOCHS__ epochs; the command fails if one cached number is wrong.
- `python3 verify.py 3 <your seed>` refetches random epochs from mainnet and requires an exact match.
- An independent pipeline agrees: our all-wallet figure is __ALL_USD__ a day, DefiLlama's is __LLAMA_BUY__.
- The bear case is in THESIS.md with the same weight: buybacks are held, not burnt; Intents volume is flat year on year; one app supplies over 90% of the payback.

The outside judge is the chain. predictions.json holds 30 epochs of burn forecasts and a buyback interval, frozen at height __LAST_HEIGHT__. Its sha256 is __PRED_HASH__. As epochs close during judging, `python3 fetch.py --epochs 45 && python3 run.py` prints PASS or FALSIFIED. We cannot edit the outcome: the command refuses to score unless predictions.json is exactly what the code derives from the frozen data.

## X post (attach the video)

NEAR pays back __PAYBACK__ of its issuance, not __BURN_COV__.

Fee-burn dashboards miss the NEAR Intents buybacks. Counted from the chain, break-even is __MULT__x away, not __BURN_MULT__x.

One command, no keys: python3 run.py
Predictions frozen, scored by mainnet during judging.
sha256 __PRED_HASH__

[repo link] [demo link]

## 60-second video

| Time | Screen | Say |
|---|---|---|
| 0:00 | Dashboard headline | "Every NEAR dashboard says the token burns back under one percent of what it mints. That number is right, and it measures the wrong layer." |
| 0:08 | Terminal: `git clone`, `python3 run.py` | "One command. No keys, no network. It rebuilds every number and prints a hash." |
| 0:18 | Terminal last line next to README hash | "The hash matches the README. Mint and burn reconcile to the yoctoNEAR or the command fails." |
| 0:25 | Terminal: `python3 verify.py 3 2026` | "Pick any seed. It pulls random epochs from mainnet and they must match the cache exactly." |
| 0:35 | Dashboard tiles and the chain-versus-indexer table | "Counting NEAR Intents buybacks, payback is __PAYBACK__ and break-even is __MULT__ times away. DefiLlama's separate pipeline lands within a few percent." |
| 0:45 | Lever calculator: drag capture share, then volume | "Two of the three levers are governance decisions." |
| 0:52 | Ledger table and THESIS.md 'Evidence against' | "The bear case is in the repo. And the forecasts are frozen: mainnet scores them during judging. If we are wrong, the page says FALSIFIED." |

## Checklist

- [ ] Create a public GitHub repo and push `main`.
- [ ] Settings, Pages: source "GitHub Actions". The `pages` workflow publishes the dashboard and rescoring every 6 hours.
- [ ] Record the video, post on X with the text above, add repo and demo links.
- [ ] Submit: repo URL, X post URL, description, NEAR mainnet payout account.
- [ ] Leave the repo public and Pages enabled until at least 25 November 2026.
