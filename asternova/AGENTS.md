# AGENTS.md

本文件为所有进入 `asternova/` 目录的 AI 编码助手（Antigravity, Claude Code, Cursor 等）提供工作准则、本地环境与决策约束。后续所有会话的 Agent 进入本仓库必须优先遵守以下规范。

---

## 0. 本地环境与工具路径（已配置就绪，直接调用）

| 工具 | 本地绝对路径 | 版本与状态 | 快捷命令 / 说明 |
| :--- | :--- | :--- | :--- |
| **Godot Engine** | `C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64.exe` | **v4.7.2-stable.official**（最新正式稳定版） | 命令行全局可用 `godot`（通过 `godot.cmd` 桥接）；桌面有快捷方式 `Godot 4.7.lnk` |
| **Blender** | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` | **Blender 5.2.1 LTS**（官方长期支持稳定版） | 内置 Python 3.11，已启用 `mmd_tools v4.5.14` 插件；桌面有 `Blender 5.2.lnk` |

---

## 1. 核心工作区拓扑（严禁走错目录）

- **`asternova/render-lab/`（当前阶段核心工作区）**：
  - **定位**：M1 渲染垂直切片与 3D 建模的**独立沙盒试验场（Sandbox）**。
  - **分工**：
    - `models/`：Blender 5 建模源工程（Aster 当前最新基模 `aster_head_base_v2.blend`）及参考模型；
    - `shaders/`：自研二次元 Toon Shader（面部、发型、描边等）；
    - `scenes/`：Godot 渲染与三视图比对舞台（`turnaround_stage.tscn`、黄昏樱花场景）；
    - `scripts/`：Blender (bpy) 自动化处理脚本与 Godot 自动化测试截图脚本。
  - **原则**：纯粹的美术与渲染环境，**隔离主工程网络/协议/UI 逻辑**。在此调优成熟后，资产直接搬迁至正式客户端。
- **`asternova/art/`（美术资产与定稿库）**：
  - 存放官方 2D 原画、三视图基准稿、同框对比验收件及三档真机渲染截图。
- **`asternova/client-godot/`（正式游戏客户端）**：
  - 承载 M2/M3 正式玩法逻辑、网络传输、React Meta UI 嵌入与战斗状态机。

---

## 2. 核心工作与决策原则

1. **最高决策优先级**：用户指令 > `docs/BLUEPRINT.md`（愿景与里程碑）> `docs/STYLE.md`（美术风格圣经）> `docs/architecture.md`（技术架构）> 本规范。
2. **技术卡点与方案校准（死磕红线）**：
   - 当发现一个技术方案或修复手段尝试很久都达不到预期效果时（如模型反复打磨依然失真、渲染风格廉价、局部修补导致代码/拓扑混乱），**严禁在错误基底/劣质路径上死磕打补丁**。
   - **必须果断停下，跳出局部死循环，深度调研工业界成熟标杆（如《鸣潮》、《原神》、《星穹铁道》等商业大厂工业级管线）的最佳实践与底层原理**。
   - 梳理出标准化、工业级的新方案并与用户商讨对齐后，再行切换与落地，并及时回填设计与技术文档。
3. **轻量高性能意识**：
   - 3D 动作游戏（绝区零/鸣潮式高速战斗）以 60~120 FPS 流畅运行为核心生命线。
   - 严禁为了追求所谓"细碎细节"而堆叠海量细面片或毛发粒子（会导致可怕的 Overdraw 与显存带宽枯竭）。
   - 恪守工业界"大形归纳（Stylized Clumps）+ 贴图分绺暗线（Crease Grooves）+ 法线球面化（Sphere Normal Transfer）"的低几何开销、高视觉还原管线。
4. **资产管理纪律（防乱放红线）**：
   - 严禁在 `art/` 或项目根目录随意堆放 `debug_*`、`crop_*`、`test_*`、`extract_*` 等临时脚本调试图片。所有中间调试产物必须在内存或临时目录（如 OS temp）处理完毕即刻销毁。
   - 角色 3D 验收以 `art/characters/aster/turnaround-final.png` 为绝对视觉基准，关键配饰齐全后同框对比，综合相似度 ≥ 90% 方可验收。
5. **验证闭环与提交规范**：
   - 独立可验证单元完成后立即提交：Conventional Commits + 中英对照（如 `feat(art): ... / ...`）。
   - 渲染与美术改动必须先出可验证件（截图对比、真机跑分、弹出窗口供用户检阅），严禁凭模型自我声称通过。

