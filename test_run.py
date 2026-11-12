#!/usr/bin/env python3
"""Self-check for the scoring maths. Usage: python3 test_run.py"""
import math
import run

assert run.quantile([1, 2, 3, 4, 5], 0.5) == 3
assert run.quantile([0, 10], 0.1) == 1
a, b = run.ols([0, 1, 2, 3], [1, 3, 5, 7])
assert abs(a - 1) < 1e-12 and abs(b - 2) < 1e-12
assert run.pinball(2.0, 1.0, 0.9) == 0.9 and abs(run.pinball(1.0, 2.0, 0.9) - 0.1) < 1e-12
assert run.sig(0.123456789) == 0.123457 and run.sig({"a": [1.23456789e-9]}) == {"a": [1.23457e-9]}

# ledger: claims are scored only when all 30 epochs have closed, and the payback claim sets the verdict
later = [{"y": math.log(100.0), "burn": 100 * run.Y, "buy": 900 * run.Y, "mint": 10000 * run.Y} for _ in range(run.H)]
per_epoch = [[90.0, 100.0, 110.0]] * run.H
commit = {"claims": {"payback": [0.08, 0.1, 0.12], "burn_total": [2000.0, 3000.0, 3500.0], "buyback_total": [1.0, 2.0, 3.0]},
          "table_model": "persistence", "models": {"persistence": per_epoch, "clock": per_epoch, "price": per_epoch}}
led = run.ledger(later, commit)
assert led["verdict"] == "PASS" and abs(led["claims"]["payback"]["actual"] - 0.1) < 1e-12
assert led["claims"]["burn_total"]["verdict"] == "HIT" and led["claims"]["buyback_total"]["verdict"] == "MISS"
assert led["hits"] == run.H
commit["claims"]["payback"] = [0.2, 0.3, 0.4]
assert run.ledger(later, commit)["verdict"] == "FALSIFIED"
assert run.ledger(later[:5], commit)["verdict"] == "PENDING" and run.ledger([], commit)["verdict"] == "PENDING"
later[3]["buy"] = None  # a missing balance must not be scored as zero
assert run.ledger(later, commit)["verdict"] == "PENDING"
print("SELFTEST PASS")
