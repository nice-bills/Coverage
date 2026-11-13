"""Render out/results.json (+ the ledger and the epoch tape) to dist/index.html, an editorial research report.

Stdlib only. One static file: fonts come from Google Fonts with system fallbacks, everything else is inline.
When run.py calls render(), this module also records the lines run.py prints after it and, once run.py
exits, writes them into the page with the result hash, so "Check it yourself" shows this build's real output.
"""
import atexit, csv, datetime, hashlib, html, json, os, sys

REPO = "https://github.com/nice-bills/Coverage"
WORKFLOW = REPO + "/actions/workflows/pages.yml"
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600"
         "&family=JetBrains+Mono:wght@400&display=swap")

# Teal: NEAR that comes back to the token (buybacks). Terracotta: NEAR burnt. Ink: NEAR minted.
CSS = """
:root{color-scheme:light;
--paper:#F5F0E6;--paper-2:#EEE7D9;--card:#FAF6EE;--ink:#1D1B17;--ink-2:#4A453C;--muted:#7A7265;--rule:#DDD4C3;--rule-2:#E7DFD0;
--teal:#008C80;--teal-soft:rgba(0,140,128,.14);--terra:#C4532D;--terra-soft:rgba(196,83,45,.16);--gray-fill:#E3DBCB;--bad:#B3261E;
--term:#1D1B17;--term-ink:#F5F0E6;--term-ok:#7FD1C4;--term-bad:#FF9C8A;
--serif:"Instrument Serif","Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
--sans:Inter,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
--mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--gut:clamp(16px,4vw,56px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;
--paper:#16150F;--paper-2:#1E1C16;--card:#1C1A14;--ink:#EDE6D8;--ink-2:#C2BAAA;--muted:#948C7D;--rule:#35322A;--rule-2:#2A2821;
--teal:#2AA597;--teal-soft:rgba(42,165,151,.18);--terra:#DB6A43;--terra-soft:rgba(219,106,67,.2);--gray-fill:#2C2A23;--bad:#F07167;
--term:#0D0C09;--term-ink:#EDE6D8}}
:root[data-theme="dark"]{color-scheme:dark;
--paper:#16150F;--paper-2:#1E1C16;--card:#1C1A14;--ink:#EDE6D8;--ink-2:#C2BAAA;--muted:#948C7D;--rule:#35322A;--rule-2:#2A2821;
--teal:#2AA597;--teal-soft:rgba(42,165,151,.18);--terra:#DB6A43;--terra-soft:rgba(219,106,67,.2);--gray-fill:#2C2A23;--bad:#F07167;
--term:#0D0C09;--term-ink:#EDE6D8}
:root{--glow-a:rgba(0,140,128,.10);--glow-b:rgba(196,83,45,.075);--ring:rgba(0,140,128,.36);--ease:cubic-bezier(.2,.7,.2,1)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--glow-a:rgba(42,165,151,.17);--glow-b:rgba(219,106,67,.12);--ring:rgba(42,165,151,.45)}}
:root[data-theme="dark"]{--glow-a:rgba(42,165,151,.17);--glow-b:rgba(219,106,67,.12);--ring:rgba(42,165,151,.45)}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:64px}
body{margin:0;background:var(--paper);color:var(--ink);font:400 16px/1.6 var(--sans);font-feature-settings:"ss01","cv11";-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration-color:var(--rule);text-underline-offset:3px}a:hover{text-decoration-color:currentColor}
:focus-visible{outline:2px solid var(--teal);outline-offset:3px}
.num{font-variant-numeric:tabular-nums}.teal{color:var(--teal)}.terra{color:var(--terra)}
code{font-family:var(--mono);font-size:.84em;overflow-wrap:anywhere}
.wrap{max-width:1360px;margin:0 auto;padding:0 var(--gut)}
.eyebrow{font:500 11.5px/1.35 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.mast{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:22px 0 18px;border-bottom:1px solid var(--rule)}
.brand{display:flex;align-items:baseline;gap:14px;min-width:0}.brand b{font:400 28px/1 var(--serif);letter-spacing:-.01em}
.brand span{font-size:13px;color:var(--muted)}
.mast nav{display:flex;gap:22px;font-size:13.5px;color:var(--ink-2)}.mast nav a{text-decoration:none}.mast nav a:hover{color:var(--ink)}
.toggle{flex:none;border:1px solid var(--rule);background:transparent;color:var(--ink-2);border-radius:999px;padding:6px 12px;font:500 12.5px var(--sans);cursor:pointer;display:inline-flex;gap:7px;align-items:center}
.toggle:hover{border-color:var(--muted)}
.mast nav a{white-space:nowrap}@media (max-width:1440px){.brand span{display:none}}
.toggle.quick{text-decoration:none;margin-left:auto;background:var(--teal);border-color:var(--teal);color:#fff;font-size:14px;font-weight:600;padding:8px 16px}
.quick-cta{grid-column:1/-1;justify-self:start;width:fit-content;display:inline-flex;align-items:center;gap:16px;margin:32px 0 28px;padding:18px 26px;border-radius:18px;background:var(--teal);color:#fff;text-decoration:none;box-shadow:0 10px 30px -12px var(--teal);max-width:100%;transition:transform .2s var(--ease),box-shadow .2s}
.inv{grid-column:1/-1;margin-top:40px;border:1px solid var(--ink);border-radius:20px;padding:24px 28px;background:var(--card)}
.inv ul{list-style:none;margin:14px 0 0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 36px}
.inv li{display:grid;gap:4px;align-content:start}.inv .k{font:600 13px var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--teal)}
.inv li:nth-child(4) .k{color:var(--terra)}.inv .v{font-size:17px;line-height:1.5;color:var(--ink)}
@media (max-width:720px){.inv ul{grid-template-columns:1fr}.inv{padding:20px}}
.quick-cta:hover{transform:translateY(-2px);box-shadow:0 14px 34px -10px var(--teal)}
.quick-cta .ic{font-size:28px;line-height:1}.quick-cta b{display:block;font:600 clamp(18px,2.2vw,22px)/1.25 var(--sans)}
.quick-cta small{display:block;font-size:15px;opacity:.9;margin-top:2px}.quick-cta .ar{font-size:26px;margin-left:auto}
@media screen and (prefers-reduced-motion:no-preference){.quick-cta .ar{animation:qnudge 1.6s ease-in-out infinite}@keyframes qnudge{50%{transform:translateX(5px)}}}
.toggle i{width:10px;height:10px;border-radius:50%;background:linear-gradient(90deg,var(--ink) 50%,transparent 50%);border:1px solid var(--ink);display:inline-block}
.hero{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:24px;padding:clamp(40px,7vw,96px) 0 40px}
.hero{position:relative;isolation:isolate;overflow-x:clip}
.hero::before,.hero::after{content:"";position:absolute;z-index:-1;pointer-events:none;border-radius:50%}
.hero::before{width:58%;aspect-ratio:1.4;left:0;top:-6%;background:radial-gradient(closest-side,var(--glow-a),transparent)}
.hero::after{width:48%;aspect-ratio:1.3;right:0;top:22%;background:radial-gradient(closest-side,var(--glow-b),transparent)}
.hero .meta{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:8px 22px;margin-bottom:28px}
.hero h1{grid-column:1/span 11;margin:0;font:400 clamp(44px,8vw,120px)/.98 var(--serif);letter-spacing:-.022em;text-wrap:balance}
.hero h1 em{font-style:italic;color:var(--teal)}
.hero h1 s{text-decoration-thickness:3px;text-decoration-color:var(--terra);color:var(--muted)}
.hero .dek{grid-column:1/span 6;margin:34px 0 0;font-size:clamp(17px,1.35vw,19.5px);line-height:1.6;color:var(--ink-2);max-width:62ch}
.hero .dek strong{color:var(--ink);font-weight:500}
.hero .byline{grid-column:8/span 5;align-self:end;font-size:13.5px;color:var(--muted);border-top:1px solid var(--rule);padding-top:14px;margin:34px 0 0}
.hero .byline b{color:var(--ink-2);font-weight:500}
.ruler{margin:20px 0 0;padding:34px 0 10px;border-top:1px solid var(--rule)}
.head{display:flex;justify-content:space-between;align-items:baseline;gap:8px 20px;flex-wrap:wrap;margin-bottom:6px}
.head h2{margin:0;font:400 clamp(22px,2.2vw,30px)/1.15 var(--serif)}
.live{display:grid;grid-template-columns:minmax(200px,1.3fr) repeat(4,minmax(0,1fr));border:1px solid var(--rule);border-radius:16px;background:var(--card);margin:44px 0 0;overflow:hidden}
.live>div{padding:18px 22px;border-left:1px solid var(--rule-2);min-width:0}
.live>div:first-child{border-left:0;display:flex;flex-direction:column;justify-content:center;gap:4px}
.pulse{display:inline-flex;align-items:center;gap:8px;font:500 12.5px var(--sans);color:var(--ink)}
.pulse::before{content:"";flex:none;width:7px;height:7px;border-radius:50%;background:var(--teal);animation:pulse 2.4s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 var(--ring)}70%{box-shadow:0 0 0 9px transparent}100%{box-shadow:0 0 0 0 transparent}}
.live small{font-size:12px;color:var(--muted);display:block;line-height:1.4}
.live .v{font:400 28px/1.15 var(--serif);margin-top:4px;white-space:nowrap;font-variant-numeric:tabular-nums}
.live .v.teal{color:var(--teal)}.live .v small{display:inline;font:400 12px var(--sans);margin-left:4px}
.lfoot{grid-column:1/-1;margin:0;padding:9px 22px!important;border-top:1px solid var(--rule-2);border-left:0!important;font-size:12px;color:var(--muted)}
.lfoot[hidden]{display:none}
.scale{margin:56px 0 0}
.scale-bar{display:flex;height:56px;border-radius:10px;overflow:hidden;gap:2px;margin:16px 0 12px}
.scale-legend{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.scale-legend div{border-top:2px solid var(--c);padding-top:10px;font-size:14px;color:var(--ink-2)}
.scale-legend b{display:block;font:400 30px/1.1 var(--serif);color:var(--ink);font-variant-numeric:tabular-nums}
.hatch{background:repeating-linear-gradient(135deg,var(--gray-fill) 0 6px,transparent 6px 9px),var(--paper-2)}
.fee{margin-top:18px;display:grid;grid-template-columns:minmax(0,220px) minmax(0,1fr);gap:16px;align-items:center;font-size:13px;color:var(--muted)}
.fee .scale-bar{height:12px;margin:0;border-radius:6px}
.body{display:grid;grid-template-columns:220px minmax(0,1fr);column-gap:clamp(24px,4vw,72px);margin-top:72px;border-top:1px solid var(--ink)}
.index{position:sticky;top:0;align-self:start;padding:34px 0 0;max-height:100vh}
.index ol{list-style:none;margin:12px 0 0;padding:0}
.index li a{display:grid;grid-template-columns:30px 1fr;align-items:baseline;text-decoration:none;color:var(--muted);padding:10px 0;position:relative;transition:color .25s}
.index li a .n{font:italic 400 15px var(--serif)}.index li a .t{font-size:14px;line-height:1.35}
.index li a .bar{position:absolute;left:30px;right:0;bottom:2px;height:1px;background:var(--rule)}
.index li a .bar i{display:block;height:100%;width:0;background:var(--ink);transition:width .12s linear}
.index li.on a,.index li.done a,.index li a:hover{color:var(--ink)}.index li.done a .bar i{width:100%}
.index .foot{margin-top:28px;font-size:12px;color:var(--muted);line-height:1.5}
.index .foot b{display:block;font:400 34px/1 var(--serif);color:var(--ink);margin-bottom:4px}
.mobile-index{display:none}
.chapter{padding:34px 0 96px;border-bottom:1px solid var(--rule);min-width:0}.chapter:last-child{border-bottom:0}
.ch-head{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:24px;align-items:end;margin-bottom:40px}
.ch-num{grid-column:1/-1;display:flex;align-items:center;gap:14px;margin-bottom:22px}
.ch-num .n{font:italic 400 20px var(--serif)}.ch-num .line{flex:1;height:1px;background:var(--rule)}
.ch-head h2{grid-column:1/span 9;margin:0;font:400 clamp(34px,4.2vw,62px)/1.02 var(--serif);letter-spacing:-.018em;text-wrap:balance}
.ch-head p{grid-column:1/span 7;margin:20px 0 0;color:var(--ink-2);font-size:17px;max-width:64ch}
.grid12{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:24px;row-gap:40px}.grid12>*{min-width:0}
.prose{color:var(--ink-2);font-size:14px;line-height:1.7;max-width:62ch;margin:14px 0 0}
sup.fn{font-size:.68em;line-height:0;vertical-align:super;margin-left:1px}sup.fn a{text-decoration:none;color:var(--teal);font-weight:600}
.pull{border-top:1px solid var(--ink);padding-top:14px}
.pull .big{font:400 clamp(84px,10vw,168px)/.86 var(--serif);letter-spacing:-.03em;margin:8px 0 14px;font-variant-numeric:tabular-nums}
.pull .big sup{font-size:.38em;vertical-align:.95em;margin-left:4px;letter-spacing:0}
.pull p{margin:0;color:var(--ink-2);max-width:34ch;font-size:15.5px}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}
.stat{padding:16px 22px 4px 0;border-top:1px solid var(--rule);margin-right:22px}
.stat .v{font:400 46px/1 var(--serif);letter-spacing:-.01em;margin:10px 0 8px;font-variant-numeric:tabular-nums}
.stat p{margin:0;font-size:13.5px;color:var(--muted);line-height:1.45}
figure{margin:0}
.fig{background:var(--card);border:1px solid var(--rule-2);border-radius:18px;padding:clamp(18px,2.4vw,32px);min-width:0}
.fig-title{display:flex;justify-content:space-between;align-items:baseline;gap:10px 16px;flex-wrap:wrap;margin-bottom:6px}
.fig-title h3{margin:0;font:400 clamp(21px,1.8vw,26px)/1.2 var(--serif);max-width:40ch;text-wrap:balance}
.fig-sub{margin:4px 0 14px;font-size:13.5px;color:var(--muted)}
.legend{display:flex;gap:6px 16px;flex-wrap:wrap;font-size:12.5px;color:var(--ink-2)}
.legend span{display:inline-flex;align-items:center;gap:7px}
.legend i{width:10px;height:10px;border-radius:3px;background:var(--c)}.legend i.l{height:2px;width:16px;border-radius:2px}
.legend i.o{background:transparent;border:1px solid var(--teal);background:var(--teal-soft)}
figcaption{margin-top:14px;font-size:12.5px;color:var(--muted);line-height:1.5}
.chart{position:relative;touch-action:pan-y}.chart[tabindex]{border-radius:6px}
.chart svg{display:block;width:100%;overflow:visible}
.chart text{font-family:var(--sans);font-size:11.5px;fill:var(--muted)}
.chart .lab{fill:var(--ink);font-size:12.5px;font-weight:500}.chart .lab-s{fill:var(--ink-2);font-size:12px}
.chart .ser{font-family:var(--serif);font-size:24px;fill:var(--ink)}
.tip{position:absolute;left:0;top:0;pointer-events:none;background:var(--ink);color:var(--paper);border-radius:10px;padding:9px 12px;font-size:12.5px;line-height:1.45;white-space:nowrap;opacity:0;transform:translateY(4px);transition:opacity .15s,transform .15s;z-index:3;box-shadow:0 8px 24px rgba(0,0,0,.18);font-variant-numeric:tabular-nums}
.tip.on{opacity:1;transform:none}.tip b{font-weight:600}
.tip .sw{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px}
#tape{display:block;width:100%;height:340px;cursor:crosshair;touch-action:pan-y}
.read{margin-top:16px;border-top:1px solid var(--rule-2);padding-top:14px;min-height:5.2rem}
.read h4{margin:0 0 8px;font:500 14px var(--sans)}.read h4 small{font-weight:400;color:var(--muted);margin-left:6px}
.read dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 24px;margin:0}
.read dt{font-size:12px;color:var(--muted)}.read dd{margin:2px 0 0;font:400 20px/1.15 var(--serif);font-variant-numeric:tabular-nums}
.read dd small{font:400 12px var(--sans);color:var(--muted);margin-left:3px}.read .hts{font:400 13px var(--sans);white-space:nowrap}
.vrow{margin-top:18px;display:flex;flex-wrap:wrap;gap:10px}
.btn{font:500 13.5px var(--sans);color:var(--ink);background:transparent;border:1px solid var(--rule);border-radius:999px;padding:9px 16px;cursor:pointer;transition:transform .1s ease-out,border-color .15s,background-color .15s}
.btn:hover{border-color:var(--ink)}.btn:active{transform:scale(.97)}.btn:disabled{opacity:.45;cursor:progress}
.btn.pri{background:var(--ink);border-color:var(--ink);color:var(--paper)}.btn.pri:hover{background:var(--ink-2)}
.check:empty{display:none}.check{margin-top:18px;border-top:1px solid var(--rule-2);padding-top:14px}
.check h4{margin:0 0 6px;font:500 14px var(--sans)}.check p{font-size:12.5px;color:var(--muted);margin:10px 0 0}
.check p.verdict{font:400 22px/1.25 var(--serif);color:var(--teal);margin-top:12px}.check p.verdict.no{color:var(--bad)}
.eq{color:var(--teal);font-weight:500}.ne{color:var(--bad);font-weight:500}.wait{color:var(--muted);animation:fade .9s ease-in-out infinite alternate}
@keyframes fade{from{opacity:.3}to{opacity:1}}
.multiples{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid var(--rule)}
.mult{padding:18px 24px 18px 0;min-width:0}.mult+.mult{padding-left:24px;border-left:1px solid var(--rule-2)}
.mult h4{margin:0 0 4px;font:400 20px/1.25 var(--serif);text-wrap:balance}
.mult .u{font-size:12.5px;color:var(--muted);margin-bottom:8px}.mult .src{font-size:11.5px;color:var(--muted);margin:8px 0 0;line-height:1.45}
.more .multiples{border-top:0}.more .mult{border-top:1px solid var(--rule)}
.more .mult:nth-child(3n+1){padding-left:0;border-left:0}
.audit{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--rule)}
.audit>div{padding:18px 20px 0 0;min-width:0}.audit>div+div{padding-left:20px;border-left:1px solid var(--rule-2)}
.audit .v{font:400 38px/1 var(--serif);margin:8px 0 10px;font-variant-numeric:tabular-nums}.audit .v span{font-size:.5em;color:var(--muted)}
.audit p{margin:0;font-size:13.5px;color:var(--ink-2);line-height:1.5}
.senders{display:flex;flex-direction:column;gap:12px;margin-top:6px}
.srow{display:grid;grid-template-columns:minmax(0,1fr) 70px;gap:12px;align-items:center;font-size:13.5px}
.srow .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink-2)}
.srow .tr{grid-column:1/-1;height:8px;border-radius:4px;background:var(--rule-2);overflow:hidden;margin-top:-6px}
.srow .tr i{display:block;height:100%;background:var(--muted);border-radius:4px;min-width:3px}.srow .tr i.t{background:var(--teal)}
.srow .pc{text-align:right;font-weight:500;font-variant-numeric:tabular-nums}
.tw{overflow-x:auto;max-width:100%}
.tbl{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}
.tbl th{font:500 11.5px var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:0 12px 12px 0;border-bottom:1px solid var(--ink);vertical-align:bottom}
.tbl td{padding:14px 12px 14px 0;border-bottom:1px solid var(--rule-2);color:var(--ink-2);vertical-align:top}
.tbl td:first-child{color:var(--ink)}.tbl .r{text-align:right}.tbl td small{display:block;font-size:12.5px;color:var(--muted)}
.tbl td.big{font:400 24px/1 var(--serif);color:var(--ink)}.tbl td.big span{font:400 13px var(--sans);color:var(--muted)}
.tbl tr:last-child td{border-bottom:0}
.inl{display:inline-block;height:6px;border-radius:3px;background:var(--muted);vertical-align:middle;margin-right:8px}
.calc{display:grid;grid-template-columns:5fr 7fr;border-radius:20px;overflow:hidden;border:1px solid var(--rule)}
.calc>div{min-width:0}
.calc .ctl{background:var(--card);padding:clamp(20px,2.6vw,36px)}
.calc .out{background:var(--paper-2);padding:clamp(20px,2.6vw,36px);display:flex;flex-direction:column;justify-content:space-between;gap:28px}
.split{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid var(--rule);padding-top:14px;gap:12px}
.split b{display:block;font:400 26px/1.1 var(--serif);margin-top:4px;font-variant-numeric:tabular-nums}.split span{font-size:12px;color:var(--muted)}
.slider{margin:0 0 28px}
.slider label{display:flex;justify-content:space-between;gap:12px;font-size:14px;color:var(--ink-2);margin-bottom:10px}
.slider label b{font:400 22px/1 var(--serif);color:var(--ink);white-space:nowrap;font-variant-numeric:tabular-nums}
.slider .hint{font-size:12px;color:var(--muted);margin-top:6px}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:22px;background:transparent;margin:0;touch-action:pan-y}
input[type=range]::-webkit-slider-runnable-track{height:3px;background:linear-gradient(90deg,var(--ink) var(--p,50%),var(--rule) var(--p,50%));border-radius:3px}
input[type=range]::-moz-range-track{height:3px;background:var(--rule);border-radius:3px}
input[type=range]::-moz-range-progress{height:3px;background:var(--ink)}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:var(--paper);border:1.5px solid var(--ink);margin-top:-8.5px;box-shadow:0 2px 6px rgba(0,0,0,.12);transition:box-shadow .25s,border-color .25s,transform .2s}
input[type=range]::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:var(--paper);border:1.5px solid var(--ink);transition:box-shadow .25s,border-color .25s,transform .2s}
input[type=range]:hover::-webkit-slider-thumb,input[type=range]:active::-webkit-slider-thumb{border-color:var(--teal);box-shadow:0 0 0 6px var(--teal-soft),0 0 18px 2px var(--teal-soft),0 2px 6px rgba(0,0,0,.12)}
input[type=range]:hover::-moz-range-thumb,input[type=range]:active::-moz-range-thumb{border-color:var(--teal);box-shadow:0 0 0 6px var(--teal-soft),0 0 18px 2px var(--teal-soft)}
input[type=range]:active::-webkit-slider-thumb{transform:scale(1.08)}input[type=range]:active::-moz-range-thumb{transform:scale(1.08)}
input[type=range]:focus-visible{outline:none}input[type=range]:focus-visible::-webkit-slider-thumb{outline:2px solid var(--teal);outline-offset:2px}
input[type=range]:focus-visible::-moz-range-thumb{outline:2px solid var(--teal);outline-offset:2px}
.out .res{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.out .res .big{font:400 clamp(56px,7vw,110px)/.9 var(--serif);letter-spacing:-.03em;margin-top:8px;font-variant-numeric:tabular-nums}
.out .res p{margin:8px 0 0;font-size:13.5px;color:var(--muted)}
.gauge{position:relative;height:44px}
.gauge .trk{position:absolute;left:0;right:0;top:16px;height:12px;border-radius:6px;background:var(--rule)}
.gauge .f1,.gauge .f2{position:absolute;top:16px;height:12px}
.gauge .f1{left:0;background:var(--terra);border-radius:6px 0 0 6px}.gauge .f2{background:var(--teal)}
.gauge .tick{position:absolute;top:8px;bottom:0;width:1px;background:var(--ink)}
.gauge .tick span{position:absolute;top:-14px;right:4px;font-size:11.5px;white-space:nowrap;color:var(--ink-2)}
.reset{border:0;background:none;color:var(--ink-2);font:500 13px var(--sans);text-decoration:underline;text-underline-offset:3px;cursor:pointer;padding:0}
.mlist{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--rule);margin-top:56px}
.mlist>div{padding:16px 18px 0 0;min-width:0}.mlist>div+div{padding-left:18px;border-left:1px solid var(--rule-2)}
.mlist h4{margin:0 0 6px;font:400 22px/1.15 var(--serif)}.mlist p{margin:0;font-size:13.5px;color:var(--ink-2);line-height:1.5}
.mlist code{display:block;margin-top:8px;font-size:11.5px;color:var(--muted)}
details{border-top:1px solid var(--rule);margin-top:40px}details[open]{border-bottom:1px solid var(--rule);padding-bottom:28px}
details>summary{cursor:pointer;list-style:none;padding:18px 34px 18px 0;position:relative;font:400 24px/1.2 var(--serif);text-wrap:balance}
details>summary::-webkit-details-marker{display:none}
details>summary::after{content:"";position:absolute;right:6px;top:50%;width:9px;height:9px;margin-top:-7px;border:solid var(--ink-2);border-width:0 1.5px 1.5px 0;transform:rotate(45deg);transition:transform .15s ease-out}
details[open]>summary::after{transform:rotate(-135deg);margin-top:-2px}
details>summary:hover{color:var(--teal)}details>summary small{display:block;font:400 13.5px/1.5 var(--sans);color:var(--muted);margin-top:4px}
.sec{margin-top:36px}.sec:first-of-type{margin-top:8px}.sec h4{margin:0 0 12px;font:400 22px/1.2 var(--serif)}
.sec .sub{font-size:13.5px;color:var(--muted);margin:0 0 14px;max-width:72ch}
.rounds{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:20px}
.round{background:var(--card);border:1px solid var(--rule-2);border-radius:16px;padding:22px 22px 18px;display:flex;flex-direction:column;gap:12px;min-width:0}
.round .top{display:flex;justify-content:space-between;align-items:center;gap:10px}
.badge{font:500 11px var(--sans);letter-spacing:.1em;text-transform:uppercase;padding:4px 9px;border-radius:999px;border:1px solid var(--rule);color:var(--ink-2);white-space:nowrap}
.badge.pass{color:var(--teal);border-color:var(--teal)}.badge.fail{color:var(--bad);border-color:var(--bad)}
.round h4{margin:0;font:400 26px/1.1 var(--serif)}
.band{position:relative;height:46px;margin:8px 0 2px}
.band .ax{position:absolute;left:0;right:0;top:22px;height:1px;background:var(--rule)}
.band .b{position:absolute;top:14px;height:16px;border-radius:8px;background:var(--teal-soft);border:1px solid var(--teal)}
.band .m{position:absolute;top:10px;height:24px;width:2px;margin-left:-1px;background:var(--ink);border-radius:2px}
.band .m span{position:absolute;top:-16px;left:50%;transform:translateX(-50%);font-size:11px;color:var(--ink-2);white-space:nowrap}
.band .a{position:absolute;top:15px;width:14px;height:14px;margin-left:-7px;border-radius:50%;border:2px solid var(--card)}
.band .lbl{position:absolute;top:33px;font-size:11px;color:var(--muted);transform:translateX(-50%);white-space:nowrap}
.live .lsf{display:block;margin-top:4px;color:var(--ink-2)}.live .lsf b{color:var(--teal);font-weight:600}
.round .sofar{display:grid;grid-template-columns:1fr auto;align-items:baseline;gap:2px 12px;border-radius:12px;padding:12px 14px;background:var(--teal-soft)}
.round .sofar span{font-size:13px;color:var(--ink-2)}.round .sofar b{font:400 30px/1 var(--serif);color:var(--teal);grid-row:span 2;align-self:center}
.round .sofar small{font-size:12.5px;color:var(--ink-2)}.round .sofar.out{background:var(--terra-soft)}.round .sofar.out b{color:var(--terra)}
.round dl{margin:0;display:grid;grid-template-columns:auto minmax(0,1fr);gap:6px 14px;font-size:13px}
.round dt{color:var(--muted)}.round dd{margin:0;text-align:right;white-space:nowrap;color:var(--ink-2);font-variant-numeric:tabular-nums}
.round dd small{display:block;font-size:11.5px;color:var(--muted)}.round dd .hit{color:var(--teal)}.round dd .miss{color:var(--bad)}
.round .fan text{font-size:10.5px}
.round .hash{font-family:var(--mono);font-size:11px;color:var(--muted);word-break:break-all;border-top:1px solid var(--rule-2);padding-top:10px}
.prog{height:4px;border-radius:2px;background:var(--rule);overflow:hidden}.prog i{display:block;height:100%;background:var(--ink)}
.pmeta{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-bottom:6px}
.rlive{font-size:12.5px;color:var(--teal)}.rlive:empty{display:none}
.judging{display:flex;gap:18px 26px;align-items:center;background:var(--ink);color:var(--paper);border-radius:16px;padding:20px 26px;margin-top:20px}
.judging .d{font:400 40px/1 var(--serif);white-space:nowrap}.judging p{margin:0;font-size:14.5px;opacity:.85;max-width:70ch}
.spread{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)}
.side{padding:30px clamp(18px,3vw,44px) 22px 0;min-width:0}
.side+.side{padding-left:clamp(18px,3vw,44px);padding-right:0;border-left:1px solid var(--rule)}
.side h3{margin:0 0 6px;font:italic 400 clamp(40px,4.4vw,64px)/1 var(--serif);letter-spacing:-.01em}
.side .k{font-size:13.5px;color:var(--muted);margin-bottom:22px}
.pt{display:grid;grid-template-columns:44px minmax(0,1fr);gap:4px 10px;padding:18px 0;border-top:1px solid var(--rule-2)}
.pt .i{font:italic 400 24px/1.1 var(--serif);color:var(--muted)}
.pt h4{margin:0;font:500 16.5px/1.35 var(--sans)}.pt p{grid-column:2;margin:4px 0 0;font-size:14.5px;color:var(--ink-2);line-height:1.6}
.verdict{margin:40px auto 0;max-width:46ch;text-align:center}
.verdict blockquote{margin:0;font:italic 400 clamp(26px,2.8vw,40px)/1.25 var(--serif);text-wrap:balance}
.verdict cite{display:block;margin-top:14px;font:500 12px var(--sans);font-style:normal;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.steps{display:flex;flex-direction:column;border-top:1px solid var(--rule)}
.step{display:grid;grid-template-columns:64px minmax(0,4fr) minmax(0,7fr);gap:20px;padding:24px 0;border-bottom:1px solid var(--rule-2);align-items:start}
.step>*{min-width:0}.step .sn{font:italic 400 34px/1 var(--serif);color:var(--muted)}
.step h4{margin:0 0 6px;font:500 16px var(--sans)}.step p{margin:0;font-size:14px;color:var(--ink-2)}
.step p+p{margin-top:8px}
pre.term{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;background:var(--term);color:var(--term-ink);border-radius:12px;padding:16px 18px;font:400 12.5px/1.65 var(--mono);font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0;overflow-x:auto;white-space:pre;position:relative;tab-size:4}
pre.term .c{opacity:.55}pre.term .ok{color:var(--term-ok)}pre.term .no{color:var(--term-bad)}pre.term .p{opacity:.55;user-select:none}pre.term[data-copy]{padding-right:76px}
pre.term button{position:absolute;top:8px;right:8px;font:500 11.5px var(--sans);padding:3px 9px;background:transparent;color:var(--term-ink);border:1px solid rgba(255,255,255,.25);border-radius:999px;cursor:pointer;opacity:.75}
pre.term button:hover{opacity:1}
.prov{margin:8px 0 0;font-size:12.5px;color:var(--muted);line-height:1.5}.prov b{color:var(--ink-2);font-weight:500}
.hashbox{margin-top:40px;display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:24px;align-items:end}
.hashbox .l{grid-column:1/span 5}.hashbox .l h3{margin:6px 0 0;font:400 clamp(28px,3vw,42px)/1.1 var(--serif)}
.hashbox .r{grid-column:6/span 7;border-left:2px solid var(--teal);padding-left:20px;min-width:0}
.hrow{padding:6px 0}.hrow>span{display:block;font-size:12px;color:var(--muted)}.hrow>span code{font-size:11.5px}
.hrow>code{display:block;font:400 clamp(13px,1.35vw,18px)/1.45 var(--mono);word-break:break-all;color:var(--teal)}
.hrow>code.x{color:var(--bad)}
.match{display:inline-flex;align-items:center;gap:8px;margin-top:10px;font:500 13px var(--sans);color:var(--teal)}
.match::before{content:"";width:16px;height:16px;border-radius:50%;background:var(--teal) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='M4.5 8.2l2.3 2.3 4.7-5' fill='none' stroke='white' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/contain no-repeat}
.match.no{color:var(--bad)}.match.no::before{background:var(--bad)}.match.wait{color:var(--muted)}.match.wait::before{background:var(--rule)}
.notes{padding:56px 0 64px;border-top:1px solid var(--ink);display:grid;grid-template-columns:220px minmax(0,1fr);column-gap:clamp(24px,4vw,72px)}
.notes ol{margin:0;padding:0 0 0 1.4em;columns:2;column-gap:48px;font-size:13px;color:var(--ink-2);line-height:1.55}
.notes li{margin-bottom:10px;break-inside:avoid}.notes li::marker{color:var(--teal);font-weight:600}
.notes h4{margin:28px 0 10px;font:500 11.5px/1.3 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.notes ul{margin:0;padding:0;list-style:none;columns:2;column-gap:48px;font-size:12.5px;color:var(--ink-2);line-height:1.5}
.notes ul li{margin-bottom:8px}.notes ul li b{font-weight:500;color:var(--ink)}
.colophon{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:22px 0 40px;border-top:1px solid var(--rule);font-size:12.5px;color:var(--muted)}
@media (max-width:1100px){
.body,.notes{grid-template-columns:minmax(0,1fr)}.index{display:none}
.mobile-index{display:block;position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--paper) 92%,transparent);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-bottom:1px solid var(--rule);margin:0 calc(-1*var(--gut));padding:0 var(--gut)}
.mobile-index details{border:0;margin:0;padding:0}.mobile-index summary{padding:10px 0;font:400 13px var(--sans)}
.mobile-index summary::after{right:2px;width:7px;height:7px}
.mobile-index .row{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding-right:22px}.mobile-index .row b{font:italic 400 17px var(--serif)}
.mobile-index .p{height:2px;background:var(--rule);margin-top:8px;border-radius:2px}.mobile-index .p i{display:block;height:100%;width:0;background:var(--ink)}
.mobile-index ol{list-style:none;margin:0;padding:0 0 10px}.mobile-index ol a{display:block;padding:8px 0;text-decoration:none;font-size:14px;color:var(--ink-2);border-top:1px solid var(--rule-2)}
.mobile-index ol a span{font:italic 400 15px var(--serif);color:var(--muted);margin-right:10px}
.notes>div:first-child{margin-bottom:18px}}
@media (max-width:980px){.live{grid-template-columns:repeat(2,minmax(0,1fr))}.live>div{border-left:0;border-top:1px solid var(--rule-2)}
.live>div:first-child{grid-column:1/-1;border-top:0}.live>div:nth-child(odd):not(:first-child):not(.lfoot){border-left:1px solid var(--rule-2)}
.mlist{grid-template-columns:repeat(2,minmax(0,1fr))}.mlist>div:nth-child(odd){padding-left:0;border-left:0}.mlist>div:nth-child(n+3){border-top:1px solid var(--rule-2);margin-top:16px}}
@media (max-width:820px){
.mast nav{display:none}
.hero h1,.hero .dek,.hero .byline,.ch-head h2,.ch-head p{grid-column:1/-1}
.live .v{font-size:23px}
.scale-legend{grid-template-columns:minmax(0,1fr)}.fee{grid-template-columns:minmax(0,1fr);gap:6px}
.grid12>*{grid-column:1/-1!important}
.stats{grid-template-columns:repeat(2,minmax(0,1fr))}
.multiples,.audit{grid-template-columns:repeat(2,minmax(0,1fr))}
.mult+.mult,.audit>div+div{padding-left:0;border-left:0}
.mult:nth-child(even),.audit>div:nth-child(even){padding-left:18px;border-left:1px solid var(--rule-2)}
.more .mult:nth-child(3n+1){padding-left:0}.more .mult:nth-child(odd){padding-left:0;border-left:0}
.calc{grid-template-columns:minmax(0,1fr)}
.spread{grid-template-columns:minmax(0,1fr)}.side+.side{padding-left:0;border-left:0;border-top:1px solid var(--ink)}.side{padding-right:0}
.step{grid-template-columns:40px minmax(0,1fr)}.step>div:last-child{grid-column:1/-1}
.hashbox .l,.hashbox .r{grid-column:1/-1}
.notes ol,.notes ul{columns:1}
#tape{height:240px}pre.term button{display:none}pre.term[data-copy]{padding-right:18px}.read dl{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 16px}}
@media (max-width:560px){
.brand span{display:none}
.multiples,.more .multiples{grid-template-columns:minmax(0,1fr)}.mult{padding-right:0}.mult:nth-child(even){padding-left:0;border-left:0}
.stats{grid-template-columns:minmax(0,1fr)}.stat{margin-right:0}
.audit>div{padding-right:10px}.audit .v{font-size:32px}
.out .res{gap:14px}.split b{font-size:21px}
.judging{flex-direction:column;align-items:flex-start}
.hide-s{display:none}.mlist{grid-template-columns:minmax(0,1fr)}.mlist>div{padding-left:0!important;border-left:0!important}.mlist>div+div{border-top:1px solid var(--rule-2);margin-top:16px}
.live .v{font-size:21px}.pt{grid-template-columns:32px minmax(0,1fr)}}
/* motion: decorative drift is CSS only; every hidden start state needs html.anim, which the script sets just before observing */
.cu{display:inline-grid}.cu>span,.cu::after{grid-area:1/1;white-space:nowrap}.cu>span{width:0;min-width:100%}.cu::after{content:attr(data-v);visibility:hidden}
@media screen and (prefers-reduced-motion:no-preference){
.hero::before{animation:drift1 30s ease-in-out infinite alternate,glowin 2.4s ease-out both}
.hero::after{animation:drift2 36s ease-in-out infinite alternate,glowin 2.4s .3s ease-out both}
@keyframes drift1{to{transform:translate(14%,10%) scale(1.12)}}
@keyframes drift2{to{transform:translate(-16%,-12%) scale(.92)}}
@keyframes glowin{from{opacity:0}}
html.anim .rv{transition:opacity .8s var(--ease) var(--d,0s),transform 1s var(--ease) var(--d,0s)}
html.anim .rv:not(.in){opacity:0;transform:translate3d(0,16px,0)}
html.anim .hero h1 s{position:relative;text-decoration-color:transparent}
html.anim .hero h1 s::after{content:"";position:absolute;left:0;right:0;top:50.7%;height:3px;margin-top:-1.5px;background:var(--terra);transform:scaleX(0);transform-origin:0 50%;transition:transform .75s cubic-bezier(.6,0,.2,1)}
html.anim .hero h1 s.drawn::after{transform:none}
html.anim .rv .draw{stroke-dasharray:1 1;transition:stroke-dashoffset 1.8s cubic-bezier(.45,.05,.2,1) calc(var(--d,0s) + .25s)}
html.anim .rv:not(.in) .draw{stroke-dashoffset:1}
html.anim .rv .area,html.anim .round .fan polygon{transition:opacity 1s ease-out calc(var(--d,0s) + .5s),transform 1.1s var(--ease) calc(var(--d,0s) + .5s)}
html.anim .rv:not(.in) .area,html.anim .rv:not(.in) .fan polygon{opacity:0;transform:translateY(10px)}
html.anim .rv .chart circle,html.anim .rv .fan circle{transform-box:fill-box;transform-origin:center}
html.anim .rv :is(.chart circle,.chart .lab,.chart .lab-s,.chart .ser,.fan circle,.band .m,.band .a){transition:opacity .6s ease-out calc(var(--d,0s) + 1.3s),transform .6s var(--ease) calc(var(--d,0s) + 1.3s)}
html.anim .rv:not(.in) :is(.chart .lab,.chart .lab-s,.chart .ser,.band .m,.band .a){opacity:0}
html.anim .rv:not(.in) :is(.chart circle,.fan circle){opacity:0;transform:scale(.3)}
html.anim .rv :is(.grow,.scale-bar>div,.srow .tr i,.prog i,.gauge .f1,.gauge .f2,.band .b){transform-origin:0 50%;transition:transform 1.2s var(--ease) calc(var(--d,0s) + .2s),opacity .8s ease-out calc(var(--d,0s) + .2s)}
html.anim .rv:not(.in) :is(.grow,.scale-bar>div:not(.hatch),.srow .tr i,.prog i,.gauge .f1,.gauge .f2,.band .b){transform:scaleX(0)}
html.anim .rv:not(.in) .scale-bar>.hatch{opacity:0}
html.anim .rv .grow.g2,html.anim .rv .scale-bar>div:nth-child(2),html.anim .rv .gauge .f2{transition-delay:calc(var(--d,0s) + .8s)}
html.anim .rv .scale-bar>div:nth-child(3){transition-delay:calc(var(--d,0s) + 1.1s)}
html.anim .rv .srow:nth-child(2) .tr i{transition-delay:.35s}html.anim .rv .srow:nth-child(3) .tr i{transition-delay:.5s}html.anim .rv .srow:nth-child(4) .tr i{transition-delay:.65s}
html.anim .rv .prog i{transition-duration:1.4s;transition-delay:calc(var(--d,0s) + .45s)}
}
@media (max-width:600px){.hero::before{width:90%;top:-4%}.hero::after{width:80%;top:40%}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,::before,::after{animation:none!important;transition:none!important}}
@media (prefers-contrast:more){:root{--muted:var(--ink-2);--rule:var(--ink-2)}}
"""

