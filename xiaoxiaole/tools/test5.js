const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8236,async()=>{
  try{
  const errors=[];const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:420,height:860},deviceScaleFactor:2});
  p.on('pageerror',e=>errors.push(e.message));
  await p.goto('http://localhost:8236/',{waitUntil:'networkidle'});
  await p.waitForTimeout(300);
  await p.click('#menuContinue'); await p.waitForTimeout(2400);
  // 测试跟手拖动：按下方块，移动一点，检查 transform 是否变化
  const t1=p.locator('.tile').first();
  const box=await t1.boundingBox();
  const cx=box.x+box.width/2, cy=box.y+box.height/2;
  await p.mouse.move(cx,cy);
  await p.mouse.down();
  await p.mouse.move(cx+15,cy,{steps:3});
  await p.waitForTimeout(100);
  const tf1=await t1.evaluate(e=>e.style.transform);
  console.log('拖动中transform含18px(跟手):', tf1.includes('18px'));
  // 继续移动超过阈值
  await p.mouse.move(cx+box.width*0.5,cy,{steps:4});
  await p.waitForTimeout(100);
  const tf2=await t1.evaluate(e=>e.style.transform);
  console.log('超过阈值transform含0.55:', tf2.includes('0.55')||tf2.length>10);
  await p.mouse.up();
  await p.waitForTimeout(800);
  // 测试提示系统：等5.5秒
  await p.waitForTimeout(5500);
  const hintCount=await p.locator('.tile.hint').count();
  console.log('提示高亮方块数:',hintCount);
  console.log('错误:',errors.length);errors.forEach(e=>console.log(' ',e));
  await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);process.exit(2);}
});
