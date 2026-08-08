const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8234,async()=>{
  try{
  const errors=[];const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:1200,height:860},deviceScaleFactor:2});
  p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  p.on('pageerror',e=>errors.push('PAGE:'+e.message));
  await p.goto('http://localhost:8234/',{waitUntil:'networkidle'});
  await p.waitForTimeout(400);
  // 检查 SVG 图标是否渲染
  const svgCount = await p.locator('#screenMenu svg').count();
  console.log('主菜单SVG数:',svgCount);
  // 进入第1关
  await p.click('#menuContinue'); await p.waitForTimeout(2400);
  const tiles=await p.locator('.tile').count();
  const movesTxt=await p.textContent('#movesLeft');
  console.log('第1关: tile数',tiles,'步数显示',movesTxt,'(应为∞)');
  await p.screenshot({path:'tools/screenshots/v21-lvl1.png'});
  // 暂停 -> 回主菜单
  await p.click('#pauseBtn'); await p.waitForTimeout(400);
  await p.click('#pauseMenuBtn'); await p.waitForTimeout(600);
  // 检查主菜单是否正常 + 棋盘是否清理
  const menuVisible=await p.locator('#screenMenu').isVisible();
  const tileRemain=await p.locator('.tile').count();
  const shellHidden=await p.evaluate(()=>document.getElementById('gameShell').hidden);
  console.log('回主菜单: 菜单可见',menuVisible,'残留tile',tileRemain,'shell隐藏',shellHidden);
  await p.screenshot({path:'tools/screenshots/v21-back-menu.png'});
  // 关卡选择
  await p.click('#menuLevels'); await p.waitForTimeout(500);
  const cards=await p.locator('.level-card').count();
  const lvl1Meta=await p.locator('.level-card').first().textContent();
  console.log('关卡数:',cards,'第1关信息含∞:',lvl1Meta.includes('∞'));
  // 检查第4关是否有步数
  const lvl4Meta=await p.locator('.level-card').nth(3).textContent();
  console.log('第4关信息:',lvl4Meta.replace(/\s+/g,' '));
  await p.screenshot({path:'tools/screenshots/v21-levels.png'});
  console.log('错误数:',errors.length);errors.forEach(e=>console.log(' ',e));
  await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);process.exit(2);}
});
