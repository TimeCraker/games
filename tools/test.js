// 自动化测试：用系统 Chrome 打开游戏，检查无 JS 错误、DOM 结构、模拟交换
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PUB = path.join(__dirname, '..', 'public');
const PORT = 8231;
const MIME = { '.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.jpg':'image/jpeg', '.png':'image/png', '.webp':'image/webp', '.webmanifest':'application/manifest+json' };

function startServer() {
  return new Promise(resolve => {
    const srv = http.createServer((req, res) => {
      let p = decodeURIComponent(req.url.split('?')[0]);
      if (p === '/') p = '/index.html';
      const fp = path.join(PUB, p);
      fs.readFile(fp, (err, data) => {
        if (err) { res.writeHead(404); res.end('404'); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(fp)] || 'application/octet-stream' });
        res.end(data);
      });
    });
    srv.listen(PORT, () => resolve(srv));
  });
}

(async () => {
  const srv = await startServer();
  console.log('server on', PORT);
  const shotsDir = path.join(__dirname, 'screenshots');
  fs.mkdirSync(shotsDir, { recursive: true });

  const errors = [];
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 420, height: 860 }, deviceScaleFactor: 2 });
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));

  await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);

  // 截图：主菜单
  await page.screenshot({ path: path.join(shotsDir, '01-menu.png') });

  // 检查主菜单存在
  const menuVisible = await page.locator('#screenMenu').isVisible();
  console.log('menu visible:', menuVisible);

  // 全局主题按钮只在菜单/关卡页显示，先在主菜单验证切换
  const themeBefore = await page.evaluate(() => document.documentElement.dataset.theme);
  await page.click('#themeBtn');
  await page.waitForTimeout(300);
  const themeAfter = await page.evaluate(() => document.documentElement.dataset.theme);
  console.log('theme toggle in menu:', themeBefore, '->', themeAfter);

  // 点 "继续闯关/开始游戏" 进入第1关（会经过入场动画）
  await page.click('#menuContinue');
  // 入场动画 ~1.6s + 棋盘生成
  await page.waitForTimeout(2400);
  await page.screenshot({ path: path.join(shotsDir, '02-board.png') });

  // 检查棋盘数据
  const tileCount = await page.locator('.tile').count();
  console.log('tile count:', tileCount);
  const boardInfo = await page.evaluate(() => {
    const tiles = [...document.querySelectorAll('.tile')];
    return tiles.slice(0,3).map(t => ({ r:+t.dataset.r, c:+t.dataset.c, type:+t.dataset.type }));
  });
  console.log('first 3 tiles:', JSON.stringify(boardInfo));

  // 模拟交换：找两个相邻方块，用 pointer 事件
  // 取 (0,0) 和 (0,1)
  async function swap(r1, c1, r2, c2) {
    const t1 = page.locator(`.tile[data-r="${r1}"][data-c="${c1}"]`);
    const t2 = page.locator(`.tile[data-r="${r2}"][data-c="${c2}"]`);
    const b1 = await t1.boundingBox();
    const b2 = await t2.boundingBox();
    if (!b1 || !b2) return null;
    // 在 t1 中心按下，滑到 t2 中心抬起
    await page.mouse.move(b1.x + b1.width/2, b1.y + b1.height/2);
    await page.mouse.down();
    await page.mouse.move(b2.x + b2.width/2, b2.y + b2.height/2, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(1200);
    return true;
  }

  const scoreBefore = await page.textContent('#score');
  // 尝试若干次随机相邻交换，直到分数变化
  let moved = false;
  for (let i = 0; i < 12 && !moved; i++) {
    const r = Math.floor(Math.random() * 8), c = Math.floor(Math.random() * 7);
    await swap(r, c, r, c + 1);
    const s = await page.textContent('#score');
    if (s !== scoreBefore) { moved = true; console.log(`swap (${r},${c})<->(${r},${c+1}) score ${scoreBefore} -> ${s}`); }
  }
  await page.screenshot({ path: path.join(shotsDir, '03-after-swap.png') });
  const scoreAfter = await page.textContent('#score');
  console.log('score before/after:', scoreBefore, scoreAfter, moved ? '(有消除)' : '(未触发消除)');

  // 移动端视口再截一张
  await page.setViewportSize({ width: 380, height: 740 });
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(shotsDir, '05-mobile.png') });

  console.log('ERRORS:', errors.length);
  errors.forEach(e => console.log('  ', e));

  await browser.close();
  srv.close();
  process.exit(errors.length ? 1 : 0);
})().catch(e => { console.error('TEST CRASH:', e); process.exit(2); });
