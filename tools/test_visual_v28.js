const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.webmanifest':'application/manifest+json'};
const server=http.createServer((req,res)=>{let p=decodeURIComponent(req.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join('public',p),(e,d)=>{if(e){res.writeHead(404);res.end();return;}res.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});res.end(d);});});

const overlaps=(a,b)=>!(a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom);

server.listen(8243,async()=>{
  try{
    const browser=await chromium.launch({channel:'chrome',headless:true});
    const errors=[];
    const mobile=await browser.newPage({viewport:{width:375,height:812},deviceScaleFactor:2});
    mobile.on('pageerror',e=>errors.push(e.message));
    await mobile.goto('http://localhost:8243/',{waitUntil:'networkidle'});
    await mobile.waitForTimeout(800);
    const menuMobile=await mobile.evaluate(()=>({
      hero:getComputedStyle(document.querySelector('.screen-menu'),'::before').backgroundImage,
      personalTokens:document.querySelectorAll('.menu-token').length,
      overflow:document.documentElement.scrollWidth>innerWidth,
      title:document.querySelector('.menu-title').textContent.trim()
    }));
    await mobile.screenshot({path:'tools/screenshots/v28-menu-mobile.png'});
    await mobile.click('#menuContinue');
    await mobile.waitForTimeout(2400);
    const gameMobile=await mobile.evaluate(()=>{
      const level=document.querySelector('.level-pill').getBoundingClientRect();
      const pause=document.querySelector('#pauseBtn').getBoundingClientRect();
      const board=document.querySelector('.board-3d').getBoundingClientRect();
      const global=getComputedStyle(document.querySelector('.global-bar'));
      return {
        level:{left:level.left,top:level.top,right:level.right,bottom:level.bottom},
        pause:{left:pause.left,top:pause.top,right:pause.right,bottom:pause.bottom},
        boardTop:Math.round(board.top),
        boardBottom:Math.round(board.bottom),
        globalHidden:global.visibility==='hidden'&&global.pointerEvents==='none',
        gameActive:document.documentElement.classList.contains('game-active'),
        tiles:document.querySelectorAll('.tile').length,
        loadedTiles:[...document.querySelectorAll('.tile img')].filter(i=>i.complete&&i.naturalWidth).length
      };
    });
    gameMobile.topbarOverlap=overlaps(gameMobile.level,gameMobile.pause);
    await mobile.screenshot({path:'tools/screenshots/v28-game-mobile.png'});

    const desktop=await browser.newPage({viewport:{width:1366,height:768}});
    desktop.on('pageerror',e=>errors.push(e.message));
    await desktop.goto('http://localhost:8243/',{waitUntil:'networkidle'});
    await desktop.waitForTimeout(800);
    const menuDesktop=await desktop.evaluate(()=>({hero:getComputedStyle(document.querySelector('.screen-menu'),'::before').backgroundImage,overflow:document.documentElement.scrollWidth>innerWidth}));
    await desktop.screenshot({path:'tools/screenshots/v28-menu-desktop.png'});

    console.log(JSON.stringify({menuMobile,gameMobile,menuDesktop,errors},null,2));
    await browser.close();server.close();
    const ok=menuMobile.hero.includes('hero-anime-mobile')&&menuDesktop.hero.includes('hero-anime-desktop')&&!menuMobile.personalTokens&&!menuMobile.overflow&&gameMobile.globalHidden&&gameMobile.gameActive&&!gameMobile.topbarOverlap&&gameMobile.tiles===64&&!errors.length;
    process.exit(ok?0:1);
  }catch(e){console.error(e);server.close();process.exit(2);}
});
