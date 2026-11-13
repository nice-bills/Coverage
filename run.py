#!/usr/bin/env python3
"""Offline and deterministic: data/ -> out/results.json, dist/index.html, and scores of the frozen rounds.

Usage: python3 run.py                 (no network, no keys, stdlib only)
       python3 run.py freeze 5 10     write new forecast rounds from the newest cached epoch
Prints `RESULT sha256=...` over out/results.json; the README states the expected value.
"""
import csv, datetime, hashlib, json, math, os, random, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
Y = 10 ** 24          # yoctoNEAR per NEAR
YEAR = 365.25 * 86400
W = 100               # rolling window in epochs (about four weeks)
H = 30                # forecast horizon in epochs (about 9 days)
QS = (0.1, 0.5, 0.9)
LUMP = 20             # see load(): buyback gains above this multiple of the trailing median are transfers


def load():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "epochs.csv"))))
    rows = [{k: int(v) for k, v in r.items()} for r in rows]
    rows.sort(key=lambda r: r["start_height"])
    # Once predictions are committed the analysis covers a fixed range of epochs, so a cache rebuilt
    # later with more history, or newer epochs, gives the same result.
    if rounds():
        first = min(c["first_start_height"] for _, c in rounds())
        rows = [r for r in rows if r["start_height"] >= first]
    if len(rows) < W:
        sys.exit(f"data/epochs.csv has {len(rows)} epochs; at least {W} are needed. Run: python3 fetch.py")
    # Continuity: every epoch must start where the previous one ended, in height and in supply.
    # This catches gaps, reordering and edited rows. It does not prove the rows match the chain;
    # verify.py does that against mainnet.
    for a, b in zip(rows, rows[1:]):
        if b["prev_end_height"] != a["end_height"] or b["supply_prev_end"] != a["supply_end"]:
            sys.exit(f"data/epochs.csv is not contiguous at height {b['start_height']}. "
                     f"Restore it with `git checkout data/` or run: python3 fetch.py")
    for r in rows:
        assert r["mint"] - r["burn"] == r["supply_end"] - r["supply_prev_end"], f"row {r['start_height']} is inconsistent"
    price = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "price.csv"))):
        price[r["date"]] = float(r["usd"])
    # NEAR accumulated by the buyback account during each epoch (None where the balance is not cached)
    bal = {int(r["end_height"]): int(r["balance"]) for r in csv.DictReader(open(os.path.join(ROOT, "data", "buybacks.csv")))}
    for r in rows:
        a, b = bal.get(r["prev_end_height"]), bal.get(r["end_height"])
        r["raw_buy"] = r["buy"] = None if a is None or b is None else b - a
    # A gain above LUMP x the median of the previous W epochs is a treasury transfer of revenue captured
    # earlier, not that epoch's revenue. It is excluded everywhere and reported separately. The rule only
    # looks backwards, so it applies unchanged to epochs that close after the predictions are frozen.
    mark_lumps(rows)
    llama = list(csv.DictReader(open(os.path.join(ROOT, "data", "llama.csv"))))
    return rows, price, llama


def rounds():
    """The frozen forecast rounds in predictions/, oldest first."""
    d = os.path.join(ROOT, "predictions")
    files = sorted(f for f in os.listdir(d) if f.endswith(".json")) if os.path.isdir(d) else []
    out = [(f, json.load(open(os.path.join(d, f)))) for f in files]
    return sorted(out, key=lambda x: (x[1]["after_end_height"], x[1]["horizon_epochs"]))


def mark_lumps(rows):
    for i, r in enumerate(rows):
        past = [p["raw_buy"] for p in rows[max(0, i - W):i] if p["raw_buy"]]  # epochs with a gain or loss
        r["lump"] = r["buy"] is not None and len(past) >= 10 and r["buy"] > LUMP * quantile(past, 0.5)
        if r["lump"]:
            r["buy"] = 0


def day(ns):
    return datetime.datetime.fromtimestamp(ns / 1e9, datetime.timezone.utc)


def quantile(xs, q):
    xs = sorted(xs)
    i = q * (len(xs) - 1)
    lo = int(i)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo)


