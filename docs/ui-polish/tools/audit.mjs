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

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CDP_HTTP = process.env.CDP_HTTP || "http://127.0.0.1:9333";
const SITE = (process.env.SITE_URL || "http://127.0.0.1:3000").replace(/\/$/, "");
const OUT_DIR = process.env.OUT_DIR || path.resolve(HERE, "..", "artifacts");
const SHOTS_DIR = path.join(OUT_DIR, "shots");
fs.mkdirSync(SHOTS_DIR, { recursive: true });

const argv = process.argv.slice(2);
const argVal = (name, def) => { const i = argv.indexOf("--" + name); return i >= 0 && argv[i + 1] ? argv[i + 1] : def; };
const ROUTES = argVal("routes", "/,/login,/lobby,/arena,/shoot-them-all,/lets-running,/merge,/nebula-survivor,/xiaoxiaole,/this-route-does-not-exist").split(",").filter(Boolean);
const VIEWPORTS = argVal("viewports", "desktop,mobile").split(",").filter(Boolean).map((n) => ({
  name: n,
  ...(n === "mobile"
    ? { width: 375, height: 812, mobile: true, dpr: 2 }
    : { width: 1440, height: 900, mobile: false, dpr: 1 }),
}));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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
  close() { try { this.ws.close(); } catch {} }
}

async function newTab(route) {
  const t = await (await fetch(CDP_HTTP + "/json/new?about:blank", { method: "PUT" })).json();
  const cdp = new Cdp(t.webSocketDebuggerUrl);
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
    const pseudoHit = (() => { const b = getComputedStyle(el, "::before"); return !!b && b.content !== "none" && /^(absolute|fixed)$/.test(b.position) && b.inset !== "auto"; })();
    if ((r.width < 24 || r.height < 24) && !pseudoHit) small.push({ tag: el.tagName, d: desc(el), w: Math.round(r.width), h: Math.round(r.height), name: (el.getAttribute("aria-label") || el.getAttribute("title") || (el.textContent || "").trim().slice(0, 20) || ""), html: el.outerHTML.slice(0, 220) });
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
      if (!seen[key]) { seen[key] = 1; bad.push({ x: txt.slice(0, 40), size: Math.round(sizePx), weight: s.fontWeight, ratio: Math.round(rr * 100) / 100, need, fg: [fg.r, fg.g, fg.b, Math.round(fg.a * 100)], bg: [Math.round(bg.r), Math.round(bg.g), Math.round(bg.b)] }); }
    }
  }
  out.contrastViolations = bad;

  out.dialogs = [...document.querySelectorAll("[role=dialog]")].map((d) => ({ labelledby: d.getAttribute("aria-labelledby") || "", modal: d.getAttribute("aria-modal") || "", visible: !!visRect(d) }));
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
  const payload = { route, viewport: vp.name, url: audit.url, audit, consoleErrors: errors.length, consoleErrorSamples: errors.slice(0, 12), screenshot: "artifacts/shots/" + base + "-" + vp.name + ".png" };
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
