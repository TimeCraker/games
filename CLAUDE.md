# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库性质

这是 **AsterNova 游戏矩阵 monorepo**，单一 Git 仓库（远端 `github.com/TimeCraker/games.git`，分支 `main`）。所有实际内容在 `asternova/` 下；根目录只有本文件和 `README.md`。

关键认知：`asternova/{web-client,backend,client-godot,client-unity,assets}` **不再是各自独立的 Git 仓库**——它们由 6 个原仓库通过 `git subtree add`（不 squash）合并而来，完整提交历史在 `git log` 中可追溯，原仓库已归档只读。不要在这些子目录里再 `git init` 或期望独立的 remote。

工作区上层 `../CLAUDE.md` 给了 monorepo 矩阵的一行概述；本文件只覆盖 `games/` 仓库自身的架构与命令。

## 整体架构（big picture）

**AsterNova 是服务端权威（server-authoritative）的实时多人动作游戏**。理解下面这条闭环是改任何战斗相关代码的前提：

- **后端（Go）独占物理裁决权**：`battle` 服务跑 **60Hz Tick**，吃客户端输入、推进状态机、广播 `State Snapshot`（Protobuf 编码）。`match` 服务以 **1Hz** 异步撮合，`auth` 走 HTTP/REST 签 JWT。
- **三个客户端（Web / Godot / Unity）只做两件事**：采集输入 + 渲染快照（Lerp 插值）。客户端**不修改本地绝对坐标**，所有位置以后端下发的快照为准。
- **Web 端是宿主外壳（Game Shell），不是战斗通道**：Next.js 负责登录、大厅、HUD 和 WASM 容器；真正的 60Hz 战斗由 WASM 引擎（Godot/Unity）**直连后端 WebSocket**，绕过 Web 层。外壳与引擎通过 JSBridge 双通道通信：
  - Command（下行）：把 JWT / 配置注入 WASM 沙箱。
  - Event（上行）：引擎抛出 HP / 能量等高频事件给 React。
- **唯一状态源**：外壳 UI 与游戏状态都走 `web-client/src/store/useGameStore.ts`（Zustand），避免 DOM 与 Canvas 状态脱节。

**联机匹配流程**（`app/lobby/page.tsx`）：大厅开 `WebSocket {wsUrl}?scope=lobby` → 发 `match_req` → 收 `match_success {room_id}` → 写入 store → 跳 `/arena`。`/arena` 有严格路由守卫：战斗中刷新会判逃跑，**清空 token/userId 并踢回 `/login`**。

**休闲小游戏**（`/lobby` 的 Arcade 区，纯前端零后端）：`/shoot-them-all`（matter-js 物理）、`/lets-running`、`/merge`、`/nebula-survivor`、`/xiaoxiaole`（立体三消 12 关）。这些路由各自挂在 `app/<game>/page.tsx` + `src/components/<game>/`。

**共享协议（铁律：保持同步）**：`backend/services/proto/game.proto` 与 `client-godot/proto/game.proto` 必须一致（当前已逐 message 校验一致）。Unity 端用对应的生成代码。改协议要三端一起改 + 重新生成 `game.pb.go`。

## 子项目与命令

### `asternova/web-client/` — Next.js 16 Game Shell（React 19 + TS + Tailwind v4 + Zustand + framer-motion + three + matter-js + react-unity-webgl）

⚠️ **这是 Next.js 16，与训练数据里的 Next.js 有破坏性差异。** 写代码前先读 `web-client/node_modules/next/dist/docs/` 下相关指南（`web-client/AGENTS.md` 强制要求，且该文件由 `next dev` 自动重写——提交它以保持工作树干净）。`next.config.ts` 里 `typescript.ignoreBuildErrors: true`，TS 报错不挡构建，**别拿 build 通过当类型正确**。

```bash
cd asternova/web-client
npm install
cp .env.development .env.local   # 仓库当前只有 .env.production；按需自建 .env.local
npm run dev      # 走 scripts/dev.mjs，默认 next dev --webpack
npm run build
npm run start
npm run lint
npm run clean    # 清 .next / node_modules / 构建产物
```

