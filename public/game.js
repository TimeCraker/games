/* ============================================================
   桓睿消消乐 v2 - 完整游戏版
   关卡系统 · 界面状态机 · 背景系统 · 增强动效音效
   ============================================================ */
(() => {
'use strict';

// ---------- 配置 ----------
const ROWS = 8, COLS = 8, TYPES = 4;
const SWAP_DUR = 260, REMOVE_DUR = 420, FALL_DUR = 320, GAP = 8, PAD = 10, SWIPE_THRESH = 0.35;
const FACE_IMG = ['./assets/faces/face0.jpg','./assets/faces/face1.jpg','./assets/faces/face2.jpg','./assets/faces/face3.jpg'];
const ACCENT = ['#ff6b6b','#4ecdc4','#ffd93d','#a78bfa'];
const SPECIAL = { NONE:0, BOMB:1, RAINBOW:2 };
const BG_LIST = [
  { key:'cloud', name:'云海白昼', icon:'🌅' },
  { key:'neon',  name:'赛博夜场', icon:'🌃' },
  { key:'photo', name:'桓睿舞台', icon:'🖼' },
];

// 关卡配置
const LEVELS = [
  { id:1, name:'初见桓睿',  target:800,  moves:24, goals:[{t:'score',v:800}] },
  { id:2, name:'连击训练',  target:1200, moves:22, goals:[{t:'score',v:1200},{t:'combo',v:3}] },
  { id:3, name:'炸弹实验室', target:1500, moves:20, goals:[{t:'score',v:1500},{t:'bomb',v:2}] },
  { id:4, name:'彩虹时刻',  target:1800, moves:18, goals:[{t:'score',v:1800},{t:'rainbow',v:1}] },
  { id:5, name:'桓睿大师局', target:2500, moves:16, goals:[{t:'score',v:2500},{t:'combo',v:4}] },
];
const GOAL_META = {
  score:  { icon:'⭐', label:'达到分数' },
  combo:  { icon:'🔥', label:'达成连击' },
  bomb:   { icon:'💣', label:'生成炸弹' },
  rainbow:{ icon:'🌈', label:'生成彩虹' },
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
let goalProgress={};  // 每个目标当前进度
let pointerStart=null, selected=null;
let bgIdx=0, soundOn=true;
let state='menu';  // menu|levels|intro|playing|paused|win|lose
let audioCtx=null, masterGain=null, bgOsc=null, bgGain=null;

// 存档
const SAVE = {
  get unlocked(){ return +localStorage.getItem('xxl-unlocked')||1; },
  set unlocked(v){ localStorage.setItem('xxl-unlocked', v); },
  stars: JSON.parse(localStorage.getItem('xxl-stars')||'{}'),
  best: JSON.parse(localStorage.getItem('xxl-best')||'{}'),
  saveStars(lvl,stars){ this.stars[lvl]=Math.max(this.stars[lvl]||0,stars); localStorage.setItem('xxl-stars',JSON.stringify(this.stars)); },
  saveBest(lvl,s){ this.best[lvl]=Math.max(this.best[lvl]||0,s); localStorage.setItem('xxl-best',JSON.stringify(this.best)); },
};
const themePref = localStorage.getItem('xxl-theme')||'light';
const bgPref = localStorage.getItem('xxl-bg')||'cloud';
const soundPref = localStorage.getItem('xxl-sound'); soundOn = soundPref===null?true:soundPref==='1';

// ---------- 工具 ----------
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const rnd=n=>Math.floor(Math.random()*n);
const inBounds=(r,c)=>r>=0&&r<ROWS&&c>=0&&c<COLS;
function showToast(msg,dur=1600){ toastEl.textContent=msg; toastEl.classList.add('show'); clearTimeout(showToast._t); showToast._t=setTimeout(()=>toastEl.classList.remove('show'),dur); }

// ---------- 尺寸 ----------
function measure(){
  const w=boardEl.clientWidth-PAD*2;
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
  if(special!==SPECIAL.NONE){ const badge=document.createElement('span'); badge.className='badge'; badge.textContent=special===SPECIAL.BOMB?'💣':'🌈'; el.appendChild(badge); }
  const {x,y}=posOf(r,c);
  el.style.setProperty('--tx',x+'px'); el.style.setProperty('--ty',y+'px');
  el.style.transform=`translate3d(${x}px,${y}px,8px)`;
  el.style.width=el.style.height=tileSize+'px';
  bindInput(el); boardEl.appendChild(el); return el;
}
function placeTile(t,r,c,animate=true){
  const {x,y}=posOf(r,c); t.el.dataset.r=r; t.el.dataset.c=c;
  t.el.style.setProperty('--tx',x+'px'); t.el.style.setProperty('--ty',y+'px');
  t.el.style.transform=`translate3d(${x}px,${y}px,8px)`;
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
  requestAnimationFrame(()=>{ boardEl.querySelectorAll('.tile').forEach((e,i)=>{
    e.style.transition='none'; e.style.opacity='0';
    setTimeout(()=>{ e.style.transition=''; e.classList.add('spawning'); e.style.opacity=''; setTimeout(()=>e.classList.remove('spawning'),450); },i*10);
  }); });
}
function createsMatch(r,c,type){
  if(c>=2&&board[r][c-1]?.type===type&&board[r][c-2]?.type===type) return true;
  if(r>=2&&board[r-1][c]?.type===type&&board[r-2][c]?.type===type) return true;
  return false;
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

  // 彩虹球
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
  usedMoves++; moves--; busy=false; updateHUD();
  // 检查胜利
  if(checkGoalsMet()){
    setTimeout(()=>winLevel(),500); return;
  }
  // 步数耗尽 -> 失败
  if(moves<=0){
    setTimeout(()=>loseLevel(),600); return;
  }
  // 死局检测
  if(!hasPossibleMove()){ showToast('没有可消除的组合，重新洗牌！'); setTimeout(shuffleBoard,600); }
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
function goalPct(g){
  const p=goalProgress[g.t]||0;
  if(g.t==='score') return Math.min(100,score/g.v*100);
  return Math.min(100,p/g.v*100);
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
    score+=gain; stats.clears+=toRemove.size; updateHUD();
    const center=centerOf(toRemove);
    floatText(center,`+${gain}`,combo>=2?'combo':'');
    if(combo>=2){ floatText({...center,dy:-34},`COMBO ×${combo}`,'combo big'); comboFlash(); }
    sfx.clear(combo);
    if([...toRemove].some(k=>{const{r,c}=parseKey(k);const t=board[r]&&board[r][c];return t&&t.special===SPECIAL.BOMB;})) sfx.bomb();
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
    if(run.len>=5){ const mid=run.cells[Math.floor(run.cells.length/2)]; out.push({r:mid.r,c:mid.c,type:run.type,special:SPECIAL.RAINBOW}); stats.rainbows++; goalProgress.rainbow=(goalProgress.rainbow||0)+1; }
    else if(run.len>=4){ const mid=run.cells[Math.floor(run.cells.length/2)]; out.push({r:mid.r,c:mid.c,type:run.type,special:SPECIAL.BOMB}); stats.bombs++; goalProgress.bomb=(goalProgress.bomb||0)+1; }
  }
  // 连击目标
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
    sfx.special(s.special); setTimeout(()=>el.classList.remove('spawning'),450);
    await sleep(60);
  }
}
async function removeCells(cells,opts={}){
  for(const {r,c} of cells){ const t=board[r]&&board[r][c]; if(!t) continue; spawnParticles(r,c,t.type,opts.rainbow); t.el.classList.add('removing'); }
  if(cells.length>=5){ appEl.classList.add('shake'); setTimeout(()=>appEl.classList.remove('shake'),350); }
  await sleep(REMOVE_DUR);
  for(const {r,c} of cells){ const t=board[r]&&board[r][c]; if(!t) continue; t.el.remove(); board[r][c]=null; }
}
async function dropAndFill(){
  const newTiles=[];
  for(let c=0;c<COLS;c++){ let write=ROWS-1;
    for(let r=ROWS-1;r>=0;r--){ if(board[r][c]){ if(r!==write){ board[write][c]=board[r][c]; board[r][c]=null; placeTile(board[write][c],write,c,true);} write--; } }
    for(let r=write;r>=0;r--){ const type=rnd(TYPES); const el=makeTile(r,c,type,SPECIAL.NONE);
      const startY=-(write-r+1)*cellUnit; el.style.transition='none'; el.style.transform=`translate3d(${c*cellUnit}px,${startY}px,8px)`;
      board[r][c]={type,special:SPECIAL.NONE,el}; newTiles.push({tile:board[r][c],r,c}); }
  }
  await sleep(20);
  for(const {tile,r,c} of newTiles){ tile.el.style.transition=''; placeTile(tile,r,c,true); }
  await sleep(FALL_DUR);
}

// ---------- 粒子 ----------
const ctx=fxCanvas.getContext('2d'); let particles=[]; let dpr=window.devicePixelRatio||1;
function resizeFx(){ dpr=window.devicePixelRatio||1; const rect=boardEl.getBoundingClientRect(); fxCanvas.width=rect.width*dpr; fxCanvas.height=rect.height*dpr; fxCanvas.style.width=rect.width+'px'; fxCanvas.style.height=rect.height+'px'; }
function spawnParticles(r,c,type,rainbow){
  const {x,y}=posOf(r,c); const cx=(x+tileSize/2+PAD)*dpr, cy=(y+tileSize/2+PAD)*dpr;
  const colors=rainbow?['#ff6b6b','#4ecdc4','#ffd93d','#a78bfa']:[ACCENT[type],'#ffffff'];
  const n=16;
  for(let i=0;i<n;i++){ const a=(Math.PI*2*i)/n+Math.random()*.4; const sp=(1.8+Math.random()*2.6)*dpr;
    particles.push({x:cx,y:cy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-1,life:1,decay:.018+Math.random()*.02,size:(3+Math.random()*4)*dpr,color:colors[i%colors.length],rot:Math.random()*Math.PI,vr:(Math.random()-.5)*.3}); }
  particles.push({ring:true,x:cx,y:cy,r:4*dpr,life:1,decay:.05,color:ACCENT[type]});
}
function tickParticles(){
  ctx.clearRect(0,0,fxCanvas.width,fxCanvas.height);
  particles=particles.filter(p=>{ p.life-=p.decay; if(p.life<=0) return false;
    if(p.ring){ p.r+=3*dpr; ctx.save(); ctx.globalAlpha=p.life*.6; ctx.strokeStyle=p.color; ctx.lineWidth=3*dpr; ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.stroke(); ctx.restore(); }
    else { p.x+=p.vx; p.y+=p.vy; p.vy+=.15*dpr; p.rot+=p.vr; ctx.save(); ctx.globalAlpha=p.life; ctx.translate(p.x,p.y); ctx.rotate(p.rot); ctx.fillStyle=p.color; ctx.fillRect(-p.size/2,-p.size/2,p.size,p.size); ctx.restore(); }
    return true; });
  requestAnimationFrame(tickParticles);
}
function comboFlash(){ const f=document.querySelector('.combo-flash')||(()=>{const d=document.createElement('div');d.className='combo-flash';document.body.appendChild(d);return d;})(); f.classList.remove('on'); void f.offsetWidth; f.classList.add('on'); }
function floatText(pos,text,cls=''){ const el=document.createElement('div'); el.className='float-text '+cls; el.textContent=text; el.style.left=(pos.x+PAD)+'px'; el.style.top=(pos.y+PAD+(pos.dy||0))+'px'; floatLayer.appendChild(el); setTimeout(()=>el.remove(),950); }
function centerOf(set){ let sx=0,sy=0,n=0; for(const k of set){const{r,c}=parseKey(k);const{x,y}=posOf(r,c);sx+=x+tileSize/2;sy+=y+tileSize/2;n++;} return {x:sx/n,y:sy/n}; }
const parseKey=k=>{const[r,c]=k.split(',').map(Number);return{r,c};};

// ---------- HUD ----------
function updateHUD(){
  scoreEl.textContent=score; bigScoreEl.textContent=score;
  movesLeftEl.textContent=Math.max(0,moves);
  comboEl.textContent='×'+Math.max(1,combo);
  if(currentLevel){ const pct=Math.min(100,score/currentLevel.target*100); progressBar.style.width=pct+'%'; progressText.textContent=`${score} / ${currentLevel.target}`; }
  bestScoreEl.textContent=(currentLevel&&SAVE.best[currentLevel.id])||0;
  statClears.textContent=stats.clears; statCombo.textContent='×'+stats.maxCombo; statMoves.textContent=usedMoves;
  // 步数低警告
  const movesStat=movesLeftEl.closest('.hud-stat'); if(movesStat){ movesStat.classList.toggle('low', moves<=3 && moves>0); }
  renderGoals();
}
function renderGoals(){
  if(!currentLevel) return;
  goalsEl.innerHTML='';
  for(const g of currentLevel.goals){
    const meta=GOAL_META[g.t]; const p=g.t==='score'?score:(goalProgress[g.t]||0);
    const done=g.t==='score'?score>=g.v:p>=g.v;
    const item=document.createElement('div'); item.className='goal-item'+(done?' done':'');
    item.innerHTML=`<div class="goal-icon">${meta.icon}</div><div class="goal-text">${meta.label}</div><div class="goal-progress">${Math.min(p,g.v)}/${g.v}</div>`;
    goalsEl.appendChild(item);
  }
}

// ---------- 输入 ----------
function bindInput(el){ el.addEventListener('pointerdown',onDown,{passive:false}); }
function onDown(e){
  if(busy||state!=='playing') return;
  if(e.pointerType==='mouse'&&e.button!==0) return;
  e.preventDefault();
  const el=e.currentTarget; const r=+el.dataset.r,c=+el.dataset.c;
  pointerStart={r,c,x:e.clientX,y:e.clientY,el};
  el.setPointerCapture&&el.setPointerCapture(e.pointerId);
  window.addEventListener('pointermove',onMove,{passive:false});
  window.addEventListener('pointerup',onUp,{once:true});
}
function onMove(e){
  if(!pointerStart) return;
  const dx=e.clientX-pointerStart.x, dy=e.clientY-pointerStart.y;
  if(Math.hypot(dx,dy)>tileSize*SWIPE_THRESH){
    let nr=pointerStart.r,nc=pointerStart.c;
    if(Math.abs(dx)>Math.abs(dy)) nc+=dx>0?1:-1; else nr+=dy>0?1:-1;
    const sr=pointerStart.r,sc=pointerStart.c; cleanupPointer(); trySwap(sr,sc,nr,nc);
  }
}
function onUp(e){
  if(!pointerStart) return;
  const dx=e.clientX-pointerStart.x, dy=e.clientY-pointerStart.y;
  if(Math.hypot(dx,dy)<tileSize*SWIPE_THRESH) handleTap(pointerStart.r,pointerStart.c);
  cleanupPointer();
}
function cleanupPointer(){ pointerStart=null; window.removeEventListener('pointermove',onMove); }
function handleTap(r,c){
  if(!selected){ selected={r,c}; board[r][c]?.el.classList.add('selected'); sfx.select(); return; }
  board[selected.r][selected.c]?.el.classList.remove('selected');
  if(selected.r===r&&selected.c===c){ selected=null; return; }
  if((Math.abs(selected.r-r)+Math.abs(selected.c-c))===1){ const s=selected; selected=null; trySwap(s.r,s.c,r,c); }
  else { selected={r,c}; board[r][c]?.el.classList.add('selected'); sfx.select(); }
}
function clearSelection(){ if(selected){ board[selected.r]?.[selected.c]?.el.classList.remove('selected'); selected=null; } }

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
    btn:()=>tone(660,0.06,'sine',0.12),
  };
})();

