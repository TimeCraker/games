# UI Polish 审计台账（AUDIT）

> 永续循环目标：前端 UI 细节打磨（零人类参与）。每轮追加一节，最新在上。
> 截图与扫描 JSON 存临时目录：`%TEMP%\ui-polish-r1\`（不进仓库）。
> 站点：dev server `http://localhost:3311`（`npm run dev`，web-client 目录）。

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
