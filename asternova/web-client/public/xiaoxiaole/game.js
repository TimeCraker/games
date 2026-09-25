/* ============================================================
   桓睿消消乐 v2.1 - 完整游戏版
   关卡系统 · 界面状态机 · 背景系统 · SVG图标 · 增强动效音效
   ============================================================ */
(() => {
'use strict';

// ---------- 配置 ----------
const ROWS = 8, COLS = 8, TYPES = 4;
const SWAP_DUR = 260, REMOVE_DUR = 420, FALL_DUR = 320, GAP = 8, PAD = 10, SWIPE_THRESH = 0.22;
const FACE_IMG = ['./assets/faces/face0.jpg','./assets/faces/face1.jpg','./assets/faces/face2.jpg','./assets/faces/face3.jpg'];
const ACCENT = ['#ff6b6b','#4ecdc4','#ffd93d','#a78bfa'];
const SPECIAL = { NONE:0, ROCKET_H:1, ROCKET_V:2, BOMB:3, RAINBOW:4 };
// 资源版本号（部署时同步更新，强制刷新缓存）
const CACHE_VER = '2.28';
// 移动端关闭 3D（性能）：z 偏移为 0，纯 2D 合成
const IS_MOBILE = matchMedia('(max-width:960px)').matches;
const Z_TILE = IS_MOBILE ? 0 : 8;
const Z_DRAG = IS_MOBILE ? 0 : 18;

// ---------- SVG 图标系统 ----------
const SVG = {
  spark:'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 1.5l2.6 7.9L22.5 12l-7.9 2.6L12 22.5l-2.6-7.9L1.5 12l7.9-2.6z"/></svg>',
  bomb:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="15" r="6.5"/><path d="M16 9l2-2"/><path d="M18 7l1.5-1.5"/><circle cx="20" cy="5" r="1.2" fill="currentColor" stroke="none"/><path d="M14.5 9.5l1.5-1.5"/></svg>',
  rainbow:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 19a9 9 0 0118 0"/><path d="M6.5 19a5.5 5.5 0 0111 0"/><path d="M10 19a2 2 0 014 0"/></svg>',
  star:'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.9 6.9L22 10l-5.5 4.8L18 22l-6-3.6L6 22l1.5-7.2L2 10l7.1-1.1z"/></svg>',
  starO:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 2l2.9 6.9L22 10l-5.5 4.8L18 22l-6-3.6L6 22l1.5-7.2L2 10l7.1-1.1z"/></svg>',
  fire:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M12 2c2 3-1 5-1 8 0 1.2 1 2 2 2s2-0.8 2-2c1.5 1.5 2.5 3.5 2.5 5.5A6.5 6.5 0 015.5 15.5C5.5 12 8 10 9 9c0 1.2 1 2 2 2 0-3-1-5 1-9z"/></svg>',
  target:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></svg>',
  trophy:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4h10v6a5 5 0 01-10 0z"/><path d="M7 6H4v1a4 4 0 003 4M17 6h3v1a4 4 0 01-3 4"/><path d="M12 15v3M8.5 21h7l-1-3h-5z"/></svg>',
  chart:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="11" width="3" height="6" rx="1"/><rect x="12" y="7" width="3" height="10" rx="1"/><rect x="17" y="13" width="3" height="4" rx="1"/></svg>',
  pause:'<svg viewBox="0 0 24 24" fill="currentColor"><rect x="7" y="5" width="3.5" height="14" rx="1.2"/><rect x="13.5" y="5" width="3.5" height="14" rx="1.2"/></svg>',
  restart:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 11-2.6-6.4M21 4v4h-4"/></svg>',
  back:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>',
  lock:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>',
  check:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5 9-10"/></svg>',
  party:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21l7-7M10 14L4 5l9 5z"/><path d="M14 3l.7 2M18 7l2 .7M15.5 8.5L17 7"/></svg>',
  sad:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 15a4 4 0 018 0M9 9h.01M15 9h.01"/></svg>',
  moon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14a8 8 0 11-9-11 6.5 6.5 0 009 11z"/></svg>',
  sun:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.5 4.5l1.8 1.8M17.7 17.7l1.8 1.8M19.5 4.5l-1.8 1.8M6.3 17.7l-1.8 1.8"/></svg>',
  sound:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H3v6h3l5 4z"/><path d="M16 9a4 4 0 010 6M19 7a8 8 0 010 10"/></svg>',
  mute:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H3v6h3l5 4z"/><path d="M17 9l4 4M21 9l-4 4"/></svg>',
  cloud:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18a4 4 0 01-.5-8A5.5 5.5 0 0117 9.5a4 4 0 011 7.5z"/></svg>',
  neon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21l4-8h6l4 8M9 13l3-9 3 9"/></svg>',
  photo:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.8"/><path d="M21 16l-5-5-8 8"/></svg>',
  home:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l9-8 9 8M5 10v10h14V10"/></svg>',
  image:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5-10 10"/></svg>',
  zoomIn:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3M8 11h6M11 8v6"/></svg>',
  zoomOut:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3M8 11h6"/></svg>',
  fit:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9V5a2 2 0 012-2h4M15 3h4a2 2 0 012 2v4M21 15v4a2 2 0 01-2 2h-4M9 21H5a2 2 0 01-2-2v-4"/></svg>',
  rocketH:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h18"/><path d="M15 8l4 4-4 4M9 8l-4 4 4 4"/></svg>',
  rocketV:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M8 15l4 4 4-4M8 9l4-4 4 4"/></svg>',
  infinity:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16C3.8 16 2.5 14.2 2.5 12S3.8 8 6 8c1.5 0 2.5 1 3.5 3 1 2 2 3 3.5 3 2.2 0 3.5-1.8 3.5-4s-1.3-4-3.5-4c-1.5 0-2.5 1-3.5 3-1 2-2 3-3.5 3z"/></svg>',
  clock:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  calendarDay:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M8 2v4M16 2v4M3 9h18"/></svg>',
};
function ic(name, cls=''){ return `<span class="ic ${cls}">${SVG[name]||''}</span>`; }

const BG_LIST = [
  { key:'cloud',  name:'云海白昼',  icon:'cloud' },
  { key:'neon',   name:'赛博夜场',  icon:'neon'  },
  { key:'photo1', name:'二次元·壹', icon:'photo' },
  { key:'photo2', name:'二次元·贰', icon:'photo' },
];

// 关卡配置 (moves: 0 = 无限步数)
const LEVELS = [
  { id:1,  name:'初见桓睿',   target:2000, moves:0,  goals:[{t:'score',v:2000}] },
  { id:2,  name:'渐入佳境',   target:3000, moves:0,  goals:[{t:'score',v:3000}] },
  { id:3,  name:'连击初体验', target:3500, moves:0,  goals:[{t:'score',v:3500},{t:'combo',v:3}] },
  { id:4,  name:'步数挑战',   target:3000, moves:30, goals:[{t:'score',v:3000}] },
  { id:5,  name:'炸弹实验室', target:3500, moves:26, goals:[{t:'score',v:3500},{t:'bomb',v:1}] },
  { id:6,  name:'彩虹时刻',   target:4500, moves:26, goals:[{t:'score',v:4500},{t:'rainbow',v:1}] },
  { id:7,  name:'连击大师',   target:5000, moves:25, goals:[{t:'score',v:5000},{t:'combo',v:4}] },
  { id:8,  name:'极速通关',   target:4000, moves:20, goals:[{t:'score',v:4000}] },
  { id:9,  name:'双重目标',   target:5000, moves:24, goals:[{t:'score',v:5000},{t:'bomb',v:2}] },
  { id:10, name:'彩虹盛宴',   target:6000, moves:22, goals:[{t:'score',v:6000},{t:'rainbow',v:2}] },
  { id:11, name:'极限连击',   target:7000, moves:20, goals:[{t:'score',v:7000},{t:'combo',v:5}] },
  { id:12, name:'桓睿大师',   target:8000, moves:18, goals:[{t:'score',v:8000},{t:'combo',v:5},{t:'rainbow',v:2}] },
];
const GOAL_META = {
  score:  { icon:'star',     label:'达到分数' },
  combo:  { icon:'fire',     label:'达成连击' },
  bomb:   { icon:'bomb',     label:'生成炸弹' },
  rainbow:{ icon:'rainbow',  label:'生成彩虹' },
};

// ---------- DOM ----------
const $ = id => document.getElementById(id);
const boardEl=$('board'), fxCanvas=$('fxCanvas'), floatLayer=$('floatLayer');
const scoreEl=$('score'), bigScoreEl=$('bigScore'), progressBar=$('progressBar'), progressText=$('progressText');
const comboEl=$('combo'), movesLeftEl=$('movesLeft');
const levelPill=$('levelPill'), levelNum=$('levelNum'), levelName=$('levelName');
const goalsEl=$('goals'), hintEl=$('hint');
const bestScoreEl=$('bestScore'), statClears=$('statClears'), statCombo=$('statCombo'), statMoves=$('statMoves');
const toastEl=$('toast'), appEl=document.body;
const bgParticles=$('bgParticles');

// ---------- 状态 ----------
let board=[], tileSize=0, cellUnit=0;
let score=0, moves=0, usedMoves=0, combo=0, busy=false;
let currentLevel=null, levelIdx=0;
let stats={ clears:0, maxCombo:0, bombs:0, rainbows:0 };
let goalProgress={};
let selected=null;
let bgIdx=0, soundOn=true;
let state='menu';
let mode='campaign';
const M_CAMPAIGN='campaign', M_ENDLESS='endless', M_TIMED='timed', M_DAILY='daily';
let dailyRng=null, timerInt=null, timeLeftMs=0, timeBonusTotal=0, timerExpired=false, lastTick=0;
const TIME_TOTAL=60000, TIME_BONUS_CAP=10000;
let audioCtx=null, masterGain=null, bgOsc=null, bgGain=null;
// 背景音乐（MP3 列表播放）
const MUSIC_LIST = [
  { file:'bgm1.mp3', name:'Puzzle Loop' },
  { file:'bgm2.mp3', name:'Puzzle Bright' },
  { file:'bgm3.mp3', name:'8-Bit Game' },
  { file:'bgm4.mp3', name:'Retro Arcade' },
];
let bgAudio=null, musicIdx=0;

const SAVE = {
  get unlocked(){ return +localStorage.getItem('xxl-unlocked')||1; },
  set unlocked(v){ localStorage.setItem('xxl-unlocked', v); },
  stars: JSON.parse(localStorage.getItem('xxl-stars')||'{}'),
  best: JSON.parse(localStorage.getItem('xxl-best')||'{}'),
  saveStars(lvl,s){ this.stars[lvl]=Math.max(this.stars[lvl]||0,s); localStorage.setItem('xxl-stars',JSON.stringify(this.stars)); },
  saveBest(lvl,s){ this.best[lvl]=Math.max(this.best[lvl]||0,s); localStorage.setItem('xxl-best',JSON.stringify(this.best)); },
};
const themePref = localStorage.getItem('xxl-theme')||'light';
const bgPref = localStorage.getItem('xxl-bg')||'cloud';
const soundPref = localStorage.getItem('xxl-sound'); soundOn = soundPref===null?true:soundPref==='1';

// 设置
const settings = {
  sfx: localStorage.getItem('xxl-sfx')!=='0',
  music: localStorage.getItem('xxl-music')!=='0',
  volume: +localStorage.getItem('xxl-vol')||45,
  motion: localStorage.getItem('xxl-motion')!=='0',
  haptic: localStorage.getItem('xxl-haptic')!=='0',
  quality: localStorage.getItem('xxl-quality')||'auto',
  save(){ localStorage.setItem('xxl-sfx',this.sfx?'1':'0'); localStorage.setItem('xxl-music',this.music?'1':'0'); localStorage.setItem('xxl-vol',this.volume); localStorage.setItem('xxl-motion',this.motion?'1':'0'); localStorage.setItem('xxl-haptic',this.haptic?'1':'0'); localStorage.setItem('xxl-quality',this.quality); }
};
soundOn = settings.sfx;

// 特效质量档位
const QUALITY_PRESETS = {
  high:   { dpr:2,    particles:12, shockwaves:2, shake:true,  glow:true  },
  medium: { dpr:1.5,  particles:8,  shockwaves:1, shake:true,  glow:true  },
  low:    { dpr:1,    particles:4,  shockwaves:0, shake:false, glow:false },
};
function detectQuality(){
  const dm=navigator.deviceMemory||4, hc=navigator.hardwareConcurrency||4, dpr=window.devicePixelRatio||1;
  const saveData=navigator.connection&&navigator.connection.saveData;
  if(saveData||dm<=2||hc<=2) return 'low';
  if(dm>=6&&hc>=6&&dpr<=2) return 'high';
  return 'medium';
}
function resolveQuality(){
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) return 'low';
  if(!settings.motion) return 'low';
  return settings.quality==='auto'?detectQuality():settings.quality;
}
let Q = QUALITY_PRESETS[resolveQuality()];

// 成就系统
const ACHIEVEMENTS = [
  { id:'first_clear', name:'初出茅庐', desc:'完成首次消除', icon:'spark' },
  { id:'combo3', name:'连击新星', desc:'达成 3 连击', icon:'fire' },
  { id:'combo5', name:'连击大师', desc:'达成 5 连击', icon:'fire' },
  { id:'combo8', name:'连击之王', desc:'达成 8 连击', icon:'fire' },
  { id:'make_bomb', name:'爆破专家', desc:'首次生成炸弹', icon:'bomb' },
  { id:'make_rainbow', name:'彩虹召唤', desc:'首次生成彩虹', icon:'rainbow' },
  { id:'clear5', name:'群体消除', desc:'单次消除 5 个方块', icon:'star' },
  { id:'clear8', name:'清场达人', desc:'单次消除 8 个方块', icon:'star' },
  { id:'beat1', name:'闯关启程', desc:'通关第 1 关', icon:'trophy' },
  { id:'beat6', name:'彩虹猎手', desc:'通关第 6 关', icon:'trophy' },
  { id:'beat12', name:'桓睿大师', desc:'通关全部关卡', icon:'trophy' },
  { id:'total500', name:'消消达人', desc:'累计消除 500 个方块', icon:'chart' },
  { id:'daily_win', name:'每日一题', desc:'完成一次每日挑战', icon:'calendarDay' },
];
const achState = JSON.parse(localStorage.getItem('xxl-ach')||'{}');
let totalClears = +localStorage.getItem('xxl-total')||0;
function unlockAchievement(id){
  if(achState[id]) return;
  const a = ACHIEVEMENTS.find(x=>x.id===id); if(!a) return;
  achState[id]=Date.now(); localStorage.setItem('xxl-ach',JSON.stringify(achState));
  showAchievement(a);
}
function showAchievement(a){
  const el=$('achievement');
  el.innerHTML = `<div class="ach-icon">${SVG[a.icon]||''}</div><div class="ach-text"><div class="ach-label">成就解锁</div><div class="ach-name">${a.name}</div></div>`;
  el.classList.add('show');
  sfx.achieve();
  clearTimeout(showAchievement._t); showAchievement._t=setTimeout(()=>el.classList.remove('show'),3200);
}
function haptic(ms){ if(settings.haptic && navigator.vibrate) try{ navigator.vibrate(ms); }catch(e){} }

// ---------- 工具 ----------
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const rnd=n=>Math.floor((mode==='daily'&&dailyRng?dailyRng():Math.random())*n);
function mulberry32(a){ return function(){ a|=0; a=(a+0x6D2B79F5)|0; let t=Math.imul(a^(a>>>15),1|a); t=(t+Math.imul(t^(t>>>7),61|t))^t; return ((t^(t>>>14))>>>0)/4294967296; }; }
function todayKey(){ const d=new Date(); return d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0'); }
function typeCount(){ if(mode==='endless') return score>=15000?6:score>=5000?5:4; return TYPES; }
const inBounds=(r,c)=>r>=0&&r<ROWS&&c>=0&&c<COLS;
function showToast(msg,dur=1600){ toastEl.textContent=msg; toastEl.classList.add('show'); clearTimeout(showToast._t); showToast._t=setTimeout(()=>toastEl.classList.remove('show'),dur); }
const isInfiniteMoves = ()=> currentLevel && currentLevel.moves===0;

// ---------- 尺寸 ----------
function measure(){
  const w=boardEl.clientWidth-PAD*2;
  if(w<=0) return;
  tileSize=(w-GAP*(COLS-1))/COLS; cellUnit=tileSize+GAP;
  boardEl.style.setProperty('--tile-size',tileSize+'px');
  boardEl.style.setProperty('--gap',GAP+'px'); boardEl.style.setProperty('--board-pad',PAD+'px');
}
const posOf=(r,c)=>({x:c*cellUnit,y:r*cellUnit});

// ---------- 方块 ----------
function makeTile(r,c,type,special=SPECIAL.NONE){
  const el=document.createElement('div');
  el.className=`tile t${type}`;
  if(special===SPECIAL.ROCKET_H) el.classList.add('special-rocket-h');
  if(special===SPECIAL.ROCKET_V) el.classList.add('special-rocket-v');
  if(special===SPECIAL.BOMB) el.classList.add('special-bomb');
  if(special===SPECIAL.RAINBOW) el.classList.add('special-rainbow');
  el.dataset.r=r; el.dataset.c=c; el.dataset.type=type;
  const face=document.createElement('div'); face.className='face';
  const img=document.createElement('img'); img.src=faceSrcOf(type); img.draggable=false; img.alt='';
  img.onerror=()=>{ face.style.background=ACCENT[type]; };
  face.appendChild(img);
  const ring=document.createElement('div'); ring.className='ring';
  const corner=document.createElement('div'); corner.className='corner'; corner.textContent=type+1;
  el.appendChild(face); el.appendChild(ring); el.appendChild(corner);
  if(special!==SPECIAL.NONE){ const badge=document.createElement('span'); badge.className='badge'; badge.innerHTML=ic(({[SPECIAL.BOMB]:'bomb',[SPECIAL.RAINBOW]:'rainbow',[SPECIAL.ROCKET_H]:'rocketH',[SPECIAL.ROCKET_V]:'rocketV'})[special]||'star'); el.appendChild(badge); }
  const {x,y}=posOf(r,c);
  el.style.setProperty('--tx',x+'px'); el.style.setProperty('--ty',y+'px');
  el.style.transform=`translate3d(${x}px,${y}px,${Z_TILE}px)`;
  el.style.width=el.style.height=tileSize+'px';
  bindInput(el); boardEl.appendChild(el); return el;
}
function placeTile(t,r,c,animate=true){
  const {x,y}=posOf(r,c); t.el.dataset.r=r; t.el.dataset.c=c;
  t.el.style.setProperty('--tx',x+'px'); t.el.style.setProperty('--ty',y+'px');
  t.el.style.transform=`translate3d(${x}px,${y}px,${Z_TILE}px)`;
  if(!animate) t.el.style.transition='none';
  return sleep(animate?SWAP_DUR:0).then(()=>{ if(!animate) t.el.style.transition=''; });
}

// ---------- 棋盘初始化 ----------
function initBoard(){
  boardEl.querySelectorAll('.tile').forEach(e=>e.remove()); board=[];
  for(let r=0;r<ROWS;r++){ board[r]=[];
    for(let c=0;c<COLS;c++){
      let type; do{ type=rnd(typeCount()); }while(createsMatch(r,c,type));
      const el=makeTile(r,c,type,SPECIAL.NONE);
      board[r][c]={type,special:SPECIAL.NONE,el};
    }
  }
  requestAnimationFrame(()=>{ const tiles=boardEl.querySelectorAll('.tile'); tiles.forEach((e,i)=>{
    e.style.animationDelay=(i*10)+'ms'; e.classList.add('spawning');
    e.addEventListener('animationend',()=>{ e.classList.remove('spawning'); e.style.animationDelay=''; },{once:true});
  }); });
}
function createsMatch(r,c,type){
  if(c>=2&&board[r][c-1]?.type===type&&board[r][c-2]?.type===type) return true;
  if(r>=2&&board[r-1][c]?.type===type&&board[r-2][c]?.type===type) return true;
  return false;
}
function clearBoard(){
  boardEl.querySelectorAll('.tile').forEach(e=>e.remove()); board=[];
  floatLayer.innerHTML=''; stopParticleLoop();
}

// ---------- 匹配检测 ----------
function findAllMatches(){
  const matched=new Set(); const runs=[];
  for(let r=0;r<ROWS;r++){ let c=0;
    while(c<COLS){ const t=board[r][c]; if(!t){c++;continue;} let k=c+1;
      while(k<COLS&&board[r][k]&&board[r][k].type===t.type) k++;
      if(k-c>=3){ const cells=[]; for(let i=c;i<k;i++){cells.push({r,c:i});matched.add(`${r},${i}`);} runs.push({cells,type:t.type,dir:'h',len:k-c}); } c=k; }
  }
  for(let c=0;c<COLS;c++){ let r=0;
    while(r<ROWS){ const t=board[r][c]; if(!t){r++;continue;} let k=r+1;
      while(k<ROWS&&board[k][c]&&board[k][c].type===t.type) k++;
      if(k-r>=3){ const cells=[]; for(let i=r;i<k;i++){cells.push({r:i,c});matched.add(`${i},${c}`);} runs.push({cells,type:t.type,dir:'v',len:k-r}); } r=k; }
  }
  return {matched,runs};
}

// ---------- 交换 ----------
async function trySwap(r1,c1,r2,c2){
  if(busy||state!=='playing') return;
  if(!inBounds(r1,c1)||!inBounds(r2,c2)) return;
  if((Math.abs(r1-r2)+Math.abs(c1-c2))!==1) return;
  const a=board[r1][c1], b=board[r2][c2]; if(!a||!b) return;

  if(a.special===SPECIAL.RAINBOW||b.special===SPECIAL.RAINBOW){
    busy=true; clearSelection();
    swapData(r1,c1,r2,c2);
    await Promise.all([placeTile(a,r2,c2),placeTile(b,r1,c1)]); sfx.swap();
    const rainbow=a.special===SPECIAL.RAINBOW?a:b;
    const other=a.special===SPECIAL.RAINBOW?b:a;
    const rPos=a.special===SPECIAL.RAINBOW?{r:r2,c:c2}:{r:r1,c:c1};
    const oPos=a.special===SPECIAL.RAINBOW?{r:r1,c:c1}:{r:r2,c:c2};
    const set=new Set();
    set.add(rPos.r+','+rPos.c); set.add(oPos.r+','+oPos.c);
    const add=(r,c)=>{ if(inBounds(r,c)) set.add(r+','+c); };
    for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
      const t=board[r][c]; if(!t||t.type!==other.type) continue;
      if(other.special===SPECIAL.BOMB){ for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++) add(r+dr,c+dc); }
      else if(other.special===SPECIAL.ROCKET_H){ for(let nc=0;nc<COLS;nc++) add(r,nc); }
      else if(other.special===SPECIAL.ROCKET_V){ for(let nr=0;nr<ROWS;nr++) add(nr,c); }
      else { add(r,c); }
    }
    const targets=Array.from(set).map(parseKey);
    if(other.special===SPECIAL.BOMB) sfx.bomb();
    if(other.special===SPECIAL.ROCKET_H||other.special===SPECIAL.ROCKET_V) sfx.special(SPECIAL.ROCKET_H);
    await removeCells(targets,{rainbow:other.special===SPECIAL.RAINBOW});
    combo=0; await cascade(); afterMove(); return;
  }
  busy=true; clearSelection();
  swapData(r1,c1,r2,c2);
  await Promise.all([placeTile(a,r2,c2),placeTile(b,r1,c1)]); sfx.swap();
  const {matched}=findAllMatches();
  if(matched.size>0){ combo=0; await cascade(); }
  else { swapData(r2,c2,r1,c1); await Promise.all([placeTile(a,r1,c1),placeTile(b,r2,c2)]); sfx.invalid(); showToast('这里消除不了哦～'); }
  afterMove();
}
function swapData(r1,c1,r2,c2){ const t=board[r1][c1]; board[r1][c1]=board[r2][c2]; board[r2][c2]=t; }

