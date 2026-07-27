/* ============================================================
   桓睿消消乐 - 游戏核心
   架构：DOM 持久化 + transform 定位（支持流畅动画）
   功能：三消 · 连击 · 炸弹 · 彩虹 · 粒子特效 · Web Audio 音效
   ============================================================ */
(() => {
'use strict';

// ---------- 配置 ----------
const ROWS = 8, COLS = 8;
const TYPES = 4;                 // 4 种照片方块
const TARGET = 1500;             // 通关分数
const SWAP_DUR = 260;            // 交换动画时长 ms
const REMOVE_DUR = 420;          // 消除动画时长
const FALL_DUR = 320;            // 下落动画时长
const GAP = 8;                   // 间隙 px（与 css 同步）
const PAD = 10;                  // 棋盘内边距
const SWIPE_THRESH = 0.35;       // 滑动触发阈值（相对格子）

const FACE_IMG = [];
for (let i = 0; i < TYPES; i++) FACE_IMG.push(`./assets/faces/face${i}.jpg`);
const ACCENT = ['#ff6b6b', '#4ecdc4', '#ffd93d', '#a78bfa'];

const SPECIAL = { NONE: 0, BOMB: 1, RAINBOW: 2 };

// ---------- DOM ----------
const $ = id => document.getElementById(id);
const boardEl = $('board');
const boardWrap = $('boardWrap');
const board3d = document.querySelector('.board-3d');
const fxCanvas = $('fxCanvas');
const floatLayer = $('floatLayer');
const scoreEl = $('score');
const progressBar = $('progressBar');
const progressText = $('progressText');
const comboEl = $('combo');
const comboCard = $('comboCard');
const hintEl = $('hint');
const startOverlay = $('startOverlay');
const winModal = $('winModal');
const finalScoreEl = $('finalScore');
const modalStats = $('modalStats');
const toastEl = $('toast');
const appEl = document.querySelector('.app');

// ---------- 状态 ----------
let board = [];          // board[r][c] = {type, special, el} | null
let tileSize = 0;
let cellUnit = 0;        // tileSize + gap
let score = 0;
let moves = 0;
let combo = 0;
let busy = false;
let started = false;
let stats = { clears: 0, combos: 0, maxCombo: 0, bombs: 0, rainbows: 0 };
let pointerStart = null; // {r,c,x,y,t,el}

// ---------- 工具 ----------
const sleep = ms => new Promise(r => setTimeout(r, ms));
const rnd = n => Math.floor(Math.random() * n);
const inBounds = (r, c) => r >= 0 && r < ROWS && c >= 0 && c < COLS;

function showToast(msg, dur = 1600) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toastEl.classList.remove('show'), dur);
}

// ---------- 尺寸 ----------
function measure() {
  const w = boardEl.clientWidth - PAD * 2;
  tileSize = (w - GAP * (COLS - 1)) / COLS;
  cellUnit = tileSize + GAP;
  boardEl.style.setProperty('--tile-size', tileSize + 'px');
  boardEl.style.setProperty('--gap', GAP + 'px');
  boardEl.style.setProperty('--board-pad', PAD + 'px');
}

function posOf(r, c) {
  return { x: c * cellUnit, y: r * cellUnit };
}

// ---------- 方块创建 ----------
function makeTile(r, c, type, special = SPECIAL.NONE) {
  const el = document.createElement('div');
  el.className = `tile t${type}`;
  if (special === SPECIAL.BOMB) el.classList.add('special-bomb');
  if (special === SPECIAL.RAINBOW) el.classList.add('special-rainbow');
  el.dataset.r = r; el.dataset.c = c; el.dataset.type = type;

  const face = document.createElement('div'); face.className = 'face';
  const img = document.createElement('img');
  img.src = FACE_IMG[type]; img.draggable = false; img.alt = '';
  img.onerror = () => { face.style.background = ACCENT[type]; };
  face.appendChild(img);
  const ring = document.createElement('div'); ring.className = 'ring';
  el.appendChild(face); el.appendChild(ring);

  if (special !== SPECIAL.NONE) {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = special === SPECIAL.BOMB ? '💣' : '🌈';
    el.appendChild(badge);
  }

  const { x, y } = posOf(r, c);
  el.style.setProperty('--tx', x + 'px');
  el.style.setProperty('--ty', y + 'px');
  el.style.transform = `translate3d(${x}px, ${y}px, 8px)`;
  el.style.width = el.style.height = tileSize + 'px';

  bindInput(el);
  boardEl.appendChild(el);
  return el;
}

