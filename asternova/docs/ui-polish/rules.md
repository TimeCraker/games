# UI Polish 设计规则（写改前先读，改令牌先改这里）

> 依据：`web-client/app/globals.css`（Stage A 深空黑体系）· `src/components/arcade/brand.ts`（街机品牌单一真源）。
> 本文件是「审美有依据」的挂靠点。任何工艺改动必须引用此处规则或先补录规则，禁止拍脑袋。

## 1. 主题

- 站点为**深空黑单主题**（Stage A 决策）。`ThemeProvider` 锁 `forcedTheme="dark"`，浅色 token（`:root` 段）仅为 shadcn 默认残留，**不得**在组件里依赖 `bg-background`/`text-foreground` 走浅色分支，也不新增浅色适配。
- 自定义表面一律用 `bg-space-black` / `bg-surface-1/2/3` / `bg-glass-bg`，不用裸 `bg-white`/`bg-black` 拼贴。
- **禁用色族**：`violet / fuchsia / purple / indigo / pink-*` 以及高饱和 `cyan-*` / `sky-*`。
  验收口径：`grep -E 'violet|fuchsia|purple|indigo|pink-[0-9]|cyan-[0-9]'` 在 `src/components` 下命中为 0
  （注释里的历史说明不算违规，但不要再新增）。`rose-* / teal-* / emerald-*` 非硬禁用，但应优先换成品牌 token。
- **不要再引入「名字是旧色相、值是品牌色」的兼容别名**（如曾经的 `--brand-violet: #D8A33C`）。
  这类别名全仓零引用却持续误导排查；已于 2026-09-27 连同 `--glow-violet` / `--shadow-glow-violet` / `--chart-*` 蓝色定义一并清除。

## 2. 文字与对比度（实测口径：含元素 opacity 与 alpha 合成后的有效对比度）

- 文字透明度地板 `text-white/50`（≈4.8:1 on surface-2）。**22%~48% 一律违规**；装饰性 `aria-hidden` 文字可用 /35 下限。
- 正文 ≥ 4.5:1；≥24px 或 ≥18.66px 粗体大字 ≥ 3:1。
- 品牌色可用于正文强调（中文标注、数值），但**只允许单一琥珀**（`text-hud-accent` / `text-hud-accent-bright`）；
  多色混排正文必须走 `HudKit` 或 `BrandMark`，不要各游戏自己调色。

## 3. 触控目标

- 一切可点目标**视觉盒 ≥ 24px**；关键路径（主 CTA / 返回 / 关闭 / 删除）**有效命中区 ≥ 44px**。
- 视觉不变扩命中区统一用伪元素法：`relative before:absolute before:-inset-x-2 before:-inset-y-3 before:content-['']`（±12px ≈ +24px 命中）。参考 `GameBackButton`、login 返回首页/忘记密码。
- **禁止把交互控件放进 `transform: scale()` 缩放容器**（shoot-them-all 教训：HUD 随画布缩到 21px）；用 floating 变体固定在安全区。
  - 但**非交互**的 HUD / 覆盖层**可以**放在缩放容器内——见 §11，此时字号必须按缩放比留余量。

## 4. 弹层（自绘 overlay）

- **统一组件 `src/components/arcade/ArcadeEntry.tsx`**（内含 StagePortal），不要再手写规则/简报弹层。
  它把三家原有差异保留为 props：`variant`（drawer/centered）、`safeArea`、`overlayZClassName`/`overlayTint`/`overlayPadding`、
  `eyebrow`/`panelOverlay`/`footer`、`skipRules`（**受控**，localStorage 读写留在各游戏）、`confirmClassName`。
- **Esc 语义由 `onRequestClose` 有无决定**：给了才 `closeOnEsc=true`。刻意保留的差异：
  merge / star-dash 的 Esc = 等同点确认按钮；**nebula 的 briefing 不传 `onRequestClose`**（必须显式点「开始任务」），
  其 pause / reference 才可 Esc 关闭。改这一条等于改交互契约，需先确认。
- 结构必备：`role="dialog"` + `aria-modal="true"` + `aria-labelledby`（标题加 id，id 沿用各游戏原有值）。
- `confirmClassName` 是**整体覆盖**而非 twMerge 局部合并 —— 实测 twMerge 会把 `shadow-lg` 与 `shadow-amber-500/20` 判为同组并丢掉前者。
- **容器配方（三游戏规则弹层统一）**：移动端底部抽屉 `rounded-t-[1.75rem] border-b-0`，桌面 `sm:rounded-[2rem] sm:border-b`；宽度 `max-w-[420px]`；内距 `p-4 sm:p-6`；玻璃 `bg-glass-bg backdrop-blur-glass-lg`；高度 `max-h-[min(88dvh,calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-1.5rem))] overscroll-contain`。居中式弹层（如 star-dash）可保留 `rounded-[2rem] p-6` 全圆角变体，但玻璃/边框/投影 token 不得离队。

