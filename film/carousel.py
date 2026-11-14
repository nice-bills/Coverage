#!/usr/bin/env python3
"""A 10-panel X carousel (1080x1350 each) that reads as one continuous strip: the payback chart runs across
panels 3 to 7. Every number comes from out/results.json. Writes film/out/carousel/panel-01.png ... and strip.png.
Run from the repo root after python3 run.py:  python3 film/carousel.py"""
import datetime, html, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import verdict

r = json.load(open(os.path.join(ROOT, "out", "results.json")))
s, sc, se = r["summary"], r["scenarios"], [x for x in r["series"] if x.get("payback") is not None]
e = html.escape
PW, H, N = 1080, 1350, 10
W = PW * N
pct = lambda x, n=1: f"{100 * x:.{n}f}%"
num = lambda x: f"{x:,.0f}"
full = sc["levers"]["capture"][-1]
base = sc["cases"]["base"]

# ---- the chart across panels 3..7 ----
X0, X1 = 2 * PW + 70, 7 * PW - 70
Y0, Y1 = 1160, 600          # 0% at Y0, YMAX at Y1
YMAX = 0.20
t0 = datetime.date.fromisoformat(se[0]["date"]).toordinal()
t1 = datetime.date.fromisoformat(se[-1]["date"]).toordinal()
xd = lambda d: X0 + (datetime.date.fromisoformat(d).toordinal() - t0) / (t1 - t0) * (X1 - X0)
yv = lambda v: Y0 - min(v, YMAX) / YMAX * (Y0 - Y1)
pts = [(xd(p["date"]), p) for p in se]
burn_top = [(x, yv(p["coverage"])) for x, p in pts]
pay_top = [(x, yv(p["payback"])) for x, p in pts]
poly = lambda top, bot: " ".join(f"{x:.1f},{y:.1f}" for x, y in top) + " " + " ".join(f"{x:.1f},{y:.1f}" for x, y in reversed(bot))
base_line = [(x, Y0) for x, _ in pts]
svg = [f"<polygon points='{poly(pay_top, burn_top)}' fill='var(--teal)' opacity='.22'/>",
       f"<polygon points='{poly(burn_top, base_line)}' fill='var(--terra)' opacity='.55'/>",
       "<polyline fill='none' stroke='var(--ink)' stroke-width='4' stroke-linejoin='round' points='" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pay_top) + "'/>"]
for v in (0.05, 0.10, 0.15, 0.20):
    svg.append(f"<line x1='{X0}' x2='{X1}' y1='{yv(v):.1f}' y2='{yv(v):.1f}' stroke='var(--rule)' stroke-width='2'/>")
    for k in range(2, 7):  # a y label at the left of every chart panel, so each panel reads alone
        svg.append(f"<text x='{k * PW + 70}' y='{yv(v) - 10:.1f}' class='ax'>{int(v * 100)}%</text>")
svg.append(f"<line x1='{X0}' x2='{X1}' y1='{Y0}' y2='{Y0}' stroke='var(--ink)' stroke-width='3'/>")
d = datetime.date.fromordinal(t0)
while d.toordinal() <= t1:
    if d.day == 1:
        x = xd(d.isoformat())
        svg.append(f"<line x1='{x:.1f}' x2='{x:.1f}' y1='{Y0}' y2='{Y0 + 14}' stroke='var(--ink)' stroke-width='3'/><text x='{x:.1f}' y='{Y0 + 52}' class='mo'>{d:%b}</text>")
    d += datetime.timedelta(days=1)
pk = max(se, key=lambda p: p["payback"])
peak = dict(pk, payback=s["payback_peak"], date=s["payback_peak_date"])  # exact figures; the series is every third epoch
marks = [("2026-04-23", "Intents starts paying the buyback account", None),
         (peak["date"], f"Peak: {pct(peak['payback'])}", peak["payback"]),
         ("2026-10-27", "Swaps go private", None),
         (se[-1]["date"], f"Now: {pct(s['payback'])}", s["payback"])]
