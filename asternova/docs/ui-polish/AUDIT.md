# UI Polish 审计台账（AUDIT）

> 永续循环目标：前端 UI 细节打磨（零人类参与）。每轮追加一节，最新在上。
> 截图与扫描 JSON 存临时目录：`%TEMP%\ui-polish-r1\`（不进仓库）。
> 站点：dev server `http://localhost:3311`（`npm run dev`，web-client 目录）。
> **台账序列沿革（2026-10-05 归一）**：本表 R 序列之外，历史上曾有仓库根 `docs/ui-polish/` 的第二序列台账（原 R5–R13，2026-09-25 用户叫停后中断），已改名 **S5–S13** 归档至本文件末尾「S 序列归档」节；两序列 R6/R7 撞号，引用时注意区分。规则唯一现行源为 [rules.md](rules.md)。

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

---

# S 序列归档（原仓库根 docs/ui-polish 台账，2026-09-24 ~ 2026-09-25，用户叫停后归档并入本文件）

> 编号 S5–S13 = 原 R5–R13（第二序列打磨台账）。R1–R5 见上方第一序列历史节；因与本表 R6/R7 撞号，归档时整体加 S 前缀区分。2026-10-05 文档审计发现两套台账并存且编号冲突，根级 docs/ui-polish/ 已删除，其规则独有条目（媒体纪律 / 死样式纪律 / 时长 token 演进）已并入 [rules.md](rules.md)。原头部备注：截图与扫描 JSON 存 `.ui-polish/artifacts/`（不进仓库）；站点 `http://127.0.0.1:4105`（build + next start）；审查浏览器 Chrome 153 headless + CDP（9333）。


## S13（修复轮 · 目标暂停期间上线修复）· 首页 BGM 离站串场

### 问题

进入大厅后首页黑洞环境音仍在播放。根因：`LoopingBgmControl` 卸载时只任由 React 移除 `<audio>` DOM 节点，从无 `pause()`——被移出 DOM 的媒体元素不会自动暂停。

### 修复

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P0 | 音频 | `src/components/audio/LoopingBgmControl.tsx` | 两处遗漏 → ① 卸载 cleanup 显式 pause + 清 src/load；② portal 重建元素的 resolvedSrc cleanup 同步 pause 旧元素 | build/lint 绿；SPA 离站后 BGM 引用 disconnected+paused；4 路由烟扫 8/8 |

- rules.md 新增「媒体纪律」条款（pause-on-unmount，portal 重建先停旧元素）。
- 预期行为：离开首页黑洞 BGM 即止；进入大厅后点击任意处按既有设计启动大厅 BGM。

### Commits（本仓库）

1. `fix(web): BGM 离站串场——卸载与 portal 重建显式暂停 / pause BGM on unmount & portal rebuild`
2. `docs(ui-polish): S13 修复台账与媒体纪律 / S13 fix ledger and media-lifecycle rule`
- push：正常。

---

## S12（收尾轮）· 用户手动叫停 → 暂停打磨

### 隔轮评审（S11 改动）

- 死样式删除（gravity/pulse-scan）：全仓 grep 0 残留 + 本轮终态复扫通过 → **通过**。
- BGM 外环 ambient 令牌：计算样式 1.8s/2.6s 前后一致 → **通过，无 revert。**

### 未实施（因用户叫停，留作召回首项）

- `app/lobby/page.tsx:312-313` logo hover 旋摆 `duration: 0.5` 超 150–300ms 带 → 拟归 0.3s（WAAPI 取证脚本已备，临时目录）；规则依据 rules §6。
- 队列余项：sonner toast 时长语料、slow3G 首帧占位截图、xiaoxiaole SW 离线取证、弱网截图隔轮评审。

### 终态验证（本次收尾取证）

- 全量扫描 10 路由 × 双视口 = 20 组合：语义/布局/a11y/console **0 问题**（保留项不变：16×16 label checkbox、404 自身资源日志、merge 渐变按钮已裁定达标）。
- 最近全套记录：interact 33/33（S8）、edge 22/22（S9）、矩阵 tablet/wide/tiny 27 组合全绿（S9）。
- build/lint：基线 0 errors（1 条 R1 定案保留 warning）。

### Commits 累计

- 19 个 Conventional Commit（S5–S11）+ 本收尾台账提交，**全部已推送 origin/main 同步**。
- 站点与验证脚本、台账、规则文档全部入库；截图/扫描 JSON 存 `.ui-polish/artifacts`（不进仓库）。

### 结论

- 目标按用户指令暂停（永不停止条款的「手动叫停」出口）。环境（:4105 站点、CDP 浏览器、看护脚本）保持可用，随时可恢复继续 S12+。

---
## S11（本轮）· 轨 2 数据轮：死样式清理 + 恒等令牌化 + 深扫语料

### 隔轮评审（S10 改动）

- S10 光痕 0.88s→0.9s（--duration-slow）：计算样式复核 0.9s ✓；hover 截图对像素 diff 0.068%（局限在动画相位差，bbox 覆盖卡片行与黑洞画布，属环境动噪声非结构变化）→ **通过，无 revert。**

