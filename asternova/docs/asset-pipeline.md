# 资产制作流程（场景 · 角色 · 武器）

本文件合并了原来的场景 SOP、角色管线、武器管线和佩刀专档（2026-10-23 合并，旧文件可在 git 历史查到）。光照另见 [lighting-guide.md](lighting-guide.md)，美术风格约束见 [STYLE.md](STYLE.md)。

## 0. 所有资产共用的规则

- **验收只看引擎实拍**：在 Godot 里截图（`client-godot-v2/tests/lighting_preview.tscn` 可一次拍四套光照），交给制作人看。Blender 视口图只能作中间检查。不自报"相似度""分数"。
- **每改一步看图**：几何、权重、材质、光照改完先截图检查，再做下一步。
- **脚本只做非审美的批处理**：缩放标定、切图、烘焙、导出、改路径这类可以写脚本；造型、权重、动画重定向不能用脚本按坐标或高度硬算。
- **禁止用代码拼几何体去造立体或有机物件**（圆柱拼猫、球体拼灌木），也不要让 AI 一次生成整条街。
- **面数**：生成阶段不设上限，取 Tripo 最高档；性能有压力时再做 LOD 减面。
- **源文件和游戏副本分开**：源文件（`.blend`、原始 GLB、贴图）放 `art/`，游戏实际加载的副本放 `client-godot-v2/`。`.blend` 外链的贴图在 `art/textures/` 下，改名或移动会让 `.blend` 丢贴图。
- **场景材质不接管光照**：不写 `light()`、不用 `ambient_light_disabled`，见 [lighting-guide.md](lighting-guide.md) 第 4 节。
- **文档只写已经做到的事**，目标写在 [BLUEPRINT.md](BLUEPRINT.md)。

## 1. 场景与道具

### 1.1 来源

| 类型 | 做法 |
| :--- | :--- |
| 有特定造型的建筑和道具（便利店、自动售货机） | 先出一张**白底、无遮挡的 45° 轴测概念图**（不要拼三视图，透视误差会让 AI 生成扭曲）→ Tripo 最高档生成 → Blender 修补 |
| 通用设施和植被（长椅、路灯、盆栽） | 直接取 Poly Haven / CC0 资产库 |

### 1.2 Blender 修补与标定

1. **修几何**：删掉 AI 生成的破碎假玻璃和贴在墙内的平面"假内景"，换成干净的窗框、玻璃和真实货架；删掉悬空的碎片。
2. **标定尺寸**：1 单位 = 1 米，底面贴 `Z = 0`，建筑立面按 2 m / 4 m 网格对齐。
3. **程序化材质要烘焙**：glTF 带不走 Blender 的程序化节点（砖纹、噪波、色带），导出会变白模。地面、墙面这类材质要用 Cycles 烘焙成 2048 的 Albedo / Roughness / Normal 位图。积水处粗糙度 0.02–0.08，干燥石板 0.45–0.60。
4. **贴花**：招牌、路面标线用 PIL 脚本生成 2K PNG。Godot 里贴花材质设 `render_priority = 1~2`，防止和地面闪烁（Z-Fighting）；注意负缩放或 UV 翻转会让字反过来。
5. **导出**：GLB 放 `art/models/<类别>/`，同时复制一份到 `client-godot-v2/models/`。

### 1.3 进 Godot

- 每个建筑和道具做成独立的 `.tscn`（`client-godot-v2/scenes/entities/buildings/`、`props/`），带简化碰撞体。
- 道具和建筑用 `toon_prop.gdshader`（普通 PBR，不改光照），玻璃用 `glass_facade.gdshader`，地面用 `toon_ground_pbr.gdshader`。
- 灯光类（招牌灯、店灯、路灯）加入 `practical_light` 组，随光照预设缩放。
- 摆进 `scenes/levels/m1_street.tscn`，在四套光照下截图验收。

### 1.4 现有场景资产与脚本

| 资产 | 源文件 | 脚本（`asternova/scripts/pipeline/environment/`） |
| :--- | :--- | :--- |
| 便利店 | `art/models/neighborhood/buildings/convenience_store/` | `slice_convenience_store_concept.py`（切概念图）→ `process_convenience_store_full.py`（标定）→ `rebuild_convenience_store_endfield.py`（重建玻璃与立面）→ `surgery_convenience_store_body.py`（修残缺）→ `patch_convenience_store_crown.py`（女儿墙材质）；`build_store_game_albedo.py`、`build_store_emission_mask.py`（游戏用贴图与自发光遮罩） |
| 自动售货机 | `art/models/neighborhood/props/vending_machine/` | `slice_vending_concept.py` → `process_vending_machine.py`；`build_vending_emission_mask.py` |
| 街区整体 | `art/models/neighborhood/modern_japan_neighborhood.blend`（贴图在 `art/textures/nextgen_pbr/`） | — |
| 地面贴图 | 输出到 `client-godot-v2/art/textures/ground/` | `process_ground_pbr.py` |
| 光映广场（游戏内已删，留作素材） | `art/models/lumina_plaza/`（贴图在 `art/textures/lumina_plaza/`） | `lumina_plaza/build_lumina_assets.py` |

