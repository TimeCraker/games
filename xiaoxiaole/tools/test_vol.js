const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8262,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    const p=await b.newPage({viewport:{width:375,height:812}});
    const errs=[];p.on('pageerror',e=>errs.push(e.message));
    await p.goto('http://localhost:8262/',{waitUntil:'networkidle'});await p.waitForTimeout(500);
    await p.click('#menuContinue');await p.waitForTimeout(2600);
    const gameMute=await p.locator('#gameSoundBtn').count();
    await p.click('#pauseBtn');await p.waitForTimeout(400);
    const pauseVol=await p.locator('#pauseVol').count();
    const pauseMute=await p.locator('#pauseMuteBtn').count();
    console.log('游戏内静音按钮:',gameMute,'暂停音量滑块:',pauseVol,'暂停静音按钮:',pauseMute,'错误:',errs.length);
    await b.close();srv.close();process.exit(gameMute&&pauseVol&&pauseMute&&!errs.length?0:1);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
