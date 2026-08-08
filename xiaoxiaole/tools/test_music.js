const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8252,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    const p=await b.newPage({viewport:{width:375,height:812}});
    const errors=[];p.on('pageerror',e=>errors.push(e.message));
    await p.goto('http://localhost:8252/',{waitUntil:'networkidle'});await p.waitForTimeout(400);
    await p.click('#settingsBtn');await p.waitForTimeout(300);
    const hasMusic=await p.locator('#musicLabel').count();
    const label=await p.textContent('#musicLabel');
    // 下一首
    await p.click('#musicNext');await p.waitForTimeout(200);
    const label2=await p.textContent('#musicLabel');
    // 上一首
    await p.click('#musicPrev');await p.waitForTimeout(200);
    const label3=await p.textContent('#musicLabel');
    await p.click('#settingsClose');await p.waitForTimeout(300);
    await p.click('#menuContinue');await p.waitForTimeout(2400);
    const tiles=await p.locator('.tile').count();
    console.log('音乐选择器:',hasMusic,'初始:',label,'下一首后:',label2,'上一首后:',label3,'tiles:',tiles);
    console.log('错误:',errors.length);errors.forEach(e=>console.log(' ',e));
    await b.close();srv.close();process.exit(hasMusic&&tiles===64&&!errors.length?0:1);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
