# Submission kit

Everything needed to submit. Numbers below are filled from `out/results.json`.

## Description (paste into the form, under 2,000 characters)

Coverage: what offsets NEAR's issuance, measured from the chain with no keys.

NEAR mints about 2.5% of supply a year. Fee-burn dashboards say under 1% of that comes back, so break-even looks 108x away. That measures one layer. Since February 2026 the NEAR Intents contract has been sending NEAR to buybacks.multisignature.near. Counting burn plus that buyback flow, 12.0% of issuance is offset and break-even is 8.4x away.

What makes it checkable:
- One command, `python3 run.py`: no keys, no network, no dependencies. It prints a result hash that must equal the one in the README.
- `python3 verify.py 3 <your seed>` refetches random epochs from mainnet, requires an exact match with the cache, and checks block by block that supply fell by the fees burnt.
- `python3 test_run.py` shows the command refuses a cache with one yoctoNEAR changed and refuses edited predictions.
- Attribution: 2979 of the last 2996 transfers into the buyback account come from intents.near. A separate pipeline (DefiLlama, via Dune) gives 13,589 NEAR a day for all revenue wallets; ours gives 13,984.
- The bear case has equal weight in THESIS.md: buybacks are held, not burnt; payback has fallen from 16.5% to 12.0%; Intents volume is flat year on year; one app supplies over 90% of the flow.

The outside judge is the chain. Short forecast rounds in predictions/ commit to intervals for payback, burn and buyback gain over the epochs after a fixed height, each timestamped in Bitcoin with OpenTimestamps. They close before and during judging: `python3 fetch.py --epochs 45 && python3 run.py` prints PASS or FALSIFIED per round. The command refuses a round that is not exactly what the code derives from the data up to its height, so we cannot edit the outcome. Round hashes: round-224265136-h05.json e4cf5acdca0e2f74153a91c93febba9a185b9c7b0e1c2a0edc97df11db7530ba; round-224265136-h10.json 2c738b805dd13904d226f2511ebb437fb7780f908a96e79c6a3f2cedab39321f; round-224265136-h20.json 926ba45df2401210a5d871b512caddbd92f41fca761cbcebf02d53814c9bddf5

## X post (attach the video)

NEAR's burn offsets 0.92% of its issuance. Burn plus NEAR Intents buybacks: 12.0%.

Measured from the chain, break-even is 8.4x away, not 108x.

No keys: python3 run.py
Forecasts frozen and Bitcoin-timestamped; mainnet scores them this week.

https://github.com/nice-bills/Coverage

(Reply to it with the demo link and the round hashes: round-224265136-h05.json e4cf5acdca0e2f74153a91c93febba9a185b9c7b0e1c2a0edc97df11db7530ba; round-224265136-h10.json 2c738b805dd13904d226f2511ebb437fb7780f908a96e79c6a3f2cedab39321f; round-224265136-h20.json 926ba45df2401210a5d871b512caddbd92f41fca761cbcebf02d53814c9bddf5)

## 60-second video

| Time | Screen | Say |
|---|---|---|
| 0:00 | Dashboard headline | "Every NEAR dashboard says the token burns back under one percent of what it mints. That number is right, and it measures the wrong layer." |
| 0:08 | Terminal: `git clone`, `python3 run.py` | "One command. No keys, no network. It rebuilds every number and prints a hash." |
| 0:18 | Terminal last line next to README hash | "The hash matches the README. Change one yoctoNEAR in the cache and the command refuses to run." |
| 0:25 | Terminal: `python3 verify.py 3 2026` | "Pick any seed. It pulls random epochs from mainnet and they must match the cache exactly." |
| 0:35 | Dashboard tiles and the chain-versus-indexer table | "Counting the NEAR Intents buyback flow, 12.0% of issuance is offset and break-even is 8.4 times away. A separate pipeline at DefiLlama gives nearly the same total." |
| 0:45 | Lever calculator: drag capture share, then volume | "Two of the three levers are governance decisions." |
| 0:52 | Ledger table and THESIS.md 'Evidence against' | "The bear case is in the repo: buybacks are held, not burnt, and payback has been falling. The forecasts are frozen, and mainnet scores them during judging. If we are wrong, the page says FALSIFIED." |

## Checklist

Before submitting (Saturday 14 November, before 23:59 UTC):

- [ ] Create a public GitHub repo and push `main`. Do this as early as possible: the push time is
      one of the independent timestamps on the forecast rounds.
- [ ] Settings, Pages: source "GitHub Actions". The `pages` workflow publishes the dashboard and
      rescoring every 6 hours. Put the Pages URL at the top of `templates/README.md`.
- [ ] Refresh the scores so the first round (closes about 14 November 07:00 UTC) shows its result:

      python3 fetch.py --epochs 45
      python3 run.py
      python3 docs.py
      uvx --from opentimestamps-client ots upgrade predictions/*.ots
      git add -A && git commit -m "Score round 1; upgrade timestamps" && git push

- [ ] Optional: freeze one more round at submission time so a fresh one closes during judging
      (16 to 18 November): `python3 run.py freeze 10`, then stamp it with
      `uvx --from opentimestamps-client ots stamp predictions/<new file>`, rerun `run.py` and
      `docs.py`, commit and push. The README hash changes; `docs.py` updates it.
- [ ] Record the video, post on X with the text above, add repo and demo links.
- [ ] Submit: repo URL, X post URL, description, NEAR mainnet payout account.
- [ ] Leave the repo public and Pages enabled until at least 25 November 2026.
