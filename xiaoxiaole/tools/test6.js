const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8237,async()=>{
  try{
  const errors=[];const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:420,height:860}});
  p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://localhost:8237/',{waitUntil:'networkidle'});
  await p.waitForTimeout(300);
  // 清除存档测成就
  await p.evaluate(()=>{localStorage.clear();});
  await p.reload();await p.waitForTimeout(400);
  await p.click('#menuContinue');await p.waitForTimeout(2400);
  // 做几次交换触发消除+成就
  async function swap(r1,c1,r2,c2){
    const t1=p.locator(`.tile[data-r="${r1}"][data-c="${c1}"]`);
    const b1=await t1.boundingBox(); const b2=await p.locator(`.tile[data-r="${r2}"][data-c="${c2}"]`).boundingBox();
    if(!b1||!b2) return;
    await p.mouse.move(b1.x+b1.width/2,b1.y+b1.height/2);await p.mouse.down();
    await p.mouse.move(b2.x+b2.width/2,b2.y+b2.height/2,{steps:6});await p.mouse.up();await p.waitForTimeout(900);
  }
  for(let i=0;i<8;i++){ const r=Math.floor(Math.random()*8),c=Math.floor(Math.random()*7); await swap(r,c,r,c+1); }
  // 检查成就解锁
  await p.waitForTimeout(500);
  const achVisible=await p.locator('#achievement').isVisible().catch(()=>false);
  const achCount=await p.evaluate(()=>Object.keys(JSON.parse(localStorage.getItem('xxl-ach')||'{}')).length);
  console.log('成就解锁数:',achCount,'通知显示过:',achVisible);
  // 测试设置面板
  
  await p.click("#settingsBtn");await p.waitForTimeout(400);
  const setVis=await p.locator('#modalSettings').isVisible();
  const setRows=await p.locator('.setting-row').count();
  console.log('设置面板可见:',setVis,'设置项数:',setRows);
  // 测音量滑块
  await p.fill('#setVol','80');
  const vol=await p.evaluate(()=>+localStorage.getItem('xxl-vol'));
  console.log('音量设置:',vol);
  await p.screenshot({path:'tools/screenshots/v23-settings.png'});
  console.log('错误:',errors.length);errors.forEach(e=>console.log(' ',e));
  await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);process.exit(2);}
});
