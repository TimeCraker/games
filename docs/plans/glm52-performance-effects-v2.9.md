# GLM-5.2 执行计划：v2.9 帧率、性能与特效优化

> 直接交给 GLM-5.2 执行。不要修改 v2.8 已完成的动漫主页、移动端布局和图片裁切。

## 项目上下文

- 项目：`C:/Users/TimeCraker/Desktop/my_workspace/huanrui-xiaoxiaole`
- 分支：`v2-fullgame`
- 线上：`https://game.asterforge.top/xiaoxiaole/`
- 技术：纯 HTML/CSS/JS、DOM 棋盘、Canvas 特效、无构建依赖
- 核心文件：`public/game.js`、`public/styles.css`、`public/sw.js`
- 当前测试：`node tools/test.js`、`node tools/test_visual_v28.js`
- 铁律：先基准、再修改；每完成一个 Task 立即勾选并 commit；只改性能/特效，不改 UI 方向、图片和玩法平衡。

## 已确认的真实瓶颈

1. `tickParticles()` 从启动起永久 RAF，即使 `particles.length===0` 仍每帧清除整张高 DPR Canvas。
2. `tickBgStars()` 永久 RAF；非霓虹背景也每帧 `clearRect()` 全屏 Canvas。
3. `resizeFx()` / `resizeBgCanvas()` 直接使用未封顶的 `devicePixelRatio`。3× DPR 手机的像素工作量约为 1× 的 9 倍。
4. `tickParticles()` 每帧通过 `particles.filter()` 创建新数组，并对每颗粒子 `save()/restore()`。
5. 每个消除方块固定生成 16 粒子；大连锁时粒子数量瞬间成倍增加，缺少总预算。
6. 64 个 DOM 方块叠加多层 `box-shadow`、3D transform；彩虹方块持续执行 `filter:hue-rotate()` + `drop-shadow()`。
7. 移动端多个面板使用 `backdrop-filter:blur(14px)`，实时毛玻璃扩大合成/采样成本。
8. 拖动 `pointermove` 每个事件直接写 transform，没有 RAF 合帧。
9. 分数/连击动画通过 `offsetWidth` 强制同步布局刷新。
10. 页面进入后台后 Canvas 动画没有统一暂停；设置关闭动效时 JS Canvas 仍可能继续运行。

## 性能目标（验收门槛）

测试视口以 `375×812` 为主，Chrome Mobile Emulation + 一台真实中端 Android：

- 静止游戏画面：无活动特效、非霓虹背景时，不存在持续 Canvas RAF；CPU 接近空闲。
- 普通交换/消除：平均 FPS ≥ 55，P95 帧耗时 ≤ 24ms。
- 8 个以上方块连锁：P95 帧耗时 ≤ 32ms，不出现连续 3 帧以上明显卡顿。
- 单次操作 Long Task：正常交换无 >100ms；复杂连锁最多 1 个 >100ms。
- 30 次交换后 JS Heap 不持续增长，回落后相对基线增量 <10MB。
- 首屏 Lighthouse Mobile：Performance ≥90、LCP ≤2.5s、CLS ≤0.05、TBT ≤200ms。
- 功能回归：64 tiles、交换、连锁、炸弹、彩虹、提示、暂停、胜负、设置均正常。

---

## Task 0 — 建立可重复基准（必须先做）

- [ ] 新建 `docs/stages/stage-v2.9-performance-effects.md`，复制本计划 Tasks 并逐项勾选。
- [ ] 新建 `tools/test_perf.js`：记录 10 秒 RAF 帧间隔、平均 FPS、P95/P99、Long Tasks、JS Heap（支持时）。
- [ ] 测试脚本必须包含：静止 5 秒、连续随机交换 20 次、等待回落 5 秒。
- [ ] 使用 `PerformanceObserver({entryTypes:['longtask']})` 采集 Long Task。
- [ ] 跑本地 Lighthouse Mobile 3 次取中位数，并将原始结果保存到 `docs/perf/baseline/`。
- [ ] 保存 Chrome Performance trace 或至少保存 JSON 指标，不允许只凭肉眼说“变流畅”。
- [ ] 记录修改前结果到 stage 文档并 commit。

