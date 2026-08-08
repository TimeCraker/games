const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8233,async()=>{
  try{
  const errors=[];const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:1200,height:860},deviceScaleFactor:2});
  p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  p.on('pageerror',e=>errors.push('PAGE:'+e.message));
  await p.goto('http://localhost:8233/',{waitUntil:'networkidle'});
  await p.waitForTimeout(400);
  await p.click('#menuLevels'); await p.waitForTimeout(500);
  const levelCards=await p.locator('.level-card').count();
  console.log('关卡卡片数:',levelCards);
  await p.screenshot({path:'tools/screenshots/v2-levels.png'});
  await p.click('#levelsBack'); await p.waitForTimeout(300);
  await p.click('#menuBg'); await p.waitForTimeout(400); const bg1=await p.evaluate(()=>document.documentElement.dataset.bg);
  await p.click('#menuBg'); await p.waitForTimeout(400); const bg2=await p.evaluate(()=>document.documentElement.dataset.bg);
  await p.click('#menuBg'); await p.waitForTimeout(400); const bg3=await p.evaluate(()=>document.documentElement.dataset.bg);
  console.log('背景切换:',bg1,'->',bg2,'->',bg3);
  await p.click('#menuContinue'); await p.waitForTimeout(2400);
  const layout=await p.evaluate(()=>{const b=document.querySelector('.game-body');const cs=getComputedStyle(b);return{cols:cs.gridTemplateColumns,panelLeft:!!document.querySelector('.panel-left'),panelRight:!!document.querySelector('.panel-right')}});
  console.log('桌面布局:',JSON.stringify(layout));
  await p.screenshot({path:'tools/screenshots/v2-desktop.png'});
  // 暂停测试
  await p.click('#pauseBtn'); await p.waitForTimeout(400);
  const pauseVisible=await p.locator('#modalPause').isVisible();
  console.log('暂停弹窗:',pauseVisible);
  await p.screenshot({path:'tools/screenshots/v2-pause.png'});
  console.log('错误数:',errors.length);errors.forEach(e=>console.log(' ',e));
  await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);process.exit(2);}
});
