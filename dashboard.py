"""Render out/results.json (+ optional ledger) to one static HTML file. No dependencies."""
import html, json

CSS = """
:root{color-scheme:light;--bg:#f5f4f1;--surface:#fcfcfb;--text:#0b0b0b;--text2:#52514e;--muted:#8a897f;
--grid:#e4e3de;--s1:#2a78d6;--good:#1a7f37;--bad:#c62828}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#111110;--surface:#1a1a19;--text:#f0efec;
--text2:#c3c2b7;--muted:#8a897f;--grid:#2e2e2b;--s1:#3987e5;--good:#4cc26a;--bad:#ef6b6b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:28px;line-height:1.2;margin:0 0 8px;text-wrap:balance}h2{font-size:17px;margin:40px 0 4px}
p{margin:0 0 12px;color:var(--text2);max-width:72ch}code{font:13px ui-monospace,monospace;overflow-wrap:anywhere}
.grid>*,.tiles>*{min-width:0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:24px 0}
.tile,.card{background:var(--surface);border:1px solid var(--grid);border-radius:10px;padding:16px}
.tile b{display:block;font-size:30px;line-height:1.1;font-variant-numeric:tabular-nums}
.tile span{color:var(--text2);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.card h3{font-size:14px;margin:0;font-weight:600}.card small{color:var(--text2)}
svg{display:block;width:100%;height:auto;overflow:visible}svg text{fill:var(--muted);font-size:11px}
.tip{position:absolute;pointer-events:none;background:var(--text);color:var(--surface);padding:4px 8px;
border-radius:6px;font-size:12px;white-space:nowrap;transform:translate(-50%,-130%);display:none}
.card{position:relative}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{text-align:right;padding:6px 10px;border-bottom:1px solid var(--grid)}
th:first-child,td:first-child{text-align:left}th{color:var(--text2);font-weight:500;font-size:13px}
.wrap{overflow-x:auto}.pass{color:var(--good);font-weight:600}.fail{color:var(--bad);font-weight:600}
.calc label{display:block;margin:0 0 14px;font-size:14px}.calc output{float:right;color:var(--text2);font-variant-numeric:tabular-nums}
.calc input{display:block;width:100%;margin-top:6px;accent-color:var(--s1)}
.meter{height:10px;border-radius:5px;background:var(--grid);overflow:hidden}.meter i{display:block;height:100%;background:var(--s1);width:0}
.banner{border-left:4px solid var(--s1);padding:10px 14px;background:var(--surface);margin:16px 0}
"""

