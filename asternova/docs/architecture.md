# AsterNova 技术架构定案

> 状态：v1.0（2026-08-30，随 BLUEPRINT.md 定稿）。本文记录**已拍板**的技术选型与红线；升级 / 换栈必须先改本文并经用户拍板。

## 1. 技术栈总览

| 层 | 选型 | 关键说明 |
|---|---|---|
| 游戏引擎 | **Godot 4.5.x stable**（钉死当前 stable 线，大版本升级需专项评估） | C++ 引擎内核 + 脚本胶水 |
| 客户端语言 | **GDScript** | 全平台导出 exe/APK/Web、包体最轻；热点兜底 shader(GPU) → GDExtension（仅原生端） |
| 渲染风格 | **NPR 卡通渲染** | toon ramp 色阶 + SDF 面部阴影 + 描边 + 后处理调教（见 STYLE.md） |
| 画质分级 | **三档（低/中/高），运行时可切** | 低：关后处理 + 降分辨率 + 帧率上限 30/45；高：全特效 + 高贴图分辨率 + 帧率解锁 |
| 后端语言 | **Go**（现有 backend 保留核心） | 60Hz tick、池化控分配；battle tick 热核独立模块，性能红线触发才可 Rust 重写 |
| 协议 | **Protobuf 消息层 + 双通道语义** | 可靠有序（登录/事件/结算）+ 不可靠高频（60Hz 快照流）；客户端 Transport 接口可插拔 |
| 传输选路 | **先全 WebSocket，原生端 ENet UDP 后置（M4）** | Web=WS（浏览器唯一选项）；原生首版也走 WS，Android 启动前再落 ENet（Go 侧库选型届时评估，CGo 交叉编译成本为主要风险项）；WebTransport / KCP 为后置升级位 |
| 数据库 | **PostgreSQL + Redis**（迁移自 MySQL，见 §5） | PG JSONB 玩家存档（schema 版本化）；Redis 在线状态/房间/匹配/排行；Go 侧 sqlc + golang-migrate |
| UI 架构 | **大厅=Web(React)，HUD=Godot**（见 §3） | 三端宿主：Win=WebView2 / Android=系统 WebView / Web=DOM |
| 资产管线 | ChatGPT 原画 → VRoid/在线 image-to-3D → Blender bpy → GLB+KTX2 | 零授权成本；本机不跑推理；M1 垂直切片先行验证（见 BLUEPRINT） |
| agent 接入 | godot-mcp + blender-mcp + GD Agentic Skills | agent 深度参与开发、建模、调试 |
| 部署 | Docker Compose + GitHub Actions | 沿用工作区约定（asterforge-deploy）；演进：单机 → 分离 → 多地域房间服 |
| 测试 | Go 确定性回放 + Godot headless (GdUnit4) + CI | 输入流回放比对快照 hash；注意 tick 内浮点/map 遍历顺序的非确定性来源 |

## 2. 服务端权威闭环（不变式，沿用现有架构）

- **后端独占物理裁决权**：`battle` 60Hz Tick 吃输入、推状态机、广播 Protobuf 快照；`match` 1Hz 撮合；`auth` HTTP/REST 签 JWT。
- **客户端只做两件事**：采集输入 + 渲染快照（Lerp 插值），不修改本地绝对坐标。
- **唯一状态源**：Web 外壳侧 UI 状态走 Zustand store，避免 DOM 与 Canvas 脱节。
- 三端共享 `game.proto`（backend ↔ client-godot 逐 message 校验一致）；改协议三端同步 + 重新生成。

## 3. UI 混合架构（2026-08-30 定案）

### 两类 UI，两个归属

| 类型 | 内容 | 实现 | 理由 |
|---|---|---|---|
| 大厅类（Meta） | 登录、主菜单、背包、商城、设置 | **一份 React 应用** | 列表/表单/图文，Web 生态效率与审美上限最高，复用既有前端技能与设计资产 |
| 战斗 HUD | 血条、技能冷却、小地图、伤害飘字 | **Godot** | 跟随 3D 世界坐标、60Hz 同步刷新；DOM 每秒改 60 次必卡 |

### 三端宿主

| 端 | 大厅宿主 | 战斗 | 备注 |
|---|---|---|---|
| Windows exe | WebView2（系统自带，包体≈0 增量）嵌 Godot 窗口 | Godot | 战斗时 WebView 隐藏挂起 |
| Android APK | 系统 WebView 嵌 Godot 界面 | Godot | Android 是架构决定性约束：无法"网页壳+弹游戏窗口"双进程，只能引擎为主内嵌 |
| Web | DOM 本身（现 web-client 模式） | Godot WASM | 现有 JSBridge 模式直接沿用 |

