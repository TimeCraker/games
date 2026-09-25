#!/usr/bin/env node
/** edge.mjs — 边界扫描器：弱网/离线/超长 emoji 数据 + 弹层容器配方测量（零依赖 CDP） */
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

class Cdp { constructor(u){this.ws=new WebSocket(u);this.id=0;this.p=new Map();}
  async open(){await new Promise((res,rej)=>{this.ws.onopen=res;this.ws.onerror=()=>rej(new Error("ws"));});
    this.ws.onmessage=(ev)=>{const m=JSON.parse(ev.data);if(m.id){const p=this.p.get(m.id);if(p){this.p.delete(m.id);m.error?p.rej(new Error(m.error.message)):p.res(m.result);}}};}
  send(method,params={}){const id=++this.id;return new Promise((res,rej)=>{this.p.set(id,{res,rej});this.ws.send(JSON.stringify({id,method,params}));});}
  async eval(expr){const r=await this.send("Runtime.evaluate",{expression:expr,returnByValue:true,awaitPromise:true}); if(r.exceptionDetails) throw new Error(String(r.exceptionDetails.exception?.description||r.exceptionDetails.text).slice(0,160)); return r.result.value;}
  close(){try{this.ws.close()}catch{}}}
const results=[]; const report=(n,p,d)=>{results.push({name:n,pass:!!p,detail:String(d).slice(0,240)}); console.log(JSON.stringify({name:n,pass:!!p,detail:String(d).slice(0,180)}));};
async function newTab(){
  await ensureBrowser();const t=await (await fetch(CDP_HTTP+"/json/new?about:blank",{method:"PUT"})).json(); const c=new Cdp(t.webSocketDebuggerUrl); c.targetId=t.id; await c.open(); await c.send("Page.enable"); await c.send("Runtime.enable"); await c.send("Log.enable"); return c;}
const SEED = "try{localStorage.setItem('game-store', JSON.stringify({state:{token:'audit-token',userId:7,username:'航行员',selectedClass:'Role2_Cursemancer',currentRoomId:''},version:0}));}catch(e){}";
const SEED_LONG = "try{localStorage.setItem('game-store', JSON.stringify({state:{token:'audit-token',userId:7,username:'🚀极地深空航线观测员Polaris-Crew-0987超长昵称测试样例abcdefghijklmnopqrstuvwxyz 📡',selectedClass:'Role2_Cursemancer',currentRoomId:''},version:0}));}catch(e){}";
const EXPR1 = "(function(){var d=document.documentElement; var h1s=document.querySelectorAll('h1'); var hov=d.scrollWidth-(d.clientWidth+1); return {h1:h1s.length, hOver:Math.max(0,hov), interactives:document.querySelectorAll('a,button,[role=button]').length, title:document.title};})()";
const EXPR2 = "(function(){var span=document.querySelector('main span.truncate, header span.truncate, [class*=truncate]'); if(!span) return {noEllipsis:false, found:false}; return {found:true, sw:span.scrollWidth, cw:span.clientWidth, ellipsis:getComputedStyle(span).textOverflow, overflow:span.scrollWidth>span.clientWidth+2, docOver:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};})()";
const EXPR3 = "(function(){var out=[]; document.querySelectorAll('[role=dialog]').forEach(function(d){var panel=null; [].slice.call(d.children).forEach(function(ch){var cs=getComputedStyle(ch); if(!panel && (cs.maxWidth!=='none' || cs.borderRadius!=='0px')) panel=ch;}); panel=panel||d; var s=getComputedStyle(panel); var w=panel.getBoundingClientRect(); out.push({id:(d.getAttribute('aria-labelledby')||String(d.className).slice(0,20)), w:Math.round(w.width), radius:s.borderRadius.slice(0,42), bg:s.backgroundColor.slice(0,46), border:s.borderColor.slice(0,48), blur:s.backdropFilter.slice(0,26), maxw:s.maxWidth, pad:s.padding.slice(0,22)});}); return out;})()";

const EXPR4 = "(function(){var rows=[]; document.querySelectorAll('.star-chart-grid,.star-chart-grid-fine').forEach(function(g){var s=getComputedStyle(g); rows.push({cls:g.className, opacity:s.opacity, bg:s.backgroundImage.slice(0,150), size:s.backgroundSize});}); return rows;})()";
const EXPR5 = "(function(){var d=[].slice.call(document.querySelectorAll('[role=dialog]')).find(function(x){return x.getAttribute('aria-labelledby')==='reset-password-title';}); if(!d) return {absent:true}; var panel=null; [].slice.call(d.children).forEach(function(ch){var cs=getComputedStyle(ch); if(!panel && (cs.maxWidth!=='none'||cs.borderRadius!=='0px')) panel=ch;}); panel=panel||d; var s=getComputedStyle(panel); var w=panel.getBoundingClientRect(); return {w:Math.round(w.width), radius:s.borderRadius.slice(0,42), bg:s.backgroundColor.slice(0,46), border:s.borderColor.slice(0,48), blur:s.backdropFilter.slice(0,26), maxw:s.maxWidth, pad:s.padding.slice(0,22)};})()";
// 1) 弱网（慢速 3G 近似）加载关键路由
for (const [name, route, seed] of [["home","/",null],["login","/login",null],["lobby","/lobby",SEED],["merge","/merge",null],["xiaoxiaole","/xiaoxiaole",null]]) {
  const c = await newTab();
  if (seed) await c.send("Page.addScriptToEvaluateOnNewDocument",{source:seed});
  await c.send("Network.emulateNetworkConditions",{offline:false,latency:700,downloadThroughput:18750,uploadThroughput:7500,connectionType:"cellular3g"});
  const errs=[];
  const evH = (ev)=>{const m=ev.method,p=ev.params||{}; if(m==="Runtime.exceptionThrown") errs.push("ex"); else if(m==="Log.entryAdded"&&p.entry&&p.entry.level==="error"&&!/favicon/.test(p.entry.text||"")) errs.push("log");};
  const cdpEvt = c;
  await c.send("Page.navigate",{url:SITE+route});
  await sleep(9500);
  const r = await c.eval(EXPR1);
  report("weaknet·"+name+"·渲染完整(h1=1且无横向溢出)", r.h1===1 && r.hOver===0, JSON.stringify(r));
  await c.send("Network.emulateNetworkConditions",{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1,connectionType:"none"});
  await c.close();
}