function placeTile(t, r, c, animate = true) {
  const { x, y } = posOf(r, c);
  t.el.dataset.r = r; t.el.dataset.c = c;
  t.el.style.setProperty('--tx', x + 'px');
  t.el.style.setProperty('--ty', y + 'px');
  t.el.style.transform = `translate3d(${x}px, ${y}px, 8px)`;
  if (!animate) t.el.style.transition = 'none';
  return sleep(animate ? SWAP_DUR : 0).then(() => {
    if (!animate) t.el.style.transition = '';
  });
}

// ---------- 初始化棋盘 ----------
function initBoard() {
  boardEl.querySelectorAll('.tile').forEach(e => e.remove());
  board = [];
  for (let r = 0; r < ROWS; r++) {
    board[r] = [];
    for (let c = 0; c < COLS; c++) {
      let type;
      do { type = rnd(TYPES); } while (createsImmediateMatch(r, c, type));
      const el = makeTile(r, c, type, SPECIAL.NONE);
      board[r][c] = { type, special: SPECIAL.NONE, el };
    }
  }
  // 入场动画
  requestAnimationFrame(() => {
    boardEl.querySelectorAll('.tile').forEach((e, i) => {
      e.style.transition = 'none';
      e.style.opacity = '0';
      setTimeout(() => {
        e.style.transition = '';
        e.classList.add('spawning');
        e.style.opacity = '';
        setTimeout(() => e.classList.remove('spawning'), 450);
      }, i * 12);
    });
  });
}

function createsImmediateMatch(r, c, type) {
  if (c >= 2 && board[r][c-1]?.type === type && board[r][c-2]?.type === type) return true;
  if (r >= 2 && board[r-1][c]?.type === type && board[r-2][c]?.type === type) return true;
  return false;
}

// ---------- 匹配检测 ----------
function findAllMatches() {
  const matched = new Set(); // "r,c"
  const runs = [];           // [{cells:[{r,c}...], type, dir}]

  // 横向
  for (let r = 0; r < ROWS; r++) {
    let c = 0;
    while (c < COLS) {
      const t = board[r][c];
      if (!t) { c++; continue; }
      let k = c + 1;
      while (k < COLS && board[r][k] && board[r][k].type === t.type) k++;
      if (k - c >= 3) {
        const cells = [];
        for (let i = c; i < k; i++) { cells.push({r, c: i}); matched.add(`${r},${i}`); }
        runs.push({ cells, type: t.type, dir: 'h', len: k - c });
      }
      c = k;
    }
  }
  // 纵向
  for (let c = 0; c < COLS; c++) {
    let r = 0;
    while (r < ROWS) {
      const t = board[r][c];
      if (!t) { r++; continue; }
      let k = r + 1;
      while (k < ROWS && board[k][c] && board[k][c].type === t.type) k++;
      if (k - r >= 3) {
        const cells = [];
        for (let i = r; i < k; i++) { cells.push({r: i, c}); matched.add(`${i},${c}`); }
        runs.push({ cells, type: t.type, dir: 'v', len: k - r });
      }
      r = k;
    }
  }
  return { matched, runs };
}

// ---------- 交换 ----------
async function trySwap(r1, c1, r2, c2) {
  if (busy || !started) return;
  if (!inBounds(r1,c1) || !inBounds(r2,c2)) return;
  const adj = (Math.abs(r1-r2) + Math.abs(c1-c2)) === 1;
  if (!adj) return;

  const a = board[r1][c1], b = board[r2][c2];
  if (!a || !b) return;

  // 彩虹球：与任意方块交换 -> 清除该类型全场
  if (a.special === SPECIAL.RAINBOW || b.special === SPECIAL.RAINBOW) {
    busy = true; clearSelection();
    swapData(r1,c1,r2,c2);
    await Promise.all([placeTile(a, r2, c2), placeTile(b, r1, c1)]);
    sfx.swap();
    const rainbow = a.special === SPECIAL.RAINBOW ? a : b;
    const otherType = (a.special === SPECIAL.RAINBOW ? b : a).type;
    // 清除全场该类型 + 彩虹本身
    const targets = [];
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
      if (board[r][c] && (board[r][c].type === otherType || board[r][c] === rainbow)) targets.push({r,c});
    }
    await removeCells(targets, { rainbow: true });
    combo = 0;
    await cascade();
    afterMove();
    return;
  }

  busy = true; clearSelection();
  swapData(r1,c1,r2,c2);
  await Promise.all([placeTile(a, r2, c2), placeTile(b, r1, c1)]);
  sfx.swap();

  const { matched } = findAllMatches();
  if (matched.size > 0) {
    combo = 0;
    await cascade();
  } else {
    // 换回
    swapData(r2,c2,r1,c1);
    await Promise.all([placeTile(a, r1, c1), placeTile(b, r2, c2)]);
    sfx.invalid();
    showToast('这里消除不了哦～');
  }
  afterMove();
}

