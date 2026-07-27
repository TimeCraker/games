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
const SPECIAL = { NONE:0, BOMB:1, RAINBOW:2 };
// 资源版本号（部署时同步更新，强制刷新缓存）
const CACHE_VER = '2.20';
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
  { id:5,  name:'炸弹实验室', target:4000, moves:28, goals:[{t:'score',v:4000},{t:'bomb',v:2}] },
  { id:6,  name:'彩虹时刻',   target:4500, moves:26, goals:[{t:'score',v:4500},{t:'rainbow',v:1}] },
  { id:7,  name:'连击大师',   target:5000, moves:25, goals:[{t:'score',v:5000},{t:'combo',v:4}] },
  { id:8,  name:'极速通关',   target:4000, moves:20, goals:[{t:'score',v:4000}] },
  { id:9,  name:'双重目标',   target:5500, moves:24, goals:[{t:'score',v:5500},{t:'bomb',v:3}] },
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
const rnd=n=>Math.floor(Math.random()*n);
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
  if(special===SPECIAL.BOMB) el.classList.add('special-bomb');
  if(special===SPECIAL.RAINBOW) el.classList.add('special-rainbow');
  el.dataset.r=r; el.dataset.c=c; el.dataset.type=type;
  const face=document.createElement('div'); face.className='face';
  const img=document.createElement('img'); img.src=FACE_IMG[type]; img.draggable=false; img.alt='';
  img.onerror=()=>{ face.style.background=ACCENT[type]; };
  face.appendChild(img);
  const ring=document.createElement('div'); ring.className='ring';
  const corner=document.createElement('div'); corner.className='corner'; corner.textContent=type+1;
  el.appendChild(face); el.appendChild(ring); el.appendChild(corner);
  if(special!==SPECIAL.NONE){ const badge=document.createElement('span'); badge.className='badge'; badge.innerHTML=ic(special===SPECIAL.BOMB?'bomb':'rainbow'); el.appendChild(badge); }
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
      let type; do{ type=rnd(TYPES); }while(createsMatch(r,c,type));
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
    const otherType=(a.special===SPECIAL.RAINBOW?b:a).type;
    const targets=[];
    for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++) if(board[r][c]&&(board[r][c].type===otherType||board[r][c]===rainbow)) targets.push({r,c});
    if(targets.some(t=>board[t.r][t.c]?.special===SPECIAL.BOMB)) sfx.bomb();
    await removeCells(targets,{rainbow:true});
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
  usedMoves++;
  if(!isInfiniteMoves()) moves--;
  busy=false; updateHUD();
  if(checkGoalsMet()){ setTimeout(()=>winLevel(),500); return; }
  if(!isInfiniteMoves() && moves<=0){ setTimeout(()=>loseLevel(),600); return; }
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
  const out=[];
  for(const run of runs){
    if(run.len>=5){ const mid=run.cells[Math.floor(run.cells.length/2)]; out.push({r:mid.r,c:mid.c,type:run.type,special:SPECIAL.RAINBOW}); stats.rainbows++; goalProgress.rainbow=(goalProgress.rainbow||0)+1; unlockAchievement('make_rainbow'); }
    else if(run.len>=4){ const mid=run.cells[Math.floor(run.cells.length/2)]; out.push({r:mid.r,c:mid.c,type:run.type,special:SPECIAL.BOMB}); stats.bombs++; goalProgress.bomb=(goalProgress.bomb||0)+1; unlockAchievement('make_bomb'); }
  }
  if(combo>=2) goalProgress.combo=Math.max(goalProgress.combo||0,combo);
  return out;
}
function collectSpecialTriggers(set){ const extra=new Set(); for(const k of set){ const{r,c}=parseKey(k); const t=board[r][c]; if(t&&t.special!==SPECIAL.NONE) extra.add(k);} return extra; }
function expandSpecials(set){
  const result=new Set(set); const queue=Array.from(set); const seen=new Set(set);
  while(queue.length){ const key=queue.shift(); const{r,c}=parseKey(key); const t=board[r]&&board[r][c]; if(!t) continue;
    if(t.special===SPECIAL.BOMB){ for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++){ const nr=r+dr,nc=c+dc; if(!inBounds(nr,nc)) continue; const k=`${nr},${nc}`; if(!seen.has(k)){seen.add(k);result.add(k);queue.push(k);} } }
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
    for(let r=write;r>=0;r--){ const type=rnd(TYPES); const el=makeTile(r,c,type,SPECIAL.NONE);
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
  const col = sp===SPECIAL.RAINBOW?'#a78bfa':'#ff6b6b';
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
  movesLeftEl.textContent = isInfiniteMoves() ? '∞' : Math.max(0,moves);
  comboEl.textContent='×'+Math.max(1,combo);
  if(currentLevel){ const pct=Math.min(100,score/currentLevel.target*100); progressBar.style.width=pct+'%'; progressText.textContent=`${score} / ${currentLevel.target}`; }
  bestScoreEl.textContent=(currentLevel&&SAVE.best[currentLevel.id])||0;
  statClears.textContent=stats.clears; statCombo.textContent='×'+stats.maxCombo; statMoves.textContent=usedMoves;
  const movesStat=movesLeftEl.closest('.hud-stat'); if(movesStat){ movesStat.classList.toggle('low', !isInfiniteMoves() && moves<=3 && moves>0); }
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
    for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){ if(board[r][c]){ board[r][c].type=types[idx++]; board[r][c].el.dataset.type=board[r][c].type; board[r][c].el.className=`tile t${board[r][c].type}`; const img=board[r][c].el.querySelector('img'); if(img) img.src=FACE_IMG[board[r][c].type]; } }
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
    special:(sp)=>{ if(sp===SPECIAL.RAINBOW){ [523,659,784,1047].forEach((f,i)=>setTimeout(()=>tone(f,0.15,'triangle',0.2),i*50)); } else { tone(80,0.2,'sawtooth',0.3,2); noise(0.15,0.3); } },
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
  $('gameShell').hidden=true; stopBgMusic();
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
  levelIdx=idx; currentLevel=LEVELS[idx];
  score=0; moves=currentLevel.moves; usedMoves=0; combo=0; busy=false;
  stats={clears:0,maxCombo:0,bombs:0,rainbows:0}; goalProgress={};
  state='intro'; showScreen('screenIntro');
  $('introNum').textContent=currentLevel.id; $('introName').textContent=currentLevel.name;
  $('introGoals').innerHTML=currentLevel.goals.map(g=>{const m=GOAL_META[g.t];return `<div>${ic(m.icon,'sm')} ${m.label} <b>${g.v}</b></div>`;}).join('') + (currentLevel.moves===0?'':'<div>'+ic('target','sm')+' '+currentLevel.moves+' 步内完成</div>');
  sfx.init(); await sleep(1600);
  state='playing'; showScreen(null); $('gameShell').hidden=false;
  syncBgStars();
  levelPill.textContent=`Level ${currentLevel.id}`; levelNum.textContent=currentLevel.id; levelName.textContent=currentLevel.name;
  hintEl.textContent = `${currentLevel.name} · ${currentLevel.moves===0?'无限步数':currentLevel.moves+'步内'}完成目标`;
  await new Promise(r=>requestAnimationFrame(r)); await new Promise(r=>requestAnimationFrame(r));
  measure(); resizeFx();
  initBoard(); updateHUD();
  if(soundOn) startBgMusic();
}