// 1b) 3G/4G 档（轻量：仅首页与登录）
for (const [tierName, latency, download] of [["3g",270,97500],["4g",60,375000]]) {
  for (const [name, route, seed] of [["home","/",null],["login","/login",null]]) {
    const c = await newTab();
    if (seed) await c.send("Page.addScriptToEvaluateOnNewDocument",{source:seed});
    await c.send("Network.emulateNetworkConditions",{offline:false,latency,downloadThroughput:download,uploadThroughput:download,connectionType:"cellular4g"});
    await c.send("Page.navigate",{url:SITE+route});
    await sleep(7000);
    const r = await c.eval(EXPR1);
    report("weaknet."+tierName+"."+name+"·渲染完整", r.h1===1 && r.hOver===0, JSON.stringify(r));
    await c.send("Network.emulateNetworkConditions",{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1,connectionType:"none"});
    await c.close();
  }
}
// 2) 离线行为：浏览器默认错误页（本站无离线壳/SW 属设计内保留，仅取证）
let off = await newTab();
await off.send("Network.emulateNetworkConditions",{offline:true,latency:0,downloadThroughput:-1,uploadThroughput:-1});
await off.send("Page.navigate",{url:SITE+"/"});
await sleep(4000);
const offTitle = await off.eval("document.title");
report("offline·首页", true, "离线呈现=" + (offTitle && offTitle.indexOf("无法访问")>=0 ? "浏览器错误页(预期)" : String(offTitle).slice(0,40)));
await off.close();

// 3) 超长+emoji 昵称（大厅头部截断行为）
const c3 = await newTab();
await c3.send("Page.addScriptToEvaluateOnNewDocument",{source:SEED_LONG});
await c3.send("Page.navigate",{url:SITE+"/lobby"});
await sleep(6000);
const r3 = await c3.eval(EXPR2);
report("longname·头部截断无页面级溢出", !!r3.found && r3.ellipsis==="ellipsis" && !r3.docOver, JSON.stringify(r3));
await c3.close();

// 4) 弹层容器配方测量（桌面 + 移动）：rules §4 基准 = 420px 宽 / glass 底 / 桌面 2rem 全圆角 移动 1.75rem 顶部圆角
for (const vpName of ["desktop","mobile"]) {
  for (const [name, route, seed] of [["merge","/merge",null],["nebula","/nebula-survivor",null],["star","/lets-running",null],["login","/login",null]]) {
    const c = await newTab();
    if (vpName === "mobile") await c.send("Emulation.setDeviceMetricsOverride",{width:375,height:812,deviceScaleFactor:2,mobile:true,screenWidth:375,screenHeight:812});
    if (seed) await c.send("Page.addScriptToEvaluateOnNewDocument",{source:seed});
    await c.send("Page.navigate",{url:SITE+route});
    await sleep(5600);
    const dlg = await c.eval(EXPR3);
    report("recipe·"+name+"·"+(vpName==="mobile"?"移动":"桌面")+"·弹层数据", true, JSON.stringify(dlg));
    await c.close();
  }
}


// 5) login 重置弹层打开态配方（R8 补测）+ 星象台 fine-grid 节奏数据
{
  const c = await newTab();
  await c.send("Page.navigate",{url:SITE+"/login"});
  await sleep(5200);
  await c.eval("[].slice.call(document.querySelectorAll('button')).find(function(b){return (b.textContent||'').indexOf('忘记密码')>=0;})?.click()");
  await sleep(700);
  const reset = await c.eval(EXPR5);
  report("recipe·login-reset·打开态·弹层面板（桌面）", true, JSON.stringify(reset));
  await c.close();
  const c2 = await newTab();
  await c2.send("Page.navigate",{url:SITE+"/"});
  await sleep(5200);
  const gridsHome = await c2.eval(EXPR4);
  await c2.send("Page.navigate",{url:SITE+"/login"});
  await sleep(5200);
  const gridsLogin = await c2.eval(EXPR4);
  await c2.close();
  report("finedata·首页·粗网格（主网格）", gridsHome.length >= 1, JSON.stringify(gridsHome));
  report("finedata·登录·细网格（fine-grid，24px 0.025 白线）", gridsLogin.length >= 2, JSON.stringify(gridsLogin));
}
fs.mkdirSync(OUT_DIR,{recursive:true});
fs.writeFileSync(path.join(OUT_DIR,"edge-summary.json"),JSON.stringify({at:new Date().toISOString(),results},null,2));
console.log("EDGE_SUMMARY total="+results.length+" failed="+results.filter(r=>!r.pass).length);
process.exitCode = results.some(r=>!r.pass) ? 1 : 0;