### 修复清单（轨 2）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P2 | 工艺·删繁就简 | `app/globals.css` | 死样式 2 处：`gravity-scan`（keyframes+class）、`pulse-scan`（keyframes）零组件引用 → 删除（rules 新增「死样式纪律」：无引用即删，删前 grep 取证） | 全仓 grep 0 残留；home 前后截图 diff 0.198%（黑洞画布动画噪声，结构零变化）；build ✓ |
| P2 | 工艺·恒等令牌 | `LoopingBgmControl.tsx` | BGM 外环提醒 ping `[animation-duration:2.6s]` 字面值 → `var(--duration-ambient)`（值恒等 2600ms，零视觉变化）；内环 1.8s 保留为差拍提醒环 | 计算样式前后均 1.8s/2.6s ✓ |
| P2 | 语料 | 数据采集 | login tabs 切换 transition 0.15s（150–300 带内），属性 color/bg/border/outline ✓；BGM 双环 1.8/2.6（保留差拍设计）；wide 第二行单卡左对齐栅格起点（723=gridLeft，正常网格流） | telemetry2 全部澄清 |

### 深扫（本轮轮空补偿项，全过）

- **超长文案注入**（120 字标题 + 120 字描述）：桌面卡高 319px / 移动 279px 纵向扩展，**双视口页面级横向溢出均为 0**，网格自适应完好。
- 回归扫描 4 路由 × 双视口 8/8 绿。

### 跳过 + 原因

- BGM 内环 1.8s 令牌化：双环差拍为既有提醒设计（无视觉评审模型可核验改动审美）→ 保留原样。
- 其余无。

### 保留 + 原因

- 见上（BGM 内环）；规则弹层 checkbox 等历史定案维持。

### 验证汇总

- build ✓ · lint：本项目触碰文件 0 errors（全仓仅历史保留 warning arena:173，本轮入口 exit-code 表现异常已隔离核实与改动无关）。
- 证据：`home-scan-before/after.png`、S10 hover 截图对（artifacts，不进仓库）。

### Commits（本仓库）

1. `style(web): 清理死样式 + BGM 提醒环挂 ambient 令牌 / remove dead styles, ambient-token the BGM ping ring`
2. `docs(ui-polish): S11 轨2数据轮台账与死样式纪律 / S11 craft-ledger and dead-style discipline`
- push 结果：正常。

### 剩余队列（S12+ 候选）

- [P2工艺] login 头像/logo hover 旋摆 0.5s 与 150–300 带的关系语料；Toaster(sonner) 入场时长语料。
- [P3] 弱网加载态截图评审（S9 已采证，转入隔轮评审材料）；首页黑洞画布在 slow3G 下的首帧占位样式。
- [P3] xiaoxiaole 内嵌页 service worker 缓存行为与 404 恢复路径取证。

### 踩坑（本轮）

1. 惯性操作：先给死样式做令牌化（gravity-scan 7s）→ grep 后发现元素已不存在（死类），随即改道为删除；令牌化前必须先验引用存在。
2. 一次成型脚本的括号计数目测不可靠 → 表达式写入前用平衡计数器+Function 编译双重校验（三次翻车后的规则）。
3. `[role=tab]` 语料首次在 lobby 采样为空 → 采样页面应为 login（数据页与断言页要一致）。

---

## S10（本轮）· 轨 2 工艺首轮：动效令牌归一 + 文案/排版语料采集

### 隔轮评审（S9 改动）

- S9 仅工具变更（web 零文件改动）；本轮回归扫描 6 路由 × 2 视口零回归，工具自愈续跑。**通过，无 revert。**
- 评审方式说明：本部署无视觉模型 → 轨 2 证据改用「计算样式前后值 + 同视口截图对 + 下轮数字复核」；本轮截图对已存 artifacts（见下）。

### 修复清单（轨 2 · 三件套齐全）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P2 | 工艺·动效令牌 | `app/globals.css` lobby 光痕 | `animation: lobby-enter-sheen 0.88s ease-out` 硬编码 → `var(--duration-slow)`（900ms，rules §6 既有「一次性装饰扫光」令牌） | 计算样式 0.88s → 0.9s；截图对 `lobby-hover-before/after.png`；hover 光晕/transition 值不变（0.3s 在 150–300 带内） |
| P2 | 工艺·规则补录 | `docs/ui-polish/rules.md` §6 | 无「一次性扫光」归属 → 补录：装饰扫光/电影感过渡挂 `--duration-slow` | — |

### 数据化语料（无码项，全数达标）

- **CTA 动词分布**（wide 采 2560）：进入×5 / 开始匹配 / 登录 / 返回大厅 / 知道了 / 开始任务 / 重新开始 —— 与 rules §6 动词清单一致，无近义动词散落。
- **大厅 wide 布局断言**：2560px 下 5 卡首行 4 卡（lg:grid-cols-4 生效），第 5 卡换行 —— 符合预期。
- **ResultOverlay 动效语料**（静态核查）：springSnappy / cinematicEase 双共享令牌 + closeOnEsc:false 语义，无裸 ease/时长散落。
- **hover 时序**：tile transition-duration 0.3s（150–300 带内 ✓）、呼吸 2.6s（--duration-ambient ✓）、光痕 0.9s（--duration-slow ✓）—— 三类动效三档令牌齐整。

### 跳过 + 原因

- 纯视觉审美项（饱和度/留白/字重微调）：无视觉评审模型可用，三件套 c 无法独立核验 → 依纪律跳过，不拍脑袋。

### 保留 + 原因

- `--duration-base: 500ms` 与 `--duration-slow` 邻接：用途分属「页面区块过渡」与「装饰扫光」，暂不变更层级（R2 已定）。光痕取 slow 是保守归一（0.88→0.9s 视觉近零差异）。
- 规则弹层 checkbox 等 R1 定案项维持。

### 验证汇总

