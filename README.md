<div align="center">

<img src="assets/banner.svg" alt="AsterNova" width="880"/>

# AsterNova

**服务端权威的实时联机动作游戏 · 一套后端，三端客户端**

*"Feel the impact, not the latency."*

[在线试玩](https://asterforge.top/game) · [AsterForge](https://asterforge.top)

</div>

---

## 战场

<div align="center">
<img src="asternova/assets/hero-arena.png" alt="AsterNova 竞技场" width="720"/>
</div>

**赛博珍珠白竞技场**：Go 后端以 60Hz 裁决全部物理，客户端只做输入采集与快照插值——本地零预测、零作弊面。普攻命中 0.08s、拼刀 0.15s 的 **Hit-Stop 卡肉**，配合衰减式屏幕震动，把打击感做进引擎时间膨胀里。

## 架构

<div align="center">
<img src="assets/architecture.svg" alt="AsterNova 架构" width="880"/>
</div>

三条铁律撑起整个系统：

1. **后端独占裁决权** — `battle` 服务跑 60Hz Tick 纯数学物理（矢量 / 碰撞盒 / 状态机），客户端上报输入、接收 `State Snapshot`（Protobuf 编码）、Lerp 插值渲染。
2. **Web 是外壳不是通道** — Next.js 只管登录 / 大厅 / HUD / WASM 容器；战斗由 WASM 引擎**直连**后端 WebSocket，绕过 Web 层的 HTTP 限制。JSBridge 双通道：Command 下行注入 JWT，Event 上行回抛 HP / 能量。
3. **一套协议三端共享** — Web / Godot / Unity 共用一份 `game.proto`，改协议三端同步。

## 三端实现

| | Web Shell | Godot 4 → WASM | Unity → WebGL |
|---|---|---|---|
| 定位 | 游戏运行时容器 | 主战斗客户端 | 备选战斗客户端 |
| 技术栈 | Next.js 16 · React 19 · Zustand | GDScript · 零第三方插件 | C# · react-unity-webgl |
| 工程亮点 | Scale-to-Fit 视口矩阵（移动端物理级自适应）；`.wasm/.pck` Brotli 压缩减体积 30-50%；唯一状态源杜绝 DOM/Canvas 脱节 | **自研零依赖 Protobuf**（几百行纯 GDScript 编解码，压榨 WASM 体积）；0.35s 预测锁防表现回扯；动态虚拟摇杆 | 高频输入捕获 · 快照插值 · WebGL JSBridge |
| 目录 | [`asternova/web-client`](asternova/web-client) | [`asternova/client-godot`](asternova/client-godot) | [`asternova/client-unity`](asternova/client-unity) |

## 压测

单机腾讯云实测（完整图表见 [`asternova/assets/`](asternova/assets/)）：

<div align="center">
<img src="asternova/assets/stress-tick.png" alt="帧同步压测" width="560"/>
</div>

| 指标 | 结果 |
|---|---|
| 60Hz Tick 稳定性 | 长尾稳定，无积压 |
| RTT | 局域网 <10ms · 公网 P95 <80ms |
| 满房间并发 CPU | 单核占用可控 |

## Arcade · 休闲矩阵

大厅 `/lobby` 内置纯前端小游戏，零后端依赖：

<table>
<tr>
<td width="50%" align="center">
<a href="https://game.asterforge.top/xiaoxiaole/">
<img src="asternova/assets/xiaoxiaole-screenshot-game.jpg" alt="三消游戏" width="360"/>
</a>
<p><b>立体三消</b> — 12 关闯关</p>
<p><sub>4 连炸弹 · 5 连彩虹 · 连击 · 成就 · 双主题 · PWA 可安装</sub></p>
</td>
<td width="50%" align="center">
<img src="asternova/assets/stress-rtt.png" alt="RTT 压测" width="360"/>
<p><b>shoot-them-all</b> — matter-js 物理弹幕</p>
<p><sub>另有 lets-running · merge · nebula-survivor</sub></p>
</td>
</tr>
</table>

## 快速开始

```bash
# 后端（:8081，需 Docker 起 MySQL + Redis）
cd asternova/backend && docker compose up -d && go run main.go

# Web 外壳
cd asternova/web-client && npm install && cp .env.development .env.local && npm run dev
```

> 服务端权威设计：客户端独立运行无法移动，必须先起后端；Godot 端需在 `GameManager.gd` 配 Mock Token。

## Monorepo

```
games/asternova/
├── web-client/     # Next.js 16 Game Shell + Arcade（原 asternova-web-client）
├── backend/        # Go · Gin · WS · MySQL · Redis（原 game-backend-demo）
├── client-godot/   # Godot 4 → WASM（原 go-dot-game）
├── client-unity/   # Unity → WebGL（原 MyGameDemo_Client-unity-）
└── assets/         # 共享静态资源（原 asternova-assets）
```

六仓经 `git subtree add`（保留完整历史）合并，原仓库归档只读，历史可在 `git log` 追溯。

---

<div align="center">
<sub>AsterForge · <a href="https://asterforge.top">asterforge.top</a> · 鄂ICP备2026015662号-1</sub>
</div>