function afterMove(){
  if(mode===M_TIMED&&timerExpired){ setTimeout(()=>finishMode(),450); return; }
  usedMoves++;
  if(mode===M_CAMPAIGN&&!isInfiniteMoves()) moves--;
  if(mode===M_DAILY) moves--;
  busy=false; updateHUD();
  if(checkGoalsMet()){ setTimeout(()=>winLevel(),500); return; }
  if((mode===M_CAMPAIGN||mode===M_DAILY) && !isInfiniteMoves() && moves<=0){ setTimeout(()=>loseLevel(),600); return; }
  if(!hasPossibleMove()){ showToast('没有可消除的组合，重新洗牌！'); setTimeout(shuffleBoard,600); return; }
  scheduleHint();
}

// ---------- 目标 ----------
function checkGoalsMet(){
  if(!currentLevel) return false;
  for(const g of currentLevel.goals){
    const p=goalProgress[g.t]||0;
    if(g.t==='score'){ if(score<g.v) return false; }
    else { if(p<g.v) return false; }
  }
  return true;
}

// ---------- 连锁 ----------
async function cascade(){
  while(true){
    const {matched,runs}=findAllMatches();
    if(matched.size===0) break;
    combo++; stats.maxCombo=Math.max(stats.maxCombo,combo);
    const specials=planSpecials(runs);
    let toRemove=new Set(matched);
    for(const k of collectSpecialTriggers(matched)) toRemove.add(k);
    toRemove=expandSpecials(toRemove);
    const gain=scoreFor(toRemove.size,combo);
    score+=gain; stats.clears+=toRemove.size; totalClears+=toRemove.size; localStorage.setItem('xxl-total',totalClears);
    updateHUD();
    const center=centerOf(toRemove);
    if(mode===M_TIMED&&combo>=2&&timeBonusTotal<TIME_BONUS_CAP){
      const add=2000; timeBonusTotal+=add; timeLeftMs+=add;
      floatText({...center,dy:-66},'+2秒','time');
    }
    floatText(center,`+${gain}`,combo>=2?'combo':'');
    if(combo>=2){ floatText({...center,dy:-34},`COMBO ×${combo}`,'combo big'); if(combo>=3) comboFlash(combo); }
    sfx.clear(combo); haptic(combo>=3?40:20);
    // 成就检测
    unlockAchievement('first_clear');
    if(combo>=3) unlockAchievement('combo3');
    if(combo>=5) unlockAchievement('combo5');
    if(combo>=8) unlockAchievement('combo8');
    if(toRemove.size>=5) unlockAchievement('clear5');
    if(toRemove.size>=8) unlockAchievement('clear8');
    if(totalClears>=500) unlockAchievement('total500');
    if([...toRemove].some(k=>{const{r,c}=parseKey(k);const t=board[r]&&board[r][c];return t&&t.special===SPECIAL.BOMB;})) sfx.bomb();
    // 预闪烁：匹配方块在移除前轻微缩放高亮（仅 transform/opacity）
    if(Q.glow){ for(const k of toRemove){ const{r,c}=parseKey(k); const t=board[r]&&board[r][c]; if(t) t.el.classList.add('pre-clear'); } await sleep(110); }
    await removeCells(Array.from(toRemove).map(parseKey),{specials});
    await placeSpecials(specials);
    await dropAndFill();
  }
  combo=0; updateHUD();
}
function scoreFor(n,c){ return Math.round(n*30*(1+(c-1)*0.5)); }
function planSpecials(runs){
  const out=[]; const planned=new Set();
  const key=(r,c)=>r+','+c;
  // 1) 直线 5+ → 彩虹
  for(const run of runs){
    if(run.len>=5){
      const mid=run.cells[Math.floor(run.cells.length/2)];
      if(!planned.has(key(mid.r,mid.c))){
        planned.add(key(mid.r,mid.c));
        out.push({r:mid.r,c:mid.c,type:run.type,special:SPECIAL.RAINBOW});
        stats.rainbows++; goalProgress.rainbow=(goalProgress.rainbow||0)+1; unlockAchievement('make_rainbow');
      }
    }
  }
  // 2) 横竖交叉（T/L/十字）→ 炸弹（交叉点）
  const hs=runs.filter(x=>x.dir==='h'&&x.len>=3), vs=runs.filter(x=>x.dir==='v'&&x.len>=3);
  for(const h of hs){
    for(const v of vs){
      let hit=null;
      for(const hc of h.cells){ if(v.cells.some(vc=>vc.r===hc.r&&vc.c===hc.c)){ hit=hc; break; } }
      if(hit&&!planned.has(key(hit.r,hit.c))){
        planned.add(key(hit.r,hit.c));
        out.push({r:hit.r,c:hit.c,type:h.type,special:SPECIAL.BOMB});
        stats.bombs++; goalProgress.bomb=(goalProgress.bomb||0)+1; unlockAchievement('make_bomb');
      }
    }
  }
  // 3) 直线 4 → 条纹火箭（方向=连线走向）
  for(const run of runs){
    if(run.len!==4) continue;
    const mid=run.cells[Math.floor(run.cells.length/2)];
    if(planned.has(key(mid.r,mid.c))) continue;
    planned.add(key(mid.r,mid.c));
    out.push({r:mid.r,c:mid.c,type:run.type,special:run.dir==='h'?SPECIAL.ROCKET_H:SPECIAL.ROCKET_V});
    stats.rockets++;
  }
  if(combo>=2) goalProgress.combo=Math.max(goalProgress.combo||0,combo);
  return out;
}
function collectSpecialTriggers(set){ const extra=new Set(); for(const k of set){ const{r,c}=parseKey(k); const t=board[r][c]; if(t&&t.special!==SPECIAL.NONE) extra.add(k);} return extra; }
function expandSpecials(set){
  const result=new Set(set); const queue=Array.from(set); const seen=new Set(set);
  const add=(nr,nc)=>{ if(!inBounds(nr,nc)) return; const k=nr+','+nc; if(!seen.has(k)){seen.add(k);result.add(k);queue.push(k);} };
  while(queue.length){ const key=queue.shift(); const{r,c}=parseKey(key); const t=board[r]&&board[r][c]; if(!t) continue;
    if(t.special===SPECIAL.BOMB){ for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++) add(r+dr,c+dc); }
    else if(t.special===SPECIAL.ROCKET_H){ for(let nc=0;nc<COLS;nc++) add(r,nc); }
    else if(t.special===SPECIAL.ROCKET_V){ for(let nr=0;nr<ROWS;nr++) add(nr,c); }
  }
  return result;
}
async function placeSpecials(specials){
  for(const s of specials){
    const el=makeTile(s.r,s.c,s.type,s.special); el.classList.add('spawning');
    board[s.r][s.c]={type:s.type,special:s.special,el};
    sfx.special(s.special); shockwave(s.r,s.c,s.special); setTimeout(()=>el.classList.remove('spawning'),450);
    await sleep(60);
  }
}
async function removeCells(cells,opts={}){
  for(const {r,c} of cells){ const t=board[r]&&board[r][c]; if(!t) continue; spawnParticles(r,c,t.type,opts.rainbow); t.el.classList.add('removing'); }
  if(cells.length>=5&&Q.shake){ appEl.classList.add('shake'); setTimeout(()=>appEl.classList.remove('shake'),350); }
  await sleep(REMOVE_DUR);
  for(const {r,c} of cells){ const t=board[r]&&board[r][c]; if(!t) continue; t.el.remove(); board[r][c]=null; }
}
async function dropAndFill(){
  const newTiles=[];
  for(let c=0;c<COLS;c++){ let write=ROWS-1;
    for(let r=ROWS-1;r>=0;r--){ if(board[r][c]){ if(r!==write){ board[write][c]=board[r][c]; board[r][c]=null; placeTile(board[write][c],write,c,true);} write--; } }
    for(let r=write;r>=0;r--){ const type=rnd(typeCount()); const el=makeTile(r,c,type,SPECIAL.NONE);
      const startY=-(write-r+1)*cellUnit; el.style.transition='none'; el.style.transform=`translate3d(${c*cellUnit}px,${startY}px,${Z_TILE}px)`;
      board[r][c]={type,special:SPECIAL.NONE,el}; newTiles.push({tile:board[r][c],r,c}); }
  }
  await sleep(20);
  for(const {tile,r,c} of newTiles){ tile.el.style.transition=''; placeTile(tile,r,c,true); }
  await sleep(FALL_DUR);
}