建议命令：

```bash
node tools/test_perf.js
node tools/test.js
node tools/test_visual_v28.js
# Lighthouse 使用 perf-audit skill 或 npx lighthouse，需 cache-bust
```

## Task 1 — 将永久 RAF 改成按需调度（最高优先级）

### 粒子 Canvas

- [ ] 增加 `particleRAF=null`。
- [ ] `spawnParticles()` / `shockwave()` 仅在 RAF 未运行时启动 `tickParticles()`。
- [ ] 粒子清空后执行一次 `clearRect()`，随后停止 RAF 并设回 `null`。
- [ ] `clearBoard()`、离开游戏、页面 hidden 时取消粒子 RAF。

### 背景星粒子

- [ ] 只在 `data-bg==='neon' && settings.motion && !document.hidden` 时运行星空 RAF。
- [ ] 切换到 cloud/photo、关闭动效、页面进入后台时立即 cancel RAF 并清屏。
- [ ] 使用统一 `syncAnimationLoops()`，由 `setBg()`、设置变更、`visibilitychange` 调用。
- [ ] 禁止在 `start()` 无条件启动两个永久循环。

### 验收

- [ ] 静止 cloud/photo 游戏页 5 秒内 Canvas draw 调用为 0。
- [ ] 切到后台后全部 RAF 停止；回前台按状态恢复。
- [ ] commit：`perf(raf): 按需调度 Canvas 动画 / schedule canvas loops on demand`

## Task 2 — Canvas 分辨率与粒子预算

- [ ] 引入效果 DPR：移动端 `min(devicePixelRatio,1.5)`，桌面 `min(devicePixelRatio,2)`；背景 Canvas 可进一步封顶 1.25/1.5。
- [ ] 使用 `ResizeObserver(boardEl)`，仅尺寸实际变化时重设 Canvas，避免无意义清空和重分配。
- [ ] 设置硬粒子预算：移动端最多 96，桌面最多 160；超预算时丢弃最老或降低本次生成量。
- [ ] 普通移动端每格 6～8 粒子，特殊方块 10～12；禁止继续固定 16。
- [ ] 将 `particles.filter()` 改为原地倒序更新/压缩，避免每帧分配数组。
- [ ] 合并 Canvas 状态：同色粒子批量绘制，避免每颗粒子 `save/restore`；至少取消不必要的 `save/restore`。
- [ ] 增加粒子对象池，生命周期结束回收；对象池设上限，禁止无限增长。
- [ ] `settings.motion===false` 或 `prefers-reduced-motion` 时：不生成粒子，仅保留 120～180ms 的方块缩放/淡出。
- [ ] commit：`perf(canvas): 限制 DPR 与粒子预算 / cap DPR and particle budget`

## Task 3 — 移动端 CSS 合成与绘制降本

在 `@media (max-width:960px)` 下执行，不改变当前布局：

- [ ] 游戏中的 `.panel-card`、`.hud-stat` 改为高不透明度纯色/渐变背景，移除或降至 `blur(4px)`，优先完全移除 `backdrop-filter`。
- [ ] `.board`、`.board-3d::before` 阴影从多层大半径缩为一层小半径。
- [ ] tile 阴影保留一层外阴影 + 一层 inset，删除重复大模糊半径。
- [ ] 彩虹特殊方块禁止持续 `filter:hue-rotate()`；改为旋转 conic-gradient 伪元素，只动画 `transform`。
- [ ] 炸弹/提示禁止动画 `filter/drop-shadow/brightness`；改为伪元素光圈的 `opacity + transform`。
- [ ] 全屏 combo flash 使用纯 opacity 渐变层，避免动画巨型 inset box-shadow。
- [ ] 给 `.board` 增加合理的 `contain:layout paint style`；确认不裁切浮字/粒子后再提交。
- [ ] 不要滥用永久 `will-change`；只在 dragging/removing/spawning 状态临时添加。
- [ ] 使用 DevTools Layers 检查：不要让 64 个 tile 全部常驻独立合成层。
- [ ] commit：`perf(css): 降低移动端滤镜与合成成本 / reduce mobile paint cost`

