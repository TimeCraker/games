# ⚠️ 此目录已冻结（2026-08-30）

本目录是 AsterNova 第一代 Godot 客户端（WASM 形态，宿主为 web-client），**冻结为参考实现，不再开发**。

- 新客户端开发在 `asternova/client-godot-v2/`（M2 启动，见 [docs/BLUEPRINT.md](../docs/BLUEPRINT.md)）。
- 仍然有参考价值的部分：
  - `scripts/ProtoParser.gd` — 自研零依赖 Protobuf 3 编解码（几百行纯 GDScript，压榨 WASM 体积），v2 协议升级时评估复用或重写；
  - `scripts/BattleWsClient.gd` — 60Hz WS 收发 + 粘包/重连处理；
  - `scripts/GameManager.gd` — WASM↔React JSBridge 总线（双通道协议思想已定案沿用到新架构，见 [docs/architecture.md](../docs/architecture.md) §3）。
- `proto/game.proto` 与 backend 的同步校验结论仍有效；v2 起协议演进以 backend 侧为源。