// 背景环境音（轻 pad loop）
function startBgMusic(){
  if(!soundOn||bgOsc) return; sfx.init(); const a=audioCtx;
  bgOsc=a.createOscillator(); bgGain=a.createGain(); const filt=a.createBiquadFilter(); filt.type='lowpass'; filt.frequency.value=600;
  bgOsc.type='sine'; bgOsc.frequency.value=130; bgGain.gain.value=0;
  bgOsc.connect(filt); filt.connect(bgGain); bgGain.connect(masterGain); bgOsc.start();
  bgGain.gain.linearRampToValueAtTime(0.04,a.currentTime+2);
  // 缓慢颤音
  const lfo=a.createOscillator(); const lfoG=a.createGain(); lfo.frequency.value=0.15; lfoG.gain.value=4; lfo.connect(lfoG); lfoG.connect(bgOsc.frequency); lfo.start();
  bgOsc._lfo=lfo;
}
function stopBgMusic(){ if(bgOsc){ try{ bgGain.gain.linearRampToValueAtTime(0,audioCtx.currentTime+0.5); bgOsc._lfo&&bgOsc._lfo.stop(); bgOsc.stop(audioCtx.currentTime+0.6);}catch(e){} bgOsc=null; bgGain=null; } }

// ---------- 背景粒子 ----------
const bgCtx=bgParticles.getContext('2d'); let bgStars=[];
function initBgStars(){ bgStars=[]; const n=60; for(let i=0;i<n;i++) bgStars.push({x:Math.random(),y:Math.random(),r:Math.random()*1.6+0.4,s:Math.random()*0.3+0.05,tw:Math.random()*Math.PI*2}); resizeBgCanvas(); }
function resizeBgCanvas(){ bgParticles.width=innerWidth*dpr; bgParticles.height=innerHeight*dpr; bgParticles.style.width=innerWidth+'px'; bgParticles.style.height=innerHeight+'px'; }
function tickBgStars(){
  bgCtx.clearRect(0,0,bgParticles.width,bgParticles.height);
  const show = document.documentElement.dataset.bg==='neon';
  if(show){ for(const s of bgStars){ s.tw+=0.03; const a=0.3+Math.sin(s.tw)*0.3; bgCtx.globalAlpha=Math.max(0,a); bgCtx.fillStyle='#a78bfa'; bgCtx.beginPath(); bgCtx.arc(s.x*bgParticles.width,s.y*bgParticles.height,s.r*dpr,0,Math.PI*2); bgCtx.fill(); } }
  requestAnimationFrame(tickBgStars);
}

