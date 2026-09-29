# UI Polish 审计台账（AUDIT）

> 永续循环目标：前端 UI 细节打磨（零人类参与）。每轮追加一节，最新在上。
> 截图与扫描 JSON 存临时目录：`%TEMP%\ui-polish-r1\`（不进仓库）。
> 站点：dev server `http://localhost:3311`（`npm run dev`，web-client 目录）。

---

## R7（2026-09-29）· 前端 Meta UI 风格打造轮

**主题**：把「前端」本体页面（首页 Hero / 登录）拉升到 STYLE.md §5 定稿语言的完成度水准。起因：用户明确本轮要的是「前端 UI 风格的打造」；两页基线与产品语言的差距集中在「白色 SaaS 胶囊按钮」与双语标注/HUD 母题缺失。
**方法**：design-skill（§12 项目级升级轮方法 + §11 模式库），风格词汇全部取自 STYLE.md §5 既有 token，不新造；dev `localhost:3000` 双视口基线/修后截图（`%TEMP%\ui-polish-r6\r7-*.png`）。
**范围边界**：/lobby 受登录墙（沿用「待后端凭据」口径）本轮不做视觉改动；游戏内页面不在本轮范围（R6 已覆盖其动效）。

### 改动矩阵

| 页面 · 元素 | 前值 | 后值 | 备注 |
| --- | --- | --- | --- |
| 首页 · 主 CTA | 白色圆角胶囊（generic SaaS 观感） | **双层壳纯白胶囊**：外圈半透明环 + 内芯白底 + 琥珀箭头唯一点缀；hover 外圈转琥珀 ring+光晕、箭头右移 | 用户先见琥珀 chamfer 版反馈「不如纯白」→ 回白底重设计，保留形态升级 |
| 首页 · hero 帽线 | 无 | `DEEP SPACE OBSERVATORY · 深空观测站` mono 双语 kicker + 琥珀侧发丝线（窄屏收字号+隐藏发丝线防断词） | design-skill §12.1 帽线图注，项目双语标注惯例 |
| 首页 · 分隔线 | via-white/35 | via-hud-accent/40 | 单一琥珀纪律 |
| 首页 · CTA 副标注 | 「登录后进入游戏大厅」 | + `· ENTER THE LOBBY` | 双语标注 |
| 首页 · 页脚（移动端） | 版权行被右下 BGM 盘遮挡 | `pb-20`（sm 恢复）避让 | 溢出复查 0px |
| 登录 · 主提交按钮 ×2（登录 / 登录·注册） | shadcn 白底 | `bg-hud-accent` + ink-900 文字 + 内高光，hover brightness-105 | 对齐暂停面板/结算 CTA 语言 |
| 登录 · 激活页签 ×2 | 白玻璃（实为基类 dark:data-active:bg-input/30） | 琥珀玻璃 `bg-hud-accent/15!` + `text-hud-accent-bright!` + 琥珀边/光晕 | v4 尾随 `!` 压过基类级联（页面级 override 曾被静默压制，改为显式 important） |
| 登录 · 面板 | 玻璃 + 顶部高光线 | + 琥珀四角括号母题（nebula Panel 同款，左上/右下） | HUD 签名语言落位 |

### 验证汇总

- lint 0 errors（存量 warning 不变）；dev 双视口截图前后对照齐备。
- **程序化断言**（截图在 IAB 节流环境会拿到冻结入场帧，故以 getComputedStyle 为准）：首页 CTA `bg rgb(216,163,60)` + `clip-path chamfer`（回白底后改为双层壳断言 `borderRadius 0→圆角` 由类检查覆盖）、kicker 文案/颜色 ✓；登录提交钮 `rgb(216,163,60)` ✓、激活页签 `bg amber/15 / text rgb(233,190,105)` ✓、角标 span ✓。
- 对比度抽查：kicker 琥珀/90 on ink ≈ 8.9:1 ✓；CTA ink-900 on 白 ≈ 17:1 ✓；登录钮同 ✓。遗留小项：CTA 副标注 white/50 在环亮区对比略降（沿袭基线处理，10px mono 注记，下轮候选 white/60）。
- **环境坑登记**：IAB 面板不可见时 rAF 节流 → framer 入场动画冻结在中途帧，截图呈「半透明/糊化」假象；用「轻推视口强制重合成 + JS 落定内联样式」取真实落定帧。结论性视觉判断一律以 computed style 断言为准。

### 剩余队列（R8+ 候选）

- [P2] lobby 登录后视觉审查（卡片群是否需要同轮琥珀语言统一；待凭据）。
- [P3] 首页 CTA 副标注 white/50→/60 对比复核；「忘记密码」hover 下划线仪式感。
- [P3] 首页标题「Text Scramble 终端解码」入场候选（§11 模式，观测台语言契合；待用户拍板是否加戏）。

