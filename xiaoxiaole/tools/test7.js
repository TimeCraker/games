const { chromium } = require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB='public';const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p=='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8238,async()=>{
  try{
  const b=await chromium.launch({channel:'chrome',headless:true});
  const p=await b.newPage({viewport:{width:420,height:860},deviceScaleFactor:2});
  await p.goto('http://localhost:8238/',{waitUntil:'networkidle'});
  await p.waitForTimeout(400);
  // 主菜单状态下检查 topbar 按钮可见性
  const info=await p.evaluate(()=>{
    const shell=document.getElementById('gameShell');
    const topbar=document.querySelector('.topbar');
    const btns=document.querySelectorAll('.topbar .icon-btn');
    const screen=document.getElementById('screenMenu');
    const screenRect=screen.getBoundingClientRect();
    return {
      shellHidden: shell.hidden,
      shellDisplay: getComputedStyle(shell).display,
      topbarDisplay: topbar?getComputedStyle(topbar).display:'none',
      btnCount: btns.length,
      btnInfo: [...btns].map(b=>{const r=b.getBoundingClientRect();return {id:b.id,visible:r.width>0, x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width)}}),
      screenZ: getComputedStyle(screen).zIndex,
      screenVis: getComputedStyle(screen).visibility,
      screenOpacity: getComputedStyle(screen).opacity,
    };
  });
  console.log(JSON.stringify(info,null,2));
  await p.screenshot({path:'tools/screenshots/diag-menu.png'});
  await b.close();srv.close();process.exit(0);
  }catch(e){console.error(e);process.exit(2);}
});
