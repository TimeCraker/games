# Stage Spec：白、橙、紫三角色装配与动作验证

> **2026-10-01 状态校正**：三角色动作工程原型可运行，但静态装配和艺术品质未通过。原“6/6”是历史工程交付记录，不能作为美术完成结论。当前先返工白色静态样板并等待用户确认；执行 `docs/stage-specs/character-art-rework.md`（相对 asternova 根目录）。

开始：2026-09-30；交付检查：2026-10-01。用户已授权直接修正流程并完成三位角色的拼装、绑定和游戏动作验证。

## 目标与边界

保留 STYLE.md 中精致二次元角色、终末地式清冷通透场景和高质量动作目标。本阶段使用用户已有的九个 GLB，不重新生成角色，不改动冻结客户端。交付可编辑 Blender 工程、带蒙皮的 GLB、正式 Godot v2 工程中的可操作验证场景、真实截图及检查报告。

美术终审与工程检查分别记录；骨骼数量或脚本成功不能证明造型、穿模和动作质量合格。表情、完整战斗招式、布料物理与最终 NPR 材质仍需各自验证，不能随绑骨自动宣告完成。

## 输入与实测问题

- 源目录：`C:\Users\TimeCraker\Pictures\游戏人物建模参考`，白色、橙色、紫色各三件。
- 九件均无 skin、无 animation，各部件独立缩放至约一个单位高；不能一起底面对齐。
- GLB 使用三角面 primitive；`quad` 文件名不是四边面拓扑证明。
- 素体自带短发；装配独立发型时需检查旧发遮挡与重叠。
- **橙色文件名错配**：`02_服装_quad.glb` 实为头发，`03_头发_quad.glb` 实为服装（已查看模型渲染确认）。通过清单映射正确角色，保留原始文件。

## 技术路径

1. Blender 本地导入并逐部件出图，记录哈希、尺度、轴向与模型内容。
2. 以人体为比例基准，在肩线、领口、腰线、手腕和头部标定部件变换；保留三个网格与材质，不要求焊为一个物体。
3. 适配人形骨架，使用 Blender 蒙皮工具建立身体权重。服装继承身体对应区域权重，长下摆与长发使用辅助骨并独立验证；禁止直接把长发最近点权重吸到手臂。
4. 优先复用项目已有动画来源；校准 rest pose、骨轴和比例，不能只靠相同骨名。动作烘焙后以 GLB 为交付边界，Godot 使用 AnimationPlayer/AnimationTree。
5. 验证输入源未改变、全部变形顶点有归一化权重、单顶点至多四个骨影响、导出后重导入、实际游戏移动与动画切换。正侧背及迈步/抬臂姿态出图检查。

## 路径约定

- 脚本与装配清单：`scripts/pipeline/characters/`。
- 可编辑工程：`art/characters/{white,orange,purple}/`。
- 游戏资产：`client-godot-v2/models/characters/`。
- 游戏验证场景：`client-godot-v2/scenes/character_lab/`。
- 交付证据：`art/characters/rigging-review/`；过程图片写系统临时目录。
- Blender / Godot 可执行文件由启动脚本解析，避免把旧安装路径当成事实。

## 进度（6/6）

- [x] 九件源资产检查与模型内容辨认。
- [x] 修正当前角色流程文档与工具路径。
- [x] 三角色装配、比例和多视图检查。
- [x] 三角色骨骼、蒙皮和动画导出。
- [x] Godot 可操作场景与动作/移动验证。
- [x] 交付证据、使用说明与提交。

## 参考

- [Godot：Retargeting 3D Skeletons](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html)：骨名、rest pose、轴与位移比例都影响重定向。
- [Blender：glTF 2.0](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html)：以实际导出的 skin、animation 与重导入结果验证。

### 实施记录

- 旧 Aster 骨架存在不适用于新身体的休止姿态，改用 Quaternius 免费 Standard 动作源校准。保存 CC0 许可和来源。
- AI 网格的自动热权重使用完整身体的临时封闭体求解，在厘米尺度求解后还原为米；通过表面传递保留高精模型。肩、腰、手套与靴子仍需分区修正和可视检查。
- 躯干和肢体使用 23 个主体骨（含 root），另加 4 个头发/衣摆骨；不把骨数当质量指标。
- 三人分别导出 Idle、Walk、Run、Sprint、Jump、Fall、Land、Attack（直拳）、Talk；Blender 工程已打包纹理并保留九段可编辑动作。
- 装配时按角色测量手腕和袖管截面。身体使用封闭代理体热权重，服装继承身体表面权重；肩部的细碎网格按物理距离平滑，袖口和衣摆维持独立分区。
- 当前模型具备动作基础；抽查仍有衣摆、饰件和袖管的局部拉伸/穿插。`deformation_report.json` 记录具体动作和采样帧，未据此宣称美术终审通过。
- Godot 4.7.2 Forward+ 实机中，三人各导入 26 个变形骨，九段动作均可读取；三人跳跃控制器最高约 0.89 m，白色步行产生约 0.84 m 位移，橙/紫跑步分别产生约 4.40 / 4.31 m 位移。真实画面与播放状态一起保存在报告中。
- [使用说明](../../art/characters/README.md) 与 [检查记录](../../art/characters/rigging-review/acceptance.md) 已交付；根目录提供可直接启动的测试场入口。此处 6/6 表示本阶段工程交付完成，美术终审及上文注明的后续能力仍待完成。
