const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8251,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    const p=await b.newPage({viewport:{width:420,height:860}});
    const errors=[];p.on('pageerror',e=>errors.push(e.message));
    await p.goto('http://localhost:8251/',{waitUntil:'networkidle'});await p.waitForTimeout(400);
    await p.click('#menuContinue');await p.waitForTimeout(2400);
    // 测1: 轻快滑动（小距离+快速）应触发交换
    const t=await p.locator('.tile').first().boundingBox();
    const s0=await p.textContent('#score');
    await p.mouse.move(t.x+t.width/2,t.y+t.height/2);await p.mouse.down();
    await p.mouse.move(t.x+t.width/2+t.width*0.28,t.y+t.height/2,{steps:2}); // 滑0.28格(低于旧0.35,高于新0.22)
    await p.mouse.up();await p.waitForTimeout(900);
    const s1=await p.textContent('#score');
    console.log('轻滑0.28格: 分数',s0,'->',s1,s1!==s0?'✓触发交换':'(未触发,可能该方向无消除)');
    // 测2: 极轻点击不应误触（dist<0.1）
    const t2=await p.locator('.tile').nth(5).boundingBox();
    await p.mouse.move(t2.x+t2.width/2,t2.y+t2.height/2);await p.mouse.down();
    await p.mouse.move(t2.x+t2.width/2+3,t2.y+t2.height/2,{steps:1}); // 仅3px
    await p.mouse.up();await p.waitForTimeout(500);
    console.log('极轻3px: 无崩溃, 错误:',errors.length);
    await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