// ---------- 主题/背景 ----------
function setTheme(t){ document.documentElement.dataset.theme=t; $('themeBtn').querySelector('.ico').textContent=t==='light'?'🌙':'☀️'; localStorage.setItem('xxl-theme',t); }
function setBg(key){ document.documentElement.dataset.bg=key; bgIdx=BG_LIST.findIndex(b=>b.key===key); const cur=BG_LIST[bgIdx]; $('bgBtn').querySelector('.ico').textContent=cur.icon; const mb=$('menuBg'); if(mb) mb.textContent='背景：'+cur.name; localStorage.setItem('xxl-bg',key); }
function cycleBg(){ setBg(BG_LIST[(bgIdx+1)%BG_LIST.length].key); sfx.btn(); showToast('背景：'+BG_LIST[(bgIdx+1)%BG_LIST.length===0?BG_LIST.length-1:bgIdx].name); }

// ---------- 界面状态机 ----------
function showScreen(id){ document.querySelectorAll('.screen').forEach(s=>s.classList.remove('show')); if(id) $(id).classList.add('show'); }
function showModal(id){ document.querySelectorAll('.modal').forEach(m=>m.classList.remove('show')); if(id) $(id).classList.add('show'); }
function hideAllModal(){ document.querySelectorAll('.modal').forEach(m=>m.classList.remove('show')); }