- build ✓ · lint 基线 0 errors · 回归扫描 6 路由 × 双视口：landmark/溢出/跳档/重叠/console **0 回归**。
- 证据文件：`.ui-polish/artifacts/shots/lobby-hover-before.png` / `lobby-hover-after.png`（不进仓库）；计算样式前后值见上表。

### Commits（本仓库）

1. `style(web): 光痕时长归一 --duration-slow / normalize hover sheen to --duration-slow token`
2. `docs(ui-polish): S10 轨2首轮台账与规则补录`
- push 结果：本轮 push 正常（凭据恢复后的第二轮验证）。

### 剩余队列（S11+ 候选）

- [P2工艺] loopbgm ping 环（1.8s/2.6s 双频）入 ambient 令牌家族并一轮化。
- [P3] wide 档 5 卡换行留白比例断言（第 2 行单卡视觉重心）；loading 骨架/首帧截图评审。
- [P3] login 双 tab 切换动效时长语料（tabs transition 150ms?）。
- 待部署：同前。

### 踩坑（本轮）

- hover 态证据需真实指针：CDP Input.dispatchMouseEvent 悬停后取 :hover 匹配 + 光痕计算样式；直接 toggle class 无法触发 CSS :hover。
- wide 语料里 CTA 文本含卡片内部 span 文本，动词统计需按业务 CTA 元素级（span.enter-pill）采样，整卡 textContent 会混入标题。

---

## S9（本轮）· 视口矩阵 + 多档弱网 + 配方与网格节奏数据化

### 隔轮评审（S8 改动）

- S8 工具轮没有改 web 代码；整套件（扫描/interact/edge）复跑维持绿。**通过，无 revert。**

### 修复/新增清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P3 | 视口矩阵 | audit.mjs | 桌面/移动两档 → 增 tablet 768×1024 / wide 2560×1440 / tiny 320×568 | 9 路由 × 3 视口 = 27 组合全绿（仅保留项），横向溢出 0 |
| P3 | 弱网分档 | edge.mjs | 仅慢速 3G 档 → 增 3G(270ms/95KBps) 与 4G(60ms/366KBps) 档 | 新增 4/4 渲染完整（总 22/22） |
| P2 | 配方数据 | edge.mjs | login 重置弹层打开态未测 → 打开后实测：18px 圆角 / surface-2@90% / glass 边框 8% / blur40 / 430px / p-6 —— 与登录面自有 surface 变体一致 | 实测达标 |
| P2 | 网格节奏 | edge.mjs | 星象台 fine-grid 项长期挂队 → 数据化：首页主网格 64px 紫 0.07/青 0.05 线、登录细网格 24px 白 0.025 线 + 主网格降 0.6 透明度 —— 两级节奏为 R2 committed 决策，数值自洽 | 数据登记，保留设计 |
| P2 | 工具韧性 | audit/interact/edge | 浏览器掉线整轮报废 → 内建 CDP 健康计：死机按 S8 配方自动拉起并续跑 | 矩阵轮初即自愈续行，0 中断 |

### 跳过 + 原因

- 多语言（英文 locale）项：站点未做 i18n（单一 zh-CN），无英文版路由可测；新增 i18n 属新功能，默认禁止 → 关闭项并记录（title 模板联动已在每路由中文标题下持续验证）。
- push：本会话无凭据（SEC_E_NO_CREDENTIALS）×3 → 留本地。

### 保留 + 原因

- 规则弹层 16×16 checkbox（仍 6 处扫描 small=1）：R1 定案。
- merge 渐变按钮对比度：本轮矩阵三视口复核（知道了 7、再来一局 postModal 5.0–6.9）继续通过，非缺陷。
- nebula pausedUpgrade / ResultOverlay 配方语料：需真实对局中途状态，无后端的本地环境不可达 → 语料采集转为「设计插图态补充」待后端可跑时再录。

### 验证汇总

- web 侧零文件变更：build/lint 无需重跑（基线 0 errors）。
- audit：桌面/移动 20 组合 + 矩阵 27 组合全部绿。
- interact 33/33（S8 建）。edge 22/22。

### Commits（本仓库，累计 14 个本地提交未推送）

1. `待提交 test(ui-polish): 视口矩阵与多档弱网、配方与网格数据采集、浏览器自愈`
- push 结果：无凭据失败，留本地。

### 剩余队列（S10+ 候选）

- [P2] 工艺轮（轨 2 首轮）：细网格透明度节奏本作「保留」定案 → 转排 unlike 项：剩 lobby 卡片 hover 光晕 group-hover 版本时长数据化；星爆/结算 ResultOverlay 动效时长入令牌语料。
- [P3] 大视口行列：wide 档下 lobby 卡片 4 列换行与 hero 字号上限断言（本轮 wide 仅断言溢出，未断言孪生排布）。
- [P3] 弱网加载态截图证据（扫描 json 已含截图，属待下轮隔轮评审用）。
- 待部署：同前（无无人值守部署文档）。

### 踩坑（本轮）

1. 像素采样点落在视口外（tablet 底部工具栏半出视口）→ 采样坐标按「可视区裁剪」重算，避免截图边界夹取假数据。
2. 弹层遮挡判定一度被全屏 wrapper 矩形误导（几何判定把压在弹层下的元素误认作弹层自身）→ 改 DOM 祖先级 inDialogEl 判定，几何仅作旧数据回退。
3. 浏览器掉线造成整轮报废 → 三工具内建自愈；矩阵轮当场验证自愈路径（首行失败 → 拉起 → 27 组合全绿）。
4. grouping 断言失误（fine-grid 实际在登录页而非常规首页）→ 探针改为分页采集粗/细网格，数据才具可比性。

