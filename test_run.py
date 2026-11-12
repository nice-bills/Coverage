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

# ledger: perfect medians inside a tight interval beat a model that is off by 2x
later = [{"y": math.log(100.0), "burn": 100 * run.Y} for _ in range(run.H)]
good, off = [[90.0, 100.0, 110.0]] * run.H, [[180.0, 200.0, 220.0]] * run.H
led = run.ledger(later, {"models": {"usage": good, "price": off, "persistence": off}})
assert led["hits"] == run.H and led["loss"]["usage"] < led["loss"]["price"]
assert led["verdict"] == "FALSIFIED"  # 30 of 30 hits is outside the 20-28 calibration band: too wide is a fail too
assert run.ledger(later[:5], {"models": {"usage": good, "price": off, "persistence": off}})["verdict"] == "PENDING"
print("SELFTEST PASS")