---

## R6（2026-09-29）· 动效完成度审计与 game-feel 升级

**主题**：把 UI 从「静态好看」补到「有 game-feel 的丝滑」——一切展开/切换有曲线、三态齐备、数字有翻牌、锁定有反馈。美术风格零改动，只补动效与微交互。
**判据**：STYLE.md §5.4 token（`--ease-instrument` 微交互 / `--ease-cinematic` 进场；200/500/900/2600ms）+ `ui-polish/rules.md`（只 transform/opacity、禁线性缓动、焦点环=琥珀环）。
**方法**：全 React UI 组件静态代码审计（逐元素）+ 真实浏览器走查（IAB，桌面 1280×800 / 移动 390×844，dev `localhost:3000`，webpack）。
**证据**：`%TEMP%\ui-polish-r6\r6-before-*.png`（选关桌面/移动、对局 HUD、暂停面板入场中间帧+落定帧、merge 规则弹层、lobby 登录墙）。

### 打分表（修前，按 game-feel 重要性排序）

图例：✅ 有动画且合 token · ⚠️ 简陋（有反馈但缺态/缺曲线/瞬跳）· ❌ 瞬变/无反馈

| # | 屏幕 · 元素 | 现状 | 判级 | 证据（文件:行） |
| --- | --- | --- | --- | --- |
| 1 | 规则/开场弹层 `ArcadeEntry`（merge/star-dash/nebula 三游戏首屏） | 条件渲染直挂直卸，无任何进出动画 | ❌ | `arcade/ArcadeEntry.tsx:175-226` |
| 2 | STA 选关屏 · 卡片群 | 挂载即全部出现，无 stagger | ❌ | `shoot-them-all/ui/StaLevelSelect.tsx:49-87` |
| 3 | STA 选关屏 ↔ 对局切换 | AnimatePresence 已包但子组件非 motion，实际硬切 | ❌ | `shoot-them-all/StaRoot.tsx:335-339` |
| 4 | 共享结算 `ResultOverlay` · 分数/最高分 | 静态文本瞬跳，无 count-up（结算情绪核心） | ❌ | `ui/ResultOverlay.tsx:130-141` |
| 5 | 锁定关点击 | `disabled` + cursor 变化，无 shake 无提示 | ❌ | `StaLevelSelect.tsx:134,154,168-170` |
| 6 | nebula 商店按钮组（购买/直升/刷新） | 无 transition 属性、无 active、无 focus-visible，购买成功无反馈 | ❌ | `nebula-survivor/NebulaGame.tsx:426-452` |
| 7 | star-dash 底部动作钮 | 无 hover 变化、无 focus-visible，仅 active:scale-95 | ❌ | `star-dash/StarDashGame.tsx:1041-1073` |
| 8 | 加载屏 `GameLoadingScreen` | 整屏瞬变出现；百分比文字瞬跳 | ❌ | `ui/GameLoadingScreen.tsx:27-60` |
| 9 | STA 球托 · 空槽（×0）点击 | opacity 0.35 + disabled，无 shake/提示 | ❌ | `StaBallDock.tsx:90,103,112-124` |
| 10 | STA 球托 · 选中态 | 原地变边框色（无滑动过渡） | ⚠️ | `StaBallDock.tsx:134-136,149-155` |
| 11 | DynamicIsland · CLEAR 横幅切换 | 条件渲染硬切，缺 art bible 点名的交叉淡入淡出 | ⚠️ | `StaDynamicIsland.tsx:71-74` |
| 12 | 暂停面板 · 遮罩 | opacity 200ms 有，但无 backdrop-blur 渐入 | ⚠️ | `StaPausePanel.tsx:52-74`（入场 spring ✅，走查已证） |
| 13 | 暂停面板 · 主按钮 | `transition-transform` 不覆盖 hover:brightness-105（提亮瞬跳） | ⚠️ | `StaPausePanel.tsx:103` |
| 14 | HUD 比分 `RollingNumber` | 数位滚动 150ms ✅，但大跳分只按 ±1 格滚（跨位瞬跳） | ⚠️ | `ui/RollingNumber.tsx:26-31` |
| 15 | 选关 · CURRENT 卡 | 静态金边 + CURRENT 字样，无呼吸 | ⚠️ | `StaLevelSelect.tsx:146,272-276` |
| 16 | 选关 · 星星 | 静态 SVG，无 check-pop | ⚠️ | `StaLevelSelect.tsx:262-271` |
| 17 | nebula HUD 系统键 | hover/active 有，缺 focus-visible | ⚠️ | `nebula-survivor/ui/Hud.tsx:77` |
| 18 | nebula E 技冷却环 | conic-gradient 读数逐帧瞬跳 | ⚠️ | `nebula-survivor/ui/Hud.tsx:194-198` |
| 19 | BGM Dial 按钮 | 环读数/面板展开 ✅，Dial 本体无 hover/active | ⚠️ | `audio/LoopingBgmControl.tsx` |
| 20 | 结算 CRT 扫描线 | 静态叠层不闪动 | ⚠️ | `ui/ResultOverlay.tsx:78-86` |
| 21 | 暂停/教学条 ghost 按钮 | `transition-colors` 不覆盖 `active:scale`（按压缩放瞬跳，系统性） | ⚠️ | `StaPausePanel.tsx:115,127`、`StaTutorialBar.tsx:117-127`、`ui/GameBackButton.tsx:33` |
| 22 | STA 选关卡 hover/press/focus | translate-y + scale + 焦点环齐备 | ✅ | `StaLevelSelect.tsx:141,147` |
| 23 | 选关 Spotlight Border | 预烘焙渐变 + transform 跟随，200ms | ✅ | `StaLevelSelect.tsx:172-191` |
| 24 | 球托 Dock 放大 | 距离衰减 scale 1.35/1.09，180ms | ✅ | `StaBallDock.tsx:81-137` |
| 25 | DynamicIsland 胶囊变形/连击 pop | 220ms 变形 + scale pop 齐备 | ✅ | `StaDynamicIsland.tsx:58-66,130-151` |
| 26 | 教学条进出 | slide-up+fade 220ms，exit 有 | ✅ | `StaTutorialBar.tsx:98-104` |
| 27 | 结算浮层进出 | springSnappy 进出 + exit | ✅ | `ResultOverlay.tsx:72-95` |
| 28 | CLEAR/FAIL 节拍 | 380/300ms 节拍设计，尊重 reduced-motion | ✅ | `StaRoot.tsx:46-47,139-164` |