## 2. 角色

### 2.1 现状

- 玩家角色目前是 **CC0 人偶**，只为让战斗沙盒能跑：
  - 文件在 `client-godot-v2/models/mannequin/`，是 Quaternius 的 Universal Animation Library 免费 Standard 版，CC0 1.0，随附 `LICENSE.txt`。
  - 来源：[作者与许可说明](https://quaternius.com/packs/universalanimationlibrary.html)、[官方下载页](https://quaternius.itch.io/universal-animation-library)；实际取自 [GLTF 镜像](https://github.com/J-Ponzo/gltf-universal-animation-library)（2025-06-10 免费版，未用付费 Pro / Source 内容）。
  - 骨架是 Rigify 命名（`DEF-*`，52 骨），带 46 个动作。
  - 状态树里的旧剪辑名（`LightIdle`、`Slash1`…）到人偶剪辑名（`Idle_Loop`、`Sword_Attack`…）的映射，写在 `scripts/entities/player/character_rig.gd` 的 `CLIP_ALIASES`。连招四段暂时都映射到 `Sword_Attack`。
- 白、橙、紫三角色只有原画和 AI 分件生成的原始模型，在 `art/characters/source/`。Aster 只有设定图和 Tripo 原始雕刻（`art/models/source/aster_tripo_39caf44b/`）。都没有骨骼和权重，没有可用的绑定角色。来源与文件对应见 [art/README.md](../art/README.md)。
- 正式角色的地基（见 2.3）**待制作人选定**。

### 2.2 旧路线为什么走不通

旧做法：身体、服装、头发分别送 Tripo 生成，再在 Blender 里对齐，用脚本按高度分配权重，手算动画重定向。问题出在地基上，后面怎么修都修不好：

1. **三个部件各自生成，尺度和形状不对应**。头发模型里带假头，身体模型里带短发，服装要靠缩放硬套，一动就穿。
2. **AI 生成的脸没有五官几何**，眼睛嘴巴画在贴图上，不能眨眼、不能做表情。
3. **AI 模型没有骨骼和权重**。旧文档写"Tripo 直接生成 Humanoid 骨骼"，实际 9 个 GLB 全部零蒙皮；脚本按高度分骨，头发和衣领跟错骨头，攻击时头部后翻。

行业做法是：**先有一个拓扑、五官、骨骼都正确的身体，头发和服装在这个身体上做**。AI 适合出设定图、贴图和道具，不适合直接出要绑定的角色。

### 2.3 地基三选一（待制作人决定）

| 方案 | 做法 | 优点 | 代价 |
| :--- | :--- | :--- | :--- |
| **A. VRoid（推荐起步）** | VRoid Studio 按原画捏脸、做发型和服装，导出 VRM | 自带五官、表情形态键、Humanoid 骨骼和头发骨骼；Godot 有成熟的 VRM 导入插件 | 默认偏"VRoid 脸"，要靠贴图、发型、服装拉开风格；复杂服装需 Blender 补 |
| **B. 商用二次元素体** | 买可商用的 anime base mesh，在其上做头发和服装 | 质量上限高，拓扑和表情是专业做的 | 要花钱、读许可；建模工作量大 |
| **C. AI 一体生成 + 自动绑骨** | 一次生成完整角色（不拆件），AccuRIG 或 Mixamo 绑骨 | 最快 | 无表情，头发是硬块，近景不能看；只适合中远景 |

无论选哪种，头、脖子、头发都来自同一个身体，"头部绑不上"的问题从结构上消失。

### 2.4 制作步骤

1. **设定图**：用 `art/characters/` 里的海报和多视图做参考。新出图要求：纯白背景、正交四视图（正、左、背、右）、微 A-Pose（双臂离体约 40°）、头顶到脚底完整。
2. **身体与脸**：按选定的地基制作，比例按每个角色的海报测量，不套固定头身比。
3. **头发和服装**：在这个身体上做，不单独生成后再套。
4. **骨骼与权重**：用地基自带骨骼（VRM），或 AccuRIG / Mixamo。服装权重在 Blender 里用数据传递（Data Transfer）从身体拷贝，摆姿势检查。
5. **导入 Godot**：VRM 用导入插件，其他用 glTF；导入设置里配 `BoneMap` + `SkeletonProfileHumanoid`，项目动画即可重定向。
6. **接入游戏**：
   1. 参照 `scenes/entities/character_mannequin.tscn` 新建角色场景，挂 `CharacterRig`。
   2. 按新骨骼改 `hand_bone`、`scabbard_bone` 和握刀、挂鞘的位置朝向，并把 `CLIP_ALIASES` 改成指向新动画。
   3. 在 `player.tscn` 里替换 `Character` 节点。
7. **着色**：用 `toon_character.gdshader`。面部 SDF 阴影、表情等精修做出来并实拍验证后，才写进"现状"。
8. **验收**：跑 `tests/test_combat_runner.gd`（插槽、动画、零权重检查），再在 `m1_street` 四套光照下各截一张给制作人看。

## 3. 武器

### 3.1 规范

| 类型 | 三角面 | 材质 | 贴图 |
| :--- | :--- | :--- | :--- |
| 单手兵器（太刀、单手剑） | 800–1,500（刀身 500–900，鞘 300–600） | 1 | 2048 图集 |
| 双手兵器（大剑、长枪） | 1,500–2,500 | 1 | 2048 图集 |
| 法器、浮游刃 | 600–1,200 | 1 | 1024 或 2048 |

- **不雕细碎花纹**，抓修长剪影和大块面特征，细节靠贴图刻线。
- **拓扑**：不留布尔运算杂面，整理成四边面再三角化；刀柄、刀鞘截面 8 或 10 边形加平滑着色。
- **分件与原点**：刀身（`Blade_Mesh`）和刀鞘（`Scabbard_Mesh`）分开，**原点都放在鞘口（Koiguchi）中心**，入鞘时两者都在原点。
- **贴图**：武器这类硬表面允许用脚本绘制贴图（对称、可复现）；角色的脸、眼睛不行。配色遵守 STYLE.md。
- **描边**：游戏里由 `CharacterRig` 给武器加 `outline.gdshader`（Inverted Hull），厚度 0.0009，颜色 `#3D435C`。
- **导出**：glTF Binary，只导出两个分件，Y 轴朝上、应用修改器、带切线。

### 3.2 怎么挂到角色上

由 `client-godot-v2/scripts/entities/player/character_rig.gd` 处理：

- 骨骼插槽：右手 `Hand_R_Weapon_Socket`（挂在 `hand_bone`），左腰 `Pelvis_L_Scabbard_Socket`（挂在 `scabbard_bone`）。
- 游戏里的太刀（`client-godot-v2/models/weapons/katana.glb`）刀身沿原点 −Y 方向伸展，长约 0.7 m；握心在 +Y 0.13 m。
- 纳刀时刀身和刀鞘都挂在腰部插槽。拔刀时刀身改挂到右手插槽，并偏移 `(0, -0.13, 0)`，让握心正好落在掌心。
- 换角色时只需改插槽的骨骼名和位置朝向（`hand_grip_*`、`scabbard_*` 这几个导出参数），刀的结构不用动。

### 3.3 现有武器：Aster 佩刀「星霜月华」

- **设定图**：`art/characters/aster/weapon-turnaround-final.png`
- **尺寸**：全长约 95.9 cm（刃 70 cm，柄 24.5 cm，鞘 72.1 cm）
- **面数**：899 三角面（刀身 503，刀鞘 396）
- **配色**：象牙白 `#E0E0E8`（鞘身）、香槟金 `#EBC57A`（护手、鞘口、鞘尾）、深蓝 `#18243B`–`#223E75`（柄卷）、浅蓝 `#8AC2EB`（系绪蝴蝶结）、水蓝 `#5FD2EE`（宝石）
- **文件**（`art/models/weapons/aster_katana/`）：
  - `aster_katana.blend`：源工程
  - `aster_katana.glb`
  - `textures/tex_katana_basecolor.png`：2048 图集
  - `katana_preview.png`：五视角看板
  - `aster_katana_3d_viewer.html`：双击用浏览器打开，可 360° 旋转、按空格拔刀、按 W 看线框
- **脚本**（`asternova/scripts/pipeline/weapons/`）：
  - `build_aster_katana_mesh.py`：建模与导出
  - `build_katana_texture.py`：贴图
  - `composite_katana_showcase.py`：看板
  - `generate_katana_web_viewer.py`：网页检视器

### 3.4 做一把新武器

1. 拿到正交全分件设定图（全长、刃长、柄长、截面）。
2. 定分件，原点放在插槽锁扣中心。
3. 用最简块面建低模，控制在预算内。
4. 在一张 2048 图集里画贴图。
5. 导出 GLB，复制到 `client-godot-v2/models/weapons/`。
6. 在战斗沙盒里看手持和挂腰效果，四套光照下截图给制作人看。