function gotoMenu(){
  state='menu'; showScreen('screenMenu'); hideAllModal(); $('gameShell').hidden=true; stopBgMusic();
  $('menuContinue').textContent = SAVE.unlocked>1 ? `继续闯关 (第${SAVE.unlocked}关)` : '开始游戏';
}
function gotoLevels(){
  state='levels'; showScreen('screenLevels'); renderLevelsGrid(); hideAllModal(); $('gameShell').hidden=true;
}
function renderLevelsGrid(){
  const grid=$('levelsGrid'); grid.innerHTML='';
  LEVELS.forEach((lv,i)=>{
    const unlocked = (i+1)<=SAVE.unlocked;
    const stars=SAVE.stars[lv.id]||0;
    const card=document.createElement('div'); card.className='level-card'+(unlocked?'':' locked');
    card.style.setProperty('--accent-c',ACCENT[i%4]);
    const starHtml='★★★'.split('').map((_,k)=>k<stars?'<span>★</span>':'<span class="empty">★</span>').join('');
    card.innerHTML=`<div class="lc-num">${lv.id}</div><div class="lc-name">${lv.name}</div><div class="lc-stars">${starHtml}</div>${unlocked?'':'<div class="lc-lock">🔒</div>'}`;
    if(unlocked) card.onclick=()=>{ sfx.btn(); startLevel(i); };
    grid.appendChild(card);
  });
}