JS = r"""
const D=JSON.parse(document.getElementById('data').textContent),S=D.s,$=q=>document.querySelector(q),root=document.documentElement,
 V=n=>getComputedStyle(root).getPropertyValue(n).trim(),MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
 fmt=(x,d=0)=>Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d}),pct=(x,d=1)=>(x*100).toFixed(d)+'%',
 dlab=s=>{const d=new Date(s+'T00:00:00Z');return d.getUTCDate()+' '+MON[d.getUTCMonth()]},
 esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])),REDRAW=[];let GROW=null;
function el(t,a,txt){return '<'+t+' '+Object.entries(a||{}).map(([k,v])=>k+'="'+v+'"').join(' ')+'>'+(txt!=null?esc(txt):'')+'</'+t+'>'}
function tipFor(box){let t=box.querySelector(':scope>.tip');if(!t){t=document.createElement('div');t.className='tip';t.setAttribute('aria-hidden','true');box.appendChild(t)}return t}
function placeTip(box,t,x,y){const w=box.clientWidth;let l=x+14;if(l+t.offsetWidth>w)l=x-t.offsetWidth-14;t.style.left=Math.max(0,Math.min(l,w-t.offsetWidth))+'px';t.style.top=Math.max(y-t.offsetHeight-10,-8)+'px'}
// hover, touch and arrow keys on an SVG chart whose points sit at xAt(i), yAt(i) in CSS pixels of the box
function interact(box,n,xAt,yAt,html){const tip=tipFor(box);let k=-1;
 const ln=()=>box.querySelector('.xh'),show=i=>{k=i;const l=ln();if(l){l.setAttribute('x1',xAt(i));l.setAttribute('x2',xAt(i));l.setAttribute('opacity',.35)}
  tip.innerHTML=html(i);tip.classList.add('on');placeTip(box,tip,xAt(i),yAt(i))},
 hide=()=>{tip.classList.remove('on');const l=ln();l&&l.setAttribute('opacity',0)},
 at=e=>{const px=e.clientX-box.getBoundingClientRect().left;let b=0;for(let j=1;j<n;j++)if(Math.abs(xAt(j)-px)<Math.abs(xAt(b)-px))b=j;return b};
 box.onpointermove=e=>show(at(e));box.onpointerdown=e=>show(at(e));box.onpointerleave=hide;box.onblur=hide;
 box.onkeydown=e=>{const d={ArrowLeft:-1,ArrowRight:1}[e.key];if(!d)return;e.preventDefault();show(Math.max(0,Math.min(n-1,k<0?n-1:k+d*(e.shiftKey?10:1))))}}

// distance to break-even, log scale
function drawRuler(){const box=$('#ruler');if(!box)return;const R=D.ruler,W=box.clientWidth,mob=W<600,H=mob?150:130,pl=6,pr=mob?18:28,
 hi=Math.log(R.max),x=v=>pl+Math.log(v)/hi*(W-pl-pr),y=mob?88:74;let s='';
 R.ticks.forEach(v=>{s+=el('line',{x1:x(v),x2:x(v),y1:y-5,y2:y+5,stroke:'var(--muted)'});s+=el('text',{x:x(v),y:y+22,'text-anchor':'middle'},v+'×')});
 s+=el('line',{x1:pl,x2:W-pr,y1:y,y2:y,stroke:'var(--rule)','stroke-width':1.5});
 s+=el('line',{x1:x(R.today),x2:x(R.burn),y1:y,y2:y,stroke:'var(--terra)','stroke-width':2,'stroke-dasharray':'2 4',opacity:.7,class:'grow g2',style:'transform-origin:'+x(R.today).toFixed(1)+'px 0'});
 s+=el('line',{x1:x(1),x2:x(R.today),y1:y,y2:y,stroke:'var(--teal)','stroke-width':3,'stroke-linecap':'round',class:'grow',style:'transform-origin:'+x(1).toFixed(1)+'px 0'});
 s+=el('text',{x:x(1),y:y-16,class:'lab-s'},mob?'Break-even':'Break-even, 1×');
 R.pts.forEach(([v,l,ls,kind,dir])=>{const xx=x(v),c=kind=='burn'?'var(--terra)':'var(--teal)',open=kind=='alt',ty=dir<0?y-30:y+44;
  s+=el('circle',{cx:xx,cy:y,r:open?5:7,fill:open?'var(--card)':c,stroke:c,'stroke-width':2});
  s+=el('line',{x1:xx,x2:xx,y1:dir<0?y-10:y+28,y2:dir<0?y-24:y+31,stroke:c});
  s+=el('text',{x:xx,y:ty,'text-anchor':xx>W-110?'end':xx<70?'start':'middle',class:'lab'},mob?ls:l)});
 box.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" height="'+H+'" role="img" aria-label="'+esc(R.aria)+'">'+s+'</svg>'}

// rolling payback, burn under buybacks
function drawPayback(){const box=$('#ch-payback');if(!box)return;const W=box.clientWidth,mob=W<600,H=mob?280:380,ml=36,mr=mob?14:110,mt=24,mb=30,
 ser=D.series,n=ser.length,t=i=>new Date(ser[i].date+'T00:00:00Z').getTime(),t0=t(0),t1=t(n-1),X=i=>ml+(t(i)-t0)/(t1-t0)*(W-ml-mr),
 mx=Math.max(...ser.map(p=>p.payback)),step=mx>.3?.1:.05,ymax=Math.ceil(mx*1.12/step)*step,Y=v=>mt+(1-v/ymax)*(H-mt-mb);let s='';
 for(let v=0;v<ymax-1e-9;v+=step){s+=el('line',{x1:ml,x2:W-mr,y1:Y(v),y2:Y(v),stroke:'var(--rule-2)'});s+=el('text',{x:ml-8,y:Y(v)+4,'text-anchor':'end'},Math.round(v*100)+'%')}
 const d0=new Date(t0);for(let m=0;;m++){const d=Date.UTC(d0.getUTCFullYear(),d0.getUTCMonth()+1+m,1);if(d>t1)break;const mo=new Date(d).getUTCMonth();if(mob&&mo%2)continue;
  s+=el('text',{x:ml+(d-t0)/(t1-t0)*(W-ml-mr),y:H-8,'text-anchor':'middle'},MON[mo])}
 let burn='',up='',dn='';ser.forEach((p,i)=>{burn+=(i?'L':'M')+X(i).toFixed(1)+','+Y(p.coverage).toFixed(1);up+=(i?'L':'M')+X(i).toFixed(1)+','+Y(p.payback).toFixed(1)});
 for(let i=n-1;i>=0;i--)dn+='L'+X(i).toFixed(1)+','+Y(ser[i].coverage).toFixed(1);
 s+=el('path',{d:up+dn+'Z',fill:'var(--teal-soft)',class:'area'})+el('path',{d:burn+'L'+X(n-1)+','+Y(0)+'L'+X(0)+','+Y(0)+'Z',fill:'var(--terra-soft)',class:'area'});
 s+=el('path',{d:burn,fill:'none',stroke:'var(--terra)','stroke-width':1.5,class:'draw',pathLength:1})+el('path',{d:up,fill:'none',stroke:'var(--teal)','stroke-width':2,'stroke-linejoin':'round',class:'draw',pathLength:1});
 let pk=0;ser.forEach((p,i)=>{if(p.payback>ser[pk].payback)pk=i});const tp=ser.findIndex(p=>p.date>=S.payback_peak_date);if(S.payback_peak_date&&tp>=0)pk=tp;
 const ann=(i,txt,anchor)=>{s+=el('circle',{cx:X(i),cy:Y(ser[i].payback),r:4.5,fill:'var(--card)',stroke:'var(--ink)','stroke-width':1.5});
  s+=el('text',{x:anchor=='start'?X(i)+4:X(i),y:Y(ser[i].payback)-12,'text-anchor':anchor,class:'lab'},txt)};
 if(pk<n-4)ann(pk,'Peak '+pct(S.payback_peak_date?S.payback_peak:ser[pk].payback)+' · '+dlab(S.payback_peak_date||ser[pk].date),X(pk)>W-mr-90?'end':'middle');
 ann(0,pct(ser[0].payback)+' · '+dlab(ser[0].date),'start');
 const xe=X(n-1),ye=Y(ser[n-1].payback);s+=el('circle',{cx:xe,cy:ye,r:4.5,fill:'var(--teal)',stroke:'var(--card)','stroke-width':2});
 if(!mob){s+=el('text',{x:xe+12,y:ye-2,class:'ser'},pct(ser[n-1].payback))+el('text',{x:xe+12,y:ye+16,class:'lab-s'},'payback now');
  s+=el('text',{x:xe+12,y:Y(ser[n-1].coverage)+4,class:'lab-s'},'burn '+pct(ser[n-1].coverage,2))}
 else s+=el('text',{x:xe-4,y:ye+22,'text-anchor':'end',class:'lab'},pct(ser[n-1].payback)+' now');
 s+=el('text',{x:ml+6,y:mt-10,class:'lab-s'},'↑ break-even at 100%');
 box.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" height="'+H+'" role="img" aria-label="'+esc(box.dataset.aria)+'">'+s+'<line class="xh" x1="0" x2="0" y1="'+mt+'" y2="'+(H-mb)+'" stroke="var(--ink)" opacity="0"/></svg>';
 interact(box,n,X,i=>Y(ser[i].payback),i=>{const p=ser[i];return '<b>'+dlab(p.date)+' '+p.date.slice(0,4)+'</b><br><span class="sw" style="background:var(--teal)"></span>Payback '+pct(p.payback)+
  '<br><span class="sw" style="background:var(--terra)"></span>Burn '+pct(p.coverage,2)+'<br>Break-even '+p.multiple.toFixed(1)+'×'})}

// small multiples: one series, its last value and its low, with a tooltip
function spark(box){const k=box.dataset.key,src=D[box.dataset.src],mul=+box.dataset.mul,dp=+box.dataset.dp,pre=box.dataset.pre||'',unit=box.dataset.unit||'',teal=box.dataset.color=='teal',
 P=src.filter(p=>p[k]!=null);if(P.length<2){box.closest('.mult').remove();return}
 const W=box.clientWidth,H=150,ml=4,mr=62,mt=16,mb=22,n=P.length,vals=P.map(p=>p[k]*mul),mx=Math.max(...vals)*1.12||1,
 X=i=>ml+i/(n-1)*(W-ml-mr),Y=v=>mt+(1-Math.max(v,0)/mx)*(H-mt-mb),f=v=>pre+fmt(v,dp)+unit;let ln='';
 vals.forEach((v,i)=>ln+=(i?'L':'M')+X(i).toFixed(1)+','+Y(v).toFixed(1));
 let s=el('line',{x1:ml,x2:W-mr,y1:Y(0),y2:Y(0),stroke:'var(--rule)'});
 if(box.dataset.ref){const r=+box.dataset.ref*mul;s+=el('line',{x1:ml,x2:W-mr,y1:Y(r),y2:Y(r),stroke:'var(--muted)','stroke-dasharray':'2 3'})}
 s+=el('path',{d:ln+'L'+X(n-1)+','+Y(0)+'L'+X(0)+','+Y(0)+'Z',fill:teal?'var(--teal-soft)':box.dataset.color=='terra'?'var(--terra-soft)':'var(--gray-fill)',opacity:.85,class:'area'});
 s+=el('path',{d:ln,fill:'none',stroke:teal?'var(--teal)':box.dataset.color=='terra'?'var(--terra)':'var(--ink-2)','stroke-width':1.75,'stroke-linejoin':'round',class:'draw',pathLength:1});
 const mi=vals.indexOf(Math.min(...vals));
 s+=el('circle',{cx:X(n-1),cy:Y(vals[n-1]),r:3.5,fill:teal?'var(--teal)':'var(--ink)'})+el('text',{x:X(n-1)+7,y:Y(vals[n-1])+4,class:'lab'},f(vals[n-1]));
 if(mi<n-3){s+=el('circle',{cx:X(mi),cy:Y(vals[mi]),r:2.5,fill:'var(--card)',stroke:'var(--muted)'})+((ly,x)=>el('text',ly<H-mb?{x:Math.max(x,28),y:ly,'text-anchor':'middle','font-size':10.5}:x<72?{x:52,y:H-4,'text-anchor':'start','font-size':10.5}:x>W-mr-72?{x:W-mr-52,y:H-4,'text-anchor':'end','font-size':10.5}:{x,y:H-4,'text-anchor':'middle','font-size':10.5},'low '+f(vals[mi])))(Y(vals[mi])+15,X(mi))}
 s+=el('text',{x:ml,y:H-4},dlab(P[0].date))+el('text',{x:W-mr,y:H-4,'text-anchor':'end'},dlab(P[n-1].date));
 box.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" height="'+H+'" role="img" aria-label="'+esc(box.dataset.aria||'')+'">'+s+'<line class="xh" x1="0" x2="0" y1="'+mt+'" y2="'+(H-mb)+'" stroke="var(--ink)" opacity="0"/></svg>';
 interact(box,n,X,i=>Y(vals[i]),i=>'<b>'+dlab(P[i].date)+' '+P[i].date.slice(0,4)+'</b><br>'+pre+fmt(vals[i],dp+1)+unit)}

// every epoch, one column each (canvas), with the committed band after the freeze, mainnet checks and the live strip
const TD=D.tape;if(TD){const N=x=>Number(x)/1e24,cv=$('#tape'),cx=cv.getContext('2d'),box=cv.parentElement,tip=tipFor(box),
 E=TD.E.map(r=>({s:r[0],e:r[1],p:r[2],t:r[3],mint:N(r[4]),burn:N(r[5]),buy:r[6]==null?null:N(r[6]),lump:r[7],raw:r}));
 E.forEach(d=>{d.share=(d.burn+(d.lump?0:Math.max(d.buy||0,0)))/d.mint});
 const hist=E.filter(d=>d.e<=TD.snap),fut=E.filter(d=>d.e>TD.snap),slots=Math.max(0,fut.length,...TD.rounds.map(r=>r.n)),RW=100,
 sorted=hist.filter(d=>!d.lump).map(d=>d.share).sort((a,b)=>a-b),ymax=Math.ceil(sorted[Math.floor(sorted.length*.985)]*1.15*10)/10,
 roll=hist.map((d,i)=>{if(i<RW-1)return null;let a=0,m=0;for(let j=i-RW+1;j<=i;j++){if(hist[j].buy==null)return null;a+=hist[j].burn+(hist[j].lump?0:hist[j].buy);m+=hist[j].mint}return a/m}),
 idx=t=>{const k=hist.findIndex(d=>d.t>=t);return k<0?hist.length-1:k},all=hist.concat(fut),
 marks=[[hist.findIndex(d=>d.buy>0),'buybacks begin'],[hist.findIndex(d=>d.lump),'transfer from another wallet, excluded'],
  [idx(Date.UTC(2026,9,27)/1000),'swaps go private'],[hist.length-1,'forecasts frozen']].filter(m=>m[0]>=0),
 when=t=>new Date(t*1000).toLocaleString('en-GB',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC'})+' UTC';
 $('#tape-clip').textContent=Math.round(ymax*100)+'%';
 let sel=hist.length-1,pin=false,w=0,h=0,g,C={},gk=1;
 function layout(){const r=cv.getBoundingClientRect(),dpr=window.devicePixelRatio||1;w=r.width;h=r.height;cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr);cx.setTransform(dpr,0,0,dpr,0,0);
  const ml=34,top=w<560?12:62,bot=h-22,futW=slots?Math.max(w<560?44:80,(w-ml)*.13):0,gap=slots?12:0,hw=w-ml-futW-gap;
  g={ml,top,bot,hw,fx:ml+hw+gap,sw:slots?futW/slots:0,cw:hw/hist.length,y:v=>bot-Math.min(v,ymax)/ymax*(bot-top)}}
 const xOf=i=>i<hist.length?g.ml+i*g.cw:g.fx+(i-hist.length)*g.sw,cwOf=i=>i<hist.length?g.cw:g.sw;
 function draw(quiet){C={ink:V('--ink'),ink2:V('--ink-2'),muted:V('--muted'),rule:V('--rule-2'),teal:V('--teal'),terra:V('--terra'),bad:V('--bad'),paper:V('--card')};
  cx.clearRect(0,0,w,h);cx.font='11px '+V('--sans');cx.textBaseline='middle';
  for(let v=0;v<ymax+1e-9;v+=.1){cx.fillStyle=C.rule;cx.fillRect(g.ml,Math.round(g.y(v)),w-g.ml,1);cx.fillStyle=C.muted;cx.textAlign='right';cx.fillText(Math.round(v*100)+'%',g.ml-8,g.y(v))}
  TD.rounds.slice().sort((a,b)=>b.n-a.n).forEach(r=>{const ww=r.n*g.sw,y1=g.y(r.hi),y0=g.y(r.lo);cx.globalAlpha=.14;cx.fillStyle=C.teal;cx.fillRect(g.fx,y1,ww,y0-y1);
   cx.globalAlpha=.7;cx.strokeStyle=C.teal;cx.lineWidth=1;cx.strokeRect(g.fx+.5,y1+.5,ww-1,y0-y1-1);cx.globalAlpha=1});
  all.forEach((d,i)=>{const x=xOf(i),c=cwOf(i),cw=Math.max(.6,c-(i<hist.length?(c>3?.8:0):2));
   if(d.lump){cx.globalAlpha=.3;cx.fillStyle=C.muted;cx.fillRect(x,g.top,cw,g.bot-g.top);cx.globalAlpha=1;return}
   const yb=g.y(d.burn/d.mint*gk),yt=g.y(d.share*gk);cx.fillStyle=C.terra;cx.fillRect(x,yb,cw,g.bot-yb);cx.globalAlpha=.88;cx.fillStyle=C.teal;cx.fillRect(x,yt,cw,yb-yt);cx.globalAlpha=1;
   if(d.share>ymax){cx.fillStyle=C.ink;cx.fillRect(x,g.top,cw,2)}if(d.buy<0){cx.fillStyle=C.bad;cx.fillRect(x-1,g.bot+3,Math.max(3,cw),3)}});
  for(let j=fut.length;j<slots;j++){cx.fillStyle=C.muted;cx.fillRect(g.fx+j*g.sw+1,g.bot-1,g.sw-2,1)}
  const line=()=>{cx.beginPath();let on=false;roll.forEach((v,i)=>{if(v==null)return;const x=xOf(i)+g.cw/2,y=g.y(v*gk);on?cx.lineTo(x,y):cx.moveTo(x,y);on=true})};
  line();cx.strokeStyle=C.paper;cx.lineWidth=4;cx.globalAlpha=.9;cx.stroke();cx.globalAlpha=1;line();cx.strokeStyle=C.ink;cx.lineWidth=1.75;cx.stroke();
  cx.fillStyle=C.ink;cx.fillRect(g.ml,g.bot,w-g.ml,1);if(slots){cx.fillRect(g.fx-6,g.top-4,1,g.bot-g.top+4)}
  marks.forEach((m,k)=>{const x=Math.round(xOf(m[0])),y0=w<560?g.top-6:6+k*13;cx.globalAlpha=.45;cx.fillStyle=C.muted;
   for(let y=y0;y<g.bot;y+=4)cx.fillRect(x,y,1,2);cx.globalAlpha=1;
   if(w>=560){cx.fillStyle=C.ink2;cx.textAlign=x>w*.7?'right':'left';cx.fillText(m[1],x+(x>w*.7?-5:5),6+k*13)}});
  if(slots&&w>=560&&TD.rounds.length){cx.fillStyle=C.teal;cx.textAlign='left';cx.fillText('committed band',g.fx,g.y(Math.max(...TD.rounds.map(r=>r.hi)))-9)}
  const x=xOf(sel),c=cwOf(sel);cx.fillStyle=C.ink;cx.globalAlpha=.75;cx.fillRect(Math.round(x+c/2),g.top-4,1,g.bot-g.top+8);cx.globalAlpha=1;
  cx.fillStyle=C.muted;cx.textAlign='center';let pm=-1;hist.forEach((d,i)=>{const m=new Date(d.t*1000),k=m.getUTCFullYear()*12+m.getUTCMonth();
   if(pm>=0&&k!==pm&&(w>=560||m.getUTCMonth()%2==0)){const x=xOf(i);cx.fillRect(x,g.bot+1,1,4);cx.fillText(MON[m.getUTCMonth()],x,h-8)}pm=k});if(!quiet)read()}
 const cell=(k,v)=>'<div><dt>'+k+'</dt><dd>'+v+'</dd></div>';
 function read(){const d=all[sel];$('#read').innerHTML='<h4>Epoch ending '+when(d.t)+(sel>=hist.length?'<small>closed after the forecasts were frozen</small>':pin?'':'<small>hover, tap or use the arrow keys</small>')+'</h4><dl>'+
  cell('Minted',fmt(d.mint)+'<small>NEAR</small>')+cell('Burnt in gas fees',fmt(d.burn,1)+'<small>NEAR</small>')+
  (d.buy==null?cell('Buyback gain','not cached'):d.lump?cell('Moved in from another wallet, excluded',fmt(d.buy)+'<small>NEAR</small>'):cell('Buyback gain',fmt(d.buy)+'<small>NEAR</small>')+cell('Share of mint matched',pct(d.share)))+
  cell('Block heights','<span class="hts">'+fmt(d.s)+' to '+fmt(d.e)+'</span>')+'</dl>'}
 function tipAt(i){const d=all[i];tip.innerHTML='<b>Epoch ending '+when(d.t)+'</b><br>Minted '+fmt(d.mint)+' NEAR<br><span class="sw" style="background:var(--terra)"></span>Burnt '+fmt(d.burn,1)+' · '+pct(d.burn/d.mint,2)+
  (d.buy==null?'':'<br><span class="sw" style="background:var(--teal)"></span>'+(d.lump?'Transfer in, excluded ':'Buyback gain ')+fmt(d.buy)+(d.lump?'':' · '+pct(Math.max(d.buy,0)/d.mint)));
  tip.classList.add('on');placeTip(box,tip,xOf(i)+cwOf(i)/2,Math.max(g.y(d.share),g.top))}
 function pick(e){const px=e.clientX-cv.getBoundingClientRect().left;const i=px<g.fx-6?Math.floor((px-g.ml)/g.cw):hist.length+Math.floor((px-g.fx)/g.sw);
  return Math.max(0,Math.min(px<g.fx-6?hist.length-1:all.length-1,i))}
 cv.addEventListener('pointermove',e=>{const i=pick(e);tipAt(i);if(!pin){sel=i;draw()}});cv.addEventListener('pointerdown',e=>{sel=pick(e);pin=true;draw();tipAt(sel)});
 cv.addEventListener('pointerleave',()=>{tip.classList.remove('on');if(!pin){sel=hist.length-1;draw()}});cv.addEventListener('blur',()=>tip.classList.remove('on'));
 cv.addEventListener('keydown',e=>{const k={ArrowLeft:-1,ArrowRight:1}[e.key];if(k){pin=true;sel=Math.max(0,Math.min(all.length-1,sel+k*(e.shiftKey?10:1)));draw();tipAt(sel);e.preventDefault()}});
 new ResizeObserver(()=>{layout();draw()}).observe(cv);layout();draw();REDRAW.push(()=>draw());GROW=k=>{gk=k;draw(true)};
 // check one epoch against mainnet, in this browser
 const ARCH='https://archival-rpc.mainnet.fastnear.com',LIVE='https://rpc.mainnet.fastnear.com',BUY='buybacks.multisignature.near',chk=$('#check'),
 rpc=async(u,method,params)=>{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method,params})});
  if(!r.ok)throw new Error('the endpoint answered '+r.status);const j=await r.json();if(j.error)throw new Error(j.error.cause&&j.error.cause.name||j.error.message);return j.result},
 near=x=>fmt(Number(x/10n**18n)/1e6,3),
 bal=async hh=>{try{return BigInt((await rpc(ARCH,'query',{request_type:'view_account',block_id:hh,account_id:BUY})).amount)}catch(e){if(/UNKNOWN_ACCOUNT/.test(e.message))return 0n;throw e}};
 function show(st){chk.innerHTML='<h4>Epoch ending '+when(st.d.t)+', checked against mainnet</h4><div class="tw"><table class="tbl"><tr><th>Quantity</th><th class="r">Mainnet, just now</th><th class="r">Committed cache</th><th class="r">Result</th></tr>'+
  st.rows.map(r=>'<tr><td>'+r.k+'</td><td class="r">'+(r.a==null?'<span class="wait">reading</span>':near(r.a)+' NEAR')+'</td><td class="r">'+near(r.b)+' NEAR</td><td class="r">'+(r.a==null?'':r.a===r.b?'<span class="eq">Equal to the yoctoNEAR</span>':'<span class="ne">Different</span>')+'</td></tr>').join('')+
  '</table></div>'+(st.verdict?'<p class="verdict'+(st.ok?'':' no')+'">'+esc(st.verdict)+'</p>':'')+
  '<p>Read from the headers of blocks '+st.d.p+', '+st.d.s+' and '+st.d.e+(st.rows.length>2?' and the balance of '+BUY+' at the first and last of them':'')+', on '+ARCH.slice(8)+'.</p>'}
 async function verify(i){const d=all[i],bs=[...document.querySelectorAll('.vrow button')];bs.forEach(b=>b.disabled=true);sel=i;pin=true;draw();
  const st={d,rows:[{k:'Minted',a:null,b:BigInt(d.raw[4])},{k:'Burnt in gas fees',a:null,b:BigInt(d.raw[5])}]};
  if(d.raw[6]!=null)st.rows.push({k:d.lump?'Buyback account change':'Buyback gain',a:null,b:BigInt(d.raw[6])});show(st);
  try{const B={};for(const [k,hh] of [['prev',d.p],['first',d.s],['last',d.e]]){const b=await rpc(ARCH,'block',{block_id:hh});
    B[k]={sup:BigInt(b.header.total_supply),burnt:b.chunks.filter(c=>c.height_included===hh).reduce((a,c)=>a+BigInt(c.balance_burnt),0n)}}
   st.rows[0].a=B.first.sup-B.prev.sup+B.first.burnt;st.rows[1].a=B.first.burnt+B.first.sup-B.last.sup;show(st);
   if(st.rows[2]){st.rows[2].a=await bal(d.e)-await bal(d.p)}
   st.ok=st.rows.every(r=>r.a===r.b);st.verdict=st.ok?'Mainnet and the committed cache agree for this epoch.':'The cache does not match mainnet for this epoch.'}
  catch(err){st.ok=false;st.verdict='Could not finish: '+err.message+'. The free endpoint limits requests; try again in a minute.'}
  show(st);bs.forEach(b=>b.disabled=false)}
 $('#vsel').addEventListener('click',()=>verify(sel));$('#vrnd').addEventListener('click',()=>verify(Math.floor(Math.random()*all.length)));
 // what mainnet says right now: the build painted the cached values; a live read overwrites them
 const set=(id,v)=>{const e=document.getElementById(id);if(e)e.innerHTML=v},msg=$('#lmsg'),sub=$('#lsub'),fail=$('#lfail');
 async function now(){try{const b=await rpc(LIVE,'block',{finality:'final'}),a=await rpc(LIVE,'query',{request_type:'view_account',finality:'final',account_id:BUY});
   const hgt=b.header.height,bl=BigInt(a.amount),gain=TD.bal?bl-BigInt(TD.bal):null,ep=(hgt-TD.snap)/TD.len;
   set('l-h',fmt(hgt));set('l-s',fmt(Number(BigInt(b.header.total_supply)/10n**24n)));set('l-b',fmt(Number(bl/10n**24n)));
   if(gain!=null&&TD.rounds.length){set('l-g',(gain<0n?'':'+')+fmt(Number(gain/10n**21n)/1e3));set('l-gs','NEAR in '+ep.toFixed(1)+' epochs')}
   msg.textContent='Mainnet, live';sub.textContent='Read by your browser just now, block '+fmt(hgt);fail.hidden=true;
   document.querySelectorAll('.rlive').forEach(s=>{const n=+s.dataset.n,h0=+s.dataset.h,e2=(hgt-h0)/TD.len;s.textContent=e2>=n?'Live: the window has closed on mainnet. The next rebuild scores it.':
    'Live: about '+e2.toFixed(1)+' of '+n+' epochs elapsed'+(gain!=null&&h0==TD.snap?', buyback gain so far '+fmt(Number(gain/10n**21n)/1e3)+' NEAR':'')+'.'})}
  catch(err){if(!msg.dataset.ok){fail.hidden=false;sub.textContent=sub.dataset.cache}return}
  msg.dataset.ok=1}
 now();setInterval(()=>{if(!document.hidden)now()},60000)}

// lever calculator
const CA=$('.calc');if(CA){const q=id=>document.getElementById(id),v=q('s-vol'),c=q('s-cap'),i=q('s-iss'),K=CA.dataset,capNow=+K.cap,iss0=+K.iss;
 function upd(){[v,c,i].forEach(r=>r.style.setProperty('--p',((r.value-r.min)/(r.max-r.min)*100)+'%'));
  const vol=+v.value,cap=+c.value/100,iss=+i.value,sc=iss0/iss,burn=+K.burn*sc,bb=+K.buy*vol*(cap/capNow)*sc,p=burn+bb;
  q('o-vol').textContent=vol.toFixed(1)+'× today';q('o-cap').textContent=Math.round(cap*100)+'%';q('o-iss').textContent=iss.toFixed(1)+'% a year';
  q('o-pay').textContent=pct(p);q('o-b').textContent=pct(burn,2);q('o-bb').textContent=pct(bb,2);q('o-nd').textContent=fmt(+K.burnd+(+K.buyd)*vol*(cap/capNow));
  q('o-mult').textContent=p>=1?'Met':(1/p).toFixed(1)+'×';q('o-note').textContent=p>=1?'burn plus buybacks equal or exceed issuance':'flows must grow this much';
  const b1=Math.min(burn,1),p1=Math.min(p,1);q('g1').style.width=b1*100+'%';q('g2').style.left=b1*100+'%';q('g2').style.width=Math.max(0,p1-b1)*100+'%';
  q('g2').style.borderRadius=p>=1?'0 6px 6px 0':'0'}
 CA.addEventListener('input',upd);q('s-reset').onclick=()=>{v.value=1;c.value=capNow*100;i.value=iss0;upd()};c.value=capNow*100;upd()}

// copy buttons on commands
document.querySelectorAll('pre[data-copy]').forEach(p=>{if(!navigator.clipboard)return;const b=document.createElement('button');b.type='button';b.textContent='Copy';
 b.addEventListener('click',()=>navigator.clipboard.writeText(p.dataset.copy).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1200)},()=>{}));p.appendChild(b)});

function drawAll(){drawRuler();drawPayback();document.querySelectorAll('.spark').forEach(spark)}
drawAll();let rz,lastW=innerWidth;addEventListener('resize',()=>{if(innerWidth===lastW)return;lastW=innerWidth;clearTimeout(rz);rz=setTimeout(drawAll,120)});
document.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)d.querySelectorAll('.spark').forEach(spark)}));
REDRAW.push(drawAll);

// paper and ink
(function(){const b=$('#theme');let saved=null;try{saved=localStorage.getItem('cov-theme')}catch(e){}
 if(saved==='dark'||saved==='light')root.dataset.theme=saved;
 const mq=matchMedia('(prefers-color-scheme: dark)'),cur=()=>root.dataset.theme||(mq.matches?'dark':'light'),
 lab=()=>{b.querySelector('span').textContent=cur()==='dark'?'Paper':'Ink';b.setAttribute('aria-pressed',cur()==='dark')};lab();
 b.onclick=()=>{root.dataset.theme=cur()==='dark'?'light':'dark';try{localStorage.setItem('cov-theme',root.dataset.theme)}catch(e){}lab();REDRAW.forEach(f=>f())};
 mq.addEventListener&&mq.addEventListener('change',()=>{lab();REDRAW.forEach(f=>f())})})();

// chapter index and reading progress
(function(){const chs=[...document.querySelectorAll('.chapter')],lis=[...document.querySelectorAll('#idx li')],mi=$('.mobile-index details');
 function on(){const mid=innerHeight*.35;let act=0;
  chs.forEach((c,i)=>{const r=c.getBoundingClientRect(),f=Math.max(0,Math.min(1,(mid-r.top)/r.height));if(lis[i]){lis[i].querySelector('i').style.width=(f*100)+'%';lis[i].classList.toggle('done',f>=1)}if(r.top<mid)act=i});
  lis.forEach((l,i)=>{l.classList.toggle('on',i===act);const a=l.querySelector('a');i===act?a.setAttribute('aria-current','true'):a.removeAttribute('aria-current')});
  const r=chs[act].getBoundingClientRect(),f=Math.max(0,Math.min(1,(mid-r.top)/r.height));
  $('#mi-t').textContent=String(act+1).padStart(2,'0')+' '+chs[act].dataset.t;$('#mi-n').textContent=(act+1)+' / '+chs.length;$('#mi-p').style.width=((act+f)/chs.length*100)+'%'}
 addEventListener('scroll',on,{passive:true});addEventListener('resize',on);on();
 mi&&mi.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>mi.open=false))})();

// motion: only when the reader allows it and the browser can observe. Without this block every element is in its final state.
(function(){if(navigator.webdriver||matchMedia('(prefers-reduced-motion: reduce)').matches||!('IntersectionObserver' in window)||!window.requestAnimationFrame)return;
 const TW=new Set(),ease=k=>1-Math.pow(1-k,3);let raf=0,seen=false;
 function loop(now){raf=0;TW.forEach(t=>{const k=Math.max(0,Math.min(1,(now-t.t0)/t.dur));t.fn(ease(k));if(k>=1){TW.delete(t);t.end&&t.end()}});if(TW.size)raf=requestAnimationFrame(loop)}
 const tween=(dur,delay,fn,end)=>{const t={t0:performance.now()+delay,dur,fn,end};TW.add(t);fn(0);if(!raf)raf=requestAnimationFrame(loop);return t},
  settle=all=>{const now=performance.now();TW.forEach(t=>{if(all||now-t.t0>t.dur+400){TW.delete(t);t.fn(1);t.end&&t.end()}})};
 // count-up: the first number in the element's first text node runs from 0 to its value, then the original text node is put back untouched
 function count(elm,delay,end){const tw=document.createTreeWalker(elm,NodeFilter.SHOW_TEXT);let n;while((n=tw.nextNode())&&!/\d/.test(n.nodeValue));
  if(!n){end&&end();return}const txt=n.nodeValue,m=txt.match(/\d[\d,]*(\.\d+)?/),v=parseFloat(m[0].replace(/,/g,'')),dp=m[1]?m[1].length-1:0,gp=m[0].indexOf(',')>=0,
  pre=txt.slice(0,m.index),post=txt.slice(m.index+m[0].length),wrap=document.createElement('span'),inner=document.createElement('span');
  wrap.className='cu';wrap.dataset.v=txt;wrap.appendChild(inner);n.replaceWith(wrap);
  tween(1500,delay,k=>{inner.textContent=pre+(v*k).toLocaleString('en-US',{minimumFractionDigits:dp,maximumFractionDigits:dp,useGrouping:gp})+post},
   ()=>{if(wrap.isConnected)wrap.replaceWith(n);end&&end()})}
 const CNT=[...document.querySelectorAll('.pull .big,.stat .v,.scale-legend b,.audit .v,.out .res .big')],
  LEAF='.ruler,.live,.scale,.ch-head,.pull,.stat,.fig,.mult,.audit>div,.calc,.mlist>div,.round,.judging,.pt,div.verdict,.step,.hashbox,.sec,.notes>div,.colophon',
  rv=[];
 document.querySelectorAll(LEAF).forEach(e=>{if(!e.closest('.rv'))e.classList.add('rv')});
 document.querySelectorAll('.grid12>div,.side').forEach(e=>{if(!e.classList.contains('rv')&&!e.closest('.rv')&&!e.querySelector('.rv'))e.classList.add('rv')});
 document.querySelectorAll('.rv').forEach(e=>{const sib=[...e.parentElement.children].filter(x=>x.classList.contains('rv'));e.style.setProperty('--d',Math.min(sib.indexOf(e)*.09,.45).toFixed(2)+'s');rv.push(e)});
 function show(t,now){if(t.classList.contains('in'))return;t.classList.add('in');io.unobserve(t);
  CNT.forEach(c=>{if(!c.dataset.cd&&t.contains(c)){c.dataset.cd=1;if(!now)count(c,parseFloat(t.style.getPropertyValue('--d'))*1000+150)}});
  if(GROW&&t.querySelector('#tape')){if(now)GROW(1);else tween(1300,250,GROW)}}
 const io=new IntersectionObserver(es=>{seen=true;es.forEach(en=>{if(en.isIntersecting)show(en.target);else if(en.boundingClientRect.bottom<0&&en.target.getClientRects().length)show(en.target,true)})},{rootMargin:'0px 0px -6% 0px'});
 // the hero: 12.0% and 8.4x count up once the fonts are in, then the struck-out burn-only multiple is crossed out
 const hn=[...document.querySelectorAll('.hero h1 em')],strike=document.querySelector('.hero h1 s');let hs=false;
 const cross=()=>{strike&&strike.classList.add('drawn')};
 root.classList.add('anim');rv.forEach(e=>io.observe(e));
 const hero=()=>{if(hs)return;hs=true;let left=hn.length;if(!left)cross();hn.forEach((e,i)=>count(e,350+i*250,()=>{if(!--left)setTimeout(cross,120)}))};hero();
 // never leave anything hidden: after 2.5 s, whatever is in or above the viewport is shown and stuck tweens are finished; with no observer callback at all, motion is dropped
 setTimeout(()=>{hero();if(!seen){root.classList.remove('anim');settle(true);cross();return}
  rv.forEach(t=>{if(!t.classList.contains('in')&&t.getClientRects().length&&t.getBoundingClientRect().top<innerHeight)show(t)});settle(false);
  setTimeout(()=>{settle(false);cross()},1600)},2500);
 addEventListener('beforeprint',()=>{rv.forEach(t=>show(t,true));settle(true);cross()})})();
"""