// ---------- 粒子 ----------
const ctx=fxCanvas.getContext('2d'); let particles=[]; let particleRAF=null;
const isMobile = IS_MOBILE;
let dpr = Math.min(window.devicePixelRatio||1, Q.dpr);   // fx canvas 效果 DPR
let bgDpr = Math.min(window.devicePixelRatio||1, isMobile?1.25:1.5); // 背景 canvas DPR
const MAX_PARTICLES = isMobile?96:160;
// 粒子对象池
const particlePool = [];
function newParticle(){ return particlePool.pop() || {}; }
function freeParticle(p){ if(particlePool.length<MAX_PARTICLES){ for(const k in p) p[k]=undefined; particlePool.push(p); } }
function resizeFx(){ dpr=Math.min(window.devicePixelRatio||1, Q.dpr); const rect=boardEl.getBoundingClientRect(); if(rect.width<=0) return; fxCanvas.width=rect.width*dpr; fxCanvas.height=rect.height*dpr; fxCanvas.style.width=rect.width+'px'; fxCanvas.style.height=rect.height+'px'; }
function spawnParticles(r,c,type,rainbow){
  if(!settings.motion) return;
  const {x,y}=posOf(r,c); const cx=(x+tileSize/2+PAD)*dpr, cy=(y+tileSize/2+PAD)*dpr;
  const colors=rainbow?['#ff6b6b','#4ecdc4','#ffd93d','#a78bfa']:[ACCENT[type],'#ffffff'];
  const n = Q.particles;
  for(let i=0;i<n;i++){ const a=(Math.PI*2*i)/n+Math.random()*.4; const sp=(1.8+Math.random()*2.6)*dpr;
    if(particles.length>=MAX_PARTICLES) break;
    const p=newParticle(); Object.assign(p,{x:cx,y:cy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-1,life:1,decay:.018+Math.random()*.02,size:(3+Math.random()*4)*dpr,color:colors[i%colors.length],rot:Math.random()*Math.PI,vr:(Math.random()-.5)*.3});
    particles.push(p); }
  if(particles.length<MAX_PARTICLES){ const p=newParticle(); Object.assign(p,{ring:true,x:cx,y:cy,r:4*dpr,life:1,decay:.05,color:ACCENT[type]}); particles.push(p); }
  ensureParticleLoop();
}
function shockwave(r,c,sp){
  if(!settings.motion||Q.shockwaves<=0) return;
  const {x,y}=posOf(r,c); const cx=(x+tileSize/2+PAD)*dpr, cy=(y+tileSize/2+PAD)*dpr;
  const col = sp===SPECIAL.RAINBOW?'#a78bfa':sp===SPECIAL.BOMB?'#ff6b6b':sp===SPECIAL.ROCKET_V?'#ffaa3c':'#4ecdc4';
  for(let k=0;k<Q.shockwaves;k++){ if(particles.length>=MAX_PARTICLES) break; const p=newParticle(); Object.assign(p,{ring:true,x:cx,y:cy,r:6*dpr,life:1,decay:.04,color:col}); particles.push(p); }
  ensureParticleLoop();
}
function tickParticles(){
  ctx.clearRect(0,0,fxCanvas.width,fxCanvas.height);
  let write=0;
  for(let i=0;i<particles.length;i++){ const p=particles[i]; p.life-=p.decay; if(p.life<=0){ freeParticle(p); continue; }
    if(p.ring){ p.r+=3*dpr; ctx.save(); ctx.globalAlpha=p.life*.6; ctx.strokeStyle=p.color; ctx.lineWidth=3*dpr; ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.stroke(); ctx.restore(); }
    else { p.x+=p.vx; p.y+=p.vy; p.vy+=.15*dpr; p.rot+=p.vr; ctx.save(); ctx.globalAlpha=p.life; ctx.translate(p.x,p.y); ctx.rotate(p.rot); ctx.fillStyle=p.color; ctx.fillRect(-p.size/2,-p.size/2,p.size,p.size); ctx.restore(); }
    particles[write++]=p;
  }
  particles.length=write;
  if(write>0){ particleRAF=requestAnimationFrame(tickParticles); }
  else { particleRAF=null; }
}
function ensureParticleLoop(){ if(particleRAF===null && particles.length>0) particleRAF=requestAnimationFrame(tickParticles); }
function stopParticleLoop(){ if(particleRAF!==null){ cancelAnimationFrame(particleRAF); particleRAF=null; } ctx.clearRect(0,0,fxCanvas.width,fxCanvas.height); particles.length=0; }
function comboFlash(level){ const f=document.querySelector('.combo-flash')||(()=>{const d=document.createElement('div');d.className='combo-flash';document.body.appendChild(d);return d;})(); const col = level>=8?'rgba(167,139,250,.35)':level>=5?'rgba(255,107,107,.3)':'rgba(255,217,61,.25)'; f.style.background=`radial-gradient(ellipse at center,${col},transparent 70%)`; if(f.animate){ f.animate([{opacity:0},{opacity:1,offset:.3},{opacity:0}],{duration:400,easing:'ease-out'}); } else { f.classList.remove('on'); f.classList.add('on'); } }
function floatText(pos,text,cls=''){ const el=document.createElement('div'); el.className='float-text '+cls; el.textContent=text; el.style.left=(pos.x+PAD)+'px'; el.style.top=(pos.y+PAD+(pos.dy||0))+'px'; floatLayer.appendChild(el); setTimeout(()=>el.remove(),950); }
function centerOf(set){ let sx=0,sy=0,n=0; for(const k of set){const{r,c}=parseKey(k);const{x,y}=posOf(r,c);sx+=x+tileSize/2;sy+=y+tileSize/2;n++;} return {x:sx/n,y:sy/n}; }
const parseKey=k=>{const[r,c]=k.split(',').map(Number);return{r,c};};

// ---------- HUD ----------
let lastScore=0;
let scoreAnimRAF=null;
function bumpEl(el){ if(el.animate){ el.animate([{transform:'scale(1)'},{transform:'scale(1.22)',offset:.4},{transform:'scale(1)'}],{duration:350,easing:'cubic-bezier(.34,1.56,.64,1)'}); } else { el.classList.remove('bump'); el.classList.add('bump'); } }
function animateScoreTo(target){
  const from=lastScore; if(from===target){ scoreEl.textContent=target; bigScoreEl.textContent=target; return; }
  cancelAnimationFrame(scoreAnimRAF);
  const start=performance.now(); const dur=400;
  function step(now){
    const t=Math.min(1,(now-start)/dur);
    const eased=1-Math.pow(1-t,3);
    const v=Math.round(from+(target-from)*eased);
    scoreEl.textContent=v; bigScoreEl.textContent=v;
    if(t<1) scoreAnimRAF=requestAnimationFrame(step); else lastScore=target;
  }
  scoreAnimRAF=requestAnimationFrame(step);
}
function updateHUD(){
  if(score!==lastScore){ bumpEl(scoreEl); bumpEl(bigScoreEl); animateScoreTo(score); }
  if(mode===M_TIMED){
    // 倒计时由 timerTick 渲染
  } else if(mode===M_ENDLESS){
    const lv = score>=15000?3:score>=5000?2:1;
    movesLeftEl.textContent='Lv'+lv;
    const next=lv===3?null:(lv===1?5000:15000);
    if(next){ progressBar.style.width=Math.min(100,score/next*100)+'%'; progressText.textContent=score+' / '+next+' 下一难度'; }
    else{ progressBar.style.width='100%'; progressText.textContent='最高难度 · 6 种方块'; }
  } else {
    movesLeftEl.textContent = isInfiniteMoves() ? '∞' : Math.max(0,moves);
    if(currentLevel){ const pct=Math.min(100,score/currentLevel.target*100); progressBar.style.width=pct+'%'; progressText.textContent=score+' / '+currentLevel.target; }
  }
  comboEl.textContent='×'+Math.max(1,combo);
  bestScoreEl.textContent=(mode==='campaign'&&currentLevel&&SAVE.best[currentLevel.id])||0;
  statClears.textContent=stats.clears; statCombo.textContent='×'+stats.maxCombo; statMoves.textContent=usedMoves;
  const movesStat=movesLeftEl.closest('.hud-stat');
  if(movesStat){
    if(mode===M_TIMED) movesStat.classList.toggle('low', timeLeftMs<=10000);
    else movesStat.classList.toggle('low', !isInfiniteMoves() && moves<=3 && moves>0);
  }
  renderGoals();
}
function renderGoals(){
  if(!currentLevel) return;
  goalsEl.innerHTML='';
  for(const g of currentLevel.goals){
    const meta=GOAL_META[g.t]; const p=g.t==='score'?score:(goalProgress[g.t]||0);
    const done=g.t==='score'?score>=g.v:p>=g.v;
    const item=document.createElement('div'); item.className='goal-item'+(done?' done':'');
    item.innerHTML=`<div class="goal-icon">${ic(meta.icon)}</div><div class="goal-text">${meta.label}</div><div class="goal-progress">${Math.min(p,g.v)}/${g.v}${done?' '+ic('check','inline'):''}</div>`;
    goalsEl.appendChild(item);
  }
}

