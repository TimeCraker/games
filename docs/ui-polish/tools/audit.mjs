#! /usr/bin/env node
// 注意：本审计器从工作目录沿用 SITE_URL 与 CDP_HTTP 环境变量；产物写到 .ui-polish/artifacts（不进仓库）
/**
 * AsterNova UI-polish 零依赖审计器（CDP + Node 原生 WebSocket）
 * 用法：node audit.mjs [--routes /,/lobby] [--viewports desktop,mobile]
 * 环境变量：CDP_HTTP(默认 http://127.0.0.1:9333) SITE_URL(默认 http://127.0.0.1:3000)
 * 产物：artifacts/scan-<route>-<vp>.json + artifacts/shots/<route>-<vp>.png + artifacts/summary.json
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { inflateSync } from "node:zlib";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CDP_HTTP = process.env.CDP_HTTP || "http://127.0.0.1:9333";
const SITE = (process.env.SITE_URL || "http://127.0.0.1:3000").replace(/\/$/, "");
const OUT_DIR = process.env.OUT_DIR || path.resolve(HERE, "..", "artifacts");
const SHOTS_DIR = path.join(OUT_DIR, "shots");
fs.mkdirSync(SHOTS_DIR, { recursive: true });

const argv = process.argv.slice(2);
const argVal = (name, def) => { const i = argv.indexOf("--" + name); return i >= 0 && argv[i + 1] ? argv[i + 1] : def; };
const ROUTES = argVal("routes", "/,/login,/lobby,/arena,/shoot-them-all,/lets-running,/merge,/nebula-survivor,/xiaoxiaole,/this-route-does-not-exist").split(",").filter(Boolean);
const VIEWPORT_DEFS = {
  desktop: { width: 1440, height: 900, mobile: false, dpr: 1 },
  mobile: { width: 375, height: 812, mobile: true, dpr: 2 },
  tablet: { width: 768, height: 1024, mobile: false, dpr: 2 },
  wide: { width: 2560, height: 1440, mobile: false, dpr: 1 },
  tiny: { width: 320, height: 568, mobile: true, dpr: 2 },
};
const VIEWPORTS = argVal("viewports", "desktop,mobile").split(",").filter(Boolean).map((n) => ({
  name: n,
  ...(VIEWPORT_DEFS[n] || VIEWPORT_DEFS.desktop),
}));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const EDGE_EXE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const CHROME_EXE = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
/** CDP 无响应时自动拉起浏览器（Crashpad 禁用 + 工作区 profile，R8 踩坑配方） */
async function ensureBrowser() {
  try { await (await fetch(CDP_HTTP + "/json/version")).text(); return true; } catch {}
  if (typeof process === "undefined" || !process.getuid && !process.title) {}
  try {
    const { spawn } = await import("node:child_process");
    const exe = (await import("node:fs")).existsSync(EDGE_EXE) ? EDGE_EXE : CHROME_EXE;
    const flags = ["--headless=new","--no-sandbox","--disable-gpu","--disable-dev-shm-usage","--disable-features=Crashpad","--no-first-run","--window-size=1440,900","--remote-debugging-port=9333","--remote-allow-origins=*","--no-proxy-server","--user-data-dir=C:\\Users\\TimeCraker\\Desktop\\my_workspace\\games\\.ui-polish\\edge-profile","about:blank"];
    const child = spawn(exe, flags, { stdio: "ignore", detached: true });
    child.unref();
  } catch {}
  for (let i = 0; i < 30; i++) {
    await sleep(2000);
    try { await (await fetch(CDP_HTTP + "/json/version")).text(); return true; } catch {}
  }
  return false;
}


