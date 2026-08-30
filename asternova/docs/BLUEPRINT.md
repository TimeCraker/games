# AsterNova 总蓝图（BLUEPRINT）

> 状态：**v1.0 定稿**（2026-08-30）。本文是 AsterNova 所有开发决策的最高锚点；任何实现与本文冲突时以本文为准，修改本文必须由用户（TimeCraker）拍板。
>
> 配套文档：[architecture.md](architecture.md)（技术定案）· [STYLE.md](STYLE.md)（美术风格圣经）

## 愿景

- **先做出高质量的游戏**，暂不考虑商业化；玩法文案在 M1 后由用户主导定稿（见「玩法占位」）。
- **轻量高性能**：低配设备流畅，高配设备享受更高帧率与更精致画面（三档画质分级，运行时可切）。
- **画面走二次元角色渲染**：对标崩铁 / 原神 / 绝区零 / 终末地 / 鸣潮的画风（toon ramp + SDF 面部阴影 + 描边 + 后处理），风格化路线，不做写实。
  - 预期管理：可复制的是**技术管线**；零授权 AI 资产管线的现实上限是"风格统一、干净讨喜的独立游戏二次元画风"，逼近上限靠 STYLE.md 约束 + 用户验收把关。
- **全栈零授权成本**，只用开源 / 免费工具；本机不跑 AI 推理。
- **分工**：用户只负责指挥、设计玩法、审核验收；代码、建模、测试、部署全部由 agent 完成。所有改动必须可验证（测试 / 构建 / 真实运行），渲染与资产先出验证件给用户过目再批量生产。

## 产品形态

- **三端**：Windows exe / Android APK / Web（浏览器 WASM）。
- **服务端权威实时联机**：保留现有 Go 后端 60Hz 战斗核心（已压测达标），客户端只做输入采集 + 快照插值渲染。
- **UI 混合架构**（2026-08-30 定案）：
  - **大厅类 UI**（登录 / 主菜单 / 背包 / 商城 / 设置）= **Web**：一份 React 应用，三端宿主加载。
  - **战斗 HUD**（血条 / 技能冷却 / 小地图 / 伤害飘字）= **Godot**：跟随 3D 世界、60Hz 高频刷新，Web 技术做 HUD 是性能灾难，无争议归引擎。
  - 三端宿主：Windows = WebView2（系统自带，包体零增量）/ Android = 系统 WebView / Web = DOM 本身。战斗时 WebView 隐藏挂起，Godot 独占渲染。
  - **风险与备胎**：Godot 嵌 WebView 的社区方案（godot_wry 等）成熟度一般，M3 先做嵌入 spike；跑不通则大厅 UI 退回 Godot 实现（用 Web 思维自研组件库 + 主题后再铺页面）。

## 里程碑

### M0 蓝图定稿与仓库整理 ✅ **已关闭（2026-08-30）**

- [x] 技术栈定案（本文 + architecture.md）
- [x] client-unity 归档（2026-08-30，`git log` 可追溯）
- [x] 旧 client-godot 冻结标记（FROZEN.md）
- [x] 重写根 README.md 与 games/CLAUDE.md
- [x] backend 迁移 PostgreSQL + module 改名 `github.com/TimeCraker/asternova-backend`（2026-08-30 验收通过：sqlc + golang-migrate + JSONB，8 包单测全绿，动态冒烟复验；验收修复 `ac56510`：Redis 地址与游客邀请码 env 化）
- [ ] STYLE.md 从骨架填充为可执行的资产生成约束（**归 M1**，随垂直切片迭代）
- [x] 收尾清理：.cursorrules ×3、.roo/rules、.wiki.git 出清

### M1 渲染垂直切片（美术验证件）← **当前（与 M2 并行）**

一个二次元人形角色 + **黄昏樱花商店街**场景（2026-08-30 用户定案：日漫动画樱花场景气质，参考《路人女主》樱花斜坡一脉动画观感）走完整条资产管线（原画 → 粗模 → Blender 打磨 → 二次元渲染四件套 → 三档画质），出真机截图 / 视频给用户验收。

- 验收标准：**用户对画面水准说"过"**，才允许批量生产；不过则迭代管线或调 STYLE.md。
- 同时验证：VRoid / 在线 image-to-3D 出的粗模拓扑是否可用；若角色非日式人形，管线的 VRoid 环要替换。

### M2 Transport 抽象 + client-godot-v2 骨架 ← **当前（与 M1 并行）**

- [ ] Transport 抽象接口（可靠有序 / 不可靠高频双通道语义）+ **fake transport 回环测试**作为接口验收标准
- [ ] 两个槽位先用 WebSocket 实现（Web / 原生统一），ENet 实现后置到 M4
- [ ] client-godot-v2 场景骨架 → 战斗循环 → 逐功能从旧 client-godot 迁入
- [ ] UI 先最简（dev 直连模式），大厅 UI 后置到 M3
- [ ] guest-login 补 IP 限流（M0 验收移交：接口保留，env 门禁已加，限流窗口待补）
- [ ] RTT P95 公网复测（M0 验收移交：PG 迁移后基准重校，目标仍 <80ms，出对比图表）

> 执行细则见 [stage-specs/m2-transport-and-v2-skeleton.md](stage-specs/m2-transport-and-v2-skeleton.md)

### M3 Windows exe 首验证 + WebView 嵌入 spike

- [ ] 战斗循环闭环：登录 → 匹配 → 战斗 → 结算
- [ ] **WebView2 嵌入 spike**：Godot 窗口内嵌 WebView2 加载 React 大厅页 + 双向传话（复用 JSBridge 协议思想）跑通 → 大厅 UI 正式铺开；跑不通 → 启动备胎（全 Godot UI）
- [ ] 交付一键可跑的 Windows exe demo build

### M4 Android + ENet + 画质分级真机验证

- [ ] Android WebView 嵌入 spike + APK 交付
- [ ] ENet UDP 双通道落地（Godot 内置 ENet ↔ Go 侧选型届时定，CGo 交叉编译成本是主要评估项）
- [ ] 低 / 高档基准设备真机跑分（见 architecture.md「性能锚点」）

## 验收节奏

- **agent 日常闭环**：headless 测试（Go 回放 / GdUnit4）+ 截图自检，不事事上抛。
- **用户验收**：每个里程碑交付一键可跑的 demo build，用户只验里程碑件；用户时间优先花在玩法决策与美术验收。
- **性能红线**：tick 预算 16.6ms / GC 停顿 / RTT P95 一律以实测数据为准，不凭感觉换语言换组件；battle tick 热核保持独立模块，性能红线触发才可用 Rust 重写该模块。

## 玩法占位（M1 后由用户定稿）

- 品类 / 同屏人数 / 单局时长 / 首发角色规模 / PvP or PvE：**待定**。
- 已知边界：60Hz 服务端权威架构适合实时竞技动作品类；若最终玩法偏 PvE 轻量，快照频率可降到 20-30Hz 省一半同步成本——此项在玩法定稿时复核。

## 遗留资产处置

| 资产 | 处置 |
|---|---|
| `asternova/client-unity/` | 已归档（git rm，历史可追溯） |
| `asternova/client-godot/` | 冻结为参考实现（见其 FROZEN.md），自研 ProtoParser.gd 等 v2 需要时再评估复用 |
| `asternova/web-client/` Arcade 小游戏 | 保留，随 web-client 退化为官网 + Web 托管壳后作为引流位挂官网 |
| 线上旧版（game.asterforge.top） | 冻结展示态，不阻塞新栈开发 |
