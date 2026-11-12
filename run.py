#!/usr/bin/env python3
"""Offline and deterministic: data/*.csv -> out/results.json, out/predictions.json, dist/index.html.

Usage: python3 run.py        (no network, no keys, stdlib only)
Prints `RESULT sha256=...` over out/results.json; the README states the expected value.
"""
import csv, datetime, hashlib, json, math, os

ROOT = os.path.dirname(os.path.abspath(__file__))
Y = 10 ** 24          # yoctoNEAR per NEAR
YEAR = 365.25 * 86400
W = 100               # rolling window in epochs (about 28 days)
H = 30                # forecast horizon in epochs (about 9 days)
QS = (0.1, 0.5, 0.9)


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
    return rows, price


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
        out.append(dict(date=day(w[-1]["t1_ns"]).strftime("%Y-%m-%d"), t=w[-1]["t1_ns"] / 1e9,
                        coverage=cov, utilization=util, ceiling=cov / util, multiple=mint / burn,
                        burn_per_day=burn / Y / secs * 86400, mint_per_day=mint / Y / secs * 86400,
                        inflation=mint / w[-1]["supply_end"] * YEAR / secs))
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


def predict(rows, pool):
    o = len(rows)
    out = {"after_end_height": rows[-1]["end_height"], "horizon_epochs": H, "unit": "NEAR burnt per epoch",
           "models": {}}
    for m, f in MODELS.items():
        pred, offs = f(rows, o), [quantile(pool[m], q) for q in QS]
        out["models"][m] = [[round(math.exp(p + off), 3) for off in offs] for p in pred]
    return out


def ledger(later, commit):
    """Score the committed predictions against epochs that closed after the commit."""
    k = min(len(later), H)
    if not k:
        return None
    loss, rows = {}, []
    for m, qs in commit["models"].items():
        loss[m] = sum(pinball(later[i]["y"], math.log(q), tau) for i in range(k)
                      for q, tau in zip(qs[i], QS)) / (k * len(QS))
    for i in range(k):
        q10, q50, q90 = commit["models"]["usage"][i]
        a = later[i]["burn"] / Y
        rows.append(dict(k=i + 1, q10=q10, q50=q50, q90=q90, actual=a, hit=q10 <= a <= q90))
    hits = sum(r["hit"] for r in rows)
    # pre-registered rule: the price-free model beats the price-only model, and its 80% interval is calibrated
    ok = loss["usage"] < loss["price"] and 20 <= hits <= 28
    verdict = "PENDING" if k < H else "PASS" if ok else "FALSIFIED"
    return dict(resolved=k, total=H, hits=hits, loss=loss, verdict=verdict, rows=rows,
                commit=hashlib.sha256(open(os.path.join(ROOT, "predictions.json"), "rb").read()).hexdigest())


def sig(x, n=6):  # round floats so the hash does not depend on the platform's libm
    if isinstance(x, float):
        return float(f"{x:.{n}g}")
    if isinstance(x, dict):
        return {k: sig(v, n) for k, v in x.items()}
    if isinstance(x, list):
        return [sig(v, n) for v in x]
    return x


def main():
    rows, price = load()
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
    a, b = ols([r["t"] / 86400 for r in roll], [math.log(r["coverage"]) for r in roll])
    summary = dict(
        epochs=len(rows), first=day(rows[0]["t0_ns"]).strftime("%Y-%m-%d"), last=now["date"],
        first_height=rows[0]["start_height"], last_height=rows[-1]["end_height"],
        coverage=now["coverage"], utilization=now["utilization"], ceiling=now["ceiling"],
        multiple=now["multiple"], breakeven_utilization=1 / now["ceiling"],
        burn_per_day=now["burn_per_day"], mint_per_day=now["mint_per_day"],
        realized_inflation=sum(r["mint"] for r in rows) / rows[-1]["supply_end"] * YEAR / secs,
        coverage_growth_per_year=b * 365.25,
        years_to_breakeven_at_trend=math.log(now["multiple"]) / (b * 365.25) if b > 0 else None)
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
    print("RESULT sha256=" + sha)


if __name__ == "__main__":
    main()