## 5. 语义与键盘

- 每路由唯一 `document.title`（`metadata` + `%s · AsterNova` 模板）；正文有且仅有一个 `<h1>`，游戏壳用 `sr-only` h1。
  **游戏名一律走 `brand.ts`**，见 §8。
- `<main id="main-content" tabIndex={-1}>` 为 skip link 落点；skip link 挂 `app/layout.tsx`（fixed + translate 出入屏，禁用 sr-only/not-sr-only 组合——二者 position 冲突）。
- 全站焦点环 `:focus-visible` 为**琥珀环**（`rgb(216 163 60 / 0.75)`，globals.css 兜底）；图标按钮必须 `aria-label`。

## 6. 动效与排版

- 时长 token：`--duration-fast: 200ms`（hover/微交互 150–300ms 区间）；缓动 `--ease-cinematic`。
- 字体：正文 Geist Sans；数据/坐标 `font-mono-data`（JetBrains Mono + tnum）；品牌大字 Orbitron（`.aster-title`，颜色 `var(--paper)`）。
- 间距/圆角走 token：`--radius` 阶梯、`max-w-aster`（1180px）容器。

## 7. 工具链

- `public/**` 已加入 eslint 忽略（Godot 导出产物与静态游戏，非手写源码）。
- `typescript.ignoreBuildErrors: true` → build 通过 ≠ 类型正确，改动后跑 `npx tsc --noEmit` 或依赖 IDE。
- 既有 tsc 报错基线（**别去动，也别拿它当新问题**）：`CinematicBlackHole.tsx` ×4（缺 @types/three）、
  `nebula-survivor/render/NebulaBackground.ts(61,17)`、`hooks/useMobileGameViewport.ts(40,105)`。
- lint 基线：0 errors / 6 warnings（arena exhaustive-deps、fetch-arcade-art.mjs ×3、LoopingBgmControl、NebulaScene）。

## 8. 街机品牌单一真源（brand.ts）

- 5 个游戏的**英文主名 / 中文标注 / 分类 / 序号 / 副色 / href** 全部定义在 `src/components/arcade/brand.ts`，
  并由它派生：大厅卡片、各路由 `metadata.title`、游戏内开场与结算的品牌字。
- `brand.ts` 必须保持**纯数据**（5 个 game route 是服务端组件，会 import 它生成 metadata）。
- 它带一个**编译期哨兵**：`_SlugParityWithKeyArt` 断言 `ArcadeSlug` 与产图脚本生成的 `KeyArtSlug` 完全一致 —— 两边增删游戏不同步会直接报类型错误。
- **禁止**在任何位置硬写游戏中英文名。历史事故：改完大厅没改游戏，线上出现「大厅叫弹珠风暴、页面 title 叫射击大战」的断层。
- 统一品牌标记组件 `BrandMark`（`strip` / `title` / `inline` 三变体），名字一律取自 brand.ts。

## 9. 副强调色（--arcade-accent）与 portal 陷阱

- 每个游戏一个低饱和副色，定义在 globals.css 的 `--arcade-<slug>`，**硬约束：同一亮度带（OKLCH L≈0.74–0.78）、低饱和（C 0.08–0.11）**。
  取值必须落在琥珀同体系内，避免重回高饱和霓虹。
- 消费方式是**作用域 CSS 变量** `var(--arcade-accent)`，不是 `text-arcade-merge` 这类动态类名（Tailwind 无法为运行时拼接的类名生成样式）。
- ⚠️ **CSS 自定义属性不跨 portal 边界**。规则弹层 / 结算卡 / 悬浮返回钮都经 `StagePortal` 挂到 `document.body`，
  挂在游戏根节点上的 `--arcade-accent` 对它们完全不可见，会**静默回落成琥珀**（本项目实测踩到：结算卡里的「星轨疾驰」本应冰蓝，实际渲染成金色）。
  故必须**两者并存**：根节点 `arcadeAccentStyle(slug)` 负责首帧，`useArcadeAccent(slug)` 负责 portal 子树（挂 `<html>`、卸载还原）。

## 10. 记录总线（asternova.arcade.v1）

- 唯一入口 `src/components/arcade/records.ts`：命名空间 `asternova.arcade.v1`，含 version + 逐字段净化 + 隐私模式内存兜底 + 跨标签页订阅。
- 游戏结束时走 `ArcadeResult`（它内部调 `submitRecord`），不要各游戏自己写 localStorage。
- `submitRecord` 带 **roundId 幂等**：同一局重复提交（StrictMode 双调用初始化器 / 结算组件重挂载）不会把 `plays` 计两次。
- 局中显示「最高」时必须取 `max(历史最高, 本局分数)` —— 历史最高只在局末写入，
  否则本局已破纪录时会显示成「1960 / 最高 960」这种自相矛盾的读数。

