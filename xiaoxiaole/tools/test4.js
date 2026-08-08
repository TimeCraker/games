const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8235,async()=>{
  try{
  const errors=[];const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:420,height:860},deviceScaleFactor:2});
  p.on('pageerror',e=>errors.push('PAGE:'+e.message));
  await p.goto('http://localhost:8235/',{waitUntil:'networkidle'});
  await p.waitForTimeout(300);
  // 临时降低第1关难度: 通过 localStorage 改不了 LEVELS。直接循环交换。
  await p.click('#menuContinue'); await p.waitForTimeout(2400);
  async function swap(r1,c1,r2,c2){
    const t1=p.locator(`.tile[data-r="${r1}"][data-c="${c1}"]`);
    const b1=await t1.boundingBox(); const b2=await p.locator(`.tile[data-r="${r2}"][data-c="${c2}"]`).boundingBox();
    if(!b1||!b2) return;
    await p.mouse.move(b1.x+b1.width/2,b1.y+b1.height/2);
    await p.mouse.down(); await p.mouse.move(b2.x+b2.width/2,b2.y+b2.height/2,{steps:6}); await p.mouse.up();
    await p.waitForTimeout(900);
  }
  let won=false;
  for(let i=0;i<60&&!won;i++){
    const r=Math.floor(Math.random()*8),c=Math.floor(Math.random()*7);
    await swap(r,c,r,c+1);
    won=await p.locator('#modalWin').isVisible();
  }
  const score=await p.textContent('#score');
  console.log('胜利:',won,'分数:',score);
  if(won){
    // 点回主菜单
    await p.click('#winMenuBtn'); await p.waitForTimeout(700);
    const menuVis=await p.locator('#screenMenu').isVisible();
    const tileRem=await p.locator('.tile').count();
    const shellHid=await p.evaluate(()=>document.getElementById('gameShell').hidden);
    console.log('胜利后回菜单: 菜单可见',menuVis,'残留tile',tileRem,'shell隐藏',shellHid);
    await p.screenshot({path:'tools/screenshots/v21-win-back.png'});
    // 再次进入游戏确认正常
    await p.click('#menuContinue'); await p.waitForTimeout(2400);
    const tiles2=await p.locator('.tile').count();
    console.log('再次进入游戏 tile数:',tiles2);
  }
  console.log('错误:',errors.length);errors.forEach(e=>console.log(' ',e));
  await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);process.exit(2);}
});
