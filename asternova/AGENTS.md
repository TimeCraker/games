# AGENTS.md

本文件为所有进入 `asternova/` 目录的 AI 编码助手（Antigravity, Claude Code, Cursor 等）提供工作准则、本地环境与决策约束。后续所有会话的 Agent 进入本仓库必须优先遵守以下规范。

> **先读 [docs/README.md](docs/README.md) 第 1 节「当前真实状态」**。2026-10-23 起：玩家角色是 CC0 人偶占位，正式角色地基待用户决定，之前的角色返工产物已全部删除；光照走 `LightingRig` + 预设。

---

## 0. 本地基础设施与工具调用规范（CLI 与 MCP 按会话验证 · 必读基础）

工具以当前会话实测为准。CLI、MCP 与可用的界面控制互相补充；插件文件存在不代表客户端已接通：

| 模式 | 工具 / 服务 | 本地绝对路径 / 配置源 | 状态与版本 | 核心使用场景与规范 |
| :--- | :--- | :--- | :--- | :--- |
| **CLI 模式**<br>(底层无头批处理) | **Godot 4.7** | `C:\Users\TimeCraker\tools\godot\Godot_v4.7.2-stable_win64_console.exe`；交互窗口用同目录的非 console 版本 | **v4.7.2 stable** | 本次未解析到全局 `godot` 命令，按安装目录或显式参数调用；Windows PowerShell 调用图形版本须等待实际进程退出，再检查退出码。用于无头检查、实际场景运行与截屏。 |
| **CLI 模式**<br>(本地自动化) | **Blender** | 使用 `Get-Command blender` 解析；本次为 `C:\Users\TimeCraker\tools\blender\blender-5.2.1-windows-x64\blender.exe` | 运行 `blender --version` 核实 | 导入、装配、蒙皮、烘焙、导出与渲染均可自动化；变形与视觉效果须看图验证。插件和 Python 版本需实际查询。 |
| **MCP 模式**<br>(前台可视化交互) | **Blender MCP**（`blender-mcp`，视口插件已装入 5.2） | 各客户端分别核验可调用能力（配置随客户端各自维护：Claude Code 在 `~/.claude.json` / 项目 `.mcp.json`；Gemini CLI 在 `~/.gemini/`） | 安装文件存在；当前客户端须实际连接测试 | **活动场景检查与编辑的优先通道；不保证自动得到合格造型**：视口截图、代码执行、Hunyuan3D / Hyper3D Rodin 图生 3D 直连导入、PolyHaven / PolyPizza 素材库检索。 |
| **MCP 模式**<br>(前台可视化交互) | **Godot MCP**（`@coding-solo/godot-mcp`） | 同上（按客户端配置） | ⬜ **尚未接入 Claude Code**（此前仅 Gemini 侧配置） | 前台唤起 Godot 编辑器、运行调试、动态增删节点与实时抓取控制台报错；接入前 Godot 侧自动化一律走 CLI。 |

> **调用准则（2026-09-10 修订：视觉闭环铁律，所有建模 Agent 强制遵守）**：
> 1. **审美类操作优先使用已验证的活动 Blender 连接；不可用时采用可用界面或 Python，并逐次看图**；
> 2. **自动化必须可检查**：脚本用于非审美批处理（导入导出、贴图处理、烘焙、截图）；角色绑定与权重不用脚本做（见 §2.8）。关键变更后出图检查，不得因脚本无异常而宣称视觉合格。
> 3. **视觉闭环铁律**：任何几何 / 材质 / 光照修改之后，必须**立即截图**（MCP 视口截图或无头渲染均可），由 Agent 多模态能力**亲自看图**并与参考图比对，确认无误才准执行下一步；**严禁连续多步盲改后才看结果，严禁未看图就声称通过**；
> 4. **参考图同框验收**：按参考图生产的资产必须交付「参考图 vs 成品」同框对比看板（成品前后同相机、同光照；二维原画无法严格复现时标注差异），由制作人拍板；**严禁自报数值化相似度**（详细流程见 modular SOP §2.6）；
> 5. **并行纪律**：**一个资产一个 Agent**；`.blend` 无法合并编辑，严禁多 Agent 同改一个文件 / 一个资产目录；需要并行时按资产拆分任务；
> 6. **面数策略**：保留高精源；实际工作网格按轮廓、变形与设备帧时选择，LOD 经测试确认（详见 modular SOP §1.3）。