async function startLevel(idx){
  levelIdx=idx; currentLevel=LEVELS[idx];
  score=0; moves=currentLevel.moves; usedMoves=0; combo=0; busy=false;
  stats={clears:0,maxCombo:0,bombs:0,rainbows:0}; goalProgress={};
  // 入场动画
  state='intro'; showScreen('screenIntro');
  $('introNum').textContent=currentLevel.id; $('introName').textContent=currentLevel.name;
  $('introGoals').innerHTML=currentLevel.goals.map(g=>{const m=GOAL_META[g.t];return `<div>${m.icon} ${m.label} ${g.v}</div>`;}).join('');
  sfx.init(); await sleep(1600);
  // 进入游戏
  state='playing'; showScreen(null); $('gameShell').hidden=false;
  levelPill.textContent=`Level ${currentLevel.id}`; levelNum.textContent=currentLevel.id; levelName.textContent=currentLevel.name;
  hintEl.textContent = `${currentLevel.name} · ${currentLevel.moves}步内完成目标`;
  await new Promise(r=>requestAnimationFrame(r)); measure(); resizeFx();
  initBoard(); updateHUD();
  if(soundOn) startBgMusic();
}

function pauseGame(){ if(state!=='playing') return; state='paused'; showModal('modalPause'); stopBgMusic(); sfx.btn(); }
function resumeGame(){ if(state!=='paused') return; state='playing'; hideAllModal(); if(soundOn) startBgMusic(); sfx.btn(); }

