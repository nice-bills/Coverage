"""Render dist/quick.html: Coverage in 60 seconds.

The same results, design and motion as dist/index.html, cut down for readers who skim: a few steps, one idea
each, one big number each, plain words, nothing hidden behind hover or a click. Every number comes from
out/results.json, so this page cannot drift from the full report. Stdlib only.
"""
import html

import dashboard as D

e = html.escape

QUICK_CSS = """
body{font-size:18px;line-height:1.6}
.q-wrap{max-width:980px;margin:0 auto;padding:0 var(--gut)}
.q-mast{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:20px 0 16px;border-bottom:1px solid var(--rule)}
.q-mast .brand span{font-size:14px}
.q-mast .acts{display:flex;align-items:center;gap:10px}
.q-btn{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:12px 20px;font:500 16px/1 var(--sans);text-decoration:none;border:1px solid var(--ink);color:var(--ink)}
.q-btn.solid{background:var(--ink);color:var(--paper)}
.q-btn.small{padding:8px 14px;font-size:14px}
.q-btn:hover{box-shadow:0 0 0 4px var(--ring)}
.q-prog{position:sticky;top:0;z-index:5;background:var(--paper);border-bottom:1px solid var(--rule);padding:10px 0}
.q-prog .row{display:flex;justify-content:space-between;align-items:center;gap:12px;font:500 15px var(--sans)}
.q-prog .row b{font-weight:600}
.q-prog .bar{height:6px;border-radius:3px;background:var(--rule-2);margin-top:8px;overflow:hidden}
.q-prog .bar i{display:block;height:100%;width:0;background:var(--teal);border-radius:3px;transition:width .3s var(--ease)}
.q-hero{padding:56px 0 24px}
.q-hero h1{font:400 clamp(44px,7vw,84px)/1.02 var(--serif);letter-spacing:-.02em;margin:14px 0 22px;max-width:16ch}
.q-hero h1 em{color:var(--teal);font-style:italic}
.q-hero .lead{font-size:21px;line-height:1.5;color:var(--ink-2);max-width:34ch;margin:0}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px;padding:0;list-style:none}
.chips li{border:1px solid var(--rule);border-radius:999px;padding:8px 16px;font-size:16px;color:var(--ink);background:var(--card)}
.q-step{background:var(--card);border:1px solid var(--rule-2);border-radius:24px;padding:clamp(24px,4vw,48px);margin:28px 0;scroll-margin-top:80px}
.q-step .tag{display:flex;align-items:center;gap:12px;font:500 15px var(--sans);color:var(--muted);letter-spacing:.08em;text-transform:uppercase}
.q-step .tag .n{display:inline-grid;place-items:center;width:40px;height:40px;border-radius:50%;background:var(--ink);color:var(--paper);font:400 22px/1 var(--serif);letter-spacing:0}
.q-step h2{font:400 clamp(34px,4.6vw,52px)/1.08 var(--serif);letter-spacing:-.015em;margin:18px 0 8px}
.q-step .big{font:400 clamp(72px,12vw,140px)/.95 var(--serif);letter-spacing:-.03em;margin:22px 0 6px;font-variant-numeric:tabular-nums}
.q-step .big small{font:500 clamp(18px,2.2vw,24px) var(--sans);letter-spacing:0;color:var(--ink-2);margin-left:10px}
.q-step .say{font-size:21px;line-height:1.5;margin:6px 0 0;max-width:36ch;color:var(--ink)}
.q-step .say b{font-weight:600}
.q-step .plain{margin:20px 0 0;padding:14px 18px;border-left:4px solid var(--teal);background:var(--teal-soft);border-radius:0 12px 12px 0;font-size:17px;color:var(--ink);max-width:56ch}
.q-step .plain.terra{border-left-color:var(--terra);background:var(--terra-soft)}
.q-bars{margin-top:28px;display:grid;gap:16px}
.q-bar .lab{display:flex;justify-content:space-between;gap:12px;font-size:16px;margin-bottom:6px;flex-wrap:wrap}
.q-bar .lab b{font-weight:600}
.q-bar .track{height:30px;border-radius:8px;background:var(--gray-fill);overflow:hidden;display:flex}
.q-bar .track>div{height:100%}
.q-vs{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:28px}
.q-vs>div{border:1px solid var(--rule);border-radius:16px;padding:18px 20px}
.q-vs .k{font-size:15px;color:var(--ink-2)}
.q-vs .v{font:400 56px/1 var(--serif);margin-top:8px;font-variant-numeric:tabular-nums}
.q-vs .old .v{color:var(--terra);text-decoration:line-through;text-decoration-thickness:3px}
.q-vs .new{border-color:var(--teal);box-shadow:0 0 0 3px var(--teal-soft)}.q-vs .new .v{color:var(--teal)}
.q-cases{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px}
.q-cases>div{border-radius:16px;padding:16px 18px;border:1px solid var(--rule)}
.q-cases .k{font:600 15px var(--sans)}.q-cases .g{font-size:14.5px;color:var(--ink-2)}
.q-cases .y{font:400 44px/1.05 var(--serif);margin-top:6px}
.q-cases .bull .y{color:var(--teal)}.q-cases .bear .y{color:var(--terra);font-style:italic}
.q-list{list-style:none;margin:24px 0 0;padding:0;display:grid;gap:14px}
.q-list li{display:grid;grid-template-columns:44px 1fr;gap:14px;align-items:start;border-top:1px solid var(--rule);padding-top:14px}
.q-list .ic{font:400 30px/1 var(--serif);color:var(--terra)}
.q-list b{display:block;font-size:20px;font-weight:600}
.q-list span{color:var(--ink-2);font-size:17px}
.q-verdict{list-style:none;margin:22px 0 0;padding:0;display:grid;gap:14px}
.q-verdict li{border:1px solid var(--rule);border-radius:16px;padding:16px 18px;display:grid;gap:6px;background:var(--paper)}
.q-verdict .k{font:600 14px var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--teal)}
.q-verdict li:nth-child(4) .k{color:var(--terra)}
.q-verdict .v{font-size:18px;line-height:1.5}
.q-live{margin-top:20px;border:2px solid var(--teal);border-radius:16px;padding:16px 18px;display:grid;gap:8px}
.q-live .k{font:600 14px var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--teal)}
.q-live .v{font-size:18px}.q-live .q-btn{justify-self:start;margin-top:6px}
.q-cmd{margin-top:22px;background:var(--term);color:var(--term-ink);border-radius:14px;padding:18px 20px;font:400 18px var(--mono);overflow-x:auto}
.q-cmd .ok{color:var(--term-ok)}
.q-end{text-align:center;padding:40px 0 72px}
.q-end h2{font:400 clamp(40px,6vw,64px)/1.05 var(--serif);margin:0 0 10px}
.q-end p{font-size:19px;color:var(--ink-2);margin:0 auto 26px;max-width:40ch}
.q-end .acts{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.q-foot{border-top:1px solid var(--rule);padding:18px 0 28px;font-size:14px;color:var(--muted);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.q-step .chart svg{width:100%;height:auto;display:block}
.q-step .fan-n{display:none}
@media (max-width:720px){.q-vs,.q-cases{grid-template-columns:1fr}.q-step .fan-w{display:none}.q-step .fan-n{display:block}
 .q-mast .brand span{display:none}.q-hero{padding-top:36px}}
@media screen and (prefers-reduced-motion:no-preference){
html.anim .q-grow{transform-origin:0 50%;transition:transform 1.2s var(--ease) calc(var(--d,0s) + .25s)}
html.anim .rv:not(.in) .q-grow{transform:scaleX(0)}
html.anim .q-grow.g2{transition-delay:calc(var(--d,0s) + .75s)}
html.anim .q-vs .old .v{transition:text-decoration-color .6s ease-out 1.4s}
html.anim .rv:not(.in) .q-vs .old .v{text-decoration-color:transparent}}
@media print{.q-prog{display:none}}
"""