function pauseGame(){ if(state!=='playing') return; state='paused'; clearHint(); showModal('modalPause'); stopBgMusic(); sfx.btn(); }
function resumeGame(){ if(state!=='paused') return; state='playing'; hideAllModal(); if(soundOn) startBgMusic(); sfx.btn(); scheduleHint(); }

function winLevel(){
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
  $('winStats').innerHTML=`消除方块 <b>${stats.clears}</b> · 最高连击 <b>×${stats.maxCombo}</b><br>生成炸弹 <b>${stats.bombs}</b> · 生成彩虹 <b>${stats.rainbows}</b>`;
  $('nextLevelBtn').style.display=(levelIdx+1<LEVELS.length)?'':'none';
  showModal('modalWin');
}
function loseLevel(){
  state='lose'; stopBgMusic(); sfx.lose();
  if(Q.shake){ appEl.classList.add('shake'); setTimeout(()=>appEl.classList.remove('shake'),350); }
  const gap=currentLevel.target-score;
  $('loseScore').textContent=score;
  $('loseSub').textContent=`差 ${gap} 分达成目标，再来一次！`;
  showModal('modalLose');
}
function confetti(){ const colors=ACCENT; for(let i=0;i<70;i++){ particles.push({x:Math.random()*fxCanvas.width,y:-10*dpr,vx:(Math.random()-.5)*4*dpr,vy:(2+Math.random()*4)*dpr,life:1,decay:.006,size:(4+Math.random()*5)*dpr,color:colors[rnd(colors.length)],rot:Math.random()*Math.PI,vr:(Math.random()-.5)*.3}); } }

// ---------- 事件绑定 ----------
$('brandBtn').onclick=()=>{ sfx.btn(); gotoMenu(); };
$('bgBtn').onclick=()=>cycleBg();
$('themeBtn').onclick=()=>{ setTheme(document.documentElement.dataset.theme==='light'?'dark':'light'); sfx.btn(); };
$('soundBtn').onclick=()=>toggleSound();
$('pauseBtn').onclick=()=>pauseGame();
$('menuContinue').onclick=()=>{ sfx.init(); sfx.btn(); startBgMusic(); startLevel(Math.min(SAVE.unlocked-1,LEVELS.length-1)); };
$('menuLevels').onclick=()=>{ sfx.btn(); gotoLevels(); };
$('menuBg').onclick=()=>cycleBg();
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
  settings.sfx=!settings.sfx; soundOn=settings.sfx; settings.save();
  $('soundBtn').innerHTML=ic(soundOn?'sound':'mute');
  $('soundBtn').classList.toggle('off',!soundOn);
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
  $('soundBtn').innerHTML=ic(soundOn?'sound':'mute'); $('soundBtn').classList.toggle('off',!soundOn);
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

// ---------- 启动 ----------
function start(){
  setTheme(themePref); setBg(bgPref);
  $('soundBtn').innerHTML=ic(soundOn?'sound':'mute'); $('soundBtn').classList.toggle('off',!soundOn);
  $('pauseBtn').innerHTML=ic('pause'); $('levelsBack').innerHTML=ic('back');
  $('menuSound').textContent=`音效 · ${soundOn?'开':'关'}`;
  document.documentElement.classList.toggle('reduce-motion',!settings.motion);
  syncBgStars();
  initBgStars(); syncBgStars();
  musicIdx = Math.min(+localStorage.getItem('xxl-music-idx')||0, MUSIC_LIST.length-1);
  // 预解码方块图，避免首次交换/洗牌解码抖动
  FACE_IMG.forEach(src=>{ const img=new Image(); img.src=src; img.decode&&img.decode().catch(()=>{}); });
  gotoMenu();
}
start();

document.addEventListener('visibilitychange',()=>{ syncBgStars(); if(document.hidden){ stopParticleLoop(); } });

})();