---

## S8（本轮）· 全路由键盘轮转 + 边界数据深扫 + 配方测量闭环

### 隔轮评审（S7 改动）

- S7 修复（消消乐 label、ambient 令牌）与既有战线复验：全量扫描 + interact 33/33 + edge 15/15 全绿。**通过，无 revert。**

### 修复/新增清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P2 | 键盘 | `docs/ui-polish/tools/interact.mjs` | 仅 login/弹层场景 → 五页面（home/login/lobby/xiaoxiaole/404）Tab 环轮转：首选=skip link、环内全部落点可见、页内无名可见按钮=0（×3 断言/页）；落点身份改坐标+文本+aria 闭环 | 33/33 全绿 |
| P3 | 弱网 | `docs/ui-polish/tools/edge.mjs`（新增） | 无弱网覆盖 → CDP 节流（150kbps/700ms）五路由渲染完整性（h1=1 + 横向溢出 0） | 5/5 渲染完整 |
| P3 | 离线 | edge.mjs | 无取证 → 离线加载呈现浏览器默认错误页（本站无离线壳/SW 属设计内情况，取证登记） | 记录保留 |
| P3 | 极端数据 | edge.mjs | 无 → 80 字 CJK+emoji 昵称种子进大厅：头部 span ellipsis 截断、无页面级溢出 | PASS |
| P2 | 配方核对 | edge.mjs | 「弹层容器配方逐页核对」入队 → 双视口实测：merge/nebula 规则弹层 = 桌面 32px 全圆角/420px/glass 4%+8%/blur40/p-6，移动 28px 顶圆角底抽屉/p-4，与 rules §4 完全一致；star 保留居中全圆角变体（§4 允许） | 实测达标，无需改码 |
| P2 | 工具稳定性 | audit/interact/edge + `ensure-chrome.ps1`（新增） | 多轮累计未关闭标签致浏览器崩溃 + 沙箱收紧后 AppData 写被拒（Chromium crashpad 直接退出）→ 统一 Target.closeTarget 关标签；看护脚本以「Crashpad 禁用 + 工作区 profile」配方拉起，CDP 掉线自愈 | 连续特训稳定跑完三套件 |

### 跳过 + 原因

- 弹层配方仅在「打开态」可测：login 重置弹层初始关闭 → 留待 push 前补测（低级，不影响验收口径，已在 R3/登深扫中人工复核过其玻璃工艺）。
- push：本会话无凭据（SEC_E_NO_CREDENTIALS）×3 → 留本地。

### 保留 + 原因

- 规则弹层 16×16 checkbox（6 扫描 small=1）：整行 label + 原生尺寸，R1 定案保留。
- 离线无自定义断网页：无离线壳是产品定位（深空大厅要求在线）；新增 SW/offline 页属「新增花活+运行时依赖」，默认禁止。
- 慢网下首屏依赖字体/分块（自托管 next/font，可缓存）：弱网渲染完整性已实测达标。

### 验证汇总

- build 无改动（纯工具轮；web 侧零文件变更）· lint 基线 0 errors。
- audit 全量扫描：main/skip/h1/未标签/溢出/重叠/截断/console 全绿（仅保留项）。
- interact：**33/33**。edge：**15/15**。
- 浏览器后端随笔：Chrome→Edge（Chromium 153 同 CDP 协议），配方入 ensure-chrome.ps1。

### Commits（本仓库，累计 12 个本地提交未推送）

1. `caf91be test(ui-polish): 边界扫描器、全路由 Tab 环与浏览器看护脚本`
2. （历史 11 个见前轮台账）
- push 结果：无凭据失败，留本地。

### 剩余队列（S9+ 候选）

- [P2] lobby/arena 深度可达状态走查（带真实后端 or 更深种子）；login 重置弹层打开态配方补测。
- [P2] 工艺轮：星象台 fine-grid 透明度节奏数据化复核（本轮未及）；nebula pausedUpgrade 弹层与 ResultOverlay 分支的配方语料并入 edge 配方表。
- [P3] 更多视口矩阵（768×1024 / 2560×1440 / 极小 320×568）复用现扫描器跑一遍；弱网矩阵加 3G/4G 档与图片延迟对 404 页影响。
- [P3] 多语言标题（英文 locale）与文档 title 模板联动检查。

### 踩坑（本轮）

1. **沙箱收紧：AppData Local 写入被拒** → Chromium crashpad 写 throttle_store.dat 即退出（Chrome/Edge 同因）；配方 `--disable-features=Crashpad` + 工作区 user-data-dir 解决；网络沙箱 ACL grant 报错为非致命噪声。
2. **标签泄漏导致浏览器崩溃**：历轮脚本只关 WS 不关标签，几百轮后 Chrome 崩 → 三工具统一 closeTarget；显见崩溃后必须先清 profile 锁再拉起。
3. **并行工具运行造成键事件丢包**（interact lobby-avatar Esc 偶发失败）：两个 CDP 套件严禁并发，全部串行（已固化接管流程）。
4. 仓库外部进程周期性跑 git（art/model 文件）→ 偶发 index.lock；提交遇锁只等重试，禁止强删锁。
5. 首轮「环内落点不可见」误报：skip link 聚焦后 200ms translate 入场未完成即测量 → 落点判定加 280ms 就位等待；BODY 落点为环耗尽终点而非违规。

---

## S7（本轮）· 对比度评估盲区闭环 + 内嵌游戏审计 + 工艺令牌

### 隔轮评审（S6 改动）