// ---------- 输入（跟手拖动） ----------
let drag = null; // {r,c,el,dx,dy,dir,moved}
let dragRAF = null;
let hintTimer = null;
function bindInput(el){ el.addEventListener('pointerdown',onDown,{passive:false}); }
function onDown(e){
  if(busy||state!=='playing') return;
  if(e.pointerType==='mouse'&&e.button!==0) return;
  e.preventDefault();
  clearHint();
  const el=e.currentTarget; const r=+el.dataset.r,c=+el.dataset.c;
  drag={r,c,x:e.clientX,y:e.clientY,el,dx:0,dy:0,dir:null,moved:false,lastT:performance.now(),lastX:e.clientX,lastY:e.clientY,vx:0,vy:0};
  el.classList.add('dragging');
  el.style.transition='none';
  try{ el.setPointerCapture(e.pointerId); }catch(_){}
  window.addEventListener('pointermove',onMove,{passive:false});
  window.addEventListener('pointerup',onUp,{once:true});
  window.addEventListener('pointercancel',onUp,{once:true});
}
function onMove(e){
  if(!drag) return;
  let dx=e.clientX-drag.x, dy=e.clientY-drag.y;
  // 锁定主导方向
  if(!drag.dir){
    if(Math.hypot(dx,dy)>6) drag.dir = Math.abs(dx)>Math.abs(dy)?'h':'v';
    else return;
  }
  if(drag.dir==='h'){ dy=0; dx=Math.max(-cellUnit*0.55,Math.min(cellUnit*0.55,dx)); }
  else { dx=0; dy=Math.max(-cellUnit*0.55,Math.min(cellUnit*0.55,dy)); }
  drag.dx=dx; drag.dy=dy; drag.moved=true;
  // 记录瞬时速度（用于轻扫触发）
  const now=performance.now(); const dt=now-drag.lastT;
  if(dt>0){ drag.vx=(e.clientX-drag.lastX)/dt; drag.vy=(e.clientY-drag.lastY)/dt; }
  drag.lastT=now; drag.lastX=e.clientX; drag.lastY=e.clientY;
  // 即时写 transform（跟手优先，transform 是合成属性不触发 layout）
  const {x,y}=posOf(drag.r,drag.c);
  drag.el.style.transform=`translate3d(${x+dx}px,${y+dy}px,${Z_DRAG}px) scale(1.05)`;
}
function flushDrag(){
  // 仅 onUp 时同步确保最终位置
  if(!drag) return;
  const {x,y}=posOf(drag.r,drag.c);
  drag.el.style.transform=`translate3d(${x+drag.dx}px,${y+drag.dy}px,${Z_DRAG}px) scale(1.05)`;
}
function onUp(e){
  if(!drag) return;
  if(dragRAF!==null){ cancelAnimationFrame(dragRAF); dragRAF=null; flushDrag(); }
  const d=drag; drag.el.classList.remove('dragging');
  drag.el.style.transition='';
  window.removeEventListener('pointermove',onMove);
  // 判断是否达到交换阈值：距离够 或 轻扫速度够快
  const dist = Math.hypot(d.dx,d.dy);
  const speed = d.dir==='h' ? Math.abs(d.vx) : Math.abs(d.vy);
  const reach = dist > tileSize*SWIPE_THRESH || (dist > tileSize*0.1 && speed > 0.6);
  if(reach){
    let nr=d.r,nc=d.c;
    if(d.dir==='h') nc+=d.dx>0?1:-1; else nr+=d.dy>0?1:-1;
    // 回弹起始方块（trySwap 会重新定位）
    placeTile(board[d.r][d.c], d.r, d.c, false);
    drag=null;
    trySwap(d.r,d.c,nr,nc);
  } else {
    // 回弹
    placeTile(board[d.r][d.c], d.r, d.c, true);
    if(!d.moved){ handleTap(d.r,d.c); } // 当点击
    drag=null;
  }
  scheduleHint();
}
function handleTap(r,c){
  if(!selected){ selected={r,c}; board[r][c]?.el.classList.add('selected'); sfx.select(); return; }
  board[selected.r][selected.c]?.el.classList.remove('selected');
  if(selected.r===r&&selected.c===c){ selected=null; return; }
  if((Math.abs(selected.r-r)+Math.abs(selected.c-c))===1){ const s=selected; selected=null; trySwap(s.r,s.c,r,c); }
  else { selected={r,c}; board[r][c]?.el.classList.add('selected'); sfx.select(); }
}
function clearSelection(){ if(selected){ board[selected.r]?.[selected.c]?.el.classList.remove('selected'); selected=null; } }

// ---------- 提示系统 ----------
function scheduleHint(){ clearHint(); if(state!=='playing') return; hintTimer=setTimeout(showHint,5000); }
function clearHint(){ if(hintTimer){ clearTimeout(hintTimer); hintTimer=null; } document.querySelectorAll('.tile.hint').forEach(e=>e.classList.remove('hint')); }
function showHint(){
  if(busy||state!=='playing') return;
  const move=findHintMove(); if(!move) return;
  const a=board[move.r1][move.c1]?.el, b=board[move.r2][move.c2]?.el;
  if(a) a.classList.add('hint');
  if(b) b.classList.add('hint');
  setTimeout(clearHint,2500);
}
function findHintMove(){
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
    if(board[r][c]&&board[r][c].special!==SPECIAL.NONE) return {r1:r,c1:c,r2:r,c2:Math.min(COLS-1,c+1)};
  }
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
    if(c<COLS-1){ swapData(r,c,r,c+1); const m=findAllMatches().matched.size; swapData(r,c,r,c+1); if(m) return {r1:r,c1:c,r2:r,c2:c+1}; }
    if(r<ROWS-1){ swapData(r,c,r+1,c); const m=findAllMatches().matched.size; swapData(r,c,r+1,c); if(m) return {r1:r,c1:c,r2:r+1,c2:c}; }
  }
  return null;
}

// ---------- 死局/洗牌 ----------
function hasPossibleMove(){
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){ const t=board[r][c]; if(t&&t.special!==SPECIAL.NONE) return true; }
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){
    if(c<COLS-1){ swapData(r,c,r,c+1); const m=findAllMatches().matched.size; swapData(r,c,r,c+1); if(m) return true; }
    if(r<ROWS-1){ swapData(r,c,r+1,c); const m=findAllMatches().matched.size; swapData(r,c,r+1,c); if(m) return true; }
  }
  return false;
}
async function shuffleBoard(){
  busy=true; const types=[];
  for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++) if(board[r][c]) types.push(board[r][c].type);
  let attempts=0;
  do{ for(let i=types.length-1;i>0;i--){const j=rnd(i+1);[types[i],types[j]]=[types[j],types[i]];}
    let idx=0;
    for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){ if(board[r][c]){ board[r][c].type=types[idx++]; board[r][c].el.dataset.type=board[r][c].type; board[r][c].el.className=`tile t${board[r][c].type}`; const img=board[r][c].el.querySelector('img'); if(img) img.src=faceSrcOf(board[r][c].type); } }
    attempts++;
  } while((findAllMatches().matched.size>0||!hasPossibleMove())&&attempts<50);
  boardEl.querySelectorAll('.tile').forEach(e=>{e.classList.add('spawning');setTimeout(()=>e.classList.remove('spawning'),450);});
  await sleep(500); busy=false;
}

// ---------- 音效 (Web Audio) ----------
const sfx=(()=>{
  function ensure(){ if(!audioCtx){ audioCtx=new(window.AudioContext||window.webkitAudioContext)(); masterGain=audioCtx.createGain(); masterGain.gain.value=0.45; masterGain.connect(audioCtx.destination);} if(audioCtx.state==='suspended') audioCtx.resume(); return audioCtx; }
  function tone(freq,dur,type='sine',vol=0.3,glide=0){ if(!soundOn) return; const a=ensure(); const o=a.createOscillator(),g=a.createGain(); o.type=type; o.frequency.value=freq; if(glide) o.frequency.exponentialRampToValueAtTime(freq*glide,a.currentTime+dur); g.gain.setValueAtTime(0,a.currentTime); g.gain.linearRampToValueAtTime(vol,a.currentTime+0.01); g.gain.exponentialRampToValueAtTime(0.0001,a.currentTime+dur); o.connect(g); g.connect(masterGain); o.start(); o.stop(a.currentTime+dur+0.02); }
  function noise(dur,vol=0.4){ if(!soundOn) return; const a=ensure(); const n=a.createBufferSource(); const buf=a.createBuffer(1,a.sampleRate*dur,a.sampleRate); const d=buf.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=(Math.random()*2-1)*(1-i/d.length); n.buffer=buf; const g=a.createGain(); g.gain.value=vol; const f=a.createBiquadFilter(); f.type='lowpass'; f.frequency.value=1200; n.connect(f); f.connect(g); g.connect(masterGain); n.start(); }
  return {
    init:()=>{ ensure(); },
    select:()=>tone(520,0.08,'sine',0.15),
    swap:()=>tone(440,0.09,'triangle',0.2,1.2),
    invalid:()=>tone(180,0.18,'sawtooth',0.18,0.6),
    clear:(combo)=>{ const base=523+(combo-1)*70; tone(base,0.12,'triangle',0.22,1.5); setTimeout(()=>tone(base*1.5,0.1,'sine',0.16),60); },
    bomb:()=>{ noise(0.3,0.5); tone(120,0.3,'sawtooth',0.3,0.4); },
    special:(sp)=>{ if(sp===SPECIAL.RAINBOW){ [523,659,784,1047].forEach((f,i)=>setTimeout(()=>tone(f,0.15,'triangle',0.2),i*50)); } else if(sp===SPECIAL.ROCKET_H||sp===SPECIAL.ROCKET_V){ tone(620,0.1,'square',0.18,2.6); setTimeout(()=>{ noise(0.18,0.28); tone(180,0.3,'sawtooth',0.2,0.3); },70); } else { tone(80,0.2,'sawtooth',0.3,2); noise(0.15,0.3); } },
    win:()=>{ [523,659,784,1047,1319].forEach((f,i)=>setTimeout(()=>tone(f,0.3,'triangle',0.3),i*120)); },
    lose:()=>{ [400,330,260].forEach((f,i)=>setTimeout(()=>tone(f,0.35,'sawtooth',0.25),i*150)); },
    achieve:()=>{ [659,784,988,1319].forEach((f,i)=>setTimeout(()=>tone(f,0.25,'triangle',0.25),i*90)); },
    btn:()=>tone(660,0.06,'sine',0.12),
  };
})();
function startBgMusic(){
  if(!settings.music) return;
  // 已在播放同一首则不重复启动
  if(bgAudio && !bgAudio.paused && bgAudio.src.includes(MUSIC_LIST[musicIdx].file)) return;
  sfx.init(); // 确保 audioCtx 激活（解锁自动播放）
  if(!bgAudio){ bgAudio=new Audio(); bgAudio.loop=true; bgAudio.preload='auto'; }
  bgAudio.src=`./assets/music/${MUSIC_LIST[musicIdx].file}?v=${CACHE_VER}`;
  bgAudio.volume = (settings.volume/100)*0.55;
  bgAudio.play().catch(()=>{});
  updateMusicLabel();
}
function stopBgMusic(){ if(bgAudio){ bgAudio.pause(); } }
function switchMusic(idx){
  musicIdx = (idx+MUSIC_LIST.length)%MUSIC_LIST.length;
  localStorage.setItem('xxl-music-idx',musicIdx);
  if(bgAudio&&settings.music){ bgAudio.src=`./assets/music/${MUSIC_LIST[musicIdx].file}?v=${CACHE_VER}`; bgAudio.play().catch(()=>{}); }
  updateMusicLabel();
}
function updateMusicLabel(){ const el=$('musicLabel'); if(el) el.textContent=MUSIC_LIST[musicIdx].name; }

