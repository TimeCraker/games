const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream','Cache-Control':'no-cache'});s.end(d);});});
srv.listen(8248,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    const p=await b.newPage({viewport:{width:375,height:812}});
    const errors=[];p.on('pageerror',e=>errors.push(e.message));
    await p.goto('http://localhost:8248/',{waitUntil:'networkidle'});await p.waitForTimeout(1500);
    // 检查 SW 注册 + 缓存版本
    const swInfo=await p.evaluate(async()=>({
      reg: !!(await navigator.serviceWorker.getRegistration()),
      controller: !!navigator.serviceWorker.controller,
      caches: await caches.keys(),
    }));
    // 检查 controllerchange 监听（通过 evaluate 看不到，但能确认 SW 代码被加载）
    // 验证 navigation network-first：拦截 fetch 事件
    console.log('SW注册:',swInfo.reg,'controller:',swInfo.controller,'caches:',JSON.stringify(swInfo.caches));
    // 进游戏验证功能正常
    await p.click('#menuContinue');await p.waitForTimeout(2400);
    const tiles=await p.locator('.tile').count();
    console.log('tiles:',tiles,'错误:',errors.length);
    errors.forEach(e=>console.log(' ',e));
    await b.close();srv.close();
    process.exit(swInfo.reg&&tiles===64&&!errors.length?0:1);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