QUICK_JS = r"""
const root=document.documentElement,$=q=>document.querySelector(q);
(function(){const b=$('#theme');let saved=null;try{saved=localStorage.getItem('cov-theme')}catch(e){}
 if(saved==='dark'||saved==='light')root.dataset.theme=saved;
 const mq=matchMedia('(prefers-color-scheme: dark)'),cur=()=>root.dataset.theme||(mq.matches?'dark':'light'),
 lab=()=>{b.querySelector('span').textContent=cur()==='dark'?'Paper':'Ink';b.setAttribute('aria-pressed',cur()==='dark')};lab();
 b.onclick=()=>{root.dataset.theme=cur()==='dark'?'light':'dark';try{localStorage.setItem('cov-theme',root.dataset.theme)}catch(e){}lab()};
 mq.addEventListener&&mq.addEventListener('change',lab)})();
// progress: which step is on screen, and how far down the page the reader is
(function(){const st=[...document.querySelectorAll('.q-step')],n=$('#q-n'),t=$('#q-t'),bar=$('#q-bar');
 function on(){let k=0;st.forEach((s,i)=>{if(s.getBoundingClientRect().top<innerHeight*.5)k=i});
  n.textContent='Step '+(k+1)+' of '+st.length;t.textContent=st[k].dataset.t;
  const h=document.documentElement.scrollHeight-innerHeight;bar.style.width=(h>0?Math.min(1,scrollY/h)*100:100)+'%'}
 addEventListener('scroll',on,{passive:true});addEventListener('resize',on);on()})();
// motion, as on the full report: only when the reader allows it, and nothing can stay hidden
(function(){if(navigator.webdriver||matchMedia('(prefers-reduced-motion: reduce)').matches||!('IntersectionObserver' in window)||!window.requestAnimationFrame)return;
 const ease=k=>1-Math.pow(1-k,3);
 function count(elm,delay){const tw=document.createTreeWalker(elm,NodeFilter.SHOW_TEXT);let n;while((n=tw.nextNode())&&!/\d/.test(n.nodeValue));if(!n)return;
  const txt=n.nodeValue,m=txt.match(/\d[\d,]*(\.\d+)?/),v=parseFloat(m[0].replace(/,/g,'')),dp=m[1]?m[1].length-1:0,gp=m[0].indexOf(',')>=0,
  pre=txt.slice(0,m.index),post=txt.slice(m.index+m[0].length),t0=performance.now()+delay;
  const f=now=>{const k=Math.max(0,Math.min(1,(now-t0)/1400));n.nodeValue=pre+(v*ease(k)).toLocaleString('en-US',{minimumFractionDigits:dp,maximumFractionDigits:dp,useGrouping:gp})+post;
   if(k<1)requestAnimationFrame(f);else n.nodeValue=txt};f(performance.now());setTimeout(()=>{n.nodeValue=txt},delay+2500)}
 const rv=[...document.querySelectorAll('.q-hero,.q-step,.q-end')];rv.forEach(e=>e.classList.add('rv'));
 let seen=false;
 function show(t,now){if(t.classList.contains('in'))return;t.classList.add('in');io.unobserve(t);
  if(!now)t.querySelectorAll('.big,.q-vs .new .v,.q-cases .y').forEach((c,i)=>count(c,200+i*120))}
 const io=new IntersectionObserver(es=>{seen=true;es.forEach(en=>{if(en.isIntersecting)show(en.target);else if(en.boundingClientRect.bottom<0)show(en.target,true)})},{rootMargin:'0px 0px -8% 0px'});
 root.classList.add('anim');rv.forEach(e=>io.observe(e));
 setTimeout(()=>{if(!seen){root.classList.remove('anim');return}rv.forEach(t=>{if(t.getBoundingClientRect().top<innerHeight)show(t)})},2500);
 addEventListener('beforeprint',()=>rv.forEach(t=>show(t,true)))})();
"""