// ---------- 背景粒子 ----------
const bgCtx=bgParticles.getContext('2d'); let bgStars=[]; let bgStarRAF=null;
function initBgStars(){ bgStars=[]; for(let i=0;i<60;i++) bgStars.push({x:Math.random(),y:Math.random(),r:Math.random()*1.6+0.4,tw:Math.random()*Math.PI*2}); resizeBgCanvas(); }
function resizeBgCanvas(){ bgDpr=Math.min(window.devicePixelRatio||1, isMobile?1.25:1.5); bgParticles.width=innerWidth*bgDpr; bgParticles.height=innerHeight*bgDpr; bgParticles.style.width=innerWidth+'px'; bgParticles.style.height=innerHeight+'px'; }
function tickBgStars(){
  bgCtx.clearRect(0,0,bgParticles.width,bgParticles.height);
  if(document.documentElement.dataset.bg==='neon'){ for(const s of bgStars){ s.tw+=0.03; const a=0.3+Math.sin(s.tw)*0.3; bgCtx.globalAlpha=Math.max(0,a); bgCtx.fillStyle='#a78bfa'; bgCtx.beginPath(); bgCtx.arc(s.x*bgParticles.width,s.y*bgParticles.height,s.r*bgDpr,0,Math.PI*2); bgCtx.fill(); } }
  bgStarRAF=requestAnimationFrame(tickBgStars);
}
function syncBgStars(){
  const shouldRun = document.documentElement.dataset.bg==='neon' && settings.motion && !document.hidden && state!=='menu';
  if(shouldRun){ if(bgStarRAF===null){ bgStarRAF=requestAnimationFrame(tickBgStars); } }
  else { if(bgStarRAF!==null){ cancelAnimationFrame(bgStarRAF); bgStarRAF=null; } bgCtx.clearRect(0,0,bgParticles.width,bgParticles.height); }
}

// ---------- 主题/背景 ----------
function setTheme(t){
  document.documentElement.dataset.theme=t;
  $('themeBtn').innerHTML = ic(t==='light'?'moon':'sun');
  localStorage.setItem('xxl-theme',t);
}
function setBg(key){
  document.documentElement.dataset.bg=key.startsWith('photo')?'photo':key;
  if(key.startsWith('photo')){
    const idx = key==='photo1'?1:2;
    document.documentElement.style.setProperty('--bg-photo-url', `url('./assets/backgrounds/bg-anime-${idx}.webp?v=${CACHE_VER}')`);
  }
  bgIdx=BG_LIST.findIndex(b=>b.key===key);
  const cur=BG_LIST[bgIdx];
  $('bgBtn').innerHTML = ic(cur.icon);
  const mb=$('menuBg'); if(mb) mb.textContent = `背景 · ${cur.name}`;
  localStorage.setItem('xxl-bg',key);
  syncBgStars();
}
// 刷新资源: 清 SW 缓存 + 注销 SW + 强制 reload (普通用户无法 F12 清缓存的兜底)
function refreshAssets(){
  showToast('刷新资源中…');
  Promise.all(caches.keys().then(keys => keys.map(k => caches.delete(k))))
    .then(() => navigator.serviceWorker.getRegistrations())
    .then(rs => Promise.all(rs.map(r => r.unregister())))
    .then(() => setTimeout(() => location.reload(), 400))
    .catch(() => location.reload());
}
function cycleBg(){
  // 只在 2 张二次元图之间轮换
  const photos = BG_LIST.filter(b=>b.key.startsWith('photo'));
  const curKey = BG_LIST[bgIdx]?.key;
  const curPos = photos.findIndex(b=>b.key===curKey);
  const next = photos[(curPos+1)%photos.length];
  setBg(next.key); sfx.btn(); showToast('背景：'+next.name);
}

// ---------- 界面状态机 ----------
function showScreen(id){
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('show'));
  if(id) $(id).classList.add('show');
  document.documentElement.classList.toggle('menu-active',id==='screenMenu');
  document.documentElement.classList.toggle('game-active',id===null && state==='playing');
}
function showModal(id){ document.querySelectorAll('.modal').forEach(m=>m.classList.remove('show')); if(id) $(id).classList.add('show'); }
function hideAllModal(){ document.querySelectorAll('.modal').forEach(m=>m.classList.remove('show')); }

function gotoMenu(){
  state='menu'; showScreen('screenMenu'); hideAllModal();
  $('gameShell').hidden=true; stopBgMusic(); stopTimer(); timerExpired=false;
  sessionTimeMs=0; playStartTs=0;
  clearBoard(); combo=0; busy=false; clearSelection(); selected=null;
  syncBgStars();
  const unlocked=Math.min(SAVE.unlocked,LEVELS.length);
  $('menuContinue').querySelector('span').textContent = unlocked>1 ? `继续第 ${unlocked} 关` : '开始游戏';
  $('menuProgress').textContent = `${String(unlocked).padStart(2,'0')} / ${LEVELS.length}`;
}
function gotoLevels(){
  state='levels'; showScreen('screenLevels'); hideAllModal(); $('gameShell').hidden=true; renderLevelsGrid();
}
function renderLevelsGrid(){
  const grid=$('levelsGrid'); grid.innerHTML='';
  LEVELS.forEach((lv,i)=>{
    const unlocked=(i+1)<=SAVE.unlocked;
    const stars=SAVE.stars[lv.id]||0;
    const card=document.createElement('div'); card.className='level-card'+(unlocked?'':' locked');
    card.style.setProperty('--accent-c',ACCENT[i%4]);
    const starHtml=[0,1,2].map(k=>k<stars?ic('star','sm'):ic('starO','sm')).join('');
    const moveTxt = lv.moves===0?'无限步':'步';
    card.innerHTML=`<div class="lc-num">${lv.id}</div><div class="lc-name">${lv.name}</div><div class="lc-stars">${starHtml}</div><div class="lc-meta">${lv.moves===0?'∞ 步':lv.moves+' 步'}</div>${unlocked?'':'<div class="lc-lock">'+ic('lock','sm')+'</div>'}`;
    if(unlocked) card.onclick=()=>{ sfx.btn(); startLevel(i); };
    grid.appendChild(card);
  });
}

async function startLevel(idx){
  mode=M_CAMPAIGN; dailyRng=null; stopTimer(); timerExpired=false;
  $('movesLabel').textContent='步数';
  levelIdx=idx; currentLevel=LEVELS[idx];
  score=0; moves=currentLevel.moves; usedMoves=0; combo=0; busy=false;
  stats={clears:0,maxCombo:0,bombs:0,rainbows:0,rockets:0}; goalProgress={};
  state='intro'; showScreen('screenIntro');
  $('introNum').textContent=currentLevel.id; $('introName').textContent=currentLevel.name;
  $('introGoals').innerHTML=currentLevel.goals.map(g=>{const m=GOAL_META[g.t];return `<div>${ic(m.icon,'sm')} ${m.label} <b>${g.v}</b></div>`;}).join('') + (currentLevel.moves===0?'':'<div>'+ic('target','sm')+' '+currentLevel.moves+' 步内完成</div>');
  sfx.init(); await sleep(1600);
  state='playing'; showScreen(null); $('gameShell').hidden=false;
  bumpPlay(); timeStart();
  syncBgStars();
  levelPill.textContent=`Level ${currentLevel.id}`; levelNum.textContent=currentLevel.id; levelName.textContent=currentLevel.name;
  hintEl.textContent = `${currentLevel.name} · ${currentLevel.moves===0?'无限步数':currentLevel.moves+'步内'}完成目标`;
  await new Promise(r=>requestAnimationFrame(r)); await new Promise(r=>requestAnimationFrame(r));
  measure(); resizeFx();
  initBoard(); updateHUD();
  if(soundOn) startBgMusic();
}

function pauseGame(){ if(state!=='playing') return; state='paused'; clearHint(); timeFlush(); showModal('modalPause'); stopBgMusic(); if(mode===M_TIMED) stopTimer(); $('pauseEndBtn').hidden = mode!==M_ENDLESS; sfx.btn(); $('pauseVol').value=settings.volume; const pm=$('pauseMuteBtn'); if(pm){ pm.innerHTML=ic(soundOn?'sound':'mute'); pm.classList.toggle('off',!soundOn); } }
function resumeGame(){ if(state!=='paused') return; state='playing'; hideAllModal(); timeStart(); if(mode===M_TIMED) resumeTimer(); if(soundOn) startBgMusic(); sfx.btn(); scheduleHint(); }

function winLevel(){
  if(mode===M_DAILY){
    const prev=(dailyRecall()[todayKey()]||{}).score||0;
    const rank=(score>prev)?lbSubmit(M_DAILY,{score,maxCombo:stats.maxCombo}):0;
    dailyStash(score); unlockAchievement('daily_win'); stopTimer();
    showModeResult(M_DAILY,rank,true);
    return;
  }
  if(mode!==M_CAMPAIGN){ finishMode(); return; }
  recordEnd(); bumpEnd(true);
  state='win'; stopBgMusic(); sfx.win(); confetti();
  const movesRatio = isInfiniteMoves() ? 0.5 : moves/Math.max(1,currentLevel.moves);
  let stars=1; if(movesRatio>=0.3) stars=2; if(movesRatio>=0.5) stars=3;
  SAVE.saveStars(currentLevel.id,stars); SAVE.saveBest(currentLevel.id,score);
  if(levelIdx+1<LEVELS.length) SAVE.unlocked=Math.max(SAVE.unlocked,levelIdx+2);
  // 通关成就
  unlockAchievement('beat1');
  if(currentLevel.id>=6) unlockAchievement('beat6');
  if(levelIdx+1>=LEVELS.length) unlockAchievement('beat12');
  $('winScore').textContent=score;
  $('winStars').innerHTML=[0,1,2].map(i=>i<stars?ic('star','lg full'):ic('starO','lg empty')).join('');
  $('winStats').innerHTML=`消除方块 <b>${stats.clears}</b> · 最高连击 <b>×${stats.maxCombo}</b><br>生成炸弹 <b>${stats.bombs}</b> · 彩虹 <b>${stats.rainbows}</b> · 火箭 <b>${stats.rockets}</b>`;
  $('nextLevelBtn').style.display=(levelIdx+1<LEVELS.length)?'':'none';
  showModal('modalWin');
}
function loseLevel(){
  if(mode===M_DAILY){
    const prev=(dailyRecall()[todayKey()]||{}).score||0;
    const rank=(score>prev)?lbSubmit(M_DAILY,{score,maxCombo:stats.maxCombo}):0;
    dailyStash(score); stopTimer();
    showModeResult(M_DAILY,rank,false);
    return;
  }
  recordEnd(); bumpEnd(false);
  state='lose'; stopBgMusic(); sfx.lose();
  if(Q.shake){ appEl.classList.add('shake'); setTimeout(()=>appEl.classList.remove('shake'),350); }
  const gap=currentLevel.target-score;
  $('loseScore').textContent=score;
  $('loseSub').textContent=`差 ${gap} 分达成目标，再来一次！`;
  showModal('modalLose');
}
function confetti(){ const colors=ACCENT; for(let i=0;i<70;i++){ particles.push({x:Math.random()*fxCanvas.width,y:-10*dpr,vx:(Math.random()-.5)*4*dpr,vy:(2+Math.random()*4)*dpr,life:1,decay:.006,size:(4+Math.random()*5)*dpr,color:colors[rnd(colors.length)],rot:Math.random()*Math.PI,vr:(Math.random()-.5)*.3}); } }

// ---------- 模式系统（无尽/限时/每日 + 本地排行榜） ----------
const LB_KEY={endless:'xxl-lb-endless',timed:'xxl-lb-timed',daily:'xxl-lb-daily'};
function lbGet(m){ try{ return JSON.parse(localStorage.getItem(LB_KEY[m])||'[]'); }catch(e){ return []; } }
function lbSubmit(m, obj){
  const list=lbGet(m);
  const entry={score:obj.score, combo:obj.maxCombo, ts:Date.now()};
  list.push(entry);
  list.sort((a,b)=> b.score-a.score || b.ts-a.ts);
  const top=list.slice(0,10);
  try{ localStorage.setItem(LB_KEY[m], JSON.stringify(top)); }catch(e){}
  return top.indexOf(entry)+1; // 0 = 未进榜
}
function dailyRecall(){ try{ return JSON.parse(localStorage.getItem('xxl-daily-results')||'{}'); }catch(e){ return {}; } }
function dailyStash(score){
  const r=dailyRecall(); const key=todayKey(); const prev=(r[key]&&r[key].score)||0;
  r[key]={score:Math.max(prev,score), ts:Date.now()};
  try{ localStorage.setItem('xxl-daily-results', JSON.stringify(r)); }catch(e){}
}
function fmtTs(ts){ const d=new Date(ts); return (d.getMonth()+1)+'/'+d.getDate()+' '+(d.getHours()<10?'0':'')+d.getHours()+':'+(d.getMinutes()<10?'0':'')+d.getMinutes(); }

// ---------- 计时器（限时模式） ----------
function startTimer(){ stopTimer(); timeLeftMs=TIME_TOTAL; timeBonusTotal=0; timerExpired=false; lastTick=Date.now(); timerInt=setInterval(timerTick,250); renderTimeUI(timeLeftMs); }
function stopTimer(){ if(timerInt){ clearInterval(timerInt); timerInt=null; } }
function resumeTimer(){ lastTick=Date.now(); if(!timerInt) timerInt=setInterval(timerTick,250); }
function timerTick(){
  const now=Date.now(); timeLeftMs-=now-lastTick; lastTick=now;
  if(timeLeftMs<=0){
    timeLeftMs=0; renderTimeUI(0); stopTimer(); timerExpired=true;
    if(state==='playing'&&!busy) finishMode();
    return;
  }
  renderTimeUI(timeLeftMs);
}
function renderTimeUI(ms){
  const s=Math.ceil(ms/1000), m=Math.floor(s/60);
  movesLeftEl.textContent=m+':'+String(s%60).padStart(2,'0');
  progressBar.style.width=(ms/TIME_TOTAL*100)+'%';
  progressText.textContent=Math.ceil(ms/1000)+' 秒';
  const st=movesLeftEl.closest('.hud-stat'); if(st) st.classList.toggle('low', s<=10);
}

