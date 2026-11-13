// node render.js stills t1,t2,...   -> reviews/still-<t>.png
// node render.js video [fps]        -> out/frames.mp4 (no audio), frames piped straight into ffmpeg
const {chromium}=require('playwright');const {spawn}=require('child_process');const http=require('http'),fs=require('fs'),path=require('path');
const ROOT=__dirname,mode=process.argv[2];
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,b)=>{if(e){r.writeHead(404);return r.end()}
 r.writeHead(200,{'content-type':f.endsWith('.html')?'text/html':f.endsWith('.js')?'text/javascript':f.endsWith('.png')?'image/png':'application/octet-stream'});r.end(b)})}).listen(4310);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await p.route(u=>!/localhost|fonts\.g/.test(u.hostname),r=>r.abort());
 await p.goto('http://localhost:4310/src/index.html');await p.evaluate(()=>window.ready);await p.waitForTimeout(500);
 if(mode==='stills'){for(const t of process.argv[3].split(',')){await p.evaluate(t=>seek(+t),t);await p.screenshot({path:`reviews/still-${String(t).padStart(5,'0')}.png`})}}
 else{const fps=+(process.argv[3]||30),N=Math.round(72*fps);
  const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium','out/frames.mp4'],{stdio:['pipe','inherit','inherit']});
  for(let i=0;i<N;i++){await p.evaluate(t=>seek(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:95});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%300==0)console.log('frame',i,'/',N)}
  ff.stdin.end();await new Promise(r=>ff.on('close',r))}
 await b.close();srv.close()})();