def ols(xs, ys):
    n, mx, my = len(xs), sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return my - b * mx, b


def rolling(rows):
    out = []
    for i in range(W, len(rows) + 1):
        w = rows[i - W:i]
        burn, mint = sum(r["burn"] for r in w), sum(r["mint"] for r in w)
        used, limit = sum(r["sample_gas_used"] for r in w), sum(r["sample_gas_limit"] for r in w)
        secs = (w[-1]["t1_ns"] - w[0]["t0_ns"]) / 1e9
        cov, util = burn / mint, used / limit
        buy = None if any(r["buy"] is None for r in w) else sum(r["buy"] for r in w)
        out.append(dict(date=day(w[-1]["t1_ns"]).strftime("%Y-%m-%d"), t=w[-1]["t1_ns"] / 1e9,
                        coverage=cov, utilization=util, ceiling=cov / util,
                        burn_per_day=burn / Y / secs * 86400, mint_per_day=mint / Y / secs * 86400,
                        inflation=mint / w[-1]["supply_end"] * YEAR / secs,
                        buyback_per_day=None if buy is None else buy / Y / secs * 86400,
                        buyback_coverage=None if buy is None else buy / mint,
                        payback=None if buy is None else (burn + buy) / mint,
                        multiple=None if buy is None else mint / (burn + buy)))
    return out


# ---- forecasters: each returns the predicted log burn (NEAR) for epochs o .. o+H-1 from rows[:o]

