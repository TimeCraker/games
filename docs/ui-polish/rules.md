# UI 细节打磨 · 工艺规则（轨 2 挂靠用）

> 轨 2 纪律：审美不许拍脑袋，三件套缺一即跳过 —— a) 挂靠本规则或现有设计令牌；b) 截图前后对比存 `.ui-polish/artifacts/shots/`；c) 隔轮评审，不通过 revert。
> 通用修法：共性问题改令牌/组件层一次解决；品牌色误作文字时做令牌分层（文字色/实底色/装饰色分开）。

## 设计令牌来源（现有，勿新造）

- 颜色：`app/globals.css` Stage A 令牌 —— `--space-black / --surface-1..3 / --glass-bg / --glass-border / --glass-highlight / --brand-cyan|violet|indigo|pink`；深色语义层 `.dark`。文字灰阶统一 `text-white/{50,65,70,88,90,96}` 类（white 透明度阶梯），**不引入新灰系**。
- 阴影：`--elev-sm/md/lg`（tinted hue 280）+ `--glow-violet/cyan`；禁用纯黑 `rgba(0,0,0,x)` 阴影新写（存量收口到 elev 令牌）。
- 圆角：`--radius: 0.625rem` 阶梯（sm/md/lg/xl/2xl/3xl/4xl）。
- 动效：`--duration-fast: 200ms`（150–300ms 区间）；ease 统一 `--ease-cinematic: cubic-bezier(0.22,1,0.36,1)`（`src/lib/motion.ts` 的 cinematicEase 同值同源）；弹簧 springSnappy/springTight；禁 `ease-in-out`、禁 500ms+ 微交互。
- 字体：Orbitron（display/品牌）、Geist Sans（正文）、Geist Mono / JetBrains Mono（数据 `font-mono-data`）。
- 图标：lucide-react 统一（已装）；UI 内小图标 strokeWidth 1.6–1.75，视觉强调 2–2.5。

## 一致性规则

- 间距：4/8dp 网格（`--section-gap / --container-px` 已有容器令牌）。
- 点击目标：≥24px；主 CTA/返回/关闭/删除 ≥44px（min-h-11 / min-h-12，移动端放大点击区用 before: absolute inset 扩展）。
- 按钮动词统一：登录 / 进入大厅 / 返回大厅 / 重新开始 / 确认修改 / 取消（现有文案为准，不新增近义动词）。
- 错误文案：说原因 + 给出路（例：登录失败 → 「请检查用户名/密码」+ 重试入口；网络失败 → 重试按钮）。
- 空态/加载/出错：GameLoadingScreen（spinner 或真进度）+ 404 品牌页 + GameRuntimeErrorBoundary + arena 守卫空态为现有标准件，新页面复用，禁止自造。
- 焦点可见：已统一 `:focus-visible` 紫环兜底（globals.css 2026-09-22）；弹层焦点陷阱用 `useDialogA11y`。

## 默认禁止（Goal 红线）

- 禁止新增运行时依赖、渐变/动效花活、新主题；删繁就简。
- 不改业务逻辑 / API 契约 / 数据结构；只动样式层、组件结构、模板、文案。
