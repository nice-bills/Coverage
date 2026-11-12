#!/usr/bin/env python3
"""Fill README.md, THESIS.md and SUBMISSION.md from templates/ and out/results.json.

Usage: python3 docs.py          write the three files
       python3 docs.py --check  exit 1 if a committed file differs from what the results give

Every number in those files is a placeholder in the template, so prose cannot drift from the data.
Run `python3 run.py` first.
"""
import datetime, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = ("README.md", "THESIS.md", "SUBMISSION.md")


def values():
    blob = open(os.path.join(ROOT, "out", "results.json")).read()
    r = json.loads(blob)
    s, bt, cb = r["summary"], r["backtest"], r["claims_backtest"]
    pct = lambda x, n=1: f"{100 * x:.{n}f}%"
    usd = lambda x: f"${x:,.0f}"
    num = lambda x: f"{x:,.0f}"
    skill = lambda m: f"{abs(100 * m['skill_vs_persistence']):.0f}% {'better' if m['skill_vs_persistence'] > 0 else 'worse'}"

    # one row per frozen round
    rdir = os.path.join(ROOT, "predictions")
    names = sorted(f for f in os.listdir(rdir) if f.endswith(".json")) if os.path.isdir(rdir) else []
    hours = s["window_days"] * 24 / 100  # average epoch length in the last window
    end = datetime.datetime.strptime(s["last_end_utc"], "%Y-%m-%d %H:%M")
    lines, hashes = [], []
    for name in names:
        raw = open(os.path.join(rdir, name), "rb").read()
        c, sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
        h, cl, held = c["horizon_epochs"], c["claims"], cb[str(c["horizon_epochs"])]["payback"]
        hashes.append(f"{name} {sha}")
        close = ((end + datetime.timedelta(hours=hours * h)).strftime("about %Y-%m-%d %H:00")
                 if c["after_end_height"] == s["last_height"] else "see the ledger")
        lines.append(f"| `{name}` | {h} | {close} | {pct(cl['payback'][0])} to {pct(cl['payback'][2])} "
                     f"| {num(cl['burn_total'][0])} to {num(cl['burn_total'][2])} "
                     f"| {num(cl['buyback_total'][0])} to {num(cl['buyback_total'][2])} "
                     f"| {held['hit']} of {held['n']} | `{sha}` |")
    table = ("| Round | Epochs | Expected to close (UTC) | Payback | NEAR burnt | Buyback gain, NEAR "
             "| Payback interval held in the past | sha256 |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(lines)
             if lines else "(no rounds frozen yet)")

    return dict(
        RESULT_HASH=hashlib.sha256(blob.encode()).hexdigest(), EPOCHS=str(s["epochs"]), LAST=s["last"],
        LAST_HEIGHT=str(s["last_height"]), WINDOW_DAYS=f"{s['window_days']:.0f}",
        MINT=num(s["mint_per_day"]), BURN=num(s["burn_per_day"]), BUY=num(s["buyback_per_day"]),
        BURN_COV=pct(s["burn_coverage"], 2), BUY_COV=pct(s["buyback_coverage"]), PAYBACK=pct(s["payback"]),
        MULT=f"{s['multiple']:.1f}", MULT_HSP=f"{s['multiple_at_1_6_issuance']:.1f}",
        BURN_MULT=f"{s['burn_only_multiple']:.0f}",
        G3=pct(s["growth_needed_3y"], 0), G5=pct(s["growth_needed_5y"], 0), G10=pct(s["growth_needed_10y"], 0),
        INFL=pct(s["realized_inflation"], 2), IF_BURNT=pct(s["inflation_if_buybacks_were_burnt"], 2),
        UTIL=pct(s["utilization"], 2), CEIL=pct(s["ceiling"], 0),
        CEIL_LO=pct(s["ceiling_p05"], 0), CEIL_HI=pct(s["ceiling_p95"], 0),
        LLAMA_BUY_NEAR=num(s["llama_buyback_near_per_day"]), ALL_NEAR=num(s["all_revenue_wallets_per_day"]),
        LLAMA_BURN_NEAR=num(s["llama_burn_near_per_day"]), LLAMA_FEES_NEAR=num(s["llama_fees_near_per_day"]),
        FEES_USD=usd(s["intents_fees_usd_per_day"]), CAPTURE=pct(s["capture_share"], 0),
        LEVER=pct(s["payback_if_all_intents_fees_captured"], 0),
        WEEKS=str(s["intents_weeks"]), CORR=f"{s['intents_volume_captured_correlation']:.2f}",
        BPS=f"{s['intents_take_bps_median']:.1f}", BPS_LO=f"{s['intents_take_bps_min']:.1f}",
        BPS_HI=f"{s['intents_take_bps_max']:.1f}",
        VOL_LOW=f"{s['intents_volume_musd_low']:.0f}", VOL_NOW=f"{s['intents_volume_musd_latest']:.0f}",
        VOL_RATIO=f"{s['intents_volume_usd_ratio_1y']:.2f}", FEE_RATIO=f"{s['intents_fees_usd_ratio_1y']:.2f}",
        GAS_RATIO=f"{s['near_fees_usd_ratio_1y']:.2f}",
        INFLOW_N=str(s["inflow_transfers"]), INFLOW_INTENTS=str(s["inflow_transfers_from_intents"]),
        INFLOW_SHARE=pct(s["inflow_share_from_intents"]), INFLOW_H=str(s["inflow_first_height"]),
        LUMP=num(s["lump_transfers_near"]), LUMP_OUT=num(s["lump_matched_outflow_near"]),
        OUT_N=str(s["buyback_outflow_epochs"]), OUT_NEAR=num(s["buyback_outflow_near"]),
        BUY_EPOCHS=str(s["buyback_epochs"]),
        PAY_FIRST=pct(s["payback_first"]), PAY_FIRST_DATE=s["payback_first_date"],
        PAY_PEAK=pct(s["payback_peak"]), PAY_PEAK_DATE=s["payback_peak_date"],
        BT_N=str(bt["persistence"]["n"]), BT_PERSIST=f"{bt['persistence']['pinball']:.4f}",
        BT_CLOCK=f"{bt['clock']['pinball']:.4f}", BT_PRICE=f"{bt['price']['pinball']:.4f}",
        BT_PRICE_SKILL=skill(bt["price"]), BT_CLOCK_SKILL=skill(bt["clock"]),
        ROUNDS_TABLE=table, ROUND_HASHES="; ".join(hashes) or "(none)")


def main():
    v, stale = values(), []
    for f in FILES:
        text = open(os.path.join(ROOT, "templates", f)).read()
        for k, x in v.items():
            text = text.replace(f"__{k}__", x)
        left = re.findall(r"__[A-Z_0-9]+__", text)
        if left:
            sys.exit(f"templates/{f} has placeholders with no value: {sorted(set(left))}")
        path = os.path.join(ROOT, f)
        if "--check" in sys.argv:
            if not os.path.exists(path) or open(path).read() != text:
                stale.append(f)
        else:
            open(path, "w").write(text)
    if stale:
        sys.exit(f"DOCS STALE: {', '.join(stale)} differ from templates/ + out/results.json. Run: python3 docs.py")
    print("DOCS " + ("IN SYNC" if "--check" in sys.argv else "WRITTEN") + f" from result {v['RESULT_HASH'][:12]}")


if __name__ == "__main__":
    main()
