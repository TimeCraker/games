const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8253,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    const p=await b.newPage({viewport:{width:375,height:812}});
    const errors=[];p.on('pageerror',e=>errors.push(e.message));
    await p.goto('http://localhost:8253/',{waitUntil:'networkidle'});await p.waitForTimeout(400);
    await p.click('#menuContinue');await p.waitForTimeout(2400);
    // 场景1: 暂停->设置->换歌->关闭设置
    await p.click('#pauseBtn');await p.waitForTimeout(300);
    await p.click('#pauseSettingsBtn');await p.waitForTimeout(300);
    await p.click('#musicNext');await p.waitForTimeout(200);
    await p.click('#settingsClose');await p.waitForTimeout(400);
    const s1=await p.evaluate(()=>({state:window.state||'?',modalShown:[...document.querySelectorAll('.modal.show')].map(m=>m.id),tilesClickable:document.querySelectorAll('.tile').length}));
    console.log('场景1(暂停->设置->换歌->关闭):',JSON.stringify(s1));
    // 此时应该回到暂停弹窗(modalPause show), 方块不可点(paused正常)
    // 恢复游戏
    await p.click('#resumeBtn');await p.waitForTimeout(300);
    const s2=await p.evaluate(()=>({modalShown:[...document.querySelectorAll('.modal.show')].map(m=>m.id)}));
    console.log('场景1恢复后:',JSON.stringify(s2),'(应无弹窗=可操作)');
    // 场景2: 暂停->回主菜单->点设置
    await p.click('#pauseBtn');await p.waitForTimeout(300);
    await p.click('#pauseMenuBtn');await p.waitForTimeout(500);
    await p.click('#settingsBtn');await p.waitForTimeout(300);
    const s3=await p.evaluate(()=>({modalShown:[...document.querySelectorAll('.modal.show')].map(m=>m.id)}));
    console.log('场景2(暂停->主菜单->设置):',JSON.stringify(s3),'(应modalSettings show)');
    console.log('错误:',errors.length);
    await b.close();srv.close();process.exit(errors.length?1:0);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