function winLevel(){
  state='win'; stopBgMusic(); sfx.win(); confetti();
  // 星级：剩余步数比例
  const movesRatio = moves/currentLevel.moves;
  let stars=1; if(movesRatio>=0.3) stars=2; if(movesRatio>=0.5) stars=3;
  SAVE.saveStars(currentLevel.id,stars); SAVE.saveBest(currentLevel.id,score);
  if(levelIdx+1<LEVELS.length) SAVE.unlocked=Math.max(SAVE.unlocked,levelIdx+2);
  // 渲染
  $('winScore').textContent=score;
  $('winStars').innerHTML = [0,1,2].map(i=>i<stars?'<span class="full">★</span>':'<span class="empty">★</span>').join('');
  $('winStats').innerHTML = `消除方块 <b>${stats.clears}</b> · 最高连击 <b>×${stats.maxCombo}</b><br>生成炸弹 <b>${stats.bombs}</b> · 生成彩虹 <b>${stats.rainbows}</b>`;
  $('nextLevelBtn').style.display = (levelIdx+1<LEVELS.length)?'':'none';
  showModal('modalWin');
}
function loseLevel(){
  state='lose'; stopBgMusic(); sfx.lose();
  appEl.classList.add('shake'); setTimeout(()=>appEl.classList.remove('shake'),350);
  const gap = currentLevel.target-score;
  $('loseScore').textContent=score;
  $('loseSub').textContent = `差 ${gap} 分达成目标，再来一次！`;
  showModal('modalLose');
}

