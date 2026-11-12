"""Render out/results.json (+ optional ledger) to one static HTML file. No dependencies, no external assets."""
import datetime, html, json

REPO = "https://github.com/nice-bills/Coverage"

# Tokens. Teal: NEAR that comes back to the token (buybacks). Orange: NEAR burnt. Ink: NEAR minted.
CSS = """
:root{color-scheme:light;--bg:oklch(.985 .003 180);--panel:oklch(.958 .005 180);--ink:oklch(.2 .01 200);
--ink2:oklch(.4 .012 200);--rule:oklch(.86 .006 180);--rest:oklch(.905 .005 180);--back:oklch(.5 .095 180);
--burn:oklch(.58 .16 45);--good:oklch(.45 .12 150);--bad:oklch(.5 .19 25);--z-nav:10;--z-tip:20}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:oklch(.17 .008 190);--panel:oklch(.215 .01 190);
--ink:oklch(.94 .005 180);--ink2:oklch(.76 .01 180);--rule:oklch(.32 .01 190);--rest:oklch(.27 .01 190);
--back:oklch(.74 .11 180);--burn:oklch(.74 .14 50);--good:oklch(.76 .14 150);--bad:oklch(.72 .16 25)}}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:56px}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
-webkit-font-smoothing:antialiased}
a{color:inherit;text-underline-offset:3px;text-decoration-thickness:1px}a:hover{color:var(--back)}
:focus-visible{outline:2px solid var(--back);outline-offset:2px}
code,.mono{font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere}
nav{position:sticky;top:0;z-index:var(--z-nav);background:var(--bg);border-bottom:1px solid var(--rule)}
nav div{max-width:1120px;margin:0 auto;padding:0 20px;display:flex;gap:22px;align-items:center;height:44px;
overflow-x:auto;white-space:nowrap;font-size:13.5px;scrollbar-width:none}
nav b{font-size:15px;letter-spacing:-.01em;margin-right:6px}nav a{text-decoration:none;color:var(--ink2)}
nav a:hover{color:var(--ink)}nav a:last-child{margin-left:auto;color:var(--ink)}
main{max-width:1120px;margin:0 auto;padding:0 20px 80px}
section{padding-top:56px}section>h2{font-size:22px;line-height:1.25;letter-spacing:-.015em;margin:0 0 6px;text-wrap:balance}
h3{font-size:15px;line-height:1.4;margin:0;font-weight:600;text-wrap:balance}
p{margin:0 0 12px;color:var(--ink2);max-width:72ch;text-wrap:pretty}
.stamp{color:var(--ink2);margin:40px 0 14px}
h1{font-size:38px;line-height:1.12;letter-spacing:-.025em;margin:0 0 14px;max-width:24ch;text-wrap:balance}
.lede{font-size:17px;max-width:64ch}
.strip{margin:34px 0 0}.strip h3{font-weight:500;color:var(--ink2);font-size:13.5px;margin-bottom:8px}
.bar{display:flex;height:44px;background:var(--rest);border:1px solid var(--ink)}.bar.thin{height:18px}
.bar i{display:block;min-width:3px;transition:width .2s cubic-bezier(.22,1,.36,1)}.bar .bk{background:var(--back)}.bar .bn{background:var(--burn)}
.key{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:6px 28px;margin:12px 0 0;padding:0;list-style:none;font-size:13.5px;color:var(--ink2)}
.key li{display:flex;gap:8px;align-items:baseline}.key b{color:var(--ink);font-variant-numeric:tabular-nums}
.sw{flex:none;width:10px;height:10px;display:inline-block;border:1px solid var(--ink);transform:translateY(1px)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin:36px 0 0;border-top:1px solid var(--ink)}
.facts div{padding:14px 20px 14px 0;border-bottom:1px solid var(--rule)}
.facts dt{font-size:13px;color:var(--ink2)}.facts dd{margin:2px 0 0;font-size:24px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.facts small{display:block;font-size:12.5px;font-weight:400;letter-spacing:0;color:var(--ink2)}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:0 40px;margin-top:20px}
figure{margin:0;padding:18px 0 20px;border-top:1px solid var(--rule);position:relative;min-width:0}
figure.lead{grid-column:1/-1;border-top-color:var(--ink)}
.sub{font-size:12.5px;margin:3px 0 10px;max-width:none}.src{font-size:11.5px;margin:8px 0 0;max-width:none}.src code{font-size:11px}
svg{display:block;width:100%;height:auto;overflow:visible}svg text{fill:var(--ink2);font:11px system-ui,sans-serif;font-variant-numeric:tabular-nums}
.tip{position:absolute;z-index:var(--z-tip);pointer-events:none;background:var(--ink);color:var(--bg);padding:3px 8px;
font-size:12px;white-space:nowrap;transform:translate(-50%,-135%);display:none;font-variant-numeric:tabular-nums}
.wrap{overflow-x:auto;margin:14px 0 0}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:14px}
th,td{text-align:right;padding:8px 0 8px 18px;border-bottom:1px solid var(--rule);vertical-align:top}
th:first-child,td:first-child{text-align:left;padding-left:0}th{color:var(--ink2);font-weight:500;font-size:12.5px;border-bottom-color:var(--ink)}
td small{color:var(--ink2)}.pass{color:var(--good);font-weight:600}.fail{color:var(--bad);font-weight:600}
.model{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:8px 40px;padding:22px 0;border-top:1px solid var(--rule)}
.model:first-of-type{border-top-color:var(--ink);margin-top:20px}.model h3{font-size:16px;margin-bottom:6px}
.model .wrap{margin:0}.how{font-size:12.5px;color:var(--ink2);margin:8px 0 0}
.inl{display:inline-block;height:8px;background:var(--ink2);vertical-align:middle;margin-right:8px}
.calc label{display:block;margin:0 0 16px;font-size:14px}.calc output{float:right;color:var(--ink2);font-variant-numeric:tabular-nums}
.calc input{display:block;width:100%;margin-top:6px;accent-color:var(--back)}
#o-pay{margin:8px 0 0;color:var(--ink);font-weight:600}
.round{padding:22px 0;border-top:1px solid var(--rule)}.round:first-of-type{border-top-color:var(--ink);margin-top:20px}
.round header{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;margin-bottom:4px}.round h3{font-size:16px}
.pill{font-size:12px;font-weight:600;padding:1px 8px;border:1px solid currentColor;border-radius:99px}
.pill.pending{color:var(--ink2)}.pill.pass{color:var(--good)}.pill.fail{color:var(--bad)}
.rgrid{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:8px 40px;margin-top:10px}
.claim{display:grid;grid-template-columns:minmax(0,1fr) 108px;gap:2px 12px;padding:9px 0;border-bottom:1px solid var(--rule);font-size:13.5px}
.claim b{font-weight:600}.claim span{color:var(--ink2);font-variant-numeric:tabular-nums}.claim .v{text-align:right;font-weight:600}
.claim svg{grid-column:1/-1;margin-top:2px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:0 40px;margin-top:20px}
.two h3{padding:10px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--rule)}
.two ul{margin:0;padding:0;list-style:none}.two li{padding:10px 0;border-bottom:1px solid var(--rule);color:var(--ink2);font-size:14px}
.two li b{color:var(--ink);font-weight:600}
.cmd{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:6px 40px;padding:16px 0;border-top:1px solid var(--rule)}
.cmd:first-of-type{border-top-color:var(--ink);margin-top:20px}.cmd p{margin:0;font-size:14px}
pre{margin:0;padding:10px 64px 10px 12px;background:var(--panel);border:1px solid var(--rule);position:relative;white-space:pre-wrap;overflow-wrap:anywhere;
font:12.5px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
pre .out{color:var(--ink2)}
pre button{position:absolute;top:6px;right:6px;font:12px system-ui,sans-serif;padding:2px 8px;background:var(--bg);color:var(--ink);
border:1px solid var(--rule);cursor:pointer}pre button:hover{border-color:var(--ink)}pre button:active{background:var(--panel)}
footer{margin-top:56px;padding-top:14px;border-top:1px solid var(--ink);color:var(--ink2);font-size:12.5px}
@media (max-width:720px){h1{font-size:29px}.lede{font-size:16px}.model,.rgrid,.cmd{grid-template-columns:minmax(0,1fr)}section{padding-top:44px}
.facts div{padding-right:12px}pre button{display:none}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.bar i{transition:none}}
"""