CHARTS = [  # key, title, subtitle, multiplier, unit, decimals, source, one sentence on what it shows, colour
    ("multiple", "Distance to break-even", "Multiple of today's burn plus buybacks that equals issuance", 1, "×", 1,
     "mint / (burn + buyback gain)",
     lambda s: f"Flows would have to grow {s['multiple']:.1f}× at constant issuance; on burn alone {s['burn_only_multiple']:.0f}×.", "ink"),
    ("buyback_per_day", "Buybacks", "NEAR added to the buyback account per day", 1, "", 0,
     "view_account balance of buybacks.multisignature.near at each epoch's last block, differenced",
     lambda s: f"The account gains {s['buyback_per_day']:,.0f} NEAR a day; its balance fell in {s['buyback_outflow_epochs']} of {s['buyback_epochs']} epochs.", "teal"),
    ("burn_per_day", "Burn", "NEAR burnt in gas fees per day (exact)", 1, "", 0,
     "block header total_supply: supply(first block) - supply(last block) + burnt(first block), per epoch",
     lambda s: f"Gas fees burn {s['burn_per_day']:,.0f} NEAR a day against {s['mint_per_day']:,.0f} minted.", "terra"),
    ("coverage", "Burn-only coverage", "Fee burn as % of issuance (exact)", 100, "%", 2,
     "burn / mint, both from block header total_supply",
     lambda s: f"Burn alone equals {100 * s['burn_coverage']:.2f}% of issuance, which is what a fee-burn dashboard reports.", "terra"),
    ("mint_per_day", "Mint", "NEAR minted to validators per day (exact)", 1, "", 0,
     "block header total_supply: supply(first block) - supply(last block of previous epoch) + burnt(first block)",
     lambda s: f"Validators are minted {s['mint_per_day']:,.0f} NEAR a day, {100 * s['realized_inflation']:.2f}% of supply a year.", "ink"),
    ("utilization", "Block utilization", "Gas used as % of gas limit, sampled", 100, "%", 2,
     "chunk gas_used / gas_limit over 3 seeded random heights per epoch",
     lambda s: f"Blocks are {100 * s['utilization']:.2f}% full, so burn is limited by demand for block space, not by capacity.", "ink"),
]

ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def _d(s):
    return datetime.datetime.strptime(s[:10], "%Y-%m-%d")


