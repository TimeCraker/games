const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8240,async()=>{
  try{
  const errors=[];const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:420,height:860},deviceScaleFactor:2});
  p.on('pageerror',e=>errors.push(e.message));
  p.on('console',m=>{if(m.type()==='error')errors.push('CON:'+m.text());});
  await p.goto('http://localhost:8240/',{waitUntil:'networkidle'});
  await p.waitForTimeout(800);
  // 主菜单状态下点 themeBtn（全局顶栏）
  const themeBefore=await p.evaluate(()=>document.documentElement.dataset.theme);
  await p.click('#themeBtn'); await p.waitForTimeout(300);
  const themeAfter=await p.evaluate(()=>document.documentElement.dataset.theme);
  console.log('主菜单点themeBtn:',themeBefore,'->',themeAfter, themeBefore!==themeAfter?'✓可点':'✗点不到');
  // 点 settingsBtn
  await p.click('#settingsBtn'); await p.waitForTimeout(400);
  const setVis=await p.locator('#modalSettings').isVisible();
  console.log('主菜单点settingsBtn弹设置:',setVis);
  await p.click('#settingsClose'); await p.waitForTimeout(300);
  // 检查字体加载
  const fontLoaded=await p.evaluate(()=>document.fonts.check('16px "ZCOOL QingKe HuangYou"'));
  console.log('展示字体加载:',fontLoaded);
  // 截图主菜单
  await p.screenshot({path:'tools/screenshots/v24-menu.png'});
  // 桌面端也截一张
  await p.setViewportSize({width:1200,height:860}); await p.waitForTimeout(500);
  await p.screenshot({path:'tools/screenshots/v24-menu-desktop.png'});
  console.log('错误:',errors.length);errors.forEach(e=>console.log(' ',e));
  await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);process.exit(2);}
});