**已核对的良好面**：动效基建齐全（framer-motion 12 + `src/lib/motion.ts` token + globals.css reduced-motion 全局开关 + MotionConfig reducedMotion="user"），缺的是覆盖面不是轮子。

### 修复计划（本轮 commit 切分）

1. `feat(web-client)` 动效微件基建：globals.css keyframes（shake/呼吸环/check-pop）+ motion.ts stagger + `CountUpValue`
2. `feat(shoot-them-all)` 选关屏：stagger 入场 / CURRENT 呼吸描边 / 锁定卡 shake+提示 / 星星 pop / select↔game 真转场
3. `feat(shoot-them-all)` HUD：BallDock morphing 滑块 / CLEAR 交叉淡入 / 暂停遮罩 blur 渐入 / RollingNumber 大跳平滑 / transition 组合修复
4. `feat(web-client)` 共享：ArcadeEntry 进出动画 / ResultOverlay count-up + 统计行 stagger / 加载屏入场
5. `fix(web-client)` 按钮三态补全：nebula 商店 + HUD / star-dash / BGM Dial
6. `docs(asternova)` 台账 R6 修后对照 + rules.md 工艺补录

### 修复清单（R6 实施）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 弹层 | `arcade/ArcadeEntry.tsx` + 5 个挂载点（nebula×3 / merge / star-dash） | 条件渲染直挂直卸 → 遮罩 fade 200ms + 面板进场 500ms `--ease-cinematic`（drawer 上滑 / centered 缩放），exit 反向（挂载点补 AnimatePresence） | merge 实机编译 200；中间态截图见 `%TEMP%\ui-polish-r6\` |
| P1 | 选关屏 | `shoot-them-all/ui/StaLevelSelect.tsx` | 卡片挂载即全部出现 → stagger 入场（500ms cinematic，+30ms/张）+ header 同步入场 | **中间帧实拍**：`r6-after-sta-select-transition-mid.png`（01→02/03→04→05+ 级联清晰可见） |
| P1 | 屏间转场 | `StaRoot.tsx` + `StaHud.tsx` | select↔game 硬切 → 选关根节点接 AnimatePresence（exit fade+y 上行）+ HUD 淡入淡出 250ms | 同上中间帧（HUD 已淡出、选关级联进入） |
| P1 | 锁定反馈 | `StaLevelSelect.tsx` | 锁定卡 disabled 死响应 → aria-disabled + WAAPI shake ±3px 160ms + 「先通过第 N 关」提示浮层（200ms 进出，1.6s 自消） | 实拍 `r6-after-sta-locked-shake-tip.png`（浮层在位） |
| P1 | 结算数字 | `ui/ResultOverlay.tsx` + `arcade/ArcadeResult.tsx` + 新增 `ui/CountUpValue.tsx` | 分数/最高分瞬跳 → CountUpValue 翻牌（900ms `--duration-slow` + cinematic，0.25s 起随行入场）+ 统计行 stagger（+40ms/行） | lint 0 error + build 通过；**实机触发未复现**（见环境限制），挂下轮隔轮评审 |
| P2 | 选中态 | `shoot-them-all/ui/StaBallDock.tsx` | 选中原地变色 → morphing 滑块（琥珀环+底部指示条一体，x 弹簧 springSnappy） | 实拍 `r6-after-sta-game-dock-pill.png`（滑块在位） |
| P2 | 空槽反馈 | `StaBallDock.tsx` | ×0 死响应 → aria-disabled + WAAPI shake（composite:"add" 不扰 hover scale） | `document.getAnimations()` 抓到 160ms running 动画 ✓ |
| P2 | HUD 内容切换 | `ui/StaDynamicIsland.tsx` | CLEAR 横幅条件渲染硬切 → 与常规读数交叉淡入淡出 180ms（art bible §5 #10 点名项） | lint + build ✓ |
| P2 | 大跳分 | `ui/RollingNumber.tsx` | 列按「总位数-列序」key，跨千位整列重挂瞬跳 → 按「从右位次」key，既有列平滑滚动、新增高位列落位即现 | lint + build ✓ |
| P2 | 当前关表达 | `StaLevelSelect.tsx` + globals.css | CURRENT 静态金边 → `hud-breathe-ring` 呼吸描边（opacity 0.45↔1，2.6s ambient） | 落定态截图 `r6-after-sta-select-settled.png` |
| P3 | 加载屏 | `ui/GameLoadingScreen.tsx` | 整屏瞬变 → 入场 fade 300ms + spinner 外圈琥珀描线环（`hud-draw-ring` 900ms 单圈，SVG stroke 例外工艺） | dev 实拍（选关加载中画面） |
| P3 | 按钮三态 | `nebula/NebulaGame.tsx`（商店 4 钮 + 金币读数 pop + 面板入场）、`nebula/ui/Hud.tsx`（系统键 focus 环 + E 技冷却环 @property 平滑）、`star-dash/StarDashGame.tsx`（底栏 3 钮 hover+focus）、`audio/LoopingBgmControl.tsx`（Dial hover/active） | 无 transition/active/focus 缺失 → 三态齐备；商店面板 scale/slide 进场 | lint + build ✓；冷却环用 globals.css 注册的 `--nd-cd-progress`（@property），回零帧免过渡防倒转 |
| P3 | transition 组合 | `StaDynamicIsland` 暂停钮 / `StaPausePanel` 3 钮 / `StaTutorialBar` / `ui/GameBackButton.tsx` | `transition-colors`（或 transform）不覆盖 `active:scale` 按压瞬跳 → 统一 `transition-[...,scale]` + `--ease-instrument` | lint ✓ |
| P3 | 页签切换 | globals.css（`[data-slot="tabs-content"][data-state=active]`） | login 页签内容瞬切 → 全局 Radix Tabs 激活面板淡入上浮 250ms | build ✓（login 页可达已证） |