JS = """
const C=document.querySelector('.calc');if(C){const g=id=>document.getElementById(id),f=()=>{
 const v=+g('vol').value,c=+g('cap').value,n=+g('inf').value,c0=+C.dataset.cap;
 const bk=+C.dataset.buy*v*c/c0*2.5/n,bn=+C.dataset.burn*2.5/n,p=bk+bn;
 g('o-vol').textContent=v.toFixed(1)+'x today';g('o-cap').textContent=c+'%'+(c==c0?' (today)':'');
 g('o-inf').textContent=n.toFixed(1)+'% a year'+(n==2.5?' (today)':'');
 g('c-bk').style.width=Math.min(100,bk*100)+'%';g('c-bn').style.width=Math.min(100-Math.min(100,bk*100),bn*100)+'%';
 g('o-pay').textContent='Burn plus buybacks: '+(p*100).toFixed(1)+'% of issuance'+(p>=1?'. The flows equal issuance.':'. Break-even is '+(1/p).toFixed(1)+'x away.')};
 C.addEventListener('input',f);f()}
document.querySelectorAll('pre[data-copy]').forEach(p=>{const b=document.createElement('button');b.type='button';b.textContent='Copy';
 b.addEventListener('click',()=>navigator.clipboard.writeText(p.dataset.copy).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1200)}));p.appendChild(b)});
const ALL=JSON.parse(document.getElementById('data').textContent),NS='http://www.w3.org/2000/svg';
function el(n,a,p){const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);p&&p.appendChild(e);return e}
document.querySelectorAll('[data-chart]').forEach(card=>{
 const key=card.dataset.chart,mul=+card.dataset.mul,unit=card.dataset.unit,dp=+card.dataset.dp,D=ALL[card.dataset.src],col=`var(--${card.dataset.color})`;
 const P=D.filter(d=>d[key]!=null);if(P.length<2){card.remove();return}
 const lead=card.classList.contains('lead'),xs=P.map(d=>d.t),ys=P.map(d=>d[key]*mul),W=lead?1080:520,Ht=lead?280:190,L=42,R=lead?64:58,T=10,B=22;
 const x0=xs[0],x1=xs[xs.length-1],y1=Math.max(...ys)*1.08,sx=x=>L+(x-x0)/(x1-x0)*(W-L-R),sy=y=>Ht-B-y/y1*(Ht-T-B);
 const svg=el('svg',{viewBox:`0 0 ${W} ${Ht}`,role:'img','aria-label':card.querySelector('.sub').textContent});
 card.insertBefore(svg,card.querySelector('.src'));
 for(let i=0;i<=4;i++){const v=y1*i/4;el('line',{x1:L,x2:W-R,y1:sy(v),y2:sy(v),stroke:i?'var(--rule)':'var(--ink)'},svg);
  el('text',{x:L-6,y:sy(v)+4,'text-anchor':'end'},svg).textContent=v.toFixed(dp)}
 [0,.5,1].forEach(f=>{const i=Math.round(f*(P.length-1));
  el('text',{x:sx(xs[i]),y:Ht-6,'text-anchor':f==0?'start':f==1?'end':'middle'},svg).textContent=P[i].date});
 const line=xs.map((x,i)=>sx(x).toFixed(1)+','+sy(ys[i]).toFixed(1)).join('L');
 el('path',{d:'M'+line+`L${sx(x1)},${sy(0)}L${sx(x0)},${sy(0)}Z`,fill:col,opacity:.1},svg);
 el('path',{d:'M'+line,fill:'none',stroke:col,'stroke-width':lead?2:1.75,'stroke-linejoin':'round'},svg);
 const n=ys.length-1;el('circle',{cx:sx(xs[n]),cy:sy(ys[n]),r:3,fill:col},svg);
 const lab=el('text',{x:sx(xs[n])+7,y:sy(ys[n])+4,style:'fill:var(--ink);font-weight:600'},svg);lab.textContent=ys[n].toFixed(dp)+unit.trim().replace('NEAR','');
 if(lead){let m=0;ys.forEach((y,i)=>{if(y>ys[m])m=i});if(m<n-8){el('circle',{cx:sx(xs[m]),cy:sy(ys[m]),r:3,fill:'var(--bg)',stroke:col,'stroke-width':1.5},svg);
  el('text',{x:sx(xs[m]),y:sy(ys[m])-9,'text-anchor':'middle'},svg).textContent='peak'}}
 const ch=el('line',{y1:T,y2:Ht-B,stroke:'var(--ink2)',visibility:'hidden'},svg),dot=el('circle',{r:4,fill:col,stroke:'var(--bg)','stroke-width':2,visibility:'hidden'},svg);
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

P = lambda x, n=1: f"{100 * x:.{n}f}%"
CHARTS = [  # key, title, subtitle, multiplier, unit, decimals, source, one sentence on what it shows, colour role
    ("payback", "Payback", "Burn plus buybacks as % of issuance, 100-epoch rolling", 100, "%", 1,
     "(burn + buyback gain) / mint, from data/epochs.csv and data/buybacks.csv",
     lambda s: f"Burn plus buybacks equal {P(s['payback'])} of issuance, down from a peak of {P(s['payback_peak'])} on {s['payback_peak_date']}.", "back"),
    ("multiple", "Distance to break-even", "Multiple of today's burn plus buybacks that equals issuance", 1, "x", 1,
     "mint / (burn + buyback gain)",
     lambda s: f"Flows would have to grow {s['multiple']:.1f}x at constant issuance to equal it; on burn alone the figure is {s['burn_only_multiple']:.0f}x.", "ink"),
    ("buyback_per_day", "Buybacks", "NEAR added to the buyback account per day", 1, " NEAR", 0,
     "view_account balance of buybacks.multisignature.near at each epoch's last block, differenced",
     lambda s: f"The account gains {s['buyback_per_day']:,.0f} NEAR a day; it is held, not burnt, and its balance fell in {s['buyback_outflow_epochs']} of {s['buyback_epochs']} epochs.", "back"),
    ("burn_per_day", "Burn", "NEAR burnt in gas fees per day (exact)", 1, " NEAR", 0,
     "block header total_supply: supply(first block) - supply(last block) + burnt(first block), per epoch",
     lambda s: f"Gas fees burn {s['burn_per_day']:,.0f} NEAR a day against {s['mint_per_day']:,.0f} minted.", "burn"),
    ("coverage", "Burn-only coverage", "Fee burn as % of issuance (exact)", 100, "%", 2,
     "burn / mint, both from block header total_supply",
     lambda s: f"Burn alone equals {P(s['burn_coverage'], 2)} of issuance, which is what a fee-burn dashboard reports.", "burn"),
    ("mint_per_day", "Mint", "NEAR minted to validators per day (exact)", 1, " NEAR", 0,
     "block header total_supply: supply(first block) - supply(last block of previous epoch) + burnt(first block)",
     lambda s: f"Validators are minted {s['mint_per_day']:,.0f} NEAR a day, {P(s['realized_inflation'], 2)} of supply a year.", "ink"),
    ("utilization", "Block utilization", "Gas used as % of gas limit, sampled", 100, "%", 2,
     "chunk gas_used / gas_limit over 3 seeded random heights per epoch",
     lambda s: f"Blocks are {P(s['utilization'], 2)} full, so burn is limited by demand for block space, not by capacity.", "ink"),
]
WEEKLY = [
    ("volume_musd", "NEAR Intents volume", "USD millions a day, weekly average", 1, "M", 0,
     "DefiLlama summary/dexs/near-intents, in data/llama.csv",
     lambda s: f"Volume is ${s['intents_volume_musd_latest']:.0f}M a day, up from a weekly low of ${s['intents_volume_musd_low']:.0f}M and {s['intents_volume_usd_ratio_1y']:.2f}x its level a year ago.", "ink"),
    ("captured_kusd", "Revenue captured by NEAR", "USD thousands a day, all revenue wallets", 1, "k", 0,
     "DefiLlama summary/fees/near-intents dailyHoldersRevenue, in data/llama.csv",
     lambda s: f"Captured revenue has moved with volume (correlation {s['intents_volume_captured_correlation']:.2f} over {s['intents_weeks']} weeks).", "back"),
    ("take_bps", "Take rate", "Captured revenue per unit of volume, basis points", 1, " bps", 1,
     "captured revenue / volume, weekly, from data/llama.csv",
     lambda s: f"NEAR keeps a median {s['intents_take_bps_median']:.1f} basis points of volume, between {s['intents_take_bps_min']:.1f} and {s['intents_take_bps_max']:.1f}: the rate is not stable.", "ink"),
]


def track(lo, mid, hi, actual, ok):
    """One committed interval on a common scale, with the outcome once it exists."""
    top = max(hi, actual or 0) * 1.12
    x = lambda v: 2 + v / top * 396
    out = (f"<svg viewBox='0 0 400 20' role='img' aria-label='committed interval'>"
           f"<line x1='2' x2='398' y1='10' y2='10' stroke='var(--rule)'/>"
           f"<rect x='{x(lo):.1f}' y='4' width='{x(hi) - x(lo):.1f}' height='12' fill='var(--back)' opacity='.22'/>"
           f"<path d='M{x(lo):.1f},3V17M{x(hi):.1f},3V17' stroke='var(--back)' stroke-width='1.5'/>"
           f"<path d='M{x(mid):.1f},6V14' stroke='var(--back)'/>")
    if actual is not None:
        out += f"<circle cx='{x(actual):.1f}' cy='10' r='4.5' fill='var(--{'good' if ok else 'bad'})' stroke='var(--bg)' stroke-width='1.5'/>"
    return out + "</svg>"


def fan(rows):
    """Per-epoch burn: the committed 10% to 90% band, its median, and the outcomes so far."""
    n, W, H, L, B, T = len(rows), 440, 150, 34, 20, 8
    top = max(max(r["q90"] for r in rows), max((r["actual"] or 0) for r in rows)) * 1.1
    x = lambda i: L + (i + .5) / n * (W - L - 6)
    y = lambda v: H - B - v / top * (H - T - B)
    band = " ".join(f"{x(i):.1f},{y(r['q90']):.1f}" for i, r in enumerate(rows)) + " " + \
           " ".join(f"{x(i):.1f},{y(r['q10']):.1f}" for i, r in reversed(list(enumerate(rows))))
    out = f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='NEAR burnt per epoch against the committed band'>"
    for k in range(3):
        v = top * k / 2
        out += (f"<line x1='{L}' x2='{W - 6}' y1='{y(v):.1f}' y2='{y(v):.1f}' stroke='var(--{'rule' if k else 'ink'})'/>"
                f"<text x='{L - 5}' y='{y(v) + 4:.1f}' text-anchor='end'>{v:.0f}</text>")
    out += f"<polygon points='{band}' fill='var(--burn)' opacity='.18'/>"
    if n > 1:
        med = " ".join(f"{x(i):.1f},{y(r['q50']):.1f}" for i, r in enumerate(rows))
        out += f"<polyline points='{med}' fill='none' stroke='var(--burn)' stroke-dasharray='3 3'/>"
    else:
        out += f"<path d='M{x(0) - 30:.1f},{y(rows[0]['q10']):.1f}h60v{y(rows[0]['q90']) - y(rows[0]['q10']):.1f}h-60z' fill='var(--burn)' opacity='.18'/>"
    for i, r in enumerate(rows):
        if r["actual"] is not None:
            out += f"<circle cx='{x(i):.1f}' cy='{y(r['actual']):.1f}' r='3.5' fill='var(--{'good' if r['hit'] else 'bad'})' stroke='var(--bg)'/>"
    for i in sorted({0, n // 2, n - 1}):
        out += f"<text x='{x(i):.1f}' y='{H - 5}' text-anchor='middle'>epoch {rows[i]['k']}</text>"
    return out + "</svg>"


def render(results, sha, ledgers=None):
    s, e = results["summary"], html.escape
    pct = lambda x, n=2: f"{100 * x:.{n}f}%"
    num = lambda x: f"{x:,.0f}"
    nr = lambda x: "n/a" if x is None else f"{x:,.0f}"
    has = s["payback"] is not None
    days = f"{s['window_days']:.0f}"

    # ---- headline: the flows to scale ----
    if has:
        head = (f"NEAR's fee burn plus Intents buybacks equal {pct(s['payback'], 1)} of what it mints. "
                f"Break-even is {s['multiple']:.1f}x away.")
        lede = (f"{pct(s['buyback_coverage'], 1)} is NEAR sent by the NEAR Intents contract to the buyback account, "
                f"where it is held, not burnt. {pct(s['burn_coverage'])} is gas fees burnt. A fee-burn dashboard "
                f"sees only the second number and puts break-even {s['burn_only_multiple']:.0f}x away.")
        bk, bn = 100 * s["buyback_coverage"], 100 * s["burn_coverage"]
        strip = (f"<div class='strip'><h3>Every NEAR minted in the last {days} days, to scale</h3>"
                 f"<div class='bar' role='img' aria-label='Buybacks {bk:.1f}%, burn {bn:.2f}%, not matched {100 - bk - bn:.1f}% of issuance'>"
                 f"<i class='bk' style='width:{bk:.3f}%'></i><i class='bn' style='width:{bn:.3f}%'></i></div>"
                 f"<ul class='key'><li><span class='sw' style='background:var(--back)'></span><span><b>{num(s['buyback_per_day'])}</b> NEAR a day "
                 f"gained by the buyback account, {pct(s['buyback_coverage'], 1)}</span></li>"
                 f"<li><span class='sw' style='background:var(--burn)'></span><span><b>{num(s['burn_per_day'])}</b> NEAR a day burnt in gas fees, "
                 f"{pct(s['burn_coverage'])}</span></li>"
                 f"<li><span class='sw' style='background:var(--rest)'></span><span><b>{num(s['mint_per_day'] - s['burn_per_day'] - s['buyback_per_day'])}</b> "
                 f"NEAR a day minted and not matched, {pct(1 - s['payback'], 1)}</span></li></ul></div>"
                 f"<div class='strip'><h3>What a fee-burn dashboard counts</h3>"
                 f"<div class='bar thin' role='img' aria-label='Burn only, {bn:.2f}% of issuance'><i class='bn' style='width:{bn:.3f}%'></i></div></div>")
        rng = (f"<small>90% resampling range {pct(s['payback_p05'], 1)} to {pct(s['payback_p95'], 1)}</small>"
               if s.get("payback_p05") is not None else "")
        facts = [("Payback: burn plus buybacks over mint", pct(s["payback"], 1), rng),
                 ("Distance to break-even", f"{s['multiple']:.1f}x",
                  f"<small>{s['multiple_at_1_6_issuance']:.1f}x if issuance falls to 1.6% (HSP-029)</small>"),
                 ("On burn alone", f"{s['burn_only_multiple']:.0f}x", f"<small>{pct(s['burn_coverage'])} of issuance</small>"),
                 ("Realized inflation a year", pct(s["realized_inflation"]), "<small>measured from mint, whole cache</small>")]
    else:
        head = f"NEAR burns back {pct(s['burn_coverage'])} of what it mints."
        lede = "Buyback balances are not cached for this window yet."
        strip = (f"<div class='strip'><h3>Every NEAR minted in the last {days} days, to scale</h3><div class='bar'>"
                 f"<i class='bn' style='width:{100 * s['burn_coverage']:.3f}%'></i></div></div>")
        facts = [("Burn over mint", pct(s["burn_coverage"]), ""), ("NEAR burnt a day", num(s["burn_per_day"]), ""),
                 ("NEAR minted a day", num(s["mint_per_day"]), "")]
    facts_html = "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}{c}</dd></div>" for a, b, c in facts)

    # ---- charts ----
    def figs(src, rows, lead=None):
        out = ""
        for k, t, sub, m, u, dp, source, say, color in rows:
            try:
                sentence = say(s)
            except (TypeError, KeyError):  # a figure this sentence needs is not available yet
                sentence = t
            out += (f"<figure{' class=lead' if k == lead else ''} data-src='{src}' data-chart='{k}' data-mul='{m}' data-unit='{u}' "
                    f"data-dp='{dp}' data-color='{color}'><h3>{e(sentence)}</h3><p class='sub'>{e(t)}. {e(sub)}</p>"
                    f"<p class='src'>Source: <code>{e(source)}</code></p></figure>")
        return out

    attr = ""
    if s.get("inflow_transfers"):
        attr = (f"<p style='margin-top:14px'>Sender check: {s['inflow_transfers_from_intents']} of the {s['inflow_transfers']} transfers since height "
                f"{s['inflow_first_height']} into the buyback account came from <code>intents.near</code>, carrying "
                f"{pct(s['inflow_share_from_intents'], 1)} of the NEAR (NearBlocks, with transaction hashes in <code>data/inflows.csv</code>).</p>")
    check = (f"<tr><td>Gas fees burnt</td><td>{nr(s['burn_per_day'])}</td><td>{nr(s['llama_burn_near_per_day'])} "
             f"<small>(its revenue series; its fees series is {nr(s['llama_fees_near_per_day'])})</small></td></tr>"
             f"<tr><td>Buyback account gain</td><td>{nr(s['buyback_per_day'])}</td><td rowspan='2'>{nr(s['llama_buyback_near_per_day'])} "
             f"<small>(captured revenue, all wallets)</small></td></tr>"
             f"<tr><td>All three revenue wallets, gain</td><td>{nr(s['all_revenue_wallets_per_day'])}</td></tr>")
    intents = ""
    if results.get("weekly"):
        intents = (f"<section id='app'><h2>The application behind the flow</h2><p>NEAR Intents by week since buybacks began "
                   f"(DefiLlama, USD). This is third-party context; none of it feeds mint, burn, the buyback gain or payback.</p>"
                   f"<div class='figs'>{figs('weekly', WEEKLY)}</div></section>")

    # ---- models ----
    models = ""
    if has:
        models += (f"<div class='model'><div><h3>Flow identity</h3><p>Mint and burn per epoch from <code>total_supply</code> in block "
                   f"headers, exact to the yoctoNEAR. The buyback gain is a balance change. No parameters.</p>"
                   f"<p class='how'><code>fetch.py: fetch_epoch</code>, checked by <code>run.py: load</code> and <code>verify.py</code></p></div>"
                   f"<div class='wrap'><table><tr><th>Quantity</th><th>Definition</th></tr>"
                   f"<tr><td>mint</td><td><code>supply(first) - supply(prev last) + burnt(first)</code></td></tr>"
                   f"<tr><td>burn</td><td><code>burnt(first) + supply(first) - supply(last)</code></td></tr>"
                   f"<tr><td>payback</td><td><code>(burn + buyback gain) / mint</code></td></tr>"
                   f"<tr><td>multiple</td><td><code>mint / (burn + buyback gain)</code></td></tr></table></div></div>")
    if results["backtest"]:
        bt = results["backtest"]
        worst = max(v["pinball"] for v in bt.values())
        about = {"persistence": "recent level only", "clock": "level plus a time-of-week profile", "price": "level plus NEAR's price"}
        rows = "".join(
            f"<tr><td>{e(m)}<br><small>{about.get(m, '')}</small></td><td><span class='inl' style='width:{70 * v['pinball'] / worst:.0f}px'></span>{v['pinball']:.4f}</td>"
            f"<td>{100 * v['skill_vs_persistence']:+.1f}%</td><td>{100 * v['interval_hit']:.0f}%</td></tr>" for m, v in bt.items())
        n = next(iter(bt.values()))["n"]
        models += (f"<div class='model'><div><h3>Burn forecasters</h3><p>Three models forecast NEAR burnt per epoch as 10%, 50% and 90% "
                   f"quantiles. Walk-forward backtest, {n} forecasts, up to 30 epochs ahead; each forecast uses only data before its date. "
                   f"Lower pinball loss is better. The bands are too narrow: they hold about two-thirds of outcomes against a nominal 80%.</p>"
                   f"<p class='how'><code>run.py: f_persistence, f_clock, f_price, backtest</code></p></div>"
                   f"<div class='wrap'><table><tr><th>Model</th><th>Pinball loss</th><th>Against persistence</th><th>10-90% band held</th></tr>{rows}</table></div></div>")
    cb = results.get("claims_backtest", {})
    if cb:
        cell = lambda v: f"{v['hit']} of {v['n']} <small>({100 * v['hit'] / v['n']:.0f}%)</small>" if v and v["n"] else "n/a"
        rows = "".join(f"<tr><td>{h} epochs</td><td>{cell(v.get('payback'))}</td><td>{cell(v.get('burn_total'))}</td>"
                       f"<td>{cell(v.get('buyback_total'))}</td></tr>" for h, v in sorted(cb.items(), key=lambda kv: int(kv[0])))
        models += (f"<div class='model'><div><h3>Window bands</h3><p>For a window of the next N epochs: the last N-epoch value, scaled by the "
                   f"5% to 95% range of how much consecutive windows have differed. The table is how often that procedure, run at earlier "
                   f"dates on data available then, contained the outcome. Nominal coverage is 90%.</p>"
                   f"<p class='how'><code>run.py: window_claims, predict</code></p></div>"
                   f"<div class='wrap'><table><tr><th>Window</th><th>Payback</th><th>NEAR burnt</th><th>Buyback gain</th></tr>{rows}</table></div></div>")
    if has and s.get("capture_share"):
        cap = max(1, round(100 * s["capture_share"]))
        yr = lambda x: "over 100" if x is None else f"{x:.1f}"
        by = results.get("breakeven_years") or {}
        rows_ = "".join(f"<tr><td>{g} a year</td><td>{yr(v['constant_issuance'])}</td><td>{yr(v['hsp029'])}</td></tr>"
                        for g, v in sorted(by.items(), key=lambda kv: int(kv[0][:-1])))
        models += f"""<div class='model'><div><h3>Break-even levers</h3><p>Payback scales with Intents volume and with the share of