def render(results, sha, ledgers=None):
    s, sc = results["summary"], results.get("scenarios")
    if s.get("payback") is None:
        return None
    pct = lambda x, n=1: f"{100 * x:.{n}f}%"
    num = lambda x: f"{x:,.0f}"
    m, u, b = s["mint_per_day"], s["burn_per_day"], s["buyback_per_day"]
    w = lambda x: f"{max(100 * x, .6):.2f}%"

    steps = []

    def step(key, title, body):
        steps.append((key, title, body))

    step("mint", "NEAR makes new coins", f"""
<h2>Every day, NEAR makes new coins.</h2>
<div class="big num">{num(m)}<small>new NEAR a day</small></div>
<p class="say">That adds about <b>{100 * s['realized_inflation']:.1f}%</b> to the supply each year.</p>
<p class="plain">Why it matters: more coins means each coin you hold is a slightly smaller slice. This is called <b>issuance</b>.</p>
<div class="q-bars"><div class="q-bar"><div class="lab"><b>New NEAR each day</b><span>{num(m)}</span></div>
<div class="track"><div class="q-grow" style="width:100%;background:var(--ink)"></div></div></div></div>""")

    step("burn", "The usual view", f"""
<h2>Most dashboards only count the fee burn.</h2>
<div class="big num terra">{pct(s['burn_coverage'], 2)}</div>
<p class="say">That's how much of the new NEAR gets <b>burnt</b> (destroyed) in fees.</p>
<div class="q-bars"><div class="q-bar"><div class="lab"><b>Burnt in fees</b><span>{num(u)} of {num(m)} a day</span></div>
<div class="track"><div class="q-grow" style="width:{w(u / m)};background:var(--terra)"></div></div></div></div>
<p class="plain terra">Seen this way, NEAR needs <b>{s['burn_only_multiple']:.0f}×</b> more activity before it destroys as much as it makes.</p>""")

    step("buyback", "What gets missed", f"""
<h2>But there's a second flow: buybacks.</h2>
<p class="say">The <b>NEAR Intents</b> app sends NEAR into a buyback account every day. Count that too:</p>
<div class="big num teal">{pct(s['payback'])}</div>
<p class="say">of the new NEAR is won back. That's <b>{s['payback'] / s['burn_coverage']:.0f} times</b> what the fee burn alone shows.</p>
<div class="q-bars"><div class="q-bar"><div class="lab"><b>Won back each day</b><span><span class="teal">{num(b)} buybacks</span> + <span class="terra">{num(u)} burn</span></span></div>
<div class="track"><div class="q-grow" style="width:{w(b / m)};background:var(--teal)"></div><div class="q-grow g2" style="width:{w(u / m)};background:var(--terra)"></div></div></div></div>
<div class="q-vs"><div class="old"><div class="k">Distance to break-even, fee burn only</div><div class="v num">{s['burn_only_multiple']:.0f}×</div></div>
<div class="new"><div class="k">Distance to break-even, burn + buybacks</div><div class="v num">{s['multiple']:.1f}×</div></div></div>""")

    if sc:
        c = sc["cases"]
        yr = lambda k: str(c[k]["year"]) if c[k]["year"] else "Never"
        g = lambda k: f"{'+' if c[k]['growth'] >= 0 else '−'}{abs(100 * c[k]['growth']):.0f}% a year"
        full = sc["levers"]["capture"][-1]
        step("path", "Where it goes next", f"""
<h2>When could NEAR win back everything it makes?</h2>
<p class="say">It depends on how fast NEAR Intents grows. Three speeds, all taken from real data:</p>
<div class="q-cases"><div class="bull"><div class="k">Fast</div><div class="g">{g('bull')}</div><div class="y num">{yr('bull')}</div></div>
<div class="base"><div class="k">Middle</div><div class="g">{g('base')}</div><div class="y num">{yr('base')}</div></div>
<div class="bear"><div class="k">Shrinking</div><div class="g">{g('bear')}</div><div class="y">{yr('bear')}</div></div></div>
<div class="chart fan-w" style="margin-top:26px">{D.path_svg(sc, True)}</div><div class="chart fan-n" style="margin-top:22px">{D.path_svg(sc, False)}</div>
<p class="plain">The fastest fix isn't growth. If the buyback took <b>every</b> Intents fee and NEAR cut issuance (a proposal called <b>HSP-029</b>), even the middle speed {'gets there in about <b>' + format(full['years_base_hsp029'], '.0f') + ' years</b>' if full.get('years_base_hsp029') is not None else 'still takes over a century'}.</p>""")

    quiet = ""
    try:
        import bq
        bs = bq.summary(bq.load())
        x, a_ = bs.get("intents_share"), bs.get("daily_active_accounts")
        if x and a_ and x["per_day_first"]:
            quiet = (f"<li><span class='ic'>iv</span><div><b>The chain got quieter.</b><span>Daily active accounts are {e(a_['change'])} since February. Most of the drop in app activity "
                     f"is one app (KaiChing) leaving. Intents went the other way: {x['per_day_last'] / x['per_day_first']:.1f}× more activity.</span></div></li>")
    except Exception:
        pass
    step("catch", "The honest catch", f"""
<h2>The catch. We show this too.</h2>
<ul class="q-list">
<li><span class="ic">i</span><div><b>Bought back isn't burnt.</b><span>The NEAR sits in an account. Its owners could spend it.</span></div></li>
<li><span class="ic">ii</span><div><b>It has dipped.</b><span>From a peak of {pct(s['payback_peak'])} down to {pct(s['payback'])} now.</span></div></li>
<li><span class="ic">iii</span><div><b>One app does most of it.</b><span>NEAR Intents supplies {pct(s['buyback_coverage'] / s['payback'], 0)} of what's won back.</span></div></li>
{quiet}
</ul>""")

    import verdict
    vi = verdict.html(results, e)
    if vi:
        step("verdict", "So, buy or not?", f"""
<h2>So what should an investor do?</h2>
<p class="say">Our honest call, in four lines:</p>
<ul class="q-verdict">{vi}</ul>""")

    cb = results.get("claims_backtest") or {}
    tot = [sum(v["payback"][k] for v in cb.values() if "payback" in v) for k in ("hit", "n")]
    held = tot[0] / tot[1] if tot[1] else None
    if held is not None:
        step("ranges", "Ranges, not guesses", f"""
<h2>We give ranges, not guesses.</h2>
<p class="say">One exact number is almost always wrong. So for every forecast we give a <b>range</b>, like "between 7% and 27%".</p>
<div class="big num teal">{pct(held, 0)}</div>
<p class="say">of the time, the real number landed <b>inside</b> our range when we tested it on past data.</p>
<p class="plain">That's the honest bar: tight enough to be useful, wide enough to be right most of the time. Expect the odd miss. A range that is never wrong is too wide to mean anything.</p>""")

    live = ""
    pend = [L for L in (ledgers or []) if L["verdict"] == "PENDING" and L.get("so_far") is not None and L["claims"].get("payback")]
    if pend and s.get("last_end_utc"):
        import datetime
        end = datetime.datetime.strptime(s["last_end_utc"], "%Y-%m-%d %H:%M")
        hrs = s["window_days"] * 24 / 100
        at = lambda L: ((datetime.datetime.fromtimestamp(L["frozen_t"], datetime.timezone.utc).replace(tzinfo=None) if L.get("frozen_t") else end)
                        + datetime.timedelta(hours=hrs * L["total"]))
        pend = sorted(pend, key=at)
        cl = [at(L) for L in pend]
        ins = sum(L["claims"]["payback"]["lo"] <= L["so_far"] <= L["claims"]["payback"]["hi"] for L in pend)
        d = lambda t: f"{t.day} {t:%b}"
        live = (f"<div class='q-live'><div class='k'>Live right now</div><div class='v'><b>{ins} of {len(pend)}</b> live forecasts are inside their range so far "
                f"(the first to close: payback {pct(pend[0]['so_far'])} after {pend[0]['resolved']} of {pend[0]['total']} epochs).</div>"
                f"<div class='v'>The first closes about <b>{d(cl[0])} {cl[0]:%H}:00 UTC</b>; " + (f"all close by <b>{d(cl[-1])}</b>." if len(cl) > 1 else "")
                + f"</div><a class='q-btn small' href='index.html#c5'>See the live scoreboard</a></div>")

    step("check", "Check it yourself", f"""
<h2>Don't trust us. Check it.</h2>
<p class="say">One command rebuilds every number on this page from the chain data, in under 2 seconds:</p>
<div class="q-cmd">$ python3 run.py<br><span class="ok">RESULT sha256={sha[:16]}…</span></div>
<p class="plain">Our newest ranges were locked <b>before</b> the data existed and stamped in Bitcoin. NEAR's own chain scores them live.</p>{live}""")

    n = len(steps)
    body = "".join(
        f"<section class='q-step' id='s{i + 1}' data-t='{e(t)}'><div class='tag'><span class='n'>{i + 1}</span>{e(t)}</div>{html_}</section>"
        for i, (k, t, html_) in enumerate(steps))
    title = f"Coverage in 60 seconds: NEAR wins back {pct(s['payback'])} of what it mints"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Coverage in 60 seconds</title>