### 验证汇总

- `npm run lint`：0 errors（9 个存量 unused-vars warning，与本轮无关）· `npm run build`（Next 16 Turbopack）：全 12 页静态生成通过。
- **包体红线**：零新依赖；framer-motion 12 已在全部受影响路由的 chunk 图内（ArcadeEntry/GameLoadingScreen/BallDock 新增的 motion import 不引入新库代码）；`public/godot/` 50MB WASM git 零改动。全站 client chunks 合计 2.9MB/50 文件（Turbopack 产出，无对照基线，增量为本轮组件级 KB 级源码）。
- 实机走查（IAB，桌面 1280×800）：选关 stagger 中间帧、锁定卡 shake+提示、空槽 shake（getAnimations 证实 160ms WAAPI）、球托滑块、选关↔对局转场全部实拍通过；暂停面板入场 spring（修前已证，本轮保留）；视觉风格零偏离（对照 `r6-before/after-sta-select-*.png` 同构图）。
- reduced-motion：全部新增动效走 framer `MotionConfig reducedMotion="user"`（StaRoot 已有）+ globals.css 全局 0.01ms kill switch 双保险；CSS 类（breathe/check-pop/draw-ring/fade-in-up）被 kill switch 自动覆盖。

### 环境限制（登记）

- **lobby 登录后走查仍不可行**：游客进入需邀请码、邮箱注册需真实验证码（沿用 R2 起的「待后端凭据」口径）；lobby 卡片动效本轮降级为 login 页签切换全局动效（见修复清单），lobby 卡片 stagger 挂剩余队列。
- **结算 count-up 实机触发未复现**：STA 走「5 球未达标→失败结算」路径时球体滞留球托下方沟底、落定判定不触发（见下方新登记引擎边角案例）；merge 堆球自动化未越过警戒线。CountUpValue 以代码级 + 编译验证收口，挂下轮隔轮评审实拍。
- 线上旧版 game.asterforge.top 为冻结展示态（BLUEPRINT.md:128），本轮不作为修前对照基准，修前证据一律取本地 HEAD。

