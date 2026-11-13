"""Render out/results.json (+ optional ledger) to one static HTML file. No dependencies, no external assets."""
import csv, datetime, html, json, os

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
body{margin:0;background:var(--bg);color:var(--ink);font:0.9375rem/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
-webkit-font-smoothing:antialiased;font-optical-sizing:auto}
a{color:inherit;text-underline-offset:3px;text-decoration-thickness:1px}a:hover{color:var(--back)}
:focus-visible{outline:2px solid var(--back);outline-offset:2px}
code,.mono{font:0.78125rem/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere}
nav{position:sticky;top:0;z-index:var(--z-nav);background:color-mix(in oklch,var(--bg) 72%,transparent);
-webkit-backdrop-filter:blur(20px) saturate(180%);backdrop-filter:blur(20px) saturate(180%);border-bottom:1px solid color-mix(in oklch,var(--rule) 60%,transparent)}
nav div{max-width:1120px;margin:0 auto;padding:0 20px;display:flex;gap:22px;align-items:center;height:44px;
overflow-x:auto;white-space:nowrap;font-size:0.84375rem;scrollbar-width:none}
nav a,nav b{flex:none}nav b{font-size:0.9375rem;letter-spacing:-.01em;margin-right:6px}nav a{text-decoration:none;color:var(--ink2)}
nav a:hover,nav a[aria-current]{color:var(--ink)}nav a[aria-current]{font-weight:600}nav a:last-child{margin-left:auto;color:var(--ink)}
main{max-width:1120px;margin:0 auto;padding:0 20px 80px}
section{padding-top:72px}section>h2{font-size:1.875rem;line-height:1.15;letter-spacing:-.025em;margin:0 0 10px;text-wrap:balance}section>h2+p{font-size:1rem}
h3{font-size:0.9375rem;line-height:1.4;margin:0;font-weight:600;text-wrap:balance}
p{margin:0 0 12px;color:var(--ink2);max-width:72ch;text-wrap:pretty}
.stamp{color:var(--ink2);margin:40px 0 14px}
h1{font-size:2.375rem;line-height:1.12;letter-spacing:-.025em;margin:0 0 14px;max-width:24ch;text-wrap:balance}
.lede{font-size:1.0625rem;max-width:64ch}
.strip{margin:44px 0 0}.strip h3{font-weight:500;color:var(--ink2);font-size:0.84375rem;margin-bottom:8px}
.bar{display:flex;height:44px;background:var(--rest);border:1px solid var(--ink)}.bar.thin{height:18px}
.bar i{display:block;min-width:3px;transition:width .2s cubic-bezier(.22,1,.36,1)}.bar .bk{background:var(--back)}.bar .bn{background:var(--burn)}
.key{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:6px 28px;margin:12px 0 0;padding:0;list-style:none;font-size:0.84375rem;color:var(--ink2)}
.key li{display:flex;gap:8px;align-items:baseline}.key b{color:var(--ink);font-variant-numeric:tabular-nums}
.sw{flex:none;width:10px;height:10px;display:inline-block;border:1px solid var(--ink);transform:translateY(1px)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin:36px 0 0;border-top:1px solid var(--ink)}
.facts div{padding:14px 20px 14px 0;border-bottom:1px solid var(--rule)}
.facts dt{font-size:0.8125rem;color:var(--ink2)}.facts dd{margin:2px 0 0;font-size:2rem;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.facts small{display:block;font-size:0.78125rem;font-weight:400;letter-spacing:0;color:var(--ink2)}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:0 40px;margin-top:20px}
figure{margin:0;padding:18px 0 20px;border-top:1px solid var(--rule);position:relative;min-width:0}
figure.lead{grid-column:1/-1;border-top-color:var(--ink)}
.sub{font-size:0.78125rem;margin:3px 0 10px;max-width:none}.src{font-size:0.71875rem;margin:8px 0 0;max-width:none}.src code{font-size:0.6875rem}
svg{touch-action:pan-y;display:block;width:100%;height:auto;overflow:visible}svg text{fill:var(--ink2);font:0.6875rem system-ui,sans-serif;font-variant-numeric:tabular-nums}
.tip{position:absolute;z-index:var(--z-tip);pointer-events:none;background:var(--ink);color:var(--bg);padding:3px 8px;
font-size:0.75rem;white-space:nowrap;transform:translate(-50%,-135%);display:none;font-variant-numeric:tabular-nums}
.wrap{overflow-x:auto;margin:14px 0 0}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:0.875rem}
th,td{text-align:right;padding:8px 0 8px 18px;border-bottom:1px solid var(--rule);vertical-align:top}
th:first-child,td:first-child{text-align:left;padding-left:0}th{letter-spacing:.01em;color:var(--ink2);font-weight:500;font-size:0.78125rem;border-bottom-color:var(--ink)}
td small{color:var(--ink2)}.pass{color:var(--good);font-weight:600}.fail{color:var(--bad);font-weight:600}
.model{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:8px 40px;padding:22px 0;border-top:1px solid var(--rule)}
.model:first-of-type{border-top-color:var(--ink);margin-top:20px}.model h3{font-size:1rem;margin-bottom:6px}
.model .wrap{margin:0}.how{font-size:0.78125rem;color:var(--ink2);margin:8px 0 0}
.inl{display:inline-block;height:8px;background:var(--ink2);vertical-align:middle;margin-right:8px}
.calc label{display:block;margin:0 0 16px;font-size:0.875rem}.calc output{float:right;color:var(--ink2);font-variant-numeric:tabular-nums}
.calc input{display:block;width:100%;margin-top:6px;accent-color:var(--back);touch-action:pan-y}.calc .bar i{transition:none}
#o-pay{margin:8px 0 0;color:var(--ink);font-weight:600}
.round{padding:22px 0;border-top:1px solid var(--rule)}.round:first-of-type{border-top-color:var(--ink);margin-top:20px}
.round header{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;margin-bottom:4px}.round h3{font-size:1rem}
.pill{font-size:0.75rem;font-weight:600;padding:1px 8px;border:1px solid currentColor;border-radius:99px}
.pill.pending{color:var(--ink2)}.pill.pass{color:var(--good)}.pill.fail{color:var(--bad)}
.rgrid{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:8px 40px;margin-top:10px}
.claim{display:grid;grid-template-columns:minmax(0,1fr) 108px;gap:2px 12px;padding:9px 0;border-bottom:1px solid var(--rule);font-size:0.84375rem}
.claim b{font-weight:600}.claim span{color:var(--ink2);font-variant-numeric:tabular-nums}.claim .v{text-align:right;font-weight:600}
.claim svg{grid-column:1/-1;margin-top:2px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:0 40px;margin-top:20px}
.two h3{padding:10px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--rule)}
.two ul{margin:0;padding:0;list-style:none}.two li{padding:10px 0;border-bottom:1px solid var(--rule);color:var(--ink2);font-size:0.875rem}
.two li b{color:var(--ink);font-weight:600}
.cmd{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:6px 40px;padding:16px 0;border-top:1px solid var(--rule)}
.cmd:first-of-type{border-top-color:var(--ink);margin-top:20px}.cmd p{margin:0;font-size:0.875rem}
pre{border-radius:6px;margin:0;padding:10px 64px 10px 12px;background:var(--panel);border:1px solid var(--rule);position:relative;white-space:pre-wrap;overflow-wrap:anywhere;
font:0.78125rem/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
pre .out{color:var(--ink2)}
pre button{position:absolute;top:6px;right:6px;font:0.75rem system-ui,sans-serif;padding:2px 8px;background:var(--bg);color:var(--ink);
border:1px solid var(--rule);border-radius:4px;cursor:pointer}pre button:hover{border-color:var(--ink)}pre button:active{background:var(--panel);transform:scale(.97)}pre button{transition:transform .1s ease-out}
footer{margin-top:56px;padding-top:14px;border-top:1px solid var(--ink);color:var(--ink2);font-size:0.78125rem}
.hero{--h-ink:#eef3f2;--h-ink2:#a9b8b5;--h-rule:#2a3533;background:#0e1514;color:var(--h-ink)}
.hin{max-width:1120px;margin:0 auto;padding:1px 20px 34px}.hero p{color:var(--h-ink2)}.hero code{color:var(--h-ink)}
.hero h1{font-size:3.375rem;line-height:1.04;letter-spacing:-.035em;max-width:none;margin:0}
.htop{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,4fr);gap:20px 48px;align-items:end}.htop .lede{margin:0 0 6px;font-size:1rem}
@media (max-width:900px){.htop{grid-template-columns:minmax(0,1fr)}}
.stamp{font-size:.8125rem}
.livebar{margin:28px 0 0;border-top:1px solid var(--h-rule);border-bottom:1px solid var(--h-rule)}
.lstat{margin:0;padding:11px 0 0;font-size:.8125rem;display:flex;align-items:center;gap:9px;max-width:none}
.lstat i{flex:none;width:7px;height:7px;border-radius:50%;background:#43d1b7;animation:beat 2.4s ease-out infinite}
@keyframes beat{0%{box-shadow:0 0 0 0 rgba(67,209,183,.6)}70%,100%{box-shadow:0 0 0 7px rgba(67,209,183,0)}}
.hero dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:0 28px;margin:0}.livebar dl div{padding:9px 0 13px}
.hero dt{font-size:.75rem;color:var(--h-ink2)}.hero dd{margin:1px 0 0;font-size:1.25rem;font-weight:600;letter-spacing:-.015em;font-variant-numeric:tabular-nums}
.hero dd small,.read h3 small{font-size:.75rem;font-weight:400;color:var(--h-ink2);letter-spacing:0;margin-left:3px}
.tape{margin-top:30px}.tape h2{font-size:1.0625rem;margin:0 0 4px;letter-spacing:-.01em}.tape>p{font-size:.8125rem;max-width:92ch;margin-bottom:12px}
.tape .k{display:inline-block;width:9px;height:9px;margin:0 5px 0 2px}
#tape{display:block;width:100%;height:320px;cursor:crosshair;touch-action:pan-y}
.read{margin-top:12px;min-height:5.4rem}.read h3{font-size:.9375rem;margin-bottom:6px}.read dl{grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 28px}.read dd{font-size:1rem}.hts{font-size:.875rem;font-weight:500;white-space:nowrap}
.vrow{margin-top:18px;display:flex;flex-wrap:wrap;gap:10px}
.vrow button{font:inherit;font-size:.875rem;font-weight:600;color:var(--h-ink);background:transparent;border:1px solid #4a5a57;border-radius:6px;padding:9px 16px;cursor:pointer;
transition:transform .1s ease-out,border-color .15s,background-color .15s}
.vrow button:hover{border-color:var(--h-ink)}.vrow button:active{transform:scale(.97)}.vrow button:disabled{opacity:.45;cursor:progress}
#vsel{background:#43d1b7;border-color:#43d1b7;color:#06201c}#vsel:hover{background:#63ddc6;border-color:#63ddc6}
.vrow button:focus-visible,#tape:focus-visible{outline:2px solid #43d1b7;outline-offset:2px}
.check{margin-top:18px;border-top:1px solid var(--h-rule);padding-top:14px}.check:empty{display:none}.check h3{font-size:.9375rem;margin-bottom:2px}
.check table{font-size:.875rem;max-width:820px}.check th{color:var(--h-ink2);border-bottom-color:#4a5a57}.check td{border-bottom-color:var(--h-rule)}
.check .eq{color:#43d1b7;font-weight:600}.check .ne{color:#ff7b72;font-weight:600}.check .wait{color:var(--h-ink2);animation:fade .9s ease-in-out infinite alternate}
@keyframes fade{from{opacity:.3}to{opacity:1}}
.check p{font-size:.8125rem;margin:10px 0 0;max-width:none}.check p.verdict{font-size:.9375rem;font-weight:600;color:#43d1b7;margin-top:12px}.check p.verdict.no{color:#ff7b72}
.rmeta{color:var(--ink2);font-size:.875rem}.rlive{flex-basis:100%;color:var(--back);font-size:.875rem;font-weight:500}.rlive:empty{display:none}
@media (max-width:720px){.hero h1{font-size:2.125rem}#tape{height:190px}h1{font-size:1.8125rem}.lede{font-size:1rem}.model,.rgrid,.cmd{grid-template-columns:minmax(0,1fr)}section{padding-top:44px}
.facts div{padding-right:12px}pre button{display:none}}
.lsrc{color:var(--h-ink2);font-weight:400}.lfoot{margin:0;padding:0 0 12px;font-size:.75rem;color:var(--h-ink2);max-width:none}.lfoot[hidden]{display:none}
.lede b{color:var(--h-ink);font-weight:600;font-variant-numeric:tabular-nums}
details{border-top:1px solid var(--rule);margin-top:24px}details[open]{border-bottom:1px solid var(--rule)}
details>summary{cursor:pointer;list-style:none;padding:14px 28px 14px 0;position:relative;font-weight:600;font-size:1rem;line-height:1.4;text-wrap:balance}
details>summary::-webkit-details-marker{display:none}
details>summary::after{content:"";position:absolute;right:4px;top:50%;width:8px;height:8px;margin-top:-6px;border:solid var(--ink2);border-width:0 2px 2px 0;transform:rotate(45deg);transition:transform .15s ease-out}
details[open]>summary::after{transform:rotate(-135deg);margin-top:-1px}
details>summary:hover{color:var(--back)}details>summary small{display:block;font-weight:400;font-size:.875rem;color:var(--ink2);margin-top:2px}
details>:last-child{margin-bottom:20px}.calc{margin-top:14px}.calc+details{margin-top:28px}
@media (max-width:480px){.livebar dl{grid-template-columns:repeat(2,minmax(0,1fr));gap:0 16px}.livebar dd{font-size:1.0625rem}.livebar dd small{display:block;margin:0}}
@media (max-width:720px){nav div{padding:0 20px;gap:18px;-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 var(--fl,0px),#000 calc(100% - var(--fr,32px)),transparent 100%);
mask-image:linear-gradient(90deg,transparent 0,#000 var(--fl,0px),#000 calc(100% - var(--fr,32px)),transparent 100%)}nav a:last-child{margin-left:0}}
@media (prefers-reduced-motion:reduce){details>summary::after{transition:none}.lstat i,.check .wait{animation:none}.vrow button{transition:none}html{scroll-behavior:auto}.bar i,pre button{transition:none}pre button:active{transform:none}}
@media (prefers-reduced-transparency:reduce){nav{background:var(--bg);-webkit-backdrop-filter:none;backdrop-filter:none;border-bottom-color:var(--rule)}}
@media (prefers-contrast:more){:root{--ink2:var(--ink);--rule:var(--ink)}nav{background:var(--bg);-webkit-backdrop-filter:none;backdrop-filter:none}}
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
const NB=document.querySelector('nav div');if(NB){const nf=()=>{const m=NB.scrollWidth-NB.clientWidth;NB.style.setProperty('--fl',NB.scrollLeft>4?'32px':'0px');NB.style.setProperty('--fr',m-NB.scrollLeft>4?'32px':'0px')};
 NB.addEventListener('scroll',nf,{passive:true});addEventListener('resize',nf);nf()}
const NAV=[...document.querySelectorAll('nav a[href^="#"]')];if('IntersectionObserver' in window){
 const io=new IntersectionObserver(es=>es.forEach(x=>{if(x.isIntersecting)NAV.forEach(a=>a.getAttribute('href')=='#'+x.target.id?a.setAttribute('aria-current','true'):a.removeAttribute('aria-current'))}),{rootMargin:'-45% 0px -50% 0px'});
 document.querySelectorAll('section[id]').forEach(s=>io.observe(s))}
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
 const show=e=>{const r=svg.getBoundingClientRect(),px=(e.clientX-r.left)/r.width*W;
  let i=0;for(let j=1;j<xs.length;j++)if(Math.abs(sx(xs[j])-px)<Math.abs(sx(xs[i])-px))i=j;
  ch.setAttribute('x1',sx(xs[i]));ch.setAttribute('x2',sx(xs[i]));ch.setAttribute('visibility','visible');
  dot.setAttribute('cx',sx(xs[i]));dot.setAttribute('cy',sy(ys[i]));dot.setAttribute('visibility','visible');
  tip.textContent=P[i].date+': '+ys[i].toFixed(dp+1)+unit;tip.style.display='block';
  tip.style.left=(svg.offsetLeft+sx(xs[i])/W*r.width)+'px';tip.style.top=(svg.offsetTop+sy(ys[i])/Ht*r.height)+'px'};
 svg.addEventListener('pointermove',show);svg.addEventListener('pointerdown',show);
 svg.addEventListener('pointerleave',()=>{tip.style.display='none';ch.setAttribute('visibility','hidden');dot.setAttribute('visibility','hidden')});
});
const TD=document.getElementById('tape-data');if(TD){const T=JSON.parse(TD.textContent),cv=document.getElementById('tape'),cx=cv.getContext('2d'),
 N=x=>Number(x)/1e24,E=T.E.map(r=>({s:r[0],e:r[1],p:r[2],t:r[3],mint:N(r[4]),burn:N(r[5]),buy:r[6]==null?null:N(r[6]),lump:r[7],raw:r}));
 E.forEach(d=>{d.share=(d.burn+(d.lump?0:Math.max(d.buy||0,0)))/d.mint});
 const hist=E.filter(d=>d.e<=T.snap),fut=E.filter(d=>d.e>T.snap),slots=Math.max(0,...T.rounds.map(r=>r.n)),W=100,
 sorted=hist.filter(d=>!d.lump).map(d=>d.share).sort((a,b)=>a-b),ymax=sorted[Math.floor(sorted.length*.985)]*1.15,
 roll=hist.map((d,i)=>{if(i<W-1)return null;let a=0,m=0;for(let j=i-W+1;j<=i;j++){if(hist[j].buy==null)return null;a+=hist[j].burn+(hist[j].lump?0:hist[j].buy);m+=hist[j].mint}return a/m}),
 C={ink:'#eef3f2',ink2:'#a9b8b5',rule:'#2a3533',back:'#43d1b7',burn:'#f2915a',bad:'#ff7b72'},
 idx=t=>{let k=hist.findIndex(d=>d.t>=t);return k<0?hist.length-1:k},
 marks=[[hist.findIndex(d=>d.buy>0),'buybacks begin'],[hist.findIndex(d=>d.lump),'wallet transfer, excluded'],
  [idx(Date.UTC(2026,9,27)/1000),'swaps go private'],[hist.length-1,'forecasts frozen']].filter(m=>m[0]>=0);
 let sel=hist.length-1,pin=false,w=0,h=0,geo;
 const fmt=(x,d=0)=>x.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}),
 when=t=>new Date(t*1000).toISOString().slice(0,16).replace('T',' ')+' UTC',
 nice=t=>new Date(t*1000).toLocaleString('en-GB',{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC'})+' UTC',all=()=>hist.concat(fut);
 function layout(){const r=cv.getBoundingClientRect(),dpr=window.devicePixelRatio||1;w=r.width;h=r.height;cv.width=w*dpr;cv.height=h*dpr;cx.setTransform(dpr,0,0,dpr,0,0);
  const top=w<560?10:60,bot=h-18,futW=slots?Math.max(90,w*.15):0,gap=slots?14:0,hw=w-futW-gap;
  geo={top,bot,hw,fx:hw+gap,sw:slots?futW/slots:0,cw:hw/hist.length,y:v=>bot-Math.min(v,ymax)/ymax*(bot-top)}}
 function xOf(i){return i<hist.length?i*geo.cw:geo.fx+(i-hist.length)*geo.sw}
 function draw(){const g=geo;cx.clearRect(0,0,w,h);cx.font='11px system-ui,sans-serif';cx.textBaseline='middle';
  for(let v=.1;v<ymax;v+=.1){cx.fillStyle=C.rule;cx.fillRect(0,g.y(v),w,1);cx.fillStyle=C.ink2;cx.textAlign='left';cx.fillText(Math.round(v*100)+'%',2,g.y(v)-7)}
  T.rounds.slice().sort((a,b)=>b.n-a.n).forEach(r=>{const x=g.fx,ww=r.n*g.sw,y1=g.y(r.hi),y0=g.y(r.lo);
   cx.fillStyle='rgba(67,209,183,.13)';cx.fillRect(x,y1,ww,y0-y1);cx.strokeStyle='rgba(67,209,183,.6)';cx.lineWidth=1;cx.strokeRect(x+.5,y1+.5,ww-1,y0-y1-1)});
  all().forEach((d,i)=>{const x=xOf(i),cw=Math.max(1,(i<hist.length?g.cw:g.sw)-(i<hist.length?(g.cw>3?1:0):2));
   if(d.lump){cx.fillStyle='rgba(169,184,181,.35)';cx.fillRect(x,g.top,Math.max(1,cw),g.bot-g.top);return}
   const yb=g.y(d.burn/d.mint),yt=g.y(d.share);cx.fillStyle=C.burn;cx.fillRect(x,yb,cw,g.bot-yb);cx.fillStyle=C.back;cx.fillRect(x,yt,cw,yb-yt);
   if(d.share>ymax){cx.fillStyle=C.ink;cx.fillRect(x,g.top,cw,2)}
   if(d.buy<0){cx.fillStyle=C.bad;cx.fillRect(x-1,g.bot+3,Math.max(3,cw),3)}});
  for(let j=fut.length;j<slots;j++){cx.fillStyle=C.rule;cx.fillRect(g.fx+j*g.sw+1,g.bot-1,g.sw-2,1)}
  cx.beginPath();let on=false;roll.forEach((v,i)=>{if(v==null)return;const x=xOf(i)+g.cw/2,y=g.y(v);on?cx.lineTo(x,y):cx.moveTo(x,y);on=true});cx.strokeStyle=C.ink;cx.lineWidth=1.5;cx.stroke();
  cx.fillStyle=C.ink;cx.fillRect(0,g.bot,w,1);
  if(slots){cx.fillStyle=C.ink2;cx.fillRect(g.fx-7,g.top,1,g.bot-g.top)}
  marks.forEach((m,k)=>{const x=Math.round(xOf(m[0]));cx.fillStyle='rgba(238,243,242,.35)';cx.fillRect(x,w<560?g.top-6:2+k*13,1,g.bot-(w<560?g.top-6:2+k*13));
   if(w>=560){cx.fillStyle=C.ink2;cx.textAlign=x>w*.7?'right':'left';cx.fillText(m[1],x+(x>w*.7?-5:5),8+k*13)}});
  if(slots&&w>=560){cx.fillStyle=C.back;cx.textAlign='left';cx.fillText('committed band',g.fx+2,g.y(T.rounds[0].hi)-8)}
  const d=all()[sel],x=xOf(sel),cw=sel<hist.length?g.cw:g.sw;cx.fillStyle='rgba(238,243,242,.9)';cx.fillRect(x+cw/2-.5,g.top-6,1,g.bot-g.top+10);
  cx.textAlign='left';cx.fillStyle=C.ink2;cx.fillText(when(hist[0].t).slice(0,10),0,h-6);cx.textAlign='right';cx.fillText(when(hist[hist.length-1].t).slice(0,10),g.hw,h-6);
  const cell=(k,v)=>`<div><dt>${k}</dt><dd>${v}</dd></div>`;
  document.getElementById('read').innerHTML=`<h3>Epoch ending ${nice(d.t)}`+(sel>=hist.length?' <small>closed after the forecasts were frozen</small>':'')+'</h3><dl>'+
   cell('Minted',fmt(d.mint)+' <small>NEAR</small>')+cell('Burnt in gas fees',fmt(d.burn,1)+' <small>NEAR</small>')+
   (d.buy==null?cell('Buyback gain','not cached'):d.lump?cell('Moved in from other wallets, excluded',fmt(d.buy)+' <small>NEAR</small>'):cell('Buyback gain',fmt(d.buy)+' <small>NEAR</small>')+cell('Share of mint matched',(d.share*100).toFixed(1)+'%'))+
   cell('Block heights','<span class="hts">'+d.s+' to '+d.e+'</span>')+'</dl>'}
 function pick(e){const r=cv.getBoundingClientRect(),px=e.clientX-r.left,n=all().length;
  let i=px<geo.fx-7?Math.floor(px/geo.cw):hist.length+Math.floor((px-geo.fx)/geo.sw);return Math.max(0,Math.min(n-1,Math.min(i,px<geo.fx-7?hist.length-1:n-1)))}
 cv.addEventListener('pointermove',e=>{if(!pin){sel=pick(e);draw()}});cv.addEventListener('pointerdown',e=>{sel=pick(e);pin=true;draw()});
 cv.addEventListener('pointerleave',()=>{if(!pin){sel=hist.length-1;draw()}});
 cv.addEventListener('keydown',e=>{const k={ArrowLeft:-1,ArrowRight:1}[e.key];if(k){pin=true;sel=Math.max(0,Math.min(all().length-1,sel+k*(e.shiftKey?10:1)));draw();e.preventDefault()}});
 new ResizeObserver(()=>{layout();draw()}).observe(cv);layout();draw();
 // --- check one epoch against mainnet, in this browser ---
 const ARCH='https://archival-rpc.mainnet.fastnear.com',LIVE='https://rpc.mainnet.fastnear.com',BUY='buybacks.multisignature.near',box=document.getElementById('check'),
 rpc=async(u,method,params)=>{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method,params})});
  if(!r.ok)throw new Error('the endpoint answered '+r.status);const j=await r.json();if(j.error)throw new Error(j.error.cause&&j.error.cause.name||j.error.message);return j.result},
 near=x=>fmt(Number(x/10n**18n)/1e6,3),
 bal=async hh=>{try{return BigInt((await rpc(ARCH,'query',{request_type:'view_account',block_id:hh,account_id:BUY})).amount)}catch(e){if(/UNKNOWN_ACCOUNT/.test(e.message))return 0n;throw e}};
 function show(st){box.innerHTML=`<h3>Epoch ending ${nice(st.d.t)}, checked against mainnet</h3><div class="wrap"><table><tr><th>Quantity</th><th>Mainnet, just now</th><th>Committed cache</th><th>Result</th></tr>`+
  st.rows.map(r=>`<tr><td>${r.k}</td><td>${r.a==null?'<span class="wait">reading</span>':near(r.a)+' NEAR'}</td><td>${near(r.b)} NEAR</td><td>${r.a==null?'':r.a===r.b?'<span class="eq">Equal to the yoctoNEAR</span>':'<span class="ne">Different</span>'}</td></tr>`).join('')+
  '</table></div>'+(st.verdict?`<p class="verdict${st.ok?'':' no'}">${st.verdict}</p>`:'')+
  `<p>Read from the headers of blocks ${st.d.p}, ${st.d.s} and ${st.d.e}`+(st.rows.length>2?` and the balance of ${BUY} at the first and last of them`:'')+`, on ${ARCH.slice(8)}.</p>`}
 async function verify(i){const d=all()[i],bs=[...document.querySelectorAll('.vrow button')];bs.forEach(b=>b.disabled=true);sel=i;pin=true;draw();
  const st={d,rows:[{k:'Minted',a:null,b:BigInt(d.raw[4])},{k:'Burnt in gas fees',a:null,b:BigInt(d.raw[5])}]};
  if(d.raw[6]!=null)st.rows.push({k:d.lump?'Buyback account change':'Buyback gain',a:null,b:BigInt(d.raw[6])});show(st);
  try{const B={};for(const [k,hh] of [['prev',d.p],['first',d.s],['last',d.e]]){const b=await rpc(ARCH,'block',{block_id:hh});
    B[k]={sup:BigInt(b.header.total_supply),burnt:b.chunks.filter(c=>c.height_included===hh).reduce((a,c)=>a+BigInt(c.balance_burnt),0n)}}
   st.rows[0].a=B.first.sup-B.prev.sup+B.first.burnt;st.rows[1].a=B.first.burnt+B.first.sup-B.last.sup;show(st);
   if(st.rows[2]){st.rows[2].a=await bal(d.e)-await bal(d.p)}
   st.ok=st.rows.every(r=>r.a===r.b);st.verdict=st.ok?'Mainnet and the committed cache agree for this epoch.':'The cache does not match mainnet for this epoch.'}
  catch(err){st.ok=false;st.verdict=`Could not finish: ${err.message}. The free endpoint limits requests; try again in a minute.`}
  show(st);bs.forEach(b=>b.disabled=false)}
 document.getElementById('vsel').addEventListener('click',()=>verify(sel));
 document.getElementById('vrnd').addEventListener('click',()=>verify(Math.floor(Math.random()*all().length)));
 // --- what mainnet says right now ---
 const set=(id,v)=>document.getElementById(id).innerHTML=v,msg=document.getElementById('lmsg'),fail=document.getElementById('lfail');
 async function now(){try{const b=await rpc(LIVE,'block',{finality:'final'}),a=await rpc(LIVE,'query',{request_type:'view_account',finality:'final',account_id:BUY});
   const hgt=b.header.height,bl=BigInt(a.amount),gain=T.bal?bl-BigInt(T.bal):null,ep=(hgt-T.snap)/43200;
   set('l-h',fmt(hgt));set('l-s',fmt(Number(BigInt(b.header.total_supply)/10n**24n))+' <small>NEAR</small>');set('l-b',fmt(Number(bl/10n**24n))+' <small>NEAR</small>');
   if(gain!=null&&T.rounds.length)set('l-g',(gain<0n?'':'+')+fmt(Number(gain/10n**21n)/1e3)+` <small>NEAR in ${ep.toFixed(1)} epochs</small>`);
   msg.textContent='Live from NEAR mainnet, read by your browser';msg.className='';fail.hidden=true;
   document.querySelectorAll('.rlive').forEach(s=>{const n=+s.dataset.n;s.textContent=ep>=n?'Live: the window has closed on mainnet. The next rebuild scores it.':
    `Live: about ${ep.toFixed(1)} of ${n} epochs elapsed`+(gain!=null?`, buyback gain so far ${fmt(Number(gain/10n**21n)/1e3)} NEAR`:'')+'.'})}
  catch(err){if(!msg.dataset.ok)fail.hidden=false;return}
  msg.dataset.ok=1}
 now();setInterval(()=>{if(!document.hidden)now()},60000)}
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


def render(results, sha, ledgers=None, tape=None):
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
        bk, bn = 100 * s["buyback_coverage"], 100 * s["burn_coverage"]
        lede = (f"<b>Burn {bn:.2f}% and Intents buybacks {bk:.2f}% add up to {pct(s['payback'], 1)} of issuance.</b> "
                f"Break-even means the flows would have to grow {s['multiple']:.1f}x to equal issuance. The buyback share is NEAR "
                f"sent by the NEAR Intents contract to the buyback account, where it is held, not burnt. A fee-burn dashboard "
                f"sees only the burn and puts break-even {s['burn_only_multiple']:.0f}x away.")
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
        lede = html.escape("Buyback balances are not cached for this window yet.")
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
    audit, w = "", results.get("wallet")
    if w:
        c, top, out = w["custody"], w["top_senders"], sum(x["near"] for x in w["paid"])
        tiles = [("Epochs that reconcile to the yoctoNEAR", f"{w['exact_with_receipts']} of {w['epochs_with_receipts']}",
                  f"<small>{num(w['receipts'])} receipts against balances read from the chain. {w['call_epochs']} epochs with multisig calls differ by "
                  f"{abs(w['call_residual_near']):.2f} NEAR of gas.</small>"),
                 (f"Share sent by {top[0]['account']}", pct(top[0]["share"], 1),
                  f"<small>{pct(top[1]['share'], 1)} came from <code>{e(top[1]['account'])}</code> in {top[1]['transfers']} transfers, "
                  f"including the one the headline excludes.</small>"),
                 ("NEAR that has left the account", num(out),
                  f"<small>{pct(out / w['inflow_near'], 2)} of what came in. The largest went to a bridge account on "
                  f"{max(w['paid'], key=lambda x: x['near'])['date']}; not traced further. None burnt.</small>"),
                 ("Keys needed to move it", f"{c['confirmations_required']} of {c['function_call_keys']}",
                  f"<small>{c['full_access_keys']} full-access keys, {c['requests_ever']} requests ever, {c['requests_pending']} pending. "
                  f"The chain does not say who holds the keys.</small>")]
        audit = ("<h3 style='margin-top:28px'>The buyback account, audited like a short seller would</h3>"
                 "<p class='sub'>Does the balance add up, who pays in, has it sold, and who can move it. Rebuild with "
                 "<code>python3 fetch.py history</code> and <code>python3 fetch.py multisig</code>; <code>test_run.py</code> fails if an epoch is unexplained.</p>"
                 "<dl class='facts' style='margin-top:14px'>" + "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}{x}</dd></div>" for a, b, x in tiles) + "</dl>")
    plog, pl = "", results.get("private_logs") or {}
    if pl and pl["before"]["share"] is not None and pl["since"]["share"] is not None:
        row = lambda name, x: (f"<tr><td>{name}</td><td>{x['blocks']}</td><td>{num(x['events'])}</td><td>{pct(x['share'], 0)}</td>"
                               f"<td>{pct(x['share_p05'], 0)} to {pct(x['share_p95'], 0)}</td></tr>")
        plog = ("<p class='sub' style='margin-top:14px'>Checked from raw mainnet blocks: the share of <code>intents.near</code> event logs that name the "
                "Confidential Intents treasury, in seeded random blocks (<code>data/private_sample.csv</code>).</p>"
                "<div class='wrap'><table><tr><th>Period</th><th>Blocks sampled</th><th>Event logs</th><th>Share naming the treasury</th><th>90% interval</th></tr>"
                + row("30 days before 2026-10-27", pl["before"]) + row("Since", pl["since"]) + "</table></div>")
    private, pv = "", results.get("private_settlement") or {}
    if pv.get("before") and pv.get("since"):
        b, a = pv["before"], pv["since"]
        private = (f"<h3 style='margin-top:28px'>The flow did not fall when swaps went private</h3>"
                   f"<p class='sub'>Since 2026-10-27 a growing share of Intents swaps settles on a private chain (reported by the "
                   f"<a href='https://github.com/ervhint/tideline-thesis'>Tideline</a> entry; our own check of mainnet logs is below), which hides "
                   f"their fees from public swap data. The buyback account is a mainnet balance and still records what arrives.</p>"
                   f"<div class='wrap'><table><tr><th>Period</th><th>Buyback gain, NEAR a day</th><th>Payback</th><th>Epochs with an inflow</th></tr>"
                   f"<tr><td>{b['days']:.0f} days before 2026-10-27</td><td>{num(b['buyback_per_day'])}</td><td>{pct(b['payback'], 1)}</td>"
                   f"<td>{b['epochs_with_inflow']} of {b['epochs']}</td></tr>"
                   f"<tr><td>{a['days']:.0f} days since</td><td>{num(a['buyback_per_day'])}</td><td>{pct(a['payback'], 1)}</td>"
                   f"<td>{a['epochs_with_inflow']} of {a['epochs']}</td></tr></table></div>")
    intents = ""
    if results.get("weekly"):
        intents = (f"<section id='app'><h2>The application behind the flow</h2><p>NEAR Intents by week since buybacks began "
                   f"(DefiLlama, USD). This is third-party context; none of it feeds mint, burn, the buyback gain or payback.</p>"
                   f"<div class='figs'>{figs('weekly', WEEKLY)}</div></section>")

    # ---- models ----
    models, calc = "", ""
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
"""
        calc = f"""<h3 style="margin-top:20px">Lever calculator</h3><p class="sub">Move volume, the share of Intents fees that reaches the buyback account, and the issuance rate to see how far burn plus buybacks move toward issuance.</p>