def dshort(s):
    d = _d(s)
    return f"{d.day} {MONTHS[d.month - 1][:3]}"


def dlong(s):
    d = _d(s)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def frac(x):
    """0.12 -> 'an eighth', 0.0092 -> 'a hundredth': a share as words, close enough to say in a headline."""
    n = 1 / x
    r = round(n)
    words = {2: "a half", 3: "a third", 4: "a quarter", 5: "a fifth", 6: "a sixth", 7: "a seventh", 8: "an eighth",
             9: "a ninth", 10: "a tenth", 11: "an eleventh", 12: "a twelfth"}
    if r in words and abs(n - r) / r < .08:
        return words[r]
    for p, w in ((20, "a twentieth"), (50, "a fiftieth"), (100, "a hundredth"), (1000, "a thousandth")):
        if abs(n / p - 1) < .15:
            return w
    return f"one part in {r}"


def provenance():
    """When and where this build ran, with a link to the exact run log on GitHub Actions."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    env = os.environ
    if env.get("GITHUB_ACTIONS") == "true" and all(env.get(k) for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")):
        return dict(utc=now, ci=True, url=f"{env['GITHUB_SERVER_URL']}/{env['GITHUB_REPOSITORY']}/actions/runs/{env['GITHUB_RUN_ID']}")
    return dict(utc=now, ci=False, url=None)


def prov_html(p, what="Recorded"):
    e = html.escape
    if p.get("ci") and p.get("url"):
        head = f"<b>{what} by GitHub Actions at {e(p['utc'])}</b>: <a href='{e(p['url'])}'>the log of that run</a>."
    else:
        head = f"<b>{what} locally at {e(p['utc'])}</b>."
    return f"<p class='prov'>{head} <a href='{WORKFLOW}'>Every run's full log is public.</a></p>"


def term(cmd, lines=(), note=None, copy=True):
    """A terminal transcript: the command and its real output, nothing else."""
    e = html.escape
    out = []
    for ln in lines:
        k = "ok" if (" PASS" in ln or ln.startswith("RESULT ") or ln.endswith("-> HIT") or ": MATCH" in ln or ln.startswith("DOCS ")) else \
            "no" if (" FAIL" in ln or "FALSIFIED" in ln.split("->")[-1] or ln.endswith("-> MISS") or "MISMATCH" in ln) else ""
        out.append(f"<span class='{k}'>{e(ln)}</span>" if k else e(ln))
    body = f"<span class='p'>$ </span>{e(cmd)}" + ("\n<span class='c'>" + e(note) + "</span>" if note else "") + \
           ("\n" + "\n".join(out) if out else "")
    return f"<pre class='term'{' data-copy=' + chr(39) + e(cmd) + chr(39) if copy else ''}>{body}</pre>"


# ---- the run.py transcript: recorded in this process and written into the page when run.py exits ----
MARK = ("<!--CAP:{0}-->", "<!--/CAP:{0}-->")


class _Tee:
    def __init__(self, real):
        self.real, self.parts = real, []

    def write(self, x):
        self.parts.append(x)
        return self.real.write(x)

    def flush(self):
        self.real.flush()

    def __getattr__(self, k):
        return getattr(self.real, k)


def _between(page, key, new):
    a, b = MARK[0].format(key), MARK[1].format(key)
    i, j = page.find(a), page.find(b)
    return page if i < 0 or j < i else page[:i + len(a)] + new + page[j:]


def hash_html(expected, printed):
    if printed is None:
        verdict = "<span class='match wait'>This build's printed hash appears here when run.py finishes</span>"
    elif printed == expected:
        verdict = "<span class='match'>Match: this build printed the expected hash</span>"
    else:
        verdict = "<span class='match no'>Different: the printed hash does not match out/results.json</span>"
    return (f"<div class='hrow'><span>Expected: sha256 of <code>out/results.json</code>, as README.md states</span><code>{expected}</code></div>"
            f"<div class='hrow'><span>This build: the <code>RESULT</code> line <code>python3 run.py</code> printed</span>"
            f"<code{'' if printed in (None, expected) else ' class=x'}>{printed or '&ndash;'}</code></div>{verdict}")


def _finish(tee):
    sys.stdout = tee.real
    try:
        lines = "".join(tee.parts).splitlines()
        res = [ln for ln in lines if ln.startswith("RESULT sha256=")]
        path = os.path.join(HERE, "dist", "index.html")
        if not res or not os.path.exists(path):
            return
        page = open(path, encoding="utf-8").read()
        expected = hashlib.sha256(open(os.path.join(HERE, "out", "results.json"), "rb").read()).hexdigest()
        printed = res[-1].split("=", 1)[1].strip()
        page = _between(page, "run", term("python3 run.py", lines, "... summary values printed above, as in out/results.json") + prov_html(provenance()))
        page = _between(page, "hash", hash_html(expected, printed))
        open(path, "w", encoding="utf-8").write(page)
    except Exception as err:  # the page stays valid, with the fallback text, if this fails
        print(f"dashboard: transcript not written ({err})", file=sys.stderr)


def _capture():
    """Record what run.py prints after render(): its ledger lines and the RESULT line."""
    main = getattr(sys.modules.get("__main__"), "__file__", "") or ""
    if os.path.basename(main) != "run.py" or isinstance(sys.stdout, _Tee):
        return
    tee = _Tee(sys.stdout)
    sys.stdout = tee
    atexit.register(_finish, tee)


def _recorded(name):
    try:
        return json.load(open(os.path.join(HERE, "out", name), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def track(L, s):
    """One round's committed payback interval on a common scale, its midpoint, and the outcome once it exists."""
    c = L["claims"]["payback"]
    top = max(c["hi"], c["actual"] or 0) * 1.15
    x = lambda v: f"{100 * v / top:.2f}%"
    out = (f"<div class='band' role='img' aria-label='Committed payback {100 * c['lo']:.1f}% to {100 * c['hi']:.1f}%'>"
           f"<div class='ax'></div><div class='b' style='left:{x(c['lo'])};width:{100 * (c['hi'] - c['lo']) / top:.2f}%'></div>"
           f"<div class='m' style='left:{x(c['mid'])}'><span>mid {100 * c['mid']:.1f}%</span></div>"
           f"<span class='lbl' style='left:{x(c['lo'])}'>{100 * c['lo']:.1f}%</span><span class='lbl' style='left:{x(c['hi'])}'>{100 * c['hi']:.1f}%</span>")
    if c["actual"] is not None:
        out += f"<div class='a' style='left:{x(c['actual'])};background:var(--{'teal' if c['verdict'] == 'HIT' else 'bad'})' title='actual {100 * c['actual']:.1f}%'></div>"
    return out + "</div>"