/** 零依赖 PNG 解码（8bit、RGB/RGBA；Adam interlace 不支持，CDP 截图无 interlace） */
function decodePng(buf) {
  if (buf.readUInt32BE(0) !== 0x89504e47) throw new Error("not a png");
  let pos = 8; let width = 0, height = 0, bitDepth = 0, colorType = 0;
  const idat = [];
  while (pos < buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.toString("ascii", pos + 4, pos + 8);
    const data = buf.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") { width = data.readUInt32BE(0); height = data.readUInt32BE(4); bitDepth = data[8]; colorType = data[9]; }
    else if (type === "IDAT") idat.push(data);
    else if (type === "IEND") break;
    pos += 12 + len;
  }
  if (bitDepth !== 8 || (colorType !== 6 && colorType !== 2)) throw new Error("unsupported png depth/type " + bitDepth + "/" + colorType);
  const raw = inflateSync(Buffer.concat(idat));
  const bpp = colorType === 6 ? 4 : 3;
  const stride = width * bpp;
  const out = Buffer.alloc(height * stride);
  let p = 0;
  for (let y = 0; y < height; y++) {
    const filter = raw[p++];
    const line = raw.subarray(p, p + stride); p += stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? out[y * stride + x - bpp] : 0;
      const b = y > 0 ? out[(y - 1) * stride + x] : 0;
      const c = x >= bpp && y > 0 ? out[(y - 1) * stride + x - bpp] : 0;
      let v = line[x];
      if (filter === 1) v = (v + a) & 255;
      else if (filter === 2) v = (v + b) & 255;
      else if (filter === 3) v = (v + ((a + b) >> 1)) & 255;
      else if (filter === 4) {
        const p0 = a + b - c;
        const pa = Math.abs(p0 - a), pb = Math.abs(p0 - b), pc = Math.abs(p0 - c);
        const pr = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
        v = (v + pr) & 255;
      }
      out[y * stride + x] = v;
    }
  }
  return { width, height, data: out, bpp };
}

function samplePng(png, x, y) {
  const cx = Math.max(0, Math.min(png.width - 1, Math.round(x)));
  const cy = Math.max(0, Math.min(png.height - 1, Math.round(y)));
  const o = (cy * png.width + cx) * png.bpp;
  return [png.data[o], png.data[o + 1], png.data[o + 2]];
}

/** 像素级对比度复核：screenshot 中取元素四角内缩点做真实底色，与 DOM 报告的
 *  文字色计算 WCAG 比值——弥补「渐变底/复杂背景」时 DOM 层无法判定的盲区。 */