### 新登记问题（非本轮引入）

- [P2·引擎] STA 球体可滞留球托下方沟底（y≈1240+），settle 判定不触发 → 本关永不判负/判胜，只能暂停退出。复现：第 1 关贴边发球使球落入 dock 下缘。疑 PhysicsWorld 边界/settle 检测未覆盖 dock 下缘区（`engine/PhysicsWorld.ts`）。

### 剩余队列（R7+ 候选）

- [P1] R6 隔轮评审：结算 count-up / CLEAR 交叉淡入 / 冷却环平滑的实机截图复核（需可复现的结算触发路径）。
- [P2] lobby 登录后全量审计 + 卡片 stagger（待凭据/后端，原 R2 遗留）。
- [P2] 上表 STA 引擎球体滞留边角案例（交引擎侧轮次）。
- [P3] 结算 CRT 扫描线静态叠层的微动效候选（本轮判 ⚠️ 保留）。
- [P3] xiaoxiaole（vanilla iframe）内部动效（iframe 壳既定不动）。

---

## R2（2026-09-24）· 隔轮评审 + 深扫 + 工艺轮

### 隔轮评审（R1 改动，截图证据）

| 对象 | 证据 | 结论 |
| --- | --- | --- |
| login main 包裹/命中区 | 几何验证：卡片中心 (720,480)=视口正中，表单可交互 | ✅ 无回归 |
| shoot floating 返回钮 | `r2-review-shoot.png`：左上真实尺寸 41px，品牌字右上完好 | ✅ |
| merge/nebula/star-dash 规则弹层 | `r2-review-merge.png` / `r2-review-nebula.png` / `r2-review-running.png`：弹层渲染完好、glass/排版未变 | ✅ |
| 主题锁定 | 全部截图均为深空黑 | ✅ |
| login 视觉取证 | framer 冻结致卡片不可见，强制解锁尝试无效 → 以几何验证替代（见 R1 踩坑 3） | ⚠️ 环境限制，登记 |

**结论：R1 全部改动通过隔轮评审，无 revert 项。**

### 修复清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 弹层 | `src/components/ui/ResultOverlay.tsx`（5 处结算共用） | 无 role/无陷阱 → 接 useDialogA11y（`closeOnEsc:false`，结算无关闭语义）+ role/aria-labelledby（useId） | lint 0 errors；调用方 nebula/nova-ball/arena 行为不变 |
| P2 | 深扫 | 8 路由 × 320/700、812×375 横屏、2560×1440 | 横向溢出全部 0px（脚本矩阵） | 脚本 ✓ |
| P2 | 工艺·一致性 | `src/components/nebula-survivor/NebulaSurvivorGame.tsx:552` | 弹层容器 1.5rem/440px/90dvh → 对齐统一配方 1.75rem/420px/88dvh-safe-area（merge 同款） | before/after 截图：`r2-review-nebula.png` → `r3-review-nebula.png`（下轮隔轮评审） |

### 保留 + 原因

- star-dash 规则弹层保留居中全圆角变体（`rounded-[2rem] p-6`）：其布局模式本就非底部抽屉，改响应式行为超出 token 统一范畴；玻璃/边框 token 已一致。已将两变体配方写入 rules.md §4。

### 验证汇总

- `npm run lint` 0 errors 1 warning（R1 保留项）· build OK。
- 极端视口（320×700 / 812×375 / 2560×1440）× 8 路由：横向溢出 0、document.title 唯一性不变。

### 剩余队列（R3+ 候选）

- [P1] login 重置弹层 / nebula、star-dash Esc 语义的端到端复验（真实浏览器环境，本环境 rAF 冻结限制）。
- [P2] iframe 壳内部页面 a11y（xiaoxiaole/arena 内嵌游戏本体）。
- [P2] 工艺：GameLoadingScreen / lobby（待后端可登录后）逐项节奏审查。
- [P3] 弱网 / 超长内容 / emoji 昵称边界深扫。

---

## R3（2026-09-24）· 登录交互深扫 + 隔轮评审 + 工艺轮

### 隔轮评审（R2 改动）

- nebula 弹层容器统一（1.75rem/420px/88dvh-safe-area）：`r3-review-nebula.png` 渲染干净、无截断、按钮完好 → **通过**。
- R1/R2 其余改动维持上轮评审结论。

