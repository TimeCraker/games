const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const MIME = { '.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.jpg':'image/jpeg', '.png':'image/png', '.webp':'image/webp', '.webmanifest':'application/manifest+json' };
const server = http.createServer((req,res) => {
  let pathname = decodeURIComponent(req.url.split('?')[0]);
  if(pathname === '/') pathname = '/index.html';
  fs.readFile(path.join('public', pathname), (error,data) => {
    if(error){ res.writeHead(404); res.end(); return; }
    res.writeHead(200, {'Content-Type':MIME[path.extname(pathname)] || 'application/octet-stream'});
    res.end(data);
  });
});

async function inspectMenu(browser, viewport, name){
  const page = await browser.newPage({ viewport });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://localhost:8242/', { waitUntil:'networkidle' });
  await page.waitForTimeout(800);
  const result = await page.evaluate(() => {
    const inside = element => {
      const r = element.getBoundingClientRect();
      return r.left >= -1 && r.top >= -1 && r.right <= innerWidth + 1 && r.bottom <= innerHeight + 1;
    };
    return {
      title: document.querySelector('.menu-title')?.textContent.trim(),
      tokens: [...document.querySelectorAll('.menu-token img')].filter(image => image.complete && image.naturalWidth > 0).length,
      controlsInside: [...document.querySelectorAll('.global-bar .icon-btn')].every(inside),
      primaryInside: inside(document.querySelector('#menuContinue')),
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
      touchSize: Math.round(document.querySelector('#settingsBtn').getBoundingClientRect().width),
      menuActive: document.documentElement.classList.contains('menu-active')
    };
  });
  await page.screenshot({ path:`tools/screenshots/v27-${name}.png` });
  await page.close();
  return { name, ...result, errors };
}

server.listen(8242, async () => {
  try {
    const browser = await chromium.launch({ channel:'chrome', headless:true });
    const layouts = [];
    layouts.push(await inspectMenu(browser, {width:375,height:812}, 'mobile'));
    layouts.push(await inspectMenu(browser, {width:1366,height:768}, 'desktop'));
    layouts.push(await inspectMenu(browser, {width:844,height:390}, 'landscape'));
    console.log(JSON.stringify(layouts, null, 2));

    const page = await browser.newPage({ viewport:{width:375,height:812} });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://localhost:8242/', { waitUntil:'networkidle' });
    await page.click('#themeBtn');
    await page.click('#settingsBtn');
    await page.waitForTimeout(400);
    const settingsVisible = await page.locator('#modalSettings').isVisible();
    await page.click('#settingsClose');
    await page.waitForTimeout(400);
    await page.click('#menuLevels');
    await page.waitForTimeout(450);
    const levelsVisible = await page.locator('#screenLevels.show').isVisible();
    await page.click('#levelsBack');
    await page.click('#menuContinue');
    await page.waitForTimeout(2400);
    const tiles = await page.locator('.tile').count();
    console.log(JSON.stringify({ settingsVisible, levelsVisible, tiles, interactionErrors:errors }, null, 2));
    await browser.close();
    server.close();
    process.exit(errors.length || !settingsVisible || !levelsVisible || tiles !== 64 ? 1 : 0);
  } catch(error){
    console.error(error);
    server.close();
    process.exit(2);
  }
});