gross Intents fees that reaches the buyback account, and inversely with the issuance rate. Two of the three are governance decisions.
HSP-029, passed by NEAR's House of Stake on 2026-11-02 and awaiting ratification, would lower maximum issuance to 1.6% a year.</p>
<p class='how'><code>run.py: main</code> (<code>breakeven_years</code>, <code>growth_needed_*</code>, <code>payback_if_all_intents_fees_captured</code>)</p>
<div class='wrap' style='margin-top:14px'><table><tr><th>Growth in burn plus buybacks</th><th>Years, issuance 2.5%</th><th>Years, ramp to 1.6%</th></tr>{rows_}</table></div></div>
<div class="calc" data-burn="{s['burn_coverage']}" data-buy="{s['buyback_coverage']}" data-cap="{cap}">
<label>NEAR Intents volume <output id="o-vol">1.0x today</output>
<input type="range" id="vol" min="1" max="20" step="0.5" value="1"></label>
<label>Share of gross Intents fees reaching the buyback account <output id="o-cap">{cap}% (today)</output>
<input type="range" id="cap" min="{cap}" max="100" step="1" value="{cap}"></label>
<label>Issuance rate <output id="o-inf">2.5% a year (today)</output>
<input type="range" id="inf" min="0.5" max="2.5" step="0.1" value="2.5"></label>
<div class="bar"><i class="bk" id="c-bk"></i><i class="bn" id="c-bn"></i></div>
<p id="o-pay" aria-live="polite"></p></div></div>"""

    # ---- forecast rounds ----
    led = ""
    cls = {"PASS": "pass", "HIT": "pass", "FALSIFIED": "fail", "MISS": "fail", "PENDING": "pending"}
    names = {"payback": "Payback over the window", "burn_total": "NEAR burnt over the window",
             "buyback_total": "NEAR gained by the buyback account"}
    fmt = lambda n, x: "pending" if x is None else f"{100 * x:.1f}%" if n == "payback" else f"{x:,.0f}"
    end = datetime.datetime.strptime(s["last_end_utc"], "%Y-%m-%d %H:%M") if s.get("last_end_utc") else None
    for L in ledgers or []:
        if L["ends"]:
            when = f"closed {L['ends']}"
        elif end and L["after_end_height"] == s["last_height"]:
            when = "closes about " + (end + datetime.timedelta(hours=s["window_days"] * 24 / 100 * L["total"])).strftime("%Y-%m-%d %H:00 UTC")
        else:
            when = "open"
        claims = "".join(
            f"<div class='claim'><b>{names[n]}{' (sets the verdict)' if n == 'payback' else ''}</b>"
            f"<span class='v {cls.get(c['verdict'], '')}'>{c['verdict']}</span>"
            f"<span>committed {fmt(n, c['lo'])} to {fmt(n, c['hi'])}</span><span class='v'>{fmt(n, c['actual'])}</span>"
            f"{track(c['lo'], c['mid'], c['hi'], c['actual'], c['verdict'] == 'HIT')}</div>" for n, c in sorted(L["claims"].items(), key=lambda kv: kv[0] != "payback"))
        inside = f"{L['hits']} of {L['resolved']} inside" if L["resolved"] else "no epoch has closed yet"
        led += (f"<div class='round'><header><h3>Next {L['total']} epochs after height {L['after_end_height']}</h3>"
                f"<span class='pill {cls.get(L['verdict'], 'pending')}'>{e(L['verdict'])}</span>"
                f"<span class='mono'>{L['resolved']} of {L['total']} epochs closed, {when}</span></header>"
                f"<div class='rgrid'><div>{claims}</div><div><p class='sub' style='margin-top:9px'>NEAR burnt in each epoch against the committed "
                f"10% to 90% band ({e(L['table_model'])} model): {inside}</p>{fan(L['rows'])}</div></div>"
                f"<p class='src'><code>predictions/{e(L['file'])}</code> sha256 <code>{e(L['commit'])}</code>, "
                f"OpenTimestamps proof in <code>predictions/{e(L['file'])}.ots</code></p></div>")
    if led:
        tot = [sum(v["payback"][k] for v in cb.values() if "payback" in v) for k in ("hit", "n")]
        held = f"{100 * tot[0] / tot[1]:.0f}%" if tot[1] else "an unknown share"
        led = (f"<section id='rounds'><h2>Forecast rounds: the chain scores them</h2><p>Each round was frozen before the epochs it "
               f"describes existed, and its hash is anchored in Bitcoin. <code>run.py</code> refuses a round that is not exactly what "
               f"the code derives from the data up to its height, so neither the numbers nor the method can be edited afterwards. "
               f"Historically the payback band has held {held} of the time, so an occasional miss is expected even when the model "
               f"is right, and a pass near the bounds is weak support.</p>{led}</section>")

    # ---- for and against ----
    case = ""
    if has:
        f_ = [f"<b>The flow is on chain and exact.</b> {num(s['buyback_per_day'])} NEAR a day reach the buyback account, against {num(s['burn_per_day'])} burnt.",
              (f"<b>It comes from one contract.</b> {s['inflow_transfers_from_intents']} of {s['inflow_transfers']} recent transfers were sent by <code>intents.near</code>."
               if s.get("inflow_transfers") else ""),
              f"<b>A separate pipeline agrees.</b> DefiLlama gives {nr(s['llama_buyback_near_per_day'])} NEAR a day for all revenue wallets; balances read from chain give {nr(s['all_revenue_wallets_per_day'])}.",
              f"<b>Capture is a lever.</b> The buyback account receives about {pct(s['capture_share'], 0)} of gross Intents fees. All of it, at today's volume, would be {pct(s['payback_if_all_intents_fees_captured'], 0)} of issuance.",
              f"<b>Issuance is a lever in motion.</b> At 1.6% a year the multiple is {s['multiple_at_1_6_issuance']:.1f}x at today's flows."]
        a_ = ["<b>Buybacks are not burns.</b> The NEAR sits in a multisig account. Supply does not fall and the holders can spend it.",
              f"<b>Payback has been falling.</b> From a peak of {pct(s['payback_peak'], 1)} on {s['payback_peak_date']} to {pct(s['payback'], 1)}.",
              f"<b>NEAR Intents is not growing.</b> Over a year, daily volume is {s['intents_volume_usd_ratio_1y']:.2f}x and gross fees {s['intents_fees_usd_ratio_1y']:.2f}x (DefiLlama).",
              f"<b>The flow is concentrated.</b> One application supplies {pct(s['buyback_coverage'] / s['payback'], 0)} of the payback.",
              f"<b>The balance has fallen before.</b> {num(s['buyback_outflow_near'])} NEAR left the account in {s['buyback_outflow_epochs']} of {s['buyback_epochs']} epochs."]
        li = lambda xs: "".join(f"<li>{x}</li>" for x in xs if x)
        case = (f"<section id='case'><h2>The case, both ways</h2><p>The full argument, with what would change our mind, is in "
                f"<a href='{REPO}/blob/main/THESIS.md'>THESIS.md</a>.</p><div class='two'><div><h3>For</h3><ul>{li(f_)}</ul></div>"
                f"<div><h3>Against</h3><ul>{li(a_)}</ul></div></div></section>")

    def cmd(text, what, out=""):
        return (f"<div class='cmd'><p>{what}</p><pre data-copy='{e(text)}'>{e(text)}"
                + (f"\n<span class='out'>{e(out)}</span>" if out else "") + "</pre></div>")
    repro = (cmd(f"git clone {REPO} && cd Coverage", "Get the repository. Python 3.9 or later, no packages, no keys.")
             + cmd("python3 run.py", "Rebuild every number on this page from the cached chain data. Offline, under two seconds.", f"RESULT sha256={sha}")
             + cmd("python3 test_run.py", "Self-test: scoring maths, data hashes, and refusal of a cache or a round with one value changed.", "SELFTEST PASS")
             + cmd("python3 verify.py 3 12345", "Pick any seed. Random epochs are refetched from mainnet and must match the cache exactly.",
                   "VERIFY seed=12345 PASS (3/3 epochs match the chain, 6 blocks checked against their parents)")
             + cmd("python3 fetch.py --epochs 45 && python3 run.py", "Fetch the epochs that closed since and score the forecast rounds.",
                   "LEDGER round-<height>-h05.json: 5/5 epochs closed -> PASS or FALSIFIED"))

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Coverage: what NEAR pays back</title>
<meta name="description" content="{e(head)}">
<style>{CSS}</style></head><body>
<nav><div><b>Coverage</b><a href="#chain">Onchain dashboard</a>{'<a href="#app">NEAR Intents</a>' if intents else ''}<a href="#models">Models</a>{'<a href="#rounds">Forecast rounds</a>' if led else ''}{'<a href="#case">For and against</a>' if case else ''}<a href="#reproduce">Reproduce</a><a href="{REPO}">GitHub</a></div></nav>
<main>
<p class="stamp mono">NEAR mainnet, {e(s['first'])} to {e(s['last'])}: {s['epochs']} epochs, heights {s['first_height']} to {s['last_height']}. Headline window: last 100 epochs, {days} days.</p>
<h1>{e(head)}</h1>
<p class="lede">{e(lede)}</p>
{strip}
<dl class="facts">{facts_html}</dl>
<section id="chain"><h2>Onchain dashboard</h2>
<p>Mint and burn are read from <code>total_supply</code> in block headers and are exact to the yoctoNEAR. The buyback gain is the
change in the account's balance between epoch ends. Every point is a 100-epoch rolling window; hover a chart for values.</p>
<div class="figs">{figs('series', CHARTS, 'payback')}</div>
<h3 style="margin-top:28px">Chain versus the indexer</h3>
<p class="sub">The same flows over the same days, in NEAR a day. DefiLlama reports USD; each day is converted at that day's price.</p>
<div class="wrap"><table><tr><th>Flow, NEAR a day</th><th>This repo, from chain</th><th>DefiLlama</th></tr>{check}</table></div>
{attr}</section>
{intents}
<section id="models"><h2>Models</h2>
<p>Four models, each a few functions in <code>run.py</code>, each rebuilt by <code>python3 run.py</code> from the cached data with
no network. Their outputs are in <code>out/results.json</code>.</p>{models}</section>
{led}
{case}
<section id="reproduce"><h2>Reproduce it</h2>
<p>The result hash below covers every number on this page. If your run prints a different hash, the page and the data disagree.</p>
{repro}</section>
<footer>Result hash <code>{sha}</code>. MIT licence. <a href="{REPO}">{REPO.split('//')[1]}</a></footer>
</main><script type="application/json" id="data">{json.dumps(dict(series=results['series'], weekly=results.get('weekly', [])), separators=(',', ':'))}</script>
<script>{JS}</script></body></html>"""
