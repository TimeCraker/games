const {chromium}=require('playwright');
const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8254,async()=>{
  try{
    const b=await chromium.launch({channel:'chrome',headless:true});
    // 1. 桌面主菜单
    let p=await b.newPage({viewport:{width:1280,height:800},deviceScaleFactor:2});
    await p.goto('http://localhost:8254/',{waitUntil:'networkidle'});await p.waitForTimeout(1500);
    await p.screenshot({path:'docs/images/screenshot-menu.png'});
    // 2. 桌面游戏中
    await p.click('#menuContinue');await p.waitForTimeout(2800);
    await p.screenshot({path:'docs/images/screenshot-game.png'});
    await p.close();
    // 3. 移动端主菜单
    p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:3,isMobile:true,hasTouch:true});
    await p.goto('http://localhost:8254/',{waitUntil:'networkidle'});await p.waitForTimeout(1500);
    await p.screenshot({path:'docs/images/screenshot-mobile-menu.png'});
    // 4. 移动端游戏中
    await p.click('#menuContinue');await p.waitForTimeout(2800);
    await p.screenshot({path:'docs/images/screenshot-mobile-game.png'});
    await p.close();
    // 5. 关卡选择
    p=await b.newPage({viewport:{width:1280,height:800},deviceScaleFactor:2});
    await p.goto('http://localhost:8254/',{waitUntil:'networkidle'});await p.waitForTimeout(1000);
    await p.click('#menuLevels');await p.waitForTimeout(600);
    await p.screenshot({path:'docs/images/screenshot-levels.png'});
    await b.close();srv.close();
    // 自动压缩 png -> jpg
    try{ require('child_process').execSync('python - <<"PY"\nfrom PIL import Image\nfrom pathlib import Path\nfor f in sorted(Path("docs/images").glob("screenshot-*.png")):\n    im=Image.open(f).convert("RGB")\n    w,h=im.size\n    if w>1280: im=im.resize((1280,int(1280*h/w)),Image.Resampling.LANCZOS)\n    im.save(str(f).replace(".png",".jpg"),"JPEG",quality=82,optimize=True)\n    f.unlink()\nPY',{stdio:'inherit'}); }catch(e){}
    console.log('截图完成');
    require('child_process').execSync('ls -lh docs/images/');
    process.exit(0);
  }catch(e){console.error(e);srv.close();process.exit(2);}
});
