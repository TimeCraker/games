# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库性质

这是 **AsterNova 游戏矩阵 monorepo**，单一 Git 仓库（远端 `github.com/TimeCraker/games.git`，分支 `main`）。所有实际内容在 `asternova/` 下。

**2026-08-30 项目已按新栈重启**（详见 `asternova/docs/BLUEPRINT.md`）。最高决策锚点顺序：用户当前指令 > `asternova/docs/BLUEPRINT.md`（愿景与里程碑）> `asternova/docs/architecture.md`（技术定案与红线）> 本文件（操作手册）。

历史背景：`asternova/` 各子目录由 6 个原仓库经 `git subtree add`（不 squash）合并而来，完整历史在 `git log` 可追溯。不要在子目录里 `git init` 或期望独立 remote。

## 当前状态（M0：蓝图定稿与仓库整理）

- [x] 技术栈定案、client-unity 归档、client-godot 冻结、README/CLAUDE.md 重写
- [x] **backend 迁移 PostgreSQL**（弃 GORM/MySQL → sqlc + golang-migrate，本地开发数据直接弃，module 改名 `github.com/TimeCraker/asternova-backend`）
- [ ] STYLE.md 从骨架填充为可执行约束（随 M1 切片）
- 下一里程碑：**M1 渲染垂直切片**（Aster + 黄昏樱花商店街 + 二次元渲染四件套 + 三档画质，出验证件给用户过目后才批量生产；场景定案见 STYLE.md §4）与 **M2 战斗骨架**（client-godot-v2 + GDScript 模拟核心单机可玩）并行

## 整体架构（big picture）

**AsterNova 是单机为主的 3D 动作游戏（Roguelite，绝区零/鸣潮式自由视角）+ 房主联机（2~6 人 PvE 合作）**（2026-08-31 重大定案）。发布优先级：Steam(Windows) 首发，Web=试玩 demo 引流，Android 后置。核心定案：

1. **模拟核心在 Godot 进程内（GDScript，60Hz 固定步长）**：单机 = 本地直调（零网络零序列化）；联机 = **房主进程即权威端**，广播快照；**客户端分层预测**：自己的位置/出手 = 预测 + 软校正，死亡/受击/拾取等关键结果 = 房主独裁（绝不预测），其他实体 = 快照插值。防作弊按好友场景松弛。
2. **Go backend 一期封存为二期「大型联机」起点资产**：auth/匹配/PG/Redis 不部署不开发；其 60Hz tick/快照/插值设计作为 GDScript 模拟核心的参考实现。二期切中心服务器时客户端协议层经 Transport 抽象无缝兼容（协议源 `backend/services/proto/game.proto` 演进）。
3. **UI 分界（React 主方案）**：菜单/设置类 = React（Windows 走 WebView2 嵌入；手柄用空间导航库；Steamworks 由 Godot 进程持有 + 桥接）；游戏内 HUD = Godot。M3 spike 三验收（手柄/成就弹出/嵌入稳定性），不过才退 Godot 菜单。
4. **传输与连接**：Transport 接口可插拔（WS 先行 / SteamTransport / ENet UDP 后置 M4）。**连接两套栈**：Steam 版 = Steam Networking 一条道（GodotSteam，内部自含「直连优先→自动升 Valve 免费中继」，不叠手搓逻辑）；非 Steam 版（Web demo/官网版）= 手搓降级（局域网 → IPv6 → UPnP → 打洞 → 自建中继后置）。快照热路径 = 手工二进制 + 增量 + 量化（≈20KB/s/人设计目标）；fake transport 回环含延迟/丢包混沌变体。
5. **渲染**：渲染器**全端 Compatibility**；渲染帧率与模拟解耦——模拟 60Hz 固定，渲染 120 起步上不封顶（低档锁 60 / 中档 120 / 高档解锁至显示器上限，Web demo 锁 60 豁免）。

