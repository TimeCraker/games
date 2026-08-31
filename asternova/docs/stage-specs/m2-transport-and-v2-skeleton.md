# Stage Spec：M2 Transport 抽象 + client-godot-v2 骨架

> 状态：**⚠️ 已过时（2026-08-31）**——本文系「中心服务器」旧方向所写；当天项目翻转为**单机优先 + 房主联机**（见 BLUEPRINT「产品形态」），M2 重定义为「战斗骨架 + Transport 抽象」。本文留作参考，随 M2 开工按新方向重写。Transport 抽象 + fake 回环测试的验收思想在新版沿用。
>
> 原状态：待用户放行（2026-08-30 起草）。上游锚点：[BLUEPRINT.md M2](../BLUEPRINT.md) · [architecture.md §2/§4](../architecture.md)。

## 目标（一句话）

把传输层从 gorilla/websocket 直连解耦为**可插拔 Transport 抽象**，并以它为地基搭起 `client-godot-v2` 骨架，在 Godot 4.5 原生调试运行下跑通「登录 → 匹配 → 战斗 → 快照渲染」闭环。

## 范围内

### A. backend：传输抽象（不改变线上行为）

1. `gateway` 侧定义 `Transport`/`Connection` 接口：`Send`（可靠/高频两种语义标注）/ `OnMessage` / `Close`；现有 gorilla/websocket 代码整体移到 `WSTransport` 实现下，**hub/battle/match 逻辑不动**。
2. `FakeTransport` 回环实现 + 单测：同输入序列驱动 fake 与 WS 两条路径 → **快照输出逐字节一致**（接口一致性的验收硬标准，也是未来 ENet 实现的回归护栏）。
3. 协议升级预留：`game.proto` 不改 message 结构，仅评估双通道分包头方案（可靠/高频标志位），改动需在本文追加记录后再动。

### B. client-godot-v2（新建 `asternova/client-godot-v2/`）

1. Godot **4.5.x stable** 项目骨架：目录规范（`scripts/` `scenes/` `proto/`）、`.gitignore`（`.godot/`）、README。
2. `Transport.gd` 抽象接口 + `WsTransport.gd` 实现（对接 A 的接口语义；参考一代 `BattleWsClient.gd` 的粘包/重连处理，**拷贝迁移并适配**，不重写）。
3. `ProtoParser.gd` 从一代**拷贝迁移**（零依赖自研编解码，保持体积优势）+ GdUnit4 编解码单测迁移。
4. 战斗循环最小版：连接 → JWT 鉴权 → `match_req` → 进房 → 收 60Hz 快照 → Lerp 插值渲染测试方块（两 Godot 实例同房互相可见移动）。
5. UI 最简：dev 直连模式（env 配 token/地址），不做大厅，不做 HUD。

### C. M0 移交项

1. **guest-login IP 限流**：Redis 固定窗口计数（如同 IP 每分钟 ≤5 次创建），超限返回 429；单测覆盖。
2. **RTT P95 公网复测**：复用 `test/test_client.go` 打真实流量（本地起服务 + 公网走服务器实例的时间点由部署节奏定，先出本地基线图），与旧基线（<80ms）对比，图表入 `asternova/assets/`。

## 范围外（防扩散清单）

- ENet UDP、Android、Web WASM 导出（M4）
- WebView 嵌入、React 大厅（M3）
- 二次元渲染、正式角色资产（M1 线）
- 打击感/HIT-Stop、特效、音频迁移（M3+）
- web-client 任何改动（现役不动，M3 才演化）

## 验收标准（全部以真实运行取证）

| # | 验收点 | 证据形式 |
|---|---|---|
| 1 | `go build/vet/test ./...` 全绿，含 fake↔WS 一致性测试 | 命令输出 |
| 2 | 两个 Godot 4.5 实例进同房，双方 60Hz 快照驱动互相可见移动 | 录屏/截图 + 日志帧计数 |
| 3 | ProtoParser GdUnit4 单测通过（headless：`godot --headless` 跑 GdUnit4 CLI） | 测试报告输出 |
| 4 | guest-login 脚本打 >5 次/分钟 → 429 | curl 序列输出 |
| 5 | RTT 复测基线图（本地） | 图表文件 |

## 风险与预案

- **proto 双端同步**：分包头方案若动 proto，必须 backend pb.go 与 v2 ProtoParser 同批改（铁律见 CLAUDE.md）。
- 一代 `ProtoParser.gd` 写于 Godot 4.3 时代，迁移到 4.5 的 API 兼容风险小但存在——迁移后先跑单测再接战斗循环。
- FakeTransport 的一致性测试要求 battle tick 确定性（浮点/map 遍历顺序）——若发现非确定性来源，单独记录并修复，不绕过。

## 交付物

- backend：Transport 接口 + WS/Fake 实现 + 单测
- `client-godot-v2/`：骨架 + 战斗循环最小版 + GdUnit4 测试
- 限流 + RTT 基线图
- 更新 BLUEPRINT M2 checkbox + CLAUDE.md 命令节（v2 跑法）
