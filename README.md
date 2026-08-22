<div align="center">

<img src="assets/banner.svg" alt="AsterNova" width="880"/>

# AsterNova

**服务端权威的实时联机游戏矩阵**

一套协议 · 一个 Go 后端 · 三端客户端（Web / Unity / Godot），外加纯前端休闲 Arcade。

[在线试玩](https://asterforge.top/game) · [压测报告](#压测) · [架构](#架构)

</div>

---

## 架构

**后端独占裁决权**：Go 服务跑 60Hz 帧同步，吃输入、推状态、广播快照；客户端只做两件事——采集输入、Lerp 插值渲染快照。Web 外壳（Next.js）负责登录 / 大厅 / HUD，真正的战斗由 WASM 引擎直连后端 WebSocket，绕过 Web 层。

<div align="center">
<img src="assets/architecture.svg" alt="AsterNova 架构" width="880"/>
</div>

| 层 | 技术 | 职责 |
|---|---|---|
| Web 外壳 | Next.js 16 · React 19 · Zustand | 登录 / 大厅 / HUD / WASM 容器 · Arcade 休闲区 |
| 战斗引擎 | Godot 4 (WASM) · Unity (WebGL) | 60Hz 输入收发 · 快照插值 · JSBridge 与外壳通信 |
| 后端 | Go · Gin · gorilla/ws | **battle** 60Hz 物理状态机 · **match** 1Hz 撮合 · **auth** JWT · **gateway** WS Hub |
| 存储 | MySQL 8 · Redis 7 | 账户战绩 · 匹配队列与会话态 |
| 协议 | Protobuf | 三端共享一份 `game.proto`，改协议三端同步 |

> Godot 端为压榨 WASM 体积，Protobuf 编解码是**几百行纯 GDScript 手写实现**，零第三方依赖。

## 压测

单机腾讯云，Go 后端压测数据（完整图表见 `asternova/assets/`）：

| 指标 | 结果 |
|---|---|
| 帧同步稳定性 | 60Hz tick 长尾稳定，无积压 |
| RTT | 局域网 <10ms · 公网 P95 <80ms |
| CPU | 满房间并发下单核占用可控 |

## Arcade · 休闲矩阵

大厅 `/lobby` 内置纯前端小游戏（零后端依赖）：立体三消「桓睿消消乐」12 关 · `shoot-them-all` 物理弹幕 · `lets-running` · `merge` · `nebula-survivor`。

## Monorepo 结构

```
games/
└── asternova/
    ├── web-client/     # Next.js 16 Game Shell + Arcade
    ├── backend/        # Go · Gin · WS · MySQL · Redis
    ├── client-godot/   # Godot 4 → WASM
    ├── client-unity/   # Unity → WebGL
    └── assets/         # 共享静态资源
```

六个原仓库经 `git subtree add`（保留完整历史）合并而来，各子项目提交历史可在 `git log` 追溯，原仓库已归档只读。

## 快速开始

```bash
# 后端（:8081）
cd asternova/backend && docker compose up -d && go run main.go

# 前端外壳
cd asternova/web-client && npm install && cp .env.development .env.local && npm run dev
```

客户端独立运行无法移动——服务端权威设计，必须先起后端。

---

<div align="center">
<sub>AsterForge · <a href="https://asterforge.top">asterforge.top</a></sub>
</div>