function swapData(r1,c1,r2,c2) {
  const t = board[r1][c1];
  board[r1][c1] = board[r2][c2];
  board[r2][c2] = t;
}

function afterMove() {
  moves++;
  busy = false;
  updateHUD();
  if (score >= TARGET && !winModal.classList.contains('show')) {
    setTimeout(showWin, 500);
    return;
  }
  // 死局检测：无可行交换则洗牌
  if (!hasPossibleMove()) {
    showToast('没有可消除的组合，重新洗牌！');
    setTimeout(shuffleBoard, 600);
  }
}

// ---------- 死局检测 / 洗牌 ----------
function hasPossibleMove() {
  // 检查是否存在一次交换能产生匹配，或存在特殊方块（总能触发）
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const t = board[r][c];
    if (t && t.special !== SPECIAL.NONE) return true;
  }
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    // 尝试与右、下交换
    if (c < COLS - 1) { swapData(r,c,r,c+1); const m = findAllMatches().matched.size; swapData(r,c,r,c+1); if (m) return true; }
    if (r < ROWS - 1) { swapData(r,c,r+1,c); const m = findAllMatches().matched.size; swapData(r,c,r+1,c); if (m) return true; }
  }
  return false;
}

async function shuffleBoard() {
  busy = true;
  // 收集所有方块类型，打乱后重新分布，保证无初始三连且有解
  const types = [];
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (board[r][c]) types.push(board[r][c].type);
  let attempts = 0;
  do {
    // Fisher-Yates 洗牌
    for (let i = types.length - 1; i > 0; i--) { const j = rnd(i+1); [types[i], types[j]] = [types[j], types[i]]; }
    let idx = 0;
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
      if (board[r][c]) { board[r][c].type = types[idx++]; board[r][c].el.dataset.type = board[r][c].type;
        board[r][c].el.className = `tile t${board[r][c].type}`;
        const img = board[r][c].el.querySelector('img'); if (img) img.src = FACE_IMG[board[r][c].type];
      }
    }
    attempts++;
  } while ((findAllMatches().matched.size > 0 || !hasPossibleMove()) && attempts < 50);
  // 洗牌动画：全部 tile 抖动
  boardEl.querySelectorAll('.tile').forEach(e => { e.classList.add('spawning'); setTimeout(()=>e.classList.remove('spawning'), 450); });
  await sleep(500);
  busy = false;
}

// ---------- 连锁消除 ----------
async function cascade() {
  let chain = 0;
  while (true) {
    const { matched, runs } = findAllMatches();
    if (matched.size === 0) break;
    chain++; combo++;
    stats.combos = Math.max(stats.combos, combo);
    stats.maxCombo = Math.max(stats.maxCombo, combo);

    // 计算特殊方块生成
    const specials = planSpecials(runs);
    // 收集要消除的格子（含特殊方块触发）
    let toRemove = new Set(matched);
    // 触发已存在的特殊方块（若被包含在匹配中）
    const triggered = collectSpecialTriggers(matched);
    for (const k of triggered) toRemove.add(k);
    toRemove = expandSpecials(toRemove);

    const gain = scoreFor(toRemove.size, combo);
    score += gain;
    stats.clears += toRemove.size;
    updateHUD();

    // 飘字
    const center = centerOf(toRemove);
    floatText(center, `+${gain}`, combo >= 2 ? 'combo' : '');
    if (combo >= 2) floatText({ ...center, dy: -34 }, `COMBO ×${combo}`, 'combo big');

    // 音效
    sfx.clear(combo);
    // 含炸弹则额外爆破音
    if ([...toRemove].some(k => { const {r,c}=parseKey(k); const t=board[r]&&board[r][c]; return t&&t.special===SPECIAL.BOMB; })) sfx.bomb();

    await removeCells(Array.from(toRemove).map(parseKey), { specials });

    // 生成特殊方块
    await placeSpecials(specials);

    // 下落 + 填充
    await dropAndFill();
  }
  combo = 0;
  updateHUD();
}