**渲染方向**：二次元角色渲染，对标崩铁 / 原神 / 绝区零 / 终末地 / 鸣潮画风（toon ramp + SDF 面部阴影 + 描边 inverted hull + 后处理）+ 三档画质（低档=核显/骁龙778G **锁 60**；中档=120；高档=RTX 3060/骁龙 8 Gen2 **解锁至显示器上限**；Web demo 锁 60 豁免），渲染器**全端 Compatibility**。美术资产生成的一切约束以 `docs/STYLE.md` 为准，**先出验证件给用户过目再批量生产**。

## 子项目与命令

### `asternova/web-client/` — Next.js 16 Game Shell（React 19 + TS + Tailwind v4 + Zustand + framer-motion + three + matter-js）

⚠️ **Next.js 16 与训练数据有破坏性差异**，写代码前先读 `web-client/node_modules/next/dist/docs/`（`AGENTS.md` 强制要求且由 `next dev` 自动重写——提交它保持工作树干净）。`next.config.ts` 有 `typescript.ignoreBuildErrors: true`，**别拿 build 通过当类型正确**。

```bash
cd asternova/web-client
npm install
cp .env.development .env.local   # 仓库当前只有 .env.production；按需自建 .env.local
npm run dev      # 走 scripts/dev.mjs，默认 next dev --webpack
npm run build && npm run start && npm run lint
```

开发陷阱：默认 Webpack 非 Turbopack（Turbopack 首屏编译 panic）；`dev.mjs` 强制 `NEXT_PRIVATE_DEV_DIR`=项目根，命令务必在本目录执行；Tailwind/tw-animate-css 路径 alias 硬解析到本目录 `node_modules`，别动；WASM 依赖 `SharedArrayBuffer`，纯 IP 局域网联调需 Chrome 开 `chrome://flags/#unsafely-treat-insecure-origin-as-secure`；`rewrites` 把 `/api/proxy/:path*` 转发到 `{NEXT_PUBLIC_API_URL}/api/v1/:path*`；环境变量统一从 `src/config/public-env.ts` 取。

目录：`app/`（路由，含 Arcade 小游戏 `/shoot-them-all` `/lets-running` `/merge` `/nebula-survivor` `/xiaoxiaole`）· `src/components/` · `src/store/useGameStore.ts`（Zustand 状态总线）· `src/api/` · `public/godot/`（WASM 挂载点）。

**角色演化**：随 v2 推进退化为官网 + Web 托管壳；Arcade 保留作引流位；React HUD 在 v2 HUD 就绪后逐步退役。

### `asternova/backend/` — Go 游戏服务端（❄️ 一期封存：二期「大型联机」起点资产，不部署不开发）

```bash
cd asternova/backend
docker compose up -d    # PostgreSQL 16 + Redis 7
go run main.go          # 监听 :8081，启动时自动 migrate up（内嵌 golang-migrate）
./scripts/local_{up,down,logs}.ps1
```

`main.go` 唯一入口：`db.InitPostgres(migrationsFS)`（内嵌迁移自动 up）+ `db.InitRedis()` → `match.GlobalMatcher`(1Hz) → `GlobalHub.ListenMatchResults()` → Gin 路由（CORS 通配）。服务四块（`services/`）：`auth/`（账户+JWT+验证码限流）· `gateway/handlers/`（Hub 会话 + WS 收发）· `match/matcher.go`（1Hz 撮合）· `battle/`（60Hz 物理状态机）· `proto/`。

**存储层**：SQL 只在 `queries/*.sql` 声明 → `sqlc generate` 生成 `services/auth/db/sqlc/`（产物入库，业务禁止手写内联 SQL）；迁移文件 `migrations/`（golang-migrate 格式，up/down 成对，启动时 embed 后自动 up）；玩家存档类数据用 JSONB 列 + payload 内 schema_version（见 `player_positions` 表与 `posPayload`）。