### 深扫（登录页 = 唯一可完整交互的可达页面）

| 项 | 结果 |
| --- | --- |
| 空表单提交 | toast「请输入用户名/邮箱和密码」——原因明确 + 表单本身即出路 ✅ |
| 后端错误路径 | 生产 API（api.asterforge.top）真实 401 → toast「用户名或密码错误」error 态，表单有「忘记密码？」出路 ✅ |
| 超长输入（209 字符） | 无横向溢出、输入框不破卡 ✅ |
| Tab 顺序 | skip link 首位 → identifier → 忘记密码？→ password（与视觉序一致）✅ |
| 环境事实 | dev 的 `.env.local` 指向生产 API（既有配置，非本任务范围，不改） |

### 修复清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P3 | 工艺·字体 | `app/not-found.tsx:26` | 「SIGNAL LOST」用 `font-mono`（Geist Mono）→ `font-mono-data`（JetBrains Mono，全站数据 mono 约定） | 脚本 computed font ✓；before/after 截图 `r3-before-404.png` / `r3-after-404.png` |

### 保留 + 原因

- 404 页正文其余字体（标题 Orbitron、按钮 Geist Sans）与全站一致，无需改。

### 验证汇总

- lint 0 errors（1 保留 warning）· build OK · 8 路由 console/axe/溢出维持全绿。

### 剩余队列（R4+ 候选）

- [P1] login 重置弹层 / nebula、star-dash Esc 语义端到端复验（真实浏览器）。
- [P2] lobby 登录后全量审计（待 backend 可启动或提供测试凭据）。
- [P2] iframe 壳内部 a11y。
- [P3] GameLoadingScreen / nova-ball（无路由，藏于 lobby）。

---

## R5（2026-09-24）· 工艺轮：CTA 图形语言统一

### 隔轮评审（R4）

R4 无代码改动，无需评审。

### 修复清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P3 | 工艺·图标 | `app/not-found.tsx` CTA | 文本箭头「→」→ lucide `ChevronRight`（与首页「进入大厅」CTA 同图形语言），`aria-hidden` 保留 | 脚本：hasChevronSvg ✓ arrowTextGone ✓ 链接高 44px ✓；after 截图 `r5-after-404.png`（before：`r3-after-404.png`） |

### 验证汇总

- lint 0 errors（1 保留 warning）· build OK。

### 剩余队列（R6+ 候选）

- [P1] login 重置弹层 / nebula、star-dash Esc 语义端到端复验（真实浏览器）。
- [P2] lobby 登录后全量审计（待凭据/后端）。
- [P2] iframe 壳内部 a11y。
- [P3] 工艺候选：GameLoadingScreen 品牌一致性与节奏（可截图对象）。

---

## R4（2026-09-24）· 平板盲区扫描 + 隔轮评审

### 隔轮评审（R3 改动）

- 404 「SIGNAL LOST」换 JetBrains Mono：`r3-after-404.png` 渲染精致、与全站 mono 图形语言统一 → **通过**。
- 另证：左下「N」圆钮为 Next.js dev 工具角标（仅 dev 构建出现），排除出审计范围。

### 深扫（平板/方形视口补盲区：768×1024、1024×768、900×900 × 8 路由）

- 横向溢出：全部 0px。
- /login 在平板视口报告 2 个「小目标」＝已知已修的 返回首页/忘记密码（视觉盒 17px + 伪元素扩区 → 有效 45px；快速检查不计量伪元素），非回归。
- 其余路由 0 小目标。

### 修复清单

本轮无新增修复（硬验证轨全绿）。

### 剩余队列（R5+ 候选）

- [P1] login 重置弹层 / nebula、star-dash Esc 语义端到端复验（真实浏览器）。
- [P2] lobby 登录后全量审计（待凭据/后端）。
- [P2] iframe 壳内部 a11y。
- [P3] 工艺：404 CTA 箭头为文本「→」，home CTA 为 lucide 图标 —— 图形语言统一候选。

---


## R1（2026-09-24）· 全量基线轮

**范围**：9 路由 × 双视口（1440×900 / 375×812）脚本审计 + 人工截图复核。
**工具**：axe-core 4.x（页面注入，critical/serious 过滤）· 自研探针（有效对比度含 opacity 合成 / 触控目标 / 溢出 / 语义 / console）· IAB 浏览器截图。

### 前置：lint 归零（P0 工程项）

- [P1][工具链] `eslint.config.mjs`：8 个 error 全在 `public/godot/GoDot_game.js`（Godot 导出产物）→ `globalIgnores` 增 `public/**`。9 errors → 0 errors。
- [P2][类型] `app/arena/page.tsx:201` `contentWindow as any` → `{ startFight?: () => void } | null`；`catch (e)` → `catch {}`。
- 验证：`npm run lint` = 0 errors 1 warning（见「保留」）。