// ---------- 模式启动 ----------
async function startMode(m){
  mode=m; dailyRng=null;
  score=0; moves=0; usedMoves=0; combo=0; busy=false;
  stats={clears:0,maxCombo:0,bombs:0,rainbows:0,rockets:0}; goalProgress={};
  currentLevel=null;
  if(m===M_DAILY){
    let h=0; const s=todayKey(); for(let i=0;i<s.length;i++) h=(Math.imul(31,h)+s.charCodeAt(i))|0;
    dailyRng=mulberry32(h>>>0);
    const target=3000+Math.floor(dailyRng()*3)*500;
    const dmoves=22+Math.floor(dailyRng()*7);
    currentLevel={ id:999, name:'每日挑战', target:target, moves:dmoves, goals:[{t:'score',v:target},{t:'combo',v:3}] };
  }
  timeBonusTotal=0; stopTimer();
  state='intro'; showScreen('screenIntro'); hideAllModal();
  const im={
    endless:{num:'∞',label:'ENDLESS',name:'无尽模式',goalTxt:'难度随分数提升 · 方块 4→6 种', goalIcon:'infinity' },
    timed:{num:'60s',label:'TIME ATTACK',name:'限时模式',goalTxt:'连击加时间 · 单局最高 +10 秒', goalIcon:'clock' },
    daily:{num:'今日',label:'DAILY',name:'每日挑战',goalTxt:'本机每日同题 · 步数内完成目标', goalIcon:'calendarDay' }
  }[m];
  $('introLabel').textContent=im.label; $('introNum').textContent=im.num; $('introName').textContent=im.name;
  if(m===M_DAILY&&currentLevel){
    $('introGoals').innerHTML=currentLevel.goals.map(g=>{ const gmm=GOAL_META[g.t]; return '<div>'+ic(gmm.icon,'sm')+' '+gmm.label+' <b>'+g.v+'</b></div>'; }).join('')+(currentLevel.moves===0?'':'<div>'+ic('target','sm')+' '+currentLevel.moves+' 步内完成</div>');
  } else {
    $('introGoals').innerHTML='<div>'+ic(im.goalIcon,'sm')+' '+im.goalTxt+'</div>';
  }
  sfx.init(); await sleep(1500);
  state='playing'; showScreen(null); $('gameShell').hidden=false;
  bumpPlay(); timeStart();
  syncBgStars();
  levelPill.textContent={endless:'无尽模式',timed:'限时模式',daily:'每日挑战'}[m];
  levelNum.textContent=im.num; levelName.textContent=im.name;
  $('movesLabel').textContent = m===M_TIMED?'倒计时':m===M_ENDLESS?'难度':'步数';
  hintEl.textContent={endless:'无尽模式 · 分数越高方块种类越多',timed:'限时模式 · 连击可加时间',daily:'每日挑战 · 步数内完成目标'}[m];
  if(m===M_DAILY){ renderGoals(); }
  else { goalsEl.innerHTML='<div class="goal-item"><div class="goal-icon">'+ic(im.goalIcon)+'</div><div class="goal-text">'+im.goalTxt+'</div></div>'; }
  await new Promise(r=>requestAnimationFrame(r)); await new Promise(r=>requestAnimationFrame(r));
  measure(); resizeFx();
  initBoard(); updateHUD();
  if(m===M_TIMED){ startTimer(); }
  if(soundOn) startBgMusic();
}

// ---------- 结算与遗弃 ----------
function finishMode(){
  if(state!=='playing'&&state!=='paused') return;
  const m=mode;
  stopTimer(); stopBgMusic(); confetti(); sfx.win();
  state='win';
  const rank=lbSubmit(m,{score,maxCombo:stats.maxCombo});
  showModeResult(m,rank,true);
}
function showModeResult(m, rank, win){
  state=(m===M_DAILY&&!win)?'lose':'win';
  recordEnd();
  if(m===M_DAILY) bumpEnd(win);
  stopTimer(); stopBgMusic();
  if(win){ sfx.win(); confetti(); } else { sfx.lose(); }
  const titles={endless:'无尽模式结算',timed:'时间到！',daily:win?'今日挑战完成':'挑战未完成'};
  $('modeEndTitle').textContent=titles[m];
  $('modeEndScore').textContent=score;
  $('modeEndStats').innerHTML='最高连击 <b>×'+stats.maxCombo+'</b> · 消除 <b>'+stats.clears+'</b>'+(stats.rockets>0?' · 火箭 <b>'+stats.rockets+'</b>':'')+(stats.bombs>0?' · 炸弹 <b>'+stats.bombs+'</b>':'')+(stats.rainbows>0?' · 彩虹 <b>'+stats.rainbows+'</b>':'');
  $('modeEndRank').innerHTML=rank>0? ic('trophy','inline')+' 历史第 <b>'+rank+'</b> 名':'未进入 TOP10';
  $('modeEndRetry').textContent = m===M_DAILY? '再战一次（保留最佳）' : '再来一局';
  showModal('modalModeEnd');
}

// ---------- 每日挑战弹窗 ----------
function openDailyModal(){
  $('dailyDate').textContent=new Date().toLocaleDateString('zh-CN',{year:'numeric',month:'long',day:'numeric',weekday:'long'});
  const best=(dailyRecall()[todayKey()]||{}).score||0;
  $('dailyBest').textContent=best?('今日最佳：'+best+' 分'):'今天还没挑战过';
  $('dailyGo').textContent=best?'再玩一次':'开始挑战';
  renderDailyStrip();
  showModal('modalDaily'); sfx.btn();
}
function renderDailyStrip(){
  const box=$('dailyStrip'); box.innerHTML='';
  const recall=dailyRecall(); const wk=['日','一','二','三','四','五','六'];
  for(let i=6;i>=0;i--){
    const d=new Date(); d.setDate(d.getDate()-i);
    const key=d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0');
    const rec=recall[key];
    const el=document.createElement('div'); el.className='daily-day'+(i===0?' today':'');
    el.innerHTML='<span>周'+wk[d.getDay()]+'</span><b>'+(rec?rec.score:'·')+'</b>';
    box.appendChild(el);
  }
}

// ---------- 排行榜弹窗 ----------
function openLeaderboard(){
  const box=$('lbSections'); box.innerHTML='';
  const meta={endless:['无尽模式','infinity'],timed:['限时模式','clock'],daily:['每日挑战','calendarDay']};
  for(const m in meta){
    const list=lbGet(m);
    const sec=document.createElement('div'); sec.className='lb-section';
    let rows='';
    if(list.length===0){ rows='<div class="lb-empty">暂无成绩，快去挑战吧</div>'; }
    else{
      list.forEach((e,i)=>{
        rows+='<div class="lb-row'+(i<3?' top'+(i+1):'')+'"><span class="lb-rank">'+(i+1)+'</span><span class="lb-score">'+e.score+'</span><span class="lb-meta">连击 ×'+e.combo+' · '+fmtTs(e.ts)+'</span></div>';
      });
    }
    sec.innerHTML='<div class="lb-head">'+ic(meta[m][1],'sm')+' '+meta[m][0]+'</div>'+rows;
    box.appendChild(sec);
  }
  showModal('modalLeaderboard'); sfx.btn();
}

// ---------- 模式绑定 ----------
document.getElementById('menuEndless').querySelector('.mode-ic').innerHTML=ic('infinity');
document.getElementById('menuTimed').querySelector('.mode-ic').innerHTML=ic('clock');
document.getElementById('menuDaily').querySelector('.mode-ic').innerHTML=ic('calendarDay');
document.getElementById('menuEndless').onclick=()=>{ sfx.init(); sfx.btn(); startMode(M_ENDLESS); };
document.getElementById('menuTimed').onclick=()=>{ sfx.init(); sfx.btn(); startMode(M_TIMED); };
document.getElementById('menuDaily').onclick=()=>{ openDailyModal(); };
document.getElementById('menuLeaderboard').onclick=()=>{ openLeaderboard(); };
document.getElementById('dailyGo').onclick=()=>{ hideAllModal(); sfx.init(); sfx.btn(); startMode(M_DAILY); };
document.getElementById('dailyClose').onclick=()=>{ hideAllModal(); };
document.getElementById('lbClose').onclick=()=>{ hideAllModal(); };
document.getElementById('modeEndRetry').onclick=()=>{ hideAllModal(); startMode(mode); };
document.getElementById('modeEndMenu').onclick=()=>{ hideAllModal(); gotoMenu(); };
document.getElementById('pauseEndBtn').onclick=()=>{ hideAllModal(); finishMode(); };
// ---------- 数据统计 + 成绩分享卡片 ----------
const STATS = {
  get(){ try{ return JSON.parse(localStorage.getItem('xxl-stats')||'null')||{}; }catch(e){ return {}; } },
  set(v){ try{ localStorage.setItem('xxl-stats', JSON.stringify(v)); }catch(e){} },
  bump(fn){ const s=STATS.get(); fn(s); STATS.set(s); },
};
let playStartTs=0, sessionTimeMs=0;
function timeStart(){ playStartTs=Date.now(); }
function timeFlush(){ if(playStartTs>0){ sessionTimeMs+=Date.now()-playStartTs; playStartTs=0; } }
function recordEnd(){ timeFlush(); STATS.bump(s=>{ s.totalTimeMs=(s.totalTimeMs||0)+sessionTimeMs; s.maxCombo=Math.max(s.maxCombo||0, stats.maxCombo); }); sessionTimeMs=0; }
function bumpPlay(){ STATS.bump(s=>{ s.plays=(s.plays||0)+1; s.byMode=s.byMode||{}; const bm=s.byMode[mode]=s.byMode[mode]||{}; bm.plays=(bm.plays||0)+1; }); }
function bumpEnd(win){ STATS.bump(s=>{ s.byMode=s.byMode||{}; const bm=s.byMode[mode]=s.byMode[mode]||{}; if(win){ s.wins=(s.wins||0)+1; bm.wins=(bm.wins||0)+1; } else { s.losses=(s.losses||0)+1; } }); }
function fmtDur(ms){ const m=Math.round(ms/60000); if(m<60) return m+' 分钟'; return Math.floor(m/60)+' 小时 '+(m%60)+' 分'; }

// ---------- 统计面板 ----------
function openStats(){
  const s=STATS.get();
  const total=s.totalTimeMs||0, plays=s.plays||0, wins=s.wins||0, losses=s.losses||0;
  const grid=$('statsGrid'); grid.innerHTML='';
  const cells=[
    ['总时长', fmtDur(total)],
    ['总局数', plays],
    ['胜率', (wins+losses)>0?Math.round(wins/(wins+losses)*100)+'%':'—'],
    ['总消除', totalClears],
    ['最高连击', '×'+(s.maxCombo||0)],
    ['星级', Object.keys(SAVE.stars).reduce((a,k)=>a+(+SAVE.stars[k]||0),0)+' / '+(LEVELS.length*3)],
  ];
  for(const [k,v] of cells){ const el=document.createElement('div'); el.className='stat-cell'; el.innerHTML='<span>'+k+'</span><b>'+v+'</b>'; grid.appendChild(el); }
  const bm=s.byMode||{};
  const mk=(m,l)=>{ const b=bm[m]||{}; const best=(lbGet(m)[0]||{}).score; return '<div class="stat-cell"><span>'+l+'</span><b>'+(b.plays||0)+' 局</b><small>'+(best?('最佳 '+best):'暂无成绩')+'</small></div>'; };
  $('statsModes').innerHTML='<span class="stats-h">模式战绩</span><div class="stats-mode-grid">'+mk('campaign','闯关模式')+mk('endless','无尽模式')+mk('timed','限时模式')+mk('daily','每日挑战')+'</div>';
  // 成就墙
  const ach=$('achGrid'); ach.innerHTML='';
  for(const a of ACHIEVEMENTS){
    const un=achState[a.id];
    const el=document.createElement('div'); el.className='ach-cell'+(un?'':' locked');
    el.innerHTML='<span class="a-ic">'+ic(a.icon,'sm')+'</span><b>'+a.name+'</b><small>'+(un?((new Date(un).getMonth()+1)+'/'+new Date(un).getDate()+' 解锁'):'未解锁')+'</small>';
    ach.appendChild(el);
  }
  showModal('modalStats'); sfx.btn();
}