---

## 1. 核心工作区拓扑（严禁走错目录）

- **`asternova/client-godot-v2/`（唯一的 Godot 工程）**：玩法、战斗、场景、光照、着色器都在这里。
  - `scenes/levels/`：`combat_playground.tscn`（主场景，战斗沙盒）、`m1_street.tscn`（街区 + 光照预设参考场景）；
  - `lighting/`：`LightingRig` 与光照预设（用法见 `docs/pipeline/lighting-guide.md`）；
  - `scripts/entities/player/`：`CharacterRig`（角色视觉、插槽、动画）、`PlayerAnimDriver`、`PlayerController`；
  - `models/mannequin/`：当前玩家占位人偶与标准动作库；
  - `tests/`：`test_combat_runner.gd`（战斗门禁）、`lighting_preview.tscn`（光照对比截图）。
- **`asternova/art/`**：原画、源模型、参考图与渲染预览（见其 README）。
- **`asternova/scripts/pipeline/`**：贴图与资产批处理脚本（环境、武器）。
- 原 `render-lab/`（渲染沙盒）与 `client-godot/`（一代客户端）已于 2026-10-23 删除，git 历史可恢复，不要重建。

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
4. **资产管理纪律（防乱放红线）**：
   - 严禁在 `art/` 或项目根目录随意堆放 `debug_*`、`crop_*`、`test_*`、`extract_*` 等临时脚本调试图片。所有中间调试产物必须在内存或临时目录（如 OS temp）处理完毕即刻销毁。
   - 角色按各自原画验收（白/橙/紫看 `art/characters/source/<角色>/poster/`，Aster 看 `art/characters/aster/turnaround-final.png`）。同框对比并记录具体差异，最终美术验收由用户判断，不自报相似度。
5. **验证闭环与提交规范**：
   - 独立可验证单元完成后立即提交：Conventional Commits + 中英对照（如 `feat(art): ... / ...`）。
   - 渲染与美术改动必须先出可验证件（截图对比、真机跑分、弹出窗口供用户检阅），严禁凭模型自我声称通过。
6. **武器与道具建模管线（SOP 必读）**：
   - 所有武器与穿戴道具制作必须严格遵循 [`docs/pipeline/weapon-modeling-pipeline.md`](docs/pipeline/weapon-modeling-pipeline.md)；
   - 核心铁律：① 严控 800~1,500 三角面（120 FPS 性能红线）；② 双分件原点必须绝对锁定在刀鞘口/锁扣 `(0, 0, 0)` 实现拔刀零偏置；③ 单张 2K Atlas 贴图；④ 提供 360° 交互检视件（自包含 Web 检视器 + Godot 视口）。
7. **渲染与光照**：
   - 渲染器 **Forward+ (Vulkan Clustered)**，色调映射 **AgX**；不退回 `gl_compatibility`。
   - 每个 3D 场景放一个 `LightingRig`，选一个 `lighting/presets/` 预设；场景里不另放 WorldEnvironment / DirectionalLight3D。
   - 场景材质（地面、建筑、道具）用普通 PBR：着色器不写 `light()`，不用 `ambient_light_disabled`，不做亮度补偿系数。角色可用 `toon_character.gdshader` 的色阶，但暗部跟随光源，不写固定底色。
   - 调光照前读 [`docs/pipeline/lighting-guide.md`](docs/pipeline/lighting-guide.md)；改完用 `tests/lighting_preview.tscn` 出四套预设对比图给用户看。
8. **角色、骨骼与动画**：
   - 按 [`docs/pipeline/character-pipeline.md`](docs/pipeline/character-pipeline.md)：角色要建在有正确拓扑、五官和骨骼的身体上；AI 分件生成后硬拼的路线已废弃。
   - 绑定用地基自带骨骼（VRM）或 AccuRIG / Mixamo；动画重定向用 Godot `BoneMap` + `SkeletonProfileHumanoid`，播放用 `AnimationTree`。
   - 禁止脚本按坐标/高度分配权重、手算四元数重定向；禁止代码 Tween 摆骨做假动画。
   - 换角色只换模型：新角色场景挂 `CharacterRig`，按新骨骼改插槽骨名与 `CLIP_ALIASES`。