function scoreFor(n, c) {
  const base = n * 30;
  const mult = 1 + (c - 1) * 0.5;
  return Math.round(base * mult);
}

// 特殊方块生成规划：每个 >=4 的 run 生成一个特殊方块
function planSpecials(runs) {
  const out = [];
  for (const run of runs) {
    if (run.len >= 5) {
      const mid = run.cells[Math.floor(run.cells.length / 2)];
      out.push({ r: mid.r, c: mid.c, type: run.type, special: SPECIAL.RAINBOW });
      stats.rainbows++;
    } else if (run.len >= 4) {
      const mid = run.cells[Math.floor(run.cells.length / 2)];
      out.push({ r: mid.r, c: mid.c, type: run.type, special: SPECIAL.BOMB });
      stats.bombs++;
    }
  }
  return out;
}

// 收集被匹配触发的已有特殊方块
function collectSpecialTriggers(matchedSet) {
  const extra = new Set();
  for (const key of matchedSet) {
    const { r, c } = parseKey(key);
    const t = board[r][c];
    if (t && t.special !== SPECIAL.NONE) extra.add(key);
  }
  return extra;
}

// 扩展特殊方块范围（炸弹 3x3）
function expandSpecials(set) {
  const result = new Set(set);
  const queue = Array.from(set);
  const seen = new Set(set);
  while (queue.length) {
    const key = queue.shift();
    const { r, c } = parseKey(key);
    const t = board[r] && board[r][c];
    if (!t) continue;
    if (t.special === SPECIAL.BOMB) {
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
        const nr = r + dr, nc = c + dc;
        if (!inBounds(nr, nc)) continue;
        const k = `${nr},${nc}`;
        if (!seen.has(k)) {
          seen.add(k); result.add(k); queue.push(k);
        }
      }
    }
  }
  return result;
}

async function placeSpecials(specials) {
  for (const s of specials) {
    // 该位置可能已被消除（在下落中），需要保留生成
    const existing = board[s.r] && board[s.r][s.c];
    // 在 removeCells 中已设为 null，这里重建
    const el = makeTile(s.r, s.c, s.type, s.special);
    el.classList.add('spawning');
    const tile = { type: s.type, special: s.special, el };
    board[s.r][s.c] = tile;
    setTimeout(() => el.classList.remove('spawning'), 450);
    await sleep(60);
  }
}

// ---------- 消除单元格 ----------
async function removeCells(cells, opts = {}) {
  // 粒子 & 动画
  for (const { r, c } of cells) {
    const t = board[r] && board[r][c];
    if (!t) continue;
    spawnParticles(r, c, t.type, opts.rainbow);
    t.el.classList.add('removing');
  }
  // 屏幕震动（大消除）
  if (cells.length >= 5) { appEl.classList.add('shake'); setTimeout(() => appEl.classList.remove('shake'), 350); }
  await sleep(REMOVE_DUR);
  for (const { r, c } of cells) {
    const t = board[r] && board[r][c];
    if (!t) continue;
    t.el.remove();
    board[r][c] = null;
  }
}

