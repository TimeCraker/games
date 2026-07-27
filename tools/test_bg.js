const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8255,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    const p=await b.newPage({viewport:{width:1280,height:800}});
    const errors=[];p.on('pageerror',e=>errors.push(e.message));
    await p.goto('http://localhost:8255/',{waitUntil:'networkidle'});await p.waitForTimeout(600);
    // 连续点背景按钮4次,看是否在 cloud->neon->photo1->photo2 轮换
    const seq=[];
    for(let i=0;i<4;i++){
      await p.click('#bgBtn');await p.waitForTimeout(250);
      const bg=await p.evaluate(()=>document.documentElement.dataset.bg);
      const cssVar=await p.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--bg-photo-url'));
      seq.push({bg,bgImg:cssVar.slice(0,50)});
    }
    console.log('轮换序列:',JSON.stringify(seq,null,1));
    console.log('错误:',errors.length);
    await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