function verifyPixels(base64, dpr, violations, dialogs = []) {
  let png;
  try { png = decodePng(Buffer.from(base64, "base64")); } catch (e) { return [{ error: String((e && e.message) || e) }]; }
  const lumOf = (c) => { const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratioOf = (a, b) => { const l1 = lumOf(a), l2 = lumOf(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
  const visDialogs = (dialogs || []).filter((d) => d.visible && d.rect);
  const inDialog = (x, y) => visDialogs.some((d) => { const [l, t, w, h] = d.rect; return x >= l && x <= l + w && y >= t && y <= t + h; });
  const out = [];
  for (const v of violations) {
    if (!v.rect || !v.fg) continue;
    const [left, top, w, h] = v.rect;
    const raw = { r: v.fg[0], g: v.fg[1], b: v.fg[2], a: (v.fg[3] ?? 100) / 100 };
    if (w < 8 || h < 8) continue;
    const elInDialog = v.inDialogEl !== undefined ? v.inDialogEl === true : inDialog(left + w / 2, top + h / 2);
    const vw = png.width / dpr, vh = png.height / dpr;
    const vTop = Math.max(0, top), vBottom = Math.min(top + h, vh), vLeft = Math.max(0, left), vRight = Math.min(left + w, vw);
    if (vBottom - vTop < 6 || vRight - vLeft < 6) { out.push({ x: v.x.slice(0, 24), need: v.need, domRatio: v.ratio, obscured: true, note: "元素大部分在视口外" }); continue; }
    const padY = Math.min(8, (vBottom - vTop) / 2), padX = Math.min(Math.max(4, w * 0.11), (vRight - vLeft) / 3);
    const pts = [[vLeft + padX, vTop + padY], [vRight - padX, vTop + padY], [vLeft + padX, vBottom - padY], [vRight - padX, vBottom - padY]];
    const obscuredSamples = pts.filter(([x, y]) => !elInDialog && inDialog(x, y)).length;
    if (obscuredSamples === pts.length) { out.push({ x: v.x.slice(0, 24), need: v.need, domRatio: v.ratio, obscured: true, note: "元素被打开的弹层遮罩覆盖，采样无代表性（弹层关闭后复核）" }); continue; }
    const samples = pts.map(([x, y]) => { const px = samplePng(png, (x + 0.5) * dpr, (y + 0.5) * dpr); return { r: px[0], g: px[1], b: px[2] }; });
    const fg = raw.a < 1 ? { r: raw.r * raw.a + samples[0].r * (1 - raw.a), g: raw.g * raw.a + samples[0].g * (1 - raw.a), b: raw.b * raw.a + samples[0].b * (1 - raw.a) } : raw;
    const ratios = samples.map((s) => Math.round(ratioOf(fg, s) * 10) / 10);
    out.push({ x: v.x.slice(0, 24), need: v.need, domRatio: v.ratio, sampled: ratios, best: Math.max(...ratios), pass: Math.max(...ratios) >= v.need });
  }
  return out;
}

class Cdp {
  constructor(url) { this.ws = new WebSocket(url); this.id = 0; this.pending = new Map(); this.events = []; }
  async open() {
    await new Promise((res, rej) => { this.ws.onopen = res; this.ws.onerror = () => rej(new Error("ws open failed")); });
    this.ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id) { const p = this.pending.get(m.id); if (p) { this.pending.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } }
      else this.events.push(m);
    };
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async close() { try { if (this.targetId) await this.send("Target.closeTarget", { targetId: this.targetId }); } catch {} try { this.ws.close(); } catch {} }
}

async function newTab(route) {
  await ensureBrowser();
  const t = await (await fetch(CDP_HTTP + "/json/new?about:blank", { method: "PUT" })).json();
  const cdp = new Cdp(t.webSocketDebuggerUrl);
  cdp.targetId = t.id;
  await cdp.open();
  return cdp;
}

const MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1";

/** localStorage 种子：让 /lobby 免登录渲染（游戏大厅审计用） */
const SEED_SCRIPT = `
try {
  if (location.origin !== "null") {
    localStorage.setItem("game-store", JSON.stringify({ state: { token: "audit-token", userId: 7, username: "审计访客", selectedClass: "Role2_Cursemancer", currentRoomId: "" }, version: 0 }));
    localStorage.setItem("asternova-lobby-avatar-id", "avatar-3");
  }
} catch (e) {}`;

const AUDIT_FN = `() => {
  const out = { url: location.href, title: document.title, ready: document.readyState,
    viewport: { w: innerWidth, h: innerHeight }, lang: document.documentElement.lang };
  const visRect = (el) => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return null;
    const s = getComputedStyle(el);
    return (s.display === "none" || s.visibility === "hidden" || parseFloat(s.opacity) === 0) ? null : r;
  };
  const desc = (el) => (el.tagName + (el.id ? "#" + el.id : "") + "." + String(el.className).split(" ").slice(0, 2).join(".")).slice(0, 70);

  // 标题层级
  const hs = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")];
  out.headings = hs.map((h) => ({ t: h.tagName, x: (h.textContent || "").trim().slice(0, 50) }));
  out.h1Count = hs.filter((h) => h.tagName === "H1").length;
  const skips = []; let prev = 0;
  for (const h of hs) { const lvl = Number(h.tagName[1]); if (prev && lvl > prev + 1) skips.push({ prev: prev, cur: lvl, x: (h.textContent || "").trim().slice(0, 40) }); prev = lvl; }
  out.headingSkips = skips;

  // landmark
  const cnt = (s) => document.querySelectorAll(s).length;
  out.landmarks = { main: cnt("main"), nav: cnt("nav"), header: cnt("header"), footer: cnt("footer"), aside: cnt("aside"), roleMain: cnt("[role=main]") };
  out.hasMainLandmark = cnt("main") + cnt("[role=main]") > 0;

  // skip link
  const skip = document.querySelector('a[href*="#main-content"]');
  out.skipLink = skip ? { href: skip.getAttribute("href"), targetExists: !!document.querySelector(skip.getAttribute("href")) } : { exists: false };

  // label 关联
  out.unlabeledControls = [...document.querySelectorAll("input:not([type=hidden]), select, textarea")]
    .filter((i) => { if (i.getAttribute("aria-label") || i.getAttribute("aria-labelledby") || i.closest("label")) return false; return !(i.id && document.querySelector('label[for="' + CSS.escape(i.id) + '"]')); })
    .map((i) => ({ tag: i.tagName, type: i.type || "", id: i.id, ph: (i.placeholder || "").slice(0, 30) }));

  // 点击目标尺寸 / 图标按钮命名
  const clickSel = 'a, button, input, select, textarea, [role="button"], [tabindex]:not([tabindex="-1"])';
  const small = [], unnamed = [];
  const clickables = [];
  for (const el of document.querySelectorAll(clickSel)) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (r.top < -900 || r.left < -900) continue; // 离屏定位节点（如 Pixi 注入的 1×1 accessibility 占位按钮，top/left=-1000）
    const s = getComputedStyle(el);
    if (s.visibility === "hidden" || s.display === "none") continue;
    // 累计祖先 transform 缩放（ScaleFitGameStage 等比缩放舞台）：<0.9 视为「缩放壳内」
    let sc = 1; let nd = el.parentElement;
    while (nd && nd.nodeType === 1) {
      const t = getComputedStyle(nd).transform;
      if (t && t !== "none") {
        if (t.startsWith("matrix(")) { const p = t.slice(7, -1).split(",").map(Number); sc *= Math.hypot(p[0], p[1]); }
        else if (t.startsWith("matrix3d(")) { const p = t.slice(9, -1).split(",").map(Number); sc *= Math.hypot(p[0], p[1], p[2]); }
      }
      nd = nd.parentElement;
    }
    sc = Math.round(sc * 1000) / 1000;
    const pseudoHit = (() => { const b = getComputedStyle(el, "::before"); return !!b && b.content !== "none" && /^(absolute|fixed)$/.test(b.position) && b.inset !== "auto"; })();
    // 伪元素扩区仅在未缩放的上下文里作数；缩放壳内无论伪元素都按视觉盒判定（关键路径必须出壳）
    if ((r.width < 24 || r.height < 24) && (!pseudoHit || sc < 0.9)) small.push({ tag: el.tagName, d: desc(el), w: Math.round(r.width), h: Math.round(r.height), name: (el.getAttribute("aria-label") || el.getAttribute("title") || (el.textContent || "").trim().slice(0, 20) || ""), scale: sc, html: el.outerHTML.slice(0, 220) });
    if (el.tagName === "BUTTON" && !(el.textContent || "").trim() && !el.getAttribute("aria-label") && !el.getAttribute("title") && !el.getAttribute("aria-labelledby")) unnamed.push(desc(el));
    clickables.push({ el, r: visRect(el) });
  }
  out.smallTargetsCount = small.length; out.smallTargets = small.slice(0, 40);
  out.unnamedIconButtonsCount = unnamed.length; out.unnamedIconButtons = unnamed.slice(0, 20);

  // 交互元素重叠
  const items = clickables.filter((x) => x.r && x.r.width >= 16 && x.r.height >= 16);
  const overlaps = [];
  const inFixedLayer = (el) => { let n = el; while (n && n.nodeType === 1) { if (getComputedStyle(n).position === "fixed") return true; n = n.parentElement; } return false; };
  outer: for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    if (items[i].el.contains(items[j].el) || items[j].el.contains(items[i].el)) continue; // 容器与子元素重叠不算
    if (inFixedLayer(items[i].el) !== inFixedLayer(items[j].el)) continue; // fixed dock/悬浮按钮压过滚动内容属预期
    const a = items[i].r, b = items[j].r;
    if (a.top >= b.bottom || b.top >= a.bottom || a.left >= b.right || b.left >= a.right) continue;
    const ix = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ix < 1 || iy < 1) continue;
    const ratio = (ix * iy) / Math.min(a.width * a.height, b.width * b.height);
    if (ratio > 0.4) { overlaps.push({ A: desc(items[i].el), B: desc(items[j].el), ratio: Math.round(ratio * 100) / 100 }); if (overlaps.length >= 30) break outer; }
  }
  out.overlaps = overlaps;

  // 横向溢出
  const hOver = [];
  const doc = document.documentElement;
  if (doc.scrollWidth > doc.clientWidth + 1) hOver.push({ el: "html", clientW: doc.clientWidth, scrollW: doc.scrollWidth });
  for (const el of document.querySelectorAll("main, section, [class*=overflow]")) el;
  out.horizontalOverflow = hOver;

  // 文本截断（overflow hidden + 内容超宽，或 line-clamp 超高）
  const trunc = [];
  for (const el of document.querySelectorAll("*")) {
    if (el.children.length) continue;
    if (el.classList.contains("sr-only")) continue; // 屏幕阅读器专用文本：1px 裁剪是设计行为
    const txt = (el.textContent || "").trim(); if (!txt) continue;
    const s = getComputedStyle(el);
    const clip = s.overflow === "hidden" || /(auto|hidden|clip)/.test(s.overflowX) || s.textOverflow === "ellipsis" || (s.webkitLineClamp && s.webkitLineClamp !== "none");
    if (!clip) continue;
    if (el.scrollWidth > el.clientWidth + 2 || (s.webkitLineClamp && el.scrollHeight > el.clientHeight + 2))
      trunc.push({ d: desc(el), sw: el.scrollWidth, cw: el.clientWidth, clamp: s.webkitLineClamp || "", x: txt.slice(0, 40) });
    if (trunc.length >= 40) break;
  }
  out.textTruncation = trunc;

  // 对比度（仅深色主题；canvas 解析 oklch/oklab/rgba）
  function parseColor(str) { try { const c = document.createElement("canvas"); c.width = c.height = 1; const x = c.getContext("2d", { willReadFrequently: true }); x.fillStyle = "#000"; x.fillStyle = str; x.fillRect(0, 0, 1, 1); const d = x.getImageData(0, 0, 1, 1).data; return { r: d[0], g: d[1], b: d[2], a: d[3] / 255 }; } catch { return null; } }
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
  const bgFor = (el) => {
    let acc = parseColor(getComputedStyle(document.body).backgroundColor) || { r: 12, g: 12, b: 16, a: 1 };
    let node = el;
    while (node && node.nodeType === 1) {
      const bg = parseColor(getComputedStyle(node).backgroundColor);
      if (bg && bg.a > 0) {
        const a = bg.a + acc.a * (1 - bg.a);
        acc = { r: (bg.r * bg.a + acc.r * acc.a * (1 - bg.a)) / a, g: (bg.g * bg.a + acc.g * acc.a * (1 - bg.a)) / a, b: (bg.b * bg.a + acc.b * acc.a * (1 - bg.a)) / a, a };
        if (acc.a >= 0.98) break;
      }
      node = node.parentElement;
    }
    return acc;
  };
  const bad = [];
  let scanned = 0;
  const seen = {};
  for (const el of document.querySelectorAll("*")) {
    if (scanned > 6000 || bad.length >= 60) break;
    const txt = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("").trim();
    if (txt.length < 2 || el.closest("svg") || el.closest("canvas") || el.closest("[aria-hidden=true]")) continue;
    const r = visRect(el); if (!r) continue;
    if (r.top < -r.height || r.left < -r.width) continue;
    const s = getComputedStyle(el);
    if (parseFloat(s.opacity) === 0) continue;
    const fg = parseColor(s.color); if (!fg || fg.a === 0) continue;
    const bg = bgFor(el);
    if (bg.a < 0.95) continue; // 玻璃/透明底无法可靠判定 → 跳过
    scanned++;
    let rr = ratio(fg, bg);
    const sizePx = parseFloat(s.fontSize);
    const large = sizePx >= 24 || (sizePx >= 18.66 && Number(s.fontWeight || 400) >= 700);
    const need = large ? 3 : 4.5;
    if (rr < need) {
      const key = Math.round(rr * 100) + "|" + Math.floor(sizePx);
      if (!seen[key]) { seen[key] = 1; bad.push({ x: txt.slice(0, 40), size: Math.round(sizePx), weight: s.fontWeight, ratio: Math.round(rr * 100) / 100, need, fg: [fg.r, fg.g, fg.b, Math.round(fg.a * 100)], bg: [Math.round(bg.r), Math.round(bg.g), Math.round(bg.b)], rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], inDialogEl: !!el.closest('[role=dialog]') }); }
    }
  }
  out.contrastViolations = bad;

  out.dialogs = [...document.querySelectorAll("[role=dialog]")].map((d) => { const r = visRect(d); return { labelledby: d.getAttribute("aria-labelledby") || "", modal: d.getAttribute("aria-modal") || "", visible: !!r, rect: r ? [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] : null }; });
  return out;
}`;

async function evalJson(cdp, expr) {
  const r = await cdp.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error("page eval failed: " + JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 300));
  return r.result.value;
}

async function auditRoute(route, vp, seedAuth) {
  const cdp = await newTab(route);
  const consoleMsgs = []; const errors = [];
  cdp.events = [];
  const url = SITE + route;
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Log.enable");
  await cdp.send("Network.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: vp.width, height: vp.height, deviceScaleFactor: vp.dpr, mobile: vp.mobile, screenWidth: vp.width, screenHeight: vp.height });
  if (vp.mobile) {
    await cdp.send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
    await cdp.send("Network.setUserAgentOverride", { userAgent: MOBILE_UA, platform: "iPhone", platformVersion: "17.0", deviceModel: "iPhone 15" });
  }
  if (seedAuth) await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: SEED_SCRIPT });
  cdp.events.length = 0;
  await cdp.send("Page.navigate", { url });
  await sleep(3200);
  let ready = false;
  for (let i = 0; i < 20 && !ready; i++) { try { ready = (await evalJson(cdp, "document.readyState")) === "complete"; } catch { ready = false; } if (!ready) await sleep(500); }
  await sleep(1600);
  const audit = await evalJson(cdp, "(" + AUDIT_FN + ")()");
  for (const ev of cdp.events) {
    const m = ev.method || "";
    const p = ev.params || {};
    if (m === "Runtime.exceptionThrown") {
      const d = p.exceptionDetails?.exception;
      errors.push({ kind: "exception", text: String(d?.description || d?.value || d?.text || p.exceptionDetails?.text || "").slice(0, 200), url: p.exceptionDetails?.url || "" });
    } else if (m === "Runtime.consoleAPICalled" && (p.type === "error" || p.type === "warning")) {
      const txt = (p.args || []).map((a) => (a && (a.value ?? a.description)) != null ? String(a.value ?? a.description) : a ? String(a.type) : "").join(" ").slice(0, 220);
      errors.push({ kind: "console." + p.type, text: txt });
    } else if (m === "Log.entryAdded" && p.entry) {
      const e = p.entry;
      if ((e.level === "error" || (e.level === "warning" && /favicon|logo|icon/i.test(e.text || "") === false)) && !/favicon/.test(e.text || "")) errors.push({ kind: "log." + e.level, text: String(e.text || "").slice(0, 220), url: e.url || "" });
    }
  }
  errors.push(...auditIssues(audit));
  function auditIssues(a) { const list = []; return list; }
  const scr = await cdp.send("Page.captureScreenshot", { format: "png", fromSurface: true });
  const base = route.replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "") || "index";
  fs.writeFileSync(path.join(SHOTS_DIR, base + "-" + vp.name + ".png"), Buffer.from(scr.data, "base64"));
  const contrastVerify = (audit.contrastViolations || []).length && scr.data ? verifyPixels(scr.data, vp.dpr, audit.contrastViolations, audit.dialogs) : [];
  // 第二遍：若存在可见弹层（games 开局的 briefing/规则弹层），Esc 关闭后复核被遮罩覆盖的底层 UI
  let postModal = null;
  if ((audit.dialogs || []).some((d) => d.visible)) {
    await cdp.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 });
    await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 });
    await sleep(1400);
    const stillOpen = await evalJson(cdp, "!!document.querySelector('[role=dialog]')");
    if (!stillOpen) {
      const audit2 = await evalJson(cdp, "(" + AUDIT_FN + ")()");
      const scr2 = await cdp.send("Page.captureScreenshot", { format: "png", fromSurface: true });
      fs.writeFileSync(path.join(SHOTS_DIR, base + "-" + vp.name + "-postmodal.png"), Buffer.from(scr2.data, "base64"));
      postModal = {
        audit: audit2,
        contrastVerify: (audit2.contrastViolations || []).length ? verifyPixels(scr2.data, vp.dpr, audit2.contrastViolations, audit2.dialogs) : [],
        screenshot: "artifacts/shots/" + base + "-" + vp.name + "-postmodal.png",
      };
    }
  }
  const payload = { route, viewport: vp.name, url: audit.url, audit, consoleErrors: errors.length, consoleErrorSamples: errors.slice(0, 12), contrastVerify, postModal, screenshot: "artifacts/shots/" + base + "-" + vp.name + ".png" };
  fs.writeFileSync(path.join(OUT_DIR, "scan-" + base + "-" + vp.name + ".json"), JSON.stringify(payload, null, 2));
  await cdp.close();
  return payload;
}

const results = [];
for (const route of ROUTES) {
  for (const vp of VIEWPORTS) {
    const seedAuth = route.startsWith("/lobby");
    const t0 = Date.now();
    try {
      const r = await auditRoute(route, vp, seedAuth);
      results.push(r);
      console.log(JSON.stringify({ ok: 1, route, vp: vp.name, ms: Date.now() - t0, title: r.audit.title, cViol: (r.audit.contrastViolations || []).length, small: r.audit.smallTargetsCount }));
    } catch (e) {
      results.push({ route, viewport: vp.name, error: String(e && e.message || e) });
      console.log(JSON.stringify({ ok: 0, route, vp: vp.name, error: String(e && e.message || e).slice(0, 200) }));
    }
  }
}
const summary = { site: SITE, at: new Date().toISOString(), results };
fs.writeFileSync(path.join(OUT_DIR, "summary.json"), JSON.stringify(summary, null, 2));
console.log("SUMMARY_WRITTEN " + path.join(OUT_DIR, "summary.json"));
console.log("TITLES: " + results.filter((r) => r.audit).map((r) => r.route + "=[" + r.audit.title + "]").join(" | "));
