// 移动端真实帧率测试：CPU 4x 限速 + 触摸模拟
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const PUB = path.join(__dirname, '..', 'public');
const MIME = { '.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.jpg':'image/jpeg', '.png':'image/png', '.webp':'image/webp', '.webmanifest':'application/manifest+json' };
const srv = http.createServer((q, s) => { let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html'; fs.readFile(path.join(PUB, p), (e, d) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); s.end(d); }); });
srv.listen(8249, async () => {
  try {
    const b = await chromium.launch({ channel: 'chrome', headless: true, args: ['--enable-features=Vulkan'] });
    // 模拟中端手机：CPU 4 倍限速
    const ctx = await b.newContext({ viewport: { width: 375, height: 812 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
    const p = await ctx.newPage();
    const client = await p.context().newCDPSession(p);
    await client.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    const errors = []; p.on('pageerror', e => errors.push(e.message));
    await p.goto('http://localhost:8249/', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
    await p.click('#menuContinue'); await p.waitForTimeout(2800);

    // 采集帧
    await p.evaluate(() => { window.__p = { frames: [], longTasks: [] }; try { new PerformanceObserver(l => l.getEntries().forEach(e => window.__p.longTasks.push(+e.duration.toFixed(1)))).observe({ entryTypes: ['longtask'] }); } catch (e) {} let last = performance.now(); (function loop(t) { window.__p.frames.push(+(t - last).toFixed(2)); last = t; requestAnimationFrame(loop); })(performance.now()); });

    async function doSwap(r, c) {
      const a = await p.locator(`.tile[data-r="${r}"][data-c="${c}"]`).boundingBox().catch(() => null);
      const b2 = await p.locator(`.tile[data-r="${r}"][data-c="${c+1}"]`).boundingBox().catch(() => null);
      if (!a || !b2) return;
      await p.mouse.move(a.x + a.width / 2, a.y + a.height / 2); await p.mouse.down();
      await p.mouse.move(b2.x + b2.width / 2, b2.y + b2.height / 2, { steps: 6 }); await p.mouse.up();
    }
    await p.waitForTimeout(3000); // 静止
    for (let i = 0; i < 12; i++) { const r = Math.floor(Math.random() * 8), c = Math.floor(Math.random() * 7); await doSwap(r, c); await p.waitForTimeout(900); }
    await p.waitForTimeout(3000); // 回落

    const r = await p.evaluate(() => {
      const f = window.__p.frames, avg = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0;
      const sF = f.slice(0, 180), eF = f.slice(f.length - 180), mF = f.slice(180, f.length - 180);
      return { total: f.length, static: { fps: +(1000 / (avg(sF) || 1)).toFixed(1), avg: +avg(sF).toFixed(2) }, swap: { fps: +(1000 / (avg(mF) || 1)).toFixed(1), avg: +avg(mF).toFixed(2), p95: +([...mF].sort((a, b) => a - b)[Math.floor(mF.length * 0.95)] || 0).toFixed(2) }, settle: { fps: +(1000 / (avg(eF) || 1)).toFixed(1) }, longTasks: window.__p.longTasks, longOver100: window.__p.longTasks.filter(d => d > 100).length };
    });
    console.log(JSON.stringify(r, null, 2));
    if (errors.length) console.log('ERRORS:', errors);
    await b.close(); srv.close(); process.exit(0);
  } catch (e) { console.error(e); srv.close(); process.exit(2); }
});