// ---------- 成绩分享卡片 ----------
function shareCard(){
  const W=750, H=1200;
  const cv=document.createElement('canvas'); cv.width=W; cv.height=H;
  const c=cv.getContext('2d');
  const bg=c.createLinearGradient(0,0,W,H); bg.addColorStop(0,'#17203a'); bg.addColorStop(.55,'#11182b'); bg.addColorStop(1,'#0a0e1c');
  c.fillStyle=bg; c.fillRect(0,0,W,H);
  c.strokeStyle='rgba(78,205,196,.22)'; c.lineWidth=5;
  c.beginPath(); c.arc(W/2,380,235,0,Math.PI*2); c.stroke();
  c.strokeStyle='rgba(255,107,107,.16)';
  c.beginPath(); c.arc(W/2,380,292,0,Math.PI*2); c.stroke();
  for(let i=0;i<40;i++){ const a=Math.random()*Math.PI*2, r=280+Math.random()*420; c.fillStyle='rgba(255,255,255,'+(.02+Math.random()*.08)+')'; c.beginPath(); c.arc(W/2+Math.cos(a)*r,380+Math.sin(a)*r,1.5+Math.random()*2.5,0,Math.PI*2); c.fill(); }
  c.textAlign='center';
  c.fillStyle='rgba(255,255,255,.6)'; c.font='600 26px "PingFang SC","Microsoft YaHei",sans-serif';
  c.fillText('HUANRUI MATCH-3', W/2, 90);
  c.fillStyle='#ffffff'; c.font='900 62px "PingFang SC","Microsoft YaHei",sans-serif';
  c.fillText('桓睿消消乐', W/2, 162);
  const modeTxt={campaign:(currentLevel&&currentLevel.name)||'闯关模式',endless:'无尽模式',timed:'限时模式',daily:'每日挑战'}[mode]||'闯关模式';
  c.fillStyle='rgba(255,255,255,.78)'; c.font='600 30px "PingFang SC","Microsoft YaHei",sans-serif';
  c.fillText(modeTxt, W/2, 232);
  c.fillStyle='#ffd93d'; c.font='900 170px sans-serif';
  c.fillText(String(score), W/2, 452);
  c.fillStyle='rgba(255,255,255,.55)'; c.font='600 28px sans-serif';
  c.fillText('S C O R E', W/2, 500);
  c.strokeStyle='rgba(255,255,255,.16)'; c.beginPath(); c.moveTo(130,580); c.lineTo(W-130,580); c.stroke();
  const items=[
    ['最高连击', '×'+stats.maxCombo],
    ['消除方块', stats.clears],
    ['火箭', stats.rockets],
    ['日期', new Date().toLocaleDateString('zh-CN')],
  ];
  let y=690;
  for(const it of items){
    c.fillStyle='rgba(255,255,255,.55)'; c.textAlign='left'; c.font='600 28px "PingFang SC","Microsoft YaHei",sans-serif';
    c.fillText(it[0], W/2-160, y);
    c.fillStyle='#fff'; c.textAlign='right';
    c.fillText(String(it[1]), W/2+160, y);
    y+=96;
  }
  if(mode==='campaign'){
    const stars=SAVE.stars[currentLevel.id]||0;
    c.fillStyle='#ffd93d'; c.font='900 72px sans-serif'; c.textAlign='center';
    c.fillText('★'.repeat(stars)+'☆'.repeat(3-stars), W/2, 1000);
  }
  c.fillStyle='rgba(255,255,255,.38)'; c.font='400 24px "PingFang SC","Microsoft YaHei",sans-serif'; c.textAlign='center';
  c.fillText('Asternova Arcade · '+new Date().toLocaleDateString('zh-CN'), W/2, H-70);
  return cv;
}
function downloadCard(cv){
  const a=document.createElement('a');
  a.download='huanrui-score.png'; a.href=cv.toDataURL('image/png');
  document.body.appendChild(a); a.click(); a.remove();
  showToast('成绩卡片已保存');
}
function shareScore(){
  const cv=shareCard(); sfx.btn();
  if('undefined'!==typeof navigator&&navigator.share&&navigator.canShare){
    cv.toBlob(blob=>{
      if(!blob){ downloadCard(cv); return; }
      const file=new File([blob],'huanrui-score.png',{type:'image/png'});
      if(navigator.canShare({files:[file]})){
        navigator.share({files:[file], title:'桓睿消消乐成绩'}).catch(()=>downloadCard(cv));
      } else downloadCard(cv);
    },'image/png');
  } else { downloadCard(cv); }
}

document.getElementById('menuStats').onclick=()=>{ openStats(); };
document.getElementById('settingsStats').onclick=()=>{ openStats(); };
document.getElementById('statsClose').onclick=()=>{ hideAllModal(); };
document.getElementById('winShareBtn').onclick=()=>{ shareScore(); };
document.getElementById('modeEndShare').onclick=()=>{ shareScore(); };
// ---------- 事件绑定 ----------
$('brandBtn').onclick=()=>{ sfx.btn(); gotoMenu(); };
$('bgBtn').onclick=()=>cycleBg();
$('themeBtn').onclick=()=>{ setTheme(document.documentElement.dataset.theme==='light'?'dark':'light'); sfx.btn(); };
$('soundBtn').onclick=()=>toggleSound();
$('gameSoundBtn').onclick=()=>toggleSound();
$('pauseMuteBtn').onclick=()=>toggleSound();
$('pauseVol').oninput=e=>{ settings.volume=+e.target.value; settings.save(); if(masterGain) masterGain.gain.value=settings.volume/100; if(bgAudio) bgAudio.volume=(settings.volume/100)*0.55; };
$('pauseBtn').onclick=()=>pauseGame();
$('menuContinue').onclick=()=>{ sfx.init(); sfx.btn(); startBgMusic(); startLevel(Math.min(SAVE.unlocked-1,LEVELS.length-1)); };
$('menuLevels').onclick=()=>{ sfx.btn(); gotoLevels(); };
$('menuBg').onclick=()=>cycleBg();
$('menuRefresh').onclick=()=>refreshAssets();
$('menuSound').onclick=()=>toggleSound();
$('levelsBack').onclick=()=>{ sfx.btn(); gotoMenu(); };
$('resumeBtn').onclick=()=>resumeGame();
$('restartBtn2').onclick=()=>{ hideAllModal(); startLevel(levelIdx); };
$('pauseMenuBtn').onclick=()=>{ hideAllModal(); gotoMenu(); };
$('nextLevelBtn').onclick=()=>{ hideAllModal(); startLevel(levelIdx+1); };
$('winRetryBtn').onclick=()=>{ hideAllModal(); startLevel(levelIdx); };
$('winMenuBtn').onclick=()=>{ hideAllModal(); gotoMenu(); };
$('loseRetryBtn').onclick=()=>{ hideAllModal(); startLevel(levelIdx); };
$('loseMenuBtn').onclick=()=>{ hideAllModal(); gotoMenu(); };

function toggleSound(){
  settings.sfx=!settings.sfx; settings.music=settings.sfx; soundOn=settings.sfx; settings.save();
  // 同步所有静音按钮图标
  for(const id of ['soundBtn','gameSoundBtn','pauseMuteBtn']){ const el=$(id); if(el){ el.innerHTML=ic(soundOn?'sound':'mute'); el.classList.toggle('off',!soundOn); } }
  const ms=$('menuSound'); if(ms) ms.textContent=`音效 · ${soundOn?'开':'关'}`;
  if(!soundOn) stopBgMusic(); else if(state==='playing'&&settings.music) startBgMusic();
  syncSettingsUI();
  sfx.btn();
}

// 设置面板
function openSettings(){ showModal('modalSettings'); syncSettingsUI(); sfx.btn(); }
function syncSettingsUI(){
  $('setSfx').checked=settings.sfx; $('setMusic').checked=settings.music; $('setVol').value=settings.volume;
  $('setMotion').checked=settings.motion; $('setHaptic').checked=settings.haptic; $('setQuality').value=settings.quality;
  updateMusicLabel();
}
function applySettings(){
  if(masterGain) masterGain.gain.value=settings.volume/100;
  if(!settings.music) stopBgMusic(); else if(state==='playing'&&(!bgAudio||bgAudio.paused)) startBgMusic();
  if(bgAudio) bgAudio.volume=(settings.volume/100)*0.55;
  document.documentElement.classList.toggle('reduce-motion',!settings.motion);
  Q = QUALITY_PRESETS[resolveQuality()];
  if(!$('gameShell').hidden){ resizeFx(); }
  syncBgStars();
  soundOn=settings.sfx;
  $('soundBtn').innerHTML=ic(soundOn?'sound':'mute'); $('soundBtn').classList.toggle('off',!soundOn); const gsb=$('gameSoundBtn'); if(gsb){ gsb.innerHTML=ic(soundOn?'sound':'mute'); gsb.classList.toggle('off',!soundOn); }
}
$('settingsBtn').onclick=()=>openSettings();
$('pauseSettingsBtn').onclick=()=>{ hideAllModal(); openSettings(); };
$('pauseBgBtn').onclick=()=>{ cycleBg(); };
$('settingsClose').onclick=()=>{ hideAllModal(); sfx.btn(); if(state==='playing'){ scheduleHint(); } else if(state==='paused'){ showModal('modalPause'); } };
$('setSfx').onchange=e=>{ settings.sfx=e.target.checked; settings.save(); soundOn=settings.sfx; applySettings(); sfx.btn(); };
$('setMusic').onchange=e=>{ settings.music=e.target.checked; settings.save(); applySettings(); sfx.btn(); };
$('setVol').oninput=e=>{ settings.volume=+e.target.value; settings.save(); if(masterGain) masterGain.gain.value=settings.volume/100; if(bgAudio) bgAudio.volume=(settings.volume/100)*0.55; };
$('setMotion').onchange=e=>{ settings.motion=e.target.checked; settings.save(); applySettings(); };
$('setHaptic').onchange=e=>{ settings.haptic=e.target.checked; settings.save(); if(settings.haptic) haptic(30); };
$('setQuality').onchange=e=>{ settings.quality=e.target.value; settings.save(); applySettings(); sfx.btn(); };
$('musicPrev').onclick=()=>{ switchMusic(musicIdx-1); sfx.btn(); };
$('musicNext').onclick=()=>{ switchMusic(musicIdx+1); sfx.btn(); };

let resizeTimer=null;
window.addEventListener('resize',()=>{ clearTimeout(resizeTimer); resizeTimer=setTimeout(()=>{ if(!$('gameShell').hidden){ measure(); resizeFx(); relayoutAll(); } resizeBgCanvas(); },100); });
// 棋盘尺寸变化时重设特效 canvas（仅在游戏中）
if('ResizeObserver' in window){ new ResizeObserver(()=>{ if(!$('gameShell').hidden) resizeFx(); }).observe(boardEl); }
function relayoutAll(){ for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){ const t=board[r]?.[c]; if(!t) continue; const{x,y}=posOf(r,c); t.el.style.width=t.el.style.height=tileSize+'px'; t.el.style.setProperty('--tx',x+'px'); t.el.style.setProperty('--ty',y+'px'); t.el.style.transform=`translate3d(${x}px,${y}px,${Z_TILE}px)`; } }
document.addEventListener('touchmove',e=>{ if(e.touches.length>1) e.preventDefault(); },{passive:false});
document.addEventListener('gesturestart',e=>e.preventDefault());
document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&(state==='playing'||state==='paused')){ state==='playing'?pauseGame():resumeGame(); } });

// ---------- 自定义皮肤（传图 + 1:1 裁剪 + IndexedDB 持久化） ----------
const SkinDB = (() => {
  const DB='xxl-skin-db', STORE='skins', KEY='custom', LS='xxl-skin';
  let dbp=null;
  function open(){
    if(dbp) return dbp;
    dbp=new Promise((res,rej)=>{
      if(!('indexedDB' in window)){ rej(new Error('no-idb')); return; }
      let req; try{ req=indexedDB.open(DB,1); }catch(e){ rej(e); return; }
      req.onupgradeneeded=()=>{ const db=req.result; if(!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE); };
      req.onsuccess=()=>res(req.result);
      req.onerror=()=>rej(req.error||new Error('idb-open-fail'));
      req.onblocked=()=>rej(new Error('idb-blocked'));
    });
    return dbp;
  }
  async function get(){
    try{
      const db=await open();
      const v=await new Promise((res,rej)=>{
        const tx=db.transaction(STORE,'readonly');
        const rq=tx.objectStore(STORE).get(KEY);
        rq.onsuccess=()=>res(rq.result||null);
        rq.onerror=()=>rej(rq.error);
      });
      if(v&&v.imgs&&Array.isArray(v.imgs)) return v;
      return lsGet();
    }catch(e){ return lsGet(); }
  }
  async function set(v){
    let ok=false;
    try{
      const db=await open();
      await new Promise((res,rej)=>{
        const tx=db.transaction(STORE,'readwrite');
        tx.objectStore(STORE).put(v,KEY);
        tx.oncomplete=()=>res(null);
        tx.onerror=()=>rej(tx.error);
      });
      ok=true;
    }catch(e){ ok=false; }
    return lsSet(v)||ok;
  }
  async function clear(){
    try{
      const db=await open();
      await new Promise((res)=>{
        const tx=db.transaction(STORE,'readwrite');
        tx.objectStore(STORE).delete(KEY);
        tx.oncomplete=()=>res(null);
        tx.onerror=()=>res(null);
      });
    }catch(e){}
    try{ localStorage.removeItem(LS); }catch(e){}
  }
  function lsGet(){ try{ return JSON.parse(localStorage.getItem(LS)||'null'); }catch(e){ return null; } }
  function lsSet(v){ try{ localStorage.setItem(LS,JSON.stringify(v)); return true; }catch(e){ return false; } }
  return { get:get, set:set, clear:clear };
})();

