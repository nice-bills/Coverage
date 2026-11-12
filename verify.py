#!/usr/bin/env python3
"""Spot-check the committed cache against NEAR mainnet. No keys.

Usage: python3 verify.py [n] [seed]
Refetches n random epochs (default 3) from the chain and requires every field to match
data/epochs.csv exactly, and the buyback balance to match data/buybacks.csv. It also checks,
on two random blocks per epoch, that total_supply fell by exactly the fees burnt in that block. Pick your own seed so the check is one we could not have prepared for.
"""
import csv, random, sys, time
import fetch

print(f"verify.py n={sys.argv[1] if len(sys.argv) > 1 else 3} at {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC, "
      f"sources {fetch.RPC} and {fetch.NEARDATA}")

n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
seed = int(sys.argv[2]) if len(sys.argv) > 2 else int(time.time())
rows = list(csv.DictReader(open(fetch.OUT)))
bal = {r["end_height"]: r["balance"] for r in csv.DictReader(open(fetch.BOUT))}
bad = blocks = 0
rnd = random.Random(seed)
for r in rnd.sample(rows, n):
    got, _ = fetch.fetch_epoch(fetch.block(int(r["end_height"])))
    ok = all(str(got[k]) == r[k] for k in fetch.FIELDS)
    if r["end_height"] in bal:  # the buyback account balance at this epoch's last block
        ok = ok and str(fetch.balance(int(r["end_height"])) or 0) == bal[r["end_height"]]
    # The premise behind every number: a block's total_supply is its parent's minus the fees burnt in it.
    # Checked on two random blocks inside the epoch, each against its parent fetched by hash.
    for h in rnd.sample(range(int(r["start_height"]) + 1, int(r["end_height"])), 2):
        while (b := fetch.block(h)) is None and h < int(r["end_height"]):
            h += 1  # skipped height: take the next block, but never leave the epoch
        if b is None or b["header"]["height"] > int(r["end_height"]):
            continue
        parent = fetch.block(b["header"]["prev_hash"])
        ok = ok and int(parent["header"]["total_supply"]) - int(b["header"]["total_supply"]) == fetch.burnt(b)
        blocks += 1
    bad += not ok
    print(f"epoch {r['start_height']}-{r['end_height']}: {'MATCH' if ok else 'MISMATCH'}"
          f"  mint={int(r['mint']) / 1e24:.3f} burn={int(r['burn']) / 1e24:.3f} NEAR")
print(f"VERIFY seed={seed} {'PASS' if not bad else 'FAIL'} ({n - bad}/{n} epochs match the chain, "
      f"{blocks} blocks checked against their parents)")
sys.exit(bad)