def fan(rows):
    """Per-epoch burn: the committed 10% to 90% band, its median, and the outcomes so far."""
    n, W, H, L, B, T = len(rows), 300, 96, 30, 16, 6
    top = max(max(r["q90"] for r in rows), max((r["actual"] or 0) for r in rows)) * 1.1
    x = lambda i: L + (i + .5) / n * (W - L - 4)
    y = lambda v: H - B - v / top * (H - T - B)
    band = " ".join(f"{x(i):.1f},{y(r['q90']):.1f}" for i, r in enumerate(rows)) + " " + \
        " ".join(f"{x(i):.1f},{y(r['q10']):.1f}" for i, r in reversed(list(enumerate(rows))))
    out = f"<svg class='fan' viewBox='0 0 {W} {H}' role='img' aria-label='NEAR burnt per epoch against the committed band'>"
    for k in range(3):
        v = top * k / 2
        out += (f"<line x1='{L}' x2='{W - 4}' y1='{y(v):.1f}' y2='{y(v):.1f}' stroke='var(--{'rule-2' if k else 'rule'})'/>"
                f"<text x='{L - 5}' y='{y(v) + 3.5:.1f}' text-anchor='end' fill='var(--muted)' font-size='10'>{v:.0f}</text>")
    out += f"<polygon points='{band}' fill='var(--terra)' opacity='.16'/>"
    med = " ".join(f"{x(i):.1f},{y(r['q50']):.1f}" for i, r in enumerate(rows))
    out += f"<polyline points='{med}' fill='none' stroke='var(--terra)' stroke-dasharray='3 3'/>"
    for i, r in enumerate(rows):
        if r["actual"] is not None:
            out += f"<circle cx='{x(i):.1f}' cy='{y(r['actual']):.1f}' r='3.5' fill='var(--{'teal' if r['hit'] else 'bad'})' stroke='var(--card)'/>"
    for i in sorted({0, n - 1}):
        out += f"<text x='{x(i):.1f}' y='{H - 3}' text-anchor='{'start' if i == 0 else 'end'}' fill='var(--muted)' font-size='10'>epoch {rows[i]['k']}</text>"
    return out + "</svg>"

# ---- chapter: the path to break-even (results["scenarios"] from run.py: scenarios). Static SVG, so it reads without JS.

PATH_CSS = """
.paths .fan-w{display:block}.paths .fan-n{display:none}
.yrs{border-top:1px solid var(--ink);padding-top:14px}
.yrs .y{font:400 clamp(56px,6.4vw,104px)/.9 var(--serif);letter-spacing:-.03em;margin:10px 0 10px;font-variant-numeric:tabular-nums}
.yrs .y.never{font-style:italic;color:var(--terra)}.yrs.bull .y{color:var(--teal)}
.yrs .y small{font:400 13.5px var(--sans);letter-spacing:0;color:var(--muted);margin-left:8px}
.yrs .h{font:400 15px/1.4 var(--sans);color:var(--ink-2);margin:0 0 10px}.yrs .h b{font-weight:600;color:var(--ink)}
.yrs p{margin:0;font-size:14.5px;line-height:1.55;color:var(--ink-2);max-width:38ch}
.paths .defs{margin-top:28px;font-size:12.5px;line-height:1.6;color:var(--muted);max-width:90ch;border-top:1px solid var(--rule-2);padding-top:12px}
@media (max-width:820px){.paths .fan-w{display:none}.paths .fan-n{display:block}.yrs .y{font-size:64px}}
"""


def path_svg(sc, wide):
    """Payback over the next ten years under bear, base and bull, on a log scale, with the 100% line."""
    import math
    W, H = (880, 400) if wide else (360, 330)
    L, R, T, B = (44, 128, 18, 30) if wide else (38, 12, 16, 28)
    lo, hi = 0.005, 2.0
    P, yrs = sc["path"], sc["path"]["years"]
    x = lambda t: L + t / yrs[-1] * (W - L - R)
    y = lambda v: T + (math.log(hi) - math.log(min(max(v, lo / 4), hi * 4))) / (math.log(hi) - math.log(lo)) * (H - T - B)  # drawn past the frame, clipped
    line = lambda vs: " ".join(f"{'M' if i == 0 else 'L'}{x(t):.1f},{y(v):.1f}" for i, (t, v) in enumerate(zip(yrs, vs)))
    cid = "pclip-" + ("w" if wide else "n")
    col = {"bear": "var(--terra)", "base": "var(--ink)", "bull": "var(--teal)"}
    start = int(sc["start"][:4]) + int(sc["start"][5:7]) / 12
    o = (f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='Payback over the next ten years under the bear, base and bull growth rates, "
         f"with and without HSP-029, against the 100% break-even line'><defs><clipPath id='{cid}'><rect x='{L}' y='{T}' width='{W - L - R}' height='{H - T - B}'/></clipPath></defs>")
    for v, lab in ((0.01, "1%"), (0.03, "3%"), (0.1, "10%"), (0.3, "30%"), (1.0, "100%")):
        o += (f"<line x1='{L}' x2='{W - R}' y1='{y(v):.1f}' y2='{y(v):.1f}' stroke='var(--{'ink' if v == 1 else 'rule-2'})' stroke-width='{1.25 if v == 1 else 1}'/>"
              f"<text x='{L - 6}' y='{y(v) + 4:.1f}' text-anchor='end'{' class=lab' if v == 1 else ''}>{lab}</text>")
    o += f"<text x='{x(0):.1f}' y='{H - 8}' text-anchor='start'>Today</text>"
    for yr in range(int(start) + 1, int(start) + 11):  # ticks on 1 January
        t = yr - start
        if (yr % 2 == 0 if wide else yr % 5 == 0) and 1 < t <= yrs[-1]:
            o += f"<line x1='{x(t):.1f}' x2='{x(t):.1f}' y1='{H - B}' y2='{H - B + 4}' stroke='var(--rule)'/><text x='{x(t):.1f}' y='{H - 8}' text-anchor='middle'>{yr}</text>"
    o += f"<text x='{x(10) - 4:.1f}' y='{y(1.0) - 8:.1f}' text-anchor='end' class='lab-s'>{'Break-even: burn + buybacks = issuance' if wide else 'Break-even'}</text>"
    band = line(P["bull"]) + " " + " ".join(f"L{x(t):.1f},{y(v):.1f}" for t, v in reversed(list(zip(yrs, P["bear"])))) + " Z"
    o += f"<g clip-path='url(#{cid})'><path class='area' d='{band}' fill='var(--gray-fill)' opacity='.55'/>"
    for n in ("bear", "base", "bull"):
        o += f"<path class='area' d='{line(P[n + '_hsp029'])}' fill='none' stroke='{col[n]}' stroke-width='1.5' stroke-dasharray='5 4' opacity='.9'/>"
        o += f"<path class='draw' pathLength='1' d='{line(P[n])}' fill='none' stroke='{col[n]}' stroke-width='2.25' stroke-linejoin='round'/>"
    o += "</g>"
    c = sc["cases"]
    for n, k in (("bull", ""), ("bull", "_hsp029")):
        yv = c[n]["years" + k]
        if yv is not None and yv <= yrs[-1]:
            o += f"<circle cx='{x(yv):.1f}' cy='{y(1.0):.1f}' r='{4.5 if not k else 3.5}' fill='{'var(--teal)' if not k else 'var(--card)'}' stroke='var(--teal)' stroke-width='1.5'/>"
    yb = c["bull"]["years"]
    if yb is not None and yb <= yrs[-1]:
        o += f"<text x='{x(yb) + 8:.1f}' y='{y(1.0) + 18:.1f}' class='lab' style='fill:var(--teal)'>{c['bull']['year']}</text>"
    if wide:  # end labels, nudged apart
        ends = sorted(((min(max(P[n][-1], lo), hi), n) for n in ("bear", "base", "bull")), key=lambda a: -a[0])
        last = -99
        for v, n in ends:
            yy = max(y(v) + 4, last + 30)
            last = yy
            g = c[n]["growth"]
            o += (f"<text x='{W - R + 8}' y='{yy:.1f}' class='lab' style='fill:{col[n]}'>{n.capitalize()}</text>"
                  f"<text x='{W - R + 8}' y='{yy + 14:.1f}' class='lab-s'>{'+' if g >= 0 else '−'}{abs(100 * g):.1f}% a year</text>")
    return o + "</svg>"


def path_chapter(sc, s, num_, fnk):
    """The forward-looking chapter: three data-ruled growth rates and the year each reaches break-even."""
    if not sc:
        return ""
    c, pct = sc["cases"], lambda x, n=1: f"{100 * x:.{n}f}%"
    g = lambda x: f"{'+' if x >= 0 else '−'}{abs(100 * x):.1f}%"
    fn = f"<sup class='fn'><a href='#n{fnk}'>{fnk}</a></sup>"
    def big(n):
        k = c[n]
        if k["year"] is None:
            return "<div class='y never'>Never</div>"
        return f"<div class='y'>{k['year']}<small>in {k['years']:.0f} years</small></div>"
    def hsp(n):
        k = c[n]
        return ("never with HSP-029 either" if k["year_hsp029"] is None and k["growth"] < 0 else
                "not within 100 years with HSP-029" if k["year_hsp029"] is None else
                f"<b>{k['year_hsp029']}</b> with HSP-029 ({k['years_hsp029']:.0f} years)")
    sent = {
        "bear": (f"If gross Intents fees keep shrinking as they did over the past year, the flow shrinks with them and never reaches issuance."
                 if c["bear"]["growth"] < 0 else "At the slowest year-long rate in the data, break-even does not come this century."
                 if c["bear"]["year"] is None else f"Even at the slowest year-long rate in the data, break-even comes in {c['bear']['year']}."),
        "base": f"At the median year-long rate, payback is {pct(c['base']['payback_10y'], 0)} of issuance in ten years. At this pace, growth alone is too slow; capture is the lever."
                if c["base"]["year"] and c["base"]["years"] > 15 else f"At the median year-long rate, break-even comes in {c['base']['year'] or 'over a century'}.",
        "bull": f"If Intents volume keeps the trend it set over the past year, break-even comes in about {c['bull']['years']:.0f} years. "
                f"Five-year break-even needs {pct(s['growth_needed_5y'], 0)} a year.",
    }
    label = {"bear": "Bear", "base": "Base", "bull": "Bull"}
    tiles = "".join(f"<div style='grid-column:span 4'><div class='yrs {n}'><div class='eyebrow'>{label[n]} · {g(c[n]['growth'])} a year</div>"
                    f"{big(n)}<p class='h'>{hsp(n)}</p><p>{sent[n]}</p></div></div>" for n in ("bear", "base", "bull"))
    cap = sc["levers"]["capture"]
    full = cap[-1]
    yy = lambda v: "—" if v is None else f"{v:.0f}"
    lev = ("<div style='grid-column:1/span 7'><div class='eyebrow' style='margin-bottom:14px'>Levers on the base case · at today's volume</div>"
           "<div class='tw'><table class='tbl'><thead><tr><th>Share of gross Intents fees captured</th><th class='r'>Payback today</th><th class='r'>Break-even, 2.5%</th><th class='r'>With HSP-029</th></tr></thead><tbody>"
           + "".join(f"<tr><td>{pct(x['share'], 0)}{' <small>today</small>' if abs(x['share'] - s['capture_share']) < 1e-9 else ''}</td><td class='r'>{pct(x['payback'], 0)}</td>"
                     f"<td class='r big'>{yy(x['years_base'])} <span>yrs</span></td><td class='r big teal'>{yy(x['years_base_hsp029'])} <span>yrs</span></td></tr>"
                     for x in cap)
           + "</tbody></table></div></div>"
           f"<div style='grid-column:9/span 4'><div class='eyebrow' style='margin-bottom:14px'>Issuance</div><p class='prose' style='margin-top:0'>Today's flow would equal issuance "
           f"if issuance were <b>{sc['levers']['breakeven_issuance_pct']:.2f}%</b> a year. HSP-029's 1.6% takes the distance from {s['multiple']:.1f}× to "
           f"{s['multiple_at_1_6_issuance']:.1f}×. Capture is the larger lever: all of it, with HSP-029, brings the base case to {yy(full['years_base_hsp029'])} years.</p></div>")
    m = sc["measures"]
    defs = (f"How the three rates are set: one rule, not a choice. The captured flow is nine months old and was ramping up, so its own growth is not used; "
            f"what drives it is (buybacks are {pct(s['buyback_coverage'] / s['payback'], 0)} of payback and follow NEAR Intents volume, r = {s['intents_volume_captured_correlation']:.2f} by week). "
            f"Four year-long rates from the DefiLlama year: Intents volume, last 30 days against the first 30 ({g(m['intents_volume_yoy'])}) and log-linear trend ({g(m['intents_volume_trend'])}); "
            f"gross Intents fees, the same two ways ({g(m['intents_fees_yoy'])}, {g(m['intents_fees_trend'])}). Bear is the lowest, base the median, bull the highest. "
            f"Shorter windows are left out: they annualise August's jump into several hundred percent a year. Paths start at today's {pct(s['payback'])} and hold capture share and NEAR price constant; "
            f"HSP-029 is a linear ramp from 2.5% to 1.6% over 24 months, starting at its earliest possible date, {sc.get('hsp029_start', sc['start'])} (veto window closes 16 Nov 2026, then a 90-day grace period; validators must also adopt the upgrade). Dashed lines: with HSP-029. Shaded: between bear and bull. "
            f"<code>run.py: scenarios</code>, <code>scenarios</code> in <code>out/results.json</code>.")
    full = sc["levers"]["capture"][-1]  # every Intents fee captured, at the base growth rate
    head = (f"Break-even turns on growth and capture. At Intents' volume trend it comes in about {c['bull']['years']:.0f} years; "
            f"at slow growth, capturing every Intents fee with HSP-029 brings it to {full['years_base_hsp029']:.0f}."
            if c["bull"]["years"] is not None and full.get("years_base_hsp029") is not None and full["share"] == 1.0 else
            "Where the flow goes from here, under three growth rates the data set.")
    return f"""<section class="chapter paths" id="c-path" data-t="The path to break-even"><div class="ch-head"><div class="ch-num"><span class="n">{num_}</span><span class="eyebrow">The path to break-even</span><span class="line"></span></div>
<h2>{head}</h2><p>Not a forecast: three growth rates taken from the data by one rule, and where each takes payback from today's {pct(s['payback'])}. HSP-029, passed on 2 November 2026 and awaiting ratification, moves every date earlier; it does not change which paths arrive.{fn}</p></div>
<figure class="fig" style="margin:0"><div class="fig-title"><h3>Payback over the next ten years, bear to bull</h3><div class="legend"><span><i class="l" style="--c:var(--teal)"></i>Bull</span><span><i class="l" style="--c:var(--ink)"></i>Base</span><span><i class="l" style="--c:var(--terra)"></i>Bear</span><span><i class="l" style="--c:var(--muted);background:repeating-linear-gradient(90deg,var(--muted) 0 5px,transparent 5px 9px)"></i>With HSP-029</span></div></div>
<p class="fig-sub">Burn plus buybacks as a share of issuance, log scale. Above the line, NEAR's flows pay back more than it mints.</p>
<div class="chart fan-w">{path_svg(sc, True)}</div><div class="chart fan-n">{path_svg(sc, False)}</div>
<figcaption>Source: <code>out/results.json</code> → <code>scenarios.path</code>. Quarterly steps; the chart stops at 200%.</figcaption></figure>
<div class="grid12" style="margin-top:56px">{tiles}</div>
<div class="grid12" style="margin-top:56px">{lev}</div>
<p class="defs">{defs}</p></section>"""


