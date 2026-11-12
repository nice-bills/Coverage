#!/usr/bin/env python3
"""Offline and deterministic: data/*.csv -> out/results.json, out/predictions.json, dist/index.html.

Usage: python3 run.py        (no network, no keys, stdlib only)
Prints `RESULT sha256=...` over out/results.json; the README states the expected value.
"""
import csv, datetime, hashlib, json, math, os, random

ROOT = os.path.dirname(os.path.abspath(__file__))
Y = 10 ** 24          # yoctoNEAR per NEAR
YEAR = 365.25 * 86400
W = 100               # rolling window in epochs (about 28 days)
H = 30                # forecast horizon in epochs (about 9 days)
QS = (0.1, 0.5, 0.9)
LUMP = 20             # see load(): buyback gains above this multiple of the trailing median are transfers


def load():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "epochs.csv"))))
    rows = [{k: int(v) for k, v in r.items()} for r in rows]
    rows.sort(key=lambda r: r["start_height"])
    # keep the newest contiguous run; a gap means a partial fetch
    for i in range(len(rows) - 1, 0, -1):
        if rows[i]["prev_end_height"] != rows[i - 1]["end_height"]:
            rows = rows[i:]
            break
    for a, b in zip(rows, rows[1:]):
        assert b["supply_prev_end"] == a["supply_end"], "supply chain broken"
    # the accounting identity, exact in yoctoNEAR: every minted and burnt token is accounted for
    assert rows[-1]["supply_end"] - rows[0]["supply_prev_end"] == sum(r["mint"] - r["burn"] for r in rows)
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
    for i, r in enumerate(rows):
        past = [p["raw_buy"] for p in rows[max(0, i - W):i] if p["raw_buy"] is not None]
        r["lump"] = r["buy"] is not None and len(past) >= 10 and r["buy"] > LUMP * quantile(past, 0.5)
        if r["lump"]:
            r["buy"] = 0
    llama = list(csv.DictReader(open(os.path.join(ROOT, "data", "llama.csv"))))
    return rows, price, llama


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


def f_usage(rows, o):
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
    """Burn explained by NEAR price alone: the rival the thesis must beat."""
    hist = rows[max(0, o - 400):o]
    a, b = ols([r["lp"] for r in hist], [r["y"] for r in hist])
    return [a + b * rows[o - 1]["lp"]] * H


MODELS = {"persistence": f_persistence, "usage": f_usage, "price": f_price}


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


def buyback_forecast(rows):
    """NEAR the buyback account gains over the next H epochs: the last H-epoch gain, with an
    interval from how much consecutive H-epoch gains have differed in the past."""
    buy = []
    for r in reversed(rows):
        if r["buy"] is None:
            break
        buy.append(r["buy"])
    buy.reverse()
    sums = [sum(buy[i - H:i]) for i in range(H, len(buy) + 1)]
    ratios = [math.log(sums[i + H] / sums[i]) for i in range(0, len(sums) - H, 5) if sums[i] > 0 and sums[i + H] > 0]
    if len(ratios) < 10:
        return None
    return [round(sums[-1] / Y * math.exp(quantile(ratios, q)), 1) for q in QS]


def predict(rows, pool):
    o = len(rows)
    out = {"after_end_height": rows[-1]["end_height"], "horizon_epochs": H, "unit": "NEAR burnt per epoch",
           "buyback_gain": buyback_forecast(rows), "models": {}}
    for m, f in MODELS.items():
        pred, offs = f(rows, o), [quantile(pool[m], q) for q in QS]
        out["models"][m] = [[round(math.exp(p + off), 3) for off in offs] for p in pred]
    return out