<div class="calc" data-burn="{s['burn_coverage']}" data-buy="{s['buyback_coverage']}" data-cap="{cap}">
<label>NEAR Intents volume <output id="o-vol">1.0x today</output>
<input type="range" id="vol" min="1" max="20" step="0.5" value="1"></label>
<label>Share of gross Intents fees reaching the buyback account <output id="o-cap">{cap}% (today)</output>
<input type="range" id="cap" min="{cap}" max="100" step="1" value="{cap}"></label>
<label>Issuance rate <output id="o-inf">2.5% a year (today)</output>
<input type="range" id="inf" min="0.5" max="2.5" step="0.1" value="2.5"></label>
<div class="bar"><i class="bk" id="c-bk"></i><i class="bn" id="c-bn"></i></div>
<p id="o-pay" aria-live="polite"></p></div>"""

    # ---- forecast rounds ----
    led = ""
    cls = {"PASS": "pass", "HIT": "pass", "FALSIFIED": "fail", "MISS": "fail", "PENDING": "pending"}
    names = {"payback": "Payback over the window", "burn_total": "NEAR burnt over the window",
             "buyback_total": "NEAR gained by the buyback account"}
    fmt = lambda n, x: "pending" if x is None else f"{100 * x:.1f}%" if n == "payback" else f"{x:,.0f}"
    end = datetime.datetime.strptime(s["last_end_utc"], "%Y-%m-%d %H:%M") if s.get("last_end_utc") else None
    newest = max((L["after_end_height"] for L in ledgers or []), default=0)
    day = {r[1]: datetime.datetime.fromtimestamp(r[3], datetime.timezone.utc).strftime("%Y-%m-%d") for r in (tape or {}).get("E", [])}
    board, tally = "", {}
    for L in sorted(ledgers or [], key=lambda L: (-L["after_end_height"], L["total"])):
        c = L["claims"]["payback"]
        tally[L["verdict"]] = tally.get(L["verdict"], 0) + 1
        board += (f"<tr><td>{day.get(L['after_end_height'], L['after_end_height'])}</td><td>{L['total']} epochs</td>"
                  f"<td>{fmt('payback', c['lo'])} to {fmt('payback', c['hi'])}</td><td>{fmt('payback', c['actual'])}</td>"
                  f"<td>{L['resolved']} of {L['total']}</td><td><span class='pill {cls.get(L['verdict'], 'pending')}'>{e(L['verdict'])}</span></td></tr>")
    for L in ledgers or []:
        if L["after_end_height"] != newest and L["verdict"] != "PENDING":
            continue  # closed older rounds live in the scoreboard only
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
                f"<span class='rmeta'>{L['resolved']} of {L['total']} epochs closed, {when}</span>"
                f"<span class='rlive' data-n='{L['total']}' aria-live='polite'></span></header>"
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
               f"is right, and a pass near the bounds is weak support.</p>"
               f"<details><summary>Scoreboard<small>{len(ledgers)} rounds frozen: "
               + ", ".join(f"{n} {k.lower()}" for k, n in sorted(tally.items())) + "</small></summary>"
               f"<p class='sub'>{len(ledgers)} rounds frozen: "
               + ", ".join(f"{n} {k.lower()}" for k, n in sorted(tally.items())) +
               ". A scheduled job freezes a new 5-epoch round about once a day, timestamps it and commits it; nothing is ever removed.</p>"
               f"<div class='wrap'><table><tr><th>Frozen</th><th>Window</th><th>Committed payback</th><th>Actual</th>"
               f"<th>Epochs closed</th><th>Verdict</th></tr>{board}</table></div></details>{led}</section>")

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
        gist = (f"For: the flow is on chain and exact, and capture and issuance are both levers. Against: buybacks are held, not burnt; "
                f"payback is {pct(s['payback'], 1)} against a peak of {pct(s['payback_peak'], 1)}; Intents volume is "
                f"{s['intents_volume_usd_ratio_1y']:.2f}x a year ago.")
        case = (f"<section id='case'><h2>The case, both ways</h2><p>The full argument, with what would change our mind, is in "
                f"<a href='{REPO}/blob/main/THESIS.md'>THESIS.md</a>.</p>"
                f"<details><summary>Read the case for and against<small>{e(gist)}</small></summary>"
                f"<div class='two'><div><h3>For</h3><ul>{li(f_)}</ul></div>"
                f"<div><h3>Against</h3><ul>{li(a_)}</ul></div></div></details></section>")

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

    c_h = c_s = c_b = c_g = c_when = None  # newest cached epoch, for the live strip's first paint
    if tape:
        try:
            d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            with open(os.path.join(d, "epochs.csv")) as fh:
                ep = list(csv.DictReader(fh))
            with open(os.path.join(d, "buybacks.csv")) as fh:
                bal = {int(r["end_height"]): int(r["balance"]) for r in csv.DictReader(fh) if r["balance"]}
            last = ep[-1]
            h = int(last["end_height"])
            c_h = f"{h:,}"
            c_s = f"{int(last['supply_end']) // 10**24:,}"
            c_when = datetime.datetime.fromtimestamp(int(last["t1_ns"]) / 1e9, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            if h in bal:
                c_b = f"{bal[h] // 10**24:,}"
                if tape["rounds"] and tape["snap"] in bal:
                    n = sum(int(r["end_height"]) > tape["snap"] for r in ep)
                    g = (bal[h] - bal[tape["snap"]]) / 10**24
                    c_g = f"{'+' if g >= 0 else ''}{g:,.0f} <small>NEAR in {n} epochs</small>"
        except (OSError, KeyError, ValueError, IndexError):
            pass
    nc = lambda v, u="": "&ndash;" if v is None else v + (f" <small>{u}</small>" if u else "")
    tape_html = "" if not tape else (
        f"<div class='livebar'><p class='lstat'><i></i><span id='lmsg' aria-live='polite'>{'<span class=lsrc>From cache, epoch ending ' + c_when + '</span>' if c_when else 'Reading NEAR mainnet from your browser'}</span></p>"
        f"<dl><div><dt>Latest block</dt><dd id='l-h'>{nc(c_h)}</dd></div><div><dt>Total supply</dt><dd id='l-s'>{nc(c_s, 'NEAR')}</dd></div>"
        f"<div><dt>Buyback account holds</dt><dd id='l-b'>{nc(c_b, 'NEAR')}</dd></div>"
        + (f"<div><dt>Gained since the forecasts were frozen</dt><dd id='l-g'>{nc(c_g)}</dd></div>" if tape["rounds"] else "")
        + "</dl><p class='lfoot' id='lfail' hidden>Live read unavailable (rate limited); showing the committed cache.</p></div>"
        f"<div class='tape'><h2>Every epoch since {e(s['first'])}, one column each</h2>"
        "<p>Column height is the share of that epoch's minted NEAR matched by <span class='k' style='background:#f2915a'></span>gas burn and "
        "<span class='k' style='background:#43d1b7'></span>buyback gain. The white line is the 100-epoch payback. Right of the divider are the "
        "epochs after the forecasts were frozen, against the committed payback band. Hover or use the arrow keys; click to hold an epoch.</p>"
        "<canvas id='tape' tabindex='0' role='img' aria-label='Burn and buyback gain as a share of mint, for every epoch'></canvas>"
        "<div class='read' id='read' aria-live='polite'></div>"
        "<div class='vrow'><button type='button' id='vsel'>Check this epoch against mainnet</button>"
        "<button type='button' id='vrnd'>Check a random epoch</button></div><div class='check' id='check' aria-live='polite'></div></div>"
        f"<script type='application/json' id='tape-data'>{json.dumps(tape, separators=(',', ':'))}</script>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Coverage: what NEAR pays back</title>
<meta name="description" content="{e(head)}">
<style>{CSS}</style></head><body>
<nav><div><b>Coverage</b><a href="#chain">Onchain dashboard</a>{'<a href="#app">NEAR Intents</a>' if intents else ''}<a href="#models">Models</a>{'<a href="#rounds">Forecast rounds</a>' if led else ''}{'<a href="#case">For and against</a>' if case else ''}<a href="#reproduce">Reproduce</a><a href="{REPO}">GitHub</a></div></nav>
<header class="hero"><div class="hin">
<p class="stamp">NEAR mainnet, {e(s['first'])} to {e(s['last'])} &middot; {s['epochs']} epochs &middot; headline figures cover the last 100 epochs, {days} days</p>
<div class="htop"><h1>{e(head)}</h1>
<p class="lede">{lede}</p></div>
{tape_html}</div></header>
<main>
{strip}
<dl class="facts">{facts_html}</dl>
<section id="chain"><h2>Onchain dashboard</h2>
<p>Mint and burn are read from <code>total_supply</code> in block headers and are exact to the yoctoNEAR. The buyback gain is the
change in the account's balance between epoch ends. Every point is a 100-epoch rolling window; hover a chart for values.</p>
<div class="figs">{figs('series', CHARTS, 'payback')}</div>
<details><summary>Cross-checks and data tables<small>Private settlement, chain versus indexer, and the buyback account audit</small></summary>
{private}{plog}
<h3 style="margin-top:28px">Chain versus the indexer</h3>
<p class="sub">The same flows over the same days, in NEAR a day. DefiLlama reports USD; each day is converted at that day's price.</p>
<div class="wrap"><table><tr><th>Flow, NEAR a day</th><th>This repo, from chain</th><th>DefiLlama</th></tr>{check}</table></div>
{attr}{audit}</details></section>
{intents}
<section id="models"><h2>Models</h2>
<p>Four models, each a few functions in <code>run.py</code>, each rebuilt by <code>python3 run.py</code> from the cached data with
no network. Their outputs are in <code>out/results.json</code>.</p>{calc}
<details><summary>Model detail<small>Flow identity, burn forecasters, window bands and break-even years</small></summary>{models}</details></section>
{led}
{case}
<section id="reproduce"><h2>Reproduce it</h2>
<p>The result hash below covers every number on this page. If your run prints a different hash, the page and the data disagree.</p>
{repro}</section>
<footer>Result hash <code>{sha}</code>. MIT licence. <a href="{REPO}">{REPO.split('//')[1]}</a></footer>
</main><script type="application/json" id="data">{json.dumps(dict(series=results['series'], weekly=results.get('weekly', [])), separators=(',', ':'))}</script>
<script>{JS}</script></body></html>"""
