# UI Polish 设计规则（写改前先读，改令牌先改这里）

> 依据：`web-client/app/globals.css`（Stage A 深空黑体系）· 本文件是「审美有依据」的挂靠点。
> 任何工艺改动必须引用此处规则或先补录规则，禁止拍脑袋。
> 承接历史台账：R1–R4 规则位于 `asternova/docs/ui-polish/rules.md`（git 历史可查），本节为其合并延续。

## 1. 主题

- 站点为**深空黑单主题**（Stage A 决策）。`ThemeProvider` 锁 `forcedTheme="dark"`，浅色 token（`:root` 段）仅为 shadcn 默认残留，**不得**在组件里依赖 `bg-background`/`text-foreground` 走浅色分支，也不新增浅色适配。
- 自定义表面一律用 `bg-space-black` / `bg-surface-1/2/3` / `bg-glass-bg`，不用裸 `bg-white`/`bg-black` 拼贴。

## 2. 文字与对比度（实测口径：含元素 opacity 与 alpha 合成后的有效对比度）

- 文字透明度地板 `text-white/50`（≈4.8:1 on surface-2）。**22%~48% 一律违规**；装饰性 `aria-hidden` 文字可用 /35 下限。
- 正文 ≥ 4.5:1；≥24px 或 ≥18.66px 粗体大字 ≥ 3:1。
- 品牌色不做正文文字色（`--brand-violet` 等只用于实底/描边/光晕）。
- 渐变底上的文字用扫描器像素级复核（canvas 采样暂缺时人工核对：merge 「再来一局/知道了」为 rose→amber→teal 浅渐变 + `text-gray-950`，有效对比 ≥5:1，R5 判为设计正确，待像素级验证器接管）。

## 3. 触控目标

- 一切可点目标**视觉盒 ≥ 24px**；关键路径（主 CTA / 返回 / 关闭 / 删除）**有效命中区 ≥ 44px**。
- 视觉不变扩命中区统一用伪元素法：`relative before:absolute before:-inset-x-2 before:-inset-y-3 before:content-['']`（±12px ≈ +24px 命中）。参考 `GameBackButton`、login 返回首页/忘记密码。
- **禁止把交互控件放进 `transform: scale()` 缩放容器**（R1 shoot-them-all 教训：HUD 随画布缩到 21px；R5 复查确认 merge/nebula/star-dash 手机端规则弹层与 BGM 仍在缩放壳内——R6 队列）；用 floating 变体固定在安全区。

## 4. 弹层（自绘 overlay）

- 一律接 `useDialogA11y`（`src/hooks/useDialogA11y.ts`）：Esc 关闭 + Tab 焦点循环 + 打开移焦/关闭还焦；`closeOnEsc: false` 仅用于「必须显式确认」的弹层（如开局 briefing、Game Over）。
- 结构必备：`role="dialog"` + `aria-modal="true"` + `aria-labelledby`（标题加 id）。
- Radix 组件（ui/dialog 等）自带上述行为，优先用 Radix。
- **容器配方（规则弹层统一）**：移动端底部抽屉 `rounded-t-[1.75rem] border-b-0`，桌面 `sm:rounded-[2rem] sm:border-b`；宽度 `max-w-[420px]`；内距 `p-4 sm:p-6`；玻璃 `bg-glass-bg backdrop-blur-glass-lg`；高度 `max-h-[min(88dvh,calc(100dvh-env(safe-area-inset-top)-env(safe-area-inset-bottom)-1.5rem))] overscroll-contain`。居中式弹层（star-dash）可保留 `rounded-[2rem] p-6` 全圆角变体，玻璃/边框/投影 token 不得离队。

## 5. 语义与键盘

- 每路由唯一 `document.title`（`metadata` + `%s · AsterNova` 模板）；正文有且仅有一个 `<h1>`，游戏壳/大厅用 `sr-only` h1。
- `<main id="main-content" tabIndex={-1}>` 为 skip link 落点；skip link 挂 `app/layout.tsx`（fixed + translate 出入屏，禁用 sr-only/not-sr-only 组合——二者 position 冲突）。
- 全站焦点环 `:focus-visible` 紫环（globals.css 兜底）；图标按钮必须 `aria-label`；表单控件用 Label htmlFor 或包裹 `<label>`（规则弹层 checkbox 的整行包裹 label 为既有正确形态）。
- R5 修订：游戏壳（五 Arcade）改为**必须**带 `main#main-content`（R1 保留项「全屏画布壳不强加 landmark」被推翻：skip link 覆盖矩阵要求全路由可用落点，实测无回归）。

## 6. 动效与排版

- 时长 token：`--duration-fast: 200ms`（hover/微交互 150–300ms 区间）；缓动 `--ease-cinematic`；氛围呼吸类循环动效统一 `--duration-ambient: 2600ms`（R7 起，lobby 光晕已挂接）；一次性装饰扫光/电影感过渡挂 `--duration-slow: 900ms`（R10 起，lobby 光痕由 0.88s 归一至该令牌）；低于秒级的重复闪烁禁用。
- 死样式纪律（R11 起）：keyframes/工具类无任何组件引用即删（删繁就简）；删除前 grep 全仓取证。
- 字体：正文 Geist Sans；数据/坐标 `font-mono-data`（JetBrains Mono + tnum）；品牌大字 Orbitron（`.aster-title`）。
- 间距/圆角走 token：`--radius` 阶梯、`max-w-aster`（1180px）容器。
- 按钮动词统一：登录 / 进入大厅 / 返回大厅 / 重新开始 / 确认修改 / 取消（既有文案为准）。

## 7. 工具链

- `public/**` 已加入 eslint 忽略（Godot 导出产物与静态游戏，非手写源码）。
- `typescript.ignoreBuildErrors: true` → build 通过 ≠ 类型正确，改动后跑 `npx tsc --noEmit` 或依赖 IDE。
- R5 起：`next.config.ts` 已启用 `experimental.workerThreads`（沙箱禁管道 stdio 时 dev/build 的 fork 均 EPERM，线程模式通过）；站点用 `npm run build && node node_modules/next/dist/bin/next start -H 127.0.0.1 -p 4105 .`。
- 审计脚本：`docs/ui-polish/tools/audit.mjs`（零依赖 CDP 扫描器），产物落 `.ui-polish/artifacts/`（不进仓库）；改扫描器判定后同步 `.ui-polish/tools` 可执行副本。