def ledger(later, commit):
    """Score the committed predictions against epochs that closed after the commit."""
    k = min(len(later), H)
    loss, rows = {}, []
    for m, qs in commit["models"].items():
        loss[m] = sum(pinball(later[i]["y"], math.log(q), tau) for i in range(k)
                      for q, tau in zip(qs[i], QS)) / (k * len(QS)) if k else None
    for i in range(H):
        q10, q50, q90 = commit["models"]["usage"][i]
        a = later[i]["burn"] / Y if i < k else None
        rows.append(dict(k=i + 1, q10=q10, q50=q50, q90=q90, actual=a, hit=a is not None and q10 <= a <= q90))
    hits = sum(r["hit"] for r in rows)
    # pre-registered rule: the price-free model beats the price-only model, and its 80% interval is calibrated
    ok = k == H and loss["usage"] < loss["price"] and 20 <= hits <= 28
    verdict = "PENDING" if k < H else "PASS" if ok else "FALSIFIED"
    buyback, q = None, commit.get("buyback_gain")
    if q and k == H and all(r["buy"] is not None for r in later[:H]):  # second claim: total buyback gain
        got = sum(r["buy"] for r in later[:H]) / Y
        buyback = dict(q10=q[0], q50=q[1], q90=q[2], actual=got, verdict="HIT" if q[0] <= got <= q[2] else "MISS")
    elif q:
        buyback = dict(q10=q[0], q50=q[1], q90=q[2], actual=None, verdict="PENDING")
    return dict(buyback=buyback, resolved=k, total=H, hits=hits, loss=loss, verdict=verdict, rows=rows)


def sig(x, n=6):  # round floats so the hash does not depend on the platform's libm
    if isinstance(x, float):
        return float(f"{x:.{n}g}")
    if isinstance(x, dict):
        return {k: sig(v, n) for k, v in x.items()}
    if isinstance(x, list):
        return [sig(v, n) for v in x]
    return x


