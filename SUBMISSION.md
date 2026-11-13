# Submission kit

Everything needed to submit. Numbers below are filled from `out/results.json`.

## Description (paste into the form, under 2,000 characters)

Coverage: what offsets NEAR's issuance, measured from the chain with no keys.

NEAR mints about 2.5% of supply a year. Fee-burn dashboards say under 1% of that comes back, so break-even looks 108x away. Since February 2026 the NEAR Intents contract has been sending NEAR to buybacks.multisignature.near. Counting burn plus that buyback flow, 12.0% of issuance is offset and break-even is 8.4x away.

Since 27 October a growing share of Intents swaps settles privately (found by another entry, Tideline), so public swap data no longer shows their fees. The buyback account is a mainnet balance and still does: 10,452 NEAR a day since, against 9,298 before.

What makes it checkable:
- One command, `python3 run.py`: no keys, no network, no dependencies. It prints a result hash that must equal the one in the README.
- `python3 verify.py 3 <your seed>` refetches random epochs from mainnet and requires an exact match with the cache.
- `python3 test_run.py` shows the command refuses a cache with one yoctoNEAR changed and refuses edited predictions.
- Attribution: 2979 of the last 2996 transfers into the buyback account come from intents.near. A separate pipeline (DefiLlama, via Dune) gives 13,589 NEAR a day for all revenue wallets; ours gives 13,984.
- The bear case has equal weight in THESIS.md: buybacks are held, not burnt; payback has fallen from 16.5% to 12.0%; Intents volume is flat year on year; one app supplies over 90% of the flow.

The outside judge is the chain. Short forecast rounds in predictions/ commit to intervals for payback, burn and buyback gain over the epochs after a fixed height, each timestamped in Bitcoin with OpenTimestamps. They close before and during judging: `python3 fetch.py --epochs 45 && python3 run.py` prints PASS or FALSIFIED per round. The command refuses any round the code cannot re-derive exactly, so we cannot edit the outcome. Hashes are in the README.

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
| 0:30 | Dashboard: click "Check a random epoch" | "The page does the same check in your browser: three block headers from mainnet, mint and burn equal to the yoctoNEAR." |
| 0:38 | Dashboard epoch tape and the chain-versus-indexer table | "Counting the NEAR Intents buyback flow, 12.0% of issuance is offset and break-even is 8.4 times away. A separate pipeline at DefiLlama gives nearly the same total." |
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