<meta name="description" content="{e(title)}"><meta name="color-scheme" content="light dark">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{D.FONTS}">
<style>{D.CSS}{D.PATH_CSS}{QUICK_CSS}</style></head><body>
<div class="q-wrap"><header class="q-mast"><div class="brand"><b>Coverage</b><span>in 60 seconds</span></div>
<div class="acts"><a class="q-btn small" href="index.html">Full report</a><button class="toggle" id="theme" type="button" aria-label="Switch between paper and ink"><i></i><span>Ink</span></button></div></header></div>
<div class="q-prog" aria-hidden="true"><div class="q-wrap"><div class="row"><b id="q-n">Step 1 of {n}</b><span id="q-t">{e(steps[0][1])}</span></div><div class="bar"><i id="q-bar"></i></div></div></div>
<main class="q-wrap">
<section class="q-hero"><span class="eyebrow">NEAR · the short version</span>
<h1>NEAR makes new coins. We measured how much it <em>wins back</em>.</h1>
<p class="lead">{n} quick steps. One idea each. Every number is real and you can check it.</p>
<ul class="chips"><li>About 60 seconds</li><li>{n} steps</li><li>Last {s['window_days']:.0f} days of NEAR mainnet</li></ul></section>
{body}
<section class="q-end"><h2>That's it.</h2><p>NEAR wins back <b>{pct(s['payback'])}</b> of what it makes, and break-even is <b>{s['multiple']:.1f}×</b> away, not {s['burn_only_multiple']:.0f}×.</p>
<div class="acts"><a class="q-btn solid" href="index.html">Read the full report</a><a class="q-btn" href="{D.REPO}">See the code</a></div></section>
<footer class="q-foot"><span>Coverage · MIT licence · result <code>{sha[:12]}</code></span><span>Same numbers as the full report, from <code>out/results.json</code>.</span></footer>
</main><script>{QUICK_JS}</script></body></html>"""
