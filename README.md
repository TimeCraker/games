# games

游戏项目 monorepo —— 把 AsterNova 矩阵整合到一处，各子目录保留原仓库完整 git 历史；桓睿消消乐已作为休闲小游戏集成进 web-client 大厅。

## 结构

```
games/
└── asternova/              # AsterNova 多客户端矩阵游戏
    ├── web-client/         # Next.js 前端 (React UI + WASM 战斗引擎, JSBridge; 含消消乐 /lobby 小游戏)
    ├── backend/            # Go 后端 (服务端权威, 60Hz 帧同步, Gin+WS+MySQL+Redis)
    ├── client-godot/       # Godot 4 (WASM) 客户端
    ├── client-unity/       # Unity (WebGL) 客户端
    └── assets/             # 共享静态资源 (logo/icon/宣传图)
```

## 子项目说明

| 子目录 | 技术栈 | 来源仓库 |
|---|---|---|
| `asternova/web-client` | Next.js 15 + React + WASM | asternova-web-client |
| `asternova/backend` | Go + Gin + WebSocket + MySQL + Redis | game-backend-demo |
| `asternova/client-godot` | Godot 4 (WASM) | go-dot-game |
| `asternova/client-unity` | Unity (WebGL) | MyGameDemo_Client-unity- |
| `asternova/assets` | 静态资源 | asternova-assets |

## 架构

AsterNova 是服务端权威的实时多人动作游戏：Go 后端跑 60Hz 帧同步与对战逻辑，三个客户端（Web/Unity/Godot）只负责输入捕获与快照插值渲染，通过 JSBridge 与 React 宿主通信。三个客户端共享同一后端协议。

桓睿消消乐（立体三消闯关，纯前端零依赖）已作为休闲小游戏集成进 web-client 大厅 `/lobby`，原独立仓库（huanrui-xiaoxiaole）历史见 git log。

## 历史

本 monorepo 由 6 个独立仓库通过 `git subtree add`（不 squash）合并而成，各子项目的提交历史可在 `git log` 中追溯。原仓库已归档为只读。消消乐子目录后已并入 web-client，其源仓库历史仍可追溯。
