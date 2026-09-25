#!/usr/bin/env node
/** interact.mjs — CDP 键鼠端到端验证器：Tab 环 / 弹层焦点陷阱 / Esc 语义（零依赖） */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CDP_HTTP = process.env.CDP_HTTP || "http://127.0.0.1:9333";
const SITE = (process.env.SITE_URL || "http://127.0.0.1:4105").replace(/\/$/, "");
const OUT_DIR = process.env.OUT_DIR || path.resolve(HERE, "..", "..", ".ui-polish", "artifacts");
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


class Cdp {
  constructor(u) { this.ws = new WebSocket(u); this.id = 0; this.p = new Map(); }
  async open() {
    await new Promise((res, rej) => { this.ws.onopen = res; this.ws.onerror = () => rej(new Error("ws open failed")); });
    this.ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id) { const p = this.p.get(m.id); if (p) { this.p.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } }
    };
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((res, rej) => { this.p.set(id, { res, rej }); this.ws.send(JSON.stringify({ id, method, params })); });
  }
  async close() { try { if (this.targetId) await this.send("Target.closeTarget", { targetId: this.targetId }); } catch {} try { this.ws.close(); } catch {} }
}

async function newTab() {
  await ensureBrowser();
  const t = await (await fetch(CDP_HTTP + "/json/new?about:blank", { method: "PUT" })).json();
  const c = new Cdp(t.webSocketDebuggerUrl);
  c.targetId = t.id;
  await c.open();
  return c;
}

const MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1";
const SEED = "try{localStorage.setItem('game-store', JSON.stringify({state:{token:'audit-token',userId:7,username:'审计访客',selectedClass:'Role2_Cursemancer',currentRoomId:''},version:0}));localStorage.setItem('asternova-lobby-avatar-id','avatar-3')}catch(e){}";

async function evalJson(c, expr) {
  const r = await c.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(String(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 200));
  return r.result.value;
}

