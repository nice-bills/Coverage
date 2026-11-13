"""NEAR network activity from Google's public BigQuery dataset: load data/bq/*.csv and describe it.

Stdlib only. The SQL is in queries/; a person with a Google account runs it (see README) and saves
each result as data/bq/<name>.csv. Nothing here needs credentials or the network, and a missing or
malformed CSV only puts that query in a "pending" state.

These figures are context for the thesis, not inputs to it: run.py never reads them, so they are
not in out/results.json and do not change the result hash. dashboard.py draws them and docs.py
writes their status into README.md and THESIS.md.
"""
import csv, hashlib, html, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = "bigquery-public-data.crypto_near_mainnet_us"
WINDOW = ("2026-02-13", "2026-11-12")
INTENTS = "intents.near"

# name, columns the CSV must have, what it measures, the table it reads
QUERIES = [
    ("daily_active_accounts", ("block_date", "active_accounts"),
     "Daily active accounts: distinct transaction signers per UTC day", "transactions"),
    ("daily_transactions", ("block_date", "transactions"),
     "Transactions included on chain per UTC day", "transactions"),
    ("intents_share", ("block_date", "receipts", "intents_receipts", "function_calls", "intents_function_calls"),
     "Contract usage: receipts and function calls per day, and how many went to intents.near", "receipt_actions"),
    ("top_contracts", ("period", "rank", "contract", "function_calls", "share"),
     "Contract usage: the 25 contracts with the most function calls, first and last 30 days of the window", "receipt_actions"),
]
NUMERIC = {"active_accounts", "transactions", "receipts", "intents_receipts", "function_calls", "intents_function_calls", "rank"}


def _num(x):
    x = x.strip()
    return float(x) if any(c in x for c in ".eE") else int(x)


def load(d=None):
    """{name: {"status": "ok" | "pending" | "invalid", "rows", "sha256", "reason", "path"}} for every query."""
    d = d or os.path.join(HERE, "data", "bq")
    out = {}
    for name, cols, _, _ in QUERIES:
        path = os.path.join(d, name + ".csv")
        q = dict(status="pending", rows=[], sha256=None, reason=None, path=f"data/bq/{name}.csv")
        out[name] = q
        if not os.path.isfile(path):
            continue
        try:
            raw = open(path, "rb").read()
            q["sha256"] = hashlib.sha256(raw).hexdigest()
            reader = csv.DictReader(raw.decode("utf-8-sig").splitlines())
            missing = [c for c in cols if c not in (reader.fieldnames or [])]
            if missing:
                raise ValueError("missing column " + ", ".join(missing))
            rows = []
            for r in reader:
                row = {c: (_num(r[c]) if c in NUMERIC else float(r[c]) if c == "share" else r[c].strip()) for c in cols}
                rows.append(row)
            if not rows:
                raise ValueError("no rows")
            if "block_date" in cols:
                rows.sort(key=lambda r: r["block_date"])
            q.update(status="ok", rows=rows)
        except (OSError, ValueError, KeyError, TypeError, UnicodeDecodeError) as ex:
            q.update(status="invalid", reason=str(ex) or type(ex).__name__)
    return out