### 修复清单（按批次）

**批次一：主题锁定 + 全站键盘出口**

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P0 | 主题 | `app/layout.tsx:55` | `enableSystem`（浅色系统用户落入未设计浅色态：实测 `html.light` 时 body 白底 oklch(1 0 0)、hero 字 #f5f5ff 不可读） | `forcedTheme="dark"`；实测存 `theme=light` 后 reload 仍 `html.dark` ✓ | 浏览器 reload 实测 |
| P1 | 键盘 | `app/layout.tsx` | 全站无 skip link → fixed+translate 方案「跳到主内容」（首个 Tab 落点） | 脚本：activeElement 落点 ✓；点击跳转 activeElement=main ✓ |
| P1 | 语义 | `app/page.tsx:54` · `app/not-found.tsx:16` · `app/login/page.tsx` · `app/arena/page.tsx` | 无 `main#main-content` → 四页补 `<main id="main-content" tabIndex={-1}>` | 脚本 mainExists ✓ |
| P1 | 空态 | `app/arena/page.tsx:232` | `if (!canEnterArena) return null`（纯黑屏无出路）→ 「战斗舱未解锁」空态卡 + 前往登录/返回首页（均 min-h-11） | 脚本 hasLoginLink/hasHomeLink ✓ |

**批次二：弹层键盘可达性（新共享 hook）**

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 弹层 | `src/hooks/useDialogA11y.ts`（新增） | — | Esc + Tab 循环 + 移焦/还焦；latest-ref effect 写法（过 `react-hooks/refs`） |
| P1 | 弹层 | `src/components/merge/MergeGame.tsx` | 规则弹层无 Esc/陷阱 → 接 hook（Esc=知道了）；Game Over 弹层 → 接 hook（`closeOnEsc:false` 陷阱）+ role/aria-labelledby | 脚本：trapWrapped ✓ tabPrevented ✓ mergeDialogClosed ✓ |
| P1 | 弹层 | `src/components/nebula-survivor/NebulaSurvivorGame.tsx` | → 接 hook；Esc 语义沿用原逻辑（仅 pause/reference 可 Esc 关，briefing 须显式确认） | 与 merge 同构验证 |
| P1 | 弹层 | `src/components/star-dash/StarDashGame.tsx` | → 接 hook（Esc=确认并关闭） | 与 merge 同构验证 |
| P1 | 弹层 | `app/login/page.tsx` 重置弹层 | 无 role/无陷阱/无 Esc → 接 hook + `role="dialog"` + aria-labelledby + 初始焦点 reset-email | 脚本：初始焦点 ✓ Esc 处理器触发（defaultPrevented ✓，见「踩坑」3） |

**批次三：触控目标 + 语义**

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 触控 | `app/login/page.tsx` 返回首页/忘记密码 | 有效命中 17px → 45px（伪元素扩区，视觉不变） | 脚本 effectiveH=45 ✓ |
| P1 | 触控 | `src/components/ui/GameBackButton.tsx` | 24px（上轮）→ 命中区 48px（伪元素扩区）；`relative` 移入 base | 脚本 shoot 返回钮 boxH=41（floating 后）+pseudo=65 ✓ |
| P1 | 触控 | `src/components/shoot-them-all/StaRoot.tsx` | 返回钮随 StaGameShell `scale()` 缩到 21px → 移出缩放容器用 floating 变体（fixed 安全区左上，实高 41px）；品牌字留在壳内右上 | 脚本 fixed ✓ boxH=41 ✓ |
| P2 | 语义 | `app/xiaoxiaole/page.tsx` | 壳无 h1 → `<h1 class="sr-only">桓睿消消乐</h1>`（对齐四壳先例 19ccb6c） | 脚本 h1=桓睿消消乐 ✓ |
| P2 | 语义 | `src/components/merge/MergeGame.tsx:586` | 双 h1（页面 sr-only h1「AsterNova Merge」+ 面板 h1「Merge」）→ 面板降 h2 | 脚本 mergeH1 唯一 ✓ |
| P1 | 表单 | `app/login/page.tsx` 游客输入 | 仅 placeholder → `aria-label="游客邀请码"` | 脚本 guestNamed ✓ |
| P2 | 语义 | `app/arena/page.tsx` 授权视图 | 无 h1 → sr-only「竞技场对战」 | 脚本 h1 ✓ |

### 跳过 + 原因