JS = """
const C=document.querySelector('.calc');if(C){const g=id=>document.getElementById(id),f=()=>{
 const v=+g('vol').value,c=+g('cap').value,n=+g('inf').value,c0=+C.dataset.cap;
 const p=(+C.dataset.burn+ +C.dataset.buy*v*c/c0)*2.5/n;
 g('o-vol').textContent=v.toFixed(1)+'x today';g('o-cap').textContent=c+'%'+(c==c0?' (today)':'');
 g('o-inf').textContent=n.toFixed(1)+'% a year'+(n==2.5?' (today)':'');
 g('bar').style.width=Math.min(100,p*100)+'%';
 g('o-pay').textContent='Payback: '+(p*100).toFixed(1)+'% of issuance'+(p>=1?'. Break-even reached: supply stops growing net of buybacks.':'. Break-even is '+(1/p).toFixed(1)+'x away.')};
 C.addEventListener('input',f);f()}
const D=JSON.parse(document.getElementById('data').textContent),NS='http://www.w3.org/2000/svg';
function el(n,a,p){const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);p&&p.appendChild(e);return e}
document.querySelectorAll('[data-chart]').forEach(card=>{
 const key=card.dataset.chart,mul=+card.dataset.mul,unit=card.dataset.unit,dp=+card.dataset.dp;
 const P=D.filter(d=>d[key]!=null);if(P.length<2){card.remove();return}const xs=P.map(d=>d.t),ys=P.map(d=>d[key]*mul),W=480,Ht=200,L=44,R=8,T=10,B=22;
 const x0=xs[0],x1=xs[xs.length-1],y1=Math.max(...ys)*1.08,sx=x=>L+(x-x0)/(x1-x0)*(W-L-R),sy=y=>Ht-B-y/y1*(Ht-T-B);
 const svg=el('svg',{viewBox:`0 0 ${W} ${Ht}`,role:'img','aria-label':card.querySelector('h3').textContent},card);
 for(let i=0;i<=4;i++){const v=y1*i/4;el('line',{x1:L,x2:W-R,y1:sy(v),y2:sy(v),stroke:'var(--grid)'},svg);
  el('text',{x:L-6,y:sy(v)+4,'text-anchor':'end'},svg).textContent=v.toFixed(dp)}
 [0,.5,1].forEach(f=>{const i=Math.round(f*(P.length-1));
  el('text',{x:sx(xs[i]),y:Ht-6,'text-anchor':f==0?'start':f==1?'end':'middle'},svg).textContent=P[i].date});
 el('path',{d:'M'+xs.map((x,i)=>sx(x).toFixed(1)+','+sy(ys[i]).toFixed(1)).join('L'),fill:'none',stroke:'var(--s1)','stroke-width':2,'stroke-linejoin':'round'},svg);
 const ch=el('line',{y1:T,y2:Ht-B,stroke:'var(--muted)',visibility:'hidden'},svg),dot=el('circle',{r:4,fill:'var(--s1)',stroke:'var(--surface)','stroke-width':2,visibility:'hidden'},svg);
 const tip=document.createElement('div');tip.className='tip';card.appendChild(tip);
 svg.addEventListener('pointermove',e=>{const r=svg.getBoundingClientRect(),px=(e.clientX-r.left)/r.width*W;
  let i=0;for(let j=1;j<xs.length;j++)if(Math.abs(sx(xs[j])-px)<Math.abs(sx(xs[i])-px))i=j;
  ch.setAttribute('x1',sx(xs[i]));ch.setAttribute('x2',sx(xs[i]));ch.setAttribute('visibility','visible');
  dot.setAttribute('cx',sx(xs[i]));dot.setAttribute('cy',sy(ys[i]));dot.setAttribute('visibility','visible');
  tip.textContent=P[i].date+': '+ys[i].toFixed(dp+1)+unit;tip.style.display='block';
  tip.style.left=(svg.offsetLeft+sx(xs[i])/W*r.width)+'px';tip.style.top=(svg.offsetTop+sy(ys[i])/Ht*r.height)+'px'});
 svg.addEventListener('pointerleave',()=>{tip.style.display='none';ch.setAttribute('visibility','hidden');dot.setAttribute('visibility','hidden')});
});
"""

CHARTS = [  # key, title, subtitle, multiplier, unit, decimals
    ("payback", "Payback", "Burn plus buybacks as % of issuance, 100-epoch rolling", 100, "%", 1),
    ("multiple", "Distance to break-even", "Multiple of today's burn plus buybacks that offsets issuance", 1, "x", 1),
    ("buyback_per_day", "Buybacks", "NEAR added to the buyback account per day", 1, " NEAR", 0),
    ("burn_per_day", "Burn", "NEAR burnt in gas fees per day (exact)", 1, " NEAR", 0),
    ("coverage", "Burn-only coverage", "Fee burn as % of issuance (exact)", 100, "%", 2),
    ("utilization", "Block utilization", "Gas used as % of gas limit, sampled", 100, "%", 2),
]