def render(results, sha, ledgers=None, tape=None):
    _capture()
    s, e = results["summary"], html.escape
    pct = lambda x, n=1: f"{100 * x:.{n}f}%"
    num = lambda x: f"{x:,.0f}"
    nr = lambda x: "n/a" if x is None else f"{x:,.0f}"
    fn = lambda k: f"<sup class='fn'><a href='#n{k}'>{k}</a></sup>"
    has = s["payback"] is not None
    days = f"{s['window_days']:.0f}"
    try:
        proto = json.load(open(os.path.join(HERE, "data", "protocol.json")))
        iss = 100 * proto["max_inflation_rate"][0] / proto["max_inflation_rate"][1]
        epoch_len = proto["epoch_length"]
    except (OSError, KeyError, ValueError, ZeroDivisionError):
        iss, epoch_len = 2.5, 43200
    iss_s = f"{iss:g}%"
    E = (tape or {}).get("E", [])
    day = {r[1]: datetime.datetime.fromtimestamp(r[3], datetime.timezone.utc).strftime("%Y-%m-%d") for r in E}
    first_buy = next((r for r in E if r[6] is not None and int(r[6]) > 0), None)
    since_buy = (lambda d: f"{MONTHS[d.month - 1]} {d.year}")(datetime.datetime.fromtimestamp(first_buy[3], datetime.timezone.utc)) if first_buy else None
    try:  # the month the Intents contract first sent NEAR, from the account's receipts (the balance first grew from other senders)
        with open(os.path.join(HERE, "data", "wallet_history.csv")) as fh:
            h_in = next(int(r["block_height"]) for r in csv.DictReader(fh) if r["predecessor"] == "intents.near" and int(r["yocto"]) > 0)
        e_in = next((r for r in E if r[1] >= h_in), None)
        if e_in:
            d = datetime.datetime.fromtimestamp(e_in[3], datetime.timezone.utc)
            since_buy = f"{MONTHS[d.month - 1]} {d.year}"
    except (OSError, StopIteration, KeyError, ValueError):
        pass
    yr0, yr1 = s["first"][:4], s["last"][:4]
    span = f"{dshort(s['first'])}{' ' + yr0 if yr0 != yr1 else ''} – {dshort(s['last'])} {yr1}"

    # ---- hero ----
    if has:
        title = f"NEAR gives back {pct(s['payback'])} of what it mints. Break-even is {s['multiple']:.1f}× away, not {s['burn_only_multiple']:.0f}×."
        h1 = (f"NEAR gives back <em>{pct(s['payback'])}</em> of what it mints. Break-even is <em>{s['multiple']:.1f}×</em> away, "
              f"not&nbsp;<s>{s['burn_only_multiple']:.0f}×</s>.")
        dek = (f"NEAR mints about {100 * s['realized_inflation']:.1f}% of its supply a year. A fee-burn dashboard sees only the gas burn, "
               f"<strong>{pct(s['burn_coverage'], 2)} of issuance</strong>, and puts break-even {s['burn_only_multiple']:.0f} times away. "
               + (f"Since {since_buy} the NEAR Intents contract has also been sending NEAR to a buyback account, where it is held, not burnt. "
                  if since_buy else "The NEAR Intents contract also sends NEAR to a buyback account, where it is held, not burnt. ")
               + f"Count that, and <strong>burn plus buybacks offset {pct(s['payback'])} of issuance</strong>.{fn(1)}")
    else:
        title = f"NEAR burns back {pct(s['burn_coverage'], 2)} of what it mints."
        h1, dek = e(title), "Buyback balances are not cached for this window yet."
    byline = (f"<b>Headline window:</b> last 100 epochs, {days} days, ending {e(s.get('last_end_utc') or s['last'])} UTC. "
              f"Every figure rebuilds offline with one command and a result hash.{fn(6)}")

    ruler = scale = ""
    if has:
        mx = max(150, s["burn_only_multiple"] * 1.4)
        ticks = [t for t in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if t <= mx]
        rd = dict(max=mx, ticks=ticks, today=s["multiple"], burn=s["burn_only_multiple"],
                  pts=[[s["multiple_at_1_6_issuance"], f"{s['multiple_at_1_6_issuance']:.1f}× at 1.6% issuance", f"{s['multiple_at_1_6_issuance']:.1f}× HSP-029", "alt", -1],
                       [s["multiple"], f"{s['multiple']:.1f}× today", f"{s['multiple']:.1f}× today", "today", 1],
                       [s["burn_only_multiple"], f"{s['burn_only_multiple']:.0f}× burn only", f"{s['burn_only_multiple']:.0f}× burn only", "burn", -1]],
                  aria=f"Log ruler: break-even 1×, {s['multiple_at_1_6_issuance']:.1f}× at 1.6% issuance, {s['multiple']:.1f}× today, {s['burn_only_multiple']:.0f}× on burn alone")
        ruler = ("<div class='ruler'><div class='head'><h2>Distance to break-even, on a log scale</h2><span class='legend'>"
                 "<span><i style='--c:var(--terra)'></i>burn only</span><span><i style='--c:var(--teal)'></i>burn + buybacks</span></span></div>"
                 "<div class='chart' id='ruler'></div></div>")
        m, b, u = s["mint_per_day"], s["buyback_per_day"], s["burn_per_day"]
        scale = (f"<div class='scale'><div class='head'><h2>Every NEAR minted in the last {days} days, to scale</h2><span class='eyebrow num'>{num(m)} NEAR minted a day</span></div>"
                 f"<div class='scale-bar' role='img' aria-label='Buybacks {pct(b / m, 1)}, burn {pct(u / m, 2)}, not matched {pct(1 - (b + u) / m)} of issuance'>"
                 f"<div style='width:{100 * b / m:.3f}%;background:var(--teal)'></div><div style='width:{max(100 * u / m, .5):.3f}%;background:var(--terra)'></div><div class='hatch' style='flex:1'></div></div>"
                 f"<div class='scale-legend'><div style='--c:var(--teal)'><b>{num(b)}</b>NEAR a day gained by the buyback account · {pct(s['buyback_coverage'], 2)}</div>"
                 f"<div style='--c:var(--terra)'><b>{num(u)}</b>NEAR a day burnt in gas fees · {pct(s['burn_coverage'], 2)}</div>"
                 f"<div style='--c:var(--muted)'><b>{num(m - b - u)}</b>NEAR a day minted and not matched · {pct(1 - s['payback'])}</div></div>"
                 f"<div class='fee'><span>What a fee-burn dashboard counts</span><div class='scale-bar' role='img' aria-label='Burn only, {pct(s['burn_coverage'], 2)} of issuance'>"
                 f"<div style='width:{max(100 * u / m, .5):.3f}%;background:var(--terra)'></div><div class='hatch' style='flex:1'></div></div></div></div>")
    else:
        rd = None

    # ---- live strip: the newest cached epoch painted at build time; the browser overwrites it from mainnet ----
    live = ""
    if tape:
        c_h = c_s = c_b = c_g = c_n = c_when = None
        try:
            d = os.path.join(HERE, "data")
            with open(os.path.join(d, "epochs.csv")) as fh:
                ep = list(csv.DictReader(fh))
            with open(os.path.join(d, "buybacks.csv")) as fh:
                bal = {int(r["end_height"]): int(r["balance"]) for r in csv.DictReader(fh) if r["balance"]}
            last = ep[-1]
            h = int(last["end_height"])
            c_h, c_s = f"{h:,}", f"{int(last['supply_end']) // 10**24:,}"
            c_when = datetime.datetime.fromtimestamp(int(last["t1_ns"]) / 1e9, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            if h in bal:
                c_b = f"{bal[h] // 10**24:,}"
                if tape["rounds"] and tape["snap"] in bal:
                    c_n = sum(int(r["end_height"]) > tape["snap"] for r in ep)
                    g = (bal[h] - bal[tape["snap"]]) / 10**24
                    c_g = f"{'+' if g >= 0 else ''}{g:,.0f}"
        except (OSError, KeyError, ValueError, IndexError):
            pass
        nd = lambda v: "&ndash;" if v is None else v
        pend = [L for L in (ledgers or []) if L["verdict"] == "PENDING" and L.get("so_far") is not None and L["claims"].get("payback")
                and L["after_end_height"] == tape.get("snap")]
        sofar_live = ""
        if pend:
            ins = sum(L["claims"]["payback"]["lo"] <= L["so_far"] <= L["claims"]["payback"]["hi"] for L in pend)
            sofar_live = (f"<small class='lsf'>Payback so far <b>{pct(pend[0]['so_far'])}</b>: inside {ins} of {len(pend)} committed ranges, "
                          f"<a href='#c5'>scoreboard</a></small>")
        live = (f"<div class='live' role='group' aria-label='NEAR mainnet now'><div><span class='pulse' id='lmsg' aria-live='polite'>Mainnet, from cache</span>"
                f"<small id='lsub' data-cache='{'Epoch ending ' + c_when + ', committed cache' if c_when else 'Committed cache'}'>{'Epoch ending ' + c_when + ', reading mainnet' if c_when else 'Reading NEAR mainnet from your browser'}</small></div>"
                f"<div><small>Latest block</small><div class='v' id='l-h'>{nd(c_h)}</div></div>"
                f"<div><small>Total supply, NEAR</small><div class='v' id='l-s'>{nd(c_s)}</div></div>"
                f"<div><small>Buyback account holds, NEAR</small><div class='v' id='l-b'>{nd(c_b)}</div></div>"
                + (f"<div><small>Gained since the forecasts were frozen</small><div class='v teal' id='l-g'>{nd(c_g)}</div>"
                   f"<small id='l-gs'>{'NEAR in ' + str(c_n) + ' epochs' if c_n is not None else ''}</small>{sofar_live}</div>" if tape["rounds"] else "<div></div>")
                + "<p class='lfoot' id='lfail' hidden>Live read unavailable (the free endpoint rate-limits); showing the committed cache.</p></div>")

    # ---- chapter 01: the claim ----
    ch1 = ""
    if has:
        stats = [("Break-even", f"{s['multiple']:.1f}×", "", "Growth in flows needed to equal issuance at constant issuance."),
                 ("Under HSP-029", f"{s['multiple_at_1_6_issuance']:.1f}×", "", f"If maximum issuance falls from {iss_s} to 1.6% a year."),
                 ("Burn alone", f"{s['burn_only_multiple']:.0f}×", "terra", f"What a fee-burn dashboard reports: {pct(s['burn_coverage'], 2)} of issuance.")]
        rng = (f" 90% resampling range {pct(s['payback_p05'])} to {pct(s['payback_p95'])}." if s.get("payback_p05") is not None else "")
        peak_d = _d(s["payback_peak_date"])
        trend = ("is at its peak" if s["payback"] >= s["payback_peak"] else f"has eased to {pct(s['payback'])}")
        ptitle = f"Payback climbed to {pct(s['payback_peak'])} in {MONTHS[peak_d.month - 1]} and {trend}"
        more = ""
        for k, t, sub, mul, u, dp, src, say, col in CHARTS:
            try:
                sentence = say(s)
            except (TypeError, KeyError):
                sentence = t
            more += (f"<div class='mult'><h4>{e(sentence)}</h4><div class='u'>{e(t)}. {e(sub)}, 100-epoch rolling</div>"
                     f"<div class='chart spark' tabindex='0' data-src='series' data-key='{k}' data-mul='{mul}' data-dp='{dp}' data-unit='{e(u)}' data-color='{col}' "
                     f"data-aria='{e(t)}'></div><p class='src'>Source: <code>{e(src)}</code></p></div>")
        ch1 = f"""<section class="chapter" id="c1" data-t="The claim"><div class="ch-head"><div class="ch-num"><span class="n">01</span><span class="eyebrow">The claim</span><span class="line"></span></div>
<h2>Burn and buybacks offset {frac(s['payback'])} of issuance. A burn-only view sees {frac(s['burn_coverage'])}.</h2>
<p>Payback is burn plus the buyback account's gain, divided by NEAR minted to validators. Mint and burn come from <code>total_supply</code> in block headers, exact to the yoctoNEAR; the buyback gain is a balance change between epoch ends.{fn(2)}</p></div>
<div class="grid12"><div class="pull" style="grid-column:1/span 4"><div class="eyebrow">Payback, last {days} days</div><div class="big">{100 * s['payback']:.1f}<sup>%</sup></div>
<p>of issuance, from <span class="terra">burn {pct(s['burn_coverage'], 2)}</span> and <span class="teal">buybacks {pct(s['buyback_coverage'], 2)}</span>.{rng}</p></div>
<div class="stats" style="grid-column:5/span 8;align-self:end">{''.join(f"<div class='stat'><div class='eyebrow'>{a}</div><div class='v {c}'>{v}</div><p>{p}</p></div>" for a, v, c, p in stats)}</div>
<figure class="fig" style="grid-column:1/-1"><div class="fig-title"><h3>{e(ptitle)}</h3><div class="legend"><span><i style="--c:var(--teal)"></i>Intents buybacks</span><span><i style="--c:var(--terra)"></i>Gas-fee burn</span></div></div>
<p class="fig-sub">Share of minted NEAR matched, 100-epoch rolling window. Hover, tap or use the arrow keys for values.</p>
<div class="chart" id="ch-payback" tabindex="0" data-aria="{e(ptitle)}"></div>
<figcaption>Source: (burn + buyback gain) / mint, from <code>data/epochs.csv</code> and <code>data/buybacks.csv</code>.{fn(2)} Break-even is 100%, off the top of this frame.</figcaption></figure></div>
<details class="more"><summary>Every series behind the headline<small>Distance to break-even, buybacks, burn, burn-only coverage, mint and block utilization, each with its method</small></summary>
<div class="multiples">{more}</div></details></section>"""

    # ---- chapter 02: the flow ----
    w, pv = results.get("wallet"), results.get("private_settlement") or {}
    tape_fig = ""
    if tape:
        tape_fig = (f"<figure class='fig' style='grid-column:1/-1'><div class='fig-title'><h3>Every epoch since {dshort(s['first'])}, one column each</h3>"
                    "<div class='legend'><span><i style='--c:var(--teal)'></i>Buyback gain</span><span><i style='--c:var(--terra)'></i>Burn</span>"
                    "<span><i class='l' style='--c:var(--ink)'></i>100-epoch payback</span>"
                    + ("<span><i class='o'></i>Committed band</span>" if tape["rounds"] else "") + "</div></div>"
                    "<p class='fig-sub'>Share of each epoch's minted NEAR matched by gas burn and buyback gain. Hover or use the arrow keys; click to hold an epoch.</p>"
                    "<div class='chart'><canvas id='tape' tabindex='0' role='img' aria-label='Burn and buyback gain as a share of mint, for every epoch'></canvas></div>"
                    "<div class='read' id='read' aria-live='polite'></div>"
                    "<div class='vrow'><button type='button' class='btn pri' id='vsel'>Check this epoch against mainnet</button>"
                    "<button type='button' class='btn' id='vrnd'>Check a random epoch</button></div><div class='check' id='check' aria-live='polite'></div>"
                    f"<figcaption>Columns above <span id='tape-clip'>the top</span> are clipped and capped in ink; a grey column is a transfer from another wallet, excluded. "
                    f"Right of the divider: epochs that closed after the forecast rounds were frozen at height {tape['snap']:,}, against the committed payback band. "
                    "The check buttons refetch three block headers from mainnet in your browser and compare them with the cache to the yoctoNEAR.</figcaption></figure>")
    senders = audit = private = ""
    if w:
        top = w["top_senders"]
        rows = "".join(
            f"<div class='srow'><span class='nm'><code>{e(r['account'] if len(r['account']) <= 30 else r['account'][:10] + '…' + r['account'][-6:])}</code> · "
            f"{num(r['transfers'])} transfer{'s' if r['transfers'] != 1 else ''}</span><span class='pc'>{pct(r['share'])}</span>"
            f"<div class='tr'><i{' class=t' if r['account'] == 'intents.near' else ''} style='width:{max(100 * r['share'], .6):.2f}%'></i></div></div>" for r in top[:4])
        line = (f"{num(s['inflow_transfers_from_intents'])} of the {num(s['inflow_transfers'])} transfers since height {s['inflow_first_height']:,} came from "
                f"<code>intents.near</code>. " if s.get("inflow_transfers") else "")
        senders = (f"<div style='grid-column:1/span 5'><div class='eyebrow' style='margin-bottom:14px'>Who pays in · share of NEAR received</div>"
                   f"<div class='senders'>{rows}</div><p class='prose'>{line}<code>{e(top[1]['account'])}</code> sent {pct(top[1]['share'])} in "
                   f"{top[1]['transfers']} transfers, including the one the headline excludes.{fn(3)}</p></div>")
        c, out = w["custody"], sum(x["near"] for x in w["paid"])
        big = max(w["paid"], key=lambda x: x["near"]) if w["paid"] else None
        tiles = [(f"{w['exact_with_receipts']}<span> / {w['epochs_with_receipts']}</span>", "",
                  f"Epochs that reconcile to the yoctoNEAR, from {num(w['receipts'])} receipts. {w['call_epochs']} epochs with multisig calls differ by {abs(w['call_residual_near']):.2f} NEAR of gas."),
                 (pct(top[0]["share"]), "", f"Sent by <code>{e(top[0]['account'])}</code>; {pct(top[1]['share'])} by <code>{e(top[1]['account'][:24])}</code> in {top[1]['transfers']} transfers."),
                 (num(out), "terra", f"NEAR that has left: {pct(out / w['inflow_near'], 2)} of inflow"
                  + (f", the largest to a bridge account on {big['date']}" if big else "") + ". None burnt."),
                 (f"{c['confirmations_required']} of {c['function_call_keys']}", "",
                  f"Keys needed to move it. {c['full_access_keys']} full-access keys, {c['requests_ever']} requests ever, {c['requests_pending']} pending. The chain does not say who holds the keys.")]
        audit = ("<div style='grid-column:1/-1'><div class='eyebrow' style='margin-bottom:4px'>The buyback account, audited like a short seller would</div><div class='audit'>"
                 + "".join(f"<div><div class='v {k}'>{v}</div><p>{p}</p></div>" for v, k, p in tiles) + "</div></div>")
    if pv.get("before") and pv.get("since"):
        b, a = pv["before"], pv["since"]
        private = (f"<div style='grid-column:7/span 6'><div class='eyebrow' style='margin-bottom:14px'>The flow did not fall when swaps went private</div>"
                   if a["buyback_per_day"] >= b["buyback_per_day"] else
                   f"<div style='grid-column:7/span 6'><div class='eyebrow' style='margin-bottom:14px'>The flow since swaps went private</div>")
        private += (f"<div class='tw'><table class='tbl'><thead><tr><th>Period</th><th class='r'>NEAR a day</th><th class='r'>Payback</th><th class='r hide-s'>Inflow epochs</th></tr></thead><tbody>"
                    f"<tr><td>{b['days']:.0f} days before<small>27 Oct, private settlement</small></td><td class='r big'>{num(b['buyback_per_day'])}</td><td class='r'>{pct(b['payback'])}</td>"
                    f"<td class='r hide-s'>{b['epochs_with_inflow']} of {b['epochs']}</td></tr>"
                    f"<tr><td>{a['days']:.0f} days since</td><td class='r big'>{num(a['buyback_per_day'])}</td><td class='r'>{pct(a['payback'])}</td>"
                    f"<td class='r hide-s'>{a['epochs_with_inflow']} of {a['epochs']}</td></tr></tbody></table></div>"
                    f"<p class='prose'>Since 2026-10-27 a growing share of Intents swaps settles on a private chain (reported by the "
                    f"<a href='https://github.com/ervhint/tideline-thesis'>Tideline</a> entry; our own check of mainnet logs is in the cross-checks below), "
                    f"which hides their fees from public swap data. The buyback balance is on mainnet and still records what arrives.</p></div>")
    intents = ""
    if results.get("weekly"):
        wk = [("volume_musd", f"Volume is ${s['intents_volume_musd_latest']:.0f}M a day, {s['intents_volume_usd_ratio_1y']:.2f}× a year ago",
               "USD millions a day, weekly average", "$", "M", 0, "teal", None, "DefiLlama summary/dexs/near-intents"),
              ("captured_kusd", f"Captured revenue tracks volume (r = {s['intents_volume_captured_correlation']:.2f} over {s['intents_weeks']} weeks)",
               "USD thousands a day, all revenue wallets", "$", "k", 0, "teal", None, "DefiLlama summary/fees/near-intents dailyHoldersRevenue"),
              ("take_bps", f"Take rate: median {s['intents_take_bps_median']:.1f} bps, ranging {s['intents_take_bps_min']:.1f} to {s['intents_take_bps_max']:.1f}",
               "Captured revenue per unit of volume, bps · dashed = median", "", "", 1, "ink", s["intents_take_bps_median"], "captured revenue / volume, weekly")]
        intents = ("<div style='grid-column:1/-1;margin-top:20px'><div class='fig-title' style='margin-bottom:18px'><h3 style='font:400 clamp(26px,2.6vw,38px)/1.1 var(--serif)'>"
                   f"The application behind the flow: NEAR Intents, by week</h3><span class='eyebrow'>DefiLlama · context only, feeds no headline figure{fn(4)}</span></div><div class='multiples'>"
                   + "".join(f"<div class='mult'><h4>{e(t)}</h4><div class='u'>{e(u)}</div><div class='chart spark' tabindex='0' data-src='weekly' data-key='{k}' data-mul='1' "
                             f"data-dp='{dp}' data-pre='{pre}' data-unit='{un}' data-color='{col}'{'' if ref is None else f' data-ref={ref}'} data-aria='{e(t)}'></div>"
                             f"<p class='src'>Source: <code>{e(src)}</code>, in <code>data/llama.csv</code></p></div>"
                             for k, t, u, pre, un, dp, col, ref, src in wk) + "</div></div>")
    plog, pl = "", results.get("private_logs") or {}
    if pl and pl["before"]["share"] is not None and pl["since"]["share"] is not None:
        row = lambda name, x: (f"<tr><td>{name}</td><td class='r'>{x['blocks']}</td><td class='r'>{num(x['events'])}</td><td class='r'>{pct(x['share'], 0)}</td>"
                               f"<td class='r'>{pct(x['share_p05'], 0)} to {pct(x['share_p95'], 0)}</td></tr>")
        plog = ("<div class='sec'><h4>Private settlement, checked from raw mainnet blocks</h4><p class='sub'>The share of <code>intents.near</code> event logs that name the "
                "Confidential Intents treasury, in seeded random blocks (<code>data/private_sample.csv</code>, <code>python3 fetch.py private</code>).</p>"
                "<div class='tw'><table class='tbl'><tr><th>Period</th><th class='r'>Blocks</th><th class='r'>Event logs</th><th class='r'>Naming the treasury</th><th class='r'>90% interval</th></tr>"
                + row("30 days before 2026-10-27", pl["before"]) + row("Since", pl["since"]) + "</table></div></div>")
    check = ("<div class='sec'><h4>Chain versus the indexer</h4><p class='sub'>The same flows over the same days, in NEAR a day. DefiLlama reports USD; each day is converted at that day's price.</p>"
             "<div class='tw'><table class='tbl'><tr><th>Flow, NEAR a day</th><th class='r'>This repo, from chain</th><th class='r'>DefiLlama</th></tr>"
             f"<tr><td>Gas fees burnt</td><td class='r'>{nr(s['burn_per_day'])}</td><td class='r'>{nr(s['llama_burn_near_per_day'])}<small>its revenue series; its fees series is {nr(s['llama_fees_near_per_day'])}</small></td></tr>"
             f"<tr><td>Buyback account gain</td><td class='r'>{nr(s['buyback_per_day'])}</td><td class='r' rowspan='2'>{nr(s['llama_buyback_near_per_day'])}<small>captured revenue, all wallets</small></td></tr>"
             f"<tr><td>All three revenue wallets, gain</td><td class='r'>{nr(s['all_revenue_wallets_per_day'])}</td></tr></table></div></div>")
    attr = ""
    if s.get("inflow_transfers"):
        attr = (f"<div class='sec'><h4>Who sent it, transfer by transfer</h4><p class='sub'>{s['inflow_transfers_from_intents']} of the {s['inflow_transfers']} transfers since height "
                f"{s['inflow_first_height']} into the buyback account came from <code>intents.near</code>, carrying {pct(s['inflow_share_from_intents'])} of the NEAR "
                f"(NearBlocks, with transaction hashes in <code>data/inflows.csv</code>). The account audit rebuilds with <code>python3 fetch.py history</code> and "
                f"<code>python3 fetch.py multisig</code>; <code>test_run.py</code> fails if an epoch is unexplained.</p></div>")
    xchecks = f"<details><summary>Cross-checks and data tables<small>Private settlement from raw blocks, chain versus the indexer, and the sender check</small></summary>{plog}{check}{attr}</details>"
    if has:
        most = (s.get("inflow_transfers") and s["inflow_transfers_from_intents"] / s["inflow_transfers"] >= .9)
        every = pv.get("since") and pv["since"]["epochs_with_inflow"] == pv["since"]["epochs"]
        h2 = (f"{'Almost all' if most else 'Most'} of it arrives from one contract, {'every epoch' if every else 'most epochs'}, and "
              f"{'stays put' if s['buyback_outflow_near'] < .05 * (w or {}).get('inflow_near', 1e30) else 'some of it leaves'}.")
    else:
        h2 = "The buyback account"
    ch2 = f"""<section class="chapter" id="c2" data-t="The flow"><div class="ch-head"><div class="ch-num"><span class="n">02</span><span class="eyebrow">The flow</span><span class="line"></span></div>
<h2>{e(h2)}</h2><p>The buyback account, <code>buybacks.multisignature.near</code>, gains about {num(s['buyback_per_day'] or 0)} NEAR a day against {num(s['burn_per_day'])} NEAR burnt in gas. It is held, not burnt.{fn(3)}</p></div>
<div class="grid12">{tape_fig}{senders}{private}{audit}{intents}</div>{xchecks}</section>"""

    # ---- chapter 03: the models ----
    ch3 = calc = ""
    by = results.get("breakeven_years") or {}
    yr = lambda x: "over 100" if x is None else f"{x:.1f}"
    if has and s.get("capture_share"):
        cap = 100 * s["capture_share"]
        calc = f"""<div class="calc" data-burn="{s['burn_coverage']}" data-buy="{s['buyback_coverage']}" data-cap="{s['capture_share']}" data-iss="{iss:g}" data-burnd="{s['burn_per_day']}" data-buyd="{s['buyback_per_day']}">
<div class="ctl"><div class="slider"><label for="s-vol">NEAR Intents volume <b id="o-vol">1.0× today</b></label><input id="s-vol" type="range" min="0.5" max="20" step="0.1" value="1"><div class="hint">${s['intents_volume_musd_latest']:.0f}M a day today</div></div>
<div class="slider"><label for="s-cap">Share of gross Intents fees reaching the buyback account <b id="o-cap">{cap:.0f}%</b></label><input id="s-cap" type="range" min="5" max="100" step="any" value="{cap:.2f}"><div class="hint">About {cap:.0f}% today</div></div>
<div class="slider"><label for="s-iss">Issuance rate <b id="o-iss">{iss:.1f}% a year</b></label><input id="s-iss" type="range" min="0.5" max="{max(3, iss):g}" step="0.1" value="{iss:g}"><div class="hint">HSP-029 proposes 1.6%</div></div>
<button class="reset" id="s-reset" type="button">Reset to today</button></div>
<div class="out" aria-live="polite"><div class="res"><div><div class="eyebrow">Payback</div><div class="big" id="o-pay">{pct(s['payback'])}</div><p>burn + buybacks, as a share of issuance</p></div>
<div><div class="eyebrow">Distance to break-even</div><div class="big" id="o-mult">{s['multiple']:.1f}×</div><p id="o-note">flows must grow this much</p></div></div>
<div><div class="split"><div><span>Burn</span><b class="terra" id="o-b">{pct(s['burn_coverage'], 2)}</b></div><div><span>Buybacks</span><b class="teal" id="o-bb">{pct(s['buyback_coverage'], 2)}</b></div><div><span>NEAR a day</span><b id="o-nd">{num(s['burn_per_day'] + s['buyback_per_day'])}</b></div></div>
<div class="gauge" aria-hidden="true" style="margin-top:22px"><div class="trk"></div><div class="f1" id="g1"></div><div class="f2" id="g2"></div><div class="tick" style="left:100%"><span>Break-even</span></div></div>
<div class="legend" style="margin-top:6px"><span><i style="--c:var(--terra)"></i>Burn</span><span><i style="--c:var(--teal)"></i>Buybacks</span><span><i style="--c:var(--rule)"></i>Unmatched issuance</span></div></div></div></div>"""
    bt, cb = results.get("backtest") or {}, results.get("claims_backtest") or {}
    about = {"persistence": "recent level only", "clock": "level plus a time-of-week profile", "price": "level plus NEAR's price"}
    years_tbl = ("<div style='grid-column:1/span 6'><div class='eyebrow' style='margin-bottom:14px'>Years to break-even, by growth in burn plus buybacks</div>"
                 f"<div class='tw'><table class='tbl'><thead><tr><th>Growth a year</th><th class='r'>Issuance {iss_s}</th><th class='r'>Ramp to 1.6%</th></tr></thead><tbody>"
                 + "".join(f"<tr><td>{g} a year</td><td class='r big'>{yr(v['constant_issuance'])} <span>yrs</span></td><td class='r big teal'>{yr(v['hsp029'])} <span>yrs</span></td></tr>"
                           for g, v in sorted(by.items(), key=lambda kv: int(kv[0][:-1])))
                 + "</tbody></table></div><p class='prose'>Function: <code>run.py: main</code> (<code>breakeven_years</code>, <code>growth_needed_*</code>).</p></div>") if by else ""
    fc_tbl = ""
    if bt:
        n_bt = next(iter(bt.values()))["n"]
        fc_tbl = ("<div style='grid-column:8/span 5'><div class='eyebrow' style='margin-bottom:14px'>Burn forecasters · walk-forward backtest, " + f"{n_bt} forecasts</div>"
                  "<div class='tw'><table class='tbl'><thead><tr><th>Model</th><th class='r'>Pinball</th><th class='r'>Band held</th></tr></thead><tbody>"
                  + "".join(f"<tr><td>{e(m.capitalize())}<small>{about.get(m, '')}</small></td><td class='r'>{v['pinball']:.4f}</td><td class='r'>{100 * v['interval_hit']:.0f}%</td></tr>"
                            for m, v in bt.items())
                  + "</tbody></table></div><p class='prose'>Lower pinball loss is better. The 10–90% bands are too narrow: they hold about two-thirds of outcomes against a nominal 80%. "
                  "Functions: <code>run.py: f_persistence, f_clock, f_price, backtest</code>.</p></div>")
    mlist = ("<div class='mlist'>"
             "<div><h4>Flow identity</h4><p>Mint and burn per epoch from block-header supply; the buyback gain is a balance change. No parameters.</p><code>fetch.py: fetch_epoch · run.py: load</code></div>"
             f"<div><h4>Burn forecasters</h4><p>Three models give 10/50/90% quantiles of NEAR burnt per epoch, backtested walk-forward.</p><code>run.py: f_persistence, f_clock, f_price, backtest</code></div>"
             "<div><h4>Window bands</h4><p>Intervals for the next N epochs, from how much consecutive windows have differed. These are the frozen rounds.</p><code>run.py: window_claims, predict</code></div>"
             "<div><h4>Break-even levers</h4><p>Volume, capture share and issuance, and the years to break-even at a steady growth rate.</p><code>run.py: main (breakeven_years)</code></div></div>")
    detail = ""
    if bt:
        rows = "".join(f"<tr><td>{e(m)}<small>{about.get(m, '')}</small></td><td class='r'><span class='inl' style='width:{60 * v['pinball'] / max(x['pinball'] for x in bt.values()):.0f}px'></span>{v['pinball']:.4f}</td>"
                       f"<td class='r'>{100 * v['skill_vs_persistence']:+.1f}%</td><td class='r'>{100 * v['interval_hit']:.0f}%</td></tr>" for m, v in bt.items())
        detail += (f"<div class='sec'><h4>Burn forecasters</h4><p class='sub'>Each forecast uses only data before its date, up to 30 epochs ahead. Lower pinball loss is better.</p>"
                   f"<div class='tw'><table class='tbl'><tr><th>Model</th><th class='r'>Pinball loss</th><th class='r'>Against persistence</th><th class='r'>10–90% band held</th></tr>{rows}</table></div></div>")
    if cb:
        cell = lambda v: f"{v['hit']} of {v['n']} <small>{100 * v['hit'] / v['n']:.0f}%</small>" if v and v["n"] else "n/a"
        rows = "".join(f"<tr><td>{h} epochs</td><td class='r'>{cell(v.get('payback'))}</td><td class='r'>{cell(v.get('burn_total'))}</td><td class='r'>{cell(v.get('buyback_total'))}</td></tr>"
                       for h, v in sorted(cb.items(), key=lambda kv: int(kv[0])))
        detail += ("<div class='sec'><h4>Window bands</h4><p class='sub'>For a window of the next N epochs: the last N-epoch value, scaled by the 5% to 95% range of how much consecutive "
                   "windows have differed. The table is how often that procedure, run at earlier dates on data available then, contained the outcome. Nominal coverage is 90%.</p>"
                   f"<div class='tw'><table class='tbl'><tr><th>Window</th><th class='r'>Payback</th><th class='r'>NEAR burnt</th><th class='r'>Buyback gain</th></tr>{rows}</table></div></div>")
    detail += ("<div class='sec'><h4>Flow identity</h4><div class='tw'><table class='tbl'><tr><th>Quantity</th><th>Definition</th></tr>"
               "<tr><td>mint</td><td><code>supply(first) - supply(prev last) + burnt(first)</code></td></tr>"
               "<tr><td>burn</td><td><code>burnt(first) + supply(first) - supply(last)</code></td></tr>"
               "<tr><td>payback</td><td><code>(burn + buyback gain) / mint</code></td></tr>"
               "<tr><td>multiple</td><td><code>mint / (burn + buyback gain)</code></td></tr></table></div>"
               "<p class='prose'>Checked by <code>run.py: load</code> (continuity of heights and supply) and against mainnet by <code>verify.py</code>.</p></div>")
    ch3 = f"""<section class="chapter" id="c3" data-t="The models"><div class="ch-head"><div class="ch-num"><span class="n">03</span><span class="eyebrow">The models</span><span class="line"></span></div>
<h2>Three levers move payback. Two of them are governance votes.</h2>
<p>Payback scales with Intents volume and with the share of gross Intents fees reaching the buyback account, and inversely with the issuance rate. HSP-029, passed by NEAR's House of Stake on 2 November 2026 and awaiting ratification, would lower maximum issuance to 1.6% a year.{fn(5)}</p></div>
{calc}<div class="grid12" style="margin-top:56px">{years_tbl}{fc_tbl}</div>{mlist}
<details><summary>Model detail<small>Four models, each a few functions in <code>run.py</code>, rebuilt by <code>python3 run.py</code> with no network; outputs in <code>out/results.json</code></small></summary>{detail}</details></section>"""

    # ---- chapter 04: the path to break-even (path_chapter above) ----
    ch_path = path_chapter(results.get("scenarios"), s, "04", 8) if has else ""
    later = (lambda k: f"{k + (1 if ch_path else 0):02d}")

    # ---- chapter 05: the case, both ways ----
    ch4 = ""
    if has:
        f_ = [("The flow is on chain and exact.", f"{num(s['buyback_per_day'])} NEAR a day reach the buyback account, against {num(s['burn_per_day'])} burnt."),
              ("It comes from one contract.", f"{num(s['inflow_transfers_from_intents'])} of {num(s['inflow_transfers'])} recent transfers were sent by <code>intents.near</code>.")
              if s.get("inflow_transfers") else None,
              ("A separate pipeline agrees.", f"DefiLlama gives {nr(s['llama_buyback_near_per_day'])} NEAR a day for all revenue wallets; balances read from chain give {nr(s['all_revenue_wallets_per_day'])}."),
              ("Capture is a lever.", f"The account receives about {pct(s['capture_share'], 0)} of gross Intents fees. All of it, at today's volume, would be {pct(s['payback_if_all_intents_fees_captured'], 0)} of issuance."),
              ("Issuance is a lever in motion.", f"At 1.6% a year the multiple is {s['multiple_at_1_6_issuance']:.1f}× at today's flows.")]
        a_ = [("Buybacks are not burns.", "The NEAR sits in a multisig account. Supply does not fall and the holders can spend it."),
              ("Payback has been falling." if s["payback"] < s["payback_peak"] else "Payback has swung widely.",
               f"From a peak of {pct(s['payback_peak'])} on {dlong(s['payback_peak_date'])} to {pct(s['payback'])}."),
              ("NEAR Intents is not growing." if s["intents_volume_usd_ratio_1y"] < 1.1 else "NEAR Intents growth is uneven.",
               f"Over a year, daily volume is {s['intents_volume_usd_ratio_1y']:.2f}× and gross fees {s['intents_fees_usd_ratio_1y']:.2f}× (DefiLlama)."),
              ("The flow is concentrated.", f"One application supplies {pct(s['buyback_coverage'] / s['payback'], 0)} of the payback."),
              ("The balance has fallen before.", f"{num(s['buyback_outflow_near'])} NEAR left the account in {s['buyback_outflow_epochs']} of {s['buyback_epochs']} epochs.")]
        try:  # BigQuery: the network got quieter while Intents grew; one point on each side, or neither
            import bq
            bs = bq.summary(bq.load())
            xi, xa, xt = bs.get("intents_share"), bs.get("daily_active_accounts"), bs.get("daily_transactions")
            if xi and xa and xt and xi["per_day_first"]:
                f_.append(("Intents grows as the chain shrinks.", f"intents.near's daily receipts grew {xi['per_day_last'] / xi['per_day_first']:.1f}× since February; "
                                                                  f"its share of all receipts rose from {pct(xi['first'])} to {pct(xi['last'])} (BigQuery)."))
                a_.append(("The chain got quieter.", f"Daily active accounts are {xa['change']} and transactions {xt['change']} since February. Most of the drop in app activity is one app, KaiChing, leaving (BigQuery)."))
        except Exception:
            pass
        side = lambda name, k, xs: (f"<div class='side'><h3>{name}</h3><div class='k'>{k}</div>"
                                    + "".join(f"<div class='pt'><span class='i'>{ROMAN[i]}</span><h4>{h}</h4><p>{p}</p></div>"
                                              for i, (h, p) in enumerate(x for x in xs if x)) + "</div>")
        ch4 = f"""<section class="chapter" id="c4" data-t="The case, both ways"><div class="ch-head"><div class="ch-num"><span class="n">{later(4)}</span><span class="eyebrow">The case, both ways</span><span class="line"></span></div>
<h2>The bear case gets the same page as the bull case.</h2><p>{dict(enumerate(["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven"])).get(len([x for x in a_ if x]), "Several")} points each side, at equal weight. The full argument, with what would change our mind, is in <a href="{REPO}/blob/main/THESIS.md">THESIS.md</a>.</p></div>
<div class="spread">{side('For', 'The flow is on chain, exact, and has levers.', f_)}{side('Against', 'Held is not burnt, and the trend matters.', a_)}</div>
<div class="verdict"><blockquote>“If the buybacks were burnt, net inflation would be {pct(s['inflation_if_buybacks_were_burnt'], 2)} instead of {pct(s['inflation_if_buybacks_were_burnt'] / (1 - s['payback']) * (1 - s['burn_coverage']), 2)}. They are not, yet.”<cite>Inflation if buybacks were burnt · out/results.json</cite></blockquote></div></section>"""

    # ---- chapter 05: check it yourself ----
    cls = {"PASS": "pass", "HIT": "pass", "FALSIFIED": "fail", "MISS": "fail"}
    fmtc = lambda n, x: "pending" if x is None else f"{100 * x:.1f}%" if n == "payback" else f"{x:,.0f}"
    end = datetime.datetime.strptime(s["last_end_utc"], "%Y-%m-%d %H:%M") if s.get("last_end_utc") else None
    newest = max((L["after_end_height"] for L in ledgers or []), default=0)
    board, tally, cards, closes = "", {}, "", []
    for L in sorted(ledgers or [], key=lambda L: (-L["after_end_height"], L["total"])):
        c = L["claims"]["payback"]
        tally[L["verdict"]] = tally.get(L["verdict"], 0) + 1
        board += (f"<tr><td>{day.get(L['after_end_height'], L['after_end_height'])}</td><td>{L['total']} epochs</td>"
                  f"<td class='r'>{fmtc('payback', c['lo'])} to {fmtc('payback', c['hi'])}</td><td class='r'>{fmtc('payback', c['actual'])}</td>"
                  f"<td class='r'>{L['resolved']} of {L['total']}</td><td class='r'><span class='badge {cls.get(L['verdict'], '')}'>{e(L['verdict'])}</span></td></tr>")
    for L in sorted(ledgers or [], key=lambda L: (-L["after_end_height"], L["total"])):
        if L["after_end_height"] != newest and L["verdict"] != "PENDING":
            continue  # closed older rounds live in the scoreboard only
        if L["ends"]:
            ce = datetime.datetime.strptime(L["ends"], "%Y-%m-%d %H:%M UTC")
            when = f"closed {ce.day} {MONTHS[ce.month - 1][:3]} {ce:%H:%M}<small>UTC</small>"
        elif L.get("frozen_t"):
            t = (datetime.datetime.fromtimestamp(L["frozen_t"], datetime.timezone.utc).replace(tzinfo=None)
                 + datetime.timedelta(hours=s["window_days"] * 24 / 100 * L["total"]))
            closes.append(t)
            when = "≈ " + f"{t.day} {MONTHS[t.month - 1][:3]} {t:%H}:00<small>UTC</small>"
        else:
            when = "open"
        dd = lambda n: (lambda c: f"{fmtc(n, c['lo'])} – {fmtc(n, c['hi'])}" + (
            f"<small class='{'hit' if c['verdict'] == 'HIT' else 'miss'}'>actual {fmtc(n, c['actual'])}, {c['verdict']}</small>" if c["actual"] is not None else ""))(L["claims"][n])
        inside = f"{L['hits']} of {L['resolved']} inside burn band" if L["resolved"] else "no epoch closed yet"

        def sofar(L):
            v, c = L.get("so_far"), L["claims"].get("payback")
            if v is None or not c or L["verdict"] != "PENDING":
                return ""
            ok = c["lo"] <= v <= c["hi"]
            return (f"<div class='sofar {'ok' if ok else 'out'}'><span>Payback so far, {L['resolved']} of {L['total']} epochs</span>"
                    f"<b>{pct(v)}</b><small>{'inside' if ok else 'outside'} the committed {pct(c['lo'])}–{pct(c['hi'])}</small></div>")
        frozen = day.get(L["after_end_height"])
        cards += (f"<article class='round'><div class='top'><span class='eyebrow'>{'Frozen ' + dshort(frozen) + ' ' + frozen[:4] if frozen else 'Frozen'}</span>"
                  f"<span class='badge {cls.get(L['verdict'], '')}'>{e(L['verdict'])}</span></div><h4>Next {L['total']} epochs</h4>{track(L, s)}{sofar(L)}"
                  f"<dl><dt>After height</dt><dd>{L['after_end_height']:,}</dd><dt>Committed payback</dt><dd>{dd('payback')}</dd>"
                  + (f"<dt>NEAR burnt</dt><dd>{dd('burn_total')}</dd>" if "burn_total" in L["claims"] else "")
                  + (f"<dt>Buyback gain</dt><dd>{dd('buyback_total')}</dd>" if "buyback_total" in L["claims"] else "")
                  + f"<dt>Closes</dt><dd>{when}</dd></dl>"
                  f"<div><div class='pmeta'><span>{L['resolved']} of {L['total']} epochs closed</span><span>{inside}</span></div>"
                  f"<div class='prog'><i style='width:{100 * L['resolved'] / L['total']:.1f}%'></i></div></div>"
                  f"<div><div class='pmeta'><span>NEAR burnt per epoch, committed 10–90% band ({e(L['table_model'])} model)</span></div>{fan(L['rows'])}</div>"
                  f"<span class='rlive' data-n='{L['total']}' data-h='{L['after_end_height']}' aria-live='polite'></span>"
                  f"<div class='hash'>predictions/{e(L['file'])}<br>sha256 {e(L['commit'])}</div></article>")
    rounds = ""
    if cards:
        tot = [sum(v["payback"][k] for v in cb.values() if "payback" in v) for k in ("hit", "n")]
        held = f"{100 * tot[0] / tot[1]:.0f}%" if tot[1] else "an unknown share"
        tal = ", ".join(f"{n} {k.lower()}" for k, n in sorted(tally.items()))
        if closes:
            a_, b_ = min(closes), max(closes)
            rng_ = (f"{a_.day}–{b_.day} {MONTHS[b_.month - 1][:3]}" if (a_.month, a_.year) == (b_.month, b_.year)
                    else f"{a_.day} {MONTHS[a_.month - 1][:3]} – {b_.day} {MONTHS[b_.month - 1][:3]}") if a_.date() != b_.date() else f"{a_.day} {MONTHS[a_.month - 1][:3]}"
            k = len(closes)
            lead = f"{('Both open rounds close' if k == 2 else 'All ' + str(k) + ' open rounds close') if k > 1 else 'The open round closes'} in this window, each scored by mainnet when it does."
        else:
            rng_, lead = f"{sum(tally.values())} rounds", f"Scored so far: {tal}."
        rounds = (f"<div class='rounds'>{cards}</div><div class='judging'><div class='d'>{rng_}</div><p>{lead} Historically the payback band has held {held} "
                  "of the time, so an occasional miss is expected even when the model is right, and a pass near the bounds is weak support.</p></div>"
                  f"<details><summary>Scoreboard<small>{len(ledgers)} rounds frozen: {tal}. An hourly job scores each round as its epochs close; nothing is ever removed. Freezing new rounds is paused during judging.</small></summary>"
                  "<div class='tw'><table class='tbl'><tr><th>Frozen</th><th>Window</th><th class='r'>Committed payback</th><th class='r'>Actual</th>"
                  f"<th class='r'>Epochs closed</th><th class='r'>Verdict</th></tr>{board}</table></div></details>")
    # recorded output
    st = _recorded("selftest.json")
    if st and st.get("output") is not None:
        st_lines = st["output"].rstrip("\n").splitlines()
        st_html = (term(st.get("command") or "python3 test_run.py", st_lines[-12:],
                        None if len(st_lines) <= 12 else f"... last 12 of {len(st_lines)} lines")
                   + prov_html(st, "Recorded").replace("</b>:", f"</b>{', exit code ' + str(st.get('exit')) if st.get('exit') else ''}:"))
    else:
        st_html = term("python3 test_run.py") + "<p class='prov'>Not recorded yet: the scheduled GitHub Actions run records it before every build. " \
                                                f"<a href='{WORKFLOW}'>Every run's full log is public.</a></p>"
    try:
        vlines = open(os.path.join(HERE, "VERIFY.txt"), encoding="utf-8").read().rstrip("\n").splitlines()
        seed = next((ln.split("seed=")[1].split()[0] for ln in vlines if "seed=" in ln), None)
        vwhen = next((ln.split(" at ", 1)[1].split(" UTC")[0] + " UTC" for ln in vlines if " at " in ln and "UTC" in ln), None)
        n_ = vlines[0].split("n=")[1].split()[0] if vlines and "n=" in vlines[0] else "3"
        v_html = (term(f"python3 verify.py {n_} {seed}" if seed else "python3 verify.py", vlines, copy=True)
                  + f"<p class='prov'><b>Recorded {e(vwhen or '')}{' with seed ' + e(seed) if seed else ''}</b>, in "
                    f"<a href='{REPO}/blob/main/VERIFY.txt'>VERIFY.txt</a>. Pick your own seed: the free endpoints rate-limit, so the scheduled job does not run it. "
                    "The “Check a random epoch” button in chapter 02 does the same check in your browser.</p>")
    except OSError:
        v_html = term("python3 verify.py 3 12345")
    run_fallback = term("python3 run.py") + "<p class='prov'>This build's output was not recorded (the page was rendered outside <code>python3 run.py</code>). " \
                                           f"<a href='{WORKFLOW}'>Every run's full log is public.</a></p>"
    cap = lambda k, body: MARK[0].format(k) + body + MARK[1].format(k)
    steps = [("Get the repository", "Python 3.9 or later, no packages, no keys.", term(f"git clone {REPO}\ncd Coverage")),
             ("Rebuild offline", "Every figure on this page, from the cached chain data, in about two seconds with no network. "
              "Below is the output of the build that produced this page, ending with the result hash.", cap("run", run_fallback)),
             ("Run the self-test", "Scoring maths, data hashes, and refusal of a cache or a forecast round with one value changed.", st_html),
             ("Check against mainnet", "Random epochs are refetched from the chain and must match the cache exactly.", v_html),
             ("Score the rounds", "Fetch the epochs that closed since; run.py prints PASS or FALSIFIED per round (the LEDGER lines above).",
              term("python3 fetch.py --epochs 45 && python3 run.py"))]
    steps_html = "".join(f"<div class='step'><span class='sn'>{i + 1}</span><div><h4>{a}</h4><p>{b}</p></div><div>{c}</div></div>" for i, (a, b, c) in enumerate(steps))
    ch5 = f"""<section class="chapter" id="c5" data-t="Check it yourself"><div class="ch-head"><div class="ch-num"><span class="n">{later(6)}</span><span class="eyebrow">Check it yourself</span><span class="line"></span></div>
<h2>Forecasts frozen in Bitcoin, scored by the chain while you judge.</h2><p>Each round was frozen before the epochs it describes existed, and its hash is anchored with OpenTimestamps. <code>run.py</code> refuses a round that is not exactly what the code derives from the data up to its height.{fn(7)}</p></div>
{rounds}<div style="margin-top:72px" id="reproduce"><div class="eyebrow" style="margin-bottom:14px">Reproduce every number · recorded output, so you can check without running anything</div>
<div class="steps">{steps_html}</div>
<div class="hashbox"><div class="l"><div class="eyebrow">Result hash</div><h3>If your run prints a different hash, the page and the data disagree.</h3></div><div class="r">{cap('hash', hash_html(sha, None))}</div></div></div></section>"""

    # ---- notes and sources ----
    notes = [f"Headline window: last 100 epochs ({s['window_days']:.1f} days) ending {e(s.get('last_end_utc') or s['last'])} UTC at height {s['last_height']:,}. "
             f"Payback {s['payback']}; burn coverage {s['burn_coverage']}; buyback coverage {s['buyback_coverage']}. <code>out/results.json</code> → summary." if has else
             f"Headline window ending at height {s['last_height']:,}.",
             "Mint = supply(first) − supply(prev last) + burnt(first); burn = burnt(first) + supply(first) − supply(last), per epoch from block-header "
             "<code>total_supply</code>. <code>data/epochs.csv</code>.",
             "<code>view_account</code> balance of <code>buybacks.multisignature.near</code> at each epoch's last block, differenced (<code>data/buybacks.csv</code>). "
             "Senders from NearBlocks with transaction hashes (<code>data/inflows.csv</code>)."
             + (f" A {num(s['lump_transfers_near'])} NEAR transfer from another wallet is excluded as a lump (<code>run.py: mark_lumps</code>)." if s.get("lump_transfers") else ""),
             f"DefiLlama summary/dexs/near-intents and fees/near-intents dailyHoldersRevenue, {s.get('intents_weeks', 0)} weeks (<code>data/llama.csv</code>). Third-party context only.",
             (f"Lever model: payback = burn/mint × {iss:g}/i + buyback/mint × volume × capture/{s['capture_share']:.3f} × {iss:g}/i, with i the issuance rate in % "
              f"(today's maximum, {iss_s}, from <code>data/protocol.json</code>). All Intents fees captured at today's volume gives {pct(s['payback_if_all_intents_fees_captured'])}.")
             if has and s.get("capture_share") else "Lever model: see run.py.",
             f"<code>python3 run.py</code> prints <code>RESULT sha256={sha[:8]}…{sha[-4:]}</code>. <code>test_run.py</code> fails if any epoch of the buyback account is unexplained.",
             f"<code>predictions/</code>, each round with an <code>.ots</code> proof: <code>ots verify predictions/&lt;file&gt;.ots</code>. "
             f"Bands are 5–95% from window-to-window variation.",
             # 8: the path to break-even
             "Scenarios: <code>run.py: scenarios</code> and <code>growth_measures</code>; bear, base and bull are the lowest, median and highest of four year-long "
             "growth rates of NEAR Intents volume and gross fees (DefiLlama). HSP-029: "
             "https://gov.near.org/t/hsp-029-establish-a-24-month-issuance-ramp-to-a-1-6-target-rate-of-near-token-emissions/42644, "
             "passed by the House of Stake on 2026-11-02 (99.96% of voting power, 36 voters). The Security Council veto window closes 2026-11-16 16:48 UTC; "
             "without a veto it is ratified, a 90-day grace period follows (earliest start about 2027-02-14), and validators must adopt a nearcore release. "
             "As of 2026-11-13 no veto and no release had been reported."]
    try:
        srcs = json.load(open(os.path.join(HERE, "data", "sources.json")))
    except (OSError, ValueError):
        srcs = {}
    host = lambda u: u.split("//")[-1].split("/")[0].split()[0]
    data_list = "".join(
        f"<li><b><code>data/{e(f)}</code></b> · {e(', '.join(sorted({host(u) for u in (v.get('urls') if isinstance(v.get('urls'), list) else [str(v.get('urls', ''))]) if u})))}"
        f"{' · fetched ' + e(v['fetched_utc'][:10]) if v.get('fetched_utc') else ''}</li>" for f, v in sorted(srcs.items()))
    notes_html = (f"<footer class='notes'><div><div class='eyebrow'>Notes &amp; sources</div></div><div><ol>"
                  + "".join(f"<li id='n{i + 1}'>{n}</li>" for i, n in enumerate(notes)) + "</ol>"
                  + (f"<h4>Data, each file hashed in data/sources.json and checked by test_run.py</h4><ul>{data_list}</ul>" if data_list else "") + "</div></footer>")

    # ---- chapter 06: network activity (BigQuery); bq.py reads data/bq/*.csv, which run.py and the result hash never use ----
    import bq
    ch6, bq_data = bq.chapter(later(5), "c6")

    chapters = [(c, t) for c, t, body in (("c1", "The claim", ch1), ("c2", "The flow", ch2), ("c3", "The models", ch3),
                                          ("c-path", "The path to break-even", ch_path), ("c4", "The case, both ways", ch4), ("c6", "Network activity", ch6),
                                          ("c5", "Check it yourself", ch5)) if body]
    idx = "".join(f"<li><a href='#{c}'><span class='n'>{i + 1:02d}</span><span class='t'>{t}</span><span class='bar'><i></i></span></a></li>" for i, (c, t) in enumerate(chapters))
    midx = "".join(f"<li><a href='#{c}'><span>{i + 1:02d}</span>{t}</a></li>" for i, (c, t) in enumerate(chapters))
    navs = {"c1": "The claim", "c2": "The flow", "c3": "The models", "c-path": "Break-even", "c4": "Both ways", "c5": "Check it", "c6": "Network"}
    nav = "".join(f"<a href='#{c}'>{navs[c]}</a>" for c, _ in chapters) + f"<a href='{REPO}'>GitHub</a>"
    foot = (f"<div class='foot'><b>{s['multiple']:.1f}×</b>flows must grow to match issuance at {iss_s} a year; {s['multiple_at_1_6_issuance']:.1f}× at 1.6%.</div>" if has else "")

    data = dict(s=s, series=results["series"], weekly=results.get("weekly", []), ruler=rd,
                tape=dict(tape, len=epoch_len) if tape else None, **bq_data)
    meta = f"NEAR mainnet · {span} · {s['epochs']:,} epochs"
    import verdict
    vi = verdict.html(results, e)
    inv = (f"<div class='inv'><div class='eyebrow'>Verdict for an investor</div><ul>{vi}</ul></div>" if vi else "")
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Coverage: what NEAR pays back</title>
<meta name="description" content="{e(title)}"><meta name="color-scheme" content="light dark">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{CSS}{PATH_CSS}</style></head><body><div class="wrap">
<header class="mast"><div class="brand"><b>Coverage</b><span>A research report on what NEAR pays back</span></div>
<nav aria-label="Chapters">{nav}</nav><a class="toggle quick" href="quick.html">60-second version</a><button class="toggle" id="theme" type="button" aria-label="Switch between paper and ink"><i></i><span>Ink</span></button></header>
<section class="hero" id="top" aria-label="{e(meta)}"><div class="meta"><span class="eyebrow">NEAR mainnet</span><span class="eyebrow">{span}</span><span class="eyebrow">{s['epochs']:,} epochs</span></div>
<h1>{h1}</h1><a class="quick-cta" href="quick.html"><span class="ic">⏱</span><span><b>Short on time? Read it in 60 seconds</b><small>One idea per step, in plain words</small></span><span class="ar">→</span></a><p class="dek">{dek}</p><p class="byline">{byline}</p>{inv}</section>
{ruler}{live}{scale}
<div class="body"><aside class="index" aria-label="Contents"><div class="eyebrow">Contents</div><ol id="idx">{idx}</ol>{foot}</aside>
<main><div class="mobile-index"><details><summary><span class="row"><b id="mi-t">01 {chapters[0][1] if chapters else ''}</b><span id="mi-n" class="eyebrow">1 / {len(chapters)}</span></span><span class="p" style="display:block"><i id="mi-p"></i></span></summary><ol>{midx}</ol></details></div>
{ch1}{ch2}{ch3}{ch_path}{ch4}{ch6}{ch5}</main></div>
{notes_html}
<div class="colophon"><span>Coverage · MIT licence · <a href="{REPO}">{REPO.split('//')[1]}</a> · result <code>{sha[:12]}</code></span><span>Set in Instrument Serif &amp; Inter. Teal comes back to the token; terracotta is burnt.</span></div>
</div><script type="application/json" id="data">{blob}</script>
<script>{JS}</script></body></html>"""