### 桥接与风险

- **JSBridge**：现有 web-client 的 Command（下行：注入 JWT/配置）/ Event（上行：HP/能量等）双通道协议思想直接复用到原生端。
- **最大风险**：Godot ↔ WebView 嵌入的社区方案（godot_wry 等 GDExtension）成熟度一般 → **M3 先 spike**（Windows + Android 各跑通"引擎内嵌 WebView 加载 React 页 + 双向传话"最小 demo）；跑不通的备胎：大厅 UI 退回 Godot，用 Web 思维（锚点/容器 ≈ flexbox、theme ≈ design token）先自研组件库 + 主题再铺页面。
- **web-client 角色演化**：退化为**官网 / 落地页 + Web 端 WASM 托管壳**；现有 Arcade 小游戏保留作引流位；React HUD 层在 v2 HUD 就绪后逐步退役。
- **内存代价**：WebView 常驻约 50-100MB，大厅阶段无所谓性能；战斗阶段挂起，不占渲染。

## 4. 传输层规划

```
客户端                          后端
┌─────────────────────┐        ┌──────────────────┐
│ Transport 接口(可插拔)│        │ gateway          │
│  ├ ReliableChannel   │◄─WS──►│  会话/登录/结算    │
│  └ UnreliableChannel │◄─WS──►│  60Hz 快照广播    │
│   (M4: 原生端换 ENet UDP)      │                  │
└─────────────────────┘        └──────────────────┘
```

- **接口先行**（M2）：`Transport` 抽象 + **fake transport 回环测试**为接口验收标准，保证两种实现语义一致。
- **WS 先行**：首版 Web / Windows 统一 WebSocket（桌面宽带下延迟足够）。
- **ENet 后置**（M4）：弱网收益主要在移动端；Go 侧 ENet 服务端库是边缘生态（CGo 绑定为主），届时先做选型 spike 再定，不提前引入 CGo 包袱。

## 5. 数据层迁移（M0 任务）

- 现状：MySQL 8 + GORM AutoMigrate（`gorm.io/driver/mysql`），module 名 `github.com/TimeCraker/asternova-backend`。
- 目标：**PostgreSQL + sqlc + golang-migrate**，JSONB 存玩家存档（payload 带 schema_version），module 改名 `github.com/TimeCraker/asternova-backend`。
- 本地开发数据直接弃（无生产数据），无痛切换；auth / gateway / match / battle 逻辑不动。
- Redis 职责不变：在线状态 / 房间 / 匹配队列 / 排行 ZSET。

## 6. 性能锚点（验收量化基准）

| 档位 | 基准设备 | 目标 |
|---|---|---|
| 低档 | 核显笔记本（Intel Iris Xe / AMD 680M）· 骁龙 778G | 低画质档，帧率上限 30/45，稳定不卡顿 |
| 高档 | RTX 3060 及以上 · 骁龙 8 Gen2 及以上 | 高画质 + 高贴图分辨率，帧率解锁 120 |
| 后端 | 单机（沿用腾讯云） | 60Hz tick 预算 16.6ms 内、无积压；RTT 公网 P95 <80ms（旧压测已达标，迁移后复测） |

> 「低配流畅」不量化就会在验收时扯皮——上表是性能相关改动的验收锚点，写进 CI 基准。

## 7. 安全基线

- HTTPS-only；JWT 密钥 / SMTP 授权码等一律环境变量，永不入库（已有改造保持）。
- WS Origin 白名单校验（已有）；token 轮换机制随 M2 Transport 重构一并落地。
- 服务端权威本身是防作弊根基（客户端零裁决权）；输入合法性在 gateway 校验（范围/频率）。
- 验证码限流（已有）；PG 迁移后账号体系沿用 auth 模块（bcrypt + 邮箱验证）。

## 8. 红线

1. 性能优化必须以实测数据为准（tick 16.6ms / GC 停顿 / RTT P95），不凭感觉换语言换组件。
2. 破坏性操作先确认；不混仓库提交；切换工具前检查 `git status`。
3. 渲染与资产必须先出验证件给用户过目，验收通过才批量生产。
4. 玩法方向变化导致的架构级调整（如快照频率），先改 BLUEPRINT.md 再动代码。
