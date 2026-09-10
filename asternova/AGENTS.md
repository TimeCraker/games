# AGENTS.md

本文件为所有进入 `asternova/` 目录的 AI 编码助手（Antigravity, Claude Code, Cursor 等）提供工作准则、本地环境与决策约束。后续所有会话的 Agent 进入本仓库必须优先遵守以下规范。

---

## 0. 本地基础设施与工具调用规范（CLI 与 MCP 双模就绪 · 必读基础）

开发工具链已建立**「底层无头 CLI 脚本 + 前台交互 MCP 协议」双模体系**，两者皆为工程基础知识，Agent 应根据任务类型自由选用、互为补充：

| 模式 | 工具 / 服务 | 本地绝对路径 / 配置源 | 状态与版本 | 核心使用场景与规范 |
| :--- | :--- | :--- | :--- | :--- |
| **CLI 模式**<br>(底层无头批处理) | **Godot 4.7** | `C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64.exe` | **v4.7.2 stable** | 全局 `godot` 命令行可用；用于无头执行测试脚本、三视图截屏与场景跑分。 |
| **CLI 模式**<br>(底层无头批处理) | **Blender 5.2** | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` | **5.2.1 LTS** | 内置 Python 3.11 + `mmd_tools v4.5.14`；仅限非审美批处理（导出 / LOD / 贴图通道搬运 / 自动化出图），见下方调用准则。 |
| **MCP 模式**<br>(前台可视化交互) | **Blender MCP**（`blender-mcp`，视口插件已装入 5.2） | Claude Code 会话可直接调用（配置随客户端各自维护：Claude Code 在 `~/.claude.json` / 项目 `.mcp.json`；Gemini CLI 在 `~/.gemini/`） | ✅ 2026-09-10 验证可用 | **一切审美相关建模操作的首选通道**：视口截图、代码执行、Hunyuan3D / Hyper3D Rodin 图生 3D 直连导入、PolyHaven / PolyPizza 素材库检索。 |
| **MCP 模式**<br>(前台可视化交互) | **Godot MCP**（`@coding-solo/godot-mcp`） | 同上（按客户端配置） | ⬜ **尚未接入 Claude Code**（此前仅 Gemini 侧配置） | 前台唤起 Godot 编辑器、运行调试、动态增删节点与实时抓取控制台报错；接入前 Godot 侧自动化一律走 CLI。 |

> **调用准则（2026-09-10 修订：视觉闭环铁律，所有建模 Agent 强制遵守）**：
> 1. **审美类操作（造型 / 比例 / 材质 / 光照 / 几何手术）一律优先在 MCP 会话内完成**；
> 2. **CLI + Python 无头脚本仅限非审美的确定性批处理**：格式导出、LOD 减面、贴图通道搬运、自动化出图与 CI 跑分——**严禁用无头脚本做「不看效果就无法确认好坏」的修改**（有机角色绑定与重定向的禁令见 character-modeling-pipeline §1.1 红线 5）；
> 3. **视觉闭环铁律**：任何几何 / 材质 / 光照修改之后，必须**立即截图**（MCP 视口截图或无头渲染均可），由 Agent 多模态能力**亲自看图**并与参考图比对，确认无误才准执行下一步；**严禁连续多步盲改后才看结果，严禁未看图就声称通过**；
> 4. **参考图同框验收**：按参考图生产的资产必须交付「参考图 vs 成品」同框对比看板（同透视、同光照），由制作人拍板；**严禁自报数值化相似度**（详细流程见 modular SOP §2.6）；
> 5. **并行纪律**：**一个资产一个 Agent**；`.blend` 无法合并编辑，严禁多 Agent 同改一个文件 / 一个资产目录；需要并行时按资产拆分任务；
> 6. **面数策略**：AI 生成资产（角色 / 建筑 / 道具）一律取 Tripo 最高面数档，**生成阶段不设上限**，LOD 后置兜底（详见 modular SOP §1.3）。


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
- **`asternova/client-godot-v2/`（正式游戏客户端）**：
  - 承载 M2/M3 正式玩法逻辑、网络传输、React Meta UI 嵌入与战斗状态机。
- **`asternova/client-godot/`（旧工程，已冻结）**：
  - 见 `FROZEN.md`，仅供历史参考，严禁在其上开发新功能。

---

## 2. 核心工作与决策原则

1. **最高决策优先级**：用户指令 > `docs/BLUEPRINT.md`（愿景与里程碑）> `docs/STYLE.md`（美术风格圣经）> `docs/architecture.md`（技术架构）> 本规范。
2. **技术卡点与方案校准（死磕红线）**：
   - 当发现一个技术方案或修复手段尝试很久都达不到预期效果时（如模型反复打磨依然失真、渲染风格廉价、局部修补导致代码/拓扑混乱），**严禁在错误基底/劣质路径上死磕打补丁**。
   - **必须果断停下，跳出局部死循环，深度调研工业界成熟标杆（以《明日方舟：终末地》为首选标杆，辅以《鸣潮》《星穹铁道》商业大厂工业级管线）的最佳实践与底层原理**。
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
6. **武器与道具建模管线（SOP 必读）**：
   - 所有武器与穿戴道具制作必须严格遵循 [`docs/pipeline/weapon-modeling-pipeline.md`](docs/pipeline/weapon-modeling-pipeline.md)；
   - 核心铁律：① 严控 800~1,500 三角面（120 FPS 性能红线）；② 双分件原点必须绝对锁定在刀鞘口/锁扣 `(0, 0, 0)` 实现拔刀零偏置；③ 单张 2K Atlas 贴图；④ 提供 360° 交互检视件（自包含 Web 检视器 + Godot 视口）。
7. **渲染底座与色彩科学标准（Forward+ 与 AgX，2026-09-06 统一定案）**：
   - 全工程（`render-lab` 与 `client-godot-v2`）统一运行在 **Forward+ (Vulkan Clustered)** 渲染器与 **AgX 色调映射（模式 4）**；
   - 严禁倒退回 `gl_compatibility`，严禁在着色器中硬写 2.88x 光照补偿 hack（如 `diffuse_scale = 0.20`）；
   - 标准环境预设使用 `environments/endfield_studio_environment.tres`，标准布光使用 `scenes/lighting/endfield_lighting_studio.tscn`（45° 侧逆主光 + 盒投影反射探针 + 全分辨率 SSAO + SSR）；
   - 场景遵循「场景硬表面真实 PBR + 角色二次元赛璐璐 NPR」双管线架构。
8. **人形骨骼与动画驱动规范（2026-09-06 定案）**：
   - Aster 原模具备标准 43 骨 Humanoid 工业骨架与四重蒙皮权重，动作驱动必须通过 Godot 4.7 原生 `BoneMap` + `SkeletonProfileHumanoid` + `AnimationTree`；
   - 严禁继续使用代码 Tween 强转单根骨骼实现伪动画（导致手肘不弯、双腿滑步等假动作）。
9. **资产工业化流水线（AI 底模 + 自动化手术修补，2026-09-06 定案）**：
   - 严禁从零手动拉白模，严禁裸用未经治理的 AI 糙模；
   - 必须严格遵循 `docs/pipeline/modular_art_and_asset_production_sop.md`，采用「Tripo3D 2.0 负责 85% 宏观资产 + Blender 自动化脚本手术（`surgery_<asset>.py`）切除撕裂假玻璃与扁平贴纸、清理飞刃、嵌装铝合金窗框与真实 3D 室内货架」模式。