def render(results, sha, ledger=None):
    s, e = results["summary"], html.escape
    pct = lambda x, n=2: f"{100 * x:.{n}f}%"
    num = lambda x: f"{x:,.0f}"
    if s["payback"] is not None:
        head = (f"NEAR's fee burn plus Intents buybacks equal {pct(s['payback'], 1)} of what it mints. "
                f"Break-even is {s['multiple']:.1f}x away.")
        lede = (f"{pct(s['buyback_coverage'], 1)} is NEAR sent by the NEAR Intents contract to the buyback account, "
                f"where it is held, not burnt. {pct(s['burn_coverage'])} is gas fees burnt. A fee-burn dashboard "
                f"sees only the second number and puts break-even {s['burn_only_multiple']:.0f}x away.")
        tiles = [(pct(s["payback"], 1), "of new issuance offset by burn plus buybacks"),
                 (f"{s['multiple']:.1f}x", "growth in fee flows that offsets issuance"),
                 (num(s["buyback_per_day"]), "NEAR a day into the buyback account (on-chain balance)"),
                 (num(s["burn_per_day"]), "NEAR a day burnt in gas fees (exact)"),
                 (num(s["mint_per_day"]), "NEAR a day minted to validators (exact)"),
                 (pct(s["net_inflation"]), f"net inflation after payback (gross {pct(s['realized_inflation'])})")]
    else:
        head = f"NEAR burns back {pct(s['burn_coverage'])} of what it mints."
        lede = "Buyback balances are not cached for this window yet."
        tiles = [(pct(s["burn_coverage"]), "of issuance burnt back by fees"),
                 (num(s["burn_per_day"]), "NEAR a day burnt in gas fees (exact)"),
                 (num(s["mint_per_day"]), "NEAR a day minted to validators (exact)")]
    tiles.append((pct(s["ceiling"], 0), f"burn coverage if blocks were full at today's gas price "
                                        f"(90% range {pct(s['ceiling_p05'], 0)} to {pct(s['ceiling_p95'], 0)})"))
    g = s.get("payback_growth_per_year")
    trend = ("Not enough history with buyback data for a trend yet." if g is None else
             f"Payback has grown {pct(g, 0)} a year (log scale) and reaches break-even in "
             f"{s['years_to_breakeven_at_trend']:.1f} years at that rate." if s.get("years_to_breakeven_at_trend") else
             f"Payback has changed {pct(g, 0)} a year (log scale); at that rate break-even is not reached.")
    nr = lambda x: "n/a" if x is None else f"{x:,.0f}"
    check = (f"<tr><td>Gas fees burnt</td><td>{nr(s['burn_per_day'])}</td><td>{nr(s['llama_burn_near_per_day'])} "
             f"(assumes 70% of {nr(s['llama_fees_near_per_day'])} in fees)</td></tr>"
             f"<tr><td>Buyback account gain</td><td>{nr(s['buyback_per_day'])}</td><td rowspan='2'>{nr(s['llama_buyback_near_per_day'])} "
             f"(captured revenue, all wallets)</td></tr>"
             f"<tr><td>All three revenue wallets, gain</td><td>{nr(s['all_revenue_wallets_per_day'])}</td></tr>")
    rows = "".join(
        f"<tr><td>{e(m)}</td><td>{v['pinball']:.4f}</td><td>{100 * v['skill_vs_persistence']:+.1f}%</td>"
        f"<td>{100 * v['interval_hit']:.0f}%</td><td>{v['n']}</td></tr>" for m, v in results["backtest"].items())
    led = ""
    if ledger:
        cls = {"PASS": "pass", "HIT": "pass", "FALSIFIED": "fail", "MISS": "fail"}
        names = {"payback": "Payback over the 30 epochs (90% interval). This one sets the verdict.",
                 "burn_total": "NEAR burnt over the 30 epochs (80% interval)",
                 "buyback_total": "NEAR gained by the buyback account (80% interval)"}
        fmt = lambda n, x: "pending" if x is None else f"{100 * x:.1f}%" if n == "payback" else f"{x:,.0f}"
        cr = "".join(f"<tr><td>{names[n]}</td><td>{fmt(n, c['lo'])} to {fmt(n, c['hi'])}</td><td>{fmt(n, c['actual'])}</td>"
                     f"<td class='{cls.get(c['verdict'], '')}'>{c['verdict']}</td></tr>" for n, c in ledger["claims"].items())
        lr = "".join(f"<tr><td>{r['k']}</td><td>{r['q10']:.1f}</td><td>{r['q50']:.1f}</td><td>{r['q90']:.1f}</td>"
                     + (f"<td>{r['actual']:.1f}</td><td>{'yes' if r['hit'] else 'no'}</td></tr>" if r["actual"] is not None
                        else "<td>pending</td><td></td></tr>") for r in ledger["rows"])
        led = (f"<h2>Live ledger</h2><p>These forecasts were frozen before the epochs they describe existed; commitment "
               f"<code>{e(ledger['commit'])}</code>. {ledger['resolved']} of {ledger['total']} epochs have closed. Verdict: "
               f"<span class='{cls.get(ledger['verdict'], '')}'>{e(ledger['verdict'])}</span>.</p>"
               f"<div class='card wrap'><table><tr><th>Claim</th><th>Committed interval</th><th>Actual</th><th>Result</th></tr>{cr}</table></div>"
               f"<p style='margin-top:16px'>NEAR burnt in each epoch against the committed 80% interval "
               f"({e(ledger['table_model'])} model). {ledger['hits']} of {ledger['resolved']} inside so far.</p>"
               f"<div class='card wrap'><table><tr><th>Epoch</th><th>10%</th><th>50%</th><th>90%</th><th>Actual</th>"
               f"<th>In interval</th></tr>{lr}</table></div>")
    cards = "".join(f"<div class='card' data-chart='{k}' data-mul='{m}' data-unit='{u}' data-dp='{d}'>"
                    f"<h3>{e(t)}</h3><small>{e(sub)}</small></div>" for k, t, sub, m, u, d in CHARTS)
    bt = (f"<h2>Does the clock or the price explain the burn?</h2><p>Walk-forward backtest of burn per epoch, "
          f"{next(iter(results['backtest'].values()))['n']} forecasts, up to 30 epochs ahead. Lower pinball loss is better. "
          f"All three models share the same recent level; one adds a time-of-week profile, one adds NEAR's price."
          f"</p><div class='card wrap'><table><tr><th>Model</th>"
          f"<th>Pinball loss</th><th>Skill vs persistence</th><th>80% interval hit rate</th><th>Forecasts</th></tr>{rows}"
          f"</table></div>") if results["backtest"] else ""
    calc = ""
    if s["payback"] is not None and s.get("capture_share"):
        cap = max(1, round(100 * s["capture_share"]))
        calc = f"""<h2>What closes the gap</h2>
<p>Payback is burn plus buybacks over issuance. Three levers move it. Two of them are governance decisions.</p>
<div class="card calc" data-burn="{s['burn_coverage']}" data-buy="{s['buyback_coverage']}" data-cap="{cap}">
<label>NEAR Intents volume <output id="o-vol">1.0x today</output>
<input type="range" id="vol" min="1" max="20" step="0.5" value="1"></label>
<label>Share of gross Intents fees reaching the buyback account <output id="o-cap">{cap}% (today)</output>
<input type="range" id="cap" min="{cap}" max="100" step="1" value="{cap}"></label>
<label>Issuance rate <output id="o-inf">2.5% a year (today)</output>
<input type="range" id="inf" min="0.5" max="2.5" step="0.1" value="2.5"></label>
<div class="meter"><i id="bar"></i></div>
<p id="o-pay" aria-live="polite" style="margin:8px 0 0;color:var(--text)"></p></div>"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Coverage: what NEAR pays back</title>
<style>{CSS}</style></head><body><main>
<h1>{e(head)}</h1>
<p>{e(lede)}</p>
<p>Mint, burn and the buyback balance are read from NEAR mainnet, {e(s['first'])} to {e(s['last'])}
({s['epochs']} epochs, heights {s['first_height']} to {s['last_height']}). Mint and burn are exact to the yoctoNEAR.
Rebuild with <code>python3 run.py</code>: no keys, no network.</p>
<div class="banner">{e(trend)}</div>
<div class="tiles">{''.join(f"<div class='tile'><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in tiles)}</div>
<div class="grid">{cards}</div>
{calc}
<h2>Chain versus the indexer</h2>
<p>The same flows over the same days, in NEAR a day. DefiLlama reports USD; each day is converted at that day's price.</p>
<div class="card wrap"><table><tr><th>Flow, NEAR a day</th><th>This repo, from chain</th><th>DefiLlama</th></tr>{check}</table></div>
{bt}
{led}
<p style="margin-top:32px"><small>Result hash <code>{sha}</code></small></p>
</main><script type="application/json" id="data">{json.dumps(results['series'], separators=(',', ':'))}</script>
<script>{JS}</script></body></html>"""