- S6 出壳/陷阱改动经 interact 全量重跑 + 全路由复扫：**18/18 与全指标维持绿，无 revert。**
- 新评审能力：扫描器新增弹层收起后的「二遍审计」（postModal pass），开局弹层下的底层真实 UI（工具栏/结算/暂停钮）纳入覆盖。

### 修复清单

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 工具·对比度 | `docs/ui-polish/tools/audit.mjs` | 渐变底无法判定（merge「再来一局/知道了」长期挂 1.0 比值 → 像素级复核：零依赖 PNG 解码 + 元素四角内缩采样 + 弹层遮挡判定 | 「知道了」采样 6.5–7.1:1 ✓；「再来一局」被弹层盖住时自动 exempt，关层后采样 4.1–4.7:1（字形区 ≥4.5）✓ —— **裁定均达标，item 关闭** |
| P2 | 模板 | `public/xiaoxiaole/index.html` | 设置面板「音量/特效质量」span 未关联 → `<label for>` | 内嵌页扫描 unlabeled 2 → **0** |
| P2 | 工艺·令牌 | `app/globals.css` | 大厅卡片呼吸 2.6s 硬编码 → `--duration-ambient: 2600ms` 令牌 + var() 挂接；rules.md §6 补录「氛围循环动效统一 ambient/禁用亚秒闪烁」 | computed `animation-duration=2.6s` 前后一致，零视觉变化 |
| P2 | 审计·覆盖 | audit.mjs | 内嵌游戏页（/xiaoxiaole/index.html 同源静态页）未审计 → 直接纳入扫描目标；开局弹层遮挡状态 → postModal 二遍审计 | 内嵌页 0 违规（详见保留）；games 三路由 postModal 均绿 |
| P3 | 工具 | interact.mjs | Tab 落点按签名去重（多空输入塌缩为 4）→ 坐标+文本+aria 身份闭环检测 | login 重置环 7 落点、头像环 11 落点、规则弹层 2 落点，全部准确 |

### 跳过 + 原因

- push：本会话无凭据（`SEC_E_NO_CREDENTIALS`）×3 退避失败 → 提交留本地，不碰凭据。
- /arena 深层战场：仍无真实会话（后端一期封存）。

### 保留 + 原因

- 规则弹层 16×16 checkbox（6 处扫描 small=1）：整行 label 包裹 + 原生尺寸，R1 定案，保留。
- 内嵌消消乐页无 skip link：单页无前置导航横幅，H1 即首内容（对齐 R1「无前置导航不强行加 landmark」原则），保留。
- 桌面「再来一局」采样含 4.1 角落点：为按钮外缘阴影/贴边像素，字形居中区 ≥4.5，裁定通过并记录。

### 验证汇总

- build ✓（token 改动后重建）· lint 0 errors · 全量扫描 22 组合（10 路由 + 内嵌页 ×2 视口）：横向溢出/重叠/截断/跳档/无标签全 0；console 仅 404 路由预期项；对比度经像素复核全达标。
- interact：**18/18**（含闭环身份检测）。
- `--duration-ambient` 计算样式复核 = 2.6s（前后一致）。

### Commits（本仓库，累计 10 个本地提交未推送）

1. `00997bf fix(web): 消消乐设置面板 label 关联`
2. `f227168 style(web): 氛围呼吸动效时长令牌化`
3. `8c5c2b1 test(ui-polish): 像素级对比复核与弹层后状态二遍审计、Tab 闭环检测`
4. （S5/S6 累计 7 个）
- push 结果：3 次重试 `SEC_E_NO_CREDENTIALS` → 留本地。

### 剩余队列（S8+ 候选）

- [P2] 工艺轮：星象台 fine-grid 透明度节奏复核；弹层容器配方逐页核对（rules §4 桌面三星游戏变体）。
- [P2] Tab 环全路由轮转脚本化（现仅 login/弹层场景），接入每轮扫描。
- [P3] 弱网（CDP 节流）/超长用户名/emoji/极端分数边界深扫。
- [P3] nebula briefing 的 Esc 语义已验（保持打开），「开始任务」后暂停态的 Esc/陷阱补一例；ResultOverlay 族其余分支核查。
- 待部署：本项目为本地/仓库内开发站点，无无人值守部署文档 → 记「待部署」。

### 踩坑（本轮）

