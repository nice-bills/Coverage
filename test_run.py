#!/usr/bin/env python3
"""Self-check: scoring maths, then an end-to-end run with tamper checks. Usage: python3 test_run.py"""
import math
import run

assert run.quantile([1, 2, 3, 4, 5], 0.5) == 3
assert run.quantile([0, 10], 0.1) == 1
a, b = run.ols([0, 1, 2, 3], [1, 3, 5, 7])
assert abs(a - 1) < 1e-12 and abs(b - 2) < 1e-12
assert run.pinball(2.0, 1.0, 0.9) == 0.9 and abs(run.pinball(1.0, 2.0, 0.9) - 0.1) < 1e-12
assert run.sig(0.123456789) == 0.123457 and run.sig({"a": [1.23456789e-9]}) == {"a": [1.23457e-9]}

# lump rule: one gain 50x the trailing median is excluded; ordinary gains and unknown balances are left alone
rows = [{"raw_buy": 100, "buy": 100} for _ in range(40)]
rows[30] = {"raw_buy": 5000, "buy": 5000}
rows[35] = {"raw_buy": None, "buy": None}
rows[5] = {"raw_buy": 5000, "buy": 5000}  # fewer than 10 earlier epochs: not judged
run.mark_lumps(rows)
assert [i for i, r in enumerate(rows) if r["lump"]] == [30] and rows[30]["buy"] == 0 and rows[31]["buy"] == 100

# window claims: a perfectly steady history gives a zero-width interval at the last value, and it always held
steady = [{"burn": 2 * run.Y, "buy": 8 * run.Y, "mint": 100 * run.Y} for _ in range(200)]
claims, held = run.window_claims(steady, run.H)
assert claims["payback"] == [0.1, 0.1, 0.1] and claims["burn_total"][1] == 2.0 * run.H
assert held["payback"]["hit"] == held["payback"]["n"] > 0

# ledger: claims are scored only when all 30 epochs have closed, and the payback claim sets the verdict
later = [{"y": math.log(100.0), "burn": 100 * run.Y, "buy": 900 * run.Y, "mint": 10000 * run.Y, "t1_ns": 0} for _ in range(run.H)]
per_epoch = [[90.0, 100.0, 110.0]] * run.H
commit = {"horizon_epochs": run.H, "after_end_height": 1, "claims": {"payback": [0.08, 0.1, 0.12], "burn_total": [2000.0, 3000.0, 3500.0], "buyback_total": [1.0, 2.0, 3.0]},
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

# end to end, on a copy of the repo: the real cache must pass, and tampering must make the command fail
import json, os, shutil, subprocess, sys, tempfile
src = os.path.dirname(os.path.abspath(__file__))
with tempfile.TemporaryDirectory() as tmp:
    for f in ("run.py", "dashboard.py", "bq.py", "queries", "data"):
        (shutil.copytree if f in ("data", "queries") else shutil.copy)(os.path.join(src, f), os.path.join(tmp, f))
    go = lambda: subprocess.run([sys.executable, "run.py"], cwd=tmp, capture_output=True, text=True)
    first = go()
    assert first.returncode == 0, first.stderr
    result = first.stdout.splitlines()[-1]
    assert result.startswith("RESULT sha256=")
    # freeze two rounds: the result must not change and the ledger must appear
    fr = subprocess.run([sys.executable, "run.py", "freeze", "5", "10"], cwd=tmp, capture_output=True, text=True)
    assert fr.returncode == 0 and fr.stdout.count("ROUND ") == 2, fr.stderr
    frozen = go()
    assert frozen.returncode == 0 and frozen.stdout.splitlines()[-1] == result and frozen.stdout.count("-> PENDING") >= 2
    # a frozen round is never rewritten
    assert subprocess.run([sys.executable, "run.py", "freeze", "5"], cwd=tmp, capture_output=True).returncode != 0
    # an edited round is refused
    name = sorted(os.listdir(os.path.join(tmp, "predictions")))[0]
    p = json.load(open(os.path.join(tmp, "predictions", name)))
    p["claims"]["payback"][0] /= 2
    json.dump(p, open(os.path.join(tmp, "predictions", name), "w"))
    assert go().returncode != 0
    shutil.rmtree(os.path.join(tmp, "predictions"))
    # an edited cache row is refused
    path = os.path.join(tmp, "data", "epochs.csv")
    lines = open(path).read().splitlines()
    cells = lines[50].split(",")
    cells[8] = str(int(cells[8]) + 1)  # one yoctoNEAR added to one epoch's mint
    lines[50] = ",".join(cells)
    open(path, "w").write("\n".join(lines) + "\n")
    assert go().returncode != 0
# every file in data/ is listed in data/sources.json with the sha256 it has now
import hashlib
_d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_src = json.load(open(os.path.join(_d, "sources.json")))
for _f in sorted(os.listdir(_d)):
    if _f != "sources.json" and os.path.isfile(os.path.join(_d, _f)):  # data/bq/ holds optional BigQuery exports, checked below
        assert _src[_f]["sha256"] == hashlib.sha256(open(os.path.join(_d, _f), "rb").read()).hexdigest(), _f

# The buyback account reconciles: in every epoch where it only received or sent transfers, receipts
# sum to the balance change read from the chain, to the yoctoNEAR.
_w = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "results.json"))).get("wallet")
if _w:
    assert _w["quiet_exact"] == _w["epochs_quiet"] and _w["quiet_worst_yocto"] == "0", _w
    assert abs(_w["call_residual_near"]) < 1, _w  # gas and contract rewards in the epochs with multisig calls

# BigQuery loader: a missing CSV is "pending", a tiny fixture parses, a malformed one is "invalid"; the chapter renders in every state
import bq
with tempfile.TemporaryDirectory() as tmp:
    assert all(q["status"] == "pending" for q in bq.load(tmp).values())
    assert "Pending" in bq.doc_values(tmp)["BQ_STATUS"] and "Not run yet" in bq.chapter(d=tmp)[0]
    w = lambda n, s: open(os.path.join(tmp, n + ".csv"), "w").write(s)
    w("intents_share", "block_date,receipts,intents_receipts,function_calls,intents_function_calls,intents_receipt_share\n"
      "2026-02-14,1000,100,800,90,0.1\n2026-02-13,1000,100,800,90,0.1\n2026-11-12,1000,200,800,180,0.2\n")
    w("daily_transactions", "block_date,transactions\n2026-02-13,5\n")
    w("top_contracts", "period,rank\nlast_30d,1\n")
    got = bq.load(tmp)
    assert got["intents_share"]["status"] == "ok" and got["intents_share"]["rows"][0]["block_date"] == "2026-02-13"
    assert got["top_contracts"]["status"] == "invalid" and got["daily_active_accounts"]["status"] == "pending"
    sm = bq.summary(got)["intents_share"]
    assert abs(sm["first"] - 0.1) < 1e-12 and abs(sm["last"] - 0.2) < 1e-12 and sm["trend"] == "rose"
    page, blob = bq.chapter(d=tmp)
    assert "bq_share" in blob and "could not be read" in page and "rose" in page
# a committed BigQuery export must parse
for _n, _q in bq.load().items():
    assert _q["status"] != "invalid", (_n, _q["reason"])

print("SELFTEST PASS")