## 11. 等比缩放游戏的 letterbox 与 HUD 字号

- 竖版 720×1280（弹珠风暴）与横版 960×540（星轨疾驰）在宽屏/竖屏下都会留大边。
  **不要再用蓝紫渐变填 gutter**（旧 `StaGameShell` 的 AI 味来源），统一用 `.arcade-letterbox`：冷黑底 + 琥珀星图网格 + 暗角。
- 缩放容器内的 HUD 字号必须按**缩放比留余量**：手机竖屏 `scale ≈ 0.5`，
  故逻辑画布内的字号按 **24–40** 给（落到真实 12–20px）。实测 390×844 下按此规则的 HUD 完全可读。
- 参考实现：`src/components/shoot-them-all/StaHud.tsx`。HUD 数值**必须取自引擎真实状态**，不做装饰性假数字。

## 12. 色阶设计约束（十档进化的血泪）

- 多档色阶必须**明度单调**：玩家靠亮度就能读出「进化到第几级」。跳色盘（明度非单调）一律不合格。
- 生成坡道时**必须避开绿（90–160°）与紫/品红（270–330°）**。
  实测教训：`215° → 42°` 的线性插值会经过 120°，渲染出**糖果薄荷绿**——它与紫色同属不属于品牌体系的 AI 味。
- 正确做法是**显式给表**而非线性插值。参考 `merge/MergeGame.tsx` 的 `TIER_RAMP`：
  1–3 级低饱和冷灰（矿石感）→ 4 级起跳到暖区 → 4–10 级在 58°→30° 窄暖带里靠明度(63→91)与饱和(30→60)拉档次。

## 13. 结算卡

- 统一走 `src/components/arcade/ArcadeResult.tsx`（内部调 `submitRecord` + 渲染 `ui/ResultOverlay`）。
- 巨型标题**按最长单词反推字号**（`min(26/最长词长 rem, 12vw)`），不要写死 clamp ——
  原 `clamp(3rem,9vw,6.6rem)` 是按 4 字母短词估的，实测 5 字母的 `CRASH` 在 1440px 下就被切掉尾字母，`VICTORY`/`DEFEAT` 更糟。
- 标题为中文时走紧凑档并去斜体（那个形态只吃得下拉丁展示词）。
- 失败态用 `--signal-red`，不要 Tailwind 原生 `red-500` + 高饱和大红辉光。

## 14. 验收纪律（这一节的价值高于前面所有配方）

- **build / lint / tsc 全绿 ≠ 能跑**。本项目连续踩过两次：
  1. 替换 canvas 结算块时误删 loop 体内的**每帧泵** `requestAnimationFrame(loop)`，只留 effect 末尾的初始点火 →
     游戏只画一帧即静止，而三项静态检查全绿。**rAF 驱动的游戏改动后必须取证画面在持续演进**
     （注入 rAF 计数器 + 连拍两帧比对 `canvas.toDataURL()`，不能只看静态首屏）。
  2. matter-js 0.20 里用 `{ isStatic: true }` 创建的刚体**永远无法变回动态体**（`Body.create` 在 `Common.extend`
     阶段就置位，导致 `setStatic` 记录恢复快照的 `if (!part.isStatic)` 不成立，`_original` 从未记录）。
     后果：`mass` 停在 `Infinity` → 重力累加成 `force=Infinity` → `Body.update` 里 `force/mass = Infinity/Infinity = NaN`
     → 出界与静止判定（`NaN < 0.3` 恒假）全部失效。**整个游戏每次打开只能开一炮然后永久卡死**，而 build/lint/tsc 全绿。
     正确写法：**先建动态体，再显式 `Body.setStatic(body, true)`**。
- **HTTP 200 ≠ 通过**；**元素存在 ≠ 交互可用**。必须真正走一遍用户路径。
- **每条证据都要先证明「我测的是我以为的那个东西」**。实测踩坑：探针连测几轮全失败，以为是产品问题，
  实为**后端服务已随子代理会话结束被回收**，探针打在浏览器错误页上；而**错误页的 rAF 照样跑**，
  于是 `rafFrames=75` 成了彻头彻尾的假阳性。戳破它的是 `localStorage: Access is denied`（错误页是 opaque origin）。
- 视觉验收**必须亲眼看图**，不要用「我改完了」代替；改动涉及图片时记得**注销 Service Worker + 清 CacheStorage** 再截图，否则会读到旧图。
- 需要渲染状态但无法从 DOM 观察时，挂**只读调试钩子**（先例：`window.__staEngine`）。它是定位上面那个 NaN 的唯一手段。