// ---------- 下落 + 填充 ----------
async function dropAndFill() {
  // 计算每列下落
  const newTiles = [];
  for (let c = 0; c < COLS; c++) {
    let write = ROWS - 1;
    for (let r = ROWS - 1; r >= 0; r--) {
      if (board[r][c]) {
        if (r !== write) {
          board[write][c] = board[r][c];
          board[r][c] = null;
          placeTile(board[write][c], write, c, true);
        }
        write--;
      }
    }
    // 顶部填充新方块
    for (let r = write; r >= 0; r--) {
      const type = rnd(TYPES);
      const el = makeTile(r, c, type, SPECIAL.NONE);
      // 从上方落下：先定位到棋盘上方
      const startY = -(write - r + 1) * cellUnit;
      el.style.transition = 'none';
      el.style.transform = `translate3d(${c * cellUnit}px, ${startY}px, 8px)`;
      const tile = { type, special: SPECIAL.NONE, el };
      board[r][c] = tile;
      newTiles.push({ tile, r, c });
    }
  }
  // 触发下落动画
  await sleep(20);
  for (const { tile, r, c } of newTiles) {
    tile.el.style.transition = '';
    placeTile(tile, r, c, true);
  }
  await sleep(FALL_DUR);
}

// ---------- 粒子特效（Canvas） ----------
const ctx = fxCanvas.getContext('2d');
let particles = [];
let dpr = window.devicePixelRatio || 1;

function resizeFx() {
  dpr = window.devicePixelRatio || 1;
  const rect = boardEl.getBoundingClientRect();
  fxCanvas.width = rect.width * dpr;
  fxCanvas.height = rect.height * dpr;
  fxCanvas.style.width = rect.width + 'px';
  fxCanvas.style.height = rect.height + 'px';
}

function spawnParticles(r, c, type, rainbow) {
  const { x, y } = posOf(r, c);
  const cx = (x + tileSize / 2 + PAD) * dpr;
  const cy = (y + tileSize / 2 + PAD) * dpr;
  const color = rainbow ? ['#ff6b6b','#4ecdc4','#ffd93d','#a78bfa'] : [ACCENT[type], '#ffffff'];
  const n = 14;
  for (let i = 0; i < n; i++) {
    const a = (Math.PI * 2 * i) / n + Math.random() * 0.4;
    const sp = (1.6 + Math.random() * 2.4) * dpr;
    particles.push({
      x: cx, y: cy,
      vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 1,
      life: 1, decay: 0.018 + Math.random() * 0.02,
      size: (3 + Math.random() * 4) * dpr,
      color: color[i % color.length],
      rot: Math.random() * Math.PI, vr: (Math.random() - .5) * .3
    });
  }
  // 光环
  particles.push({ ring: true, x: cx, y: cy, r: 4 * dpr, life: 1, decay: 0.05, color: ACCENT[type] });
}

function tickParticles() {
  ctx.clearRect(0, 0, fxCanvas.width, fxCanvas.height);
  if (particles.length === 0) { requestAnimationFrame(tickParticles); return; }
  particles = particles.filter(p => {
    p.life -= p.decay;
    if (p.life <= 0) return false;
    if (p.ring) {
      p.r += 3 * dpr;
      ctx.save();
      ctx.globalAlpha = p.life * 0.6;
      ctx.strokeStyle = p.color; ctx.lineWidth = 3 * dpr;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
    } else {
      p.x += p.vx; p.y += p.vy; p.vy += 0.15 * dpr; p.rot += p.vr;
      ctx.save();
      ctx.globalAlpha = p.life;
      ctx.translate(p.x, p.y); ctx.rotate(p.rot);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
      ctx.restore();
    }
    return true;
  });
  requestAnimationFrame(tickParticles);
}

// ---------- 飘字 ----------
function centerOf(set) {
  let sx = 0, sy = 0, n = 0;
  for (const k of set) { const { r, c } = parseKey(k); const { x, y } = posOf(r, c); sx += x + tileSize/2; sy += y + tileSize/2; n++; }
  return { x: sx / n, y: sy / n };
}
function floatText(pos, text, cls = '') {
  const el = document.createElement('div');
  el.className = 'float-text ' + cls;
  el.textContent = text;
  el.style.left = (pos.x + PAD) + 'px';
  el.style.top = (pos.y + PAD + (pos.dy || 0)) + 'px';
  floatLayer.appendChild(el);
  setTimeout(() => el.remove(), 950);
}

function parseKey(k) { const [r, c] = k.split(',').map(Number); return { r, c }; }

// ---------- HUD ----------
function updateHUD() {
  scoreEl.textContent = score;
  const pct = Math.min(100, (score / TARGET) * 100);
  progressBar.style.width = pct + '%';
  progressText.textContent = `${score} / ${TARGET}`;
  comboEl.textContent = '×' + Math.max(1, combo);
  if (combo >= 2) { comboCard.classList.add('boom'); setTimeout(() => comboCard.classList.remove('boom'), 200); }
}

