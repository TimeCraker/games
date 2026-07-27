# Stage v2.9 - 帧率、性能与特效优化（GLM-5.2 执行）

## Task 0 - 建立可重复基准
- [x] 新建 stage 文档
- [x] 新建 `tools/test_perf.js`
- [x] 跑 baseline perf + Lighthouse，保存到 `docs/perf/baseline/`
- [x] 记录修改前结果并 commit

### Baseline 数据 (375×812 headless)
- 静止: 179.9 fps (avg 5.56ms, p95 9.1ms) — **持续空转，证明永久 RAF 存在**
- 交换: 170.6 fps (avg 5.86ms, p95 9.1ms, p99 9.2ms)
- 回落: 179.8 fps (avg 5.56ms)
- LongTask: 0 个, >100ms 0 个
- Heap: used 3MB / total 4MB
- Lighthouse: Windows npx 超时，Task 6 重试

## Task 1 - 按需调度 Canvas 动画
- [x] 粒子 Canvas 按需 RAF
- [x] 背景星粒子仅 neon 运行
- [x] 统一 syncAnimationLoops + visibilitychange
- [x] 验收：静止 cloud/photo 无 Canvas draw；后台停 RAF
- [x] commit

### 验收: cloud 静止 RAF=0, 后台 RAF=0 (test_raf.js)

## Task 2 - Canvas 分辨率与粒子预算
- [x] 效果 DPR 封顶（移动 1.5 / 桌面 2）
- [x] ResizeObserver
- [x] 粒子预算 + 原地压缩 + 对象池
- [x] 关闭动效时不生成粒子
- [x] commit

### 验收: 静止 RAF=0, 粒子移动端封顶96, DPR封顶1.5

## Task 3 - 移动端 CSS 合成降本
- [ ] 移除/降级 backdrop-filter
- [ ] 简化阴影
- [ ] 彩虹/炸弹/提示改 transform/opacity
- [ ] combo flash 改 opacity 层
- [ ] contain + 临时 will-change
- [ ] commit

## Task 4 - 输入、DOM 批处理
- [ ] pointermove RAF 合帧
- [ ] 缓存 tile 列表
- [ ] DOM 写批处理
- [ ] 移除 offsetWidth reflow
- [ ] 初始化错峰改 CSS delay
- [ ] resize debounce + ResizeObserver
- [ ] 预解码方块图
- [ ] commit

## Task 5 - 质量档位与轻量特效
- [ ] effectsQuality auto/high/medium/low
- [ ] 消除前预闪烁
- [ ] 炸弹/彩虹特效精简
- [ ] 连击分档强调
- [ ] 设置面板加质量选择
- [ ] prefers-reduced-motion 覆盖
- [ ] commit

## Task 6 - 回归、对比、部署
- [ ] 3 次 perf 中位数写入 after/
- [ ] test.js + test_visual_v28.js 0 error
- [ ] 三视口截图对比
- [ ] Lighthouse 对比
- [ ] SW 缓存版本 + 部署
- [ ] 最终 commit + 数据汇报
