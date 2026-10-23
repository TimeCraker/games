# AsterNova 文档索引

> **决策优先级**：用户当前指令 > [BLUEPRINT.md](BLUEPRINT.md)（愿景与里程碑）> [architecture.md](architecture.md)（技术定案与红线）> [STYLE.md](STYLE.md)（美术风格）> 阶段施工单 / 管线文档 > 仓库根 `CLAUDE.md`。

---

## 1. 当前真实状态（2026-10-23）

这一节只写已经做到、能在工程里打开验证的事。愿景和目标见 BLUEPRINT。

**工程结构**

- 唯一的 Godot 工程是 `client-godot-v2/`（Godot 4.7.2，Forward+）。原 `render-lab/` 渲染沙盒已并入它后删除；一代客户端 `client-godot/` 已删除。两者都可从 git 历史恢复。
- `backend/` 一期封存，`web-client/` 是官网与 Web 壳，二者不受本轮影响。

**战斗（M2）**

- 战斗沙盒 `scenes/levels/combat_playground.tscn` 可玩：移动、疾跑、滑铲、二段跳、蹬墙跳、四段连招、居合、弹刀、单体卡肉、星闪。
- 自动化门禁 `tests/test_combat_runner.gd` 共 109 项检查，全部通过。
- Transport 抽象与联机未开始。

**角色**

- 玩家角色是 **CC0 中性人偶占位**（Quaternius），挂 `CharacterRig`，佩刀可拔可收。四段连招暂时都用同一个 `Sword_Attack` 动作。
- **没有正式角色**。白/橙/紫三角色只有原画和 AI 分件模型（`art/characters/source/`），Aster 只有设定图和原始雕刻。之前的装配、绑定、返工产物已全部删除，原因见 [character-pipeline.md](pipeline/character-pipeline.md) 第 2 节。
- 正式角色的制作地基（VRoid / 商用素体 / AI 一体生成）**待用户决定**。

**场景与光照（M1）**

- 街区场景 `scenes/levels/m1_street.tscn`：便利店、自动售货机、街道道具、樱花，从 render-lab 迁入。
- 光照系统 `LightingRig` + 四套预设（晴天、黄昏、阴天、夜晚），实拍见 `art/render_previews/lighting/`。**待用户看图确认作为标准**。
- 场景材质已去掉自定义 `light()` 光照补偿，统一让引擎算光照。
- 场景整体美术（信息密度、贴图、招牌）尚未通过用户终审。

---

## 2. 文档列表

| 文档 | 内容 | 状态 |
| :--- | :--- | :--- |
| [BLUEPRINT.md](BLUEPRINT.md) | 愿景、商业节奏、核心玩法、M0～M4 里程碑 | 定案 |
| [architecture.md](architecture.md) | 技术选型、房主权威、UI 分界、网络、性能与安全红线 | 定案 |
| [STYLE.md](STYLE.md) | 美术风格：配色、角色造型方向、渲染与光照基线 | 定案 |
| [CONTENT_BACKLOG.md](CONTENT_BACKLOG.md) | 创意内容池（彩蛋、后续角色、流派构想） | 持续更新 |
| [pipeline/lighting-guide.md](pipeline/lighting-guide.md) | 光照方案：怎么换预设、调参数、加灯、出对比图 | 现行 |
| [pipeline/character-pipeline.md](pipeline/character-pipeline.md) | 角色制作：旧路线为何失败、可选地基、流程与规则 | 现行（地基待定） |
| [pipeline/weapon-modeling-pipeline.md](pipeline/weapon-modeling-pipeline.md) | 武器与道具：双分件、鞘口原点、拔刀插槽 | 现行 |
| [pipeline/modular_art_and_asset_production_sop.md](pipeline/modular_art_and_asset_production_sop.md) | 场景与道具资产制作 | 现行 |
| [pipeline/trim_sheet_and_modular_spec.md](pipeline/trim_sheet_and_modular_spec.md) | 地面 PBR Trim Sheet 规范 | 收缩维护 |
| [stage-specs/m1-render-vertical-slice.md](stage-specs/m1-render-vertical-slice.md) | M1 渲染垂直切片施工单 | 推进中 |
| [stage-specs/m2-transport-and-v2-skeleton.md](stage-specs/m2-transport-and-v2-skeleton.md) | M2 战斗骨架与 Transport 施工单 | 推进中 |
| [stage-specs/web-client-perf2-content.md](stage-specs/web-client-perf2-content.md) | web-client 性能二期与官网内容化 | 草案 |
| [shoot-them-all-whitepaper.md](shoot-them-all-whitepaper.md) · [shoot-them-all-art-bible.md](shoot-them-all-art-bible.md) | 《弹珠风暴》玩法与美术 | 定稿 |
| [nebula-survivor-whitepaper.md](nebula-survivor-whitepaper.md) · [nebula-survivor-ui-spec.md](nebula-survivor-ui-spec.md) | 《星域突围》玩法与 UI | 定稿 |
| [ui-polish/rules.md](ui-polish/rules.md) · [ui-polish/AUDIT.md](ui-polish/AUDIT.md) | web-client UI 打磨规则与审计台账 | 现行 |
| [archive/initial_prompt.md](archive/initial_prompt.md) | 早期角色建模 Prompt | 归档，内容已过时 |

---

## 3. 红线速查

1. **渲染**：Forward+ + AgX。模拟 60Hz 固定步长，渲染帧率与之解耦。
2. **场景材质不接管光照**：场景着色器不写 `light()`、不用 `ambient_light_disabled`，详见 [lighting-guide.md](pipeline/lighting-guide.md) 第 4 节。
3. **角色绑定**：用地基自带骨骼或 AccuRIG / Mixamo，重定向用 Godot BoneMap。禁止脚本按坐标分配权重、手算四元数重定向。
4. **看图验收**：每步修改后截图检查；用户看实机画面后的判断是唯一验收，不自报分数或相似度。
5. **文档只写现状**：没做到的写进 BLUEPRINT 的目标，不写成已具备。
6. **单体卡肉**：联机战斗中禁止全局时间缩放（`Engine.time_scale`），卡肉只冻结攻守双方。