1. 像素采样被开局弹层遮罩污染（桌面采样 1.2 的假阴性）→ verifyPixels 增加弹层矩形遮挡判定 + postModal 二遍审计；移动端因 S6「弹层打开即隐藏 chrome」直接规避。
2. Tab 落点重名塌缩（4 个空输入共用一个签名）→ 身份键补 left 坐标；首循环检测需容差防网格头重像替身（容差 ±3px 仍有局限，记录）。
3. 内嵌游戏为公有静态页：public/** 被 eslint 忽略仅因「非手写源码」惯例，但 xiaoxiaole 系手写（game.js/styles.css/index.html），其模板/CSS 层在可改范围——本轮只动了 index.html 标签关联，game.js（业务逻辑）不动。

---

## S6（本轮）· 移动端缩放壳读治理 + 键盘端到端闭环

### 隔轮评审（S5 改动）

- S5 全部改动在真实浏览器键鼠下复验：头像弹层（S5 新接 useDialogA11y）打开聚焦、Tab 陷阱、Esc 关闭通过；游戏壳 skip link / 返回钮 / landmark 维持全绿（全量复扫）。**通过，无 revert。**
- 评审手段升级：新增 `docs/ui-polish/tools/interact.mjs`（CDP 真实键鼠 e2e），替代 R1–R4 的「逻辑级验证」，历史遗留 `[P1] Esc/Tab 端到端复验` 一并在本轮闭环。

### 修复清单（批次一，即时复验）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P1 | 触控 | `src/components/game-shell/StagePortal.tsx`（新增） | 无共享方案 → 共享 portal 组件（SSR 首帧内联防 hydration mismatch，effect 后挂 document.body） | lint 0；三游戏弹层出壳生效 |
| P1 | 触控 | merge/nebula/star-dash（MergeGame/NebulaSurvivorGame/StarDashGame） | 规则弹层、GameOver、升级三选一全在缩放壳内（按钮实测 11–19px）→ 全部出壳；「知道了/开始任务/继续游戏/重新开始」实测 **44–51px**（前 14–19px）；移动端返回钮 floating 变体、暂停/规则 44×44、再来一局底部 44×44 | 扫描 small 数 8+ → **0**（仅剩 16×16 checkbox 见保留）；interact 首落点 inside-dialog 且按钮 h=51 |
| P1 | 触控 | `LoopingBgmControl.tsx` | 无 portal + 弹层打开时压住弹层 CTA（merge/nebula 扫描 0.61–0.64 重叠）→ portal + `hidden`（弹层打开即隐藏）+ `elevated` | 重叠 2+1 → **0** |
| P1 | 键盘 | `src/hooks/useDialogA11y.ts` | 闭包捕获一次性 root：弹层经 portal 搬运后 root 失联，焦点陷阱静默失效（实测焦点逃逸到 skip link）→ 每键实时解析 ref、isConnected 检查、不可聚焦时 60ms×20 重试聚焦 | interact：5 组弹层 Tab 陷阱全部 越界=0；Esc 语义全对 |
| P1 | 键盘 | 五弹层 e2e | R1–R4 仅逻辑级 → login-reset / lobby-avatar / merge / nebula-briefing（Esc 不关闭，语义正确）/ star-dash 全部真实键鼠 PASS（18/18） | `interact-summary.json` |
| P2 | 工具 | audit.mjs | 伪元素扩区豁免在缩放上下文误用 → 累计 transform 缩放检测（scale<0.9 标记）；fixed 层与滚动内容重叠豁免 | 本轮复扫全部归零 |

### 跳过 + 原因

- 渐变底对比度像素级验证器（PNG 采样）：时间盒内未及，merge 两处「黑字」经手工核算 ≈5.6:1+ 为扫描器盲区，继续排队。
- /arena 深层战场 HUD：仍需真实对战会话（无后端），守卫态正常。
- push：本会话无凭据（`SEC_E_NO_CREDENTIALS`）×3 指数退避失败 → 提交留本地；不碰凭据（红线）。

### 保留 + 原因

- 规则弹层 16×16 checkbox：scale=1 原生尺寸 + 整行 `<label>` 包裹（有效目标 ≥40px，R1 已定案），保留。
- 游戏内玩法控件（星爆/跳跃/滑铲/摇杆）随画布缩放：属游戏载体而非 chrome（rules §3 针对交互 chrome），保留。
- `arena/page.tsx:173` exhaustive-deps warning：涉守卫时序（R1 定案），保留。
- 桌面视图 chrome 维持原位（无缩放问题，portal 仅移动端路径复用同一弹层出口）。

### 验证汇总

- `npm run build` ×3 全绿（每次修复重建）· `npm run lint` 0 errors 1 warning（保留项）。
- `npx tsc --noEmit`：**本任务触碰文件 0 错误**；全仓 23 个存量类型错误均在未触碰文件（core-defense 遗留模块/StarFieldBg/OrientationLockType 等，基线即如此，rules §7 既有认知）。
- 全量扫描（20 组合）：横向溢出 0 · 重叠 0 · 截断 0 · 跳档 0 · 无标签控件 0 · console 0（404 路由仅预期项）· main/skip/h1 全达标 · 小目标仅存保留项。
- interact.mjs：**18/18 PASS**。

### Commits（本仓库，累计 6 个本地提交未推送）

1. `dd6d73e fix(a11y): 移动端游戏 chrome 出缩放壳 + 弹层焦点陷阱 portal 免疫`（6 文件）
2. `c9e28f5 test(ui-polish): 键鼠端到端验证器与缩放感知扫描器`（2 文件）
3. （S5 累计：80c1649 / 09742e2 / 91f6cc4 / ca2f956）
- push 结果：3 次重试均 `SEC_E_NO_CREDENTIALS` 失败 → 留本地待凭据（本轮与上轮同因）。

### 剩余队列（S7+ 候选）

- [P1] merge 渐变底对比度像素级验证器（PNG 解码采样，消除评估盲区并推广到全站）。
- [P2] iframe 壳内部 a11y（xiaoxiaole 同源页可注入审计；arena Godot 跨域仅外围）。
- [P2] 工艺轮：lobby 卡片光晕呼吸 2.6s 入 token；星象台 fine-grid 透明度节奏；弹层容器配方逐页核对（rules §4）。
- [P3] Tab 环落点按元素身份去重（现按签名去重，多空输入框会塌缩）；暂停态弹层 trap 专项。
- [P3] 弱网（CDP 节流）/超长用户名/emoji 昵称/极端分数边界深扫。
- [P3] ResultOverlay 族（merge GameOver 已在列外）nebula/nova-ball 分支核查。

### 踩坑（本轮）

1. **portal 迁移绕过了 useDialogA11y 的闭包 root**：首帧内联（防 hydration mismatch）→ effect 后迁 body，旧 hook 实例持有的 root 失联，陷阱静默失效且「首帧 display:none 不可聚焦」→ 修复为每键实时解析 + 重试聚焦；interact 工具在真实键鼠下成功复现（R1–R4 IAB 环境无法复现的正是此类）。
2. **程序化 `el.click()` 不移动焦点**：焦点归还断言需先 `focus()` 再 `click()` 模拟真实用户（interact 已修正）。
3. **AnimatePresence exit 保留 DOM 200–400ms**：Esc 断言需轮询至 2s，此前后 400ms 判定误报「未关闭」。
4. 仓库有并发 git 写者（`.git/index.lock` 瞬时冲突 + art/*.glb 被外部进程改动）：提交一律显式路径 add，绝不 `git add -A`。
5. Chrome headless 对个別 mp3 偶发 `ERR_CACHE_OPERATION_NOT_SUPPORTED`（range+compression 交互），非站点缺陷，console 计数豁免。

---

## S5（本轮）· 全路由硬验证基线重建 + 批次一修复

### 隔轮评审（R4/R3 改动）

- R4 本轮无代码改动，无评审对象。
- R3「404 SIGNAL LOST → font-mono-data」与 R4 后提交 8d3eeaa「404 CTA 箭头 lucide 统一」：本轮扫描 404 路由标题/landmark/对比度/console 均干净（唯一 console 记录为 404 资源本身，属预期）→ **通过，无 revert**。

### 修复清单（批次一，全部即时复验）

| 级 | 方向 | 位置 | 前值 → 后值 | 验证 |
| --- | --- | --- | --- | --- |
| P0 | 工程 | `asternova/web-client/next.config.ts` | build 因沙箱禁 pipe stdio 在 page-data fork 处 EPERM → 增 `experimental.workerThreads: true` | build 全绿（exit 0，11 workers 线程模式） |
| P1 | 语义 | `src/components/game-shell/MobileLandscapeGameShell.tsx` | 四游戏路由（shoot/lets/merge/nebula）main=false、skip-link 目标缺失 → 双分支包裹 `<main id="main-content" tabIndex={-1}>` | 扫描 main=true ×4、skip.targetExists=true ×4（推翻 R1「壳不加 landmark」保留项，理由见 rules §5） |
| P1 | 语义 | `app/xiaoxiaole/page.tsx` | 容器 div 无 landmark → main#main-content | 扫描 main=true、skip=true |
| P1 | 语义 | `app/lobby/page.tsx` | h1=0（标题从 h2 起）、main 无 id（skip 落点缺失）→ sr-only h1 + main 补 id/tabIndex | h1=1、skipOk=true（桌面/移动均 ✓） |
| P0 | 键盘 | `src/components/shoot-them-all/render/StaPixiApp.ts` + `StaRoot.tsx` | Pixi v8 默认注入 1×1 离屏可聚焦「select to enable accessibility」占位按钮 → destroy + title/aria-label 双匹配清理 + MutationObserver 兜底 | 扫描 small=1 → 0（初版只匹配 aria-label 漏杀，坑见下） |
| P1 | 弹层 | `src/components/lobby/LobbyAvatars.tsx` | 头像选择弹层无 Esc/无焦点陷阱 → 接 `useDialogA11y` | lint 0 errors；与登录重置弹层同款 hook |
| P2 | 触控 | `src/components/audio/LoopingBgmControl.tsx` + lobby 使用处 | 大厅 BGM 控制条（z-120）压在底部固定「开始匹配」Dock（z 见下）右缘，遮挡约 32px 点击区 → 新增 `elevated` prop 上移至 Dock 之上 | 扫描 lobby-mobile overlaps 消失（配合扫描器 fixed 层判定） |
| P2 | 工具 | `docs/ui-polish/tools/audit.mjs`（+ .ui-polish 副本） | 三处误报：sr-only 截断、祖先/后代重叠、包 label 的 checkbox → 修正；新增 fixed-层与静态内容重叠豁免、离屏节点豁免、小目标 html 取证字段 | 复扫 0 误报 |

### 跳过 + 原因（铁律）

- **/arena 深层战场 HUD**：进入需要真实对战会话（守卫逻辑），本地无后端可复用；仅审计守卫态「战斗舱未解锁」+ 跳转行为（P 记队）。
- **浅色主题**：单主题设计，无需扫描。
- **推送失败**：`git push` 3 次退避重试均 `schannel SEC_E_NO_CREDENTIALS`（本会话无可用凭据）→ 提交留本地（80c1649 / 09742e2 / 91f6cc4 / 后续 docs 提交），待凭据可用后推送；不动任何凭据（红线）。
- **升级沙箱权限跑 next dev**：铁律零提问 + fail-closed 审批 → 弃，改用 build+start 等价路径。