def _ord(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _change(a, b):
    """'up 12%', 'down 3%' or 'about the same' for a move from a to b."""
    if not a or b is None:
        return "n/a"
    r = b / a - 1
    return "about the same" if abs(r) < 0.02 else f"{'up' if r > 0 else 'down'} {abs(100 * r):.0f}%"


def summary(data):
    """Plain figures from whatever is loaded: first and last 30 days of each daily series, the Intents share, ranks."""
    s = {}
    for name, key in (("daily_active_accounts", "active_accounts"), ("daily_transactions", "transactions")):
        rows = data[name]["rows"]
        if data[name]["status"] == "ok" and len(rows) >= 2:
            k = min(30, len(rows) // 2)
            a, b = _mean([r[key] for r in rows[:k]]), _mean([r[key] for r in rows[-k:]])
            s[name] = dict(first=a, last=b, days=k, change=_change(a, b), start=rows[0]["block_date"], end=rows[-1]["block_date"], n=len(rows))
    rows = data["intents_share"]["rows"]
    if data["intents_share"]["status"] == "ok" and len(rows) >= 2:
        k = min(30, len(rows) // 2)
        sh = lambda rs, a, b: sum(r[a] for r in rs) / max(1, sum(r[b] for r in rs))
        a, b = sh(rows[:k], "intents_receipts", "receipts"), sh(rows[-k:], "intents_receipts", "receipts")
        fa, fb = sh(rows[:k], "intents_function_calls", "function_calls"), sh(rows[-k:], "intents_function_calls", "function_calls")
        trend = "rose" if b > 1.1 * a else "fell" if b < 0.9 * a else "held about steady"
        s["intents_share"] = dict(first=a, last=b, calls_first=fa, calls_last=fb, days=k, trend=trend,
                                  per_day_last=_mean([r["intents_receipts"] for r in rows[-k:]]),
                                  start=rows[0]["block_date"], end=rows[-1]["block_date"], n=len(rows))
    rows = data["top_contracts"]["rows"]
    if data["top_contracts"]["status"] == "ok":
        rank = {p: next((r for r in rows if r["period"] == p and r["contract"] == INTENTS), None) for p in ("first_30d", "last_30d")}
        s["top_contracts"] = dict(first=rank["first_30d"], last=rank["last_30d"],
                                  top_last=[r for r in rows if r["period"] == "last_30d" and r["rank"] <= 25][:10],
                                  top_first={r["contract"]: r["rank"] for r in rows if r["period"] == "first_30d"})
    return s


def sentences(data, s=None):
    """One plain sentence per query, written from the data; None when the query's CSV is not in."""
    s = summary(data) if s is None else s
    num = lambda x: f"{x:,.0f}"
    pct = lambda x: f"{100 * x:.1f}%" if x >= 0.001 else f"{100 * x:.2f}%"
    out = {}
    if "daily_active_accounts" in s:
        x = s["daily_active_accounts"]
        out["daily_active_accounts"] = (f"Accounts signing at least one transaction averaged {num(x['first'])} a day over the first {x['days']} days "
                                        f"and {num(x['last'])} over the last {x['days']}, {x['change']}.")
    if "daily_transactions" in s:
        x = s["daily_transactions"]
        out["daily_transactions"] = (f"NEAR carried {num(x['first'])} transactions a day over the first {x['days']} days "
                                     f"and {num(x['last'])} over the last {x['days']}, {x['change']}.")
    if "intents_share" in s:
        x = s["intents_share"]
        out["intents_share"] = (f"intents.near received {pct(x['last'])} of all receipts over the last {x['days']} days, "
                                f"against {pct(x['first'])} over the first {x['days']}: its share of network activity {x['trend']}.")
    if "top_contracts" in s:
        x = s["top_contracts"]
        r1, r0 = x["last"], x["first"]
        if r1:
            out["top_contracts"] = (f"intents.near ranked {_ord(r1['rank'])} by function calls over the last 30 days ({pct(r1['share'])} of all calls)"
                                    + (f", against {_ord(r0['rank'])} over the first 30." if r0 else ", and was not among the top 25 over the first 30."))
        else:
            out["top_contracts"] = "intents.near was not among the contracts returned for the last 30 days."
    return out


def status_line(data):
    ok = [n for n, q in data.items() if q["status"] == "ok"]
    bad = [n for n, q in data.items() if q["status"] == "invalid"]
    if not ok and not bad:
        return ("the queries are written; their results are not committed yet, so the dashboard shows each query "
                "with its SQL and no chart. They never feed the headline numbers or the result hash")
    dates = sorted(r["block_date"] for n in ok for r in data[n]["rows"] if "block_date" in r)
    rng = f", block dates {dates[0]} to {dates[-1]}" if dates else ""
    return (f"{len(ok)} of {len(data)} query results loaded from `data/bq/`{rng}"
            + (f"; {len(bad)} could not be read ({', '.join(bad)})" if bad else ""))


def doc_values(d=None):
    """Placeholders for docs.py: BQ_STATUS, BQ_TABLE, BQ_FINDING."""
    data = load(d)
    s = summary(data)
    say = sentences(data, s)
    st = lambda q: ("pending" if q["status"] == "pending" else f"could not be read: {q['reason']}" if q["status"] == "invalid"
                    else f"{len(q['rows'])} rows, sha256 `{q['sha256'][:12]}`")
    table = ("| Query | Measures | Table | Result |\n|---|---|---|---|\n"
             + "\n".join(f"| [`queries/{n}.sql`](queries/{n}.sql) | {what} | `{t}` | {st(data[n])} |" for n, _, what, t in QUERIES))
    finding = say.get("intents_share") or "Pending until `data/bq/intents_share.csv` is added."
    return dict(BQ_STATUS=status_line(data), BQ_TABLE=table, BQ_FINDING=finding)


# ---------------- dashboard chapter ----------------

CSS = """
.bq .bqg{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
.bq .bqg>*{min-width:0}
.bq .mult{padding:0;border:0;margin-top:6px}
.bq .fig h3{font:400 clamp(20px,1.6vw,24px)/1.25 var(--serif);margin:6px 0 0;text-wrap:balance}
.bq .says{margin:12px 0 0;font-size:14.5px;color:var(--ink-2);line-height:1.55;max-width:60ch}
.bq .pend{margin-top:14px;border-radius:12px;padding:22px 20px;font-size:13.5px;color:var(--ink-2);line-height:1.5}
.bq .pend b{display:block;font:400 20px/1.2 var(--serif);color:var(--ink);margin-bottom:4px}
.bq .meta{margin:12px 0 0;font-size:12px;color:var(--muted);overflow-wrap:anywhere}
.bq details.sql{margin-top:14px;border-top:1px solid var(--rule-2)}
.bq details.sql[open]{border-bottom:0;padding-bottom:0}
.bq details.sql>summary{font:500 13px var(--sans);padding:12px 26px 4px 0;color:var(--ink-2)}
.bq details.sql>summary::after{width:7px;height:7px;top:58%}
.bq details.sql pre.term{margin-top:10px;font-size:11.5px;max-height:420px;overflow:auto}
.bq .why{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid var(--rule);margin-top:40px}
.bq .why>div{padding:16px 20px 0 0;min-width:0}.bq .why>div+div{padding-left:20px;border-left:1px solid var(--rule-2)}
.bq .why h4{margin:0 0 6px;font:400 20px/1.2 var(--serif)}.bq .why p{margin:0;font-size:13.5px;color:var(--ink-2);line-height:1.55}
.bq .bars .srow .nm code{font-size:12.5px}.bq .bars .srow .rk{color:var(--muted);font-size:12px;margin-left:6px}
@media (max-width:900px){.bq .bqg{grid-template-columns:minmax(0,1fr)}.bq .why{grid-template-columns:minmax(0,1fr)}
 .bq .why>div+div{padding-left:0;border-left:0;border-top:1px solid var(--rule-2);margin-top:16px}}
"""


def chapter(num="06", cid="c6", d=None):
    """(section html, data for the page's JSON blob). Always renders; queries without a CSV show as pending."""
    e = html.escape
    data = load(d)
    s = summary(data)
    say = sentences(data, s)
    pct = lambda x: f"{100 * x:.1f}%" if x >= 0.001 else f"{100 * x:.2f}%"
    sql = {n: open(os.path.join(HERE, "queries", n + ".sql")).read() for n, _, _, _ in QUERIES
           if os.path.isfile(os.path.join(HERE, "queries", n + ".sql"))}
    blob = {}

    def card(name, title, chart):
        q = data[name]
        if q["status"] == "ok":
            body = chart + f"<p class='says'>{e(say.get(name, ''))}</p>"
            rng = ""
            if q["rows"] and "block_date" in q["rows"][0]:
                rng = f" · {q['rows'][0]['block_date']} to {q['rows'][-1]['block_date']}"
            meta = f"<p class='meta'><code>{q['path']}</code> · {len(q['rows'])} rows{rng} · sha256 <code>{q['sha256'][:12]}</code></p>"
        else:
            what = ("Not run yet" if q["status"] == "pending" else "Result file could not be read")
            why = (f"Run <code>queries/{name}.sql</code> and save the result as <code>{q['path']}</code>; the chart and its sentence are written from that file."
                   if q["status"] == "pending" else f"<code>{q['path']}</code>: {e(q['reason'] or '')}. Re-export it from BigQuery as CSV with a header row.")
            body = f"<div class='pend hatch'><b>{what}</b>{why}</div>"
            meta = ""
        code = sql.get(name, "")
        sqlh = (f"<details class='sql'><summary>The query behind it · <code>queries/{name}.sql</code></summary>"
                f"<pre class='term'>{e(code)}</pre></details>") if code else ""
        eyebrow = next(w for n, _, w, _ in QUERIES if n == name)
        return (f"<figure class='fig'><div class='eyebrow'>{e(eyebrow)}</div><h3>{e(title)}</h3>{body}{meta}{sqlh}</figure>")

    def spark(key, rows, field, mul=1, unit="", dp=0, color="ink", aria=""):
        blob[key] = [{"date": r["block_date"], "v": r[field]} for r in rows]
        return (f"<div class='mult'><div class='chart spark' tabindex='0' data-src='{key}' data-key='v' data-mul='{mul}' data-dp='{dp}' "
                f"data-unit='{unit}' data-color='{color}' data-aria='{e(aria)}'></div></div>")

    cards = []
    q = data["daily_active_accounts"]
    x = s.get("daily_active_accounts")
    cards.append(card("daily_active_accounts",
                      f"Daily active accounts {x['change']} across the window" if x else "Daily active accounts",
                      spark("bq_dau", q["rows"], "active_accounts", aria="Daily active accounts on NEAR, by day") if x else ""))
    q = data["daily_transactions"]
    x = s.get("daily_transactions")
    cards.append(card("daily_transactions",
                      f"Daily transactions {x['change']} across the window" if x else "Daily transactions",
                      spark("bq_tx", q["rows"], "transactions", aria="Transactions on NEAR, by day") if x else ""))
    q = data["intents_share"]
    x = s.get("intents_share")
    if x:
        rows = [dict(block_date=r["block_date"], share=r["intents_receipts"] / r["receipts"] if r["receipts"] else None) for r in q["rows"]]
        ch = spark("bq_share", [r for r in rows if r["share"] is not None], "share", mul=100, unit="%", dp=1, color="teal",
                   aria="Share of all NEAR receipts received by intents.near, by day")
        t = f"intents.near's share of NEAR receipts {x['trend']}: {pct(x['first'])} to {pct(x['last'])}"
    else:
        ch, t = "", "intents.near's share of NEAR receipts"
    cards.append(card("intents_share", t, ch))
    x = s.get("top_contracts")
    if x:
        top = x["top_last"]
        mx = max((r["share"] for r in top), default=1) or 1
        rows = "".join(
            f"<div class='srow'><span class='nm'><code>{e(r['contract'])}</code><span class='rk'>"
            f"{'was ' + str(x['top_first'][r['contract']]) if r['contract'] in x['top_first'] else 'new in top 25'}</span></span>"
            f"<span class='pc'>{pct(r['share'])}</span><span class='tr'><i class='{'t' if r['contract'] == INTENTS else ''}' style='width:{100 * r['share'] / mx:.1f}%'></i></span></div>"
            for r in top)
        ch = (f"<p class='fig-sub' style='margin-top:10px'>Share of all function calls, last 30 days, top 10; grey text: rank in the first 30 days</p>"
              f"<div class='senders bars' role='list'>{rows}</div>")
        r1 = x["last"]
        t = f"intents.near ranks {_ord(r1['rank'])} by function calls" if r1 else "The contracts NEAR's function calls go to"
    else:
        ch, t = "", "The contracts NEAR's function calls go to"
    cards.append(card("top_contracts", t, ch))

    x = s.get("intents_share")
    if x:
        h2 = (f"intents.near received {pct(x['last'])} of NEAR's receipts in the last {x['days']} days, "
              + ("up from" if x["trend"] == "rose" else "down from" if x["trend"] == "fell" else "close to") + f" {pct(x['first'])}.")
        link = {"rose": "Intents is taking a larger share of the chain's activity, which fits the claim that NEAR's token flow is moving to the application layer. "
                        "It does not by itself raise payback: the buyback account is paid from Intents fees, not from receipts.",
                "fell": "Intents is a smaller share of the chain's activity than at the start of the window. Payback depends on Intents fees, not on receipts, "
                        "so this is context for the thesis rather than a test of it.",
                "held about steady": "Intents' footprint on chain has held about steady. Payback depends on Intents fees, not on receipts, "
                                     "so this is context for the thesis rather than a test of it."}[x["trend"]]
    else:
        h2 = "Network activity: the queries are ready; their results are not committed yet."
        link = ("The queries are written and filtered on <code>block_date</code>; their results are not in this build yet. "
                "Each panel below shows its SQL and says what file it is waiting for.")
    intro = (f"Daily active accounts, transactions and contract usage, from Google's public NEAR dataset "
             f"<code>{DATASET}</code>. {link}")
    why = ("<div class='why'>"
           "<div><h4>How to run them</h4><p>Open the BigQuery console (the sandbox is free and needs no card), paste a file from <code>queries/</code>, "
           "Run, then Save results → CSV (local file) as <code>data/bq/&lt;name&gt;.csv</code>. Or: <code>bq query --use_legacy_sql=false --format=csv "
           "--max_rows=1000 &lt; queries/x.sql &gt; data/bq/x.csv</code>. Then <code>python3 run.py</code>.</p></div>"
           "<div><h4>Kept apart from the result</h4><p><code>run.py</code> never reads these files, so the headline numbers and the result hash do not depend on "
           "an account with Google. Each CSV's sha256 is shown under its chart.</p></div>"
           "<div><h4>No Intents Explorer pull</h4><p>The 1Click Swap API terms (section 4.1(e)) forbid keeping its data beyond 24 hours, so a committed copy "
           "could not be re-checked. Intents volume and fees come from DefiLlama's public series instead.</p></div></div>")
    page = (f"<style>{CSS}</style><section class='chapter bq' id='{cid}' data-t='Network activity'><div class='ch-head'><div class='ch-num'>"
            f"<span class='n'>{num}</span><span class='eyebrow'>Network activity (BigQuery)</span><span class='line'></span></div>"
            f"<h2>{e(h2)}</h2><p>{intro}</p></div><div class='bqg'>{''.join(cards)}</div>{why}</section>")
    return page, blob
