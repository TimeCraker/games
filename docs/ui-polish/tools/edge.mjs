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
class Cdp { constructor(u){this.ws=new WebSocket(u);this.id=0;this.p=new Map();}
  async open(){await new Promise((res,rej)=>{this.ws.onopen=res;this.ws.onerror=()=>rej(new Error("ws"));});
    this.ws.onmessage=(ev)=>{const m=JSON.parse(ev.data);if(m.id){const p=this.p.get(m.id);if(p){this.p.delete(m.id);m.error?p.rej(new Error(m.error.message)):p.res(m.result);}}};}
  send(method,params={}){const id=++this.id;return new Promise((res,rej)=>{this.p.set(id,{res,rej});this.ws.send(JSON.stringify({id,method,params}));});}
  async eval(expr){const r=await this.send("Runtime.evaluate",{expression:expr,returnByValue:true,awaitPromise:true}); if(r.exceptionDetails) throw new Error(String(r.exceptionDetails.exception?.description||r.exceptionDetails.text).slice(0,160)); return r.result.value;}
  close(){try{this.ws.close()}catch{}}}
const results=[]; const report=(n,p,d)=>{results.push({name:n,pass:!!p,detail:String(d).slice(0,240)}); console.log(JSON.stringify({name:n,pass:!!p,detail:String(d).slice(0,180)}));};
async function newTab(){const t=await (await fetch(CDP_HTTP+"/json/new?about:blank",{method:"PUT"})).json(); const c=new Cdp(t.webSocketDebuggerUrl); c.targetId=t.id; await c.open(); await c.send("Page.enable"); await c.send("Runtime.enable"); await c.send("Log.enable"); return c;}
const SEED = "try{localStorage.setItem('game-store', JSON.stringify({state:{token:'audit-token',userId:7,username:'航行员',selectedClass:'Role2_Cursemancer',currentRoomId:''},version:0}));}catch(e){}";
const SEED_LONG = "try{localStorage.setItem('game-store', JSON.stringify({state:{token:'audit-token',userId:7,username:'🚀极地深空航线观测员Polaris-Crew-0987超长昵称测试样例abcdefghijklmnopqrstuvwxyz 📡',selectedClass:'Role2_Cursemancer',currentRoomId:''},version:0}));}catch(e){}";
const EXPR1 = "(function(){var d=document.documentElement; var h1s=document.querySelectorAll('h1'); var hov=d.scrollWidth-(d.clientWidth+1); return {h1:h1s.length, hOver:Math.max(0,hov), interactives:document.querySelectorAll('a,button,[role=button]').length, title:document.title};})()";
const EXPR2 = "(function(){var span=document.querySelector('main span.truncate, header span.truncate, [class*=truncate]'); if(!span) return {noEllipsis:false, found:false}; return {found:true, sw:span.scrollWidth, cw:span.clientWidth, ellipsis:getComputedStyle(span).textOverflow, overflow:span.scrollWidth>span.clientWidth+2, docOver:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};})()";
const EXPR3 = "(function(){var out=[]; document.querySelectorAll('[role=dialog]').forEach(function(d){var panel=null; [].slice.call(d.children).forEach(function(ch){var cs=getComputedStyle(ch); if(!panel && (cs.maxWidth!=='none' || cs.borderRadius!=='0px')) panel=ch;}); panel=panel||d; var s=getComputedStyle(panel); var w=panel.getBoundingClientRect(); out.push({id:(d.getAttribute('aria-labelledby')||String(d.className).slice(0,20)), w:Math.round(w.width), radius:s.borderRadius.slice(0,42), bg:s.backgroundColor.slice(0,46), border:s.borderColor.slice(0,48), blur:s.backdropFilter.slice(0,26), maxw:s.maxWidth, pad:s.padding.slice(0,22)});}); return out;})()";

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

fs.mkdirSync(OUT_DIR,{recursive:true});
fs.writeFileSync(path.join(OUT_DIR,"edge-summary.json"),JSON.stringify({at:new Date().toISOString(),results},null,2));
console.log("EDGE_SUMMARY total="+results.length+" failed="+results.filter(r=>!r.pass).length);
process.exitCode = results.some(r=>!r.pass) ? 1 : 0;