let skinSet=null;
const skinActiveFlag = ()=> localStorage.getItem('xxl-skin-active')==='custom';
const skinCustom = ()=> !!(skinSet&&skinSet.imgs&&skinSet.imgs.filter(Boolean).length===TYPES);
const skinActive = ()=> skinActiveFlag()&&skinCustom();
function faceSrcOf(i){ return skinActive()? skinSet.imgs[i] : FACE_IMG[i]; }
function predecodeFaces(){ for(let i=0;i<TYPES;i++){ const im=new Image(); im.src=faceSrcOf(i); if(im.decode) im.decode().catch(()=>{}); } }
async function loadSkin(){
  skinSet=await SkinDB.get();
  predecodeFaces();
}
function applySkinToBoard(){
  document.querySelectorAll('#board .tile img').forEach(img=>{
    const tile=img.closest('.tile'); if(!tile) return;
    img.src=faceSrcOf(tile.dataset.type|0);
  });
}

// 皮肤草稿（未应用前仅内存）
const cropDraft=[null,null,null,null];
const pendingSrc=[null,null,null,null];

async function decodeSource(file){
  let source=null;
  if('createImageBitmap' in window){
    try{ source=await createImageBitmap(file,{imageOrientation:'from-image'}); }catch(e){ source=null; }
  }
  if(!source){
    const url=URL.createObjectURL(file);
    try{
      const im=await new Promise((res,rej)=>{ const i=new Image(); i.onload=()=>res(i); i.onerror=()=>rej(new Error('bad-image')); i.src=url; });
      const cv=document.createElement('canvas'); cv.width=im.naturalWidth; cv.height=im.naturalHeight;
      cv.getContext('2d').drawImage(im,0,0); source=cv;
    }catch(e){ throw e; }
    finally{ URL.revokeObjectURL(url); }
  }
  // 源图上限 2048px 控内存
  const m=Math.max(source.width,source.height);
  if(m>2048){
    const k=2048/m;
    const cv=document.createElement('canvas'); cv.width=Math.max(1,Math.round(source.width*k)); cv.height=Math.max(1,Math.round(source.height*k));
    cv.getContext('2d').drawImage(source,0,0,cv.width,cv.height);
    source=cv;
  }
  // 归一化为 canvas（统一 width/height 语义）
  const out=document.createElement('canvas'); out.width=source.width; out.height=source.height;
  out.getContext('2d').drawImage(source,0,0);
  return out;
}

// ---------- 1:1 裁剪器 ----------
const crop=(()=>{
  const can=document.getElementById('cropCanvas'), ctx2=can.getContext('2d');
  const SIZE=360; can.width=SIZE; can.height=SIZE;
  let src=null, scale=1, ox=0, oy=0, slot=-1;
  let drag=null, pinch=null;
  const pts=new Map();
  function cover(){ return Math.max(SIZE/src.width, SIZE/src.height); }
  function clamp(){
    if(!src) return;
    const min=cover(); if(scale<min) scale=min;
    const max=Math.max(min*8,8); if(scale>max) scale=max;
    const w=src.width*scale, h=src.height*scale;
    ox=Math.min(Math.max(ox,SIZE-w),0);
    oy=Math.min(Math.max(oy,SIZE-h),0);
  }
  function draw(){
    ctx2.clearRect(0,0,SIZE,SIZE);
    ctx2.fillStyle='#10141f'; ctx2.fillRect(0,0,SIZE,SIZE);
    if(src) ctx2.drawImage(src,ox,oy,src.width*scale,src.height*scale);
  }
  function fitCenter(){ if(!src) return; scale=cover(); ox=(SIZE-src.width*scale)/2; oy=(SIZE-src.height*scale)/2; draw(); }
  function zoomAt(px,py,factor){
    if(!src) return;
    const old=scale; scale*=factor;
    ox=px-(px-ox)*(scale/old); oy=py-(py-oy)*(scale/old);
    clamp(); draw();
  }
  function open(i){ if(!pendingSrc[i]) return; slot=i; src=pendingSrc[i]; fitCenter(); showModal('modalCrop'); sfx.btn(); }
  function close(){ src=null; slot=-1; pts.clear(); drag=pinch=null; ctx2.clearRect(0,0,SIZE,SIZE); }
  function exportSquare(){
    const out=document.createElement('canvas'); out.width=512; out.height=512;
    const c=out.getContext('2d');
    c.fillStyle='#10141f'; c.fillRect(0,0,512,512);
    const k=512/SIZE;
    c.drawImage(src,ox*k,oy*k,src.width*scale*k,src.height*scale*k);
    return out.toDataURL('image/jpeg',.85);
  }
  function autoExport(sourceCanvas){
    const saved=src; src=sourceCanvas; fitCenter();
    const out=exportSquare(); src=saved;
    return out;
  }
  can.addEventListener('pointerdown',e=>{
    if(!src) return;
    e.preventDefault();
    try{ can.setPointerCapture(e.pointerId); }catch(_){}
    pts.set(e.pointerId,{x:e.offsetX,y:e.offsetY});
    can.classList.add('panning');
    if(pts.size===1){ drag={x:e.offsetX,y:e.offsetY,ox:ox,oy:oy}; pinch=null; }
    else{
      const arr=[...pts.values()], a=arr[0], b=arr[1];
      pinch={ d:Math.hypot(b.x-a.x,b.y-a.y), scale:scale, mid:{x:(a.x+b.x)/2,y:(a.y+b.y)/2}, ox:ox, oy:oy };
      drag=null;
    }
  });
  can.addEventListener('pointermove',e=>{
    if(!src||!pts.has(e.pointerId)) return;
    pts.set(e.pointerId,{x:e.offsetX,y:e.offsetY});
    if(pts.size===1&&drag){
      ox=drag.ox+(e.offsetX-drag.x); oy=drag.oy+(e.offsetY-drag.y);
      clamp(); draw();
    }else if(pts.size>=2&&pinch){
      const arr=[...pts.values()], a=arr[0], b=arr[1];
      const d=Math.hypot(b.x-a.x,b.y-a.y);
      const mid={x:(a.x+b.x)/2,y:(a.y+b.y)/2};
      scale=pinch.scale*(d/Math.max(1,pinch.d));
      const ix=(pinch.mid.x-pinch.ox)/pinch.scale, iy=(pinch.mid.y-pinch.oy)/pinch.scale;
      ox=mid.x-ix*scale; oy=mid.y-iy*scale;
      clamp(); draw();
    }
  });
  function up(e){
    if(!pts.has(e.pointerId)) return;
    pts.delete(e.pointerId);
    if(pts.size===1){ const p=[...pts.values()][0]; drag={x:p.x,y:p.y,ox:ox,oy:oy}; pinch=null; }
    if(pts.size===0){ can.classList.remove('panning'); drag=pinch=null; }
  }
  can.addEventListener('pointerup',up);
  can.addEventListener('pointercancel',up);
  can.addEventListener('wheel',e=>{
    if(!src) return;
    e.preventDefault();
    zoomAt(e.offsetX,e.offsetY, e.deltaY<0?1.12:0.9);
  },{passive:false});
  return { open:open, close:close, exportSquare:exportSquare, autoExport:autoExport, fitCenter:fitCenter, zoomAt:zoomAt, getSlot:()=>slot };
})();

// ---------- 皮肤弹窗 ----------
function renderSkinGrid(){
  const grid=document.getElementById('skinGrid'); grid.innerHTML='';
  for(let i=0;i<TYPES;i++){
    const slotEl=document.createElement('div'); slotEl.className='skin-slot';
    slotEl.style.setProperty('--ring-c',ACCENT[i]);
    const has=!!cropDraft[i];
    slotEl.innerHTML = '<div class="skin-preview">' + (has ? '<img src="'+cropDraft[i]+'" alt="">' : '<span class="skin-ph">'+ic('image')+'</span>') + '</div>' +
      '<div class="skin-row"><span class="skin-label">方块 '+(i+1)+'</span><span class="skin-state'+(has?' ok':'')+'">'+(has?'已就绪':'待上传')+'</span></div>' +
      '<div class="skin-actions">' +
        '<button class="mini-btn" data-act="pick" data-i="'+i+'">'+(has?'重传':'上传')+'</button>' +
        '<button class="mini-btn" data-act="crop" data-i="'+i+'"'+(pendingSrc[i]?'':' disabled')+'>裁剪</button>' +
      '</div>';
    grid.appendChild(slotEl);
  }
  document.getElementById('skinApply').disabled = cropDraft.filter(Boolean).length<TYPES;
}
function openSkinModal(){
  const cur = skinCustom()? skinSet.imgs.slice() : [null,null,null,null];
  for(let i=0;i<TYPES;i++){ cropDraft[i]=cur[i]; pendingSrc[i]=null; }
  renderSkinGrid();
  showModal('modalSkin');
  sfx.btn();
}
function pickSkinFile(i){
  const inp=document.createElement('input');
  inp.type='file'; inp.accept='image/*';
  inp.onchange=async()=>{
    const f=inp.files&&inp.files[0];
    if(!f) return;
    if(!f.type||f.type.indexOf('image/')!==0){ showToast('请选择图片文件'); return; }
    if(f.size>10*1024*1024){ showToast('图片不能超过 10MB'); return; }
    let src=null;
    try{ src=await decodeSource(f); }
    catch(e){ showToast('图片加载失败，换一张试试'); return; }
    pendingSrc[i]=src;
    crop.open(i);
  };
  inp.click();
}
function confirmCrop(){
  cropDraft[crop.getSlot()]=crop.exportSquare();
  crop.close();
  hideAllModal();
  showModal('modalSkin');
  renderSkinGrid();
  sfx.btn();
}
function autoCropRemaining(){
  let missing=0, doneCount=0;
  for(let i=0;i<TYPES;i++){
    if(cropDraft[i]) continue;
    if(!pendingSrc[i]){ missing++; continue; }
    cropDraft[i]=crop.autoExport(pendingSrc[i]);
    doneCount++;
  }
  renderSkinGrid();
  if(doneCount>0) sfx.btn();
  if(missing>0) showToast('还有 '+missing+' 个方块未上传照片');
  else if(doneCount===0&&cropDraft.filter(Boolean).length===TYPES) showToast('照片都已就绪');
  else if(doneCount===0) showToast('请先上传照片');
  else showToast('已自动裁剪 '+doneCount+' 张');
}
async function applySkin(){
  if(cropDraft.filter(Boolean).length<TYPES){ showToast('请先裁剪完 4 张照片'); return; }
  skinSet={v:1, imgs:cropDraft.slice(), ts:Date.now()};
  const ok=await SkinDB.set(skinSet);
  if(!ok) showToast('存储空间不足，皮肤仅本次生效');
  localStorage.setItem('xxl-skin-active','custom');
  applySkinToBoard();
  predecodeFaces();
  renderSkinGrid();
  sfx.btn();
  showToast('自定义皮肤已应用！');
}
function resetSkin(){
  localStorage.setItem('xxl-skin-active','default');
  applySkinToBoard();
  predecodeFaces();
  renderSkinGrid();
  sfx.btn();
  showToast('已恢复默认头像');
}

document.getElementById('menuSkin').onclick=()=>{ openSkinModal(); };
document.getElementById('settingsSkin').onclick=()=>{ openSkinModal(); };
document.getElementById('skinApply').onclick=()=>{ applySkin(); };
document.getElementById('skinAuto').onclick=()=>{ autoCropRemaining(); };
document.getElementById('skinReset').onclick=()=>{ resetSkin(); };
document.getElementById('skinClose').onclick=()=>{ hideAllModal(); };
document.getElementById('cropOk').onclick=()=>{ confirmCrop(); };
document.getElementById('cropCancel').onclick=()=>{ crop.close(); hideAllModal(); showModal('modalSkin'); renderSkinGrid(); };
document.getElementById('skinGrid').addEventListener('click',e=>{
  const btn=e.target.closest('button[data-act]'); if(!btn) return;
  const i=+btn.dataset.i, act=btn.dataset.act;
  if(act==='pick'){ sfx.btn(); pickSkinFile(i); }
  else if(act==='crop'&&pendingSrc[i]){ crop.open(i); }
  else if(act==='crop'){ showToast('先上传一张照片'); }
});
document.getElementById('cropOut').innerHTML=ic('zoomOut');
document.getElementById('cropIn').innerHTML=ic('zoomIn');
document.getElementById('cropFit').innerHTML=ic('fit');
document.getElementById('cropOut').onclick=()=>crop.zoomAt(180,180,.8);
document.getElementById('cropIn').onclick=()=>crop.zoomAt(180,180,1.25);
document.getElementById('cropFit').onclick=()=>crop.fitCenter();
// ---------- 启动 ----------
function start(){
  setTheme(themePref); setBg(bgPref);
  $('soundBtn').innerHTML=ic(soundOn?'sound':'mute'); $('soundBtn').classList.toggle('off',!soundOn); const gsb=$('gameSoundBtn'); if(gsb){ gsb.innerHTML=ic(soundOn?'sound':'mute'); gsb.classList.toggle('off',!soundOn); }
  $('pauseBtn').innerHTML=ic('pause'); $('levelsBack').innerHTML=ic('back');
  $('menuSound').textContent=`音效 · ${soundOn?'开':'关'}`;
  document.documentElement.classList.toggle('reduce-motion',!settings.motion);
  syncBgStars();
  initBgStars(); syncBgStars();
  musicIdx = Math.min(+localStorage.getItem('xxl-music-idx')||0, MUSIC_LIST.length-1);
  // 预解码方块图，避免首次交换/洗牌解码抖动
  predecodeFaces(); loadSkin();
  gotoMenu();
}
start();

document.addEventListener('visibilitychange',()=>{ syncBgStars(); if(document.hidden){ stopParticleLoop(); if(state==='playing'&&mode===M_TIMED) pauseGame(); } });

})();