for dd, label, v in marks:
    x = xd(dd)
    svg.append(f"<line x1='{x:.1f}' x2='{x:.1f}' y1='{Y1 - 60}' y2='{Y0}' stroke='var(--ink)' stroke-width='2' stroke-dasharray='6 8' opacity='.55'/>")
    if v is not None:
        svg.append(f"<circle cx='{x:.1f}' cy='{yv(v):.1f}' r='11' fill='var(--paper)' stroke='var(--ink)' stroke-width='4'/>")
    if dd == se[-1]["date"]:  # "now": beside the end point, below the line
        svg.append(f"<text x='{x - 18:.1f}' y='{yv(v) + 56:.1f}' text-anchor='end' class='mk'>{e(label)}</text>")
    elif dd == "2026-04-23":  # sits near the panel 3/4 seam: keep the label inside panel 3
        svg.append(f"<text x='{x - 16:.1f}' y='{Y1 - 34}' text-anchor='end' class='mk'>{e(label)}</text>")
    else:
        svg.append(f"<text x='{x + 16:.1f}' y='{Y1 - 34}' class='mk'>{e(label)}</text>")
chart = f"<svg class='chart' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>{''.join(svg)}</svg>"

# ---- copy per panel: (eyebrow, html) ----
def first(prefix):
    return next(p for p in se if p["date"] >= prefix)
apr, aug = first("2026-06-01"), first("2026-08-01")
P = [
    ("Coverage · NEAR, measured from the chain",
     f"<h1>NEAR makes <em>{num(s['mint_per_day'])}</em> new coins a day.</h1><p class='lead'>About {pct(s['realized_inflation'])} more supply every year. How many come back?</p><p class='swipe'>Swipe →</p>"),
    ("The usual answer",
     f"<div class='big terra'>{pct(s['burn_coverage'], 2)}</div><p class='lead'>is burnt in gas fees. On that view NEAR needs <b>{s['burn_only_multiple']:.0f}×</b> more activity before it destroys as much as it makes.</p>"
     f"<div class='bar'><i style='width:{max(100 * s['burn_coverage'], .8):.2f}%'></i></div><p class='cap'>Every NEAR minted. The red sliver is what gets burnt.</p>"),
    ("March to April", "<h2>Until April, only the burn came back.</h2><p class='lead'>Red: gas burnt, as a share of all new NEAR.</p>"),
    ("April onwards", f"<h2>Then <em>NEAR Intents</em> started paying a buyback account.</h2><p class='lead'>The teal band. By 1 June: {pct(apr['payback'])} of issuance.</p>"),
    ("Summer", f"<h2>The buybacks grow with Intents' volume.</h2><p class='lead'>The black line is both together: {pct(aug['payback'])} by 1 August.</p>"),
    ("September", f"<h2>Peak: <em>{pct(peak['payback'])}</em> of new NEAR came back.</h2><p class='lead'>On {datetime.date.fromisoformat(peak['date']):%-d %B}, over a 100-epoch window.</p>"),
    ("October to now", f"<h2>Swaps went private on 27 October. The money still shows.</h2><p class='lead'>The buyback balance is on chain, so it still counts.</p>"),
    ("So what changed?",
     f"<p class='lead'>Distance to break-even</p><div class='big'><span class='teal'>{s['multiple']:.1f}×</span></div><div class='big strike'>{s['burn_only_multiple']:.0f}×</div>"
     f"<p class='lead'>Count the buybacks and NEAR is <b>{s['burn_only_multiple'] / s['multiple']:.0f} times</b> closer to winning back what it mints.</p>"),
    ("Verdict for an investor",
     f"<h2>Not yet a supply story.</h2><h2 class='teal'><i>The bet is governance.</i></h2>"
     f"<p class='lead'>At the median growth rate, break-even comes in {base['year'] or 'over a century'}. Send every Intents fee to the buyback and cut issuance (HSP-029), and it comes in about <b>{full['years_base_hsp029']:.0f} years</b>.</p>"
     f"<p class='cap'>HSP-029's veto window closes 16 Nov 2026.</p>"),
    ("Don't trust us. Check it.",
     f"<div class='term'><span class='dim'>$</span> python3 run.py</div><p class='lead'>One command rebuilds every number here from NEAR block headers. No keys, no network.</p>"
     f"<p class='lead'>Our forecasts were frozen in Bitcoin before the data existed. The chain scores them while you judge.</p><p class='url'>nice-bills.github.io/Coverage</p>"),
]
blocks = []
for i, (eb, body) in enumerate(P):
    top = 110 if 2 <= i <= 6 else 150
    blocks.append(f"<section style='left:{i * PW}px;top:{top}px'><div class='eyebrow'><span class='n'>{i + 1:02d}</span>{e(eb)}</div>{body}</section>")
    blocks.append(f"<div class='foot' style='left:{i * PW + 70}px'>Coverage · {i + 1}/{N}</div>")

page = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=JetBrains+Mono&display=block">
<style>
:root{{--paper:#F5F0E6;--card:#FAF6EE;--ink:#1D1B17;--ink2:#4A453C;--muted:#7A7265;--rule:#DDD4C3;--teal:#008C80;--terra:#C4532D;--gray:#E3DBCB;
--serif:"Instrument Serif",Georgia,serif;--sans:Inter,system-ui,sans-serif;--mono:"JetBrains Mono",monospace}}
*{{margin:0;box-sizing:border-box}}html,body{{width:{W}px;height:{H}px;overflow:hidden;background:var(--paper);color:var(--ink);font-family:var(--sans)}}
.chart{{position:absolute;left:0;top:0}}
.chart .ax{{font:500 26px var(--sans);fill:var(--muted)}}.chart .mo{{font:500 30px var(--sans);fill:var(--ink2);text-anchor:middle}}
.chart .mk{{font:600 30px var(--sans);fill:var(--ink)}}
section{{position:absolute;width:{PW}px;padding:0 70px}}
.eyebrow{{display:flex;align-items:center;gap:18px;font:500 24px var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:34px}}
.eyebrow .n{{font:italic 400 40px/1 var(--serif);letter-spacing:0;color:var(--teal)}}
h1{{font:400 118px/1 var(--serif);letter-spacing:-.025em}}h1 em,h2 em{{color:var(--teal)}}
h2{{font:400 74px/1.04 var(--serif);letter-spacing:-.02em;max-width:940px}}
.lead{{font:400 38px/1.4 var(--sans);color:var(--ink2);margin-top:30px;max-width:920px}}.lead b{{color:var(--ink);font-weight:600}}
.big{{font:400 300px/.95 var(--serif);letter-spacing:-.04em}}.terra{{color:var(--terra)}}.teal{{color:var(--teal)}}
.strike{{color:var(--muted);text-decoration:line-through;text-decoration-color:var(--terra);text-decoration-thickness:12px;font-size:180px}}
.bar{{height:70px;background:var(--gray);border-radius:12px;overflow:hidden;margin-top:70px}}.bar i{{display:block;height:100%;background:var(--terra)}}
.cap{{font:500 28px/1.4 var(--sans);color:var(--muted);margin-top:22px}}
.swipe{{font:400 64px var(--serif);font-style:italic;color:var(--teal);margin-top:120px}}
.term{{background:var(--ink);color:var(--paper);font:400 46px var(--mono);padding:34px 40px;border-radius:20px;margin-top:10px}}.term .dim{{color:#9C9384}}
.url{{font:400 54px var(--serif);margin-top:60px;border-bottom:3px solid var(--ink);display:inline-block}}
.foot{{position:absolute;bottom:52px;font:500 24px var(--sans);color:var(--muted);letter-spacing:.06em}}
</style></head><body>{chart}{''.join(blocks)}</body></html>"""
out = os.path.join(ROOT, "film", "out", "carousel")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w").write(page)
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:{W},height:{H}}},deviceScaleFactor:1}});
await p.route(u=>!/^file:|fonts\\.g/.test(u.href||u.toString()),r=>r.abort());await p.goto('file://{out}/index.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(800);
await p.screenshot({{path:'{out}/strip.png'}});await b.close()}})()"""
subprocess.run(["node", "-e", js], check=True)
from PIL import Image
im = Image.open(os.path.join(out, "strip.png")).convert("RGB")
for i in range(N):
    im.crop((i * PW, 0, (i + 1) * PW, H)).save(os.path.join(out, f"panel-{i + 1:02d}.png"))
im.resize((W // 6, H // 6)).save(os.path.join(out, "preview.png"))
print("wrote", N, "panels to", out)
