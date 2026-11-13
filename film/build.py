#!/usr/bin/env python3
"""Write film/src/data.js from out/results.json and the built dashboard, so every number in the film is real."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
r = json.load(open(os.path.join(ROOT, "out", "results.json")))
s, sc = r["summary"], r["scenarios"]
page = open(os.path.join(ROOT, "dist", "index.html"), encoding="utf-8").read()
m = re.search(r"Payback so far <b>([\d.]+%)</b>: inside (\d+) of (\d+)", page)
run = open(os.path.join(HERE, "assets", "run_output.txt")).read().splitlines()
res = next(l for l in run if l.startswith("RESULT sha256="))
readme = re.search(r"sha256=([0-9a-f]{64})", open(os.path.join(ROOT, "README.md")).read()).group(1)
import bq
bs = bq.summary(bq.load())
x = bs["intents_share"]
d = dict(
    mint=round(s["mint_per_day"]), burn=round(s["burn_per_day"]), buy=round(s["buyback_per_day"]),
    burn_cov=f"{100 * s['burn_coverage']:.2f}%", payback=f"{100 * s['payback']:.1f}%", payback_v=s["payback"],
    burn_v=s["burn_coverage"], buy_v=s["buyback_coverage"],
    mult=f"{s['multiple']:.1f}×", burn_mult=f"{s['burn_only_multiple']:.0f}×",
    so_far=m.group(1) if m else None, inside=f"{m.group(2)} of {m.group(3)}" if m else None,
    ledger=[l for l in run if l.startswith("LEDGER")][:6], result=res, readme_hash=readme, match=res.endswith(readme),
    intents_x=f"{x['per_day_last'] / x['per_day_first']:.1f}×",
    dau=bs["daily_active_accounts"]["change"],
    epochs=f"{s['epochs']:,}",
    full_cap_years=round(sc["levers"]["capture"][-1]["years_base_hsp029"]),
)
assert d["match"], "run.py hash does not match README"
open(os.path.join(HERE, "src", "data.js"), "w").write("window.D=" + json.dumps(d, ensure_ascii=False) + ";")
print(json.dumps(d, ensure_ascii=False, indent=1))