## Task 4 — 输入、DOM 与布局批处理

- [ ] `pointermove` 只保存最新坐标，由单个 drag RAF 写入 transform；`pointerup/cancel` 清理 RAF。
- [ ] 缓存 tile 元素列表；热路径不要反复 `querySelectorAll('.tile')`。
- [ ] 将连续 DOM 写操作集中到同一 RAF，所有布局读（rect/clientWidth）在写之前完成。
- [ ] `comboFlash()`、分数 bump 使用 Web Animations API 或双 RAF 重启动画，移除 `void offsetWidth` 强制 reflow。
- [ ] 棋盘初始化 64 个错峰 `setTimeout` 改成 CSS delay 变量或最多一条 RAF 时间线。
- [ ] `resize` 使用 80～120ms debounce；棋盘尺寸变化用 ResizeObserver。
- [ ] 预解码 4 张方块图：首关前 `Promise.all(images.map(img.decode))`，避免首次交换/洗牌解码抖动。
- [ ] commit：`perf(dom): 合帧输入与 DOM 更新 / batch input and DOM updates`

## Task 5 — 质量档位与“更好但更省”的特效

实现 `effectsQuality: auto | high | medium | low`，默认 auto：

- 自动参考 `navigator.deviceMemory`、`hardwareConcurrency`、`devicePixelRatio`、`navigator.connection.saveData`。
- Low：DPR 1、粒子 4/格、无屏震/毛玻璃/彩虹滤镜、短淡入淡出。
- Medium：DPR 1.5、粒子 8/格、单层冲击波、轻微屏震。
- High：DPR 2、粒子 12/格、最多 2 层冲击波、完整连击强调。

特效升级原则：**减少数量、提高信息表达**。

- [ ] 消除前 100～140ms：匹配方块统一轻微缩放 + 高亮边框，仅 transform/opacity。
- [ ] 普通消除：6～12 个方向明确的粒子，不做大量随机噪点。
- [ ] 四连炸弹：一层快速冲击波 + 4 条方向线；不要 3 个重复圆环。
- [ ] 五连彩虹：旋转色环 + 单次径向扫光，不使用持续 hue filter。
- [ ] 连击按 2/3/5/8 档改变颜色、音高和震动，避免每次都全屏闪。
- [ ] 特效全部复用一个 Canvas 和对象池，禁止新增每粒子 DOM。
- [ ] 在设置面板增加“特效质量：自动/高/中/低”，保存到 localStorage。
- [ ] `prefers-reduced-motion` 永远覆盖质量档位。
- [ ] commit：`feat(effects): 自适应质量与轻量特效 / adaptive effects quality`

## Task 6 — 回归、性能对比与部署

- [ ] 连续运行 3 次 `node tools/test_perf.js`，取中位数并写入 `docs/perf/after/`。
- [ ] 运行 `node tools/test.js`、`node tools/test_visual_v28.js`，必须 0 error。
- [ ] 使用 375×812、844×390、1366×768 三种视口截图对比，布局不可回退。
- [ ] 验证 `prefers-reduced-motion`、动效关闭、页面后台、低质量档位。
- [ ] Chrome Performance trace 检查：主线程无持续空转，普通交换没有连续长帧。
- [ ] Lighthouse Mobile 3 次取中位数，与 baseline 表格对比。
- [ ] 更新 Service Worker 缓存版本，部署后验证线上缓存与资源。
- [ ] stage 全部勾选后最终 commit，汇报“数据前/后”，禁止只写主观结论。

## 禁止事项

- 不重写为 Canvas 全棋盘、WebGL、React 或游戏引擎；当前 DOM 持久化架构可以优化好，避免过度架构。
- 不改变 v2.8 的动漫主页、图片素材、关卡目标和分数平衡。
- 不以关闭全部特效冒充性能优化；必须保留 Medium 档的游戏反馈。
- 不永久开启 `will-change` 给 64 个方块。
- 不在没有基准数据时声称 FPS 已提升。
- 不一次修改全部阶段；每个 Task 独立测试、勾选、commit，出问题可回滚。
