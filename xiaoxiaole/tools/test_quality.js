const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8247,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    const p=await b.newPage({viewport:{width:375,height:812}});
    const errors=[];p.on('pageerror',e=>errors.push(e.message));
    await p.goto('http://localhost:8247/',{waitUntil:'networkidle'});await p.waitForTimeout(400);
    await p.click('#settingsBtn');await p.waitForTimeout(300);
    const hasSelect=await p.locator('#setQuality').count();
    const opts=await p.locator('#setQuality option').count();
    // 切到 low
    await p.selectOption('#setQuality','low');await p.waitForTimeout(300);
    const qLow=await p.evaluate(()=>localStorage.getItem('xxl-quality'));
    // 切到 high
    await p.selectOption('#setQuality','high');await p.waitForTimeout(300);
    const qHigh=await p.evaluate(()=>localStorage.getItem('xxl-quality'));
    await p.click('#settingsClose');await p.waitForTimeout(300);
    await p.click('#menuContinue');await p.waitForTimeout(2400);
    const tiles=await p.locator('.tile').count();
    console.log('质量select:',hasSelect,'选项数:',opts,'low存储:',qLow,'high存储:',qHigh,'tiles:',tiles);
    console.log('错误:',errors.length);errors.forEach(e=>console.log(' ',e));
    await b.close();srv.close();process.exit(hasSelect&&opts===4&&qLow==='low'&&qHigh==='high'&&tiles===64&&!errors.length?0:1);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