开发陷阱（都在 `scripts/dev.mjs` + `next.config.ts` 里）：
- **默认走 Webpack，不是 Turbopack**——Turbopack 在本项目首屏编译会 panic；要试 Turbopack 显式传 `--turbopack`。
- **dev.mjs 强制 `NEXT_PRIVATE_DEV_DIR` = 项目根**，防止从父目录（如 Desktop）跑 dev 时把目录判错。命令务必在 `web-client/` 下执行。
- **Tailwind / tw-animate-css / shadcn 的路径别名被硬解析到本目录 `node_modules`**，多目录工作区下不要动这些 alias。
- WASM 依赖 `SharedArrayBuffer`；纯 IP 局域网联调时需在 Chrome 开 `chrome://flags/#unsafely-treat-insecure-origin-as-secure`。
- `next.config.ts` 的 `rewrites` 把 `/api/proxy/:path*` 转发到 `{NEXT_PUBLIC_API_URL}/api/v1/:path*`；`headers` 给 `/godot/*.{wasm,data,js}.gz` 配 gzip 解压头。
- 环境变量统一从 `src/config/public-env.ts` 取（`apiUrlRoot` / `wsUrl` / `apiV1BaseUrl`），别散落硬编码。

目录约定：`app/`（App Router 路由）· `src/components/{game-shell,arena,lobby,game-pages,<各小游戏>,ui}` · `src/store/useGameStore.ts`（状态总线）· `src/api/{auth,jwt}.ts` · `public/godot/`（Godot 导出产物挂载点）。`web-client/CLAUDE.md` 仅 `@AGENTS.md` 一行。

### `asternova/backend/` — Go 1.25 游戏服务端（Gin + gorilla/websocket + GORM/MySQL + go-redis + JWT + Protobuf，module `github.com/TimeCraker/game-backend-demo`）

```bash
cd asternova/backend
docker compose up -d            # 起 MySQL 8 + Redis 7（+ Qdrant，仅 Roo Code 索引用）
go run main.go                  # 或 ./scripts/local_up.ps1；监听 :8081，首启 GORM AutoMigrate
./scripts/local_down.ps1        # 停服务
./scripts/local_logs.ps1        # 看日志
```

`main.go` 是唯一入口：`db.InitMySQL()` + `db.InitRedis()` → 启动 `match.GlobalMatcher`（1Hz）→ `GlobalHub.ListenMatchResults()`（撮合结果驱动开房）→ Gin 路由（全局 CORS 通配 `*`，含 OPTIONS 预检）。服务分四块，全在 `services/`：`auth/`（账户 + JWT + 验证码限流，依赖 `utils/email.go` 的 SMTP 配置）、`gateway/handlers/`（Hub 会话管理 + WS 收发）、`match/matcher.go`（1Hz 撮合）、`battle/{math,player_state,room}.go`（60Hz 物理状态机）、`proto/`（`game.proto` + 生成产物 `game.pb.go`）。

**注意**：`test/` 下只有 `test_client.go`（手动压测/网关路由模拟客户端），**没有 `*_test.go` 单测**，`go test ./...` 基本跑不出东西；验证靠跑服务 + 用 `test_client.go` 打流量。`docs/`、`backend/docs/`、各端的 `*_all_code_merged.txt` / `project_tree.txt` 是 `generate_docs` 脚本生成的全量快照，改代码后别手改这些。

### `asternova/client-godot/` — Godot 4 WASM 客户端

用 Godot 4.2+ 打开 `project.godot`。核心脚本（`scripts/`）：`GameManager.gd`（WASM↔React 跨端总线）、`BattleWsClient.gd`（60Hz WS 收发 + 粘包/重连）、`ProtoParser.gd`（**自研零依赖 Protobuf 3 编解码**，几百行纯 GDScript，不引第三方插件以压榨 WASM 体积）、`AudioManager.gd`。

因强制服务端权威，**客户端独立运行无法移动**——必须先起后端（`:8081`）并在 `GameManager.gd` 配 Mock Token。导出 Web 预设的目标路径硬编码为 `../asternova-web-client/public/godot/GoDot_game.html`（配合 Next.js 静态托管）。

### `asternova/client-unity/` — Unity WebGL 客户端

Unity 工程（`Assets/` `Packages/` `ProjectSettings/`），通过 `react-unity-webgl` 接入 web-client。导出 WebGL 后由外壳加载。

### `asternova/assets/` — 共享静态资源（logo / 架构图 / 压测图表 / 宣传图）

## 工作约定（来自上层 + 全局）

- **子仓库内提交一个独立、可验证单元后即提交**；commit 用 Conventional Commits + 中英对照，如 `feat(arena): 接入 WASM 战斗 / wire WASM combat engine`。
- **最小改动**：只动需求所需，不顺手重构；新增抽象/换技术栈前先报备。
- 改 `game.proto` 记得三端（backend pb.go / godot ProtoParser / unity）同步。
- 验证界面改动必须看真实页面与关键 API，HTTP 200 或模型声称 PASS ≠ 验收通过。