async function pressKey(c, key, code, vk) {
  await c.send("Input.dispatchKeyEvent", { type: "keyDown", key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
  await c.send("Input.dispatchKeyEvent", { type: "keyUp", key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
}

const focusInfo = "(function(){var a=document.activeElement; if(!a||a===document.body) return {tag:'BODY'}; var r=a.getBoundingClientRect(); return {tag:a.tagName,cls:String(a.className).slice(0,44),txt:(a.textContent||'').trim().slice(0,14),aria:a.getAttribute('aria-label')||'',w:Math.round(r.width),h:Math.round(r.height),top:Math.round(r.top),left:Math.round(r.left),inDialog:!!a.closest('[role=dialog]')};})()";

const results = [];
function report(name, pass, detail) {
  results.push({ name, pass: !!pass, detail: String(detail).slice(0, 260) });
  console.log(JSON.stringify({ name, pass: !!pass, detail: String(detail).slice(0, 200) }));
}

async function runScenario(name, route, opts = {}) {
  const { seed = false, mobile = false, settle = 5200 } = opts;
  const c = await newTab();
  await c.send("Page.enable");
  await c.send("Runtime.enable");
  await c.send("Emulation.setDeviceMetricsOverride", { width: mobile ? 375 : 1440, height: mobile ? 812 : 900, deviceScaleFactor: mobile ? 2 : 1, mobile, screenWidth: mobile ? 375 : 1440, screenHeight: mobile ? 812 : 900 });
  if (mobile) { await c.send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 }); await c.send("Network.setUserAgentOverride", { userAgent: MOBILE_UA, platform: "iPhone", platformVersion: "17.0", deviceModel: "iPhone 15" }); }
  if (seed) await c.send("Page.addScriptToEvaluateOnNewDocument", { source: SEED });
  await c.send("Page.navigate", { url: SITE + route });
  await sleep(settle);
  return c;
}

async function tabRingInDialog(c, scenarioName, tabs = 12) {
  const stops = []; let outside = 0; let cycleLen = null;
  const sameStop = (a, b) => a.tag === b.tag && a.txt === b.txt && a.aria === b.aria && Math.abs(a.top - b.top) < 3 && Math.abs((a.left ?? 0) - (b.left ?? 0)) < 3;
  for (let i = 0; i < tabs; i++) {
    await pressKey(c, "Tab", "Tab", 9);
    const f = await evalJson(c, focusInfo);
    stops.push(f);
    if (!f.inDialog) outside++;
    if (cycleLen === null && i > 0 && sameStop(stops[0], f)) { cycleLen = stops.length - 1; break; } // 首循环回到起点即闭环
  }
  report(scenarioName + "·Tab焦点陷阱", outside === 0 && stops.length >= 2, "落点数=" + stops.length + (cycleLen !== null ? "（首循环长 " + cycleLen + "）" : "") + "，越界=" + outside + "，首落点=" + JSON.stringify(stops[0]));
  return stops;
}

async function pressEscAndCheck(c, name, expectClosed) {
  await pressKey(c, "Escape", "Escape", 27);
  // AnimatePresence exit 动画保留 DOM 200~400ms：轮询至多 2.4s；未生效再补一次 Esc（双击幂等）
  let open = true;
  for (let round = 0; round < 2; round++) {
    for (let i = 0; i < 8; i++) {
      await sleep(300);
      open = await evalJson(c, "!!document.querySelector('[role=dialog]')");
      if (open === !expectClosed) break;
    }
    if (open === !expectClosed) break;
    await pressKey(c, "Escape", "Escape", 27);
  }
  const pass = open === !expectClosed;
  report(name, pass, "弹层仍打开=" + open + "（期望关闭=" + expectClosed + "）");
  return pass;
}

try {
  // A. login 忘记密码 弹层：打开聚焦、Tab 陷阱、Esc 关闭、焦点归还
  {
    const c = await runScenario("login-reset", "/login");
    // 真实用户路径：先聚焦触发钮再激活（程序化 click 不移动焦点，须显式 focus 才能验证归还语义）
    await evalJson(c, "[...document.querySelectorAll('button')].find(function(b){ return (b.textContent||'').indexOf('忘记密码')>=0; })?.focus()");
    await evalJson(c, "[...document.querySelectorAll('button')].find(function(b){ return (b.textContent||'').indexOf('忘记密码')>=0; })?.click()");
    await sleep(500);
    let f = await evalJson(c, focusInfo);
    report("login-reset·打开后焦点进弹层", !!f.inDialog, JSON.stringify(f));
    await tabRingInDialog(c, "login-reset", 12);
    const closed = await pressEscAndCheck(c, "login-reset·Esc关闭", true);
    await sleep(900);
    f = await evalJson(c, focusInfo);
    report("login-reset·Esc后焦点归还触发钮", closed && (f.txt.indexOf("忘记密码") >= 0), JSON.stringify(f));
    await c.close();
  }
  // B. lobby 头像选择弹层（上轮新接 hook，隔轮评审对象）
  {
    const c = await runScenario("lobby-avatar", "/lobby", { seed: true });
    await evalJson(c, "document.querySelector('button[aria-label=\"打开头像选择\"]')?.click()");
    await sleep(500);
    let f = await evalJson(c, focusInfo);
    report("lobby-avatar·打开后焦点进弹层", !!f.inDialog, JSON.stringify(f));
    await tabRingInDialog(c, "lobby-avatar", 12);
    await pressEscAndCheck(c, "lobby-avatar·Esc关闭", true);
    await c.close();
  }
  // C-F 游戏弹层（移动端，入场 briefing 自动打开）
  {
    const c = await runScenario("merge-rules", "/merge", { mobile: true });
    report("merge-rules·入场自动打开", await evalJson(c, "!!document.querySelector('[role=dialog]')"), "");
    await tabRingInDialog(c, "merge-rules", 12);
    await pressEscAndCheck(c, "merge-rules·Esc关闭", true);
    await c.close();
  }
  {
    const c = await runScenario("nebula-briefing", "/nebula-survivor", { mobile: true });
    report("nebula-briefing·入场自动打开", await evalJson(c, "!!document.querySelector('[role=dialog]')"), "");
    await tabRingInDialog(c, "nebula-briefing", 12);
    await pressEscAndCheck(c, "nebula-briefing·Esc保持打开（briefing）", false);
    await c.close();
  }
  {
    const c = await runScenario("star-rules", "/lets-running", { mobile: true });
    report("star-rules·入场自动打开", await evalJson(c, "!!document.querySelector('[role=dialog]')"), "");
    await tabRingInDialog(c, "star-rules", 12);
    await pressEscAndCheck(c, "star-rules·Esc关闭", true);
    await c.close();
  }
  // F. 静态页 Tab 环：skip link 首落点 + 页内无名可见按钮检查
  {
    const c = await runScenario("tab-ring-login", "/login");
    await evalJson(c, "(document.activeElement && document.activeElement.blur && document.activeElement.blur(), true)");
    for (let i = 0; i < 30; i++) {
      await pressKey(c, "Tab", "Tab", 9);
      if (i === 0) {
        const f = await evalJson(c, focusInfo);
        report("tab-ring-login·首落点=skip link", f.txt.indexOf("跳到主内容") >= 0, JSON.stringify(f));
      }
    }
    const summary = await evalJson(c, "(function(){var els=[...document.querySelectorAll('a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex=\"-1\"])')]; var bad=els.filter(function(e){var r=e.getBoundingClientRect(); var s=getComputedStyle(e); return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&(e.tagName==='BUTTON'&&!(e.textContent||'').trim()&&!e.getAttribute('aria-label')&&!e.getAttribute('title')&&!e.getAttribute('aria-labelledby'));}); return {focusables:els.length, unnamedVisibleButtons:bad.length};})()");
    report("tab-ring-login·页内无名可见按钮=0", summary.unnamedVisibleButtons === 0, JSON.stringify(summary));
    await c.close();
  }
  // G. 全路由 Tab 环轮转：跳过链接首落点 + 环内落点全部可见 + 无无名按钮
  {
    const pages = [
      { name: "home", route: "/" },
      { name: "login", route: "/login" },
      { name: "lobby", route: "/lobby", seed: true },
      { name: "xiaoxiaole", route: "/xiaoxiaole" },
      { name: "notfound", route: "/this-route-does-not-exist" },
    ];
    for (const pg of pages) {
      const c = await runScenario("tab-ring-" + pg.name, pg.route, { seed: !!pg.seed });
      await evalJson(c, "(document.activeElement && document.activeElement.blur && document.activeElement.blur(), true)");
      const stops = [];
      let firstOk = false, allVisible = true;
      const invis = [];
      const maxTabs = 40;
      for (let i = 0; i < maxTabs; i++) {
        await pressKey(c, "Tab", "Tab", 9);
        await sleep(280); // skip link 的 translate 入场 200ms：等落点就位再测可见性
        const f = await evalJson(c, focusInfo);
        if (f.tag === "BODY") break; // 环耗尽落回 body：终点而非违规
        stops.push(f);
        const visible = (f.w ?? 0) > 0 && (f.h ?? 0) > 0 && (f.top ?? -999) > -60;
        if (!visible) { allVisible = false; if (invis.length < 4) invis.push({ tag: f.tag, txt: (f.txt || "").slice(0, 12), top: f.top, w: f.w }); }
        if (i === 0) firstOk = (f.txt || "").indexOf("跳到主内容") >= 0;
        // 回到首落点 = 完整闭环（容差：同 tag/txt/aria/坐标）
        if (i > 0 && stops[0].tag === f.tag && stops[0].txt === f.txt && stops[0].aria === f.aria && Math.abs((stops[0].top ?? 0) - (f.top ?? 0)) < 3 && Math.abs((stops[0].left ?? 0) - (f.left ?? 0)) < 3) break;
      }
      const unnamed = await evalJson(c, "(function(){var bad=[].slice.call(document.querySelectorAll('button:not([disabled])')).filter(function(e){var r=e.getBoundingClientRect();var s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&!(e.textContent||'').trim()&&!e.getAttribute('aria-label')&&!e.getAttribute('title')&&!e.getAttribute('aria-labelledby');});return bad.length;})()");
      report("tab-ring-" + pg.name + "·首选=skip链接", firstOk, JSON.stringify(stops[0]));
      report("tab-ring-" + pg.name + "·环内落点全部可见", allVisible && stops.length >= 2, "stops=" + stops.length + (invis.length ? " 不可见=" + JSON.stringify(invis) : ""));
      report("tab-ring-" + pg.name + "·页内无名可见按钮=0", unnamed === 0, "unnamed=" + unnamed);
      await c.close();
    }
  }
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(path.join(OUT_DIR, "interact-summary.json"), JSON.stringify({ at: new Date().toISOString(), results }, null, 2));
  const failed = results.filter((r) => !r.pass).length;
  console.log("INTERACT_SUMMARY total=" + results.length + " failed=" + failed);
  process.exitCode = failed > 0 ? 1 : 0;
} catch (e) {
  console.log("INTERACT_ERROR: " + String((e && e.message) || e).slice(0, 400));
  process.exitCode = 1;
}