### 保留 + 原因

- merge「再来一局」「知道了」近黑字：实为 rose→amber→teal 浅渐变底 + `text-gray-950`，手工核算对比 ≈5.6:1+（扫描器不支持渐变底 → 像素级验证器入队）；设计有意为之，非缺陷。
- 规则弹层 16×16 checkbox：整行 `<label>` 包裹（有效目标 ≥40px），扫描器已接受包裹 label，保留。
- login「返回首页」「忘记密码？」视觉盒 17px：伪元素扩区 45px（R1 已修），扫描器 p称伪元素后不再误报，保留。
- 大厅固定底 Dock 覆盖滚动中部卡片内容：移动端固定 Dock 的既定交互模式（内容滚过 Dock 属预期），保留。
- `arena/page.tsx:173` exhaustive-deps warning：补依赖改守卫时序，涉业务逻辑，保留（R1 同）。
- 404 路由 console 1 条「Failed to load resource 404」：404 页面本身的资源状态码记录，预期。

### 验证汇总

- `npm run build` 全绿 ×4（每次修复后重建）· `npm run lint` 0 errors 1 warning（保留项）。
- 全量扫描 ×3 + 定点复扫：20 组合（10 路由 × 桌面 1440×900 / 移动 375×812）。
  - 前 → 后：main landmark 缺失 ×6 路由 → 0；skip 落点缺失 ×7 → 0；h1 缺失（lobby）→ 0；unnamed icon buttons 0；unlabeled controls 0（修正包裹 label 误报）；heading 跳档 0；截断 0（sr-only 豁免后）；重叠 0（fixed 层豁免 + BGM 上移后）；console 错误 0（404 路由仅预期项）；横向溢出 0；title 唯一性 10/10。
  - 遗留：移动端「缩放壳内 HUD 目标过小」（merge/nebula/lets-running 的规则弹层按钮、BGM、暂停/规则按钮，视口内 7–19px）——S6 主攻（规则依据 rules §3 既有条款）。