function confetti(){ const colors=ACCENT; for(let i=0;i<70;i++){ particles.push({x:Math.random()*fxCanvas.width,y:-10*dpr,vx:(Math.random()-.5)*4*dpr,vy:(2+Math.random()*4)*dpr,life:1,decay:.006,size:(4+Math.random()*5)*dpr,color:colors[rnd(colors.length)],rot:Math.random()*Math.PI,vr:(Math.random()-.5)*.3}); } }

// ---------- 事件绑定 ----------
$('brandBtn').onclick=()=>{ sfx.btn(); gotoMenu(); };
$('bgBtn').onclick=()=>cycleBg();
$('themeBtn').onclick=()=>{ setTheme(document.documentElement.dataset.theme==='light'?'dark':'light'); sfx.btn(); };
$('soundBtn').onclick=()=>toggleSound();
$('pauseBtn').onclick=()=>pauseGame();
$('menuContinue').onclick=()=>{ sfx.init(); sfx.btn(); startLevel(Math.min(SAVE.unlocked-1,LEVELS.length-1)); };
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

function toggleSound(){ soundOn=!soundOn; localStorage.setItem('xxl-sound',soundOn?'1':'0'); $('soundBtn').classList.toggle('off',!soundOn); $('soundBtn').querySelector('.ico').textContent=soundOn?'🔊':'🔇'; const ms=$('menuSound'); if(ms) ms.textContent='音效：'+(soundOn?'开启':'关闭'); if(!soundOn) stopBgMusic(); else if(state==='playing') startBgMusic(); sfx.btn(); }

window.addEventListener('resize',()=>{ if(!$('gameShell').hidden){ measure(); resizeFx(); relayoutAll(); } resizeBgCanvas(); });
function relayoutAll(){ for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){ const t=board[r]?.[c]; if(!t) continue; const{x,y}=posOf(r,c); t.el.style.width=t.el.style.height=tileSize+'px'; t.el.style.setProperty('--tx',x+'px'); t.el.style.setProperty('--ty',y+'px'); t.el.style.transform=`translate3d(${x}px,${y}px,8px)`; } }
document.addEventListener('touchmove',e=>{ if(e.touches.length>1) e.preventDefault(); },{passive:false});
document.addEventListener('gesturestart',e=>e.preventDefault());
// 键盘：ESC 暂停
document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&(state==='playing'||state==='paused')){ state==='playing'?pauseGame():resumeGame(); } });

// ---------- 启动 ----------
function start(){
  setTheme(themePref); setBg(bgPref);
  $('soundBtn').classList.toggle('off',!soundOn); $('soundBtn').querySelector('.ico').textContent=soundOn?'🔊':'🔇';
  $('menuSound').textContent='音效：'+(soundOn?'开启':'关闭');
  initBgStars(); requestAnimationFrame(tickBgStars); requestAnimationFrame(tickParticles);
  gotoMenu();
}
start();

})();
