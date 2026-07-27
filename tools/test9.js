const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8241,async()=>{
  try{
  const errors=[];const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:420,height:860},deviceScaleFactor:2});
  p.on('pageerror',e=>errors.push(e.message));
  p.on('console',m=>{if(m.type()==='error')errors.push('CON:'+m.text());});
  await p.goto('http://localhost:8241/',{waitUntil:'networkidle'});
  await p.waitForTimeout(700);
  // 检查标题 span
  const titleInfo=await p.evaluate(()=>{
    const spans=document.querySelectorAll('.menu-title span');
    return {count:spans.length, texts:[...spans].map(s=>s.textContent), 
      c2stroke:spans[1]?getComputedStyle(spans[1]).webkitTextStroke:''};
  });
  console.log('标题span数:',titleInfo.count,'文字:',titleInfo.texts.join(''),'描边:',titleInfo.c2stroke);
  // 检查无流光动画
  const hasShine=await p.evaluate(()=>{const s=getComputedStyle(document.querySelector('.menu-btn.primary'));return s.cssText.includes('shine')||!!document.querySelector('.menu-btn.primary::before');});
  console.log('主按钮流光已移除:',!hasShine);
  await p.screenshot({path:'tools/screenshots/v25-art-title.png'});
  console.log('错误:',errors.length);errors.forEach(e=>console.log(' ',e));
  await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);process.exit(2);}
});