**测试现状**：`services/` 下已有 9 包单测（auth 全域 + battle + gateway + match + proto，`go test ./...` 全绿）；端到端验证仍需起服务打真实流量（`/health`、`/api/guest-login`（需 env `GUEST_INVITE_CODE`，未配置返回 503 禁用）、双端进房快照流，`test/test_client.go` 为手动压测客户端）。M2 起引入确定性回放测试（输入流回放比对快照 hash）。`docs/`、`*_all_code_merged.txt` 是生成脚本的全量快照，别手改。

### `asternova/client-godot/` — 一代 Godot 客户端（❄️ 已冻结）

见其 `FROZEN.md`。不再开发；`ProtoParser.gd`（自研零依赖 Protobuf）、`BattleWsClient.gd`（60Hz WS + 粘包/重连）、`GameManager.gd`（JSBridge 总线）在 client-godot-v2（M2 启动）需要时参考复用。导出预设路径硬编码为 web-client 的 `public/godot/`。

### `asternova/docs/` — 蓝图与设计文档（决策锚点，改需用户拍板）

`BLUEPRINT.md`（愿景+里程碑+核心玩法定案+验收节奏）· `architecture.md`（技术定案+性能锚点+安全基线+红线）· `STYLE.md`（美术风格圣经）· `CONTENT_BACKLOG.md`（创意内容池备忘）。

### `asternova/art/` — 美术与角色资产库（自包含角色包 / 模型 / 场景贴图）

`characters/aster/`（Aster 完整自包含包：设定档 `aster.md` + 官方定稿三视图 `turnaround-final.png`）· `environments/`（场景原画与贴图）· `ui/`（游戏界面资产）。

### `asternova/assets/` — 共享静态资源（logo / 架构图 / 压测图表 / README 引用）

## 遗留与陷阱（subtree 带来的旧文件，勿误读）

- **旧 AI 规则文件已全部清除**（2026-08-30）：三份 `.cursorrules` 与 `.roo/rules/*`（backend_rules.md 为旧 Cursor 规则的原样复制）均已删除，勿再引入。有效规则 = 全局 rules + 本文件 + docs/ 蓝图。
- **CI 是死文件**：`backend/.github/workflows/ci.yml` 与 `web-client/.github/workflows/ci.yml` 不被 GitHub 执行（Actions 只认仓库根 `.github/workflows/`，本仓库没有）→ **当前无生效 CI**。建真 CI 时放仓库根，两份旧文件可作模板（backend：vet/test/build；web-client：lint non-blocking + build）。
- **旧版线上运维知识**在 `backend/.agents/skills/game-asternova/SKILL.md`：线上旧版跑在阿里云（game.asterforge.top → :3001 / api.asterforge.top → :8081，CynosDB MySQL + Redis :6380），服务器内存仅 1.6GB、**禁止在服务器编译**（本地交叉编译后上传）——仅维护线上旧版时参考；新栈部署以工作区 asterforge-deploy 体系为准。
## 工作约定

- **完成一个独立、可验证单元后即提交**；Conventional Commits + 中英对照，如 `feat(arena): 接入 WASM 战斗 / wire WASM combat engine`。
- **最小改动**：只动需求所需，不顺手重构；换技术栈/加抽象先报备。
- **技术卡点与方案校准（死磕红线）**：当发现一个技术方案或修复手段尝试很久都达不到预期效果时，严禁在错误基模/劣质路径上死磕打补丁；**必须果断停下，跳出局部死循环，深度调研工业界成熟标杆（如原神/鸣潮/米哈游等工业级管线）的最佳实践与技术选型**，校准方向、与用户对齐后再执行。
- **红线**（完整版见 architecture.md §8）：性能优化以实测数据为准（tick 16.6ms / GC / RTT P95），不凭感觉换语言；破坏性操作先确认；渲染与资产先出验证件再批量生产；玩法方向导致的架构调整先改 BLUEPRINT 再动代码。
- 验证界面改动必须看真实页面与关键 API，HTTP 200 或模型声称 PASS ≠ 验收通过。
- 安全：密钥一律环境变量永不入库；不输出完整环境变量清单，只查指定变量报 SET/UNSET。