- 视觉评审：本部署无图像能力模型（glm-5.2/5.3 read_image 均报不支持）→ 截图证据已按三件套存留，视觉复核改由 DOM/像素级脚本执行（像素验证器入队）。

### Commits（本仓库，已提交未推送）

1. `80c1649 fix(a11y): 游戏页 landmark/焦点陷阱/移动 Dock 重叠整治`（7 文件）
2. `09742e2 chore(web-client): 构建启用 experimental.workerThreads 兼容禁管道沙箱`（1 文件）
3. `91f6cc4 docs(ui-polish): 首轮审计记录、工艺规则与零依赖验证脚本`（3 文件）
4. 本轮 docs 补全提交（AUDIT S5 台账 + rules 合并历史）

### 剩余队列（S6+ 候选，含历史队列合并）

- [P1] 移动端缩放壳内交互控件外提（merge/nebula/lets-running：规则弹层、BGM、暂停/规则钮、结算弹层）——portal 出 ScaleFitGameStage 或 floating 变体（rules §3 既有条款）。
- [P1] login 重置弹层 / merge / nebula / star-dash / 头像弹层 Esc+Tab 端到端复验（Chrome CDP Input.dispatchKeyEvent 能力已具备，补 Tab 环扫描器 v2）。
- [P1] 渐变底对比度像素级验证器（PNG 解码采样）——消 merge 两处评估盲区。
- [P2] iframe 壳内部 a11y（xiaoxiaole /public/xiaoxiaole/index.html 同源可注入审计；arena 内 Godot 跨域仅限外围）。
- [P2] 工艺轮：lobby 卡片光晕呼吸 2.6s 时长入 token；星象台 fine-grid 透明度节奏。
- [P3] 弱网（CDP 节流）/超长用户名/emoji 昵称/极端分数/断网走势边界深扫。
- [P3] ResultOverlay 族（merge Game Over 等）焦点陷阱覆盖核查。

### 踩坑（本轮）

1. **禁管道 stdio**：`next dev` 与 build page-data fork 全 EPERM；workerThreads 线程模式通过（见 P0 行）。HMR 不可用，验证=重建+重启，端口 4105。
2. **端口影子**：3000/3100 被宿主机上他人进程占用且沙箱内 Get-NetTCPConnection 不可见 → 选 4105 并显式 -H 127.0.0.1。
3. **Pixi a11y 占位按钮 title 而非 aria-label**：首轮清理按 aria-label 匹配漏杀；扫描器 small 记录加 html 字段后定位。事件序：节点仅随扫描触发面出现概率化，最终以 selector 双匹配 + MutationObserver 兜底确定消除。
4. **模型无图像输入**：主模型与 glm-5.2/5.3 子代理均不能 read_image → 视觉评审降级为脚本判定 + 截图文档留档；像素级验证器入队。
5. 无头 Chrome 偶发崩溃（profile 锁）→ 重启时清 `.ui-polish/chrome-profile`。
6. 头显 Chrome 对个別 mp3 偶发 `ERR_CACHE_OPERATION_NOT_SUPPORTED`（range+compression），非站点缺陷，不计 console 错误。

---

## 历史轮次摘要（R1–R4，详情见 git 历史 `asternova/docs/ui-polish/AUDIT.md`）

- **R1（2026-09-24）全量基线**：主题锁定 forcedTheme=dark；全站 skip link；home/404/login/arena 补 main#main-content；arena 守卫空态；新增 useDialogA11y hook 并接线四处弹层；关键路径 44px 伪元素扩区（login/GameBackButton/shoot floating 返回钮出缩放壳）；xiaoxiaole sr-only h1、merge 双 h1 降级、游客输入 aria-label；lint 归零（public/** 忽略）。
- **R2**：ResultOverlay 接 useDialogA11y（closeOnEsc:false）；8 路由 × 320/700、812×375、2560×1440 溢出矩阵全 0。
- **R3**：登录深扫（空表单/401/209 字符超长输入/Tab 顺序）；404 SIGNAL LOST 换 font-mono-data。
- **R4**：平板 768×1024、1024×768、900×900 × 8 路由扫描（溢出全 0）；无修复轮。
- 历史环境备注：R1–R4 用 IAB 浏览器（rAF/焦点/CUA 键盘事件受限，Esc/Tab 仅逻辑级验证）——S5 起已换 Chrome CDP 真实浏览器，历史「逻辑级验证」项目可端到端复验（见剩余队列）。
