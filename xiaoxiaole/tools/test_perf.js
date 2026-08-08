// 性能基准测试：FPS / 帧耗时 / Long Task / Heap
// 场景：静止5s -> 随机交换20次 -> 回落5s
// 用法：node tools/test_perf.js [tag]   tag 默认 baseline
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');

const PUB = path.join(__dirname, '..', 'public');
const MIME = { '.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.jpg':'image/jpeg', '.png':'image/png', '.webp':'image/webp', '.webmanifest':'application/manifest+json' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/') p = '/index.html';
  fs.readFile(path.join(PUB, p), (e, d) => {
    if (e) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
    res.end(d);
  });
});
const VIEWPORT = { width: 375, height: 812, deviceScaleFactor: 2, isMobile: true, hasTouch: true };
const pct = (arr, p) => { if (!arr.length) return 0; const s = [...arr].sort((a, b) => a - b); return s[Math.floor((p / 100) * (s.length - 1))]; };
const avg = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

server.listen(8244, async () => {
  try {
    const browser = await chromium.launch({ channel: 'chrome', headless: true });
    const page = await browser.newPage({ viewport: VIEWPORT });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://localhost:8244/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.click('#menuContinue');
    await page.waitForTimeout(2600);

    // 注入采集器：帧间隔 + longtask
    await page.evaluate(() => {
      window.__p = { frames: [], longTasks: [] };
      try { new PerformanceObserver(l => l.getEntries().forEach(e => window.__p.longTasks.push(+e.duration.toFixed(1)))).observe({ entryTypes: ['longtask'] }); } catch (e) {}
      let last = performance.now();
      (function loop(t) { window.__p.frames.push(+(t - last).toFixed(2)); last = t; requestAnimationFrame(loop); })(performance.now());
    });

    async function doSwap(r, c, r2, c2) {
      const a = await page.locator(`.tile[data-r="${r}"][data-c="${c}"]`).boundingBox().catch(() => null);
      const b = await page.locator(`.tile[data-r="${r2}"][data-c="${c2}"]`).boundingBox().catch(() => null);
      if (!a || !b) return;
      await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2);
      await page.mouse.down();
      await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 6 });
      await page.mouse.up();
    }

    await page.waitForTimeout(5000);                              // 静止 5s
    for (let i = 0; i < 20; i++) {                                // 随机交换 20 次
      const r = Math.floor(Math.random() * 8), c = Math.floor(Math.random() * 7);
      await doSwap(r, c, r, c + 1);
      await page.waitForTimeout(850);
    }
    await page.waitForTimeout(5000);                              // 回落 5s

    const final = await page.evaluate(() => {
      const avg = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
      const pct = (arr, p) => { if (!arr.length) return 0; const s = [...arr].sort((a, b) => a - b); return s[Math.floor((p / 100) * (s.length - 1))]; };
      const f = window.__p.frames;
      // 静止段约前300帧，回落段约后300帧，中间为交换段
      const n = f.length, sEnd = Math.min(300, n), eStart = Math.max(sEnd, n - 300);
      const staticF = f.slice(0, sEnd), settleF = f.slice(eStart), swapF = f.slice(sEnd, eStart);
      return {
        totalFrames: n, durationMs: Math.round(f.reduce((a, b) => a + b, 0)),
        static: { n: staticF.length, avgMs: +avg(staticF).toFixed(2), p95Ms: +pct(staticF, 95).toFixed(2), fps: +(1000 / avg(staticF) || 0).toFixed(1) },
        swap: { n: swapF.length, avgMs: +avg(swapF).toFixed(2), p95Ms: +pct(swapF, 95).toFixed(2), p99Ms: +pct(swapF, 99).toFixed(2), fps: +(1000 / avg(swapF) || 0).toFixed(1) },
        settle: { n: settleF.length, avgMs: +avg(settleF).toFixed(2), p95Ms: +pct(settleF, 95).toFixed(2), fps: +(1000 / avg(settleF) || 0).toFixed(1) },
        longTasks: window.__p.longTasks, longTaskCount: window.__p.longTasks.length,
        longTaskMax: window.__p.longTasks.length ? Math.round(Math.max(...window.__p.longTasks)) : 0,
        longTaskOver100: window.__p.longTasks.filter(d => d > 100).length,
        heap: performance.memory ? { usedMB: Math.round(performance.memory.usedJSHeapSize / 1048576), totalMB: Math.round(performance.memory.totalJSHeapSize / 1048576) } : null,
      };
    });
    final.errors = errors;

    const tag = process.argv[2] || 'baseline';
    const dir = path.join(__dirname, '..', 'docs', 'perf', tag === 'baseline' ? 'baseline' : 'after');
    fs.mkdirSync(dir, { recursive: true });
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    fs.writeFileSync(path.join(dir, `perf-${ts}.json`), JSON.stringify(final, null, 2));

    console.log(`\n=== PERF [${tag}] ${ts} ===`);
    console.log(`静止: ${final.static.fps} fps (avg ${final.static.avgMs}ms, p95 ${final.static.p95Ms}ms)`);
    console.log(`交换: ${final.swap.fps} fps (avg ${final.swap.avgMs}ms, p95 ${final.swap.p95Ms}ms, p99 ${final.swap.p99Ms}ms)`);
    console.log(`回落: ${final.settle.fps} fps (avg ${final.settle.avgMs}ms)`);
    console.log(`LongTask: ${final.longTaskCount} 个, 最大 ${final.longTaskMax}ms, >100ms ${final.longTaskOver100} 个`);
    if (final.heap) console.log(`Heap: used ${final.heap.usedMB}MB / total ${final.heap.totalMB}MB`);
    if (errors.length) console.log('ERRORS:', errors);

    await browser.close(); server.close();
    process.exit(errors.length ? 1 : 0);
  } catch (e) { console.error(e); server.close(); process.exit(2); }
});
