const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const PUB = path.join(__dirname, '..', 'public');
const MIME = { '.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.jpg':'image/jpeg', '.png':'image/png', '.webp':'image/webp', '.webmanifest':'application/manifest+json' };
const srv = http.createServer((q, s) => {
  let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html';
  fs.readFile(path.join(PUB, p), (e, d) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); s.end(d); });
});
function countRAF(p, ms) {
  return p.evaluate(ms => new Promise(resolve => {
    const orig = requestAnimationFrame; let c = 0;
    requestAnimationFrame = (cb) => { c++; return orig.call(window, cb); };
    setTimeout(() => { requestAnimationFrame = orig; resolve(c); }, ms);
  }), ms);
}
srv.listen(8246, async () => {
  try {
    const b = await chromium.launch({ channel: 'chrome', headless: true });
    const p = await b.newPage({ viewport: { width: 375, height: 812 }, deviceScaleFactor: 2 });
    const errors = []; p.on('pageerror', e => errors.push(e.message));
    await p.goto('http://localhost:8246/', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);

    // 菜单切到 neon
    for (let i = 0; i < 3; i++) { await p.click('#bgBtn'); await p.waitForTimeout(250); }
    const bg = await p.evaluate(() => document.documentElement.dataset.bg);
    console.log('菜单背景:', bg);
    await p.click('#menuContinue'); await p.waitForTimeout(2600);

    if (bg === 'neon') {
      const c = await countRAF(p, 2000);
      console.log('neon 游戏中 2s RAF:', c, '(应>0)');
    }

    // 回菜单切 cloud 再进游戏测静止
    await p.click('#pauseBtn'); await p.waitForTimeout(400);
    await p.click('#pauseMenuBtn'); await p.waitForTimeout(500);
    let cur = '';
    for (let i = 0; i < 3; i++) { cur = await p.evaluate(() => document.documentElement.dataset.bg); if (cur === 'cloud') break; await p.click('#bgBtn'); await p.waitForTimeout(250); }
    console.log('切回背景:', cur);
    await p.click('#menuContinue'); await p.waitForTimeout(2600);
    const c0 = await countRAF(p, 2000);
    console.log('cloud 游戏静止 2s RAF:', c0, '(应0)');

    // 后台
    await p.evaluate(() => Object.defineProperty(document, 'hidden', { get: () => true, configurable: true }));
    await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
    await p.waitForTimeout(300);
    const ch = await countRAF(p, 1500);
    console.log('后台 1.5s RAF:', ch, '(应0)');

    console.log('错误:', errors.length);
    await b.close(); srv.close();
    process.exit(c0 === 0 && ch === 0 && !errors.length ? 0 : 1);
  } catch (e) { console.error(e); srv.close(); process.exit(2); }
});
