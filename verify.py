#!/usr/bin/env python3
"""Spot-check the committed cache against NEAR mainnet. No keys.

Usage: python3 verify.py [n] [seed]
Refetches n random epochs (default 3) from the chain and requires every field to match
data/epochs.csv exactly. Pick your own seed so the check is one we could not have prepared for.
"""
import csv, random, sys, time
import fetch

n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
seed = int(sys.argv[2]) if len(sys.argv) > 2 else int(time.time())
rows = list(csv.DictReader(open(fetch.OUT)))
bad = 0
for r in random.Random(seed).sample(rows, n):
    got, _ = fetch.fetch_epoch(fetch.block(int(r["end_height"])))
    ok = all(str(got[k]) == r[k] for k in fetch.FIELDS)
    bad += not ok
    print(f"epoch {r['start_height']}-{r['end_height']}: {'MATCH' if ok else 'MISMATCH'}"
          f"  mint={int(r['mint']) / 1e24:.3f} burn={int(r['burn']) / 1e24:.3f} NEAR")
print(f"VERIFY seed={seed} {'PASS' if not bad else 'FAIL'} ({n - bad}/{n} epochs match the chain)")
sys.exit(bad)