def cell(t):  # weekend flag x 6-hour UTC bucket
    d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
    return (d.weekday() >= 5, d.hour // 6)


def prep(rows, price):
    dates = sorted(price)
    for r in rows:
        r["dur"] = (r["t1_ns"] - r["t0_ns"]) / 1e9
        r["mid"] = (r["t1_ns"] + r["t0_ns"]) / 2e9
        r["y"] = math.log(r["burn"] / Y)
        r["rate"] = r["y"] - math.log(r["dur"])
        d = day(r["t0_ns"] - 86400e9).strftime("%Y-%m-%d")  # last full day before the epoch
        r["lp"] = math.log(price[max((x for x in dates if x <= d), default=dates[0])])


def f_persistence(rows, o):
    return [sum(r["y"] for r in rows[o - H:o]) / H] * H


def f_clock(rows, o):
    """Level of the last H epochs plus a time-of-week profile. Uses no price."""
    hist, last = rows[max(0, o - 400):o], rows[o - H:o]
    mean = sum(r["rate"] for r in hist) / len(hist)
    cells = {}
    for r in hist:
        cells.setdefault(cell(r["mid"]), []).append(r["rate"] - mean)
    season = {c: sum(v) / len(v) for c, v in cells.items()}
    level = sum(r["rate"] - season[cell(r["mid"])] for r in last) / H
    dur = sum(r["dur"] for r in last) / H
    t = rows[o - 1]["t1_ns"] / 1e9
    return [level + season.get(cell(t + (h + 0.5) * dur), 0.0) + math.log(dur) for h in range(H)]


def f_price(rows, o):
    """The same recent level, moved by NEAR's price instead of the clock.
    The price sensitivity is fitted on the last 400 epochs; the forecast uses the last known price."""
    hist, last = rows[max(0, o - 400):o], rows[o - H:o]
    _, b = ols([r["lp"] for r in hist], [r["y"] for r in hist])
    level = sum(r["y"] for r in last) / H
    return [level + b * (rows[o - 1]["lp"] - sum(r["lp"] for r in last) / H)] * H


MODELS = {"persistence": f_persistence, "clock": f_clock, "price": f_price}


def pinball(y, q, tau):
    return (tau - (y < q)) * (y - q)


def backtest(rows, start=300):
    res = {m: dict(loss=[], hit=[]) for m in MODELS}
    pool = {m: [] for m in MODELS}  # past out-of-sample errors set the interval width
    origins = list(range(start, len(rows) - H + 1, H))
    for o in origins:
        for m, f in MODELS.items():
            pred = f(rows, o)
            err = [rows[o + h]["y"] - pred[h] for h in range(H)]
            if len(pool[m]) >= 3 * H:
                offs = [quantile(pool[m], q) for q in QS]
                for h in range(H):
                    y = rows[o + h]["y"]
                    res[m]["loss"].append(sum(pinball(y, pred[h] + off, q) for off, q in zip(offs, QS)) / len(QS))
                    res[m]["hit"].append(pred[h] + offs[0] <= y <= pred[h] + offs[2])
            pool[m] += err
    out = {m: dict(pinball=sum(v["loss"]) / len(v["loss"]), interval_hit=sum(v["hit"]) / len(v["hit"]),
                   n=len(v["loss"])) for m, v in res.items() if v["loss"]}
    for m in out:
        out[m]["skill_vs_persistence"] = 1 - out[m]["pinball"] / out["persistence"]["pinball"]
    return out, pool


# ---- claims about the next h epochs taken as one window

CLAIMS = {  # name: (value of a window of epochs, quantiles of the committed interval)
    "payback": (lambda w: (sum(r["burn"] for r in w) + sum(r["buy"] for r in w)) / sum(r["mint"] for r in w), (0.05, 0.5, 0.95)),
    "burn_total": (lambda w: sum(r["burn"] for r in w) / Y, (0.05, 0.5, 0.95)),
    "buyback_total": (lambda w: sum(r["buy"] for r in w) / Y, (0.05, 0.5, 0.95)),
}


def window_claims(rows, h):
    """Forecast each claim as the last h-epoch value, with an interval from how much consecutive
    h-epoch windows have differed in the past. Also reports how often that interval would have
    held if it had been issued at earlier dates using only data available then."""
    tail = []
    for r in reversed(rows):
        if r["buy"] is None:
            break
        tail.append(r)
    tail.reverse()
    out, held = {}, {}
    for name, (value, qs) in CLAIMS.items():
        vals = [value(tail[i - h:i]) for i in range(h, len(tail) + 1)]  # vals[j]: window ending at tail[j + h]
        # ratios observable at tail[p]; a window with a net outflow has no log ratio and is skipped
        known = lambda p: [math.log(vals[i + h] / vals[i]) for i in range(0, max(0, p - 2 * h + 1), 5)
                           if vals[i] > 0 and vals[i + h] > 0]
        if len(known(len(tail))) < 10:
            out[name] = None
            continue
        out[name] = [float(f"{vals[-1] * math.exp(quantile(known(len(tail)), q)):.6g}") for q in qs]
        hits = [vals[p - h] * math.exp(quantile(known(p), qs[0])) <= vals[p] <= vals[p - h] * math.exp(quantile(known(p), qs[-1]))
                for p in range(h, len(tail) - h + 1, h) if len(known(p)) >= 10 and vals[p - h] > 0]
        held[name] = dict(hit=sum(hits), n=len(hits))
    return out, held


def predict(rows, pool, bt, h):
    """Everything a round commits to, derived only from epochs up to rows[-1]."""
    o = len(rows)
    out = {"first_start_height": rows[0]["start_height"], "after_end_height": rows[-1]["end_height"],
           "horizon_epochs": h, "claims": window_claims(rows, h)[0],
           "per_epoch_unit": "NEAR burnt per epoch, 10% / 50% / 90%",
           "table_model": min(bt, key=lambda m: bt[m]["pinball"]), "models": {}}
    for m, f in MODELS.items():
        pred, offs = f(rows, o)[:h], [quantile(pool[m], q) for q in QS]
        out["models"][m] = [[round(math.exp(p + off), 3) for off in offs] for p in pred]
    return out


def ledger(later, commit):
    """Score one frozen round against the epochs that closed after it."""
    h = commit["horizon_epochs"]
    k = min(len(later), h)
    done = k == h and all(r["buy"] is not None for r in later[:h])
    claims = {}
    for name, q in commit["claims"].items():
        if q is None:
            continue
        got = CLAIMS[name][0](later[:h]) if done else None
        claims[name] = dict(lo=q[0], mid=q[1], hi=q[2], actual=got,
                            verdict="PENDING" if got is None else "HIT" if q[0] <= got <= q[2] else "MISS")
    loss, rows = {}, []
    for m, qs in commit["models"].items():
        loss[m] = sum(pinball(later[i]["y"], math.log(q), tau) for i in range(k)
                      for q, tau in zip(qs[i], QS)) / (k * len(QS)) if k else None
    for i in range(h):
        q10, q50, q90 = commit["models"][commit["table_model"]][i]
        a = later[i]["burn"] / Y if i < k else None
        rows.append(dict(k=i + 1, q10=q10, q50=q50, q90=q90, actual=a, hit=a is not None and q10 <= a <= q90))
    # the verdict is the payback claim: the thesis number must hold on epochs that did not exist when it was frozen
    v = claims.get("payback", {}).get("verdict", "PENDING")
    verdict = {"HIT": "PASS", "MISS": "FALSIFIED"}.get(v, "PENDING")
    return dict(claims=claims, resolved=k, total=h, hits=sum(r["hit"] for r in rows), loss=loss, verdict=verdict,
                rows=rows, table_model=commit["table_model"], after_end_height=commit["after_end_height"],
                ends=day(later[h - 1]["t1_ns"]).strftime("%Y-%m-%d %H:%M UTC") if k == h else None)


def freeze(rows, horizons):
    """Write a new round for each horizon from the newest cached epoch. Never overwrites."""
    bt, pool = backtest(rows)
    os.makedirs(os.path.join(ROOT, "predictions"), exist_ok=True)
    for h in horizons:
        name = f"round-{rows[-1]['end_height']}-h{h:02d}.json"
        path = os.path.join(ROOT, "predictions", name)
        if os.path.exists(path):
            sys.exit(f"{name} already exists; a frozen round is never rewritten")
        blob = json.dumps(predict(rows, pool, bt, h), sort_keys=True, separators=(",", ":"))
        open(path, "w").write(blob)
        print(f"ROUND {name} sha256={hashlib.sha256(blob.encode()).hexdigest()}")


def sig(x, n=6):  # round floats so the hash does not depend on the platform's libm
    if isinstance(x, float):
        return float(f"{x:.{n}g}")
    if isinstance(x, dict):
        return {k: sig(v, n) for k, v in x.items()}
    if isinstance(x, list):
        return [sig(v, n) for v in x]
    return x


def main():
    every, price, llama = load()
    prep(every, price)
    if sys.argv[1:2] == ["freeze"]:
        return freeze(every, [int(a) for a in sys.argv[2:]] or [10])
    # Once a round is frozen, the analysis stops at the newest round's height. Epochs after a
    # round's height are used only to score that round.
    frozen = rounds()
    snap = max((c["after_end_height"] for _, c in frozen), default=every[-1]["end_height"])
    rows = [r for r in every if r["end_height"] <= snap]
    roll = rolling(rows)
    now = roll[-1]
    secs = (rows[-1]["t1_ns"] - rows[0]["t0_ns"]) / 1e9

    # sampling error of the ceiling: resample the window's epochs (fixed seed, so the hash is stable)
    rnd, w, boot = random.Random(0), rows[-W:], []
    for _ in range(500):
        s = [w[rnd.randrange(W)] for _ in range(W)]
        boot.append(sum(r["burn"] for r in s) / sum(r["mint"] for r in s)
                    * sum(r["sample_gas_limit"] for r in s) / sum(r["sample_gas_used"] for r in s))
    # sampling error of payback: same resampling, separate seed so the ceiling figures do not move
    rnd, pboot = random.Random(1), []
    if all(r["buy"] is not None for r in w):
        for _ in range(500):
            s = [w[rnd.randrange(W)] for _ in range(W)]
            pboot.append(sum(r["burn"] + r["buy"] for r in s) / sum(r["mint"] for r in s))
    # Flow before and since private settlement began (date as reported by the Tideline entry, not verified here)
    cut = datetime.datetime(2026, 10, 27, tzinfo=datetime.timezone.utc).timestamp() * 1e9
    def span(rs):
        rs = [r for r in rs if r["buy"] is not None]
        if not rs:
            return None
        d = (rs[-1]["t1_ns"] - rs[0]["t0_ns"]) / 86400e9
        return dict(epochs=len(rs), days=d, buyback_per_day=sum(r["buy"] for r in rs) / Y / d,
                    payback=sum(r["burn"] + r["buy"] for r in rs) / sum(r["mint"] for r in rs),
                    epochs_with_inflow=sum(r["raw_buy"] > 0 for r in rs))
    private = dict(since=span([r for r in rows if r["t1_ns"] >= cut]),
                   before=span([r for r in rows if cut - 30 * 86400e9 <= r["t1_ns"] < cut]))
    # third-party cross-check over the same days as the last window
    d0, d1 = day(w[0]["t0_ns"]).strftime("%Y-%m-%d"), day(w[-1]["t1_ns"]).strftime("%Y-%m-%d")
    days = [r for r in llama if d0 < r["date"] < d1]
    avg = lambda k: sum(float(r[k] or 0) for r in days) / len(days) if days else None
    # DefiLlama reports USD; convert each day at that day's price so the comparison is in NEAR
    priced = [r for r in days if r["date"] in price]
    near = lambda k: sum(float(r[k] or 0) / price[r["date"]] for r in priced) / len(priced) if priced else None
    usd = sum(price[r["date"]] for r in days if r["date"] in price) / max(1, sum(r["date"] in price for r in days))
    pay = now["payback"]
    upto = [r for r in llama if r["date"] < d1]
    # wider cross-check: NEAR plus wNEAR in all three NEAR Intents revenue wallets across the same window
    wal, other = {}, {}
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "wallets.csv"))):
        wal[int(r["height"])] = wal.get(int(r["height"]), 0) + int(r["near"]) + int(r["wnear"])
        if r["account"] != "buybacks.multisignature.near":
            other[int(r["height"])] = other.get(int(r["height"]), 0) + int(r["near"]) + int(r["wnear"])
    h0, h1 = w[0]["prev_end_height"], w[-1]["end_height"]
    wsecs = (w[-1]["t1_ns"] - w[0]["t0_ns"]) / 1e9
    allw = (wal[h1] - wal[h0]) / Y / wsecs * 86400 if h0 in wal and h1 in wal else None
    # NEAR Intents by complete week since buybacks began (DefiLlama, USD): does captured revenue follow volume?
    wk = {}
    for r in upto:
        if r["date"] >= "2026-02-23":
            d = datetime.date.fromisoformat(r["date"])
            k = wk.setdefault(d - datetime.timedelta(days=d.weekday()), [0.0, 0.0, 0.0, 0])
            for i, c in enumerate(("intents_volume_usd", "intents_fees_usd", "intents_buyback_usd")):
                k[i] += float(r[c] or 0)
            k[3] += 1
    weekly = [dict(date=str(d), t=datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc).timestamp(),
                   volume_musd=v / 7e6, fees_kusd=f / 7e3, captured_kusd=b / 7e3, take_bps=b / v * 1e4, capture_share=b / f)
              for d, (v, f, b, n) in sorted(wk.items()) if n == 7 and v > 0 and f > 0]
    vs, bs = [x["volume_musd"] for x in weekly], [x["captured_kusd"] for x in weekly]
    mv, mb = sum(vs) / max(1, len(vs)), sum(bs) / max(1, len(bs))
    corr = (sum((x - mv) * (y - mb) for x, y in zip(vs, bs))
            / math.sqrt(sum((x - mv) ** 2 for x in vs) * sum((y - mb) ** 2 for y in bs))) if len(weekly) > 2 else None
    # who sent NEAR to the buyback account (NearBlocks indexer; each row has a transaction hash)
    inf = list(csv.DictReader(open(os.path.join(ROOT, "data", "inflows.csv"))))
    inf = [r for r in inf if int(r["block_height"]) <= rows[-1]["end_height"]]
    paid = [r for r in roll if r["payback"] is not None]
    peak = max(paid, key=lambda r: r["payback"]) if paid else None
    def years_to_breakeven(growth, ramp):
        """Years until burn plus buybacks, growing at a constant yearly rate, equal issuance.
        ramp=True lowers issuance linearly from 2.5% to 1.6% over 24 months (HSP-029)."""
        for month in range(1, 12 * 100 + 1):
            issuance = 1 - (1 - 1.6 / 2.5) * min(month, 24) / 24 if ramp else 1.0
            if (1 + growth) ** (month / 12) >= now["multiple"] * issuance:
                return month / 12
        return None

    paths = None if now["multiple"] is None else {
        f"{round(100 * g)}%": dict(constant_issuance=years_to_breakeven(g, False), hsp029=years_to_breakeven(g, True))
        for g in (0.1, 0.25, 0.5, 1.0)}
    summary = dict(
        epochs=len(rows), first=day(rows[0]["t0_ns"]).strftime("%Y-%m-%d"), last=now["date"],
        first_height=rows[0]["start_height"], last_height=rows[-1]["end_height"],
        last_end_utc=day(rows[-1]["t1_ns"]).strftime("%Y-%m-%d %H:%M"),
        mint_per_day=now["mint_per_day"], burn_per_day=now["burn_per_day"], buyback_per_day=now["buyback_per_day"],
        burn_coverage=now["coverage"], buyback_coverage=now["buyback_coverage"], payback=pay,
        multiple=now["multiple"], burn_only_multiple=1 / now["coverage"],
        realized_inflation=sum(r["mint"] for r in rows) / rows[-1]["supply_end"] * YEAR / secs,
        inflation_if_buybacks_were_burnt=None if pay is None else now["inflation"] * (1 - pay),
        # HSP-029 would lower maximum issuance from 2.5% to 1.6% a year; at today's flows the multiple scales with it
        multiple_at_1_6_issuance=None if pay is None else now["multiple"] * 1.6 / 2.5,
        window_days=(w[-1]["t1_ns"] - w[0]["t0_ns"]) / 86400e9,
        # constant yearly growth in burn plus buybacks that reaches break-even in 3, 5 and 10 years
        **({} if pay is None else {f"growth_needed_{n}y": now["multiple"] ** (1 / n) - 1 for n in (3, 5, 10)}),
        utilization=now["utilization"], ceiling=now["ceiling"],
        ceiling_p05=quantile(boot, 0.05), ceiling_p95=quantile(boot, 0.95),
        window_price_usd=usd, llama_burn_near_per_day=near("near_burn_usd"), llama_fees_near_per_day=near("near_fees_usd"),
        llama_buyback_near_per_day=near("intents_buyback_usd"),
        # how much left the other two revenue wallets during the lump epochs (where those heights are cached)
        intents_weeks=len(weekly), intents_volume_captured_correlation=corr,
        intents_take_bps_median=quantile([x["take_bps"] for x in weekly], 0.5) if weekly else None,
        intents_take_bps_min=min((x["take_bps"] for x in weekly), default=None),
        intents_take_bps_max=max((x["take_bps"] for x in weekly), default=None),
        intents_volume_musd_low=min(vs, default=None), intents_volume_musd_latest=vs[-1] if vs else None,
        inflow_transfers=len(inf), inflow_first_height=int(inf[0]["block_height"]) if inf else None,
        inflow_share_from_intents=sum(float(r["near"]) for r in inf if r["predecessor"] == "intents.near")
        / sum(float(r["near"]) for r in inf) if inf else None,
        inflow_transfers_from_intents=sum(r["predecessor"] == "intents.near" for r in inf),
        payback_first=paid[0]["payback"] if paid else None, payback_first_date=paid[0]["date"] if paid else None,
        payback_peak=peak["payback"] if peak else None, payback_peak_date=peak["date"] if peak else None,
        lump_matched_outflow_near=sum(other.get(r["prev_end_height"], 0) - other.get(r["end_height"], 0) for r in rows
                                      if r["lump"] and r["prev_end_height"] in other and r["end_height"] in other) / Y,
        buyback_outflow_epochs=sum(r["raw_buy"] is not None and r["raw_buy"] < 0 for r in rows),
        buyback_outflow_near=-sum(r["raw_buy"] for r in rows if r["raw_buy"] is not None and r["raw_buy"] < 0) / Y,
        buyback_epochs=sum(r["raw_buy"] is not None and r["raw_buy"] != 0 for r in rows),
        lump_transfers=sum(r["lump"] for r in rows),
        # robustness: the excluded transfer and the one outflow both lie outside the headline window
        lump_epochs_in_window=sum(r["lump"] for r in w),
        outflow_epochs_in_window=sum(r["raw_buy"] is not None and r["raw_buy"] < 0 for r in w),
        payback_p05=quantile(pboot, 0.05) if pboot else None, payback_p95=quantile(pboot, 0.95) if pboot else None,
        lump_transfers_near=sum(r["raw_buy"] for r in rows if r["lump"]) / Y,
        all_revenue_wallets_per_day=allw,
        all_revenue_wallets_payback=None if allw is None else (allw + now["burn_per_day"]) / now["mint_per_day"],
        capture_share=now["buyback_per_day"] * usd / avg("intents_fees_usd") if pay is not None and days else None,
        intents_volume_usd_per_day=avg("intents_volume_usd"), intents_fees_usd_per_day=avg("intents_fees_usd"),
        # year on year, first 30 days against last 30 days of the DefiLlama series up to the snapshot
        **{k + "_ratio_1y": sum(float(r[k] or 0) for r in upto[-30:]) / max(1.0, sum(float(r[k] or 0) for r in upto[:30]))
           for k in ("intents_volume_usd", "intents_fees_usd", "near_fees_usd")},
        # lever: payback if every dollar of gross NEAR Intents fees were captured, at today's volume
        payback_if_all_intents_fees_captured=(avg("intents_fees_usd") / usd + now["burn_per_day"]) / now["mint_per_day"]
        if days and usd else None)
    bt, pool = backtest(rows) if len(rows) >= 300 + 5 * H else ({}, None)
    results = sig(dict(summary=summary, private_settlement=private, backtest=bt, breakeven_years=paths, claims_backtest={str(h): window_claims(rows, h)[1] for h in sorted({5, 10} | {c["horizon_epochs"] for _, c in frozen})},
                       series=roll[::3], weekly=weekly))
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    blob = json.dumps(results, sort_keys=True, separators=(",", ":"))
    open(os.path.join(ROOT, "out", "results.json"), "w").write(blob)
    leds = []
    for name, commit in frozen:  # each round must be exactly what this code derives from the epochs up to its height
        idx = [r["end_height"] for r in every].index(commit["after_end_height"])
        b, p = backtest(every[:idx + 1])
        if commit != predict(every[:idx + 1], p, b, commit["horizon_epochs"]):
            sys.exit(f"predictions/{name} is not what the model derives from the data up to its height")
        led = ledger(every[idx + 1:], commit)
        led["file"] = name
        led["commit"] = hashlib.sha256(open(os.path.join(ROOT, "predictions", name), "rb").read()).hexdigest()
        leds.append(led)
    for k, v in results["summary"].items():
        print(f"{k:30} {v}")
    for m, v in results["backtest"].items():
        print(f"backtest {m:12} {v}")
    sha = hashlib.sha256(blob.encode()).hexdigest()
    import dashboard
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    open(os.path.join(ROOT, "dist", "index.html"), "w").write(dashboard.render(results, sha, leds, dict(
        E=[[r["start_height"], r["end_height"], r["prev_end_height"], r["t1_ns"] // 10**9, str(r["mint"]), str(r["burn"]),
            None if r["raw_buy"] is None else str(r["raw_buy"]), int(r["lump"])] for r in every],
        snap=snap, rounds=[dict(n=l["total"], lo=l["claims"]["payback"]["lo"], hi=l["claims"]["payback"]["hi"]) for l in leds],
        bal=next((r["balance"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "buybacks.csv")))
                  if int(r["end_height"]) == snap), None))))
    for led in leds:
        print(f"LEDGER {led['file']}: {led['resolved']}/{led['total']} epochs closed -> {led['verdict']}")
        for name, c in led["claims"].items():
            print(f"LEDGER   {name}: {sig(c['lo'])} to {sig(c['hi'])}, actual {sig(c['actual'])} -> {c['verdict']}")
    print("RESULT sha256=" + sha)


if __name__ == "__main__":
    main()