def main():
    rows, price, llama = load()
    prep(rows, price)
    # once predictions are committed, the analysis is frozen at that height; later epochs only score it
    cpath, commit, later = os.path.join(ROOT, "predictions.json"), None, []
    if os.path.exists(cpath):
        commit = json.load(open(cpath))
        later = [r for r in rows if r["end_height"] > commit["after_end_height"]]
        rows = [r for r in rows if r["end_height"] <= commit["after_end_height"]]
    roll = rolling(rows)
    now = roll[-1]
    secs = (rows[-1]["t1_ns"] - rows[0]["t0_ns"]) / 1e9

    def trend(value):  # log-linear growth per year over non-overlapping windows, so the points are independent
        blocks = [rows[i - W:i] for i in range(len(rows), W - 1, -W)][::-1]
        pts = [(b[-1]["t1_ns"] / 1e9 / 86400, value(b)) for b in blocks]
        pts = [(x, math.log(v)) for x, v in pts if v is not None and v > 0]
        return ols(*zip(*pts))[1] * 365.25 if len(pts) > 2 else None

    mint = lambda b: sum(r["mint"] for r in b)
    g_burn = trend(lambda b: sum(r["burn"] for r in b) / mint(b))
    g_pay = trend(lambda b: None if any(r["buy"] is None for r in b)
                  else (sum(r["burn"] for r in b) + sum(r["buy"] for r in b)) / mint(b))
    # sampling error of the ceiling: resample the window's epochs (fixed seed, so the hash is stable)
    rnd, w, boot = random.Random(0), rows[-W:], []
    for _ in range(500):
        s = [w[rnd.randrange(W)] for _ in range(W)]
        boot.append(sum(r["burn"] for r in s) / sum(r["mint"] for r in s)
                    * sum(r["sample_gas_limit"] for r in s) / sum(r["sample_gas_used"] for r in s))
    # third-party cross-check over the same days as the last window
    d0, d1 = day(w[0]["t0_ns"]).strftime("%Y-%m-%d"), day(w[-1]["t1_ns"]).strftime("%Y-%m-%d")
    days = [r for r in llama if d0 < r["date"] < d1]
    avg = lambda k: sum(float(r[k] or 0) for r in days) / len(days) if days else None
    usd = sum(price[r["date"]] for r in days if r["date"] in price) / max(1, sum(r["date"] in price for r in days))
    pay = now["payback"]
    upto = [r for r in llama if r["date"] < d1]
    # wider cross-check: NEAR plus wNEAR in all three NEAR Intents revenue wallets across the same window
    wal = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "wallets.csv"))):
        wal[int(r["height"])] = wal.get(int(r["height"]), 0) + int(r["near"]) + int(r["wnear"])
    h0, h1 = w[0]["prev_end_height"], w[-1]["end_height"]
    wsecs = (w[-1]["t1_ns"] - w[0]["t0_ns"]) / 1e9
    allw = (wal[h1] - wal[h0]) / Y / wsecs * 86400 if h0 in wal and h1 in wal else None
    summary = dict(
        epochs=len(rows), first=day(rows[0]["t0_ns"]).strftime("%Y-%m-%d"), last=now["date"],
        first_height=rows[0]["start_height"], last_height=rows[-1]["end_height"],
        mint_per_day=now["mint_per_day"], burn_per_day=now["burn_per_day"], buyback_per_day=now["buyback_per_day"],
        burn_coverage=now["coverage"], buyback_coverage=now["buyback_coverage"], payback=pay,
        multiple=now["multiple"], burn_only_multiple=1 / now["coverage"],
        realized_inflation=sum(r["mint"] for r in rows) / rows[-1]["supply_end"] * YEAR / secs,
        net_inflation=None if pay is None else now["inflation"] * (1 - pay),
        utilization=now["utilization"], ceiling=now["ceiling"],
        ceiling_p05=quantile(boot, 0.05), ceiling_p95=quantile(boot, 0.95),
        burn_coverage_growth_per_year=g_burn, payback_growth_per_year=g_pay,
        years_to_breakeven_at_trend=math.log(now["multiple"]) / g_pay if pay and g_pay and g_pay > 0 else None,
        window_price_usd=usd, burn_usd_per_day=now["burn_per_day"] * usd, llama_burn_usd_per_day=avg("near_burn_usd"),
        buyback_usd_per_day=None if pay is None else now["buyback_per_day"] * usd,
        llama_buyback_usd_per_day=avg("intents_buyback_usd"),
        lump_transfers=sum(r["lump"] for r in rows),
        lump_transfers_near=sum(r["raw_buy"] for r in rows if r["lump"]) / Y,
        all_revenue_wallets_per_day=allw, all_revenue_wallets_usd_per_day=None if allw is None else allw * usd,
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
    results = sig(dict(summary=summary, backtest=bt, series=roll[::3]))
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    blob = json.dumps(results, sort_keys=True, separators=(",", ":"))
    open(os.path.join(ROOT, "out", "results.json"), "w").write(blob)
    led = None
    if pool:
        pred = predict(rows, pool)
        json.dump(pred, open(os.path.join(ROOT, "out", "predictions.json"), "w"), sort_keys=True, separators=(",", ":"))
        if commit:  # the committed file must be exactly what this code derives from the frozen data
            assert commit == pred, "predictions.json does not match the model"
            led = ledger(later, commit)
            led["commit"] = hashlib.sha256(open(cpath, "rb").read()).hexdigest()
    for k, v in results["summary"].items():
        print(f"{k:30} {v}")
    for m, v in results["backtest"].items():
        print(f"backtest {m:12} {v}")
    sha = hashlib.sha256(blob.encode()).hexdigest()
    import dashboard
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    open(os.path.join(ROOT, "dist", "index.html"), "w").write(dashboard.render(results, sha, led))
    if led:
        print(f"LEDGER {led['resolved']}/{led['total']} epochs resolved, {led['hits']} in interval, "
              f"loss {sig(led['loss'], 4)} -> {led['verdict']}")
        if led["buyback"]:
            print(f"LEDGER buyback gain {led['buyback']}")
    print("RESULT sha256=" + sha)


if __name__ == "__main__":
    main()