// ---------- 输入（点击两次 / 滑动） ----------
function bindInput(el) {
  el.addEventListener('pointerdown', onDown, { passive: false });
}

function onDown(e) {
  if (busy || !started) return;
  if (e.pointerType === 'mouse' && e.button !== 0) return;
  e.preventDefault();
  const el = e.currentTarget;
  const r = +el.dataset.r, c = +el.dataset.c;
  pointerStart = { r, c, x: e.clientX, y: e.clientY, el };
  el.setPointerCapture && el.setPointerCapture(e.pointerId);
  window.addEventListener('pointermove', onMove, { passive: false });
  window.addEventListener('pointerup', onUp, { once: true });
}

function onMove(e) {
  if (!pointerStart) return;
  const dx = e.clientX - pointerStart.x;
  const dy = e.clientY - pointerStart.y;
  const dist = Math.hypot(dx, dy);
  if (dist > tileSize * SWIPE_THRESH) {
    // 判定方向
    let nr = pointerStart.r, nc = pointerStart.c;
    if (Math.abs(dx) > Math.abs(dy)) nc += dx > 0 ? 1 : -1;
    else nr += dy > 0 ? 1 : -1;
    const sr = pointerStart.r, sc = pointerStart.c;
    cleanupPointer();
    trySwap(sr, sc, nr, nc);
  }
}

function onUp(e) {
  if (!pointerStart) return;
  const dx = e.clientX - pointerStart.x;
  const dy = e.clientY - pointerStart.y;
  if (Math.hypot(dx, dy) < tileSize * SWIPE_THRESH) {
    // 当作点击：选择/交换
    handleTap(pointerStart.r, pointerStart.c);
  }
  cleanupPointer();
}

function cleanupPointer() {
  pointerStart = null;
  window.removeEventListener('pointermove', onMove);
}

let selected = null;
function handleTap(r, c) {
  if (!selected) {
    selected = { r, c };
    board[r][c]?.el.classList.add('selected');
    sfx.select();
    return;
  }
  board[selected.r][selected.c]?.el.classList.remove('selected');
  if (selected.r === r && selected.c === c) { selected = null; return; }
  const adj = (Math.abs(selected.r - r) + Math.abs(selected.c - c)) === 1;
  if (adj) {
    const s = selected; selected = null;
    trySwap(s.r, s.c, r, c);
  } else {
    selected = { r, c };
    board[r][c]?.el.classList.add('selected');
    sfx.select();
  }
}
function clearSelection() {
  if (selected) { board[selected.r]?.[selected.c]?.el.classList.remove('selected'); selected = null; }
}