- **/lobby 登录后内容**：backend 一期封存（CLAUDE.md「不部署不开发」），无凭据可登录；仅审计了未登录重定向到 /login 的行为。记覆盖缺口。
- **浅色主题逐页扫描**：修复后不存在浅色态（单主题），无需扫描。
- **断网 / 弱网 / 大数据列表 / 多语言边界**：列入 R2 深扫队列。

### 保留 + 原因

- 规则弹层 16×16 checkbox（merge/nebula/star-dash）：包在整行 `<label>` 内，有效目标 ≥40px，axe 无告警。
- `app/arena/page.tsx:173` `react-hooks/exhaustive-deps`（缺 userId）：补依赖会改变守卫时序，涉业务逻辑，保留并登记。
- 首页 header/footer/slogan `text-white/50`：有效对比度 ≈4.8:1 ≥ 4.5（上轮地板生效）。
- 游戏壳（五 Arcade）skip link 不落 `#main-content`：全屏画布壳无前置导航可跳，首个可聚焦元素即返回钮；无 main 的壳不强加 landmark。

### 验证汇总

- `npm run build` OK（Next 16.3.0，webpack）· `npm run lint` 0 errors 1 warning（保留项）。
- axe critical/serious：9 路由全部 0（home/login/merge/shoot/nebula/running/xiaoxiaole/404/arena-redirect）。
- 横向溢出：全部 0（merge 的 -10 为负值即无溢出）。
- console 错误：全路由 0（含 uncaught/unhandledrejection）。
- 主题：forcedTheme 实测生效（存 light → 仍 dark）。
- 对比度探针（含 opacity/alpha 合成）：全路由 0 违规（深色主题）。

### Commits（本仓库 push 含用户此前本地提交 bd59af7 一并推送）

1. `chore(web): eslint 忽略 public 导出产物，lint 归零 / ignore public artifacts for lint`
2. `fix(web): 锁定深空黑单主题并补全站 skip link 与主内容锚点 / lock dark-only theme, add sitewide skip link and main anchors`
3. `fix(web): arena 未就绪空态出口与 lint 类型修复 / arena not-ready empty state and lint type fixes`
4. `fix(web): 自绘弹层键盘可达性 hook 与四处接线 / dialog a11y hook with Esc and focus trap`
5. `fix(web): 关键路径触控 44px 与壳页语义 / 44px key-path hit areas and shell heading semantics`
6. `docs(ui-polish): 首轮审计台账与设计规则 / first-round audit ledger and UI rules`
- push 结果：✅ 一次成功（6672356..1c1fcaf → github.com/TimeCraker/games main，含用户此前本地提交 bd59af7）。

### 剩余队列（R2+ 候选）

- [P1] login 重置弹层 Esc/取消的**端到端**复验（本轮受 IAB rAF 冻结限制，仅逻辑级验证，见踩坑 3）。
- [P1] nebula/star-dash 弹层 Esc 语义逐项实测（与 merge 同构，未逐页跑）。
- [P2] merge Game Over 弹层与其它 ResultOverlay 族的焦点陷阱覆盖核查。
- [P2] iframe 壳（xiaoxiaole/arena）内页面本身的 a11y（跨 iframe 边界本轮未扫）。
- [P2] 工艺轮：lobby 卡片 hover 光晕呼吸时长统一（2.6s vs token 体系）、星象观测台 fine-grid 透明度节奏。
- [P3] 深扫轮：弱网（CDP 节流）/ 超长用户名与极端分数破版 / emoji 昵称截断。

### 踩坑

1. **IAB fullPage 截图拼接伪影**：fixed 背景层在长页截图重复渲染 → 一律分段滚动截图。
2. **IAB 截图 30s 超时**：WebGL 常驻动画（CinematicBlackHole rAF）致画面不稳定 → 截图前 `requestAnimationFrame = () => 0` + 冻结 CSS 动画，且**数据收集与截图必须分 cell**（超时会丢整个 cell 的结果）。
3. **IAB 标签页 rAF 永不触发**（`document.hasFocus()=false`、`:focus` 全体不匹配、framer-motion 入/退场冻结）：可见性能力 `set(true)` 也无效。后果：① 依赖 :focus 的样式无法在本环境验证；② AnimatePresence 关闭类交互只能逻辑级验证（Esc 处理器 defaultPrevented ✓ + 同 setter 的取消按钮路径同构）。真实浏览器不受影响。
4. **CUA 键盘事件在该环境不可达**（Escape/Tab 均无 keydown 到达）→ 键盘行为用页内 dispatchEvent + defaultPrevented/焦点落点判定。
5. Tailwind v4 的 `-translate-y-24` 编译为 `translate: 0px -96px` 属性（非 transform），调试时别用 `getComputedStyle().transform` 判断。
6. React Compiler lint（`react-hooks/refs`）禁止 render 期写 ref → latest-ref 模式必须写在 effect 里。

---