// ---------- 音效（Web Audio 合成） ----------
const sfx = (() => {
  let actx = null, enabled = true, master = null;
  function ensure() {
    if (!actx) {
      actx = new (window.AudioContext || window.webkitAudioContext)();
      master = actx.createGain(); master.gain.value = 0.5; master.connect(actx.destination);
    }
    if (actx.state === 'suspended') actx.resume();
    return actx;
  }
  function tone(freq, dur, type = 'sine', vol = 0.3, glide = 0) {
    if (!enabled) return;
    const a = ensure();
    const o = a.createOscillator(), g = a.createGain();
    o.type = type; o.frequency.value = freq;
    if (glide) o.frequency.exponentialRampToValueAtTime(freq * glide, a.currentTime + dur);
    g.gain.setValueAtTime(0, a.currentTime);
    g.gain.linearRampToValueAtTime(vol, a.currentTime + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + dur);
    o.connect(g); g.connect(master); o.start(); o.stop(a.currentTime + dur + 0.02);
  }
  function noise(dur, vol = 0.4) {
    if (!enabled) return;
    const a = ensure();
    const n = a.createBufferSource();
    const buf = a.createBuffer(1, a.sampleRate * dur, a.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    n.buffer = buf;
    const g = a.createGain(); g.gain.value = vol;
    const f = a.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 1200;
    n.connect(f); f.connect(g); g.connect(master); n.start();
  }
  return {
    enable: () => { enabled = true; ensure(); },
    disable: () => { enabled = false; },
    isEnabled: () => enabled,
    select: () => tone(520, 0.08, 'sine', 0.15),
    swap: () => { tone(440, 0.09, 'triangle', 0.2, 1.2); },
    invalid: () => tone(180, 0.18, 'sawtooth', 0.18, 0.6),
    clear: (combo) => {
      const base = 523 + (combo - 1) * 70;
      tone(base, 0.12, 'triangle', 0.22, 1.5);
      setTimeout(() => tone(base * 1.5, 0.1, 'sine', 0.16), 60);
    },
    bomb: () => { noise(0.3, 0.5); tone(120, 0.3, 'sawtooth', 0.3, 0.4); },
    win: () => { [523, 659, 784, 1047].forEach((f, i) => setTimeout(() => tone(f, 0.3, 'triangle', 0.3), i * 120)); },
  };
})();

// ---------- 主题 ----------
function setTheme(t) {
  document.documentElement.dataset.theme = t;
  $('themeBtn').querySelector('.ico').textContent = t === 'light' ? '🌙' : '☀️';
  localStorage.setItem('xxl-theme', t);
  $('themeBtn').title = t === 'light' ? '切换到深色' : '切换到浅色';
}

// ---------- 通关 ----------
function showWin() {
  finalScoreEl.textContent = score;
  modalStats.innerHTML = `消除方块 <b>${stats.clears}</b> · 触发连击 <b>${stats.combos}</b><br>最高 COMBO <b>×${stats.maxCombo}</b> · 炸弹 <b>${stats.bombs}</b> · 彩虹 <b>${stats.rainbows}</b>`;
  winModal.classList.add('show');
  sfx.win();
  confetti();
}

// ---------- 彩纸 ----------
function confetti() {
  const colors = ACCENT;
  for (let i = 0; i < 60; i++) {
    particles.push({
      x: Math.random() * fxCanvas.width,
      y: -10 * dpr,
      vx: (Math.random() - .5) * 4 * dpr,
      vy: (2 + Math.random() * 4) * dpr,
      life: 1, decay: 0.006,
      size: (4 + Math.random() * 5) * dpr,
      color: colors[rnd(colors.length)],
      rot: Math.random() * Math.PI, vr: (Math.random() - .5) * .3
    });
  }
}

// ---------- 重开 ----------
function restart() {
  score = 0; moves = 0; combo = 0; busy = false;
  stats = { clears: 0, combos: 0, maxCombo: 0, bombs: 0, rainbows: 0 };
  winModal.classList.remove('show');
  initBoard();
  updateHUD();
}

// ---------- 事件绑定 ----------
$('startBtn').addEventListener('click', () => {
  startOverlay.classList.remove('show');
  started = true; sfx.enable();
});
$('restartBtn').addEventListener('click', () => { if (confirm('确定重新开始吗？')) restart(); });
$('playAgainBtn').addEventListener('click', restart);
$('themeBtn').addEventListener('click', () => {
  setTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light');
});
$('soundBtn').addEventListener('click', () => {
  if (sfx.isEnabled()) { sfx.disable(); $('soundBtn').classList.add('off'); $('soundBtn').querySelector('.ico').textContent = '🔇'; }
  else { sfx.enable(); $('soundBtn').classList.remove('off'); $('soundBtn').querySelector('.ico').textContent = '🔊'; }
});

window.addEventListener('resize', () => { measure(); resizeFx(); relayoutAll(); });

function relayoutAll() {
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const t = board[r]?.[c]; if (!t) continue;
    const { x, y } = posOf(r, c);
    t.el.style.width = t.el.style.height = tileSize + 'px';
    t.el.style.setProperty('--tx', x + 'px');
    t.el.style.setProperty('--ty', y + 'px');
    t.el.style.transform = `translate3d(${x}px, ${y}px, 8px)`;
  }
}

// 防止页面滚动 / 双指缩放
document.addEventListener('touchmove', e => { if (e.touches.length > 1) e.preventDefault(); }, { passive: false });
document.addEventListener('gesturestart', e => e.preventDefault());

// ---------- 启动 ----------
function start() {
  const savedTheme = localStorage.getItem('xxl-theme') || 'light';
  setTheme(savedTheme);
  measure();
  resizeFx();
  initBoard();
  updateHUD();
  startOverlay.classList.add('show');
  requestAnimationFrame(tickParticles);
}
start();

})();
